"""Erzeugt alle Markentrix-Logo-Dateien (SVG) aus der vermessenen Konstruktion.
Aufruf: python3 build_logo.py <wm.json> <zielordner>"""
import json, sys
wm = json.load(open(sys.argv[1])); out = sys.argv[2]
NAVY, WHITE, BLACK = '#0B1020', '#FFFFFF', '#05070B'
MW, MH = 522, 447                      # Bildmarke
C = MH / 1.66                          # Versalhöhe der Wortmarke
s = C / wm['cap']                      # Skalierung Schrift
GAP = 0.62 * C
BASE = MH - 9                          # Grundlinie (Rundungen stehen leicht über)
GRAD = ('<linearGradient id="mx" gradientUnits="userSpaceOnUse" x1="51" y1="468" x2="469" y2="-30">'
        '<stop offset="0" stop-color="#28C7F7"/><stop offset=".55" stop-color="#1E9BFF"/>'
        '<stop offset="1" stop-color="#8B5CF6"/></linearGradient>')
def mark(paint):
    return (f'<g fill="none" stroke="{paint}" stroke-linecap="round" stroke-linejoin="round">'
            '<path stroke-width="82" d="M41 406V107.5L227.5 277.5 414 107.5V406"/>'
            '<path stroke-width="54" d="M414 107.5 495 27M415 27h80v80.5"/></g>')
# Wortmarke als Pfade (Space Grotesk Bold, in Kurven)
import re
def word(fill, x0):
    first_lsb = 62  # linker Rand des M in Schrifteinheiten wird unten exakt bestimmt
    g = ''.join(f'<path transform="translate({x})" d="{d}"/>' for x, d in wm['paths'])
    return f'<g fill="{fill}" transform="translate({x0:.1f} {BASE}) scale({s:.5f} -{s:.5f})">{g}</g>'
def svg(w, h, body, defs='', pad=0, bg=None):
    vb = f'{-pad:.0f} {-pad:.0f} {w+2*pad:.0f} {h+2*pad:.0f}'
    rect = f'<rect x="{-pad}" y="{-pad}" width="{w+2*pad}" height="{h+2*pad}" fill="{bg}"/>' if bg else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="Markentrix">'
            f'<defs>{defs}</defs>{rect}{body}</svg>\n')
ink_l, ink_r = wm['ink']
WX = MW + GAP - ink_l * s
LW = MW + GAP + (ink_r - ink_l) * s
files = {
 'markentrix-logo-farbe-hell':  svg(LW, MH, mark('url(#mx)') + word(NAVY, WX), GRAD),
 'markentrix-logo-farbe-dunkel':svg(LW, MH, mark('url(#mx)') + word(WHITE, WX), GRAD),
 'markentrix-logo-navy':        svg(LW, MH, mark(NAVY) + word(NAVY, WX)),
 'markentrix-logo-schwarz':     svg(LW, MH, mark(BLACK) + word(BLACK, WX)),
 'markentrix-logo-weiss':       svg(LW, MH, mark(WHITE) + word(WHITE, WX)),
 'markentrix-bildmarke-farbe':  svg(MW, MH, mark('url(#mx)'), GRAD),
 'markentrix-bildmarke-navy':   svg(MW, MH, mark(NAVY)),
 'markentrix-bildmarke-weiss':  svg(MW, MH, mark(WHITE)),
}
# Profilbild / App-Icon: Bildmarke auf Quadrat, Marke = 56 % der Kantenlänge
def icon(bg, paint, defs=''):
    S = MW / 0.56; ox = (S - MW) / 2; oy = (S - MH) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S:.0f} {S:.0f}" role="img" aria-label="Markentrix">'
            f'<defs>{defs}</defs><rect width="{S:.0f}" height="{S:.0f}" fill="{bg}"/>'
            f'<g transform="translate({ox:.1f} {oy:.1f})">{mark(paint)}</g></svg>\n')
files['markentrix-profilbild-hell'] = icon(WHITE, 'url(#mx)', GRAD)
files['markentrix-profilbild-dunkel'] = icon(NAVY, 'url(#mx)', GRAD)
for n, c in files.items(): open(f'{out}/{n}.svg', 'w').write(c)
json.dump({'MW': MW, 'MH': MH, 'C': C, 'GAP': GAP, 'LW': LW, 'BASE': BASE}, open(f'{out}/../masse.json', 'w'), indent=1)
print({k: round(v, 1) for k, v in {'C': C, 'GAP': GAP, 'LW': LW}.items()})
