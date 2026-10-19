# -*- coding: utf-8 -*-
"""Gemeinsame Bausteine: Inhalte laden, Icons, Layout (Head, Header, Footer), Komponenten."""
import datetime
import glob
import html
import json
import os
import re
import urllib.parse

import md

ESC = lambda s: html.escape(str(s), quote=True)


def inl(s, prefix=""):
    """Inline-Markdown (fett/kursiv/Links) für kurze Felder wie H1 und Lead."""
    return md.inline(s or "", prefix)


# --------------------------------------------------------------------------- Icons
I = {
 "wa": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15L2 22l5.2-1.4A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3.1.8.8-3-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1s-.7.8-.9 1c-.2.2-.3.2-.6.1a6.7 6.7 0 0 1-2-1.2 7.4 7.4 0 0 1-1.4-1.7c-.1-.2 0-.4.1-.5l.4-.5c.1-.1.2-.3.2-.5s0-.3-.1-.5l-.7-1.7c-.2-.4-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2c0 1.3.9 2.6 1.1 2.8.1.2 2 3 4.8 4.2.7.3 1.2.5 1.6.6a3.8 3.8 0 0 0 1.8.1c.5-.1 1.5-.6 1.8-1.2.2-.6.2-1.1.2-1.2s-.2-.2-.4-.3Z"/></svg>',
 "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.1-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.7a2 2 0 0 1-.4 2.1L8.1 9.7a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.4c.9.3 1.8.5 2.7.6a2 2 0 0 1 1.7 2Z"/></svg>',
 "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 5h18v14H3zM3 5l9 7 9-7"/></svg>',
 "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>',
 "cal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M3 10h18M8 2v4M16 2v4"/></svg>',
 "zoom": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4M11 8v6M8 11h6"/></svg>',
 "check": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 10l4 4 8-8"/></svg>',
 "x": '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l8 8M14 6l-8 8"/></svg>',
 "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
 "star": '<svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 1.6l2.5 5.1 5.6.8-4 3.9.9 5.6L10 14.5l-5 2.5.9-5.6-4-3.9 5.6-.8L10 1.6z"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
 "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="M9 12l2 2 4-4"/></svg>',
 "hand": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 11V6a2 2 0 0 0-4 0v5M14 10V4a2 2 0 0 0-4 0v6M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 0 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.9-5.9-2.4L3.6 16a2 2 0 0 1 2.8-2.8L8 14.5"/></svg>',
 "spark": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="M19 17l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2Z"/></svg>',
 "euro": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6.5A7 7 0 0 0 7.3 9M18 17.5A7 7 0 0 1 7.3 15M4 10.5h10M4 13.5h10"/></svg>',
 "key": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="8" cy="15" r="4"/><path d="M10.8 12.2 20 3M15 8l3 3M18 5l3 3"/></svg>',
 "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8Z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
 "car": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 16v2H3v-6l2-6h14l2 6v6h-2v-2"/><path d="M5 12h14"/><circle cx="7.5" cy="15.5" r="1.5"/><circle cx="16.5" cy="15.5" r="1.5"/></svg>',
 "paw": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="10" r="2"/><circle cx="18" cy="10" r="2"/><circle cx="9.5" cy="5.5" r="2"/><circle cx="14.5" cy="5.5" r="2"/><path d="M12 11c-3 0-6 3-6 6 0 2 1.5 3 3 3 1 0 2-.5 3-.5s2 .5 3 .5c1.5 0 3-1 3-3 0-3-3-6-6-6Z"/></svg>',
 "brief": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18"/></svg>',
 "gift": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13M5 12v9h14v-9M7.5 8a2.5 2.5 0 0 1 0-5C10 3 12 8 12 8s2-5 4.5-5a2.5 2.5 0 0 1 0 5"/></svg>',
 "book": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14Z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/></svg>',
 "snow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 2v20M4.9 4.9l14.2 14.2M2 12h20M4.9 19.1 19.1 4.9M9 3l3 3 3-3M9 21l3-3 3 3M3 9l3 3-3 3M21 9l-3 3 3 3"/></svg>',
 "menu": '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
 "insta": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>',
 "fb": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-7.5H16l.4-3H13.5V8.4c0-.9.2-1.5 1.5-1.5h1.6V4.3C16.3 4.2 15.3 4 14.2 4c-2.3 0-3.9 1.4-3.9 4v2.5H7.8v3h2.5V21h3.2Z"/></svg>',
 "tiktok": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 3c.5 2.4 2 4 4.5 4.3V10c-1.7 0-3.2-.5-4.5-1.4V15a5.5 5.5 0 1 1-5.5-5.5c.3 0 .7 0 1 .1v2.6a2.9 2.9 0 1 0 2 2.8V3h2.5Z"/></svg>',
 "gstar": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.4l-5.8 3.1 1.1-6.5L2.6 9.4l6.5-.9L12 2.6z"/></svg>',
}
STARS5 = '<div class="stars" aria-hidden="true">' + I["star"] * 5 + "</div>"


# --------------------------------------------------------------------------- Inhalte
class Site:
    def __init__(self, content_dir):
        self.dir = content_dir
        j = lambda n: json.load(open(os.path.join(content_dir, n), encoding="utf-8"))
        self.s = j("site.json")
        self.pricing = j("pricing.json")
        self.reviews = j("reviews.json")
        self.faq = j("faq.json")["items"]
        self.gallery = j("gallery.json")["items"]
        try:
            self.certs = j("zertifikate.json").get("items", [])
        except FileNotFoundError:
            self.certs = []
        try:
            offers = j("angebote.json").get("items", [])
        except FileNotFoundError:
            offers = []
        today = datetime.date.today().isoformat()
        self.offers = [o for o in offers if o.get("active", True) and (not o.get("validUntil") or o["validUntil"] >= today)
                       and (not o.get("validFrom") or o["validFrom"] <= today)]
        self.services = sorted((json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(content_dir, "services", "*.json"))),
                               key=lambda x: x.get("order", 99))
        self.articles = []
        for f in glob.glob(os.path.join(content_dir, "ratgeber", "*.md")):
            meta, body = md.parse_frontmatter(open(f, encoding="utf-8").read())
            if meta.get("draft"):
                continue
            meta["slug"] = os.path.splitext(os.path.basename(f))[0]
            meta["body"] = body
            self.articles.append(meta)
        self.articles.sort(key=lambda a: (a.get("date", ""), a.get("title", "")), reverse=True)
        # Preis-Platzhalter wie {ab:komplett} in Texten durch den aktuellen Richtpreis ersetzen
        self.services = [self.fill(sv) for sv in self.services]
        self.faq = self.fill(self.faq)
        self.offers = self.fill(self.offers)
        self.articles = [self.fill(a) for a in self.articles]
        self.url = self.s["url"].rstrip("/")
        self.asset_v = {}
        self.media = {}   # Galerie-Bilder: name -> {"srcset":..., "src":..., "w":..., "h":...}

    # Hilfen
    def pkg(self, key):
        return next(p for p in self.pricing["packages"] if p["key"] == key)

    def service(self, slug):
        return next((s for s in self.services if s["slug"] == slug), None)

    def wa(self, text=None):
        base = "https://wa.me/" + self.s["whatsapp"]
        return base + ("?text=" + urllib.parse.quote(text) if text else "")

    def min_price(self, key):
        return min(self.pkg(key)["prices"].values())

    def fill(self, obj):
        keys = {p["key"] for p in self.pricing["packages"]}
        rep = lambda m: str(self.min_price(m.group(1))) if m.group(1) in keys else m.group(0)
        def rep_cls(m):  # {preis:komplett:suv} → Richtpreis dieses Pakets für diese Fahrzeugklasse
            if m.group(1) not in keys:
                return m.group(0)
            v = self.pkg(m.group(1))["prices"].get(m.group(2))
            return str(v) if v is not None else m.group(0)
        if isinstance(obj, str):
            return re.sub(r"\{preis:(\w+):(\w+)\}", rep_cls, re.sub(r"\{ab:(\w+)\}", rep, obj))
        if isinstance(obj, list):
            return [self.fill(x) for x in obj]
        if isinstance(obj, dict):
            return {k: self.fill(v) for k, v in obj.items()}
        return obj

    def addr_line(self):
        a = self.s["address"]
        return f'{a["street"]}, {a["zip"]} {a["city"]}'

    def maps_url(self):
        return "https://www.google.com/maps/place/?q=" + urllib.parse.quote_plus(self.addr_line())

    def asset(self, prefix, name):
        v = self.asset_v.get(name)
        return f"{prefix}{name}" + (f"?v={v}" if v else "")


# --------------------------------------------------------------------------- Layout
def logo(site, prefix, lazy=False):
    lz = ' loading="lazy"' if lazy else ""
    return f'<img src="{prefix}logo.svg" alt="ElbDetail – Premium Fahrzeugaufbereitung" width="173" height="60"{lz}>'


def head(site, title, desc, path, prefix="", ld=None, noindex=False, og_type="website", extra=""):
    lds = "".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False, separators=(",", ":")) + "</script>\n" for o in (ld or []))
    robots = "noindex, follow" if noindex else "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"
    url = site.url + path
    ver = site.s.get("verification") or {}
    verify = "".join(f'<meta name="{n}" content="{ESC(ver[k])}">\n' for k, n in (("google", "google-site-verification"), ("bing", "msvalidate.01")) if ver.get(k))
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<title>{ESC(title)}</title>
<meta name="description" content="{ESC(desc)}">
<link rel="canonical" href="{ESC(url)}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#1e2229">
<meta name="geo.region" content="DE-NI">
<meta name="geo.placename" content="{ESC(site.s["address"]["city"])}">
{verify}<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<link rel="manifest" href="{prefix}site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="ElbDetail Ratgeber" href="{prefix}ratgeber/feed.xml">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{ESC(site.s["name"])}">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{ESC(title)}">
<meta property="og:description" content="{ESC(desc)}">
<meta property="og:url" content="{ESC(url)}">
<meta property="og:image" content="{site.url}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="ElbDetail – Premium Fahrzeugaufbereitung in Celle">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ESC(title)}">
<meta name="twitter:description" content="{ESC(desc)}">
<meta name="twitter:image" content="{site.url}/og-image.png">
<link rel="preload" href="{prefix}fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{prefix}fonts/instrument-serif-italic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{site.asset(prefix, "styles.css")}">
{extra}{lds}</head>
<body>
'''


def nav_href(prefix, home, target):
    """target: '#anker' (Startseite) oder 'pfad.html'."""
    if target.startswith("#"):
        return target if home else f"{prefix}index.html{target}"
    return prefix + target


NAV = [("Leistungen", "#leistungen"), ("Preise", "preise.html"), ("Angebote", "angebote.html"), ("Über uns", "ueber-uns.html"), ("Ratgeber", "ratgeber/index.html"),
       ("Gutscheine", "gutscheine.html"), ("Firmenkunden", "firmenkunden.html"), ("Kontakt", "kontakt.html")]


def header(site, prefix="", home=False, current=None):
    cur = ' aria-current="page"'
    items = "".join(
        f'<li><a href="{nav_href(prefix, home, t)}"{cur if current == t else ""}>{l}</a></li>' for l, t in NAV)
    svc = "".join(f'<li><a class="nav-sub" href="{prefix}leistungen/{s["slug"]}.html">{ESC(s["short"])}</a></li>' for s in site.services)
    brand_href = "#main" if home else f"{prefix}index.html"
    return f'''<a class="skip-link" href="#main">Zum Inhalt springen</a>

<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{brand_href}" aria-label="ElbDetail – zur Startseite">
      {logo(site, prefix)}
    </a>
    <nav class="main-nav" aria-label="Hauptnavigation"><ul>{items}</ul></nav>
    <div class="header-cta">
      <div class="header-social" aria-label="ElbDetail in sozialen Netzwerken">
        <a href="{site.s["social"]["instagram"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf Instagram">{I["insta"]}</a>
        <a href="{site.s["social"]["facebook"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf Facebook">{I["fb"]}</a>
        <a href="{site.s["social"]["tiktok"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf TikTok">{I["tiktok"]}</a>
      </div>
      <a class="btn btn-icon btn-wa-ghost" href="{site.wa()}" target="_blank" rel="noopener" aria-label="WhatsApp schreiben">{I["wa"]}</a>
      <a class="btn btn-primary btn-sm header-book" href="{prefix}termin.html">{I["cal"]}<span class="btn-label">Termin anfragen</span></a>
      <button class="menu-toggle" id="menuToggle" type="button" aria-expanded="false" aria-controls="mobileNav" aria-label="Menü öffnen">{I["menu"]}</button>
    </div>
  </div>
  <nav class="mobile-nav" id="mobileNav" hidden aria-label="Mobile Navigation">
    <ul>
      <li><a href="{nav_href(prefix, home, '#leistungen')}">Leistungen</a></li>
      {svc}
      <li><a href="{prefix}preise.html">Pakete &amp; Preise</a></li>
      <li><a href="{prefix}angebote.html">Aktuelle Angebote</a></li>
      <li><a href="{prefix}termin.html">Termin online anfragen</a></li>
      <li><a href="{prefix}gutscheine.html">Gutscheine</a></li>
      <li><a href="{prefix}firmenkunden.html">Firmenkunden &amp; Flotten</a></li>
      <li><a href="{prefix}elbdetail-care.html">ElbDetail Care</a></li>
      <li><a href="{prefix}ueber-uns.html">Über uns</a></li>
      <li><a href="{prefix}zertifikate.html">Zertifikate</a></li>
      <li><a href="{prefix}ratgeber/index.html">Ratgeber</a></li>
      <li><a href="{nav_href(prefix, home, '#bewertungen')}">Bewertungen</a></li>
      <li><a href="{prefix}kontakt.html">Kontakt</a></li>
    </ul>
    <div class="mobile-social">
      <a class="social-btn" href="{site.s["social"]["instagram"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf Instagram">{I["insta"]}</a>
      <a class="social-btn" href="{site.s["social"]["facebook"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf Facebook">{I["fb"]}</a>
      <a class="social-btn" href="{site.s["social"]["tiktok"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf TikTok">{I["tiktok"]}</a>
      <span>@elbdetail</span>
    </div>
  </nav>
</header>
'''


def footer(site, prefix="", home=False):
    s = site.s
    services = "".join(f'<li><a href="{prefix}leistungen/{x["slug"]}.html">{ESC(x["short"])} Celle</a></li>' for x in site.services)
    brand_href = "#main" if home else f"{prefix}index.html"
    return f'''<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <a class="footer-brand" href="{brand_href}">{logo(site, prefix, True)}</a>
      <p class="footer-about">Premium Fahrzeugaufbereitung in Celle: Lackaufbereitung, Keramikversiegelung, Innen- &amp; Außenaufbereitung in Handarbeit. Offizieller C²Coating Excellence Partner.</p>
      <p class="footer-areas">Für Kund:innen aus {ESC(", ".join(s["areas"]["city"]))} sowie {ESC(", ".join(s["areas"]["region"]))} und dem ganzen Landkreis Celle.</p>
      <div class="social-row">
        <a class="social-btn" href="{s["social"]["instagram"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf Instagram">{I["insta"]}</a>
        <a class="social-btn" href="{s["social"]["facebook"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf Facebook">{I["fb"]}</a>
        <a class="social-btn" href="{s["social"]["tiktok"]}" target="_blank" rel="noopener" aria-label="ElbDetail auf TikTok">{I["tiktok"]}</a>
        <a class="social-btn" href="{s["googleMapsUrl"]}" target="_blank" rel="noopener" aria-label="ElbDetail bei Google">{I["gstar"]}</a>
      </div>
    </div>
    <div>
      <h2 class="footer-h">Leistungen</h2>
      <ul>{services}</ul>
    </div>
    <div>
      <h2 class="footer-h">Service</h2>
      <ul>
        <li><a href="{prefix}termin.html">Termin online anfragen</a></li>
        <li><a href="{prefix}preise.html">Pakete &amp; Preise</a></li>
        <li><a href="{prefix}angebote.html">Aktuelle Angebote</a></li>
        <li><a href="{prefix}gutscheine.html">Gutscheine</a></li>
        <li><a href="{prefix}firmenkunden.html">Firmenkunden &amp; Flotten</a></li>
        <li><a href="{prefix}elbdetail-care.html">ElbDetail Care</a></li>
        <li><a href="{prefix}aktion/winterschutz.html">Winter-Lackschutz</a></li>
        <li><a href="{prefix}ueber-uns.html">Über uns</a></li>
        <li><a href="{prefix}zertifikate.html">Zertifikate &amp; Qualifikationen</a></li>
        <li><a href="{prefix}ratgeber/index.html">Ratgeber</a></li>
      </ul>
    </div>
    <div>
      <h2 class="footer-h">Kontakt</h2>
      <address>
        {ESC(s["name"])}<br>
        {ESC(s["address"]["street"])}<br>
        {ESC(s["address"]["zip"])} {ESC(s["address"]["city"])}<br>
        <a href="tel:{s["phone"]}">{ESC(s["phoneDisplay"])}</a><br>
        <a href="mailto:{s["email"]}">{ESC(s["email"])}</a><br>
        {ESC(s["openingHours"]["text"])}
      </address>
    </div>
  </div>
  <div class="container footer-bottom">
    <p>&copy; <span id="year">{s["standIso"][:4]}</span> {ESC(s["name"])} · Fahrzeugaufbereitung {ESC(s["address"]["city"])}</p>
    <ul>
      <li><a href="{prefix}impressum.html">Impressum</a></li>
      <li><a href="{prefix}datenschutz.html">Datenschutz</a></li>
      {'<li><button class="link-btn" type="button" data-consent-open>Cookie-Einstellungen</button></li>' if (s.get("analytics") or {}).get("ga4") else ""}
    </ul>
  </div>
</footer>

<div class="mobile-actionbar" aria-label="Schnellkontakt">
  <a href="tel:{s["phone"]}">{I["phone"]}<span>Anrufen</span></a>
  <a href="{site.wa()}" target="_blank" rel="noopener">{I["wa"]}<span>WhatsApp</span></a>
  <a href="{prefix}termin.html">{I["cal"]}<span>Termin</span></a>
</div>

<script src="{site.asset(prefix, "config.js")}"></script>
<script src="{site.asset(prefix, "script.js")}" defer></script>
</body>
</html>
'''


# --------------------------------------------------------------------------- Komponenten
def faq_html(items, prefix="", first_open=True):
    out = []
    for i, it in enumerate(items):
        out.append(f'''<details class="faq-item reveal"{" open" if (i == 0 and first_open) else ""}>
          <summary>{ESC(it["q"])}</summary>
          <div class="faq-body-wrap"><div class="faq-body-clip"><div class="faq-body">{md.inline(it["a"], prefix)}</div></div></div>
        </details>''')
    return "\n".join(out)


def consent_row(prefix, fid):
    return f'''<div class="consent-row">
            <input type="checkbox" id="{fid}" name="einwilligung" value="ja" required>
            <label for="{fid}">Ich habe die <a href="{prefix}datenschutz.html">Datenschutzerklärung</a> gelesen und bin einverstanden, dass meine Angaben zur Bearbeitung der Anfrage gespeichert und verwendet werden.*</label>
          </div>'''


def honeypot(fid):
    return f'<div class="hp" aria-hidden="true"><label for="{fid}">Website</label><input type="text" id="{fid}" name="website" tabindex="-1" autocomplete="off"></div>'


def form_status(fid):
    return f'<p class="form-status" id="{fid}" role="status" aria-live="polite"></p>'


def package_options(site, include_extra=True, selected=None):
    opts = ['<option value="" disabled selected>Bitte wählen</option>'] if not selected else []
    for p in site.pricing["packages"]:
        sel = " selected" if selected == p["key"] else ""
        opts.append(f'<option value="{ESC(p["name"])}"{sel}>{ESC(p["name"])} – ab {site.min_price(p["key"])} €</option>')
    if include_extra:
        for v in ["Keramikversiegelung", "Lederreparatur / Lederpflege", "ElbDetail Care (regelmäßige Pflege)", "Leasingrückgabe / Verkaufsvorbereitung", "Einzelleistung (z. B. nur Politur)", "Unsicher – bitte beraten"]:
            opts.append(f"<option>{v}</option>")
    return "".join(opts)


def contact_section(site, prefix=""):
    s = site.s
    return f'''  <section id="kontakt" aria-labelledby="kontakt-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Kontakt &amp; Termin</p>
        <h2 id="kontakt-h" class="display">Anfrage stellen. Antwort kommt schnell.</h2>
        <p>Nennen Sie uns kurz Fahrzeug, Wunschpaket und Zeitraum. Sie erhalten ein verbindliches Angebot, bevor irgendetwas passiert. Für einen konkreten Termin nutzen Sie am besten die <a class="text-link" href="{prefix}termin.html">Online-Terminanfrage</a>.</p>
      </div>

      <div class="contact-split reveal">
        <div class="contact-info">
          <div class="info-row">{I["wa"]}<div><a href="{site.wa()}" target="_blank" rel="noopener">WhatsApp: {ESC(s["phoneIntl"])}</a><p>Schnellster Weg für kurze Fragen</p></div></div>
          <div class="info-row">{I["phone"]}<div><a href="tel:{s["phone"]}">Telefon: {ESC(s["phoneDisplay"])}</a><p>Direkt anrufen</p></div></div>
          <div class="info-row">{I["mail"]}<div><a href="mailto:{s["email"]}">{ESC(s["email"])}</a><p>Für ausführliche Anfragen und Firmenkunden</p></div></div>
          <div class="info-row">{I["pin"]}<div><a href="{site.maps_url()}" target="_blank" rel="noopener">{ESC(site.addr_line())}</a><p>Route in Google Maps öffnen</p></div></div>
          <div class="info-row">{I["cal"]}<div><span>{ESC(s["openingHours"]["text"])}</span><p>{ESC(s["openingHours"]["detail"])}</p></div></div>
        </div>

        <form class="contact-form js-form" id="contactForm" data-form="kontakt" action="/api/anfrage" method="post" novalidate>
          <input type="hidden" name="typ" value="kontakt">
          <div class="two-col">
            <div class="form-row"><label for="k-name">Name*</label><input type="text" id="k-name" name="name" autocomplete="name" required maxlength="120"></div>
            <div class="form-row"><label for="k-phone">Telefon / WhatsApp <span class="hint">(für Rückruf)</span></label><input type="tel" id="k-phone" name="telefon" autocomplete="tel" maxlength="40"></div>
          </div>
          <div class="form-row"><label for="k-email">E-Mail <span class="hint">(Telefon oder E-Mail angeben)</span></label><input type="email" id="k-email" name="email" autocomplete="email" maxlength="160"></div>
          <div class="two-col">
            <div class="form-row"><label for="k-package">Gewünschtes Paket*</label><select id="k-package" name="paket" required>{package_options(site)}</select></div>
            <div class="form-row"><label for="k-vehicle">Fahrzeug <span class="hint">(Modell, Baujahr)</span></label><input type="text" id="k-vehicle" name="fahrzeug" maxlength="120" placeholder="z. B. VW Tiguan 2019"></div>
          </div>
          <div class="form-row"><label for="k-message">Nachricht <span class="hint">(optional)</span></label><textarea id="k-message" name="nachricht" rows="3" maxlength="2000" placeholder="Zustand, besondere Wünsche, Leasingrückgabe-Termin …"></textarea></div>
          {honeypot("k-website")}
          {consent_row(prefix, "k-consent")}
          <div class="form-actions">
            <button class="btn btn-primary" type="submit">{I["mail"]}Anfrage senden</button>
            <button class="btn btn-line-light" type="button" data-wa-from-form>{I["wa"]}Lieber per WhatsApp</button>
          </div>
          {form_status("k-status")}
          <p class="hint">*Pflichtfeld. Ihre Anfrage wird verschlüsselt an unseren eigenen Server in Deutschland übertragen und nur zur Bearbeitung verwendet.</p>
        </form>
      </div>

      <div class="map-wrap">
        <div class="map-placeholder" id="mapPlaceholder">
          {I["pin"]}
          <p><strong>{ESC(s["name"])}, {ESC(site.addr_line())}.</strong> Beim Laden der Karte wird eine Verbindung zu Google-Servern aufgebaut; dabei können Cookies gesetzt werden.</p>
          <button class="btn btn-primary btn-sm" id="loadMapBtn" type="button">Karte laden</button>
        </div>
      </div>
    </div>
  </section>
'''


def cta_band(site, prefix="", title="Bereit für ein Auto, das sich wieder neu anfühlt?",
             text="Schreiben Sie uns kurz, welches Fahrzeug es ist und was gemacht werden soll. Sie erhalten ein verbindliches Angebot, bevor irgendetwas passiert."):
    return f'''  <section class="tight" aria-label="Termin anfragen">
    <div class="container">
      <div class="cta-band reveal">
        <p class="eyebrow">Termine nach Vereinbarung</p>
        <h2 class="display">{ESC(title)}</h2>
        <p>{ESC(text)}</p>
        <div class="hero-actions">
          <a class="btn btn-primary btn-lg" href="{prefix}termin.html">{I["cal"]}Termin online anfragen</a>
          <a class="btn btn-wa btn-lg" href="{site.wa("Hallo ElbDetail, ich möchte einen Termin zur Fahrzeugaufbereitung anfragen. Fahrzeug: … Wunsch: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
          <a class="btn btn-line" href="tel:{site.s["phone"]}">{I["phone"]}{ESC(site.s["phoneDisplay"])}</a>
        </div>
      </div>
    </div>
  </section>
'''


def breadcrumb(prefix, items):
    """items: [(label, href_or_None)]"""
    lis = []
    for label, href in items:
        if href:
            lis.append(f'<li><a href="{href}">{ESC(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{ESC(label)}</li>')
    return f'<nav class="breadcrumb" aria-label="Brotkrumen"><ol>{"".join(lis)}</ol></nav>'


def review_cards(site):
    return "".join(f'''
        <figure class="review-card reveal">
          {STARS5}
          <blockquote>{ESC(r["text"])}</blockquote>
          <figcaption>{ESC(r["name"])} <span>· {ESC(r.get("source", "Google"))}-Rezension</span></figcaption>
        </figure>''' for r in site.reviews["items"])
