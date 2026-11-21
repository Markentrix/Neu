#!/usr/bin/env python3
"""qa-statisch.py: Qualitäts-Gate für eine statische Kundenwebsite. Aufruf: python3 qa-statisch.py website-fertig
Prüft ohne Netz und ohne Browser: Pflichtangaben je Seite, Überschriften, Links, Bilder, Formulare, Wortwahl, Sitemap, JSON-LD.
Exit-Code 1 bei FEHLER. HINWEIS = ansehen, kein Abbruch."""
import os, re, sys, json, glob, html, collections

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'website-fertig'
errors, notes = [], []
def err(m): errors.append(m)
def note(m): notes.append(m)
def txt(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()

files = sorted(glob.glob(ROOT + '/**/*.html', recursive=True))
if not files: sys.exit('Keine HTML-Dateien in ' + ROOT)
pages = {os.path.relpath(f, ROOT).replace(os.sep, '/'): open(f, encoding='utf-8').read() for f in files}
def exists(p):
    p = p.split('#')[0].split('?')[0]
    if p.startswith('/'): p = p[1:]
    return p == '' or os.path.exists(os.path.join(ROOT, p)) or os.path.exists(os.path.join(ROOT, p, 'index.html')) or os.path.exists(os.path.join(ROOT, p + '.html'))

BAD = ['rechtssicher', 'abmahnsicher', '24/7', 'rund um die Uhr', 'Haftung für Links', 'jederzeit an eine', 'nahtlos', 'ganzheitlich',
       'maßgeschneidert', 'innovativ', 'Ihr Partner für', 'auf das nächste Level', 'Lorem ipsum', 'Platzhalter', 'localhost']
NOINDEX_OK = ('404.html', 'danke.html')
for rel, t in pages.items():
    low = rel in NOINDEX_OK
    main = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<!--.*?-->', '', t, flags=re.S)
    if not re.search(r'<html[^>]*\blang="de"', t): err(f'{rel}: <html lang="de"> fehlt')
    ti = re.search(r'<title>(.*?)</title>', t, re.S)
    if not ti: err(f'{rel}: kein <title>')
    elif len(txt(ti.group(1))) > 60: err(f'{rel}: Title {len(txt(ti.group(1)))} Zeichen (über 60)')
    d = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', t)
    if not low:
        if not d: err(f'{rel}: keine Description')
        elif not 70 <= len(d.group(1)) <= 160: note(f'{rel}: Description {len(d.group(1))} Zeichen (70 bis 160)')
    if 'name="viewport"' not in t: err(f'{rel}: kein viewport')
    if low and 'noindex' not in t: err(f'{rel}: noindex fehlt')
    # Überschriften
    hs = [(int(m.group(1)), txt(m.group(2))) for m in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', main, re.S)]
    h1 = [h for l, h in hs if l == 1]
    if len(h1) != 1: err(f'{rel}: {len(h1)} H1')
    else:
        raw = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', main, re.S).group(1)))  # wie der Browser: Tags ohne Leerzeichen entfernen
        if re.search(r'[a-zäöüß][.!?][A-ZÄÖÜ][a-zäöüß]', raw): err(f'{rel}: H1 ohne Leerzeichen zwischen Sätzen (Unterzeile gehört nicht ins H1): {h1[0][:50]}')
        if len(h1[0]) > 90: err(f'{rel}: H1 {len(h1[0])} Zeichen')
        elif len(h1[0]) > 70: note(f'{rel}: H1 {len(h1[0])} Zeichen (über 70)')
    prev = 0
    for l, h in hs:
        if prev and l > prev + 1: err(f'{rel}: Überschriftenebene übersprungen (H{prev} auf H{l}: {h[:40]})')
        prev = l
    if '<main' not in t: note(f'{rel}: kein <main>')
    # Pflichtlinks auf jeder Seite
    for pf in ('impressum', 'datenschutz'):
        if not re.search(r'href="[^"]*' + pf + r'(\.html)?(#[^"]*)?"', t): err(f'{rel}: kein Link auf {pf}')
    # Bilder
    for im in re.findall(r'<img[^>]*>', main):
        if 'alt=' not in im: err(f'{rel}: Bild ohne alt: {im[:60]}')
        elif re.search(r'alt=""', im) and 'aria-hidden' not in im: note(f'{rel}: Bild mit leerem alt ohne aria-hidden')
        if not (re.search(r'\bwidth=', im) and re.search(r'\bheight=', im)): err(f'{rel}: Bild ohne width/height: {im[:60]}')
    # Links
    seen = collections.defaultdict(set)
    for m in re.finditer(r'<a ([^>]*)href="([^"#][^"]*|#[^"]+)"([^>]*)>(.*?)</a>', main, re.S):
        a, href, text = m.group(1) + m.group(3), m.group(2), txt(m.group(4))
        if re.match(r'(https?:|mailto:|tel:|javascript:)', href):
            if 'target="_blank"' in a and 'noopener' not in a: err(f'{rel}: target=_blank ohne rel=noopener: {href[:50]}')
            if href.startswith('http://') and 'localhost' not in href: note(f'{rel}: unsichere http-Adresse: {href[:50]}')
            continue
        if href.startswith('#'):
            if f'id="{href[1:]}"' not in t: err(f'{rel}: Anker fehlt {href}')
            continue
        base = os.path.dirname(rel)
        target = href if href.startswith('/') else os.path.normpath(os.path.join(base, href)).replace(os.sep, '/')
        if not exists(target): err(f'{rel}: toter Link {href}')
        if '?' in href.split('#')[0] and 'nofollow' not in a: err(f'{rel}: Link mit Parameter ohne rel="nofollow": {href}')
        if len(text) > 90: note(f'{rel}: sehr langer Linktext ({len(text)}): {text[:40]}… (nur die Überschrift verlinken)')
        if text: seen[text.lower()].add(href.split('#')[0])
    for k, v in seen.items():
        if len(v) > 1: note(f'{rel}: gleicher Linktext „{k[:30]}“ mit {len(v)} Zielen')
    # Formulare
    for fm in re.finditer(r'<form[^>]*>(.*?)</form>', main, re.S):
        f = fm.group(1)
        if not re.search(r'type="(email|tel)"|name="(email|telefon|tel|name)"', f): continue  # Suche, Filter und ähnliche Formulare ohne persönliche Daten
        if not re.search(r'name="einwilligung"[^>]*required|required[^>]*name="einwilligung"', f): err(f'{rel}: Formular ohne Pflicht-Einwilligung (name="einwilligung")')
        if not re.search(r'href="[^"]*datenschutz', f): err(f'{rel}: Formular ohne Datenschutz-Link in der Einwilligung')
    # Wortwahl (Rechtstexte ausgenommen)
    if rel not in ('impressum.html', 'datenschutz.html', 'agb.html'):
        body = txt(main)
        for p in BAD:
            if re.search(re.escape(p), body, re.I): err(f'{rel}: „{p}“ (Zusage, Floskel oder Platzhalter)')
        if re.search(r'(?<!Ist das alles )DSGVO-konform(?!\?)', body): err(f'{rel}: „DSGVO-konform“ als Zusage')
    # JSON-LD
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try: json.loads(m.group(1))
        except Exception as e: err(f'{rel}: JSON-LD ungültig ({e})')
        if 'aggregateRating' in m.group(1): err(f'{rel}: aggregateRating im JSON-LD (nicht erlaubt ohne echte Quelle)')

# Pflichtdateien, Sitemap
for must in ('index.html', 'impressum.html', 'datenschutz.html', '404.html', 'robots.txt', 'sitemap.xml'):
    if not os.path.exists(os.path.join(ROOT, must)): err(f'Datei fehlt: {must}')
sm = os.path.join(ROOT, 'sitemap.xml')
if os.path.exists(sm):
    locs = re.findall(r'<loc>(.*?)</loc>', open(sm, encoding='utf-8').read())
    for l in locs:
        p = re.sub(r'^https?://[^/]+', '', l) or '/'
        if not exists(p): err(f'Sitemap-URL ohne Seite: {l}')
        if any(p.endswith(n) or p.endswith(n[:-5]) for n in NOINDEX_OK): err(f'noindex-Seite in der Sitemap: {l}')
    note(f'Sitemap: {len(locs)} Adressen')

for n in sorted(set(notes)): print('HINWEIS', n)
for e in errors: print('FEHLER ', e)
print(f'{len(pages)} Seiten: {len(errors)} Fehler, {len(set(notes))} Hinweise')
sys.exit(1 if errors else 0)
