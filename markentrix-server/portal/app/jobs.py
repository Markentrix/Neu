"""Hintergrundaufgaben des Portals (einmal pro Minute): Benachrichtigungen, Terminerinnerungen, Monatsberichte, Fehlermeldungen.
Mehrfachversand wird durch Markieren der Zeilen beim Abholen (FOR UPDATE SKIP LOCKED) verhindert."""
import json
import logging
import threading
import time
from datetime import date, datetime, timedelta, timezone

from . import abo, aufgabendetail, berichte, config, betrieb, domaincheck, preisaenderung, webbetrieb, zustellung, einstellungen, mailer, pdf, push, security
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
            with tx("system") as cur:   # nicht verloren geben: beim nächsten Lauf erneut versuchen (Fenster: 3 Tage)
                cur.execute("UPDATE anfragen SET benachrichtigt=false WHERE id = ANY(%s)", ([x["id"] for x in liste],))


def termin_erinnerungen(cfg):
    if not cfg["termin_erinnerung"]:
        return
    with tx("system") as cur:
        cur.execute("""WITH offen AS (SELECT t.id FROM termine t WHERE NOT t.erinnerung_gesendet AND t.status IN ('geplant','bestaetigt')
                                      AND t.beginn > now() AND t.beginn <= now() + make_interval(hours => %s) LIMIT 100 FOR UPDATE SKIP LOCKED)
                       UPDATE termine t SET erinnerung_gesendet = true FROM offen WHERE t.id = offen.id
                       RETURNING t.id, t.kunden_id, t.titel, t.beginn, t.kontakt_name""", (int(cfg["termin_stunden"]),))
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
            with tx("system") as cur:   # beim nächsten Lauf erneut versuchen (Termin liegt noch in der Zukunft)
                cur.execute("UPDATE termine SET erinnerung_gesendet=false WHERE id = ANY(%s)", ([x["id"] for x in liste],))


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
        cur.execute("SELECT daten FROM berichte WHERE id=%s", (bid,))
        tipp = berichte.empfehlung(cur.fetchone()["daten"])
    an = _empfaenger(k)
    if not mail:
        return {"id": bid, "gesendet": False, "grund": ""}
    if not an:
        return {"id": bid, "gesendet": False, "grund": "Der Kunde hat keine E-Mail-Adresse hinterlegt."}
    ok, fehler = mailer.monatsbericht(an, k["firma"], pdf.monat_name(monat), daten, name, tipp)
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
                         AND NOT EXISTS (SELECT 1 FROM lead_kampagnen k WHERE k.id = l.kampagne_id AND k.folge_aktiv)   -- eigene Nachfass-Mails der Kampagne
                         AND ((l.folge_stufe = 0 AND l.erstellt_am < now() - make_interval(days => %s))
                           OR (l.folge_stufe = 1 AND l.folge_gesendet_am < now() - make_interval(days => %s)))
                       ORDER BY l.erstellt_am LIMIT 20""", (f["tage_1"], max(1, f["tage_2"] - f["tage_1"])))
        faellig = cur.fetchall()
        auftraege = []
        for l in faellig:
            auftraege.append((l, token_fuer(cur, l["id"])))
            cur.execute("UPDATE leads SET folge_stufe=folge_stufe+1, folge_gesendet_am=now() WHERE id=%s", (l["id"],))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'mail_gesendet',%s,'automatisch')", (l["id"], f"Automatische Folgemail {l['folge_stufe'] + 1}"))
    for l, tok in auftraege:
        n = l["folge_stufe"] + 1
        mailer.lead_folge(l["email"], l["ansprechpartner"], l["firma"], f["betreff_%d" % n], f["text_%d" % n], tok)


def funnel_plaetze_monat(cfg):
    """Plätze pro Monat: am Monatsanfang „frei“ wieder auf „insgesamt“ setzen (nur Kampagnen mit Monatszähler)."""
    with tx("system") as cur:
        cur.execute("""UPDATE lead_kampagnen SET plaetze_frei = plaetze_gesamt, plaetze_monat = date_trunc('month', (now() AT TIME ZONE 'Europe/Berlin'))::date
                       WHERE plaetze_monatlich AND plaetze_gesamt IS NOT NULL
                         AND (plaetze_monat IS NULL OR plaetze_monat < date_trunc('month', (now() AT TIME ZONE 'Europe/Berlin'))::date)""")


def funnel_checks_nachholen(cfg):
    """Website-Checks, die nach der Anmeldung nicht fertig wurden (z. B. Neustart), erneut ausführen; nach 3 Versuchen als Fehler markieren."""
    from . import funnelcheck
    with tx("system") as cur:
        cur.execute("""UPDATE lead_checks SET status='fehler' WHERE status='laeuft' AND versuche >= 3 AND erstellt_am < now() - interval '30 minutes' RETURNING lead_id""")
        for r in cur.fetchall():
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz','Website-Check ließ sich nicht durchführen (Seite bitte von Hand ansehen)','automatisch')", (r["lead_id"],))
        cur.execute("SELECT id FROM lead_checks WHERE status='laeuft' AND versuche < 3 AND erstellt_am < now() - interval '5 minutes' ORDER BY erstellt_am LIMIT 1")
        offen = [r["id"] for r in cur.fetchall()]
        # Ergebnis-Mails, deren Versand fehlschlug (z. B. Mailserver kurz weg): bis zu 3 Versuche im Abstand von 15 Minuten, nur am ersten Tag
        cur.execute("""SELECT c.id FROM lead_checks c JOIN lead_kampagnen k ON k.id = c.kampagne_id
                       WHERE c.status='fertig' AND c.mail_gesendet_am IS NULL AND k.check_mail AND c.mail_versuche BETWEEN 1 AND 2
                         AND c.mail_versucht_am < now() - interval '15 minutes' AND c.erstellt_am > now() - interval '1 day' ORDER BY c.erstellt_am LIMIT 5""")
        mails = [r["id"] for r in cur.fetchall()]
    for cid in offen:
        funnelcheck.ausfuehren(cid)
    if mails and mailer.konfiguriert():
        for cid in mails:
            funnelcheck.mail_senden(cid)


def funnel_folgemails(cfg, stunde: int | None = None):
    """Nachfass-Mails je Funnel-Kampagne (z. B. Tag 1, 3, 7) an Leads mit Einwilligung, solange kein Gespräch und keine Antwort da ist.
    Nur zwischen 8 und 19 Uhr, je Lead höchstens eine Mail in 20 Stunden, jede Stufe genau einmal."""
    from zoneinfo import ZoneInfo
    from . import funnelcheck, sperre
    from .routes_folgemails import token_fuer
    if not 8 <= (datetime.now(ZoneInfo("Europe/Berlin")).hour if stunde is None else stunde) < 19:
        return
    auftraege = []
    with tx("system") as cur:
        cur.execute("SELECT id, folge_tage, folge_betreffe, folge_texte FROM lead_kampagnen WHERE folge_aktiv AND cardinality(folge_tage) > 0")
        for k in cur.fetchall():
            for stufe, tag in enumerate(k["folge_tage"], start=1):
                cur.execute("""SELECT l.id, l.firma, l.ansprechpartner, l.email, l.website FROM leads l
                               WHERE l.kampagne_id=%s AND l.email IS NOT NULL AND NOT l.abgemeldet AND l.kunden_id IS NULL AND l.status IN ('neu','kontaktiert')
                                 AND EXISTS (SELECT 1 FROM lead_aktivitaeten a WHERE a.lead_id = l.id AND a.art = 'consent')
                                 AND NOT EXISTS (SELECT 1 FROM lead_aktivitaeten a WHERE a.lead_id = l.id AND a.art IN ('antwort','termin'))
                                 AND coalesce(l.kampagne_seit, l.erstellt_am) < now() - make_interval(days => %s) AND coalesce(l.kampagne_seit, l.erstellt_am) > now() - interval '90 days'
                                 AND (SELECT count(*) FROM lead_funnel_folge f WHERE f.lead_id = l.id) = %s
                                 AND NOT EXISTS (SELECT 1 FROM lead_funnel_folge f WHERE f.lead_id = l.id AND f.gesendet_am > now() - interval '20 hours')
                               ORDER BY l.erstellt_am LIMIT 20""", (k["id"], tag, stufe - 1))
                for l in cur.fetchall():
                    cur.execute("INSERT INTO lead_funnel_folge (lead_id, stufe) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING lead_id", (l["id"], stufe))
                    if not cur.fetchone():
                        continue
                    cur.execute("SELECT ergebnis FROM lead_checks WHERE lead_id=%s AND status='fertig' ORDER BY erstellt_am DESC LIMIT 1", (l["id"],))
                    c = cur.fetchone()
                    werte = funnelcheck.platzhalter(l, c and c["ergebnis"] if c and (c["ergebnis"] or {}).get("punkte") else None)
                    if sperre.treffer(cur, email=l["email"]):
                        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'automatisch')", (l["id"], f"Nachfass-Mail {stufe} nicht verschickt: Adresse steht auf der Sperrliste"))
                        continue
                    cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'mail_gesendet',%s,'automatisch')", (l["id"], f"Nachfass-Mail {stufe} der Kampagne"))
                    auftraege.append((l["id"], stufe, l["email"], funnelcheck.fuellen(k["folge_betreffe"][stufe - 1], werte), funnelcheck.fuellen(k["folge_texte"][stufe - 1], werte), token_fuer(cur, l["id"])))
    for lid, stufe, an, betreff, text, tok in auftraege:
        ok, grund = mailer.funnel_mail(an, betreff, text, tok)
        if not ok:
            with tx("system") as cur:
                cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'automatisch')", (lid, f"Nachfass-Mail {stufe} nicht zugestellt: {grund[:200]}"))


def umfragen_anlegen(cfg):
    """Täglich: legt Zufriedenheitsumfragen an (30 Tage nach Start, danach alle 90 Tage). Beantwortet wird im Portal; eine Mail gibt es nur mit Einwilligung."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 7 or not _marker("umfragen-" + jetzt.strftime("%Y-%m-%d")):
        return
    umfragen_erzeugen()


def umfragen_erzeugen():
    from .routes_umfrage import einwilligung
    with tx("system") as cur:
        cur.execute("UPDATE kunden_umfragen SET verfallen = true WHERE beantwortet_am IS NULL AND NOT verfallen AND angelegt_am < now() - interval '30 days'")
        cur.execute("""INSERT INTO kunden_umfragen (kunden_id, art)
                       SELECT k.id, CASE WHEN NOT EXISTS (SELECT 1 FROM kunden_umfragen u WHERE u.kunden_id = k.id) THEN 'start' ELSE 'quartal' END FROM kunden k
                       WHERE k.status = 'aktiv' AND k.erstellt_am < now() - interval '30 days'
                         AND NOT EXISTS (SELECT 1 FROM kunden_umfragen u WHERE u.kunden_id = k.id AND u.angelegt_am > now() - interval '90 days')
                       LIMIT 50 RETURNING id, kunden_id""")
        neu = cur.fetchall()
        ziele = []
        for u in neu:
            if einwilligung(cur, u["kunden_id"]):
                cur.execute("SELECT ansprechpartner, email FROM kunden WHERE id=%s", (u["kunden_id"],))
                k = cur.fetchone()
                ziele.append((u["id"], k["email"], k["ansprechpartner"]))
    for uid, an, name in ziele:
        try:
            if (an or "").strip():
                mailer.umfrage_einladung(an.strip(), name)
                with tx("system") as cur:
                    cur.execute("UPDATE kunden_umfragen SET mail_gesendet_am = now() WHERE id=%s", (uid,))
        except Exception:  # noqa: BLE001
            log.exception("Umfrage-Mail %s", uid)


def kunden_feedback(cfg):
    """Eine Feedback-Mail 30 Tage nach Start, wenn in den Einstellungen eingeschaltet."""
    from .routes_folgemails import lesen as folge_lesen
    with tx("system") as cur:
        if not folge_lesen(cur)["kunden_feedback"]:
            return
        cur.execute("""UPDATE kunden k SET feedback_mail_am = now() WHERE k.id IN
                         (SELECT id FROM kunden WHERE status = 'aktiv' AND feedback_mail_am IS NULL AND erstellt_am < now() - interval '30 days'
                            AND (SELECT erteilt FROM kunden_einwilligungen e WHERE e.kunden_id = kunden.id AND e.art = 'umfrage_mail' ORDER BY zeit DESC LIMIT 1) LIMIT 20)
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


def provisionsvorschau(cfg):
    """Ab dem 2. des Monats: Vorschau der Provisionen des Vormonats ausrechnen und dem Admin melden (gebucht wird erst nach dem Klick im Portal)."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.day < 2 or jetzt.hour < 7:
        return
    vormonat = (jetzt.replace(day=1) - timedelta(days=1)).replace(day=1)
    if not _marker("provvorschau-" + vormonat.strftime("%Y-%m")):
        return
    from .routes_verwaltung import BERECHNUNG
    with tx("system") as cur:
        cur.execute("SELECT count(*) AS n FROM provisionsregeln WHERE art='laufend' AND status='freigegeben'")
        if cur.fetchone()["n"] == 0:
            return
        cur.execute("SELECT count(*) AS n FROM provisionen WHERE monat=%s", (vormonat.date(),))
        if cur.fetchone()["n"]:
            return
        cur.execute("SELECT wert FROM konfiguration WHERE schluessel='provision.nachlauf_monate' ORDER BY version DESC LIMIT 1")
        nl = cur.fetchone()
        try:
            nachlauf = int(str(nl["wert"]).strip('"')) if nl else 6
        except ValueError:
            nachlauf = 6
        cur.execute(BERECHNUNG, {"m": vormonat.date().isoformat(), "nachlauf": nachlauf})
        zeilen = cur.fetchall()
        an = admin_empfaenger(cur)
        ids = push.admins(cur)
    if not zeilen or not an:
        return
    summe = sum(int(z["betrag_cent"]) for z in zeilen) / 100
    text = f"Für {vormonat:%m/%Y} ergeben sich {len(zeilen)} Provisionspositionen mit zusammen {summe:,.2f} €.".replace(",", "X").replace(".", ",").replace("X", ".")
    mailer.senden(an, f"Provisionen {vormonat:%m/%Y}: Vorschau liegt bereit", text + f"\n\nBitte prüfen und im Portal unter Vertrieb → Provisionen berechnen:\n{config.BASE_URL}/admin#vertrieb" + mailer.SIGNATUR)
    push.senden(ids, "Provisions-Vorschau", text, "/admin#vertrieb", "provision")


def gespraech_erinnerungen(cfg):
    """Jede Minute: Interessenten 24 Stunden und 2 Stunden vor dem Erstgespräch erinnern; 2 Stunden vorher bekommt auch der Zuständige einen Hinweis."""
    from .routes_buchung import TZ, lesen as buchung_lesen
    with tx("system") as cur:
        ort = buchung_lesen(cur)["ort"]
        cur.execute("""WITH f AS (SELECT id, 24 AS std FROM gespraechstermine WHERE status='gebucht' AND NOT erinnert_24 AND start > now() + interval '3 hours' AND start <= now() + interval '25 hours'
                                  UNION ALL SELECT id, 2 FROM gespraechstermine WHERE status='gebucht' AND NOT erinnert_2 AND start > now() AND start <= now() + interval '3 hours')
                       SELECT g.id, g.name, g.email, g.start, g.token, g.lead_id, f.std, l.vertriebspartner_id FROM f JOIN gespraechstermine g ON g.id = f.id LEFT JOIN leads l ON l.id = g.lead_id LIMIT 40""")
        faellig = cur.fetchall()
        for g in faellig:   # zuerst markieren; bei Mailfehler unten zurücksetzen
            cur.execute("UPDATE gespraechstermine SET erinnert_24=true WHERE id=%s" if g["std"] == 24 else "UPDATE gespraechstermine SET erinnert_2=true, erinnert_24=true WHERE id=%s", (g["id"],))
        team = {g["id"]: (push.admins(cur) + (push.partner(cur, g["vertriebspartner_id"]) if g["vertriebspartner_id"] else [])) for g in faellig if g["std"] == 2}
    for g in faellig:
        lokal = g["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
        ok, fehler = mailer.gespraech_erinnerung(g["email"], g["name"], lokal, f"{config.BASE_URL}/api/public/buchung/absagen?t={g['token']}", ort, g["std"])
        if not ok:
            log.warning("Gesprächserinnerung an %s fehlgeschlagen: %s", g["email"], fehler)
            with tx("system") as cur:
                cur.execute("UPDATE gespraechstermine SET erinnert_24=false, erinnert_2=false WHERE id=%s" if g["std"] == 2 else "UPDATE gespraechstermine SET erinnert_24=false WHERE id=%s", (g["id"],))
        if g["std"] == 2 and team.get(g["id"]):
            push.senden(team[g["id"]], "Gespräch in 2 Stunden", f"{g['name']} um {g['start'].astimezone(TZ):%H:%M} Uhr.", "/vertrieb#heute", "buchung")


def anfragen_eskalation(cfg):
    """Jede Minute: heiße Anfragen von der Website, die nach der Reaktionszeit noch niemand bearbeitet hat, einmal an Team und Zuständigen melden."""
    from . import zuweisung
    with tx("system") as cur:
        stunden = zuweisung.einstellung(cur)["reaktionsstunden"]
        cur.execute("""SELECT id, firma, vertriebspartner_id FROM leads WHERE quelle='website' AND temperatur='heiss' AND letzter_kontakt_am IS NULL AND kunden_id IS NULL
                         AND status IN ('neu','antwort') AND erstellt_am < now() - make_interval(hours => %s) AND erstellt_am > now() - interval '7 days' LIMIT 20""", (stunden,))
        offen = cur.fetchall()
    for l in offen:
        if not _marker("eskalation-" + str(l["id"])):
            continue
        with tx("system") as cur:
            ids = push.admins(cur) + (push.partner(cur, l["vertriebspartner_id"]) if l["vertriebspartner_id"] else [])
        push.senden(ids, "Anfrage wartet seit über %d Std." % stunden, f"{l['firma']}: bitte jetzt melden.", "/admin#lead/" + str(l["id"]), "check")


def veroeffentlichung_wacht(cfg):
    """Jede Minute: meldet dem Team, wenn eine Veröffentlichung fehlgeschlagen ist oder Aufträge liegen bleiben (Worker steht)."""
    q = config.QUEUE_DIR
    if not q.is_dir():
        return
    meldungen = []
    for f in q.glob("ergebnis-*.json"):
        try:
            if time.time() - f.stat().st_mtime > 86400 * 2:
                continue
            e = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        if e.get("ok") is False and e.get("aktion") in ("veroeffentlichen", "zurueck", "sicherung") and _marker("pubfehler-" + f.name):
            meldungen.append(f"Veröffentlichung fehlgeschlagen: {e.get('name') or '?'} – {str(e.get('text') or '')[:200]}")
    for f in q.glob("auftrag-*.json"):
        try:
            alt = time.time() - f.stat().st_mtime
        except OSError:
            continue
        if alt > 900 and _marker("pubstau-" + f.name):
            meldungen.append("Ein Auftrag für den Server wartet seit über 15 Minuten (läuft der Worker? Cron „bin/worker.py“ prüfen).")
    if not meldungen:
        return
    with tx("system") as cur:
        for m in meldungen:
            cur.execute("INSERT INTO alarme (stufe, quelle, titel, details) VALUES ('kritisch','veroeffentlichung',%s,'{}'::jsonb)", (m[:200],))
        ids = push.admins(cur)
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        r = cur.fetchone()
        an = cfg.get("alarm_email") or (r and r["email"])
    push.senden(ids, "Veröffentlichung: Problem", meldungen[0], "/admin#websites", "betriebsalarm")
    if an and mailer.konfiguriert():
        mailer.senden(an, "Markentrix: Problem bei der Veröffentlichung", "\n".join(meldungen) + mailer.SIGNATUR)


def website_online_meldungen(cfg):
    """Jede Minute: sagt dem Kunden Bescheid, sobald seine neue Website online ist oder ein Update eingespielt wurde. Wartet, bis die Seite wirklich erreichbar ist."""
    with tx("system") as cur:
        cur.execute("""SELECT m.id, m.kunden_id, m.domain, m.upload_id, m.hinweis, m.erstellt_am < now() - interval '2 hours' AS zu_alt_ohne_ergebnis,
                              m.erstellt_am < now() - interval '14 days' AS verfallen, k.ansprechpartner,
                              EXISTS (SELECT 1 FROM website_wacht w WHERE w.domain = m.domain AND w.seite_ok AND w.geprueft_am > now() - interval '30 minutes') AS erreichbar,
                              m.erstellt_am < now() - interval '6 hours' AS lange_wartend
                       FROM website_meldungen m JOIN kunden k ON k.id = m.kunden_id
                       WHERE m.status = 'offen' ORDER BY m.erstellt_am LIMIT 20""")
        offen = cur.fetchall()
    for r in offen:
        try:
            p = config.QUEUE_DIR / f"ergebnis-{r['upload_id']}.json"
            if not p.is_file():
                if r["zu_alt_ohne_ergebnis"]:
                    _meldung_setzen(r["id"], "verworfen")
                continue
            e = json.loads(p.read_text())
            if not e.get("ok"):
                _meldung_setzen(r["id"], "verworfen")
                continue
            neu = bool(e.get("neu"))
            # Es zählt, dass die Startseite antwortet; die Website-API (/api/health) ist dafür nicht nötig.
            # Ein Update einer Seite, die schon online war, wird nach 6 Stunden auch ohne Check gemeldet, damit die Meldung nie ewig hängt.
            if not r["erreichbar"] and not (not neu and r["lange_wartend"]):
                if r["verfallen"]:
                    _meldung_setzen(r["id"], "verworfen")
                elif r["zu_alt_ohne_ergebnis"]:
                    log.warning("Website-Meldung %s wartet seit über 2 Stunden: Startseite von %s antwortet nicht", r["id"], r["domain"])
                continue
            with tx("system") as cur:
                an = kunden_empfaenger(cur, r["kunden_id"])
                ids = push.kunde(cur, r["kunden_id"])
            for a in an:
                (mailer.website_online if neu else mailer.website_aktualisiert)(a, r["ansprechpartner"], r["domain"], r["hinweis"], r["kunden_id"])
            push.senden(ids, "Ihre Website ist online" if neu else "Ihre Website ist aktualisiert", r["domain"], "/app#website", "websiteonline")
            _meldung_setzen(r["id"], "gesendet")
        except Exception:  # noqa: BLE001
            log.exception("Website-Meldung %s", r["id"])


def _meldung_setzen(mid, status):
    with tx("system") as cur:
        cur.execute("UPDATE website_meldungen SET status=%s, gesendet_am=CASE WHEN %s='gesendet' THEN now() END WHERE id=%s", (status, status, mid))


def avv_kunde_erinnerung(cfg):
    """Werktags: Kunden, denen der AVV im Portal bereitliegt und die nach 3 Tagen noch nicht bestätigt haben, höflich erinnern (höchstens zweimal, alle 3 Tage)."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 8 or jetzt.weekday() >= 5 or not _marker("avvkunde-" + jetzt.strftime("%Y-%m-%d")):
        return
    avv_kunde_erinnern()


def avv_kunde_erinnern():
    with tx("system") as cur:
        cur.execute("""SELECT a.id, k.email, k.ansprechpartner FROM avv a JOIN kunden k ON k.id = a.kunden_id
                       WHERE a.datei IS NULL AND a.portal_freigabe_am IS NOT NULL AND a.erinnerungen < 2 AND k.status IN ('onboarding','aktiv','pausiert')
                         AND COALESCE(a.erinnert_am, a.portal_freigabe_am) < now() - interval '3 days' LIMIT 20""")
        todo = cur.fetchall()
    for r in todo:
        try:
            if (r["email"] or "").strip():
                mailer.avv_erinnerung_kunde(r["email"].strip(), r["ansprechpartner"])
            with tx("system") as cur:
                cur.execute("UPDATE avv SET erinnert_am=now(), erinnerungen=erinnerungen+1 WHERE id=%s", (r["id"],))
        except Exception:  # noqa: BLE001
            log.exception("AVV-Erinnerung %s", r["id"])


def vertrag_erinnerung(cfg):
    """Werktags: Verträge, die vor 7 Tagen verschickt und noch nicht bestätigt wurden, einmal nach 7 und einmal nach 14 Tagen erinnern. Das Team bekommt eine Sammelmail."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 8 or jetzt.weekday() >= 5 or not _marker("vertragerinnerung-" + jetzt.strftime("%Y-%m-%d")):
        return
    vertrag_erinnern(cfg)


def vertrag_erinnern(cfg=None):
    with tx("system") as cur:
        cur.execute("""SELECT d.id, d.art, d.gesendet_an, d.erinnerungen, COALESCE(k.firma, p.name) AS wer,
                              COALESCE(NULLIF(d.daten->>'name',''), k.ansprechpartner, p.name) AS anrede
                       FROM vertragsdokumente d LEFT JOIN kunden k ON k.id = d.kunden_id LEFT JOIN vertriebspartner p ON p.id = d.partner_id
                       WHERE d.gesendet_am IS NOT NULL AND d.unterschrieben_am IS NULL AND d.datei IS NULL AND d.widerrufen_am IS NULL AND d.erinnerungen < 2
                         AND COALESCE(d.erinnert_am, d.gesendet_am) < now() - interval '7 days'
                         AND (k.status IN ('onboarding','aktiv','pausiert') OR p.status IN ('anfrage','aktiv','pausiert'))
                       ORDER BY d.gesendet_am LIMIT 20""")
        todo = cur.fetchall()
    erledigt = []
    for r in todo:
        try:
            if (r["gesendet_an"] or "").strip():
                mailer.vertrag_erinnerung(r["gesendet_an"].strip(), r["anrede"], r["art"])
            with tx("system") as cur:
                cur.execute("UPDATE vertragsdokumente SET erinnert_am=now(), erinnerungen=erinnerungen+1 WHERE id=%s", (r["id"],))
            erledigt.append(r)
        except Exception:  # noqa: BLE001
            log.exception("Vertrags-Erinnerung %s", r["id"])
    if erledigt:
        with tx("system") as cur:
            an = (cfg or {}).get("alarm_email")
            if not an:
                cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
                x = cur.fetchone()
                an = x and x["email"]
        if an:
            zeilen = [f"- {r['wer']}: {'Referenzvertrag' if r['art'] == 'referenz' else 'Handelsvertretervertrag'} ({r['erinnerungen'] + 1}. Erinnerung)" for r in erledigt]
            mailer.senden(an, "Verträge noch offen: Erinnerungen verschickt", "Diese Verträge sind noch nicht bestätigt, die Empfänger wurden erinnert:\n\n" + "\n".join(zeilen) +
                          "\n\nÜbersicht im Portal: Admin → Verträge." + mailer.SIGNATUR)


def vertrieb_erinnerung(cfg):
    """Werktags morgens: erinnert jeden aktiven Vertriebler an Leads mit fälliger Wiedervorlage und an Leads, bei denen seit einer Woche nichts passiert ist (Mail und Push)."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 6 or jetzt.weekday() >= 5 or not _marker("vertriebserinnerung-" + jetzt.strftime("%Y-%m-%d")):
        return
    vertrieb_erinnern()


def vertrieb_erinnern():
    from . import push
    with tx("system") as cur:
        cur.execute("SELECT id, name, email FROM vertriebspartner WHERE status='aktiv' AND erinnerung_mail AND email IS NOT NULL AND (erinnerung_am IS NULL OR erinnerung_am < current_date) LIMIT 200")
        partner = cur.fetchall()
    for p in partner:
        try:
            with tx("system") as cur:
                cur.execute("""SELECT firma, ort, wiedervorlage_am, letzter_kontakt_am, status FROM leads
                               WHERE vertriebspartner_id=%s AND status NOT IN ('verloren','gewonnen','gesperrt','tot','consent_ausstehend')
                                 AND (wiedervorlage_am <= current_date OR (status='kontaktiert' AND wiedervorlage_am IS NULL AND letzter_kontakt_am < now() - interval '7 days'))
                               ORDER BY wiedervorlage_am NULLS LAST, letzter_kontakt_am LIMIT 50""", (p["id"],))
                leads = cur.fetchall()
                cur.execute("UPDATE vertriebspartner SET erinnerung_am=current_date WHERE id=%s", (p["id"],))
                cur.execute("SELECT id FROM benutzer WHERE vertriebspartner_id=%s AND aktiv", (p["id"],))
                ids = [r["id"] for r in cur.fetchall()]
            if not leads:
                continue
            mailer.vertrieb_nachfassen((p["email"] or "").strip(), p["name"], leads)
            push.senden(ids, "Heute nachfassen", f"{len(leads)} Leads warten auf dich", "/vertrieb#heute", "nachfassen")
        except Exception:  # noqa: BLE001
            log.exception("Vertriebs-Erinnerung %s", p["id"])


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
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Wir warten seit einer Woche auf den Kunden
        f"""INSERT INTO aufgaben (kunden_id, ticket_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT t.kunden_id, t.id, 'Nachfassen: ' || k.firma || ' – ' || t.betreff, {admin}, current_date, 'auto', 'nachfassen-' || t.id || '-' || to_char(t.geaendert_am, 'YYYYMMDDHH24MISS')
            FROM tickets t JOIN kunden k ON k.id = t.kunden_id
            WHERE t.status = 'wartet_auf_kunde' AND t.geaendert_am < now() - interval '7 days'
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Rechnung überfällig
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT b.kunden_id, 'Rechnung ' || b.nummer || ' überfällig: ' || k.firma, {admin}, current_date, 'auto', 'rechnung-' || b.id
            FROM belege b JOIN kunden k ON k.id = b.kunden_id
            WHERE b.art = 'rechnung' AND b.status IN ('gestellt','versendet') AND b.faellig_am < current_date AND b.nummer IS NOT NULL
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Mindestlaufzeit endet in den nächsten 60 Tagen
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT b.kunden_id, 'Vertrag: Mindestlaufzeit endet am ' || to_char(b.mindestlaufzeit_ende, 'DD.MM.YYYY') || ' – ' || k.firma, {admin}, current_date, 'auto', 'vertrag-' || b.id || '-' || b.mindestlaufzeit_ende
            FROM buchungen b JOIN kunden k ON k.id = b.kunden_id
            WHERE b.status = 'aktiv' AND b.mindestlaufzeit_ende BETWEEN current_date AND current_date + 60 AND k.status = 'aktiv'
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Domain läuft in den nächsten 60 Tagen ab (auch bei automatischer Verlängerung: Zahlungsmittel und Kundenabsprache prüfen)
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT d.kunden_id, 'Domain läuft ab: ' || d.domain || ' am ' || to_char(d.ablauf_am, 'DD.MM.YYYY') || ' – ' || k.firma, {admin}, current_date, 'auto', 'domain-' || d.id || '-' || to_char(d.ablauf_am, 'YYYYMMDD')
            FROM domains d JOIN kunden k ON k.id = d.kunden_id
            WHERE d.status = 'aktiv' AND d.ablauf_am BETWEEN current_date AND current_date + 60 AND k.status IN ('onboarding', 'aktiv', 'pausiert')
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Kunde hängt im Onboarding: seit 5 Tagen angelegt, einmal pro Woche eine Aufgabe zum Nachfassen
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT k.id, 'Onboarding nachfassen: ' || k.firma, {admin}, current_date, 'auto', 'onboarding-' || k.id || '-' || to_char(current_date, 'IYYY-IW')
            FROM kunden k
            WHERE k.status = 'onboarding' AND k.erstellt_am < now() - interval '5 days'
              AND EXISTS (SELECT 1 FROM onboarding_punkte p WHERE p.kunden_id = k.id AND NOT p.erledigt)
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Einladung nie angenommen oder abgelaufen: Zugang neu schicken (einmal pro Woche)
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT k.id, 'Zugang prüfen, Einladung neu senden: ' || k.firma, {admin}, current_date, 'auto', 'einladung-' || k.id || '-' || to_char(current_date, 'IYYY-IW')
            FROM kunden k
            WHERE k.status = 'onboarding' AND k.erstellt_am < now() - interval '3 days'
              AND NOT EXISTS (SELECT 1 FROM benutzer b WHERE b.kunden_id = k.id AND b.aktiv AND b.passwort_hash IS NOT NULL)
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Stillstand: seit 14 Tagen nichts erledigt, der Kunde ist am Zug: anrufen statt noch eine Mail
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT k.id, 'Kunde anrufen (Stillstand im Onboarding): ' || k.firma, {admin}, current_date, 'auto', 'stillstand-' || k.id || '-' || to_char(current_date, 'IYYY-IW')
            FROM kunden k
            WHERE k.status = 'onboarding' AND k.erstellt_am < now() - interval '14 days'
              AND NOT EXISTS (SELECT 1 FROM onboarding_punkte p WHERE p.kunden_id = k.id AND p.erledigt_am > now() - interval '14 days')
              AND EXISTS (SELECT 1 FROM onboarding_punkte p WHERE p.kunden_id = k.id AND NOT p.erledigt AND p.code = ANY(ARRAY['avv','briefing','stammdaten','branding','konten','dns','zugang']))
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Angebot an einen Lead liegt seit 5 Tagen ohne Antwort: nachfassen
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT NULL, 'Angebot nachfassen: ' || coalesce(l.firma, b.nummer), {admin}, current_date, 'auto', 'angebotnachfassen-' || b.id
            FROM belege b JOIN leads l ON l.id = b.lead_id
            WHERE b.art = 'angebot' AND b.status IN ('gestellt', 'versendet') AND b.lead_id IS NOT NULL AND l.kunden_id IS NULL
              AND coalesce(b.versendet_am, b.erstellt_am) < now() - interval '5 days' AND (b.faellig_am IS NULL OR b.faellig_am >= current_date)
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Kunde mit Vertriebler, aber ohne Buchung: es entsteht keine Provision (einmal pro Woche)
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT k.id, 'Keine Buchung, keine Provision: ' || k.firma, {admin}, current_date, 'auto', 'ohnebuchung-' || k.id || '-' || to_char(current_date, 'IYYY-IW')
            FROM kunden k
            WHERE k.vertriebspartner_id IS NOT NULL AND k.status IN ('onboarding', 'aktiv') AND k.referenzkunde = false AND k.erstellt_am < now() - interval '3 days'
              AND NOT EXISTS (SELECT 1 FROM buchungen b WHERE b.kunden_id = k.id AND b.status IN ('beauftragt', 'in_einrichtung', 'aktiv') AND b.beginn IS NOT NULL)
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Gespräch war vor über einer Stunde: Ergebnis im Lead festhalten
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT NULL, 'Gespräch-Ergebnis festhalten: ' || g.name, {admin}, current_date, 'auto', 'gespraechergebnis-' || g.id
            FROM gespraechstermine g JOIN leads l ON l.id = g.lead_id
            WHERE g.status = 'gebucht' AND g.start < now() - interval '1 hour' AND g.start > now() - interval '3 days' AND l.status IN ('termin', 'antwort', 'neu', 'kontaktiert')
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
        # Angebot läuft in 3 Tagen ab
        f"""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
            SELECT NULL, 'Angebot läuft bald ab: ' || coalesce(l.firma, b.nummer) || ' (bis ' || to_char(b.faellig_am, 'DD.MM.') || ')', {admin}, current_date, 'auto', 'angebotablauf-' || b.id
            FROM belege b JOIN leads l ON l.id = b.lead_id
            WHERE b.art = 'angebot' AND b.status IN ('gestellt', 'versendet') AND b.lead_id IS NOT NULL AND l.kunden_id IS NULL
              AND b.faellig_am BETWEEN current_date AND current_date + 3
            ON CONFLICT (auto_schluessel) DO NOTHING RETURNING id, kunden_id, ticket_id, titel""",
    ]
    neu, erinnern, onb = [], [], []
    with tx("system") as cur:
        for sql_text in regeln:
            cur.execute(sql_text)
            gefunden = cur.fetchall()
            for r in gefunden:
                neu.append(aufgabendetail.beschreibe(cur, r))
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
            cur.execute("SELECT code FROM onboarding_punkte WHERE kunden_id = %s AND NOT erledigt AND code IN ('branding','konten','dns')", (k["id"],))
            codes = {r["code"] for r in cur.fetchall()}
            offen += (["Ihr Logo und Fotos hochladen"] if "branding" in codes else []) + (["uns die Zugänge zu Ihren Konten (z. B. Google-Profil) senden"] if "konten" in codes else []) + (["die Domain auf unseren Server umstellen (wir erklären Ihnen im Portal, wie)"] if "dns" in codes else [])
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


_lauf_lokal = threading.local()


def _marker(schluessel: str) -> bool:
    """True genau einmal je Schlüssel (verhindert Mehrfachläufe nach Neustart).
    Stürzt der Job danach ab, gibt _lauf den Schlüssel wieder frei, damit er in der nächsten Minute erneut versucht wird."""
    with tx("system") as cur:
        cur.execute("INSERT INTO job_marker (schluessel) VALUES (%s) ON CONFLICT DO NOTHING", (schluessel,))
        neu = cur.rowcount == 1
    if neu and getattr(_lauf_lokal, "marker", None) is not None:
        _lauf_lokal.marker.append(schluessel)
    return neu


_fehlserie: dict[str, int] = {}


def _lauf(job, cfg) -> None:
    """Führt einen Job aus. Bei einem Absturz werden seine Tagesmarker freigegeben (der Job wird wiederholt),
    der Fehler wird gezählt und erst nach einem erfolgreichen Lauf wieder gelöscht."""
    _lauf_lokal.marker = []
    try:
        job(cfg)
    except Exception:
        log.exception("Job %s fehlgeschlagen", job.__name__)
        marker = _lauf_lokal.marker
        if marker:
            try:
                with tx("system") as cur:
                    cur.execute("DELETE FROM job_marker WHERE schluessel = ANY(%s)", (marker,))
            except Exception:
                log.exception("Marker konnten nicht freigegeben werden")
        n = _fehlserie[job.__name__] = _fehlserie.get(job.__name__, 0) + 1
        import sys
        from . import fehlerhilfe
        fehlerhilfe.melden("job:" + job.__name__, sys.exc_info()[1], titel=f"Hintergrundjob „{job.__name__}“ fehlgeschlagen", sperre_sek=3600)
        betrieb.notieren("jobs", {"fehler_am": betrieb.jetzt(), "fehler_job": job.__name__, "fehler_serie": n})
    else:
        if _fehlserie.pop(job.__name__, None) is not None and not _fehlserie:
            betrieb.notieren("jobs", {"fehler_job": None, "fehler_serie": 0})
    finally:
        _lauf_lokal.marker = None


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


def preisaenderung_anwenden(cfg):
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 4 or not _marker(f"preisaenderung-{jetzt.date()}"):
        return
    preisaenderung.anwenden(cfg)


def zahlungsverzug(cfg):
    """Täglich: Kunden mit einer Rechnung, die lange nach der 2. Mahnung unbezahlt ist, bekommen ihren Wartungsplan (und auf Wunsch Formular/Buchung der Website) pausiert.
    Sobald nichts Überfälliges mehr offen ist, wird alles wieder freigegeben. Der Admin wird jeweils informiert."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 7 or not _marker(f"verzug-{jetzt.date()}"):
        return
    from .routes_zahlung import mahn_cfg
    with tx("system") as cur:
        m = mahn_cfg(cur)
        tage = int(m.get("verzug_tage") or 0)
        if tage <= 0:
            cur.execute("SELECT kunden_id FROM abrechnungsplaene WHERE pausiert_verzug UNION SELECT kunden_id FROM website_dienste WHERE verzug_pause")
            frei = [r["kunden_id"] for r in cur.fetchall()]       # Funktion ausgeschaltet: alles freigeben
            verzug = []
        else:
            cur.execute("""SELECT b.kunden_id, k.firma, min(b.nummer) AS nummer FROM belege b JOIN kunden k ON k.id = b.kunden_id
                           WHERE b.art='rechnung' AND b.status IN ('gestellt','versendet') AND b.storno_von IS NULL AND b.mahnstufe >= 3 AND b.mahn_am <= current_date - %s
                             AND NOT k.referenzkunde AND k.status = 'aktiv' GROUP BY b.kunden_id, k.firma""", (tage,))
            verzug = cur.fetchall()
            cur.execute("""SELECT kunden_id FROM abrechnungsplaene WHERE pausiert_verzug UNION SELECT kunden_id FROM website_dienste WHERE verzug_pause""")
            gesperrt = {r["kunden_id"] for r in cur.fetchall()}
            frei = [k for k in gesperrt if k not in {v["kunden_id"] for v in verzug}]
    for v in verzug:
        with tx("system") as cur:
            cur.execute("UPDATE abrechnungsplaene SET aktiv=false, pausiert_verzug=true WHERE kunden_id=%s AND aktiv", (v["kunden_id"],))
            plaene = cur.rowcount
            dienste = 0
            if m.get("verzug_dienste"):
                cur.execute("UPDATE website_dienste SET verzug_pause=true WHERE kunden_id=%s AND NOT verzug_pause", (v["kunden_id"],))
                dienste = cur.rowcount
            ids = push.admins(cur) if (plaene or dienste) else []
            if plaene or dienste:
                cur.execute("INSERT INTO audit_log (kunden_id, aktion, details) VALUES (%s,'zahlungsverzug_pausiert',%s::jsonb)", (v["kunden_id"], json.dumps({"plaene": plaene, "dienste": bool(dienste), "rechnung": v["nummer"]})))
        if ids:
            push.senden(ids, "Zahlungsverzug", f"{v['firma']}: Rechnung {v['nummer']} unbezahlt. " + ("Wartungsplan pausiert" if plaene else "") + (" · Formular/Buchung der Website pausiert" if dienste else ""), "/admin#kunden", "verzug")
    for kid in frei:
        with tx("system") as cur:
            cur.execute("UPDATE abrechnungsplaene SET aktiv=true, pausiert_verzug=false WHERE kunden_id=%s AND pausiert_verzug", (kid,))
            plaene = cur.rowcount
            cur.execute("UPDATE website_dienste SET verzug_pause=false WHERE kunden_id=%s AND verzug_pause", (kid,))
            dienste = cur.rowcount
            cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
            f = (cur.fetchone() or {}).get("firma", "")
            ids = push.admins(cur) if (plaene or dienste) else []
            if plaene or dienste:
                cur.execute("INSERT INTO audit_log (kunden_id, aktion, details) VALUES (%s,'zahlungsverzug_aufgehoben',%s::jsonb)", (kid, json.dumps({"plaene": plaene, "dienste": bool(dienste)})))
        if ids:
            push.senden(ids, "Zahlungsverzug beendet", f"{f}: nichts Überfälliges mehr offen, Pause aufgehoben.", "/admin#kunden", "verzug")


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
        cur.execute("DELETE FROM alarme WHERE zeit < now() - interval '365 days' OR (bestaetigt_am IS NOT NULL AND zeit < now() - interval '180 days')")
        cur.execute("DELETE FROM workflow_fehler WHERE zeit < now() - interval '180 days'")
        cur.execute("DELETE FROM website_ereignisse WHERE zeit < now() - interval '180 days'")
        cur.execute("DELETE FROM website_stat WHERE tag < current_date - 800")
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

        # Leads im Status Termin/Angebot ohne jede Aktivität seit 12 Monaten: als verloren ablegen (danach greift die normale Löschfrist)
        cur.execute("""UPDATE leads SET status='verloren', wiedervorlage_am=NULL WHERE kunden_id IS NULL AND status IN ('termin','angebot')
                       AND coalesce(letzter_kontakt_am, geaendert_am) < now() - interval '12 months' RETURNING id""")
        for r in cur.fetchall():
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel','Automatisch als verloren abgelegt: seit 12 Monaten keine Aktivität','automatisch')", (r["id"],))
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


def fotos_aufraeumen(cfg):
    """Löscht Fotos aus Anfragen/Terminen nach der Frist des Betriebs und nie verknüpfte Uploads nach 24 Stunden. Jede Löschung steht im Löschprotokoll."""
    from . import fotos
    with tx("system") as cur:
        abgelaufen, verwaist = fotos.aufraeumen(cur)
        for n, name in ((abgelaufen, "website_fotos (Löschfrist abgelaufen)"), (verwaist, "website_fotos (nie abgeschickt)")):
            if n:
                cur.execute("INSERT INTO loeschprotokoll (tabelle, geloescht_anzahl, ausgeloest_durch) VALUES (%s,%s,'automatik')", (name, n))


def anrufe_aufraeumen(cfg):
    """Personenbezogene Angaben aus Telefonprotokollen nach 180 Tagen entfernen (Datensparsamkeit)."""
    if datetime.now(timezone.utc).hour < 2 or not _marker(f"anrufe-aufraeumen-{date.today()}"):
        return
    anrufe_bereinigen()


def website_erinnerungen(cfg):
    webbetrieb.erinnerungen(cfg)


def anzahlung_fristen(cfg):
    webbetrieb.anzahlung_frist(cfg)


def gutschein_erinnerungen(cfg):
    webbetrieb.gutschein_erinnerung(cfg)


def kuendigungen_vollziehen(cfg):
    """Am Vertragsende: Kunde auf „gekündigt“, laufende Buchungen beenden, Team informieren (Übergabe der Domains, Export, Löschung)."""
    with tx("system") as cur:
        cur.execute("""UPDATE kuendigungswuensche q SET vollzogen_am = now() WHERE q.vollzogen_am IS NULL AND q.status IN ('offen','bearbeitet') AND q.ende_am <= current_date
                       RETURNING q.kunden_id, q.ende_am""")
        fertig = cur.fetchall()
        namen = []
        for r in fertig:
            cur.execute("UPDATE kunden SET status='gekuendigt' WHERE id=%s AND status NOT IN ('gekuendigt','beendet') RETURNING firma, kundennummer", (r["kunden_id"],))
            k = cur.fetchone()
            cur.execute("UPDATE buchungen SET status='gekuendigt', ende=%s WHERE kunden_id=%s AND status IN ('beauftragt','in_einrichtung','aktiv','pausiert')", (r["ende_am"], r["kunden_id"]))
            if k:
                namen.append(f"{k['firma']} ({k['kundennummer']})")
        ids = push.admins(cur) if namen else []
    if ids:
        push.senden(ids, "Vertragsende", "Gekündigt zum Ende: " + ", ".join(namen), "/admin#kunden", "vertragsende")


def zustellung_pruefen(cfg):
    """Einmal täglich: SPF, DKIM und DMARC der Absender-Domains prüfen und melden, wenn die Absenderdomain von Markentrix Probleme hat."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 5 or not _marker("zustellung-" + jetzt.strftime("%Y-%m-%d")):
        return
    with tx("system") as cur:
        smtp = einstellungen.lesen(cur, "smtp") or {}
        cur.execute("SELECT DISTINCT smtp_absender FROM website_dienste WHERE smtp_absender IS NOT NULL AND smtp_enc IS NOT NULL")
        domains = {(r["smtp_absender"].rsplit("@", 1)[-1]).lower() for r in cur.fetchall() if "@" in r["smtp_absender"]}
        cur.execute("DELETE FROM mail_protokoll WHERE zeit < now() - interval '90 days'")
    sys_domain = (smtp.get("absender") or "").rsplit("@", 1)[-1].lower()
    if sys_domain:
        domains.add(sys_domain)
    ergebnisse = {d: zustellung.pruefen_domain(d) for d in sorted(domains)[:200] if d}
    with tx("system") as cur:
        for r in ergebnisse.values():
            zustellung.speichern(cur, r)
        ids = push.admins(cur)
    r = ergebnisse.get(sys_domain)
    if r and zustellung.schlecht(r) and ids:
        probleme = ", ".join(f"{n.upper()}: {r[n]}" for n in ("spf", "dkim") if r[n] in ("fehlt", "warn"))
        push.senden(ids, "Mail-Zustellbarkeit", f"{sys_domain}: {probleme}. Mails können im Spam landen.", "/admin#einstellungen", "zustellung")


def domain_pruefen(cfg):
    """Alle 10 Minuten: Live-Domains, die noch nicht richtig auf den Server zeigen, erneut prüfen; Admin benachrichtigen, sobald sie live sind."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.minute % 10 != 0 or not _marker("domaincheck-" + jetzt.strftime("%Y-%m-%d-%H-%M")):
        return
    domain_lauf()


def domain_lauf():
    with tx("system") as cur:
        v4, v6 = domaincheck.server_adressen(cur)
        if not v4:
            return
        cur.execute("""SELECT w.domain, w.kunden_id, k.firma, p.ok, p.live_gemeldet, p.geprueft_am FROM websites w JOIN kunden k ON k.id = w.kunden_id
                       LEFT JOIN domain_pruefung p ON p.domain = w.domain
                       WHERE w.art = 'live' AND (p.domain IS NULL OR p.ok IS NOT TRUE OR p.live_gemeldet IS NOT TRUE OR p.geprueft_am < now() - interval '1 day') LIMIT 30""")
        todo = cur.fetchall()
    for t in todo:
        r = domaincheck.pruefen(t["domain"], v4, v6)
        domaincheck.verbuchen(t["domain"], t["kunden_id"], t["firma"], t["live_gemeldet"], r)


def domain_erinnerung(cfg):
    """Täglich: Kunden, denen die DNS-Anleitung geschickt wurde und deren Domain nach 3 Tagen noch nicht stimmt, höflich erinnern (höchstens zweimal)."""
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 8 or jetzt.weekday() >= 5 or not _marker("domainerinnerung-" + jetzt.strftime("%Y-%m-%d")):
        return
    domain_erinnern()


def domain_erinnern():
    with tx("system") as cur:
        cur.execute("""SELECT domain FROM domain_pruefung WHERE ok IS NOT TRUE AND kundenmail_am IS NOT NULL AND erinnerungen < 2
                       AND COALESCE(erinnert_am, kundenmail_am) < now() - interval '3 days' LIMIT 20""")
        todo = [r["domain"] for r in cur.fetchall()]
    for d in todo:
        try:
            domaincheck.kundenmail(d, erinnerung=True)
        except Exception:  # noqa: BLE001
            log.exception("DNS-Erinnerung %s", d)


def website_bewertungen(cfg):
    webbetrieb.bewertungsanfragen(cfg)


def website_qualitaet(cfg):
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 3 or not _marker("webqualitaet-" + jetzt.strftime("%Y-%m-%d")):
        return
    webbetrieb.qualitaetslauf(cfg)


def abrechnungslauf(cfg):
    jetzt = datetime.now(timezone.utc)
    if jetzt.hour < 6 or not _marker("abo-" + jetzt.strftime("%Y-%m-%d")):
        return
    abo.lauf(cfg)


def website_wacht(cfg):
    webbetrieb.wacht(cfg)


def website_still(cfg):
    """Täglich ab 7 Uhr: Betriebe melden, bei denen die sonst regelmäßigen Website-Anfragen ungewöhnlich lange ausbleiben."""
    jetzt = datetime.now(webbetrieb.TZ)
    if jetzt.hour < 7 or not _marker("anfragen-still-" + jetzt.strftime("%Y-%m-%d")):
        return
    webbetrieb.anfragen_still(cfg)


def rate_aufraeumen(cfg):
    """Täglich: alte Zähler der Anfragen-Begrenzung entfernen."""
    jetzt = datetime.now(webbetrieb.TZ)
    if not _marker("rate-aufraeumen-" + jetzt.strftime("%Y-%m-%d")):
        return
    with tx("system") as cur:
        security.rate_aufraeumen(cur)


def angebote_erinnern(cfg):
    """Werktags ab 9 Uhr, einmal täglich: unbeantwortete Angebote erinnern (Stufe 1 und 2), nur wenn in den Einstellungen eingeschaltet (Standard aus)."""
    jetzt = datetime.now(webbetrieb.TZ)
    if jetzt.hour < 9 or jetzt.weekday() >= 5 or not _marker("angebote-erinnern-" + jetzt.strftime("%Y-%m-%d")):
        return
    from . import angebotserinnerung
    angebotserinnerung.auto_lauf()


def angebote_abgelaufen(cfg):
    """Einmal täglich: abgelaufene, noch offene Angebote melden."""
    jetzt = datetime.now(webbetrieb.TZ)
    if jetzt.hour < 8 or not _marker("angebote-abgelaufen-" + jetzt.strftime("%Y-%m-%d")):
        return
    from . import angebotserinnerung
    angebotserinnerung.abgelaufen_melden()


def dsgvo_fristen(cfg):
    """Täglich: Datenschutz-Anfragen, deren Frist (ein Monat) in 7 Tagen oder früher endet, als dringende Aufgabe melden (einmal je Anfrage)."""
    jetzt = datetime.now(webbetrieb.TZ)
    if jetzt.hour < 7 or not _marker("dsgvo-fristen-" + jetzt.strftime("%Y-%m-%d")):
        return
    dsgvo_fristen_pruefen()


def dsgvo_fristen_pruefen() -> int:
    """Legt für bald ablaufende Anfragen je eine Aufgabe an (einmal je Anfrage). Gibt die Zahl der neuen Aufgaben zurück."""
    neu = 0
    with tx("system") as cur:
        cur.execute("SELECT id, art, name, frist_am FROM datenschutz_anfragen WHERE status IN ('neu','in_arbeit') AND frist_am <= current_date + 7")
        for a in cur.fetchall():
            cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                           VALUES (NULL, %s, %s, %s, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                        (f"Frist läuft ab: Datenschutz-Anfrage von {a['name'][:80]} ({a['frist_am'].strftime('%d.%m.%Y')})", admin_empfaenger(cur), a["frist_am"], f"dsgvo-frist-{a['id']}"))
            if cur.rowcount:
                neu += 1
                push.senden(push.admins(cur), "Datenschutz-Anfrage: Frist läuft ab", f"{a['name'][:60]}: Frist am {a['frist_am'].strftime('%d.%m.%Y')}.", "/admin#dsgvo", "dsgvo")
    return neu


def tick():
    betrieb.notieren("jobs")   # Herzschlag für die Betriebs-Ampel
    with tx("system") as cur:
        cfg = einstellungen_lesen(cur)
    for job in (vertrieb_morgens, anfragen_eskalation, veroeffentlichung_wacht, anrufe_aufraeumen, fotos_aufraeumen, rate_aufraeumen, fristen_loeschen, dsgvo_fristen, betriebs_alarm, wochenrueckblick, website_wacht, website_qualitaet, funnel_checks_nachholen, funnel_plaetze_monat, domain_pruefen, zustellung_pruefen, kuendigungen_vollziehen, zahlungsverzug, preisaenderung_anwenden, abrechnungslauf):
        _lauf(job, cfg)
    if not mailer.konfiguriert():
        return
    for job in (gespraech_erinnerungen, provisionsvorschau, mahnungen_automatisch, fruehwarnung_woche, geschaeftszahlen_mail, anfragen_mails, termin_erinnerungen, gutschein_erinnerungen, anzahlung_fristen, website_erinnerungen, website_bewertungen, domain_erinnerung, website_still, angebote_erinnern, angebote_abgelaufen, monatsberichte, fehler_melden, avv_erinnerung, avv_kunde_erinnerung, vertrag_erinnerung, umfragen_anlegen, vertrieb_erinnerung, website_online_meldungen, aufgaben_automatisch, lead_folgemails, funnel_folgemails, kunden_feedback, ueberwachung_stumm):
        _lauf(job, cfg)   # ein kaputter Job darf die anderen nicht stoppen


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
