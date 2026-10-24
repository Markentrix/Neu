"""Betrieb der Kunden-Websites: Terminerinnerungen an die Besucher und Überwachung (Erreichbarkeit, Zertifikat, Website-API).
Beides läuft als Hintergrundaufgabe des Portals (jobs.py). Mehrfachversand wird durch Markieren der Zeilen beim Abholen verhindert."""
import logging
import math
import re
import socket
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from . import config, mailer, push
from . import sitedienste as sd
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger, kunden_empfaenger

log = logging.getLogger("webbetrieb")
TZ = sd.TZ


# ---------------------------------------------------------------- Terminerinnerungen an die Besucher
def erinnerungen(cfg=None):
    """Erinnert Besucher per E-Mail an ihren Termin (Standard: 24 und 2 Stunden vorher), mit Link zum Absagen.
    Wer erst kurz vor dem Erinnerungszeitpunkt gebucht hat, bekommt keine zweite Mail direkt nach der Bestätigung."""
    with tx("system") as cur:
        cur.execute("""WITH offen AS (
                         SELECT w.id FROM website_termine w JOIN website_dienste z ON z.kunden_id = w.kunden_id JOIN kunden k ON k.id = w.kunden_id
                         WHERE w.status = 'gebucht' AND w.start > now() AND z.erinnerung_aktiv AND k.status IN ('onboarding','aktiv') AND w.erinnerung < 2
                           AND ((w.erinnerung < 1 AND z.erinnerung_std1 > 0 AND w.start <= now() + make_interval(hours => z.erinnerung_std1))
                             OR (z.erinnerung_std2 > 0 AND w.start <= now() + make_interval(hours => z.erinnerung_std2)))
                         ORDER BY w.start LIMIT 100 FOR UPDATE OF w SKIP LOCKED)
                       UPDATE website_termine w SET erinnerung = CASE WHEN z.erinnerung_std2 > 0 AND w.start <= now() + make_interval(hours => z.erinnerung_std2) THEN 2 ELSE 1 END
                       FROM offen, website_dienste z WHERE w.id = offen.id AND z.kunden_id = w.kunden_id
                       RETURNING w.id, z.erinnerung_std1, z.erinnerung_std2""")
        stufen = {r["id"]: (r["erinnerung_std1"], r["erinnerung_std2"]) for r in cur.fetchall()}
        if not stufen:
            return 0
        cur.execute("""SELECT w.id, w.kunden_id, w.start, w.name, w.email, w.token, w.erstellt_am, w.erinnerung, z.site_id, z.kal_ort, k.firma,
                              l.name AS leistung, m.name AS mitarbeiter
                       FROM website_termine w JOIN website_dienste z ON z.kunden_id = w.kunden_id JOIN kunden k ON k.id = w.kunden_id
                            LEFT JOIN website_leistungen l ON l.id = w.leistung_id LEFT JOIN website_mitarbeiter m ON m.id = w.mitarbeiter_id
                       WHERE w.id = ANY(%s)""", (list(stufen),))
        zeilen = cur.fetchall()
    gesendet = 0
    for r in zeilen:
        std1, std2 = stufen[r["id"]]
        if not r["email"]:
            continue                                   # von Hand eingetragener Termin ohne E-Mail-Adresse
        stunden = std2 if r["erinnerung"] == 2 else std1
        if r["erstellt_am"] > r["start"] - timedelta(hours=stunden + 1):
            continue                                   # erst kurz vorher gebucht: die Bestätigung genügt
        lokal = r["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
        wer = " · ".join(x for x in (r["leistung"], ("bei " + r["mitarbeiter"]) if r["mitarbeiter"] else "") if x)
        absagen = f"{config.BASE_URL}/site/{r['site_id']}/termin/absagen?t={r['token']}"
        komme = f"{config.BASE_URL}/site/{r['site_id']}/termin/komme?t={r['token']}"
        bald = "morgen" if r["erinnerung"] == 1 and stunden >= 12 else "bald"
        text = (f"Guten Tag {r['name']},\n\nwir erinnern Sie an Ihren Termin {bald}: {lokal}.\n{wer + chr(10) if wer else ''}{r['kal_ort'] + chr(10) if r['kal_ort'] else ''}\n"
                f"Bitte bestätigen Sie kurz mit einem Klick, dass Sie kommen:\n{komme}\n\nFalls Sie nicht kommen können, sagen Sie bitte hier ab, dann kann jemand anderes die Zeit nutzen:\n{absagen}\n\nWir freuen uns auf Sie!\n\nViele Grüße\n{r['firma']}")
        ok, via = sd.kundenmail(r["kunden_id"], r["email"], f"Erinnerung: Ihr Termin bei {r['firma']} am {lokal}", text, art="erinnerung")
        sd.ereignis(r["kunden_id"], "erinnerung", ok, "gesendet" if ok else "Versand fehlgeschlagen: " + str(via)[:150])
        gesendet += 1 if ok else 0
    return gesendet


def bewertungsanfragen(cfg=None):
    """Bittet Besucher nach einem erschienenen Termin um eine Google-Bewertung (nur mit Opt-in des Kunden, mit Abmeldelink)."""
    with tx("system") as cur:
        cur.execute("""WITH f AS (SELECT w.id FROM website_termine w JOIN kunden k ON k.id = w.kunden_id
                                  WHERE w.bewertung_faellig <= now() AND w.bewertung_gesendet IS NULL AND k.status IN ('onboarding','aktiv')
                                  ORDER BY w.bewertung_faellig LIMIT 50 FOR UPDATE OF w SKIP LOCKED)
                       UPDATE website_termine w SET bewertung_gesendet = now(), bewertung_faellig = NULL FROM f WHERE w.id = f.id
                       RETURNING w.id""")
        ids = [r["id"] for r in cur.fetchall()]
        if not ids:
            return 0
        cur.execute("""SELECT w.id, w.kunden_id, w.name, w.email, w.token, z.site_id, z.bew_link, z.bew_place_id, k.firma
                       FROM website_termine w JOIN website_dienste z ON z.kunden_id = w.kunden_id JOIN kunden k ON k.id = w.kunden_id WHERE w.id = ANY(%s)""", (ids,))
        zeilen = cur.fetchall()
    n = 0
    for r in zeilen:
        link = r["bew_link"] or (f"https://search.google.com/local/writereview?placeid={r['bew_place_id']}" if r["bew_place_id"] else "")
        if not link or not r["email"]:
            continue
        ab = f"{config.BASE_URL}/site/{r['site_id']}/bewertung/abmelden?t={r['token']}"
        text = (f"Guten Tag {r['name']},\n\nvielen Dank für Ihren Besuch bei {r['firma']}. Wenn Sie zufrieden waren, würden wir uns über eine kurze Bewertung bei Google freuen:\n{link}\n\n"
                f"Das dauert eine Minute und hilft uns sehr.\n\nViele Grüße\n{r['firma']}\n\n--\nKeine weiteren Bewertungsanfragen erhalten: {ab}")
        ok, via = sd.kundenmail(r["kunden_id"], r["email"], f"Wie war Ihr Besuch bei {r['firma']}?", text, art="bewertung")
        sd.ereignis(r["kunden_id"], "bewertung", ok, "gesendet" if ok else "Versand fehlgeschlagen: " + str(via)[:150])
        n += 1 if ok else 0
    return n


# ---------------------------------------------------------------- Überwachung der Kundenseiten
_letzter_lauf = 0.0


def _abrufen(url: str, host: str, timeout: int = 10, limit: int = 65536) -> tuple[int, bytes, int]:
    """(Statuscode, Inhalt bis 64 KB, Millisekunden). Fehler werden als ValueError mit lesbarem Text gemeldet."""
    req = urllib.request.Request(url, headers={"Host": host, "User-Agent": "Markentrix-Wachdienst/1", "Accept": "*/*"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(limit), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, b"", int((time.time() - t0) * 1000)
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError) as e:
        grund = getattr(e, "reason", e)
        raise ValueError(f"nicht erreichbar ({str(grund)[:120]})")


def _zertifikat_tage(domain: str) -> int | None:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=8) as s, ctx.wrap_socket(s, server_hostname=domain) as t:
            ende = ssl.cert_time_to_seconds(t.getpeercert()["notAfter"])
        return int((ende - time.time()) // 86400)
    except ssl.SSLCertVerificationError as e:
        raise ValueError("Zertifikat ungültig (" + str(getattr(e, "verify_message", e))[:80] + ")")
    except Exception:  # noqa: BLE001 - Zertifikat nicht lesbar: kein eigener Alarm, die Seitenprüfung meldet es
        return None


def _klartext(fehler: str) -> str:
    if "ALERT_INTERNAL_ERROR" in fehler or "tlsv1 alert internal error" in fehler:
        return "nicht erreichbar (der Webserver hat für diese Domain noch kein Zertifikat: Domain noch nicht eingebunden, DNS zu neu oder Zertifikat wird gerade geholt)"
    return fehler


def pruefen(domain: str) -> dict:
    """Prüft Startseite, Website-API (/api/health) und Zertifikat einer Website."""
    test = config.WACHT_BASIS
    basis = test or f"https://{domain}"
    out = {"domain": domain, "seite_ok": False, "api_ok": False, "http": None, "ms": None, "cert_tage": None, "fehler": ""}
    fehler = []
    try:
        code, body, ms = _abrufen(basis + "/", domain)
        out["http"], out["ms"] = code, ms
        out["seite_ok"] = 200 <= code < 400
        if not out["seite_ok"]:
            fehler.append(f"Startseite antwortet mit Fehler {code}")
    except ValueError as e:
        fehler.append("Startseite " + _klartext(str(e)))
    try:
        code, body, _ = _abrufen(basis + config.WACHT_API_PRAEFIX + "/api/health", domain)
        out["api_ok"] = code == 200 and b'"ok"' in body.replace(b" ", b"")
        if not out["api_ok"]:
            fehler.append("Website-API (/api/health) antwortet nicht richtig")
    except ValueError as e:
        fehler.append("Website-API " + _klartext(str(e)))
    if not test:
        try:
            out["cert_tage"] = _zertifikat_tage(domain)
        except ValueError as e:
            fehler.append(str(e))
    out["ok"] = out["seite_ok"] and out["api_ok"] and not any("Zertifikat ungültig" in f for f in fehler)
    out["fehler"] = "; ".join(fehler)[:300]
    return out


def _mail_admin(cfg, betreff: str, text: str, titel_push: str | None = None):
    with tx("system") as cur:
        an = (cfg or {}).get("alarm_email") or admin_empfaenger(cur)
        ids = push.admins(cur) if titel_push else []
    if ids:
        push.senden(ids, titel_push, text[:160], "/admin#websites", "websitealarm")
    if an and mailer.konfiguriert():
        try:
            mailer.senden(an, betreff, text + mailer.SIGNATUR)
        except Exception:  # noqa: BLE001
            log.exception("Wachdienst-Mail")


def ohne_www_doppel(seiten: list) -> list:
    """„www.firma.de“ wird nicht extra überwacht, wenn „firma.de“ desselben Kunden schon überwacht wird (die Hauptadresse zählt)."""
    haupt = {(s["kunden_id"], s["domain"]) for s in seiten}
    return [s for s in seiten if not (s["domain"].startswith("www.") and (s["kunden_id"], s["domain"][4:]) in haupt)]


def diagnose(domain: str, fehler: str) -> list[dict]:
    """Erklärt die Fehlermeldung der Prüfung: je Problem {titel, ursache, schritte, wer}. Schritte mit `Befehl` in Backticks."""
    f = fehler or ""
    www = domain.startswith("www.")
    haupt = domain[4:] if www else domain
    aus = []
    if "ALERT_INTERNAL_ERROR" in f or "tlsv1 alert internal error" in f:
        if www:
            aus.append({"titel": f"{domain}: Der Webserver hat für die www-Adresse kein Zertifikat",
                        "ursache": f"Die Adresse {domain} wird zwar geprüft, ist aber nicht beim Webserver (Caddy) eingerichtet oder zeigt per DNS nicht auf den Server. Die Hauptadresse {haupt} ist davon meist nicht betroffen.",
                        "schritte": [f"Wird {domain} gar nicht gebraucht: im Admin beim Kunden unter Websites die Zeile {domain} auf offline stellen oder löschen. Die Meldung verschwindet dann.",
                                     f"Soll {domain} funktionieren: beim Domain-Anbieter (INWX/IONOS) einen A-Eintrag `www` auf `5.75.146.212` anlegen.",
                                     f"Dann auf dem Server `mkctl site-list` prüfen und für {domain} eine Weiterleitung auf {haupt} im Webserver einrichten, danach 5 bis 10 Minuten warten (Zertifikat wird geholt)."],
                        "wer": "server"})
        else:
            aus.append({"titel": f"{domain}: Kein Zertifikat beim Webserver",
                        "ursache": "Der Webserver (Caddy) kennt diese Domain nicht oder konnte noch kein Zertifikat holen. Häufige Gründe: Domain noch nicht eingerichtet, DNS zeigt noch nicht auf den Server, DNS ist zu neu.",
                        "schritte": [f"DNS prüfen: `dig +short {domain}` muss `5.75.146.212` liefern. Wenn nicht: beim Domain-Anbieter den A-Eintrag auf `5.75.146.212` setzen.",
                                     f"Auf dem Server einmal `mkctl site-add {domain}` ausführen (legt Ordner und Webserver-Eintrag an).",
                                     "Danach 5 bis 10 Minuten warten, bis das Zertifikat geholt ist. Mit `docker logs server-caddy-1 --tail 50` sieht man Fehler dazu."],
                        "wer": "server"})
    elif "Name or service not known" in f or "nodename nor servname" in f or "Temporary failure in name resolution" in f:
        aus.append({"titel": f"{domain}: Die Domain wird nicht gefunden (DNS)",
                    "ursache": "Die Domain hat keinen oder einen falschen DNS-Eintrag, oder die Domain ist abgelaufen.",
                    "schritte": [f"`dig +short {domain}` auf dem Server ausführen. Keine Antwort heißt: A-Eintrag fehlt.",
                                 f"Beim Domain-Anbieter einen A-Eintrag für {domain} auf `5.75.146.212` setzen und Laufzeit der Domain prüfen."], "wer": "admin"})
    elif "timed out" in f or "Connection refused" in f or "Connection reset" in f or "Errno 111" in f or "Errno 110" in f:
        aus.append({"titel": f"{domain}: Keine Verbindung zum Server",
                    "ursache": "Die Domain zeigt auf eine Adresse, aber dort antwortet der Webserver nicht (Caddy gestoppt, Firewall oder falsche IP).",
                    "schritte": [f"`dig +short {domain}` muss `5.75.146.212` zeigen.", "Auf dem Server `mkctl status` ausführen und prüfen, ob der Webserver läuft.", "Falls nicht: `docker restart server-caddy-1` und `mkctl selbsttest`."], "wer": "server"})
    if "Zertifikat ungültig" in f:
        aus.append({"titel": f"{domain}: Zertifikat ist ungültig oder abgelaufen",
                    "ursache": "Das HTTPS-Zertifikat passt nicht zur Domain oder ist abgelaufen. Caddy erneuert es normalerweise selbst, das klappt nur, wenn die Domain auf den Server zeigt.",
                    "schritte": [f"`dig +short {domain}` muss `5.75.146.212` zeigen.", "Fehler beim Erneuern ansehen: `docker logs server-caddy-1 --tail 100`.", "Nach Korrektur Caddy neu laden: `docker restart server-caddy-1`."], "wer": "server"})
    m = re.search(r"Startseite antwortet mit Fehler (\d+)", f)
    if m:
        code = int(m.group(1))
        ursache = {404: "Die Startseite fehlt im Website-Ordner oder die Domain ist nicht dem richtigen Ordner zugeordnet.",
                   403: "Der Zugriff wird verweigert (Dateirechte im Website-Ordner oder Sperre).",
                   502: "Der Webserver erreicht das Portal oder die Website nicht (Dienst gestoppt).", 503: "Der Dienst ist überlastet oder gestoppt.",
                   500: "Auf dem Server ist ein interner Fehler aufgetreten."}.get(code, f"Die Startseite liefert den Fehlercode {code}.")
        aus.append({"titel": f"{domain}: Startseite meldet Fehler {code}", "ursache": ursache,
                    "schritte": [f"Seite im Browser öffnen: https://{domain}/", f"Ordner prüfen: `mkctl site-list` (muss {domain} mit einer index.html zeigen). Neu hochladen im Admin unter Websites & Demos.",
                                 "Logs ansehen: `docker logs server-caddy-1 --tail 50` und `docker logs mk-portal --tail 50`."], "wer": "server"})
    if "Website-API (/api/health) antwortet nicht richtig" in f or ("Website-API" in f and "nicht erreichbar" in f and not aus):
        aus.append({"titel": f"{domain}: Website-API (/api/health) antwortet nicht",
                    "ursache": "Kontaktformular, Terminbuchung und Bewertungen der Website brauchen die Website-API. Der Webserver leitet /api/ für diese Domain nicht ans Portal weiter oder das Portal läuft nicht.",
                    "schritte": [f"`curl -s https://{domain}/api/health` ausführen: erwartet wird eine Antwort mit ok.", "Fehlt die Weiterleitung: Domain-Datei in `/srv/caddy-sites` prüfen oder `mkctl site-add " + haupt + "` erneut ausführen.",
                                 "Läuft das Portal? `mkctl status` und `docker logs mk-portal --tail 50`."], "wer": "server"})
    if not aus and f:
        aus.append({"titel": f"{domain}: Prüfung meldet einen Fehler", "ursache": f"Meldung: {f}",
                    "schritte": [f"Seite im Browser öffnen: https://{domain}/", "`mkctl selbsttest` auf dem Server ausführen und `docker logs server-caddy-1 --tail 50` ansehen.", "Hilft das nicht: Meldung unter Admin > Übersicht > Fehler-Hilfe einfügen."], "wer": "server"})
    return aus


def probleme(cur, kid) -> list[dict]:
    """Gestörte, aktive Websites eines Kunden mit Fehlertext und Erklärung (für die Kundenseite im Admin)."""
    cur.execute("""SELECT x.domain, x.fehler, x.seit, x.geprueft_am FROM website_wacht x
                   WHERE x.kunden_id=%s AND NOT x.ok AND EXISTS (SELECT 1 FROM websites w WHERE w.domain=x.domain AND w.kunden_id=x.kunden_id AND w.art='live' AND w.status='live')
                   ORDER BY x.domain""", (kid,))
    return [{"domain": r["domain"], "fehler": r["fehler"] or "", "seit": r["seit"], "geprueft_am": r["geprueft_am"], "erklaerung": diagnose(r["domain"], r["fehler"] or "")} for r in cur.fetchall()]


def wacht(cfg=None, erzwingen: bool = False):
    """Alle fünf Minuten: jede veröffentlichte Website prüfen. Alarm nach zwei Fehlschlägen in Folge, Entwarnung bei Erholung,
    Hinweis bei Zertifikat unter 14 Tagen. Neue Websites, deren Domain noch nicht auf den Server zeigt, lösen keinen Alarm aus."""
    global _letzter_lauf
    if not erzwingen and time.time() - _letzter_lauf < 280:
        return
    _letzter_lauf = time.time()
    with tx("system") as cur:
        cur.execute("""SELECT w.domain, w.kunden_id, k.firma, k.kundennummer, w.letzte_veroeffentlichung,
                              EXISTS (SELECT 1 FROM website_wacht_tag t WHERE t.domain = w.domain AND t.ok > 0) AS lief_schon
                       FROM websites w JOIN kunden k ON k.id = w.kunden_id
                       WHERE w.art = 'live' AND w.status = 'live' ORDER BY w.domain LIMIT 500""")
        seiten = cur.fetchall()
    seiten = ohne_www_doppel(seiten)
    if not seiten:
        return
    with ThreadPoolExecutor(max_workers=8) as pool:
        ergebnisse = list(pool.map(lambda s: pruefen(s["domain"]), seiten))
    for s, e in zip(seiten, ergebnisse):
        try:
            _verbuchen(cfg, s, e)
        except Exception:  # noqa: BLE001
            log.exception("Wachdienst %s", s["domain"])
    with tx("system") as cur:
        if int(time.time()) % 50 == 0:
            cur.execute("DELETE FROM website_wacht_tag WHERE tag < current_date - 400")


def _verbuchen(cfg, s: dict, e: dict):
    domain, kid = s["domain"], s["kunden_id"]
    with tx("system") as cur:
        cur.execute("SELECT * FROM website_wacht WHERE domain=%s FOR UPDATE", (domain,))
        alt = cur.fetchone()
        ok = e["ok"]
        fehlversuche = 0 if ok else (alt["fehlversuche"] + 1 if alt else 1)
        gemeldet = bool(alt and alt["gemeldet"])
        seit = alt["seit"] if alt and alt["ok"] == ok else datetime.now(timezone.utc)
        cert_melden = False
        cert_am = alt["cert_gemeldet_am"] if alt else None
        if e["cert_tage"] is not None and e["cert_tage"] < 14 and (cert_am is None or cert_am < datetime.now(timezone.utc) - timedelta(days=3)):
            cert_melden, cert_am = True, datetime.now(timezone.utc)
        if e["cert_tage"] is not None and e["cert_tage"] >= 14:
            cert_am = None
        lief = bool(s["lief_schon"]) or ok or (s["letzte_veroeffentlichung"] is not None and s["letzte_veroeffentlichung"] < datetime.now(timezone.utc) - timedelta(days=3))
        alarm = (not ok) and fehlversuche >= 2 and not gemeldet and lief
        entwarnung = ok and gemeldet
        if alarm:
            gemeldet = True
        if entwarnung:
            gemeldet = False
        cur.execute("""INSERT INTO website_wacht (domain, kunden_id, geprueft_am, ok, seite_ok, api_ok, http, ms, cert_tage, fehler, seit, fehlversuche, gemeldet, cert_gemeldet_am)
                       VALUES (%s,%s,now(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (domain) DO UPDATE SET kunden_id=EXCLUDED.kunden_id, geprueft_am=now(), ok=EXCLUDED.ok, seite_ok=EXCLUDED.seite_ok, api_ok=EXCLUDED.api_ok,
                         http=EXCLUDED.http, ms=EXCLUDED.ms, cert_tage=EXCLUDED.cert_tage, fehler=EXCLUDED.fehler, seit=EXCLUDED.seit,
                         fehlversuche=EXCLUDED.fehlversuche, gemeldet=EXCLUDED.gemeldet, cert_gemeldet_am=EXCLUDED.cert_gemeldet_am""",
                    (domain, kid, ok, e["seite_ok"], e["api_ok"], e["http"], e["ms"], e["cert_tage"], e["fehler"] or None, seit, fehlversuche, gemeldet, cert_am))
        cur.execute("""INSERT INTO website_wacht_tag (domain, tag, geprueft, ok) VALUES (%s, current_date, 1, %s)
                       ON CONFLICT (domain, tag) DO UPDATE SET geprueft = website_wacht_tag.geprueft + 1, ok = website_wacht_tag.ok + EXCLUDED.ok""", (domain, 1 if ok else 0))
    wer = f"{s['firma']} ({s['kundennummer']})"
    if ok and not s["lief_schon"]:
        with tx("system") as cur:
            ids = push.admins(cur)
        if ids:
            push.senden(ids, "Website ist live", f"{domain} ({wer}) ist erreichbar, das Zertifikat ist aktiv.", "/admin#websites", "websitelive")
    if alarm:
        _mail_admin(cfg, f"Website nicht erreichbar: {domain}", f"Die Website {domain} von {wer} ist nicht in Ordnung:\n\n{e['fehler'] or 'keine Antwort'}\n\n"
                    "Bitte prüfen: Läuft Caddy? Zeigt die Domain (A-Eintrag) auf den Server? Ist das Zertifikat gültig?", f"Website nicht erreichbar: {domain}")
    if entwarnung:
        dauer = int((datetime.now(timezone.utc) - alt["seit"]).total_seconds() // 60) if alt else 0
        _mail_admin(cfg, f"Website wieder erreichbar: {domain}", f"Die Website {domain} von {wer} antwortet wieder (Ausfall etwa {dauer} Minuten).", f"Wieder erreichbar: {domain}")
    if cert_melden:
        _mail_admin(cfg, f"Zertifikat läuft ab: {domain}", f"Das HTTPS-Zertifikat von {domain} ({wer}) läuft in {e['cert_tage']} Tagen ab. Caddy erneuert es normalerweise selbst: "
                    "Bitte prüfen, ob die Domain noch auf den Server zeigt.", f"Zertifikat läuft ab: {domain}")


LANGSAM_MS = 3000


def qualitaet_pruefen(domain: str) -> dict:
    """Ruft die Startseite und bis zu 25 verschiedene interne Seiten auf: tote Verweise (Fehlercode oder nicht erreichbar) und langsame Seiten."""
    from urllib.parse import urldefrag, urljoin, urlparse
    from .livecheck import _P
    basis = config.WACHT_BASIS or f"https://{domain}"
    seiten = {}
    try:
        code, body, ms = _abrufen(basis + "/", domain, 15, 3_000_000)
    except ValueError as e:
        return {"fehler": str(e), "seiten": 0, "median_ms": None, "startseite_kb": None, "tote": [], "langsam": []}
    seiten["/"] = (code, ms)
    startseite_kb = round(len(body) / 1024)
    ps = _P()
    try:
        ps.feed(body.decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        pass
    ziele, herkunft = [], {}
    for ref in ps.links + ps.refs:
        ref, _ = urldefrag(ref.strip())
        if not ref or ref.startswith(("mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:")):
            continue
        u = urlparse(urljoin("https://" + domain + "/", ref))
        if u.netloc.lower().removeprefix("www.") != domain.lower().removeprefix("www."):
            continue
        pfad = u.path or "/"
        if pfad not in herkunft and pfad != "/":
            herkunft[pfad] = "/"
            ziele.append(pfad + (("?" + u.query) if u.query else ""))
    for pfad in ziele[:25]:
        try:
            code, _, ms = _abrufen(basis + pfad, domain, 15, 1024)
        except ValueError:
            code, ms = 0, None
        seiten[pfad] = (code, ms)
    tote = [{"pfad": k, "code": v[0]} for k, v in seiten.items() if v[0] == 0 or v[0] >= 400][:25]
    zeiten = sorted(v[1] for v in seiten.values() if v[1] is not None)
    langsam = [{"pfad": k, "ms": v[1]} for k, v in seiten.items() if v[1] is not None and v[1] > LANGSAM_MS][:10]
    return {"fehler": "", "seiten": len(seiten), "median_ms": zeiten[len(zeiten) // 2] if zeiten else None, "startseite_kb": startseite_kb, "tote": tote, "langsam": langsam}


def qualitaetslauf(cfg=None):
    """Einmal täglich je Live-Website: Ladezeit und tote Verweise prüfen und speichern. Bei neuen toten Verweisen erhält der Admin einen Hinweis."""
    import json
    with tx("system") as cur:
        cur.execute("""SELECT w.domain, w.kunden_id, k.firma FROM websites w JOIN kunden k ON k.id = w.kunden_id
                       WHERE w.art = 'live' AND w.status = 'live' AND k.status IN ('onboarding','aktiv') ORDER BY w.domain LIMIT 200""")
        seiten = cur.fetchall()
    if not seiten:
        return 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        erg = list(pool.map(lambda s: qualitaet_pruefen(s["domain"]), seiten))
    for s, e in zip(seiten, erg):
        if e["fehler"]:
            continue
        with tx("system") as cur:
            cur.execute("SELECT jsonb_array_length(tote) AS n FROM website_qualitaet WHERE domain=%s", (s["domain"],))
            alt = cur.fetchone()
            cur.execute("""INSERT INTO website_qualitaet (domain, kunden_id, geprueft_am, seiten, median_ms, startseite_kb, tote, langsam) VALUES (%s,%s,now(),%s,%s,%s,%s,%s)
                           ON CONFLICT (domain) DO UPDATE SET kunden_id=EXCLUDED.kunden_id, geprueft_am=now(), seiten=EXCLUDED.seiten, median_ms=EXCLUDED.median_ms,
                             startseite_kb=EXCLUDED.startseite_kb, tote=EXCLUDED.tote, langsam=EXCLUDED.langsam""",
                        (s["domain"], s["kunden_id"], e["seiten"], e["median_ms"], e["startseite_kb"], json.dumps(e["tote"]), json.dumps(e["langsam"])))
        if e["tote"] and (not alt or alt["n"] == 0):
            _mail_admin(cfg, f"Tote Links auf {s['domain']}", f"Auf {s['domain']} ({s['firma']}) antworten {len(e['tote'])} Verweise mit Fehler:\n\n"
                        + "\n".join(f"{t['pfad']} (Code {t['code'] or 'keine Antwort'})" for t in e["tote"][:10]), f"Tote Links: {s['domain']}")
    return len(seiten)


def status(cur, kid=None) -> list:
    """Letzter Stand je Website (mit Erreichbarkeit der letzten 30 Tage in Prozent und der täglichen Qualitätsprüfung)."""
    cur.execute("""SELECT w.domain, w.kunden_id, w.geprueft_am, w.ok, w.seite_ok, w.api_ok, w.http, w.ms, w.cert_tage, w.fehler, w.seit,
                          (SELECT round(100.0 * sum(t.ok) / nullif(sum(t.geprueft), 0), 2) FROM website_wacht_tag t WHERE t.domain = w.domain AND t.tag > current_date - 30) AS prozent,
                          q.geprueft_am AS q_am, q.seiten AS q_seiten, q.median_ms AS q_median, q.startseite_kb AS q_kb, q.tote AS q_tote, q.langsam AS q_langsam,
                          (EXISTS (SELECT 1 FROM website_wacht_tag t WHERE t.domain = w.domain AND t.ok > 0) = false
                           AND COALESCE((SELECT x.letzte_veroeffentlichung FROM websites x WHERE x.domain = w.domain AND x.art = 'live'), now()) > now() - interval '3 days') AS wartet_dns
                   FROM website_wacht w LEFT JOIN website_qualitaet q ON q.domain = w.domain
                   WHERE (%s::uuid IS NULL OR w.kunden_id = %s::uuid) AND EXISTS (SELECT 1 FROM websites z WHERE z.domain = w.domain AND z.kunden_id = w.kunden_id AND z.art = 'live' AND z.status = 'live') ORDER BY w.domain""", (kid, kid))
    return [{"domain": r["domain"], "kunden_id": str(r["kunden_id"]), "geprueft_am": r["geprueft_am"], "ok": r["ok"], "seite_ok": r["seite_ok"], "api_ok": r["api_ok"], "http": r["http"],
             "ms": r["ms"], "cert_tage": r["cert_tage"], "fehler": r["fehler"] or "", "wartet_dns": bool(r["wartet_dns"]) and not r["ok"], "seit": r["seit"], "prozent": float(r["prozent"]) if r["prozent"] is not None else None,
             "qualitaet": {"geprueft_am": r["q_am"], "seiten": r["q_seiten"], "median_ms": r["q_median"], "startseite_kb": r["q_kb"], "tote": r["q_tote"] or [], "langsam": r["q_langsam"] or []} if r["q_am"] else None}
            for r in cur.fetchall()]


def erreichbarkeit(cur, kid, von, bis):
    """Erreichbarkeit aller Websites eines Kunden im Zeitraum in Prozent (None, wenn nicht gemessen)."""
    cur.execute("""SELECT sum(t.ok) AS ok, sum(t.geprueft) AS n FROM website_wacht_tag t JOIN websites w ON w.domain = t.domain
                   WHERE w.kunden_id = %s AND t.tag >= %s AND t.tag < %s""", (kid, von, bis))
    r = cur.fetchone()
    return round(100.0 * r["ok"] / r["n"], 2) if r and r["n"] else None


# ---------------------------------------------------------------- Gutschein-Anfragen, die einen Tag lang offen sind
def gutschein_erinnerung(cfg=None):
    """Erinnert den Betrieb einmal, wenn eine Gutschein-Anfrage nach einem Tag noch offen ist (Zahlungslink oder Code fehlt noch)."""
    with tx("system") as cur:
        cur.execute("""WITH f AS (SELECT g.id FROM website_gutscheine g JOIN kunden k ON k.id = g.kunden_id
                                  WHERE g.status IN ('angefragt','zahlungslink_gesendet') AND g.erinnert_am IS NULL AND k.status IN ('onboarding','aktiv')
                                    AND coalesce(g.zahlungslink_am, g.erstellt_am) < now() - interval '1 day' AND g.erstellt_am > now() - interval '30 days'
                                  ORDER BY g.erstellt_am LIMIT 50 FOR UPDATE OF g SKIP LOCKED)
                       UPDATE website_gutscheine g SET erinnert_am = now() FROM f WHERE g.id = f.id
                       RETURNING g.kunden_id, g.name, g.ref, g.betrag, g.status""")
        zeilen = cur.fetchall()
    gesendet = 0
    for r in zeilen:
        with tx("system") as cur:
            cur.execute("SELECT firma FROM kunden WHERE id=%s", (r["kunden_id"],))
            firma = cur.fetchone()["firma"]
            an = kunden_empfaenger(cur, r["kunden_id"])
            ids = push.kunde(cur, r["kunden_id"])
        betrag = f" über {r['betrag']:.2f}".replace(".", ",") + " €" if r["betrag"] is not None else ""
        schritt = ("Der Zahlungslink wurde noch nicht gesendet." if r["status"] == "angefragt"
                   else "Der Zahlungslink ging raus. Bitte prüfen, ob die Zahlung da ist, und dann den Gutschein-Code senden.")
        text = (f"Hallo {firma},\n\ndie Gutschein-Anfrage von {r['name']}{betrag} ({r['ref']}) ist seit einem Tag offen. {schritt}\n\n"
                f"Das geht im Portal unter Website-Dienste → Gutschein-Anfragen:\n{config.BASE_URL}/app#dienste" + mailer.SIGNATUR)
        for a in an:
            ok, _ = mailer.senden(a, f"Offene Gutschein-Anfrage: {r['name']} ({r['ref']})", text, kunden_id=r["kunden_id"], art="gutschein_erinnerung")
            gesendet += 1 if ok else 0
        push.senden(ids, "Gutschein-Anfrage offen", f"{r['name']}: seit einem Tag ohne Abschluss.", "/app#dienste", "gutschein")
    return gesendet


# ---------------------------------------------------------------- Anzahlung nicht eingegangen: Termin wieder freigeben
def anzahlung_frist(cfg=None):
    """Hat der Betrieb eine Frist für die Anzahlung eingestellt und ist bis dahin kein Zahlungseingang markiert, wird der Termin freigegeben."""
    with tx("system") as cur:
        cur.execute("""WITH f AS (SELECT w.id FROM website_termine w JOIN website_dienste d ON d.kunden_id = w.kunden_id JOIN kunden k ON k.id = w.kunden_id
                                  WHERE d.anz_frist_std > 0 AND w.anzahlung_betrag > 0 AND w.anzahlung_erhalten_am IS NULL AND w.status IN ('gebucht','reserviert')
                                    AND w.start > now() AND w.erstellt_am < now() - make_interval(hours => d.anz_frist_std) AND k.status IN ('onboarding','aktiv')
                                  ORDER BY w.erstellt_am LIMIT 50 FOR UPDATE OF w SKIP LOCKED)
                       UPDATE website_termine w SET status = 'abgesagt' FROM f WHERE w.id = f.id
                       RETURNING w.kunden_id, w.termin_id, w.start, w.name, w.email, w.anzahlung, w.ref""")
        zeilen = cur.fetchall()
        for r in zeilen:
            if r["termin_id"]:
                cur.execute("UPDATE termine SET status='abgesagt' WHERE id=%s", (r["termin_id"],))
    n = 0
    for r in zeilen:
        lokal = r["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
        with tx("system") as cur:
            cur.execute("SELECT firma FROM kunden WHERE id=%s", (r["kunden_id"],))
            firma = cur.fetchone()["firma"]
            an = kunden_empfaenger(cur, r["kunden_id"])
            ids = push.kunde(cur, r["kunden_id"])
        sd.kundenmail(r["kunden_id"], r["email"], f"Ihr Termin bei {firma} am {lokal} wurde freigegeben",
                      f"Guten Tag {r['name']},\n\nleider ist die Anzahlung von {str(r['anzahlung']).replace('.', ',')} € für Ihren Termin am {lokal} nicht bei uns eingegangen. "
                      f"Wir haben den Termin deshalb wieder freigegeben. Sie können gern jederzeit neu buchen.\n\nViele Grüße\n{firma}", art="termin")
        for a in an:
            mailer.senden(a, f"Termin freigegeben: {r['name']} ({r['ref'] or ''})",
                          f"Für den Termin von {r['name']} am {lokal} ist innerhalb der Frist keine Anzahlung als erhalten markiert worden. Das Portal hat den Termin freigegeben und {r['name']} informiert. "
                          f"Falls die Zahlung doch da ist, bitte den Termin neu eintragen." + mailer.SIGNATUR, kunden_id=r["kunden_id"], art="termin")
        push.senden(ids, "Termin freigegeben", f"{r['name']}: keine Anzahlung bis zur Frist ({lokal}).", "/app#heute", "termin")
        n += 1
    return n


# ---------------------------------------------------------------- Stillstand-Alarm und Start-Checkliste
def still_schwelle(n60: int) -> int:
    """Nach wie vielen Tagen ohne Anfrage fällt es auf: Kunden mit vielen Anfragen schon früh, mit wenigen spät (zwischen 4 und 14 Tagen).
    Grundlage: Pause, die bei der bisherigen Anfragehäufigkeit nur in etwa 1 von 100 Fällen vorkommt."""
    lam = max(n60, 1) / 60
    return int(min(14, max(4, math.ceil(4.6 / lam))))


def anfragen_still(cfg=None):
    """Täglich: meldet Betriebe, bei denen über die Website sonst regelmäßig Anfragen kommen, jetzt aber seit ungewöhnlich langer Zeit keine mehr.
    Das ist oft das einzige Anzeichen, dass ein Formular, die Mail oder die Verbindung zur Website kaputt ist, obwohl die Seite selbst erreichbar ist."""
    with tx("system") as cur:
        cur.execute("""SELECT k.id, k.firma, w.domain,
                              (SELECT count(*) FROM anfragen a WHERE a.kunden_id=k.id AND a.quelle='website' AND a.erstellt_am > now() - interval '60 days') AS n60,
                              (SELECT max(a.erstellt_am) FROM anfragen a WHERE a.kunden_id=k.id AND a.quelle='website') AS letzte,
                              (SELECT count(*) FROM mail_protokoll m WHERE m.kunden_id=k.id AND NOT m.ok AND m.zeit > now() - interval '7 days') AS mailfehler
                       FROM kunden k JOIN websites w ON w.kunden_id=k.id AND w.art='live' AND w.status='live'
                       WHERE k.status='aktiv' ORDER BY k.firma LIMIT 500""")
        zeilen = cur.fetchall()
    jetzt = datetime.now(timezone.utc)
    for z in zeilen:
        if z["n60"] < 12 or not z["letzte"]:
            continue
        tage = (jetzt - z["letzte"]).days
        if tage < still_schwelle(z["n60"]):
            continue
        if not _marker_neu(f"still-{z['id']}-{z['letzte']:%Y%m%d}"):
            continue
        _mail_admin(cfg, f"Keine Anfragen mehr bei {z['firma']}",
                    f"Bei {z['firma']} ({z['domain']}) kamen in den letzten 60 Tagen {z['n60']} Anfragen über die Website, die letzte vor {tage} Tagen ({z['letzte'].astimezone(TZ):%d.%m.%Y}).\n"
                    "Das ist für diesen Betrieb ungewöhnlich. Bitte prüfen:\n"
                    "- Testanfrage über die Website absenden: Kommt sie im Portal unter „Anfragen“ an?\n"
                    "- Kommt die Mail an den Betrieb? (Admin → Kunde → Website-Dienste, Zustellung)\n"
                    "- Hat sich die Website geändert (neu hochgeladen)? Dann das Formular testen." + (f"\n- In den letzten 7 Tagen gab es {z['mailfehler']} fehlgeschlagene Mails." if z["mailfehler"] else ""),
                    f"Keine Anfragen mehr: {z['firma']}")


def _marker_neu(schluessel: str) -> bool:
    with tx("system") as cur:
        cur.execute("INSERT INTO job_marker (schluessel) VALUES (%s) ON CONFLICT DO NOTHING", (schluessel,))
        return cur.rowcount == 1


def start_checkliste(cur, kid) -> dict:
    """Was fehlt, damit die Website eines Kunden wirklich funktioniert? Wird live berechnet, nichts davon ist von Hand abzuhaken."""
    cur.execute("SELECT * FROM website_dienste WHERE kunden_id=%s", (kid,))
    d = cur.fetchone() or {}
    cur.execute("SELECT (logo IS NOT NULL) AS logo FROM kunden WHERE id=%s", (kid,))
    logo = bool((cur.fetchone() or {}).get("logo"))
    cur.execute("SELECT domain FROM websites WHERE kunden_id=%s AND art='live' AND status='live' ORDER BY domain LIMIT 1", (kid,))
    web = cur.fetchone()
    ok_seite = False
    if web:
        cur.execute("SELECT ok FROM website_wacht WHERE domain=%s", (web["domain"],))
        w = cur.fetchone()
        ok_seite = bool(w and w["ok"])
    cur.execute("SELECT exists(SELECT 1 FROM mail_protokoll WHERE kunden_id=%s AND art='test' AND ok) AS t", (kid,))
    test_ok = bool(cur.fetchone()["t"])
    cur.execute("SELECT exists(SELECT 1 FROM anfragen WHERE kunden_id=%s AND quelle='website') AS a", (kid,))
    anfrage_da = bool(cur.fetchone()["a"])
    punkte = [
        ("seite", "Website ist veröffentlicht und erreichbar", bool(web) and ok_seite, True, "Admin → Kunde → Websites: ZIP hochladen und veröffentlichen, Domain auf den Server zeigen lassen."),
        ("empfaenger", "Anfragen gehen an eine E-Mail-Adresse des Betriebs", bool(d.get("mail_aktiv") and (d.get("mail_empfaenger") or "").strip()), True, "Website-Dienste → Kontaktformular: Formular einschalten und Adresse eintragen."),
        ("logo", "Logo für die Mails ist hinterlegt", logo, True, "Admin → Kunde → Branding: Logo (PNG oder JPG) hochladen."),
        ("signatur", "Signatur für Mails an die Gäste ist eingetragen", bool((d.get("mail_signatur") or "").strip()), True, "Website-Dienste → Kontaktformular: „Vorschlag aus meinen Firmendaten einfügen“."),
        ("testmail", "Testmail erfolgreich gesendet", test_ok, True, "Website-Dienste → Kontaktformular: „Testmail senden“."),
        ("anfrage", "Eine Testanfrage über die Website ist im Portal angekommen", anfrage_da, True, "Auf der echten Website das Formular absenden und unter „Anfragen“ nachsehen."),
    ]
    if d.get("kal_aktiv"):
        cur.execute("SELECT exists(SELECT 1 FROM website_termine WHERE kunden_id=%s) AS t", (kid,))
        punkte.append(("termin", "Eine Testbuchung ist angekommen", bool(cur.fetchone()["t"]), True, "Auf der Website einen Termin anfragen; er erscheint unter „Heute“ bzw. bei den Buchungen."))
    if d.get("pp_aktiv"):
        punkte.append(("paypal", "PayPal ist eingerichtet", bool(d.get("pp_me_link") or d.get("pp_client_id")), False, "Website-Dienste → PayPal: PayPal.Me-Link eintragen."))
    liste = [{"code": c, "titel": t, "erledigt": e, "pflicht": p, "hinweis": h} for c, t, e, p, h in punkte]
    pflicht = [x for x in liste if x["pflicht"]]
    return {"punkte": liste, "fertig": all(x["erledigt"] for x in pflicht), "erledigt": sum(1 for x in pflicht if x["erledigt"]), "gesamt": len(pflicht)}
