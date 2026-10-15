"""Aufruf: python3 tools/logo-svg.py static/logo.svg static/logo-dark.svg  (braucht: pip install fonttools)

Erzeugt logo.svg (Vektor-Nachbau des ElbDetail-Logos, Text als Pfade, transparenter Hintergrund)."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

def text_path(font_file, text, size, x, y, spacing=0.0):
    f = TTFont(font_file)
    gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
    s = size / upm
    d_parts = []; cx = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            cx += size * 0.3; continue
        pen = SVGPathPen(gs)
        tp = TransformPen(pen, (s, 0, 0, -s, x + cx, y))
        gs[gname].draw(tp)
        d_parts.append(pen.getCommands())
        cx += gs[gname].width * s + spacing
    return " ".join(p for p in d_parts if p), cx

BI = "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"
B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
W, H = 300, 120
word, ww = text_path(BI, "ElbDetail", 66, 0, 0)
# Wortmarke mittig ausrichten
wx = (W - ww) / 2
word, ww = text_path(BI, "ElbDetail", 66, wx, 86)
tag_size = 10.2
_, tw = text_path(B, "PREMIUM FAHRZEUGAUFBEREITUNG", tag_size, 0, 0, spacing=1.6)
tx = (W - tw) / 2
tag, _ = text_path(B, "PREMIUM FAHRZEUGAUFBEREITUNG", tag_size, tx, 108, spacing=1.6)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="ElbDetail – Premium Fahrzeugaufbereitung">
<defs>
<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5b9be8" stop-opacity="0"/><stop offset=".45" stop-color="#5b9be8"/><stop offset=".55" stop-color="#9cc4f5"/><stop offset="1" stop-color="#1c4f9c" stop-opacity="0"/></linearGradient>
<linearGradient id="roof" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".2"/><stop offset=".35" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity=".35"/></linearGradient>
<filter id="glow" x="-200%" y="-10%" width="500%" height="120%"><feGaussianBlur stdDeviation="1.6"/></filter>
</defs>
<g filter="url(#glow)"><rect x="236" y="2" width="3" height="116" fill="url(#bar)"/><rect x="252" y="2" width="4" height="116" fill="url(#bar)"/><rect x="266" y="8" width="2.5" height="104" fill="url(#bar)"/></g>
<rect x="237" y="6" width="1.2" height="108" fill="url(#bar)"/><rect x="253.4" y="6" width="1.4" height="108" fill="url(#bar)"/>
<path d="M14 54 C 40 46, 70 41, 96 38 C 116 26, 136 17, 162 15 C 196 13, 226 20, 252 33 C 266 37, 280 40, 292 46" fill="none" stroke="url(#roof)" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M104 39 C 122 30, 140 24, 164 23 C 192 22, 216 28, 236 37" fill="none" stroke="url(#roof)" stroke-width="1.9" stroke-linecap="round" opacity=".85"/>
<path d="{word}" fill="#fff"/>
<rect x="{tx - 22:.1f}" y="102.6" width="16" height="1.4" fill="#5b9be8"/><rect x="{tx + tw + 4:.1f}" y="102.6" width="16" height="1.4" fill="#5b9be8"/>
<path d="{tag}" fill="#c9d3e1"/>
</svg>
'''
import re
svg = re.sub(r'd="([^"]+)"', lambda m: 'd="' + re.sub(r"-?\d+\.\d+", lambda n: ("%.1f" % float(n.group())).rstrip("0").rstrip("."), m.group(1)) + '"', svg)
open(sys.argv[1], "w").write(svg)
if len(sys.argv) > 2:  # dunkle Schrift für helle Hintergründe
    open(sys.argv[2], "w").write(svg.replace('fill="#fff"', 'fill="#1f2329"').replace('fill="#c9d3e1"', 'fill="#4a5361"').replace('stop-color="#fff"', 'stop-color="#1f2329"'))
print("ok", round(ww), round(tw), len(svg))
