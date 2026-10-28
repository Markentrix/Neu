"""Erzeugt die Schichtwerk-Logodateien in brand/ (SVG mit Schrift als Pfade, PNG-Exporte).
Aufruf: python3 build/logo.py"""
import os, sys, subprocess, json, tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "brand")
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website-fertig", "assets", "fonts", "Fraunces-normal.woff2")
FONT_LOCATION = {"wght": 600, "opsz": 72}
NAVY, CREAM = "#1f4d3a", "#f1ede4"
L1, L2, L3 = "#f1e6d2", "#d9a06b", "#b8763f"   # Schichten hell -> dunkel (Sand -> Kupfer)


def mark(tile=True, mono=None):
    """Bildmarke 64x64: drei versetzte Schichten bilden ein S."""
    c1, c2, c3 = (mono, mono, mono) if mono else (L1, L2, L3)
    s = ""
    if tile:
        s += f'<rect width="64" height="64" rx="14" fill="{NAVY}"/>'
    s += (f'<rect x="18" y="14" width="34" height="11" rx="4" fill="{c1}"/>'
          f'<rect x="12" y="27" width="34" height="11" rx="4" fill="{c2}"/>'
          f'<rect x="18" y="40" width="34" height="11" rx="4" fill="{c3}"/>')
    return s


def wordmark_paths(text, size, x0, baseline, tracking=0.0):
    """Text als SVG-Pfade aus Inter Bold. Gibt (pfade, breite) zurück."""
    font = TTFont(FONT); gs = font.getGlyphSet(location=FONT_LOCATION) if "fvar" in font else font.getGlyphSet(); cmap = font.getBestCmap(); upm = font["head"].unitsPerEm
    kern = {}
    try:
        gpos = font["GPOS"].table
        for lookup in gpos.LookupList.Lookup:
            for st in lookup.SubTable:
                if getattr(st, "Format", 0) == 1 and hasattr(st, "PairSet"):
                    for g1, ps in zip(st.Coverage.glyphs, st.PairSet):
                        for pr in ps.PairValueRecord:
                            v = getattr(pr.Value1, "XAdvance", 0)
                            if v: kern[(g1, pr.SecondGlyph)] = v
    except Exception:
        pass
    scale = size / upm; x = x0; out = []; prev = None
    for ch in text:
        g = cmap[ord(ch)]
        if prev and (prev, g) in kern:
            x += kern[(prev, g)] * scale
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        d = pen.getCommands()
        if d: out.append(d)
        x += gs[g].width * scale + tracking * size
        prev = g
    return out, x - x0 - tracking * size


def logo_svg(dark_bg=False, with_tile=True):
    """Horizontales Logo: Marke + Wortmarke. Höhe 64, Breite dynamisch."""
    size = 44; gap = 16; x0 = 64 + gap; baseline = 32 + size * 0.34
    p1, w1 = wordmark_paths("Schicht", size, x0, baseline)
    p2, w2 = wordmark_paths("werk", size, x0 + w1, baseline)
    text_col = CREAM if dark_bg else NAVY
    width = int(x0 + w1 + w2 + 2)
    paths = "".join(f'<path d="{d}" fill="{text_col}"/>' for d in p1) + "".join(f'<path d="{d}" fill="{"#d9a06b" if dark_bg else "#9e6230"}"/>' for d in p2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" width="{width}" height="64" role="img" aria-label="Schichtwerk">'
            f'{mark(tile=with_tile)}{paths}</svg>')


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {
        "schichtwerk-logo.svg": logo_svg(False, True),
        "schichtwerk-logo-dunkel.svg": logo_svg(True, True),
        "schichtwerk-logo-ohne-kachel-dunkel.svg": logo_svg(True, False),
        "schichtwerk-marke.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(True)}</svg>',
        "schichtwerk-marke-ohne-kachel.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(False)}</svg>',
        "schichtwerk-marke-einfarbig.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(False, "#1c2a24")}</svg>',
    }
    for name, svg in files.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(svg)
    # PNG-Exporte und Vorschau
    jobs = []; tmp = tempfile.mkdtemp()
    def job(svg, name, w, h, bg):
        p = os.path.join(tmp, name + ".svg"); open(p, "w").write(svg)
        jobs.append({"svg": p, "png": os.path.join(OUT, name + ".png"), "w": w, "h": h, "bg": bg})
    def pad(svg, w, h, bg, scale):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/>'
                f'<g transform="translate({w/2},{h/2}) scale({scale})">{svg}</g></svg>')
    inner = logo_svg(False, True); vb = int(inner.split('viewBox="0 0 ')[1].split(' ')[0])
    job(pad(f'<g transform="translate({-vb/2},-32)">{inner.split(">",1)[1][:-6]}</g>', 2400, 800, "#ffffff", 6), "schichtwerk-logo-2400", 2400, 800, "#ffffff")
    inner = logo_svg(True, True)
    job(pad(f'<g transform="translate({-vb/2},-32)">{inner.split(">",1)[1][:-6]}</g>', 2400, 800, NAVY, 6), "schichtwerk-logo-dunkel-2400", 2400, 800, NAVY)
    job(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="1024" height="1024">{mark(True)}</svg>', "schichtwerk-marke-1024", 1024, 1024, "")
    jf = os.path.join(tmp, "jobs.json"); json.dump(jobs, open(jf, "w"))
    subprocess.run(["node", os.path.join(ROOT, "build", "render.js"), jf], check=True)
    print("Logo-Dateien:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
