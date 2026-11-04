#!/usr/bin/env python3
"""SEO-Regressionsprüfung für dist/ (und optional die Live-Seite).

Aufruf:
  python3 tools/seo_audit.py            # prüft dist/ offline, Exit-Code 1 bei Fehlern
  python3 tools/seo_audit.py --live     # prüft zusätzlich https://markentrix.de (nur lesende GET/HEAD)
  python3 tools/seo_audit.py --table    # gibt eine Seitentabelle aus (URL, Title, H1, Canonical, Robots, eingehende Links)

Geprüft wird (Fehler = Exit 1, Hinweis = nur Ausgabe):
  Fehler: fehlender/abweichender Canonical, Canonical nicht https://markentrix.de ohne .html und ohne Slash,
          Sitemap-Eintrag ohne Datei / mit noindex / mit abweichendem Canonical / doppelt,
          indexierbare Seite fehlt in der Sitemap, noindex-Seite in der Sitemap,
          fehlender oder doppelter Title / Meta Description, nicht genau eine h1, Bild ohne alt-Attribut,
          ungültiges JSON-LD, JSON-LD-URL mit fremder Domain, interner Link ins Leere oder auf .html / http / www,
          robots.txt sperrt eine Sitemap-URL, Sitemap-Zeile in robots.txt fehlt, hreflang ohne mehrsprachige Seiten.
  Hinweis: Seiten mit weniger als zwei eingehenden internen Links, Title > 65, Description > 160 oder < 70 Zeichen.
"""
import html as html_mod, json, re, sys, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urljoin

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
SITE = 'https://markentrix.de'


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''; self._t = False; self.meta = {}; self.canon = []; self.h1 = []; self._h1 = False
        self.links = []; self.imgs_noalt = []; self.ld = []; self._ld = False; self.hreflang = []; self.lang = None
        self.ogurl = None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'title': self._t = True
        elif tag == 'meta':
            n = a.get('name') or a.get('property')
            if n: self.meta[n.lower()] = a.get('content', '')
        elif tag == 'link':
            rel = (a.get('rel') or '').lower()
            if rel == 'canonical': self.canon.append(a.get('href'))
            if rel == 'alternate' and a.get('hreflang'): self.hreflang.append(a.get('hreflang'))
        elif tag == 'h1': self._h1 = True; self.h1.append('')
        elif tag == 'a' and a.get('href') is not None: self.links.append(a['href'])
        elif tag == 'img' and 'alt' not in a: self.imgs_noalt.append(a.get('src', '?'))
        elif tag == 'script' and a.get('type') == 'application/ld+json': self._ld = True; self.ld.append('')

    def handle_endtag(self, tag):
        if tag == 'title': self._t = False
        if tag == 'h1': self._h1 = False
        if tag == 'script': self._ld = False

    def handle_data(self, d):
        if self._t: self.title += d
        if self._h1 and self.h1: self.h1[-1] += d
        if self._ld and self.ld: self.ld[-1] += d


def url_of(f: Path) -> str:
    rel = f.relative_to(DIST).as_posix()
    if rel == 'index.html': return '/'
    if rel.endswith('/index.html'): rel = rel[:-len('index.html')]
    elif rel.endswith('.html'): rel = rel[:-5]
    return '/' + rel.rstrip('/')


def load_pages():
    pages = {}
    for f in sorted(DIST.rglob('*.html')):
        rel = f.relative_to(DIST).as_posix()
        p = P(); p.feed(f.read_text(encoding='utf-8')); p.file = f
        pages[url_of(f)] = p
    return pages


def robots_blocks(robots: str):
    dis = []; applies = False
    for line in robots.splitlines():
        line = line.split('#')[0].strip()
        if not line: continue
        k, _, v = line.partition(':'); k = k.strip().lower(); v = v.strip()
        if k == 'user-agent': applies = (v == '*')
        elif k == 'disallow' and applies and v: dis.append(v)
    return dis


def main():
    live = '--live' in sys.argv; table = '--table' in sys.argv
    err, note = [], []
    pages = load_pages()
    # Sitemap
    sm = (DIST / 'sitemap.xml').read_text(encoding='utf-8')
    locs = re.findall(r'<loc>([^<]+)</loc>', sm)
    if len(locs) != len(set(locs)): err.append('Sitemap: doppelte Einträge')
    smpaths = []
    for l in locs:
        if not l.startswith(SITE): err.append(f'Sitemap: fremde Domain {l}'); continue
        smpaths.append(l[len(SITE):] or '/')
    robots = (DIST / 'robots.txt').read_text(encoding='utf-8')
    if f'Sitemap: {SITE}/sitemap.xml' not in robots: err.append('robots.txt: Sitemap-Zeile fehlt')
    dis = robots_blocks(robots)
    titles, descs, h1s = {}, {}, {}
    indexable = {}
    for u, p in pages.items():
        rb = (p.meta.get('robots') or '').lower()
        noidx = 'noindex' in rb
        is404 = u == '/404'
        if not is404 and not noidx and not p.canon:
            err.append(f'{u}: Canonical fehlt')
        if p.canon:
            if len(p.canon) > 1: err.append(f'{u}: mehrere Canonicals')
            c = p.canon[0]
            exp = SITE + ('' if u == '/' else u)
            if not noidx and c != exp: err.append(f'{u}: Canonical {c} != {exp}')
            if not re.fullmatch(r'https://markentrix\.de(/[^?#]*[^/?#.])?', c) and c != SITE + '/' and not noidx:
                err.append(f'{u}: Canonical nicht normalisiert: {c}')
        if p.hreflang: err.append(f'{u}: hreflang vorhanden, aber Seite ist einsprachig')
        if p.lang != 'de': err.append(f'{u}: html lang={p.lang}')
        t = p.title.strip(); d = (p.meta.get('description') or '').strip()
        if not t: err.append(f'{u}: Title fehlt')
        if not d and not is404: err.append(f'{u}: Meta Description fehlt')
        if len([h for h in p.h1 if h.strip()]) != 1: err.append(f'{u}: {len(p.h1)} h1')
        if p.imgs_noalt: err.append(f'{u}: Bild ohne alt: {p.imgs_noalt[:2]}')
        if len(t) > 65: note.append(f'{u}: Title {len(t)} Zeichen')
        if d and (len(d) > 160 or len(d) < 70): note.append(f'{u}: Description {len(d)} Zeichen')
        # FAQPage: Frage und Antwort müssen sichtbar auf der Seite stehen (Google-Richtlinie, Wahrhaftigkeit)
        _src = p.file.read_text(encoding='utf-8')
        _vis = html_mod.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>', '', _src, flags=re.S)))
        _vis = ' '.join(_vis.split())
        for raw in p.ld:
            try:
                for nd in (lambda j: j.get('@graph', [j]))(json.loads(raw)):
                    if nd.get('@type') == 'FAQPage':
                        for q in nd.get('mainEntity', []):
                            qn = ' '.join(q['name'].split()); an = ' '.join(re.sub(r'<[^>]+>', '', q['acceptedAnswer']['text']).split())
                            if qn not in _vis or an[:60] not in _vis: err.append(f'{u}: FAQ-JSON-LD nicht sichtbar auf der Seite: {qn[:50]}')
            except Exception:
                pass
        for raw in p.ld:
            try:
                j = json.loads(raw)
            except Exception as e:
                err.append(f'{u}: JSON-LD ungültig ({e})'); continue
            for m in re.findall(r'https?://[^"\s]+', raw):
                if re.match(r'https?://(www\.)?markentrix\.de', m) and not m.startswith(SITE): err.append(f'{u}: JSON-LD-URL nicht kanonisch: {m}')
        if not noidx and not is404:
            indexable[u] = p
            titles.setdefault(t, []).append(u); descs.setdefault(d, []).append(u); h1s.setdefault(' '.join(p.h1[0].split()) if p.h1 else '', []).append(u)
    for name, dd in (('Title', titles), ('Description', descs), ('H1', h1s)):
        for k, v in dd.items():
            if k and len(v) > 1: err.append(f'Doppelte(r) {name}: {v} -> {k[:70]}')
    # Sitemap <-> Seiten
    for sp in smpaths:
        if sp not in pages: err.append(f'Sitemap-Eintrag ohne Seite: {sp}'); continue
        rb = (pages[sp].meta.get('robots') or '').lower()
        if 'noindex' in rb: err.append(f'Sitemap enthält noindex-Seite: {sp}')
        if any(sp.startswith(x) for x in dis): err.append(f'robots.txt sperrt Sitemap-URL {sp}')
    for u, p in indexable.items():
        if u not in smpaths and not u.startswith('/beispiel/'):
            err.append(f'Indexierbare Seite fehlt in Sitemap: {u}')
        elif u not in smpaths: note.append(f'Beispielseite nicht in Sitemap (bewusst?): {u}')
    # Interne Links
    inbound = {u: set() for u in pages}
    for u, p in pages.items():
        for h in p.links:
            if h.startswith(('mailto:', 'tel:', 'javascript:', '#', 'data:')) or not h: continue
            pu = urlparse(urljoin(SITE + u, h))
            if pu.netloc not in ('markentrix.de', 'www.markentrix.de', ''):
                continue
            if pu.scheme == 'http' or pu.netloc == 'www.markentrix.de': err.append(f'{u}: Link mit http/www: {h}'); continue
            tgt = pu.path or '/'
            if tgt.endswith('.html') and '/beispiel/' not in tgt: err.append(f'{u}: Link auf .html: {h}')
            norm = tgt.rstrip('/') or '/'
            if norm in pages: inbound[norm].add(u)
            else:
                f = DIST / norm.lstrip('/')
                if not f.exists() and not (DIST / (norm.lstrip('/') + '.html')).exists() and not (DIST / norm.lstrip('/') / 'index.html').exists():
                    err.append(f'{u}: Link ins Leere: {h}')
    for u in indexable:
        if len(inbound[u] - {u}) < 2 and u != '/': note.append(f'{u}: nur {len(inbound[u]-{u})} eingehende interne Links')
    if table:
        print('URL | Title | H1 | Robots | eingehend')
        for u, p in pages.items():
            print(f"{u} | {p.title.strip()[:60]} | {' '.join(p.h1[0].split())[:50] if p.h1 else '-'} | {p.meta.get('robots','index')} | {len(inbound[u]-{u})}")
    # Live
    if live:
        def get(u, method='GET', follow=False):
            class NoRedir(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k): return None
            op = urllib.request.build_opener(*( [] if follow else [NoRedir]))
            rq = urllib.request.Request(u, method=method, headers={'User-Agent': 'Mozilla/5.0 (seo_audit)'})
            try:
                r = op.open(rq, timeout=25); return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read() if method == 'GET' else b''
            except urllib.error.HTTPError as e:
                return e.code, {k.lower(): v for k, v in e.headers.items()}, b''
            except Exception as e:
                return 0, {'err': str(e)}, b''
        for src, exp in (('http://markentrix.de/', 308), ('https://www.markentrix.de/', 301), ('http://www.markentrix.de/', None)):
            s, h, _ = get(src)
            loc = h.get('location', '')
            if s not in (301, 308) or not loc.startswith('https://'): err.append(f'LIVE {src}: {s} -> {loc}')
        s, h, _ = get(SITE + '/diese-seite-gibt-es-nicht-x7')
        if s != 404: err.append(f'LIVE 404-Test lieferte {s}')
        s, h, _ = get(SITE + '/preise/')
        if s not in (301, 308) or not h.get('location', '').endswith('/preise'): err.append(f'LIVE Slash-Redirect /preise/: {s} {h.get("location")}')
        s, h, _ = get(SITE + '/preise.html')
        if s not in (301, 308): err.append(f'LIVE .html-Redirect: {s}')
        for sp in smpaths:
            s, h, body = get(SITE + ('' if sp == '/' else sp))
            if s != 200: err.append(f'LIVE {sp}: Status {s}'); continue
            if 'noindex' in (h.get('x-robots-tag', '') or '').lower(): err.append(f'LIVE {sp}: X-Robots-Tag noindex')
            m = re.search(rb'<link rel="canonical" href="([^"]+)"', body)
            exp = SITE + ('' if sp == '/' else sp)
            if not m or m.group(1).decode() != exp: err.append(f'LIVE {sp}: Canonical {m.group(1).decode() if m else None}')
        print(f'Live geprüft: {len(smpaths)} Sitemap-URLs')
    print(f'{len(pages)} Seiten, {len(smpaths)} Sitemap-URLs, {len(indexable)} indexierbar')
    for n in sorted(set(note)): print('HINWEIS', n)
    for e in sorted(set(err)): print('FEHLER ', e)
    print('OK' if not err else f'{len(set(err))} Fehler')
    sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()
