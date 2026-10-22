"""Website-Dienste: die Bausteine hinter Kontaktformular, Terminbuchung und Bewertungen der Kunden-Websites.

Die Website bekommt nie ein Geheimnis. Zugangsdaten liegen verschlüsselt auf dem Server (einstellungen.verschluesseln),
fremde Adressen (SMTP-Server, Kalender) werden nur geholt, wenn sie ins öffentliche Internet zeigen."""
import ipaddress
import json
import re
import secrets
import smtplib
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from zoneinfo import ZoneInfo

from . import config, einstellungen, mailer, zustellung
from .db import tx

TZ = ZoneInfo("Europe/Berlin")
EMAIL = re.compile(r"^[^@\s,;<>\"]+@[^@\s,;<>\"]+\.[^@\s,;<>\"]+$")
ERLAUBTE_PORTS = (25, 465, 587, 2525)

# Voreinstellungen je Anbieter (aus der Domain der E-Mail-Adresse). hinweis = was der Kunde vorher tun muss.
ANBIETER = {
    "gmail": {"name": "Google Mail", "host": "smtp.gmail.com", "port": 587, "sicherung": "starttls",
              "hinweis": "Bei Google brauchst du ein „App-Passwort“: Google-Konto → Sicherheit → Bestätigung in zwei Schritten einschalten → App-Passwörter → neues Passwort erstellen. Das 16-stellige Passwort hier eintragen, nicht dein normales."},
    "gmx": {"name": "GMX", "host": "mail.gmx.net", "port": 587, "sicherung": "starttls",
            "hinweis": "Bei GMX muss „POP3/IMAP/SMTP“ aktiviert sein: GMX-Postfach → Einstellungen → POP3 und IMAP → Zugriff aktivieren."},
    "web.de": {"name": "WEB.DE", "host": "smtp.web.de", "port": 587, "sicherung": "starttls",
               "hinweis": "Bei WEB.DE muss „POP3/IMAP/SMTP“ aktiviert sein: Einstellungen → POP3 und IMAP → Zugriff aktivieren."},
    "t-online": {"name": "Telekom / T-Online", "host": "securesmtp.t-online.de", "port": 465, "sicherung": "ssl",
                 "hinweis": "Bei der Telekom brauchst du ein eigenes „E-Mail-Passwort“ (Kundencenter → E-Mail → Passwort für E-Mail-Programme). Benutzername ist die komplette Adresse."},
    "microsoft": {"name": "Microsoft 365 / Outlook", "host": "smtp.office365.com", "port": 587, "sicherung": "starttls",
                  "hinweis": "Microsoft sperrt den Versand mit Passwort oft. Wenn die Prüfung scheitert, lass den Versand einfach über Markentrix laufen – das funktioniert immer."},
    "ionos": {"name": "IONOS", "host": "smtp.ionos.de", "port": 587, "sicherung": "starttls", "hinweis": "Benutzername ist die komplette Adresse, Passwort wie im Postfach."},
    "strato": {"name": "STRATO", "host": "smtp.strato.de", "port": 465, "sicherung": "ssl", "hinweis": "Benutzername ist die komplette Adresse, Passwort wie im Postfach."},
    "icloud": {"name": "iCloud", "host": "smtp.mail.me.com", "port": 587, "sicherung": "starttls",
               "hinweis": "Bei Apple brauchst du ein „App-spezifisches Passwort“ (appleid.apple.com → Anmeldung und Sicherheit)."},
}
DOMAIN_ZU_ANBIETER = {
    "gmail.com": "gmail", "googlemail.com": "gmail", "gmx.de": "gmx", "gmx.net": "gmx", "gmx.at": "gmx", "gmx.ch": "gmx", "web.de": "web.de",
    "t-online.de": "t-online", "magenta.de": "t-online", "outlook.com": "microsoft", "outlook.de": "microsoft", "hotmail.com": "microsoft",
    "hotmail.de": "microsoft", "live.de": "microsoft", "live.com": "microsoft", "icloud.com": "icloud", "me.com": "icloud",
}


def vorschlag(email: str) -> dict:
    """Passende Server-Einstellungen zur E-Mail-Adresse. Leer, wenn der Anbieter unbekannt ist (eigene Domain)."""
    teile = email.strip().lower().rsplit("@", 1)
    if len(teile) != 2:
        return {}
    key = DOMAIN_ZU_ANBIETER.get(teile[1])
    if not key:
        return {"anbieter": "", "benutzer": email.strip(),
                "hinweis": "Frag deinen E-Mail-Anbieter nach dem „SMTP-Server“. Meist heißt er smtp.%s oder mail.%s, Port 587 (STARTTLS) oder 465 (SSL)." % (teile[1], teile[1])}
    a = ANBIETER[key]
    return {"anbieter": a["name"], "host": a["host"], "port": a["port"], "sicherung": a["sicherung"], "benutzer": email.strip(), "hinweis": a["hinweis"], "schluessel": key}


# ---------------------------------------------------------------- Schutz vor Zugriffen ins eigene Netz
def oeffentlich(host: str) -> bool:
    """Wahr nur, wenn der Name ausschließlich auf öffentliche Adressen zeigt (kein Zugriff auf Datenbank, Docker-Netz, Metadaten)."""
    if config.SITE_LOKAL_ERLAUBT:
        return True
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    if not infos:
        return False
    for i in infos:
        ip = ipaddress.ip_address(i[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False
    return True


# ---------------------------------------------------------------- Zeilen und Hilfen
def neue_site_id() -> str:
    return "mk_" + secrets.token_urlsafe(9).replace("-", "a").replace("_", "b")


def zeile(cur, kid) -> dict:
    cur.execute("SELECT * FROM website_dienste WHERE kunden_id=%s", (kid,))
    r = cur.fetchone()
    if r:
        return r
    cur.execute("INSERT INTO website_dienste (kunden_id, site_id) VALUES (%s,%s) RETURNING *", (kid, neue_site_id()))
    return cur.fetchone()


def betrag_lesen(text) -> float | None:
    """Liest Beträge wie „50“, „50 €“, „49,90 EUR“, „1.000,50“. Gibt None zurück, wenn es keine Zahl ist."""
    t = re.sub(r"(?i)eur(o)?|€|\s", "", str(text or ""))
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return v if v == v and v not in (float("inf"), float("-inf")) else None


def preis_zahl(text) -> float | None:
    """Erste Zahl aus einem Preistext: „45 €“, „ab 49,90 €“, „1.200 EUR“. None, wenn keine Zahl darin steht."""
    m = re.search(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?", str(text or ""))
    if not m:
        return None
    t = m.group(0)
    t = t.replace(".", "").replace(",", ".") if "," in t or re.match(r"^\d{1,3}(\.\d{3})+$", t) else t
    try:
        return float(t)
    except ValueError:
        return None


def anzahlung_berechnen(l: dict | None) -> float | None:
    """Anzahlung einer Leistung in Euro (fester Betrag oder Prozent vom Preis). None = keine Anzahlung."""
    if not l or (l.get("anzahlung_art") or "keine") == "keine" or l.get("anzahlung_wert") is None:
        return None
    wert = float(l["anzahlung_wert"])
    if l["anzahlung_art"] == "prozent":
        preis = preis_zahl(l.get("preis"))
        if preis is None:
            return None
        wert = preis * wert / 100
    wert = round(wert + 1e-9, 2)
    return wert if wert >= 1 else None


def zahlungsabsatz(z: dict, betrag) -> str:
    """Textblock für Mails: Anzahlung, PayPal.Me-Link mit Betrag und Absageregel. Leer, wenn keine Anzahlung gilt."""
    if betrag in (None, "", 0):
        return ""
    b = f"{float(betrag):.2f}"
    text = f"\nZur Sicherung des Termins bitten wir um eine Anzahlung von {b.replace('.', ',')} €."
    me = (z.get("pp_me_link") or "").strip().rstrip("/")
    if z.get("pp_aktiv") and me.startswith("https://"):
        text += f"\nSie können bequem per PayPal zahlen: {me}/{b}{z.get('pp_waehrung') or 'EUR'}"
    n = z.get("storno_std", 24)
    if n:
        text += f"\nKostenlose Absage ist bis {n} Stunden vor dem Termin möglich, die Anzahlung wird dann erstattet. Danach ist der volle Betrag zu zahlen."
    if z.get("anz_frist_std"):
        text += f"\nBitte zahlen Sie innerhalb von {z['anz_frist_std']} Stunden, sonst geben wir den Termin wieder frei."
    return text + "\n"


def leistungen_wissen_sync(cur, kid):
    """Hält die Leistungen (Preis, Dauer, Anzahlung) als automatischen Eintrag in der Wissensdatenbank aktuell, damit der Assistent dieselben Zahlen kennt wie die Website."""
    z = zeile(cur, kid)
    cur.execute("SELECT * FROM website_leistungen WHERE kunden_id=%s AND aktiv ORDER BY sort, name", (kid,))
    zeilen = cur.fetchall()
    if not zeilen:
        cur.execute("DELETE FROM wissensbasis WHERE kunden_id=%s AND bereich='leistungen' AND quelle='system'", (kid,))
        return
    teile = []
    for l in zeilen:
        t = f"- {l['name']}"
        if l["preis"]:
            t += f": {l['preis']}"
        t += f", Dauer etwa {l['dauer_min']} Minuten"
        a = anzahlung_berechnen(l)
        if a:
            t += f", Anzahlung {a:.2f}".replace(".", ",") + " €"
        if l["freigabe"]:
            t += " (Termin wird erst nach Bestätigung durch den Betrieb fest)"
        if l["beschreibung"]:
            t += f". {l['beschreibung']}"
        teile.append(t)
    text = "Leistungen und Preise (wird automatisch aus dem Portal erzeugt):\n" + "\n".join(teile)
    if z["storno_std"]:
        text += f"\n\nAbsage kostenlos bis {z['storno_std']} Stunden vor dem Termin, danach ist der volle Betrag zu zahlen."
    cur.execute("""INSERT INTO wissensbasis (kunden_id, bereich, schluessel, wert, quelle, aktiv) VALUES (%s,'leistungen','Leistungen und Preise (automatisch)',%s,'system',true)
                   ON CONFLICT (kunden_id, bereich, schluessel) DO UPDATE SET wert=EXCLUDED.wert""", (kid, text))


def ereignis(kid, art: str, ok: bool, hinweis: str = ""):
    try:
        with tx("system") as cur:
            cur.execute("INSERT INTO website_ereignisse (kunden_id, art, ok, hinweis) VALUES (%s,%s,%s,%s)", (kid, art, ok, hinweis[:300] or None))
            cur.execute("DELETE FROM website_ereignisse WHERE kunden_id=%s AND zeit < now() - interval '90 days'", (kid,))
            cur.execute("DELETE FROM website_termine WHERE kunden_id=%s AND ende < now() - interval '180 days'", (kid,))
            cur.execute("DELETE FROM website_gutscheine WHERE kunden_id=%s AND erstellt_am < now() - interval '400 days'", (kid,))
    except Exception:  # noqa: BLE001 - Protokoll darf nie den eigentlichen Vorgang stören
        pass


def erlaubte_hosts(cur, kid, root: str) -> set:
    hosts = {f"demo.{root}"} if root else set()
    cur.execute("SELECT domain FROM domains WHERE kunden_id=%s AND status<>'gekuendigt'", (kid,))
    ds = [r["domain"] for r in cur.fetchall()]
    cur.execute("SELECT domain FROM websites WHERE kunden_id=%s AND status<>'offline'", (kid,))
    ds += [r["domain"] for r in cur.fetchall()]
    for d in ds:
        d = d.lower().strip()
        hosts.add(d)
        hosts.add(d[4:] if d.startswith("www.") else "www." + d)
    return hosts


# ---------------------------------------------------------------- SMTP des Kunden
def smtp_fehlertext(e: Exception, schluessel: str = "") -> str:
    a = ANBIETER.get(schluessel, {})
    extra = (" " + a["hinweis"]) if a.get("hinweis") else ""
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return "Der Anbieter hat Benutzername oder Passwort abgelehnt." + (extra or " Bitte prüfe beides. Viele Anbieter verlangen ein eigenes App-Passwort statt des normalen.")
    if isinstance(e, smtplib.SMTPNotSupportedError):
        return "Der Server unterstützt diese Anmeldung nicht. Probiere den anderen Verschlüsselungs-Port (587 mit STARTTLS oder 465 mit SSL)."
    if isinstance(e, (socket.gaierror,)):
        return "Der Server-Name wurde nicht gefunden. Bitte prüfe die Schreibweise (zum Beispiel smtp.gmail.com)."
    if isinstance(e, (socket.timeout, TimeoutError)):
        return "Der Server antwortet nicht. Prüfe Server-Name und Port – oder lass den Versand über Markentrix laufen."
    if isinstance(e, ConnectionRefusedError):
        return "Der Server hat die Verbindung abgelehnt. Prüfe den Port (587 oder 465)."
    if isinstance(e, ssl.SSLError):
        return "Die verschlüsselte Verbindung ist fehlgeschlagen. Probiere den anderen Port: 587 mit STARTTLS oder 465 mit SSL."
    if isinstance(e, smtplib.SMTPSenderRefused):
        return "Der Anbieter erlaubt diese Absender-Adresse nicht. Nimm die Adresse, mit der du dich anmeldest."
    if isinstance(e, smtplib.SMTPRecipientsRefused):
        return "Der Anbieter hat den Empfänger abgelehnt."
    if isinstance(e, (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError)):
        return "Die Verbindung wurde vom Server getrennt. Prüfe Port und Verschlüsselung."
    return "Der Versand ist fehlgeschlagen (" + type(e).__name__ + ")." + extra


def smtp_verbinden(c: dict):
    """Öffnet und meldet an. Gibt die offene Verbindung zurück. Wirft bei jedem Fehler."""
    host, port, modus = c["host"].strip(), int(c["port"]), c.get("sicherung", "starttls")
    if port not in ERLAUBTE_PORTS and not config.SITE_LOKAL_ERLAUBT:
        raise ValueError("Bitte einen üblichen Mail-Port nutzen: 587, 465, 25 oder 2525.")
    if not oeffentlich(host):
        raise ValueError("Dieser Server ist nicht erreichbar oder nicht erlaubt.")
    ctx = ssl.create_default_context()
    s = smtplib.SMTP_SSL(host, port, timeout=15, context=ctx) if modus == "ssl" else smtplib.SMTP(host, port, timeout=15)
    try:
        s.ehlo()
        if modus == "starttls":
            s.starttls(context=ctx)
            s.ehlo()
        if c.get("benutzer"):
            s.login(c["benutzer"], c.get("passwort", ""))
    except Exception:
        try:
            s.close()
        except Exception:  # noqa: BLE001
            pass
        raise
    return s


def smtp_pruefen(c: dict) -> str:
    """Leer = alles gut, sonst der verständliche Fehlertext."""
    key = vorschlag(c.get("absender", "")).get("schluessel", "")
    try:
        s = smtp_verbinden(c)
        s.quit()
        return ""
    except ValueError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001
        return smtp_fehlertext(e, key)


def _nachricht(von: str, von_name: str, an: str, betreff: str, text: str, reply_to: str | None, anhang) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr((von_name, von))
    msg["To"] = an
    msg["Subject"] = betreff
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=von.split("@")[-1])
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    if anhang:
        name, daten, mime = anhang
        mt, st = mime.split("/")
        msg.add_attachment(daten, maintype=mt, subtype=st, filename=name)
    return msg


def kundenmail(kid, an: str, betreff: str, text: str, reply_to: str | None = None, anhang=None, art: str = "mail") -> tuple[bool, str]:
    """Verschickt eine Mail im Namen des Kunden. Erst über sein eigenes Postfach (wenn eingerichtet), sonst oder bei Fehler über Markentrix.
    Gibt (ok, 'eigen'|'markentrix'|Fehlertext) zurück."""
    with tx("system") as cur:
        z = zeile(cur, kid)
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
        firma = (cur.fetchone() or {}).get("firma") or "Website"
    name = (z.get("mail_name") or firma)[:80]
    grund = ""
    if z.get("smtp_enc") and z.get("smtp_absender"):
        try:
            c = json.loads(einstellungen.entschluesseln(z["smtp_enc"]) or "{}")
            s = smtp_verbinden(c)
            with s:
                s.send_message(_nachricht(z["smtp_absender"], name, an, betreff, text, reply_to, anhang))
            zustellung.protokoll(kid, art, an, True)
            return True, "eigen"
        except Exception as e:  # noqa: BLE001
            grund = str(e) if isinstance(e, ValueError) else smtp_fehlertext(e, vorschlag(z["smtp_absender"]).get("schluessel", ""))
            zustellung.protokoll(kid, art, an, False, f"{type(e).__name__}: {e}")
            ereignis(kid, art, False, "Eigenes Postfach fehlgeschlagen, Versand über Markentrix. " + grund)
    ok, fehler = mailer.senden(an, betreff, text, anhang, reply_to=reply_to, von_name=name, kunden_id=kid, art=art)
    return (True, "markentrix") if ok else (False, fehler)


# ---------------------------------------------------------------- Kalender (iCal)
def ical_url_pruefen(url: str) -> str:
    u = url.strip()
    if u.lower().startswith("webcal://"):
        u = "https://" + u[9:]
    p = urllib.parse.urlparse(u)
    if (p.scheme != "https" and not (config.SITE_LOKAL_ERLAUBT and p.scheme == "http")) or not p.hostname or len(u) > 1500:
        raise ValueError("Die Kalender-Adresse muss mit https:// (oder webcal://) beginnen.")
    return u


class _KeineUmleitung(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # Umleitungen folgen wir selbst, damit jedes Ziel geprüft wird
        return None


def ical_laden(url: str) -> str:
    u = ical_url_pruefen(url)
    opener = urllib.request.build_opener(_KeineUmleitung)
    for _ in range(4):
        host = urllib.parse.urlparse(u).hostname or ""
        if not oeffentlich(host):
            raise ValueError("Diese Kalender-Adresse ist nicht erreichbar oder nicht erlaubt.")
        try:
            with opener.open(urllib.request.Request(u, headers={"User-Agent": "Markentrix-Kalender/1.0"}), timeout=10) as r:
                daten = r.read(3_000_001)
            break
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                u = ical_url_pruefen(urllib.parse.urljoin(u, e.headers["Location"]))
                continue
            if e.code in (401, 403, 404):
                raise ValueError("Der Kalender ist unter dieser Adresse nicht abrufbar. Bitte kopiere die „geheime Adresse im iCal-Format“ neu.")
            raise ValueError(f"Der Kalender-Anbieter meldet einen Fehler ({e.code}).")
        except (urllib.error.URLError, OSError):
            raise ValueError("Der Kalender konnte nicht geladen werden. Bitte prüfe die Adresse.")
    else:
        raise ValueError("Die Kalender-Adresse leitet zu oft um.")
    if len(daten) > 3_000_000:
        raise ValueError("Der Kalender ist zu groß. Bitte nutze einen eigenen Kalender nur für Termine.")
    text = daten.decode("utf-8", "replace")
    if "BEGIN:VCALENDAR" not in text:
        raise ValueError("Unter dieser Adresse liegt kein Kalender im iCal-Format.")
    return text


WINDOWS_ZONEN = {"W. Europe Standard Time": "Europe/Berlin", "Central Europe Standard Time": "Europe/Berlin", "Romance Standard Time": "Europe/Berlin",
                 "GMT Standard Time": "Europe/London", "UTC": "UTC", "Eastern Standard Time": "America/New_York", "Pacific Standard Time": "America/Los_Angeles"}
WOCHE = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


def _zone(name: str | None):
    if not name:
        return TZ
    try:
        return ZoneInfo(WINDOWS_ZONEN.get(name, name))
    except Exception:  # noqa: BLE001
        return TZ


def _zeilen(text: str) -> list[str]:
    aus: list[str] = []
    for z in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if z[:1] in (" ", "\t") and aus:
            aus[-1] += z[1:]
        else:
            aus.append(z)
    return aus


def _prop(zeile_: str):
    kopf, _, wert = zeile_.partition(":")
    teile = kopf.split(";")
    params = {}
    for t in teile[1:]:
        k, _, v = t.partition("=")
        params[k.upper()] = v.strip('"')
    return teile[0].upper(), params, wert


def _zeit(wert: str, params: dict):
    """-> (datetime tz-aware, ganztaegig)"""
    w = wert.strip()
    if params.get("VALUE") == "DATE" or (len(w) == 8 and w.isdigit()):
        d = date(int(w[0:4]), int(w[4:6]), int(w[6:8]))
        return datetime(d.year, d.month, d.day, tzinfo=TZ), True
    z = w.endswith("Z")
    w = w.rstrip("Z")
    dt = datetime(int(w[0:4]), int(w[4:6]), int(w[6:8]), int(w[9:11] or 0), int(w[11:13] or 0), int(w[13:15] or 0))
    return dt.replace(tzinfo=timezone.utc if z else _zone(params.get("TZID"))), False


def _dauer(w: str) -> timedelta:
    m = re.match(r"^(-)?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$", w.strip())
    if not m:
        return timedelta(hours=1)
    _, wo, d, h, mi, s = m.groups()
    return timedelta(weeks=int(wo or 0), days=int(d or 0), hours=int(h or 0), minutes=int(mi or 0), seconds=int(s or 0))


def _regel(w: str) -> dict:
    r = {}
    for t in w.split(";"):
        k, _, v = t.partition("=")
        r[k.upper()] = v
    return r


def _passt(r: dict, d: date, start: date) -> bool:
    iv = int(r.get("INTERVAL") or 1)
    f = r.get("FREQ")
    byday = [x for x in (r.get("BYDAY") or "").split(",") if x]
    if f == "DAILY":
        return (d - start).days % iv == 0
    if f == "WEEKLY":
        wochen = ((d - timedelta(days=d.weekday())) - (start - timedelta(days=start.weekday()))).days // 7
        tage = [WOCHE[x[-2:]] for x in byday if x[-2:] in WOCHE] or [start.weekday()]
        return wochen % iv == 0 and d.weekday() in tage
    if f == "MONTHLY":
        if ((d.year - start.year) * 12 + d.month - start.month) % iv:
            return False
        if r.get("BYMONTHDAY"):
            return str(d.day) in r["BYMONTHDAY"].split(",")
        if byday:
            for x in byday:
                if x[-2:] not in WOCHE or WOCHE[x[-2:]] != d.weekday():
                    continue
                n = x[:-2]
                if not n:
                    return True
                n = int(n)
                nr = (d.day - 1) // 7 + 1
                if n > 0 and nr == n:
                    return True
                if n < 0 and (d + timedelta(days=7 * (-n))).month != d.month and (d + timedelta(days=7 * (-n - 1))).month == d.month:
                    return True
            return False
        return d.day == start.day
    if f == "YEARLY":
        return (d.year - start.year) % iv == 0 and d.month == start.month and d.day == start.day
    return False


def ical_belegt(text: str, von: datetime, bis: datetime) -> list[tuple[datetime, datetime]]:
    """Alle belegten Zeiträume (UTC) im Fenster [von, bis). Unterstützt einfache und wiederkehrende Termine."""
    ereignisse: list[dict] = []
    aktuell = None
    for z in _zeilen(text):
        if z == "BEGIN:VEVENT":
            aktuell = {"exdate": []}
        elif z == "END:VEVENT" and aktuell is not None:
            ereignisse.append(aktuell)
            aktuell = None
        elif aktuell is not None and ":" in z:
            try:
                n, p, w = _prop(z)
                if n == "DTSTART":
                    aktuell["start"], aktuell["ganz"] = _zeit(w, p)
                elif n == "DTEND":
                    aktuell["ende"] = _zeit(w, p)[0]
                elif n == "DURATION":
                    aktuell["dauer"] = _dauer(w)
                elif n == "RRULE":
                    aktuell["rrule"] = _regel(w)
                elif n == "EXDATE":
                    for x in w.split(","):
                        aktuell["exdate"].append(_zeit(x, p)[0])
                elif n == "RECURRENCE-ID":
                    aktuell["rid"] = _zeit(w, p)[0]
                elif n == "UID":
                    aktuell["uid"] = w
                elif n == "STATUS" and w.upper() == "CANCELLED":
                    aktuell["abgesagt"] = True
                elif n == "TRANSP" and w.upper() == "TRANSPARENT":
                    aktuell["frei"] = True
            except (ValueError, IndexError):
                continue
    ausnahmen: dict = {}
    for e in ereignisse:
        if e.get("rid") and e.get("uid"):
            ausnahmen.setdefault(e["uid"], []).append(e["rid"])
    belegt: list[tuple[datetime, datetime]] = []
    for e in ereignisse:
        if e.get("abgesagt") or e.get("frei") or "start" not in e:
            continue
        s = e["start"]
        if "ende" in e:
            dauer = e["ende"] - s
        elif "dauer" in e:
            dauer = e["dauer"]
        else:
            dauer = timedelta(days=1) if e.get("ganz") else timedelta(0)
        if dauer <= timedelta(0):
            dauer = timedelta(minutes=1) if not e.get("ganz") else timedelta(days=1)
        r = e.get("rrule")
        if not r or e.get("rid"):
            if s + dauer > von and s < bis:
                belegt.append((s.astimezone(timezone.utc), (s + dauer).astimezone(timezone.utc)))
            continue
        until = None
        if r.get("UNTIL"):
            try:
                until = _zeit(r["UNTIL"], {})[0]
            except (ValueError, IndexError):
                until = None
        anzahl = int(r["COUNT"]) if r.get("COUNT", "").isdigit() else None
        tz = s.tzinfo
        start_tag = s.astimezone(tz).date()
        ausgeschlossen = {x.astimezone(timezone.utc) for x in e["exdate"]} | {x.astimezone(timezone.utc) for x in ausnahmen.get(e.get("uid"), [])}
        ende_tag = (bis + timedelta(days=1)).astimezone(tz).date()
        d, n = start_tag, 0
        while d <= ende_tag and (d - start_tag).days <= 9000:
            if _passt(r, d, start_tag):
                occ = datetime(d.year, d.month, d.day, s.hour, s.minute, s.second, tzinfo=tz)
                n += 1
                if anzahl is not None and n > anzahl:
                    break
                if until and occ > until:
                    break
                if occ.astimezone(timezone.utc) not in ausgeschlossen and occ + dauer > von and occ < bis:
                    belegt.append((occ.astimezone(timezone.utc), (occ + dauer).astimezone(timezone.utc)))
            d += timedelta(days=1)
    return belegt


# kleine Zwischenspeicher, damit Besucher den Kalender des Kunden nicht bei jedem Aufruf neu laden
_ical_cache: dict = {}


def ical_belegt_enc(schluessel: str, enc: str, von: datetime, bis: datetime) -> list:
    """Belegte Zeiten aus einer (verschlüsselt gespeicherten) Kalender-Adresse, fünf Minuten zwischengespeichert."""
    c = _ical_cache.get(schluessel)
    if c and time.time() - c[0] < 300 and c[2] == enc:
        text = c[1]
    else:
        text = ical_laden(einstellungen.entschluesseln(enc))
        _ical_cache[schluessel] = (time.time(), text, enc)
    return ical_belegt(text, von, bis)


def kalender_belegt(z: dict, von: datetime, bis: datetime) -> list:
    if not z.get("kal_ical_enc"):
        return []
    return ical_belegt_enc(str(z["kunden_id"]), z["kal_ical_enc"], von, bis)


ZEIT_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def zeiten_liste(z: dict) -> list[str]:
    """Feste Uhrzeiten des Inhabers (z. B. Fahrzeugabgabe um 08:00, 10:00). Leer: Raster aus Beginn, Ende und Dauer."""
    return sorted({x.strip() for x in (z.get("kal_zeiten") or "").split(",") if ZEIT_RE.match(x.strip())})


def reservierungen_verfallen(cur, kid, stunden: int):
    """Unbestätigte Reservierungen geben den Termin nach Ablauf der Haltefrist wieder frei."""
    cur.execute("""UPDATE website_termine SET status='abgesagt' WHERE kunden_id=%s AND status='reserviert' AND erstellt_am < now() - make_interval(hours => %s)
                   RETURNING termin_id""", (kid, stunden))
    ids = [r["termin_id"] for r in cur.fetchall() if r["termin_id"]]
    if ids:
        cur.execute("UPDATE termine SET status='abgesagt' WHERE id = ANY(%s) AND status='geplant'", (ids,))


def ressourcen(cur, z: dict, leistung_id=None, mitarbeiter_id=None) -> list[dict]:
    """Wer kann die Leistung ausführen? Ohne angelegte Mitarbeiter gibt es eine einzige, unbenannte Ressource (der Betrieb selbst)."""
    cur.execute("SELECT * FROM website_mitarbeiter WHERE kunden_id=%s ORDER BY sort, name", (z["kunden_id"],))
    alle_ma = cur.fetchall()
    ms = [m for m in alle_ma if m["aktiv"]]
    allg = {"wochentage": z["kal_wochentage"], "von": z["kal_von"], "bis": z["kal_bis"], "zeiten": zeiten_liste(z)}
    if not alle_ma:
        return [{"id": None, "name": "", "ical_enc": None, **allg}]     # kein Team angelegt: der Betrieb selbst
    if not ms:
        return []                                                       # Team angelegt, aber alle pausiert: nichts buchbar
    cur.execute("SELECT mitarbeiter_id, leistung_id FROM website_mitarbeiter_leistungen WHERE mitarbeiter_id = ANY(%s)", ([m["id"] for m in ms],))
    bietet: dict = {}
    for r in cur.fetchall():
        bietet.setdefault(r["mitarbeiter_id"], set()).add(r["leistung_id"])
    out = []
    for m in ms:
        if mitarbeiter_id and m["id"] != mitarbeiter_id:
            continue
        if leistung_id and bietet.get(m["id"]) and leistung_id not in bietet[m["id"]]:
            continue
        own_z = zeiten_liste({"kal_zeiten": m["zeiten"]})
        out.append({"id": m["id"], "name": m["name"], "ical_enc": m["ical_enc"], "wochentage": m["wochentage"] or allg["wochentage"],
                    "von": m["von"] or allg["von"], "bis": m["bis"] or allg["bis"], "zeiten": own_z or allg["zeiten"]})
    return out


def slotplan(cur, z: dict, mit_ical: bool = True, tage: int | None = None, leistung: dict | None = None, mitarbeiter=None) -> dict:
    """Alle Termine der nächsten Tage je Datum (nur Öffnungstage): {datum: [(Uhrzeit, UTC-Beginn, frei, Mitarbeiter-ID)]}.
    Je Mitarbeiter (oder für den Betrieb) gilt: Vorlauf eingehalten, Tag nicht gesperrt, Tageslimit nicht erreicht, Dauer der Leistung passt vor die nächste
    Buchung, nicht im Kalender belegt. Ohne Wunsch-Mitarbeiter ist ein Termin frei, sobald irgendjemand Zeit hat; die Zuordnung geht an den mit den wenigsten Terminen."""
    jetzt = datetime.now(timezone.utc)
    frueh = jetzt + timedelta(hours=z["kal_vorlauf_std"])
    tage = z["kal_tage"] if tage is None else tage
    ende_ges = jetzt + timedelta(days=tage + 2)
    dauer = timedelta(minutes=(leistung or {}).get("dauer_min") or z["kal_dauer"])
    puffer = timedelta(minutes=(leistung or {}).get("puffer_min") or 0)
    res = ressourcen(cur, z, (leistung or {}).get("id"), mitarbeiter)
    cur.execute("""SELECT mitarbeiter_id, start, ende, puffer_min FROM website_termine WHERE kunden_id=%s AND ende > %s AND start < %s
                   AND (status='gebucht' OR (status='reserviert' AND erstellt_am > now() - make_interval(hours => %s)))""",
                (z["kunden_id"], jetzt - timedelta(days=1), ende_ges, z.get("kal_halte_std") or 72))
    buchungen = cur.fetchall()
    cur.execute("SELECT tag, mitarbeiter_id FROM website_sperrtage WHERE kunden_id=%s AND tag >= %s", (z["kunden_id"], datetime.now(TZ).date()))
    sperr = cur.fetchall()
    heute = datetime.now(TZ).date()
    kap = z.get("kal_kapazitaet") or 0
    allg_fremd: list = []
    if mit_ical:
        try:
            allg_fremd = kalender_belegt(z, jetzt - timedelta(days=1), ende_ges)
        except ValueError:
            allg_fremd = []     # Kalender gerade nicht erreichbar: lieber nur eigene Buchungen berücksichtigen als nichts anzubieten
    zeitplan: dict = {}         # (Tag, Uhrzeit) -> [(Anzahl Termine an dem Tag, Reihenfolge, UTC-Beginn, Mitarbeiter-ID)] der freien Ressourcen
    alle: dict = {}             # (Tag, Uhrzeit) -> UTC-Beginn, auch wenn belegt
    for nr, r in enumerate(res):
        eigene = [(b["start"], b["ende"] + timedelta(minutes=b["puffer_min"] or 0)) for b in buchungen if b["mitarbeiter_id"] in (r["id"], None)]
        fremd = list(allg_fremd)
        if mit_ical and r["ical_enc"]:
            try:
                fremd += ical_belegt_enc("m:" + str(r["id"]), r["ical_enc"], jetzt - timedelta(days=1), ende_ges)
            except ValueError:
                pass
        gesperrt = {s["tag"] for s in sperr if s["mitarbeiter_id"] in (None, r["id"])}
        h1, m1 = map(int, r["von"].split(":"))
        h2, m2 = map(int, r["bis"].split(":"))
        raster = timedelta(minutes=max(10, z["kal_dauer"]))
        for i in range(tage + 1):
            tag = heute + timedelta(days=i)
            if tag.isoweekday() not in r["wochentage"]:
                continue
            anzahl = sum(1 for b0, _ in eigene if b0.astimezone(TZ).date() == tag)
            beginne = []
            if r["zeiten"]:
                for f in r["zeiten"]:
                    hh, mm = map(int, f.split(":"))
                    beginne.append(datetime(tag.year, tag.month, tag.day, hh, mm, tzinfo=TZ))
            else:
                t = datetime(tag.year, tag.month, tag.day, h1, m1, tzinfo=TZ)
                schluss = datetime(tag.year, tag.month, tag.day, h2, m2, tzinfo=TZ)
                while t + dauer <= schluss:
                    beginne.append(t)
                    t += raster
            zu = tag in gesperrt or (kap > 0 and anzahl >= kap)
            for t in beginne:
                u = t.astimezone(timezone.utc)
                schluessel = (tag, t.strftime("%H:%M"))
                alle[schluessel] = u
                ende_slot = u + dauer + puffer
                if not zu and u >= frueh and not any(a < ende_slot and b > u for a, b in eigene + fremd):
                    zeitplan.setdefault(schluessel, []).append((anzahl, nr, u, r["id"]))
    plan: dict = {}
    for (tag, zeit) in sorted(alle):
        frei = sorted(zeitplan.get((tag, zeit), []))
        plan.setdefault(tag, []).append((zeit, alle[(tag, zeit)], bool(frei), frei[0][3] if frei else None))
    return plan


def freie_slots(cur, z: dict, mit_ical: bool = True) -> list[datetime]:
    return [u for slots in slotplan(cur, z, mit_ical).values() for _, u, frei, _ in slots if frei]


def freier_platz(cur, z: dict, start: datetime, leistung: dict | None = None, mitarbeiter=None):
    """(True, Mitarbeiter-ID) wenn der Beginn buchbar ist, sonst None."""
    tag = start.astimezone(TZ).date()
    for _, u, frei, rid in slotplan(cur, z, True, leistung=leistung, mitarbeiter=mitarbeiter).get(tag, []):
        if u == start and frei:
            return True, rid
    return None


def ics(uid: str, start: datetime, ende: datetime, titel: str, ort: str, abgesagt: bool = False) -> bytes:
    f = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
    esc = lambda s: s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", " ")  # noqa: E731
    z = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Markentrix//Website//DE", "METHOD:" + ("CANCEL" if abgesagt else "PUBLISH"), "BEGIN:VEVENT",
         f"UID:{uid}@markentrix.de", f"DTSTAMP:{f(datetime.now(timezone.utc))}", f"DTSTART:{f(start)}", f"DTEND:{f(ende)}",
         f"SUMMARY:{esc(titel)}", f"LOCATION:{esc(ort)}", "STATUS:" + ("CANCELLED" if abgesagt else "CONFIRMED"), "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(z) + "\r\n").encode()


# ---------------------------------------------------------------- Google-Bewertungen
PLACE_ID = re.compile(r"^[A-Za-z0-9_-]{10,200}$")


def places_holen(api_key: str, place_id: str) -> dict:
    """Holt Sterne, Anzahl und die neuesten Bewertungen von Google. Wirft ValueError mit verständlichem Text."""
    if not PLACE_ID.match(place_id):
        raise ValueError("Die Place-ID sieht ungültig aus. Sie beginnt meist mit „ChIJ“.")
    req = urllib.request.Request(
        config.PLACES_BASE_URL + "/v1/places/" + urllib.parse.quote(place_id) + "?languageCode=de",
        headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": "rating,userRatingCount,googleMapsUri,reviews"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read(500_000))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError("Zu dieser Place-ID hat Google keinen Eintrag gefunden.")
        if e.code in (400, 403):
            raise ValueError("Google lehnt die Abfrage ab (Schlüssel oder Places-API bei Markentrix nicht aktiv).")
        raise ValueError(f"Google meldet einen Fehler ({e.code}).")
    except (urllib.error.URLError, OSError, ValueError):
        raise ValueError("Google ist gerade nicht erreichbar.")
    rev = []
    for x in (d.get("reviews") or [])[:5]:
        t = ((x.get("text") or x.get("originalText") or {}).get("text") or "").strip()
        rev.append({"autor": ((x.get("authorAttribution") or {}).get("displayName") or "Google-Nutzer")[:60], "sterne": int(x.get("rating") or 0),
                    "text": t[:400], "wann": (x.get("relativePublishTimeDescription") or "")[:40]})
    return {"sterne": round(float(d.get("rating") or 0), 1), "anzahl": int(d.get("userRatingCount") or 0), "link": d.get("googleMapsUri") or "", "bewertungen": rev}


def bewertungen_fuer(z: dict) -> dict:
    """Was die Website anzeigen darf: Google-Daten (zwischengespeichert, höchstens 12 Stunden alt) oder die manuell eingetragenen Zahlen."""
    schreib = "https://search.google.com/local/writereview?placeid=" + z["bew_place_id"] if z.get("bew_place_id") else (z.get("bew_link") or "")
    cache = z.get("bew_cache")
    if z.get("bew_place_id"):
        alt = z.get("bew_stand") is None or (datetime.now(timezone.utc) - z["bew_stand"]) > timedelta(hours=12)
        if alt:
            with tx("system") as cur:
                key = einstellungen.lesen(cur, "places").get("api_key", "")
            if key:
                try:
                    cache = places_holen(key, z["bew_place_id"])
                    with tx("system") as cur:
                        cur.execute("UPDATE website_dienste SET bew_cache=%s::jsonb, bew_stand=now() WHERE kunden_id=%s", (json.dumps(cache), z["kunden_id"]))
                except ValueError as e:
                    ereignis(z["kunden_id"], "bewertungen", False, str(e))
    if cache:
        return {"sterne": cache["sterne"], "anzahl": cache["anzahl"], "bewertungen": cache["bewertungen"], "schreiben": schreib, "quelle": "google"}
    return {"sterne": float(z["bew_sterne"]) if z.get("bew_sterne") is not None else None, "anzahl": z.get("bew_anzahl"), "bewertungen": [], "schreiben": schreib, "quelle": "manuell"}
