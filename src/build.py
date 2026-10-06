# -*- coding: utf-8 -*-
"""Statischer Shop-Generator: python3 src/build.py  -> site/"""
import json, os, html, datetime
from data import *

OUT = os.path.join(os.path.dirname(__file__), "..", "site")
U = SITE["url"]
TODAY = datetime.date.today().isoformat()
esc = html.escape
PAGES = []  # (url, priority) für sitemap
SEARCH = []

def eur(n):
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")+ " €"

# ---------- Icons (Lucide-ähnlich, 24x24, stroke) ----------
ICONS = {
 "hitch": '<circle cx="12" cy="14" r="4"/><path d="M12 10V3M8 3h8M4 21h16"/>',
 "rack": '<rect x="3" y="12" width="18" height="4" rx="1"/><path d="M6 12V7h12v5M6 20v-4M18 20v-4"/>',
 "spring": '<path d="M8 3h8M8 7h8M5 11c0-2 14-2 14 0s-14 2-14 4 14 2 14 4"/><path d="M12 21v0"/>',
 "jack": '<path d="M12 3v14M7 12l5 5 5-5M5 21h14"/>',
 "bike": '<circle cx="6" cy="16" r="3.5"/><circle cx="18" cy="16" r="3.5"/><path d="M6 16l4-8h5l3 8M10 8H7M13 12h5"/>',
 "wheel": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/>',
 "snow": '<path d="M12 2v20M4.9 7l14.2 10M19.1 7L4.9 17M9 3.5l3 2 3-2M9 20.5l3-2 3 2"/>',
 "remote": '<rect x="7" y="2" width="10" height="20" rx="3"/><circle cx="12" cy="8" r="2"/><path d="M10 14h4M10 17h4"/>',
 "step": '<path d="M3 20h6v-5h6v-5h6"/><path d="M3 20v1M21 10v11"/>',
 "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
 "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 6L2 7"/>',
 "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
 "check": '<path d="M20 6L9 17l-5-5"/>',
 "truck": '<path d="M1 3h15v13H1zM16 8h4l3 3v5h-7"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
 "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.3L5.8 21 7 14.2 2 9.3l6.9-1z"/>',
 "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
 "cart": '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6"/>',
 "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
 "pin": '<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
 "wrench": '<path d="M14.7 6.3a4 4 0 0 0 5 5L22 13.6 13.6 22l-2.3-2.3a4 4 0 0 0-5-5L3 12.4 11.4 4z"/>',
 "arrow": '<path d="M5 12h14M13 5l7 7-7 7"/>',
 "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
 "card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
 "headset": '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/><rect x="2" y="14" width="5" height="6" rx="2"/><rect x="17" y="14" width="5" height="6" rx="2"/>',
 "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5V22h16"/>',
}
def ic(n, cls=""):
    return f'<svg class="ico {cls}" aria-hidden="true"><use href="#i-{n}"/></svg>'
SPRITE = '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">' + "".join(
    f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + "</svg>"

LOGO = '<svg viewBox="0 0 48 48" aria-hidden="true"><rect width="48" height="48" rx="12" fill="#0B5D4B"/><path d="M8 29h3l2-7h17l5 7h5v5H8z" fill="#fff"/><circle cx="16" cy="35" r="4" fill="#F97316" stroke="#0B5D4B" stroke-width="2"/><circle cx="34" cy="35" r="4" fill="#F97316" stroke="#0B5D4B" stroke-width="2"/><path d="M16 22l2-6h10l2 6" fill="none" stroke="#7EE7B7" stroke-width="2"/></svg>'

CAT = {c["slug"]: c for c in CATEGORIES}
for p in PRODUCTS:
    p["url"] = f"produkt-{p['slug']}.html"
    p["tone"] = CAT[p["cat"]]["tone"]; p["icon"] = CAT[p["cat"]]["icon"]
PBYC = {c["slug"]: [p for p in PRODUCTS if p["cat"] == c["slug"]] for c in CATEGORIES}

def jld(*objs):
    return "".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in objs)

ORG = {"@context": "https://schema.org", "@type": "AutomotiveBusiness", "@id": U + "/#org", "name": SITE["name"], "url": U + "/",
       "telephone": SITE["phone"], "email": SITE["email"], "foundingDate": str(SITE["since"]),
       "description": "Fachhändler und Montagebetrieb für Wohnmobil-Nachrüstung: Anhängerkupplungen, Luftfederung, Stützensysteme, Heckträger.",
       "priceRange": "€€", "areaServed": {"@type": "Country", "name": "Deutschland"},
       "paymentAccepted": "PayPal, Kreditkarte, Überweisung, Rechnung", "currenciesAccepted": "EUR",
       "department": [{"@type": "AutoRepair", "name": f"{SITE['name']} {l['city']}",
                       "address": {"@type": "PostalAddress", "postalCode": l["plz"], "addressLocality": l["city"], "addressRegion": l["state"], "addressCountry": "DE"},
                       "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lon"]}, "telephone": SITE["phone"]} for l in LOCATIONS]}
WEBSITE = {"@context": "https://schema.org", "@type": "WebSite", "@id": U + "/#web", "url": U + "/", "name": SITE["name"], "inLanguage": "de-DE",
           "publisher": {"@id": U + "/#org"},
           "potentialAction": {"@type": "SearchAction", "target": U + "/suche.html?q={q}", "query-input": "required name=q"}}

def crumbs(items):
    lis = "".join(f'<li>{"<a href=%s>%s</a>" % (chr(34)+u+chr(34), esc(t)) if u else "<span aria-current=page>%s</span>" % esc(t)}</li>' for t, u in items)
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, **({"item": f"{U}/{u}"} if u else {})} for i, (t, u) in enumerate(items)]}
    return f'<nav class="crumbs wrap" aria-label="Brotkrumen"><ol>{lis}</ol></nav>', schema

def faq_html(faq, schema=True):
    h = "".join(f"<details><summary>{esc(q)}</summary><div><p>{esc(a)}</p></div></details>" for q, a in faq)
    s = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    return h, s

def card(p, i=0):
    price = p["price"]
    if price:
        pr = f'<div class="price">{"<span class=from>ab</span>" if p["from_"] else ""}{eur(price)}' + (f' <del>{eur(p["old"])}</del>' if p["old"] else "") + '<br><small>inkl. MwSt., versandkostenfrei</small></div>'
        btn = f'<button class="btn btn-cta btn-block" data-add="{p["slug"]}">{ic("cart")} In den Warenkorb</button>'
    else:
        pr = '<div class="price ask">Preis auf Anfrage</div>'
        btn = f'<a class="btn btn-out btn-block" href="kontakt.html?produkt={esc(p["name"])}">Angebot anfordern</a>'
    tag = f'<span class="tag{" sale" if p["old"] else ""}">{esc(p["badge"])}</span>'
    return (f'<article class="card" data-price="{price or ""}" data-i="{i}"><div class="art tone-{p["tone"]}">{tag}{ic(p["icon"])}</div>'
            f'<div class="body"><h3><a href="{p["url"]}">{esc(p["name"])}</a></h3><p class="sub">{esc(p["short"])}</p>{pr}<div class="foot">{btn}</div></div></article>')

NAV = [({"Anhängerkupplung":"Anhängerkupplung","Heckträger":"Heckträger","Luftfederung":"Luftfederung","Stützensysteme":"Stützen","Motorradanhänger":"Motorradanhänger","Räder":"Räder","Klimaanlagen":"Klima","Rangierhilfe":"Rangierhilfe","Trittstufen":"Trittstufen"}[c["name"].split(" &")[0]], f'{c["slug"]}.html') for c in CATEGORIES]
FOOT_CATS = [(c["name"], f'{c["slug"]}.html') for c in CATEGORIES]

def page(fname, title, desc, body, schemas=(), crumb_items=None, og_type="website", noindex=False, prio="0.7", nav_cur=None, extra_head="", mbar=""):
    canon = f"{U}/{'' if fname == 'index.html' else fname}"
    bc = ""
    sch = list(schemas)
    if crumb_items:
        bc, s = crumbs(crumb_items); sch.append(s)
    if fname == "index.html":
        sch += [ORG, WEBSITE]
    navs = "".join(f'<li><a href="{u}"{" aria-current=page" if u == nav_cur else ""}>{esc(t)}</a></li>' for t, u in NAV)
    html_ = f'''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">{'<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'}
<meta property="og:type" content="{og_type}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canon}"><meta property="og:locale" content="de_DE"><meta property="og:site_name" content="{SITE['name']}">
<meta name="theme-color" content="#0B5D4B"><meta name="geo.region" content="DE"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700&family=Rubik:wght@500;600;700&display=swap">
<link rel="stylesheet" href="assets/css/style.css">{extra_head}{jld(*sch)}</head>
<body>{SPRITE}<a class="skip" href="#main">Zum Inhalt springen</a>
<div class="topbar"><div class="wrap"><ul><li>{ic("truck")} Versandkostenfrei in Deutschland</li><li>{ic("shield")} EG-Typgenehmigung · keine TÜV-Abnahme*</li><li>{ic("star")} {SITE['rating']} / 5 bei Google</li></ul>
<span>{ic("phone")} <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a></span></div></div>
<header class="header"><div class="wrap"><a class="logo" href="index.html" aria-label="Italia Camper 24 – Startseite">{LOGO}<span>Italia Camper <b>24</b></span></a>
<form class="search" role="search" action="suche.html">{ic("search")}<label class="sr" for="q">Shop durchsuchen</label><input id="q" name="q" type="search" placeholder="Suchen: Anhängerkupplung, Luftfederung …" autocomplete="off"><ul class="suggest" id="suggest"></ul></form>
<div class="hdr-actions"><a class="icon-btn hdr-phone" href="tel:{SITE['phone_href']}" aria-label="Anrufen">{ic("phone")}<span>Beratung</span></a>
<a class="icon-btn" href="warenkorb.html" aria-label="Warenkorb">{ic("cart")}<span class="badge" data-cart-badge data-n="0"></span></a>
<button class="icon-btn menu-btn" id="menuBtn" aria-expanded="false" aria-controls="nav" aria-label="Menü">{ic("menu")}</button></div></div>
<nav class="nav" id="nav" aria-label="Hauptnavigation"><div class="wrap"><ul>{navs}<li><a href="ratgeber.html">Ratgeber</a></li><li><a href="montage-service.html">Montage-Service</a></li></ul></div></nav></header>
{bc}<main id="main">{body}</main>
{footer()}<div class="toast" id="toast" role="status" aria-live="polite"></div>{mbar}
<script>window.IC={json.dumps(JS_DATA, ensure_ascii=False)};</script><script src="assets/js/app.js" defer></script></body></html>'''
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(html_)
    if not noindex:
        PAGES.append((fname, prio))

def footer():
    col = lambda items: "".join(f'<li><a href="{u}">{esc(t)}</a></li>' for t, u in items)
    return f'''<footer class="footer"><div class="wrap"><div class="cols">
<div><a class="logo" href="index.html" style="color:#fff">{LOGO}<span>Italia Camper <b style="color:#FDBA74">24</b></span></a>
<p style="margin-top:14px">Ihr Spezialist für Wohnmobil-Nachrüstung seit {SITE['since']}. Über 100 Produkte mit EG-Typgenehmigung – mit Montage an zwei Standorten.</p>
<p>{ic("phone")} <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a><br>{ic("mail")} <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
<div class="pay" aria-label="Zahlarten"><span>PayPal</span><span>Visa</span><span>Mastercard</span><span>Überweisung</span><span>Rechnung</span></div></div>
<div><h3>Sortiment</h3><ul>{col(FOOT_CATS[:5])}</ul></div>
<div><h3>Service</h3><ul>{col([("Montage-Service","montage-service.html"),("Fahrzeugfinder","index.html#fahrzeugfinder"),("Versand & Zahlung","versand-zahlung.html"),("FAQ","faq.html"),("Ratgeber","ratgeber.html"),("Kontakt","kontakt.html"),("Über uns","ueber-uns.html")])}</ul></div>
<div><h3>Standorte & Rechtliches</h3><ul>{col([("Montage Bohmte","standort-bohmte.html"),("Montage Diez","standort-diez.html"),("Impressum","impressum.html"),("AGB","agb.html"),("Widerrufsbelehrung","widerruf.html"),("Datenschutz","datenschutz.html")])}</ul></div>
</div><div class="bottom"><span>© {datetime.date.today().year} {SITE['name']} · Alle Preise inkl. gesetzl. MwSt., versandkostenfrei innerhalb Deutschlands.</span><span>* Bei Produkten mit EG-Typgenehmigung; Einzelheiten je Fahrzeug im Beratungsgespräch.</span></div></div></footer>'''

JS_DATA = {"mail": SITE["email"],
           "products": [{"id": p["slug"], "name": p["name"], "price": p["price"], "from": p["from_"], "u": p["url"], "tone": p["tone"], "icon": p["icon"]} for p in PRODUCTS],
           "pages": []}
def reg(title, url, kind, kw=""):
    JS_DATA["pages"].append({"t": title, "u": url, "c": kind, "k": kw})
for c in CATEGORIES: reg(c["name"], c["slug"] + ".html", "Kategorie", c["short"] + " " + c["h1"])
for p in PRODUCTS: reg(p["name"], p["url"], "Produkt", p["short"])
for b in BRANDS: reg(f'Zubehör für {b["name"]}', f'fahrzeug-{b["slug"]}.html', "Fahrzeug", "wohnmobil nachrüsten")
for g in GUIDES: reg(g["title"], f'ratgeber-{g["slug"]}.html', "Ratgeber", g["lead"])
for l in LOCATIONS: reg(f'Montage {l["city"]}', f'standort-{l["slug"]}.html', "Standort", l["region"] + " Einbau Werkstatt")
reg("Montage-Service", "montage-service.html", "Service", "einbau werkstatt termin")
reg("Versand & Zahlung", "versand-zahlung.html", "Service", "lieferung paypal rechnung")
reg("Kontakt", "kontakt.html", "Service", "beratung telefon")

def stars():
    return f'<span class="stars">{ic("star")}{ic("star")}{ic("star")}{ic("star")}{ic("star")} {SITE["rating"]} / 5 bei Google</span>'

def band(title="Nicht sicher, was zu Ihrem Fahrzeug passt?", btn="Kostenlos beraten lassen"):
    return f'<div class="cta-band"><div class="wrap"><h2>{title}</h2><a class="btn btn-lg" href="kontakt.html">{btn} {ic("arrow")}</a></div></div>'

def brand_options():
    return '<option value="">Fahrzeugmarke wählen …</option>' + "".join(f'<option value="{b["slug"]}">{esc(b["name"])}</option>' for b in BRANDS)

# ================= STARTSEITE =================
def home():
    feats = [p for p in PRODUCTS if p["price"]]
    cats = "".join(f'<a class="cat" href="{c["slug"]}.html"><div class="cat-art tone-{c["tone"]}">{ic(c["icon"])}</div><div class="cat-body"><h3>{esc(c["name"])}</h3><p>{esc(c["short"])}</p><span class="more">Ansehen {ic("arrow")}</span></div></a>' for c in CATEGORIES)
    brands = "".join(f'<a class="chip" href="fahrzeug-{b["slug"]}.html">{esc(b["name"])}</a>' for b in BRANDS)
    faq, fs = faq_html(FAQ_GENERAL)
    locs = "".join(f'<div class="loc"><h3>{ic("pin")} {l["city"]}</h3><p>{l["plz"]} {l["city"]}, {l["region"]}</p><a class="btn btn-out" href="standort-{l["slug"]}.html">Montage in {l["city"]}</a></div>' for l in LOCATIONS)
    body = f'''<section class="hero"><div class="wrap"><div><span class="kicker">Wohnmobil-Nachrüstung seit {SITE['since']}</span>
<h1>Anhängerkupplung, Luftfederung &amp; Stützen für Ihr Wohnmobil</h1>
<p class="lead">Über 100 Produkte mit EG-Typgenehmigung, persönliche Fachberatung und Montage an zwei Standorten. Versandkostenfrei in ganz Deutschland.</p>
<div class="cta-row"><a class="btn btn-cta btn-lg" href="anhaengerkupplung.html">Anhängerkupplungen ansehen {ic("arrow")}</a><a class="btn btn-ghost btn-lg" href="kontakt.html">Beratung anfordern</a></div>
<ul class="ticks"><li>{ic("check")} Festpreise</li><li>{ic("check")} 2–4 Werktage Lieferzeit</li><li>{ic("check")} {SITE['rating']} / 5 Google-Bewertung</li></ul></div>
<form class="finder" id="finder"  novalidate><h2>Fahrzeugfinder</h2><p>Wählen Sie Ihr Basisfahrzeug und sehen Sie passendes Zubehör.</p>
<label for="marke">Fahrzeugmarke</label><select id="marke" name="marke" required>{brand_options()}</select>
<button class="btn btn-cta btn-block btn-lg" style="margin-top:16px" type="submit">Passendes Zubehör zeigen</button>
<p style="margin:12px 0 0;font-size:.85rem">Auch für {", ".join(COACH_BRANDS[:4])} u. a. – wir prüfen die Passung vor jedem Kauf.</p></form></div></section>
<section id="fahrzeugfinder" style="padding:32px 0"><div class="wrap"><ul class="usp"><li>{ic("shield")}<div><strong>EG-Typgenehmigung</strong><span>EG-Gutachten inklusive, keine TÜV-Abnahme nötig*</span></div></li>
<li>{ic("truck")}<div><strong>Versandkostenfrei</strong><span>Lieferung in 2–4 Werktagen</span></div></li>
<li>{ic("wrench")}<div><strong>Montage vor Ort</strong><span>Bohmte &amp; Diez, zum Festpreis</span></div></li>
<li>{ic("headset")}<div><strong>Fachberatung</strong><span>Persönlich per Telefon oder E-Mail</span></div></li></ul></div></section>
<section id="kategorien" class="soft"><div class="wrap"><div class="sec-head"><div><h2>Unser Sortiment</h2><p>Alles, was Ihr Reisemobil sicherer, komfortabler und vielseitiger macht.</p></div></div><div class="cats">{cats}</div></div></section>
<section><div class="wrap"><div class="sec-head"><div><h2>Beliebte Produkte</h2><p>Direkt bestellen – inkl. MwSt. und versandkostenfrei.</p></div>{stars()}</div><div class="grid">{"".join(card(p,i) for i,p in enumerate(feats))}</div></div></section>
<section class="soft"><div class="wrap"><div class="sec-head"><div><h2>In 4 Schritten zum fertig ausgerüsteten Wohnmobil</h2></div></div>
<ol class="steps"><li><h3>Fahrzeug wählen</h3><p>Marke im Fahrzeugfinder wählen oder uns Ihr Modell nennen.</p></li><li><h3>Beraten lassen</h3><p>Wir prüfen Passung, Gewichte und Zulassung vorab.</p></li><li><h3>Bestellen</h3><p>Online kaufen – PayPal, Karte, Rechnung oder Überweisung.</p></li><li><h3>Einbauen</h3><p>Selbst montieren oder Termin bei uns in Bohmte oder Diez.</p></li></ol></div></section>
<section><div class="wrap split"><div><h2>Zubehör für Ihre Fahrzeugbasis</h2><p>Ob Ducato, Jumper, Boxer, Sprinter, Crafter, MAN TGE oder Ford Transit: Wir kennen die Besonderheiten der gängigen Basisfahrzeuge und der Ausbauten von Carthago, Dethleffs, Hymer, Bürstner, Knaus, Laika und Weinsberg.</p><div class="chips">{brands}</div></div>
<div class="panel"><h2>Montage-Service</h2><p>Zwei Standorte, ein Anspruch: Ihr Wohnmobil kommt fertig montiert zurück – zum vorher vereinbarten Festpreis.</p><div class="locs" style="grid-template-columns:1fr">{locs}</div></div></div></section>
<section class="soft"><div class="wrap"><div class="sec-head"><div><h2>Ratgeber</h2><p>Wissen, das Sie vor dem Kauf weiterbringt.</p></div><a class="btn btn-out" href="ratgeber.html">Alle Ratgeber</a></div><div class="cats">{"".join(f'<a class="cat" href="ratgeber-{g["slug"]}.html"><div class="cat-art tone-g">{ic("book")}</div><div class="cat-body"><h3>{esc(g["title"])}</h3><p>{esc(g["lead"])}</p><span class="more">Lesen {ic("arrow")}</span></div></a>' for g in GUIDES[:3])}</div></div></section>
<section><div class="wrap" style="max-width:860px"><h2>Häufige Fragen</h2>{faq}<p><a href="faq.html">Alle Fragen &amp; Antworten →</a></p></div></section>{band()}'''
    page("index.html", "Wohnmobil-Zubehör & Nachrüstung | Italia Camper 24",
         "Anhängerkupplung, Luftfederung, Stützen & Heckträger für Wohnmobil und Kastenwagen. EG-Typgenehmigung, versandkostenfrei, Montage in Bohmte & Diez.",
         body, [fs], prio="1.0")

# ================= KATEGORIE =================
def category(c):
    prods = PBYC[c["slug"]]
    grid = "".join(card(p, i) for i, p in enumerate(prods))
    faq, fs = faq_html(c["faq"])
    side = "".join(f'<li><a href="{x["slug"]}.html"{" aria-current=page" if x["slug"] == c["slug"] else ""}>{esc(x["name"])}</a></li>' for x in CATEGORIES)
    itemlist = {"@context": "https://schema.org", "@type": "CollectionPage", "name": c["h1"], "description": c["meta"], "url": f'{U}/{c["slug"]}.html',
                "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f'{U}/{p["url"]}', "name": p["name"]} for i, p in enumerate(prods)]}}
    body = f'''<div class="page-head"><div class="wrap"><h1>{esc(c["h1"])}</h1><p>{esc(c["intro"])}</p></div></div>
<div class="wrap shop"><aside class="side" aria-label="Kategorien"><h2>Kategorien</h2><ul>{side}</ul><div class="notice">{ic("headset")} <strong>Unsicher?</strong><br>Wir beraten kostenlos: <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a></div></aside>
<div><div class="toolbar"><strong>{len(prods)} Artikel</strong><div><label class="sr" for="sort">Sortieren</label><select id="sort"><option value="">Empfohlen</option><option value="asc">Preis aufsteigend</option><option value="desc">Preis absteigend</option></select></div></div>
<div class="grid three" id="prodgrid">{grid}</div>
<div style="margin-top:48px"><h2>Worauf Sie beim Kauf achten sollten</h2><p>{esc(c["intro"])} Nennen Sie uns Fahrzeug und Baujahr, wir prüfen Passung, Gewichte und Zulassung, bevor Sie bestellen. Montage ist an den Standorten <a href="standort-bohmte.html">Bohmte</a> und <a href="standort-diez.html">Diez</a> möglich.</p>
<h2>Häufige Fragen</h2>{faq}</div></div></div>{band()}'''
    page(f'{c["slug"]}.html', f'{c["h1"]} kaufen | Italia Camper 24', c["meta"], body, [fs, itemlist],
         [("Startseite", "index.html"), (c["name"], None)], prio="0.9", nav_cur=f'{c["slug"]}.html')

# ================= PRODUKT =================
def product(p):
    c = CAT[p["cat"]]
    faq, fs = faq_html(c["faq"][:2] + [FAQ_GENERAL[0]])
    rel = [x for x in PRODUCTS if x["cat"] != p["cat"] and x["price"]][:4]
    pr = p["price"]
    if pr:
        price = f'<div class="price">{"<span class=from>ab </span>" if p["from_"] else ""}{eur(pr)}{f" <del>{eur(p[chr(111)+chr(108)+chr(100)])}</del>" if p["old"] else ""}</div><small>inkl. gesetzl. MwSt. · versandkostenfrei · Lieferzeit 2–4 Werktage</small>'
        buy = f'<div class="buyrow"><div class="qty"><button type="button" data-d="-" aria-label="Menge verringern">−</button><input id="qty" value="1" inputmode="numeric" aria-label="Menge"><button type="button" data-d="+" aria-label="Menge erhöhen">+</button></div><button class="btn btn-cta btn-lg" data-add="{p["slug"]}" data-useqty>{ic("cart")} In den Warenkorb</button></div>'
        mb = f'<div class="mbar"><div style="flex:0 0 auto;font:700 1.2rem var(--f-h);align-self:center">{eur(pr)}</div><button class="btn btn-cta" data-add="{p["slug"]}">In den Warenkorb</button></div>'
    else:
        price = '<div class="price ask">Preis auf Anfrage</div><small>Wir erstellen Ihnen ein individuelles Festpreis-Angebot.</small>'
        buy = f'<div class="buyrow"><a class="btn btn-cta btn-lg" href="kontakt.html?produkt={esc(p["name"])}">Angebot anfordern</a><a class="btn btn-out btn-lg" href="tel:{SITE["phone_href"]}">{ic("phone")} Anrufen</a></div>'
        mb = f'<div class="mbar"><a class="btn btn-cta" href="kontakt.html?produkt={esc(p["name"])}">Angebot anfordern</a><a class="btn btn-out" href="tel:{SITE["phone_href"]}">Anrufen</a></div>'
    prod_s = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["desc"], "category": c["name"],
              "brand": {"@type": "Brand", "name": SITE["name"]}, "sku": p["slug"], "url": f'{U}/{p["url"]}'}
    if pr:
        prod_s["offers"] = {"@type": "Offer", "priceCurrency": "EUR", "price": f"{pr:.2f}", "url": f'{U}/{p["url"]}', "availability": "https://schema.org/InStock",
                            "itemCondition": "https://schema.org/NewCondition", "priceValidUntil": f"{datetime.date.today().year + 1}-12-31",
                            "seller": {"@id": U + "/#org"},
                            "shippingDetails": {"@type": "OfferShippingDetails", "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "EUR"},
                                                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "DE"},
                                                "deliveryTime": {"@type": "ShippingDeliveryTime", "transitTime": {"@type": "QuantitativeValue", "minValue": 2, "maxValue": 4, "unitCode": "DAY"}}}}
    specs = "".join(f"<tr><th>{esc(a)}</th><td>{esc(b)}</td></tr>" for a, b in p["specs"])
    ticks = "".join(f'<li>{ic("check")} {esc(b)}</li>' for b in p["bullets"])
    body = f'''<div class="wrap pdp"><div><div class="gallery tone-{p["tone"]}" role="img" aria-label="{esc(p["name"])} – Produktsymbol">{ic(p["icon"])}<span class="note">Produktfoto folgt – Symbolbild</span></div></div>
<div><p style="margin:0"><a href="{c["slug"]}.html">{esc(c["name"])}</a></p><h1 style="font-size:clamp(1.6rem,3vw,2.2rem)">{esc(p["name"])}</h1>{stars()}
<p style="margin-top:12px">{esc(p["short"])}</p>
<div class="buybox">{price}{buy}<ul class="meta-list"><li>{ic("truck")} Versandkostenfrei, Lieferzeit 2–4 Werktage</li><li>{ic("shield")} EG-Typgenehmigung, Gutachten inklusive*</li><li>{ic("wrench")} Montage in Bohmte &amp; Diez möglich</li><li>{ic("headset")} Passt es? Wir prüfen es vorab: <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a></li></ul></div>
<ul class="ticks">{ticks}</ul></div></div>
<div class="wrap" style="max-width:900px;padding-bottom:40px"><details open><summary>Beschreibung</summary><div><p>{esc(p["desc"])}</p></div></details>
<details><summary>Technische Daten</summary><div><table class="spec">{specs}</table></div></details>
<details><summary>Passend für</summary><div><p>{", ".join(b["name"] for b in BRANDS)} sowie Reisemobile von {", ".join(COACH_BRANDS)}. Die konkrete Passung prüfen wir vor Ihrer Bestellung anhand Fahrzeugtyp und Baujahr.</p></div></details>
<details><summary>Lieferung, Montage &amp; Rückgabe</summary><div><p>Versandkostenfrei innerhalb Deutschlands in 2–4 Werktagen. Montage nach Terminvereinbarung zum Festpreis in <a href="standort-bohmte.html">Bohmte</a> oder <a href="standort-diez.html">Diez</a>. Es gelten die gesetzlichen Widerrufsrechte, siehe <a href="widerruf.html">Widerrufsbelehrung</a>.</p></div></details>
<h2 style="margin-top:32px">Fragen zum Produkt</h2>{faq}</div>
<section class="soft"><div class="wrap"><h2>Das könnte Sie auch interessieren</h2><div class="grid">{"".join(card(x,i) for i,x in enumerate(rel))}</div></div></section>'''
    page(p["url"], f'{p["name"]}{" ab "+eur(pr) if pr else ""} | Italia Camper 24',
         f'{p["name"]}: {p["short"]} {"Ab " + eur(pr) + ", " if pr else ""}versandkostenfrei, Montage in Bohmte & Diez.'[:160], body, [fs, prod_s],
         [("Startseite", "index.html"), (c["name"], f'{c["slug"]}.html'), (p["name"], None)], og_type="product", prio="0.8", mbar=mb)

# ================= FAHRZEUG (GEO/Long-Tail) =================
def brand(b):
    prods = [p for p in PRODUCTS if p["price"]]
    faq = [(f"Welches Zubehör können Sie für den {b['name']} nachrüsten?", f"Für den {b['name']} bieten wir unter anderem Anhängerkupplungen, Luftfederung, Stützensysteme, Heckträger, Klimaanlagen und Rangierhilfen an. Die genaue Passung prüfen wir anhand Ihres Baujahrs."),
           (f"Brauche ich für den {b['name']} eine TÜV-Abnahme nach dem Einbau einer Anhängerkupplung?", "Bei Kupplungen mit EG-Typgenehmigung liegt das EG-Gutachten bei und eine TÜV-Abnahme ist in der Regel nicht nötig. Wir sagen Ihnen vorab, was für Ihr Fahrzeug gilt."),
           (f"Kann ich meinen {b['name']} bei Ihnen umrüsten lassen?", "Ja, an unseren Standorten Bohmte (Niedersachsen) und Diez (Rheinland-Pfalz) nach Terminvereinbarung zum Festpreis.")]
    fh, fs = faq_html(faq)
    cats = "".join(f'<a class="cat" href="{c["slug"]}.html"><div class="cat-art tone-{c["tone"]}">{ic(c["icon"])}</div><div class="cat-body"><h3>{esc(c["name"])}</h3><p>{esc(c["short"])}</p></div></a>' for c in CATEGORIES)
    body = f'''<div class="page-head"><div class="wrap"><h1>Wohnmobil-Zubehör für {esc(b["name"])}</h1><p>{esc(b["note"])} {esc(b["same"])}</p></div></div>
<section><div class="wrap"><div class="answer"><strong>Kurz gesagt:</strong> Italia Camper 24 rüstet den {esc(b["name"])} mit Anhängerkupplung, Luftfederung, Stützen, Heckträger und mehr nach – mit EG-Typgenehmigung, Festpreis und Montage in Bohmte und Diez.</div>
<h2>Nachrüst-Kategorien für den {esc(b["name"])}</h2><div class="cats">{cats}</div></div></section>
<section class="soft"><div class="wrap"><h2>Beliebt bei {esc(b["name"])}-Fahrern</h2><div class="grid">{"".join(card(p,i) for i,p in enumerate(prods))}</div><p style="margin-top:16px">Bitte nennen Sie uns Baujahr und Ausbauhersteller – wir bestätigen die Passung vor jeder Bestellung.</p></div></section>
<section><div class="wrap" style="max-width:860px"><h2>Fragen zum {esc(b["name"])}</h2>{fh}</div></section>{band(f"Ihren {b['name']} nachrüsten?")}'''
    page(f'fahrzeug-{b["slug"]}.html', f'{b["name"]} Zubehör & Nachrüstung | Italia Camper 24',
         f'Zubehör für {b["name"]}: Anhängerkupplung, Luftfederung, Stützen, Heckträger. EG-Typgenehmigung, Montage in Bohmte & Diez.', body, [fs],
         [("Startseite", "index.html"), ("Fahrzeuge", "index.html#fahrzeugfinder"), (b["name"], None)], prio="0.7")

# ================= STANDORT =================
def location(l):
    faq = [(f"Wo montiert Italia Camper 24 in {l['city']}?", f"Am Standort {l['plz']} {l['city']} ({l['region']}). Die genaue Adresse erhalten Sie bei der Terminvergabe."),
           ("Muss ich einen Termin vereinbaren?", "Ja. Wir planen jede Montage fest ein, damit Ihr Fahrzeug zum vereinbarten Zeitpunkt fertig ist."),
           ("Was kostet die Montage?", "Wir nennen Ihnen vorab einen Festpreis, abhängig von Fahrzeug und Zubehör.")]
    fh, fs = faq_html(faq)
    lb = {"@context": "https://schema.org", "@type": "AutoRepair", "name": f'{SITE["name"]} {l["city"]}', "url": f'{U}/standort-{l["slug"]}.html',
          "telephone": SITE["phone"], "email": SITE["email"], "parentOrganization": {"@id": U + "/#org"},
          "address": {"@type": "PostalAddress", "postalCode": l["plz"], "addressLocality": l["city"], "addressRegion": l["state"], "addressCountry": "DE"},
          "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lon"]}}
    body = f'''<div class="page-head"><div class="wrap"><h1>Wohnmobil-Montage in {l["city"]}</h1><p>Anhängerkupplung, Luftfederung und Stützen einbauen lassen – {l["plz"]} {l["city"]}, {l["region"]}.</p></div></div>
<section><div class="wrap split"><div><div class="answer"><strong>Kurz gesagt:</strong> In {l["city"]} montieren wir Wohnmobil-Zubehör nach Terminvereinbarung zum Festpreis. Rufen Sie an: <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a>.</div><p>{esc(l["text"])}</p>
<h2>Das montieren wir in {l["city"]}</h2><ul class="ticks">{"".join(f'<li>{ic("check")} {esc(c["name"])}</li>' for c in CATEGORIES)}</ul></div>
<div class="panel"><h2>Termin anfragen</h2><p>Nennen Sie uns Fahrzeug, Baujahr und Wunschprodukt – wir melden uns mit Terminvorschlag und Festpreis.</p><a class="btn btn-cta btn-lg btn-block" href="kontakt.html?produkt=Montage {l["city"]}">Termin anfragen</a><p style="margin-top:16px">{ic("phone")} <a style="color:#fff" href="tel:{SITE['phone_href']}">{SITE['phone']}</a></p></div></div></section>
<section class="soft"><div class="wrap" style="max-width:860px"><h2>Fragen zur Montage in {l["city"]}</h2>{fh}</div></section>{band()}'''
    page(f'standort-{l["slug"]}.html', f'Wohnmobil Zubehör einbauen in {l["city"]} ({l["region"]}) | Italia Camper 24',
         f'Montage von Anhängerkupplung, Luftfederung & Stützen in {l["plz"]} {l["city"]}. Festpreis, EG-Typgenehmigung, Termin nach Absprache.', body, [fs, lb],
         [("Startseite", "index.html"), ("Montage-Service", "montage-service.html"), (l["city"], None)], prio="0.8")

# ================= RATGEBER =================
def guide(g):
    secs = "".join(f"<h2>{esc(h)}</h2><p>{esc(t)}</p>" for h, t in g["sections"])
    rel = "".join(f'<li><a href="{r}.html">{esc(CAT[r]["name"])}</a></li>' for r in g["related"])
    art = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["meta"], "inLanguage": "de-DE",
           "datePublished": TODAY, "dateModified": TODAY, "author": {"@id": U + "/#org"}, "publisher": {"@id": U + "/#org"},
           "mainEntityOfPage": f'{U}/ratgeber-{g["slug"]}.html'}
    body = f'''<div class="wrap"><article class="article"><h1>{esc(g["title"])}</h1><p class="lead">{esc(g["lead"])}</p>{secs}
<div class="answer"><strong>Passende Produkte:</strong><ul>{rel}</ul></div><p><a class="btn btn-cta" href="kontakt.html">Persönliche Beratung anfragen</a></p></article></div>'''
    page(f'ratgeber-{g["slug"]}.html', f'{g["title"]} | Ratgeber', g["meta"], body, [art],
         [("Startseite", "index.html"), ("Ratgeber", "ratgeber.html"), (g["title"], None)], og_type="article", prio="0.6")

def guides_index():
    body = f'''<div class="page-head"><div class="wrap"><h1>Ratgeber für Wohnmobil-Nachrüstung</h1><p>Praxiswissen zu Anhängerkupplung, Luftfederung, Stützen &amp; Co.</p></div></div>
<section><div class="wrap"><div class="cats">{"".join(f'<a class="cat" href="ratgeber-{g["slug"]}.html"><div class="cat-art tone-g">{ic("book")}</div><div class="cat-body"><h3>{esc(g["title"])}</h3><p>{esc(g["lead"])}</p><span class="more">Lesen {ic("arrow")}</span></div></a>' for g in GUIDES)}</div></div></section>{band()}'''
    page("ratgeber.html", "Ratgeber Wohnmobil-Nachrüstung | Italia Camper 24", "Ratgeber zu Anhängerkupplung, Luftfederung, Stützensystemen und Nachrüst-Reihenfolge für Wohnmobile.", body, [],
         [("Startseite", "index.html"), ("Ratgeber", None)], prio="0.6")

# ================= INFO-SEITEN =================
def simple(fname, title, desc, h1, content, prio="0.5", noindex=False, schemas=()):
    body = f'<div class="page-head"><div class="wrap"><h1>{esc(h1)}</h1></div></div><div class="wrap"><div class="article">{content}</div></div>'
    page(fname, title, desc, body, schemas, [("Startseite", "index.html"), (h1, None)], prio=prio, noindex=noindex)

def info_pages():
    faq, fs = faq_html(FAQ_GENERAL)
    simple("faq.html", "Häufige Fragen (FAQ) | Italia Camper 24", "Antworten zu Lieferung, Zahlung, EG-Typgenehmigung, Montage und Widerruf.", "Häufige Fragen", faq, "0.6", schemas=[fs])
    simple("versand-zahlung.html", "Versand & Zahlung | Italia Camper 24", "Versandkostenfrei in Deutschland, Lieferzeit 2–4 Werktage. Zahlung per PayPal, Kreditkarte, Überweisung oder Rechnung.", "Versand &amp; Zahlung".replace("&amp;", "&"),
           f'<div class="answer"><strong>Kurz gesagt:</strong> Versand kostenlos in Deutschland, Lieferzeit 2–4 Werktage, Zahlung per PayPal, Kreditkarte, Überweisung oder Rechnung.</div><h2>Versand</h2><p>Wir liefern versandkostenfrei innerhalb Deutschlands. Die Lieferzeit beträgt in der Regel 2–4 Werktage.</p><h2>Zahlungsarten</h2><ul class="ticks"><li>{ic("check")} PayPal</li><li>{ic("check")} Kreditkarte (Visa / Mastercard)</li><li>{ic("check")} Überweisung</li><li>{ic("check")} Rechnung</li></ul><p>Alle Preise verstehen sich inklusive gesetzlicher Mehrwertsteuer.</p><h2>Montage statt Versand</h2><p>Sie können Ihr Fahrzeug auch direkt bei uns umrüsten lassen: <a href="montage-service.html">Zum Montage-Service</a>.</p>', "0.6")
    locs = "".join(f'<div class="loc"><h3>{ic("pin")} {l["city"]}</h3><p>{esc(l["text"])}</p><a class="btn btn-out" href="standort-{l["slug"]}.html">Mehr zum Standort</a></div>' for l in LOCATIONS)
    simple("montage-service.html", "Montage-Service Bohmte & Diez | Italia Camper 24", "Wohnmobil-Zubehör einbauen lassen: Standorte Bohmte und Diez, Festpreis, Termin nach Absprache.", "Montage-Service",
           f'<div class="answer"><strong>Kurz gesagt:</strong> Wir bauen Ihr Zubehör an zwei Standorten ein – in Bohmte (Niedersachsen) und Diez (Rheinland-Pfalz), nach Termin und zum Festpreis.</div><div class="locs">{locs}</div><h2>So läuft es ab</h2><ol><li>Fahrzeug und Wunschprodukt nennen</li><li>Festpreis &amp; Termin erhalten</li><li>Fahrzeug bringen, montiert abholen</li></ol><a class="btn btn-cta btn-lg" href="kontakt.html">Termin anfragen</a>', "0.8")
    simple("ueber-uns.html", "Über uns | Italia Camper 24", f"Italia Camper 24 – Spezialist für Wohnmobil-Nachrüstung seit {SITE['since']}.", "Über Italia Camper 24",
           f'<p>Seit {SITE["since"]} rüsten wir Wohnmobile und Kastenwagen nach. Unser Sortiment umfasst über 100 Produkte mit EG-Typgenehmigung. Ob Anhängerkupplung, Luftfederung oder Stützensystem: Wir beraten persönlich, nennen Festpreise und montieren an unseren Standorten in Bohmte und Diez.</p><ul class="ticks"><li>{ic("star")} {SITE["rating"]} von 5 Sternen bei Google</li><li>{ic("shield")} EG-Gutachten inklusive</li><li>{ic("truck")} Versandkostenfrei in Deutschland</li></ul>', "0.5")
    form = f'''<form id="contactform" class="form-grid" novalidate><div><label for="name">Name *</label><input id="name" name="name" required autocomplete="name"><div class="err">Bitte Namen angeben.</div></div>
<div><label for="email">E-Mail *</label><input id="email" name="email" type="email" required autocomplete="email"><div class="err">Bitte gültige E-Mail angeben.</div></div>
<div><label for="tel">Telefon</label><input id="tel" name="tel" type="tel" autocomplete="tel"></div>
<div><label for="betreff">Betreff</label><select id="betreff" name="betreff"><option>Produktberatung</option><option>Montage-Termin</option><option>Bestellung</option><option>Sonstiges</option></select></div>
<div class="full"><label for="nachricht">Ihre Nachricht (bitte Fahrzeug &amp; Baujahr nennen) *</label><textarea id="nachricht" name="nachricht" required></textarea><div class="err">Bitte Nachricht eingeben.</div></div>
<div class="full"><button class="btn btn-cta btn-lg" type="submit">Anfrage senden</button><p id="sent" hidden class="notice">Ihr E-Mail-Programm wurde geöffnet. Bitte senden Sie die Nachricht dort ab.</p></div></form>'''
    simple("kontakt.html", "Kontakt & Beratung | Italia Camper 24", "Kontakt zu Italia Camper 24: Telefon +49 151 404 790 19, E-Mail info@italiacamper24.de.", "Kontakt &amp; Beratung".replace("&amp;", "&"),
           f'<p>{ic("phone")} <a href="tel:{SITE["phone_href"]}">{SITE["phone"]}</a><br>{ic("mail")} <a href="mailto:{SITE["email"]}">{SITE["email"]}</a></p>{form}', "0.7")
    ph = '<div class="notice"><strong>Hinweis:</strong> Platzhalter – bitte durch die rechtsverbindlichen Texte des Betreibers ersetzen.</div>'
    simple("impressum.html", "Impressum | Italia Camper 24", "Impressum Italia Camper 24", "Impressum", f'{ph}<p><strong>{SITE["name"]}</strong><br>[Inhaber / Rechtsform ergänzen]<br>[Straße, Nr.]<br>49163 Bohmte<br>Telefon: {SITE["phone"]}<br>E-Mail: {SITE["email"]}<br>USt-IdNr.: [ergänzen]</p>', noindex=True)
    simple("agb.html", "AGB | Italia Camper 24", "AGB", "Allgemeine Geschäftsbedingungen", f"{ph}<p>[AGB-Text einfügen]</p>", noindex=True)
    simple("widerruf.html", "Widerrufsbelehrung | Italia Camper 24", "Widerrufsbelehrung", "Widerrufsbelehrung", f"{ph}<p>[Widerrufsbelehrung einfügen]</p>", noindex=True)
    simple("datenschutz.html", "Datenschutz | Italia Camper 24", "Datenschutzerklärung", "Datenschutzerklärung", f"{ph}<p>[Datenschutzerklärung einfügen]. Diese Seite nutzt Google Fonts (extern geladen) und speichert den Warenkorb lokal im Browser.</p>", noindex=True)

def cart_checkout():
    body = f'''<div class="page-head"><div class="wrap"><h1>Warenkorb</h1></div></div><div class="wrap two"><div id="cartlist" aria-live="polite"></div>
<aside class="summary" id="sum" hidden><h2>Zusammenfassung</h2><dl><div><dt>Zwischensumme</dt><dd id="t-sub">–</dd></div><div><dt>Versand</dt><dd>kostenlos</dd></div><div><dt>darin enth. MwSt. 19 %</dt><dd id="t-vat">–</dd></div><div class="total"><dt>Gesamt</dt><dd id="t-tot">–</dd></div></dl>
<a class="btn btn-cta btn-lg btn-block" id="tocheckout" href="kasse.html" style="margin-top:16px">Zur Kasse</a><ul class="meta-list"><li>{ic("shield")} Sichere Bestellung</li><li>{ic("truck")} Lieferung in 2–4 Werktagen</li><li>{ic("headset")} Fragen? {SITE['phone']}</li></ul></aside></div>'''
    page("warenkorb.html", "Warenkorb | Italia Camper 24", "Ihr Warenkorb bei Italia Camper 24", body, [], noindex=True)
    f = lambda i, l, t="text", req=True, ac="", full=False: f'<div{" class=full" if full else ""}><label for="{i}">{l}{" *" if req else ""}</label><input id="{i}" name="{i}" type="{t}"{" required" if req else ""}{f" autocomplete={ac}" if ac else ""}><div class="err">Bitte ausfüllen.</div></div>'
    body = f'''<div class="page-head"><div class="wrap"><h1>Kasse</h1></div></div><div class="wrap two"><div><p id="cohint" hidden>Ihr Warenkorb ist leer. <a href="index.html">Zum Shop</a></p>
<form id="checkout" novalidate><h2>Ihre Daten</h2><div class="form-grid">{f("vorname","Vorname",ac="given-name")}{f("nachname","Nachname",ac="family-name")}{f("strasse","Straße & Hausnummer",ac="street-address",full=True)}{f("plz","PLZ",ac="postal-code")}{f("ort","Ort",ac="address-level2")}{f("email","E-Mail","email",ac="email")}{f("tel","Telefon (für Rückfragen)","tel",False,"tel")}{f("fahrzeug","Fahrzeug & Baujahr (zur Passungsprüfung)",full=True)}</div>
<h2 style="margin-top:28px">Zahlart &amp; Montage</h2><div class="form-grid"><div><label for="zahlart">Zahlart</label><select id="zahlart" name="zahlart"><option>PayPal</option><option>Kreditkarte</option><option>Überweisung</option><option>Rechnung</option></select></div>
<div><label for="montage">Montage</label><select id="montage" name="montage"><option>Ich montiere selbst</option><option>Montage in Bohmte</option><option>Montage in Diez</option></select></div>
<div class="full"><label for="note">Anmerkung</label><textarea id="note" name="note"></textarea></div>
<div class="full"><label style="display:flex;gap:10px;align-items:flex-start;font-weight:400"><input type="checkbox" name="agb" required style="width:24px;min-height:24px;margin-top:2px"> <span>Ich habe die <a href="agb.html">AGB</a>, die <a href="widerruf.html">Widerrufsbelehrung</a> und die <a href="datenschutz.html">Datenschutzerklärung</a> gelesen. *</span></label></div></div>
<div class="notice">Bestellung wird als Anfrage an unser Team übermittelt, wir bestätigen Verfügbarkeit, Passung und Zahlungsdetails.</div>
<button class="btn btn-cta btn-lg btn-block" type="submit">Verbindlich anfragen</button><p id="done" hidden class="notice">Danke! Bitte senden Sie die vorbereitete E-Mail in Ihrem Mailprogramm ab.</p></form></div>
<aside class="summary"><h2>Ihre Bestellung</h2><div id="orderlines"></div><div class="total" style="display:flex;justify-content:space-between;border-top:2px solid var(--line);margin-top:8px;padding-top:12px;font:700 1.25rem var(--f-h)"><span>Gesamt</span><span id="o-tot">–</span></div><small>inkl. MwSt., versandkostenfrei</small></aside></div>'''
    page("kasse.html", "Kasse | Italia Camper 24", "Kasse", body, [], noindex=True)

def search_page():
    body = '<div class="page-head"><div class="wrap"><h1>Suche</h1><p>Nutzen Sie das Suchfeld oben. Hier die wichtigsten Bereiche:</p></div></div><div class="wrap"><div class="chips" style="padding:32px 0">' + "".join(f'<a class="chip" href="{c["slug"]}.html">{esc(c["name"])}</a>' for c in CATEGORIES) + '</div></div>'
    page("suche.html", "Suche | Italia Camper 24", "Shop durchsuchen", body, [], noindex=True)

def notfound():
    body = f'<div class="wrap" style="text-align:center;padding:80px 16px"><h1>Seite nicht gefunden</h1><p>Die Seite gibt es leider nicht (mehr).</p><a class="btn btn-cta btn-lg" href="index.html">Zur Startseite</a></div>'
    page("404.html", "404 | Italia Camper 24", "Seite nicht gefunden", body, [], noindex=True)

def system_files():
    urls = "".join(f'<url><loc>{U}/{"" if f=="index.html" else f}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>' for f, p in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /warenkorb.html\nDisallow: /kasse.html\nDisallow: /suche.html\n\nSitemap: {U}/sitemap.xml\n")
    llm = [f"# {SITE['name']}", "", f"> Fachhändler und Montagebetrieb für Wohnmobil-Nachrüstung seit {SITE['since']}: Anhängerkupplungen, Luftfederung, Stützensysteme, Heckträger. Versandkostenfrei in Deutschland, Montage in Bohmte (49163) und Diez (65582).", "", "## Wichtige Seiten"]
    llm += [f"- [{c['name']}]({U}/{c['slug']}.html): {c['short']}" for c in CATEGORIES]
    llm += ["", "## Fahrzeuge"] + [f"- [{b['name']}]({U}/fahrzeug-{b['slug']}.html)" for b in BRANDS]
    llm += ["", "## Service", f"- [Montage-Service]({U}/montage-service.html)", f"- [Versand & Zahlung]({U}/versand-zahlung.html)", f"- [FAQ]({U}/faq.html)", f"- [Ratgeber]({U}/ratgeber.html)", f"- Telefon: {SITE['phone']}", f"- E-Mail: {SITE['email']}"]
    open(os.path.join(OUT, "llms.txt"), "w").write("\n".join(llm) + "\n")
    open(os.path.join(OUT, "assets", "favicon.svg"), "w").write(LOGO.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" '))

if __name__ == "__main__":
    home()
    for c in CATEGORIES: category(c)
    for p in PRODUCTS: product(p)
    for b in BRANDS: brand(b)
    for l in LOCATIONS: location(l)
    for g in GUIDES: guide(g)
    guides_index(); info_pages(); cart_checkout(); search_page(); notfound(); system_files()
    print(len(PAGES), "indexierbare Seiten")
