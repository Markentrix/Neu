"""Markentrix-Logo als SVG: Bildzeichen (Original-Pfade) + Schriftzug in Space Grotesk 700 als Pfade."""
import sys, re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
font_file, out, color = sys.argv[1], sys.argv[2], sys.argv[3]
f = TTFont(font_file); gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
size = 28.0; s = size / upm; x0 = 51.0; base = 33.5; tracking = -0.02 * size
parts = []; cx = 0.0
for ch in "markentrix":
    g = cmap[ord(ch)]; pen = SVGPathPen(gs)
    gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x0 + cx, base))); parts.append(pen.getCommands())
    cx += gs[g].width * s + tracking
d = " ".join(parts)
d = re.sub(r"-?\d+\.\d+", lambda n: ("%.1f" % float(n.group())).rstrip("0").rstrip("."), d)
W = round(x0 + cx + 2)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 48" width="{W}" height="48" role="img" aria-label="Markentrix">
<defs><linearGradient id="mxg" x1="9" y1="40" x2="39" y2="9" gradientUnits="userSpaceOnUse"><stop stop-color="#28C7F7"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>
<g fill="none" stroke="url(#mxg)" stroke-linecap="round" stroke-linejoin="round"><path d="M11 38V13.5L23.5 26.5L31 18.5" stroke-width="5.6"/><path d="M31 38V18.5" stroke-width="5.6"/><path d="M31 18.5L37 12.5M37 12.5L30.5 12.5M37 12.5L37 19" stroke-width="5"/></g>
<path d="{d}" fill="{color}"/>
</svg>
'''
open(out, "w").write(svg); print(W, len(svg))
