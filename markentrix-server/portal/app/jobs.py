"""Hintergrundaufgaben des Portals (einmal pro Minute): Benachrichtigungen, Terminerinnerungen, Monatsberichte, Fehlermeldungen.
Mehrfachversand wird durch Markieren der Zeilen beim Abholen (FOR UPDATE SKIP LOCKED) verhindert."""
import logging
import threading
import time
from datetime import date, datetime, timezone

from . import berichte, einstellungen, mailer, pdf
from .db import tx

log = logging.getLogger("jobs")
_stop = threading.Event()
STANDARD = {"alarm_email": "", "anfrage_mails": True, "termin_erinnerung": True, "termin_stunden": 24, "monatsbericht": True}


def einstellungen_lesen(cur) -> dict:
    return {**STANDARD, **einstellungen.lesen(cur, "benachrichtigung")}


def _empfaenger(k) -> str | None:
    return (k.get("benachr_email") or k.get("email") or "").strip() or None


def anfragen_mails(cfg):
    if not cfg["anfrage_mails"]:
        return
    with tx("system") as cur:
        cur.execute("""WITH offen AS (SELECT a.id FROM anfragen a WHERE NOT a.benachrichtigt AND a.erstellt_am > now() - interval '3 days'
                                      ORDER BY a.erstellt_am LIMIT 50 FOR UPDATE SKIP LOCKED)
                       UPDATE anfragen a SET benachrichtigt = true FROM offen WHERE a.id = offen.id
                       RETURNING a.id, a.kunden_id, a.name, a.kontakt, a.nachricht, a.quelle, a.status, a.erstellt_am""")
        rows = cur.fetchall()
        kunden = {}
        for r in rows:
            if r["status"] == "spam":
                continue
            kunden.setdefault(r["kunden_id"], []).append(r)
        ziele = []
        for kid, liste in kunden.items():
            cur.execute("SELECT firma, email, benachr_email, benachr_anfragen, status FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if k and k["benachr_anfragen"] and k["status"] in ("onboarding", "aktiv") and _empfaenger(k):
                ziele.append((k, liste))
    for k, liste in ziele:
        ok, fehler = mailer.neue_anfragen(_empfaenger(k), k["firma"], liste)
        if not ok:
            log.warning("Anfrage-Mail an %s fehlgeschlagen: %s", k["firma"], fehler)


def termin_erinnerungen(cfg):
    if not cfg["termin_erinnerung"]:
        return
    with tx("system") as cur:
        cur.execute("""WITH offen AS (SELECT t.id FROM termine t WHERE NOT t.erinnerung_gesendet AND t.status IN ('geplant','bestaetigt')
                                      AND t.beginn > now() AND t.beginn <= now() + make_interval(hours => %s) LIMIT 100 FOR UPDATE SKIP LOCKED)
                       UPDATE termine t SET erinnerung_gesendet = true FROM offen WHERE t.id = offen.id
                       RETURNING t.kunden_id, t.titel, t.beginn, t.kontakt_name""", (int(cfg["termin_stunden"]),))
        rows = cur.fetchall()
        kunden = {}
        for r in rows:
            kunden.setdefault(r["kunden_id"], []).append(r)
        ziele = []
        for kid, liste in kunden.items():
            cur.execute("SELECT firma, email, benachr_email, benachr_termine, status FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if k and k["benachr_termine"] and k["status"] in ("onboarding", "aktiv") and _empfaenger(k):
                ziele.append((k, sorted(liste, key=lambda x: x["beginn"])))
    for k, liste in ziele:
        ok, fehler = mailer.termin_erinnerung(_empfaenger(k), liste)
        if not ok:
            log.warning("Terminerinnerung an %s fehlgeschlagen: %s", k["firma"], fehler)


def monatsberichte(cfg):
    """Ab dem 1. eines Monats (7 Uhr UTC) für den Vormonat; jeder Kunde genau einmal."""
    jetzt = datetime.now(timezone.utc)
    if not cfg["monatsbericht"] or jetzt.day > 7 or jetzt.hour < 7:
        return
    vm = berichte.vormonat(jetzt.date())
    von, bis = berichte.monat_grenzen(vm)
    with tx("system") as cur:
        cur.execute("""SELECT k.id FROM kunden k WHERE k.status = 'aktiv' AND k.erstellt_am < %s AND k.benachr_bericht
                       AND NOT EXISTS (SELECT 1 FROM berichte b WHERE b.kunden_id = k.id AND b.art = 'monatsbericht' AND b.zeitraum_von = %s)
                       ORDER BY k.erstellt_am LIMIT 20""", (bis, von))
        ids = [r["id"] for r in cur.fetchall()]
    for kid in ids:
        bericht_senden(kid, vm, mail=True)


def bericht_senden(kid, monat: date, mail: bool = True) -> dict:
    """Erstellt/aktualisiert den Bericht und verschickt ihn. Gibt {id, gesendet, grund} zurück."""
    with tx("system") as cur:
        bid = berichte.erstellen(cur, kid, monat)
        cur.execute("SELECT firma, email, benachr_email FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        daten, name = berichte.pdf_erzeugen(cur, bid)
    an = _empfaenger(k)
    if not mail:
        return {"id": bid, "gesendet": False, "grund": ""}
    if not an:
        return {"id": bid, "gesendet": False, "grund": "Der Kunde hat keine E-Mail-Adresse hinterlegt."}
    ok, fehler = mailer.monatsbericht(an, k["firma"], pdf.monat_name(monat), daten, name)
    if ok:
        with tx("system") as cur:
            cur.execute("UPDATE berichte SET versendet_am=now() WHERE id=%s", (bid,))
    return {"id": bid, "gesendet": ok, "grund": fehler}


def fehler_melden(cfg):
    with tx("system") as cur:
        cur.execute("""WITH offen AS (SELECT id FROM workflow_fehler WHERE NOT benachrichtigt AND zeit > now() - interval '2 days' ORDER BY zeit LIMIT 50 FOR UPDATE SKIP LOCKED)
                       UPDATE workflow_fehler f SET benachrichtigt = true FROM offen WHERE f.id = offen.id
                       RETURNING f.workflow_name, f.knoten, f.fehlertext, f.zeit""")
        rows = cur.fetchall()
        an = cfg["alarm_email"]
        if not an:
            cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
            r = cur.fetchone()
            an = r and r["email"]
    if rows and an:
        zeilen = [f"- {r['zeit']:%d.%m. %H:%M} {r['workflow_name'] or 'Workflow'} / {r['knoten'] or '?'}: {(r['fehlertext'] or '')[:200]}" for r in rows]
        mailer.senden(an, f"{len(rows)} Workflow-Fehler" if len(rows) > 1 else "Workflow-Fehler", "Es sind Fehler in Automationen aufgetreten:\n\n" + "\n".join(zeilen) + mailer.SIGNATUR)


def avv_erinnerung(cfg):
    """Erinnert den Admin höchstens einmal pro Woche und Kunde, wenn drei Tage nach Anlage noch kein unterschriebener AVV vorliegt."""
    with tx("system") as cur:
        cur.execute("""WITH offen AS (
                         SELECT k.id FROM kunden k
                         WHERE k.status IN ('onboarding','aktiv','pausiert') AND k.erstellt_am < now() - interval '3 days'
                           AND (k.avv_erinnert_am IS NULL OR k.avv_erinnert_am < now() - interval '7 days')
                           AND NOT EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.datei IS NOT NULL AND a.unterschrieben_am IS NOT NULL)
                         ORDER BY k.erstellt_am LIMIT 50 FOR UPDATE SKIP LOCKED)
                       UPDATE kunden k SET avv_erinnert_am = now() FROM offen WHERE k.id = offen.id
                       RETURNING k.kundennummer, k.firma""")
        rows = cur.fetchall()
        an = cfg["alarm_email"]
        if not an:
            cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
            r = cur.fetchone()
            an = r and r["email"]
    if rows and an:
        zeilen = [f"- {r['kundennummer']} {r['firma']}" for r in rows]
        mailer.senden(an, "AVV fehlt bei " + (f"{len(rows)} Kunden" if len(rows) > 1 else "einem Kunden"),
                      "Für diese Kunden liegt noch kein unterschriebener Auftragsverarbeitungsvertrag (AVV) vor:\n\n" + "\n".join(zeilen) +
                      "\n\nIm Portal beim jeweiligen Kunden: AVV erstellen, senden und die unterschriebene Fassung ablegen." + mailer.SIGNATUR)


def tick():
    with tx("system") as cur:
        cfg = einstellungen_lesen(cur)
    if not mailer.konfiguriert():
        return
    for job in (anfragen_mails, termin_erinnerungen, monatsberichte, fehler_melden, avv_erinnerung):
        try:
            job(cfg)
        except Exception:  # ein kaputter Job darf die anderen nicht stoppen
            log.exception("Job %s fehlgeschlagen", job.__name__)


def _schleife():
    time.sleep(15)
    while not _stop.is_set():
        try:
            tick()
        except Exception:
            log.exception("Tick fehlgeschlagen")
        _stop.wait(60)


def starten():
    _stop.clear()
    threading.Thread(target=_schleife, name="mk-jobs", daemon=True).start()


def stoppen():
    _stop.set()
