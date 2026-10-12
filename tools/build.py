#!/usr/bin/env python3
"""Markentrix · statischer Build.

    python3 tools/build.py          # baut dist/
    python3 tools/build.py --check  # baut und prüft interne Links/Anker

Quellen:
  src/layout.html        gemeinsames Gerüst (Header, Footer, Modal)
  src/pages/**/*.html    eine Datei je Seite: Front-Matter (--- … ---) + Inhalt von <main>
  src/partials/*.html    wiederverwendbare Bausteine, im Inhalt per {{> name}} einbinden
  static/                wird 1:1 nach dist/ kopiert (assets, fonts, img, robots.txt, _headers …)

Front-Matter-Schlüssel: title, description, path (URL-Pfad, z. B. /preise), robots,
og_type, body_class, lastmod (YYYY-MM-DD), sitemap (true/false), ld (JSON-LD-Block),
head_extra (zusätzliche Head-Zeilen).
"""
import json, os, re, shutil, sys, time, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, STATIC, DIST = (os.path.join(ROOT, p) for p in ('src', 'static', 'dist'))
SITE = 'https://markentrix.de'
BUILD = time.strftime('%Y%m%d%H%M')

LOGO = ('<svg viewBox="0 0 48 48" fill="none" aria-hidden="true"><defs><linearGradient id="mxg{n}" x1="9" y1="40" x2="39" y2="9" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#28C7F7"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>'
        '<path d="M11 38V13.5L23.5 26.5L31 18.5" stroke="url(#mxg{n})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M31 38V18.5" stroke="url(#mxg{n})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M31 18.5L37 12.5M37 12.5L30.5 12.5M37 12.5L37 19" stroke="url(#mxg{n})" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>')

FM_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.S)


def parse_front_matter(text):
    m = FM_RE.match(text)
    if not m:
        raise SystemExit('Front-Matter fehlt')
    meta, body = {}, text[m.end():]
    key, buf = None, []
    for line in m.group(1).split('\n'):
        if key and (line.startswith('  ') or line.strip() == '' and buf):
            buf.append(line[2:] if line.startswith('  ') else '')
            continue
        if key:
            meta[key] = '\n'.join(buf).strip() if buf else meta[key]
        key, buf = None, []
        if ':' in line:
            k, v = line.split(':', 1)
            key, v = k.strip(), v.strip()
            if v == '|':
                buf = []
                meta[key] = ''
            else:
                meta[key] = v
                key = None
    if key:
        meta[key] = '\n'.join(buf).strip()
    return meta, body


def load_partials():
    parts = {}
    pdir = os.path.join(SRC, 'partials')
    if os.path.isdir(pdir):
        for f in os.listdir(pdir):
            if f.endswith('.html'):
                parts[f[:-5]] = open(os.path.join(pdir, f), encoding='utf-8').read().strip()
    return parts


def render(layout, meta, body, partials):
    def sub_partials(s):
        return re.sub(r'\{\{>\s*([\w-]+)\s*\}\}', lambda m: partials.get(m.group(1), f'<!-- partial {m.group(1)} fehlt -->'), s)
    body = sub_partials(body)
    path = meta.get('path', '/')
    canonical = SITE + ('' if path == '/' else path)
    ld = meta.get('ld', '').strip()
    if ld:
        json.loads(ld)  # validieren
        ld = '<script type="application/ld+json">' + ld + '</script>'
    vals = {
        'title': html.escape(meta['title'], quote=True),
        'description': html.escape(meta['description'], quote=True),
        'canonical': canonical,
        'robots': meta.get('robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1'),
        'og_type': meta.get('og_type', 'website'),
        'body_class': meta.get('body_class', ''),
        'head_extra': meta.get('head_extra', ''),
        'ld_json': ld,
        'content': body,
        'build': BUILD,
    }
    out = layout
    n = [0]
    def logo(_):
        n[0] += 1
        return LOGO.format(n=n[0])
    out = re.sub(r'\{\{logo\}\}', logo, out)
    out = sub_partials(out)
    for k, v in vals.items():
        out = out.replace('{{' + k + '}}', v)
    left = re.findall(r'\{\{[^}]+\}\}', out)
    if left:
        raise SystemExit(f'Unaufgelöste Platzhalter in {path}: {left[:5]}')
    return out


def build(check=False):
    layout = open(os.path.join(SRC, 'layout.html'), encoding='utf-8').read()
    partials = load_partials()
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)
    pages = []
    for dirpath, _, files in os.walk(os.path.join(SRC, 'pages')):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            src = os.path.join(dirpath, f)
            meta, body = parse_front_matter(open(src, encoding='utf-8').read())
            rel = os.path.relpath(src, os.path.join(SRC, 'pages'))
            meta.setdefault('path', '/' if rel == 'index.html' else '/' + rel[:-5])
            out_path = os.path.join(DIST, rel)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            html_out = render(layout, meta, body, partials)
            open(out_path, 'w', encoding='utf-8').write(html_out)
            pages.append((meta, rel, html_out))
    # Sitemap
    urls = []
    for meta, rel, _ in pages:
        if meta.get('sitemap', 'true').lower() == 'false' or 'noindex' in meta.get('robots', ''):
            continue
        loc = SITE + ('' if meta['path'] == '/' else meta['path'])
        urls.append(f'  <url><loc>{loc}</loc><lastmod>{meta.get("lastmod", time.strftime("%Y-%m-%d"))}</lastmod></url>')
    open(os.path.join(DIST, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>\n')
    print(f'{len(pages)} Seiten gebaut, {len(urls)} in der Sitemap → dist/')
    if check:
        return check_links(pages)
    return 0


def check_links(pages):
    known = {'/': 'index.html'}
    ids = {}
    for meta, rel, out in pages:
        known[meta['path']] = rel
        ids[meta['path']] = set(re.findall(r'\sid="([^"]+)"', out))
    for dirpath, _, files in os.walk(DIST):
        for f in files:
            p = '/' + os.path.relpath(os.path.join(dirpath, f), DIST).replace(os.sep, '/')
            known[p] = f
    errors = 0
    for meta, rel, out in pages:
        for href in re.findall(r'(?:href|src)="([^"]+)"', out):
            if href.startswith(('http', 'mailto:', 'tel:', 'data:', '//')):
                continue
            h = href.split('?')[0]
            target, _, frag = h.partition('#')
            if target == '':
                target = meta['path']
            if target not in known:
                print(f'  ✗ {meta["path"]}: Link-Ziel fehlt: {href}'); errors += 1; continue
            if frag and target in ids and frag not in ids[target] and frag not in ('main', 'cookie-einstellungen', 'potenzial-check'):
                print(f'  ✗ {meta["path"]}: Anker fehlt: {href}'); errors += 1
        h1 = re.findall(r'<h1[\s>]', out)
        if len(h1) != 1:
            print(f'  ✗ {meta["path"]}: {len(h1)} h1-Elemente'); errors += 1
        if len(meta['title']) > 65:
            print(f'  ! {meta["path"]}: Titel {len(meta["title"])} Zeichen')
        if len(meta['description']) > 165:
            print(f'  ! {meta["path"]}: Description {len(meta["description"])} Zeichen')
    print('Linkcheck: ' + ('ok' if not errors else f'{errors} Fehler'))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(build(check='--check' in sys.argv))
