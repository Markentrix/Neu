"""SEO- und GEO-Bausteine: strukturierte Daten (Schema.org), Sitemap, robots, llms.txt, Weiterleitungen, OG-Bilder."""
import json, re, html, os
from datetime import date

DOMAIN = 'https://motorradhandel-celle.de'
TODAY = date.today().isoformat()
BIZ_ID = DOMAIN + '/#business'
SITE_ID = DOMAIN + '/#website'
OWNER_ID = DOMAIN + '/#inhaber'

def url(fn):
    fn = fn.replace('index.html', '')
    return DOMAIN + '/' + fn

def strip(h):
    t = re.sub(r'<[^>]+>', '', h); return re.sub(r'\s+', ' ', html.unescape(t)).strip()

def business(bikes_n):
    return {
        '@type': ['MotorcycleDealer', 'LocalBusiness'], '@id': BIZ_ID, 'name': 'Motorradhandel-Celle',
        'alternateName': ['Motorradhandel Celle', 'Motorradhandel-Celle.de'], 'url': DOMAIN + '/',
        'description': 'Motorradhändler in Celle-Altenhagen: gebrauchte Motorräder und Roller (Honda, Yamaha, Suzuki, Kawasaki, BMW, Triumph, Piaggio), Probefahrt nach Terminabsprache, Ankauf, Inzahlungnahme, Finanzierung auf Anfrage und Winterlager.',
        'image': [DOMAIN + '/assets/og/default.jpg'],
        'telephone': '+49 1520 8880000', 'email': 'vollcool007@web.de', 'vatID': 'DE174231599',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Lachtehäuserstraße 6', 'postalCode': '29223', 'addressLocality': 'Celle', 'addressRegion': 'Niedersachsen', 'addressCountry': 'DE'},
        'areaServed': [{'@type': 'City', 'name': n} for n in ('Celle', 'Hannover', 'Hamburg', 'Uelzen')] + [{'@type': 'AdministrativeArea', 'name': 'Niedersachsen'}],
        'founder': {'@id': OWNER_ID}, 'numberOfEmployees': {'@type': 'QuantitativeValue', 'value': 5},
        'knowsAbout': ['Gebrauchte Motorräder', 'Motorrad kaufen', 'Motorrad verkaufen', 'Motorrad Inzahlungnahme', 'Motorrad überwintern', 'Motorrad Import', 'Honda', 'Yamaha', 'Suzuki', 'Kawasaki', 'BMW', 'Triumph'],
        'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': 'Leistungen', 'itemListElement': [
            {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': n, 'url': u}} for n, u in [
                ('Gebrauchte Motorräder kaufen', DOMAIN + '/motorraeder.html'), ('Motorrad verkaufen und Ankauf', DOMAIN + '/ankauf.html'),
                ('Motorrad überwintern (Winterlager)', DOMAIN + '/ueberwintern.html'), ('Inzahlungnahme', DOMAIN + '/service.html#inzahlungnahme'),
                ('Finanzierung auf Anfrage', DOMAIN + '/service.html#finanzierung'), ('Kommissionsverkauf', DOMAIN + '/service.html#kommission'),
                ('Import und Wunschsuche', DOMAIN + '/service.html#import')]]},
    }

def owner():
    return {'@type': 'Person', '@id': OWNER_ID, 'name': 'Ingo Werner', 'jobTitle': 'Inhaber', 'worksFor': {'@id': BIZ_ID}}

def website():
    return {'@type': 'WebSite', '@id': SITE_ID, 'url': DOMAIN + '/', 'name': 'Motorradhandel-Celle', 'inLanguage': 'de-DE', 'publisher': {'@id': BIZ_ID}}

def breadcrumb(fn, crumbs):
    items = [{'@type': 'ListItem', 'position': 1, 'name': 'Start', 'item': DOMAIN + '/'}]
    for i, (name, link) in enumerate(crumbs, 2):
        items.append({'@type': 'ListItem', 'position': i, 'name': name, 'item': url(link) if link else url(fn)})
    return {'@type': 'BreadcrumbList', '@id': url(fn) + '#breadcrumb', 'itemListElement': items}

def webpage(fn, kind, title, desc, image, has_crumbs, extra=None):
    d = {'@type': kind, '@id': url(fn) + '#webpage', 'url': url(fn), 'name': title, 'description': desc, 'inLanguage': 'de-DE',
         'isPartOf': {'@id': SITE_ID}, 'about': {'@id': BIZ_ID}, 'dateModified': TODAY,
         'primaryImageOfPage': {'@type': 'ImageObject', 'url': image}}
    if has_crumbs: d['breadcrumb'] = {'@id': url(fn) + '#breadcrumb'}
    if extra: d.update(extra)
    return d

def faq(fn, qa):
    ents = [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': strip(a)}} for q, a in qa if 'ph-note' not in a]
    return {'@type': 'FAQPage', '@id': url(fn) + '#faq', 'mainEntity': ents} if ents else None

def itemlist(fn, items):
    return {'@type': 'ItemList', '@id': url(fn) + '#liste', 'numberOfItems': len(items), 'itemListElement': [{'@type': 'ListItem', 'position': i, 'url': url(u), 'name': n} for i, (n, u) in enumerate(items, 1)]}

def product(b, fn, images, desc):
    return {'@type': ['Product', 'Motorcycle'], '@id': url(fn) + '#produkt', 'name': b['name'], 'description': desc, 'sku': b['slug'],
            'brand': {'@type': 'Brand', 'name': b['brand']}, 'model': b['model'], 'url': url(fn), 'image': images,
            'itemCondition': 'https://schema.org/UsedCondition',
            'dateVehicleFirstRegistered': f"{b['ez'][3:]}-{b['ez'][:2]}", 'vehicleModelDate': str(b['year']),
            'mileageFromOdometer': {'@type': 'QuantitativeValue', 'value': b['km'], 'unitCode': 'KMT'},
            'offers': {'@type': 'Offer', 'url': url(fn), 'price': str(b['price']), 'priceCurrency': 'EUR', 'itemCondition': 'https://schema.org/UsedCondition', 'seller': {'@id': BIZ_ID}}}

def service(fn, name, desc, stype):
    return {'@type': 'Service', '@id': url(fn) + '#leistung', 'name': name, 'serviceType': stype, 'description': desc, 'url': url(fn),
            'provider': {'@id': BIZ_ID}, 'areaServed': [{'@type': 'City', 'name': 'Celle'}, {'@type': 'AdministrativeArea', 'name': 'Niedersachsen'}]}

def article(fn, headline, desc, image):
    return {'@type': 'Article', '@id': url(fn) + '#artikel', 'headline': headline, 'description': desc, 'inLanguage': 'de-DE',
            'datePublished': TODAY, 'dateModified': TODAY, 'image': image, 'mainEntityOfPage': {'@id': url(fn) + '#webpage'},
            'author': {'@id': BIZ_ID}, 'publisher': {'@id': BIZ_ID}}

def graph(nodes):
    return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': [n for n in nodes if n]}, ensure_ascii=False, separators=(',', ':')) + '</script>\n'

# ---------- Dateien ----------
def sitemap(pages):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for p in pages:
        out.append(f'<url><loc>{url(p["fn"])}</loc><lastmod>{TODAY}</lastmod>')
        for im in p.get('images', []): out.append(f'<image:image><image:loc>{DOMAIN}/assets/img/{im}</image:loc></image:image>')
        out.append('</url>')
    out.append('</urlset>'); return '\n'.join(out) + '\n'

def robots(live):
    if not live: return 'User-agent: *\nDisallow: /\n# Demo: nicht indexieren.\n'
    return f'''# Suchmaschinen und KI-Suche dürfen alles Öffentliche lesen.
User-agent: *
Allow: /
Disallow: /danke.html
Disallow: /merkliste.html

# KI-Such- und Antwortdienste ausdrücklich erlaubt (Entscheidung des Inhabers; Training separat sperrbar, z. B. GPTBot, Google-Extended, CCBot).
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: GPTBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
'''

OLD = {  # alte Seite -> neue Seite (301)
 'Seite5.html': 'ueber-uns.html', 'Seite8.html': 'impressum.html', 'Seite21.html': 'motorraeder.html', 'Seite22.html': 'kontakt.html',
 'Seite29.html': 'fahrzeug/honda-cbr600rr-2004.html', 'Seite32.html': 'fahrzeug/honda-cbr1000rr-2006.html', 'Seite33.html': 'fahrzeug/honda-varadero-xl1000v.html',
 'Seite36.html': 'fahrzeug/yamaha-yzf-r1-2000.html', 'Seite40.html': 'fahrzeug/suzuki-gsxr750-k5.html', 'Seite44.html': 'fahrzeug/triumph-speed-triple-955.html',
 'Seite45.html': 'motorraeder.html', 'Seite48.html': 'fahrzeug/kawasaki-zx10r-2005.html', 'Seite49.html': 'ankauf.html', 'Seite50.html': 'fahrzeug/suzuki-gsxr750-k1.html',
 'Seite51.html': 'motorraeder.html', 'Seite52.html': 'fahrzeug/bmw-f650-cr.html', 'Seite53.html': 'service.html', 'Seite56.html': 'fahrzeug/kawasaki-z1000-2015.html',
 'Seite57.html': 'fahrzeug/honda-crf1000-dct-a.html', 'Seite58.html': 'fahrzeug/honda-crf1000-dct-b.html', 'Seite63.html': 'motorraeder.html', 'Seite64.html': 'fahrzeug/piaggio-hexagon-sport.html',
 'Seite65.html': 'fahrzeug/yamaha-yzf-r6-silver.html', 'Seite68.html': 'motorraeder.html', 'Seite72.html': 'fahrzeug/kawasaki-z1000-abs.html', 'Seite75.html': 'fahrzeug/piaggio-hexagon-lx.html'}

def redirects():
    lines = ['# Alte URLs der bisherigen Website -> neue Seiten (301). Format: Netlify _redirects']
    for o, n in OLD.items(): lines.append(f'/{o} /{n} 301')
    lines.append('/index.html / 301'); lines.append('/* /404.html 404')
    return '\n'.join(lines) + '\n'

def headers(live):
    base = '''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
  X-Frame-Options: DENY
  Strict-Transport-Security: max-age=63072000; includeSubDomains
/assets/*
  Cache-Control: public, max-age=31536000, immutable
'''
    return base if live else base.replace('/*\n', '/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n', 1)

def llms(bikes, cats, guides):
    L = ['# Motorradhandel-Celle', '',
         '> Motorradhändler in Celle-Altenhagen (Niedersachsen). Gebrauchte Motorräder und Roller kaufen, Probefahrt nach Terminabsprache, Motorrad verkaufen (Ankauf, Inzahlungnahme, Kommission), Finanzierung auf Anfrage, Motorrad überwintern (Winterlager) sowie Import und Wunschsuche. Inhaber: Ingo Werner, Bikerteam mit 17 Jahren Erfahrung.', '',
         '## Kontakt und Standort', f'- Adresse: Lachtehäuserstraße 6, 29223 Celle (Altenhagen), Deutschland', '- Telefon: +49 1520 8880000 (auch abends und am Wochenende, Termin absprechen)', '- E-Mail: vollcool007@web.de', f'- Website: {DOMAIN}/', '- Einzugsgebiet: Celle, Hannover, Hamburg, Uelzen, Niedersachsen', '',
         '## Wichtige Seiten',
         f'- [Gebrauchte Motorräder im Bestand]({DOMAIN}/motorraeder.html): aktueller Bestand mit Preis, Erstzulassung und Kilometerstand',
         f'- [Motorrad überwintern: Winterlager]({DOMAIN}/ueberwintern.html): Winterplatz anfragen, im Winter verkaufen oder im Frühjahr wechseln',
         f'- [Motorrad verkaufen: Ankauf]({DOMAIN}/ankauf.html): Ankauf von Aprilia bis Zündapp, Inzahlungnahme, Kommission',
         f'- [Service und Finanzierung]({DOMAIN}/service.html)', f'- [Über uns]({DOMAIN}/ueber-uns.html)', f'- [Kontakt und Probefahrt]({DOMAIN}/kontakt.html)', '',
         '## Ratgeber'] + [f'- [{n}]({DOMAIN}/{u})' for n, u in guides] + ['', '## Bestand nach Marke und Art'] + [f'- [{n}]({DOMAIN}/{u})' for n, u in cats] + ['', '## Aktuelle Fahrzeuge (Preis in Euro, VB = Verhandlungsbasis)']
    for b in bikes:
        L.append(f'- [{b["name"]}]({DOMAIN}/fahrzeug/{b["slug"]}.html): Erstzulassung {b["ez"]}, {b["km"]:,} km, {b["price"]:,} € VB'.replace(',', '.'))
    L += ['', '## Hinweise', '- Preise und Bestand wechseln laufend, Zwischenverkauf ist möglich. Verfügbarkeit bitte telefonisch bestätigen.', f'- Stand dieser Datei: {TODAY}', '']
    return '\n'.join(L)
