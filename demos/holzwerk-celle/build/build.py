#!/usr/bin/env python3
"""Erzeugt alle Seiten der Demo aus gemeinsamen Bausteinen.
Aufruf im Ordner demos/holzwerk-celle:  python3 build/build.py
Das kritische CSS (inkl. Überschrift-Schrift als Base64) wird in jede Seite eingebettet (schneller Erstaufruf)."""
import re, base64, html, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ---------- CSS inline (minifiziert, Schrift eingebettet) ----------
css = open('assets/main.css').read()
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
css = re.sub(r'\s*([{};:,>])\s*', r'\1', css); css = re.sub(r'\s+', ' ', css).replace(';}', '}').strip()
b64 = base64.b64encode(open('assets/fonts/fraunces-sub-wght.woff2', 'rb').read()).decode()
css = css.replace('url("fonts/fraunces-sub-wght.woff2")', 'url(data:font/woff2;base64,' + b64 + ')')
css = css.replace('url("fonts/', 'url("assets/fonts/')

def esc(s): return html.escape(s, quote=True)
def size(p):
    w, h = Image.open('assets/img/' + p).size; return w, h
def img(name, alt, cls='', lazy=True, ext='webp', prio=False):
    w, h = size(f'{name}.{ext}')
    return f'<img src="assets/img/{name}.{ext}" width="{w}" height="{h}" alt="{esc(alt)}"' + (' loading="lazy"' if lazy else '') + (' fetchpriority="high"' if prio else '') + (f' class="{cls}"' if cls else '') + '>'

NAV = [('Leistungen', 'leistungen.html'), ('Referenzen', 'referenzen.html'), ('Über uns', 'ueber-uns.html'), ('Kontakt', 'kontakt.html')]
SERVICES = [('Fachwerk & Altbausanierung', 'fachwerk-altbausanierung.html'), ('Dach & Dachstühle', 'dach-dachstuehle.html'), ('Umbau, Anbau & Carports', 'leistungen.html#umbau'), ('Innenausbau', 'leistungen.html#innenausbau'), ('Verschalung & Verkleidung', 'leistungen.html#verschalung'), ('Bauleitung & Gesamtangebot', 'leistungen.html#bauleitung')]

def no_reveal_above_fold(body, n):
    """Elemente im ersten Bildschirm nicht per Einblend-Animation verstecken (sonst verzögert sich der LCP)."""
    parts = body.split('</section>')
    for i in range(min(n, len(parts))): parts[i] = parts[i].replace(' data-reveal', '')
    return '</section>'.join(parts)

def layout(fn, title, desc, body, crumbs=None, active=None, robots='noindex, nofollow', extra_head='', json_ld=''):
    body = no_reveal_above_fold(body, 1 if fn == 'index.html' else 2)
    nav = ''.join(f'<li><a href="{h}"' + (' aria-current="page"' if h == active else '') + f'>{esc(t)}</a></li>' for t, h in NAV)
    foot_srv = ''.join(f'<li><a href="{h}">{esc(t)}</a></li>' for t, h in SERVICES)
    page = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#ffffff">
<link rel="canonical" href="https://[KUNDEN-DOMAIN]/{'' if fn == 'index.html' else fn}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<script>document.documentElement.className+=' js'</script>
<link rel="preload" href="assets/fonts/inter-sub-wght.woff2" as="font" type="font/woff2" crossorigin>
{extra_head}<style>{css}</style>
<script src="assets/main.js" defer></script>
{json_ld}</head>
<body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<div class="demo-bar" data-demo role="note">Designvorschlag von Markentrix für die HOLZWERK GmbH · nicht veröffentlicht · Texte sind Vorschläge, <span class="ph-note">[Platzhalter]</span> vom Kunden</div>
<header class="site"><div class="wrap">
  <a class="logo" href="index.html" aria-label="HOLZWERK GmbH, Zimmerei, Dachdeckerei, Maurer- und Malereibetrieb, zur Startseite"><img src="assets/img/logo.png" width="490" height="102" alt="HOLZWERK GmbH"></a>
  <nav class="main" id="nav" aria-label="Hauptnavigation" data-open="false"><ul>{nav}</ul></nav>
  <div class="hdr-cta"><a class="btn sm" href="tel:+4951419095610">05141 90 95 610</a><button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">Menü</button></div>
</div></header>
<main id="main">
{('<div class="wrap"><nav class="crumbs" aria-label="Brotkrumen"><a href="index.html">Start</a> / ' + crumbs + '</nav></div>') if crumbs else ''}
{body}
</main>
<footer class="site"><div class="wrap">
  <div class="foot-grid">
    <div><h2>HOLZWERK GmbH</h2><p>Zimmerei, Dachdeckerei,<br>Maurer- und Malereibetrieb<br>Breite Straße 38<br>29221 Celle</p></div>
    <div><h2>Leistungen</h2><ul>{foot_srv}</ul></div>
    <div><h2>Unternehmen</h2><ul><li><a href="referenzen.html">Referenzen</a></li><li><a href="ueber-uns.html">Über uns</a></li><li><a href="kontakt.html">Kontakt</a></li></ul></div>
    <div><h2>Kontakt</h2><ul><li><a href="tel:+4951419095610">0 51 41 – 90 95 610</a></li><li><a href="mailto:info@holzwerk-celle.de">info@holzwerk-celle.de</a></li><li><span class="ph-note">[Zeiten vom Kunden]</span></li></ul></div>
  </div>
  <div class="legal"><p>© HOLZWERK GmbH</p><p><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></p></div>
</div></footer>
<dialog class="lb" id="lb" aria-label="Bildansicht"><figure><img src="" alt=""><figcaption></figcaption></figure><div class="bar"><button type="button" data-prev>← Zurück</button><button type="button" data-close>Schließen</button><button type="button" data-next>Weiter →</button></div></dialog>
</body>
</html>
'''
    open(fn, 'w').write(page)
    print(fn, len(page) // 1024, 'KB')

def head(eyebrow, h1, lead):
    return f'<section class="page-hero"><div class="wrap"><p class="eyebrow">{esc(eyebrow)}</p><h1>{h1}</h1><p class="lead">{lead}</p></div></section>'

def gallery(prefix, items):
    lis = ''
    for n, (cap, alt) in enumerate(items, 1):
        name = f'{prefix}-{n}'; w, h = size(name + '-t.webp')
        lis += f'<li><a href="assets/img/{name}.webp" data-cap="{esc(cap)}" data-alt="{esc(alt)}"><img src="assets/img/{name}-t.webp" width="{w}" height="{h}" loading="lazy" alt="{esc(alt)}"></a></li>'
    return f'<ul class="gallery">{lis}</ul>'

def ba(name, label, a_before, a_after, d=0):
    return f'''<figure class="ba-f" data-reveal style="--d:{d}s">
      <div class="ba">{img(name + '-vorher', a_before)}{img(name + '-nachher', a_after, 'after')}<span class="tag l">Vorher</span><span class="tag r">Nachher</span><span class="knob" aria-hidden="true">↔</span><input type="range" min="0" max="100" value="50" aria-label="Vorher-Nachher-Vergleich {esc(label)}: Regler verschieben"></div>
      <figcaption>{esc(label)}</figcaption></figure>'''

def cta(h='Erzählen Sie uns von Ihrem Vorhaben.', p='Wir freuen uns auf Ihre Anfrage.'):
    return f'<section class="sec"><div class="wrap"><div class="cta-band" data-reveal><div><h2>{h}</h2><p>{p}</p></div><div class="acts"><a class="btn" href="kontakt.html">Anfrage senden</a><a class="btn ghost" href="tel:+4951419095610">Jetzt anrufen</a></div></div></div></section>'

LD = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"HomeAndConstructionBusiness","name":"HOLZWERK GmbH","description":"Zimmerei, Dachdeckerei, Maurer- und Malereibetrieb","address":{"@type":"PostalAddress","streetAddress":"Breite Straße 38","postalCode":"29221","addressLocality":"Celle","addressCountry":"DE"},"telephone":"+49 5141 9095610","email":"info@holzwerk-celle.de","areaServed":["Celle","Hannover","Braunschweig","Bremen","Hildesheim"]}</script>\n'

# =============== 1 START ===============
def card(no, h, p, imgname, alt, href, d=0, w=720, hh=480):
    iw, ih = size(imgname + '.webp')
    return f'<article class="card" data-reveal style="--d:{d}s"><div class="ph"><img src="assets/img/{imgname}.webp" width="{iw}" height="{ih}" loading="lazy" alt="{esc(alt)}"></div><div class="body"><span class="no">{no}</span><h3><a href="{href}" class="stretch">{h}</a></h3><p>{p}</p></div></article>'

home = f'''<section class="hero" id="top"><div class="wrap">
  <div class="grid">
    <div>
      <p class="eyebrow">Meisterbetrieb · Celle</p>
      <h1>Zimmerei &amp; Dachdeckerei in&nbsp;Celle. <em>Traditionell gut.</em></h1>
      <p class="lead">Fachwerk, Dachstühle und Altbausanierung vom Meisterbetrieb. Solides Handwerk mit modernen Baustoffen, für Celle, Hannover, Braunschweig, Bremen und Hildesheim.</p>
      <div class="actions"><a class="btn" href="kontakt.html">Anfrage senden</a><a class="btn ghost" href="tel:+4951419095610">Jetzt anrufen</a></div>
    </div>
    <div class="hero-media"><img src="assets/img/hero-720.webp" srcset="assets/img/hero-480.webp 480w, assets/img/hero-720.webp 720w, assets/img/hero.webp 840w" sizes="(max-width: 1000px) 100vw, 45vw" width="840" height="560" alt="Saniertes Fachwerkhaus mit Terrasse und Garten in Celle" fetchpriority="high"></div>
  </div>
  <div class="trust" data-reveal>
    <div><strong>Meisterbetrieb</strong><span>Zimmerei, Dachdeckerei, Maurer- und Malerbetrieb</span></div>
    <div><strong>Seit 2002</strong><span>Gegründet in Celle</span></div>
    <div><strong>Über 40 Mitarbeiter</strong><span>Ein Team, viele Gewerke</span></div>
    <div><strong>Ausbildungsbetrieb</strong><span>Wissen für die nächste Generation</span></div>
  </div>
</div></section>

<section aria-labelledby="leistungen-h"><div class="wrap">
  <div class="head" data-reveal><div><p class="eyebrow">Leistungen</p><h2 id="leistungen-h">Alles aus Holz. Und alles aus einer Hand.</h2></div><p>Vom Dachstuhl bis zur Fassade: Wir bauen, sanieren und koordinieren. Mit güteüberwachten, zertifizierten Produkten.</p></div>
  <div class="cards">
    {card('01','Fachwerk','Neubau, Sanierung und Umbau mit traditionellen Holzverbindungen und konstruktivem Holzschutz.','fachwerk','Restaurierte Fachwerkfassade mit Holzfenstern','fachwerk-altbausanierung.html')}
    {card('02','Altbausanierung','Feuchtigkeits- und Wasserschäden fachgerecht beheben, Holz langfristig schützen.','altbau','Detail eines sanierten Altbaufensters mit Fachwerkbalken','fachwerk-altbausanierung.html#altbausanierung',.06)}
    {card('03','Dachstühle','Satteldach, Pultdach, Walmdach. Auch Fledermaus- und Tonnengauben sowie Turmdächer.','dachstuhl','Zimmerer beim Aufbau eines Dachstuhls','dach-dachstuehle.html',.12)}
    {card('04','Umbau, Anbau &amp; Carports','Erker, Loggien, Wintergärten, Holzrahmenbau und Carports, von der Planung bis zur Ausführung.','umbau','Weiß gestrichener Holz-Wintergarten an einem Wohnhaus','leistungen.html#umbau',.18)}
    {card('05','Innenausbau','Leichtbauwände, Deckenverkleidungen und kompletter Trockenbau, im Neubau wie im Altbau.','innenausbau','Heller Flur mit Holztreppe und Dielenboden','leistungen.html#innenausbau')}
    {card('06','Verschalung &amp; Verkleidung','Holzfassaden ganz oder teilweise, von traditionell bis elegant-modern.','verschalung','Fachwerkhaus mit teilweiser Holzverschalung an der Fassade','leistungen.html#verschalung',.06)}
    <article class="card wide" data-reveal style="--d:.12s"><div class="body"><span class="no">07</span><h3><a href="leistungen.html#bauleitung" class="stretch">Bauleitung &amp; Gesamtangebot</a></h3><p>Mehrere Gewerke, ein Ansprechpartner. Auf Wunsch erhalten Sie ein Gesamtangebot, wir koordinieren alle Beteiligten bis zur Schlussabnahme. Das spart Zeit, Mühe und Nerven.</p></div></article>
  </div>
</div></section>

<section class="alt" aria-labelledby="ref-h"><div class="wrap">
  <div class="head" data-reveal><div><p class="eyebrow">Referenzen</p><h2 id="ref-h">Projekte, die für sich sprechen.</h2></div><p><a href="referenzen.html">Alle Referenzen ansehen</a></p></div>
  <div class="refs">
    <article class="ref big" data-reveal><a href="referenzen.html#haghof" class="stretch" aria-label="Gutshaus Haghof, Isernhagen"></a>{img('ref-haghof','Gutshaus Haghof in Isernhagen mit rotem Ziegeldach')}<div class="cap"><h3>Gutshaus Haghof, Isernhagen</h3><small>Umfangreiche Restaurierung</small></div></article>
    <article class="ref" data-reveal style="--d:.08s"><a href="referenzen.html#jaegerstrasse" class="stretch" aria-label="Einfamilienhaus Jägerstraße, Celle"></a>{img('ref-jaegerstr','Saniertes Fachwerkhaus in der Jägerstraße in Celle am Abend')}<div class="cap"><h3>Einfamilienhaus Jägerstraße, Celle</h3><small>Restaurierung eines Fachwerkhauses</small></div></article>
    <article class="ref" data-reveal style="--d:.14s"><a href="referenzen.html#petersburgstrasse" class="stretch" aria-label="Einfamilienhaus Petersburgstraße, Celle"></a>{img('ref-petersburgstr','Restauriertes Einfamilienhaus in der Petersburgstraße in Celle')}<div class="cap"><h3>Einfamilienhaus Petersburgstraße, Celle</h3><small>Restaurierung</small></div></article>
  </div>
</div></section>

<section aria-labelledby="ablauf-h"><div class="wrap">
  <div class="head" data-reveal><div><p class="eyebrow">Ablauf</p><h2 id="ablauf-h">Von der Anfrage bis zur Abnahme.</h2></div><p>Ein Ansprechpartner begleitet Ihr Vorhaben, auch wenn mehrere Gewerke beteiligt sind.</p></div>
  <ol class="steps">
    <li data-reveal><h3>Anfrage</h3><p>Sie schildern Ihr Vorhaben per Formular, E-Mail oder Telefon.</p></li>
    <li data-reveal style="--d:.07s"><h3>Gesamtangebot</h3><p>Auf Wunsch bündeln wir die Gewerke mit bewährten Partnerfirmen zu einem Angebot.</p></li>
    <li data-reveal style="--d:.14s"><h3>Ausführung</h3><p>Wir koordinieren den Ablauf und arbeiten fachgerecht und mit größter Sorgfalt.</p></li>
    <li data-reveal style="--d:.21s"><h3>Schlussabnahme</h3><p>Wir prüfen die Bautätigkeit gemeinsam mit Ihnen bis zur Abnahme.</p></li>
  </ol>
</div></section>

<section class="alt" aria-labelledby="ueber-h"><div class="wrap about">
  <figure data-reveal>{img('about','Detail einer sanierten Holzfassade mit Fenster und Backsteinwand')}{img('walz','Schwarz-Weiß-Foto: Zimmerer in traditioneller Tracht bei der Arbeit','inset')}</figure>
  <div data-reveal style="--d:.08s">
    <p class="eyebrow">Über uns</p>
    <h2 id="ueber-h">Handwerk mit Geschichte. Gebaut für heute.</h2>
    <p>Inhaber Jörg Reinstorf gründete HOLZWERK 2002 in seinem Heimatort Celle, nachdem er zwei Jahre auf der Walz war. Heute beschäftigt der Meisterbetrieb über 40 Mitarbeiter und gibt als Ausbildungsbetrieb sein Fachwissen an die nächste Generation weiter.</p>
    <p><a class="btn ghost" href="ueber-uns.html">Mehr über HOLZWERK</a></p>
  </div>
</div></section>
''' + cta()
layout('index.html', 'Zimmerei & Dachdeckerei in Celle | HOLZWERK GmbH', 'HOLZWERK GmbH in Celle: Zimmerei, Dachdeckerei, Maurer- und Malerbetrieb. Fachwerk, Dachstühle, Altbausanierung. Jetzt Anfrage senden.', home, active=None,
       extra_head='<link rel="preload" as="image" href="assets/img/hero-720.webp" imagesrcset="assets/img/hero-480.webp 480w, assets/img/hero-720.webp 720w, assets/img/hero.webp 840w" imagesizes="(max-width: 1000px) 100vw, 45vw" fetchpriority="high">\n', json_ld=LD)

# =============== 2 LEISTUNGEN ===============
def block(id_, no, h, text_html, imgname, alt, rev=False, link=None):
    more = f'<p><a class="more" href="{link[0]}">{link[1]} →</a></p>' if link else ''
    pic = f'<div class="pic">{img(imgname, alt)}</div>'
    txt = f'<div><span class="no" style="font:600 .75rem var(--font-body);letter-spacing:.14em;color:var(--gold-ink)">{no}</span><h2>{h}</h2>{text_html}{more}</div>'
    return f'<section class="sec" id="{id_}"><div class="wrap"><div class="split{" rev" if rev else ""}" data-reveal>{pic if not rev else txt}{txt if not rev else pic}</div></div></section>'

lei = head('Leistungen', 'Alles aus Holz. Und alles aus einer Hand.', 'HOLZWERK verbindet solides, traditionelles Handwerk mit den neuesten Standards. Wir bieten bewährte Qualität mit höchstem Anspruch und nutzen gleichzeitig modernste Techniken und Materialien.')
lei += '<section class="sec" style="padding-top:0"><div class="wrap"><div class="values">' + ''.join(f'<article class="card" data-reveal style="--d:{i*.07}s"><div class="body"><h2>{h}</h2><p>{p}</p></div></article>' for i, (h, p) in enumerate([('Sorgfältig ausgeführt', 'Unsere Arbeiten werden fachgerecht und mit größter handwerklicher Sorgfalt ausgeführt.'), ('Güteüberwachte Produkte', 'Zur Verwendung gelangen ausschließlich güteüberwachte bzw. zertifizierte Produkte.'), ('Zügig und verlässlich', 'Die Auftragsabwicklung erfolgt zügig und reibungslos, unsere Zusagen sind verlässlich.')])) + '</div></div></section>'
lei += block('fachwerk', '01', 'Fachwerk', '<p>Fachwerkhäuser besitzen ihren ganz eigenen Charme und Reiz. Neben dem Neubau übernehmen wir auch die Sanierung und den Umbau bestehender Gebäude, mit traditionellen Holzverbindungen und größter Sachkenntnis.</p>', 'fachwerk', 'Restaurierte Fachwerkfassade mit Holzfenstern', link=('fachwerk-altbausanierung.html', 'Mehr zu Fachwerk und Altbausanierung'))
lei += block('altbausanierung', '02', 'Altbausanierung', '<p>Im Laufe der Zeit können Alterungsprozesse, Schädlinge oder Feuchtigkeit Holzbauteile angreifen. Wir sanieren Feuchtigkeits- und Wasserschäden kompetent und schützen das Holz langfristig.</p>', 'altbau', 'Detail eines sanierten Altbaufensters mit Fachwerkbalken', rev=True, link=('fachwerk-altbausanierung.html#altbausanierung', 'Mehr zur Altbausanierung'))
lei += block('dachstuehle', '03', 'Dachstühle', '<p>Egal, welche Form Ihr Wunschdach haben soll: Wir setzen Ihre Vorstellungen um, im Neubau ebenso wie bei Sanierung und Umbau von Altbauten.</p>', 'dachstuhl', 'Zimmerer beim Aufbau eines Dachstuhls', link=('dach-dachstuehle.html', 'Mehr zu Dach und Dachstühlen'))
lei += block('umbau', '04', 'Umbau, Anbau &amp; Carports', '<p>Falls Sie Teile Ihres Hauses oder Ihrer Wohnung baulich verändern oder erweitern möchten, stehen wir Ihnen mit einer Reihe von Leistungen zur Verfügung:</p><ul class="checks"><li>nachträglicher Einbau von Erkern und Loggien (Dachterrassen)</li><li>Holzbalkone und Terrassen</li><li>Wintergärten</li><li>Holzrahmenbau</li><li>Einbau von Dachflächenfenstern</li><li>Carports</li></ul><p>Wir übernehmen jeweils die komplette Abwicklung: von der Planung über die Klärung baurechtlicher Fragen bis zur Ausführung.</p>', 'umbau', 'Weiß gestrichener Holz-Wintergarten an einem Wohnhaus', rev=True)
lei += block('innenausbau', '05', 'Innenausbau', '<p>Holz lässt sich im Innenausbau in Verbindung mit anderen Baustoffen konstruktiv und gestalterisch vielseitig einsetzen. Wir fertigen Leichtbauwände für eine neue Raumaufteilung, verkleiden Decken und führen auf Wunsch in Trockenbauweise den gesamten Innenausbau durch, im Neubau wie in der Altbausanierung.</p><p>Bei Bedarf koordinieren wir zudem die Prüfung der Luftdichtigkeit in Form eines Blower-Door-Tests.</p>', 'innenausbau', 'Heller Flur mit Holztreppe und Dielenboden')
lei += block('verschalung', '06', 'Verschalung &amp; Verkleidung', '<p>Zur Putz- oder Klinkerfassade gibt es eine attraktive Alternative: die Verschalung bzw. Verkleidung mit Holz. Die Fassade lässt sich ganz oder teilweise verkleiden. Je nach Material, Farbe und Ausführung reicht das Ergebnis von traditionell bis elegant-modern.</p><p>Wir beraten Sie gerne umfassend. Rufen Sie einfach an oder senden Sie uns Ihre Anfrage.</p>', 'verschalung', 'Fachwerkhaus mit teilweiser Holzverschalung an der Fassade', rev=True)
lei += '<section class="sec alt" id="bauleitung"><div class="wrap"><div class="split" data-reveal><div><span class="no" style="font:600 .75rem var(--font-body);letter-spacing:.14em;color:var(--gold-ink)">07</span><h2>Bauleitung &amp; Gesamtangebot</h2><p>Bei Altbausanierung, Um- und Anbauten werden häufig Handwerker unterschiedlicher Gewerke gebraucht. Das heißt für Sie normalerweise: mehrere Angebote einholen und die Gewerke koordinieren.</p><p>Durch die enge Zusammenarbeit mit bewährten Partnerfirmen können wir Ihnen auf Wunsch ein Gesamtangebot unterbreiten. Anschließend koordinieren wir den Ablauf und überprüfen die Bautätigkeit bis zur Schlussabnahme. Alle Fragen und Wünsche richten Sie an nur einen Gesprächspartner. Das spart viel Zeit, Mühe und Nerven.</p></div><div><ol class="steps" style="grid-template-columns:1fr 1fr"><li><h3>Gesamtangebot</h3><p>Ein Angebot für alle Gewerke.</p></li><li><h3>Koordination</h3><p>Wir steuern den Ablauf.</p></li><li><h3>Kontrolle</h3><p>Wir prüfen die Bautätigkeit.</p></li><li><h3>Schlussabnahme</h3><p>Ein Ansprechpartner bis zum Ende.</p></li></ol></div></div></div></section>'
lei += cta()
layout('leistungen.html', 'Leistungen: Fachwerk, Dachstühle, Umbau | HOLZWERK Celle', 'Fachwerk, Altbausanierung, Dachstühle, Umbau, Innenausbau und Verschalung vom Meisterbetrieb in Celle. Mit Bauleitung und Gesamtangebot.', lei, crumbs='Leistungen', active='leistungen.html')

# =============== 3 FACHWERK & ALTBAU ===============
fw = head('Fachwerk & Altbausanierung', 'Fachwerk bauen, sanieren, bewahren.', 'Fachwerkhäuser besitzen ihren ganz eigenen Charme und Reiz. Sie sind etwas Besonderes, deshalb erfordern Bau und Sanierung spezielle Kenntnisse und Fertigkeiten.')
fw += '<section class="sec" style="padding-top:0" id="fachwerk"><div class="wrap"><div class="two">' + ''.join(f'<article class="card" data-reveal style="--d:{i*.08}s"><div class="body"><span class="no">{n}</span><h2>{h}</h2><p>{p}</p></div></article>' for i, (n, h, p) in enumerate([('NEUBAU', 'Fachwerk-Neubau', 'Auf Wunsch übernehmen wir die komplette Ausführung Ihres Fachwerk-Neubaus. Dabei arbeiten wir ausschließlich mit traditionellen Holzverbindungen (wie dem konstruktiven Holzschutz) und kooperieren eng mit bewährten Spezialfirmen, die angrenzende Arbeiten wie das Ausmauern der Gefache übernehmen.'), ('SANIERUNG', 'Fachwerk-Sanierung', 'Wir restaurieren und sanieren Ihr Fachwerk mit größter Sorgfalt und Sachkenntnis. Die Richtlinien der Denkmalpflege sind uns geläufig, bei Bedarf führen wir sämtliche statischen Berechnungen durch. Am Ende stellen wir den ursprünglichen Zustand des Gebäudes wieder her: Sie brauchen keine gravierenden Änderungen der Optik zu befürchten.')])) + '</div><p style="margin-top:1.4rem">Die zu sanierenden Gebäudeteile werden fachgerecht abgestützt und die Lasten provisorisch im Zuge der Sanierung abgefangen.</p></div></section>'
fw += '<section class="sec alt" id="altbausanierung"><div class="wrap"><div class="split" data-reveal><div><p class="eyebrow">Altbausanierung</p><h2>Wenn Holz in die Jahre kommt.</h2><p>In Altbauten wurde der Werkstoff Holz aufgrund seiner positiven Eigenschaften und seiner Langlebigkeit vielseitig eingesetzt. Alterungsprozesse, Schädlinge oder Feuchtigkeit können die Holzbauteile jedoch angreifen und deren Erneuerung notwendig machen.</p><ul class="checks"><li>Feuchtigkeits- und Wasserschäden kompetent und fachgerecht sanieren</li><li>alle notwendigen Maßnahmen zum langfristigen Holzschutz</li><li>bei Schwammbefall oder Holzschädlingen: Vermittlung und Koordination versierter Spezialisten auf Wunsch</li><li>statische Verstärkungen und Erneuerung maroder oder beschädigter Holzbauteile, etwa beim Dachbodenausbau oder nach einem Brandschaden</li></ul></div><div class="pic">' + img('altbau', 'Detail eines sanierten Altbaufensters mit Fachwerkbalken') + '</div></div></div></section>'
fw += '<section class="sec"><div class="wrap"><div class="head" data-reveal><div><p class="eyebrow">Fotos</p><h2>Fachwerk aus unseren Projekten.</h2></div><p>Klicken Sie ein Bild an, um es zu vergrößern.</p></div>' + gallery('g-fw', [('Fachwerkhaus, Jägerstraße Celle', 'Restauriertes Fachwerkhaus von der Straße'), ('Fachwerk-Detail mit Fenster', 'Fachwerkbalken, Backstein und weiße Holzfenster im Detail'), ('Holzverschalung im Detail', 'Helle Holzdielen an Decke und Wand'), ('Holzfassade mit Fallrohr', 'Fachwerkbalken, Backsteinwand und Holzverkleidung im Detail'), ('Fachwerk im Bau', 'Fachwerkgebäude mit Gerüst bei der Sanierung'), ('Umbau eines Altbaus', 'Neu aufgebauter Dachstuhl auf einem Backsteingebäude')]) + '</div></section>'
fw += cta('Fachwerk oder Altbau? Sprechen Sie uns an.', 'Wir beraten Sie gerne zu Ihrem Gebäude.')
layout('fachwerk-altbausanierung.html', 'Fachwerk & Altbausanierung in Celle | HOLZWERK', 'Fachwerk-Neubau, Fachwerk-Sanierung und Altbausanierung in Celle: Holzschutz, Statik, Denkmalpflege. HOLZWERK, Ihr Meisterbetrieb.', fw, crumbs='<a href="leistungen.html">Leistungen</a> / Fachwerk &amp; Altbausanierung', active='leistungen.html')

# =============== 4 DACH ===============
da = head('Dach & Dachstühle', 'Dachstühle nach Ihren Vorstellungen.', 'Egal, welche Form Ihr Wunschdach haben soll: Wir verfügen über das notwendige Fachwissen und ausreichend Erfahrung, um Ihre Vorstellungen umzusetzen, im Neubau wie bei Sanierung und Umbau von Altbauten.')
da += '<section class="sec" style="padding-top:0"><div class="wrap"><div class="split" data-reveal><div><p class="eyebrow">Dachformen</p><h2>Vom Satteldach bis zum Turmdach.</h2><p>Neben den gängigen Dachformen wie Satteldach, Pultdach oder Walmdach errichten wir ganz nach Ihrem Wunsch auch:</p><ul class="checks"><li>Fledermaus-Gauben</li><li>Tonnen-Gauben</li><li>asymmetrische und windschiefe Dächer</li><li>Turmdächer</li></ul><p>Bei Bedarf übernehmen wir zudem die Koordination der Dacheindeckung und anderer Nebenarbeiten.</p></div><div class="pic">' + img('dachstuhl', 'Zimmerer beim Aufbau eines Dachstuhls', lazy=False) + '</div></div></div></section>'
da += '<section class="sec alt"><div class="wrap"><div class="head" data-reveal><div><p class="eyebrow">Vorher / Nachher</p><h2>Wie aus Dächern Zuhause wird.</h2></div><p>Ziehen Sie den Regler, um den Unterschied zu sehen.</p></div><div class="ba-grid" style="margin-top:0">' + ba('dach', 'Dach und Fassade erneuert', 'Wohnhaus vor der Sanierung mit altem, dunklem Dach', 'Dasselbe Wohnhaus nach der Sanierung mit neuem rotem Dach und Gaube') + ba('dachausbau', 'Dachboden ausgebaut', 'Unausgebauter Dachboden mit alten Holzbalken', 'Ausgebauter, heller Dachraum mit Holzbalken und Parkett', .08) + ba('telis', 'Gebäude komplett saniert', 'Altes, dunkles Gebäude vor der Sanierung', 'Dasselbe Gebäude nach der Sanierung in hellem Putz mit rotem Dach', .16) + '</div></div></section>'
da += '<section class="sec"><div class="wrap"><div class="head" data-reveal><div><p class="eyebrow">Baustelle</p><h2>Einblicke in die Dacharbeiten.</h2></div><p>Aus der Restaurierung des Gutshauses Haghof und weiteren Projekten.</p></div>' + gallery('g-dach', [('Dachstuhl im Aufbau', 'Zimmerer beim Aufbau eines Dachstuhls'), ('Gutshaus Haghof: Lattung', 'Dachfläche mit Konterlattung und Folie'), ('Gutshaus Haghof: Gerüst', 'Dach mit Gerüst während der Sanierung'), ('Gutshaus Haghof: Neueindeckung', 'Neu gelattetes Dach mit Gauben'), ('Gutshaus Haghof: Dachfläche', 'Dachfläche mit Lattung und Dachfenster'), ('Gutshaus Haghof: Schutzfolie', 'Dach mit blauer Schutzfolie während der Arbeiten')]) + '</div></section>'
da += cta('Ihr Dach, Ihr Wunsch. Fragen Sie uns.', 'Wir beraten Sie zu Dachform, Dachstuhl und Sanierung.')
layout('dach-dachstuehle.html', 'Dach & Dachstühle in Celle | HOLZWERK Zimmerei', 'Dachstühle, Gauben, Turmdächer und Dachsanierung vom Meisterbetrieb in Celle. Neubau und Altbau, mit Koordination der Dacheindeckung.', da, crumbs='<a href="leistungen.html">Leistungen</a> / Dach &amp; Dachstühle', active='leistungen.html')

# =============== 5 REFERENZEN ===============
def proj(id_, h, meta, text, prefix, items, extra=''):
    return f'<section class="proj" id="{id_}"><div class="wrap" data-reveal><h2>{h}</h2><p class="meta">{meta}</p><p>{text}</p>{extra}{gallery(prefix, items)}</div></section>'
rf = head('Referenzen', 'Projekte, die für sich sprechen.', 'Umfangreich restaurierte Häuser, ausgebaute Dachböden, Terrassen aus Holz: Hier sehen Sie eine Auswahl unserer Arbeiten.')
rf += proj('haghof', 'Gutshaus Haghof, Isernhagen', 'Restaurierung', 'Restaurierung des Gutshauses Haghof in Isernhagen: Fotos des umfangreich restaurierten Hauses, vom Zustand vor den Arbeiten bis zum Baufortschritt am Dach.', 'g-hag', [('Gutshaus Haghof', 'Gutshaus mit rotem Ziegeldach und Rundturm'), ('Gutshaus Haghof, Seitenansicht', 'Gutshaus mit Rundturm und Schieferdach'), ('Gutshaus Haghof, Haupthaus', 'Haupthaus mit Gauben und Schornsteinen'), ('Gutshaus Haghof, Zufahrt', 'Gutshaus von der Zufahrt aus gesehen'), ('Gutshaus Haghof, Dacharbeiten', 'Gutshaus mit Gerüst während der Dacharbeiten'), ('Gutshaus Haghof, Detail', 'Dachfläche des Gutshauses im Detail')])
rf += proj('jaegerstrasse', 'Einfamilienhaus Jägerstraße, Celle', 'Restaurierung eines Fachwerkhauses', 'Fotos eines umfangreich restaurierten Fachwerkhauses in der Jägerstraße in Celle.<br><span style="color:var(--muted);font-size:.9rem">Architektur: bussemas architekten, Lage · Fotos: Roman Thomas, Celle <span class="ph-note">[Bildrechte klären]</span></span>', 'g-jae', [('Jägerstraße am Abend', 'Saniertes Fachwerkhaus am Abend'), ('Rückseite mit Terrasse', 'Fachwerkhaus mit Terrasse und Garten'), ('Straßenansicht', 'Restauriertes Fachwerkhaus von der Straße'), ('Innenraum mit Dielenboden', 'Heller Flur mit Dielenboden'), ('Treppenhaus', 'Treppenhaus mit Holztreppe und Musterfliesen'), ('Holztreppe', 'Holztreppe mit weißem Geländer von oben')])
rf += proj('petersburgstrasse', 'Einfamilienhaus Petersburgstraße, Celle', 'Restaurierung', 'Vorher-Nachher-Fotos eines umfangreich restaurierten Hauses in der Petersburgstraße in Celle.', 'g-pet', [('Petersburgstraße', 'Fachwerkhaus mit Balkon'), ('Seitenansicht', 'Fachwerkhaus von der Straßenecke'), ('Fachwerk und Verkleidung', 'Fachwerkhaus mit Holzverkleidung'), ('Neue Fassade', 'Fachwerkhaus mit neuer Fassade und rotem Dach'), ('Holzverschalung', 'Haus mit Holzverschalung im Obergeschoss'), ('Fassadenansicht', 'Haus mit grauer Fassade und rotem Dach')])
rf += proj('terrassenbau', 'Terrassenbau', 'Terrassen und Treppenanlagen aus Holz', 'Terrassen aus Holz, passgenau gebaut, vom Rohbau bis zur fertigen Anlage.', 'g-ter', [('Terrasse mit Treppe', 'Holzterrasse mit breiter Treppe an einem Altbau'), ('Terrasse am Altbau', 'Holzterrasse mit Treppe an einem Backsteinhaus'), ('Terrasse im Garten', 'Holzterrasse an einem Fachwerkgebäude'), ('Terrasse im Bau', 'Holzterrasse mit Stufen im Bau'), ('Sitzstufen', 'Holzterrasse mit Sitzstufen'), ('Terrassenstufen', 'Holzstufen einer Terrasse im Garten')])
rf += '<section class="sec alt" id="vorher-nachher"><div class="wrap"><div class="head" data-reveal><div><p class="eyebrow">Vorher / Nachher</p><h2>Der Unterschied auf einen Blick.</h2></div><p>Ziehen Sie den Regler, um die Veränderung zu sehen.</p></div><div class="ba-grid" style="margin-top:0">' + ba('dach', 'Dach und Fassade erneuert', 'Wohnhaus vor der Sanierung mit altem, dunklem Dach', 'Dasselbe Wohnhaus nach der Sanierung mit neuem rotem Dach und Gaube') + ba('telis', 'Gebäude komplett saniert', 'Altes, dunkles Gebäude vor der Sanierung', 'Dasselbe Gebäude nach der Sanierung in hellem Putz mit rotem Dach', .08) + ba('dachausbau', 'Dachboden ausgebaut', 'Unausgebauter Dachboden mit alten Holzbalken', 'Ausgebauter, heller Dachraum mit Holzbalken und Parkett', .16) + '</div></div></section>'
rf += cta('Ihr Projekt könnte das nächste sein.', 'Schildern Sie uns Ihr Vorhaben. Wir melden uns bei Ihnen.')
layout('referenzen.html', 'Referenzen: Restaurierung, Dachausbau, Terrassen | HOLZWERK Celle', 'Referenzprojekte der HOLZWERK GmbH in Celle: Gutshaus Haghof, Fachwerkhäuser, Dachausbau und Terrassen mit Vorher-Nachher-Vergleich.', rf, crumbs='Referenzen', active='referenzen.html')

# =============== 6 ÜBER UNS ===============
ue = head('Über uns', 'Handwerk mit Geschichte. Gebaut für heute.', 'Der Meisterbetrieb HOLZWERK hat seinen Sitz im niedersächsischen Celle. Traditionell gut: Das ist unser Anspruch seit 2002.')
ue += '<section class="sec" style="padding-top:0"><div class="wrap about"><figure data-reveal>' + img('about', 'Detail einer sanierten Holzfassade mit Fenster und Backsteinwand', lazy=False, prio=True) + img('walz', 'Schwarz-Weiß-Foto: Zimmerer in traditioneller Tracht bei der Arbeit', 'inset', lazy=False) + '</figure><div data-reveal style="--d:.08s"><h2>Philosophie</h2><p>Inhaber Jörg Reinstorf gründete die Firma im Jahr 2002 in seinem Heimatort, nachdem er zuvor zwei Jahre lang auf der Walz war. Mittlerweile beschäftigt er über 40 Mitarbeiter und gibt als Ausbildungsbetrieb sein Fachwissen an die nächste Generation weiter.</p><p>HOLZWERK ist der Tradition des Zimmerer-, Dachdecker-, Maurer-, Betonbau- und Maler-Handwerks verpflichtet und verbindet Altbewährtes erfolgreich mit neuesten Technologien und Baustoffen.</p></div></div></section>'
ue += '<section class="sec alt"><div class="wrap"><div class="head" data-reveal><div><p class="eyebrow">Unsere Gewerke</p><h2>Ein Betrieb, viele Handwerke.</h2></div><p>Zimmerei, Dachdeckerei, Maurer- und Malereibetrieb unter einem Dach.</p></div><div class="values">' + ''.join(f'<article class="card" data-reveal style="--d:{i*.07}s"><div class="body"><h3>{h}</h3><p>{p}</p></div></article>' for i, (h, p) in enumerate([('Neubau und Altbausanierung', 'Neben sämtlichen Zimmerer- und Dachdeckerarbeiten liegt der Schwerpunkt unserer Arbeit im Neubau und in der Altbausanierung.'), ('Ausbildung', 'Als Ausbildungsbetrieb geben wir unser Fachwissen an die nächste Generation weiter.'), ('Ein Ansprechpartner', 'Bei größeren Bauvorhaben koordinieren wir auf Wunsch die gesamte Abwicklung.')])) + '</div></div></section>'
ue += '<section class="sec"><div class="wrap"><div class="split" data-reveal><div><p class="eyebrow">Partnerfirmen</p><h2>Gesamtangebot mit starken Partnern.</h2><p>Durch unsere enge Zusammenarbeit mit bewährten Partnerfirmen der angrenzenden Gewerke können wir Ihnen auf Wunsch ein Gesamtangebot unterbreiten. Anschließend koordinieren wir den Ablauf und überprüfen die Bautätigkeit bis zur Schlussabnahme.</p><ul class="checks"><li>Holz-Zentrum Luhmann</li><li>Niewerth Gerüstbau GmbH</li><li>Fassadenfachbetrieb Volkan Kilinc</li></ul><p><span class="ph-note">[Partnerfirmen und Verlinkung vom Kunden bestätigen]</span></p></div><div><p class="eyebrow">Einzugsgebiet</p><h2>Wir arbeiten in:</h2><ul class="chips"><li>Celle</li><li>Hannover</li><li>Braunschweig</li><li>Bremen</li><li>Hildesheim</li><li>weitere auf Anfrage</li></ul></div></div></div></section>'
ue += cta('Lernen Sie uns kennen.', 'Wir freuen uns auf Ihre Anfrage.')
layout('ueber-uns.html', 'Über uns: Meisterbetrieb seit 2002 | HOLZWERK Celle', 'HOLZWERK GmbH: Zimmerei, Dachdeckerei, Maurer- und Malereibetrieb aus Celle. Gegründet 2002, über 40 Mitarbeiter, Ausbildungsbetrieb.', ue, crumbs='Über uns', active='ueber-uns.html')

# =============== 7 KONTAKT ===============
ko = '<section class="page-hero"><div class="wrap"><p class="eyebrow">Kontakt</p><h1>Erzählen Sie uns von Ihrem Vorhaben.</h1><p class="lead">Wir freuen uns auf Ihre Anfrage und melden uns bei Ihnen. <span class="ph-note">[Antwortzeit nur nennen, wenn der Kunde sie zusagt]</span></p></div></section>'
ko += '''<section class="sec" style="padding-top:0"><div class="wrap"><div class="contact" style="color:var(--ink)">
  <div data-reveal>
    <h2 style="font-size:1.6rem">HOLZWERK GmbH</h2>
    <p>Zimmerei, Dachdeckerei,<br>Maurer- und Malereibetrieb</p>
    <ul class="facts">
      <li><b style="color:var(--brand-ink)">Telefon</b><a href="tel:+4951419095610">0 51 41 – 90 95 610</a></li>
      <li><b style="color:var(--brand-ink)">E-Mail</b><a href="mailto:info@holzwerk-celle.de">info@holzwerk-celle.de</a></li>
      <li><b style="color:var(--brand-ink)">Adresse</b><span>Breite Straße 38<br>29221 Celle</span></li>
      <li><b style="color:var(--brand-ink)">Zeiten</b><span class="ph-note">[Öffnungs- und Erreichbarkeitszeiten vom Kunden]</span></li>
      <li><b style="color:var(--brand-ink)">Anfahrt</b><a href="https://www.openstreetmap.org/search?query=Breite%20Stra%C3%9Fe%2038%2C%20Celle" rel="noopener noreferrer" target="_blank">Route in der Karte öffnen (externer Dienst, öffnet in neuem Tab)</a></li>
    </ul>
    <p style="margin-top:1.6rem">Einzugsgebiet: Celle, Hannover, Braunschweig, Bremen und Hildesheim, weitere auf Anfrage.</p>
  </div>
  <form class="card-f" id="anfrage" method="post" action="#" novalidate data-reveal style="--d:.1s;border:1px solid var(--line)">
    <div><label for="name">Name</label><input id="name" name="name" type="text" autocomplete="name" required></div>
    <div><label for="kontakt-feld">Telefon oder E-Mail</label><input id="kontakt-feld" name="kontakt" type="text" autocomplete="email" required aria-describedby="k-h"><span id="k-h" class="hint">Darüber melden wir uns bei Ihnen.</span></div>
    <div><label for="leistung">Worum geht es?</label><select id="leistung" name="leistung"><option>Dach / Dachstuhl</option><option>Fachwerk / Altbausanierung</option><option>Umbau / Anbau / Carport</option><option>Innenausbau</option><option>Fassade / Verkleidung</option><option>Gesamtangebot mit mehreren Gewerken</option><option>Etwas anderes</option></select></div>
    <div><label for="msg">Ihr Vorhaben <span class="hint">(optional)</span></label><textarea id="msg" name="msg"></textarea></div>
    <div class="hp" aria-hidden="true"><label for="website">Nicht ausfüllen</label><input id="website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
    <p>Ihre Angaben verwenden wir nur zur Bearbeitung Ihrer Anfrage. Mehr in der <a href="datenschutz.html">Datenschutzerklärung</a>.</p>
    <button class="btn" type="submit">Anfrage senden</button>
    <p class="status" id="form-status" role="status" aria-live="polite"></p>
  </form>
</div></div></section>'''
layout('kontakt.html', 'Kontakt & Anfrage | HOLZWERK Celle', 'Kontakt zur HOLZWERK GmbH in Celle: Telefon 05141 9095610, E-Mail und Anfrageformular für Zimmerei, Dachdeckerei und Altbausanierung.', ko, crumbs='Kontakt', active='kontakt.html')

# =============== Nicht gezählte Seiten ===============
imp = '<section class="sec legal-page"><div class="wrap"><h1 style="font-size:var(--fs-2)">Impressum</h1><p><strong class="ph-note">[Rechtstext liefert der Kunde (Generator oder Anwalt)]</strong> Markentrix bindet ihn ein und prüft nur die Vollständigkeit der Pflichtangaben.</p><h2>Angaben der bisherigen Website (vom Kunden zu prüfen und zu aktualisieren)</h2><p>HOLZWERK GmbH<br>Zimmerei, Dachdeckerei, Maurer- und Malereibetrieb<br>Breite Straße 38<br>29221 Celle</p><p>Telefon: 0 51 41 – 90 95 610<br>E-Mail: info@holzwerk-celle.de</p><p>Amtsgericht Lüneburg: HRB 211594<br>Geschäftsführer: Jörg Reinstorf<br>USt-IdNr.: <span class="ph-note">[vom Kunden]</span><br>Kammer / Aufsichtsbehörde: <span class="ph-note">[vom Kunden]</span></p><h2>Verbraucherstreitbeilegung</h2><p>Die HOLZWERK GmbH beteiligt sich nicht an Verbraucherschlichtungsverfahren nach dem Verbraucherstreitbeilegungsgesetz. Streitigkeiten über den geschlossenen Vertrag und dessen Ausführung können vor der Vermittlungsstelle der Handwerkskammer Braunschweig-Lüneburg-Stade, Schlichtungsstelle, Friedenstraße 6, 21335 Lüneburg, verhandelt werden. <span class="ph-note">[Aktualität vom Kunden bestätigen]</span></p></div></section>'
layout('impressum.html', 'Impressum | HOLZWERK GmbH', 'Impressum der HOLZWERK GmbH, Celle.', imp)
dat = '<section class="sec legal-page"><div class="wrap"><h1 style="font-size:var(--fs-2)">Datenschutzerklärung</h1><p><strong class="ph-note">[Rechtstext liefert der Kunde (Generator oder Anwalt)]</strong></p><h2>Hinweise für die Erstellung</h2><p>Diese Website lädt keine Drittanbieter-Inhalte: Schriften und Skripte sind selbst gehostet, es gibt kein Tracking und keine Cookies. Hosting: Hetzner Online GmbH, Serverstandort Nürnberg. Das Kontaktformular verarbeitet Name, Telefon bzw. E-Mail und Anliegen zur Bearbeitung der Anfrage. Der Link „Route in der Karte öffnen“ führt nur auf Klick zu einem externen Kartendienst.</p></div></section>'
layout('datenschutz.html', 'Datenschutz | HOLZWERK GmbH', 'Datenschutzerklärung der HOLZWERK GmbH, Celle.', dat)
nf = '<section class="sec"><div class="wrap"><p class="eyebrow">Fehler 404</p><h1 style="font-size:var(--fs-2)">Diese Seite gibt es nicht.</h1><p class="lead">Vielleicht hilft Ihnen einer dieser Wege:</p><p><a class="btn" href="index.html">Zur Startseite</a> <a class="btn ghost" href="kontakt.html">Kontakt</a></p></div></section>'
layout('404.html', 'Seite nicht gefunden | HOLZWERK GmbH', 'Diese Seite wurde nicht gefunden.', nf)
open('robots.txt', 'w').write('User-agent: *\nDisallow: /\n# Demo: nicht indexieren. Beim Livegang durch Sitemap-Verweis ersetzen.\n')
