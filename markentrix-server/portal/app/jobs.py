"""Hintergrundaufgaben des Portals (einmal pro Minute): Benachrichtigungen, Terminerinnerungen, Monatsberichte, Fehlermeldungen.
Mehrfachversand wird durch Markieren der Zeilen beim Abholen (FOR UPDATE SKIP LOCKED) verhindert."""
import logging
import threading
import time
from datetime import date, datetime, timezone

from . import berichte, betrieb, webbetrieb, einstellungen, mailer, pdf, push
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
        ziele, pushes = [], []
        for kid, liste in kunden.items():
            cur.execute("SELECT firma, email, benachr_email, benachr_anfragen, status FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if k and k["benachr_anfragen"] and k["status"] in ("onboarding", "aktiv"):
                pushes.append((push.kunde(cur, kid), len(liste)))
                if _empfaenger(k):
                    ziele.append((k, liste))
    for ids, n in pushes:
        push.senden(ids, "Neue Anfrage" if n == 1 else f"{n} neue Anfragen", "Über Ihre Website oder Ihren Assistenten ist eine Anfrage eingegangen.", "/app#anfragen", "anfrage")
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


def lead_folgemails(cfg):
    """Nachfass-Mails an Leads mit Einwilligung, wenn noch kein Gespräch zustande kam. Nur wenn in den Einstellungen eingeschaltet."""
    from .routes_folgemails import lesen as folge_lesen, token_fuer
    with tx("system") as cur:
        f = folge_lesen(cur)
        if not f["aktiv"]:
            return
        cur.execute("""SELECT l.id, l.firma, l.ansprechpartner, l.email, l.folge_stufe FROM leads l
                       WHERE l.email IS NOT NULL AND NOT l.abgemeldet AND l.status IN ('neu','kontaktiert')
                         AND EXISTS (SELECT 1 FROM lead_aktivitaeten a WHERE a.lead_id = l.id AND a.art = 'consent')
                         AND NOT EXISTS (SELECT 1 FROM lead_aktivitaeten a WHERE a.lead_id = l.id AND a.art IN ('antwort','termin'))
                         AND ((l.folge_stufe = 0 AND l.erstellt_am < now() - make_interval(days => %s))
                           OR (l.folge_stufe = 1 AND l.folge_gesendet_am < now() - make_interval(days => %s)))
                       ORDER BY l.erstellt_am LIMIT 20""", (f["tage_1"], max(1, f["tage_2"] - f["tage_1"])))
        faellig = cur.fetchall()
        auftraege = []
        for l in faellig:
            auftraege.append((l, token_fuer(cur, l["id"])))
            cur.execute("UPDATE leads SET folge_stufe=folge_stufe+1, folge_gesendet_am=now(), letzter_kontakt_am=now() WHERE id=%s", (l["id"],))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'mail_gesendet',%s,'automatisch')", (l["id"], f"Automatische Folgemail {l['folge_stufe'] + 1}"))
    for l, tok in auftraege:
        n = l["folge_stufe"] + 1
        mailer.lead_folge(l["email"], l["ansprechpartner"], l["firma"], f["betreff_%d" % n], f["text_%d" % n], tok)


def kunden_feedback(cfg):
    """Eine Feedback-Mail 30 Tage nach Start, wenn in den Einstellungen eingeschaltet."""
    from .routes_folgemails import lesen as folge_lesen
    with tx("system") as cur:
        if not folge_lesen(cur)["kunden_feedback"]:
            return
        cur.execute("""UPDATE kunden k SET feedback_mail_am = now() WHERE k.id IN
                         (SELECT id FROM kunden WHERE status = 'aktiv' AND feedback_mail_am IS NULL AND erstellt_am < now() - interval '30 days' LIMIT 20)
                       RETURNING k.id, k.ansprechpartner""")
        kunden = cur.fetchall()
        ziele = [(kunden_empfaenger(cur, k["id"]), k["ansprechpartner"]) for k in kunden]
    for adressen, name in ziele:
        for a in adressen:
            mailer.kunden_feedback(a, name)


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
        # Domain läuft in den nächsten 60 Tagen ab (auch bei automatischer Verlängerung: Zahlungsmittel und Kundenabsprache prüfen)
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT d.kunden_id, 'Domain läuft ab: ' || d.domain || ' am ' || to_char(d.ablauf_am, 'DD.MM.YYYY') || ' – ' || k.firma, {admin}, current_date, 'auto', 'domain-' || d.id || '-' || to_char(d.ablauf_am, 'YYYYMMDD')
            FROM domains d JOIN kunden k ON k.id = d.kunden_id
            WHERE d.status = 'aktiv' AND d.ablauf_am BETWEEN current_date AND current_date + 60 AND k.status IN ('onboarding', 'aktiv', 'pausiert')
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


_stumm_gemeldet = 0.0


def ueberwachung_stumm(cfg):
    """Wenn die Server-Überwachung seit über einer Stunde nichts mehr meldet, einmal pro Tag Bescheid geben (sie sollte alle 5 Minuten laufen)."""
    global _stumm_gemeldet
    from .routes_system import lesen_status
    d = lesen_status()
    if not d or d["alter_minuten"] < 60 or time.time() - _stumm_gemeldet < 86400:
        return
    with tx("system") as cur:
        an = cfg["alarm_email"]
        if not an:
            cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
            r = cur.fetchone()
            an = r and r["email"]
    if an:
        _stumm_gemeldet = time.time()
        mailer.senden(an, "Markentrix: Die Server-Überwachung meldet sich nicht", f"Die Überwachung auf dem Server hat seit {d['alter_minuten']} Minuten keinen Status mehr geliefert. "
                      "Bitte in der Hetzner-Konsole prüfen: /opt/markentrix/bin/watchdog.sh --zeigen" + mailer.SIGNATUR)


def betriebs_alarm(cfg):
    """Meldet rote Punkte der Betriebs-Ampel per Push + Glocke (und Mail, wenn eingerichtet): beim Umschlagen auf rot,
    nach 24 Stunden erneut, solange es rot bleibt, und wenn es wieder grün ist."""
    from .routes_system import lesen_status, ampel
    with tx("system") as cur:
        smtp = einstellungen.lesen(cur, "smtp") or {}
        punkte = ampel(lesen_status(), smtp, betrieb.lesen(cur, "jobs"), betrieb.lesen(cur, "mail"))
        alt = ((betrieb.lesen(cur, "alarm") or {}).get("wert") or {}).get("punkte", {})
    jetzt_s = time.time()
    neu, rot, gruen = {}, [], []
    for p in punkte:
        if p["id"] == "jobs":     # läuft dieser Job nicht, kann er auch nicht melden; das übernimmt der Wächter auf dem Server
            continue
        vorher = alt.get(p["id"]) or {}
        if p["status"] == "bad":
            if vorher.get("status") != "bad" or jetzt_s - float(vorher.get("gemeldet", 0)) > 86400:
                rot.append(p)
                neu[p["id"]] = {"status": "bad", "gemeldet": jetzt_s}
            else:
                neu[p["id"]] = vorher
        else:
            if vorher.get("status") == "bad":
                gruen.append(p)
            neu[p["id"]] = {"status": p["status"], "gemeldet": 0}
    if neu != alt:
        betrieb.notieren("alarm", {"punkte": neu})
    if not rot and not gruen:
        return
    if rot:
        titel = "Betriebsalarm: " + ", ".join(p["titel"] for p in rot)
        text = " · ".join(f"{p['titel']}: {p['detail']}" for p in rot)
    else:
        titel = "Wieder in Ordnung: " + ", ".join(p["titel"] for p in gruen)
        text = "Die Betriebs-Ampel ist an diesen Punkten wieder grün."
    with tx("system") as cur:
        ids = push.admins(cur)
        an = cfg["alarm_email"]
        if not an:
            cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
            r = cur.fetchone()
            an = r and r["email"]
    push.senden(ids, titel, text, "/admin#uebersicht", "betriebsalarm")
    if an and mailer.konfiguriert():
        try:
            mailer.senden(an, "Markentrix: " + titel, text + mailer.SIGNATUR)
        except Exception:
            log.exception("Alarm-Mail")


def _trend(jetzt_n, davor_n, einheit_ein, einheit_mehr):
    t = f"{jetzt_n} {einheit_ein if jetzt_n == 1 else einheit_mehr}"
    d = jetzt_n - davor_n
    return t + (f" ({d} mehr als davor)" if d > 0 else f" ({-d} weniger als davor)" if d < 0 else " (wie davor)")


def wochenrueckblick(cfg):
    """Montags ab 8 Uhr (Berlin) ein Satz zur letzten Woche als Push: für Kunden, Vertriebler und Admins. Nur Zahlen, keine Namen."""
    from zoneinfo import ZoneInfo
    lokal = datetime.now(ZoneInfo("Europe/Berlin"))
    if lokal.weekday() != 0 or lokal.hour < 8 or not _marker("wochenrueckblick-%d-%02d" % lokal.isocalendar()[:2]):
        return
    with tx("system") as cur:
        cur.execute("""SELECT k.id, count(a.*) FILTER (WHERE a.erstellt_am >= now() - interval '7 days') AS a1, count(a.*) FILTER (WHERE a.erstellt_am < now() - interval '7 days') AS a0
                       FROM kunden k LEFT JOIN anfragen a ON a.kunden_id = k.id AND a.erstellt_am >= now() - interval '14 days'
                       WHERE k.status = 'aktiv' GROUP BY k.id""")
        anf = {r["id"]: (r["a1"], r["a0"]) for r in cur.fetchall()}
        cur.execute("""SELECT kunden_id, count(*) FILTER (WHERE beginn >= now() - interval '7 days') AS t1
                       FROM termine WHERE beginn >= now() - interval '7 days' AND beginn <= now() AND status <> 'abgesagt' GROUP BY kunden_id""")
        ter = {r["kunden_id"]: r["t1"] for r in cur.fetchall()}
        for kid, (a1, a0) in anf.items():
            if not (a1 or a0):
                continue
            ids = push.kunde(cur, kid)
            if ids:
                t = ter.get(kid, 0)
                push.senden(ids, "Dein Rückblick auf die letzte Woche", "Letzte Woche: " + _trend(a1, a0, "Anfrage", "Anfragen") + (f", {t} Termin" + ("e" if t != 1 else "") if t else "") + ".", "/app#auswertung", "wochenrueckblick")
        cur.execute("""SELECT (SELECT count(*) FROM kunden WHERE erstellt_am >= now() - interval '7 days') AS kunden,
                              (SELECT count(*) FROM leads WHERE erstellt_am >= now() - interval '7 days') AS leads,
                              (SELECT count(*) FROM leads WHERE erstellt_am >= now() - interval '14 days' AND erstellt_am < now() - interval '7 days') AS leads0,
                              (SELECT count(*) FROM anfragen WHERE erstellt_am >= now() - interval '7 days') AS anfragen""")
        z = cur.fetchone()
        push.senden(push.admins(cur), "Wochenrückblick", f"Letzte Woche: {z['kunden']} neue Kunden, {_trend(z['leads'], z['leads0'], 'neuer Lead', 'neue Leads')}, {z['anfragen']} Kundenanfragen insgesamt.", "/admin#uebersicht", "wochenrueckblick")
        cur.execute("""SELECT p.id, count(DISTINCT l.id) FILTER (WHERE l.erstellt_am >= now() - interval '7 days') AS neu,
                              count(ak.*) FILTER (WHERE ak.art IN ('anruf','antwort','termin') AND ak.zeit >= now() - interval '7 days') AS kontakte
                       FROM vertriebspartner p LEFT JOIN leads l ON l.vertriebspartner_id = p.id LEFT JOIN lead_aktivitaeten ak ON ak.lead_id = l.id
                       WHERE p.status = 'aktiv' GROUP BY p.id""")
        for r in cur.fetchall():
            ids = push.partner(cur, r["id"])
            if ids and (r["neu"] or r["kontakte"]):
                push.senden(ids, "Dein Rückblick auf die letzte Woche", f"Letzte Woche: {r['kontakte']} Kontakte festgehalten, {r['neu']} neue Leads zugewiesen.", "/vertrieb#uebersicht", "wochenrueckblick")


def _marker(schluessel: str) -> bool:
    """True genau einmal je Schlüssel (verhindert Mehrfachläufe nach Neustart)."""
    with tx("system") as cur:
        cur.execute("INSERT INTO job_marker (schluessel) VALUES (%s) ON CONFLICT DO NOTHING", (schluessel,))
        return cur.rowcount == 1


def mahnungen_automatisch(cfg):
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 8 or jetzt.weekday() >= 5:
        return
    from .routes_zahlung import mahnlauf, mahn_cfg
    with tx("system") as cur:
        if not mahn_cfg(cur)["aktiv"]:
            return
    if _marker(f"mahnlauf-{jetzt.date()}"):
        mahnlauf(cfg)


def fruehwarnung_woche(cfg):
    jetzt = datetime.now(timezone.utc)
    if jetzt.weekday() != 0 or jetzt.hour < 6:
        return
    if not _marker("fruehwarnung-%d-%02d" % jetzt.isocalendar()[:2]):
        return
    from .routes_fruehwarnung import berechnen
    with tx("system") as cur:
        d = berechnen(cur)
        an = admin_empfaenger(cur)
        ids = push.admins(cur)
    if not d["kunden"]:
        return
    zeilen = [f"- {k['firma']} ({'hoch' if k['stufe'] == 'hoch' else 'mittel'}): " + " ".join(k["gruende"]) for k in d["kunden"][:15]]
    if an:
        mailer.senden(an, f"Kunden-Frühwarnung: {len(d['kunden'])} Kunde(n) mit Risiko",
                      "Diese Kunden sollten Sie diese Woche anrufen:\n\n" + "\n".join(zeilen) + "\n\nDetails im Portal auf der Übersicht." + mailer.SIGNATUR)
    if d["hoch"]:
        push.senden(ids, "Kunden-Frühwarnung", f"{d['hoch']} Kunde(n) mit hohem Kündigungsrisiko.", "/admin#uebersicht", "fruehwarnung")


def geschaeftszahlen_mail(cfg):
    """Am Monatsanfang eine kurze Mail mit den Zahlen des Vormonats."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.day > 5 or jetzt.hour < 7 or not _marker("cockpit-%d-%02d" % (jetzt.year, jetzt.month)):
        return
    from .routes_dashboard import cockpit_daten
    with tx("system") as cur:
        d = cockpit_daten(cur)
        an = admin_empfaenger(cur)
    if not an or len(d["reihe"]) < 2:
        return
    v = d["reihe"][-2]
    eur = lambda c: f"{c / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    mailer.senden(an, f"Geschäftszahlen {v['monat']}", f"Zahlen für {v['monat']}:\n\n- Zahlungseingang (brutto): {eur(v['umsatz_cent'])}\n- Neukunden: {v['neukunden']}\n- Kündigungen: {v['kuendigungen']}\n- Neue Leads: {v['leads']}\n\n"
                  f"Aktuell: {d['aktiv']} aktive Kunden, wiederkehrender Umsatz {eur(d['mrr_cent'])} im Monat, offene Rechnungen {eur(d['offen_cent'])} (davon überfällig {eur(d['ueberfaellig_cent'])}), Kündigungsquote 90 Tage {str(d['churn_prozent']).replace('.', ',')} %." + mailer.SIGNATUR)


def vertrieb_morgens(cfg):
    """Täglich werktags: Push an Vertriebler mit der Zahl der heute fälligen Anrufe."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 6 or jetzt.weekday() >= 5 or not _marker(f"vertrieb-morgens-{jetzt.date()}"):
        return
    with tx("system") as cur:
        cur.execute("""SELECT l.vertriebspartner_id AS pid, count(*) AS n FROM leads l
                       WHERE l.vertriebspartner_id IS NOT NULL AND l.status NOT IN ('verloren','gewonnen','gesperrt','tot','consent_ausstehend')
                         AND (l.wiedervorlage_am <= current_date OR (l.status='neu' AND l.temperatur='heiss' AND l.letzter_kontakt_am IS NULL))
                       GROUP BY 1""")
        liste = cur.fetchall()
        ziele = [(push.partner(cur, r["pid"]), r["n"]) for r in liste]
    for ids, n in ziele:
        push.senden(ids, "Heute anrufen", f"{n} Lead(s) warten auf Ihren Anruf.", "/vertrieb#heute", "heute")


def anrufe_bereinigen() -> int:
    with tx("system") as cur:
        cur.execute("UPDATE anrufe SET nummer=NULL, name=NULL, zusammenfassung=NULL WHERE beginn < now() - interval '180 days' AND (nummer IS NOT NULL OR name IS NOT NULL OR zusammenfassung IS NOT NULL)")
        n = cur.rowcount
        cur.execute("DELETE FROM job_marker WHERE am < now() - interval '60 days'")
        cur.execute("DELETE FROM benachrichtigungen WHERE erstellt_am < now() - interval '60 days'")
    return n


def fristen_loeschen(cfg):
    """Täglich: setzt die Löschfristen um (Leads mit abgelaufener Frist, tote Leads, alte Chatverläufe, Lead-Finder-Rohdaten, Akquise-Antworten). Jede Löschung steht im Löschprotokoll."""
    if datetime.now(timezone.utc).hour < 2 or not _marker(f"fristen-{date.today()}"):
        return
    fristen_ausfuehren()


def fristen_ausfuehren() -> dict:
    ergebnis = {}
    with tx("system") as cur:
        cur.execute("SELECT id, tabelle, aufbewahrung_tage FROM loeschregeln WHERE aktiv")
        regeln = {r["tabelle"]: r for r in cur.fetchall()}

        def protokoll(tabelle, n, regel=None):
            ergebnis[tabelle] = ergebnis.get(tabelle, 0) + n
            if n:
                cur.execute("INSERT INTO loeschprotokoll (tabelle, regel_id, geloescht_anzahl, ausgeloest_durch) VALUES (%s,%s,%s,'automatik')", (tabelle, regel["id"] if regel else None, n))

        def leads_loeschen(bedingung, params, name, regel=None):
            cur.execute(f"SELECT id FROM leads WHERE kunden_id IS NULL AND status NOT IN ('termin','angebot','gewonnen') AND {bedingung} LIMIT 2000", params)
            n = 0
            for r in cur.fetchall():
                try:
                    with cur.connection.transaction():  # Sicherungspunkt: ein nicht löschbarer Lead (z. B. verkauft) stoppt nicht den Rest
                        cur.execute("DELETE FROM leads WHERE id=%s", (r["id"],))
                    n += 1
                except Exception:  # noqa: BLE001
                    continue
            protokoll(name, n, regel)

        leads_loeschen("loeschen_nach IS NOT NULL AND loeschen_nach < current_date", (), "leads (Löschfrist abgelaufen)", regeln.get("leads"))
        if "leads" in regeln:
            leads_loeschen("status IN ('verloren','tot') AND geaendert_am < now() - make_interval(days => %s)", (regeln["leads"]["aufbewahrung_tage"],), "leads (verloren/tot)", regeln["leads"])
        if "chat_verlauf" in regeln:
            cur.execute("DELETE FROM chat_verlauf WHERE erstellt_am < now() - make_interval(days => %s)", (regeln["chat_verlauf"]["aufbewahrung_tage"],)); protokoll("chat_verlauf", cur.rowcount, regeln["chat_verlauf"])
        if "lf_betriebe" in regeln:
            cur.execute("DELETE FROM lf_betriebe WHERE lead_id IS NULL AND erstellt_am < now() - make_interval(days => %s)", (regeln["lf_betriebe"]["aufbewahrung_tage"],)); protokoll("lf_betriebe", cur.rowcount, regeln["lf_betriebe"])
        if "akquise_antworten" in regeln:
            cur.execute("DELETE FROM akquise_antworten WHERE erstellt_am < now() - make_interval(days => %s)", (regeln["akquise_antworten"]["aufbewahrung_tage"],)); protokoll("akquise_antworten", cur.rowcount, regeln["akquise_antworten"])
        if "audit_log" in regeln:   # nur über die Datenbankfunktion: löscht ausschließlich Einträge älter als 12 Monate
            cur.execute("SELECT audit_aufraeumen() AS n"); protokoll("audit_log", cur.fetchone()["n"], regeln["audit_log"])
        from .routes_nutzung import aufraeumen
        protokoll("nutzung (Seitenzähler)", aufraeumen(cur))
    return ergebnis


def anrufe_aufraeumen(cfg):
    """Personenbezogene Angaben aus Telefonprotokollen nach 180 Tagen entfernen (Datensparsamkeit)."""
    if datetime.now(timezone.utc).hour < 2 or not _marker(f"anrufe-aufraeumen-{date.today()}"):
        return
    anrufe_bereinigen()


def website_erinnerungen(cfg):
    webbetrieb.erinnerungen(cfg)


def website_wacht(cfg):
    webbetrieb.wacht(cfg)


def tick():
    betrieb.notieren("jobs")   # Herzschlag für die Betriebs-Ampel
    with tx("system") as cur:
        cfg = einstellungen_lesen(cur)
    for job in (vertrieb_morgens, anrufe_aufraeumen, fristen_loeschen, betriebs_alarm, wochenrueckblick, website_wacht):
        try:
            job(cfg)
        except Exception:
            log.exception("Job %s fehlgeschlagen", job.__name__)
            betrieb.notieren("jobs", {"fehler_am": betrieb.jetzt(), "fehler_job": job.__name__})
    if not mailer.konfiguriert():
        return
    for job in (mahnungen_automatisch, fruehwarnung_woche, geschaeftszahlen_mail, anfragen_mails, termin_erinnerungen, website_erinnerungen, monatsberichte, fehler_melden, avv_erinnerung, aufgaben_automatisch, lead_folgemails, kunden_feedback, ueberwachung_stumm):
        try:
            job(cfg)
        except Exception:  # ein kaputter Job darf die anderen nicht stoppen
            log.exception("Job %s fehlgeschlagen", job.__name__)
            betrieb.notieren("jobs", {"fehler_am": betrieb.jetzt(), "fehler_job": job.__name__})


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
