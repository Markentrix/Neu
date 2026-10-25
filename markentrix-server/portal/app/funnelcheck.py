"""Website-Check für Funnel-Leads: prüft die Startseite einer Website (Handy, Tempo, Google, Kontaktwege, Preise, Vertrauen, Rechtliches),
gibt eine Ampel, baut das PDF und verschickt die Ergebnis-Mail.

Sicherheit: Es werden nur öffentliche Adressen abgerufen (auch nach Umleitungen), höchstens 1,5 MB, mit Zeitlimit. Google PageSpeed wird nur gefragt,
wenn es im Admin eingeschaltet ist (dabei geht die Website-Adresse an Google)."""
import http.client
import ipaddress
import json
import logging
import re
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser
from urllib.parse import quote, urlparse

from . import config, einstellungen, mailer, pdf, sitedienste, sperre
from .db import tx

log = logging.getLogger("markentrix.funnelcheck")
GRENZE = 1_500_000
AMPEL_WORT = {"gruen": "Grün", "gelb": "Gelb", "rot": "Rot"}
ZUSAMMENFASSUNG = {"gruen": "Grün: Ihre Website ist technisch ordentlich aufgestellt.",
                   "gelb": "Gelb: eine solide Grundlage, aber an einigen Stellen gehen Anfragen verloren.",
                   "rot": "Rot: Hier gehen Ihnen vermutlich Kunden verloren."}
# Gewicht je Prüfpunkt (Summe 100) und Reihenfolge, in der fehlende Punkte als „wichtigster Punkt“ gelten
GEWICHT = {"handy": 15, "sicher": 15, "tempo": 15, "anrufen": 12, "anfrage": 12, "google": 10, "recht": 7, "preise": 7, "vertrauen": 7}
WICHTIG = ["handy", "sicher", "anrufen", "anfrage", "tempo", "google", "recht", "preise", "vertrauen"]
TERMIN = re.compile(r"termin\s*(online\s*)?(buchen|vereinbaren|wählen|anfragen)|online[\s-]*(termin|buchung|buchen)|terminbuchung|calendly|jetzt buchen|data-mk=\"termin\"", re.I)
# Ohne verschachtelte Wiederholungen (kein Rückverfolgen bei langen Ziffernfolgen); der Text wird vorher ohnehin gekürzt
PREIS = re.compile(r"\d{1,7}(?:[.,]\d{1,3})?\s?(?:€|eur\b|euro\b)|(?:€|eur)\s?\d|preisliste|preise\b", re.I)
TEXT_MAX = 200_000
TAGESGRENZE = 100   # höchstens so viele Ergebnis-Mails in 24 Stunden (Schutz vor Missbrauch des Formulars)
GESAMTFRIST = 20   # Sekunden für den ganzen Abruf (auch bei tröpfchenweise antwortenden Servern)
VERTRAUEN = re.compile(r"bewertung|rezension|kundenstimme|referenz|testimonial|sterne|★|google[\s-]*reviews|das sagen unsere kunden", re.I)


# ---------------------------------------------------------------- Adresse prüfen und sicher abrufen
def normalisieren(text: str | None) -> str | None:
    """Macht aus „www.beispiel.de“ eine vollständige Adresse. None, wenn es keine erlaubte Website-Adresse ist."""
    t = (text or "").strip()
    if not t or len(t) > 300 or any(c.isspace() for c in t):
        return None
    if not re.match(r"^https?://", t, re.I):
        t = "https://" + t
    try:
        u = urlparse(t)
        port = u.port
    except ValueError:
        return None
    host = (u.hostname or "").lower()
    if u.scheme.lower() not in ("http", "https") or not host or u.username or u.password or "." not in host.strip("."):
        return None
    if not config.SITE_LOKAL_ERLAUBT and (host.endswith((".local", ".internal", ".localhost")) or port not in (None, 80, 443)):
        return None
    return u.geturl()


def _erlaubt(url: str) -> bool:
    try:
        u = urlparse(url)
        port = u.port
    except ValueError:
        return False
    if u.scheme not in ("http", "https") or not u.hostname:
        return False
    if not config.SITE_LOKAL_ERLAUBT and port not in (None, 80, 443):
        return False
    return sitedienste.oeffentlich(u.hostname)


class _Umleitung(urllib.request.HTTPRedirectHandler):
    max_redirections = 5

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _erlaubt(newurl):
            raise urllib.error.URLError("Umleitung auf eine nicht erlaubte Adresse")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _gegenstelle_pruefen(sock):
    """Nach dem Verbinden: Ist die tatsächlich erreichte Adresse öffentlich? (Schutz gegen DNS-Tricks zwischen Prüfung und Verbindung)"""
    if config.SITE_LOKAL_ERLAUBT:
        return
    ip = ipaddress.ip_address(sock.getpeername()[0].split("%")[0])
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        sock.close()
        raise urllib.error.URLError("Verbindung zu einer nicht öffentlichen Adresse abgelehnt")


class _HttpSicher(http.client.HTTPConnection):
    def connect(self):
        super().connect()
        _gegenstelle_pruefen(self.sock)


class _HttpsSicher(http.client.HTTPSConnection):
    def connect(self):
        http.client.HTTPConnection.connect(self)   # erst TCP, Gegenstelle prüfen, dann TLS
        _gegenstelle_pruefen(self.sock)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


class _HttpHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_HttpSicher, req)


class _HttpsHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_HttpsSicher, req, context=self._context)


def _oeffner():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _Umleitung(), _HttpHandler(), _HttpsHandler(context=ssl.create_default_context()))


def _lesen(r, t0: float) -> bytes:
    """In Stücken lesen, höchstens GRENZE + 1 Byte und höchstens GESAMTFRIST Sekunden insgesamt."""
    teile, n = [], 0
    while n <= GRENZE:
        if time.time() - t0 > GESAMTFRIST:
            raise TimeoutError("Gesamtfrist überschritten")
        stueck = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
        if not stueck:
            break
        teile.append(stueck)
        n += len(stueck)
    return b"".join(teile)


def abrufen(url: str) -> dict:
    """Ruft die Startseite ab. Gibt {ok, url, status, ms, bytes, html, fehler, zertifikat_fehler} zurück, wirft nie."""
    if not _erlaubt(url):
        return {"ok": False, "url": url, "fehler": "Diese Adresse ist nicht öffentlich erreichbar."}
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14) Markentrix-Website-Check/1", "Accept": "text/html,*/*;q=0.5", "Accept-Language": "de"})
    t0 = time.time()
    try:
        with _oeffner().open(req, timeout=8) as r:
            daten = _lesen(r, t0)
            ms = int((time.time() - t0) * 1000)
            zeichensatz = r.headers.get_content_charset() or "utf-8"
            try:
                html = daten[:GRENZE].decode(zeichensatz, "replace")
            except LookupError:   # unbekannter Zeichensatz in der Kopfzeile
                html = daten[:GRENZE].decode("utf-8", "replace")
            return {"ok": 200 <= r.status < 400, "url": r.geturl(), "status": r.status, "ms": ms, "bytes": len(daten), "zu_gross": len(daten) > GRENZE,
                    "html": html, "fehler": None, "zertifikat_fehler": False}
    except urllib.error.HTTPError as e:
        return {"ok": False, "url": url, "status": e.code, "fehler": f"Die Seite antwortet mit Fehler {e.code}."}
    except ssl.SSLCertVerificationError:
        return {"ok": False, "url": url, "fehler": "Das Sicherheitszertifikat (https) ist ungültig.", "zertifikat_fehler": True}
    except urllib.error.URLError as e:
        grund = e.reason
        while isinstance(grund, urllib.error.URLError):   # eigene Ablehnung beim Verbinden kommt verpackt an
            grund = grund.reason
        if isinstance(grund, ssl.SSLCertVerificationError):
            return {"ok": False, "url": url, "fehler": "Das Sicherheitszertifikat (https) ist ungültig.", "zertifikat_fehler": True}
        return {"ok": False, "url": url, "fehler": "Die Seite ist nicht erreichbar." if not isinstance(grund, str) else grund}
    except (socket.timeout, TimeoutError):
        return {"ok": False, "url": url, "fehler": f"Die Seite hat nicht rechtzeitig geantwortet (über {GESAMTFRIST} Sekunden)."}
    except (OSError, ValueError, LookupError, ssl.SSLError, http.client.HTTPException):
        return {"ok": False, "url": url, "fehler": "Die Seite ist nicht erreichbar."}


def laden(url: str) -> dict:
    """Erst wie angegeben, bei Verbindungsfehlern (nicht bei ungültigem Zertifikat) noch einmal mit http://."""
    a = abrufen(url)
    if not a["ok"] and not a.get("status") and not a.get("zertifikat_fehler") and url.startswith("https://"):
        b = abrufen("http://" + url[len("https://"):])
        if b["ok"]:
            return b
    return a


# ---------------------------------------------------------------- Seite lesen
class _Leser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.desc, self.viewport, self.h1 = "", "", False, False
        self.tel, self.mailto, self.whatsapp, self.form = False, False, False, False
        self.hrefs, self.texte, self._titel, self._skip = [], [], False, 0
        self.termin_attr = False

    def handle_starttag(self, tag, a):
        a = {k: (v or "") for k, v in a}
        if tag == "title":
            self._titel = True
        elif tag in ("script", "style", "noscript"):
            self._skip += 1
        elif tag == "meta":
            n = a.get("name", "").lower()
            if n == "description":
                self.desc = a.get("content", "").strip()
            elif n == "viewport" and "width=device-width" in a.get("content", "").replace(" ", "").lower():
                self.viewport = True
        elif tag == "h1":
            self.h1 = True
        elif tag == "form":
            self.form = True
        elif tag == "a" and a.get("href"):
            h = a["href"].strip()
            self.hrefs.append(h.lower())
            if h.lower().startswith("tel:"):
                self.tel = True
            elif h.lower().startswith("mailto:"):
                self.mailto = True
            elif "wa.me/" in h.lower() or "api.whatsapp.com" in h.lower():
                self.whatsapp = True
        if a.get("data-mk") in ("termin", "kontakt"):
            self.termin_attr = self.termin_attr or a.get("data-mk") == "termin"
            self.form = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._titel = False
        elif tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, d):
        if self._titel:
            self.title += d
        elif not self._skip and d.strip():
            self.texte.append(d.strip())


def _pagespeed(url: str, schluessel: str | None) -> dict | None:
    adr = (f"{config.PAGESPEED_BASE_URL}?url={quote(url, safe='')}&strategy=mobile&locale=de&category=performance&category=seo"
           + (f"&key={quote(schluessel, safe='')}" if schluessel else ""))
    try:
        with urllib.request.urlopen(urllib.request.Request(adr, headers={"Accept": "application/json"}), timeout=60) as r:
            d = json.loads(r.read(3_000_000))
        c, au = d["lighthouseResult"]["categories"], d["lighthouseResult"].get("audits", {})
        lcp = (au.get("largest-contentful-paint") or {}).get("displayValue")
        return {"tempo": c["performance"]["score"], "google": (c.get("seo") or {}).get("score"), "lcp": lcp}
    except Exception as e:  # noqa: BLE001 - PageSpeed ist nur eine Ergänzung, die eigene Messung reicht
        log.info("PageSpeed nicht verfügbar: %s", str(e)[:150])
        return None


def _punkt(pid, titel, status, text, tipp=""):
    return {"id": pid, "titel": titel, "status": status, "text": text, "tipp": tipp if status != "gut" else ""}


def bewerten(seite: dict, ps: dict | None = None) -> dict:
    """Aus dem Abruf (und optional PageSpeed) die Prüfpunkte, Punktzahl und Ampel."""
    if not seite.get("ok"):
        p = [_punkt("erreichbar", "Website erreichbar", "schlecht", seite.get("fehler") or "Die Seite ist nicht erreichbar.",
                    "Wer Sie sucht und die Seite nicht öffnen kann, ruft den nächsten Betrieb an. Das sollte zuerst behoben werden.")]
        return {"erreichbar": False, "score": 0, "ampel": "rot", "punkte": p, "wichtigster_punkt": p[0]["tipp"], "zusammenfassung": ZUSAMMENFASSUNG["rot"]}
    le = _Leser()
    try:
        le.feed(seite.get("html") or "")
    except Exception:  # noqa: BLE001 - kaputtes HTML: mit dem auswerten, was gelesen wurde
        pass
    text = " ".join(le.texte)[:TEXT_MAX]
    roh = (seite.get("html") or "")[:TEXT_MAX]
    hrefs = " ".join(le.hrefs)
    p = []
    sicher = seite["url"].startswith("https://")
    p.append(_punkt("sicher", "Sichere Verbindung (https)", "gut" if sicher else "schlecht",
                    "Die Seite läuft verschlüsselt über https." if sicher else "Die Seite läuft ohne https. Browser zeigen dann „Nicht sicher“ an.",
                    "Ein Zertifikat einrichten und alle Aufrufe auf https umleiten."))
    p.append(_punkt("handy", "Fürs Handy eingerichtet", "gut" if le.viewport else "schlecht",
                    "Die Seite passt sich der Bildschirmbreite an." if le.viewport else "Die Seite ist nicht fürs Handy eingerichtet: Kunden müssen zoomen und schieben.",
                    "Die Seite für Handys umbauen. Die meisten Kunden suchen abends auf dem Handy."))
    if ps and ps.get("tempo") is not None:
        s = ps["tempo"]
        st = "gut" if s >= 0.9 else "mittel" if s >= 0.5 else "schlecht"
        txt = f"Google PageSpeed (Handy): {round(s * 100)} von 100" + (f", Hauptinhalt sichtbar nach {ps['lcp']}" if ps.get("lcp") else "") + "."
    else:
        ms, kb = seite.get("ms") or 0, round((seite.get("bytes") or 0) / 1024)
        st = "gut" if ms < 1200 and not seite.get("zu_gross") else "mittel" if ms < 3000 else "schlecht"
        txt = f"Die Startseite antwortet nach {ms / 1000:.1f} Sekunden ({kb} KB).".replace(".", ",", 1) if ms else f"Die Startseite ist {kb} KB groß."
    p.append(_punkt("tempo", "Ladezeit", st, txt, "Bilder verkleinern und die Seite schlanker bauen. Wer warten muss, ist weg."))
    if ps and ps.get("google") is not None:
        g = ps["google"]
        st = "gut" if g >= 0.9 else "mittel" if g >= 0.7 else "schlecht"
        txt = f"Google-Grundlagen laut PageSpeed: {round(g * 100)} von 100."
    else:
        n = sum([10 <= len(le.title.strip()) <= 70, len(le.desc) >= 50, le.h1])
        st = "gut" if n == 3 else "mittel" if n == 2 else "schlecht"
        fehlt = [x for x, ok in (("ein guter Seitentitel", 10 <= len(le.title.strip()) <= 70), ("eine Beschreibung für Google", len(le.desc) >= 50), ("eine Hauptüberschrift", le.h1)) if not ok]
        txt = "Titel, Beschreibung und Überschrift sind vorhanden." if not fehlt else "Es fehlt " + " und ".join(fehlt) + "."
    p.append(_punkt("google", "Für Google lesbar", st, txt, "Titel und Beschreibung mit Leistung und Ort ergänzen, z. B. „Malerbetrieb in Frankfurt“."))
    p.append(_punkt("anrufen", "Mit einem Tipp anrufen", "gut" if le.tel else "schlecht",
                    "Die Telefonnummer ist als Anruf-Link hinterlegt." if le.tel else "Auf dem Handy kann man nicht direkt aus der Seite anrufen.",
                    "Einen Anruf-Knopf ganz oben einbauen. Viele Kunden wollen sofort anrufen."))
    termin = bool(TERMIN.search(text) or TERMIN.search(roh) or le.termin_attr)
    if termin:
        st, txt = "gut", "Kunden können online einen Termin wählen oder anfragen."
    elif le.form or le.whatsapp:
        st, txt = "mittel", "Es gibt ein Formular oder WhatsApp, aber keine Online-Terminbuchung."
    else:
        st, txt = "schlecht", "Es gibt kein Anfrage- oder Terminformular." + (" Nur eine E-Mail-Adresse." if le.mailto else "")
    p.append(_punkt("anfrage", "Anfrage und Termin online", st, txt, "Ein kurzes Anfrage- oder Terminformular einbauen, das auch abends funktioniert."))
    preis = bool(PREIS.search(text))
    p.append(_punkt("preise", "Preise oder Preisrahmen", "gut" if preis else "schlecht",
                    "Auf der Startseite stehen Preise oder ein Preisrahmen." if preis else "Auf der Startseite stehen keine Preise.",
                    "Einen Preisrahmen nennen („ab … €“). Dann fragen eher die passenden Kunden an."))
    vertrauen = bool(VERTRAUEN.search(text))
    p.append(_punkt("vertrauen", "Bewertungen und Referenzen", "gut" if vertrauen else "mittel",
                    "Bewertungen oder Referenzen sind sichtbar." if vertrauen else "Auf der Startseite sind keine Bewertungen oder Referenzen zu sehen.",
                    "Echte Google-Bewertungen und Fotos eigener Arbeiten zeigen."))
    imp = "impressum" in hrefs or "impressum" in text.lower()
    ds = "datenschutz" in hrefs or "privacy" in hrefs or "datenschutz" in text.lower()
    p.append(_punkt("recht", "Impressum und Datenschutz", "gut" if imp and ds else "schlecht",
                    "Impressum und Datenschutz sind verlinkt." if imp and ds else "Es fehlt ein Link zu " + " und ".join(x for x, ok in (("Impressum", imp), ("Datenschutz", ds)) if not ok) + ".",
                    "Impressum und Datenschutzerklärung von jeder Seite aus verlinken."))
    wert = {"gut": 1, "mittel": 0.5, "schlecht": 0}
    score = round(sum(GEWICHT[x["id"]] * wert[x["status"]] for x in p))
    rot = score < 50 or any(x["id"] in ("handy", "sicher") and x["status"] == "schlecht" for x in p)
    ampel = "rot" if rot else "gelb" if score < 80 else "gruen"
    nach = {x["id"]: x for x in p}
    offen = [nach[i] for i in WICHTIG if nach[i]["status"] == "schlecht"] + [nach[i] for i in WICHTIG if nach[i]["status"] == "mittel"]
    return {"erreichbar": True, "score": score, "ampel": ampel, "punkte": p, "wichtigster_punkt": offen[0]["tipp"] if offen else "",
            "zusammenfassung": ZUSAMMENFASSUNG[ampel]}


def pruefen(website: str, cfg: dict | None = None) -> dict:
    """Kompletter Check einer Adresse. Wirft nie."""
    cfg = cfg or {}
    url = normalisieren(website) or website
    seite = laden(url)
    ps = _pagespeed(seite["url"], cfg.get("pagespeed_key")) if seite.get("ok") and cfg.get("pagespeed") else None
    e = bewerten(seite, ps)
    e.update({"version": 1, "website": seite.get("url") or url, "geprueft_am": date.today().isoformat(), "pagespeed": bool(ps),
              "messung": {"status": seite.get("status"), "ms": seite.get("ms"), "bytes": seite.get("bytes")}})
    return e


def host(url: str | None) -> str:
    try:
        h = urlparse(url or "").hostname or (url or "")
    except ValueError:
        h = url or ""
    return h[4:] if h.startswith("www.") else h


# ---------------------------------------------------------------- PDF
def _ampel_bild(farbe: str):
    from reportlab.graphics.shapes import Circle, Drawing, Rect
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    d = Drawing(36 * mm, 13 * mm)
    d.add(Rect(0, 0, 36 * mm, 13 * mm, rx=6.5 * mm, ry=6.5 * mm, fillColor=colors.HexColor("#1D2026"), strokeColor=None))
    for i, (f, hexf) in enumerate((("rot", "#D2463F"), ("gelb", "#E8A800"), ("gruen", "#1E9E5A"))):
        d.add(Circle((7 + i * 11) * mm, 6.5 * mm, 4 * mm, fillColor=colors.HexColor(hexf if f == farbe else "#3A3E46"), strokeColor=None))
    return d


def _punkt_bild(status: str):
    from reportlab.graphics.shapes import Circle, Drawing
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    d = Drawing(5 * mm, 5 * mm)
    d.add(Circle(2.5 * mm, 2.2 * mm, 1.9 * mm, fillColor=colors.HexColor({"gut": "#1E9E5A", "mittel": "#E8A800"}.get(status, "#D2463F")), strokeColor=None))
    return d


def pdf_bauen(e: dict, firma: dict) -> bytes:
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    gross = ParagraphStyle("gross", parent=pdf.TXT, fontName=pdf.F_FETT, fontSize=13, leading=17)
    fett = ParagraphStyle("fett", parent=pdf.TXT, fontName=pdf.F_FETT)
    try:
        am = date.fromisoformat(e.get("geprueft_am") or "")
    except ValueError:
        am = date.today()
    inhalt = [Paragraph("Ihr Website-Check", pdf.H1), pdf.p(f"{host(e.get('website'))} · geprüft am {pdf.datum(am)}", pdf.KLEIN), Spacer(1, 6 * mm)]
    kopf = Table([[_ampel_bild(e["ampel"]), [Paragraph(pdf.esc(e["zusammenfassung"]), gross), pdf.p(f"Gesamtwert: {e['score']} von 100 Punkten")]]], colWidths=[42 * mm, 128 * mm])
    kopf.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, -1), pdf.HELL), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("LEFTPADDING", (0, 0), (-1, -1), 9)]))
    inhalt += [kopf, Paragraph("Ergebnis im Einzelnen", pdf.H2)]
    zeilen = []
    for x in e["punkte"]:
        zeilen.append([_punkt_bild(x["status"]), Paragraph(pdf.esc(x["titel"]), fett),
                       Paragraph(pdf.esc(x["text"]) + (f"<br/><font color='#6B7390'>Tipp: {pdf.esc(x['tipp'])}</font>" if x.get("tipp") else ""), pdf.TXT)])
    inhalt.append(pdf.tabelle(["", "Prüfpunkt", "Ergebnis"], zeilen, breiten=[9 * mm, 48 * mm, 113 * mm]))
    nach = {x["id"]: x for x in e["punkte"]}
    schritte = [nach[i]["tipp"] for i in WICHTIG if i in nach and nach[i]["status"] == "schlecht"] + [nach[i]["tipp"] for i in WICHTIG if i in nach and nach[i]["status"] == "mittel"]
    if not e.get("erreichbar", True):
        schritte = [e["punkte"][0]["tipp"]]
    if schritte:
        inhalt += [Spacer(1, 4 * mm), pdf.leistungsbox("Ihre nächsten Schritte", schritte[:3])]
    inhalt += [Spacer(1, 5 * mm), pdf.p(f"Sie möchten wissen, was sich bei Ihnen lohnt? Wählen Sie ein kostenloses Erstgespräch (15 Minuten): {config.BASE_URL}/buchen"),
               Spacer(1, 4 * mm),
               pdf.p(f"So haben wir geprüft: automatische Prüfung der Startseite am {pdf.datum(am)}, gemessen von unserem Server aus"
                     + (", Ladezeit und Google-Werte von Google PageSpeed Insights (Handy)" if e.get("pagespeed") else "")
                     + ". Der Check ersetzt keine vollständige Analyse und keine Rechtsberatung.", pdf.KLEIN)]
    return pdf.dokument("Website-Check " + host(e.get("website")), "Website-Check", inhalt, firma)


def dateiname(e: dict) -> str:
    return "Website-Check-" + re.sub(r"[^A-Za-z0-9.-]", "-", host(e.get("website")) or "Website")[:60] + ".pdf"


# ---------------------------------------------------------------- Platzhalter für Mails
class _Fest(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def platzhalter(lead: dict, e: dict | None) -> dict:
    punkte = ""
    if e:
        nach = {x["id"]: x for x in e["punkte"]}
        gut = [x for x in e["punkte"] if x["status"] == "gut"][:1]
        offen = ([nach[i] for i in WICHTIG if i in nach and nach[i]["status"] == "schlecht"] + [nach[i] for i in WICHTIG if i in nach and nach[i]["status"] == "mittel"]
                 + [x for x in e["punkte"] if x["id"] not in GEWICHT and x["status"] != "gut"])[:3]
        punkte = "\n".join([f"- Gut: {x['titel']}" for x in gut] + [f"- Zu verbessern: {x['text']}" for x in offen])
    return _Fest(name=(lead.get("ansprechpartner") or "").strip() or "Sie", firma=lead.get("firma") or "", website=host((e or {}).get("website") or lead.get("website")),
                 ampel=AMPEL_WORT.get((e or {}).get("ampel"), ""), score=(e or {}).get("score", ""), punkte=punkte,
                 wichtigster_punkt=(e or {}).get("wichtigster_punkt") or "eine Website, auf der Kunden Sie sofort anrufen und einen Termin wählen können.",
                 zusammenfassung=(e or {}).get("zusammenfassung", ""), buchen=config.BASE_URL.rstrip("/") + "/buchen")


def fuellen(vorlage: str, werte: dict) -> str:
    try:
        t = vorlage.format_map(werte)
    except (ValueError, IndexError, AttributeError):
        t = vorlage
    return t.replace("Guten Tag Sie,", "Guten Tag,")


# ---------------------------------------------------------------- Ablauf nach der Anmeldung
def ausfuehren(cid: int):
    """Läuft im Hintergrund: prüfen, Ergebnis speichern, Lead aktualisieren, Ergebnis-Mail mit PDF (falls eingeschaltet)."""
    with tx("system") as cur:
        cur.execute("UPDATE lead_checks SET versuche=versuche+1 WHERE id=%s AND status='laeuft' RETURNING lead_id, website, kampagne_id, versuche", (cid,))
        r = cur.fetchone()
        if not r:
            return
        cfg = einstellungen.lesen(cur, "funnel_check") or {}
    try:
        e = pruefen(r["website"], cfg)
    except Exception:  # noqa: BLE001 - wird vom Nachhol-Job erneut versucht
        log.exception("Website-Check %s fehlgeschlagen", cid)
        return
    with tx("system") as cur:
        cur.execute("""UPDATE lead_checks SET status='fertig', score=%s, ampel=%s, ergebnis=%s::jsonb, website=%s WHERE id=%s AND status='laeuft' RETURNING id""",
                    (e["score"], e["ampel"], json.dumps(e, ensure_ascii=False), e["website"][:300], cid))
        if not cur.fetchone():
            return
        cur.execute("UPDATE leads SET score=%s WHERE id=%s", (e["score"], r["lead_id"]))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'automatisch')",
                    (r["lead_id"], f"Website-Check für {host(e['website'])}: {AMPEL_WORT[e['ampel']]} ({e['score']} von 100)"))
    mail_senden(cid)


def mail_wird_verschickt(cur, lead_id) -> bool:
    """Für die Danke-Ansicht: Bekommt dieser Lead die Ergebnis-Mail überhaupt (nicht abgemeldet, nicht gesperrt)?"""
    cur.execute("SELECT email, abgemeldet FROM leads WHERE id=%s", (lead_id,))
    l = cur.fetchone()
    return bool(l and l["email"] and not l["abgemeldet"] and not sperre.treffer(cur, email=l["email"]))


def mail_senden(cid: int) -> bool:
    """Ergebnis-Mail mit PDF, genau einmal je Check (nur mit Einwilligung, nicht nach Abmeldung, nur wenn in der Kampagne eingeschaltet)."""
    with tx("system") as cur:
        cur.execute("""SELECT c.id, c.lead_id, c.ergebnis, k.check_mail, k.check_betreff, k.check_text, l.email, l.ansprechpartner, l.firma, l.website, l.abgemeldet
                       FROM lead_checks c JOIN leads l ON l.id = c.lead_id JOIN lead_kampagnen k ON k.id = c.kampagne_id
                       WHERE c.id=%s AND c.status='fertig' AND c.mail_gesendet_am IS NULL""", (cid,))
        r = cur.fetchone()
        if not r or not r["check_mail"] or not r["email"] or r["abgemeldet"]:
            return False
        cur.execute("SELECT 1 FROM lead_aktivitaeten WHERE lead_id=%s AND art='consent'", (r["lead_id"],))
        if not cur.fetchone():
            return False
        grund = None
        if sperre.treffer(cur, email=r["email"]):
            grund = "Adresse steht auf der Sperrliste"
        else:
            cur.execute("SELECT 1 FROM lead_checks WHERE lead_id=%s AND id<>%s AND mail_gesendet_am > now() - interval '24 hours'", (r["lead_id"], cid))
            if cur.fetchone():
                grund = "an diese Adresse ging in den letzten 24 Stunden schon ein Ergebnis"
            else:
                cur.execute("SELECT count(*) AS n FROM lead_checks WHERE mail_gesendet_am > now() - interval '24 hours'")
                if cur.fetchone()["n"] >= TAGESGRENZE:
                    grund = f"Tagesgrenze von {TAGESGRENZE} Ergebnis-Mails erreicht"
        if grund:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'automatisch')",
                        (r["lead_id"], f"Ergebnis-Mail des Website-Checks nicht verschickt: {grund}"))
            return False
        cur.execute("UPDATE lead_checks SET mail_gesendet_am=now() WHERE id=%s AND mail_gesendet_am IS NULL RETURNING id", (cid,))
        if not cur.fetchone():
            return False
        firma = einstellungen.lesen(cur, "firma") or {}
        from .routes_folgemails import token_fuer
        token = token_fuer(cur, r["lead_id"])
    e = r["ergebnis"]
    werte = platzhalter(r, e)
    try:
        datei = pdf_bauen(e, firma)
    except Exception:  # noqa: BLE001 - ohne PDF keine Mail, Versuch wird im Verlauf vermerkt
        log.exception("PDF für Check %s fehlgeschlagen", cid)
        datei = None
    ok, grund = (False, "PDF konnte nicht erstellt werden.") if datei is None else mailer.funnel_mail(
        r["email"], fuellen(r["check_betreff"], werte), fuellen(r["check_text"], werte), token, (dateiname(e), datei, "application/pdf"))
    with tx("system") as cur:
        if ok:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'mail_gesendet','Ergebnis des Website-Checks mit PDF verschickt','automatisch')", (r["lead_id"],))
        else:
            cur.execute("UPDATE lead_checks SET mail_gesendet_am=NULL, mail_versuche=mail_versuche+1, mail_versucht_am=now() WHERE id=%s", (cid,))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'automatisch')",
                        (r["lead_id"], f"Ergebnis-Mail des Website-Checks nicht verschickt: {grund[:200]}"))
    return ok
