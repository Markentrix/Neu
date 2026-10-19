"""Hintergrundaufgaben des Portals (einmal pro Minute): Benachrichtigungen, Terminerinnerungen, Monatsberichte, Fehlermeldungen.
Mehrfachversand wird durch Markieren der Zeilen beim Abholen (FOR UPDATE SKIP LOCKED) verhindert."""
import logging
import threading
import time
from datetime import date, datetime, timezone

from . import berichte, einstellungen, mailer, pdf
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger, kunden_empfaenger

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


def aufgaben_automatisch(cfg):
    """Legt Aufgaben für das Team an (je Anlass genau einmal) und schickt eine Sammelmail über die neuen."""
    admin = "(SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1)"
    regeln = [
        # Kunde hat geschrieben, seit 24 Stunden keine Antwort
        f"""INSERT INTO aufgaben (kunden_id, ticket_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT t.kunden_id, t.id, 'Antworten: ' || k.firma || ' – ' || t.betreff, {admin}, current_date, 'auto',
                   'ticket-antwort-' || t.id || '-' || (SELECT max(n.id) FROM ticket_nachrichten n WHERE n.ticket_id = t.id)
            FROM tickets t JOIN kunden k ON k.id = t.kunden_id
            WHERE t.status IN ('offen','in_arbeit') AND t.letzte_nachricht_von = 'kunde' AND t.geaendert_am < now() - interval '24 hours'
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING titel""",
        # Wir warten seit einer Woche auf den Kunden
        f"""INSERT INTO aufgaben (kunden_id, ticket_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT t.kunden_id, t.id, 'Nachfassen: ' || k.firma || ' – ' || t.betreff, {admin}, current_date, 'auto', 'nachfassen-' || t.id || '-' || to_char(t.geaendert_am, 'YYYYMMDDHH24MISS')
            FROM tickets t JOIN kunden k ON k.id = t.kunden_id
            WHERE t.status = 'wartet_auf_kunde' AND t.geaendert_am < now() - interval '7 days'
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING titel""",
        # Rechnung überfällig
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT b.kunden_id, 'Rechnung ' || b.nummer || ' überfällig: ' || k.firma, {admin}, current_date, 'auto', 'rechnung-' || b.id
            FROM belege b JOIN kunden k ON k.id = b.kunden_id
            WHERE b.art = 'rechnung' AND b.status IN ('gestellt','versendet') AND b.faellig_am < current_date AND b.nummer IS NOT NULL
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING titel""",
        # Mindestlaufzeit endet in den nächsten 60 Tagen
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT b.kunden_id, 'Vertrag: Mindestlaufzeit endet am ' || to_char(b.mindestlaufzeit_ende, 'DD.MM.YYYY') || ' – ' || k.firma, {admin}, current_date, 'auto', 'vertrag-' || b.id || '-' || b.mindestlaufzeit_ende
            FROM buchungen b JOIN kunden k ON k.id = b.kunden_id
            WHERE b.status = 'aktiv' AND b.mindestlaufzeit_ende BETWEEN current_date AND current_date + 60 AND k.status = 'aktiv'
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING titel""",
        # Kunde hängt im Onboarding: seit 5 Tagen angelegt, einmal pro Woche eine Aufgabe zum Nachfassen
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT k.id, 'Onboarding nachfassen: ' || k.firma, {admin}, current_date, 'auto', 'onboarding-' || k.id || '-' || to_char(current_date, 'IYYY-IW')
            FROM kunden k
            WHERE k.status = 'onboarding' AND k.erstellt_am < now() - interval '5 days'
              AND EXISTS (SELECT 1 FROM onboarding_punkte p WHERE p.kunden_id = k.id AND NOT p.erledigt)
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING titel""",
    ]
    neu, erinnern, onb = [], [], []
    with tx("system") as cur:
        for sql_text in regeln:
            cur.execute(sql_text)
            neu += [r["titel"] for r in cur.fetchall()]
        # Freigabe wartet seit 3 Tagen: Kunde einmal erinnern
        cur.execute("""WITH offen AS (SELECT id FROM kundenfreigaben WHERE status = 'wartet' AND erinnert_am IS NULL AND angefragt_am < now() - interval '3 days' LIMIT 50 FOR UPDATE SKIP LOCKED)
                       UPDATE kundenfreigaben f SET erinnert_am = now() FROM offen WHERE f.id = offen.id RETURNING f.kunden_id, f.titel""")
        for r in cur.fetchall():
            cur.execute("SELECT ansprechpartner, status FROM kunden WHERE id=%s", (r["kunden_id"],))
            k = cur.fetchone()
            if k and k["status"] in ("onboarding", "aktiv"):
                erinnern.append((kunden_empfaenger(cur, r["kunden_id"]), k["ansprechpartner"], r["titel"]))
        # Kunde im Onboarding (seit 3 Tagen) hat Briefing oder AVV offen: höchstens einmal pro Woche erinnern
        cur.execute("""SELECT k.id, k.ansprechpartner,
                              NOT EXISTS (SELECT 1 FROM briefings b WHERE b.kunden_id = k.id AND b.status = 'abgeschickt') AS briefing_offen,
                              NOT EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id = k.id AND a.datei IS NOT NULL AND a.unterschrieben_am IS NOT NULL)
                                AND EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id = k.id AND a.portal_freigabe_am IS NOT NULL) AS avv_offen
                       FROM kunden k
                       WHERE k.status = 'onboarding' AND k.erstellt_am < now() - interval '3 days'
                         AND (k.onboarding_erinnert_am IS NULL OR k.onboarding_erinnert_am < now() - interval '7 days') LIMIT 30""")
        for k in cur.fetchall():
            offen = (["das Briefing ausfüllen"] if k["briefing_offen"] else []) + (["den Vertrag zur Auftragsverarbeitung bestätigen"] if k["avv_offen"] else [])
            if not offen:
                continue
            cur.execute("UPDATE kunden SET onboarding_erinnert_am = now() WHERE id = %s", (k["id"],))
            onb.append((kunden_empfaenger(cur, k["id"]), k["ansprechpartner"], offen))
        an = cfg["alarm_email"] or admin_empfaenger(cur)
    for ziele, name, offen in onb:
        for a in ziele:
            mailer.onboarding_erinnerung_kunde(a, name, offen)
    for ziele, name, titel in erinnern:
        for a in ziele:
            mailer.freigabe_erinnerung_kunde(a, name, titel)
    if neu and an:
        mailer.aufgaben_digest_team(an, neu[:30])


def tick():
    with tx("system") as cur:
        cfg = einstellungen_lesen(cur)
    if not mailer.konfiguriert():
        return
    for job in (anfragen_mails, termin_erinnerungen, monatsberichte, fehler_melden, avv_erinnerung, aufgaben_automatisch):
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
