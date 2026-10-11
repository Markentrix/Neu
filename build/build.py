#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt die statische Website in public/ (Deutsch und Englisch).

    python3 build/build.py                 # Entwurf nach public/ (mit Markentrix-Vermerk)
    python3 build/build.py --final         # Endversion ohne Vermerk
    python3 build/build.py --preview DIR   # Vorschau mit relativen Links (zum Ansehen ohne Server)

Benötigt nur Python 3, keine weiteren Pakete.

Zweisprachig: Deutsch liegt im Wurzelverzeichnis, Englisch unter /en/. Texte stehen als Paar
T("deutsch", "english") direkt im Code. Inhalte (Leistungen, Artikel, Fragen) liegen in
content.py (Deutsch) und content_en.py (Englisch).
"""
import argparse
import copy
import datetime
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content as C  # noqa: E402
import content_en as E  # noqa: E402

BIZ = dict(C.BIZ)
AREA = dict(C.AREA)
SERVICES, ARTICLES, REASONS, COMPARE_ROWS, HOME_FAQ, CHECKLIST = (
    C.SERVICES, C.ARTICLES, C.REASONS, C.COMPARE_ROWS, C.HOME_FAQ, C.CHECKLIST)
AREA_REGIONS = C.AREA_REGIONS
TOWNS = []
PAGE_TOWNS = []

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DOMAIN = BIZ["domain"]
TODAY = datetime.date.today()
LANGS = ("de", "en")
LANG = "de"
MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
           "September", "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}

PREVIEW = False  # wird in main() gesetzt
DRAFT = True     # Entwurfsmodus von Markentrix; mit --final ausschalten
OWNER = "Markentrix"
DRAFT_ASSETS = Path(__file__).resolve().parent / "draft_assets"


def T(de, en):
    """Text in der Sprache der Seite, die gerade gebaut wird."""
    return en if LANG == "en" else de


def month_year(iso):
    """'2026-10-11' -> 'Oktober 2026' / 'October 2026'"""
    y, m, _ = iso.split("-")
    return f"{MONTHS[LANG][int(m) - 1]} {y}"


def stand():
    return month_year(TODAY.isoformat())


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


# ---------------------------------------------------------------- Adressen in beiden Sprachen

SLUGS = {
    "de": {"home": "", "services": "leistungen", "guide": "ratgeber", "why": "gruende-fuer-ein-gutachten",
           "checklist": "unfall-checkliste", "contact": "kontakt", "area": "einsatzgebiet",
           "legal": "impressum", "privacy": "datenschutz"},
    "en": dict(E.SLUGS_EN),
}

_UM = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.translate(_UM).lower()).strip("-")


def _alt_table():
    """key -> {Sprache: Adresse}. Grundlage für Sprachumschalter und hreflang."""
    table = {}
    for lang, src in (("de", C), ("en", E)):
        towns = C.TOWNS if lang == "de" else E.localize_towns(C.TOWNS)
        prefix = "einsatzgebiet/" if lang == "de" else "en/service-area/"
        for key, slug in SLUGS[lang].items():
            table.setdefault(key, {})[lang] = slug
        for item in list(src.SERVICES) + list(src.ARTICLES):
            table.setdefault(item["key"], {})[lang] = item["slug"]
        for (de_t, t) in zip(C.TOWNS, towns):
            if t.get("page"):
                table.setdefault("town-" + de_t["name"], {})[lang] = prefix + slugify(t["name"])
    return table


ALT = _alt_table()


def S(key):
    """Adresse einer Seite in der aktuellen Sprache."""
    return ALT[key][LANG]


# Weiche Trennstellen für lange Wörter in Überschriften, damit sie auf schmalen Handys umbrechen.
SHY = {
    "Wiederbeschaffungswert": "Wieder­beschaffungs­wert",
    "Wiederbeschaffungsaufwand": "Wieder­beschaffungs­aufwand",
    "Beweissicherungsgutachten": "Beweis­sicherungs­gutachten",
    "Haftpflichtschaden": "Haft­pflicht­schaden",
    "Haftpflichtversicherung": "Haft­pflicht­versicherung",
    "Sachverständigenorganisation": "Sach­verständigen­organisation",
    "Restwertermittlung": "Rest­wert­ermittlung",
    "Nutzungsausfall": "Nutzungs­ausfall",
    "Leasingrücknahme": "Leasing­rück­nahme",
    "Unfallanalytisches": "Unfall­analytisches",
    "Kraftfahrzeugtechniker": "Kraft­fahrzeug­techniker",
    "Kraftfahrzeugwesen": "Kraft­fahrzeug­wesen",
    "Wertminderung": "Wert­minderung",
    "Schadenregulierung": "Schaden­regulierung",
    "Schadensabwicklung": "Schadens­abwicklung",
    "Fahrzeugtechnik": "Fahrzeug­technik",
    "Oldtimer-Wertgutachten": "Oldtimer-Wert­gutachten",
    "Gutachterkosten": "Gutachter­kosten",
    "Unfallgeschädigte": "Unfall­geschädigte",
    "Rechtsstreitigkeiten": "Rechtsstreitig­keiten",
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
    names = T(["Norden", "Nordosten", "Osten", "Südosten", "Süden", "Südwesten", "Westen", "Nordwesten"],
              ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"])
    return names[int(((math.degrees(math.atan2(dx, dy)) + 22.5) % 360) // 45)]


def prepare_towns():
    c_lat, c_lon = AREA["center"]
    prefix = T("einsatzgebiet/", "en/service-area/")
    for t in TOWNS:
        if t.get("page"):
            t["slug"] = prefix + slugify(t["name"])
            dist = km_between(c_lat, c_lon, t["lat"], t["lon"])
            t["dist"] = max(5, int(round(dist / 5.0) * 5))
            t["dir"] = compass(t["lat"], t["lon"])
            assert dist <= AREA["radius_km"], f"{t['name']} liegt außerhalb des Einsatzgebiets"


def set_lang(lang):
    """Stellt Texte und Daten auf eine Sprache um. Alle Bausteine lesen diese Werte beim Aufruf."""
    global LANG, SERVICES, ARTICLES, REASONS, COMPARE_ROWS, HOME_FAQ, CHECKLIST, AREA_REGIONS, TOWNS, PAGE_TOWNS
    LANG = lang
    src = C if lang == "de" else E
    SERVICES, ARTICLES, REASONS = src.SERVICES, src.ARTICLES, src.REASONS
    COMPARE_ROWS, HOME_FAQ, CHECKLIST = src.COMPARE_ROWS, src.HOME_FAQ, src.CHECKLIST
    AREA_REGIONS = src.AREA_REGIONS
    if lang == "de":
        AREA["label"] = C.AREA["label"]
        BIZ.update(role=C.BIZ["role"], craft=C.BIZ["craft"], legal_name=C.BIZ["legal_name"])
        TOWNS = copy.deepcopy(C.TOWNS)
        for t in TOWNS:
            t["key"] = "town-" + t["name"]
    else:
        AREA["label"] = E.AREA_LABEL
        BIZ.update(E.BIZ_EN)
        TOWNS = E.localize_towns(copy.deepcopy(C.TOWNS))
    prepare_towns()
    PAGE_TOWNS = [t for t in TOWNS if t.get("page")]


def in_region(region):
    """'im Landkreis Celle', aber 'in der Region Hannover' / 'in Celle district', aber 'in the Hanover region'."""
    if LANG == "en":
        return f"in the {region}" if region.endswith(" region") else f"in {region}"
    return f"in der {region}" if region.startswith("Region ") else f"im {region}"


def area_served():
    c_lat, c_lon = AREA["center"]
    return [{"@type": "City", "name": "Celle"},
            {"@type": "AdministrativeArea", "name": T("Landkreis Celle", "Celle district")},
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
    "camera": '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="3.5"/>',
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
        "alternateName": T("PS Schneider Kfz-Gutachter Celle", "PS Schneider Vehicle Expert Celle"),
        "description": T("Unabhängiger Kfz-Sachverständiger in Celle für Haftpflichtschaden-Gutachten, Beweissicherung, "
                         "Leasingrückgabe, Wertgutachten, Restwertermittlung und Unfallanalyse.",
                         "Independent vehicle expert in Celle for liability damage reports, evidence reports, "
                         "lease returns, valuation reports, residual value assessments and accident reconstruction."),
        "url": abs_url(S("home")),
        "logo": DOMAIN + "/assets/logo.png",
        "image": [DOMAIN + "/assets/og-image.jpg", DOMAIN + "/assets/portrait.jpg"],
        "telephone": "+49 172 5178150",
        "email": BIZ["email"],
        "address": address_node(),
        "areaServed": area_served(),
        "founder": {"@id": DOMAIN + "/#person"},
        "knowsAbout": T(["Kfz-Gutachten", "Haftpflichtschaden", "Restwertermittlung", "Wertgutachten",
                         "Oldtimer-Bewertung", "Leasingrückgabe", "Unfallanalyse"],
                        ["Vehicle expert reports", "Liability damage", "Residual value assessment", "Valuation reports",
                         "Classic car valuation", "Lease returns", "Accident reconstruction"]),
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": T("Leistungen", "Services"), "itemListElement": offers},
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
    return {"@type": "WebSite", "@id": DOMAIN + "/#website", "url": abs_url(S("home")), "name": BIZ["name"],
            "inLanguage": T("de-DE", "en-GB"), "publisher": {"@id": DOMAIN + "/#business"}}


def faq_node(items):
    return {"@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in items]}


def breadcrumb_node(trail):
    """trail: Liste (Name, slug) ohne Startseite, die Startseite wird vorangestellt."""
    items = [(T("Startseite", "Home"), S("home"))] + trail
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(s)} for i, (n, s) in enumerate(items)]}


# ---------------------------------------------------------------- Layout

def nav_items():
    return [
        (T("Leistungen", "Services"), S("services"), S("services")),
        (T("Ratgeber", "Guide"), S("guide"), S("guide")),
        (T("Über mich", "About me"), S("home"), "#ueber-mich"),
        (T("Unfall-Checkliste", "Accident checklist"), S("checklist"), S("checklist")),
        (T("Fragen", "FAQ"), S("home"), "#faq"),
        (T("Kontakt", "Contact"), S("contact"), S("contact")),
    ]


def logo_imgs(d):
    alt = T("PS Schneider – Sachverständiger für Fahrzeugtechnik", "PS Schneider – vehicle engineering expert")
    return (f'<img class="logo logo-light" src="{asset("logo.png", d)}" '
            f'alt="{alt}" width="546" height="152">'
            f'<img class="logo logo-dark" src="{asset("logo-dark.png", d)}" alt="" width="546" height="152">')


def lang_switch(d, key):
    """DE | EN. Führt zur gleichen Seite in der anderen Sprache."""
    if not key:
        return ""
    items = []
    for lang, label, name in (("de", "DE", "Deutsch"), ("en", "EN", "English")):
        cur = ' aria-current="true"' if lang == LANG else ""
        items.append(f'<a href="{u(ALT[key][lang], d)}" lang="{lang}" hreflang="{lang}"{cur} aria-label="{name}">{label}</a>')
    return f'<div class="lang-switch" role="group" aria-label="{T("Sprache wählen", "Choose language")}">{"".join(items)}</div>'


def header(d, slug, key=None):
    items = []
    for label, target, anchor in nav_items():
        if anchor.startswith("#"):
            href = u("", d) if LANG == "de" else u(S("home"), d)
            href += anchor
            cur = ""
        else:
            href = u(target, d)
            active = slug == target or slug.startswith(target + "/")
            cur = ' aria-current="page"' if active else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return f'''<header class="site-header" id="top">
  <div class="wrap">
    <a class="brand" href="{u(S("home"), d)}" aria-label="{T("PS Schneider, zur Startseite", "PS Schneider, home page")}">{logo_imgs(d)}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav" aria-label="{T("Menü öffnen", "Open menu")}">
      <span class="ic-menu">{svg("menu")}</span><span class="ic-close">{svg("close")}</span>
    </button>
    <nav class="primary-nav" id="primary-nav" aria-label="{T("Hauptnavigation", "Main navigation")}">
      <ul>
        {"".join(items)}
      </ul>
    </nav>
    {lang_switch(d, key)}
    <a class="btn btn-primary header-cta" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
  </div>
</header>'''


def footer(d):
    svc = "\n      ".join(f'<a href="{u(s["slug"], d)}">{_SHY_RE.sub(lambda w: SHY[w.group(0)], esc(s["short"]))}</a>' for s in SERVICES)
    design = f" · {T('Gestaltung und Umsetzung', 'Design and implementation')} © {TODAY.year} {OWNER}" if DRAFT else ""
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="col">
      {logo_imgs(d)}
      <span>{BIZ["craft"]} {BIZ["person"]}</span>
      <span>{BIZ["street"]} · {BIZ["zip"]} {BIZ["city"]}</span>
    </div>
    <div class="col">
      <strong>{T("Leistungen", "Services")}</strong>
      {svc}
    </div>
    <div class="col">
      <strong>{T("Kontakt", "Contact")}</strong>
      <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>
      <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a>
      <a href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">WhatsApp</a>
      <a href="{u(S("area"), d)}">{T("Einsatzgebiet", "Service area")}</a>
      <a href="{u(S("guide"), d)}">{T("Ratgeber", "Guide")}</a>
      <a href="{u(S("why"), d)}">{T("Gründe für ein Gutachten", "Why an expert report")}</a>
      <a href="{u(S("checklist"), d)}">{T("Unfall-Checkliste", "Accident checklist")}</a>
      <a href="{u(S("contact"), d)}">{T("Anfrage senden", "Send enquiry")}</a>
    </div>
    <div class="legal">
      <span>© <span data-year>{TODAY.year}</span> {BIZ["person"]}{design}</span>
      <span><a href="{u(S("legal"), d)}">{T("Impressum", "Legal notice")}</a> · <a href="{u(S("privacy"), d)}">{T("Datenschutzerklärung", "Privacy policy")}</a></span>
    </div>
  </div>
</footer>'''


def action_bar(d):
    return f'''<nav class="action-bar" aria-label="{T("Schnellkontakt", "Quick contact")}">
  <a class="primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{T("Anrufen", "Call")}</a>
  <a href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
  <a href="{u(S("contact"), d)}">{svg("mail")}{T("Anfrage", "Enquiry")}</a>
</nav>'''


def page_html(*, slug, d, title, desc, body, key=None, graph=None, noindex=False, canonical_slug=None, og_title=None):
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
    draft_comment = (T(f"<!-- © {TODAY.year} {OWNER}. Alle Rechte vorbehalten. Entwurf zur Ansicht. "
                       "Nutzung, Vervielfältigung, Bearbeitung oder Weitergabe nur mit schriftlicher Zustimmung. -->\n",
                       f"<!-- © {TODAY.year} {OWNER}. All rights reserved. Draft for viewing. "
                       "Use, copying, editing or distribution only with written consent. -->\n")) if DRAFT else ""
    draft_meta = T(f'\n<meta name="copyright" content="© {TODAY.year} {OWNER}. Alle Rechte vorbehalten.">',
                   f'\n<meta name="copyright" content="© {TODAY.year} {OWNER}. All rights reserved.">') if DRAFT else ""
    draft_css = f'\n<link rel="stylesheet" href="{asset("draft.css", d)}">' if DRAFT else ""
    draft_top = ((f'<div class="draft-bar" role="note"><strong>{T("Entwurf", "Draft")}</strong>'
                  f'<span>© {TODAY.year} {OWNER}</span><span class="draft-mid">· {T("Alle Rechte vorbehalten", "All rights reserved")}</span>'
                  f'<span class="draft-long">· {T("Nur zur Ansicht, keine Weitergabe oder Veröffentlichung", "For viewing only, no distribution or publication")}</span></div>\n'
                  '<div class="draft-wm" aria-hidden="true"></div>\n')) if DRAFT else ""
    draft_js = f'\n<script src="{asset("draft.js", d)}" defer></script>' if DRAFT else ""
    form_js = f'\n<script src="{asset("form.js", d)}" defer></script>' if 'id="contact-form"' in body else ""
    og = DOMAIN + "/assets/og-image.jpg"
    ld_block = ld(graph) if graph else ""
    canon_tag = "" if noindex else f'<link rel="canonical" href="{canon}">'
    hreflang = ""
    if not noindex and key and key in ALT:
        hreflang = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{abs_url(ALT[key][l])}">' for l in LANGS)
        hreflang += f'\n<link rel="alternate" hreflang="x-default" href="{abs_url(ALT[key]["de"])}">'
    og_locale = T("de_DE", "en_GB")
    og_alt = T("en_GB", "de_DE")
    og_tags = "" if noindex else f'''
<meta property="og:type" content="website">
<meta property="og:locale" content="{og_locale}">
<meta property="og:locale:alternate" content="{og_alt}">
<meta property="og:site_name" content="{esc(BIZ["name"])}">
<meta property="og:title" content="{esc(og_title or title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{T("PS Schneider, Sachverständiger für Fahrzeugtechnik in Celle", "PS Schneider, vehicle engineering expert in Celle")}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(og_title or title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og}">'''
    return soften(f'''<!DOCTYPE html>
{draft_comment}<html lang="{LANG}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
{canon_tag}{hreflang}
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
<a class="skip-link" href="#main">{T("Zum Inhalt springen", "Skip to content")}</a>
{draft_top}{header(d, slug, key)}
<main id="main">
{body}
</main>
{footer(d)}
{action_bar(d)}
<script src="{asset("site.js", d)}" defer></script>{form_js}{draft_js}
</body>
</html>
''')


# ---------------------------------------------------------------- Bausteine

def crumbs(trail, d):
    """trail: Liste (Name, slug); letzter Eintrag ist die aktuelle Seite."""
    parts = [f'<li><a href="{u(S("home"), d)}">{T("Startseite", "Home")}</a></li>']
    for i, (name, s) in enumerate(trail):
        if i == len(trail) - 1:
            parts.append(f'<li><span aria-current="page">{esc(name)}</span></li>')
        else:
            parts.append(f'<li><a href="{u(s, d)}">{esc(name)}</a></li>')
    return f'<nav class="crumbs" aria-label="{T("Brotkrumen", "Breadcrumb")}"><ol>{"".join(parts)}</ol></nav>'


def page_hero(trail, d, tag, h1, lede, byline=True, stand_text=None):
    by = ""
    if byline:
        by = (f'<p class="byline"><span>{T("Von", "By")} <strong>{BIZ["person"]}</strong>, {BIZ["role"]}, {BIZ["craft"]}</span>'
              f'<span>{T("Stand", "Updated")}: {stand_text or stand()}</span></p>')
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


def side_cta(d, heading=None, text=None):
    heading = heading or T("Direkt erreichbar", "Get in touch")
    text = text or T("Schildern Sie mir kurz Ihre Lage. Sie erhalten eine unverbindliche Beratung und ein individuelles Angebot.",
                     "Tell me briefly what happened. You will get non-binding advice and an individual quote.")
    return f'''<aside class="side-cta" aria-label="{T("Kontakt", "Contact")}">
  <h2>{esc(heading)}</h2>
  <p>{esc(text)}</p>
  <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
  <a class="btn btn-secondary" href="https://wa.me/{BIZ["phone_tel"].lstrip("+")}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
  <div class="mini">
    <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a>
    <span>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}</span>
    <a href="{u(S("contact"), d)}">{T("Anfrage per Formular", "Enquiry via form")}</a>
  </div>
</aside>'''


def faq_section(items, d, title=None, open_first=False, extra_class=""):
    det = []
    for i, (q, a) in enumerate(items):
        o = " open" if (open_first and i == 0) else ""
        det.append(f'<details{o}><summary>{esc(q)}</summary><div class="answer"><p>{rich(a, d)}</p></div></details>')
    return f'<div class="faq {extra_class}">' + "".join(det) + "</div>"


def cta_band(d, title=None, text=None):
    title = title or T("Unfall passiert? Rufen Sie an.", "Had an accident? Call now.")
    text = text or T("Ich berate Sie unverbindlich und vereinbare kurzfristig einen Besichtigungstermin.",
                     "I will advise you without obligation and arrange an inspection appointment at short notice.")
    return f'''<section class="cta-band" aria-label="{T("Kontakt aufnehmen", "Get in touch")}">
  <div class="wrap">
    <div class="copy">
      <h2>{esc(title)}</h2>
      <p>{esc(text)}</p>
    </div>
    <div class="hero-actions">
      <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
      <a class="btn btn-secondary" href="{u(S("contact"), d)}">{T("Anfrage senden", "Send enquiry")}</a>
    </div>
  </div>
</section>'''


def related(slugs, d):
    by_slug = {s["slug"]: s for s in SERVICES}
    by_slug.update({a["slug"]: a for a in ARTICLES})
    extra = {
        S("services"): (T("Alle Leistungen", "All services"),
                        T("Sechs Gutachten im Überblick und welches zu Ihrer Situation passt.", "Six reports at a glance and which one fits your situation.")),
        S("guide"): (T("Ratgeber", "Guide"),
                     T("Antworten auf häufige Fragen nach dem Unfall.", "Answers to common questions after an accident.")),
        S("area"): (T("Einsatzgebiet", "Service area"),
                    T("Landkreis Celle und Umkreis von 50 Kilometern.", "Celle district and a 50 km radius.")),
        S("why"): (T("Gründe für ein Kfz-Gutachten", "Reasons for an expert report"),
                   T("Warum ein Gutachten mehr bringt als ein Kostenvoranschlag.", "Why a report is worth more than a repair estimate.")),
        S("checklist"): (T("Unfall-Checkliste", "Accident checklist"),
                         T("Die ersten Schritte nach einem Unfall zum Abhaken.", "The first steps after an accident, to tick off.")),
        S("contact"): (T("Kontakt", "Contact"),
                       T("Anfrage senden oder direkt anrufen.", "Send an enquiry or call directly.")),
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
          <span class="more" aria-hidden="true">{T("Mehr erfahren →", "Learn more →")}</span>
        </li>''')
    return '<ul class="services">' + "\n".join(out) + "</ul>"


def contact_rows():
    wa = BIZ["phone_tel"].lstrip("+")
    copy_label = T("kopieren", "copy")
    dates = T(f"Besichtigung nach Absprache, {AREA['label']}", f"Inspection by arrangement, {AREA['label']}")
    return f'''<ul class="contact-rows">
        <li><span class="k">{T("Telefon", "Phone")}</span><span class="v"><a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a></span><button class="copy-btn" type="button" data-copy="{BIZ["phone_copy"]}">{copy_label}</button></li>
        <li><span class="k">WhatsApp</span><span class="v"><a href="https://wa.me/{wa}" target="_blank" rel="noopener">+49 172 517 81 50</a></span><span></span></li>
        <li><span class="k">{T("E-Mail", "Email")}</span><span class="v"><a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></span><button class="copy-btn" type="button" data-copy="{BIZ["email"]}">{copy_label}</button></li>
        <li><span class="k">{T("Adresse", "Address")}</span><span class="v">{BIZ["street"]}<br>{BIZ["zip"]} {BIZ["city"]}</span><span></span></li>
        <li><span class="k">{T("Termine", "Appointments")}</span><span class="v">{dates}</span><span></span></li>
      </ul>'''


def contact_lede():
    return T("Für eine unverbindliche Erstberatung, einen Besichtigungstermin oder ein individuelles Angebot. Am schnellsten erreichen Sie mich telefonisch oder per WhatsApp.",
             "For a non-binding first consultation, an inspection appointment or an individual quote. The quickest way to reach me is by phone or WhatsApp.")


def contact_compact(d):
    wa = BIZ["phone_tel"].lstrip("+")
    return f'''<section class="section section--surface-top contact-compact" id="kontakt" aria-labelledby="kontakt-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">{T("Kontakt", "Contact")}</p>
      <h2 id="kontakt-title">{T("Rufen Sie an oder schreiben Sie", "Call or send a message")}</h2>
      <p class="lede">{contact_lede()}</p>
    </div>
    <div class="contact-compact-grid">
      <div>{contact_rows()}</div>
      <div class="contact-actions">
        <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{BIZ["phone_display"]}</a>
        <a class="btn btn-secondary" href="https://wa.me/{wa}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
        <a class="btn btn-secondary" href="{u(S("contact"), d)}">{svg("mail")}{T("Anfrage per Formular", "Enquiry via form")}</a>
      </div>
    </div>
  </div>
</section>'''


def contact_section(d, h2=None, wrap_class="section contact section--surface-top"):
    h2 = h2 or T("Fragen Sie unverbindlich an", "Ask without obligation")
    wa = BIZ["phone_tel"].lstrip("+")
    required = f'<span class="req" aria-hidden="true">*</span>'
    demo = ""
    if PREVIEW:
        demo = ('<p class="demo-note">' + T("Vorschau: Hier wird nichts gesendet. Auf dem Server geht die Anfrage mit den Fotos per E-Mail an ",
                                           "Preview: nothing is sent here. On the server the enquiry is emailed with the photos to ") + BIZ["email"] + '.</p>')
    consent = T(
        f'Ich habe die <a href="{u(S("privacy"), d)}">Datenschutzerklärung</a> gelesen und bin einverstanden, dass meine Angaben und Fotos zur Bearbeitung meiner Anfrage verwendet werden.',
        f'I have read the <a href="{u(S("privacy"), d)}">privacy policy</a> and agree that my details and photos may be used to process my enquiry.')
    noscript = T(
        f'Zum Senden braucht das Formular JavaScript. Schreiben Sie sonst an <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a> oder rufen Sie an: <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>.',
        f'The form needs JavaScript to send. Otherwise write to <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a> or call: <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>.')
    success = T(
        f'Ihre Referenz: <strong id="success-ref"></strong>. Wir melden uns bei Ihnen. Bei einem akuten Schaden rufen Sie bitte direkt an: <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>.',
        f'Your reference: <strong id="success-ref"></strong>. We will get back to you. For urgent damage, please call directly: <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>.')
    options = "".join(f"<option>{esc(s['short'])}</option>" for s in SERVICES)
    return f'''<section class="{wrap_class}" id="kontakt" aria-labelledby="kontakt-title">
  <div class="wrap">
    <div class="contact-info">
      <p class="eyebrow">{T("Kontakt", "Contact")}</p>
      <h2 id="kontakt-title">{esc(h2)}</h2>
      <p class="lede">{contact_lede()}</p>
      {contact_rows()}
      <p class="contact-hint">{BIZ["person"]} · {BIZ["role"]} · {BIZ["craft"]}</p>
    </div>

    <div class="form-wrap">
    <form class="form" id="contact-form" novalidate data-endpoint="{"" if PREVIEW else "/api/anfrage.php"}"{' data-demo="true"' if PREVIEW else ""} data-phone="{BIZ["phone_display"]}" data-phone-tel="{BIZ["phone_tel"]}" data-email="{BIZ["email"]}">
      {demo}
      <div class="form-error" id="form-error" role="alert" hidden></div>
      <div class="row">
        <div class="field">
          <label for="f-name">Name {required}</label>
          <input type="text" id="f-name" name="name" autocomplete="name" autocapitalize="words" enterkeyhint="next" maxlength="100" required>
          <p class="field-error" id="err-name" hidden></p>
        </div>
        <div class="field">
          <label for="f-phone">{T("Telefon", "Phone")}</label>
          <input type="tel" id="f-phone" name="phone" autocomplete="tel" inputmode="tel" enterkeyhint="next" maxlength="40">
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label for="f-email">{T("E-Mail", "Email")} {required}</label>
          <input type="email" id="f-email" name="email" autocomplete="email" inputmode="email" autocapitalize="none" spellcheck="false" enterkeyhint="next" maxlength="254" required>
          <p class="field-error" id="err-email" hidden></p>
        </div>
        <div class="field">
          <label for="f-subject">{T("Anliegen", "Topic")} {required}</label>
          <select id="f-subject" name="subject" required>
            <option value="">{T("Bitte wählen", "Please choose")}</option>
            {options}
            <option>{T("Sonstige Frage", "Other question")}</option>
          </select>
          <p class="field-error" id="err-subject" hidden></p>
        </div>
      </div>
      <div class="field">
        <label for="f-message">{T("Nachricht", "Message")} {required}</label>
        <textarea id="f-message" name="message" maxlength="5000" required placeholder="{T("Kurz: Was ist passiert, welches Fahrzeug, wann passt Ihnen ein Termin?", "Briefly: what happened, which vehicle, when would an appointment suit you?")}"></textarea>
        <p class="field-error" id="err-message" hidden></p>
        <span class="help">{T("* Pflichtfelder", "* Required fields")}</span>
      </div>
      <div class="field" id="photos-field">
        <span class="label" id="photos-label">{T("Schadenfotos", "Damage photos")} <span class="opt">{T("optional", "optional")}</span></span>
        <div class="dropzone" id="dropzone">
          <input type="file" id="f-photos" class="file-input" accept="image/jpeg,image/png,image/webp" multiple aria-describedby="photos-help dz-count">
          <label for="f-photos" class="btn btn-secondary dz-btn">{svg("camera")}{T("Fotos auswählen", "Choose photos")}</label>
          <span class="dz-text">{T("oder hierher ziehen", "or drag them here")}</span>
          <span class="dz-count" id="dz-count">{T("Noch keine Fotos ausgewählt", "No photos selected yet")}</span>
        </div>
        <p class="help" id="photos-help">{T("Bis zu 5 Fotos (JPG, PNG, WebP). Die Fotos werden vor dem Senden verkleinert, Standortdaten werden entfernt. Bitte keine Fotos, auf denen Personen erkennbar sind.",
                                          "Up to 5 photos (JPG, PNG, WebP). Photos are reduced in size before sending and location data is removed. Please do not upload photos in which people can be recognised.")}</p>
        <ul class="photo-list" id="photo-list"></ul>
        <p class="field-error" id="err-photos" hidden></p>
      </div>
      <div class="hp" aria-hidden="true">
        <label for="f-website">{T("Bitte leer lassen", "Please leave empty")}</label>
        <input type="text" id="f-website" name="website" tabindex="-1" autocomplete="off">
      </div>
      <input type="hidden" id="f-token" name="token" value="">
      <div class="field">
        <label class="consent">
          <input type="checkbox" id="f-consent" name="consent" required>
          <span>{consent}</span>
        </label>
        <p class="field-error" id="err-consent" hidden></p>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit">{T("Anfrage senden", "Send enquiry")}</button>
        <span class="form-status" id="form-status" role="status" aria-live="polite"></span>
      </div>
      <noscript><p class="notice-js">{noscript}</p></noscript>
    </form>
    <div class="form-success" id="form-success" tabindex="-1" hidden>
      <h3>{T("Danke, Ihre Anfrage ist eingegangen.", "Thank you, we have received your enquiry.")}</h3>
      <p>{success}</p>
      <p><button class="btn btn-secondary" type="button" id="form-again">{T("Weitere Anfrage senden", "Send another enquiry")}</button></p>
    </div>
    </div>
  </div>
</section>'''


def checklist_html():
    lis = []
    for i, (t, sub) in enumerate(CHECKLIST, 1):
        lis.append(f'<li><label><input type="checkbox" id="chk-{i}"><span class="txt"><strong>{esc(t)}</strong><span>{esc(sub)}</span></span></label></li>')
    return "\n".join(lis)


def emergency_card(d):
    return f'''<aside class="emergency" aria-label="{T("Notrufnummern und W-Fragen", "Emergency numbers and the five Ws")}">
  <div class="numbers">
    <a href="tel:110"><b>110</b><small>{T("Polizei", "Police")}</small></a>
    <a href="tel:112"><b>112</b><small>{T("Rettungsdienst", "Emergency services")}</small></a>
  </div>
  <div>
    <h3>{T("Die W-Fragen beim Notruf", "What to say when you call")}</h3>
    <ol>
      <li><b>{T("Wo", "Where")}</b><span>{T("ist es passiert?", "did it happen?")}</span></li>
      <li><b>{T("Was", "What")}</b><span>{T("ist passiert?", "happened?")}</span></li>
      <li><b>{T("Wie viele", "How many")}</b><span>{T("Verletzte gibt es?", "people are injured?")}</span></li>
      <li><b>{T("Welche", "What")}</b><span>{T("Verletzungen?", "injuries?")}</span></li>
      <li><b>{T("Warten", "Wait")}</b><span>{T("auf Rückfragen.", "for questions.")}</span></li>
    </ol>
  </div>
  <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{T("Sachverständigen anrufen", "Call the expert")}</a>
</aside>'''


# ---------------------------------------------------------------- Seiten

def depth(slug):
    """Verzeichnistiefe einer Seite (Startseite: 0)."""
    return slug.count("/") + 1 if slug else 0


def sl(*keys):
    """Adressen mehrerer Seiten (nach key) in der aktuellen Sprache."""
    return [S(k) for k in keys]


def build_home():
    slug = S("home")
    d = depth(slug)
    faq = HOME_FAQ
    wa = BIZ["phone_tel"].lstrip("+")
    trust_zero = T('0<small>€</small>', '€0')
    steps = T(
        [("Kontakt aufnehmen", "Rufen Sie an oder schreiben Sie per WhatsApp. Wir klären kurz den Unfallhergang und was Sie jetzt brauchen."),
         ("Besichtigung", "Termin nach Absprache. Alle Schäden werden schriftlich und mit Fotos erfasst, auch Vor- und Altschäden."),
         ("Gutachten", "Reparaturkosten, Wertminderung, Reparaturdauer, bei Totalschaden Restwert und Wiederbeschaffungswert. Zügig und gerichtsfest."),
         ("Regulierung", "Sie legen das Gutachten der Versicherung vor und entscheiden auf sicherer Grundlage: reparieren, fiktiv abrechnen oder verkaufen.")],
        [("Get in touch", "Call or write on WhatsApp. We briefly clarify what happened and what you need now."),
         ("Inspection", "Appointment by arrangement. All damage is recorded in writing and with photos, including previous and old damage."),
         ("Report", "Repair costs, diminished value, repair time and, for a total loss, residual and replacement value. Prompt and court-proof."),
         ("Settlement", "You submit the report to the insurer and decide on a sound basis: repair, settle on the basis of the report (fiktive Abrechnung) or sell.")])
    steps_html = "\n        ".join(f"<li><h3>{esc(h)}</h3><p>{esc(p)}</p></li>" for h, p in steps)
    reasons = T(
        [("Kostenfreiheit", "Als Geschädigter dürfen Sie den Sachverständigen frei wählen. Die Kosten übernimmt in der Regel die Haftpflichtversicherung des Unfallverursachers."),
         ("Finanzielle Sicherheit", "Neben den Reparaturkosten erfasst das Gutachten Wertminderung, Reparaturdauer und Ausfallzeiten. Erst damit sind Ihre Ansprüche vollständig beziffert."),
         ("Beweissicherung", "Lehnt die gegnerische Versicherung Verantwortung ab, sind Sie mit einem Gutachten auf der sicheren Seite. Im Streitfall wird es vor Gericht anerkannt.")],
        [("No cost to you", "As the injured party you may choose the expert freely. The costs are usually paid by the liability insurer of the person at fault."),
         ("Financial security", "Besides the repair costs, the report covers diminished value, repair time and downtime. Only then are your claims fully quantified."),
         ("Evidence", "If the other party's insurer denies responsibility, a report keeps you on the safe side. In a dispute it is recognised in court.")])
    reasons_html = "\n        ".join(f"<article><h3>{esc(h)}</h3><p>{esc(p)}</p></article>" for h, p in reasons)
    facts = T([BIZ["craft"], "17 Jahre Sachverständiger in Deutschlands größter Sachverständigenorganisation",
               "Unabhängig von Versicherungen und Werkstätten", "Kontinuierliche Weiterbildung, alle Fahrzeugarten"],
              [BIZ["craft"], "17 years as an expert with Germany's largest expert organisation",
               "Independent of insurers and garages", "Continuous training, all types of vehicle"])
    facts_html = "\n          ".join(f'<li>{svg("check", "2.2")}<span>{f}</span></li>' for f in facts)
    body = f'''
  <section class="hero" aria-labelledby="hero-title">
    <div class="wrap">
      <div class="hero-copy">
        <p class="eyebrow">{T("Unverschuldeter Unfall? Wir beraten Sie gerne.", "Not-at-fault accident? We are happy to advise you.")}</p>
        <h1 id="hero-title">{T("Kfz-Gutachter in Celle: <em>unabhängig, schnell, auf Ihrer Seite.</em>", "Vehicle expert in Celle: <em>independent, fast, on your side.</em>")}</h1>
        <p class="lede">{T("Persönliche, kompetente Beratung bei der Schadensabwicklung. Ihr Kfz-Gutachten wird schnell und unkompliziert erstellt und ist unabhängig von jeder Versicherung.",
                           "Personal, competent advice when settling a claim. Your vehicle report is prepared quickly and without fuss, and is independent of any insurer.")}</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="tel:{BIZ["phone_tel"]}">{svg("phone")}{T("Jetzt anrufen", "Call now")}</a>
          <a class="btn btn-secondary" href="https://wa.me/{wa}" target="_blank" rel="noopener">{svg("whatsapp")}WhatsApp</a>
          <a class="btn btn-ghost" href="{u(S("services"), d)}">{T("Leistungen ansehen →", "View services →")}</a>
        </div>
        <p class="hero-note">{svg("shield")}<span>{T("Bei einem unverschuldeten Unfall trägt in der Regel die Haftpflichtversicherung des Unfallverursachers die Kosten für Ihr Gutachten. Sie haben das Recht, den Sachverständigen frei zu wählen.",
                                                       "After a not-at-fault accident, the liability insurer of the person at fault usually pays for your report. You have the right to choose the expert freely.")}</span></p>
      </div>
      <div class="hero-visual">
        <figure class="portrait">
          <img src="{asset("portrait.jpg", d)}" alt="{T("Patric Schneider, Kfz-Sachverständiger in Celle", "Patric Schneider, vehicle expert in Celle")}" width="543" height="618" fetchpriority="high">
        </figure>
        <div class="id-card">
          <div>
            <div class="name">{BIZ["person"]}</div>
            <div class="role">{BIZ["craft"]} · {BIZ["role"]}</div>
          </div>
          <dl>
            <dt>{T("Telefon", "Phone")}</dt><dd><a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a></dd>
            <dt>{T("E-Mail", "Email")}</dt><dd><a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></dd>
            <dt>{T("Standort", "Location")}</dt><dd>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}</dd>
          </dl>
        </div>
      </div>
    </div>
  </section>

  <section class="trust" aria-label="{T("Erfahrung und Grundsätze", "Experience and principles")}">
    <div class="wrap">
      <ul>
        <li><span class="num">30<small>+</small></span><span class="lbl">{T("Jahre Erfahrung im Kraftfahrzeugwesen", "years of experience in the motor vehicle trade")}</span></li>
        <li><span class="num">17</span><span class="lbl">{T("Jahre Kfz-Sachverständiger bei Europas größter Sachverständigenorganisation", "years as a vehicle expert with Europe's largest expert organisation")}</span></li>
        <li><span class="num">100<small>%</small></span><span class="lbl">{T("unabhängig von Versicherungen und Werkstätten", "independent of insurers and garages")}</span></li>
        <li><span class="num">{trust_zero}</span><span class="lbl">{T("Kosten für Sie im Haftpflichtfall. Die gegnerische Versicherung zahlt in der Regel.", "cost to you in a liability case. The other party's insurer usually pays.")}</span></li>
      </ul>
    </div>
  </section>

  <section class="section" id="leistungen" aria-labelledby="leistungen-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("Leistungen", "Services")}</p>
        <h2 id="leistungen-title">{T("Kfz-Gutachten in Celle für jede Situation", "Vehicle reports in Celle for every situation")}</h2>
        <p class="lede">{T("Pkw, Lkw, Nutzfahrzeug, Motorrad, Oldtimer oder E-Bike. Jedes Gutachten wird neutral erstellt und ist vor Gericht anerkannt.",
                           "Car, lorry, commercial vehicle, motorcycle, classic car or e-bike. Every report is prepared neutrally and is recognised in court.")}</p>
      </div>
      {service_cards(d)}
    </div>
  </section>

  <section class="section section--surface" id="ablauf" aria-labelledby="ablauf-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("So läuft es ab", "How it works")}</p>
        <h2 id="ablauf-title">{T("Vom Anruf bis zur Regulierung in vier Schritten", "From the first call to settlement in four steps")}</h2>
        <p class="lede">{T("Sie kümmern sich um das Wesentliche. Ich übernehme Dokumentation und Bewertung und unterstütze Sie im Umgang mit Versicherung, Werkstatt oder Anwalt.",
                           "You take care of what matters. I handle documentation and assessment and support you in dealing with the insurer, the garage or your lawyer.")}</p>
      </div>
      <ol class="steps">
        {steps_html}
      </ol>
    </div>
  </section>

  <section class="section" id="warum" aria-labelledby="warum-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("Gutachten statt Kostenvoranschlag", "Expert report instead of repair estimate")}</p>
        <h2 id="warum-title">{T("Warum ein Kostenvoranschlag nach dem Unfall nicht reicht", "Why a repair estimate is not enough after an accident")}</h2>
        <p class="lede">{T("Versicherungen akzeptieren gern einen Kostenvoranschlag mit Fotos und behaupten, einen Sachverständigen müssten Sie selbst bezahlen. Im Haftpflichtfall ist das gesetzlich anders geregelt.",
                           "Insurers like to accept a repair estimate with photos and claim that you would have to pay for an expert yourself. In a liability case the law says otherwise.")}</p>
      </div>
      <div class="reasons">
        {reasons_html}
      </div>
      <p><a class="btn btn-secondary" href="{u(S("why"), d)}">{T("Alle Gründe und Vergleich ansehen →", "See all reasons and the comparison →")}</a></p>
    </div>
  </section>

  <section class="section deep about" id="ueber-mich" aria-labelledby="about-title">
    <div class="wrap">
      <figure class="about-photo">
        <img src="{asset("portrait.jpg", d)}" alt="{T("Patric Schneider im Porträt", "Portrait of Patric Schneider")}" width="543" height="618" loading="lazy">
      </figure>
      <div class="about-copy">
        <p class="eyebrow">{T("Über mich", "About me")}</p>
        <h2 id="about-title">{T("Ein junges Unternehmen mit über 30 Jahren Erfahrung", "A young business with over 30 years of experience")}</h2>
        <p>{T(f"Mein Name ist {BIZ['person']}. Ich bin {BIZ['craft']} und {BIZ['role']} in Celle. 17 Jahre lang war ich als Kfz-Sachverständiger bei der größten Sachverständigenorganisation Deutschlands tätig und kenne alle Bereiche der Schadenregulierung aus der Praxis.",
              f"My name is {BIZ['person']}. I am a {BIZ['craft'].lower()} and {BIZ['role'].lower()} in Celle. For 17 years I worked as a vehicle expert for Germany's largest expert organisation, and I know every area of claims settlement from practical experience.")}</p>
        <p>{T("Ob Schadengutachten nach einem Verkehrsunfall, unfallanalytisches Gutachten bei Rechtsstreitigkeiten oder Wertgutachten für Ihren geliebten Oldtimer: Sie bekommen Ihr Gutachten mit dem passenden Sachverstand, zügig und ohne Umwege.",
              "Whether it is a damage report after a road accident, an accident reconstruction for a legal dispute or a valuation report for your beloved classic car: you get your report with the right expertise, promptly and without detours.")}</p>
        <ul class="facts">
          {facts_html}
        </ul>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{u(S("contact"), d)}">{T("Unverbindlich anfragen", "Enquire without obligation")}</a>
          <a class="btn btn-secondary" href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="unfall" aria-labelledby="unfall-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("Unfall passiert?", "Had an accident?")}</p>
        <h2 id="unfall-title">{T("Die ersten Schritte nach einem Unfall", "The first steps after an accident")}</h2>
        <p class="lede">{T("Ruhe bewahren und der Reihe nach vorgehen. Die vollständige Checkliste zum Abhaken finden Sie auf einer eigenen Seite.",
                           "Stay calm and work through it step by step. You will find the full checklist to tick off on a page of its own.")}</p>
      </div>
      <div class="checklist-grid">
        <div>
          <ol class="first-steps">
            {"".join(f"<li><div><strong>{esc(t)}</strong></div></li>" for t, _ in CHECKLIST)}
          </ol>
          <p class="checklist-foot"><a class="btn btn-secondary" href="{u(S("checklist"), d)}">{T("Zur Unfall-Checkliste →", "To the accident checklist →")}</a></p>
        </div>
        {emergency_card(d)}
      </div>
    </div>
  </section>

  <section class="section" id="ratgeber" aria-labelledby="ratgeber-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("Ratgeber", "Guide")}</p>
        <h2 id="ratgeber-title">{T("Antworten auf die häufigsten Fragen nach dem Unfall", "Answers to the most common questions after an accident")}</h2>
        <p class="lede">{T("Wertminderung, Totalschaden, Mietwagen und Kosten verständlich erklärt.", "Diminished value, total loss, rental cars and costs explained clearly.")}</p>
      </div>
      {related([a["slug"] for a in ARTICLES[:3]], d)}
      <p class="more-row"><a class="btn btn-secondary" href="{u(S("guide"), d)}">{T("Alle Ratgeber ansehen →", "View the whole guide →")}</a></p>
    </div>
  </section>

  <section class="section section--surface" id="faq" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("Häufige Fragen", "Frequently asked questions")}</p>
        <h2 id="faq-title">{T("Was Unfallgeschädigte am häufigsten fragen", "What accident victims ask most often")}</h2>
      </div>
      {faq_section(faq, d, open_first=True)}
    </div>
  </section>

  <section class="section" id="einsatzgebiet" aria-labelledby="gebiet-title">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">{T("Einsatzgebiet", "Service area")}</p>
        <h2 id="gebiet-title">{T("Im Landkreis Celle und im Umkreis von 50 Kilometern", "In Celle district and within 50 kilometres")}</h2>
        <p class="lede">{T("Besichtigungstermine nach Absprache, von Celle bis Hannover, Gifhorn, Soltau und Walsrode.",
                           "Inspection appointments by arrangement, from Celle to Hanover, Gifhorn, Soltau and Walsrode.")}</p>
      </div>
      {town_chips([t for t in PAGE_TOWNS], d)}
      <p class="more-row"><a class="btn btn-secondary" href="{u(S("area"), d)}">{T("Alle Orte im Einsatzgebiet →", "All places in the service area →")}</a></p>
    </div>
  </section>

  {contact_compact(d)}
'''
    graph = [business_node(), person_node(), website_node(), faq_node(faq)]
    return dict(slug=slug, d=d, key="home",
                title=T("Kfz-Gutachter Celle | Unabhängiger Sachverständiger PS Schneider",
                        "Vehicle Expert Celle | Independent Expert PS Schneider"),
                desc=T("Unabhängiger Kfz-Sachverständiger in Celle: Unfallgutachten, Wertgutachten, Beweissicherung, Leasingrückgabe, Restwert. Patric Schneider, Kfz-Meister.",
                       "Independent vehicle expert in Celle: accident reports, valuation reports, evidence reports, lease returns, residual value. Patric Schneider, master technician."),
                body=body, graph=graph)


def build_service(s):
    d = depth(s["slug"])
    trail = [(T("Leistungen", "Services"), S("services")), (s["short"], s["slug"])]
    secs = []
    for sec in s["sections"]:
        secs.append(f'''<section>
        <h2>{esc(sec["h2"])}</h2>
        {render_blocks(sec["body"], d)}
      </section>''')
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
      <div class="section-head"><h2 id="faq-title">{T("Häufige Fragen zum", "Frequently asked questions:")} {esc(s["short"])}</h2></div>
      {faq_section(s["faq"], d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">{T("Das könnte Sie auch interessieren", "You may also be interested in")}</h2></div>
      {related(s["related"], d)}
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [
        {"@type": "Service", "@id": abs_url(s["slug"]) + "#service", "name": s["short"], "serviceType": s["short"],
         "description": s["desc"], "url": abs_url(s["slug"]), "provider": business_ref(),
         "areaServed": area_served()},
        breadcrumb_node(trail),
        faq_node(s["faq"]),
    ]
    return dict(slug=s["slug"], d=d, key=s["key"], title=s["title"], desc=s["desc"], body=body, graph=graph)


def build_leistungen():
    slug = S("services")
    d = depth(slug)
    rows = T([
        ("Unverschuldeter Unfall, Schaden am Fahrzeug", "haftpflicht"),
        ("Totalschaden, das Fahrzeug soll verkauft werden", "restwert"),
        ("Gebrauchtwagen oder Reparatur ist mangelhaft", "beweis"),
        ("Rückgabe eines Leasingfahrzeugs, Streit um Wertminderung", "leasing"),
        ("Kauf, Verkauf oder Bewertung eines Oldtimers", "wert"),
        ("Unfallhergang ist strittig, es droht ein Rechtsstreit", "analyse"),
    ], [
        ("Not-at-fault accident, damage to your vehicle", "haftpflicht"),
        ("Total loss, the vehicle is to be sold", "restwert"),
        ("Used car or repair is defective", "beweis"),
        ("Return of a leased vehicle, dispute about diminished value", "leasing"),
        ("Buying, selling or valuing a classic car", "wert"),
        ("How the accident happened is disputed, a lawsuit is likely", "analyse"),
    ])
    by_key = {s["key"]: s for s in SERVICES}
    trs = "".join(f'<tr><th scope="row">{esc(a)}</th><td><a href="{u(by_key[k]["slug"], d)}">{esc(by_key[k]["short"])}</a></td></tr>' for a, k in rows)
    trail = [(T("Leistungen", "Services"), slug)]
    body = f'''
  {page_hero(trail, d, T("Leistungen", "Services"), T("Kfz-Gutachten in Celle: alle Leistungen", "Vehicle reports in Celle: all services"),
             T("Von der Schadenermittlung nach dem Unfall bis zur Bewertung Ihres Oldtimers. Alle Gutachten erstelle ich neutral, nachvollziehbar und zügig.",
               "From assessing the damage after an accident to valuing your classic car. I prepare every report neutrally, transparently and promptly."))}

  <section class="section" aria-labelledby="alle-title">
    <div class="wrap">
      <div class="section-head"><h2 id="alle-title">{T("Sechs Gutachten, ein Ansprechpartner", "Six reports, one point of contact")}</h2></div>
      {service_cards(d)}
    </div>
  </section>

  <section class="section section--surface" aria-labelledby="welches-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="welches-title">{T("Welches Gutachten brauche ich?", "Which report do I need?")}</h2>
        <p class="lede">{T("Ordnen Sie Ihre Situation zu. Wenn Sie unsicher sind, rufen Sie an. Wir klären das in wenigen Minuten.",
                           "Match your situation. If you are unsure, call. We will clear it up in a few minutes.")}</p>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead><tr><th scope="col">{T("Ihre Situation", "Your situation")}</th><th scope="col">{T("Passendes Gutachten", "Suitable report")}</th></tr></thead>
          <tbody>{trs}</tbody>
        </table>
      </div>
    </div>
  </section>

  {cta_band(d, T("Nicht sicher, was Sie brauchen?", "Not sure what you need?"),
             T("Schildern Sie mir Ihre Lage. Ich sage Ihnen ehrlich, welches Gutachten sinnvoll ist und ob es sich lohnt.",
               "Tell me about your situation. I will tell you honestly which report makes sense and whether it is worth it."))}
'''
    graph = [breadcrumb_node(trail),
             {"@type": "CollectionPage", "name": T("Leistungen", "Services"), "url": abs_url(slug),
              "about": {"@id": DOMAIN + "/#business"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "name": s["short"], "url": abs_url(s["slug"])}
                  for i, s in enumerate(SERVICES)]}}]
    return dict(slug=slug, d=d, key="services",
                title=T("Leistungen: Kfz-Gutachten in Celle | PS Schneider", "Services: Vehicle Expert Reports in Celle | PS Schneider"),
                desc=T("Alle Leistungen des Kfz-Sachverständigen in Celle: Haftpflichtschaden, Beweissicherung, Leasingrückgabe, Wertgutachten, Restwertermittlung, Unfallanalyse.",
                       "All services of the Celle vehicle expert: liability damage, evidence, lease returns, valuation reports, residual value, accident reconstruction."),
                body=body, graph=graph)


def build_article(a):
    d = depth(a["slug"])
    trail = [(T("Ratgeber", "Guide"), S("guide")), (a["short"], a["slug"])]
    secs = []
    for sec in a["sections"]:
        secs.append(f'''<section>
        <h2>{esc(sec["h2"])}</h2>
        {render_blocks(sec["body"], d)}
      </section>''')
    body = f'''
  {page_hero(trail, d, T("Ratgeber", "Guide"), a["h1"], a["lede"], stand_text=month_year(a["modified"]))}

  <div class="wrap page-grid">
    <article class="prose">
      <div class="summary">
        <p class="summary-label">{T("Kurz gesagt", "In short")}</p>
        <p>{rich(a["summary"], d)}</p>
      </div>
      {"".join(secs)}
      <p class="disclaimer">{T("Dieser Beitrag ist eine allgemeine Information und keine Rechtsberatung. Wie sich ein Schaden im Einzelfall abwickelt, hängt von den Umständen ab. Bei rechtlichen Fragen berät Sie Ihr Rechtsanwalt.",
                              "This article is general information and not legal advice. How a claim is settled in an individual case depends on the circumstances. For legal questions, please consult your lawyer.")}</p>
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">{T("Häufige Fragen", "Frequently asked questions")}</h2></div>
      {faq_section(a["faq"], d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">{T("Weiterlesen", "Further reading")}</h2></div>
      {related(a["related"], d)}
    </div>
  </section>

  {cta_band(d)}
'''
    url = abs_url(a["slug"])
    graph = [
        {"@type": "Article", "@id": url + "#article", "headline": a["h1"], "description": a["desc"],
         "datePublished": a["published"], "dateModified": a["modified"], "inLanguage": T("de-DE", "en-GB"),
         "mainEntityOfPage": url, "image": DOMAIN + "/assets/og-image.jpg",
         "author": {"@type": "Person", "@id": DOMAIN + "/#person", "name": BIZ["person"],
                    "jobTitle": BIZ["role"] + ", " + BIZ["craft"]},
         "publisher": business_ref()},
        breadcrumb_node(trail),
        faq_node(a["faq"]),
    ]
    return dict(slug=a["slug"], d=d, key=a["key"], title=a["title"], desc=a["desc"], body=body, graph=graph)


def build_ratgeber_index():
    slug = S("guide")
    d = depth(slug)
    items = []
    for a in ARTICLES:
        items.append(f'''<li>
          <h2><a href="{u(a["slug"], d)}">{esc(a["short"])}</a></h2>
          <p>{esc(a["lede"])}</p>
          <span class="more" aria-hidden="true">{T("Lesen →", "Read →")}</span>
        </li>''')
    trail = [(T("Ratgeber", "Guide"), slug)]
    checklist_line = T(f'Direkt nach einem Unfall? Die <a href="{u(S("checklist"), d)}">Unfall-Checkliste</a> führt Sie durch die ersten Schritte.',
                       f'Just had an accident? The <a href="{u(S("checklist"), d)}">accident checklist</a> takes you through the first steps.')
    body = f'''
  {page_hero(trail, d, T("Ratgeber", "Guide"), T("Ratgeber zum Kfz-Gutachten: Antworten nach dem Unfall", "Guide to vehicle reports: answers after an accident"),
             T("Was nach einem Unfall zählt, in verständlicher Sprache: Wertminderung, Totalschaden, Mietwagen, Kosten und Oldtimer-Bewertung.",
               "What matters after an accident, in plain language: diminished value, total loss, rental cars, costs and classic car valuation."), byline=False)}

  <section class="section" aria-labelledby="liste-title">
    <div class="wrap">
      <h2 class="visually-hidden" id="liste-title">{T("Alle Beiträge", "All articles")}</h2>
      <ul class="guide-list">
        {"".join(items)}
      </ul>
      <p class="more-row">{checklist_line}</p>
    </div>
  </section>

  {cta_band(d, T("Ihre Frage ist nicht dabei?", "Your question is not here?"),
             T("Schildern Sie mir Ihre Situation. Ich antworte unverbindlich und sage Ihnen ehrlich, was sinnvoll ist.",
               "Tell me about your situation. I will answer without obligation and tell you honestly what makes sense."))}
'''
    graph = [breadcrumb_node(trail),
             {"@type": "CollectionPage", "name": T("Ratgeber zum Kfz-Gutachten", "Guide to vehicle reports"), "url": abs_url(slug),
              "about": {"@id": DOMAIN + "/#business"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "name": a["short"], "url": abs_url(a["slug"])}
                  for i, a in enumerate(ARTICLES)]}}]
    return dict(slug=slug, d=d, key="guide",
                title=T("Ratgeber Kfz-Gutachten und Unfall | PS Schneider", "Guide: Vehicle Expert Reports and Accidents | PS Schneider"),
                desc=T("Ratgeber vom Kfz-Sachverständigen in Celle: Wertminderung, Totalschaden, Mietwagen, Gutachterkosten und Oldtimer-Wertgutachten verständlich erklärt.",
                       "Guide from the vehicle expert in Celle: diminished value, total loss, rental cars, expert costs and classic car valuation reports explained clearly."),
                body=body, graph=graph)


def town_chips(towns, d, current=None):
    items = []
    for t in towns:
        if t.get("home"):
            items.append(f'<li><a href="{u(S("home"), d)}">{esc(t["name"])}</a></li>')
        elif t.get("page") and t["name"] != current:
            items.append(f'<li><a href="{u(t["slug"], d)}">{esc(t["name"])}</a></li>')
        else:
            items.append(f'<li><span>{esc(t["name"])}</span></li>')
    return f'<ul class="chips">{"".join(items)}</ul>'


def area_svg(d):
    """Schematische Darstellung (keine Karte): Celle in der Mitte, Ringe bei 25 und 50 km."""
    px, mid = 5.6, 320  # Pixel pro km, Mittelpunkt
    pts = []
    for t in PAGE_TOWNS:
        dx, dy = xy_km(t["lat"], t["lon"])
        x, y = mid + dx * px, mid - dy * px
        left = dx < 0
        tx = x - 11 if left else x + 11
        anchor = "end" if left else "start"
        pts.append(f'<a href="{u(t["slug"], d)}"><circle class="pt" cx="{x:.0f}" cy="{y:.0f}" r="7"/>'
                   f'<text class="lb" x="{tx:.0f}" y="{y + 6:.0f}" text-anchor="{anchor}">{esc(t["name"])}</text></a>')
    r50, r25 = AREA["radius_km"] * px, AREA["radius_km"] / 2 * px
    label = T("Schema des Einsatzgebiets: Celle in der Mitte, Orte im Umkreis von 50 Kilometern",
              "Diagram of the service area: Celle in the centre, places within 50 kilometres")
    north = T("N", "N")
    return f'''<svg class="area-svg" viewBox="0 0 640 640" role="img" aria-label="{label}">
  <circle class="ring" cx="{mid}" cy="{mid}" r="{r50:.0f}"/>
  <circle class="ring ring-in" cx="{mid}" cy="{mid}" r="{r25:.0f}"/>
  <text class="ring-lb" x="{mid}" y="{mid - r25 - 6:.0f}" text-anchor="middle">25 km</text>
  <text class="ring-lb" x="{mid}" y="{mid - r50 - 6:.0f}" text-anchor="middle">50 km</text>
  <text class="ring-lb" x="{mid}" y="{mid - r50 - 26:.0f}" text-anchor="middle">{north}</text>
  {"".join(pts)}
  <circle class="home" cx="{mid}" cy="{mid}" r="9"/>
  <text class="lb lb-home" x="{mid}" y="{mid + 28}" text-anchor="middle">Celle</text>
</svg>'''


def area_faq():
    return T([
        ("In welchen Orten sind Sie tätig?",
         "Im gesamten Landkreis Celle und im Umkreis von 50 Kilometern um Celle, zum Beispiel in Hannover, Burgdorf, Gifhorn, Walsrode und Soltau. Die Liste auf dieser Seite nennt die größeren Orte."),
        ("Mein Ort steht nicht in der Liste. Was nun?",
         "Rufen Sie einfach an. Orte im Umkreis von rund 50 Kilometern um Celle gehören zum Einsatzgebiet, auch wenn sie hier nicht einzeln genannt sind. Liegt Ihr Ort weiter weg, fragen Sie trotzdem an."),
        ("Wo findet die Besichtigung statt?",
         "Das stimmen wir individuell ab. Rufen Sie an, dann klären wir Ort und Termin."),
    ], [
        ("In which places do you work?",
         "Throughout Celle district and within 50 kilometres of Celle, for example in Hanover, Burgdorf, Gifhorn, Walsrode and Soltau. The list on this page names the larger places."),
        ("My place is not on the list. What now?",
         "Just call. Places within about 50 kilometres of Celle belong to the service area even if they are not named individually here. If your place is further away, please ask anyway."),
        ("Where does the inspection take place?",
         "We agree that individually. Call me and we will settle the place and time."),
    ])


def build_area_hub():
    slug = S("area")
    d = depth(slug)
    regions = []
    for name, desc in AREA_REGIONS:
        towns = [t for t in TOWNS if t["region"] == name]
        regions.append(f'''<section>
        <h2>{esc(name)}</h2>
        <p>{esc(desc)}</p>
        {town_chips(towns, d)}
      </section>''')
    trail = [(T("Einsatzgebiet", "Service area"), slug)]
    faq = area_faq()
    body = f'''
  {page_hero(trail, d, T("Einsatzgebiet", "Service area"), T("Kfz-Gutachter im Landkreis Celle und Umkreis von 50 Kilometern", "Vehicle expert in Celle district and within 50 kilometres"),
             T("Unabhängige Kfz-Gutachten in Celle und in den Orten rundherum. Besichtigungstermine stimme ich individuell mit Ihnen ab.",
               "Independent vehicle reports in Celle and the places around it. I arrange inspection appointments with you individually."), byline=False)}

  <div class="wrap page-grid">
    <article class="prose">
      <section>
        <h2>{T("Wo ich für Sie da bin", "Where I am there for you")}</h2>
        <p>{T("Mein Büro ist in Celle. Von dort aus betreue ich den gesamten Landkreis Celle und die Orte im Umkreis von 50 Kilometern, vom Nordrand der Region Hannover bis in die Heide. Orte mit eigener Seite sind verlinkt.",
              "My office is in Celle. From there I serve the whole of Celle district and the places within 50 kilometres, from the northern edge of the Hanover region to the heath. Places with a page of their own are linked.")}</p>
        <figure class="area-map">
          {area_svg(d)}
          <figcaption>{T("Schema, keine Landkarte. Die Entfernungen sind Luftlinie ab Celle.", "A diagram, not a map. Distances are straight-line from Celle.")}</figcaption>
        </figure>
      </section>
      {"".join(regions)}
      <section>
        <h2>{T("Unfall außerhalb des Gebiets?", "Accident outside the area?")}</h2>
        <p>{T("Der Radius ist ein Richtwert. Liegt Ihr Ort weiter entfernt, rufen Sie an. Wir klären dann, ob sich ein Termin einrichten lässt.",
              "The radius is a guideline. If your place is further away, call. We will then see whether an appointment can be arranged.")}</p>
      </section>
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">{T("Häufige Fragen zum Einsatzgebiet", "Frequently asked questions about the service area")}</h2></div>
      {faq_section(faq, d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">{T("Leistungen", "Services")}</h2></div>
      {related(sl("services", "haftpflicht", "wert"), d)}
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [breadcrumb_node(trail),
             {"@type": "WebPage", "name": T("Einsatzgebiet", "Service area"), "url": abs_url(slug), "about": {"@id": DOMAIN + "/#business"}},
             faq_node(faq)]
    return dict(slug=slug, d=d, key="area",
                title=T("Einsatzgebiet: Kfz-Gutachter Landkreis Celle | PS Schneider", "Service Area: Vehicle Expert Celle District | PS Schneider"),
                desc=T("Kfz-Sachverständiger im Landkreis Celle und im Umkreis von 50 Kilometern: Celle, Bergen, Gifhorn, Burgdorf, Soltau, Walsrode, Hannover und weitere Orte.",
                       "Vehicle expert in Celle district and within 50 kilometres: Celle, Bergen, Gifhorn, Burgdorf, Soltau, Walsrode, Hanover and other places."),
                body=body, graph=graph)


def build_town(t):
    d = depth(t["slug"])
    name, region = t["name"], t["region"]
    here = (t["lat"], t["lon"])
    near = sorted((o for o in PAGE_TOWNS if o is not t),
                  key=lambda o: km_between(here[0], here[1], o["lat"], o["lon"]))[:3]
    h1 = T(f"Kfz-Gutachter in {name}", f"Vehicle expert in {name}")
    trail = [(T("Einsatzgebiet", "Service area"), S("area")), (T(f"Kfz-Gutachter {name}", f"Vehicle expert {name}"), t["slug"])]
    services = "".join(f'<li><a href="{u(s["slug"], d)}">{esc(s["short"])}</a></li>' for s in SERVICES)
    faq = T([
        (f"Sind Sie auch in {name} tätig?",
         f"Ja. {name} liegt rund {t['dist']} Kilometer Luftlinie von Celle entfernt und gehört zu meinem Einsatzgebiet im {AREA['label']}."),
        ("Wo findet die Besichtigung statt?",
         f"Das stimmen wir individuell ab. Rufen Sie an, dann klären wir, wo und wann ich Ihr Fahrzeug in oder um {name} besichtigen kann."),
        ("Wer zahlt das Gutachten nach einem unverschuldeten Unfall?",
         "In der Regel die Haftpflichtversicherung des Unfallverursachers. Sie haben das Recht, den Sachverständigen frei zu wählen."),
    ], [
        (f"Do you also work in {name}?",
         f"Yes. {name} is about {t['dist']} kilometres from Celle as the crow flies and belongs to my service area: {AREA['label']}."),
        ("Where does the inspection take place?",
         f"We agree that individually. Call me and we will settle where and when I can inspect your vehicle in or around {name}."),
        ("Who pays for the report after a not-at-fault accident?",
         "Usually the liability insurer of the person at fault. You have the right to choose the expert freely."),
    ])
    near_links = "".join(f'<li><a href="{u(o["slug"], d)}"><strong>{esc(o["name"])}</strong><span>{esc(o["kind"])} {esc(in_region(o["region"]))}</span></a></li>' for o in near)
    lede = T(f"Unabhängige Kfz-Gutachten für {name} und Umgebung. {name} liegt rund {t['dist']} Kilometer Luftlinie von Celle entfernt im {t['dir']}, mitten in meinem Einsatzgebiet.",
             f"Independent vehicle reports for {name} and the surrounding area. {name} lies about {t['dist']} kilometres {t['dir']} of Celle as the crow flies, right inside my service area.")
    intro = T(f"{esc(name)} ({esc(t['kind'])} {esc(in_region(region))}) gehört zu meinem Einsatzgebiet im {esc(AREA['label'])}. Wurde Ihr Fahrzeug in {esc(name)} oder Umgebung beschädigt, oder möchten Sie dort ein Fahrzeug bewerten lassen, erstelle ich Ihnen ein unabhängiges Gutachten.",
              f"{esc(name)} ({esc(t['kind'])} {esc(in_region(region))}) is part of my service area: {esc(AREA['label'])}. If your vehicle was damaged in or around {esc(name)}, or you would like a vehicle valued there, I will prepare an independent report for you.")
    steps = T([
        "Sie rufen an oder schreiben mir und schildern kurz, worum es geht.",
        f"Wir klären, wo und wann ich Ihr Fahrzeug in oder um {esc(name)} besichtigen kann.",
        "Ich dokumentiere Schaden oder Zustand und erstelle das Gutachten zügig.",
        "Sie erhalten das Gutachten und entscheiden über die nächsten Schritte.",
    ], [
        "You call or write to me and briefly describe what it is about.",
        f"We settle where and when I can inspect your vehicle in or around {esc(name)}.",
        "I document the damage or condition and prepare the report promptly.",
        "You receive the report and decide on the next steps.",
    ])
    steps_html = "\n          ".join(f"<li>{x}</li>" for x in steps)
    after = T(f'Sichern Sie zuerst die Unfallstelle. Bei Verletzten rufen Sie die 112, bei einem Unfall mit Polizeiaufnahme die 110. Danach erreichen Sie mich telefonisch. Die <a href="{u(S("checklist"), d)}">Unfall-Checkliste</a> führt Sie durch die ersten Schritte.',
              f'First secure the accident scene. If anyone is injured, call 112; for an accident the police are to attend, call 110. Then you can reach me by phone. The <a href="{u(S("checklist"), d)}">accident checklist</a> takes you through the first steps.')
    body = f'''
  {page_hero(trail, d, T("Einsatzgebiet", "Service area"), h1, lede, byline=False)}

  <div class="wrap page-grid">
    <article class="prose">
      <section>
        <h2>{T(f"Gutachten für {esc(name)}", f"Reports for {esc(name)}")}</h2>
        <p>{intro}</p>
        <ul>{services}</ul>
      </section>
      <section>
        <h2>{T("So läuft ein Termin ab", "How an appointment works")}</h2>
        <ol>
          {steps_html}
        </ol>
      </section>
      <section>
        <h2>{T(f"Nach einem Unfall in {esc(name)}", f"After an accident in {esc(name)}")}</h2>
        <p>{after}</p>
      </section>
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="faq-title">
    <div class="wrap">
      <div class="section-head"><h2 id="faq-title">{T(f"Häufige Fragen zu {esc(name)}", f"Frequently asked questions about {esc(name)}")}</h2></div>
      {faq_section(faq, d, open_first=True)}
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">{T("Weitere Orte in der Nähe", "More places nearby")}</h2></div>
      <ul class="related">{near_links}</ul>
      <p class="more-row"><a href="{u(S("area"), d)}">{T("Alle Orte im Einsatzgebiet", "All places in the service area")}</a></p>
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [
        {"@type": "Service", "@id": abs_url(t["slug"]) + "#service", "name": T(f"Kfz-Gutachter {name}", f"Vehicle expert {name}"),
         "serviceType": T("Kfz-Gutachten", "Vehicle expert reports"),
         "url": abs_url(t["slug"]), "provider": business_ref(), "areaServed": {"@type": "City", "name": name}},
        breadcrumb_node(trail),
        faq_node(faq),
    ]
    return dict(slug=t["slug"], d=d, key=t["key"],
                title=T(f"Kfz-Gutachter {name} | PS Schneider", f"Vehicle Expert {name} | PS Schneider"),
                desc=T(f"Unabhängiger Kfz-Gutachter für {name}: Unfallgutachten, Wertgutachten und mehr. Rund {t['dist']} km von Celle, Termin nach Absprache. Tel. 0172 517 81 50.",
                       f"Independent vehicle expert for {name}: accident reports, valuation reports and more. About {t['dist']} km from Celle, appointment by arrangement. Tel. +49 172 517 81 50."),
                body=body, graph=graph)


def build_gruende():
    slug = S("why")
    d = depth(slug)
    secs = []
    for h, paras in REASONS:
        secs.append(f'<section><h2>{esc(h)}</h2>' + "".join(f"<p>{rich(p, d)}</p>" for p in paras) + "</section>")
    ok = f'<td class="yes">{svg("check", "2.5")}{T("ja", "yes")}</td>'
    no = f'<td class="no">{T("nein", "no")}</td>'
    rows = "".join(f'<tr><th scope="row">{esc(n)}</th>{ok if a else no}{ok if b else no}</tr>' for n, a, b in COMPARE_ROWS)
    name = T("Gründe für ein Kfz-Gutachten", "Reasons for a vehicle expert report")
    trail = [(name, slug)]
    body = f'''
  {page_hero(trail, d, T("Gutachten statt Kostenvoranschlag", "Expert report instead of repair estimate"),
             T("Wozu ein Kfz-Gutachten erstellen lassen?", "Why have a vehicle expert report prepared?"),
             T("Nach einem Unfall schlagen Versicherungen oft einen Kostenvoranschlag vor. Sechs Gründe, warum ein unabhängiges Gutachten Ihnen mehr bringt.",
               "After an accident, insurers often suggest a repair estimate. Six reasons why an independent report is worth more to you."))}

  <div class="wrap page-grid">
    <article class="prose">
      {"".join(secs)}
    </article>
    {side_cta(d)}
  </div>

  <section class="section section--surface" aria-labelledby="cmp-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="cmp-title">{T("Kostenvoranschlag und Gutachten im Vergleich", "Repair estimate and expert report compared")}</h2>
      </div>
      <div class="compare-wrap">
        <table class="compare">
          <thead><tr><th scope="col">{T("Erfasst", "Covers")}</th><th scope="col">{T("Kosten&shy;voranschlag", "Repair estimate")}</th><th scope="col">{T("Kfz-Gutachten", "Expert report")}</th></tr></thead>
          <tbody>{rows}</tbody>
          <tfoot><tr><td colspan="3">{T("Im Haftpflichtfall werden die Gutachtenkosten dem Schaden zugerechnet und von der Versicherung des Unfallverursachers getragen. Bei reinen Bagatellschäden lohnt sich ein Gutachten oft nicht. Das klären wir vorab am Telefon.",
                                         "In a liability case the cost of the report counts as part of the damage and is borne by the insurer of the person at fault. For purely minor damage a report is often not worthwhile. We clarify that beforehand by phone.")}</td></tr></tfoot>
        </table>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">{T("Passende Leistungen", "Related services")}</h2></div>
      {related(sl("haftpflicht", "kosten", "checklist"), d)}
    </div>
  </section>

  {cta_band(d)}
'''
    graph = [breadcrumb_node(trail),
             {"@type": "WebPage", "name": name, "url": abs_url(slug), "about": {"@id": DOMAIN + "/#business"}}]
    return dict(slug=slug, d=d, key="why",
                title=T("Gründe für ein Kfz-Gutachten nach dem Unfall | PS Schneider", "Why Get a Vehicle Expert Report After an Accident | PS Schneider"),
                desc=T("Warum ein unabhängiges Kfz-Gutachten mehr bringt als ein Kostenvoranschlag: Kosten, Wertminderung, Beweissicherung, fiktive Abrechnung. Celle.",
                       "Why an independent vehicle expert report is worth more than a repair estimate: costs, diminished value, evidence, settling on the basis of the report. Celle."),
                body=body, graph=graph)


def build_checkliste():
    slug = S("checklist")
    d = depth(slug)
    trail = [(T("Unfall-Checkliste", "Accident checklist"), slug)]
    hp = next(s for s in SERVICES if s["key"] == "haftpflicht")
    link = f'<a href="{u(hp["slug"], d)}">{hp["short"]}</a>'
    link_lc = f'<a href="{u(hp["slug"], d)}">{hp["short"].lower()}</a>'
    later = T([
        "Geben Sie am Unfallort kein Schuldeingeständnis ab, auch nicht mündlich.",
        "Notieren Sie sich das polizeiliche Aktenzeichen, falls die Polizei den Unfall aufgenommen hat.",
        "Lassen Sie das Fahrzeug nicht reparieren, bevor es begutachtet wurde.",
        "Informieren Sie Ihre Versicherung zeitnah.",
        f"Rufen Sie mich früh an. Ich erkläre Ihnen, ob ein {link} sinnvoll ist.",
    ], [
        "Do not admit fault at the scene, not even verbally.",
        "Note the police reference number if the police attended the accident.",
        "Do not have the vehicle repaired before it has been assessed.",
        "Inform your insurer promptly.",
        f"Call me early. I will explain whether a {link_lc} makes sense.",
    ])
    later_html = "\n            ".join(f"<li>{x}</li>" for x in later)
    body = f'''
  {page_hero(trail, d, T("Unfall-Checkliste", "Accident checklist"), T("Wie verhält man sich nach einem Unfall?", "What to do after an accident"),
             T("Sechs Schritte in der richtigen Reihenfolge. Haken Sie ab, was erledigt ist. Die Liste bleibt auf Ihrem Gerät gespeichert und wird nicht an uns übertragen.",
               "Six steps in the right order. Tick off what is done. The list stays saved on your device and is not sent to us."))}

  <section class="section" aria-labelledby="check-title">
    <div class="wrap">
      <h2 class="visually-hidden" id="check-title">{T("Checkliste", "Checklist")}</h2>
      <div class="checklist-grid">
        <div>
          <ol class="checklist" id="checklist">
            {checklist_html()}
          </ol>
          <div class="checklist-foot">
            <span id="checklist-progress">{T(f"0 von {len(CHECKLIST)} erledigt", f"0 of {len(CHECKLIST)} done")}</span>
            <button type="button" id="checklist-reset">{T("Liste zurücksetzen", "Reset list")}</button>
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
          <h2 id="danach-title">{T("In den Tagen danach", "In the days after")}</h2>
          <ul>
            {later_html}
          </ul>
        </section>
      </div>
    </div>
  </section>

  {cta_band(d, T("Sachverständigen kontaktieren", "Contact the expert"),
             T("Je früher ich den Schaden sehe, desto besser lässt er sich dokumentieren. Rufen Sie an oder schreiben Sie per WhatsApp.",
               "The sooner I see the damage, the better it can be documented. Call or write on WhatsApp."))}
'''
    graph = [breadcrumb_node(trail),
             {"@type": "WebPage", "name": T("Unfall-Checkliste", "Accident checklist"), "url": abs_url(slug),
              "about": {"@id": DOMAIN + "/#business"}}]
    return dict(slug=slug, d=d, key="checklist",
                title=T("Unfall-Checkliste: Was tun nach einem Unfall? | PS Schneider", "Accident Checklist: What to Do After an Accident | PS Schneider"),
                desc=T("Checkliste zum Abhaken: Unfallstelle sichern, Verletzte versorgen, Polizei rufen, Daten austauschen, Fotos machen, Sachverständigen kontaktieren.",
                       "A checklist to tick off: secure the scene, help the injured, call the police, exchange details, take photos, contact the vehicle expert."),
                body=body, graph=graph)


def build_kontakt():
    slug = S("contact")
    d = depth(slug)
    trail = [(T("Kontakt", "Contact"), slug)]
    body = f'''
  {page_hero(trail, d, T("Kontakt", "Contact"), T("Kontakt zum Kfz-Sachverständigen in Celle", "Contact the vehicle expert in Celle"),
             T("Rufen Sie an, schreiben Sie per WhatsApp oder senden Sie die Anfrage über das Formular. Sie erhalten eine unverbindliche Beratung und ein individuelles Angebot.",
               "Call, write on WhatsApp or send your enquiry through the form. You will receive non-binding advice and an individual quote."),
             byline=False)}
  {contact_section(d, T("Anfrage senden", "Send an enquiry"), "section contact")}
  {cta_band(d, T("Lieber direkt sprechen?", "Prefer to talk directly?"), T("Bei einem akuten Schaden ist der Anruf der schnellste Weg.", "For urgent damage, calling is the quickest way."))}
'''
    graph = [breadcrumb_node(trail),
             {"@type": "ContactPage", "name": T("Kontakt", "Contact"), "url": abs_url(slug),
              "about": {"@id": DOMAIN + "/#business"}}, business_node()]
    return dict(slug=slug, d=d, key="contact",
                title=T("Kontakt zum Kfz-Gutachter in Celle | PS Schneider", "Contact the Vehicle Expert in Celle | PS Schneider"),
                desc=T("Kontakt zu Kfz-Sachverständigem Patric Schneider in Celle: Telefon 0172 517 81 50, E-Mail, WhatsApp und Anfrageformular. Im Röthel 43, 29225 Celle.",
                       "Contact vehicle expert Patric Schneider in Celle: phone +49 172 517 81 50, email, WhatsApp and enquiry form. Im Röthel 43, 29225 Celle, Germany."),
                body=body, graph=graph)


def legal_page(key, title, eyebrow, h1, inner):
    slug = S(key)
    d = depth(slug)
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
    return dict(slug=slug, d=d, key=key, title=title,
                desc=T(h1 + " von PS Schneider, Kfz-Sachverständiger in Celle.", h1 + " of PS Schneider, vehicle expert in Celle."),
                body=body, graph=None, noindex=True)


def build_impressum():
    if LANG == "en":
        inner = f'''
      <p class="notice">Note for the operator: the fields marked in yellow must be filled in or removed before publication. The previous site contained placeholders here. Delete this note afterwards. This English version is a courtesy translation; the German version is legally binding.</p>

      <h2>Service provider</h2>
      <address>{BIZ["person"]}<br>{BIZ["role"]}<br>{BIZ["street"]}<br>{BIZ["zip"]} {BIZ["city"]}<br>Germany</address>

      <h2>Contact</h2>
      <p>Phone: <a href="tel:{BIZ["phone_tel"]}">{BIZ["phone_display"]}</a><br>Email: <a href="mailto:{BIZ["email"]}">{BIZ["email"]}</a></p>

      <h2>Professional title</h2>
      <p>{BIZ["craft"]} (Kraftfahrzeugtechnikermeister, awarded in the Federal Republic of Germany)<br>{BIZ["role"]}</p>

      <h2>VAT</h2>
      <p>VAT identification number pursuant to § 27a of the German VAT Act (UStG): <span class="todo">enter DE XXX XXX XXX or remove paragraph</span></p>
      <p>Economic identification number (W-IdNr.): <span class="todo">enter or remove paragraph</span></p>

      <h2>Supervisory authority and chamber</h2>
      <p><span class="todo">Enter the competent Chamber of Crafts (Handwerkskammer) or remove paragraph</span></p>

      <h2>Responsible for the content</h2>
      <p>{BIZ["person"]}, address as above.</p>

      <h2>Consumer dispute resolution</h2>
      <p>We are neither willing nor obliged to take part in dispute resolution proceedings before a consumer arbitration board.</p>

      <h2>Liability for content</h2>
      <p>The content of these pages has been prepared with the greatest care. However, we cannot guarantee that it is correct, complete or up to date. As a service provider we are responsible for our own content on these pages under the general laws.</p>

      <h2>Liability for links</h2>
      <p>Our website contains links to external third-party websites over whose content we have no influence. The respective provider or operator of those pages is always responsible for their content.</p>

      <h2>Image credits</h2>
      <p>Portrait photo: {BIZ["person"]}, private.</p>
'''
        return legal_page("legal", "Legal Notice | PS Schneider Vehicle Expert Celle", "Information pursuant to § 5 DDG", "Legal notice", inner)
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
    return legal_page("legal", "Impressum | PS Schneider Kfz-Gutachter Celle", "Angaben gemäß § 5 DDG", "Impressum", inner)


def build_datenschutz():
    if LANG == "en":
        inner = f'''
      <p class="notice">Note for the operator: this statement describes the technology of this website (contact form with photos on a Hetzner server, no cookies, no analytics tools, self-hosted fonts). The places marked in yellow must be clarified and filled in before going live: server location and data processing agreement with Hetzner, mailbox provider, retention period of the server logs. If cookies, statistics or external content are added later, the notice and this statement must be adjusted. This text does not replace a legal review. This English version is a courtesy translation; the German version is legally binding. Delete this note afterwards.</p>

      <h2>1. Controller</h2>
      <address>{BIZ["person"]}<br>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}<br>Phone: {BIZ["phone_display"]}<br>Email: {BIZ["email"]}</address>

      <h2>2. Overview</h2>
      <p>This website does not set cookies and does not use any tracking or analytics services. No third-party content is embedded and no fonts are loaded from external servers. We process personal data when you use the contact form or contact us, and in the form of technically necessary connection data when you visit the site.</p>

      <h2>3. Hosting and server log files</h2>
      <p>This website is operated on a server of Hetzner Online GmbH, Industriestr. 25, 91710 Gunzenhausen, Germany. <span class="todo">Enter the location of the data centre and conclude or confirm the data processing agreement under Art. 28 GDPR with Hetzner</span></p>
      <p>When you visit the website, the web server automatically processes information transmitted by your browser: shortened IP address, date and time, page requested, amount of data transferred, browser type and operating system. This data serves the security and stability of the website and is deleted after <span class="todo">enter period, 7 days recommended</span>. The legal basis is Art. 6(1)(f) GDPR (legitimate interest in the secure operation of the site).</p>

      <h2>4. Contact form and damage photos</h2>
      <p>If you use the contact form, we transmit your details to our server in encrypted form (HTTPS): name, email address, topic, message and, if you wish, your phone number and up to five photos. Name, email address, topic and message are required so that we can answer your enquiry.</p>
      <h3>Photos</h3>
      <p>Photos are already reduced in size in your browser. The server reduces them again and removes metadata such as the location where the photo was taken. Please do not upload photos in which people can be recognised.</p>
      <h3>Forwarding and deletion</h3>
      <p>The server forwards your enquiry with the photos by email to our mailbox. The transmission to the mail server is encrypted. Mailbox provider: <span class="todo">enter name and address of the provider, check data processing agreement</span> After successful delivery, the enquiry and photos are deleted from the server. If delivery fails for technical reasons, the enquiry is kept safe for 14 days at most so that it is not lost, and is then deleted.</p>
      <h3>Protection against abuse</h3>
      <p>To prevent the form from being abused by automated programs, we limit the number of enquiries per connection. For this we do not store your IP address in plain text but only a hash with a secret key, which is deleted after two days at most. We also check a field that is invisible to people and a time-limited form token. Both work without cookies and without third-party services.</p>
      <h3>Log</h3>
      <p>The form log contains only the time, reference number, number of photos and status, but no names or contact details. It is deleted after <span class="todo">enter period, 90 days recommended</span>.</p>
      <h3>Legal basis</h3>
      <p>Processing takes place to answer your enquiry and to prepare a contract (Art. 6(1)(b) GDPR) and to protect against abuse (Art. 6(1)(f) GDPR). Enquiry data is deleted as soon as it is no longer needed for processing and no statutory retention obligations apply.</p>

      <h2>5. Email, phone and WhatsApp</h2>
      <p>If you contact us by email, phone or WhatsApp, we process the data you send to handle your enquiry and for any follow-up questions. The legal basis is Art. 6(1)(b) GDPR and Art. 6(1)(f) GDPR (legitimate interest in answering enquiries).</p>
      <p>With WhatsApp, data is transmitted to WhatsApp Ireland Limited (Meta), including your phone number and metadata of the communication. Content is end-to-end encrypted. Only use WhatsApp if you agree to this. Alternatively you can reach us at any time by phone, email or through the contact form.</p>

      <h2>6. Commissions and reports</h2>
      <p>If you commission a report, we process the data required for it: your contact details, vehicle data (registration number, vehicle identification number, mileage), details of the damage event, photos of the vehicle and, for liability damage, data of the other party and their insurer. The legal basis is Art. 6(1)(b) GDPR.</p>
      <p>For settlement we pass the report on to the recipients you name, such as the insurer handling the claim, your garage or your lawyer. For calculation and residual value assessment we use industry-standard specialist systems. <span class="todo">Enter the systems and residual value exchanges used or remove sentence</span></p>
      <p>We keep reports and related documents in line with commercial and tax law requirements (generally 10 years, § 147 AO, § 257 HGB).</p>

      <h2>7. Cookies and local storage</h2>
      <p>This website does not set cookies. It uses neither statistics nor advertising tools and does not load content, maps, videos or fonts from third-party servers.</p>
      <p>The accident checklist remembers ticked items in your browser's local storage. This information does not leave your device, is not transmitted to us and can be deleted at any time via "Reset list" or the browser settings. This is purely functional storage that is necessary for the service you requested (§ 25(2) no. 2 TDDDG). A consent prompt and a cookie banner are therefore not required.</p>

      <h2>8. Your rights</h2>
      <p>You have the following rights with regard to your personal data:</p>
      <ul>
        <li>Access (Art. 15 GDPR)</li>
        <li>Rectification (Art. 16 GDPR)</li>
        <li>Erasure (Art. 17 GDPR)</li>
        <li>Restriction of processing (Art. 18 GDPR)</li>
        <li>Data portability (Art. 20 GDPR)</li>
        <li>Objection to processing based on Art. 6(1)(f) GDPR (Art. 21 GDPR)</li>
      </ul>
      <p>You also have the right to lodge a complaint with a data protection supervisory authority. The competent authority is the State Commissioner for Data Protection of Lower Saxony (Landesbeauftragte für den Datenschutz Niedersachsen), Prinzenstraße 5, 30159 Hanover, Germany.</p>

      <h2>9. Data security</h2>
      <p>The website is delivered encrypted via HTTPS. The configuration of the form is not in the publicly accessible area of the server. We take appropriate technical and organisational measures to protect your data against loss, manipulation and unauthorised access.</p>

      <h2>10. Changes</h2>
      <p>We will amend this privacy policy if the website or the legal requirements change. The version published here at the time applies.</p>
'''
        return legal_page("privacy", "Privacy Policy | PS Schneider Vehicle Expert Celle", f"Updated: {stand()}", "Privacy policy", inner)
    inner = f'''
      <p class="notice">Hinweis für den Betreiber: Diese Erklärung beschreibt die Technik dieser Website (Kontaktformular mit Fotos auf einem Server von Hetzner, keine Cookies, keine Analyse-Tools, selbst gehostete Schriften). Die gelb markierten Stellen müssen vor dem Livegang geklärt und ausgefüllt werden: Serverstandort und Auftragsverarbeitung bei Hetzner, Anbieter des Postfachs, Aufbewahrungsdauer der Server-Protokolle. Kommen später Cookies, Statistik oder externe Inhalte hinzu, müssen Banner und Erklärung angepasst werden. Eine rechtliche Prüfung ersetzt dieser Text nicht. Diesen Hinweis danach löschen.</p>

      <h2>1. Verantwortlicher</h2>
      <address>{BIZ["person"]}<br>{BIZ["street"]}, {BIZ["zip"]} {BIZ["city"]}<br>Telefon: {BIZ["phone_display"]}<br>E-Mail: {BIZ["email"]}</address>

      <h2>2. Überblick</h2>
      <p>Diese Website setzt keine Cookies und verwendet keine Tracking- oder Analyse-Dienste. Es werden keine Inhalte von Drittanbietern eingebunden und keine Schriften von externen Servern geladen. Personenbezogene Daten verarbeiten wir, wenn Sie das Kontaktformular nutzen oder uns kontaktieren, und in Form technisch notwendiger Verbindungsdaten beim Aufruf der Seite.</p>

      <h2>3. Hosting und Server-Logfiles</h2>
      <p>Diese Website wird auf einem Server der Hetzner Online GmbH, Industriestr. 25, 91710 Gunzenhausen, betrieben. <span class="todo">Standort des Rechenzentrums eintragen und den Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO mit Hetzner abschließen beziehungsweise bestätigen</span></p>
      <p>Beim Aufruf der Website verarbeitet der Webserver automatisch Informationen, die Ihr Browser übermittelt: gekürzte IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, übertragene Datenmenge, Browsertyp und Betriebssystem. Diese Daten dienen der Sicherheit und Stabilität der Website und werden nach <span class="todo">Dauer eintragen, empfohlen 7 Tage</span> gelöscht. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse am sicheren Betrieb).</p>

      <h2>4. Kontaktformular und Schadenfotos</h2>
      <p>Wenn Sie das Kontaktformular nutzen, übertragen wir Ihre Angaben verschlüsselt (HTTPS) an unseren Server: Name, E-Mail-Adresse, Anliegen, Nachricht, auf Wunsch Ihre Telefonnummer und bis zu fünf Fotos. Die Angabe von Name, E-Mail-Adresse, Anliegen und Nachricht ist erforderlich, damit wir Ihre Anfrage beantworten können.</p>
      <h3>Fotos</h3>
      <p>Fotos werden schon in Ihrem Browser verkleinert. Der Server verkleinert sie erneut und entfernt dabei Metadaten wie den Aufnahmeort. Bitte laden Sie keine Fotos hoch, auf denen Personen erkennbar sind.</p>
      <h3>Weiterleitung und Löschung</h3>
      <p>Der Server leitet Ihre Anfrage mit den Fotos per E-Mail an unser Postfach weiter. Die Übertragung zum Mailserver ist verschlüsselt. Postfachanbieter: <span class="todo">Name und Anschrift des Anbieters eintragen, Auftragsverarbeitung prüfen</span> Nach erfolgreichem Versand werden Anfrage und Fotos auf dem Server gelöscht. Schlägt der Versand technisch fehl, bleibt die Anfrage höchstens 14 Tage gesichert, damit sie nicht verloren geht, und wird dann gelöscht.</p>
      <h3>Schutz vor Missbrauch</h3>
      <p>Damit das Formular nicht von automatischen Programmen missbraucht wird, begrenzen wir die Zahl der Anfragen pro Verbindung. Dafür speichern wir Ihre IP-Adresse nicht im Klartext, sondern nur einen Hash mit geheimem Schlüssel, der nach höchstens zwei Tagen gelöscht wird. Außerdem prüfen wir ein für Menschen unsichtbares Feld und ein zeitlich begrenztes Formular-Token. Beides arbeitet ohne Cookies und ohne Dienste Dritter.</p>
      <h3>Protokoll</h3>
      <p>Das Protokoll des Formulars enthält nur Zeitpunkt, Referenznummer, Anzahl der Fotos und Status, aber keine Namen oder Kontaktdaten. Es wird nach <span class="todo">Dauer eintragen, empfohlen 90 Tage</span> gelöscht.</p>
      <h3>Rechtsgrundlage</h3>
      <p>Die Verarbeitung erfolgt zur Beantwortung Ihrer Anfrage und zur Anbahnung eines Vertrags (Art. 6 Abs. 1 lit. b DSGVO) sowie zum Schutz vor Missbrauch (Art. 6 Abs. 1 lit. f DSGVO). Anfragedaten werden gelöscht, sobald sie für die Bearbeitung nicht mehr erforderlich sind und keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</p>

      <h2>5. E-Mail, Telefon und WhatsApp</h2>
      <p>Wenn Sie uns per E-Mail, Telefon oder WhatsApp kontaktieren, verarbeiten wir die übermittelten Daten zur Bearbeitung Ihrer Anfrage und für eventuelle Anschlussfragen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO sowie Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der Beantwortung von Anfragen).</p>
      <p>Bei WhatsApp werden Daten an WhatsApp Ireland Limited (Meta) übermittelt, darunter Ihre Telefonnummer und Metadaten der Kommunikation. Inhalte sind Ende-zu-Ende verschlüsselt. Nutzen Sie WhatsApp nur, wenn Sie damit einverstanden sind. Alternativ erreichen Sie uns jederzeit per Telefon, E-Mail oder über das Kontaktformular.</p>

      <h2>6. Auftragsbearbeitung und Gutachten</h2>
      <p>Beauftragen Sie ein Gutachten, verarbeiten wir die dafür notwendigen Daten: Ihre Kontaktdaten, Fahrzeugdaten (Kennzeichen, Fahrzeug-Identifizierungsnummer, Laufleistung), Angaben zum Schadenereignis, Fotos des Fahrzeugs sowie bei Haftpflichtschäden Daten des Unfallgegners und dessen Versicherung. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO.</p>
      <p>Zur Abwicklung übermitteln wir das Gutachten an die von Ihnen benannten Empfänger, etwa die regulierende Versicherung, Ihre Werkstatt oder Ihren Rechtsanwalt. Zur Kalkulation und Restwertermittlung setzen wir branchenübliche Fachsysteme ein. <span class="todo">Verwendete Systeme und Restwertbörsen eintragen oder Satz entfernen</span></p>
      <p>Gutachten und zugehörige Unterlagen bewahren wir nach den handels- und steuerrechtlichen Vorgaben auf (in der Regel 10 Jahre, § 147 AO, § 257 HGB).</p>

      <h2>7. Cookies und lokaler Speicher</h2>
      <p>Diese Website setzt keine Cookies. Sie nutzt weder Statistik- noch Werbe-Werkzeuge und lädt keine Inhalte, Karten, Videos oder Schriften von fremden Servern.</p>
      <p>Die Unfall-Checkliste merkt sich abgehakte Punkte im lokalen Speicher Ihres Browsers (Local Storage). Diese Information verlässt Ihr Gerät nicht, wird nicht an uns übermittelt und kann jederzeit über „Liste zurücksetzen“ oder die Browser-Einstellungen gelöscht werden. Es handelt sich um eine rein funktionale Speicherung, die für den von Ihnen gewünschten Dienst erforderlich ist (§ 25 Abs. 2 Nr. 2 TDDDG). Eine Einwilligungsabfrage und ein Cookie-Banner sind deshalb nicht erforderlich.</p>

      <h2>8. Ihre Rechte</h2>
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

      <h2>9. Datensicherheit</h2>
      <p>Die Website wird über HTTPS verschlüsselt ausgeliefert. Die Konfiguration des Formulars liegt nicht im öffentlich erreichbaren Bereich des Servers. Wir treffen angemessene technische und organisatorische Maßnahmen, um Ihre Daten gegen Verlust, Manipulation und unbefugten Zugriff zu schützen.</p>

      <h2>10. Änderungen</h2>
      <p>Wir passen diese Datenschutzerklärung an, wenn sich die Website oder die rechtlichen Anforderungen ändern. Es gilt die jeweils hier veröffentlichte Fassung.</p>
'''
    return legal_page("privacy", "Datenschutzerklärung | PS Schneider Kfz-Gutachter Celle", f"Stand: {stand()}", "Datenschutzerklärung", inner)


def build_404():
    """Eine Datei für beide Sprachen: der Server kann nur eine 404-Seite ausliefern."""
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
    <div class="notfound-en" lang="en">
      <h2>This page does not exist.</h2>
      <p class="lede">The address may have changed. Here are the main pages.</p>
      <div class="hero-actions">
        <a class="btn btn-secondary" href="{u("en", d)}" hreflang="en">Home page (English)</a>
        <a class="btn btn-secondary" href="{u("en/services", d)}" hreflang="en">Services</a>
      </div>
    </div>
  </section>
'''
    return dict(slug="404", d=d, key=None, title="Seite nicht gefunden | PS Schneider", desc="Diese Seite wurde nicht gefunden.",
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
        "# --- PHP: nur der Formular-Endpunkt ist von außen erreichbar, versteckte Dateien sind gesperrt ---",
        '<FilesMatch "\\.php$">',
        "  Require all denied",
        "</FilesMatch>",
        '<Files "anfrage.php">',
        "  Require all granted",
        "</Files>",
        '<FilesMatch "^\\.(ht|user\\.ini)">',
        "  Require all denied",
        "</FilesMatch>",
        "# Upload-Grenzen für Fotos (bei mod_php; bei php-fpm gilt die Datei .user.ini)",
        "<IfModule mod_php.c>",
        "  php_value upload_max_filesize 20M",
        "  php_value post_max_size 60M",
        "  php_value max_file_uploads 10",
        "</IfModule>",
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
        '  Header always set Content-Security-Policy "default-src \'self\'; img-src \'self\' data: blob:; script-src \'self\'; style-src \'self\'; font-src \'self\'; base-uri \'self\'; form-action \'none\'; frame-ancestors \'self\'"',
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

# IP-Adressen im Zugriffsprotokoll kürzen (Datenschutz): letzte Stelle bei IPv4, hinterer Teil bei IPv6
map $remote_addr $ip_gekuerzt {{
    ~(?P<ip>\\d+\\.\\d+\\.\\d+)\\.\\d+$  $ip.0;
    ~(?P<ip>[^:]+:[^:]+):         $ip::;
    default                       0.0.0.0;
}}
log_format gekuerzt '$ip_gekuerzt [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';

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

    root /var/www/psschneider.de/public;
    index index.html;
    access_log /var/log/nginx/psschneider.access.log gekuerzt;
    error_page 404 /404.html;

    # Alte Adressen der bisherigen Website: dauerhaft (301) auf die neuen Seiten
{red}

    # Fotos: bis zu 5 Dateien, großzügige Obergrenze
    client_max_body_size 60m;

    # PHP nur für den Formular-Endpunkt. Passen Sie Socket und Pfad zu private/ an.
    location = /api/anfrage.php {{
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PSS_PRIVATE_DIR /var/www/psschneider.de/private;
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
        fastcgi_read_timeout 90s;
    }}
    location ~ \\.php$ {{ return 404; }}
    location ~ /\\.(?!well-known) {{ deny all; }}

    location / {{
        try_files $uri $uri/ =404;
    }}

    location = /404.html {{ internal; }}

    # Sicherheit
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data: blob:; script-src 'self'; style-src 'self'; font-src 'self'; base-uri 'self'; form-action 'none'; frame-ancestors 'self'" always;
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


USER_INI = """; Von build/build.py erzeugt. Gilt für php-fpm und CGI. Upload-Grenzen für die Schadenfotos.
upload_max_filesize = 20M
post_max_size = 60M
max_file_uploads = 10
memory_limit = 256M
max_execution_time = 90
"""


def robots():
    if DRAFT:
        return "# Entwurf von Markentrix: nicht für Suchmaschinen.\nUser-agent: *\nDisallow: /\n"
    return f"""# robots.txt für {DOMAIN}
User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""


def sitemap(entries):
    """entries: Liste (key, slug). Jede Seite nennt ihre Übersetzung (hreflang), auch auf sich selbst."""
    items = []
    for key, slug in entries:
        alts = ""
        if key in ALT:
            alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{abs_url(ALT[key][l])}"/>' for l in LANGS)
            alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{abs_url(ALT[key]["de"])}"/>'
        items.append(f"  <url>\n    <loc>{abs_url(slug)}</loc>\n    <lastmod>{TODAY.isoformat()}</lastmod>{alts}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(items) + "\n</urlset>\n")


# ---------------------------------------------------------------- Ausgabe

def write(out_dir, rel, text):
    p = out_dir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def build_pages():
    """Alle Seiten der aktuellen Sprache."""
    pages = [build_home(), build_leistungen()]
    pages += [build_service(s) for s in SERVICES]
    pages += [build_ratgeber_index()] + [build_article(a) for a in ARTICLES]
    pages += [build_area_hub()] + [build_town(t) for t in PAGE_TOWNS]
    pages += [build_gruende(), build_checkliste(), build_kontakt(), build_impressum(), build_datenschutz()]
    return pages


def main():
    global PREVIEW, DRAFT
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", metavar="DIR", help="Vorschau mit relativen Links in DIR erzeugen")
    ap.add_argument("--final", action="store_true", help="Endversion ohne Entwurfsmodus (Urheberrechtsvermerk, Wasserzeichen, Sperren)")
    args = ap.parse_args()
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
        # Englische Seiten neu erzeugen, damit keine veralteten Dateien übrig bleiben
        if (out / "en").exists():
            shutil.rmtree(out / "en")

    # Alle Adressen vorab kennen (Sprachumschalter, hreflang): ALT wird beim Import gebaut
    entries, count = [], 0
    for lang in LANGS:
        set_lang(lang)
        pages = build_pages()
        if lang == "de":
            pages.append(build_404())
        for p in pages:
            slug = p["slug"]
            html_text = page_html(slug=slug, d=p["d"], title=p["title"], desc=p["desc"], body=p["body"], key=p.get("key"),
                                  graph=p.get("graph"), noindex=p.get("noindex", False))
            rel = "404.html" if slug == "404" else ("index.html" if slug == "" else f"{slug}/index.html")
            write(out, rel, html_text)
            count += 1
            if not p.get("noindex"):
                entries.append((p["key"], slug))
    set_lang("de")

    if not PREVIEW and DRAFT:
        for stale in ("sitemap.xml",):
            if (out / stale).exists():
                (out / stale).unlink()
    if not PREVIEW and not DRAFT:
        write(out, "sitemap.xml", sitemap(entries))
    if not PREVIEW:
        write(out, ".user.ini", USER_INI)
        write(out, "robots.txt", robots())
        write(out, ".htaccess", htaccess())
        write(ROOT / "server", "nginx.conf.example", nginx_conf())
    print(f"{count} Seiten nach {out} geschrieben.")


if __name__ == "__main__":
    main()
