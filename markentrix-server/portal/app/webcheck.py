"""Kurzprüfung der Startseite einer fremden Website (Ampel für die Funnel-Danke-Seite).
Zugriff nur auf öffentliche Internetadressen: Namen werden aufgelöst, private, lokale und reservierte Adressen werden abgelehnt,
verbunden wird direkt mit der geprüften Adresse (kein Nachschlagen nach der Prüfung), Weiterleitungen werden jedes Mal neu geprüft.
Die Ausgabe ist ein Hinweis aus einer automatischen Kurzprüfung, kein Rechtsurteil und keine Gewähr."""
import http.client
import ipaddress
import re
import socket
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

MAX_BYTES = 600_000
GESAMT_SEKUNDEN = 8.0
WEITERLEITUNGEN = 4


class Abbruch(Exception):
    pass


def _aufloesen(host: str, port: int) -> str:
    """Gibt eine öffentliche IP-Adresse für den Host zurück oder wirft Abbruch."""
    try:
        adressen = {a[4][0] for a in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
    except OSError:
        raise Abbruch("Der Name der Website lässt sich nicht auflösen.")
    if not adressen:
        raise Abbruch("Der Name der Website lässt sich nicht auflösen.")
    for a in adressen:
        if not ipaddress.ip_address(a).is_global:
            raise Abbruch("Diese Adresse ist nicht öffentlich erreichbar.")
    return sorted(adressen)[0]


class _Http(http.client.HTTPConnection):
    def __init__(self, host, port, ip, timeout):
        super().__init__(host, port, timeout=timeout)
        self._ip = ip

    def connect(self):
        self.sock = socket.create_connection((self._ip, self.port), self.timeout)


class _Https(http.client.HTTPSConnection):
    def __init__(self, host, port, ip, timeout):
        super().__init__(host, port, timeout=timeout)
        self._ip = ip

    def connect(self):
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)   # type: ignore[attr-defined]


def normalisieren(eingabe: str) -> str:
    u = (eingabe or "").strip()
    if not u or len(u) > 300 or re.search(r"\s", u):
        raise Abbruch("Die Adresse sieht nicht wie eine Website aus.")
    if "//" not in u:
        u = "https://" + u
    p = urlparse(u)
    if p.scheme not in ("http", "https") or not p.hostname or "." not in p.hostname:
        raise Abbruch("Die Adresse sieht nicht wie eine Website aus.")
    if p.port not in (None, 80, 443) or p.username or p.password:
        raise Abbruch("Diese Adresse lässt sich nicht prüfen.")
    return u


def holen(url: str) -> tuple[str, str, int, str]:
    """Gibt (endgültige Adresse, HTML, Millisekunden, Meldung) zurück. Wirft Abbruch."""
    start = time.monotonic()
    url = normalisieren(url)
    for _ in range(WEITERLEITUNGEN + 1):
        rest = GESAMT_SEKUNDEN - (time.monotonic() - start)
        if rest <= 0.5:
            raise Abbruch("Die Website hat zu lange gebraucht.")
        p = urlparse(url)
        port = p.port or (443 if p.scheme == "https" else 80)
        ip = _aufloesen(p.hostname, port)
        conn = (_Https if p.scheme == "https" else _Http)(p.hostname, port, ip, min(5.0, rest))
        try:
            conn.request("GET", (p.path or "/") + ("?" + p.query if p.query else ""), headers={"Host": p.netloc, "User-Agent": "Mozilla/5.0 (kompatibel; Markentrix-Kurzpruefung)", "Accept": "text/html"})
            r = conn.getresponse()
            if r.status in (301, 302, 303, 307, 308) and r.getheader("Location"):
                url = normalisieren(urljoin(url, r.getheader("Location")))
                continue
            if r.status >= 400:
                raise Abbruch(f"Die Website antwortet mit einem Fehler (Status {r.status}).")
            roh = r.read(MAX_BYTES)
            ms = int((time.monotonic() - start) * 1000)
            typ = (r.getheader("Content-Type") or "").lower()
            if "html" not in typ and b"<html" not in roh[:2000].lower():
                raise Abbruch("Unter dieser Adresse liegt keine normale Webseite.")
            return url, roh.decode(r.headers.get_content_charset() or "utf-8", "replace"), ms, ""
        except Abbruch:
            raise
        except Exception:   # noqa: BLE001 - Verbindung, Zertifikat, Zeitüberschreitung
            raise Abbruch("Die Website ließ sich nicht abrufen.")
        finally:
            conn.close()
    raise Abbruch("Die Website leitet zu oft weiter.")


class _Seite(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titel = ""
        self._in_titel = False
        self.viewport = False
        self.beschreibung = False
        self.links: list[tuple[str, str]] = []
        self._a_href: str | None = None
        self._a_text: list[str] = []
        self.formular = False
        self.tel_mail = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_titel = True
        elif tag == "meta":
            n = (a.get("name") or "").lower()
            if n == "viewport":
                self.viewport = True
            if n == "description" and (a.get("content") or "").strip():
                self.beschreibung = True
        elif tag == "a":
            self._a_href = a.get("href") or ""
            self._a_text = []
            if self._a_href.lower().startswith(("tel:", "mailto:")):
                self.tel_mail = True
        elif tag == "form":
            self.formular = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_titel = False
        elif tag == "a" and self._a_href is not None:
            self.links.append((self._a_href, " ".join(self._a_text)))
            self._a_href = None

    def handle_data(self, d):
        if self._in_titel and len(self.titel) < 300:
            self.titel += d
        if self._a_href is not None and len(self._a_text) < 20:
            self._a_text.append(d.strip())


def analysieren(html: str, url: str, ms: int) -> dict:
    """Wertet die Startseite aus. Rein rechnerisch, ohne Netzzugriff."""
    s = _Seite()
    try:
        s.feed(html[:MAX_BYTES])
    except Exception:   # noqa: BLE001 - kaputtes HTML darf die Prüfung nicht stoppen
        pass

    def link(wort):
        return any(wort in (h + " " + t).lower() for h, t in s.links)
    punkte = []

    def p(code, status, titel, text):
        punkte.append({"code": code, "status": status, "titel": titel, "text": text})
    https = urlparse(url).scheme == "https"
    p("https", "ok" if https else "bad", "Verschlüsselung (https)", "Die Seite wird verschlüsselt ausgeliefert." if https else "Die Seite lädt ohne Verschlüsselung. Browser warnen Besucher davor.")
    p("tempo", "ok" if ms < 1500 else "warn" if ms < 3500 else "bad", "Ladezeit der Startseite", f"Die Startseite hat etwa {ms / 1000:.1f} Sekunden zum Laden gebraucht." + ("" if ms < 1500 else " Langsame Seiten verlieren Besucher."))
    p("handy", "ok" if s.viewport else "bad", "Handy-Ansicht", "Die Seite ist für das Handy angepasst." if s.viewport else "Es ist keine Handy-Anpassung erkennbar. Die meisten Besucher kommen heute mit dem Handy.")
    t = s.titel.strip()
    p("titel", "ok" if len(t) >= 10 else "warn", "Seitentitel", "Die Seite hat einen aussagekräftigen Titel." if len(t) >= 10 else "Der Titel fehlt oder ist sehr kurz. Er erscheint bei Google.")
    p("beschreibung", "ok" if s.beschreibung else "warn", "Beschreibung für Google", "Eine Beschreibung ist hinterlegt." if s.beschreibung else "Es fehlt eine Beschreibung, die bei Google unter dem Titel steht.")
    kontakt = s.tel_mail or s.formular
    p("kontakt", "ok" if kontakt else "bad", "Kontaktmöglichkeit", "Telefon, E-Mail oder Formular sind auf der Startseite zu finden." if kontakt else "Auf der Startseite ist keine direkte Kontaktmöglichkeit zu erkennen. So gehen Anfragen verloren.")
    imp, dsv = link("impressum"), link("datenschutz")
    p("pflicht", "ok" if imp and dsv else "warn", "Links zu Impressum und Datenschutz", "Beide Links wurden gefunden." if imp and dsv else "Mindestens einer der Links „Impressum“ oder „Datenschutz“ wurde auf der Startseite nicht gefunden.")
    wert = {"ok": 1.0, "warn": 0.5, "bad": 0.0}
    score = round(100 * sum(wert[x["status"]] for x in punkte) / len(punkte))
    return {"score": score, "ampel": "gruen" if score >= 80 else "gelb" if score >= 50 else "rot", "punkte": punkte, "adresse": url,
            "hinweis": "Automatische Kurzprüfung der Startseite. Kein Rechtsurteil und keine Gewähr."}


def pruefen(eingabe: str) -> dict:
    """Gibt immer ein Ergebnis zurück. Bei Fehlern: {'fehler': Text}."""
    try:
        url, html, ms, _ = holen(eingabe)
    except Abbruch as e:
        return {"fehler": str(e)}
    return analysieren(html, url, ms)
