#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüft public/ auf typische Fehler. Aufruf: python3 build/check.py

Geprüft werden: Links und Anker, Überschriften, Titel und Beschreibungen, Canonical,
Bilder, Inline-Code (wegen der Sicherheitsrichtlinie), strukturierte Daten, Sitemap, Weiterleitungen.
Endet mit Exit-Code 1, wenn etwas auffällt.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import REDIRECTS, DOMAIN  # noqa: E402

PUBLIC = Path(__file__).resolve().parent.parent / "public"
errors, warnings = [], []


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.canonical = None
        self.links = []   # (attr, url)
        self.ids = set()
        self.imgs = []
        self.inline_style = 0
        self.inline_script = 0
        self.jsonld = []
        self._script = None
        self._buf = ""
        self.headings = []
        self._h = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if "style" in a:
            self.inline_style += 1
        if any(k.startswith("on") for k in a):
            self.inline_script += 1
        if tag == "h1":
            self.h1 += 1
        if tag in ("h1", "h2", "h3"):
            self._h = [tag, ""]
        if tag == "title":
            self._in_title = True
        if tag == "meta" and a.get("name"):
            self.meta[a["name"]] = a.get("content", "")
        if tag == "meta" and a.get("property"):
            self.meta[a["property"]] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "link" and a.get("href"):
            self.links.append(("href", a["href"]))
        if tag == "a" and a.get("href"):
            self.links.append(("href", a["href"]))
        if tag == "img":
            self.imgs.append(a)
            if a.get("src"):
                self.links.append(("src", a["src"]))
        if tag == "script":
            if a.get("src"):
                self.links.append(("src", a["src"]))
            elif a.get("type") == "application/ld+json":
                self._script = "ld"
                self._buf = ""
            else:
                self.inline_script += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._script == "ld":
            try:
                self.jsonld.append(json.loads(self._buf))
            except json.JSONDecodeError as e:
                errors.append(f"JSON-LD ungültig: {e}")
            self._script = None
        if self._h and tag == self._h[0]:
            self.headings.append((self._h[0], self._h[1].strip()))
            self._h = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._script == "ld":
            self._buf += data
        if self._h:
            self._h[1] += data


def page_files():
    return sorted(PUBLIC.rglob("*.html"))


def url_for(path):
    rel = path.relative_to(PUBLIC).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def resolve(url):
    """Interne URL -> Datei in public/ oder None."""
    p = PUBLIC / url.lstrip("/")
    if url.endswith("/") or url == "":
        p = PUBLIC / url.lstrip("/") / "index.html"
    return p if p.is_file() else None


pages = {}
for f in page_files():
    parser = Page()
    parser.feed(f.read_text(encoding="utf-8"))
    pages[url_for(f)] = (f, parser)

titles, descs = {}, {}
for url, (f, p) in pages.items():
    where = url
    noindex = "noindex" in p.meta.get("robots", "")
    if p.h1 != 1:
        errors.append(f"{where}: {p.h1} Hauptüberschriften statt 1")
    prev = 0
    for tag, _ in p.headings:
        lvl = int(tag[1])
        if lvl > prev + 1 and prev:
            errors.append(f"{where}: Überschriftenebene springt von h{prev} auf h{lvl}")
        prev = lvl
    t = p.title.strip()
    d = p.meta.get("description", "")
    if not t:
        errors.append(f"{where}: Titel fehlt")
    if not d:
        errors.append(f"{where}: Beschreibung fehlt")
    if not noindex:
        if t in titles:
            errors.append(f"{where}: Titel doppelt mit {titles[t]}")
        if d in descs:
            errors.append(f"{where}: Beschreibung doppelt mit {descs[d]}")
        titles[t], descs[d] = where, where
        exp = DOMAIN + (url if url != "/" else "/")
        if p.canonical != exp:
            errors.append(f"{where}: canonical {p.canonical} statt {exp}")
        for k in ("og:title", "og:description", "og:image", "og:url"):
            if not p.meta.get(k):
                errors.append(f"{where}: {k} fehlt")
        if len(t) > 66:
            warnings.append(f"{where}: Titel mit {len(t)} Zeichen")
        if len(d) > 165:
            warnings.append(f"{where}: Beschreibung mit {len(d)} Zeichen")
    if p.inline_style:
        errors.append(f"{where}: {p.inline_style} Inline-Styles (verstößt gegen die CSP)")
    if p.inline_script:
        errors.append(f"{where}: Inline-Skript oder Event-Handler (verstößt gegen die CSP)")
    for img in p.imgs:
        if "alt" not in img:
            errors.append(f"{where}: Bild ohne alt: {img.get('src')}")
        if not (img.get("width") and img.get("height")):
            warnings.append(f"{where}: Bild ohne Maße: {img.get('src')}")

    # Links
    for attr, href in p.links:
        if re.match(r"^(mailto:|tel:|https?://|data:)", href):
            continue
        pu = urlparse(href)
        target_url = pu.path or url
        if not target_url.startswith("/"):
            errors.append(f"{where}: relativer Link {href}")
            continue
        tf = resolve(target_url)
        if tf is None:
            errors.append(f"{where}: Link ins Leere: {href}")
            continue
        if pu.fragment and tf.suffix == ".html":
            tgt = pages.get(url_for(tf))
            if tgt and pu.fragment not in tgt[1].ids:
                errors.append(f"{where}: Anker fehlt: {href}")

# Sitemap
all_noindex = all("noindex" in p.meta.get("robots", "") for _, (f, p) in pages.items())
sm_file = PUBLIC / "sitemap.xml"
if all_noindex:
    draft = True
    if sm_file.exists():
        errors.append("Entwurfsmodus, aber sitemap.xml vorhanden")
else:
    draft = False
    sm = sm_file.read_text(encoding="utf-8")
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sm))
    for url, (f, p) in pages.items():
        full = DOMAIN + url
        noindex = "noindex" in p.meta.get("robots", "")
        if noindex and full in locs:
            errors.append(f"Sitemap enthält noindex-Seite {full}")
        if not noindex and full not in locs:
            errors.append(f"Sitemap fehlt: {full}")
    for loc in locs:
        if loc.replace(DOMAIN, "") not in pages:
            errors.append(f"Sitemap verweist auf fehlende Seite {loc}")

# Entwurfsdateien müssen zum Modus passen
for name in ("draft.css", "draft.js"):
    exists = (PUBLIC / "assets" / name).exists()
    if draft and not exists:
        errors.append(f"Entwurfsmodus, aber assets/{name} fehlt")
    if not draft and exists:
        errors.append(f"Endversion, aber assets/{name} liegt noch im Ordner")
if draft:
    for url, (f, p) in pages.items():
        if "Markentrix" not in p.meta.get("copyright", ""):
            errors.append(f"{url}: Urheberrechtsvermerk fehlt")
else:
    for f in PUBLIC.rglob("*.html"):
        if "Markentrix" in f.read_text(encoding="utf-8"):
            errors.append(f"Endversion enthält noch 'Markentrix': {f.relative_to(PUBLIC)}")

# Weiterleitungen
for old, new in REDIRECTS:
    if resolve(new) is None:
        errors.append(f"Weiterleitung {old} -> {new}: Ziel fehlt")

rob = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
if draft and "Disallow: /" not in rob:
    errors.append("Entwurfsmodus, aber robots.txt erlaubt Suchmaschinen")
if not draft and "Sitemap:" not in rob:
    errors.append("robots.txt ohne Sitemap")
print("Modus:", "Entwurf (Markentrix)" if draft else "Endversion")

print(f"{len(pages)} Seiten geprüft.")
for w in warnings:
    print("Hinweis:", w)
for e in errors:
    print("FEHLER:", e)
if errors:
    sys.exit(1)
print("Alles in Ordnung.")
