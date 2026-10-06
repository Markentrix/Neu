#!/usr/bin/env python3
"""Erzeugt alle Seiten der Demo (Bestand, Detailseiten, Ankauf, Service, Kontakt ...). Aufruf: python3 build/build.py
Bestand und Preise stehen unten in BIKES (Quelle: bisherige Website, Stand 06.10.2026, Aktualität vom Kunden bestätigen)."""
import re, base64, html, os, json
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
os.makedirs('fahrzeug', exist_ok=True)

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

NAV = [('Motorräder', 'motorraeder.html'), ('Motorrad verkaufen', 'ankauf.html'), ('Service & Finanzierung', 'service.html'), ('Über uns', 'ueber-uns.html'), ('Kontakt', 'kontakt.html')]

def no_reveal_above_fold(body, n):
    parts = body.split('</section>')
    for i in range(min(n, len(parts))): parts[i] = parts[i].replace(' data-reveal', '')
    return '</section>'.join(parts)

def layout(fn, title, desc, body, sub=False, active=None, ld='', fold=1, probe='kontakt.html#probefahrt', head_extra=''):
    p = '../' if sub else ''
    body = no_reveal_above_fold(body, fold)
    nav = ''.join(f'<li><a href="{p}{h}"' + (' aria-current="page"' if h == active else '') + f'>{esc(t)}</a></li>' for t, h in NAV)
    foot = ''.join(f'<li><a href="{p}{h}">{esc(t)}</a></li>' for t, h in NAV)
    page = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#0F0F10">
<link rel="canonical" href="https://[KUNDEN-DOMAIN]/{'' if fn == 'index.html' else ('fahrzeug/' if sub else '') + fn.split('/')[-1]}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<script>document.documentElement.className+=' js'</script>
<link rel="preload" href="{p}assets/fonts/inter-sub-wght.woff2" as="font" type="font/woff2" crossorigin>
{head_extra}<style>{CSS_SUB if sub else CSS_ROOT}</style>
<script src="{p}assets/main.js" defer></script>
{ld}</head>
<body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<div class="demo-bar" data-demo role="note">Designvorschlag von Markentrix für Motorradhandel-Celle · nicht veröffentlicht · Bestand und Preise laut bisheriger Website <span class="ph-note">[Aktualität vom Kunden bestätigen]</span></div>
<header class="site"><div class="wrap">
  <a class="brand" href="{p}index.html" aria-label="Motorradhandel-Celle, zur Startseite"><i aria-hidden="true"></i><span>Motorradhandel<small>CELLE · ALTENHAGEN</small></span></a>
  <nav class="main" id="nav" aria-label="Hauptnavigation" data-open="false"><ul>{nav}</ul></nav>
  <div class="hdr-cta"><a class="btn ghost sm" href="tel:{PHONE_TEL}">{PHONE_TXT}</a><a class="btn sm" href="{p}{probe}">Probefahrt anfragen</a><button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">Menü</button></div>
</div></header>
<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
  <div class="foot-grid">
    <div><h2>Motorradhandel-Celle</h2><p>Inhaber Ingo Werner<br>{esc(ADDR).replace(' · ', '<br>')}</p></div>
    <div><h2>Seiten</h2><ul>{foot}</ul></div>
    <div><h2>Bestand</h2><ul><li><a href="{p}motorraeder.html">Alle Motorräder</a></li><li><a href="{p}motorraeder.html?typ=Sportler">Sportler</a></li><li><a href="{p}motorraeder.html?typ=Naked+Bike">Naked Bikes</a></li><li><a href="{p}motorraeder.html?typ=Reise+%26+Enduro">Reise &amp; Enduro</a></li><li><a href="{p}motorraeder.html?typ=Roller">Roller</a></li></ul></div>
    <div><h2>Kontakt</h2><ul><li><a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></li><li><a href="mailto:{MAIL}">{MAIL}</a></li><li><span class="ph-note">[Öffnungszeiten vom Kunden]</span></li></ul></div>
  </div>
  <div class="legal"><p>© Motorradhandel-Celle</p><p><a href="{p}impressum.html">Impressum</a> · <a href="{p}datenschutz.html">Datenschutz</a></p></div>
</div></footer>
<div class="actionbar" role="navigation" aria-label="Schnellkontakt"><a href="tel:{PHONE_TEL}">Anrufen</a><a class="w" href="https://wa.me/{PHONE_TEL.lstrip('+')}" rel="noopener noreferrer" target="_blank">WhatsApp</a><a class="p" href="{p}{probe}">Probefahrt</a></div>
</body>
</html>
'''
    out = fn
    open(out, 'w').write(page); print(out, len(page) // 1024, 'KB')

def card(b, lazy=True, pfx='', d=0, prio=False, tag='h3'):
    w, h = isize(b['img'][0])
    badge = f'<span class="badge red">{esc(b["hl"])}</span>' if b.get('hl') else '<span class="badge">TÜV neu</span>'
    return f'''<li class="bike" data-marke="{esc(b['brand'])}" data-typ="{esc(b['typ'])}" data-preis="{b['price']}" data-jahr="{b['year']}" data-km="{b['km']}" data-pos="{b['pos']}" data-reveal style="--d:{d}s">
<div class="ph">{badge}<img src="{pfx}assets/img/{b['img'][0]}" width="{w}" height="{h}" alt="{esc(b['alts'][0])}"{' loading="lazy"' if lazy else ''}{' fetchpriority="high"' if prio else ''}></div>
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

LD = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "MotorcycleDealer", "name": "Motorradhandel-Celle", "founder": "Ingo Werner", "address": {"@type": "PostalAddress", "streetAddress": "Lachtehäuserstraße 6", "postalCode": "29223", "addressLocality": "Celle", "addressCountry": "DE"}, "telephone": "+49 1520 8880000", "email": MAIL}, ensure_ascii=False) + '</script>\n'

# ================= START =================
by_price = lambda lo, hi: sum(1 for b in BIKES if lo <= b['price'] <= hi)
feat = BIKES[:6]
opt_m = ''.join(f'<option>{esc(x)}</option>' for x in BRANDS); opt_t = ''.join(f'<option>{esc(x)}</option>' for x in TYPES)
col = [('a', 'kawasaki-z1000-2015-1.webp', 'Kawasaki Z 1000', 'Grüne Kawasaki Z 1000 vor der Verkaufshalle'), ('b', 'honda-crf1000-dct-a-2.webp', 'Honda CRF 1000', 'Honda CRF 1000 Africa Twin Seitenansicht'), ('c', 'suzuki-gsxr750-k1-1.webp', 'Suzuki GSX-R', 'Gelbe Suzuki GSX-R 750'), ('d', 'kawasaki-zx10r-2005-1.webp', 'Kawasaki ZX-10R', 'Kawasaki ZX-10R in Silber')]
FP = ' fetchpriority="high"'
collage = ''.join('<figure class="%s"><img src="assets/img/%s" width="%d" height="%d" alt="%s"%s><figcaption>%s</figcaption></figure>' % (c, f, isize(f)[0], isize(f)[1], esc(a), FP if c == 'a' else '', esc(cap)) for c, f, cap, a in col)
home = f'''<section class="hero"><div class="wrap"><div class="grid">
<div><p class="eyebrow">Motorradhandel in Celle · Altenhagen</p>
<h1>Motorrad kaufen in Celle. <span>Direkt vom Händler.</span></h1>
<p class="lead">Gepflegte Gebrauchtmotorräder von Honda, Yamaha, Suzuki, Kawasaki, BMW und mehr. Mit Probefahrt, Inzahlungnahme und auf Wunsch Finanzierung.</p>
<form class="finder" action="motorraeder.html" method="get" aria-label="Motorrad finden">
<div><label for="h-m">Marke</label><select id="h-m" name="marke"><option value="">Alle</option>{opt_m}</select></div>
<div><label for="h-t">Art</label><select id="h-t" name="typ"><option value="">Alle</option>{opt_t}</select></div>
<div><label for="h-p">Preis bis</label><select id="h-p" name="preis"><option value="">Egal</option><option value="2000">2.000 €</option><option value="4000">4.000 €</option><option value="6000">6.000 €</option><option value="10000">10.000 €</option></select></div>
<button class="btn" type="submit">Zeigen</button></form>
<ul class="chips"><li>Probefahrt nach Terminabsprache</li><li>Inzahlungnahme möglich</li><li>Finanzierung auf Anfrage</li><li>17 Jahre Erfahrung</li></ul></div>
<div class="collage" aria-label="Auswahl aus dem Bestand"><div class="count"><b>{N}</b>Motorräder<br>im Bestand</div>{collage}</div>
</div></div></section>

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
<div class="svc">{''.join(f'<article data-reveal style="--d:{i%3*.06}s"><div class="ic"></div><h3>{h}</h3><p>{t}</p></article>' for i, (h, t) in enumerate([('Inzahlungnahme', 'Wir nehmen Ihr Motorrad beim Kauf in Zahlung.'), ('Finanzierung', 'Auf Anfrage vermitteln wir Finanzierungen.'), ('Ankauf', 'Wir kaufen alles von Aprilia bis Zündapp.'), ('Kommission', 'Ihr Bike steht in unserer Verkaufshalle, wir verkaufen in Ihrem Auftrag.'), ('Überwintern', 'Ihr Motorrad kann bei uns überwintern.'), ('Import & Wunschsuche', 'Was nicht im Bestand ist, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder.')]))}</div></div></section>

<section class="dark" aria-labelledby="halle-h"><div class="wrap split">
<div data-reveal><p class="eyebrow">Verkaufshalle</p><h2 id="halle-h">Kommen Sie vorbei.</h2>
<p>In unseren Räumlichkeiten wird bereits seit 1950 Motorgeschichte geschrieben: von der Servicestation für Porsche-Trecker über VW- und BMW-Werkstatt bis zum Honda-Autohaus. Heute steht hier ein Bestand gepflegter Motorräder. Bitte kündigen Sie Ihren Besuch kurz telefonisch an.</p>
<ul class="facts"><li><b>Adresse</b><span>{esc(ADDR).replace(' · ', '<br>')}</span></li><li><b>Telefon</b><a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></li><li><b>Zeiten</b><span class="ph-note">[Öffnungszeiten vom Kunden]</span></li></ul>
<a class="btn" href="kontakt.html">Probefahrt anfragen</a></div>
<div class="pic" data-reveal style="--d:.08s"><img src="assets/img/halle-banner.webp" width="{isize('halle-banner.webp')[0]}" height="{isize('halle-banner.webp')[1]}" loading="lazy" alt="Honda Africa Twin und weitere Motorräder vor der Verkaufshalle"></div>
</div></section>

<section aria-labelledby="faq-h"><div class="wrap" style="max-width:56rem"><div class="head" data-reveal><div><p class="eyebrow">Gut zu wissen</p><h2 id="faq-h">Häufige Fragen</h2></div></div>
<div class="faq" data-reveal>
<details><summary>Kann ich ein Motorrad probefahren?</summary><div>Ja. Bitte sprechen Sie vorher einen Termin ab, per Telefon oder über die Anfrage auf der Fahrzeugseite.</div></details>
<details><summary>Nehmen Sie mein altes Motorrad in Zahlung?</summary><div>Auf Wunsch ja. Nennen Sie uns Modell, Baujahr, Kilometerstand und schicken Sie Fotos.</div></details>
<details><summary>Gibt es eine Finanzierung?</summary><div>Auf Anfrage vermitteln wir Finanzierungen. Sprechen Sie uns an.</div></details>
<details><summary>Ist das Motorrad noch verfügbar?</summary><div>Unser Bestand wechselt laufend, Zwischenverkäufe sind möglich. Rufen Sie kurz an, dann bestätigen wir die Verfügbarkeit.</div></details>
<details><summary>Mein Wunschmotorrad ist nicht dabei.</summary><div>Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder. Nennen Sie uns Modell, Baujahr und Budget.</div></details>
<details><summary>Welche Gewährleistung gibt es?</summary><div><span class="ph-note">[Gewährleistung und Garantie vom Kunden festlegen und formulieren]</span></div></details>
</div></div></section>
''' + cta_dark()
layout('index.html', 'Motorrad kaufen in Celle | Motorradhandel-Celle', f'Gebrauchte Motorräder in Celle: {N} Fahrzeuge von Honda, Yamaha, Suzuki, Kawasaki und BMW. Probefahrt, Inzahlungnahme, Finanzierung auf Anfrage.', home, active=None, ld=LD, fold=1, head_extra='<link rel="preload" as="image" href="assets/img/kawasaki-z1000-2015-1.webp" fetchpriority="high">\n')

# ================= BESTAND =================
sel = lambda i, l, opts: f'<div class="f"><label for="{i}">{l}</label><select id="{i}"><option value="">Alle</option>{opts}</select></div>'
bestand = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Bestand</p><h1>Motorräder</h1><p>Aktuell {N} Fahrzeuge im Bestand. Zwischenverkauf vorbehalten: Bitte bestätigen Sie die Verfügbarkeit kurz telefonisch.</p></div></section>
<div class="filters" role="search" aria-label="Bestand filtern"><div class="wrap"><div class="row">
{sel('f-marke', 'Marke', opt_m)}{sel('f-typ', 'Art', opt_t)}
<div class="f"><label for="f-preis">Preis bis</label><select id="f-preis"><option value="">Egal</option><option value="2000">2.000 €</option><option value="4000">4.000 €</option><option value="6000">6.000 €</option><option value="10000">10.000 €</option></select></div>
<div class="f"><label for="f-sort">Sortierung</label><select id="f-sort"><option value="empf">Empfohlen</option><option value="preis-auf">Preis aufsteigend</option><option value="preis-ab">Preis absteigend</option><option value="neu">Baujahr, neueste zuerst</option><option value="km">Kilometer, niedrigste zuerst</option></select></div>
<p class="count-out" id="count-out" aria-live="polite">{N} Motorräder</p></div></div></div>
<section style="padding-top:2rem"><div class="wrap">
<ul class="bikes" id="bikes">{''.join(card(b, lazy=i > 2, d=(i % 3) * .05, prio=(i == 0), tag='h2') for i, b in enumerate(BIKES))}</ul>
<div class="empty" id="empty"><h3>Nichts dabei?</h3><p style="margin-inline:auto">Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Nennen Sie uns Modell, Baujahr und Budget.</p><p><a class="btn" href="kontakt.html#wunsch">Wunschmotorrad anfragen</a> <button class="btn ghost" type="button" id="f-reset">Filter zurücksetzen</button></p></div>
<p class="note" style="margin-top:1.4rem">VB = Verhandlungsbasis. TÜV neu nach Vereinbarung. Angaben laut Händler, ohne Gewähr; Zwischenverkauf und Irrtümer vorbehalten. <span class="ph-note">[Formulierungen vom Kunden bestätigen]</span></p>
</div></section>
<section style="padding-top:0"><div class="wrap"><div class="band" data-reveal><div><h2>Ihr Wunschmotorrad ist nicht dabei?</h2><p>Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder nach Deutschland.</p><div class="acts"><a class="btn light" href="kontakt.html#wunsch">Wunschmotorrad anfragen</a></div></div><ul><li>Modell, Baujahr, Budget nennen</li><li>Wir suchen für Sie</li><li>Inzahlungnahme möglich</li></ul></div></div></section>'''
layout('motorraeder.html', 'Gebrauchte Motorräder in Celle: Bestand | Motorradhandel-Celle', f'Aktueller Bestand: {N} gebrauchte Motorräder von Honda, Yamaha, Suzuki, Kawasaki, BMW, Triumph und Piaggio mit Preis, Kilometerstand und Baujahr.', bestand, active='motorraeder.html', fold=1)

# ================= DETAIL =================
for b in BIKES:
    thumbs = ''.join(f'<li><button type="button" data-src="../assets/img/{f}" data-alt="{esc(a)}"' + (' aria-current="true"' if i == 0 else '') + f' aria-label="Foto {i+1} anzeigen"><img src="../assets/img/{f}" alt="" width="{isize(f)[0]}" height="{isize(f)[1]}"></button></li>' for i, (f, a) in enumerate(zip(b['img'], b['alts']))) if b['n'] > 1 else ''
    w, h = isize(b['img'][0])
    sim = [x for x in BIKES if x['typ'] == b['typ'] and x['slug'] != b['slug']][:3]
    if len(sim) < 3: sim += [x for x in BIKES if x['slug'] != b['slug'] and x not in sim][:3 - len(sim)]
    simh = ''.join(card(x, pfx='../', d=i * .05) for i, x in enumerate(sim))
    ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "Product", "name": b['name'], "brand": {"@type": "Brand", "name": b['brand']}, "itemCondition": "https://schema.org/UsedCondition", "image": f"https://[KUNDEN-DOMAIN]/assets/img/{b['img'][0]}", "offers": {"@type": "Offer", "priceCurrency": "EUR", "price": str(b['price']), "seller": {"@type": "Organization", "name": "Motorradhandel-Celle"}}}, ensure_ascii=False) + '</script>\n'
    extra = f'<li>{esc(b["hl"])}</li>' if b.get('hl') == 'Mehrfach vorhanden' else ''
    body = f'''<div class="wrap"><nav class="crumbs" aria-label="Brotkrumen"><a href="../index.html">Start</a> / <a href="../motorraeder.html">Motorräder</a> / {esc(b['name'])}</nav>
<div class="detail"><div class="gal"><div class="main"><img src="../assets/img/{b['img'][0]}" width="{w}" height="{h}" alt="{esc(b['alts'][0])}" fetchpriority="high"></div>{f'<ul class="thumbs">{thumbs}</ul>' if thumbs else ''}</div>
<div class="buy"><p class="eyebrow">{esc(b['typ'])} · {esc(b['brand'])}</p><h1>{esc(b['model'])}</h1>
<div class="price"><b>{eur(b['price'])}</b><small>VB (Verhandlungsbasis)</small></div>
<table class="spec-t"><tr><th>Erstzulassung</th><td>{b['ez']}</td></tr><tr><th>Kilometerstand</th><td>{kmf(b['km'])}</td></tr><tr><th>TÜV</th><td>neu (nach Vereinbarung)</td></tr><tr><th>Zustand</th><td>Gepflegt</td></tr><tr><th>Art</th><td>{esc(b['typ'])}</td></tr></table>
<div class="ctas"><a class="btn" href="#anfrage">Probefahrt anfragen</a><a class="btn ghost" href="tel:{PHONE_TEL}">Anrufen: {PHONE_TXT}</a><a class="btn wa" href="https://wa.me/{PHONE_TEL.lstrip('+')}?text={esc(b['name'].replace(' ', '%20'))}" rel="noopener noreferrer" target="_blank">Per WhatsApp fragen</a></div>
<ul class="trustline">{extra}<li>Probefahrt nach Terminabsprache</li><li>Inzahlungnahme Ihres Motorrads möglich</li><li>Finanzierung auf Anfrage</li></ul>
<p class="note" style="margin-top:1rem">Zwischenverkauf vorbehalten. Bitte bestätigen Sie die Verfügbarkeit kurz telefonisch.</p></div></div></div>
<section class="alt" style="padding-top:2.5rem"><div class="wrap" style="max-width:46rem"><div id="probefahrt">{probe_form('anfrage', b['name'], 'Probefahrt anfragen', f'Sie interessieren sich für die {esc(b["name"])}? Wir melden uns bei Ihnen und sprechen einen Termin ab.', pfx='../')}</div></div></section>
<section><div class="wrap"><div class="head"><div><p class="eyebrow">Weitere Motorräder</p><h2>Das könnte Ihnen auch gefallen.</h2></div><p><a href="../motorraeder.html">Alle ansehen</a></p></div><ul class="bikes">{simh}</ul></div></section>'''
    layout(f'fahrzeug/{b["slug"]}.html', f'{b["name"]}, EZ {b["ez"]}, {eur(b["price"])} | Motorradhandel-Celle', f'{b["name"]} zu verkaufen in Celle: Erstzulassung {b["ez"]}, {kmf(b["km"])}, {eur(b["price"])} VB. Jetzt Probefahrt anfragen.', body, sub=True, active='motorraeder.html', ld=ld, fold=1, probe='fahrzeug/' + b['slug'] + '.html#anfrage')

# ================= ANKAUF =================
ank = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Motorrad verkaufen</p><h1>Wir kaufen Ihr Motorrad.</h1><p>Auch wenn Sie kein neues bei uns kaufen. Von Aprilia bis Zündapp. Senden Sie uns die Eckdaten, dann sprechen wir darüber und machen Ihnen ein Angebot.</p></div></section>
<section><div class="wrap split" style="align-items:start"><div data-reveal>
<h2>Ihre Möglichkeiten</h2><ul class="svc" style="grid-template-columns:1fr;list-style:none;padding:0;margin:0">
<li><article><div class="ic"></div><h3>Ankauf</h3><p>Wir kaufen Ihr Motorrad an und machen Ihnen ein Angebot.</p></article></li>
<li><article><div class="ic"></div><h3>Inzahlungnahme</h3><p>Sie kaufen ein Motorrad bei uns, wir nehmen Ihr altes in Zahlung.</p></article></li>
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
layout('ankauf.html', 'Motorrad verkaufen in Celle: Ankauf & Inzahlungnahme | Motorradhandel-Celle', 'Wir kaufen Ihr Motorrad an, von Aprilia bis Zündapp. Ankauf, Inzahlungnahme und Kommission in Celle. Jetzt Angebot anfordern.', ank, active='ankauf.html', fold=1)

# ================= SERVICE =================
svc = '<section class="page-hero"><div class="wrap"><p class="eyebrow">Service & Finanzierung</p><h1>Mehr als ein Händler.</h1><p>Wir verkaufen, kaufen an, nehmen in Zahlung, vermitteln Finanzierungen und besorgen Ihr Wunschmotorrad.</p></div></section><section><div class="wrap"><div class="svc">' + ''.join(f'<article id="{i}" data-reveal style="--d:{n%3*.06}s"><div class="ic"></div><h3>{h}</h3><p>{t}</p></article>' for n, (i, h, t) in enumerate([
 ('inzahlungnahme', 'Inzahlungnahme', 'Sie kaufen bei uns, wir nehmen Ihr Motorrad in Zahlung. Schicken Sie uns Modell, Baujahr, Kilometerstand und Fotos.'),
 ('finanzierung', 'Finanzierung', 'Auf Anfrage vermitteln wir Finanzierungen. Sprechen Sie uns an. <span class="ph-note">[Partnerbank und Konditionen vom Kunden]</span>'),
 ('ankauf', 'Ankauf', 'Wir kaufen alles von Aprilia bis Zündapp, auch wenn Sie kein Motorrad bei uns kaufen.'),
 ('kommission', 'Kommissionsverkauf', 'Ihr Bike steht in unserer Verkaufshalle. Sie verkaufen es selbst von dort oder in Kommission in Ihrem Auftrag.'),
 ('ueberwintern', 'Überwintern', 'Ihr Motorrad kann bei uns überwintern. <span class="ph-note">[Konditionen vom Kunden]</span>'),
 ('import', 'Import & Wunschsuche', 'Was nicht im Bestand ist, besorgen wir auf Wunsch. Wir importieren regelmäßig Motorräder nach Deutschland.'),
 ('zubehoer', 'Zubehör & Helme', 'Bitte vorher anrufen. <span class="ph-note">[Sortiment vom Kunden]</span>'),
 ('werkstatt', 'Werkstatt & Service', '<span class="ph-note">[Leistungsumfang der Werkstatt vom Kunden bestätigen]</span>'),
 ('probefahrt', 'Probefahrt', 'Bei Interesse sprechen wir einen Termin ab. Rufen Sie an oder senden Sie die Anfrage.')])) + '</div></div></section>' + cta_dark()
layout('service.html', 'Service, Finanzierung & Inzahlungnahme | Motorradhandel-Celle', 'Inzahlungnahme, Finanzierung auf Anfrage, Ankauf, Kommission, Überwintern, Import und Wunschsuche beim Motorradhandel in Celle.', svc, active='service.html', fold=1)

# ================= ÜBER UNS =================
ue = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Über uns</p><h1>Ein Bikerteam. Seit 17 Jahren.</h1><p>Ingo Werner und sein Team: ein fünfköpfiges, leidenschaftliches Bikerteam. Aus dem gemeinsamen Hobby ist ein Geschäft geworden.</p></div></section>
<section><div class="wrap split"><div data-reveal><h2>Aus Leidenschaft Händler.</h2><p>Man kennt sich seit 17 Jahren durch das gemeinsame Hobby. Wir importieren Motorräder, kaufen gern auch Ihr Bike an, nehmen in Zahlung und vermitteln gegebenenfalls Finanzierungen. Ihr Bike kann bei uns überwintern oder in unserer Verkaufshalle stehen, Sie verkaufen es selbst von hier oder in Kommission.</p><p>Wir sollten uns kennenlernen: Nehmen Sie Kontakt mit uns auf, per Telefon oder E-Mail, gern auch abends.</p><a class="btn" href="kontakt.html">Kontakt aufnehmen</a></div>
<div class="pic" data-reveal style="--d:.08s"><img src="assets/img/halle.webp" width="{isize('halle.webp')[0]}" height="{isize('halle.webp')[1]}" alt="Blick in die Verkaufshalle mit vielen Motorrädern" loading="lazy"></div></div></section>
<section class="alt"><div class="wrap" style="max-width:56rem" data-reveal><p class="eyebrow">Der Standort</p><h2>Hier wird seit 1950 Motorgeschichte geschrieben.</h2><p>Es begann damals mit einer Servicestation für Porsche-Trecker, dann war es eine VW-Werkstatt. Es folgten BMW, Honda und Hyundai mit Verkaufsausstellung und Werkstatt. Heute ist hier die Verkaufshalle von Motorradhandel-Celle.</p><p class="note"><span class="ph-note">[Historie und Jahreszahlen vom Kunden bestätigen]</span></p></div></section>''' + cta_dark('Lernen Sie uns kennen.', 'Wir freuen uns über einen persönlichen Besuch. Bitte vorher kurz anrufen.')
layout('ueber-uns.html', 'Über uns: Bikerteam seit 17 Jahren | Motorradhandel-Celle', 'Ingo Werner und sein fünfköpfiges Bikerteam: Motorradhandel in Celle-Altenhagen mit 17 Jahren Erfahrung, Import, Ankauf und Inzahlungnahme.', ue, active='ueber-uns.html', fold=1)

# ================= KONTAKT =================
ko = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Kontakt</p><h1>Probefahrt, Fragen, Wunschmotorrad.</h1><p>Rufen Sie uns an, gern auch abends und am Wochenende, oder senden Sie die Anfrage. Wir melden uns bei Ihnen.</p></div></section>
<section><div class="wrap split" style="align-items:start"><div data-reveal>
<h2 style="font-size:2.2rem">Motorradhandel-Celle</h2>
<ul class="facts"><li><b>Telefon</b><a href="tel:{PHONE_TEL}">{PHONE_TXT}</a></li><li><b>E-Mail</b><a href="mailto:{MAIL}">{MAIL}</a> <span class="ph-note">[zwei E-Mail-Adressen auf alter Seite: bestätigen]</span></li><li><b>Adresse</b><span>Inhaber Ingo Werner<br>Lachtehäuserstraße 6<br>29223 Celle (Altenhagen)</span></li><li><b>Zeiten</b><span class="ph-note">[Öffnungs- und Erreichbarkeitszeiten vom Kunden]</span></li><li><b>Anfahrt</b><a href="https://www.openstreetmap.org/search?query=Lachteh%C3%A4userstra%C3%9Fe%206%2C%2029223%20Celle" rel="noopener noreferrer" target="_blank">Route in der Karte öffnen (externer Dienst, neuer Tab)</a></li></ul>
<div class="ctas" style="max-width:24rem"><a class="btn" href="tel:{PHONE_TEL}">Jetzt anrufen</a><a class="btn wa" href="https://wa.me/{PHONE_TEL.lstrip('+')}" rel="noopener noreferrer" target="_blank">WhatsApp schreiben</a></div></div>
<div data-reveal style="--d:.08s" id="probefahrt">{probe_form('kontaktform', '', 'Probefahrt oder Frage', 'Sagen Sie uns, für welches Motorrad Sie sich interessieren.', 'Anfrage senden')}</div></div></section>
<section class="alt" id="wunsch"><div class="wrap" style="max-width:46rem" data-reveal><h2>Wunschmotorrad suchen</h2><p>Was wir nicht im Bestand haben, besorgen wir auf Wunsch. Nennen Sie uns Modell, Baujahr und Budget.</p>{probe_form('wunschform', 'Wunschmotorrad', 'Wunschmotorrad anfragen', 'Welches Motorrad suchen Sie? Schreiben Sie Modell, Baujahr, Kilometer und Budget in die Nachricht.', 'Suche starten')}</div></section>'''
layout('kontakt.html', 'Kontakt & Probefahrt | Motorradhandel-Celle', 'Kontakt zu Motorradhandel-Celle in Celle-Altenhagen: Telefon 01520 8880000, Probefahrt anfragen, Wunschmotorrad suchen.', ko, active='kontakt.html', fold=1)

# ================= DANKE / RECHT / 404 =================
dk = f'''<section class="page-hero"><div class="wrap"><p class="eyebrow">Danke</p><h1>Anfrage eingegangen.</h1><p>Wir melden uns bei Ihnen. <span class="ph-note">[Antwortzeit nur nennen, wenn der Kunde sie zusagt]</span></p></div></section>
<section><div class="wrap"><h2 style="font-size:2rem">Während Sie warten</h2><ul class="bikes" style="margin-top:1rem">{''.join(card(b, d=i*.05) for i, b in enumerate(BIKES[:3]))}</ul><p style="margin-top:1.5rem"><a class="btn" href="motorraeder.html">Alle Motorräder ansehen</a> <a class="btn ghost" href="tel:{PHONE_TEL}">Lieber anrufen</a></p></div></section>'''
layout('danke.html', 'Danke für Ihre Anfrage | Motorradhandel-Celle', 'Ihre Anfrage ist eingegangen.', dk, fold=1)
imp = f'''<section><div class="wrap legal-page"><h1 style="font-size:var(--fs-2)">Impressum</h1><p><strong class="ph-note">[Rechtstext liefert der Kunde (Generator oder Anwalt)]</strong> Markentrix bindet ihn ein und prüft nur die Vollständigkeit der Pflichtangaben.</p><h2 style="font-size:1.6rem;margin-top:1.5rem">Angaben der bisherigen Website (vom Kunden zu prüfen und zu aktualisieren)</h2><p>Firma: Motorradhandel-Celle<br>Inhaber: Ingo Werner<br>Lachtehäuserstraße 6<br>29223 Celle (Altenhagen)</p><p>Telefon: +49 1520 8880000<br>E-Mail: {MAIL}<br>Handelsregister: Celle<br>Umsatzsteuer-Identifikationsnummer nach § 27a UStG: DE174231599<br>Gerichtsstand: Celle</p></div></section>'''
layout('impressum.html', 'Impressum | Motorradhandel-Celle', 'Impressum Motorradhandel-Celle.', imp, fold=0)
dat = '<section><div class="wrap legal-page"><h1 style="font-size:var(--fs-2)">Datenschutzerklärung</h1><p><strong class="ph-note">[Rechtstext liefert der Kunde (Generator oder Anwalt)]</strong></p><p>Hinweise für die Erstellung: Diese Website lädt keine Drittanbieter-Inhalte, Schriften und Skripte sind selbst gehostet, es gibt kein Tracking und keine Cookies. Hosting: Hetzner Online GmbH, Serverstandort Nürnberg. Formulare verarbeiten Name, Telefon, E-Mail und Anliegen (beim Ankauf zusätzlich Fahrzeugdaten und Fotos) zur Bearbeitung der Anfrage. WhatsApp- und Kartenlinks führen nur auf Klick zu externen Diensten.</p></div></section>'
layout('datenschutz.html', 'Datenschutz | Motorradhandel-Celle', 'Datenschutzerklärung Motorradhandel-Celle.', dat, fold=0)
layout('404.html', 'Seite nicht gefunden | Motorradhandel-Celle', 'Diese Seite wurde nicht gefunden.', '<section><div class="wrap"><p class="eyebrow">Fehler 404</p><h1 style="font-size:var(--fs-2)">Diese Seite gibt es nicht.</h1><p><a class="btn" href="motorraeder.html">Zum Bestand</a> <a class="btn ghost" href="index.html">Startseite</a></p></div></section>', fold=0)
open('robots.txt', 'w').write('User-agent: *\nDisallow: /\n# Demo: nicht indexieren.\n')
open('favicon.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#0F0F10"/><path d="M9 7h8l-5 18H4z" fill="#C8102E"/><path d="M19 7h5l-5 18h-5z" fill="#FF4A3D"/></svg>')
