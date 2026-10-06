# -*- coding: utf-8 -*-
"""Statischer Shop-Generator:  python3 src/build.py  ->  site/
Quellen: src/catalog.json (tools/extract.py + tools/normalize.py), src/imagemap.json (tools/fetch_images.py), src/content/*.json"""
import json, os, re, html, datetime, collections, urllib.parse
from data import *

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "site")
U = SITE["url"]; TODAY = datetime.date.today().isoformat(); YEAR = datetime.date.today().year
esc = html.escape
CAT_J = json.load(open(f"{HERE}/catalog.json")); IMAP = json.load(open(f"{HERE}/imagemap.json"))
BLOG = json.load(open(f"{HERE}/content/blog_posts.json")); LEGAL = json.load(open(f"{HERE}/content/legal.json")); REVIEWS = json.load(open(f"{HERE}/content/reviews.json"))
PRODUCTS = CAT_J["products"]; PARTS = CAT_J["parts"]
CAT = {c["slug"]: c for c in CATEGORIES}
PAGES = []  # (datei, priorität)
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍﻿]")

# ---------- Fahrzeug-Stammdaten (spiegelt tools/normalize.py) ----------
BASES = collections.OrderedDict([
 ("fiat-ducato", ("Fiat Ducato", "sevel")), ("citroen-jumper", ("Citroën Jumper", "sevel")), ("peugeot-boxer", ("Peugeot Boxer", "sevel")),
 ("mercedes-sprinter", ("Mercedes-Benz Sprinter", "sprinter")), ("ford-transit", ("Ford Transit", "transit")),
 ("renault-master", ("Renault Master / Opel Movano / Nissan Interstar", "master")), ("iveco-daily", ("Iveco Daily", "daily")),
 ("vw-crafter", ("VW Crafter / LT / MAN TGE", "crafter"))])
SERIES = {
 "sevel": [("zfa280", "ZFA 280/290", "bis 1994"), ("z230", "Typ 230", "1994–2002"), ("z244", "Typ 244", "2002–2006"), ("z250", "Typ 250 / X290", "ab 2006")],
 "sprinter": [("t1n", "T1N (W901–W905)", "1995–2006"), ("ncv3", "NCV3 (W906)", "2006–2018"), ("vs30", "VS30 (W907/W910)", "ab 2018")],
 "transit": [("t-alt", "FT150 / ältere Baujahre", "1986–2000"), ("t-v185", "V184 / V185", "2000–2012"), ("t-v362", "Custom V362", "ab 2012"), ("t-v363", "V363", "ab 2014")],
 "master": [("x70", "Master X70", "1998–2010"), ("x62", "Master X62", "ab 2010")],
 "daily": [("d-alt", "Daily", "bis 2006"), ("d-neu", "Daily", "ab 2006")],
 "crafter": [("c-all", "Crafter / LT / TGE", "alle Baujahre")]}
SERIES_LBL = {s[0]: (s[1], s[2]) for g in SERIES.values() for s in g}
MAKE_NOTE = {
 "fiat-ducato": "Der Ducato ist die Basis der meisten Reisemobile in Europa – entsprechend groß ist unser Sortiment. Er teilt Plattform und Fahrwerk mit Citroën Jumper und Peugeot Boxer.",
 "citroen-jumper": "Der Jumper teilt sich Plattform und Hinterachse mit Fiat Ducato und Peugeot Boxer. Vieles ist baugleich, manches fahrzeugspezifisch – wir prüfen die Passung vor jedem Kauf.",
 "peugeot-boxer": "Der Boxer ist Basis vieler Kastenwagen und Teilintegrierter und mit Ducato und Jumper baugleich. Wir rüsten ihn passgenau nach.",
 "mercedes-sprinter": "Vom T1N bis zum VS30: Beim Sprinter entscheidet nicht die Verkaufsbezeichnung wie 313 oder 316, sondern das Baumuster im Fahrzeugschein.",
 "ford-transit": "Vom Transit FT150 bis zum V363 und Custom V362: Wir rüsten die gängigen Baureihen nach.",
 "renault-master": "Der Renault Master ist baugleich mit Opel Movano und Nissan Interstar – eine Anlage deckt damit alle drei Marken ab.",
 "iveco-daily": "Der Iveco Daily wird häufig als Basis für große Reisemobile genutzt. Wir prüfen die Passung im Einzelfall.",
 "vw-crafter": "VW LT bis 2006, Crafter ab 2006 und MAN TGE: Fragen Sie uns nach Ihrem Modell, wir stellen die passende Lösung zusammen."}

# ---------- Icons ----------
ICONS = {
 "hitch": '<circle cx="12" cy="14" r="4"/><path d="M12 10V3M8 3h8M4 21h16"/>', "rack": '<rect x="3" y="12" width="18" height="4" rx="1"/><path d="M6 12V7h12v5M6 20v-4M18 20v-4"/>',
 "spring": '<path d="M8 3h8M8 7h8M5 11c0-2 14-2 14 0s-14 2-14 4 14 2 14 4"/>', "jack": '<path d="M12 3v14M7 12l5 5 5-5M5 21h14"/>',
 "bike": '<circle cx="6" cy="16" r="3.5"/><circle cx="18" cy="16" r="3.5"/><path d="M6 16l4-8h5l3 8M10 8H7M13 12h5"/>', "wheel": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/>',
 "snow": '<path d="M12 2v20M4.9 7l14.2 10M19.1 7L4.9 17M9 3.5l3 2 3-2M9 20.5l3-2 3 2"/>', "remote": '<rect x="7" y="2" width="10" height="20" rx="3"/><circle cx="12" cy="8" r="2"/><path d="M10 14h4M10 17h4"/>',
 "step": '<path d="M3 20h6v-5h6v-5h6"/><path d="M3 20v1M21 10v11"/>', "frame": '<path d="M3 7h18M3 17h18M7 7v10M17 7v10M3 12h4M17 12h4"/>',
 "plug": '<path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0zM12 18v4"/>', "grid": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
 "box": '<path d="M21 8l-9-5-9 5v8l9 5 9-5zM3 8l9 5 9-5M12 13v8"/>',"wrench": '<path d="M14.7 6.3a4 4 0 0 0 5 5L22 13.6 13.6 22l-2.3-2.3a4 4 0 0 0-5-5L3 12.4 11.4 4z"/>', "tool": '<path d="M14.7 6.3a4 4 0 0 0 5 5L22 13.6 13.6 22l-2.3-2.3a4 4 0 0 0-5-5L3 12.4 11.4 4z"/>',
 "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
 "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 6L2 7"/>', "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
 "check": '<path d="M20 6L9 17l-5-5"/>', "truck": '<path d="M1 3h15v13H1zM16 8h4l3 3v5h-7"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
 "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.3L5.8 21 7 14.2 2 9.3l6.9-1z"/>', "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
 "cart": '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6"/>', "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
 "pin": '<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>', "arrow": '<path d="M5 12h14M13 5l7 7-7 7"/>',
 "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>', "headset": '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/><rect x="2" y="14" width="5" height="6" rx="2"/><rect x="17" y="14" width="5" height="6" rx="2"/>',
 "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5V22h16"/>', "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
 "car": '<path d="M5 17h14M3 13l2-6h14l2 6v4h-3M3 13v4h3"/><circle cx="7.5" cy="17" r="1.5"/><circle cx="16.5" cy="17" r="1.5"/>',
 "chev": '<path d="M6 9l6 6 6-6"/>', "download": '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>', "filter": '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>', "van": '<path d="M2 16V8a2 2 0 0 1 2-2h10l5 5h3v5"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>',
}
def ic(n, cls=""): return f'<svg class="ico {cls}" aria-hidden="true"><use href="#i-{n}"/></svg>'
SPRITE = '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">' + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + "</svg>"
LOGO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="#008C45"/><path d="M8 29h3l2-7h17l5 7h5v5H8z" fill="#fff"/><circle cx="16" cy="35" r="4" fill="#CD212A" stroke="#fff" stroke-width="2"/><circle cx="34" cy="35" r="4" fill="#CD212A" stroke="#fff" stroke-width="2"/><path d="M16 22l2-6h10l2 6" fill="none" stroke="#F4F5F0" stroke-width="2"/></svg>'

# ---------- Hilfsfunktionen ----------
def eur(n):
    if n is None: return ""
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
def short(t, n):
    t = " ".join(t.split())
    if len(t) <= n: return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",–-:|(") + "…"
def jld(*objs): return "".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in objs)
def clean_txt(t): return " ".join(EMOJI.sub("", t).split())
def img_tag(iid, alt, sizes="(max-width:700px) 50vw, 300px", lazy=True, cls="photo"):
    r = IMAP.get(iid)
    if not r: return ""
    h, w, hh = r; W = 720 if w >= hh else round(720 * w / hh); H = round(W * hh / w) if w >= hh else 720
    w3, h3 = (360, round(360 * hh / w)) if w >= hh else (round(360 * w / hh), 360)
    return (f'<img class="{cls}" src="assets/img/p/{h}-360.webp" srcset="assets/img/p/{h}-360.webp {w3}w, assets/img/p/{h}-720.webp {min(w, 720) if w>=hh else round(720*w/hh)}w" sizes="{sizes}" '
            f'width="{w3}" height="{h3}" alt="{esc(alt)}" {"loading=lazy decoding=async" if lazy else "fetchpriority=high"}>')
def img_url(iid, big=True):
    r = IMAP.get(iid); return f'assets/img/p/{r[0]}-{720 if big else 360}.webp' if r else ""

# Produkt-Aufbereitung
for p in PRODUCTS:
    p["url"] = f"produkt-{p['slug']}.html"
    p["imgs"] = []; seen = set()
    for i in p["images"]:
        r = IMAP.get(i)
        if r and r[0] not in seen: seen.add(r[0]); p["imgs"].append(i)
    p["cover"] = p["imgs"][0] if p["imgs"] else None
    p["disp"] = p["low"] if p["low"] else p["price"]
PBY = collections.defaultdict(list)
for p in PRODUCTS: PBY[p["cat"]].append(p)
# Zusätzliche Anfrage-Kategorien (Räder/Frontscheibe) ohne Shop-Artikel
FELGEN = [("borbet-cw5-schwarz-matt", "Borbet CW5 – Schwarz matt"), ("borbet-cw5-schwarz-matt-poliert", "Borbet CW5 – Schwarz matt poliert"),
          ("borbet-cw5-anthrazit", "Borbet CW5 – Mistral Anthrazit glänzend"), ("borbet-cw5-anthrazit-poliert", "Borbet CW5 – Mistral Anthrazit glänzend poliert")]
# Boilerplate-Absätze (kommen auf vielen Produktseiten vor) nur einmal pro Seite im Aufklapper zeigen
FREQ = collections.Counter(t for p in PRODUCTS for _, t in p["body"])
BOILER = {t for t, n in FREQ.items() if n > 6}

# Index für Suche/Fahrzeugfinder (kompakt)
CAT_ORDER = [c["slug"] for c in CATEGORIES]
def idx_row(p):
    return [p["slug"], p["name"], CAT_ORDER.index(p["cat"]), p["disp"] or 0, 1 if p["from"] else 0, IMAP[p["cover"]][0] if p["cover"] else "",
            p["makes"], p["series"], p["coach"][0] if p["coach"] else "", p["coach"][1] if p["coach"] else "", p["old"] or 0]
COACHES = collections.OrderedDict()
for p in sorted(PRODUCTS, key=lambda x: (x["coach"] or ["~", ""])[0].lower()):
    if p["coach"]: COACHES.setdefault(p["coach"][0], []).append(p)
def cslug(b): return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", b.lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss"))).strip("-")
IDX = {"c": [[c["slug"], c["name"]] for c in CATEGORIES],
       "m": [[k, v[0], v[1]] for k, v in BASES.items()], "s": {g: [[s[0], s[1], s[2]] for s in L] for g, L in SERIES.items()},
       "h": [[cslug(b), b, [[p["slug"], p["coach"][1]] for p in L]] for b, L in COACHES.items()],
       "p": [idx_row(p) for p in PRODUCTS]}

# ---------- Seitenrahmen ----------
ORG = {"@context": "https://schema.org", "@type": "AutomotiveBusiness", "@id": U + "/#org", "name": SITE["name"], "url": U + "/",
       "logo": U + "/assets/img/logo-520.webp", "image": [U + "/assets/img/og.jpg"], "telephone": SITE["phone"], "email": SITE["email"], "foundingDate": str(SITE["since"]),
       "description": "Fachhändler und Montagebetrieb für Wohnmobil-Nachrüstung: Anhängerkupplungen, Luftfederung, Stützensysteme, Heckträger, Rangierhilfen.",
       "founder": {"@type": "Person", "name": SITE["owner"]}, "priceRange": "€€", "areaServed": [{"@type": "Country", "name": "Deutschland"}, {"@type": "Country", "name": "Österreich"}],
       "address": {"@type": "PostalAddress", "streetAddress": SITE["street"], "postalCode": SITE["plz"], "addressLocality": SITE["city"], "addressCountry": "DE"},
       "paymentAccepted": "PayPal, Kreditkarte, Überweisung, Rechnung", "currenciesAccepted": "EUR", "openingHours": "Mo-Su 00:00-23:59",
       "contactPoint": {"@type": "ContactPoint", "telephone": SITE["phone"], "contactType": "customer service", "availableLanguage": "German", "areaServed": "DE"},
       "department": [{"@type": "AutoRepair", "name": f"{SITE['name']} {l['city']}", "address": {"@type": "PostalAddress", "postalCode": l["plz"], "addressLocality": l["city"], "addressRegion": l["state"], "addressCountry": "DE"},
                       "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lon"]}, "telephone": SITE["phone"]} for l in LOCATIONS]}
WEBSITE = {"@context": "https://schema.org", "@type": "WebSite", "@id": U + "/#web", "url": U + "/", "name": SITE["name"], "inLanguage": "de-DE", "publisher": {"@id": U + "/#org"},
           "potentialAction": {"@type": "SearchAction", "target": U + "/suche.html?q={search_term_string}", "query-input": "required name=search_term_string"}}

def crumbs(items):
    lis = "".join(f'<li>{("<a href=%s>%s</a>" % (chr(34) + u + chr(34), esc(t))) if u else "<span aria-current=page>%s</span>" % esc(t)}</li>' for t, u in items)
    sc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t, **({"item": f"{U}/{u}"} if u else {})} for i, (t, u) in enumerate(items)]}
    return f'<nav class="crumbs wrap" aria-label="Brotkrumen"><ol>{lis}</ol></nav>', sc
def faq_html(faq):
    h = "".join(f"<details><summary>{esc(q)}</summary><div><p>{esc(a)}</p></div></details>" for q, a in faq)
    return h, {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

NAV_MAIN = [("anhaengerkupplung", "Anhängerkupplung"), ("hecktraeger", "Heckträger"), ("luftfederung", "Luftfederung"), ("stuetzensysteme", "Stützen")]
NAV_MORE = [c for c in CATEGORIES if c["slug"] not in {n[0] for n in NAV_MAIN}]

def write(fname, content, prio=None, index=True):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(content)
    if prio and index: PAGES.append((fname, prio))

def page(fname, title, desc, body, schemas=(), crumb_items=None, og_type="website", noindex=False, prio="0.7", nav_cur=None, mbar="", og_image=None, preload=""):
    canon = f"{U}/{'' if fname == 'index.html' else fname}"
    bc = ""; sch = list(schemas)
    if crumb_items: bc, s = crumbs(crumb_items); sch.append(s)
    if fname == "index.html": sch += [ORG, WEBSITE]
    nav = "".join(f'<li><a href="{s}.html"{" aria-current=page" if s + ".html" == nav_cur else ""}>{n}</a></li>' for s, n in NAV_MAIN)
    more = "".join(f'<li><a href="{c["slug"]}.html">{esc(c["name"])}</a></li>' for c in NAV_MORE)
    ogi = og_image or f"{U}/assets/img/og.jpg"
    html_ = f'''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}"><link rel="alternate" hreflang="de-DE" href="{canon}"><link rel="alternate" hreflang="x-default" href="{canon}">
{'<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">'}
<meta property="og:type" content="{og_type}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canon}"><meta property="og:locale" content="de_DE"><meta property="og:site_name" content="{SITE['name']}"><meta property="og:image" content="{ogi}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#007A3D"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/rubik-latin-f673d8.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="assets/fonts/nunito-sans-latin-fb36cb.woff2" as="font" type="font/woff2" crossorigin>{preload}
<link rel="stylesheet" href="assets/css/fonts.css"><link rel="stylesheet" href="assets/css/style.css">{jld(*sch)}</head>
<body{" class=has-mbar" if mbar else ""}>{SPRITE}<a class="skip" href="#main">Zum Inhalt springen</a>
<div class="topbar"><div class="wrap"><ul><li>{ic("truck")} Versandkostenfrei in Deutschland</li><li>{ic("shield")} EG-Typgenehmigung · EG-Gutachten inklusive</li><li>{ic("star")} {SITE['rating']} / 5 · {SITE['reviews_n']} Kundenstimmen</li></ul>
<span>{ic("phone")} <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a> <span class="t24">· 24 h erreichbar</span></span></div></div>
<header class="header"><div class="tri"></div><div class="wrap"><a class="logo" href="index.html" aria-label="Italia Camper 24 – Startseite"><img class="logo-img" src="assets/img/logo-260.webp" srcset="assets/img/logo-260.webp 260w, assets/img/logo-520.webp 520w" sizes="170px" width="260" height="115" alt="Italia Camper 24"></a>
<form class="search" role="search" action="suche.html">{ic("search")}<label class="sr" for="q">Shop durchsuchen</label><input id="q" name="q" type="search" placeholder="Suchen: Anhängerkupplung Ducato, Luftfederung …" autocomplete="off" aria-controls="suggest"><ul class="suggest" id="suggest"></ul></form>
<div class="hdr-actions"><a class="icon-btn hdr-phone" href="tel:{SITE['phone_href']}" aria-label="Anrufen">{ic("phone")}<span>Beratung</span></a>
<a class="icon-btn" href="warenkorb.html" aria-label="Warenkorb">{ic("cart")}<span class="badge" data-cart-badge data-n="0"></span></a>
<button class="icon-btn menu-btn" id="menuBtn" aria-expanded="false" aria-controls="nav" aria-label="Menü">{ic("menu")}</button></div></div>
<nav class="nav" id="nav" aria-label="Hauptnavigation"><div class="wrap"><ul><li class="finder-link"><a href="fahrzeugfinder.html"{" aria-current=page" if nav_cur == "fahrzeugfinder.html" else ""}>{ic("car")} Fahrzeugfinder</a></li>{nav}
<li class="dd"><details><summary>Weitere Kategorien {ic("chev")}</summary><ul>{more}</ul></details></li><li><a href="ratgeber.html">Ratgeber</a></li><li><a href="montage-service.html">Montage</a></li><li class="nav-cta"><a href="angebot-anfordern.html">Angebot anfordern</a></li></ul></div></nav></header>
{bc}<main id="main">{body}</main>
{footer()}<div class="toast" id="toast" role="status" aria-live="polite"></div>{mbar}
<script src="assets/js/catalog-index.js" defer></script><script src="assets/js/app.js" defer></script></body></html>'''
    write(fname, html_, prio, not noindex)

def footer():
    col = lambda items: "".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t, u in items)
    return f'''<div class="tri thick"></div><footer class="footer"><div class="wrap"><div class="cols">
<div><a class="logo-chip" href="index.html" aria-label="Italia Camper 24"><img src="assets/img/logo-260.webp" width="260" height="115" alt="Italia Camper 24" loading="lazy"></a>
<p style="margin-top:14px">Ihr Spezialist für Wohnmobil-Nachrüstung seit {SITE['since']}. Fahrzeugspezifische Anhängerkupplungen, Luftfederung, Stützen und Träger – mit Montageservice in Bohmte und Diez.</p>
<p>{ic("phone")} <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a><br>{ic("chat")} <a href="https://wa.me/{SITE['wa']}" rel="noopener">WhatsApp</a><br>{ic("mail")} <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
<div class="pay" aria-label="Zahlarten"><span>PayPal</span><span>Visa</span><span>Mastercard</span><span>Lastschrift</span><span>Überweisung</span></div></div>
<div><h3>Sortiment</h3><ul>{col([(c["name"], c["slug"] + ".html") for c in CATEGORIES[:9]])}</ul></div>
<div><h3>Fahrzeuge &amp; Service</h3><ul>{col([("Fahrzeugfinder","fahrzeugfinder.html")]+[(v[0], f"fahrzeug-{k}.html") for k, v in list(BASES.items())[:5]]+[("Wohnmobil-Hersteller","hersteller.html"),("Montage-Service","montage-service.html"),("Versand & Zahlung","versand-zahlung.html"),("Bewertungen","bewertungen.html"),("Ratgeber","ratgeber.html"),("Kontakt","kontakt.html")])}</ul></div>
<div><h3>Rechtliches</h3><ul>{col([("Impressum","impressum.html"),("AGB","agb.html"),("Widerrufsbelehrung","widerruf.html"),("Datenschutz","datenschutz.html"),("Standort Bohmte","standort-bohmte.html"),("Standort Diez","standort-diez.html"),("Über uns","ueber-uns.html")])}</ul></div>
</div><div class="bottom"><span>© {YEAR} {SITE['name']} · {SITE['owner']} · {SITE['street']}, {SITE['plz']} {SITE['city']}</span><span>Alle Preise inkl. gesetzl. MwSt. Versandkostenfrei innerhalb Deutschlands.</span></div></div></footer>'''

# ---------- Bausteine ----------
def stars(): return f'<span class="stars">{ic("star")}{ic("star")}{ic("star")}{ic("star")}{ic("star")} {SITE["rating"]} / 5 · {SITE["reviews_n"]} Bewertungen</span>'
def band(title="Nicht sicher, was zu Ihrem Fahrzeug passt?", btn="Kostenlos beraten lassen"):
    return f'<div class="cta-band"><div class="wrap"><div><h2>{title}</h2><p>Schicken Sie uns ein Foto vom Fahrzeugschein oder vom Heckunterbau – wir prüfen kostenlos und unverbindlich.</p></div><div class="band-btns"><a class="btn btn-lg btn-white" href="angebot-anfordern.html">{btn} {ic("arrow")}</a><a class="btn btn-lg btn-ghost" href="https://wa.me/{SITE["wa"]}" rel="noopener">{ic("chat")} WhatsApp</a></div></div></div>'

def price_html(p, big=False):
    if not p["disp"]: return '<div class="price ask">Preis auf Anfrage</div>'
    old = f' <del>{eur(p["old"])}</del>' if p["old"] else ""
    return f'<div class="price">{"<span class=from>ab</span> " if p["from"] else ""}{eur(p["disp"])}{old}<small>inkl. MwSt., versandkostenfrei</small></div>'

def card(p, i=0):
    simple = p["price"] and not p["variants"] and not p["options"] and not p["montage"]
    iid = p["cover"]; art = img_tag(iid, p["name"]) if iid else f'<div class="noimg">{ic(CAT[p["cat"]]["icon"])}</div>'
    badge = ""
    if p["old"]: badge = '<span class="tag sale">Angebot</span>'
    elif p["coach"]: badge = f'<span class="tag">{esc(p["coach"][0])}</span>'
    elif p["makes"]: badge = f'<span class="tag">{esc(BASES[p["makes"][0]][0].split(" /")[0])}{"" if len(p["makes"]) == 1 else " & Co."}</span>'
    btn = (f'<button class="btn btn-cta btn-block" data-add data-sku="{p["slug"]}" data-name="{esc(p["name"])}" data-price="{p["price"]}" data-img="{esc(img_url(iid, False))}" data-url="{p["url"]}">{ic("cart")} In den Warenkorb</button>'
           if simple else f'<a class="btn btn-out btn-block" href="{p["url"]}">{"Ausführung wählen" if p["price"] else "Angebot ansehen"}</a>')
    q = esc((p["name"] + " " + " ".join(BASES[m][0] for m in p["makes"]) + " " + (p["coach"][0] if p["coach"] else "")).lower())
    return (f'<article class="card" data-q="{q}" data-price="{p["disp"] or ""}" data-i="{i}" data-m="{" ".join(p["makes"])}" data-k="{"coach" if p["coach"] else ("veh" if p["makes"] else "uni")}">'
            f'<div class="art">{badge}{art}</div><div class="body"><h3><a href="{p["url"]}">{esc(p["name"])}</a></h3>{price_html(p)}<div class="foot">{btn}</div></div></article>')

def finder(cls="finder", cta="Passendes Zubehör zeigen", title="Fahrzeugfinder", sub="Wählen Sie Ihr Fahrzeug – wir zeigen nur, was passt."):
    return f'''<div class="{cls}" id="finderbox" data-finder><h2>{ic("car")} {title}</h2><p>{sub}</p>
<div class="tabs" role="tablist"><button type="button" role="tab" aria-selected="true" data-tab="base">Basisfahrzeug</button><button type="button" role="tab" aria-selected="false" data-tab="coach">Wohnmobil-Hersteller</button></div>
<form data-pane="base" novalidate><label for="f-make">Fahrzeugmarke</label><select id="f-make" required><option value="">Marke wählen …</option>{"".join(f'<option value="{k}">{esc(v[0])}</option>' for k, v in BASES.items())}</select>
<label for="f-series">Baureihe / Baujahr</label><select id="f-series" disabled><option value="">Erst Marke wählen …</option></select>
<button class="btn btn-cta btn-block btn-lg" type="submit">{cta}</button></form>
<form data-pane="coach" hidden novalidate><label for="f-brand">Aufbauhersteller</label><select id="f-brand" required><option value="">Hersteller wählen …</option>{"".join(f'<option value="{cslug(b)}">{esc(b)} ({len(L)})</option>' for b, L in COACHES.items())}</select>
<label for="f-model">Modell</label><select id="f-model" disabled><option value="">Erst Hersteller wählen …</option></select>
<button class="btn btn-cta btn-block btn-lg" type="submit">Anhängerkupplung für mein Modell</button></form>
<p class="finder-help">Fahrzeug nicht dabei? <a href="https://wa.me/{SITE['wa']}" rel="noopener">Fahrzeugschein per WhatsApp senden</a> – wir prüfen es kostenlos.</p></div>'''

# ================= Rendering von Fließtext =================
def render_blocks(body, skip_h1=True, limit=60, skip=None):
    out = []; ul = []
    def flush():
        nonlocal ul
        if ul: out.append("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in ul) + "</ul>"); ul = []
    n = 0
    for tag, t in body:
        t = clean_txt(t)
        if not t or (skip and t in skip): continue
        if tag == "li": ul.append(t); continue
        flush()
        if tag == "h1" and skip_h1: continue
        if tag in ("h1", "h2"): out.append(f"<h2>{esc(t)}</h2>")
        elif tag in ("h3", "h4"): out.append(f"<h3>{esc(t)}</h3>")
        else: out.append(f"<p>{esc(t)}</p>")
        n += 1
        if n >= limit: break
    flush(); return "".join(out)

# ================= Produktseite =================
def abbr(n):
    n = re.sub(r"Anhängerkupplung (Wohnmobil )?[Vv]ariabel 12,?5? ?kN( inkl\.)?", lambda m: "AHK 12,5 kN" + (" inkl." if m.group(2) else ""), n)
    n = n.replace("Anhängerkupplung", "AHK").replace("Rahmenverlängerung", "Rahmenverl.").replace("Elektrokabelsatz", "E-Satz").replace("Elektrosatz", "E-Satz")
    return n
TITLES = {}; _seen = collections.Counter()
for _p in PRODUCTS:
    n = _p["name"]; t = f"{n} | Italia Camper 24"
    if len(t) > 62: t = abbr(n) + " | Italia Camper 24"
    if len(t) > 66: t = short(abbr(n), 62)
    _seen[t] += 1
    if _seen[t] > 1: t = short(t, 52 if len(t) > 52 else len(t)).rstrip("…") + f" – {eur(_p['disp']) if _p['disp'] else 'Nr. ' + str(_seen[t])}"
    TITLES[_p["slug"]] = t
_dd = collections.Counter(TITLES.values())
for _p in PRODUCTS:
    if _dd[TITLES[_p["slug"]]] > 1: TITLES[_p["slug"]] = short(TITLES[_p["slug"]], 58) + f" ({_p['slug'][-6:]})"

def veh_labels(p):
    if p["coach"]: return f'Wohnmobil-Hersteller {p["coach"][0]}'
    if not p["makes"]: return "Universell (passend je nach Fahrzeug)"
    return " / ".join(BASES[m][0] for m in p["makes"])

def related(p, n=4):
    pool = [x for x in PRODUCTS if x is not p and x["cover"]]
    if p["coach"]: r = [x for x in pool if x["coach"] and x["coach"][0] == p["coach"][0]]
    elif p["makes"]: r = [x for x in pool if set(x["makes"]) & set(p["makes"]) and x["cat"] != p["cat"]]
    else: r = []
    r += [x for x in pool if x["cat"] == p["cat"] and x not in r]
    if p["coach"]: r += [x for x in pool if x["cat"] != p["cat"] and x not in r][:0]
    return r[:n]

def product_page(p):
    c = CAT[p["cat"]]; name = p["name"]
    # Galerie
    big = lambda i: img_tag(i, name, "(max-width:860px) 100vw, 560px", lazy=False, cls="photo")
    if p["imgs"]:
        main = f'<div class="gallery" id="gmain">{big(p["imgs"][0])}</div>'
        th = ""
        if len(p["imgs"]) > 1:
            th = '<div class="thumbs" aria-label="Weitere Bilder">' + "".join(f'<button type="button" data-big="{img_url(i)}" aria-label="Bild {n+1} anzeigen"{" aria-current=true" if n == 0 else ""}><img src="{img_url(i, False)}" width="76" height="76" alt="{esc(name)} – Bild {n+1}" loading=lazy></button>' for n, i in enumerate(p["imgs"][:6])) + "</div>"
        gal = main + th
    else:
        gal = f'<div class="gallery noimg-g" role="img" aria-label="{esc(name)}">{ic(c["icon"])}</div>'
    # Preis / Kauf
    sku0 = p["slug"]
    cover_u = img_url(p["cover"], False) if p["cover"] else ""
    if p["price"]:
        vsel = ""
        if p["variants"]:
            opts = "".join(f'<option value="{k}" data-price="{v["p"]}"{" selected" if k == 0 else ""}>{esc(v["t"])} – {eur(v["p"])}</option>' for k, v in enumerate(p["variants"]))
            vsel = f'<label for="variant">Ausführung wählen</label><select id="variant" name="variant">{opts}</select>'
        mont = ""
        if p["montage"]:
            m = p["montage"][0]
            vopts = m["variants"] or [{"t": "", "p": m["price"]}]
            mopts = "".join(f'<option value="{k}" data-price="{v["p"]}">{esc(v["t"]) if v["t"] else esc(m["name"])}</option>' for k, v in enumerate(vopts))
            mont = (f'<div class="mont"><label class="chk"><input type="checkbox" id="mont" data-mprice="{m["price"]}"> <span><strong>Montage in unserer Werkstatt dazubuchen</strong> – {eur(m["price"])} Festpreis'
                    f'</span></label><select id="mont-v" aria-label="Standort wählen" hidden>{mopts}</select></div>')
        buy = (f'{vsel}<div class="buyrow"><div class="qty"><button type="button" data-d="-" aria-label="Menge verringern">−</button><input id="qty" value="1" inputmode="numeric" aria-label="Menge"><button type="button" data-d="+" aria-label="Menge erhöhen">+</button></div>'
               f'<button class="btn btn-cta btn-lg" id="buy">{ic("cart")} In den Warenkorb</button></div>{mont}')
        pbox = f'<div class="price" id="pprice">{"<span class=from>ab</span> " if p["from"] and not p["variants"] else ""}{eur(p["price"])}{" <del>" + eur(p["old"]) + "</del>" if p["old"] else ""}</div><small>inkl. gesetzl. MwSt. · versandkostenfrei in Deutschland</small>'
    else:
        vsel = ""; buy = f'<div class="buyrow"><a class="btn btn-cta btn-lg" href="angebot-anfordern.html?produkt={esc(urllib.parse.quote(name))}">Angebot anfordern</a><a class="btn btn-out btn-lg" href="tel:{SITE["phone_href"]}">{ic("phone")} Anrufen</a></div>'
        pbox = '<div class="price ask">Preis auf Anfrage</div><small>Wir erstellen Ihnen ein individuelles Festpreis-Angebot.</small>'
    delivery = p["delivery"] or "2 - 7 Werktage Lieferzeit"
    buybox = (f'<div class="buybox" data-buy data-sku="{sku0}" data-name="{esc(name)}" data-img="{esc(cover_u)}" data-url="{p["url"]}" data-base="{p["price"] or 0}">{pbox}{buy}'
              f'<ul class="meta-list"><li>{ic("truck")} Versandkostenfrei · {esc(delivery.replace(" - ", "–"))}</li><li>{ic("shield")} EG-Typgenehmigung / Gutachten laut Produktbeschreibung</li><li>{ic("wrench")} Montage in Bohmte &amp; Diez möglich</li><li>{ic("chat")} Passt es? <a href="https://wa.me/{SITE["wa"]}?text={urllib.parse.quote("Hallo, passt "+name+" zu meinem Fahrzeug?")}" rel="noopener">Per WhatsApp prüfen lassen</a></li></ul></div>')
    # weitere Ausführungen / Zubehör
    opts_html = ""
    if p["options"]:
        rows = ""
        for k, o in enumerate(p["options"]):
            rows += (f'<tr><td>{esc(o["name"])}</td><td class="r">{eur(o["price"])}</td><td class="r"><button class="btn btn-out btn-sm" data-add data-sku="{p["slug"]}~o{k}" data-name="{esc(o["name"] + " (" + name + ")")}" data-price="{o["price"]}" data-img="{esc(cover_u)}" data-url="{p["url"]}">{ic("cart")} Hinzufügen</button></td></tr>')
        opts_html = f'<section class="pblock"><h2>Weitere Ausführungen &amp; Zubehör</h2><div class="tscroll"><table class="spec opt"><tbody>{rows}</tbody></table></div></section>'
    # Beschreibung
    body_items = [(a, b) for a, b in p["body"] if b not in BOILER and not re.search(r"WhatsApp|Fahrzeugschein senden|^Montage(kosten)?$", b)]
    desc_html = render_blocks(body_items, limit=45)
    boiler_items = [(a, b) for a, b in p["body"] if b in BOILER]
    veh = veh_labels(p)
    intro = f'<p class="lead-p"><strong>{esc(name)}</strong> – {esc(CAT[p["cat"]]["short"].rstrip("."))}. Passend für: {esc(veh)}.{" Preis ab " + eur(p["disp"]) + " inkl. MwSt., versandkostenfrei." if p["disp"] else ""} Montage in Bohmte und Diez nach Terminvereinbarung möglich.</p>'
    more = f'<details><summary>Allgemeine Hinweise zu Auswahl, Anhängelast &amp; Einbau</summary><div>{render_blocks(boiler_items, limit=12)}</div></details>' if boiler_items else ""
    specs = list(p["specs"])
    if p["weight"]: specs.append(["Gewicht", p["weight"]])
    specs.append(["Lieferzeit", delivery.replace(" - ", "–")]); specs.append(["Versand", "kostenfrei innerhalb Deutschlands"])
    specs_html = '<table class="spec"><tbody>' + "".join(f"<tr><th>{esc(a)}</th><td>{esc(b)}</td></tr>" for a, b in specs) + "</tbody></table>"
    # Fahrzeug-Links
    links = []
    if p["coach"]: links.append(f'<a class="chip" href="hersteller-{cslug(p["coach"][0])}.html">Alle {esc(p["coach"][0])}-Modelle</a>')
    for m in p["makes"]:
        links.append(f'<a class="chip" href="fahrzeug-{m}.html">{esc(BASES[m][0].split(" /")[0])}</a>')
        for s in p["series"]:
            if any(s == x[0] for x in SERIES[BASES[m][1]]): links.append(f'<a class="chip" href="fahrzeug-{m}-{s}.html">{esc(BASES[m][0].split(" /")[0])} {esc(SERIES_LBL[s][0])}</a>')
    pass_html = f'<section class="pblock"><h2>Passend für</h2><p>{esc(veh)}</p>{"<div class=chips>" + "".join(dict.fromkeys(links)) + "</div>" if links else ""}<p class="small">Die genaue Passung hängt von Baujahr, Chassis und Aufbau ab. Wir prüfen sie vor jeder Bestellung kostenlos – ein Foto vom Fahrzeugschein oder Heckunterbau per <a href="https://wa.me/{SITE["wa"]}" rel="noopener">WhatsApp</a> genügt.</p></section>'
    faq = list(c["faq"][:2]) + [("Wie lange dauert die Lieferung?", f"Die Lieferzeit beträgt in der Regel {delivery.replace(' - ', '–').replace(' Lieferzeit', '')}. Der Versand innerhalb Deutschlands ist kostenlos."),
                                ("Kann ich das Produkt bei Italia Camper 24 einbauen lassen?", "Ja, in unseren Werkstätten in Bohmte (Niedersachsen) und Diez (Rheinland-Pfalz) nach Terminvereinbarung zum Festpreis.")]
    fh, fs = faq_html(faq)
    rel = related(p)
    relh = f'<section class="soft"><div class="wrap"><h2>Das könnte Sie auch interessieren</h2><div class="grid">{"".join(card(x, i) for i, x in enumerate(rel))}</div></div></section>' if rel else ""
    body = f'''<div class="wrap pdp"><div>{gal}</div><div><p class="eyebrow"><a href="{c["slug"]}.html">{esc(c["name"])}</a>{" · " + esc(p["coach"][0]) if p["coach"] else ""}</p><h1>{esc(name)}</h1>{stars()}{buybox}</div></div>
<div class="wrap pcontent"><section class="pblock">{intro}{desc_html}{more}</section>{opts_html}<section class="pblock"><h2>Technische Daten &amp; Lieferung</h2>{specs_html}</section>{pass_html}<section class="pblock"><h2>Fragen &amp; Antworten</h2>{fh}</section></div>{relh}'''
    # Schema
    ps = {"@context": "https://schema.org", "@type": "Product", "@id": f'{U}/{p["url"]}#product', "name": name, "description": short(p["meta"] or intro, 300), "category": c["name"], "sku": p["slug"],
          "url": f'{U}/{p["url"]}', "brand": {"@type": "Brand", "name": SITE["name"]},
          "image": [f'{U}/{img_url(i)}' for i in p["imgs"][:4]] or [U + "/assets/img/og.jpg"]}
    if p["price"]:
        ship = {"@type": "OfferShippingDetails", "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "EUR"}, "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "DE"},
                "deliveryTime": {"@type": "ShippingDeliveryTime", "handlingTime": {"@type": "QuantitativeValue", "minValue": 0, "maxValue": 1, "unitCode": "DAY"}, "transitTime": {"@type": "QuantitativeValue", "minValue": 2, "maxValue": 7, "unitCode": "DAY"}}}
        ret = {"@type": "MerchantReturnPolicy", "applicableCountry": "DE", "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow", "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail"}
        offer = {"@type": "Offer", "priceCurrency": "EUR", "price": f'{p["price"]:.2f}', "url": f'{U}/{p["url"]}', "availability": "https://schema.org/InStock", "itemCondition": "https://schema.org/NewCondition",
                 "priceValidUntil": f"{YEAR+1}-12-31", "seller": {"@id": U + "/#org"}, "shippingDetails": ship, "hasMerchantReturnPolicy": ret}
        if p["from"] and p["low"] != p["price"]:
            offer = {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": f'{p["low"]:.2f}', "highPrice": f'{max(x for x in [p["price"]] + [v["p"] for v in p["variants"]] + [o["price"] for o in p["options"] if not o.get("extra")]):.2f}',
                     "offerCount": 1 + len(p["variants"]) + len(p["options"]), "availability": "https://schema.org/InStock", "seller": {"@id": U + "/#org"}, "shippingDetails": ship}
        ps["offers"] = offer
    t = TITLES[p["slug"]]
    md = p["meta"] if 70 <= len(p["meta"]) <= 165 else ""
    if md and sum(1 for q in PRODUCTS if q["meta"] == md) > 1: md = ""
    gen = f'{short(name, 80)}{" ab " + eur(p["disp"]) if p["disp"] else ""} – versandkostenfrei, EG-Typgenehmigung, Montage in Bohmte &amp; Diez möglich. Jetzt bei Italia Camper 24.'.replace("&amp;", "&")
    mbar = (f'<div class="mbar"><div class="mprice">{eur(p["price"])}</div><button class="btn btn-cta" id="buy2">In den Warenkorb</button></div>' if p["price"]
            else f'<div class="mbar"><a class="btn btn-cta" href="angebot-anfordern.html">Angebot anfordern</a><a class="btn btn-out" href="tel:{SITE["phone_href"]}">Anrufen</a></div>')
    page(p["url"], t, short(md or gen, 160), body, [ps, fs], [("Startseite", "index.html"), (c["name"], c["slug"] + ".html"), (short(name, 60), None)], og_type="product", prio="0.8", mbar=mbar,
         og_image=(f'{U}/{img_url(p["cover"])}' if p["cover"] else None))

# ================= Kategorie =================
def category_page(c):
    prods = PBY.get(c["slug"], [])
    faq, fs = faq_html(c["faq"]) if c["faq"] else ("", None)
    side = "".join(f'<li><a href="{x["slug"]}.html"{" aria-current=page" if x["slug"] == c["slug"] else ""}>{esc(x["name"])} <span>{len(PBY.get(x["slug"], [])) or ""}</span></a></li>' for x in CATEGORIES)
    items = {"@context": "https://schema.org", "@type": "CollectionPage", "name": c["h1"], "description": c["meta"], "url": f'{U}/{c["slug"]}.html',
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(prods), "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f'{U}/{p["url"]}', "name": p["name"]} for i, p in enumerate(prods[:100])]}}
    filt = ""
    if len(prods) > 12:
        nveh = sum(1 for p in prods if p["makes"]); ncoach = sum(1 for p in prods if p["coach"]); nuni = len(prods) - nveh - ncoach
        chips = [("all", f"Alle ({len(prods)})")] + ([("veh", f"Nach Basisfahrzeug ({nveh})")] if nveh else []) + ([("coach", f"Nach Wohnmobil-Modell ({ncoach})")] if ncoach else []) + ([("uni", f"Universal ({nuni})")] if nuni and nuni != len(prods) else [])
        mk = "".join(f'<option value="{k}">{esc(v[0].split(" /")[0])}</option>' for k, v in BASES.items() if any(k in p["makes"] for p in prods))
        filt = (f'<div class="filterbar"><div class="chips" role="group" aria-label="Filter">{"".join(f"<button type=button class=chip data-k={k}{" aria-pressed=true" if k=="all" else " aria-pressed=false"}>{esc(t)}</button>" for k, t in chips)}</div>'
                f'<div class="frow"><div class="fsearch">{ic("search")}<label class="sr" for="fq">Im Sortiment filtern</label><input id="fq" type="search" placeholder="Modell, z. B. Bürstner Nexxo, Ducato 250 …"></div>'
                + (f'<label class="sr" for="fm">Basisfahrzeug</label><select id="fm"><option value="">Alle Fahrzeuge</option>{mk}</select>' if mk else "") + "</div></div>")
    if c.get("quote"):
        if c["slug"] == "raeder-felgen":
            cards = "".join(f'<article class="card"><div class="art"><img class="photo" src="assets/img/p/{s}-360.webp" srcset="assets/img/p/{s}-360.webp 360w, assets/img/p/{s}-720.webp 720w" sizes="300px" width="360" height="209" alt="{esc(t)}" loading="lazy"></div><div class="body"><h3>{esc(t)}</h3><div class="price ask">Preis auf Anfrage</div><div class="foot"><a class="btn btn-cta btn-block" href="angebot-anfordern.html?produkt={urllib.parse.quote(t)}">Angebot anfordern</a></div></div></article>' for s, t in FELGEN)
            extra = ('<section class="pblock"><h2>Borbet CW5 mit Continental VanContact 4Season</h2><ul class="ticks"><li>Größe 6,5 x 16 Zoll, ET60 / ET68, Lochkreis 5x118 / 5x120 / 5x130</li><li>Traglast bis 1.400 kg pro Rad</li><li>Ganzjahresreifen 235/65 R16C 121R (M+S, 3PMSF), Testsieger bei promobil 10/2020</li><li>Mit TÜV-Gutachten / Teilegutachten, montiert, gewuchtet und fahrbereit geliefert</li></ul></section>')
        else:
            cards = ""; extra = ('<section class="pblock"><h2>Unsere Leistungen</h2><ul class="ticks"><li>Versicherungsabwicklung inklusive</li><li>Vor-Ort-Service im Urlaub – mobiler Service europaweit</li><li>Schnelle Steinschlag-Reparatur ohne Ausbau in 30–60 Minuten</li><li>Austausch in Erstausstatter-Qualität für perfekte Passform</li></ul><p><a class="btn btn-cta btn-lg" href="angebot-anfordern.html?produkt=Frontscheibe">Angebot anfordern</a></p></section>')
        grid = f'<div class="grid three">{cards}</div>' if cards else ""
    elif c["slug"] == "ersatzteile":
        rows = ""
        for k, q in enumerate(PARTS):
            im = img_url(q["img"][0], False) if q["img"] and IMAP.get(q["img"][0]) else ""
            rows += (f'<tr data-q="{esc(q["name"].lower())}"><td class="pimg">{"<img src=" + im + " width=56 height=56 alt= loading=lazy>" if im else ""}</td><td>{esc(q["name"])}</td><td class="r">{eur(q["price"])}</td>'
                     f'<td class="r"><button class="btn btn-out btn-sm" data-add data-sku="ersatzteil-{k}" data-name="{esc(q["name"])}" data-price="{q["price"]}" data-img="{im}" data-url="ersatzteile.html">{ic("cart")}<span class="sr"> In den Warenkorb</span></button></td></tr>')
        grid = f'<div class="filterbar"><div class="fsearch">{ic("search")}<label class="sr" for="fq">Ersatzteile filtern</label><input id="fq" type="search" placeholder="Ersatzteil suchen …"></div></div><div class="tscroll"><table class="spec parts" id="parts"><tbody>{rows}</tbody></table></div>'
        extra = ""
    else:
        grid = f'<div class="grid three" id="prodgrid">{"".join(card(p, i) for i, p in enumerate(prods))}</div><p class="noresult" id="noresult" hidden>Keine Treffer – versuchen Sie einen anderen Suchbegriff oder <a href="angebot-anfordern.html">fragen Sie uns direkt</a>.</p><div class="more-wrap"><button class="btn btn-out btn-lg" id="more" hidden>Mehr Artikel anzeigen</button></div>'
        extra = ""
    toolbar = "" if c.get("quote") or c["slug"] == "ersatzteile" else f'<div class="toolbar"><strong id="count">{len(prods)} Artikel</strong><div><label class="sr" for="sort">Sortieren</label><select id="sort"><option value="">Empfohlen</option><option value="asc">Preis aufsteigend</option><option value="desc">Preis absteigend</option></select></div></div>'
    veh_links = ""
    if c["slug"] in ("anhaengerkupplung", "rahmenverlaengerung", "elektrosaetze", "luftfederung"):
        veh_links = '<div class="notice-box">' + f'{ic("car")} <strong>Schneller zum passenden Produkt:</strong> ' + " · ".join(f'<a href="fahrzeug-{k}.html">{esc(v[0].split(" /")[0])}</a>' for k, v in BASES.items()) + ' · <a href="hersteller.html">Wohnmobil-Hersteller</a></div>'
    body = f'''<div class="page-head"><div class="wrap"><h1>{esc(c["h1"])}</h1><p>{esc(c["intro"])}</p></div></div>
<div class="wrap shop"><aside class="side" aria-label="Kategorien"><h2>Kategorien</h2><ul>{side}</ul><div class="notice">{ic("headset")} <strong>Unsicher?</strong><br>Wir beraten kostenlos: <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a></div></aside>
<div>{veh_links}{filt}{toolbar}{grid}{extra}{"<div class=faq-wrap><h2>Häufige Fragen</h2>" + faq + "</div>" if faq else ""}</div></div>{band()}'''
    page(f'{c["slug"]}.html', short(f'{c["title"]} | Italia Camper 24', 66), c["meta"], body, [x for x in (fs, items) if x], [("Startseite", "index.html"), (c["name"], None)], prio="0.9", nav_cur=f'{c["slug"]}.html')

# ================= Fahrzeug-Seiten =================
def veh_products(make, series=None):
    r = [p for p in PRODUCTS if make in p["makes"] and (series is None or not p["series"] or series in p["series"])]
    return r
def universal():
    return [p for p in PRODUCTS if not p["makes"] and not p["coach"] and p["cat"] not in ("rangierhilfe", "klimaanlagen")]
def grouped_cards(prods, base=0):
    by = collections.OrderedDict()
    for p in prods: by.setdefault(p["cat"], []).append(p)
    out = ""
    for cs in CAT_ORDER:
        if cs in by:
            L = by[cs]
            out += f'<section class="vgroup"><div class="sec-head"><h2>{esc(CAT[cs]["name"])} <span class="cnt">({len(L)})</span></h2><a href="{cs}.html">Alle {esc(CAT[cs]["name"])} →</a></div><div class="grid">{"".join(card(p, i) for i, p in enumerate(L[:8]))}</div>{"<p class=more-link><a href=#all>und " + str(len(L) - 8) + " weitere in dieser Kategorie</a></p>" if len(L) > 8 else ""}</section>'
    return out
def make_page(make):
    label, grp = BASES[make]; short_l = label.split(" /")[0]
    prods = veh_products(make)
    ser = "".join(f'<a class="cat" href="fahrzeug-{make}-{s[0]}.html"><div class="cat-body"><h3>{esc(short_l)} {esc(s[1])}</h3><p>{esc(s[2])}</p><span class="more">{len(veh_products(make, s[0]))} passende Artikel {ic("arrow")}</span></div></a>' for s in SERIES[grp])
    faq = [(f"Welches Zubehör können Sie für den {short_l} nachrüsten?", f"Für den {short_l} bieten wir Anhängerkupplungen, Rahmenverlängerungen, Elektrosätze, Luftfederung, Stützensysteme, Heckträger und weiteres Zubehör an. Die genaue Passung prüfen wir anhand von Baureihe und Baujahr."),
           (f"Brauche ich für den {short_l} nach dem Einbau einer Anhängerkupplung eine TÜV-Abnahme?", "Unsere Anhängerkupplungen werden mit EG-Typgenehmigung und EG-Gutachten geliefert. Eine separate TÜV-Einzelabnahme ist damit in der Regel nicht nötig."),
           (f"Kann ich meinen {short_l} bei Ihnen umrüsten lassen?", "Ja, an unseren Standorten Bohmte (Niedersachsen) und Diez (Rheinland-Pfalz) nach Terminvereinbarung zum Festpreis.")]
    fh, fs = faq_html(faq)
    uni = universal()
    body = f'''<div class="page-head"><div class="wrap"><h1>Wohnmobil-Zubehör für {esc(short_l)}</h1><p>{esc(MAKE_NOTE[make])}</p></div></div>
<section><div class="wrap"><div class="answer"><strong>Kurz gesagt:</strong> Für den {esc(short_l)} führen wir {len(prods)} fahrzeugspezifische Artikel – von der Anhängerkupplung bis zur Luftfederung. EG-Typgenehmigung, versandkostenfrei, Montage in Bohmte und Diez.</div>
<h2>Baureihe wählen</h2><div class="cats four">{ser}</div></div></section>
<section class="soft" id="all"><div class="wrap">{grouped_cards(prods) or "<p>Für dieses Fahrzeug erstellen wir Ihnen gern ein individuelles Angebot.</p>"}</div></section>
<section><div class="wrap"><div class="sec-head"><h2>Universelles Zubehör</h2><p>Passt je nach Fahrzeug – wir prüfen die Passung für Sie.</p></div><div class="grid">{"".join(card(p, i) for i, p in enumerate(uni[:8]))}</div></div></section>
<section class="soft"><div class="wrap" style="max-width:860px"><h2>Fragen zum {esc(short_l)}</h2>{fh}</div></section>{band(f"Ihren {short_l} nachrüsten?")}'''
    page(f"fahrzeug-{make}.html", short(f"{short_l} Zubehör & Nachrüstung | Italia Camper 24", 66),
         f"Zubehör für {short_l}: Anhängerkupplung, Rahmenverlängerung, Luftfederung, Stützen. EG-Typgenehmigung, versandkostenfrei, Montage in Bohmte & Diez.", body, [fs],
         [("Startseite", "index.html"), ("Fahrzeugfinder", "fahrzeugfinder.html"), (short_l, None)], prio="0.8", nav_cur="fahrzeugfinder.html")
def series_page(make, s):
    label, grp = BASES[make]; short_l = label.split(" /")[0]; sname, years = SERIES_LBL[s]
    full = f"{short_l} {sname} ({years})"
    prods = veh_products(make, s)
    others = "".join(f'<a class="chip" href="fahrzeug-{make}-{x[0]}.html">{esc(x[1])} · {esc(x[2])}</a>' for x in SERIES[grp] if x[0] != s)
    faq = [(f"Welche Anhängerkupplung passt zum {full}?", f"Wählen Sie unten die Anhängerkupplung für Ihr Chassis (mit oder ohne Rahmenverlängerung, mit oder ohne Elektrosatz). Wir führen {sum(1 for p in prods if p['cat'] == 'anhaengerkupplung')} passende Ausführungen. Unsicher? Foto vom Heckunterbau per WhatsApp senden."),
           (f"Brauche ich für den {short_l} eine Rahmenverlängerung?", "Bei Fiat-Leiterrahmen meist ja, bei AL-KO Tiefrahmen werden Rasterplatten und Verlängerungsprofile benötigt. Wir prüfen es kostenlos anhand eines Fotos."),
           ("Ist eine TÜV-Abnahme nötig?", "Unsere Kupplungen haben EG-Typgenehmigung (ECE R55) und EG-Gutachten; eine separate TÜV-Einzelabnahme ist in der Regel nicht nötig.")]
    fh, fs = faq_html(faq)
    note = f"Zubehör für den {full}: {len(prods)} passende Artikel aus {len({p['cat'] for p in prods})} Kategorien. Alle Preise inkl. MwSt., Versand kostenlos."
    body = f'''<div class="page-head"><div class="wrap"><h1>{esc(short_l)} {esc(sname)} – Zubehör &amp; Nachrüstung</h1><p>{esc(note)} Baujahre: {esc(years)}.</p></div></div>
<section><div class="wrap"><div class="answer"><strong>Kurz gesagt:</strong> Für den {esc(full)} bieten wir Anhängerkupplungen, Rahmenverlängerungen, Elektrosätze, Luftfederung und mehr – mit EG-Typgenehmigung, versandkostenfrei und optional mit Montage in Bohmte oder Diez.</div>
<div class="chips" style="margin-bottom:24px"><span class="chip-label">Andere Baureihen:</span>{others}<a class="chip" href="fahrzeug-{make}.html">Alle {esc(short_l)}</a></div></div></section>
<section class="soft" id="all"><div class="wrap">{grouped_cards(prods) or f'<div class="empty"><h2>Für diese Baureihe erstellen wir Ihnen ein Angebot</h2><p>Nicht jedes Teil ist ab Lager gelistet. Senden Sie uns den Fahrzeugschein, wir stellen die passende Lösung zusammen.</p><a class="btn btn-cta btn-lg" href="angebot-anfordern.html">Angebot anfordern</a></div>'}</div></section>
<section><div class="wrap"><div class="sec-head"><h2>Universelles Zubehör</h2></div><div class="grid">{"".join(card(p, i) for i, p in enumerate(universal()[:4]))}</div></div></section>
<section class="soft"><div class="wrap" style="max-width:860px"><h2>Fragen zum {esc(short_l)}</h2>{fh}</div></section>{band(f"Ihren {short_l} nachrüsten?")}'''
    page(f"fahrzeug-{make}-{s}.html", short(f"Zubehör {short_l} {sname} {years} | Italia Camper 24", 66),
         short(f"Anhängerkupplung, Rahmenverlängerung, Luftfederung & mehr für {full}. {len(prods)} passende Artikel, EG-Typgenehmigung, versandkostenfrei.", 160), body, [fs],
         [("Startseite", "index.html"), ("Fahrzeugfinder", "fahrzeugfinder.html"), (short_l, f"fahrzeug-{make}.html"), (f"{sname}", None)], prio="0.7", nav_cur="fahrzeugfinder.html")

def finder_page():
    mk = "".join(f'<a class="cat" href="fahrzeug-{k}.html"><div class="cat-body"><h3>{esc(v[0])}</h3><p>{esc(MAKE_NOTE[k][:90].rsplit(" ",1)[0])} …</p><span class="more">{len(veh_products(k))} Artikel {ic("arrow")}</span></div></a>' for k, v in BASES.items())
    co = "".join(f'<a class="chip" href="hersteller-{cslug(b)}.html">{esc(b)} <span>{len(L)}</span></a>' for b, L in COACHES.items())
    body = f'''<div class="page-head"><div class="wrap"><h1>Fahrzeugfinder: Zubehör für Ihr Wohnmobil</h1><p>Wählen Sie Ihr Basisfahrzeug oder Ihren Aufbauhersteller – wir zeigen Ihnen genau die Anhängerkupplungen, Rahmenverlängerungen, Elektrosätze und Luftfederungen, die passen.</p></div></div>
<section><div class="wrap split">{finder("finder big")}<div><h2>So finden Sie das richtige Teil</h2><ol class="steps one"><li><h3>Basisfahrzeug bestimmen</h3><p>Marke und Baureihe stehen im Fahrzeugschein (z. B. ZFA250 für Fiat Ducato 250).</p></li><li><h3>Baureihe wählen</h3><p>Die Baujahre helfen bei der Zuordnung. Beim Sprinter zählt das Baumuster, nicht 313 oder 316.</p></li><li><h3>Passende Artikel ansehen</h3><p>Alle Preise inkl. MwSt., Versand kostenlos, EG-Gutachten inklusive.</p></li></ol></div></div></section>
<section class="soft"><div class="wrap"><h2>Basisfahrzeuge</h2><div class="cats four">{mk}</div></div></section>
<section><div class="wrap"><h2>Wohnmobil-Hersteller (aufbauspezifische Anhängerkupplungen)</h2><p>Für über {sum(len(L) for L in COACHES.values())} Reisemobil-Modelle führen wir die passende Anhängerkupplung.</p><div class="chips">{co}</div><p style="margin-top:20px"><a class="btn btn-out" href="hersteller.html">Alle Hersteller ansehen</a></p></div></section>{band()}'''
    page("fahrzeugfinder.html", "Fahrzeugfinder: Wohnmobil-Zubehör | Italia Camper 24", "Fahrzeugfinder für Wohnmobil-Zubehör: Fiat Ducato, Jumper, Boxer, Sprinter, Transit, Master, Daily sowie Aufbauhersteller. Passende Anhängerkupplung finden.", body, [],
         [("Startseite", "index.html"), ("Fahrzeugfinder", None)], prio="0.9", nav_cur="fahrzeugfinder.html")

def hersteller_pages():
    chips = "".join(f'<a class="cat" href="hersteller-{cslug(b)}.html"><div class="cat-body"><h3>{esc(b)}</h3><p>Anhängerkupplung für {len(L)} Modelle</p><span class="more">Modelle ansehen {ic("arrow")}</span></div></a>' for b, L in COACHES.items())
    body = f'''<div class="page-head"><div class="wrap"><h1>Anhängerkupplung nach Wohnmobil-Hersteller</h1><p>{esc(COACH_NOTE)} Wählen Sie Ihren Hersteller.</p></div></div><section><div class="wrap"><div class="cats four">{chips}</div></div></section>{band("Ihr Modell ist nicht dabei?")}'''
    page("hersteller.html", "Anhängerkupplung für Wohnmobil-Hersteller | Italia Camper 24", "Aufbauspezifische Anhängerkupplungen für Bürstner, Weinsberg, T.E.C., Challenger, Chausson, Forster, Dethleffs, Hymer, Carthago u. v. m.", body, [],
         [("Startseite", "index.html"), ("Fahrzeugfinder", "fahrzeugfinder.html"), ("Hersteller", None)], prio="0.8", nav_cur="fahrzeugfinder.html")
    for b, L in COACHES.items():
        faq = [(f"Welche Anhängerkupplung passt zu meinem {b}?", f"Wir führen {len(L)} aufbauspezifische Ausführungen für {b}. Wählen Sie Ihr Modell – oder senden Sie uns Fahrzeugschein und ein Foto vom Heck."),
               ("Brauche ich eine TÜV-Abnahme?", "Unsere Anhängerkupplungen haben EG-Typgenehmigung, das EG-Gutachten liegt bei; eine zusätzliche TÜV-Einzelabnahme ist in der Regel nicht nötig."),
               ("Kann die Kupplung bei Ihnen montiert werden?", "Ja, in Bohmte und Diez nach Terminvereinbarung zum Festpreis – viele Montagen dauern nur wenige Stunden.")]
        fh, fs = faq_html(faq)
        body = f'''<div class="page-head"><div class="wrap"><h1>Anhängerkupplung für {esc(b)} Wohnmobil</h1><p>{len(L)} Modelle von {esc(b)} – jede Kupplung ist auf Chassis und Rahmenform abgestimmt. EG-Typgenehmigung, versandkostenfrei.</p></div></div>
<section><div class="wrap"><div class="filterbar"><div class="frow"><div class="fsearch">{ic("search")}<label class="sr" for="fq">Modell suchen</label><input id="fq" type="search" placeholder="Modell, z. B. Nexxo, Brevio …"></div></div></div><div class="grid" id="prodgrid">{"".join(card(p, i) for i, p in enumerate(L))}</div><p class="noresult" id="noresult" hidden>Kein Modell gefunden – <a href="angebot-anfordern.html">wir prüfen Ihr Fahrzeug gern</a>.</p></div></section>
<section class="soft"><div class="wrap" style="max-width:860px"><h2>Fragen zur Anhängerkupplung für {esc(b)}</h2>{fh}</div></section>{band(f"Ihr {b}-Modell nicht dabei?")}'''
        page(f"hersteller-{cslug(b)}.html", short(f"Anhängerkupplung {b} Wohnmobil nachrüsten | Italia Camper 24", 66),
             short(f"Anhängerkupplung für {b} Wohnmobil: {len(L)} Modelle, EG-Typgenehmigung, versandkostenfrei, Montage in Bohmte & Diez.", 160), body, [fs],
             [("Startseite", "index.html"), ("Fahrzeugfinder", "fahrzeugfinder.html"), ("Hersteller", "hersteller.html"), (b, None)], prio="0.7", nav_cur="fahrzeugfinder.html")

# ================= Startseite =================
FAQ_GENERAL = [
    ("Wie lange dauert die Lieferung?", "Die Lieferzeit beträgt in der Regel 2–7 Werktage, der Versand innerhalb Deutschlands ist kostenlos. Wir liefern auch nach Österreich."),
    ("Welche Zahlungsarten gibt es?", "PayPal (inkl. Kreditkarte, Lastschrift und Überweisung) sowie Überweisung. Alle Preise verstehen sich inklusive gesetzlicher Mehrwertsteuer."),
    ("Brauche ich eine TÜV-Abnahme?", "Unsere Anhängerkupplungen werden mit EG-Typgenehmigung (ECE R55) und EG-Gutachten geliefert. Eine separate TÜV-Einzelabnahme ist damit in der Regel nicht nötig – Details nennen wir Ihnen vor dem Kauf."),
    ("Kann ich bei Ihnen einbauen lassen?", "Ja, in unseren Werkstätten in Bohmte (Niedersachsen) und Diez (Rheinland-Pfalz) nach Terminvereinbarung zum Festpreis. Viele Kunden bauen auch selbst ein – eine Anleitung liegt bei."),
    ("Wie finde ich das passende Teil für mein Fahrzeug?", "Nutzen Sie den Fahrzeugfinder oder senden Sie uns ein Foto vom Fahrzeugschein per WhatsApp. Wir prüfen die Passung kostenlos, bevor Sie bestellen."),
    ("Was gilt bei Widerruf?", "Verbraucher haben ein vierzehntägiges Widerrufsrecht. Die vollständige Widerrufsbelehrung finden Sie auf unserer Seite Widerruf."),
]
def fdate(s):
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", s)
    mo = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6, "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12}
    return f"{int(m.group(1)):02d}.{mo.get(m.group(2), 1):02d}.{m.group(3)}" if m else ""
def review_card(r):
    return f'<figure class="review"><div class="stars">{ic("star")}{ic("star")}{ic("star")}{ic("star")}{ic("star")}</div><blockquote>{esc(short(r["text"], 300))}</blockquote><figcaption><strong>{esc(r["name"])}</strong> · {fdate(r["date"])}</figcaption></figure>'

def find_p(rx, cat=None):
    for p in PRODUCTS:
        if re.search(rx, p["name"]) and p["cover"] and (cat is None or p["cat"] == cat): return p
BEST = [x for x in (find_p(r"^ALU-Matic Kurbelstütze"), find_p(r"^Luftfahrwerk Z6 Basis"), find_p(r"^Anhängerkupplung Variabel 12,5 kN$"), find_p(r"^Motorradträger 120kg"),
                    find_p(r"^Robot Trolley Model RT1500"), find_p(r"^Dometic FreshJet FJX4 1500"), find_p(r"^AutoLift Stützanlage"), find_p(r"^Bike lift Standard")) if x]

def home():
    cats = ""
    for c in CATEGORIES[:12]:
        ps = PBY.get(c["slug"], [])
        cov = next((p for p in ps if p["cover"]), None)
        if c["slug"] == "raeder-felgen": art = f'<div class="cat-art pic"><img class="photo" src="assets/img/p/{FELGEN[0][0]}-360.webp" width="360" height="209" alt="Borbet CW5 Alufelge Wohnmobil" loading="lazy"></div>'
        elif cov: art = f'<div class="cat-art pic">{img_tag(cov["cover"], c["name"], "(max-width:700px) 50vw, 280px")}</div>'
        else: art = f'<div class="cat-art tone-{c["tone"]}">{ic(c["icon"])}</div>'
        cats += f'<a class="cat" href="{c["slug"]}.html">{art}<div class="cat-body"><h3>{esc(c["name"])}</h3><p>{esc(c["short"])}</p><span class="more">{len(ps) if ps else ""} {"Artikel" if ps else "Auf Anfrage"} {ic("arrow")}</span></div></a>'
    brands = "".join(f'<a class="chip" href="fahrzeug-{k}.html">{esc(v[0].split(" /")[0])}</a>' for k, v in BASES.items())
    coach = "".join(f'<a class="chip" href="hersteller-{cslug(b)}.html">{esc(b)}</a>' for b in list(COACHES)[:14])
    faq, fs = faq_html(FAQ_GENERAL)
    pick = [r for r in REVIEWS if 90 <= len(r["text"]) <= 280][:6]
    locs = "".join(f'<div class="loc"><h3>{ic("pin")} {l["city"]}</h3><p>{l["plz"]} {l["city"]}, {l["region"]}</p><a class="btn btn-out" href="standort-{l["slug"]}.html">Montage in {l["city"]}</a></div>' for l in LOCATIONS)
    blog = "".join(f'<a class="cat" href="ratgeber-{b["slug"]}.html"><div class="cat-art pic">{blog_img(b)}</div><div class="cat-body"><h3>{esc(b["title"])}</h3><p>{esc(short(b["meta"], 110))}</p><span class="more">Lesen {ic("arrow")}</span></div></a>' for b in BLOG[1:4])
    body = f'''<section class="hero"><div class="wrap"><div><span class="kicker">Wohnmobil-Nachrüstung seit {SITE['since']}</span>
<h1>Anhängerkupplung, Luftfederung &amp; Stützen für Ihr Wohnmobil</h1>
<p class="lead">{sum(1 for _ in PRODUCTS)} fahrzeugspezifische Produkte mit EG-Typgenehmigung, persönliche Fachberatung – auch am Wochenende – und Montage in Bohmte und Diez. Versandkostenfrei in ganz Deutschland.</p>
<div class="cta-row"><a class="btn btn-cta btn-lg" href="anhaengerkupplung.html">Anhängerkupplungen ansehen {ic("arrow")}</a><a class="btn btn-ghost btn-lg" href="angebot-anfordern.html">Angebot anfordern</a></div>
<ul class="ticks hticks"><li>{ic("check")} Festpreise inkl. MwSt.</li><li>{ic("check")} EG-Gutachten inklusive</li><li>{ic("check")} {SITE['rating']} / 5 · {SITE['reviews_n']} Bewertungen</li></ul></div>{finder()}</div></section>
<section class="usp-sec"><div class="wrap"><ul class="usp"><li>{ic("shield")}<div><strong>EG-Typgenehmigung</strong><span>Mit Gutachten – in der Regel keine TÜV-Einzelabnahme nötig</span></div></li>
<li>{ic("truck")}<div><strong>Versandkostenfrei</strong><span>Deutschland &amp; Österreich · Lieferzeit meist 2–7 Werktage</span></div></li>
<li>{ic("wrench")}<div><strong>Montage vor Ort</strong><span>Bohmte &amp; Diez, zum Festpreis nach Termin</span></div></li>
<li>{ic("headset")}<div><strong>Persönlich erreichbar</strong><span>Telefon &amp; WhatsApp – 24 h, auch am Wochenende</span></div></li></ul></div></section>
<section id="kategorien" class="soft"><div class="wrap"><div class="sec-head"><div><h2>Unser Sortiment</h2><p>Alles, was Ihr Reisemobil sicherer, komfortabler und vielseitiger macht.</p></div><a class="btn btn-out" href="fahrzeugfinder.html">{ic("car")} Zum Fahrzeugfinder</a></div><div class="cats four">{cats}</div></div></section>
<section><div class="wrap"><div class="sec-head"><div><h2>Beliebte Produkte</h2><p>Direkt bestellen – inkl. MwSt. und versandkostenfrei.</p></div>{stars()}</div><div class="grid">{"".join(card(p, i) for i, p in enumerate(BEST))}</div></div></section>
<section class="soft"><div class="wrap split"><div><h2>Zubehör für Ihr Basisfahrzeug</h2><p>Ducato, Jumper, Boxer, Sprinter, Transit, Master, Daily, Crafter: Wir kennen die Besonderheiten der gängigen Basisfahrzeuge – Baureihe für Baureihe.</p><div class="chips">{brands}</div>
<h3 style="margin-top:28px">Oder nach Wohnmobil-Hersteller</h3><p>Aufbauspezifische Anhängerkupplungen für {sum(len(L) for L in COACHES.values())} Modelle.</p><div class="chips">{coach}<a class="chip" href="hersteller.html">Alle Hersteller →</a></div></div>
<div class="panel"><h2>Montage-Service</h2><p>Zwei Werkstätten, ein Anspruch: Ihr Wohnmobil kommt fertig montiert zurück – zum vorher vereinbarten Festpreis.</p><div class="locs one">{locs}</div></div></div></section>
<section><div class="wrap"><div class="sec-head"><div><h2>In 4 Schritten zum fertig ausgerüsteten Wohnmobil</h2></div></div>
<ol class="steps"><li><h3>Fahrzeug wählen</h3><p>Im Fahrzeugfinder Marke und Baureihe oder Ihren Aufbauhersteller wählen.</p></li><li><h3>Beraten lassen</h3><p>Wir prüfen Passung, Gewichte und Unterlagen – per Telefon oder WhatsApp.</p></li><li><h3>Bestellen</h3><p>Online kaufen, versandkostenfrei. Zahlung per PayPal oder Überweisung.</p></li><li><h3>Einbauen</h3><p>Selbst montieren (Anleitung liegt bei) oder Termin in Bohmte oder Diez.</p></li></ol></div></section>
<section class="soft"><div class="wrap"><div class="sec-head"><div><h2>Das sagen unsere Kunden</h2><p>{SITE['reviews_n']} Bewertungen auf unserer Website – hier eine Auswahl.</p></div><a class="btn btn-out" href="bewertungen.html">Alle Bewertungen</a></div><div class="reviews">{"".join(review_card(r) for r in pick)}</div></div></section>
<section><div class="wrap"><div class="sec-head"><div><h2>Ratgeber</h2><p>Wissen, das Sie vor dem Kauf weiterbringt.</p></div><a class="btn btn-out" href="ratgeber.html">Alle Ratgeber</a></div><div class="cats">{blog}</div></div></section>
<section class="soft"><div class="wrap" style="max-width:860px"><h2>Häufige Fragen</h2>{faq}<p><a href="faq.html">Alle Fragen &amp; Antworten →</a></p></div></section>{band()}'''
    page("index.html", "Wohnmobil-Zubehör & Nachrüstung | Italia Camper 24",
         "Anhängerkupplung, Luftfederung, Stützen & Heckträger für Wohnmobil und Kastenwagen. EG-Typgenehmigung, versandkostenfrei, Montage in Bohmte & Diez.", body, [fs], prio="1.0",
         preload='<link rel="preload" as="image" href="assets/img/logo-260.webp">')

def blog_img(b, big=False):
    if not b.get("img"): return f'<div class="noimg">{ic("book")}</div>'
    w, h = b["img"]; sz = 900 if big else 450; hh = round(sz * h / w)
    return f'<img class="photo" src="assets/img/b/{b["slug"]}-450.webp" srcset="assets/img/b/{b["slug"]}-450.webp 450w, assets/img/b/{b["slug"]}-900.webp 900w" sizes="{"(max-width:860px) 100vw, 760px" if big else "300px"}" width="{450 if not big else 900}" height="{round((450 if not big else 900)*h/w)}" alt="{esc(b["title"])}" {"fetchpriority=high" if big else "loading=lazy"}>'

# ================= Ratgeber / Blog =================
def blog_pages():
    for b in BLOG:
        sec = render_blocks([x for x in b["body"] if not re.search(r"^(Mehr lesen|Zurück|Teilen)", x[1])], limit=70)
        sc = {"@context": "https://schema.org", "@type": "Article", "headline": b["title"], "description": b["meta"], "inLanguage": "de-DE", "datePublished": b["date"], "dateModified": b["date"],
              "author": {"@id": U + "/#org"}, "publisher": {"@id": U + "/#org"}, "mainEntityOfPage": f'{U}/ratgeber-{b["slug"]}.html'}
        if b.get("img"): sc["image"] = f'{U}/assets/img/b/{b["slug"]}-900.webp'
        body = f'<div class="wrap"><article class="article"><p class="eyebrow">Ratgeber · {b["date"][8:]}.{b["date"][5:7]}.{b["date"][:4]}</p><h1>{esc(b["title"])}</h1>{blog_img(b, True) if b.get("img") else ""}<div class="prose">{sec}</div>{"<div class=answer><strong>Passende Produkte:</strong> <a href=luftfederung.html>Luftfederung</a> · <a href=hecktraeger.html>Heckträger</a> · <a href=anhaengerkupplung.html>Anhängerkupplung</a></div>"}<p><a class="btn btn-cta btn-lg" href="angebot-anfordern.html">Persönliche Beratung anfragen</a></p></article></div>'
        page(f'ratgeber-{b["slug"]}.html', short(b["title"], 52) + " | Ratgeber", short(b["meta"] or b["title"], 160), body, [sc], [("Startseite", "index.html"), ("Ratgeber", "ratgeber.html"), (short(b["title"], 50), None)], og_type="article", prio="0.6",
             og_image=(f'{U}/assets/img/b/{b["slug"]}-900.webp' if b.get("img") else None))
    cards = "".join(f'<a class="cat" href="ratgeber-{b["slug"]}.html"><div class="cat-art pic">{blog_img(b)}</div><div class="cat-body"><h3>{esc(b["title"])}</h3><p>{esc(short(b["meta"], 130))}</p><span class="more">Lesen {ic("arrow")}</span></div></a>' for b in BLOG)
    page("ratgeber.html", "Ratgeber Wohnmobil-Nachrüstung | Italia Camper 24", "Ratgeber zu Luftfederung, Fahrradträger, Motorradträger und Garagenhalterung für Wohnmobile – Praxiswissen von Italia Camper 24.",
         f'<div class="page-head"><div class="wrap"><h1>Ratgeber für Wohnmobil-Nachrüstung</h1><p>Praxiswissen zu Luftfederung, Trägersystemen und Garagenhalterung.</p></div></div><section><div class="wrap"><div class="cats">{cards}</div></div></section>{band()}', [],
         [("Startseite", "index.html"), ("Ratgeber", None)], prio="0.6")

# ================= Info-Seiten =================
def simple(fname, title, desc, h1, content, prio="0.5", noindex=False, schemas=(), nav=None):
    body = f'<div class="page-head"><div class="wrap"><h1>{esc(h1)}</h1></div></div><div class="wrap"><div class="article">{content}</div></div>'
    page(fname, title, desc, body, schemas, [("Startseite", "index.html"), (h1, None)], prio=prio, noindex=noindex)

def info_pages():
    faq, fs = faq_html(FAQ_GENERAL)
    simple("faq.html", "Häufige Fragen (FAQ) | Italia Camper 24", "Antworten zu Lieferung, Zahlung, EG-Typgenehmigung, Montage und Widerruf bei Italia Camper 24.", "Häufige Fragen", faq + f'<p style="margin-top:24px"><a class="btn btn-cta" href="kontakt.html">Weitere Frage stellen</a></p>', "0.6", schemas=[fs])
    v = LEGAL["infos-zu-versand-und-bezahlmethoden"]
    simple("versand-zahlung.html", "Versand & Zahlung | Italia Camper 24", "Versandkostenfrei in Deutschland, Lieferung nach Österreich, Zahlung per PayPal oder Überweisung – alle Infos zu Versand und Bezahlung.", "Versand & Zahlung",
           f'<div class="answer"><strong>Kurz gesagt:</strong> Versand kostenlos innerhalb Deutschlands, Lieferzeit meist 2–7 Werktage, Zahlung per PayPal (inkl. Kreditkarte, Lastschrift, Überweisung) oder Überweisung.</div><div class="prose">{render_blocks(v["body"], limit=40)}</div>', "0.6")
    locs = "".join(f'<div class="loc"><h3>{ic("pin")} {l["city"]}</h3><p>{esc(l["text"])}</p><a class="btn btn-out" href="standort-{l["slug"]}.html">Mehr zum Standort</a></div>' for l in LOCATIONS)
    simple("montage-service.html", "Montage-Service Bohmte & Diez | Italia Camper 24", "Wohnmobil-Zubehör einbauen lassen: Werkstätten in Bohmte und Diez, Festpreis, Termin nach Absprache. Anhängerkupplung, Luftfederung, Stützen, Klima.", "Montage-Service",
           f'<div class="answer"><strong>Kurz gesagt:</strong> Wir bauen Ihr Zubehör in zwei Werkstätten ein – in Bohmte (Niedersachsen) und Diez (Rheinland-Pfalz), nach Termin und zum Festpreis. Montage lässt sich direkt beim Produkt dazubuchen.</div><div class="locs">{locs}</div><h2>So läuft es ab</h2><ol class="numlist"><li>Produkt wählen und beim Kauf „Montage dazubuchen“ anhaken – oder Angebot anfordern</li><li>Terminvorschlag per Telefon oder WhatsApp erhalten</li><li>Fahrzeug bringen, nach wenigen Stunden montiert abholen</li></ol><p><a class="btn btn-cta btn-lg" href="angebot-anfordern.html">Montage-Termin anfragen</a></p>', "0.8")
    simple("ueber-uns.html", "Über uns | Italia Camper 24", f"Italia Camper 24 – Spezialist für Wohnmobil-Nachrüstung seit {SITE['since']}. Inhaberin {SITE['owner']}, Werkstätten in Bohmte und Diez.", "Über Italia Camper 24",
           f'<p>Seit {SITE["since"]} rüsten wir Wohnmobile und Kastenwagen nach. Unser Sortiment umfasst fahrzeugspezifische Anhängerkupplungen für über {sum(len(L) for L in COACHES.values())} Reisemobil-Modelle und alle gängigen Basisfahrzeuge, dazu Luftfederung, Stützensysteme, Heckträger, Rangierhilfen und Klimaanlagen.</p><p>Wir beraten persönlich, nennen Festpreise und montieren in unseren Werkstätten in Bohmte und Diez. Auch am Wochenende erreichen Sie uns per Telefon und WhatsApp.</p><ul class="ticks"><li>{ic("star")} {SITE["rating"]} von 5 Sternen – {SITE["reviews_n"]} Kundenbewertungen</li><li>{ic("shield")} EG-Gutachten inklusive</li><li>{ic("truck")} Versandkostenfrei in Deutschland</li></ul><p><strong>{SITE["owner"]}</strong> · {SITE["street"]}, {SITE["plz"]} {SITE["city"]}</p>', "0.5")
    for k, t, h in (("impressum", "Impressum", "Impressum"), ("agb", "Allgemeine Geschäftsbedingungen (AGB)", "AGB"), ("widerrufsbelehrung-und-formular", "Widerrufsbelehrung und -formular", "Widerruf"), ("datenschutz", "Datenschutzerklärung", "Datenschutz")):
        fn = {"widerrufsbelehrung-und-formular": "widerruf"}.get(k, k) + ".html"
        simple(fn, f"{t} | Italia Camper 24", f"{t} von Italia Camper 24", t, f'<div class="prose legal">{render_blocks(LEGAL[k]["body"], limit=400)}</div>', noindex=True)
    # Bewertungen
    rv = "".join(review_card(r) for r in REVIEWS)
    body = f'<div class="page-head"><div class="wrap"><h1>Kundenbewertungen</h1><p>{SITE["reviews_n"]} Bewertungen – ehrliche Stimmen von Wohnmobilfahrern. Durchschnitt {SITE["rating"]} von 5 Sternen bei Google.</p></div></div><section><div class="wrap"><div class="reviews all" id="reviews">{rv}</div><p class="more-wrap"><button class="btn btn-out btn-lg" id="rmore" hidden>Weitere Bewertungen laden</button></p></div></section>{band("Auch ein Projekt am Wohnmobil?")}'
    page("bewertungen.html", "Kundenbewertungen | Italia Camper 24", f"{SITE['reviews_n']} Kundenbewertungen zu Anhängerkupplung, Luftfederung und Montage bei Italia Camper 24.", body, [], [("Startseite", "index.html"), ("Bewertungen", None)], prio="0.6")
    # Standorte
    for l in LOCATIONS:
        faq = [(f"Wo montiert Italia Camper 24 in {l['city']}?", f"In unserer Werkstatt in {l['plz']} {l['city']} ({l['region']}). Die genaue Anfahrt erhalten Sie bei der Terminvergabe."),
               ("Muss ich einen Termin vereinbaren?", "Ja. Wir planen jede Montage fest ein, damit Ihr Fahrzeug zum vereinbarten Zeitpunkt fertig ist."),
               ("Was kostet die Montage?", "Wir nennen Ihnen vorab einen Festpreis; bei vielen Produkten können Sie die Montage direkt dazubuchen.")]
        fh, fs = faq_html(faq)
        lb = {"@context": "https://schema.org", "@type": "AutoRepair", "name": f'{SITE["name"]} {l["city"]}', "url": f'{U}/standort-{l["slug"]}.html', "telephone": SITE["phone"], "email": SITE["email"], "parentOrganization": {"@id": U + "/#org"},
              "address": {"@type": "PostalAddress", "postalCode": l["plz"], "addressLocality": l["city"], "addressRegion": l["state"], "addressCountry": "DE"}, "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lon"]}}
        body = f'''<div class="page-head"><div class="wrap"><h1>Wohnmobil-Montage in {l["city"]}</h1><p>Anhängerkupplung, Luftfederung, Stützen und mehr einbauen lassen – {l["plz"]} {l["city"]}, {l["region"]}.</p></div></div>
<section><div class="wrap split"><div><div class="answer"><strong>Kurz gesagt:</strong> In {l["city"]} montieren wir Wohnmobil-Zubehör nach Terminvereinbarung zum Festpreis. Rufen Sie an: <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a>.</div><p>{esc(l["text"])}</p><h2>Das montieren wir in {l["city"]}</h2><ul class="ticks">{"".join(f"<li>{ic('check')} {esc(c['name'])}</li>" for c in CATEGORIES[:13] if c['slug'] not in ('raeder-felgen', 'frontscheibe'))}</ul></div>
<div class="panel"><h2>Termin anfragen</h2><p>Nennen Sie uns Fahrzeug, Baujahr und Wunschprodukt – wir melden uns mit Terminvorschlag und Festpreis.</p><a class="btn btn-cta btn-lg btn-block" href="angebot-anfordern.html?produkt=Montage {l["city"]}">Termin anfragen</a><p style="margin-top:16px">{ic("phone")} <a style="color:#fff" href="tel:{SITE['phone_href']}">{SITE['phone']}</a></p></div></div></section>
<section class="soft"><div class="wrap" style="max-width:860px"><h2>Fragen zur Montage in {l["city"]}</h2>{fh}</div></section>{band()}'''
        page(f'standort-{l["slug"]}.html', f'Wohnmobil-Montage {l["city"]} | Italia Camper 24', f'Montage von Anhängerkupplung, Luftfederung & Stützen in {l["plz"]} {l["city"]}. Festpreis, EG-Typgenehmigung, Termin nach Absprache.', body, [fs, lb],
             [("Startseite", "index.html"), ("Montage-Service", "montage-service.html"), (l["city"], None)], prio="0.8")

def forms():
    catopts = "".join(f"<option>{esc(c['name'])}</option>" for c in CATEGORIES)
    makeopts = "".join(f"<option>{esc(v[0])}</option>" for v in BASES.values()) + "<option>Wohnmobil-Hersteller / sonstiges Fahrzeug</option>"
    form = f'''<form id="quoteform" class="form-grid" novalidate><div><label for="name">Name *</label><input id="name" name="name" required autocomplete="name"><div class="err">Bitte Namen angeben.</div></div>
<div><label for="email">E-Mail *</label><input id="email" name="email" type="email" required autocomplete="email"><div class="err">Bitte gültige E-Mail angeben.</div></div>
<div><label for="tel">Telefon</label><input id="tel" name="tel" type="tel" autocomplete="tel"></div>
<div><label for="produkt">Gewünschtes Produkt</label><select id="produkt" name="produkt"><option value="">Bitte wählen …</option>{catopts}</select></div>
<div><label for="fzg">Basisfahrzeug</label><select id="fzg" name="fzg"><option value="">Bitte wählen …</option>{makeopts}</select></div>
<div><label for="bj">Baujahr / Typ / Modell</label><input id="bj" name="bj" placeholder="z. B. Ducato X250, 2014 · Bürstner Nexxo T 690 G"></div>
<div class="full"><label for="nachricht">Ihre Nachricht</label><textarea id="nachricht" name="nachricht" placeholder="Was möchten Sie nachrüsten? Foto vom Heckunterbau bitte per WhatsApp senden."></textarea></div>
<div class="full"><label class="chk"><input type="checkbox" name="dsgvo" required> <span>Ich habe die <a href="datenschutz.html">Datenschutzerklärung</a> gelesen und bin mit der Verarbeitung meiner Angaben zur Bearbeitung der Anfrage einverstanden. *</span></label><div class="err">Bitte zustimmen.</div></div>
<div class="full btnrow"><button class="btn btn-cta btn-lg" type="submit">Anfrage per E-Mail senden</button><a class="btn btn-out btn-lg" id="wa-send" href="https://wa.me/{SITE['wa']}" rel="noopener">{ic("chat")} Per WhatsApp senden</a></div><p id="sent" hidden class="notice">Ihr E-Mail-Programm wurde geöffnet – bitte senden Sie die Nachricht dort ab.</p></form>'''
    simple("angebot-anfordern.html", "Angebot anfordern – schnell & unverbindlich | Italia Camper 24", "Unverbindliches Angebot für Anhängerkupplung, Luftfederung, Stützen & Co. anfordern – mit Fahrzeugdaten, wir antworten schnell.", "Angebot anfordern",
           f'<p>Damit wir Ihnen ein passgenaues Angebot erstellen können, benötigen wir nur wenige Angaben zu Fahrzeug und Wunschprodukt. <strong>Tipp:</strong> Ein Foto vom Heckunterbau und vom Fahrzeugschein macht das Angebot schneller und präziser – senden Sie es gern per WhatsApp.</p>{form}', "0.8")
    simple("kontakt.html", "Kontakt & Beratung | Italia Camper 24", f"Kontakt zu Italia Camper 24: Telefon {SITE['phone']}, WhatsApp und E-Mail. Auch am Wochenende erreichbar.", "Kontakt & Beratung",
           f'<div class="contact-cards"><a class="loc" href="tel:{SITE["phone_href"]}"><h3>{ic("phone")} Telefon</h3><p>{SITE["phone"]}<br><small>24 Stunden, 365 Tage erreichbar</small></p></a><a class="loc" href="https://wa.me/{SITE["wa"]}" rel="noopener"><h3>{ic("chat")} WhatsApp</h3><p>Foto vom Fahrzeugschein senden – wir prüfen kostenlos.</p></a><a class="loc" href="mailto:{SITE["email"]}"><h3>{ic("mail")} E-Mail</h3><p>{SITE["email"]}</p></a></div><p><strong>{SITE["name"]}</strong> · {SITE["owner"]}<br>{SITE["street"]}, {SITE["plz"]} {SITE["city"]}<br>Werkstätten: Bohmte (49163) &amp; Diez (65582)</p><h2>Nachricht senden</h2>{form.replace("quoteform", "contactform").replace("Anfrage per E-Mail senden", "Nachricht senden")}', "0.7")

def cart_pages():
    body = f'''<div class="page-head"><div class="wrap"><h1>Warenkorb</h1></div></div><div class="wrap two"><div id="cartlist" aria-live="polite"></div>
<aside class="summary" id="sum" hidden><h2>Zusammenfassung</h2><dl><div><dt>Zwischensumme</dt><dd id="t-sub">–</dd></div><div><dt>Versand</dt><dd>kostenlos</dd></div><div><dt>darin enth. MwSt. 19 %</dt><dd id="t-vat">–</dd></div><div class="total"><dt>Gesamt</dt><dd id="t-tot">–</dd></div></dl>
<a class="btn btn-cta btn-lg btn-block" href="kasse.html" style="margin-top:16px">Zur Kasse</a><ul class="meta-list"><li>{ic("shield")} Sichere Bestellung</li><li>{ic("truck")} Versandkostenfrei, Lieferzeit meist 2–7 Werktage</li><li>{ic("headset")} Fragen? {SITE['phone']}</li></ul></aside></div>'''
    page("warenkorb.html", "Warenkorb | Italia Camper 24", "Ihr Warenkorb bei Italia Camper 24", body, [], noindex=True)
    f = lambda i, l, t="text", req=True, ac="", full=False: f'<div{" class=full" if full else ""}><label for="{i}">{l}{" *" if req else ""}</label><input id="{i}" name="{i}" type="{t}"{" required" if req else ""}{f" autocomplete={ac}" if ac else ""}><div class="err">Bitte ausfüllen.</div></div>'
    body = f'''<div class="page-head"><div class="wrap"><h1>Kasse</h1></div></div><div class="wrap two"><div><p id="cohint" hidden>Ihr Warenkorb ist leer. <a href="index.html">Zum Shop</a></p>
<form id="checkout" novalidate><h2>Ihre Daten</h2><div class="form-grid">{f("vorname","Vorname",ac="given-name")}{f("nachname","Nachname",ac="family-name")}{f("strasse","Straße &amp; Hausnummer",ac="street-address",full=True)}{f("plz","PLZ",ac="postal-code")}{f("ort","Ort",ac="address-level2")}{f("email","E-Mail","email",ac="email")}{f("tel","Telefon (für Rückfragen)","tel",False,"tel")}{f("fahrzeug","Fahrzeug &amp; Baujahr (zur Passungsprüfung)",full=True)}</div>
<h2 style="margin-top:28px">Zahlart</h2><div class="form-grid"><div class="full"><label for="zahlart">Zahlart</label><select id="zahlart" name="zahlart"><option>PayPal (inkl. Kreditkarte, Lastschrift)</option><option>Überweisung</option></select></div>
<div class="full"><label for="note">Anmerkung</label><textarea id="note" name="note"></textarea></div>
<div class="full"><label class="chk"><input type="checkbox" name="agb" required> <span>Ich habe die <a href="agb.html">AGB</a>, die <a href="widerruf.html">Widerrufsbelehrung</a> und die <a href="datenschutz.html">Datenschutzerklärung</a> gelesen. *</span></label><div class="err">Bitte zustimmen.</div></div></div>
<div class="notice">Demo-Checkout: Die Bestellung wird als Anfrage an unser Team übermittelt. Für den Live-Betrieb wird die Kasse an das Shop-System (Zahlung, Bestellbestätigung) angebunden.</div>
<button class="btn btn-cta btn-lg btn-block" type="submit">Verbindlich anfragen</button><p id="done" hidden class="notice">Danke! Bitte senden Sie die vorbereitete E-Mail in Ihrem Mailprogramm ab.</p></form></div>
<aside class="summary"><h2>Ihre Bestellung</h2><div id="orderlines"></div><div class="total" style="display:flex;justify-content:space-between;border-top:2px solid var(--line);margin-top:8px;padding-top:12px;font:700 1.25rem var(--f-h)"><span>Gesamt</span><span id="o-tot">–</span></div><small>inkl. MwSt., versandkostenfrei</small></aside></div>'''
    page("kasse.html", "Kasse | Italia Camper 24", "Kasse", body, [], noindex=True)
    body = f'''<div class="page-head"><div class="wrap"><h1 id="sh">Suche</h1><p id="sq"></p></div></div><div class="wrap" style="padding:28px 16px 56px"><form class="search big" role="search" action="suche.html">{ic("search")}<label class="sr" for="q2">Suchbegriff</label><input id="q2" name="q" type="search" placeholder="z. B. Anhängerkupplung Ducato 250" autocomplete="off"></form><div class="grid" id="sres" style="margin-top:28px"></div><p id="snone" hidden class="empty">Keine Treffer. Schreiben Sie uns – wir finden das passende Teil: <a href="angebot-anfordern.html">Angebot anfordern</a></p></div>'''
    page("suche.html", "Suche | Italia Camper 24", "Shop durchsuchen", body, [], noindex=True)
    page("404.html", "404 – Seite nicht gefunden | Italia Camper 24", "Seite nicht gefunden", f'<div class="wrap" style="text-align:center;padding:80px 16px"><h1>Seite nicht gefunden</h1><p>Die Seite gibt es leider nicht (mehr). Nutzen Sie den Fahrzeugfinder oder die Suche.</p><a class="btn btn-cta btn-lg" href="fahrzeugfinder.html">Zum Fahrzeugfinder</a></div>', [], noindex=True)

def system_files():
    urls = "".join(f'<url><loc>{U}/{"" if f == "index.html" else f}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>' for f, p in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /warenkorb.html\nDisallow: /kasse.html\nDisallow: /suche.html\n\nSitemap: {U}/sitemap.xml\n")
    llm = [f"# {SITE['name']}", "", f"> Fachhändler und Montagebetrieb für Wohnmobil-Nachrüstung seit {SITE['since']}: fahrzeugspezifische Anhängerkupplungen (Fiat Ducato, Citroën Jumper, Peugeot Boxer, Mercedes Sprinter, Ford Transit, Renault Master, Iveco Daily und über {sum(len(L) for L in COACHES.values())} Wohnmobil-Modelle), Luftfederung, Stützensysteme, Heckträger, Rangierhilfen. Versandkostenfrei in Deutschland, Montage in Bohmte (49163) und Diez (65582). Inhaberin: {SITE['owner']}.", "", "## Kategorien"]
    llm += [f"- [{c['name']}]({U}/{c['slug']}.html): {c['short']}" for c in CATEGORIES]
    llm += ["", "## Fahrzeuge"] + [f"- [{v[0]}]({U}/fahrzeug-{k}.html)" for k, v in BASES.items()] + [f"- [Wohnmobil-Hersteller]({U}/hersteller.html)", f"- [Fahrzeugfinder]({U}/fahrzeugfinder.html)"]
    llm += ["", "## Service", f"- [Montage-Service]({U}/montage-service.html)", f"- [Versand & Zahlung]({U}/versand-zahlung.html)", f"- [FAQ]({U}/faq.html)", f"- [Ratgeber]({U}/ratgeber.html)", f"- Telefon: {SITE['phone']} (24 h)", f"- WhatsApp: https://wa.me/{SITE['wa']}", f"- E-Mail: {SITE['email']}"]
    open(os.path.join(OUT, "llms.txt"), "w").write("\n".join(llm) + "\n")
    open(os.path.join(OUT, "assets", "favicon.svg"), "w").write(LOGO_SVG)
    js = "window.IC_IDX=" + json.dumps(IDX, ensure_ascii=False, separators=(",", ":")) + ";window.IC_MAIL=" + json.dumps(SITE["email"]) + ";window.IC_WA=" + json.dumps(SITE["wa"]) + ";"
    open(os.path.join(OUT, "assets", "js", "catalog-index.js"), "w", encoding="utf-8").write(js)

if __name__ == "__main__":
    import shutil
    for f in os.listdir(OUT):
        if f.endswith(".html") or f in ("sitemap.xml", "robots.txt", "llms.txt"): os.remove(os.path.join(OUT, f))
    home(); finder_page(); hersteller_pages()
    for c in CATEGORIES: category_page(c)
    for p in PRODUCTS: product_page(p)
    for m, (lbl, grp) in BASES.items():
        make_page(m)
        for s in SERIES[grp]: series_page(m, s[0])
    blog_pages(); info_pages(); forms(); cart_pages(); system_files()
    print(len(PAGES), "indexierbare Seiten;", len([f for f in os.listdir(OUT) if f.endswith('.html')]), "HTML-Dateien gesamt")
