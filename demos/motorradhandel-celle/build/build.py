#!/usr/bin/env python3
"""Erzeugt alle Seiten der Demo (Bestand, Detailseiten, Ankauf, Service, Kontakt ...). Aufruf: python3 build/build.py
Bestand und Preise stehen unten in BIKES (Quelle: bisherige Website, Stand 06.10.2026, Aktualität vom Kunden bestätigen)."""
import re, base64, html, os, json, sys, shutil
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, 'build'))
import seo, og
LIVE = '--live' in sys.argv                    # Live-Build: indexierbar, ohne Demo-Leiste, schreibt nach live/
OUT = 'live/' if LIVE else ''
for d_ in ('fahrzeug', 'motorraeder', 'ratgeber'): os.makedirs(OUT + d_, exist_ok=True)
PAGES, WARN = [], []                           # Sitemap-Register, Warnungen

# ---------- CSS inline (minifiziert, Überschrift-Schrift eingebettet) ----------
css = open('assets/main.css').read()
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S); css = re.sub(r'\s*([{};:,>])\s*', r'\1', css); css = re.sub(r'\s+', ' ', css).replace(';}', '}').strip()
b64 = base64.b64encode(open('assets/fonts/barlow-condensed-700-sub.woff2', 'rb').read()).decode()
CSS_ROOT = css.replace('url("fonts/barlow-condensed-700-sub.woff2")', 'url(data:font/woff2;base64,' + b64 + ')').replace('url("fonts/', 'url("assets/fonts/')
CSS_SUB = CSS_ROOT.replace('url("assets/fonts/', 'url("../assets/fonts/')

def esc(s): return html.escape(str(s), quote=True)
def eur(p): return f'{p:,}'.replace(',', '.') + ' €'
def kmf(k): return f'{k:,}'.replace(',', '.') + ' km'
def isize(p):
    return Image.open('assets/img/' + p).size

PHONE_TXT, PHONE_TEL = '01520 888 0000', '+4915208880000'
ADDR = 'Lachtehäuserstraße 6 · 29223 Celle (Altenhagen)'
MAIL = 'vollcool007@web.de'

# ---------- Bestand ----------
BIKES = [
 dict(slug='kawasaki-z1000-2015', brand='Kawasaki', model='Z 1000', ez='07/2015', year=2015, km=7254, price=9899, typ='Naked Bike', n=2, hl='Jüngstes Modell im Bestand'),
 dict(slug='honda-crf1000-dct-b', brand='Honda', model='CRF 1000 DCT', ez='04/2017', year=2017, km=12832, price=9999, typ='Reise & Enduro', n=1, hl='Wenig Kilometer'),
 dict(slug='honda-crf1000-dct-a', brand='Honda', model='CRF 1000 DCT', ez='04/2017', year=2017, km=35332, price=8899, typ='Reise & Enduro', n=2),
 dict(slug='kawasaki-z1000-abs', brand='Kawasaki', model='Z 1000 ABS', ez='04/2010', year=2010, km=4232, price=6799, typ='Naked Bike', n=3, hl='Nur 4.232 km'),
 dict(slug='kawasaki-zx10r-2005', brand='Kawasaki', model='ZX-10R', ez='07/2005', year=2005, km=12254, price=5899, typ='Sportler', n=1),
 dict(slug='honda-cbr1000rr-2006', brand='Honda', model='CBR 1000 RR', ez='04/2006', year=2006, km=31432, price=4599, typ='Sportler', n=3),
 dict(slug='suzuki-gsxr750-k5', brand='Suzuki', model='GSX-R 750 K5', ez='04/2005', year=2005, km=22432, price=3999, typ='Sportler', n=1),
 dict(slug='yamaha-yzf-r6-silver', brand='Yamaha', model='YZF-R6 RJ05 Silver Edition', ez='04/2003', year=2003, km=32183, price=3499, typ='Sportler', n=2),
 dict(slug='triumph-speed-triple-955', brand='Triumph', model='Speed Triple 955', ez='05/2001', year=2001, km=20632, price=3390, typ='Naked Bike', n=1),
 dict(slug='honda-cbr600rr-2004', brand='Honda', model='CBR 600 RR', ez='04/2004', year=2004, km=19432, price=3670, typ='Sportler', n=1),
 dict(slug='suzuki-gsxr750-k1', brand='Suzuki', model='GSX-R 750 K1', ez='04/2001', year=2001, km=26867, price=2899, typ='Sportler', n=3, hl='Mehrfach vorhanden'),
 dict(slug='honda-varadero-xl1000v', brand='Honda', model='XL 1000 V Varadero', ez='04/2000', year=2000, km=34645, price=2999, typ='Reise & Enduro', n=3),
 dict(slug='yamaha-yzf-r1-2000', brand='Yamaha', model='YZF-R1', ez='04/2000', year=2000, km=22967, price=1999, typ='Sportler', n=2, hl='Günstiger Einstieg'),
 dict(slug='bmw-f650-cr', brand='BMW', model='F 650 CR', ez='04/1996', year=1996, km=32432, price=1699, typ='Allrounder', n=2),
 dict(slug='piaggio-hexagon-sport', brand='Piaggio', model='Hexagon 125 LX Sport', ez='04/1998', year=1998, km=14053, price=899, typ='Roller', n=2),
 dict(slug='piaggio-hexagon-lx', brand='Piaggio', model='Hexagon 125 LX', ez='04/1998', year=1998, km=22053, price=899, typ='Roller', n=3),
]
for i, b in enumerate(BIKES):
    b['pos'] = i; b['name'] = f"{b['brand']} {b['model']}"
    b['alts'] = [f"{b['name']}, Foto {k} von {b['n']}" for k in range(1, b['n'] + 1)]
    b['img'] = [f"{b['slug']}-{k}.webp" for k in range(1, b['n'] + 1)]
json.dump(BIKES, open('assets/bestand.json', 'w'), ensure_ascii=False, indent=1)
BRANDS = sorted({b['brand'] for b in BIKES}); TYPES = ['Sportler', 'Naked Bike', 'Reise & Enduro', 'Allrounder', 'Roller']
N = len(BIKES)
slug_ = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')).strip('-')
CATS = [('brand', b) for b in BRANDS if sum(1 for x in BIKES if x['brand'] == b) >= 2] + [('typ', t) for t in TYPES if sum(1 for x in BIKES if x['typ'] == t) >= 2]
CAT_URL = {(f, v): f"motorraeder/{slug_(v)}.html" for f, v in CATS}
CAT_LINKS = [((f'{v} Motorräder' if f == 'brand' else v), CAT_URL[(f, v)]) for f, v in CATS]
GUIDES = [('Gebrauchtes Motorrad kaufen: Checkliste', 'ratgeber/gebrauchtes-motorrad-kaufen.html'), ('Motorrad überwintern: Checkliste', 'ratgeber/motorrad-ueberwintern.html')]
GUIDE_LINKS = GUIDES
faq_html = lambda items: '<div class="faq" data-reveal>' + ''.join(f'<details><summary>{q}</summary><div>{a}</div></details>' for q, a in items) + '</div>'
og.make_all(BIKES, eur, kmf)

WINTER = True   # Saison-Schalter: Winterlager-Kampagne (Banner, Startseiten-Streifen, Hero-Link). Im Frühjahr auf False oder durch Saisonstart-Kampagne ersetzen.
SNOW = '<svg class="snow" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7"/><path d="M9 4l3 2 3-2M9 20l3-2 3 2M4 9.5l3.2.4-.9-3.1M20 14.5l-3.2-.4.9 3.1M4 14.5l3.2-.4-.9 3.1M20 9.5l-3.2.4.9-3.1"/></g></svg>'
NAV = [('Motorräder', 'motorraeder.html'), ('Überwintern', 'ueberwintern.html'), ('Verkaufen', 'ankauf.html'), ('Service & Finanzierung', 'service.html'), ('Über uns', 'ueber-uns.html'), ('Kontakt', 'kontakt.html')]

def no_reveal_above_fold(body, n):
    parts = body.split('</section>')
    for i in range(min(n, len(parts))): parts[i] = parts[i].replace(' data-reveal', '')
    return '</section>'.join(parts)

def layout(fn, title, desc, body, sub=False, active=None, ld='', fold=1, probe='kontakt.html#probefahrt', head_extra='', kind='WebPage', crumbs=None, nodes=None, ogimg=None, index=True, vis_crumbs=True, images=None):
    p = '../' if sub else ''
    body = no_reveal_above_fold(body, fold)
    nav = ''.join(f'<li><a href="{p}{h}"' + (' aria-current="page"' if h == active else '') + f'>{esc(t)}</a></li>' for t, h in NAV)
    foot = ''.join(f'<li><a href="{p}{h}">{esc(t)}</a></li>' for t, h in NAV)
    season_bar = (f'<a class="season" href="{p}ueberwintern.html">{SNOW}<span><b>Winterlager:</b> Ihr Motorrad überwintert bei uns.</span><u>Winterplatz anfragen</u></a>\n' if WINTER else '')
    robots = 'index, follow, max-image-preview:large, max-snippet:-1' if (LIVE and index) else 'noindex, nofollow'
    og_abs = f"{seo.DOMAIN}/assets/og/{ogimg or 'default'}.jpg"
    crumb_html = ''
    if crumbs:
        parts = ' / '.join(f'<a href="{p}{l}">{esc(n)}</a>' if l else esc(n) for n, l in crumbs[:-1] if True) 
        last = esc(crumbs[-1][0]); trail = (parts + ' / ' if parts else '')
        crumb_html = f'<nav class="crumbs-bar" aria-label="Brotkrumen"><div class="wrap"><a href="{p}index.html">Start</a> / {trail}{last}</div></nav>\n' if vis_crumbs else ''
    main = next((n['@id'] for n in (nodes or []) if n.get('@type') in ('ItemList',) or 'Product' in (n['@type'] if isinstance(n['@type'], list) else [n['@type']]) or n.get('@type') == 'Article'), None)
    graph_nodes = [seo.business(N), seo.owner(), seo.website(), seo.webpage(fn, kind, title, desc, og_abs, bool(crumbs), {'mainEntity': {'@id': main}} if main and kind != 'WebPage' else {})]
    if crumbs: graph_nodes.append(seo.breadcrumb(fn, [(n, l) for n, l in crumbs]))
    if nodes: graph_nodes += nodes
    jsonld = seo.graph(graph_nodes)
    demo_bar = '' if LIVE else '<div class="demo-bar" data-demo role="note">Designvorschlag von Markentrix für Motorradhandel-Celle · nicht veröffentlicht · Bestand und Preise laut bisheriger Website <span class="ph-note">[Aktualität vom Kunden bestätigen]</span></div>\n'
    cats_f = ''.join(f'<li><a href="{p}{u}">{esc(n)}</a></li>' for n, u in CAT_LINKS)
    guides_f = ''.join(f'<li><a href="{p}{u}">{esc(n)}</a></li>' for n, u in GUIDE_LINKS)
    page = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#0F0F10">
<link rel="canonical" href="{seo.url(fn)}">
<meta property="og:locale" content="de_DE"><meta property="og:type" content="website"><meta property="og:site_name" content="Motorradhandel-Celle">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{seo.url(fn)}">
<meta property="og:image" content="{og_abs}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(title)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{og_abs}">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<script>document.documentElement.className+=' js'</script>
<link rel="preload" href="{p}assets/fonts/inter-sub-wght.woff2" as="font" type="font/woff2" crossorigin>
{head_extra}<style>{CSS_SUB if sub else CSS_ROOT}</style>
<script src="{p}assets/main.js" defer></script>
{jsonld}</head>
<body>
<a class="skip" href="#main">Zum Inhalt springen</a>
{demo_bar}{season_bar}<header class="site"><div class="wrap">
  <a class="brand" href="{p}index.html" aria-label="Motorradhandel-Celle, zur Startseite"><i aria-hidden="true"></i><span>Motorradhandel<small>CELLE · ALTENHAGEN</small></span></a>
  <nav class="main" id="nav" aria-label="Hauptnavigation" data-open="false"><ul>{nav}</ul></nav>
  <div class="hdr-cta"><a class="btn ghost sm" href="tel:{PHONE_TEL}">{PHONE_TXT}</a><a class="btn sm" href="{p}{probe}">Probefahrt anfragen</a><a class="fav-link" href="{p}merkliste.html" aria-label="Merkliste" hidden>{HEART}<b data-fav-count></b></a><button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">Menü</button></div>
</div></header>
{crumb_html}<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
  <div class="foot-grid">
    <div><h2>Motorradhandel-Celle</h2><address style="font-style:normal">Inhaber Ingo Werner<br>Lachtehäuserstraße 6<br>29223 Celle (Altenhagen)<br><a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></address></div>
    <div><h2>Seiten</h2><ul>{foot}</ul></div>
    <div><h2>Bestand</h2><ul><li><a href="{p}motorraeder.html">Alle Motorräder</a></li>{cats_f}</ul></div>
    <div><h2>Ratgeber</h2><ul>{guides_f}</ul></div>
  </div>
  <div class="legal"><p>© Motorradhandel-Celle</p><p><a href="{p}impressum.html">Impressum</a> · <a href="{p}datenschutz.html">Datenschutz</a></p></div>
</div></footer>
<div class="actionbar" role="navigation" aria-label="Schnellkontakt"><a href="tel:{PHONE_TEL}">Anrufen</a><a class="w" href="https://wa.me/{PHONE_TEL.lstrip('+')}" rel="noopener noreferrer" target="_blank">WhatsApp</a><a class="p" href="{p}{probe}">Probefahrt</a></div>
</body>
</html>
"""
    open(OUT + fn, 'w').write(page)
    if 'class="ph-note"' in page: WARN.append(fn)
    if index and fn not in ('danke.html', '404.html'): PAGES.append(dict(fn=fn, images=images or []))
    print(fn, len(page) // 1024, 'KB')

HEART = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 2.8 5 6.2 5c2 0 3.5 1 5.8 3.3C14.3 6 15.8 5 17.8 5c3.4 0 5.3 3.4 3.8 6.8C19.5 16.4 12 21 12 21z"/></svg>'

def card(b, lazy=True, pfx='', d=0, prio=False, tag='h3'):
    w, h = isize(b['img'][0])
    badge = f'<span class="badge red">{esc(b["hl"])}</span>' if b.get('hl') else '<span class="badge">TÜV neu</span>'
    return f'''<li class="bike" data-marke="{esc(b['brand'])}" data-typ="{esc(b['typ'])}" data-preis="{b['price']}" data-jahr="{b['year']}" data-km="{b['km']}" data-pos="{b['pos']}" data-reveal style="--d:{d}s">
<div class="ph">{badge}<button type="button" class="fav" data-fav="{b['slug']}" aria-pressed="false" aria-label="{esc(b['name'])} merken" hidden>{HEART}</button><img src="{pfx}assets/img/{b['img'][0]}" width="{w}" height="{h}" alt="{esc(b['alts'][0])}"{' loading="lazy"' if lazy else ''}{' fetchpriority="high"' if prio else ''}></div>
<div class="body"><{tag}><a href="{pfx}fahrzeug/{b['slug']}.html">{esc(b['name'])}</a></{tag}>
<ul class="specs"><li>EZ {b['ez']}</li><li>{kmf(b['km'])}</li><li>{esc(b['typ'])}</li></ul>
<div class="price"><b>{eur(b['price'])}</b><small>VB</small></div>
<div class="acts"><a class="btn ghost sm" href="{pfx}fahrzeug/{b['slug']}.html">Details</a><a class="btn sm" href="{pfx}fahrzeug/{b['slug']}.html#anfrage">Probefahrt</a></div></div></li>'''

def cta_dark(h='Ihr nächstes Motorrad wartet.', p='Rufen Sie kurz an oder senden Sie eine Anfrage. Wir sprechen einen Termin für die Probefahrt ab.', pfx=''):
    return f'<section class="dark"><div class="wrap" style="display:flex;flex-wrap:wrap;gap:1.5rem 3rem;align-items:center;justify-content:space-between" data-reveal><div><h2 style="margin:0 0 .2em">{h}</h2><p style="margin:0">{p}</p></div><div style="display:flex;flex-wrap:wrap;gap:.7rem"><a class="btn" href="tel:{PHONE_TEL}">Jetzt anrufen</a><a class="btn ghost" href="{pfx}motorraeder.html">Bestand ansehen</a></div></div></section>'

def probe_form(fid='anfrage', vehicle='', title='Probefahrt anfragen', sub_='Wir melden uns bei Ihnen und sprechen einen Termin ab.', btn='Probefahrt anfragen', pfx=''):
    veh = f'<input type="hidden" name="fahrzeug" value="{esc(vehicle)}">' if vehicle else ''
    return f'''<form class="card-f" id="{fid}" method="get" action="{pfx}danke.html" data-demo-form data-next="{pfx}danke.html" novalidate>
<h2 style="font-size:1.8rem;margin:0">{title}</h2><p style="font-size:1rem">{sub_}</p>{veh}
<div class="form-2"><div><label for="{fid}-n">Name</label><input id="{fid}-n" name="name" type="text" autocomplete="name" required></div><div><label for="{fid}-t">Telefon</label><input id="{fid}-t" name="telefon" type="tel" autocomplete="tel" required></div></div>
<div class="form-2"><div><label for="{fid}-e">E-Mail <span class="hint">(optional)</span></label><input id="{fid}-e" name="mail" type="email" autocomplete="email"></div><div><label for="{fid}-d">Wunschtermin <span class="hint">(optional)</span></label><input id="{fid}-d" name="termin" type="text" placeholder="z. B. Samstag Vormittag"></div></div>
<div><label for="{fid}-m">Nachricht <span class="hint">(optional)</span></label><textarea id="{fid}-m" name="nachricht" rows="3"></textarea></div>
<div class="chk"><input id="{fid}-z" name="inzahlung" type="checkbox"><label for="{fid}-z" style="margin:0;font-weight:500">Ich möchte mein Motorrad in Zahlung geben.</label></div>
<div class="chk"><input id="{fid}-f" name="finanzierung" type="checkbox"><label for="{fid}-f" style="margin:0;font-weight:500">Ich interessiere mich für eine Finanzierung.</label></div>
<div class="hp" aria-hidden="true"><label for="{fid}-w">Nicht ausfüllen</label><input id="{fid}-w" name="website" type="text" tabindex="-1" autocomplete="off"></div>
<p>Ihre Angaben verwenden wir nur zur Bearbeitung Ihrer Anfrage. Mehr in der <a href="{pfx}datenschutz.html">Datenschutzerklärung</a>.</p>
<button class="btn" type="submit">{btn}</button><p class="status" role="status" aria-live="polite"></p></form>'''

LD_OLD = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "MotorcycleDealer", "name": "Motorradhandel-Celle", "founder": "Ingo Werner", "address": {"@type": "PostalAddress", "streetAddress": "Lachtehäuserstraße 6", "postalCode": "29223", "addressLocality": "Celle", "addressCountry": "DE"}, "telephone": "+49 1520 8880000", "email": MAIL}, ensure_ascii=False) + '</script>\n'

# ================= START =================
by_price = lambda lo, hi: sum(1 for b in BIKES if lo <= b['price'] <= hi)
feat = BIKES[:6]
opt_m = ''.join(f'<option>{esc(x)}</option>' for x in BRANDS); opt_t = ''.join(f'<option>{esc(x)}</option>' for x in TYPES)
col = [('a', 'kawasaki-z1000-2015-1.webp', 'Kawasaki Z 1000', 'Grüne Kawasaki Z 1000 vor der Verkaufshalle'), ('b', 'honda-crf1000-dct-a-2.webp', 'Honda CRF 1000', 'Honda CRF 1000 Africa Twin Seitenansicht'), ('c', 'suzuki-gsxr750-k1-1.webp', 'Suzuki GSX-R', 'Gelbe Suzuki GSX-R 750'), ('d', 'kawasaki-zx10r-2005-1.webp', 'Kawasaki ZX-10R', 'Kawasaki ZX-10R in Silber')]
FP = ' fetchpriority="high"'
collage = ''.join('<figure class="%s"><img src="assets/img/%s" width="%d" height="%d" alt="%s"%s><figcaption>%s</figcaption></figure>' % (c, f, isize(f)[0], isize(f)[1], esc(a), FP if c == 'a' else '', esc(cap)) for c, f, cap, a in col)
FAQ_HOME = [
 ('Kann mein Motorrad bei Ihnen überwintern?', 'Ja, Ihr Bike kann bei uns überwintern. Fragen Sie Ihren Winterplatz an, wir stimmen Zeitraum und Konditionen mit Ihnen ab. <a href="ueberwintern.html">Zum Winterlager</a>'),
 ('Kann ich ein Motorrad probefahren?', 'Ja. Bitte sprechen Sie vorher einen Termin ab, per Telefon oder über die Anfrage auf der Fahrzeugseite.'),
 ('Nehmen Sie mein altes Motorrad in Zahlung?', 'Auf Wunsch ja. Nennen Sie uns Modell, Baujahr, Kilometerstand und schicken Sie Fotos. <a href="ankauf.html">Mehr zu Ankauf und Inzahlungnahme</a>'),
 ('Gibt es eine Finanzierung?', 'Auf Anfrage vermitteln wir Finanzierungen. Sprechen Sie uns an.'),
 ('Ist das Motorrad noch verfügbar?', 'Unser Bestand wechselt laufend, Zwischenverkäufe sind möglich. Rufen Sie kurz an, dann bestätigen wir die Verfügbarkeit.'),
 ('Mein Wunschmotorrad ist nicht dabei.', 'Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder. Nennen Sie uns Modell, Baujahr und Budget.'),
 ('Wo finde ich Motorradhandel-Celle?', 'Wir sind in Celle-Altenhagen, Lachtehäuserstraße 6, 29223 Celle. Bitte kündigen Sie Ihren Besuch kurz telefonisch an: 01520 888 0000.'),
 ('Welche Gewährleistung gibt es?', '<span class="ph-note">[Gewährleistung und Garantie vom Kunden festlegen und formulieren]</span>')]
fact_rows = [('Name', 'Motorradhandel-Celle (auch: Motorradhandel Celle)'), ('Art', 'Motorradhändler für gebrauchte Motorräder und Roller'), ('Standort', 'Lachtehäuserstraße 6, 29223 Celle (Altenhagen), Niedersachsen'), ('Inhaber', 'Ingo Werner, Bikerteam mit 17 Jahren Erfahrung'), ('Angebot', f'{N} gebrauchte Motorräder und Roller (Honda, Yamaha, Kawasaki, Suzuki, BMW, Triumph, Piaggio)'), ('Leistungen', 'Probefahrt nach Terminabsprache, Ankauf, Inzahlungnahme, Kommission, Finanzierung auf Anfrage, Winterlager, Import und Wunschsuche'), ('Einzugsgebiet', 'Celle, Hannover, Hamburg, Uelzen und Niedersachsen <span class="ph-note">[vom Kunden bestätigen]</span>'), ('Kontakt', f'<a href="tel:{PHONE_TEL}">{PHONE_TXT}</a>, <a href="mailto:{MAIL}">{MAIL}</a>'), ('Bestand aktualisiert', f'<time datetime="{seo.TODAY}">{seo.TODAY[8:]}.{seo.TODAY[5:7]}.{seo.TODAY[:4]}</time> <span class="ph-note">[Aktualität vom Kunden pflegen]</span>')]
blick = '<section class="alt" aria-labelledby="blick-h"><div class="wrap" style="max-width:56rem" data-reveal><p class="eyebrow">Auf einen Blick</p><h2 id="blick-h">Motorradhandel-Celle kurz erklärt.</h2><p class="answer"><strong>Motorradhandel-Celle ist ein Motorradhändler in Celle-Altenhagen.</strong> Wir verkaufen gebrauchte Motorräder und Roller, kaufen Motorräder an, nehmen sie in Zahlung, vermitteln auf Anfrage Finanzierungen und stellen Motorräder im Winter ein.</p><dl class="facts-dl">' + ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in fact_rows) + '</dl></div></section>\n'
hero_winter = (f'<p class="hero-winter"><a href="ueberwintern.html">{SNOW}<span>Winterzeit: Motorrad bei uns überwintern lassen</span><b aria-hidden="true">→</b></a></p>' if WINTER else '')
winter_strip = (f'''<section class="winter-strip" aria-labelledby="ws-h"><div class="wrap"><div class="ws" data-reveal><div class="ws-t"><p class="eyebrow">{SNOW} Winterlager</p><h2 id="ws-h">Ihr Motorrad überwintert bei uns.</h2><p>Die Saison ist vorbei? Stellen Sie Ihr Motorrad für den Winter bei uns ein und holen Sie es im Frühjahr wieder ab. Fragen Sie jetzt Ihren Winterplatz an.</p><div class="acts"><a class="btn ice" href="ueberwintern.html#winterplatz">Winterplatz anfragen</a><a class="btn ghost" href="tel:{PHONE_TEL}">Anrufen</a></div></div><ul class="ws-l"><li><b>Überwintern bei uns</b><span>Ihr Bike kann bei uns überwintern.</span></li><li><b>Im Winter verkaufen</b><span>Stellen Sie es in unsere Verkaufshalle und verkaufen Sie selbst oder in Kommission.</span></li><li><b>Im Frühjahr wechseln</b><span>Inzahlungnahme und Finanzierung auf Anfrage.</span></li></ul></div></div></section>\n''' if WINTER else '')
home = f'''<section class="hero"><div class="wrap"><div class="grid">
<div><p class="eyebrow">Motorradhandel in Celle · Altenhagen</p>
<h1>Motorrad kaufen in Celle. <span>Direkt vom Händler.</span></h1>
<p class="lead">Gepflegte Gebrauchtmotorräder von Honda, Yamaha, Suzuki, Kawasaki, BMW und mehr. Mit Probefahrt, Inzahlungnahme und auf Wunsch Finanzierung.</p>
<form class="finder" action="motorraeder.html" method="get" aria-label="Motorrad finden">
<div><label for="h-m">Marke</label><select id="h-m" name="marke"><option value="">Alle</option>{opt_m}</select></div>
<div><label for="h-t">Art</label><select id="h-t" name="typ"><option value="">Alle</option>{opt_t}</select></div>
<div><label for="h-p">Preis bis</label><select id="h-p" name="preis"><option value="">Egal</option><option value="2000">2.000 €</option><option value="4000">4.000 €</option><option value="6000">6.000 €</option><option value="10000">10.000 €</option></select></div>
<button class="btn" type="submit">Zeigen</button></form>
<ul class="chips"><li>Probefahrt nach Terminabsprache</li><li>Inzahlungnahme möglich</li><li>Finanzierung auf Anfrage</li><li>17 Jahre Erfahrung</li></ul>{hero_winter}</div>
<div class="collage" aria-label="Auswahl aus dem Bestand"><div class="count"><b>{N}</b>Motorräder<br>im Bestand</div>{collage}</div>
</div></div></section>
{winter_strip}
<section style="padding-block:clamp(2.5rem,1.5rem + 3vw,4.5rem) 0"><div class="wrap"><div class="tiles">
<a class="tile" href="motorraeder.html?preis=2000" data-reveal><b>Bis 2.000 €</b><span>{by_price(0, 2000)} Motorräder, günstiger Einstieg</span></a>
<a class="tile" href="motorraeder.html?preis=4000" data-reveal style="--d:.06s"><b>Bis 4.000 €</b><span>{by_price(0, 4000)} Motorräder, beliebte Sportler</span></a>
<a class="tile" href="motorraeder.html?preis=6000" data-reveal style="--d:.12s"><b>Bis 6.000 €</b><span>{by_price(0, 6000)} Motorräder, mehr Auswahl</span></a>
<a class="tile" href="motorraeder.html?sort=neu" data-reveal style="--d:.18s"><b>Neuere Modelle</b><span>ab Baujahr 2010, wenig Kilometer</span></a>
</div></div></section>

<section aria-labelledby="best-h"><div class="wrap">
<div class="head" data-reveal><div><p class="eyebrow">Aktueller Bestand</p><h2 id="best-h">Highlights im Bestand</h2></div><p><a class="btn ghost sm" href="motorraeder.html">Alle {N} Motorräder</a></p></div>
<ul class="bikes">{''.join(card(b, lazy=i > 2, d=(i % 3) * .06) for i, b in enumerate(feat))}</ul>
<p class="note" style="margin-top:1.2rem">VB = Verhandlungsbasis. Zwischenverkauf vorbehalten: Bitte bestätigen Sie die Verfügbarkeit kurz telefonisch.</p>
</div></section>

<section style="padding-top:0"><div class="wrap"><div class="band" data-reveal>
<div><p class="eyebrow" style="color:#fff">Motorrad verkaufen</p><h2>Ihr Motorrad verkaufen? Wir machen Ihnen ein Angebot.</h2><p>Wir kaufen Ihr Motorrad, auch wenn Sie kein neues bei uns kaufen. Von Aprilia bis Zündapp. Schicken Sie uns die Eckdaten, wir sprechen darüber.</p>
<div class="acts"><a class="btn light" href="ankauf.html">Angebot anfordern</a><a class="btn ghost" href="tel:{PHONE_TEL}" style="color:#fff;border-color:#fff">Anrufen</a></div></div>
<ul><li>Ankauf von Aprilia bis Zündapp</li><li>Inzahlungnahme beim Kauf</li><li>Verkauf in Kommission</li><li>Überwintern in unserer Halle</li></ul></div></div></section>

<section class="alt" style="padding-top:0" aria-labelledby="ablauf-h"><div class="wrap">
<div class="head" data-reveal><div><p class="eyebrow">So läuft der Kauf</p><h2 id="ablauf-h">In vier Schritten zum Motorrad.</h2></div><p>Ein Ansprechpartner, kurze Wege, klare Absprachen.</p></div>
<ol class="steps"><li data-reveal><h3>Aussuchen</h3><p>Bestand online ansehen oder vor Ort in der Verkaufshalle vorbeikommen.</p></li><li data-reveal style="--d:.07s"><h3>Probefahrt</h3><p>Anrufen oder Anfrage senden. Wir sprechen einen Termin ab.</p></li><li data-reveal style="--d:.14s"><h3>Konditionen klären</h3><p>Ihr altes Motorrad nehmen wir auf Wunsch in Zahlung, Finanzierungen vermitteln wir gegebenenfalls.</p></li><li data-reveal style="--d:.21s"><h3>Übergabe</h3><p>Sie nehmen Ihr neues Motorrad mit. Wir freuen uns auf Ihren Besuch.</p></li></ol></div></section>

<section aria-labelledby="svc-h"><div class="wrap">
<div class="head" data-reveal><div><p class="eyebrow">Mehr als ein Händler</p><h2 id="svc-h">Alles rund um Ihr Motorrad.</h2></div><p><a href="service.html">Alle Leistungen ansehen</a></p></div>
<div class="svc">{''.join(f'<article data-reveal style="--d:{i%3*.06}s"><div class="ic"></div><h3>{h}</h3><p>{t}</p></article>' for i, (h, t) in enumerate([('Überwintern', 'Ihr Motorrad kann bei uns überwintern. <a href="ueberwintern.html">Winterplatz anfragen</a>'), ('Inzahlungnahme', 'Wir nehmen Ihr Motorrad beim Kauf in Zahlung.'), ('Finanzierung', 'Auf Anfrage vermitteln wir Finanzierungen.'), ('Ankauf', 'Wir kaufen alles von Aprilia bis Zündapp.'), ('Kommission', 'Ihr Bike steht in unserer Verkaufshalle, wir verkaufen in Ihrem Auftrag.'), ('Import & Wunschsuche', 'Was nicht im Bestand ist, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder.')]))}</div></div></section>

<section class="dark" aria-labelledby="halle-h"><div class="wrap split">
<div data-reveal><p class="eyebrow">Verkaufshalle</p><h2 id="halle-h">Kommen Sie vorbei.</h2>
<p>In unseren Räumlichkeiten wird bereits seit 1950 Motorgeschichte geschrieben: von der Servicestation für Porsche-Trecker über VW- und BMW-Werkstatt bis zum Honda-Autohaus. Heute steht hier ein Bestand gepflegter Motorräder. Bitte kündigen Sie Ihren Besuch kurz telefonisch an.</p>
<ul class="facts"><li><b>Adresse</b><span>{esc(ADDR).replace(' · ', '<br>')}</span></li><li><b>Telefon</b><a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></li><li><b>Zeiten</b><span class="ph-note">[Öffnungszeiten vom Kunden]</span></li></ul>
<a class="btn" href="kontakt.html">Probefahrt anfragen</a></div>
<div class="pic" data-reveal style="--d:.08s"><img src="assets/img/halle-banner.webp" width="{isize('halle-banner.webp')[0]}" height="{isize('halle-banner.webp')[1]}" loading="lazy" alt="Honda Africa Twin und weitere Motorräder vor der Verkaufshalle"></div>
</div></section>

{blick}<section aria-labelledby="faq-h"><div class="wrap" style="max-width:56rem"><div class="head" data-reveal><div><p class="eyebrow">Gut zu wissen</p><h2 id="faq-h">Häufige Fragen</h2></div></div>
{faq_html(FAQ_HOME)}</div></section>
''' + cta_dark()
layout('index.html', 'Motorrad kaufen in Celle | Motorradhandel-Celle', f'Gebrauchte Motorräder in Celle kaufen: {N} Fahrzeuge von Honda, Yamaha, Kawasaki und mehr. Probefahrt, Inzahlungnahme, Winterlager.', home, fold=1, nodes=[seo.faq('index.html', FAQ_HOME), seo.itemlist('index.html', [(b['name'], 'fahrzeug/' + b['slug'] + '.html') for b in BIKES[:6]])], head_extra='<link rel="preload" as="image" href="assets/img/kawasaki-z1000-2015-1.webp" fetchpriority="high">\n', images=['halle-banner.webp'])

# ================= BESTAND =================
sel = lambda i, l, opts: f'<div class="f"><label for="{i}">{l}</label><select id="{i}"><option value="">Alle</option>{opts}</select></div>'
bestand = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Bestand</p><h1>Motorräder</h1><p>Aktuell {N} Fahrzeuge im Bestand. Zwischenverkauf vorbehalten: Bitte bestätigen Sie die Verfügbarkeit kurz telefonisch.</p></div></section>
<div class="filters" role="search" aria-label="Bestand filtern"><div class="wrap"><div class="row">
{sel('f-marke', 'Marke', opt_m)}{sel('f-typ', 'Art', opt_t)}
<div class="f"><label for="f-preis">Preis bis</label><select id="f-preis"><option value="">Egal</option><option value="2000">2.000 €</option><option value="4000">4.000 €</option><option value="6000">6.000 €</option><option value="10000">10.000 €</option></select></div>
<div class="f"><label for="f-sort">Sortierung</label><select id="f-sort"><option value="empf">Empfohlen</option><option value="preis-auf">Preis aufsteigend</option><option value="preis-ab">Preis absteigend</option><option value="neu">Baujahr, neueste zuerst</option><option value="km">Kilometer, niedrigste zuerst</option></select></div>
<p class="count-out" id="count-out" aria-live="polite">{N} Motorräder</p></div></div></div>
<section style="padding-top:2rem"><div class="wrap">
<p class="answer" style="margin-bottom:1.4rem"><strong>Gebrauchte Motorräder in Celle:</strong> Aktuell {N} Fahrzeuge von Honda, Yamaha, Kawasaki, Suzuki, BMW, Triumph und Piaggio, ab {eur(min(b['price'] for b in BIKES))} bis {eur(max(b['price'] for b in BIKES))} (VB). Alle Fahrzeuge nach Terminabsprache probefahrbar. Bestand nach Marke: {', '.join(f'<a href="{CAT_URL[("brand", v)]}">{v}</a>' for f, v in CATS if f == 'brand')}.</p>
<ul class="bikes" id="bikes">{''.join(card(b, lazy=i > 2, d=(i % 3) * .05, prio=(i == 0), tag='h2') for i, b in enumerate(BIKES))}</ul>
<div class="empty" id="empty"><h3>Nichts dabei?</h3><p style="margin-inline:auto">Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Nennen Sie uns Modell, Baujahr und Budget.</p><p><a class="btn" href="kontakt.html#wunsch">Wunschmotorrad anfragen</a> <button class="btn ghost" type="button" id="f-reset">Filter zurücksetzen</button></p></div>
<p class="note" style="margin-top:1.4rem">VB = Verhandlungsbasis. TÜV neu nach Vereinbarung. Angaben laut Händler, ohne Gewähr; Zwischenverkauf und Irrtümer vorbehalten. <span class="ph-note">[Formulierungen vom Kunden bestätigen]</span></p>
</div></section>
<section style="padding-top:0"><div class="wrap"><div class="band" data-reveal><div><h2>Ihr Wunschmotorrad ist nicht dabei?</h2><p>Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder nach Deutschland.</p><div class="acts"><a class="btn light" href="kontakt.html#wunsch">Wunschmotorrad anfragen</a></div></div><ul><li>Modell, Baujahr, Budget nennen</li><li>Wir suchen für Sie</li><li>Inzahlungnahme möglich</li></ul></div></div></section>'''
layout('motorraeder.html', 'Gebrauchte Motorräder in Celle | Motorradhandel-Celle', f'Bestand: {N} gebrauchte Motorräder von Honda, Yamaha, Kawasaki, Suzuki, BMW, Triumph und Piaggio mit Preis, EZ und Kilometerstand.', bestand, active='motorraeder.html', fold=1, kind='CollectionPage', crumbs=[('Motorräder', None)], nodes=[seo.itemlist('motorraeder.html', [(b['name'], 'fahrzeug/' + b['slug'] + '.html') for b in BIKES])], images=[b['img'][0] for b in BIKES])

# ================= DETAIL =================
SHORT = {'yamaha-yzf-r6-silver': 'Yamaha YZF-R6 RJ05', 'honda-varadero-xl1000v': 'Honda Varadero', 'piaggio-hexagon-sport': 'Piaggio Hexagon 125 Sport', 'piaggio-hexagon-lx': 'Piaggio Hexagon 125 LX', 'triumph-speed-triple-955': 'Triumph Speed Triple'}
for b in BIKES:
    thumbs = ''.join(f'<li><button type="button" data-src="../assets/img/{f}" data-alt="{esc(a)}"' + (' aria-current="true"' if i == 0 else '') + f' aria-label="Foto {i+1} anzeigen"><img src="../assets/img/{f}" alt="" width="{isize(f)[0]}" height="{isize(f)[1]}"></button></li>' for i, (f, a) in enumerate(zip(b['img'], b['alts']))) if b['n'] > 1 else ''
    w, h = isize(b['img'][0])
    sim = [x for x in BIKES if x['typ'] == b['typ'] and x['slug'] != b['slug']][:3]
    if len(sim) < 3: sim += [x for x in BIKES if x['slug'] != b['slug'] and x not in sim][:3 - len(sim)]
    simh = ''.join(card(x, pfx='../', d=i * .05) for i, x in enumerate(sim))
    extra = f'<li>{esc(b["hl"])}</li>' if b.get('hl') == 'Mehrfach vorhanden' else ''
    CALC = '''<div class="calc" hidden><h2>Ratenrechner</h2><p class="note">Unverbindliche Beispielrechnung. Die tatsächlichen Konditionen nennt unser Finanzierungspartner nach Prüfung.</p><div class="calc-g"><label>Anzahlung (€)<input type="number" inputmode="numeric" min="0" step="100" value="0" data-c="down"></label><label>Laufzeit (Monate)<select data-c="term"><option>12</option><option>24</option><option selected>36</option><option>48</option><option>60</option></select></label><label>Beispielzins p. a. (%)<input type="number" inputmode="decimal" min="0" max="20" step="0.1" value="6.9" data-c="rate"></label></div><p class="calc-out" aria-live="polite"><span>Monatliche Rate ca.</span> <b data-c-out data-price="@@P@@"></b></p></div>'''.replace('@@P@@', str(b['price']))
    body = f'''<div class="wrap">
<div class="detail"><div class="gal"><div class="main"><img src="../assets/img/{b['img'][0]}" width="{w}" height="{h}" alt="{esc(b['alts'][0])}" fetchpriority="high"></div>{f'<ul class="thumbs">{thumbs}</ul>' if thumbs else ''}</div>
<div class="buy"><p class="eyebrow">{esc(b['typ'])} · {esc(b['brand'])}</p><h1>{esc(b['name'])}</h1>
<div class="price"><b>{eur(b['price'])}</b><small>VB (Verhandlungsbasis)</small></div>
<p class="lede">{esc(b['name'])}, Erstzulassung {b['ez']}, {kmf(b['km'])}: gebraucht zu verkaufen bei Motorradhandel-Celle in Celle-Altenhagen. Probefahrt nach Terminabsprache, Inzahlungnahme möglich.</p>
<table class="spec-t"><tr><th>Erstzulassung</th><td>{b['ez']}</td></tr><tr><th>Kilometerstand</th><td>{kmf(b['km'])}</td></tr><tr><th>TÜV</th><td>neu (nach Vereinbarung)</td></tr><tr><th>Zustand</th><td>Gepflegt</td></tr><tr><th>Art</th><td>{esc(b['typ'])}</td></tr></table>
<div class="ctas"><button type="button" class="btn ghost fav-btn" data-fav="{b['slug']}" aria-pressed="false" hidden>Merken</button><a class="btn" href="#anfrage">Probefahrt anfragen</a><a class="btn ghost" href="tel:{PHONE_TEL}">Anrufen: {PHONE_TXT}</a><a class="btn wa" href="https://wa.me/{PHONE_TEL.lstrip('+')}?text={esc(b['name'].replace(' ', '%20'))}" rel="noopener noreferrer" target="_blank">Per WhatsApp fragen</a></div>
{CALC}<ul class="trustline">{extra}<li>Probefahrt nach Terminabsprache</li><li>Inzahlungnahme Ihres Motorrads möglich</li><li>Finanzierung auf Anfrage</li></ul>
<p class="note" style="margin-top:1rem">Zwischenverkauf vorbehalten. Bitte bestätigen Sie die Verfügbarkeit kurz telefonisch.</p>
<p class="note">Mehr: <a href="../{CAT_URL[('brand', b['brand'])] if ('brand', b['brand']) in CAT_URL else 'motorraeder.html'}">{'Alle ' + b['brand'] + ' im Bestand' if ('brand', b['brand']) in CAT_URL else 'Alle Motorräder'}</a>{(' · <a href="../' + CAT_URL[('typ', b['typ'])] + '">Alle ' + b['typ'] + '</a>') if ('typ', b['typ']) in CAT_URL else ''} · <a href="../ratgeber/gebrauchtes-motorrad-kaufen.html">Checkliste Gebrauchtkauf</a></p></div></div></div>
<section class="alt" style="padding-top:2.5rem"><div class="wrap" style="max-width:46rem"><div id="probefahrt">{probe_form('anfrage', b['name'], 'Probefahrt anfragen', f'Sie interessieren sich für die {esc(b["name"])}? Wir melden uns bei Ihnen und sprechen einen Termin ab.', pfx='../')}</div></div></section>
<div class="sticky-cta" aria-label="Schnellkontakt"><a class="btn ghost sm" href="tel:{PHONE_TEL}">Anrufen</a><a class="btn wa sm" href="https://wa.me/{PHONE_TEL.lstrip('+')}?text={esc(b['name'].replace(' ', '%20'))}" rel="noopener noreferrer" target="_blank">WhatsApp</a><a class="btn sm" href="#anfrage">Probefahrt</a></div>
<section><div class="wrap"><div class="head"><div><p class="eyebrow">Weitere Motorräder</p><h2>Das könnte Ihnen auch gefallen.</h2></div><p><a href="../motorraeder.html">Alle ansehen</a></p></div><ul class="bikes">{simh}</ul></div></section>'''
    d_title = next(t for t in (f"{b['name']} gebraucht, {eur(b['price'])} | Motorradhandel-Celle", f"{b['name']}, {eur(b['price'])} | Motorradhandel-Celle", f"{SHORT.get(b['slug'], b['name'])}, {eur(b['price'])} | Motorradhandel-Celle", f"{SHORT.get(b['slug'], b['name'])} | Motorradhandel-Celle") if len(t) <= 60)
    d_desc = f"{b['name']}, EZ {b['ez']}, {kmf(b['km'])}, {eur(b['price'])} VB: gebraucht kaufen in Celle. Probefahrt nach Terminabsprache, Inzahlungnahme möglich."
    fn_ = f"fahrzeug/{b['slug']}.html"
    layout(fn_, d_title, d_desc, body, sub=True, active='motorraeder.html', fold=1, probe='fahrzeug/' + b['slug'] + '.html#anfrage', kind='ItemPage', crumbs=[('Motorräder', 'motorraeder.html'), (b['name'], None)], nodes=[seo.product(b, fn_, [f"{seo.DOMAIN}/assets/img/{f}" for f in b['img']], d_desc)], ogimg=b['slug'], images=b['img'])

# ================= ANKAUF =================
ank = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Motorrad verkaufen</p><h1>Wir kaufen Ihr Motorrad.</h1><p>Auch wenn Sie kein neues bei uns kaufen. Von Aprilia bis Zündapp. Senden Sie uns die Eckdaten, dann sprechen wir darüber und machen Ihnen ein Angebot.</p></div></section>
<section style="padding-block:2rem 0"><div class="wrap"><p class="answer"><strong>Kurz erklärt:</strong> Wir kaufen Ihr Motorrad an, von Aprilia bis Zündapp. Senden Sie uns Modell, Baujahr, Kilometerstand, TÜV, Preisvorstellung und Fotos, dann sprechen wir darüber und machen Ihnen ein Angebot. Alternativ nehmen wir es in Zahlung, es überwintert bei uns oder wir verkaufen in Kommission.</p></div></section>
<section><div class="wrap split" style="align-items:start"><div data-reveal>
<h2>Ihre Möglichkeiten</h2><ul class="svc" style="grid-template-columns:1fr;list-style:none;padding:0;margin:0">
<li><article><div class="ic"></div><h3>Ankauf</h3><p>Wir kaufen Ihr Motorrad an und machen Ihnen ein Angebot.</p></article></li>
<li><article><div class="ic"></div><h3>Inzahlungnahme</h3><p>Sie kaufen ein Motorrad bei uns, wir nehmen Ihr altes in Zahlung.</p></article></li>
<li><article><div class="ic"></div><h3>Überwintern und verkaufen</h3><p>Ihr Bike kann bei uns überwintern oder im Winter in unserer Verkaufshalle stehen. <a href="ueberwintern.html">Zum Winterlager</a></p></article></li>
<li><article><div class="ic"></div><h3>Kommission</h3><p>Ihr Bike steht in unserer Verkaufshalle. Sie verkaufen es selbst von hier oder in Kommission in Ihrem Auftrag.</p></article></li></ul></div>
<div data-reveal style="--d:.08s"><form class="card-f" id="verkauf" method="get" action="danke.html" data-demo-form data-next="danke.html" novalidate><h2 style="font-size:1.8rem;margin:0">Angebot anfordern</h2><p style="font-size:1rem">Je genauer Ihre Angaben, desto schneller können wir Ihnen ein Angebot machen.</p>
<div class="form-2"><div><label for="v-mo">Marke und Modell</label><input id="v-mo" name="modell" type="text" required></div><div><label for="v-ez">Erstzulassung / Baujahr</label><input id="v-ez" name="ez" type="text" required></div></div>
<div class="form-2"><div><label for="v-km">Kilometerstand</label><input id="v-km" name="km" type="text" required></div><div><label for="v-tu">TÜV bis</label><input id="v-tu" name="tuev" type="text"></div></div>
<div class="form-2"><div><label for="v-pr">Preisvorstellung</label><input id="v-pr" name="preis" type="text"></div><div><label for="v-pl">Standort / Postleitzahl</label><input id="v-pl" name="plz" type="text" autocomplete="postal-code"></div></div>
<div class="form-2"><div><label for="v-na">Name</label><input id="v-na" name="name" type="text" autocomplete="name" required></div><div><label for="v-te">Telefon</label><input id="v-te" name="telefon" type="tel" autocomplete="tel" required></div></div>
<div><label for="v-fo">Fotos <span class="hint">(optional, mehrere möglich)</span></label><input id="v-fo" name="fotos" type="file" accept="image/*" multiple></div>
<div class="chk"><input id="v-iz" name="inzahlung" type="checkbox"><label for="v-iz" style="margin:0;font-weight:500">Ich möchte das Motorrad in Zahlung geben und ein anderes bei Ihnen kaufen.</label></div>
<div class="hp" aria-hidden="true"><label for="v-w">Nicht ausfüllen</label><input id="v-w" name="website" type="text" tabindex="-1" autocomplete="off"></div>
<p>Ihre Angaben und Fotos verwenden wir nur zur Bearbeitung Ihrer Anfrage. Mehr in der <a href="datenschutz.html">Datenschutzerklärung</a>.</p><button class="btn" type="submit">Angebot anfordern</button><p class="status" role="status" aria-live="polite"></p></form></div></div></section>''' + cta_dark('Lieber direkt sprechen?', 'Rufen Sie uns an, gern auch abends. Wir sind für Sie da.')
layout('ankauf.html', 'Motorrad verkaufen in Celle | Motorradhandel-Celle', 'Motorrad verkaufen in Celle: Wir kaufen an, von Aprilia bis Zündapp. Ankauf, Inzahlungnahme und Kommission. Jetzt Angebot anfordern.', ank, active='ankauf.html', fold=1, crumbs=[('Verkaufen', None)], nodes=[seo.service('ankauf.html', 'Motorrad-Ankauf und Inzahlungnahme', 'Ankauf von Motorrädern aller Marken, Inzahlungnahme beim Kauf und Kommissionsverkauf in Celle.', 'Motorrad Ankauf')])

# ================= ÜBERWINTERN =================
ph = lambda t: f'<span class="ph-note">[{t}]</span>'
cond = ''.join(f'<tr><th>{a}</th><td>{ph(b)}</td></tr>' for a, b in [('Einlagerungszeitraum', 'z. B. Oktober bis April, vom Kunden festlegen'), ('Preis', 'pro Monat oder pauschal je Saison, vom Kunden'), ('Leistungen im Winterlager', 'z. B. Batteriepflege, Winter-Check: vom Kunden bestätigen'), ('Versicherung und Haftung', 'vom Kunden / Anwalt formulieren'), ('Bringen und Abholen', 'Termin, ggf. Transport: vom Kunden'), ('Anzahl Winterplätze', 'Kapazität vom Kunden, nur nennen wenn belegbar')])
FAQ_WINT = [
 ('Kann mein Motorrad bei Ihnen überwintern?', 'Ja, Ihr Bike kann bei uns überwintern. Fragen Sie Ihren Winterplatz an, wir stimmen alles mit Ihnen ab.'),
 ('Wo kann ich in Celle mein Motorrad überwintern?', 'Bei Motorradhandel-Celle in Celle-Altenhagen, Lachtehäuserstraße 6. Rufen Sie an (01520 888 0000) oder senden Sie die Anfrage für Ihren Winterplatz.'),
 ('Was kostet das Überwintern?', ph('Preis vom Kunden')),
 ('Wann kann ich mein Motorrad bringen und wieder abholen?', 'Das sprechen wir mit Ihnen ab. ' + ph('Zeiten vom Kunden')),
 ('Kann ich mein Motorrad im Winter verkaufen?', 'Ja. Es kann in unserer Verkaufshalle stehen, Sie verkaufen selbst von dort oder in Kommission in Ihrem Auftrag. Wir kaufen Ihr Motorrad auch an. <a href="ankauf.html">Mehr zum Verkauf</a>'),
 ('Wie ist mein Motorrad versichert?', ph('Versicherung und Haftung vom Kunden')),
 ('Worauf muss ich vor dem Einlagern achten?', 'Eine Checkliste mit allgemeinen Hinweisen finden Sie im <a href="ratgeber/motorrad-ueberwintern.html">Ratgeber: Motorrad überwintern</a>.')]
wint = f'''<section class="page-hero winter-hero"><div class="wrap"><p class="eyebrow">{SNOW} Winterlager</p><h1>Ihr Motorrad überwintert bei uns.</h1><p>Die Saison ist vorbei, Ihr Motorrad braucht einen Platz? Wir stellen es für den Winter ein. Fragen Sie jetzt Ihren Winterplatz an, wir melden uns bei Ihnen.</p><div style="display:flex;flex-wrap:wrap;gap:.7rem;margin-top:1.6rem"><a class="btn ice" href="#winterplatz">Winterplatz anfragen</a><a class="btn ghost" href="tel:{PHONE_TEL}">Anrufen: {PHONE_TXT}</a></div></div></section>
<section style="padding-block:2rem 0"><div class="wrap"><p class="answer"><strong>Kurz erklärt:</strong> Motorradhandel-Celle in Celle-Altenhagen stellt Ihr Motorrad auf Wunsch über den Winter ein. Sie fragen Ihren Winterplatz an, wir stimmen Zeitraum und Konditionen mit Ihnen ab, Sie bringen das Motorrad und holen es im Frühjahr wieder ab. Alternativ kann es in unserer Verkaufshalle stehen und verkauft werden.</p></div></section>
<section><div class="wrap"><div class="svc" style="grid-template-columns:repeat(3,1fr)">
<article data-reveal><div class="ic ice"></div><h2 style="font-size:1.5rem">Bei uns überwintern</h2><p>Gern kann Ihr Bike bei uns überwintern. Sie bringen es vorbei und holen es im Frühjahr wieder ab.</p></article>
<article data-reveal style="--d:.06s"><div class="ic ice"></div><h2 style="font-size:1.5rem">Im Winter verkaufen</h2><p>Oder Ihr Bike steht in unserer Verkaufshalle: Sie verkaufen es selbst von dort oder in Kommission in Ihrem Auftrag.</p></article>
<article data-reveal style="--d:.12s"><div class="ic ice"></div><h2 style="font-size:1.5rem">Im Frühjahr wechseln</h2><p>Sie möchten ein anderes Motorrad? Wir nehmen Ihr Bike in Zahlung und vermitteln auf Anfrage Finanzierungen. <a href="motorraeder.html">Bestand ansehen</a></p></article></div></div></section>
<section class="alt" style="padding-top:0"><div class="wrap"><div class="head" data-reveal><div><p class="eyebrow">So läuft es ab</p><h2>In vier Schritten durch den Winter.</h2></div><p>Wir sprechen alles persönlich ab.</p></div>
<ol class="steps"><li data-reveal><h3>Winterplatz anfragen</h3><p>Modell und gewünschten Zeitraum nennen, per Formular oder Telefon.</p></li><li data-reveal style="--d:.07s"><h3>Konditionen abstimmen</h3><p>Wir sprechen Preis, Leistungen und Übergabetermin mit Ihnen ab.</p></li><li data-reveal style="--d:.14s"><h3>Motorrad bringen</h3><p>Sie bringen Ihr Bike zum vereinbarten Termin zu uns.</p></li><li data-reveal style="--d:.21s"><h3>Im Frühjahr abholen</h3><p>Zum Saisonstart holen Sie Ihr Motorrad wieder ab.</p></li></ol></div></section>
<section><div class="wrap split" style="align-items:start"><div data-reveal id="konditionen"><p class="eyebrow">Konditionen</p><h2>Was Sie wissen müssen.</h2><p>Die genauen Konditionen stimmen wir persönlich mit Ihnen ab.</p><table class="spec-t">{cond}</table></div>
<div data-reveal style="--d:.08s" id="winterplatz"><form class="card-f" id="winterform" method="get" action="danke.html" data-demo-form data-next="danke.html" novalidate><h2 style="font-size:1.8rem;margin:0">Winterplatz anfragen</h2><p style="font-size:1rem">Wir melden uns bei Ihnen und sprechen Zeitraum und Konditionen ab.</p>
<div class="form-2"><div><label for="w-n">Name</label><input id="w-n" name="name" type="text" autocomplete="name" required></div><div><label for="w-t">Telefon</label><input id="w-t" name="telefon" type="tel" autocomplete="tel" required></div></div>
<div class="form-2"><div><label for="w-m">Marke und Modell</label><input id="w-m" name="modell" type="text" required></div><div><label for="w-z">Zeitraum <span class="hint">(von bis)</span></label><input id="w-z" name="zeitraum" type="text" placeholder="z. B. November bis April"></div></div>
<div><label for="w-e">E-Mail <span class="hint">(optional)</span></label><input id="w-e" name="mail" type="email" autocomplete="email"></div>
<div><label for="w-b">Besonderheiten oder Wünsche <span class="hint">(optional)</span></label><textarea id="w-b" name="nachricht" rows="3"></textarea></div>
<div class="chk"><input id="w-k" name="kommission" type="checkbox"><label for="w-k" style="margin:0;font-weight:500">Ich möchte das Motorrad im Winter zusätzlich zum Verkauf anbieten (Kommission).</label></div>
<div class="chk"><input id="w-i" name="wechsel" type="checkbox"><label for="w-i" style="margin:0;font-weight:500">Ich möchte im Frühjahr ein anderes Motorrad kaufen (Inzahlungnahme).</label></div>
<div class="hp" aria-hidden="true"><label for="w-w">Nicht ausfüllen</label><input id="w-w" name="website" type="text" tabindex="-1" autocomplete="off"></div>
<p>Ihre Angaben verwenden wir nur zur Bearbeitung Ihrer Anfrage. Mehr in der <a href="datenschutz.html">Datenschutzerklärung</a>.</p><button class="btn ice" type="submit">Winterplatz anfragen</button><p class="status" role="status" aria-live="polite"></p></form></div></div></section>
<section class="alt"><div class="wrap" style="max-width:56rem"><div class="head" data-reveal><div><p class="eyebrow">Gut zu wissen</p><h2>Häufige Fragen zum Winterlager</h2></div></div>{faq_html(FAQ_WINT)}</div></section>''' + cta_dark('Winterplatz sichern.', 'Rufen Sie kurz an oder senden Sie die Anfrage. Wir sprechen Zeitraum und Konditionen mit Ihnen ab.')
layout('ueberwintern.html', 'Motorrad überwintern in Celle | Motorradhandel-Celle', 'Motorrad überwintern in Celle: Winterplatz anfragen, im Winter verkaufen oder im Frühjahr wechseln. Winterlager in Celle-Altenhagen.', wint, active='ueberwintern.html', fold=1, crumbs=[('Überwintern', None)], nodes=[seo.service('ueberwintern.html', 'Motorrad-Winterlager', 'Ihr Motorrad kann bei Motorradhandel-Celle überwintern. Zeitraum und Konditionen nach Absprache.', 'Motorrad überwintern'), seo.faq('ueberwintern.html', FAQ_WINT)], ogimg='winterlager')

# ================= SERVICE =================
svc = '<section class="page-hero"><div class="wrap"><p class="eyebrow">Service & Finanzierung</p><h1>Mehr als ein Händler.</h1><p>Wir verkaufen, kaufen an, nehmen in Zahlung, vermitteln Finanzierungen und besorgen Ihr Wunschmotorrad.</p></div></section><section><div class="wrap"><div class="svc">' + ''.join(f'<article id="{i}" data-reveal style="--d:{n%3*.06}s"><div class="ic"></div><h2>{h}</h2><p>{t}</p></article>' for n, (i, h, t) in enumerate([
 ('inzahlungnahme', 'Inzahlungnahme', 'Sie kaufen bei uns, wir nehmen Ihr Motorrad in Zahlung. Schicken Sie uns Modell, Baujahr, Kilometerstand und Fotos.'),
 ('finanzierung', 'Finanzierung', 'Auf Anfrage vermitteln wir Finanzierungen. Sprechen Sie uns an. <span class="ph-note">[Partnerbank und Konditionen vom Kunden]</span>'),
 ('ankauf', 'Ankauf', 'Wir kaufen alles von Aprilia bis Zündapp, auch wenn Sie kein Motorrad bei uns kaufen.'),
 ('kommission', 'Kommissionsverkauf', 'Ihr Bike steht in unserer Verkaufshalle. Sie verkaufen es selbst von dort oder in Kommission in Ihrem Auftrag.'),
 ('ueberwintern', 'Überwintern', 'Ihr Motorrad kann bei uns überwintern. <span class="ph-note">[Konditionen vom Kunden]</span> <a href="ueberwintern.html">Winterplatz anfragen</a>'),
 ('import', 'Import & Wunschsuche', 'Was nicht im Bestand ist, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder nach Deutschland.'),
 ('zubehoer', 'Zubehör & Helme', 'Bitte vorher anrufen. <span class="ph-note">[Sortiment vom Kunden]</span>'),
 ('werkstatt', 'Werkstatt & Service', '<span class="ph-note">[Leistungsumfang der Werkstatt vom Kunden bestätigen]</span>'),
 ('probefahrt', 'Probefahrt', 'Bei Interesse sprechen wir einen Termin ab. Rufen Sie an oder senden Sie die Anfrage.')])) + '</div></div></section>' + cta_dark()
layout('service.html', 'Inzahlungnahme & Finanzierung | Motorradhandel-Celle', 'Inzahlungnahme, Finanzierung auf Anfrage, Ankauf, Kommission, Winterlager, Import und Wunschsuche beim Motorradhandel in Celle.', svc, active='service.html', fold=1, crumbs=[('Service & Finanzierung', None)])

# ================= ÜBER UNS =================
ue = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Über uns</p><h1>Ein Bikerteam. Seit 17 Jahren.</h1><p>Ingo Werner und sein Team: ein fünfköpfiges, leidenschaftliches Bikerteam. Aus dem gemeinsamen Hobby ist ein Geschäft geworden.</p></div></section>
<section><div class="wrap split"><div data-reveal><h2>Aus Leidenschaft Händler.</h2><p>Man kennt sich seit 17 Jahren durch das gemeinsame Hobby. Wir importieren Motorräder, kaufen gern auch Ihr Bike an, nehmen in Zahlung und vermitteln gegebenenfalls Finanzierungen. Ihr Bike kann bei uns überwintern oder in unserer Verkaufshalle stehen, Sie verkaufen es selbst von hier oder in Kommission.</p><p>Wir sollten uns kennenlernen: Nehmen Sie Kontakt mit uns auf, per Telefon oder E-Mail, gern auch abends.</p><a class="btn" href="kontakt.html">Kontakt aufnehmen</a></div>
<div class="pic" data-reveal style="--d:.08s"><img src="assets/img/halle.webp" width="{isize('halle.webp')[0]}" height="{isize('halle.webp')[1]}" alt="Blick in die Verkaufshalle mit vielen Motorrädern" loading="lazy"></div></div></section>
<section class="alt"><div class="wrap" style="max-width:56rem" data-reveal><p class="eyebrow">Der Standort</p><h2>Hier wird seit 1950 Motorgeschichte geschrieben.</h2><p>Es begann damals mit einer Servicestation für Porsche-Trecker, dann war es eine VW-Werkstatt. Es folgten BMW, Honda und Hyundai mit Verkaufsausstellung und Werkstatt. Heute ist hier die Verkaufshalle von Motorradhandel-Celle.</p><p class="note"><span class="ph-note">[Historie und Jahreszahlen vom Kunden bestätigen]</span></p></div></section>''' + cta_dark('Lernen Sie uns kennen.', 'Wir freuen uns über einen persönlichen Besuch. Bitte vorher kurz anrufen.')
layout('ueber-uns.html', 'Über uns: Bikerteam in Celle | Motorradhandel-Celle', 'Ingo Werner und sein fünfköpfiges Bikerteam: Motorradhandel in Celle-Altenhagen mit 17 Jahren Erfahrung, Import, Ankauf und Inzahlungnahme.', ue, active='ueber-uns.html', fold=1, kind='AboutPage', crumbs=[('Über uns', None)], images=['halle.webp'])

# ================= KONTAKT =================
ko = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Kontakt</p><h1>Probefahrt, Fragen, Wunschmotorrad.</h1><p>Rufen Sie uns an, gern auch abends und am Wochenende, oder senden Sie die Anfrage. Wir melden uns bei Ihnen.</p></div></section>
<section><div class="wrap split" style="align-items:start"><div data-reveal>
<h2 style="font-size:2.2rem">Motorradhandel-Celle</h2>
<ul class="facts"><li><b>Telefon</b><a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></li><li><b>E-Mail</b><a href="mailto:{MAIL}">{MAIL}</a> <span class="ph-note">[zwei E-Mail-Adressen auf alter Seite: bestätigen]</span></li><li><b>Adresse</b><span>Inhaber Ingo Werner<br>Lachtehäuserstraße 6<br>29223 Celle (Altenhagen)</span></li><li><b>Zeiten</b><span class="ph-note">[Öffnungs- und Erreichbarkeitszeiten vom Kunden]</span></li><li><b>Anfahrt</b><a href="https://www.openstreetmap.org/search?query=Lachteh%C3%A4userstra%C3%9Fe%206%2C%2029223%20Celle" rel="noopener noreferrer" target="_blank">Route in der Karte öffnen (externer Dienst, neuer Tab)</a></li></ul>
<div class="ctas" style="max-width:24rem"><a class="btn" href="tel:{PHONE_TEL}">Jetzt anrufen</a><a class="btn wa" href="https://wa.me/{PHONE_TEL.lstrip('+')}" rel="noopener noreferrer" target="_blank">WhatsApp schreiben</a></div></div>
<div data-reveal style="--d:.08s" id="probefahrt">{probe_form('kontaktform', '', 'Probefahrt oder Frage', 'Sagen Sie uns, für welches Motorrad Sie sich interessieren.', 'Anfrage senden')}</div></div></section>
<section class="alt" id="wunsch"><div class="wrap" style="max-width:46rem" data-reveal><h2>Wunschmotorrad suchen</h2><p>Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Nennen Sie uns Modell, Baujahr und Budget.</p>{probe_form('wunschform', 'Wunschmotorrad', 'Wunschmotorrad anfragen', 'Welches Motorrad suchen Sie? Schreiben Sie Modell, Baujahr, Kilometer und Budget in die Nachricht.', 'Suche starten')}</div></section>'''
layout('kontakt.html', 'Kontakt & Probefahrt | Motorradhandel-Celle', 'Kontakt zu Motorradhandel-Celle in Celle-Altenhagen: Telefon 01520 8880000, Probefahrt anfragen, Wunschmotorrad suchen.', ko, active='kontakt.html', fold=1, kind='ContactPage', crumbs=[('Kontakt', None)])

# ================= DANKE / RECHT / 404 =================
dk = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Danke</p><h1>Anfrage eingegangen.</h1><p>Wir melden uns bei Ihnen. <span class="ph-note">[Antwortzeit nur nennen, wenn der Kunde sie zusagt]</span></p></div></section>
<section><div class="wrap"><h2 style="font-size:2rem">Während Sie warten</h2><ul class="bikes" style="margin-top:1rem">{''.join(card(b, d=i*.05) for i, b in enumerate(BIKES[:3]))}</ul><p style="margin-top:1.5rem"><a class="btn" href="motorraeder.html">Alle Motorräder ansehen</a> <a class="btn ghost" href="tel:{PHONE_TEL}">Lieber anrufen</a></p></div></section>'''
mk = f'''<section style="padding-top:2.5rem"><div class="wrap"><div class="head"><div><p class="eyebrow">Merkliste</p><h1 style="font-size:clamp(2.2rem,5vw,3.4rem)">Ihre gemerkten Motorräder.</h1></div></div>
<p class="lede" id="ml-empty">Sie haben noch kein Motorrad gemerkt. Tippen Sie bei einem Fahrzeug auf das Herz, dann finden Sie es hier wieder. Die Merkliste bleibt nur auf diesem Gerät gespeichert.</p>
<ul class="bikes" id="ml-list">{''.join(card(x, d=0, tag='h2') for x in BIKES)}</ul>
<p class="note" style="margin-top:1.5rem"><a href="motorraeder.html">Zum gesamten Bestand</a> · <a href="kontakt.html">Probefahrt für mehrere Motorräder anfragen</a></p></div></section>'''
layout('merkliste.html', 'Merkliste | Motorradhandel-Celle', 'Ihre gemerkten Motorräder bei Motorradhandel-Celle in Celle-Altenhagen: Fahrzeuge vergleichen, Probefahrt anfragen und die Auswahl später wieder öffnen.', mk, fold=1, index=False, crumbs=[('Merkliste', None)])
layout('danke.html', 'Danke für Ihre Anfrage | Motorradhandel-Celle', 'Ihre Anfrage bei Motorradhandel-Celle ist eingegangen. Wir melden uns bei Ihnen und sprechen alles Weitere persönlich mit Ihnen ab.', dk, fold=1, index=False)
imp = f'''<section><div class="wrap legal-page"><h1 style="font-size:var(--fs-2)">Impressum</h1><p><strong class="ph-note">[Rechtstext liefert der Kunde (Generator oder Anwalt)]</strong> Markentrix bindet ihn ein und prüft nur die Vollständigkeit der Pflichtangaben.</p><h2 style="font-size:1.6rem;margin-top:1.5rem">Angaben der bisherigen Website (vom Kunden zu prüfen und zu aktualisieren)</h2><p>Firma: Motorradhandel-Celle<br>Inhaber: Ingo Werner<br>Lachtehäuserstraße 6<br>29223 Celle (Altenhagen)</p><p>Telefon: +49 1520 8880000<br>E-Mail: {MAIL}<br>Handelsregister: Celle<br>Umsatzsteuer-Identifikationsnummer nach § 27a UStG: DE174231599<br>Gerichtsstand: Celle</p></div></section>'''
layout('impressum.html', 'Impressum | Motorradhandel-Celle', 'Impressum von Motorradhandel-Celle, Inhaber Ingo Werner, Lachtehäuserstraße 6, 29223 Celle-Altenhagen. Angaben nach Telemediengesetz.', imp, fold=0)
dat = '<section><div class="wrap legal-page"><h1 style="font-size:var(--fs-2)">Datenschutzerklärung</h1><p><strong class="ph-note">[Rechtstext liefert der Kunde (Generator oder Anwalt)]</strong></p><p>Hinweise für die Erstellung: Diese Website lädt keine Drittanbieter-Inhalte, Schriften und Skripte sind selbst gehostet, es gibt kein Tracking und keine Cookies. Hosting: Hetzner Online GmbH, Serverstandort Nürnberg. Formulare verarbeiten Name, Telefon, E-Mail und Anliegen (beim Ankauf zusätzlich Fahrzeugdaten und Fotos) zur Bearbeitung der Anfrage. WhatsApp- und Kartenlinks führen nur auf Klick zu externen Diensten.</p></div></section>'
layout('datenschutz.html', 'Datenschutz | Motorradhandel-Celle', 'Datenschutzerklärung von Motorradhandel-Celle, Celle-Altenhagen: Informationen zur Verarbeitung personenbezogener Daten auf dieser Website.', dat, fold=0)
layout('404.html', 'Seite nicht gefunden | Motorradhandel-Celle', 'Diese Seite wurde nicht gefunden. Zum Bestand gebrauchter Motorräder in Celle oder zurück zur Startseite von Motorradhandel-Celle.', '<section><div class="wrap"><p class="eyebrow">Fehler 404</p><h1 style="font-size:var(--fs-2)">Diese Seite gibt es nicht.</h1><p><a class="btn" href="motorraeder.html">Zum Bestand</a> <a class="btn ghost" href="index.html">Startseite</a></p></div></section>', fold=0, index=False)

# ================= MARKEN- UND ART-SEITEN =================
TYPE_TXT = {
 'Sportler': 'Sportler haben eine sportliche Sitzposition und meist eine Vollverkleidung. Sie sind für Kurven, Leistung und Landstraße gebaut.',
 'Naked Bike': 'Naked Bikes haben keine oder nur wenig Verkleidung und eine aufrechtere Sitzposition. Sie sind vielseitig im Alltag und auf der Landstraße.',
 'Reise & Enduro': 'Reise-Enduros sind komfortable Allrounder für lange Strecken und leichtes Gelände, mit hoher Sitzposition und viel Federweg.',
 'Roller': 'Roller mit 125 cm³ sind günstig im Unterhalt und für die Stadt gemacht. Je nach Führerschein (z. B. Klasse A1 oder B196) dürfen sie gefahren werden.'}
for (fld, val) in CATS:
    items = [b for b in BIKES if b['brand' if fld == 'brand' else 'typ'] == val]
    fn_ = CAT_URL[(fld, val)]
    models = ', '.join(f"{b['model']} ({b['year']})" if fld == 'brand' else f"{b['name']} ({b['year']})" for b in items)
    h1 = f'Gebrauchte {val} Motorräder in Celle' if fld == 'brand' else f'{val}: gebrauchte Motorräder in Celle'
    title = f'Gebrauchte {val} in Celle | Motorradhandel-Celle' if fld == 'brand' else f'{val} gebraucht in Celle | Motorradhandel-Celle'
    intro = (f"Aktuell haben wir {len(items)} gebrauchte {val} im Bestand: {models}. " if fld == 'brand' else f"{TYPE_TXT[val]} Aktuell haben wir {len(items)} gebrauchte {val} im Bestand: {models}. ") + f"Die Preise liegen zwischen {eur(min(b['price'] for b in items))} und {eur(max(b['price'] for b in items))} (VB), die Kilometerstände zwischen {kmf(min(b['km'] for b in items))} und {kmf(max(b['km'] for b in items))}. Alle Fahrzeuge können nach Terminabsprache probegefahren werden."
    others = ''.join(f'<li><a href="{u.split("/")[-1]}">{esc(n)}</a></li>' for n, u in CAT_LINKS if u != fn_)
    body = f"""<section class="page-hero"><div class="wrap"><p class="eyebrow">Bestand</p><h1>{esc(h1)}</h1><p>Direkt vom Händler in Celle-Altenhagen, mit Probefahrt, Inzahlungnahme und auf Wunsch Finanzierung.</p></div></section>
<section style="padding-bottom:0"><div class="wrap"><p class="answer">{intro}</p></div></section>
<section><div class="wrap"><ul class="bikes">{''.join(card(b, pfx='../', lazy=i > 2, d=(i % 3) * .05, prio=(i == 0), tag='h2') for i, b in enumerate(items))}</ul>
<p class="note" style="margin-top:1.2rem">VB = Verhandlungsbasis. Zwischenverkauf vorbehalten, bitte Verfügbarkeit telefonisch bestätigen.</p>
<h2 style="font-size:1.6rem;margin-top:2.5rem">Weitere Marken und Arten</h2><ul class="chips-links">{others}<li><a href="../motorraeder.html">Alle Motorräder</a></li></ul></div></section>
<section style="padding-top:0"><div class="wrap"><div class="band"><div><h2>Nicht das Richtige dabei?</h2><p>Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Nennen Sie uns Modell, Baujahr und Budget.</p><div class="acts"><a class="btn light" href="../kontakt.html#wunsch">Wunschmotorrad anfragen</a></div></div><ul><li>Probefahrt nach Terminabsprache</li><li>Inzahlungnahme möglich</li><li>Finanzierung auf Anfrage</li></ul></div></div></section>"""
    desc = f"{len(items)} gebrauchte {val} in Celle: {', '.join(b['model'] if fld == 'brand' else b['name'] for b in items[:3])} und mehr, ab {eur(min(b['price'] for b in items))}. Probefahrt nach Terminabsprache."
    layout(fn_, title, desc[:155], body, sub=True, active='motorraeder.html', fold=1, kind='CollectionPage', crumbs=[('Motorräder', 'motorraeder.html'), (val, None)], nodes=[seo.itemlist(fn_, [(b['name'], 'fahrzeug/' + b['slug'] + '.html') for b in items])], images=[b['img'][0] for b in items])

# ================= RATGEBER =================
def checklist(items): return '<ul class="checks">' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
def guide(fn_, title, desc, h1, lead, sections, faqs, crumb):
    secs = ''.join(f'<h2 id="{slug_(h)}">{h}</h2>{c}' for h, c in sections)
    toc = ''.join(f'<li><a href="#{slug_(h)}">{h}</a></li>' for h, c in sections)
    body = f"""<section class="page-hero"><div class="wrap"><p class="eyebrow">Ratgeber</p><h1>{h1}</h1><p>{lead}</p></div></section>
<section><div class="wrap prose-wrap"><article class="prose"><p class="note">Von Motorradhandel-Celle · Stand: <time datetime="{seo.TODAY}">{seo.TODAY[8:]}.{seo.TODAY[5:7]}.{seo.TODAY[:4]}</time> · Allgemeine Hinweise, Herstellerangaben haben Vorrang. <span class="ph-note">[Inhalt vom Händler prüfen und freigeben]</span></p>
<nav aria-label="Inhalt" class="toc"><strong>Inhalt</strong><ul>{toc}</ul></nav>{secs}
<h2 id="haeufige-fragen">Häufige Fragen</h2>{faq_html(faqs)}</article></div></section>""" + cta_dark(pfx='../')
    layout(fn_, title, desc, body, sub=True, fold=1, kind='Article', crumbs=[(crumb, None)], nodes=[seo.article(fn_, h1, desc, f'{seo.DOMAIN}/assets/og/default.jpg'), seo.faq(fn_, faqs)])
guide('ratgeber/gebrauchtes-motorrad-kaufen.html', 'Motorrad gebraucht kaufen: Checkliste | Motorradhandel-Celle', 'Gebrauchtes Motorrad kaufen: Checkliste für Papiere, Technik, Probefahrt und Kaufvertrag. Praktische Tipps vom Motorradhändler in Celle.',
 'Gebrauchtes Motorrad kaufen: Die Checkliste', 'Worauf Sie beim Kauf eines gebrauchten Motorrads vom Händler achten sollten: Papiere, Zustand, Probefahrt und Vertrag.',
 [('Vor dem Termin', '<p>Legen Sie Ihr Budget inklusive Nebenkosten fest: Versicherung, Steuer, Schutzkleidung und Wartung. Prüfen Sie, ob das Motorrad zu Ihrem Führerschein passt, und informieren Sie sich über bekannte Schwachstellen des Modells.</p>'),
  ('Papiere prüfen', checklist(['Zulassungsbescheinigung Teil I und Teil II sind vorhanden und stimmen überein', 'Die Fahrgestellnummer am Rahmen passt zu den Papieren', 'Aktueller Prüfbericht der Hauptuntersuchung (TÜV) und Zeitpunkt der nächsten HU', 'Serviceheft oder Rechnungen als Nachweis der Wartung', 'Anzahl der Vorbesitzer und plausibler Kilometerstand'])),
  ('Das Motorrad prüfen', checklist(['Reifen: Profil und Alter, das Herstellungsdatum steht als vierstellige DOT-Nummer (Woche und Jahr) auf der Flanke', 'Bremsen: Beläge, Scheiben und Bremsflüssigkeit', 'Kette und Ritzel: Verschleiß und Pflegezustand', 'Gabel und Federbein: keine Ölspuren an den Standrohren', 'Rahmen, Lenker und Verkleidung: Spuren von Stürzen oder Reparaturen', 'Beleuchtung, Blinker, Hupe und Elektrik funktionieren', 'Kaltstart: Motor springt gut an und läuft ruhig'])),
  ('Probefahrt', '<p>Vereinbaren Sie einen Termin und klären Sie vorher Führerschein, Schutzkleidung und Versicherungsschutz. Achten Sie auf Geräusche, sauberes Schalten, die Bremswirkung und ein gerades Fahrverhalten. Bei uns sprechen wir den Termin für die Probefahrt mit Ihnen ab: <a href="../kontakt.html#probefahrt">Probefahrt anfragen</a>.</p>'),
  ('Preis und Vertrag', '<p>„VB“ steht für Verhandlungsbasis. Lassen Sie sich alle Absprachen schriftlich im Kaufvertrag bestätigen und fragen Sie nach der Gewährleistung. Ihr altes Motorrad können Sie auf Wunsch in Zahlung geben, eine Finanzierung vermitteln wir auf Anfrage. Mehr dazu auf der Seite <a href="../service.html">Service und Finanzierung</a>.</p>'),
  ('Passende Motorräder', '<p>Unseren aktuellen Bestand finden Sie unter <a href="../motorraeder.html">Gebrauchte Motorräder in Celle</a>, nach Art zum Beispiel <a href="../motorraeder/sportler.html">Sportler</a> oder <a href="../motorraeder/reise-enduro.html">Reise &amp; Enduro</a>.</p>')],
 [('Was bedeutet VB beim Motorradpreis?', 'VB steht für Verhandlungsbasis: Der genannte Preis ist ein Verhandlungsvorschlag.'), ('Brauche ich einen Termin für die Probefahrt?', 'Bei uns sprechen wir Probefahrten nach Terminabsprache ab. Rufen Sie kurz an oder senden Sie die Anfrage auf der Fahrzeugseite.'), ('Kann ich mein altes Motorrad in Zahlung geben?', 'Auf Wunsch ja. Nennen Sie uns Modell, Baujahr, Kilometerstand und senden Sie Fotos. <a href="../ankauf.html">Mehr zur Inzahlungnahme</a>')],
 'Gebrauchtes Motorrad kaufen')
guide('ratgeber/motorrad-ueberwintern.html', 'Motorrad überwintern: Checkliste | Motorradhandel-Celle', 'Motorrad überwintern: Checkliste für Reinigung, Batterie, Tank, Reifen und Lagerort. Auf Wunsch überwintert Ihr Motorrad bei uns in Celle.',
 'Motorrad überwintern: Die Checkliste', 'So bringen Sie Ihr Motorrad gut durch den Winter: Vorbereitung, Lagerung und Start in die neue Saison.',
 [('Vor der Einlagerung', checklist(['Reinigen und trocknen, damit kein Schmutz und keine Feuchtigkeit zurückbleiben', 'Kette reinigen und schmieren', 'Ölstand prüfen, bei Bedarf Ölwechsel vor der Standzeit', 'Bei flüssigkeitsgekühlten Motoren den Frostschutz in der Kühlflüssigkeit prüfen', 'Kraftstoff: Tank gefüllt oder Kraftstoffstabilisator, Angaben des Herstellers beachten', 'Batterie laden, bei langer Standzeit ein Erhaltungsladegerät nutzen oder die Batterie ausbauen', 'Reifendruck prüfen, das Motorrad möglichst aufbocken, damit keine Standplatten entstehen'])),
  ('Der richtige Lagerort', '<p>Ideal ist ein trockener, frostfreier und gut belüfteter Raum. Decken Sie das Motorrad mit einer atmungsaktiven Abdeckung ab, damit sich keine Feuchtigkeit staut.</p>'),
  ('Versicherung und Zulassung', '<p>Fragen Sie Ihre Versicherung nach Saisonkennzeichen oder Ruheversicherung. Das kann Kosten sparen, die Regeln unterscheiden sich je nach Anbieter.</p>'),
  ('Winterlager bei uns', '<p>Gern kann Ihr Bike auch bei uns überwintern. Zeitraum und Konditionen stimmen wir persönlich mit Ihnen ab. Alternativ kann es in unserer Verkaufshalle stehen und verkauft werden. <a href="../ueberwintern.html">Winterplatz anfragen</a></p>'),
  ('Im Frühjahr', '<p>Prüfen Sie vor der ersten Fahrt Reifen, Bremsen, Batterie, Öl und Kette. Planen Sie rechtzeitig den Termin für die Hauptuntersuchung.</p>')],
 [('Muss ich mein Motorrad im Winter bewegen?', 'Nein, bei richtiger Vorbereitung ist das nicht nötig. Wichtig sind trockene Lagerung, geladene Batterie und gut gepflegte Technik.'), ('Soll der Tank voll sein?', 'Viele Hersteller empfehlen einen vollen Tank oder einen Kraftstoffstabilisator, damit sich im Tank weniger Kondenswasser bildet. Maßgeblich ist die Betriebsanleitung Ihres Motorrads.'), ('Kann mein Motorrad bei Motorradhandel-Celle überwintern?', 'Ja, Ihr Bike kann bei uns überwintern. Sprechen Sie uns an: <a href="../ueberwintern.html">Winterplatz anfragen</a>.')],
 'Motorrad überwintern')

# ================= DANKE / 404 / DATEIEN =================
for fn_, txt in (('sitemap.xml', seo.sitemap(PAGES)), ('robots.txt', seo.robots(LIVE)), ('llms.txt', seo.llms(BIKES, CAT_LINKS, GUIDES)), ('_redirects', seo.redirects()), ('_headers', seo.headers(LIVE))):
    open(OUT + fn_, 'w').write(txt)
FAV = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#0F0F10"/><path d="M9 7h8l-5 18H4z" fill="#C8102E"/><path d="M19 7h5l-5 18h-5z" fill="#FF4A3D"/></svg>'
open(OUT + 'favicon.svg', 'w').write(FAV)
if LIVE:
    shutil.copytree('assets', 'live/assets', dirs_exist_ok=True)
    print(f'LIVE-Build: {len(PAGES)} Seiten in der Sitemap; Seiten mit Platzhaltern: {len(WARN)}' + (' -> ' + ', '.join(WARN[:6]) + ' ...' if WARN else ''))
