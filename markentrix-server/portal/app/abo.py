"""Wartungsverträge: wiederkehrende Rechnungen. Je Plan wird zum Fälligkeitstag eine Rechnung erzeugt, ausgestellt und (wenn gewünscht) versendet."""
import calendar
import json
import logging
from datetime import date, timedelta

from fastapi import HTTPException

from . import belege, mailer, push, rechtstexte

log = logging.getLogger("abo")


def monate_addieren(d: date, n: int) -> date:
    m = d.month - 1 + n
    j, mo = d.year + m // 12, m % 12 + 1
    return date(j, mo, min(d.day, calendar.monthrange(j, mo)[1]))


def zeitraum(start: date, monate: int) -> str:
    ende = monate_addieren(start, monate) - timedelta(days=1)
    return f"{start:%d.%m.%Y} – {ende:%d.%m.%Y}"


def _positionen(cur, plan: dict) -> list:
    if not plan["aus_buchungen"]:
        return belege.positionen_pruefen(plan["positionen"])
    cur.execute("""SELECT p.name, b.monatlich_cent, b.rabatt_cent FROM buchungen b JOIN produkte p ON p.code = b.produkt_code
                   WHERE b.kunden_id = %s AND b.status IN ('aktiv') AND b.monatlich_cent > 0 ORDER BY b.erstellt_am""", (plan["kunden_id"],))
    return [{"text": f"{r['name']} – monatlich", "menge": plan["intervall_monate"], "einheit": "Monate", "preis_cent": int(r["monatlich_cent"] - (r["rabatt_cent"] or 0))}
            for r in cur.fetchall()]


def erzeugen(cur, plan: dict, jetzt: bool = False) -> dict | None:
    """Erzeugt und stellt die nächste Rechnung eines Plans aus und schiebt den Plan weiter. Gibt None zurück, wenn nichts zu tun ist (Referenzkunde, keine Positionen, Vertragsende)."""
    start = plan["naechste_am"]
    cur.execute("SELECT referenzkunde, status FROM kunden WHERE id=%s", (plan["kunden_id"],))
    k = cur.fetchone()
    if not k or k["referenzkunde"] or k["status"] != "aktiv":
        return None
    cur.execute("SELECT min(ende_am) AS e FROM kuendigungswuensche WHERE kunden_id=%s AND status IN ('offen','bearbeitet') AND vollzogen_am IS NULL", (plan["kunden_id"],))
    ende = (cur.fetchone() or {}).get("e")
    if (plan["enddatum"] and start > plan["enddatum"]) or (ende and start >= ende):
        cur.execute("UPDATE abrechnungsplaene SET aktiv=false WHERE id=%s", (plan["id"],))
        return None
    cur.execute("SELECT 1 FROM belege WHERE plan_id=%s AND leistungszeitraum=%s AND storno_von IS NULL", (plan["id"], zeitraum(start, plan["intervall_monate"])))
    if cur.fetchone():          # dieser Zeitraum wurde schon abgerechnet (z. B. Datum von Hand zurückgesetzt): nur weiterrücken
        cur.execute("UPDATE abrechnungsplaene SET naechste_am=%s WHERE id=%s", (monate_addieren(start, plan["intervall_monate"]), plan["id"]))
        return None
    pos = _positionen(cur, plan)
    if not pos:
        return None
    f = rechtstexte.firma(cur)
    belege.firmendaten_pruefen(f)
    s = belege.summen(pos, f["mwst_satz"], f["kleinunternehmer"])
    if s["brutto_cent"] <= 0:
        return None
    lz = zeitraum(start, plan["intervall_monate"])
    nummer = belege.naechste_nummer(cur, "rechnung", f["rechnungsprefix"] or "RE")
    heute = date.today()
    cur.execute("""INSERT INTO belege (art, kunden_id, betreff, positionen, leistungen, leistungszeitraum, netto_cent, ust_satz, ust_cent, brutto_cent, kleinunternehmer, plan_id,
                                       nummer, status, datum, faellig_am, empfaenger)
                   VALUES ('rechnung',%s,%s,%s::jsonb,'[]'::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,'gestellt',%s,%s,%s::jsonb) RETURNING id""",
                (plan["kunden_id"], plan["titel"], json.dumps(pos), lz, s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"], plan["id"],
                 nummer, heute, heute + timedelta(days=f["zahlungsziel_tage"]), json.dumps(belege.empfaenger_von(cur, plan["kunden_id"]), default=str)))
    bid = cur.fetchone()["id"]
    cur.execute("UPDATE abrechnungsplaene SET naechste_am=%s, zuletzt_beleg_id=%s, zuletzt_am=%s WHERE id=%s", (monate_addieren(start, plan["intervall_monate"]), bid, heute, plan["id"]))
    cur.execute("INSERT INTO audit_log (kunden_id, aktion, details) VALUES (%s,'beleg_abo_erzeugt',%s::jsonb)", (plan["kunden_id"], json.dumps({"nummer": nummer, "plan": str(plan["id"])})))
    return {"id": bid, "nummer": nummer, "zeitraum": lz}


def senden(bid) -> tuple[bool, str]:
    from .db import tx
    with tx("system") as cur:
        cur.execute("SELECT b.art, b.nummer, b.faellig_am, k.email, k.ansprechpartner FROM belege b JOIN kunden k ON k.id = b.kunden_id WHERE b.id=%s", (bid,))
        b = cur.fetchone()
        if not b or not b["email"]:
            return False, "keine E-Mail-Adresse beim Kunden"
        daten, name = belege.beleg_pdf(cur, bid)
    ok, fehler = mailer.beleg(b["email"], b["art"], b["nummer"], b["ansprechpartner"], daten, name, b["faellig_am"])
    if ok:
        with tx("system") as cur:
            cur.execute("UPDATE belege SET versendet_am=now(), status='versendet', geaendert_am=now() WHERE id=%s AND status='gestellt'", (bid,))
    return ok, fehler


def lauf(cfg=None) -> int:
    """Täglicher Lauf: alle fälligen Pläne abrechnen."""
    from .db import tx
    with tx("system") as cur:
        cur.execute("SELECT id FROM abrechnungsplaene WHERE aktiv AND naechste_am <= current_date ORDER BY naechste_am LIMIT 100")
        ids = [r["id"] for r in cur.fetchall()]
    n = 0
    for pid in ids:
        for _ in range(3):         # nachholen, wenn ein Plan länger ruhte
            try:
                with tx("system") as cur:
                    cur.execute("SELECT p.*, k.firma FROM abrechnungsplaene p JOIN kunden k ON k.id = p.kunden_id WHERE p.id=%s AND p.aktiv AND p.naechste_am <= current_date FOR UPDATE OF p SKIP LOCKED", (pid,))
                    plan = cur.fetchone()
                    if not plan:
                        break
                    r = erzeugen(cur, plan)
                    admins = push.admins(cur) if r else []
            except HTTPException as e:         # z. B. Firmendaten unvollständig: nicht jeden Tag mit Stacktrace melden
                log.warning("Abrechnungsplan %s: %s", pid, e.detail)
                break
            except Exception:  # noqa: BLE001
                log.exception("Abrechnungsplan %s", pid)
                break
            if not r:
                break
            n += 1
            gesendet = False
            if plan["auto_senden"] and mailer.konfiguriert():
                gesendet, _ = senden(r["id"])
            if admins:
                push.senden(admins, "Wartungsrechnung", f"{r['nummer']} für {plan['firma']} ({r['zeitraum']}) " + ("wurde versendet." if gesendet else "liegt zum Versand bereit."), "/admin#kunden", "abo")
    return n
