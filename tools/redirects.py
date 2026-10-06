# -*- coding: utf-8 -*-
"""Erzeugt server/redirects.json: alte Jimdo-URLs -> neue Seiten (301). Aufruf: python3 tools/redirects.py <crawl_dir>"""
import json, re, sys, urllib.parse
d = sys.argv[1]
cat = json.load(open("src/catalog.json"))
prod = {urllib.parse.urlparse(p["src"]).path: f'/produkt-{p["slug"]}.html' for p in cat["products"]}
urls = [l.strip() for l in open(f"{d}/urls.txt") if l.strip()]
RULES = [("ersatzteil", "ersatzteile"), ("rasterplatte", "rasterplatten"), ("rahmenverl", "rahmenverlaengerung"), ("elektro|e-satz|kabelsatz", "elektrosaetze"), ("anh.ngerkupplung|anhaengerkupplung|ahk", "anhaengerkupplung"),
         ("motorradanh", "motorradanhaenger"), ("heckt|motorradtr|lastentr|fahrradtr|bike", "hecktraeger"), ("alufelgen|felgen", "raeder-felgen"), ("frontscheibe", "frontscheibe"), ("klima|dometic", "klimaanlagen"),
         ("robot|rangier", "rangierhilfe"), ("luftf|kompressor|z6|z8|auflast", "luftfederung"), ("st.tz|stuetz|hubst|alu-matic|thule|flat-jack|autolift|hydraulik", "stuetzensysteme"), ("trittstufe|freistufe", "trittstufen"),
         ("garagenhalter", "garagenhalterung"), ("gaswarner|thermomatte|matratze|markise|zubeh", "zubehoer")]
STATIC = {"/impressum/": "/impressum.html", "/about/": "/ueber-uns.html", "/agb/": "/agb.html", "/datenschutz/": "/datenschutz.html", "/widerrufsbelehrung-und-formular/": "/widerruf.html", "/bewertung/": "/bewertungen.html",
          "/infos-zu-versand-und-bezahlmethoden/": "/versand-zahlung.html", "/angebot-anfordern-1/": "/angebot-anfordern.html", "/blog/": "/ratgeber.html", "/sitemap/": "/fahrzeugfinder.html", "/video-galerie/": "/", "/zubehörprogramm/": "/zubehoer.html", "/hecktraeger/": "/hecktraeger.html"}
BLOG = {b["slug"]: b for b in json.load(open("src/content/blog_posts.json"))}
out = {}
for u in urls:
    path = urllib.parse.urlparse(u).path
    key = urllib.parse.unquote(path).lower()
    if path == "/": continue
    if path in prod: out[path] = prod[path]; continue
    if urllib.parse.unquote(path) in STATIC: out[path] = STATIC[urllib.parse.unquote(path)]; continue
    for rx, c in RULES:
        if re.search(rx, key): out[path] = f"/{c}.html"; break
    else: out[path] = "/"
for b in BLOG.values():  # Blog-Beiträge mit Datum
    pass
json.dump(out, open("server/redirects.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "Weiterleitungen;", sum(1 for v in out.values() if v.startswith("/produkt-")), "auf Produktseiten")
