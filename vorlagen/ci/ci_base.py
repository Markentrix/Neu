# -*- coding: utf-8 -*-
"""Markenhandbuch Version 3.1 (November 2026): Grundlagen für den Generator.
Farbwelt D: Salz und Reif statt Kreide und Leinen, Kupfer als Handlungsfarbe, Kupferwort statt Kupferstrich."""
import os, base64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FONTS = os.path.join(ROOT, 'static', 'fonts')
LOGO = os.path.join(ROOT, 'static', 'img', 'logo')

# ── Farben (Version 3.1) ──
SALZ, TIEFSEE, PFAU, REIF, KUPFER = '#F4F6F7', '#0C2128', '#045268', '#E0E6E9', '#C67432'
KUPFER_D, KUPFER_H, PFAU_H, NEBEL, NEBEN, WEISS = '#964F08', '#F1A268', '#62B2D0', '#E1F0F6', '#465A62', '#FFFFFF'
LINIE = '#D8DFE3'
FEHLER = '#B3261E'


def svg(name):
    """SVG-Datei des CI-Pakets als Zeichenkette (inline)."""
    return open(os.path.join(LOGO, name), encoding='utf-8').read()


def svg_uri(name):
    return 'data:image/svg+xml;base64,' + base64.b64encode(open(os.path.join(LOGO, name), 'rb').read()).decode()


def font_face():
    f = lambda fam, w, file: "@font-face{font-family:'%s';font-weight:%s;src:url('file://%s/%s') format('woff2')}" % (fam, w, FONTS, file)
    return '\n'.join([f('Archivo', '700', 'archivo-700.woff2'), f('Archivo', '800', 'archivo-800.woff2'),
                      f('Source Sans 3', '400', 'source-sans-3-400.woff2'), f('Source Sans 3', '600', 'source-sans-3-600.woff2'),
                      f('Source Sans 3', '700', 'source-sans-3-700.woff2')])


CSS = font_face() + """
@page{size:A4;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{background:%(salz)s;font-family:'Source Sans 3',Arial,sans-serif;color:%(tiefsee)s;font-size:12px;line-height:1.4}
.pg{position:relative;width:794px;height:1123px;padding:48px 60px 0;overflow:hidden;background:%(salz)s;page-break-after:always;break-after:page}
.pg:last-child{page-break-after:auto;break-after:auto}
.hd{display:flex;align-items:center;gap:14px;height:14px;font:600 8.5px 'Source Sans 3';letter-spacing:.11em;text-transform:uppercase;color:%(neben)s}
.hd i{flex:1;height:1px;background:%(linie)s}
.hd b{display:block;width:38px;height:3px;background:%(kupfer)s}
.ft{position:absolute;left:60px;right:60px;bottom:30px;border-top:1px solid %(linie)s;padding-top:9px;display:flex;justify-content:space-between;font:600 8.5px 'Source Sans 3';letter-spacing:.1em;text-transform:uppercase;color:%(neben)s}
h1{font:800 36px/1.08 Archivo;letter-spacing:-.025em;margin:34px 0 8px;color:%(tiefsee)s}
h1 .k{color:%(kupfer)s}
.lead{font-size:14.5px;line-height:1.45;max-width:600px;margin-bottom:22px}
h2{font:800 15px/1.2 Archivo;letter-spacing:-.01em;margin:0 0 8px}
h3{font:700 12.5px/1.25 Archivo;margin:0 0 5px}
.k{color:%(kupfer)s}
.ky{color:%(kupfer_d)s}
.card{background:%(weiss)s;border:1px solid %(linie)s;border-radius:9px;padding:17px 18px}
.card.soft{background:%(reif)s;border-color:%(reif)s}
.card.dk{background:%(tiefsee)s;border-color:%(tiefsee)s;color:%(weiss)s}
.card.pf{background:%(pfau)s;border-color:%(pfau)s;color:%(weiss)s}
.note{background:%(reif)s;border-radius:9px;padding:13px 18px;font-size:11.5px;line-height:1.5}
.g{display:grid;gap:11px}
.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:1fr 1fr 1fr}.g4{grid-template-columns:repeat(4,1fr)}.g5{grid-template-columns:repeat(5,1fr)}.g6{grid-template-columns:repeat(6,1fr)}
.mt{margin-top:16px}.mt2{margin-top:11px}.mb{margin-bottom:11px}
.lbl{font:700 8.5px 'Source Sans 3';letter-spacing:.11em;text-transform:uppercase;color:%(pfau)s;margin-bottom:6px}
.lbl.n{color:%(neben)s}
ul.s{list-style:none}
ul.s li{position:relative;padding-left:14px;margin-bottom:5px;font-size:11.5px;line-height:1.38}
ul.s li::before{content:'';position:absolute;left:1px;top:5px;width:5px;height:5px;background:%(pfau)s}
ul.x li::before{content:'×';font-family:'DejaVu Sans',sans-serif;background:none;color:%(fehler)s;font-weight:700;top:-1px;font-size:12px;width:auto;height:auto}
ul.c li::before{content:'✓';font-family:'DejaVu Sans',sans-serif;background:none;color:%(pfau)s;font-weight:700;top:-1px;font-size:11px;width:auto;height:auto}
ol.n{list-style:none;counter-reset:n}
ol.n li{counter-increment:n;position:relative;padding:5px 0 5px 24px;border-bottom:1px solid %(linie)s;font-size:11.5px;line-height:1.38}
ol.n li:last-child{border-bottom:0}
ol.n li::before{content:counter(n);position:absolute;left:0;top:5px;font:700 11px 'Source Sans 3';color:%(pfau)s}
ol.z li::before{content:counter(n,decimal-leading-zero)}
table{border-collapse:collapse;width:100%%}
.kv td,.kv th{vertical-align:top;padding:5px 0;border-bottom:1px solid %(linie)s;font-size:11px;line-height:1.35;text-align:left}
.kv tr:last-child td{border-bottom:0}
.kv td:first-child{font-weight:700;padding-right:12px;white-space:nowrap}
.kv.w td:first-child{white-space:normal}
.kv th{font:700 8px 'Source Sans 3';letter-spacing:.1em;text-transform:uppercase;color:%(neben)s;padding-bottom:6px}
.tb td,.tb th{padding:6px 6px 6px 0;border-bottom:1px solid %(linie)s;font-size:10.8px;text-align:left;vertical-align:middle}
.tb th{font:700 8px 'Source Sans 3';letter-spacing:.09em;text-transform:uppercase;color:%(neben)s}
.tb tr:last-child td{border-bottom:0}
.tb td:first-child{font-weight:700}
.mono{font-family:'DejaVu Sans Mono','Courier New',monospace;font-size:10px}
.sw{height:54px;border-radius:7px;border:1px solid rgba(12,33,40,.12)}
.cap{font-size:10px;color:%(neben)s;line-height:1.35;margin-top:4px}
.cap b{color:%(tiefsee)s}
.ok::before{content:'✓ ';font-family:'DejaVu Sans',sans-serif;color:%(pfau)s;font-weight:700}
.no::before{content:'× ';font-family:'DejaVu Sans',sans-serif;color:%(fehler)s;font-weight:700}
.tag{display:inline-block;background:%(kupfer)s;color:%(tiefsee)s;font:700 8px 'Source Sans 3';letter-spacing:.08em;padding:2px 6px;border-radius:3px;vertical-align:1px}
.btn{display:inline-block;font:600 11.5px 'Source Sans 3';padding:9px 15px;border-radius:4px;border:1px solid %(kupfer)s;background:%(kupfer)s;color:%(tiefsee)s}
.btn.t{background:%(tiefsee)s;border-color:%(tiefsee)s;color:%(weiss)s}
.btn.s{background:%(weiss)s;border-color:%(tiefsee)s;color:%(tiefsee)s}
.code{background:%(tiefsee)s;color:#EAF2F5;border-radius:9px;padding:13px 16px;font-family:'DejaVu Sans Mono',monospace;font-size:8.6px;line-height:1.5}
.code b{color:%(kupfer_h)s;font-weight:400}
.dark{background:%(tiefsee)s;color:%(weiss)s}
.small{font-size:10.5px;color:%(neben)s;line-height:1.4}
.pg.dense h1{margin-top:26px}.pg.dense .lead{margin-bottom:14px}.pg.dense .card{padding:13px 16px}.pg.dense .mt2{margin-top:8px}.pg.dense .mt{margin-top:11px}
.pg.dense .tb td,.pg.dense .tb th{padding:4px 6px 4px 0}.pg.dense ol.n li{padding:3px 0 3px 24px}.pg.dense ul.s li{margin-bottom:3px}.pg.dense .kv td{padding:3px 0}
""" % dict(salz=SALZ, tiefsee=TIEFSEE, pfau=PFAU, reif=REIF, kupfer=KUPFER, kupfer_d=KUPFER_D, kupfer_h=KUPFER_H, neben=NEBEN, weiss=WEISS, linie=LINIE, fehler=FEHLER)


def k(txt):
    """Kupferwort (Schlüsselwort in der Überschrift)."""
    return '<span class="k">%s</span>' % txt


DENSE = {21, 22, 25, 26}


def page(n, sec, name, title, lead, body, foot_title=None):
    return ('<section class="pg%s"><div class="hd"><span>%02d — %s</span><i></i><span>Mehr Anfragen. Weniger Aufwand.</span></div>'
            '<h1>%s</h1><p class="lead">%s</p>%s'
            '<div class="ft"><span>Markentrix · Markenhandbuch 2026 · Version 3.1</span><span>%02d · %s</span></div></section>') % (' dense' if n in DENSE else '', n, sec.upper(), title, lead, body, n, (foot_title or name).upper())


def card(inner, cls=''):
    return '<div class="card %s">%s</div>' % (cls, inner)


def lst(items, cls=''):
    return '<ul class="s %s">%s</ul>' % (cls, ''.join('<li>%s</li>' % i for i in items))


def kv(rows, cls=''):
    return '<table class="kv %s">%s</table>' % (cls, ''.join('<tr><td>%s</td><td>%s</td></tr>' % (a, b) for a, b in rows))


def grid(cls, *cells, style=''):
    return '<div class="g %s" style="%s">%s</div>' % (cls, style, ''.join(cells))


def ol(items, cls='n'):
    return '<ol class="%s">%s</ol>' % (cls, ''.join('<li>%s</li>' % i for i in items))


def logo_img(name, h=None, w=None, style=''):
    st = ''
    if h: st += 'height:%spx;' % h
    if w: st += 'width:%spx;' % w
    return '<img src="%s" style="display:block;%s%s">' % (svg_uri(name), st, style)
