#!/usr/bin/env python3
"""SEO-/GEO-Prüfer. Aufruf: python3 check_seo.py <ordner> [--live] [--domain=https://kunde.de]   (ohne --live wird noindex erwartet)"""
import re, os, sys, json, glob, html
from urllib.parse import urlparse
root = next((a for a in sys.argv[1:] if not a.startswith('--')), '.'); live = '--live' in sys.argv
os.chdir(root)
DOMAIN = next((a.split('=', 1)[1].rstrip('/') for a in sys.argv if a.startswith('--domain=')), 'https://motorradhandel-celle.de')
fails, warns = [], []
F = lambda p, m: fails.append(f'{p}: {m}'); W = lambda p, m: warns.append(f'{p}: {m}')
pages = sorted(glob.glob('*.html') + glob.glob('*/*.html'))
pages = [p for p in pages if not p.startswith(('build/', 'preview/', 'live/', 'assets/'))]
titles, descs, ids_all = {}, {}, {}
for p in pages:
    s = open(p, encoding='utf-8').read(); base = os.path.dirname(p)
    url = DOMAIN + '/' + ('' if p == 'index.html' else p)
    t = re.search(r'<title>(.*?)</title>', s, re.S); t = html.unescape(t.group(1)).strip() if t else ''
    d = re.search(r'<meta name="description" content="([^"]*)"', s); d = html.unescape(d.group(1)) if d else ''
    if not t: F(p, 'Title fehlt')
    elif len(t) > 60: W(p, f'Title {len(t)} Zeichen (>60)')
    elif len(t) < 25: W(p, f'Title nur {len(t)} Zeichen')
    if not d: F(p, 'Meta-Description fehlt')
    elif not 110 <= len(d) <= 160: W(p, f'Description {len(d)} Zeichen (110-160)')
    titles.setdefault(t, []).append(p); descs.setdefault(d, []).append(p)
    h1 = len(re.findall(r'<h1[ >]', s)); 
    if h1 != 1: F(p, f'{h1} <h1>')
    # Überschriften-Reihenfolge
    lv = [int(x) for x in re.findall(r'<h([1-6])[ >]', s)]
    for a, b in zip(lv, lv[1:]):
        if b > a + 1: W(p, f'Überschriften springen h{a} -> h{b}'); break
    can = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    if not can: F(p, 'Canonical fehlt')
    elif can.group(1) != url: F(p, f'Canonical {can.group(1)} != {url}')
    rob = re.search(r'<meta name="robots" content="([^"]+)"', s); rob = rob.group(1) if rob else ''
    noidx = p in ('danke.html', '404.html')
    if live and not noidx and 'noindex' in rob: F(p, 'Live-Build mit noindex')
    if live and noidx and 'noindex' not in rob: F(p, 'danke/404 muss noindex sein')
    if not live and 'noindex' not in rob: F(p, 'Demo ohne noindex')
    for k in ('og:title', 'og:description', 'og:url', 'og:image', 'og:type', 'twitter:card', 'twitter:image'):
        if k not in s: F(p, f'{k} fehlt')
    m = re.search(r'<meta property="og:image" content="([^"]+)"', s)
    if m and not os.path.exists(m.group(1).replace(DOMAIN + '/', '')): F(p, 'og:image Datei fehlt')
    if '<html lang="de"' not in s: F(p, 'lang fehlt')
    if 'name="viewport"' not in s: F(p, 'viewport fehlt')
    for im in re.findall(r'<img\b[^>]*>', s):
        if ' alt=' not in im: F(p, 'img ohne alt')
        if ' width=' not in im or ' height=' not in im: W(p, 'img ohne width/height')
    # JSON-LD
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not blocks: F(p, 'kein JSON-LD')
    nodes = []
    for b in blocks:
        try: g = json.loads(b)
        except Exception as e: F(p, f'JSON-LD ungültig: {e}'); continue
        nodes += g.get('@graph', [g])
    defined = {n.get('@id') for n in nodes if '@id' in n}
    def refs(o):
        if isinstance(o, dict):
            if set(o) == {'@id'}: yield o['@id']
            for v in o.values(): yield from refs(v)
        elif isinstance(o, list):
            for v in o: yield from refs(v)
    for r in set(refs(nodes)):
        if r not in defined: F(p, f'JSON-LD-Referenz ohne Knoten: {r}')
    types = {t for n in nodes for t in (n['@type'] if isinstance(n['@type'], list) else [n['@type']])}
    for need in ('LocalBusiness', 'WebSite', 'WebPage' if not any(x in types for x in ('CollectionPage', 'ItemPage', 'AboutPage', 'ContactPage', 'Article')) else 'BreadcrumbList'):
        pass
    if p.startswith('fahrzeug/'):
        pr = [n for n in nodes if 'Product' in (n['@type'] if isinstance(n['@type'], list) else [n['@type']])]
        if not pr: F(p, 'Product fehlt')
        else:
            o = pr[0].get('offers', {})
            for k in ('price', 'priceCurrency'):
                if k not in o: F(p, f'Offer.{k} fehlt')
            if str(pr[0].get('offers', {}).get('price')) not in re.sub(r'[.]', '', s): W(p, 'Preis im Schema nicht auf der Seite')
        if 'BreadcrumbList' not in types: F(p, 'BreadcrumbList fehlt')
    if p != 'index.html' and not noidx and p not in ('impressum.html', 'datenschutz.html') and 'BreadcrumbList' not in types: W(p, 'BreadcrumbList fehlt')
    if 'FAQPage' in types:
        faq = [n for n in nodes if n['@type'] == 'FAQPage'][0]
        for e in faq['mainEntity']:
            if e['acceptedAnswer']['text'][:25] not in re.sub(r'<[^>]+>', '', html.unescape(s)): W(p, f"FAQ-Antwort nicht sichtbar: {e['name'][:40]}")
    # Links
    ids = set(re.findall(r'\sid="([^"]+)"', s)); ids_all[p] = ids
    for h in re.findall(r'(?:href|src|action|data-next)="([^"#][^"]*)"', s):
        if h.startswith(('http', 'mailto:', 'tel:', 'data:', '//')): continue
        f = h.split('#')[0].split('?')[0]
        if f and not os.path.exists(os.path.normpath(os.path.join(base, f))): F(p, f'toter Link {h}')
    if 'class="ph-note"' in s and live: W(p, 'Platzhalter im Live-Build')
for t, ps in titles.items():
    if len(ps) > 1 and t: F(','.join(ps), 'doppelter Title')
for d, ps in descs.items():
    if len(ps) > 1 and d: F(','.join(ps), 'doppelte Description')
for p in pages:  # Anker
    s = open(p, encoding='utf-8').read(); base = os.path.dirname(p)
    for f, a in re.findall(r'href="([^"#?]*\.html)#([^"]+)"', s):
        t = os.path.normpath(os.path.join(base, f))
        if a not in ids_all.get(t, set()): F(p, f'toter Anker {f}#{a}')
# Sitemap
if not os.path.exists('sitemap.xml'): F('sitemap.xml', 'fehlt')
else:
    sm = open('sitemap.xml').read(); locs = re.findall(r'<loc>([^<]+)</loc>', sm)
    for l in locs:
        if l.startswith(DOMAIN + '/assets/'): continue
        path = l.replace(DOMAIN + '/', '') or 'index.html'
        if not os.path.exists(path): F('sitemap.xml', f'URL ohne Datei: {l}')
        if path in ('danke.html', '404.html'): F('sitemap.xml', f'noindex-Seite in Sitemap: {l}')
    for im in re.findall(r'<image:loc>([^<]+)</image:loc>', sm):
        if not os.path.exists(im.replace(DOMAIN + '/', '')): F('sitemap.xml', f'Bild fehlt: {im}')
    need = [p for p in pages if p not in ('danke.html', '404.html')]
    miss = [p for p in need if (DOMAIN + '/' + ('' if p == 'index.html' else p)) not in locs]
    if miss: W('sitemap.xml', f'{len(miss)} Seiten fehlen: {miss[:3]}')
# robots, llms, redirects
rb = open('robots.txt').read() if os.path.exists('robots.txt') else ''
if live and ('Sitemap:' not in rb or 'Disallow: /\n' in rb.replace('Disallow: /danke.html\n', '')): F('robots.txt', 'Live-robots erlaubt nicht alles oder ohne Sitemap')
if not live and 'Disallow: /' not in rb: F('robots.txt', 'Demo-robots muss sperren')
if os.path.exists('llms.txt'):
    for l in re.findall(r'\]\((https://motorradhandel-celle\.de/[^)#]*)', open('llms.txt').read()):
        path = l.replace(DOMAIN + '/', '') or 'index.html'
        if not os.path.exists(path): F('llms.txt', f'toter Link {l}')
else: F('llms.txt', 'fehlt')
if os.path.exists('_redirects'):
    for line in open('_redirects'):
        parts = line.split()
        if len(parts) >= 3 and parts[2] == '301' and parts[1] != '/' and not os.path.exists(parts[1].lstrip('/').split('#')[0]): F('_redirects', f'Ziel fehlt {parts[1]}')
print(f'{len(pages)} Seiten geprüft ({"LIVE" if live else "DEMO"})')
for w in warns: print('WARN ', w)
for f in fails: print('FAIL ', f)
print(f'Ergebnis: {len(fails)} FAIL, {len(warns)} WARN'); sys.exit(1 if fails else 0)
