"""Betrieb der Kunden-Websites: Terminerinnerungen an die Besucher und Überwachung (Erreichbarkeit, Zertifikat, Website-API).
Beides läuft als Hintergrundaufgabe des Portals (jobs.py). Mehrfachversand wird durch Markieren der Zeilen beim Abholen verhindert."""
import logging
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
from .routes_zusammenarbeit import admin_empfaenger

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
        stunden = std2 if r["erinnerung"] == 2 else std1
        if r["erstellt_am"] > r["start"] - timedelta(hours=stunden + 1):
            continue                                   # erst kurz vorher gebucht: die Bestätigung genügt
        lokal = r["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
        wer = " · ".join(x for x in (r["leistung"], ("bei " + r["mitarbeiter"]) if r["mitarbeiter"] else "") if x)
        absagen = f"{config.BASE_URL}/site/{r['site_id']}/termin/absagen?t={r['token']}"
        bald = "morgen" if r["erinnerung"] == 1 and stunden >= 12 else "bald"
        text = (f"Guten Tag {r['name']},\n\nwir erinnern Sie an Ihren Termin {bald}: {lokal}.\n{wer + chr(10) if wer else ''}{r['kal_ort'] + chr(10) if r['kal_ort'] else ''}\n"
                f"Falls Sie nicht kommen können, sagen Sie bitte hier ab, dann kann jemand anderes die Zeit nutzen:\n{absagen}\n\nWir freuen uns auf Sie!\n{r['firma']}")
        ok, via = sd.kundenmail(r["kunden_id"], r["email"], f"Erinnerung: Ihr Termin bei {r['firma']} am {lokal}", text, art="erinnerung")
        sd.ereignis(r["kunden_id"], "erinnerung", ok, "gesendet" if ok else "Versand fehlgeschlagen: " + str(via)[:150])
        gesendet += 1 if ok else 0
    return gesendet


# ---------------------------------------------------------------- Überwachung der Kundenseiten
_letzter_lauf = 0.0


def _abrufen(url: str, host: str, timeout: int = 10) -> tuple[int, bytes, int]:
    """(Statuscode, Inhalt bis 64 KB, Millisekunden). Fehler werden als ValueError mit lesbarem Text gemeldet."""
    req = urllib.request.Request(url, headers={"Host": host, "User-Agent": "Markentrix-Wachdienst/1", "Accept": "*/*"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(65536), int((time.time() - t0) * 1000)
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
        fehler.append("Startseite " + str(e))
    try:
        code, body, _ = _abrufen(basis + config.WACHT_API_PRAEFIX + "/api/health", domain)
        out["api_ok"] = code == 200 and b'"ok"' in body.replace(b" ", b"")
        if not out["api_ok"]:
            fehler.append("Website-API (/api/health) antwortet nicht richtig")
    except ValueError as e:
        fehler.append("Website-API " + str(e))
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
    if alarm:
        _mail_admin(cfg, f"Website nicht erreichbar: {domain}", f"Die Website {domain} von {wer} ist nicht in Ordnung:\n\n{e['fehler'] or 'keine Antwort'}\n\n"
                    "Bitte prüfen: Läuft Caddy? Zeigt die Domain (A-Eintrag) auf den Server? Ist das Zertifikat gültig?", f"Website nicht erreichbar: {domain}")
    if entwarnung:
        dauer = int((datetime.now(timezone.utc) - alt["seit"]).total_seconds() // 60) if alt else 0
        _mail_admin(cfg, f"Website wieder erreichbar: {domain}", f"Die Website {domain} von {wer} antwortet wieder (Ausfall etwa {dauer} Minuten).", f"Wieder erreichbar: {domain}")
    if cert_melden:
        _mail_admin(cfg, f"Zertifikat läuft ab: {domain}", f"Das HTTPS-Zertifikat von {domain} ({wer}) läuft in {e['cert_tage']} Tagen ab. Caddy erneuert es normalerweise selbst: "
                    "Bitte prüfen, ob die Domain noch auf den Server zeigt.", f"Zertifikat läuft ab: {domain}")


def status(cur, kid=None) -> list:
    """Letzter Stand je Website (mit Erreichbarkeit der letzten 30 Tage in Prozent)."""
    cur.execute("""SELECT w.domain, w.kunden_id, w.geprueft_am, w.ok, w.seite_ok, w.api_ok, w.http, w.ms, w.cert_tage, w.fehler, w.seit,
                          (SELECT round(100.0 * sum(t.ok) / nullif(sum(t.geprueft), 0), 2) FROM website_wacht_tag t WHERE t.domain = w.domain AND t.tag > current_date - 30) AS prozent
                   FROM website_wacht w WHERE (%s::uuid IS NULL OR w.kunden_id = %s::uuid) ORDER BY w.domain""", (kid, kid))
    return [{"domain": r["domain"], "kunden_id": str(r["kunden_id"]), "geprueft_am": r["geprueft_am"], "ok": r["ok"], "seite_ok": r["seite_ok"], "api_ok": r["api_ok"], "http": r["http"],
             "ms": r["ms"], "cert_tage": r["cert_tage"], "fehler": r["fehler"] or "", "seit": r["seit"], "prozent": float(r["prozent"]) if r["prozent"] is not None else None}
            for r in cur.fetchall()]


def erreichbarkeit(cur, kid, von, bis):
    """Erreichbarkeit aller Websites eines Kunden im Zeitraum in Prozent (None, wenn nicht gemessen)."""
    cur.execute("""SELECT sum(t.ok) AS ok, sum(t.geprueft) AS n FROM website_wacht_tag t JOIN websites w ON w.domain = t.domain
                   WHERE w.kunden_id = %s AND t.tag >= %s AND t.tag < %s""", (kid, von, bis))
    r = cur.fetchone()
    return round(100.0 * r["ok"] / r["n"], 2) if r and r["n"] else None
