#!/usr/bin/env python3
"""Eigener Crawl-Audit der gebauten Seite (dist/): defekte Links und Anker, Titel und Meta, Robots, Canonical, Sitemap, Duplikate, Crawl-Tiefe,
verwaiste Seiten, Bilder, Inhalt. Aufruf: python3 tools/build.py && python3 tools/crawl_audit.py"""
import re, os, sys, glob, json, html, hashlib, collections
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag

DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dist')
SITE = 'https://markentrix.de'

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]; self.imgs=[]; self.meta={}; self.title=''; self._t=False; self.h=[]; self._h=None
        self.canon=None; self.lang=None; self.text=[]; self.skip=0; self.ld=0; self.forms=[]; self.inmain=False
        self.ids=set(); self.alt_links=[]; self._a=None; self.scripts=[]; self.hreflang=[]
    def handle_starttag(self,tag,a):
        a=dict(a)
        if 'id' in a: self.ids.add(a['id'])
        if tag=='html': self.lang=a.get('lang')
        if tag=='title': self._t=True
        if tag=='meta':
            k=a.get('name') or a.get('property')
            if k: self.meta[k.lower()]=a.get('content','')
        if tag=='link':
            if a.get('rel')=='canonical': self.canon=a.get('href')
            if a.get('rel')=='alternate' and a.get('hreflang'): self.hreflang.append(a.get('hreflang'))
        if tag=='a' and a.get('href') is not None:
            self._a={'href':a['href'],'text':'','target':a.get('target'),'rel':a.get('rel',''),'aria':a.get('aria-label','')}
            self.links.append(self._a)
        if tag=='img': self.imgs.append(a)
        if tag in('script','style','noscript'): self.skip+=1
        if tag=='script' and a.get('src'): self.scripts.append(a['src'])
        if tag=='main': self.inmain=True
        if re.fullmatch(r'h[1-6]',tag): self._h=[int(tag[1]),'']
        if tag=='form': self.forms.append(a)
    def handle_endtag(self,tag):
        if tag=='title': self._t=False
        if tag=='a': self._a=None
        if tag in('script','style','noscript'): self.skip=max(0,self.skip-1)
        if re.fullmatch(r'h[1-6]',tag) and self._h: self.h.append(tuple(self._h)); self._h=None
    def handle_data(self,d):
        if self._t: self.title+=d
        if self._a is not None: self._a['text']+=d
        if self._h is not None: self._h[1]+=d
        if not self.skip and self.inmain: self.text.append(d)

pages={}
for f in sorted(glob.glob(DIST+'/**/*.html',recursive=True)):
    rel=f[len(DIST):-5]; url='/' if rel=='/index' else rel
    if rel.endswith('/index') and rel!='/index': url=rel[:-6]+'/'
    p=P(); p.feed(open(f,encoding='utf-8').read()); pages[url]=(f,p)
urls=set(pages)
noindex={u for u,(f,p) in pages.items() if 'noindex' in p.meta.get('robots','')}
def norm(u):
    u=u.split('#')[0]
    if len(u)>1 and u.endswith('/') : u=u[:-1]
    return u
def resolve(base,href):
    if href.startswith(('mailto:','tel:','javascript:','data:','#','whatsapp:','sms:')): return None
    u=urljoin(SITE+base,href); pu=urlparse(u)
    if pu.netloc not in('markentrix.de','www.markentrix.de'): return ('ext',u)
    return ('int',norm(pu.path) or '/')
def exists(path):
    if path in urls or path+'/' in urls: return True
    q=DIST+path
    return os.path.isfile(q) or os.path.isfile(q+'.html') or os.path.isfile(q+'/index.html') or os.path.isdir(q)

out=collections.OrderedDict()
def sec(k): out[k]=[]; return out[k]

# 1 Links
broken=sec('1 Defekte interne Links/Anker'); inl=collections.defaultdict(set); ext=collections.defaultdict(set); blank=sec('1b target=_blank ohne rel=noopener'); gen=sec('1c Linktexte ohne Aussage'); emptyl=sec('1d Links ohne Text/Name')
for u,(f,p) in pages.items():
    for l in p.links:
        r=resolve(u,l['href'])
        if not r: continue
        if r[0]=='ext': ext[r[1]].add(u);
        else:
            tgt=r[1]
            if not exists(tgt): broken.append(f'{u} -> {l["href"]}')
            else: inl[tgt].add(u)
            if '#' in l['href'] and not l['href'].startswith('#'):
                an=l['href'].split('#')[1]; tp=pages.get(tgt) or pages.get(tgt+'/')
                if tp and an and an not in tp[1].ids: broken.append(f'{u} -> Anker fehlt {l["href"]}')
        if l['target']=='_blank' and 'noopener' not in l['rel']: blank.append(f'{u} -> {l["href"]}')
        tx=re.sub(r'\s+',' ',l['text']).strip().lower()
        if tx in('hier','mehr','mehr erfahren','klicken sie hier','weiterlesen','link'): gen.append(f'{u}: „{tx}“')
        if not tx and not l['aria']:
            # Bild im Link?
            pass
# 2 Titel/Meta
t=sec('2 Titel/Meta'); titles=collections.defaultdict(list); descs=collections.defaultdict(list)
for u,(f,p) in pages.items():
    if u in('/danke','/404') or u.startswith('/beispiel/'): continue
    ti=re.sub(r'\s+',' ',p.title).strip(); de=p.meta.get('description','').strip()
    titles[ti].append(u); descs[de].append(u)
    if not ti: t.append(f'{u}: kein Title')
    elif len(ti)>65 and u not in noindex: t.append(f'{u}: Title {len(ti)} Zeichen')
    if not de: t.append(f'{u}: keine Description')
    elif len(de)>160 or len(de)<70: t.append(f'{u}: Description {len(de)} Zeichen')
    for k in('og:title','og:description','og:image','twitter:card'):
        if k not in p.meta and u not in noindex: t.append(f'{u}: {k} fehlt')
    if not p.lang: t.append(f'{u}: kein lang-Attribut')
    if 'viewport' not in p.meta: t.append(f'{u}: kein viewport')
t+= [f'doppelter Title: {k!r} -> {v}' for k,v in titles.items() if len(v)>1]
t+= [f'doppelte Description: {v}' for k,v in descs.items() if len(v)>1 and k]
# 3 Robots/Canonical
r=sec('3 Robots/Canonical')
for u,(f,p) in pages.items():
    if u.startswith('/beispiel/') or u in('/danke','/404'): continue
    exp=SITE+('' if u=='/' else u)
    if not p.canon: r.append(f'{u}: kein Canonical')
    elif p.canon.rstrip('/')!=exp.rstrip('/') : r.append(f'{u}: Canonical {p.canon} weicht ab')
    if p.hreflang: r.append(f'{u}: hreflang {p.hreflang}')
rob=open(DIST+'/robots.txt',encoding='utf-8').read()
dis=[l.split(':',1)[1].strip() for l in rob.splitlines() if l.lower().startswith('disallow:') and l.split(':',1)[1].strip()]
# 4 Sitemap
s=sec('4 Sitemap'); sm=open(DIST+'/sitemap.xml',encoding='utf-8').read(); locs=re.findall(r'<loc>(.*?)</loc>',sm); mods=re.findall(r'<lastmod>(.*?)</lastmod>',sm)
s.append(f'{len(locs)} URLs, {len(mods)} lastmod')
for l in locs:
    pth=norm(urlparse(l).path) or '/'
    if not exists(pth): s.append(f'Sitemap-URL ohne Seite: {l}')
    if pth in noindex: s.append(f'noindex-Seite in Sitemap: {l}')
    if any(pth.startswith(d.rstrip('*')) for d in dis if d!='/'): s.append(f'in robots.txt gesperrt, aber in Sitemap: {l}')
    if l.endswith('/') and l!=SITE+'/': s.append(f'Slash am Ende: {l}')
for m in mods:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',m): s.append(f'lastmod-Format: {m}')
ind={u for u in pages if u not in noindex and not u.startswith('/beispiel/') and u not in('/danke','/404','/karte/')}
missing=[u for u in ind if (SITE+('' if u=='/' else u)) not in locs]
s.append(f'indexierbare Seiten nicht in Sitemap: {missing}')
# 5 Duplikate
d=sec('5 Exakte Duplikate (Hauptinhalt)'); hs=collections.defaultdict(list)
for u,(f,p) in pages.items():
    tx=re.sub(r'\s+',' ',' '.join(p.text)).strip()
    if len(tx)>200: hs[hashlib.md5(tx.encode()).hexdigest()].append(u)
d+= [str(v) for v in hs.values() if len(v)>1]
# 6 Tiefe, Verwaiste
dp=sec('6 Crawl-Tiefe / verwaiste Seiten'); depth={'/':0}; q=['/']; adj=collections.defaultdict(set)
for u,(f,p) in pages.items():
    for l in p.links:
        rr=resolve(u,l['href'])
        if rr and rr[0]=='int':
            tgt=rr[1] if rr[1] in pages else (rr[1]+'/' if rr[1]+'/' in pages else rr[1]); adj[u].add(tgt)
while q:
    c=q.pop(0)
    for n in adj[c]:
        if n in pages and n not in depth: depth[n]=depth[c]+1; q.append(n)
cnt=collections.Counter(depth.values()); dp.append('Tiefenverteilung: '+', '.join(f'T{k}:{v}' for k,v in sorted(cnt.items())))
orph=[u for u in pages if u not in depth and u not in('/404',)]
dp.append(f'von der Startseite nicht erreichbar: {orph}')
few=[(u,len(inl.get(u,[]))) for u in ind if len(inl.get(u,[]))<=2 and u!='/']
dp.append(f'indexierbare Seiten mit höchstens 2 internen Verweisen: {few}')
# 7 Bilder
im=sec('7 Bilder');
for u,(f,p) in pages.items():
    for a in p.imgs:
        src=a.get('src','')
        if 'alt' not in a: im.append(f'{u}: kein alt ({src})')
        if not(a.get('width') and a.get('height')) and not src.startswith('data:'): im.append(f'{u}: ohne width/height ({src})')
        if src.startswith('/') and not exists(src.split('?')[0]) : im.append(f'{u}: Bilddatei fehlt {src}')
        if src.startswith('http://'): im.append(f'{u}: unsicheres Bild {src}')
# 8 Inhalt: dünn, Platzhalter, Mixed Content
c=sec('8 Inhalt');
for u,(f,p) in pages.items():
    raw=open(f,encoding='utf-8').read(); tx=re.sub(r'\s+',' ',' '.join(p.text)).strip(); wc=len(tx.split())
    if wc<250 and u not in('/danke','/404','/karte/','/seitenuebersicht','/impressum','/website-check','/lp/website-check','/portal') and not u.startswith('/beispiel/'): c.append(f'{u}: nur {wc} Wörter')
    for pat in(r'lorem ipsum',r'\bTODO\b',r'\bXXX+\b',r'Platzhalter',r'\bTBD\b',r'example\.com|example\.org',r'localhost',r'http://(?!www\.w3\.org)[a-z0-9.-]+',r'  +[A-Za-zÄÖÜ]'):
        mm=re.findall(pat,tx if pat.startswith(r'  ') else raw,re.I)
        if mm and not pat.startswith(r'  '): c.append(f'{u}: Treffer „{pat}“ ×{len(mm)} z. B. {mm[0] if isinstance(mm[0],str) else mm[0]}')
    if not p.h or sum(1 for l,h in p.h if l==1)!=1: c.append(f'{u}: H1-Anzahl {sum(1 for l,h in p.h if l==1)}')
# 9 Externe Links (nur Liste)
ex=sorted(ext);
json.dump({'ext':{k:sorted(v) for k,v in ext.items()}},open('/tmp/mx-ext-links.json','w'),ensure_ascii=False)
out['9 Externe Links']=[f'{len(ex)} verschiedene externe Adressen']
for k,v in out.items():
    print(f'\n## {k}  ({len(v)} Einträge)')
    for x in v[:40]: print('  -',x)
    if len(v)>40: print(f'  … {len(v)-40} weitere')
print('\nSeiten gecrawlt:',len(pages),'| indexierbar:',len(ind))
