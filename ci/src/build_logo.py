"""Erzeugt alle Markentrix-Logo-Dateien (SVG) aus der vermessenen Konstruktion.
Aufruf: python3 build_logo.py <wortmarke.json> <zielordner>"""
import json, sys
wm = json.load(open(sys.argv[1])); out = sys.argv[2]
TIEFSEE, PFAU, PFAU_HELL, KREIDE, WEISS, SCHWARZ = '#0C2128', '#045268', '#62B2D0', '#F7F4EE', '#FFFFFF', '#000000'
MW, MH = 522, 447                      # Bildmarke
C = MH / 1.66                          # Versalhöhe der Wortmarke
s = C / wm['cap']                      # Skalierung Schrift
GAP = 0.62 * C
BASE = MH - 9                          # Grundlinie (Rundungen stehen leicht über)
def mark(m, pfeil):
    # Der Aufstrich des M und der Pfeil bilden zusammen die Aufwärtslinie und liegen oben.
    return ('<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path stroke="{m}" stroke-width="82" d="M41 406V107.5L227.5 277.5M414 107.5V406"/>'
            f'<path stroke="{pfeil}" stroke-width="82" d="M227.5 277.5 414 107.5"/>'
            f'<path stroke="{pfeil}" stroke-width="54" d="M414 107.5 495 27M415 27h80v80.5"/></g>')
def word(fill, x0):
    g = ''.join(f'<path transform="translate({x:.1f})" d="{d}"/>' for x, d in wm['paths'])
    return f'<g fill="{fill}" transform="translate({x0:.1f} {BASE}) scale({s:.5f} -{s:.5f})">{g}</g>'
def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Markentrix">{body}</svg>\n')
ink_l, ink_r = wm['ink']
WX = MW + GAP - ink_l * s
LW = MW + GAP + (ink_r - ink_l) * s
files = {
 'markentrix-logo-farbe-hell':   svg(LW, MH, mark(TIEFSEE, PFAU) + word(TIEFSEE, WX)),
 'markentrix-logo-farbe-dunkel': svg(LW, MH, mark(KREIDE, PFAU_HELL) + word(KREIDE, WX)),
 'markentrix-logo-tiefsee':      svg(LW, MH, mark(TIEFSEE, TIEFSEE) + word(TIEFSEE, WX)),
 'markentrix-logo-schwarz':      svg(LW, MH, mark(SCHWARZ, SCHWARZ) + word(SCHWARZ, WX)),
 'markentrix-logo-weiss':        svg(LW, MH, mark(WEISS, WEISS) + word(WEISS, WX)),
 'markentrix-bildmarke-farbe-hell':   svg(MW, MH, mark(TIEFSEE, PFAU)),
 'markentrix-bildmarke-farbe-dunkel': svg(MW, MH, mark(KREIDE, PFAU_HELL)),
 'markentrix-bildmarke-tiefsee': svg(MW, MH, mark(TIEFSEE, TIEFSEE)),
 'markentrix-bildmarke-weiss':   svg(MW, MH, mark(WEISS, WEISS)),
}
def icon(bg, m, pfeil):   # Profilbild: Bildmarke = 56 % der Kantenlänge, mittig
    S = MW / 0.56; ox = (S - MW) / 2; oy = (S - MH) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S:.0f} {S:.0f}" role="img" aria-label="Markentrix">'
            f'<rect width="{S:.0f}" height="{S:.0f}" fill="{bg}"/><g transform="translate({ox:.1f} {oy:.1f})">{mark(m, pfeil)}</g></svg>\n')
files['markentrix-profilbild-hell'] = icon(KREIDE, TIEFSEE, PFAU)
files['markentrix-profilbild-dunkel'] = icon(TIEFSEE, KREIDE, PFAU_HELL)
for n, c in files.items(): open(f'{out}/{n}.svg', 'w').write(c)
print({k: round(v, 2) for k, v in {'C': C, 'Abstand': GAP, 'Logobreite': LW, 'Wortmarke_in_C': (ink_r - ink_l) * s / C, 'Logo_Seitenverhaeltnis': LW / MH}.items()})
