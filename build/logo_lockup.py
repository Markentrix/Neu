"""Langes Logo "Schichtatelier": Wortmarke mit Druckdüse im „i“ und Druckspur-Linie, dazu Zeilen und Signatur.
Alle Schrift wird als Pfade ausgegeben (Abril Fatface, Hanken Grotesk, Pinyon Script; alle SIL OFL).
Aufruf: python3 build/logo_lockup.py  (schreibt brand/schichtatelier-logo-voll*.svg, -wortmarke*.svg und PNGs)
"""
import os, sys, json, subprocess, tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "brand")
DISPLAY = os.path.join(ROOT, "website-fertig", "assets", "fonts", "AbrilFatface.woff2")
TEXT = os.path.join(ROOT, "website-fertig", "assets", "fonts", "HankenGrotesk.woff2")
PINYON = os.path.join(HERE, "brand-src", "PinyonScript.woff2")

# Farbwelten: main = "Schicht", acc = "atelier" und Linie, sub = "3D MANUFAKTUR", ink = Zeile, sig = Signatur
THEMES = {
    "hell": dict(main="#1f4d3a", acc="#9e6230", sub="#2f6b52", ink="#15231c", sig="#9e6230"),
    "dunkel": dict(main="#f1ede4", acc="#e2ae7c", sub="#8fc7ab", ink="#f1ede4", sig="#e2ae7c"),
    "css": dict(main="var(--logo-main)", acc="var(--logo-accent)", sub="var(--logo-sub)", ink="var(--ink)", sig="var(--logo-accent)"),
}


class Face:
    def __init__(self, path, location=None):
        self.font = TTFont(path)
        self.gs = self.font.getGlyphSet(location=location) if location and "fvar" in self.font else self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def name(self, ch):
        return self.cmap[ord(ch)]

    def bounds(self, glyph):
        bp = BoundsPen(self.gs); self.gs[glyph].draw(bp); return bp.bounds

    def run(self, glyphs, size, x, baseline, tracking=0.0):
        """Glyphen als Pfade ab x. Gibt (Pfadliste, Endposition, [x je Glyphe]) zurück."""
        sc = size / self.upm; paths = []; xs = []
        for g in glyphs:
            xs.append(x)
            pen = SVGPathPen(self.gs); self.gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, x, baseline)))
            d = pen.getCommands()
            if d: paths.append(d)
            x += self.gs[g].width * sc + tracking * size
        return paths, x - tracking * size, xs

    def width(self, glyphs, size, tracking=0.0):
        sc = size / self.upm
        return sum(self.gs[g].width * sc for g in glyphs) + tracking * size * (len(glyphs) - 1)


def build(theme="hell", full=True, E=200.0, padf=0.22, sub=True, subscale=1.0):
    """Liefert (svg_innen, viewBox) für das Logo. E = Schriftgröße der Wortmarke."""
    T = THEMES[theme]
    fr = Face(DISPLAY)
    inter = Face(TEXT, {"wght": 600}); interr = Face(TEXT, {"wght": 450}); sig = Face(PINYON)
    # Wortmarke: Schicht + atel + (i ohne Punkt) + er
    g1 = [fr.name(c) for c in "Schicht"]
    g2 = [fr.name(c) for c in "atel"] + ["dotlessi"] + [fr.name(c) for c in "er"]
    base = 0.0; track = -0.004
    p1, x1, _ = fr.run(g1, E, 0, base, track)
    p2, x2, pos2 = fr.run(g2, E, x1 + track * E, base, track)
    W = x2
    # Position und Maße der Dotless-i
    gi = "dotlessi"; ixmin, iymin, ixmax, iymax = fr.bounds(gi); sc = E / fr.upm
    xi = pos2[4]; xs = xi + (ixmin + ixmax) / 2 * sc          # Mitte des Schafts
    xh = fr.bounds(fr.name("x"))[3] * sc                       # x-Höhe
    asc = fr.bounds(fr.name("h"))[3] * sc                      # Oberlänge
    sw = 0.034 * E                                             # Strichstärke der Linie
    yl = base + 0.17 * E; r = yl - base                        # Linie unter der Schrift, Radius der Kurve
    x_start = W * 0.16
    line = f'M{x_start:.1f} {yl:.1f}H{xs - r:.1f}A{r:.1f} {r:.1f} 0 0 0 {xs:.1f} {yl - r:.1f}V{base - 0.03 * E:.1f}'
    # Düse über dem Schaft
    nw = 0.27 * E; ntop = -(asc + 0.05 * E); nh = 0.12 * E
    nozzle = (f'<rect x="{xs - nw / 2:.1f}" y="{ntop:.1f}" width="{nw:.1f}" height="{nh:.1f}" rx="{0.03 * E:.1f}" fill="{T["acc"]}"/>'
              f'<path d="M{xs - nw / 2 + 0.012 * E:.1f} {ntop + nh - 1:.1f}H{xs + nw / 2 - 0.012 * E:.1f}L{xs + 0.034 * E:.1f} {ntop + nh + 0.085 * E:.1f}H{xs - 0.034 * E:.1f}Z" fill="{T["acc"]}"/>'
              f'<circle cx="{xs:.1f}" cy="{ntop + nh + 0.085 * E + 0.052 * E:.1f}" r="{0.027 * E:.1f}" fill="{T["acc"]}"/>')
    body = "".join(f'<path d="{d}" fill="{T["main"]}"/>' for d in p1) + "".join(f'<path d="{d}" fill="{T["acc"]}"/>' for d in p2)
    body += f'<path class="spur" pathLength="100" d="{line}" fill="none" stroke="{T["acc"]}" stroke-width="{sw:.1f}"/>' + f'<g class="duese">{nozzle}</g>'
    if not sub:  # nur Wortmarke mit Düse und Linie (Seitenkopf)
        top = ntop - 0.03 * E; pad = padf * E; bottom = yl + sw / 2
        return body, (-pad, top - pad, W + 2 * pad, bottom - top + 2 * pad)
    # 3D MANUFAKTUR (zentriert unter der Wortmarke)
    s2 = 0.168 * E * subscale; tr2 = 0.62
    gs2 = [inter.name(c) if c != " " else inter.name(" ") for c in "3D MANUFAKTUR"]
    w2 = inter.width(gs2, s2, tr2); y2 = base + 0.43 * E
    pp, _, _ = inter.run(gs2, s2, (W - w2) / 2, y2, tr2)
    body += "".join(f'<path d="{d}" fill="{T["sub"]}"/>' for d in pp)
    bottom = y2 + 0.05 * E
    if full:
        s3 = 0.128 * E; tr3 = 0.07
        txt = "Deko · Geschenke · Individuelle Anfertigungen"
        gs3 = [interr.name(c) for c in txt]; w3 = interr.width(gs3, s3, tr3); y3 = base + 0.62 * E
        x3 = (W - w3) / 2 - 0.04 * W
        pp, _, _ = interr.run(gs3, s3, x3, y3, tr3)
        body += "".join(f'<path d="{d}" fill="{T["ink"]}"/>' for d in pp)
        s4 = 0.27 * E
        gs4 = [sig.name(c) for c in "Y & C"]
        w4 = sig.width(gs4, s4, 0.0)
        pp, _, _ = sig.run(gs4, s4, W - w4 - 0.02 * W, y3 + 0.01 * E, 0.0)
        body += "".join(f'<path d="{d}" fill="{T["sig"]}"/>' for d in pp)
        bottom = y3 + 0.09 * E
    top = ntop - 0.03 * E
    pad = padf * E
    vb = (-pad, top - pad, W + 2 * pad, bottom - top + 2 * pad)
    return body, vb


def svg_file(theme, full, bg=None):
    body, (x, y, w, h) = build(theme, full)
    bgr = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="Schichtatelier 3D-Manufaktur">'
            f'{bgr}{body}</svg>')


def inline_svg(full=False, cls="lockup", sub=True, subscale=1.3):
    """Theme-fähiges Inline-SVG für die Website (Farben aus CSS-Variablen)."""
    body, (x, y, w, h) = build("css", full, padf=0.02, sub=sub, subscale=subscale)
    return f'<svg class="{cls}" viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}" role="img" aria-label="Schichtatelier 3D-Manufaktur">{body}</svg>'


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {
        "schichtatelier-logo-voll.svg": svg_file("hell", True),
        "schichtatelier-logo-voll-dunkel.svg": svg_file("dunkel", True),
        "schichtatelier-wortmarke.svg": svg_file("hell", False),
        "schichtatelier-wortmarke-dunkel.svg": svg_file("dunkel", False),
    }
    for n, s in files.items():
        open(os.path.join(OUT, n), "w").write(s)
    jobs = []; tmp = tempfile.mkdtemp()
    def job(name, svg, bg, wpx=2400):
        import re
        vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
        hpx = int(round(wpx * vb[3] / vb[2]))
        svg = re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{wpx}" height="{hpx}"', svg, count=1)
        p = os.path.join(tmp, name + ".svg"); open(p, "w").write(svg)
        jobs.append({"svg": p, "png": os.path.join(OUT, name + ".png"), "w": wpx, "h": hpx})
    job("schichtatelier-logo-voll-2400", svg_file("hell", True, "#f7f4ee"), None)
    job("schichtatelier-logo-voll-dunkel-2400", svg_file("dunkel", True, "#141a17"), None)
    jf = os.path.join(tmp, "jobs.json"); json.dump(jobs, open(jf, "w"))
    subprocess.run(["node", os.path.join(HERE, "render.js"), jf], check=True)
    print("Lockup-Dateien:", sorted(f for f in os.listdir(OUT) if "voll" in f or "wortmarke" in f))


if __name__ == "__main__":
    main()
