"""Livegang-Check: prüft einen Website-Ordner auf typische Fehler, bevor oder nachdem die Seite online geht."""
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

BILD_MAX = 1_500_000
EXTERN = [("google-analytics.com", "Google Analytics"), ("googletagmanager.com", "Google Tag Manager"), ("fonts.googleapis.com", "Google Fonts"), ("fonts.gstatic.com", "Google Fonts"),
          ("connect.facebook.net", "Facebook-Pixel"), ("youtube.com/embed", "YouTube-Einbettung"), ("maps.googleapis.com", "Google Maps"), ("google.com/maps", "Google Maps")]
BILDER = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self._in_title, self.desc, self.viewport, self.lang = "", False, "", False, False
        self.links, self.refs, self.forms, self.form_api, self.text = [], [], 0, False, []
        self._in_form = 0

    def handle_starttag(self, tag, a):
        a = {k: (v or "") for k, v in a}
        if tag == "html" and a.get("lang"):
            self.lang = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            if a.get("name", "").lower() == "description":
                self.desc = a.get("content", "").strip()
            if a.get("name", "").lower() == "viewport":
                self.viewport = True
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag in ("img", "script", "source", "iframe") and a.get("src"):
            self.refs.append(a["src"])
        elif tag == "link" and a.get("href"):
            self.refs.append(a["href"])
        elif tag == "form":
            self.forms += 1
            self._in_form += 1
            if "/api/" in a.get("action", ""):
                self.form_api = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "form" and self._in_form:
            self._in_form -= 1

    def handle_data(self, d):
        if self._in_title:
            self.title += d
        self.text.append(d)


def _aufloesen(wurzel: Path, seite: Path, ref: str) -> Path | None | bool:
    """Datei, auf die ein interner Verweis zeigt; None = kein interner Verweis (extern/mailto/#), False = Ziel fehlt."""
    ref = ref.strip()
    if not ref or ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "http://", "https://", "//", "sms:", "whatsapp:")):
        return None
    pfad = unquote(urlparse(ref).path)
    if not pfad:
        return None
    basis = wurzel if pfad.startswith("/") else seite.parent
    ziel = (basis / pfad.lstrip("/")).resolve()
    try:
        ziel.relative_to(wurzel.resolve())
    except ValueError:
        return False
    if ziel.is_dir():
        ziel = ziel / "index.html"
    if ziel.is_file():
        return ziel
    if not ziel.suffix and ziel.with_suffix(".html").is_file():
        return ziel.with_suffix(".html")
    return False


def pruefen(wurzel: Path) -> dict:
    wurzel = Path(wurzel)
    punkte = []

    def p(stufe, text, ort=""):
        punkte.append({"stufe": stufe, "text": text, "ort": ort})

    seiten = sorted(f for f in wurzel.rglob("*.htm*") if f.is_file() and not f.is_symlink())[:300]
    if not (wurzel / "index.html").is_file():
        p("fehler", "Es gibt keine index.html im Hauptordner. Die Startseite würde nicht angezeigt.")
    gesehen_extern, tot, grosse = set(), [], []
    impressum = datenschutz = False
    for f in seiten:
        rel = str(f.relative_to(wurzel))
        try:
            roh = f.read_text(errors="replace")
        except OSError:
            continue
        ps = _P()
        try:
            ps.feed(roh)
        except Exception:  # noqa: BLE001
            p("warn", "Die Seite enthält fehlerhaftes HTML.", rel)
            continue
        ist_start = rel == "index.html"
        titel = " ".join(ps.title.split())
        if not titel:
            p("warn", "Seitentitel fehlt (wichtig für Google und Browser-Tab).", rel)
        elif len(titel) > 65:
            p("hinweis", f"Seitentitel ist mit {len(titel)} Zeichen zu lang (Google kürzt ab ca. 60).", rel)
        if not ps.desc and not re.search(r"impressum|datenschutz|agb", rel, re.I):
            p("warn" if ist_start else "hinweis", "Meta-Beschreibung fehlt (Text in der Google-Suche).", rel)
        if ist_start and not ps.viewport:
            p("warn", "Viewport-Angabe fehlt: die Seite wird auf dem Handy nicht richtig skaliert.", rel)
        if ist_start and not ps.lang:
            p("hinweis", "Sprache im html-Tag fehlt (lang=\"de\").", rel)
        if re.search(r"lorem ipsum", roh, re.I):
            p("warn", "Platzhaltertext „Lorem ipsum“ gefunden.", rel)
        if re.search(r"(localhost|127\.0\.0\.1)", roh):
            p("fehler", "Verweis auf localhost/127.0.0.1 gefunden. Das funktioniert nur auf dem eigenen Rechner.", rel)
        if re.search(r"""(?:src|href|action)\s*=\s*["']http://(?!localhost)""", roh, re.I):
            p("warn", "Unverschlüsselter Verweis (http://) auf der Seite: Browser warnen vor gemischten Inhalten.", rel)
        if ps.forms and not ps.form_api and "/api/" not in roh and "mailto:" not in roh and "formspree" not in roh:
            p("warn", "Formular ohne erkennbares Ziel: Anfragen kommen vermutlich nirgends an.", rel)
        for url, name in EXTERN:
            if url in roh:
                gesehen_extern.add(name)
        for l in ps.links:
            low = l.lower()
            if "impressum" in low:
                impressum = True
            if "datenschutz" in low:
                datenschutz = True
            if _aufloesen(wurzel, f, l) is False:
                tot.append((rel, l))
        for r in ps.refs:
            ziel = _aufloesen(wurzel, f, r)
            if ziel is False:
                tot.append((rel, r))
    if not impressum:
        p("fehler", "Kein Link auf ein Impressum gefunden. In Deutschland Pflicht für geschäftliche Seiten.")
    if not datenschutz:
        p("fehler", "Kein Link auf eine Datenschutzerklärung gefunden. Pflicht, sobald Formulare, Statistik oder Einbettungen genutzt werden.")
    for rel, l in tot[:25]:
        p("fehler", f"Toter Verweis: {l[:120]} existiert nicht.", rel)
    if len(tot) > 25:
        p("fehler", f"… und {len(tot) - 25} weitere tote Verweise.")
    for f in wurzel.rglob("*"):
        if f.is_file() and not f.is_symlink() and f.suffix.lower() in BILDER and f.stat().st_size > BILD_MAX:
            grosse.append((str(f.relative_to(wurzel)), f.stat().st_size))
    for rel, gr in sorted(grosse, key=lambda x: -x[1])[:10]:
        p("warn", f"Bild ist {gr / 1048576:.1f} MB groß und macht die Seite langsam. Auf unter 1 MB verkleinern.", rel)
    for name in sorted(gesehen_extern):
        p("hinweis", f"{name} wird geladen: muss in der Datenschutzerklärung stehen" + (" und braucht meist eine Einwilligung." if name in ("Google Analytics", "Google Tag Manager", "Facebook-Pixel") else " (Daten gehen an den Anbieter)."))
    stufen = {x["stufe"] for x in punkte}
    return {"ampel": "rot" if "fehler" in stufen else "gelb" if "warn" in stufen else "gruen", "seiten": len(seiten), "punkte": punkte,
            "anzahl": {s: sum(1 for x in punkte if x["stufe"] == s) for s in ("fehler", "warn", "hinweis")}}
