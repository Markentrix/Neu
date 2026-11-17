#!/usr/bin/env python3
"""Übernimmt Variante D fest in static/assets/mx.css (einmalig). Aufruf: python3 mk_final.py
 1. Creme- und Leinen-Töne werden durch Salz und Reif ersetzt (Werte und Tokens).
 2. Der Block „44 · Farbwelt 2026-11“ wird angehängt: dunkle Flächen, Kupfer als Handlungsfarbe, Kopfzeile, Fokus."""
import re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
CSS = os.path.join(HERE, '..', '..', 'static', 'assets', 'mx.css')
css = open(CSS, encoding='utf-8').read()
if '44 · Farbwelt' in css: sys.exit('Block 44 ist schon vorhanden.')
g = open(os.path.join(HERE, 'gen_thema.py'), encoding='utf-8').read()
head = g[:g.index('rules = flat_rules(css)')]
ns = {'__file__': os.path.join(HERE, 'gen_thema.py')}
sys.argv = ['x', CSS, '/dev/null']
exec(head, ns)
rules = ns['flat_rules'](css)

def wrap(media, sels, body):
    r = '%s{%s}' % (sels, body)
    for m in reversed(media): r = '%s{%s}' % (m, r)
    return r

out = []
# (a) vorhandene Regeln für dunkle Flächen auf Angebot (Pfauenblau) und Vorher-nachher (Tiefsee) übertragen
for media, sel, decl in rules:
    if '.sec--dark' not in sel: continue
    for tgt in ('.ba-sec', '.deal-sec'):
        s2 = ','.join('html:root ' + x.strip().replace('.sec--dark', tgt) for x in sel.split(',') if '.sec--dark' in x)
        out.append(wrap(media, s2, decl))
# (b) Handregeln B und D, Präfix auf html:root umgestellt
hand = open(os.path.join(HERE, 'thema-hand.css'), encoding='utf-8').read()
hb, _, hd = hand.partition('/* ───────── D')
lines = [l for l in hb.split('\n') if 'data-thema="b"' in l]
lines += [l for l in ('/* ───────── D' + hd).split('\n')]
for l in lines:
    l = l.replace('html[data-thema="b"]', 'html:root').replace('html[data-thema="d"]', 'html:root')
    out.append(l)
block = '\n/* 44 · Farbwelt 2026-11: Salz und Reif statt Creme, Kupfer als Handlungsfarbe (Variante D) */\n:root{--dk-t:#0C2128;--dk-p:#045268}\n' + '\n'.join(out) + '\n'
css = css + block
# Werte ersetzen
css = re.sub(r'#F7F4EE', '#F4F6F7', css, flags=re.I)
css = re.sub(r'#EAE2D3', '#E0E6E9', css, flags=re.I)
css = css.replace('rgba(247,244,238,', 'rgba(244,246,247,').replace('rgba(234,226,211,', 'rgba(224,230,233,')
# Tokens
css = css.replace('--kreide:#F4F6F7;          /* Grund und Weißraum */', '--kreide:#F4F6F7;          /* Salz: Grund und Weißraum */')
css = css.replace('--leinen:#E0E6E9;          /* Flächenfarbe, Rahmen, Trennlinien */', '--leinen:#E0E6E9;          /* Reif: Flächenfarbe, Trennlinien */')
css = css.replace('  --border:#E0E6E9;', '  --border:#D8DFE3;')
css = css.replace('--nebentext:#4E5C5F;', '--nebentext:#465A62;').replace('--muted:#4E5C5F;', '--muted:#465A62;')
open(CSS, 'w', encoding='utf-8').write(css)
print('fertig,', len(out), 'Regeln im Block 44')
