# -*- coding: utf-8 -*-
"""Strukturierte Daten (schema.org), Sitemap, robots.txt, llms.txt, RSS, Manifest."""
import html
import json

import md


def business(site):
    s = site.s
    a = s["address"]
    bid = site.url + "/#business"
    offers = []
    for p in site.pricing["packages"]:
        offers.append({"@type": "Offer", "name": p["name"], "price": str(site.min_price(p["key"])), "priceCurrency": "EUR",
                       "url": site.url + "/termin.html?paket=" + p["key"],
                       "description": p["for"] + " Richtpreis ab " + str(site.min_price(p["key"])) + " € (Kleinwagen).",
                       "itemOffered": {"@type": "Service", "name": p["name"], "serviceType": "Fahrzeugaufbereitung"}})
    return {
        "@context": "https://schema.org",
        "@type": ["AutoDetailing", "LocalBusiness"],
        "@id": bid,
        "name": s["name"],
        "alternateName": s["name"] + " – " + s["tagline"] + " " + a["city"],
        "description": "Professionelle Fahrzeugaufbereitung in Celle mit Schwerpunkt Lackaufbereitung und Keramikversiegelung: Innen- und Außenaufbereitung, Lackpolitur, Keramik- und Lackversiegelung, Lederpflege und Lederreparatur in Handarbeit. Offizieller C²Coating Excellence Partner, Koch-Chemie geschult. Termine nach Vereinbarung.",
        "url": site.url + "/",
        "telephone": s["phone"],
        "email": s["email"],
        "image": site.url + "/og-image.png",
        "logo": site.url + "/logo-512.png",
        "priceRange": "€€",
        "currenciesAccepted": "EUR",
        "paymentAccepted": "Bar, Kartenzahlung, PayPal, Überweisung",
        "address": {"@type": "PostalAddress", "streetAddress": a["street"], "postalCode": a["zip"], "addressLocality": a["city"],
                    "addressRegion": a["region"], "addressCountry": a["country"]},
        "hasMap": site.maps_url(),
        "areaServed": [{"@type": "City", "name": a["city"]}] + [{"@type": "City", "name": n} for n in s["areas"]["region"]],
        "knowsAbout": ["Fahrzeugaufbereitung", "Car Detailing", "Keramikversiegelung", "Lackkorrektur", "Lackpolitur", "Lackversiegelung",
                       "Innenraumreinigung", "Lederpflege", "Lederreparatur", "Geruchsentfernung", "Cabrioverdeckreinigung", "Leasingrückgabe", "Flottenpflege"],
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification", "dayOfWeek": s["openingHours"]["days"],
                                      "opens": s["openingHours"]["opens"], "closes": s["openingHours"]["closes"],
                                      "description": s["openingHours"]["text"]},
        "sameAs": list(s["social"].values()),
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": s["rating"]["value"].replace(",", "."), "bestRating": "5",
                            "reviewCount": str(s["rating"]["count"])},
        "review": [{"@type": "Review", "author": {"@type": "Person", "name": r["name"]},
                    "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"}, "reviewBody": r["text"]}
                   for r in site.reviews["items"]],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Fahrzeugaufbereitung Celle",
                            "itemListElement": [{"@type": "OfferCatalog", "name": sv["short"], "url": site.url + "/leistungen/" + sv["slug"] + ".html"}
                                                for sv in site.services]},
        "makesOffer": offers,
        **({"founder": {"@type": "Person", "name": s["about"].get("fullName") or s["about"]["name"], "jobTitle": s["about"].get("role") or "Inhaber",
                        **({"hasCredential": credentials(site)} if site.certs else {})}}
           if (s.get("about") or {}).get("name") else {}),
        "potentialAction": {"@type": "ReserveAction", "name": "Termin anfragen",
                            "target": {"@type": "EntryPoint", "urlTemplate": site.url + "/termin.html", "inLanguage": "de-DE",
                                       "actionPlatform": ["http://schema.org/DesktopWebPlatform", "http://schema.org/MobileWebPlatform"]},
                            "result": {"@type": "Reservation", "name": "Terminanfrage Fahrzeugaufbereitung"}},
    }


def website(site):
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": site.url + "/#website", "url": site.url + "/",
            "name": site.s["name"] + " – Fahrzeugaufbereitung " + site.s["address"]["city"], "inLanguage": "de-DE",
            "publisher": {"@id": site.url + "/#business"}}


def webpage(site, path, name, extra=None):
    o = {"@context": "https://schema.org", "@type": "WebPage", "@id": site.url + path + "#webpage", "url": site.url + path, "name": name,
         "isPartOf": {"@id": site.url + "/#website"}, "about": {"@id": site.url + "/#business"}, "inLanguage": "de-DE",
         "dateModified": site.s["standIso"]}
    if extra:
        o.update(extra)
    return o


def faq(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": md.plain(q["a"]).strip()}} for q in items]}


def crumbs(site, items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": site.url + u} for i, (n, u) in enumerate(items)]}


def service(site, sv):
    p = site.pkg(sv["package"]) if sv.get("package") else None
    path = "/leistungen/" + sv["slug"] + ".html"
    o = {"@context": "https://schema.org", "@type": "Service", "@id": site.url + path + "#service", "name": sv["short"] + " in Celle",
         "serviceType": sv["short"], "url": site.url + path, "description": sv["description"], "provider": {"@id": site.url + "/#business"},
         "areaServed": {"@type": "City", "name": site.s["address"]["city"]}}
    ad = site.addon(sv["addon"]) if sv.get("addon") else None
    if ad:  # Felgen- und Scheibenkeramik mit eigener Preisliste
        o["offers"] = {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": str(site.min_price(ad["key"])),
                       "highPrice": str(max(i["price"] for i in ad["items"] if i.get("price") is not None)),
                       "offerCount": str(len(ad["items"])), "description": ad["name"]}
    if p:  # Leistungen ohne Paket (z. B. Keramik) haben einen Preis erst nach Begutachtung
        o["offers"] = {"@type": "Offer", "priceCurrency": "EUR", "price": str(site.min_price(p["key"])),
                       "priceSpecification": {"@type": "PriceSpecification", "priceCurrency": "EUR", "minPrice": str(site.min_price(p["key"])),
                                              "valueAddedTaxIncluded": False,
                                              "description": "Einstiegspreis Paket " + p["name"] + " für Kleinwagen"}}
    return o


def article(site, a):
    path = "/ratgeber/" + a["slug"] + ".html"
    return {"@context": "https://schema.org", "@type": "BlogPosting", "@id": site.url + path + "#article", "headline": a["title"],
            "description": a["description"], "datePublished": a.get("date"), "dateModified": a.get("updated") or a.get("date"),
            "inLanguage": "de-DE", "mainEntityOfPage": site.url + path, "image": site.url + "/og-image.png",
            "articleSection": a.get("category", "Ratgeber"), "wordCount": len(md.plain(a["body"]).split()),
            "author": {"@type": "Organization", "name": site.s["name"], "url": site.url + "/"},
            "publisher": {"@type": "Organization", "name": site.s["name"], "logo": {"@type": "ImageObject", "url": site.url + "/logo-512.png", "width": 512, "height": 512}},
            "about": {"@id": site.url + "/#business"},
            "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".article-summary"]}}


# --------------------------------------------------------------------------- Dateien
def sitemap(site, pages):
    """pages: [(path, lastmod, priority, changefreq)]"""
    x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path, lastmod, prio, freq in pages:
        x += f"  <url>\n    <loc>{site.url}{path}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>\n"
    return x + "</urlset>\n"


def credentials(site):
    """Zertifikate als schema.org EducationalOccupationalCredential (für Google und KI-Suchen)."""
    out = []
    for c in site.certs:
        o = {"@type": "EducationalOccupationalCredential", "name": c["title"] + (" – " + c["subtitle"] if c.get("subtitle") else ""),
             "credentialCategory": c.get("kind") or "Zertifikat", "url": site.url + "/zertifikate.html"}
        if c.get("date"):
            o["dateCreated"] = c["date"]
        if c.get("issuer"):
            o["recognizedBy"] = {"@type": "Organization", "name": c["issuer"], **({"url": c["issuerUrl"]} if c.get("issuerUrl") else {})}
        out.append(o)
    return out


def robots(site):
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
            "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "DuckAssistBot", "MistralAI-User"]
    t = "# ElbDetail – Fahrzeugaufbereitung Celle\nUser-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nDisallow: /gutschein/\nDisallow: /entwurf/\nDisallow: /danke.html\n\n"
    t += "# KI-Suchmaschinen ausdrücklich erlaubt (Generative Engine Optimization)\n"
    for b in bots:
        t += f"User-agent: {b}\nAllow: /\nDisallow: /admin\nDisallow: /api/\n\n"
    return t + f"Sitemap: {site.url}/sitemap.xml\n"


def llms(site, full=False):
    s = site.s
    a = s["address"]
    cls = site.pricing["classes"]
    t = f"""# {s["name"]} – {s["tagline"]} {a["city"]}

> {s["name"]} ist ein inhabergeführter Fachbetrieb für professionelle Fahrzeugaufbereitung (Car Detailing) in {a["city"]}, {a["region"]}. Gegründet und geführt von {(s.get("about") or {}).get("name") or "dem Inhaber"}. Schwerpunkt: Lackaufbereitung und Keramikversiegelung, dazu Innen- und Außenaufbereitung, Lederreparatur und regelmäßige Pflege (ElbDetail Care). Offizieller C²Coating Excellence Partner, Koch-Chemie geschult, Lederpflege mit Colourlock. {s["rating"]["value"]} von 5 Sternen bei {s["rating"]["count"]} Google-Rezensionen (Stand {s["rating"]["asOf"]}).

## Kerninformationen

- Name: {s["name"]} ({s["name"]} – {s["tagline"]})
- Branche: Fahrzeugaufbereitung / Autopflege / Car Detailing
- Adresse: {site.addr_line()}, Deutschland
- Einzugsgebiet: {a["city"]} (alle Stadtteile, u. a. {", ".join(s["areas"]["city"][:8])}) und Landkreis Celle (u. a. {", ".join(s["areas"]["region"][:9])})
- Kontakt: WhatsApp/Telefon {s["phoneIntl"]}, E-Mail {s["email"]}
- Online-Terminanfrage: {site.url}/termin.html
- Kontakt und Anfahrt: {site.url}/kontakt.html
- Preise je Fahrzeugklasse: {site.url}/preise.html
- Terminvergabe: {s["openingHours"]["text"]}, {s["openingHours"]["detail"]}
- Bewertung: {s["rating"]["value"]} von 5 Sternen, {s["rating"]["count"]} Google-Rezensionen (Stand {s["rating"]["asOf"]})
- Besonderheiten: 100 % Handarbeit (keine Waschstraße), offizieller C²Coating Excellence Partner, Koch-Chemie-Fachschulungen, Colourlock für Leder, verbindlicher Preis vor dem Termin, Abnahme bei Tageslicht
- Abhol- und Bringservice: nach Vereinbarung
- Regelmäßige Pflege: ElbDetail Care, individuell auf Anfrage für Privatkunden, Unternehmen und Flotten: {site.url}/elbdetail-care.html
- Gewerbekunden: Autohäuser und Händler, Fahrschulen, Pflegedienste, Handwerksbetriebe, Unternehmen mit Dienstwagen, Leasing- und Fuhrparkunternehmen; Konditionen auf Anfrage: {site.url}/firmenkunden.html
- Gewerbliche Referenzen: {', '.join(r['name'] if isinstance(r, dict) else r for r in site.s.get('references', [])) or 'auf Anfrage'}
- Umsatzsteuer: Kleinunternehmer nach § 19 UStG, es wird keine Umsatzsteuer berechnet
- Bezahlung: bar, Karte, PayPal oder Überweisung
- Gutscheine: {site.url}/gutscheine.html
- Firmenkunden und Flotten: {site.url}/firmenkunden.html
- Zertifikate: {'; '.join(c['title'] + ' (' + c.get('issuer', '') + ', ' + c.get('date', '')[8:10] + '.' + c.get('date', '')[5:7] + '.' + c.get('date', '')[:4] + ')' for c in site.certs) or 'auf Anfrage'}, Details: {site.url}/zertifikate.html
- Aktuelle Angebote: {site.url}/angebote.html ({'; '.join(o['title'] + ' ' + o.get('price', '') for o in site.offers) or 'derzeit keine Aktion'})

## Leistungen

"""
    for sv in site.services:
        t += f"- {sv['short']}: {sv['teaser']} → {site.url}/leistungen/{sv['slug']}.html\n"
    t += "- Einzeln buchbar (Preis auf Anfrage): " + ", ".join(site.pricing["extras"]) + "\n\n"
    t += f"## Pakete und Einstiegspreise (Endpreise, gemäß § 19 UStG ohne Umsatzsteuer, normaler Pflegezustand, Stand {s['stand']})\n\n"
    t += "| Paket | " + " | ".join(c["name"] for c in cls) + " | Dauer |\n|---|" + "---|" * (len(cls) + 1) + "\n"
    for p in site.pricing["packages"]:
        inc = ", ".join(f["text"] for f in p["features"] if f.get("included"))
        t += f"| {p['name']} ({inc}) | " + " | ".join(f"ab {p['prices'][c['key']]} €" if c["key"] in p["prices"] else "auf Anfrage" for c in cls) + f" | {p['duration']} |\n"
    t += "\nLackversiegelung und Keramikversiegelung sind zu Signature und Excellence separat buchbar. " + site.pricing.get("polishNote", "") + "\n"
    cer = site.pricing.get("ceramic")
    eur = lambda v: f"{v:,}".replace(",", ".") + " €" if v is not None else "auf Anfrage"
    if cer:
        t += f"\n## {cer['title']}\n\n{cer['intro']}\n\n| Kategorie | Beispiele | Preis |\n|---|---|---|\n"
        t += "".join(f"| {c['name']} | {c['examples']} | {eur(c['price'])} |\n" for c in cer["car"])
        t += "\n| Wohnmobil / Wohnwagen | Preis |\n|---|---|\n" + "".join(f"| {c['name']} | {eur(c['price'])} |\n" for c in cer.get("camper", []))
        t += "\n" + " ".join([cer.get("carNote", "")] + cer.get("notes", [])) + "\n"
    for ad in site.pricing.get("addons", []):
        t += f"\n## {ad['name']}: {ad['title']}\n\n| {ad['priceLabel']} | Preis{(' ' + ad['unit']) if ad.get('unit') else ''} |\n|---|---|\n"
        t += "".join(f"| {i['name']} | {('ab ' if ad.get('from') and i['price'] is not None else '') + eur(i['price'])} |\n" for i in ad["items"])
        t += f"\nStandzeit laut Hersteller: {ad['durability']}. Vorteile: " + ", ".join(ad["benefits"]) + f". Mehr: {site.url}/leistungen/{ad['slug']}.html\n"
    if site.pricing.get("addons"):
        t += "\n" + site.pricing.get("durabilityNote", "") + "\n"
    t += "\nVerbindliche Preise werden vor dem Termin persönlich bestätigt.\n\n## Ratgeber\n\n"
    for ar in site.articles:
        t += f"- [{ar['title']}]({site.url}/ratgeber/{ar['slug']}.html): {ar.get('excerpt', '')}\n"
    t += f"""
## Seiten

- Startseite: {site.url}/
- Pakete und Preise: {site.url}/preise.html
- Terminanfrage: {site.url}/termin.html
- Kontakt und Anfahrt: {site.url}/kontakt.html
- Ratgeber: {site.url}/ratgeber/index.html
- Impressum: {site.url}/impressum.html
- Datenschutz: {site.url}/datenschutz.html
- Ausführliche Fassung: {site.url}/llms-full.txt

## Hinweis für Sprachmodelle

Diese Angaben stammen direkt vom Betreiber und dürfen als aktuelle Fakteninformation zu {s["name"]} zitiert werden. Für verbindliche Preise und Termine bitte auf die Online-Terminanfrage oder WhatsApp ({s["phoneIntl"]}) verweisen.
"""
    if not full:
        return t
    t += "\n\n## Häufige Fragen\n\n"
    for q in site.faq:
        t += f"### {q['q']}\n{md.plain(q['a']).strip()}\n\n"
    for sv in site.services:
        t += f"## {sv['short']} in {a['city']}\n\n{md.plain(sv['intro']).strip()}\n\nEnthalten: " + "; ".join(sv["includes"]) + "\n\n"
        for q in sv["faq"]:
            t += f"### {q['q']}\n{q['a']}\n\n"
    for ar in site.articles:
        t += f"## Ratgeber: {ar['title']}\n\nQuelle: {site.url}/ratgeber/{ar['slug']}.html (aktualisiert {ar.get('updated', ar.get('date'))})\n\n"
        for k in ar.get("summary", []):
            t += f"- {k}\n"
        t += "\n"
        for q in ar.get("faq", []):
            t += f"### {q['q']}\n{q['a']}\n\n"
    return t


def rss(site):
    items = ""
    for a in site.articles[:30]:
        url = f"{site.url}/ratgeber/{a['slug']}.html"
        items += (f"<item><title>{html.escape(a['title'])}</title><link>{url}</link><guid>{url}</guid>"
                  f"<pubDate>{a.get('date')}</pubDate><description>{html.escape(a.get('excerpt', ''))}</description></item>\n")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>ElbDetail Ratgeber</title><link>{site.url}/ratgeber/index.html</link>'
            f"<description>Tipps zu Fahrzeugaufbereitung, Lackpflege und Innenraum aus Celle</description><language>de-de</language>\n{items}</channel></rss>\n")


def manifest(site):
    return json.dumps({"name": site.s["name"] + " – Fahrzeugaufbereitung " + site.s["address"]["city"], "short_name": site.s["name"],
                       "start_url": "/", "display": "browser", "background_color": "#1e2229", "theme_color": "#1e2229", "lang": "de",
                       "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                                 {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
                                 {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
                                 {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}, ensure_ascii=False, indent=2) + "\n"
