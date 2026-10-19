"""Dashboard-Funktionen: globale Suche, Kunden-Zeitachse, Geschäftszahlen, Ansicht je Benutzer, Benachrichtigungen (Glocke)."""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .db import tx
from .routes_fruehwarnung import risiko_fuer
from .security import current_user, require_admin

router = APIRouter(prefix="/api")
KEY = re.compile(r"^[a-z0-9_-]{1,30}$")


def _darf(user: dict, bereich: str) -> bool:
    r = user.get("admin_rechte")
    return r is None or bereich in r


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# ---------------------------------------------------------------- Suche
@router.get("/admin/suche")
def suche(q: str = "", user: dict = Depends(require_admin)):
    q = q.strip()[:80]
    if len(q) < 2:
        return {"gruppen": []}
    p = _like(q)
    gruppen = []
    with tx("admin") as cur:
        if _darf(user, "kunden"):
            cur.execute("""SELECT id, kundennummer, firma, ort, status FROM kunden
                           WHERE firma ILIKE %s OR kundennummer ILIKE %s OR email ILIKE %s OR ansprechpartner ILIKE %s OR ort ILIKE %s OR domain ILIKE %s
                           ORDER BY (lower(firma) LIKE lower(%s)) DESC, firma LIMIT 6""", (p, p, p, p, p, p, q.replace("%", "") + "%"))
            gruppen.append({"art": "Kunden", "treffer": [{"titel": r["firma"], "text": f"{r['kundennummer']} · {r['ort'] or ''} · {r['status']}", "link": "#kunde/" + str(r["id"])} for r in cur.fetchall()]})
        if _darf(user, "leads"):
            cur.execute("""SELECT id, firma, ansprechpartner, ort, status, temperatur FROM leads
                           WHERE firma ILIKE %s OR ansprechpartner ILIKE %s OR email ILIKE %s OR telefon ILIKE %s OR ort ILIKE %s ORDER BY erstellt_am DESC LIMIT 6""", (p, p, p, p, p))
            gruppen.append({"art": "Leads", "treffer": [{"titel": r["firma"], "text": f"{r['ort'] or ''} · {r['status']}" + (f" · {r['temperatur']}" if r["temperatur"] else ""), "link": "#lead/" + str(r["id"])} for r in cur.fetchall()]})
        if _darf(user, "finanzen"):
            cur.execute("""SELECT b.id, b.art, b.nummer, b.betreff, b.status, k.firma FROM belege b JOIN kunden k ON k.id = b.kunden_id
                           WHERE b.nummer ILIKE %s OR b.betreff ILIKE %s ORDER BY b.erstellt_am DESC LIMIT 6""", (p, p))
            gruppen.append({"art": "Angebote & Rechnungen", "treffer": [{"titel": (r["nummer"] or "Entwurf") + " " + (r["betreff"] or ""), "text": f"{r['firma']} · {r['status']}", "link": "#beleg/" + str(r["id"])} for r in cur.fetchall()]})
        if _darf(user, "nachrichten"):
            cur.execute("""SELECT t.id, t.betreff, t.status, k.firma FROM tickets t JOIN kunden k ON k.id = t.kunden_id
                           WHERE t.betreff ILIKE %s OR t.nummer::text = %s ORDER BY t.geaendert_am DESC LIMIT 6""", (p, q))
            gruppen.append({"art": "Nachrichten", "treffer": [{"titel": r["betreff"], "text": f"{r['firma']} · {r['status']}", "link": "#postfach/" + str(r["id"])} for r in cur.fetchall()]})
        cur.execute("SELECT id, titel, faellig_am FROM aufgaben WHERE status='offen' AND titel ILIKE %s ORDER BY faellig_am NULLS LAST LIMIT 5", (p,))
        gruppen.append({"art": "Aufgaben", "treffer": [{"titel": r["titel"], "text": f"fällig {r['faellig_am']:%d.%m.%Y}" if r["faellig_am"] else "offen", "link": "#aufgaben"} for r in cur.fetchall()]})
    return {"gruppen": [g for g in gruppen if g["treffer"]]}


# ---------------------------------------------------------------- Zeitachse
AUDIT_SICHTBAR = {"vorlage_angewendet": "Branchenvorlage angewendet", "mahnung": "Zahlungserinnerung/Mahnung", "sepa_mandat_erteilt": "Lastschriftmandat erteilt",
                  "sepa_mandat_widerrufen": "Lastschriftmandat widerrufen", "rechnung_bezahlt": "Rechnung bezahlt", "lastschrift_zurueck": "Lastschrift zurückgesetzt"}


@router.get("/admin/kunden/{kid}/zeitachse")
def zeitachse(kid: str, user: dict = Depends(require_admin)):
    ev = []
    with tx("admin") as cur:
        try:
            cur.execute("SELECT id, status, erstellt_am FROM kunden WHERE id=%s", (kid,))
        except Exception:
            raise HTTPException(404, "Kunde nicht gefunden.")
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        ev.append((k["erstellt_am"], "kunde", "Kunde angelegt", None))
        cur.execute("SELECT erstellt_am, name, quelle, left(nachricht, 140) AS t FROM anfragen WHERE kunden_id=%s AND status<>'spam' ORDER BY erstellt_am DESC LIMIT 30", (kid,))
        ev += [(r["erstellt_am"], "anfrage", "Anfrage" + (f" von {r['name']}" if r["name"] else "") + f" ({r['quelle']})", r["t"]) for r in cur.fetchall()]
        cur.execute("SELECT beginn, richtung, dauer_sek, left(zusammenfassung, 140) AS t FROM anrufe WHERE kunden_id=%s ORDER BY beginn DESC LIMIT 30", (kid,))
        ev += [(r["beginn"], "anruf", "Anruf " + ("eingehend" if r["richtung"] == "ein" else "ausgehend"), r["t"]) for r in cur.fetchall()]
        cur.execute("SELECT nummer, art, status, datum, bezahlt_am, brutto_cent, erstellt_am FROM belege WHERE kunden_id=%s AND status<>'entwurf' ORDER BY erstellt_am DESC LIMIT 30", (kid,))
        for r in cur.fetchall():
            eur = f"{int(r['brutto_cent']) / 100:.2f} €".replace(".", ",")
            ev.append((datetime.combine(r["datum"] or r["erstellt_am"].date(), datetime.min.time(), timezone.utc), "beleg", ("Rechnung " if r["art"] == "rechnung" else "Angebot ") + (r["nummer"] or "") + " ausgestellt", eur))
            if r["bezahlt_am"]:
                ev.append((datetime.combine(r["bezahlt_am"], datetime.min.time(), timezone.utc), "zahlung", f"Rechnung {r['nummer']} bezahlt", eur))
        cur.execute("SELECT erstellt_am, betreff, status FROM tickets WHERE kunden_id=%s ORDER BY erstellt_am DESC LIMIT 20", (kid,))
        ev += [(r["erstellt_am"], "nachricht", "Nachricht: " + r["betreff"], r["status"]) for r in cur.fetchall()]
        cur.execute("SELECT beginn, titel, status FROM termine WHERE kunden_id=%s ORDER BY beginn DESC LIMIT 20", (kid,))
        ev += [(r["beginn"], "termin", "Termin: " + r["titel"], r["status"]) for r in cur.fetchall()]
        cur.execute("SELECT versendet_am, titel FROM berichte WHERE kunden_id=%s AND versendet_am IS NOT NULL ORDER BY versendet_am DESC LIMIT 12", (kid,))
        ev += [(r["versendet_am"], "bericht", "Bericht versendet: " + (r["titel"] or ""), None) for r in cur.fetchall()]
        cur.execute("SELECT zeit, aktion FROM audit_log WHERE kunden_id=%s AND aktion = ANY(%s) ORDER BY id DESC LIMIT 20", (kid, list(AUDIT_SICHTBAR)))
        ev += [(r["zeit"], "system", AUDIT_SICHTBAR[r["aktion"]], None) for r in cur.fetchall()]
        # Zustand
        risiko = risiko_fuer(cur, kid)
        cur.execute("""SELECT coalesce(sum(brutto_cent - coalesce(bezahlt_cent,0)) FILTER (WHERE status IN ('gestellt','versendet')),0) AS offen,
                              count(*) FILTER (WHERE status IN ('gestellt','versendet') AND faellig_am < current_date) AS ueberfaellig
                       FROM belege WHERE kunden_id=%s AND art='rechnung'""", (kid,))
        b = cur.fetchone()
        cur.execute("SELECT titel, faellig_am FROM aufgaben WHERE kunden_id=%s AND status='offen' ORDER BY faellig_am NULLS LAST LIMIT 1", (kid,))
        aufgabe = cur.fetchone()
        cur.execute("SELECT max(letzter_login) AS login FROM benutzer WHERE kunden_id=%s", (kid,))
        login = cur.fetchone()["login"]
        cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND status<>'spam' AND erstellt_am > now() - interval '30 days'", (kid,))
        a30 = cur.fetchone()["n"]
    ev.sort(key=lambda e: e[0], reverse=True)
    return {"ereignisse": [{"zeit": e[0], "art": e[1], "titel": e[2], "text": e[3]} for e in ev[:60]],
            "zustand": {"risiko": risiko, "offen_cent": int(b["offen"]), "ueberfaellig": b["ueberfaellig"], "aufgabe": aufgabe, "letzter_login": login, "anfragen_30d": a30}}


# ---------------------------------------------------------------- Geschäftszahlen
def cockpit_daten(cur) -> dict:
    cur.execute("""SELECT to_char(m.mon, 'YYYY-MM') AS monat,
        (SELECT count(*) FROM kunden k WHERE NOT k.referenzkunde AND date_trunc('month', k.erstellt_am) = m.mon) AS neukunden,
        (SELECT count(*) FROM kunden k WHERE NOT k.referenzkunde AND date_trunc('month', k.gekuendigt_am) = m.mon) AS kuendigungen,
        (SELECT coalesce(sum(b.bezahlt_cent), 0) FROM belege b WHERE b.art='rechnung' AND b.status='bezahlt' AND date_trunc('month', b.bezahlt_am) = m.mon) AS umsatz_cent,
        (SELECT count(*) FROM leads l WHERE date_trunc('month', l.erstellt_am) = m.mon) AS leads
        FROM (SELECT date_trunc('month', current_date) - make_interval(months => n) AS mon FROM generate_series(0, 11) n) m ORDER BY m.mon""")
    reihe = [{**r, "umsatz_cent": int(r["umsatz_cent"])} for r in cur.fetchall()]
    cur.execute("SELECT coalesce(sum(b.monatlich_cent - b.rabatt_cent),0) AS cent FROM buchungen b JOIN kunden k ON k.id=b.kunden_id WHERE b.status IN ('aktiv','in_einrichtung','beauftragt') AND b.monatlich_cent IS NOT NULL AND NOT k.referenzkunde")
    mrr = int(cur.fetchone()["cent"])
    cur.execute("SELECT count(*) AS n FROM kunden WHERE status='aktiv' AND NOT referenzkunde")
    aktiv = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM kunden WHERE NOT referenzkunde AND gekuendigt_am > now() - interval '90 days'")
    gek90 = cur.fetchone()["n"]
    cur.execute("""SELECT coalesce(sum(brutto_cent - coalesce(bezahlt_cent,0)) FILTER (WHERE status IN ('gestellt','versendet')),0) AS offen,
                          coalesce(sum(brutto_cent - coalesce(bezahlt_cent,0)) FILTER (WHERE status IN ('gestellt','versendet') AND faellig_am < current_date),0) AS ueberfaellig
                   FROM belege WHERE art='rechnung'""")
    b = cur.fetchone()
    cur.execute("SELECT count(*) AS n FROM gespraechstermine WHERE erstellt_am > now() - interval '30 days' AND status='gebucht'")
    termine = cur.fetchone()["n"]
    return {"reihe": reihe, "mrr_cent": mrr, "aktiv": aktiv, "arpu_cent": int(mrr / aktiv) if aktiv else 0, "kuendigungen_90d": gek90,
            "churn_prozent": round(100 * gek90 / (aktiv + gek90), 1) if (aktiv + gek90) else 0.0, "offen_cent": int(b["offen"]), "ueberfaellig_cent": int(b["ueberfaellig"]),
            "leads_30d": reihe[-1]["leads"], "termine_30d": termine}


@router.get("/admin/cockpit")
def cockpit(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return cockpit_daten(cur)


# ---------------------------------------------------------------- Ansicht und Glocke
class AnsichtIn(BaseModel):
    ausgeblendet: list[str] | None = Field(default=None, max_length=40)
    push_aus: list[str] | None = Field(default=None, max_length=40)


@router.get("/me/ansicht")
def ansicht_lesen(user: dict = Depends(current_user)):
    with tx("system") as cur:
        cur.execute("SELECT ansicht FROM benutzer WHERE id=%s", (user["id"],))
        a = cur.fetchone()["ansicht"] or {}
    return {"ausgeblendet": a.get("ausgeblendet", []), "push_aus": a.get("push_aus", [])}


@router.put("/me/ansicht")
def ansicht_speichern(data: AnsichtIn, user: dict = Depends(current_user)):
    for liste in (data.ausgeblendet, data.push_aus):
        if liste and not all(KEY.match(x) for x in liste):
            raise HTTPException(400, "Ungültige Auswahl.")
    import json
    with tx("system") as cur:
        cur.execute("SELECT ansicht FROM benutzer WHERE id=%s", (user["id"],))
        a = dict(cur.fetchone()["ansicht"] or {})
        if data.ausgeblendet is not None:
            a["ausgeblendet"] = sorted(set(data.ausgeblendet))
        if data.push_aus is not None:
            a["push_aus"] = sorted(set(data.push_aus))
        cur.execute("UPDATE benutzer SET ansicht=%s::jsonb WHERE id=%s", (json.dumps(a), user["id"]))
    return {"ok": True}


@router.get("/benachrichtigungen")
def benachrichtigungen(user: dict = Depends(current_user)):
    with tx("system") as cur:
        cur.execute("SELECT count(*) AS n FROM benachrichtigungen WHERE benutzer_id=%s AND gelesen_am IS NULL", (user["id"],))
        n = cur.fetchone()["n"]
        cur.execute("SELECT id, tag, titel, text, url, erstellt_am, gelesen_am FROM benachrichtigungen WHERE benutzer_id=%s ORDER BY erstellt_am DESC, id DESC LIMIT 30", (user["id"],))
        return {"ungelesen": n, "liste": cur.fetchall()}


class GelesenIn(BaseModel):
    alle: bool = False
    ids: list[int] = Field(default=[], max_length=100)


@router.post("/benachrichtigungen/gelesen")
def gelesen(data: GelesenIn, user: dict = Depends(current_user)):
    with tx("system") as cur:
        if data.alle:
            cur.execute("UPDATE benachrichtigungen SET gelesen_am=now() WHERE benutzer_id=%s AND gelesen_am IS NULL", (user["id"],))
        elif data.ids:
            cur.execute("UPDATE benachrichtigungen SET gelesen_am=now() WHERE benutzer_id=%s AND id = ANY(%s) AND gelesen_am IS NULL", (user["id"], data.ids))
    return {"ok": True}


