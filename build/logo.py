"""Erzeugt die Schichtatelier-Logodateien in brand/ (SVG mit Schrift als Pfade, PNG-Exporte).
Aufruf: python3 build/logo.py"""
import os, sys, subprocess, json, tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "brand")
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website-fertig", "assets", "fonts", "AbrilFatface.woff2")
FONT_LOCATION = {}
NAVY, CREAM = "#1f4d3a", "#f1ede4"
L1, L2, L3 = "#f1e6d2", "#d9a06b", "#b8763f"   # Schichten hell -> dunkel (Sand -> Kupfer)


def s_path():
    """Umriss des S aus Abril Fatface, zentriert in 64x64."""
    from fontTools.pens.boundsPen import BoundsPen
    font = TTFont(FONT); gs = font.getGlyphSet(); g = gs[font.getBestCmap()[ord("S")]]
    upm = font["head"].unitsPerEm; size = 56; sc = size / upm
    bp = BoundsPen(gs); g.draw(bp); b = bp.bounds
    gw = (b[2] - b[0]) * sc; gh = (b[3] - b[1]) * sc
    x0 = 32 - gw / 2 - b[0] * sc; base = 32 + gh / 2 + b[1] * sc
    pen = SVGPathPen(gs); g.draw(TransformPen(pen, (sc, 0, 0, -sc, x0, base)))
    return pen.getCommands()


def _hex(c): return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
def _mix(a, b, t): return "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def bands(n=11, top=8, bottom=56, gap=1.6, cols=(L1, L2, L3), x=0, w=64):
    """Waagerechte Schichten mit Verlauf hell -> dunkel."""
    h = (bottom - top) / n; out = ""
    a, b, c = _hex(cols[0]), _hex(cols[1]), _hex(cols[2])
    for i in range(n):
        t = i / max(1, n - 1)
        col = _mix(a, b, t / .5) if t < .5 else _mix(b, c, (t - .5) / .5)
        out += f'<rect x="{x}" y="{top + i * h:.2f}" width="{w}" height="{h - gap:.2f}" fill="{col}"/>'
    return out


_S = None
def mark(tile=True, mono=None, uid="s", small=False, missing=None):
    """Bildmarke 64x64: ein S aus Druckschichten. small=True: weniger, kräftigere Schichten für Favicons.
    missing: Index einer fehlenden Schicht (404-Grafik)."""
    global _S
    if _S is None: _S = s_path()
    cols = (mono, mono, mono) if mono else ((L1, L2, L3) if tile else ("#c98a4f", "#9e6230", "#6e4420"))
    n, gap = (7, 2.6) if small else (11, 1.8)
    layers = bands(n=n, gap=gap, cols=cols)
    if missing is not None:
        parts = layers.split("<rect "); parts.pop(missing + 1); layers = "<rect ".join(parts)
    s = f'<defs><clipPath id="{uid}"><path d="{_S}"/></clipPath></defs>'
    if tile:
        s += f'<rect width="64" height="64" rx="14" fill="{NAVY}"/>'
    s += f'<g clip-path="url(#{uid})">{layers}</g>'
    return s


def seal(size=240):
    """Rundes Siegel für Verpackung, Aufkleber, Social-Profil."""
    inner = mark(tile=False, uid="seal", cols=None) if False else None
    body = (f'<circle cx="60" cy="60" r="58" fill="{NAVY}"/><circle cx="60" cy="60" r="52" fill="none" stroke="{L2}" stroke-width=".8" stroke-dasharray="1.5 2"/>'
            f'<circle cx="60" cy="60" r="35" fill="none" stroke="{L2}" stroke-width=".8"/>'
            f'<defs><clipPath id="sealS"><path d="{s_path()}" transform="translate(28 28)"/></clipPath><path id="sealRing" d="M60,60 m-44,0 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0"/></defs>'
            f'<g clip-path="url(#sealS)"><g transform="translate(28 28)">{bands()}</g></g>')
    return body


def wordmark_paths(text, size, x0, baseline, tracking=0.0):
    """Text als SVG-Pfade aus Hanken Grotesk. Gibt (pfade, breite) zurück."""
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
    p2, w2 = wordmark_paths("atelier", size, x0 + w1, baseline)
    text_col = CREAM if dark_bg else NAVY
    width = int(x0 + w1 + w2 + 2)
    paths = "".join(f'<path d="{d}" fill="{text_col}"/>' for d in p1) + "".join(f'<path d="{d}" fill="{"#d9a06b" if dark_bg else "#9e6230"}"/>' for d in p2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" width="{width}" height="64" role="img" aria-label="Schichtatelier">'
            f'{mark(tile=with_tile, uid="lg")}{paths}</svg>')


def main():
    os.makedirs(OUT, exist_ok=True)
    ring_paths = ""
    # Siegel-Umschrift aus Hanken Grotesk als Pfade entlang des Kreises
    import math
    ifont = TTFont(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website-fertig", "assets", "fonts", "HankenGrotesk.woff2")); igs = ifont.getGlyphSet(); icmap = ifont.getBestCmap(); iupm = ifont["head"].unitsPerEm
    text = "SCHICHTATELIER · 3D-DRUCK-MANUFAKTUR · CELLE · "; fsize = 6.5; r = 44.5; sc = fsize / iupm
    total = sum(igs[icmap[ord(ch)]].width * sc + 1.6 for ch in text); ang = -90 - 360 * 0 ; circ = 2 * math.pi * r
    step_deg = 360 / circ
    a = -90.0
    for ch in text:
        g = igs[icmap[ord(ch)]]; adv = g.width * sc + 1.6
        rad = math.radians(a + (adv / 2) * step_deg)
        cx = 60 + r * math.cos(rad); cy = 60 + r * math.sin(rad)
        rot = math.degrees(rad) + 90
        pen = SVGPathPen(igs); g.draw(TransformPen(pen, (sc, 0, 0, -sc, -g.width * sc / 2, fsize * 0.36)))
        d = pen.getCommands()
        if d: ring_paths += f'<path d="{d}" fill="{CREAM}" transform="translate({cx:.2f} {cy:.2f}) rotate({rot:.2f})"/>'
        a += adv * step_deg
    files = {
        "schichtatelier-logo.svg": logo_svg(False, True),
        "schichtatelier-logo-dunkel.svg": logo_svg(True, True),
        "schichtatelier-logo-ohne-kachel-dunkel.svg": logo_svg(True, False),
        "schichtatelier-marke.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(True)}</svg>',
        "schichtatelier-marke-ohne-kachel.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(False)}</svg>',
        "schichtatelier-marke-einfarbig.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(False, "#1c2a24")}</svg>',
        "schichtatelier-marke-klein.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{mark(True, small=True)}</svg>',
        "schichtatelier-siegel.svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="240" height="240">{seal()}{ring_paths}</svg>',
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
    job(pad(f'<g transform="translate({-vb/2},-32)">{inner.split(">",1)[1][:-6]}</g>', 2400, 800, "#ffffff", 6), "schichtatelier-logo-2400", 2400, 800, "#ffffff")
    inner = logo_svg(True, True)
    job(pad(f'<g transform="translate({-vb/2},-32)">{inner.split(">",1)[1][:-6]}</g>', 2400, 800, NAVY, 6), "schichtatelier-logo-dunkel-2400", 2400, 800, NAVY)
    job(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="1024" height="1024">{mark(True)}</svg>', "schichtatelier-marke-1024", 1024, 1024, "")
    job(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="1024" height="1024">{seal()}{ring_paths}</svg>', "schichtatelier-siegel-1024", 1024, 1024, "")
    jf = os.path.join(tmp, "jobs.json"); json.dump(jobs, open(jf, "w"))
    subprocess.run(["node", os.path.join(ROOT, "build", "render.js"), jf], check=True)
    print("Logo-Dateien:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
