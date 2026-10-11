#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt die statische Website in public/.

    python3 build/build.py                 # Live-Version nach public/
    python3 build/build.py --preview DIR   # Vorschau mit relativen Links (zum Ansehen ohne Server)

Benötigt nur Python 3, keine weiteren Pakete.
"""
import argparse
import datetime
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from content import BIZ, SERVICES, ARTICLES, REASONS, COMPARE_ROWS, HOME_FAQ, CHECKLIST, AREA, AREA_REGIONS, TOWNS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DOMAIN = BIZ["domain"]
TODAY = datetime.date.today()
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]
STAND = f"{MONTHS[TODAY.month - 1]} {TODAY.year}"

PREVIEW = False  # wird in main() gesetzt
DRAFT = True     # Entwurfsmodus von Markentrix; mit --final ausschalten
OWNER = "Markentrix"
DRAFT_ASSETS = Path(__file__).resolve().parent / "draft_assets"


def de_month(iso):
    """'2026-10-11' -> 'Oktober 2026'"""
    y, m, _ = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"

# Alte Adresse (psschneider.de bisher) -> neue Adresse. Wird zu 301-Weiterleitungen.
REDIRECTS = [
    ("/start/", "/"),
    ("/LEISTUNGEN/", "/leistungen/"),
    ("/LEISTUNGEN/Haftpflichtschaden-Gutachten/", "/leistungen/haftpflichtschaden-gutachten/"),
    ("/LEISTUNGEN/Beweissicherungsgutachten/", "/leistungen/beweissicherungsgutachten/"),
    ("/LEISTUNGEN/Leasingruecknahme-Gutachten/", "/leistungen/leasingruecknahme-gutachten/"),
    ("/LEISTUNGEN/Wertgutachten/", "/leistungen/wertgutachten/"),
    ("/LEISTUNGEN/Restwertermittlung/", "/leistungen/restwertermittlung/"),
    ("/Gruende-fuer-ein-Gutachten/", "/gruende-fuer-ein-gutachten/"),
    ("/UNFALL-CHECKLISTE/", "/unfall-checkliste/"),
    ("/kontakt/impressum/", "/impressum/"),
    ("/kontakt/datenschutz/", "/datenschutz/"),
    ("/kontakt/datenschutz/index.php/", "/datenschutz/"),
]

# ---------------------------------------------------------------- Helfer

def esc(s):
    return html.escape(s, quote=True)


def u(slug, depth):
    """Adresse einer Seite. Live: /slug/ — Vorschau: relativer Pfad zur index.html."""
    if PREVIEW:
        rel = "../" * depth
        return rel + (slug + "/index.html" if slug else "index.html")
    return "/" + (slug + "/" if slug else "")


def asset(name, depth):
    return ("../" * depth if PREVIEW else "/") + "assets/" + name


def rootfile(name, depth):
    return ("../" * depth if PREVIEW else "/") + name


def abs_url(slug):
    return DOMAIN + "/" + (slug + "/" if slug else "")


# Weiche Trennstellen für lange Wörter in Überschriften, damit sie auf schmalen Handys umbrechen.
SHY = {
    "Wiederbeschaffungswert": "Wieder\u00adbeschaffungs\u00adwert",
    "Wiederbeschaffungsaufwand": "Wieder\u00adbeschaffungs\u00adaufwand",
    "Beweissicherungsgutachten": "Beweis\u00adsicherungs\u00adgutachten",
    "Haftpflichtschaden": "Haft\u00adpflicht\u00adschaden",
    "Haftpflichtversicherung": "Haft\u00adpflicht\u00adversicherung",
    "Sachverständigenorganisation": "Sach\u00adverständigen\u00adorganisation",
    "Restwertermittlung": "Rest\u00adwert\u00adermittlung",
    "Nutzungsausfall": "Nutzungs\u00adausfall",
    "Leasingrücknahme": "Leasing\u00adrück\u00adnahme",
    "Unfallanalytisches": "Unfall\u00adanalytisches",
    "Kraftfahrzeugtechniker": "Kraft\u00adfahrzeug\u00adtechniker",
    "Kraftfahrzeugwesen": "Kraft\u00adfahrzeug\u00adwesen",
    "Wertminderung": "Wert\u00adminderung",
    "Schadenregulierung": "Schaden\u00adregulierung",
    "Schadensabwicklung": "Schadens\u00adabwicklung",
    "Fahrzeugtechnik": "Fahrzeug\u00adtechnik",
    "Oldtimer-Wertgutachten": "Oldtimer-Wert\u00adgutachten",
    "Gutachterkosten": "Gutachter\u00adkosten",
    "Unfallgeschädigte": "Unfall\u00adgeschädigte",
    "Rechtsstreitigkeiten": "Rechtsstreitig\u00adkeiten",
}
_SHY_RE = re.compile("|".join(sorted(map(re.escape, SHY), key=len, reverse=True)))
_HEAD_RE = re.compile(r"(<(h[123]|strong)\b[^>]*>)(.*?)(</\2>)", re.S)


def soften(markup):
    """Fügt in Überschriften unsichtbare Trennstellen ein, nur im Text, nie in Tags oder Adressen."""
    def fix(m):
        parts = re.split(r"(<[^>]+>)", m.group(3))
        parts = [x if x.startswith("<") else _SHY_RE.sub(lambda w: SHY[w.group(0)], x) for x in parts]
        return m.group(1) + "".join(parts) + m.group(4)
    return _HEAD_RE.sub(fix, markup)


# ---------------------------------------------------------------- Einsatzgebiet

_UM = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.translate(_UM).lower()).strip("-")


def km_between(lat1, lon1, lat2, lon2):
    """Luftlinie in Kilometern (Haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def xy_km(lat, lon):
    """Versatz in Kilometern von Celle: (Ost, Nord)."""
    c_lat, c_lon = AREA["center"]
    return ((lon - c_lon) * 111.32 * math.cos(math.radians(c_lat)), (lat - c_lat) * 111.32)


def compass(lat, lon):
    dx, dy = xy_km(lat, lon)
    names = ["Norden", "Nordosten", "Osten", "Südosten", "Süden", "Südwesten", "Westen", "Nordwesten"]
    return names[int(((math.degrees(math.atan2(dx, dy)) + 22.5) % 360) // 45)]


def prepare_towns():
    c_lat, c_lon = AREA["center"]
    for t in TOWNS:
        if t.get("page"):
            t["slug"] = "einsatzgebiet/" + slugify(t["name"])
            dist = km_between(c_lat, c_lon, t["lat"], t["lon"])
            t["dist"] = max(5, int(round(dist / 5.0) * 5))
            t["dir"] = compass(t["lat"], t["lon"])
            assert dist <= AREA["radius_km"], f"{t['name']} liegt außerhalb des Einsatzgebiets"


prepare_towns()
PAGE_TOWNS = [t for t in TOWNS if t.get("page")]


def area_served():
    c_lat, c_lon = AREA["center"]
    return [{"@type": "City", "name": "Celle"},
            {"@type": "AdministrativeArea", "name": "Landkreis Celle"},
            {"@type": "GeoCircle", "geoMidpoint": {"@type": "GeoCoordinates", "latitude": c_lat, "longitude": c_lon},
             "geoRadius": str(AREA["radius_km"] * 1000)}]


LINK_RE = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")


def rich(text, depth):
    """Maskiert Text und wandelt [[slug|Text]] in Links um."""
    out = esc(text)
    return LINK_RE.sub(lambda m: f'<a href="{u(m.group(1), depth)}">{m.group(2)}</a>', out)


def plain(text):
    """Text ohne Link-Markup, für strukturierte Daten."""
    return LINK_RE.sub(lambda m: m.group(2), text)


ICONS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6.2 6.2l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "whatsapp": '<path d="M21 11.5a8.4 8.4 0 0 1-12.6 7.3L3 21l2.2-5.2A8.5 8.5 0 1 1 21 11.5z"/><path d="M9.5 9.2c.3 1.6 1.9 3.5 3.6 4.3l1.2-1.2 1.9.8v1.6c-3.6.5-7.7-3.3-7.9-7.1h1.7l.8 1.8-1.3 1z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "check": '<path d="m5 12 5 5L20 7"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "car": '<path d="M3 13l2-5a2 2 0 0 1 1.9-1.3h10.2A2 2 0 0 1 19 8l2 5"/><path d="M2 13h20v5a1 1 0 0 1-1 1h-2a1 1 0 0 1-1-1v-1H6v1a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z"/><path d="M6.5 15.5h1M16.5 15.5h1"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/><path d="M8 10.5h5M10.5 8v5"/>',
    "key": '<circle cx="8" cy="14" r="4"/><path d="m11 11 9-9M15 7l2 2M18 4l2 2"/>',
    "tag": '<path d="M20 12.5 12.5 20 4 11.5V4h7.5z"/><circle cx="8" cy="8" r="1.3"/>',
    "euro": '<path d="M17 6.5A5.5 5.5 0 0 0 7.2 9H5v2h1.6a6 6 0 0 0 0 2H5v2h2.2A5.5 5.5 0 0 0 17 17.5"/><path d="M8 11h7M8 13h7"/>',
    "chart": '<path d="M3 17 9 7l4 6 3-4 5 8z"/><path d="M3 21h18"/>',
}


def svg(name, sw="2", cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def ld(graph):
    data = {"@context": "https://schema.org", "@graph": graph}
    s = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{s}\n</script>'


# ---------------------------------------------------------------- Strukturierte Daten

def address_node():
    return {"@type": "PostalAddress", "streetAddress": BIZ["street"], "postalCode": BIZ["zip"],
            "addressLocality": BIZ["city"], "addressCountry": "DE"}


def business_ref():
    return {"@type": "ProfessionalService", "@id": DOMAIN + "/#business", "name": BIZ["legal_name"],
            "url": DOMAIN + "/", "telephone": "+49 172 5178150", "address": address_node()}


def business_node():
    offers = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["short"], "url": abs_url(s["slug"])}}
              for s in SERVICES]
    return {
        "@type": "ProfessionalService",
        "@id": DOMAIN + "/#business",
        "name": BIZ["legal_name"],
        "alternateName": "PS Schneider Kfz-Gutachter Celle",
        "description": "Unabhängiger Kfz-Sachverständiger in Celle für Haftpflichtschaden-Gutachten, Beweissicherung, "
                       "Leasingrückgabe, Wertgutachten, Restwertermittlung und Unfallanalyse.",
        "url": DOMAIN + "/",
        "logo": DOMAIN + "/assets/logo.png",
        "image": [DOMAIN + "/assets/og-image.jpg", DOMAIN + "/assets/portrait.jpg"],
        "telephone": "+49 172 5178150",
        "email": BIZ["email"],
        "address": address_node(),
        "areaServed": area_served(),
        "founder": {"@id": DOMAIN + "/#person"},
        "knowsAbout": ["Kfz-Gutachten", "Haftpflichtschaden", "Restwertermittlung", "Wertgutachten",
                       "Oldtimer-Bewertung", "Leasingrückgabe", "Unfallanalyse"],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Leistungen", "itemListElement": offers},
    }


def person_node():
    return {
        "@type": "Person",
        "@id": DOMAIN + "/#person",
        "name": BIZ["person"],
        "jobTitle": BIZ["role"] + ", " + BIZ["craft"],
        "image": DOMAIN + "/assets/portrait.jpg",
        "worksFor": {"@id": DOMAIN + "/#business"},
        "address": address_node(),
        "telephone": "+49 172 5178150",
        "email": BIZ["email"],
    }


def website_node():
    return {"@type": "WebSite", "@id": DOMAIN + "/#website", "url": DOMAIN + "/", "name": BIZ["name"],
            "inLanguage": "de-DE", "publisher": {"@id": DOMAIN + "/#business"}}


def faq_node(items):
    return {"@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in items]}


def breadcrumb_node(trail):
    """trail: Liste (Name, slug) ohne Startseite, die Startseite wird vorangestellt."""
    items = [("Startseite", "")] + trail
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(s)} for i, (n, s) in enumerate(items)]}


# ---------------------------------------------------------------- Layout

NAV = [
    ("Leistungen", "leistungen", "leistungen"),
    ("Ratgeber", "ratgeber", "ratgeber"),
    ("Über mich", "", "#ueber-mich"),
    ("Unfall-Checkliste", "unfall-checkliste", "unfall-checkliste"),
    ("Fragen", "", "#faq"),
    ("Kontakt", "kontakt", "kontakt"),
]


def logo_imgs(d):
    return (f'<img class="logo logo-light" src="{asset("logo.png", d)}" '
            f'alt="PS Schneider – Sachverständiger für Fahrzeugtechnik" width="546" height="152">'
            f'<img class="logo logo-dark" src="{asset("logo-dark.png", d)}" alt="" width="546" height="152">')


def header(d, slug):
    items = []
    for label, target, key in NAV:
        if key.startswith("#"):
            href = u("", d) + key
            cur = ""
        else:
            href = u(target, d)
            active = slug == target or slug.startswith(target + "/")
            cur = ' aria-current="page"' if active else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return f'''<header class="site-header" id="top">
  <div class="wrap">
    <a class="brand" href="{u("", d)}" aria-label="PS Schneider, zur Startseite">{logo_imgs(d)}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav" aria-label="Menü öffnen">
      <span class="ic-menu">{svg("menu")}</span><span class="ic-close">{svg("close")}</span>
    </button>
    <nav class="primary-nav" id="primary-nav" aria-label="Hauptnavigation">
      <ul>
        {"".join(items)}
      </ul>
    </nav>
    <a class="btn btn-primary header-cta" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
  </div>
</header>'''


def footer(d):
    svc = "\n      ".join(f'<a href="{u(s["slug"], d)}">{_SHY_RE.sub(lambda w: SHY[w.group(0)], esc(s["short"]))}</a>' for s in SERVICES)
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="col">
      {logo_imgs(d)}
      <span>{BIZ["craft"]} {BIZ["person"]}</span>
      <span>{BIZ["street"]} · {BIZ["zip"]} {BIZ["city"]}</span>
    </div>
    <div class="col">
      <strong>Leistungen</strong>
      {svc}
    </div>
    <div class="col">
      <strong>Kontakt</strong>
      <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>
      <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a>
      <a href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">WhatsApp</a>
      <a href="{u("einsatzgebiet", d)}">Einsatzgebiet</a>
      <a href="{u("ratgeber", d)}">Ratgeber</a>
      <a href="{u("gruende-fuer-ein-gutachten", d)}">Gründe für ein Gutachten</a>
      <a href="{u("unfall-checkliste", d)}">Unfall-Checkliste</a>
      <a href="{u("kontakt", d)}">Anfrage senden</a>
    </div>
    <div class="legal">
      <span>© <span data-year>{TODAY.year}</span> {BIZ["person"]}{f" · Gestaltung und Umsetzung © {TODAY.year} {OWNER}" if DRAFT else ""}</span>
      <span><a href="{u("impressum", d)}">Impressum</a> · <a href="{u("datenschutz", d)}">Datenschutzerklärung</a></span>
    </div>
  </div>
</footer>'''


def action_bar(d):
    return f'''<nav class="action-bar" aria-label="Schnellkontakt">
  <a class="primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}Anrufen</a>
  <a href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
  <a href="{u("kontakt", d)}">{svg("mail")}Anfrage</a>
</nav>'''


def page_html(*, slug, d, title, desc, body, graph=None, noindex=False, canonical_slug=None, og_title=None):
    if len(title) > 66:
        print(f"  Hinweis: Titel mit {len(title)} Zeichen: {title}", file=sys.stderr)
    if len(desc) > 165:
        print(f"  Hinweis: Beschreibung mit {len(desc)} Zeichen: {slug or 'start'}", file=sys.stderr)
    noindex = noindex or DRAFT
    canon = abs_url(slug if canonical_slug is None else canonical_slug)
    if DRAFT:
        robots = "noindex, nofollow, noarchive, nosnippet, noimageindex"
    else:
        robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"
    draft_comment = (f"<!-- © {TODAY.year} {OWNER}. Alle Rechte vorbehalten. Entwurf zur Ansicht. "
                     "Nutzung, Vervielfältigung, Bearbeitung oder Weitergabe nur mit schriftlicher Zustimmung. -->\n") if DRAFT else ""
    draft_meta = f'\n<meta name="copyright" content="© {TODAY.year} {OWNER}. Alle Rechte vorbehalten.">' if DRAFT else ""
    draft_css = f'\n<link rel="stylesheet" href="{asset("draft.css", d)}">' if DRAFT else ""
    draft_top = (f'<div class="draft-bar" role="note"><strong>Entwurf</strong>'
                 f'<span>© {TODAY.year} {OWNER}</span><span class="draft-mid">· Alle Rechte vorbehalten</span><span class="draft-long">· Nur zur Ansicht, keine Weitergabe oder Veröffentlichung</span></div>\n'
                 '<div class="draft-wm" aria-hidden="true"></div>\n') if DRAFT else ""
    draft_js = f'\n<script src="{asset("draft.js", d)}" defer></script>' if DRAFT else ""
    og = DOMAIN + "/assets/og-image.jpg"
    ld_block = ld(graph) if graph else ""
    canon_tag = "" if noindex else f'<link rel="canonical" href="{canon}">'
    og_tags = "" if noindex else f'''
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="{esc(BIZ["name"])}">
<meta property="og:title" content="{esc(og_title or title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="PS Schneider, Sachverständiger für Fahrzeugtechnik in Celle">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(og_title or title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og}">'''
    return soften(f'''<!DOCTYPE html>
{draft_comment}<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
{canon_tag}
<meta name="theme-color" content="#D71A21">
<meta name="format-detection" content="telephone=no">{draft_meta}{og_tags}
<link rel="icon" href="{rootfile("favicon.ico", d)}" sizes="48x48">
<link rel="icon" href="{rootfile("icon-192.png", d)}" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="{rootfile("apple-touch-icon.png", d)}">
<link rel="preload" href="{asset("fonts/BarlowCondensed-700.woff2", d)}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{asset("fonts/Barlow-400.woff2", d)}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{asset("site.css", d)}">{draft_css}
{ld_block}
</head>
<body>
<a class="skip-link" href="#main">Zum Inhalt springen</a>
{draft_top}{header(d, slug)}
<main id="main">
{body}
</main>
{footer(d)}
{action_bar(d)}
<script src="{asset("site.js", d)}" defer></script>{draft_js}
</body>
</html>
''')


# ---------------------------------------------------------------- Bausteine

def crumbs(trail, d):
    """trail: Liste (Name, slug); letzter Eintrag ist die aktuelle Seite."""
    parts = [f'<li><a href="{u("", d)}">Startseite</a></li>']
    for i, (name, s) in enumerate(trail):
        if i == len(trail) - 1:
            parts.append(f'<li><span aria-current="page">{esc(name)}</span></li>')
        else:
            parts.append(f'<li><a href="{u(s, d)}">{esc(name)}</a></li>')
    return f'<nav class="crumbs" aria-label="Brotkrumen"><ol>{"".join(parts)}</ol></nav>'


def page_hero(trail, d, tag, h1, lede, byline=True, stand=None):
    by = ""
    if byline:
        by = (f'<p class="byline"><span>Von <strong>{BIZ["person"]}</strong>, {BIZ["role"]}, {BIZ["craft"]}</span>'
              f'<span>Stand: {stand or STAND}</span></p>')
    return f'''<section class="page-hero">
  <div class="wrap">
    {crumbs(trail, d)}
    <p class="eyebrow">{esc(tag)}</p>
    <h1>{esc(h1)}</h1>
    <p class="lede">{rich(lede, d)}</p>
    {by}
  </div>
</section>'''


def render_blocks(blocks, d):
    out = []
    for b in blocks:
        if isinstance(b, str):
            out.append(f"<p>{rich(b, d)}</p>")
        elif b[0] in ("ul", "ol"):
            lis = "".join(f"<li>{rich(x, d)}</li>" for x in b[1])
            out.append(f"<{b[0]}>{lis}</{b[0]}>")
        elif b[0] == "callout":
            out.append(f'<div class="callout"><p>{rich(b[1], d)}</p></div>')
    return "\n        ".join(out)


def side_cta(d, heading="Direkt erreichbar", text="Schildern Sie mir kurz Ihre Lage. Sie erhalten eine unverbindliche Beratung und ein individuelles Angebot."):
    return f'''<aside class="side-cta" aria-label="Kontakt">
  <h2>{esc(heading)}</h2>
  <p>{esc(text)}</p>
  <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
  <a class="btn btn-secondary" href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
  <div class="mini">
    <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a>
    <span>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}</span>
    <a href="{u("kontakt", d)}">Anfrage per Formular</a>
  </div>
</aside>'''


def faq_section(items, d, title="Häufige Fragen", open_first=False, extra_class=""):
    det = []
    for i, (q, a) in enumerate(items):
        o = " open" if (open_first and i == 0) else ""
        det.append(f'<details{o}><summary>{esc(q)}</summary><div class="answer"><p>{rich(a, d)}</p></div></details>')
    return f'<div class="faq {extra_class}">' + "".join(det) + "</div>"


def cta_band(d, title="Unfall passiert? Rufen Sie an.", text="Ich berate Sie unverbindlich und vereinbare kurzfristig einen Besichtigungstermin."):
    return f'''<section class="cta-band" aria-label="Kontakt aufnehmen">
  <div class="wrap">
    <div class="copy">
      <h2>{esc(title)}</h2>
      <p>{esc(text)}</p>
    </div>
    <div class="hero-actions">
      <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
      <a class="btn btn-secondary" href="{u("kontakt", d)}">Anfrage senden</a>
    </div>
  </div>
</section>'''


def related(slugs, d):
    by_slug = {s["slug"]: s for s in SERVICES}
    by_slug.update({a["slug"]: a for a in ARTICLES})
    extra = {
        "leistungen": ("Alle Leistungen", "Sechs Gutachten im Überblick und welches zu Ihrer Situation passt."),
        "ratgeber": ("Ratgeber", "Antworten auf häufige Fragen nach dem Unfall."),
        "einsatzgebiet": ("Einsatzgebiet", "Landkreis Celle und Umkreis von 50 Kilometern."),
        "gruende-fuer-ein-gutachten": ("Gründe für ein Kfz-Gutachten", "Warum ein Gutachten mehr bringt als ein Kostenvoranschlag."),
        "unfall-checkliste": ("Unfall-Checkliste", "Die ersten Schritte nach einem Unfall zum Abhaken."),
        "kontakt": ("Kontakt", "Anfrage senden oder direkt anrufen."),
    }
    lis = []
    for s in slugs:
        if s in by_slug:
            name, text = by_slug[s]["short"], by_slug[s]["lede"]
        else:
            name, text = extra[s]
        lis.append(f'<li><a href="{u(s, d)}"><strong>{esc(name)}</strong><span>{esc(text)}</span></a></li>')
    return f'<ul class="related">{"".join(lis)}</ul>'


def service_cards(d):
    out = []
    for s in SERVICES:
        out.append(f'''<li class="service">
          <span class="icon" aria-hidden="true">{svg(s["icon"], "1.8")}</span>
          <span class="tag">{esc(s["tag"])}</span>
          <h3><a href="{u(s["slug"], d)}">{esc(s["short"])}</a></h3>
          <p>{esc(s["card"])}</p>
          <span class="more" aria-hidden="true">Mehr erfahren →</span>
        </li>''')
    return '<ul class="services">' + "\n".join(out) + "</ul>"


def contact_rows():
    wa = BIZ["phone_tel"].lstrip("+")
    return f'''<ul class="contact-rows">
        <li><span class="k">Telefon</span><span class="v"><a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a></span><button class="copy-btn" type="button" data-copy="{BIZ["phone_copy"]}">kopieren</button></li>
        <li><span class="k">WhatsApp</span><span class="v"><a href="https://wa.me/{wa}" target="_blank" rel="noopener">+49 172 517 81 50</a></span><span></span></li>
        <li><span class="k">E-Mail</span><span class="v"><a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></span><button class="copy-btn" type="button" data-copy="{BIZ["email"]}">kopieren</button></li>
        <li><span class="k">Adresse</span><span class="v">{BIZ["street"]}<br>{BIZ["zip"]} {BIZ["city"]}</span><span></span></li>
        <li><span class="k">Termine</span><span class="v">Besichtigung nach Absprache, {AREA["label"]}</span><span></span></li>
      </ul>'''


def contact_compact(d):
    wa = BIZ["phone_tel"].lstrip("+")
    return f'''<section class="section section--surface-top contact-compact" id="kontakt" aria-labelledby="kontakt-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Kontakt</p>
      <h2 id="kontakt-title">Rufen Sie an oder schreiben Sie</h2>
      <p class="lede">Für eine unverbindliche Erstberatung, einen Besichtigungstermin oder ein individuelles Angebot. Am schnellsten erreichen Sie mich telefonisch oder per WhatsApp.</p>
    </div>
    <div class="contact-compact-grid">
      <div>{contact_rows()}</div>
      <div class="contact-actions">
        <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
        <a class="btn btn-secondary" href="https://wa.me/{wa}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
        <a class="btn btn-secondary" href="{u("kontakt", d)}">{svg("mail")}Anfrage per Formular</a>
      </div>
    </div>
  </div>
</section>'''


def contact_section(d, h2="Fragen Sie unverbindlich an", wrap_class="section contact section--surface-top"):
    wa = BIZ["phone_tel"].lstrip("+")
    return f'''<section class="{wrap_class}" id="kontakt" aria-labelledby="kontakt-title">
  <div class="wrap">
    <div class="contact-info">
      <p class="eyebrow">Kontakt</p>
      <h2 id="kontakt-title">{esc(h2)}</h2>
      <p class="lede">Für eine unverbindliche Erstberatung, einen Besichtigungstermin oder ein individuelles Angebot. Am schnellsten erreichen Sie mich telefonisch oder per WhatsApp.</p>
      {contact_rows()}
      <p class="contact-hint">{BIZ["person"]} · {BIZ["role"]} · {BIZ["craft"]}</p>
    </div>

    <form class="form" id="contact-form" novalidate>
      <div class="row">
        <div class="field">
          <label for="f-name">Name <span class="req" aria-hidden="true">*</span></label>
          <input type="text" id="f-name" name="name" autocomplete="name" autocapitalize="words" enterkeyhint="next" required>
        </div>
        <div class="field">
          <label for="f-phone">Telefon</label>
          <input type="tel" id="f-phone" name="phone" autocomplete="tel" inputmode="tel" enterkeyhint="next">
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label for="f-email">E-Mail <span class="req" aria-hidden="true">*</span></label>
          <input type="email" id="f-email" name="email" autocomplete="email" inputmode="email" autocapitalize="none" spellcheck="false" enterkeyhint="next" required>
        </div>
        <div class="field">
          <label for="f-subject">Anliegen <span class="req" aria-hidden="true">*</span></label>
          <select id="f-subject" name="subject" required>
            <option value="">Bitte wählen</option>
            {"".join(f"<option>{esc(s['short'])}</option>" for s in SERVICES)}
            <option>Sonstige Frage</option>
          </select>
        </div>
      </div>
      <div class="field">
        <label for="f-message">Nachricht <span class="req" aria-hidden="true">*</span></label>
        <textarea id="f-message" name="message" required placeholder="Kurz: Was ist passiert, welches Fahrzeug, wann passt Ihnen ein Termin?"></textarea>
        <span class="help">* Pflichtfelder</span>
      </div>
      <label class="consent">
        <input type="checkbox" id="f-consent" name="consent" required>
        <span>Ich habe die <a href="{u("datenschutz", d)}">Datenschutzerklärung</a> gelesen und bin einverstanden, dass meine Angaben zur Bearbeitung meiner Anfrage verwendet werden.</span>
      </label>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit">Anfrage senden</button>
        <span class="form-status" id="form-status" role="status" aria-live="polite"></span>
      </div>
      <pre class="form-preview" id="form-preview"></pre>
    </form>
  </div>
</section>'''


def checklist_html():
    lis = []
    for i, (t, sub) in enumerate(CHECKLIST, 1):
        lis.append(f'<li><label><input type="checkbox" id="chk-{i}"><span class="txt"><strong>{esc(t)}</strong><span>{esc(sub)}</span></span></label></li>')
    return "\n".join(lis)


def emergency_card(d):
    return f'''<aside class="emergency" aria-label="Notrufnummern und W-Fragen">
  <div class="numbers">
    <a href="tel:110"><b>110</b><small>Polizei</small></a>
    <a href="tel:112"><b>112</b><small>Rettungsdienst</small></a>
  </div>
  <div>
    <h3>Die W-Fragen beim Notruf</h3>
    <ol>
      <li><b>Wo</b><span>ist es passiert?</span></li>
      <li><b>Was</b><span>ist passiert?</span></li>
      <li><b>Wie viele</b><span>Verletzte gibt es?</span></li>
      <li><b>Welche</b><span>Verletzungen?</span></li>
      <li><b>Warten</b><span>auf Rückfragen.</span></li>
    </ol>
  </div>
  <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">Sachverständigen anrufen</a>
</aside>'''


# ---------------------------------------------------------------- Seiten

def build_home():
    d = 0
    faq = HOME_FAQ
    body = f'''
  <section class="hero" aria-labelledby="hero-title">
    <div class="wrap">
      <div class="hero-copy">
        <p class="eyebrow">Unverschuldeter Unfall? Wir beraten Sie gerne.</p>
        <h1 id="hero-title">Kfz-Gutachter in Celle: <em>unabhängig, schnell, auf Ihrer Seite.</em></h1>
        <p class="lede">Persönliche, kompetente Beratung bei der Schadensabwicklung. Ihr Kfz-Gutachten wird schnell und unkompliziert erstellt und ist unabhängig von jeder Versicherung.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}Jetzt anrufen</a>
          <a class="btn btn-secondary" href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
          <a class="btn btn-ghost" href="{u("leistungen", d)}">Leistungen ansehen →</a>
        </div>
        <p class="hero-note">{svg("shield")}<span>Bei einem unverschuldeten Unfall trägt in der Regel die Haftpflichtversicherung des Unfallverursachers die Kosten für Ihr Gutachten. Sie haben das Recht, den Sachverständigen frei zu wählen.</span></p>
      </div>
      <div class="hero-visual">
        <figure class="portrait">
          <img src="{asset("portrait.jpg", d)}" alt="Patric Schneider, Kfz-Sachverständiger in Celle" width="543" height="618" fetchpriority="high">
        </figure>
        <div class="id-card">
          <div>
            <div class="name">{BIZ["person"]}</div>
            <div class="role">{BIZ["craft"]} · {BIZ["role"]}</div>
          </div>
          <dl>
            <dt>Telefon</dt><dd><a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a></dd>
            <dt>E-Mail</dt><dd><a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></dd>
            <dt>Standort</dt><dd>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}</dd>
          </dl>
        </div>
      </div>
    </div>
  </section>

  <section class="trust" aria-label="Erfahrung und Grundsätze">
    <div class="wrap">
      <ul>
        <li><span class="num">30<small>+</small></span><span class="lbl">Jahre Erfahrung im Kraftfahrzeugwesen</span></li>
        <li><span class="num">17</span><span class="lbl">Jahre Kfz-Sachverständiger bei Europas größter Sachverständigenorganisation</span></li>
        <li><span class="num">100<small>%</small></span><span class="lbl">unabhängig von Versicherungen und Werkstätten</span></li>
        <li><span class="num">0<small>€</small></span><span class="lbl">Kosten für Sie im Haftpflichtfall. Die gegnerische Versicherung zahlt in der Regel.</span></li>
      </ul>
    </div>
  </section>

  <section class="section" id="leistungen" aria-labelledby="leistungen-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Leistungen</p>
        <h2 id="leistungen-title">Kfz-Gutachten in Celle für jede Situation</h2>
        <p class="lede">Pkw, Lkw, Nutzfahrzeug, Motorrad, Oldtimer oder E-Bike. Jedes Gutachten wird neutral erstellt und ist vor Gericht anerkannt.</p>
      </div>
      {service_cards(d)}
    </div>
  </section>

  <section class="section section--surface" id="ablauf" aria-labelledby="ablauf-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">So läuft es ab</p>
        <h2 id="ablauf-title">Vom Anruf bis zur Regulierung in vier Schritten</h2>
        <p class="lede">Sie kümmern sich um das Wesentliche. Ich übernehme Dokumentation und Bewertung und unterstütze Sie im Umgang mit Versicherung, Werkstatt oder Anwalt.</p>
      </div>
      <ol class="steps">
        <li><h3>Kontakt aufnehmen</h3><p>Rufen Sie an oder schreiben Sie per WhatsApp. Wir klären kurz den Unfallhergang und was Sie jetzt brauchen.</p></li>
        <li><h3>Besichtigung</h3><p>Termin nach Absprache. Alle Schäden werden schriftlich und mit Fotos erfasst, auch Vor- und Altschäden.</p></li>
        <li><h3>Gutachten</h3><p>Reparaturkosten, Wertminderung, Reparaturdauer, bei Totalschaden Restwert und Wiederbeschaffungswert. Zügig und gerichtsfest.</p></li>
        <li><h3>Regulierung</h3><p>Sie legen das Gutachten der Versicherung vor und entscheiden auf sicherer Grundlage: reparieren, fiktiv abrechnen oder verkaufen.</p></li>
      </ol>
    </div>
  </section>

  <section class="section" id="warum" aria-labelledby="warum-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Gutachten statt Kostenvoranschlag</p>
        <h2 id="warum-title">Warum ein Kostenvoranschlag nach dem Unfall nicht reicht</h2>
        <p class="lede">Versicherungen akzeptieren gern einen Kostenvoranschlag mit Fotos und behaupten, einen Sachverständigen müssten Sie selbst bezahlen. Im Haftpflichtfall ist das gesetzlich anders geregelt.</p>
      </div>
      <div class="reasons">
        <article><h3>Kostenfreiheit</h3><p>Als Geschädigter dürfen Sie den Sachverständigen frei wählen. Die Kosten übernimmt in der Regel die Haftpflichtversicherung des Unfallverursachers.</p></article>
        <article><h3>Finanzielle Sicherheit</h3><p>Neben den Reparaturkosten erfasst das Gutachten Wertminderung, Reparaturdauer und Ausfallzeiten. Erst damit sind Ihre Ansprüche vollständig beziffert.</p></article>
        <article><h3>Beweissicherung</h3><p>Lehnt die gegnerische Versicherung Verantwortung ab, sind Sie mit einem Gutachten auf der sicheren Seite. Im Streitfall wird es vor Gericht anerkannt.</p></article>
      </div>
      <p><a class="btn btn-secondary" href="{u("gruende-fuer-ein-gutachten", d)}">Alle Gründe und Vergleich ansehen →</a></p>
    </div>
  </section>

  <section class="section deep about" id="ueber-mich" aria-labelledby="about-title">
    <div class="wrap">
      <figure class="about-photo">
        <img src="{asset("portrait.jpg", d)}" alt="Patric Schneider im Porträt" width="543" height="618" loading="lazy">
      </figure>
      <div class="about-copy">
        <p class="eyebrow">Über mich</p>
        <h2 id="about-title">Ein junges Unternehmen mit über 30 Jahren Erfahrung</h2>
        <p>Mein Name ist {BIZ["person"]}. Ich bin {BIZ["craft"]} und {BIZ["role"]} in Celle. 17 Jahre lang war ich als Kfz-Sachverständiger bei der größten Sachverständigenorganisation Deutschlands tätig und kenne alle Bereiche der Schadenregulierung aus der Praxis.</p>
        <p>Ob Schadengutachten nach einem Verkehrsunfall, unfallanalytisches Gutachten bei Rechtsstreitigkeiten oder Wertgutachten für Ihren geliebten Oldtimer: Sie bekommen Ihr Gutachten mit dem passenden Sachverstand, zügig und ohne Umwege.</p>
        <ul class="facts">
          <li>{svg("check", "2.2")}<span>{BIZ["craft"]}</span></li>
          <li>{svg("check", "2.2")}<span>17 Jahre Sachverständiger in Deutschlands größter Sachverständigenorganisation</span></li>
          <li>{svg("check", "2.2")}<span>Unabhängig von Versicherungen und Werkstätten</span></li>
          <li>{svg("check", "2.2")}<span>Kontinuierliche Weiterbildung, alle Fahrzeugarten</span></li>
        </ul>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{u("kontakt", d)}">Unverbindlich anfragen</a>
          <a class="btn btn-secondary" href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="unfall" aria-labelledby="unfall-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Unfall passiert?</p>
        <h2 id="unfall-title">Die ersten Schritte nach einem Unfall</h2>
        <p class="lede">Ruhe bewahren und der Reihe nach vorgehen. Die vollständige Checkliste zum Abhaken finden Sie auf einer eigenen Seite.</p>
      </div>
      <div class="checklist-grid">
        <div>
          <ol class="first-steps">
            {"".join(f"<li><div><strong>{esc(t)}</strong></div></li>" for t, _ in CHECKLIST)}
          </ol>
          <p class="checklist-foot"><a class="btn btn-secondary" href="{u("unfall-checkliste", d)}">Zur Unfall-Checkliste →</a></p>
        </div>
        {emergency_card(d)}
      </div>
    </div>
  </section>

  <section class="section" id="ratgeber" aria-labelledby="ratgeber-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Ratgeber</p>
        <h2 id="ratgeber-title">Antworten auf die häufigsten Fragen nach dem Unfall</h2>
        <p class="lede">Wertminderung, Totalschaden, Mietwagen und Kosten verständlich erklärt.</p>
      </div>
      {related([a["slug"] for a in ARTICLES[:3]], d)}
      <p class="more-row"><a class="btn btn-secondary" href="{u("ratgeber", d)}">Alle Ratgeber ansehen →</a></p>
    </div>
  </section>

  <section class="section section--surface" id="faq" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Häufige Fragen</p>
        <h2 id="faq-title">Was Unfallgeschädigte am häufigsten fragen</h2>
      </div>
      {faq_section(faq, d, open_first=True)}
    </div>
  </section>

  <section class="section" id="einsatzgebiet" aria-labelledby="gebiet-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Einsatzgebiet</p>
        <h2 id="gebiet-title">Im Landkreis Celle und im Umkreis von 50 Kilometern</h2>
        <p class="lede">Besichtigungstermine nach Absprache, von Celle bis Hannover, Gifhorn, Soltau und Walsrode.</p>
      </div>
      {town_chips([t for t in PAGE_TOWNS], d)}
      <p class="more-row"><a class="btn btn-secondary" href="{u("einsatzgebiet", d)}">Alle Orte im Einsatzgebiet →</a></p>
    </div>
  </section>

  {contact_compact(d)}
'''
    graph = [business_node(), person_node(), website_node(), faq_node(faq)]
    return dict(slug="", d=d,
                title="Kfz-Gutachter Celle | Unabhängiger Sachverständiger PS Schneider",
                desc="Unabhängiger Kfz-Sachverständiger in Celle: Unfallgutachten, Wertgutachten, Beweissicherung, Leasingrückgabe, Restwert. Patric Schneider, Kfz-Meister.",
                body=body, graph=graph)


def build_service(s):
    d = s["slug"].count("/") + 1
    trail = [("Leistungen", "leistungen"), (s["short"], s["slug"])]
    secs = []
    for sec in s["sections"]:
        secs.append(f'''<section>
        <h2>{esc(sec["h2"])}</h2>
        {render_blocks(sec["body"], d)}
      </section>''')
    rel = s["related"]
    body = f'''
  {page_hero(trail, d, s["tag"], s["h1"], s["lede"])}

  <div class="wrap page-grid">
    <article class="prose">
      {"".join(secs)}
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">Häufige Fragen zum {esc(s["short"])}</h2></div>
      {faq_section(s["faq"], d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">Das könnte Sie auch interessieren</h2></div>
      {related(rel, d)}
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [
        {"@type": "Service", "@id": abs_url(s["slug"]) + "#service", "name": s["short"], "serviceType": s["short"],
         "description": s["desc"], "url": abs_url(s["slug"]), "provider": business_ref(),
         "areaServed": area_served()},
        breadcrumb_node([("Leistungen", "leistungen"), (s["short"], s["slug"])]),
        faq_node(s["faq"]),
    ]
    return dict(slug=s["slug"], d=d, title=s["title"], desc=s["desc"], body=body, graph=graph)


def build_leistungen():
    d = 1
    rows = [
        ("Unverschuldeter Unfall, Schaden am Fahrzeug", "leistungen/haftpflichtschaden-gutachten", "Haftpflichtschaden-Gutachten"),
        ("Totalschaden, das Fahrzeug soll verkauft werden", "leistungen/restwertermittlung", "Restwertermittlung"),
        ("Gebrauchtwagen oder Reparatur ist mangelhaft", "leistungen/beweissicherungsgutachten", "Beweissicherungsgutachten"),
        ("Rückgabe eines Leasingfahrzeugs, Streit um Wertminderung", "leistungen/leasingruecknahme-gutachten", "Leasingrücknahme-Gutachten"),
        ("Kauf, Verkauf oder Bewertung eines Oldtimers", "leistungen/wertgutachten", "Wertgutachten"),
        ("Unfallhergang ist strittig, es droht ein Rechtsstreit", "leistungen/unfallanalytisches-gutachten", "Unfallanalytisches Gutachten"),
    ]
    trs = "".join(f'<tr><th scope="row">{esc(a)}</th><td><a href="{u(s, d)}">{esc(n)}</a></td></tr>' for a, s, n in rows)
    body = f'''
  {page_hero([("Leistungen", "leistungen")], d, "Leistungen", "Kfz-Gutachten in Celle: alle Leistungen",
             "Von der Schadenermittlung nach dem Unfall bis zur Bewertung Ihres Oldtimers. Alle Gutachten erstelle ich neutral, nachvollziehbar und zügig.")}

  <section class="section" aria-labelledby="alle-title">
    <div class="wrap">
      <div class="section-head"><h2 id="alle-title">Sechs Gutachten, ein Ansprechpartner</h2></div>
      {service_cards(d)}
    </div>
  </section>

  <section class="section section--surface" aria-labelledby="welches-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="welches-title">Welches Gutachten brauche ich?</h2>
        <p class="lede">Ordnen Sie Ihre Situation zu. Wenn Sie unsicher sind, rufen Sie an. Wir klären das in wenigen Minuten.</p>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead><tr><th scope="col">Ihre Situation</th><th scope="col">Passendes Gutachten</th></tr></thead>
          <tbody>{trs}</tbody>
        </table>
      </div>
    </div>
  </section>

  {cta_band(d, "Nicht sicher, was Sie brauchen?", "Schildern Sie mir Ihre Lage. Ich sage Ihnen ehrlich, welches Gutachten sinnvoll ist und ob es sich lohnt.")}
'''
    graph = [breadcrumb_node([("Leistungen", "leistungen")]),
             {"@type": "CollectionPage", "name": "Leistungen", "url": abs_url("leistungen"),
              "about": {"@id": DOMAIN + "/#business"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "name": s["short"], "url": abs_url(s["slug"])}
                  for i, s in enumerate(SERVICES)]}}]
    return dict(slug="leistungen", d=d,
                title="Leistungen: Kfz-Gutachten in Celle | PS Schneider",
                desc="Alle Leistungen des Kfz-Sachverständigen in Celle: Haftpflichtschaden, Beweissicherung, Leasingrückgabe, Wertgutachten, Restwertermittlung, Unfallanalyse.",
                body=body, graph=graph)


def build_article(a):
    d = a["slug"].count("/") + 1
    trail = [("Ratgeber", "ratgeber"), (a["short"], a["slug"])]
    secs = []
    for sec in a["sections"]:
        secs.append(f'''<section>
        <h2>{esc(sec["h2"])}</h2>
        {render_blocks(sec["body"], d)}
      </section>''')
    body = f'''
  {page_hero(trail, d, "Ratgeber", a["h1"], a["lede"], stand=de_month(a["modified"]))}

  <div class="wrap page-grid">
    <article class="prose">
      <div class="summary">
        <p class="summary-label">Kurz gesagt</p>
        <p>{rich(a["summary"], d)}</p>
      </div>
      {"".join(secs)}
      <p class="disclaimer">Dieser Beitrag ist eine allgemeine Information und keine Rechtsberatung. Wie sich ein Schaden im Einzelfall abwickelt, hängt von den Umständen ab. Bei rechtlichen Fragen berät Sie Ihr Rechtsanwalt.</p>
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">Häufige Fragen</h2></div>
      {faq_section(a["faq"], d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">Weiterlesen</h2></div>
      {related(a["related"], d)}
    </div>
  </section>

  {cta_band(d)}
'''
    url = abs_url(a["slug"])
    graph = [
        {"@type": "Article", "@id": url + "#article", "headline": a["h1"], "description": a["desc"],
         "datePublished": a["published"], "dateModified": a["modified"], "inLanguage": "de-DE",
         "mainEntityOfPage": url, "image": DOMAIN + "/assets/og-image.jpg",
         "author": {"@type": "Person", "@id": DOMAIN + "/#person", "name": BIZ["person"],
                    "jobTitle": BIZ["role"] + ", " + BIZ["craft"]},
         "publisher": business_ref()},
        breadcrumb_node([("Ratgeber", "ratgeber"), (a["short"], a["slug"])]),
        faq_node(a["faq"]),
    ]
    return dict(slug=a["slug"], d=d, title=a["title"], desc=a["desc"], body=body, graph=graph)


def build_ratgeber_index():
    d = 1
    items = []
    for a in ARTICLES:
        items.append(f'''<li>
          <h2><a href="{u(a["slug"], d)}">{esc(a["short"])}</a></h2>
          <p>{esc(a["lede"])}</p>
          <span class="more" aria-hidden="true">Lesen →</span>
        </li>''')
    body = f'''
  {page_hero([("Ratgeber", "ratgeber")], d, "Ratgeber", "Ratgeber zum Kfz-Gutachten: Antworten nach dem Unfall",
             "Was nach einem Unfall zählt, in verständlicher Sprache: Wertminderung, Totalschaden, Mietwagen, Kosten und Oldtimer-Bewertung.", byline=False)}

  <section class="section" aria-labelledby="liste-title">
    <div class="wrap">
      <h2 class="visually-hidden" id="liste-title">Alle Beiträge</h2>
      <ul class="guide-list">
        {"".join(items)}
      </ul>
      <p class="more-row">Direkt nach einem Unfall? Die <a href="{u("unfall-checkliste", d)}">Unfall-Checkliste</a> führt Sie durch die ersten Schritte.</p>
    </div>
  </section>

  {cta_band(d, "Ihre Frage ist nicht dabei?", "Schildern Sie mir Ihre Situation. Ich antworte unverbindlich und sage Ihnen ehrlich, was sinnvoll ist.")}
'''
    graph = [breadcrumb_node([("Ratgeber", "ratgeber")]),
             {"@type": "CollectionPage", "name": "Ratgeber zum Kfz-Gutachten", "url": abs_url("ratgeber"),
              "about": {"@id": DOMAIN + "/#business"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "name": a["short"], "url": abs_url(a["slug"])}
                  for i, a in enumerate(ARTICLES)]}}]
    return dict(slug="ratgeber", d=d,
                title="Ratgeber Kfz-Gutachten und Unfall | PS Schneider",
                desc="Ratgeber vom Kfz-Sachverständigen in Celle: Wertminderung, Totalschaden, Mietwagen, Gutachterkosten und Oldtimer-Wertgutachten verständlich erklärt.",
                body=body, graph=graph)


def town_chips(towns, d, current=None):
    items = []
    for t in towns:
        if t.get("home"):
            items.append(f'<li><a href="{u("", d)}">{esc(t["name"])}</a></li>')
        elif t.get("page") and t["name"] != current:
            items.append(f'<li><a href="{u(t["slug"], d)}">{esc(t["name"])}</a></li>')
        else:
            items.append(f'<li><span>{esc(t["name"])}</span></li>')
    return f'<ul class="chips">{"".join(items)}</ul>'


def area_svg(d):
    """Schematische Darstellung (keine Karte): Celle in der Mitte, Ringe bei 25 und 50 km."""
    S, C = 5.6, 320  # Pixel pro km, Mittelpunkt
    pts = []
    for t in PAGE_TOWNS:
        dx, dy = xy_km(t["lat"], t["lon"])
        x, y = C + dx * S, C - dy * S
        left = dx < 0
        tx = x - 11 if left else x + 11
        anchor = "end" if left else "start"
        pts.append(f'<a href="{u(t["slug"], d)}"><circle class="pt" cx="{x:.0f}" cy="{y:.0f}" r="7"/>'
                   f'<text class="lb" x="{tx:.0f}" y="{y + 6:.0f}" text-anchor="{anchor}">{esc(t["name"])}</text></a>')
    r50, r25 = AREA["radius_km"] * S, AREA["radius_km"] / 2 * S
    return f'''<svg class="area-svg" viewBox="0 0 640 640" role="img" aria-label="Schema des Einsatzgebiets: Celle in der Mitte, Orte im Umkreis von 50 Kilometern">
  <circle class="ring" cx="{C}" cy="{C}" r="{r50:.0f}"/>
  <circle class="ring ring-in" cx="{C}" cy="{C}" r="{r25:.0f}"/>
  <text class="ring-lb" x="{C}" y="{C - r25 - 6:.0f}" text-anchor="middle">25 km</text>
  <text class="ring-lb" x="{C}" y="{C - r50 - 6:.0f}" text-anchor="middle">50 km</text>
  <text class="ring-lb" x="{C}" y="{C - r50 - 26:.0f}" text-anchor="middle">N</text>
  {"".join(pts)}
  <circle class="home" cx="{C}" cy="{C}" r="9"/>
  <text class="lb lb-home" x="{C}" y="{C + 28}" text-anchor="middle">Celle</text>
</svg>'''


AREA_FAQ = [
    ("In welchen Orten sind Sie tätig?",
     "Im gesamten Landkreis Celle und im Umkreis von 50 Kilometern um Celle, zum Beispiel in Hannover, Burgdorf, Gifhorn, Walsrode und Soltau. Die Liste auf dieser Seite nennt die größeren Orte."),
    ("Mein Ort steht nicht in der Liste. Was nun?",
     "Rufen Sie einfach an. Orte im Umkreis von rund 50 Kilometern um Celle gehören zum Einsatzgebiet, auch wenn sie hier nicht einzeln genannt sind. Liegt Ihr Ort weiter weg, fragen Sie trotzdem an."),
    ("Wo findet die Besichtigung statt?",
     "Das stimmen wir individuell ab. Rufen Sie an, dann klären wir Ort und Termin."),
]


def build_area_hub():
    d = 1
    regions = []
    for name, desc in AREA_REGIONS:
        towns = [t for t in TOWNS if t["region"] == name]
        regions.append(f'''<section>
        <h2>{esc(name)}</h2>
        <p>{esc(desc)}</p>
        {town_chips(towns, d)}
      </section>''')
    body = f'''
  {page_hero([("Einsatzgebiet", "einsatzgebiet")], d, "Einsatzgebiet", "Kfz-Gutachter im Landkreis Celle und Umkreis von 50 Kilometern",
             "Unabhängige Kfz-Gutachten in Celle und in den Orten rundherum. Besichtigungstermine stimme ich individuell mit Ihnen ab.", byline=False)}

  <div class="wrap page-grid">
    <article class="prose">
      <section>
        <h2>Wo ich für Sie da bin</h2>
        <p>Mein Büro ist in Celle. Von dort aus betreue ich den gesamten Landkreis Celle und die Orte im Umkreis von 50 Kilometern, vom Nordrand der Region Hannover bis in die Heide. Orte mit eigener Seite sind verlinkt.</p>
        <figure class="area-map">
          {area_svg(d)}
          <figcaption>Schema, keine Landkarte. Die Entfernungen sind Luftlinie ab Celle.</figcaption>
        </figure>
      </section>
      {"".join(regions)}
      <section>
        <h2>Unfall außerhalb des Gebiets?</h2>
        <p>Der Radius ist ein Richtwert. Liegt Ihr Ort weiter entfernt, rufen Sie an. Wir klären dann, ob sich ein Termin einrichten lässt.</p>
      </section>
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">Häufige Fragen zum Einsatzgebiet</h2></div>
      {faq_section(AREA_FAQ, d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">Leistungen</h2></div>
      {related(["leistungen", "leistungen/haftpflichtschaden-gutachten", "leistungen/wertgutachten"], d)}
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [breadcrumb_node([("Einsatzgebiet", "einsatzgebiet")]),
             {"@type": "WebPage", "name": "Einsatzgebiet", "url": abs_url("einsatzgebiet"), "about": {"@id": DOMAIN + "/#business"}},
             faq_node(AREA_FAQ)]
    return dict(slug="einsatzgebiet", d=d,
                title="Einsatzgebiet: Kfz-Gutachter Landkreis Celle | PS Schneider",
                desc="Kfz-Sachverständiger im Landkreis Celle und im Umkreis von 50 Kilometern: Celle, Bergen, Gifhorn, Burgdorf, Soltau, Walsrode, Hannover und weitere Orte.",
                body=body, graph=graph)


def build_town(t):
    d = t["slug"].count("/") + 1
    name, region = t["name"], t["region"]
    here = (t["lat"], t["lon"])
    near = sorted((o for o in PAGE_TOWNS if o is not t),
                  key=lambda o: km_between(here[0], here[1], o["lat"], o["lon"]))[:3]
    trail = [("Einsatzgebiet", "einsatzgebiet"), (f"Kfz-Gutachter {name}", t["slug"])]
    services = "".join(f'<li><a href="{u(s["slug"], d)}">{esc(s["short"])}</a></li>' for s in SERVICES)
    faq = [
        (f"Sind Sie auch in {name} tätig?",
         f"Ja. {name} liegt rund {t['dist']} Kilometer Luftlinie von Celle entfernt und gehört zu meinem Einsatzgebiet im {AREA['label']}."),
        ("Wo findet die Besichtigung statt?",
         f"Das stimmen wir individuell ab. Rufen Sie an, dann klären wir, wo und wann ich Ihr Fahrzeug in oder um {name} besichtigen kann."),
        ("Wer zahlt das Gutachten nach einem unverschuldeten Unfall?",
         "In der Regel die Haftpflichtversicherung des Unfallverursachers. Sie haben das Recht, den Sachverständigen frei zu wählen."),
    ]
    near_links = "".join(f'<li><a href="{u(o["slug"], d)}"><strong>{esc(o["name"])}</strong><span>{esc(o["kind"])} im {esc(o["region"])}</span></a></li>' for o in near)
    body = f'''
  {page_hero(trail, d, "Einsatzgebiet", f"Kfz-Gutachter in {name}",
             f"Unabhängige Kfz-Gutachten für {name} und Umgebung. {name} liegt rund {t['dist']} Kilometer Luftlinie von Celle entfernt im {t['dir']}, mitten in meinem Einsatzgebiet.", byline=False)}

  <div class="wrap page-grid">
    <article class="prose">
      <section>
        <h2>Gutachten für {esc(name)}</h2>
        <p>{esc(name)} ({esc(t["kind"])} im {esc(region)}) gehört zu meinem Einsatzgebiet im {esc(AREA["label"])}. Wurde Ihr Fahrzeug in {esc(name)} oder Umgebung beschädigt, oder möchten Sie dort ein Fahrzeug bewerten lassen, erstelle ich Ihnen ein unabhängiges Gutachten.</p>
        <ul>{services}</ul>
      </section>
      <section>
        <h2>So läuft ein Termin ab</h2>
        <ol>
          <li>Sie rufen an oder schreiben mir und schildern kurz, worum es geht.</li>
          <li>Wir klären, wo und wann ich Ihr Fahrzeug in oder um {esc(name)} besichtigen kann.</li>
          <li>Ich dokumentiere Schaden oder Zustand und erstelle das Gutachten zügig.</li>
          <li>Sie erhalten das Gutachten und entscheiden über die nächsten Schritte.</li>
        </ol>
      </section>
      <section>
        <h2>Nach einem Unfall in {esc(name)}</h2>
        <p>Sichern Sie zuerst die Unfallstelle. Bei Verletzten rufen Sie die 112, bei einem Unfall mit Polizeiaufnahme die 110. Danach erreichen Sie mich telefonisch. Die <a href="{u("unfall-checkliste", d)}">Unfall-Checkliste</a> führt Sie durch die ersten Schritte.</p>
      </section>
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">Häufige Fragen zu {esc(name)}</h2></div>
      {faq_section(faq, d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">Weitere Orte in der Nähe</h2></div>
      <ul class="related">{near_links}</ul>
      <p class="more-row"><a href="{u("einsatzgebiet", d)}">Alle Orte im Einsatzgebiet</a></p>
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [
        {"@type": "Service", "@id": abs_url(t["slug"]) + "#service", "name": f"Kfz-Gutachter {name}", "serviceType": "Kfz-Gutachten",
         "url": abs_url(t["slug"]), "provider": business_ref(), "areaServed": {"@type": "City", "name": name}},
        breadcrumb_node(trail),
        faq_node(faq),
    ]
    return dict(slug=t["slug"], d=d,
                title=f"Kfz-Gutachter {name} | PS Schneider",
                desc=f"Unabhängiger Kfz-Gutachter für {name}: Unfallgutachten, Wertgutachten und mehr. Rund {t['dist']} km von Celle, Termin nach Absprache. Tel. 0172 517 81 50.",
                body=body, graph=graph)


def build_gruende():
    d = 1
    secs = []
    for h, paras in REASONS:
        secs.append(f'<section><h2>{esc(h)}</h2>' + "".join(f"<p>{rich(p, d)}</p>" for p in paras) + "</section>")
    ok = f'<td class="yes">{svg("check", "2.5")}ja</td>'
    no = '<td class="no">nein</td>'
    rows = "".join(f'<tr><th scope="row">{esc(n)}</th>{ok if a else no}{ok if b else no}</tr>' for n, a, b in COMPARE_ROWS)
    body = f'''
  {page_hero([("Gründe für ein Kfz-Gutachten", "gruende-fuer-ein-gutachten")], d, "Gutachten statt Kostenvoranschlag",
             "Wozu ein Kfz-Gutachten erstellen lassen?",
             "Nach einem Unfall schlagen Versicherungen oft einen Kostenvoranschlag vor. Sechs Gründe, warum ein unabhängiges Gutachten Ihnen mehr bringt.")}

  <div class="wrap page-grid">
    <article class="prose">
      {"".join(secs)}
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="cmp-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="cmp-title">Kostenvoranschlag und Gutachten im Vergleich</h2>
      </div>
      <div class="compare-wrap">
        <table class="compare">
          <thead><tr><th scope="col">Erfasst</th><th scope="col">Kosten&shy;voranschlag</th><th scope="col">Kfz-Gutachten</th></tr></thead>
          <tbody>{rows}</tbody>
          <tfoot><tr><td colspan="3">Im Haftpflichtfall werden die Gutachtenkosten dem Schaden zugerechnet und von der Versicherung des Unfallverursachers getragen. Bei reinen Bagatellschäden lohnt sich ein Gutachten oft nicht. Das klären wir vorab am Telefon.</td></tr></tfoot>
        </table>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">Passende Leistungen</h2></div>
      {related(["leistungen/haftpflichtschaden-gutachten", "ratgeber/kfz-gutachten-kosten", "unfall-checkliste"], d)}
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [breadcrumb_node([("Gründe für ein Kfz-Gutachten", "gruende-fuer-ein-gutachten")]),
             {"@type": "WebPage", "name": "Gründe für ein Kfz-Gutachten", "url": abs_url("gruende-fuer-ein-gutachten"),
              "about": {"@id": DOMAIN + "/#business"}}]
    return dict(slug="gruende-fuer-ein-gutachten", d=d,
                title="Gründe für ein Kfz-Gutachten nach dem Unfall | PS Schneider",
                desc="Warum ein unabhängiges Kfz-Gutachten mehr bringt als ein Kostenvoranschlag: Kosten, Wertminderung, Beweissicherung, fiktive Abrechnung. Celle.",
                body=body, graph=graph)


def build_checkliste():
    d = 1
    body = f'''
  {page_hero([("Unfall-Checkliste", "unfall-checkliste")], d, "Unfall-Checkliste", "Wie verhält man sich nach einem Unfall?",
             "Sechs Schritte in der richtigen Reihenfolge. Haken Sie ab, was erledigt ist. Die Liste bleibt auf Ihrem Gerät gespeichert und wird nicht an uns übertragen.")}

  <section class="section" aria-labelledby="check-title">
    <div class="wrap">
      <h2 class="visually-hidden" id="check-title">Checkliste</h2>
      <div class="checklist-grid">
        <div>
          <ol class="checklist" id="checklist">
            {checklist_html()}
          </ol>
          <div class="checklist-foot">
            <span id="checklist-progress">0 von {len(CHECKLIST)} erledigt</span>
            <button type="button" id="checklist-reset">Liste zurücksetzen</button>
          </div>
        </div>
        {emergency_card(d)}
      </div>
    </div>
  </section>

  <section class="section section--surface" aria-labelledby="danach-title">
    <div class="wrap">
      <div class="prose">
        <section>
          <h2 id="danach-title">In den Tagen danach</h2>
          <ul>
            <li>Geben Sie am Unfallort kein Schuldeingeständnis ab, auch nicht mündlich.</li>
            <li>Notieren Sie sich das polizeiliche Aktenzeichen, falls die Polizei den Unfall aufgenommen hat.</li>
            <li>Lassen Sie das Fahrzeug nicht reparieren, bevor es begutachtet wurde.</li>
            <li>Informieren Sie Ihre Versicherung zeitnah.</li>
            <li>Rufen Sie mich früh an. Ich erkläre Ihnen, ob ein [[leistungen/haftpflichtschaden-gutachten|Haftpflichtschaden-Gutachten]] sinnvoll ist.</li>
          </ul>
        </section>
      </div>
    </div>
  </section>

  {cta_band(d, "Sachverständigen kontaktieren", "Je früher ich den Schaden sehe, desto besser lässt er sich dokumentieren. Rufen Sie an oder schreiben Sie per WhatsApp.")}
'''.replace('{rich', '{rich')
    # Links im Text auflösen
    body = LINK_RE.sub(lambda m: f'<a href="{u(m.group(1), d)}">{m.group(2)}</a>', body)
    graph = [breadcrumb_node([("Unfall-Checkliste", "unfall-checkliste")]),
             {"@type": "WebPage", "name": "Unfall-Checkliste", "url": abs_url("unfall-checkliste"),
              "about": {"@id": DOMAIN + "/#business"}}]
    return dict(slug="unfall-checkliste", d=d,
                title="Unfall-Checkliste: Was tun nach einem Unfall? | PS Schneider",
                desc="Checkliste zum Abhaken: Unfallstelle sichern, Verletzte versorgen, Polizei rufen, Daten austauschen, Fotos machen, Sachverständigen kontaktieren.",
                body=body, graph=graph)


def build_kontakt():
    d = 1
    body = f'''
  {page_hero([("Kontakt", "kontakt")], d, "Kontakt", "Kontakt zum Kfz-Sachverständigen in Celle",
             "Rufen Sie an, schreiben Sie per WhatsApp oder senden Sie die Anfrage über das Formular. Sie erhalten eine unverbindliche Beratung und ein individuelles Angebot.",
             byline=False)}
  {contact_section(d, "Anfrage senden", "section contact")}
  {cta_band(d, "Lieber direkt sprechen?", "Bei einem akuten Schaden ist der Anruf der schnellste Weg.")}
'''
    graph = [breadcrumb_node([("Kontakt", "kontakt")]),
             {"@type": "ContactPage", "name": "Kontakt", "url": abs_url("kontakt"),
              "about": {"@id": DOMAIN + "/#business"}}, business_node()]
    return dict(slug="kontakt", d=d,
                title="Kontakt zum Kfz-Gutachter in Celle | PS Schneider",
                desc="Kontakt zu Kfz-Sachverständigem Patric Schneider in Celle: Telefon 0172 517 81 50, E-Mail, WhatsApp und Anfrageformular. Im Röthel 43, 29225 Celle.",
                body=body, graph=graph)


def legal_page(slug, title, eyebrow, h1, inner):
    d = 1
    body = f'''
  <section class="legal-page">
    <div class="wrap">
      {crumbs([(h1, slug)], d)}
      <p class="eyebrow">{esc(eyebrow)}</p>
      <h1>{esc(h1)}</h1>
      {inner}
    </div>
  </section>
'''
    return dict(slug=slug, d=d, title=title, desc=h1 + " von PS Schneider, Kfz-Sachverständiger in Celle.",
                body=body, graph=None, noindex=True)


def build_impressum(d=1):
    inner = f'''
      <p class="notice">Hinweis für den Betreiber: Die gelb markierten Felder müssen vor Veröffentlichung ausgefüllt oder entfernt werden. Die bisherige Seite enthielt hier Platzhalter. Diesen Hinweis danach löschen.</p>

      <h2>Diensteanbieter</h2>
      <address>{BIZ["person"]}<br>{BIZ["role"]}<br>{BIZ["street"]}<br>{BIZ["zip"]} {BIZ["city"]}<br>Deutschland</address>

      <h2>Kontakt</h2>
      <p>Telefon: <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a><br>E-Mail: <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></p>

      <h2>Berufsbezeichnung</h2>
      <p>{BIZ["craft"]} (verliehen in der Bundesrepublik Deutschland)<br>{BIZ["role"]}</p>

      <h2>Umsatzsteuer</h2>
      <p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: <span class="todo">DE XXX XXX XXX eintragen oder Absatz entfernen</span></p>
      <p>Wirtschafts-Identifikationsnummer (W-IdNr.): <span class="todo">eintragen oder Absatz entfernen</span></p>

      <h2>Aufsichtsbehörde und Kammer</h2>
      <p><span class="todo">Zuständige Handwerkskammer eintragen oder Absatz entfernen</span></p>

      <h2>Verantwortlich für den Inhalt</h2>
      <p>{BIZ["person"]}, Anschrift wie oben.</p>

      <h2>Verbraucherstreitbeilegung</h2>
      <p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>

      <h2>Haftung für Inhalte</h2>
      <p>Die Inhalte dieser Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich.</p>

      <h2>Haftung für Links</h2>
      <p>Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Für diese fremden Inhalte ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.</p>

      <h2>Bildnachweis</h2>
      <p>Porträtfoto: {BIZ["person"]}, privat.</p>
'''
    return legal_page("impressum", "Impressum | PS Schneider Kfz-Gutachter Celle", "Angaben gemäß § 5 DDG", "Impressum", inner)


def build_datenschutz(d=1):
    inner = f'''
      <p class="notice">Hinweis für den Betreiber: Diese Erklärung ist auf die neue Seite zugeschnitten (keine Cookies, keine Analyse-Tools, selbst gehostete Schriften). Die gelb markierten Stellen bitte ergänzen. Eine rechtliche Prüfung ersetzt dieser Text nicht. Diesen Hinweis danach löschen.</p>

      <h2>1. Verantwortlicher</h2>
      <address>{BIZ["person"]}<br>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}<br>Telefon: {BIZ["phone_display"]}<br>E-Mail: {BIZ["email"]}</address>

      <h2>2. Überblick</h2>
      <p>Diese Website kommt ohne Cookies, Tracking und Analyse-Dienste aus. Es werden keine Inhalte von Drittanbietern eingebunden und keine Schriften von externen Servern geladen. Personenbezogene Daten verarbeiten wir nur, wenn Sie uns kontaktieren oder beim Aufruf der Seite technisch notwendige Verbindungsdaten anfallen.</p>

      <h2>3. Hosting und Server-Logfiles</h2>
      <p>Beim Aufruf der Website verarbeitet der Webserver automatisch Informationen, die Ihr Browser übermittelt: IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, übertragene Datenmenge, Browsertyp und Betriebssystem. Diese Daten dienen der Sicherheit und Stabilität der Website und werden nach kurzer Zeit gelöscht. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse am sicheren Betrieb).</p>
      <p>Betreiber des Servers: <span class="todo">Name und Anschrift eintragen. Bei eigenem Server: Standort und Betreiber nennen. Bei einem Hoster: Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO abschließen.</span></p>

      <h2>4. Kontaktaufnahme</h2>
      <h3>Kontaktformular</h3>
      <p>Das Kontaktformular auf dieser Seite sendet keine Daten an einen Server. Es bereitet eine E-Mail in Ihrem eigenen E-Mail-Programm vor, die Sie selbst an uns senden. Ihre Angaben (Name, E-Mail-Adresse, optional Telefonnummer, Anliegen und Nachricht) erreichen uns daher ausschließlich per E-Mail.</p>
      <h3>E-Mail, Telefon, WhatsApp</h3>
      <p>Wenn Sie uns per E-Mail, Telefon oder WhatsApp kontaktieren, verarbeiten wir die übermittelten Daten zur Bearbeitung Ihrer Anfrage und für eventuelle Anschlussfragen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Anbahnung oder Durchführung eines Vertrags) sowie Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der Beantwortung von Anfragen).</p>
      <p>Bei WhatsApp werden Daten an WhatsApp Ireland Limited (Meta) übermittelt, darunter Ihre Telefonnummer und Metadaten der Kommunikation. Inhalte sind Ende-zu-Ende verschlüsselt. Nutzen Sie WhatsApp nur, wenn Sie damit einverstanden sind. Alternativ erreichen Sie uns jederzeit per Telefon oder E-Mail.</p>
      <p>Anfragedaten werden gelöscht, sobald sie für die Bearbeitung nicht mehr erforderlich sind und keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</p>

      <h2>5. Auftragsbearbeitung und Gutachten</h2>
      <p>Beauftragen Sie ein Gutachten, verarbeiten wir die dafür notwendigen Daten: Ihre Kontaktdaten, Fahrzeugdaten (Kennzeichen, Fahrzeug-Identifizierungsnummer, Laufleistung), Angaben zum Schadenereignis, Fotos des Fahrzeugs sowie bei Haftpflichtschäden Daten des Unfallgegners und dessen Versicherung. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO.</p>
      <p>Zur Abwicklung übermitteln wir das Gutachten an die von Ihnen benannten Empfänger, etwa die regulierende Versicherung, Ihre Werkstatt oder Ihren Rechtsanwalt. Zur Kalkulation und Restwertermittlung setzen wir branchenübliche Fachsysteme ein. <span class="todo">Verwendete Systeme und Restwertbörsen eintragen oder Satz entfernen</span></p>
      <p>Gutachten und zugehörige Unterlagen bewahren wir nach den handels- und steuerrechtlichen Vorgaben auf (in der Regel 10 Jahre, § 147 AO, § 257 HGB).</p>

      <h2>6. Speicherung auf Ihrem Gerät</h2>
      <p>Die Unfall-Checkliste merkt sich abgehakte Punkte im lokalen Speicher Ihres Browsers (Local Storage). Diese Information verlässt Ihr Gerät nicht, wird nicht an uns übermittelt und kann jederzeit über „Liste zurücksetzen“ oder die Browser-Einstellungen gelöscht werden. Es handelt sich um eine rein funktionale Speicherung nach § 25 Abs. 2 Nr. 2 TDDDG.</p>

      <h2>7. Ihre Rechte</h2>
      <p>Sie haben gegenüber uns folgende Rechte hinsichtlich Ihrer personenbezogenen Daten:</p>
      <ul>
        <li>Auskunft (Art. 15 DSGVO)</li>
        <li>Berichtigung (Art. 16 DSGVO)</li>
        <li>Löschung (Art. 17 DSGVO)</li>
        <li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
        <li>Datenübertragbarkeit (Art. 20 DSGVO)</li>
        <li>Widerspruch gegen Verarbeitungen auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO (Art. 21 DSGVO)</li>
      </ul>
      <p>Sie haben zudem das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren. Zuständig ist die Landesbeauftragte für den Datenschutz Niedersachsen, Prinzenstraße 5, 30159 Hannover.</p>

      <h2>8. Datensicherheit</h2>
      <p>Die Website wird über HTTPS verschlüsselt ausgeliefert. Wir treffen angemessene technische und organisatorische Maßnahmen, um Ihre Daten gegen Verlust, Manipulation und unbefugten Zugriff zu schützen.</p>

      <h2>9. Änderungen</h2>
      <p>Wir passen diese Datenschutzerklärung an, wenn sich die Website oder die rechtlichen Anforderungen ändern. Es gilt die jeweils hier veröffentlichte Fassung.</p>
'''
    return legal_page("datenschutz", "Datenschutzerklärung | PS Schneider Kfz-Gutachter Celle", f"Stand: {STAND}", "Datenschutzerklärung", inner)


def build_404():
    d = 0
    body = f'''
  <section class="wrap notfound">
    <p class="big" aria-hidden="true">404</p>
    <h1>Diese Seite gibt es nicht mehr.</h1>
    <p class="lede">Vielleicht hat sich die Adresse geändert. Hier geht es zu den wichtigsten Seiten.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="{u("", d)}">Zur Startseite</a>
      <a class="btn btn-secondary" href="{u("leistungen", d)}">Leistungen</a>
      <a class="btn btn-secondary" href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>
    </div>
  </section>
'''
    return dict(slug="404", d=d, title="Seite nicht gefunden | PS Schneider", desc="Diese Seite wurde nicht gefunden.",
                body=body, graph=None, noindex=True)


# ---------------------------------------------------------------- Serverdateien

def rx(path):
    """Alte Adresse -> Regex mit optionalem Slash am Ende."""
    p = path.rstrip("/")
    p = re.sub(r"([.\[\]()+*?^$|{}\\])", r"\\\1", p)
    return f"^{p}/?$"


def htaccess():
    lines = [
        "# PS Schneider – Apache-Konfiguration",
        "# Diese Datei liegt im Webroot neben index.html. Sie wird von build/build.py erzeugt.",
        "# Benötigte Module: mod_alias, mod_headers, mod_expires, mod_deflate (sonst Zeilen entfernen).",
        "",
        "Options -Indexes",
        "DirectoryIndex index.html",
        "ErrorDocument 404 /404.html",
        "",
        "# --- HTTPS und eine Domain erzwingen (nach dem Einrichten des Zertifikats einkommentieren) ---",
        "# <IfModule mod_rewrite.c>",
        "#   RewriteEngine On",
        "#   RewriteCond %{HTTPS} !=on [OR]",
        "#   RewriteCond %{HTTP_HOST} ^www\\. [NC]",
        f"#   RewriteRule ^ {DOMAIN}%{{REQUEST_URI}} [L,R=301]",
        "# </IfModule>",
        "",
        "# --- Alte Adressen der bisherigen Website: dauerhaft (301) auf die neuen Seiten ---",
    ]
    for old, new in REDIRECTS:
        lines.append(f"RedirectMatch 301 {rx(old)} {new}")
    lines += [
        "",
        "# --- Sicherheit ---",
        "<IfModule mod_headers.c>",
        *(['  Header always set X-Robots-Tag "noindex, nofollow, noarchive"'] if DRAFT else []),
        '  Header always set X-Content-Type-Options "nosniff"',
        '  Header always set Referrer-Policy "strict-origin-when-cross-origin"',
        '  Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()"',
        '  Header always set X-Frame-Options "SAMEORIGIN"',
        "  # Alles kommt vom eigenen Server, es gibt keinen Inline-Code:",
        '  Header always set Content-Security-Policy "default-src \'self\'; img-src \'self\' data:; script-src \'self\'; style-src \'self\'; font-src \'self\'; base-uri \'self\'; form-action \'none\'; frame-ancestors \'self\'"',
        "  # Erst aktivieren, wenn HTTPS dauerhaft läuft:",
        '  # Header always set Strict-Transport-Security "max-age=31536000"',
        "</IfModule>",
        "",
        "# --- Komprimierung ---",
        "<IfModule mod_deflate.c>",
        "  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json application/xml image/svg+xml text/plain",
        "</IfModule>",
        "",
        "# --- Zwischenspeicher im Browser ---",
        "<IfModule mod_expires.c>",
        "  ExpiresActive On",
        '  ExpiresByType font/woff2 "access plus 1 year"',
        '  ExpiresByType image/png "access plus 1 month"',
        '  ExpiresByType image/jpeg "access plus 1 month"',
        '  ExpiresByType image/svg+xml "access plus 1 month"',
        '  ExpiresByType image/x-icon "access plus 1 month"',
        '  ExpiresByType text/css "access plus 1 week"',
        '  ExpiresByType application/javascript "access plus 1 week"',
        '  ExpiresByType text/html "access plus 5 minutes"',
        "</IfModule>",
        "",
    ]
    return "\n".join(lines)


def nginx_conf():
    red = "\n".join(f"    rewrite {rx(old)} {new} permanent;" for old, new in REDIRECTS)
    return f'''# PS Schneider – Beispiel für nginx. Pfade und Zertifikate anpassen.
# Wird von build/build.py erzeugt. Webroot = Inhalt des Ordners public/.

server {{
    listen 80;
    server_name psschneider.de www.psschneider.de;
    return 301 https://psschneider.de$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name www.psschneider.de;
    ssl_certificate     /pfad/zum/zertifikat/fullchain.pem;
    ssl_certificate_key /pfad/zum/zertifikat/privkey.pem;
    return 301 https://psschneider.de$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name psschneider.de;
    ssl_certificate     /pfad/zum/zertifikat/fullchain.pem;
    ssl_certificate_key /pfad/zum/zertifikat/privkey.pem;

    root /var/www/psschneider.de;
    index index.html;
    error_page 404 /404.html;

    # Alte Adressen der bisherigen Website: dauerhaft (301) auf die neuen Seiten
{red}

    location / {{
        try_files $uri $uri/ =404;
    }}

    location = /404.html {{ internal; }}

    # Sicherheit
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; font-src 'self'; base-uri 'self'; form-action 'none'; frame-ancestors 'self'" always;
    # add_header Strict-Transport-Security "max-age=31536000" always;

    # Komprimierung
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml application/xml;

    # Zwischenspeicher im Browser
    location ~* \\.(woff2)$ {{ expires 1y; add_header Cache-Control "public"; }}
    location ~* \\.(png|jpg|svg|ico)$ {{ expires 30d; add_header Cache-Control "public"; }}
    location ~* \\.(css|js)$ {{ expires 7d; add_header Cache-Control "public"; }}
}}
'''


def robots():
    if DRAFT:
        return "# Entwurf von Markentrix: nicht für Suchmaschinen.\nUser-agent: *\nDisallow: /\n"
    return f"""# robots.txt für {DOMAIN}
User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""


def sitemap(indexable):
    items = []
    for slug in indexable:
        pri = "1.0" if slug == "" else ("0.9" if slug.count("/") == 0 and slug in ("leistungen", "kontakt") else "0.8")
        items.append(f"  <url>\n    <loc>{abs_url(slug)}</loc>\n    <lastmod>{TODAY.isoformat()}</lastmod>\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(items) + "\n</urlset>\n")


# ---------------------------------------------------------------- Ausgabe

def write(out_dir, rel, text):
    p = out_dir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    global PREVIEW
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", metavar="DIR", help="Vorschau mit relativen Links in DIR erzeugen")
    ap.add_argument("--final", action="store_true", help="Endversion ohne Entwurfsmodus (Urheberrechtsvermerk, Wasserzeichen, Sperren)")
    args = ap.parse_args()
    global DRAFT
    DRAFT = not args.final
    # Entwurfsdateien in public/assets bereitstellen oder entfernen
    for name in ("draft.css", "draft.js"):
        target = PUBLIC / "assets" / name
        if DRAFT:
            shutil.copyfile(DRAFT_ASSETS / name, target)
        elif target.exists():
            target.unlink()

    if args.preview:
        PREVIEW = True
        out = Path(args.preview).resolve()
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(PUBLIC, out, ignore=shutil.ignore_patterns("*.html", "sitemap.xml", "robots.txt", ".htaccess"))
    else:
        out = PUBLIC

    pages = [build_home(), build_leistungen()]
    pages += [build_service(s) for s in SERVICES]
    pages += [build_ratgeber_index()] + [build_article(a) for a in ARTICLES]
    pages += [build_area_hub()] + [build_town(t) for t in PAGE_TOWNS]
    pages += [build_gruende(), build_checkliste(), build_kontakt(), build_impressum(), build_datenschutz(), build_404()]

    indexable = []
    for p in pages:
        slug = p["slug"]
        html_text = page_html(slug=slug, d=p["d"], title=p["title"], desc=p["desc"], body=p["body"],
                              graph=p.get("graph"), noindex=p.get("noindex", False))
        if slug == "404":
            rel = "404.html"
        elif slug == "":
            rel = "index.html"
        else:
            rel = f"{slug}/index.html"
        write(out, rel, html_text)
        if not p.get("noindex"):
            indexable.append(slug)

    if not PREVIEW and DRAFT:
        for stale in ("sitemap.xml",):
            if (out / stale).exists():
                (out / stale).unlink()
    if not PREVIEW and not DRAFT:
        write(out, "sitemap.xml", sitemap(indexable))
    if not PREVIEW:
        write(out, "robots.txt", robots())
        write(out, ".htaccess", htaccess())
        write(ROOT / "server", "nginx.conf.example", nginx_conf())
    print(f"{len(pages)} Seiten nach {out} geschrieben.")


if __name__ == "__main__":
    main()
