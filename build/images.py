"""Erzeugt die Produktbilder (SVG -> WebP 800x600) sowie Favicon-Dateien.
Aufruf: python3 build/images.py   (braucht node + playwright, Pillow)"""
import os, sys, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from produkte import PRODUKTE, FARBEN

ROOT = os.path.join(os.path.dirname(__file__), "..", "website-fertig")
OUT = os.path.join(ROOT, "assets", "img", "produkte")
W, H = 800, 600
# Startseiten-Foto: Quelle in build/fotos/, Zuschnitt in Pixeln des (gedrehten) Originals, quadratisch
HERO = dict(quelle="kuerbis-mini", crop=(540, 420, 2340, 2220))


def shade(hexc, f):
    hexc = hexc.lstrip("#"); r, g, b = int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)
    r, g, b = [max(0, min(255, int(c * f))) for c in (r, g, b)]
    return "#%02x%02x%02x" % (r, g, b)


def layers(x, y, w, h, color, step=7, rx=0):
    """Schichtlinien-Textur über eine Fläche."""
    out = []
    yy = y + step
    while yy < y + h:
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-opacity=".18" stroke-width="1.2"/>' % (x, yy, x + w, yy, shade(color, .55)))
        yy += step
    return "".join(out)


def frame(inner, bg="#ece7dd"):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
            '<defs><radialGradient id="g" cx="50%%" cy="40%%" r="70%%"><stop offset="0" stop-color="#fcfaf5"/><stop offset="1" stop-color="%s"/></radialGradient>'
            '<filter id="sh" x="-20%%" y="-20%%" width="140%%" height="160%%"><feGaussianBlur stdDeviation="14"/></filter></defs>'
            '<rect width="%d" height="%d" fill="url(#g)"/>'
            '<ellipse cx="400" cy="470" rx="230" ry="34" fill="#000" opacity=".16" filter="url(#sh)"/>'
            '%s</svg>') % (W, H, W, H, bg, W, H, inner)


def box(x, y, w, h, d, c, rx=10):
    """Isometrische Box: Front, Seite, Deckel."""
    top = shade(c, 1.18); side = shade(c, .78)
    return ('<path d="M%d %d h%d l%d -%d h-%d z" fill="%s"/>' % (x, y, w, d, d, w, top) +
            '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"/>' % (x, y, w, h, rx, c) +
            '<path d="M%d %d l%d -%d v%d l-%d %d z" fill="%s"/>' % (x + w, y, d, d, h, d, d, side) +
            layers(x, y, w, h, c))


def cyl(cx, y, r, h, c, ry=None):
    ry = ry or int(r * .32)
    return ('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (cx - r, y, 2 * r, h, c) +
            layers(cx - r, y, 2 * r, h, c) +
            '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="%s"/>' % (cx, y + h, r, ry, shade(c, .8)) +
            '<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (cx - r, y + h - ry, 2 * r, ry, c) +
            '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="%s"/>' % (cx, y, r, ry, shade(c, 1.2)))


def leaf(cx, cy, rot, col="#3e9c6b", s=1.0):
    return '<path transform="translate(%d %d) rotate(%d) scale(%s)" d="M0 0 C -40 -60 -20 -120 0 -130 C 20 -120 40 -60 0 0 Z" fill="%s"/><path transform="translate(%d %d) rotate(%d) scale(%s)" d="M0 0 L0 -120" stroke="%s" stroke-width="3" fill="none"/>' % (cx, cy, rot, s, col, cx, cy, rot, s, shade(col, .7))


def draw(p):
    c = FARBEN[p["farben"][0]][1]
    if c.lower() in ("#f4f2ec",):
        c = "#e9e5db"
    pid = p["id"]
    a = "#b8763f"  # Akzent (Kupfer)
    if pid == "pflanztopf-terra":
        pot = ('<path d="M250 250 L300 460 H500 L550 250 Z" fill="%s"/>' % c +
               '<path d="M400 250 L400 460" stroke="%s" stroke-width="2" opacity=".5"/>' % shade(c, .8) +
               '<path d="M250 250 L300 460 L400 460 L400 250Z" fill="%s" opacity=".35"/>' % shade(c, .85) +
               layers(250, 250, 300, 210, c, 9) +
               '<ellipse cx="400" cy="250" rx="150" ry="36" fill="%s"/>' % shade(c, 1.15) +
               '<ellipse cx="400" cy="250" rx="120" ry="24" fill="#5b4636"/>' +
               leaf(400, 250, -20) + leaf(400, 250, 20) + leaf(400, 255, 0, "#4bb07a", 1.1))
        return pot
    if pid == "kraeutertopf-selbstbewaessernd":
        return (cyl(400, 300, 130, 150, c) + '<rect x="270" y="380" width="260" height="14" fill="%s" opacity=".6"/>' % shade(c, .7) +
                '<rect x="285" y="400" width="80" height="50" rx="6" fill="#8fd3ff" opacity=".8"/>' +
                '<ellipse cx="400" cy="300" rx="110" ry="30" fill="#5b4636"/>' +
                leaf(380, 290, -30, "#3e9c6b", .9) + leaf(420, 290, 25, "#55b07b", .9) + leaf(400, 292, -5, "#4bb07a", 1.0) +
                '<circle cx="520" cy="330" r="10" fill="%s"/>' % shade(c, .6))
    if pid == "handyhalter-lean":
        return ('<path d="M260 450 L340 450 L470 230 L430 215 Z" fill="%s"/>' % shade(c, .9) + box(240, 420, 230, 40, 40, c) +
                '<rect x="330" y="150" width="150" height="270" rx="16" transform="rotate(14 405 285)" fill="#1b1e24"/>' +
                '<rect x="342" y="165" width="126" height="240" rx="8" transform="rotate(14 405 285)" fill="#4a90e2"/>')
    if pid == "kopfhoererstaender-arc":
        return ('<path d="M340 460 Q400 420 460 460" fill="none" stroke="%s" stroke-width="18"/>' % c + box(330, 450, 140, 26, 26, c) +
                '<path d="M400 450 V210" stroke="%s" stroke-width="26" stroke-linecap="round"/>' % c +
                '<path d="M330 215 Q400 170 470 215" fill="none" stroke="%s" stroke-width="34" stroke-linecap="round"/>' % c +
                '<path d="M300 240 Q400 150 500 240" fill="none" stroke="#2b2e34" stroke-width="22" stroke-linecap="round"/>' +
                '<rect x="268" y="230" width="52" height="86" rx="20" fill="#2b2e34"/><rect x="480" y="230" width="52" height="86" rx="20" fill="#2b2e34"/>')
    if pid == "kabelclips-6er":
        s = ""
        for i, (x, y) in enumerate([(230, 250), (370, 240), (510, 250), (260, 400), (400, 390), (540, 400)]):
            s += '<path d="M%d %d h60 v60 h-60 z" fill="%s" rx="8"/>' % (x, y, c) + '<rect x="%d" y="%d" width="60" height="60" rx="10" fill="%s"/>' % (x, y, c) + layers(x, y, 60, 60, c, 6)
            s += '<circle cx="%d" cy="%d" r="12" fill="#efeadf"/>' % (x + 30, y + 24) + '<rect x="%d" y="%d" width="10" height="24" fill="#efeadf"/>' % (x + 25, y + 24)
            s += '<path d="M%d %d c 40 -60 120 20 160 -30" stroke="#2b2e34" stroke-width="5" fill="none"/>' % (x - 80, y + 24)
        return s
    if pid == "organizer-grid":
        return (box(200, 300, 400, 150, 60, c) + '<rect x="200" y="300" width="400" height="150" fill="%s" opacity=".0"/>' % c +
                '<rect x="215" y="312" width="110" height="126" rx="6" fill="%s"/>' % shade(c, .72) + '<rect x="335" y="312" width="110" height="126" rx="6" fill="%s"/>' % shade(c, .72) +
                '<rect x="455" y="312" width="130" height="60" rx="6" fill="%s"/>' % shade(c, .72) + '<rect x="455" y="380" width="130" height="58" rx="6" fill="%s"/>' % shade(c, .72) +
                '<rect x="240" y="180" width="12" height="150" rx="4" fill="#b8763f"/><rect x="262" y="200" width="12" height="130" rx="4" fill="#2f4d8a"/><rect x="284" y="190" width="12" height="140" rx="4" fill="#1f9e8a"/>' +
                '<rect x="350" y="240" width="80" height="100" rx="4" fill="#fff6c2"/><rect x="470" y="330" width="90" height="30" rx="6" fill="#2b2e34"/>')
    if pid == "untersetzer-hex-4er":
        s = ""
        for i, (x, y, r) in enumerate([(300, 330, 0), (480, 330, 0), (390, 420, 0), (390, 240, 0)]):
            s += '<polygon points="%s" fill="%s" stroke="%s" stroke-width="3"/>' % (" ".join("%d,%d" % (x + 85 * [1, .5, -.5, -1, -.5, .5][k], y + 74 * [0, 1, 1, 0, -1, -1][k]) for k in range(6)), c, shade(c, .8))
            for dx in (-40, 0, 40):
                for dy in (-30, 30):
                    s += '<polygon points="%s" fill="%s"/>' % (" ".join("%d,%d" % (x + dx + 16 * [1, .5, -.5, -1, -.5, .5][k], y + dy + 14 * [0, 1, 1, 0, -1, -1][k]) for k in range(6)), "#efeadf")
            s += '<polygon points="%s" fill="%s"/>' % (" ".join("%d,%d" % (x + 16 * [1, .5, -.5, -1, -.5, .5][k], y + 14 * [0, 1, 1, 0, -1, -1][k]) for k in range(6)), "#efeadf")
        return s
    if pid == "vase-spiral":
        s = '<path d="M330 460 C300 400 290 330 330 280 C360 240 350 190 370 150 H430 C450 190 440 240 470 280 C510 330 500 400 470 460 Z" fill="%s"/>' % c
        for i in range(18):
            y = 160 + i * 17
            s += '<path d="M%d %d q 60 10 120 0" stroke="%s" stroke-opacity=".35" stroke-width="2" fill="none"/>' % (340 - (i % 3) * 6, y, shade(c, .55))
        s += '<path d="M400 150 C 380 80 420 60 450 20" stroke="#b7995c" stroke-width="4" fill="none"/><circle cx="452" cy="22" r="16" fill="#e2c37d"/><path d="M400 150 C 410 90 360 70 330 40" stroke="#b7995c" stroke-width="4" fill="none"/><circle cx="330" cy="40" r="13" fill="#d9a9a0"/>'
        return s
    if pid == "lithophan-lampe":
        return (box(250, 400, 300, 50, 40, "#1b1e24") + '<rect x="270" y="150" width="260" height="250" rx="12" fill="#fff8e6"/>' +
                '<rect x="270" y="150" width="260" height="250" rx="12" fill="url(#g2)"/>' +
                '<defs><radialGradient id="g2" cx="50%" cy="55%" r="55%"><stop offset="0" stop-color="#ffd27a" stop-opacity=".9"/><stop offset="1" stop-color="#fff8e6" stop-opacity="0"/></radialGradient></defs>' +
                '<circle cx="400" cy="250" r="48" fill="#f1c7a6" opacity=".9"/><path d="M330 400 C 340 320 460 320 470 400 Z" fill="#c9a386" opacity=".85"/>' +
                '<path d="M300 150 L270 110 M500 150 L530 110 M400 150 V100" stroke="#ffd27a" stroke-width="6" stroke-linecap="round" opacity=".7"/>')
    if pid == "flexi-drache":
        s = ""
        pts = [(220, 400), (265, 370), (310, 345), (355, 330), (400, 325), (445, 335), (490, 355), (530, 380), (565, 410)]
        for i, (x, y) in enumerate(pts):
            r = 18 + (8 if 3 <= i <= 6 else 0)
            s += '<circle cx="%d" cy="%d" r="%d" fill="%s"/>' % (x, y, r, c if i % 2 else shade(c, .85))
            s += '<path d="M%d %d l-8 -26 l16 0z" fill="%s"/>' % (x, y - r + 6, shade(c, .7))
        s += '<path d="M565 410 c 20 -40 60 -40 70 -10 c -30 10 -40 30 -70 10" fill="%s"/>' % c  # Kopf
        s += '<circle cx="605" cy="395" r="5" fill="#111"/><path d="M620 400 l 30 10" stroke="%s" stroke-width="6"/>' % shade(c, .6)
        s += '<path d="M330 340 l -20 -80 l 60 50 z" fill="%s" opacity=".9"/><path d="M450 342 l -5 -85 l 55 60 z" fill="%s" opacity=".9"/>' % (shade(c, 1.15), shade(c, 1.15))
        return s
    if pid == "wuerfelturm-keep":
        s = box(300, 200, 150, 240, 50, c)
        for i in range(5):
            s += '<rect x="%d" y="170" width="24" height="32" fill="%s"/>' % (300 + i * 32, c)
        s += '<rect x="330" y="240" width="40" height="60" rx="20" fill="%s"/><rect x="400" y="240" width="40" height="60" rx="20" fill="%s"/>' % (shade(c, .5), shade(c, .5))
        s += box(240, 420, 320, 40, 60, shade(c, .9))
        for (x, y, col) in [(290, 395, "#b8763f"), (360, 400, "#f4f2ec"), (420, 392, "#2f4d8a")]:
            s += '<rect x="%d" y="%d" width="40" height="40" rx="8" fill="%s" transform="rotate(12 %d %d)"/>' % (x, y, col, x + 20, y + 20)
            s += '<circle cx="%d" cy="%d" r="4" fill="#111"/><circle cx="%d" cy="%d" r="4" fill="#111"/><circle cx="%d" cy="%d" r="4" fill="#111"/>' % (x + 10, y + 10, x + 20, y + 20, x + 30, y + 30)
        return s
    if pid == "schluesselanhaenger-wunschtext":
        return ('<circle cx="250" cy="300" r="46" fill="none" stroke="#9aa0a6" stroke-width="10"/>' +
                '<rect x="300" y="250" width="300" height="100" rx="26" fill="%s" transform="rotate(-8 450 300)"/>' % c +
                '<text x="450" y="312" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="700" font-size="48" fill="%s" transform="rotate(-8 450 300)">LENA</text>' % a +
                '<circle cx="320" cy="300" r="12" fill="#efeadf" transform="rotate(-8 450 300)"/>')
    if pid == "wandhaken-fold-3er":
        s = '<rect x="140" y="120" width="520" height="340" rx="10" fill="#e4dccf"/>'
        for x in (250, 400, 550):
            s += '<path d="M%d 200 v110 q0 30 30 30 h10" fill="none" stroke="%s" stroke-width="22" stroke-linecap="round"/>' % (x, c)
            s += '<rect x="%d" y="170" width="44" height="44" rx="10" fill="%s"/>' % (x - 22, shade(c, 1.15))
        s += '<path d="M560 340 c 40 20 60 70 50 110 h-70 c -10 -40 0 -90 20 -110z" fill="#2f4d8a"/>'
        return s
    if pid == "kochbuchstaender":
        return ('<path d="M250 450 L300 220 L560 220 L510 450 Z" fill="%s"/>' % c + layers(260, 225, 290, 220, c, 9) +
                '<path d="M235 450 H525 L540 470 H250 Z" fill="%s"/>' % shade(c, .8) + '<rect x="310" y="240" width="200" height="190" rx="8" fill="#fff" transform="skewX(-12)"/>' +
                '<rect x="325" y="260" width="140" height="10" fill="#d8d2c4" transform="skewX(-12)"/><rect x="325" y="280" width="170" height="10" fill="#d8d2c4" transform="skewX(-12)"/><rect x="325" y="300" width="120" height="10" fill="#d8d2c4" transform="skewX(-12)"/>' +
                '<rect x="330" y="330" width="130" height="80" rx="6" fill="#b8763f" opacity=".8" transform="skewX(-12)"/>')
    if pid == "zahnbuerstenhalter-wave":
        s = '<path d="M250 460 V330 q 75 -40 150 0 t 150 0 V460 Z" fill="%s"/>' % c + layers(250, 330, 300, 130, c, 8)
        for i, x in enumerate((300, 370, 440, 510)):
            s += '<rect x="%d" y="180" width="16" height="170" rx="8" fill="%s"/><rect x="%d" y="170" width="20" height="36" rx="6" fill="%s"/>' % (x - 8, ["#f4f2ec", "#2f4d8a", "#1f9e8a", "#b8763f"][i], x - 10, "#fff")
        return s
    if pid == "controllerhalter":
        s = box(240, 420, 320, 36, 50, c) + '<rect x="290" y="250" width="30" height="180" rx="8" fill="%s"/><rect x="480" y="250" width="30" height="180" rx="8" fill="%s"/>' % (c, c)
        for x in (320, 410):
            s += '<path d="M%d 320 q 10 -40 50 -40 h 50 q 40 0 50 40 l 10 60 q 0 25 -25 25 l -40 -40 h -40 l -40 40 q -25 0 -25 -25 z" fill="#2b2e34"/>' % x
            s += '<circle cx="%d" cy="320" r="10" fill="#555"/><circle cx="%d" cy="320" r="10" fill="#555"/>' % (x + 35, x + 115)
        s += '<rect x="560" y="300" width="40" height="80" rx="12" fill="%s"/>' % shade(c, .8)
        return s
    if pid == "schubladenbox-kleinteile":
        s = box(220, 220, 360, 230, 60, c)
        for r in range(3):
            for col in range(2):
                x = 235 + col * 175; y = 235 + r * 72
                s += '<rect x="%d" y="%d" width="160" height="60" rx="6" fill="%s"/>' % (x, y, shade(c, .82))
                s += '<rect x="%d" y="%d" width="50" height="10" rx="5" fill="%s"/>' % (x + 55, y + 25, shade(c, .5))
                s += '<rect x="%d" y="%d" width="60" height="14" rx="3" fill="#fff" opacity=".85"/>' % (x + 8, y + 6)
        s += '<rect x="235" y="307" width="160" height="60" rx="6" fill="%s" transform="translate(20 0)"/>' % shade(c, .9)
        s += '<circle cx="320" cy="337" r="6" fill="#9aa0a6"/><circle cx="345" cy="332" r="5" fill="#9aa0a6"/><circle cx="365" cy="340" r="6" fill="#9aa0a6"/>'
        return s
    if pid == "stiftehalter-honeycomb":
        s = cyl(400, 250, 110, 200, c)
        for yy in range(270, 440, 34):
            for xx in range(300, 510, 36):
                off = 18 if (yy // 34) % 2 else 0
                s += '<polygon points="%s" fill="%s"/>' % (" ".join("%d,%d" % (xx + off + 13 * [1, .5, -.5, -1, -.5, .5][k], yy + 12 * [0, 1, 1, 0, -1, -1][k]) for k in range(6)), "#efeadf")
        for i, (x, col) in enumerate([(340, "#b8763f"), (380, "#2f4d8a"), (420, "#1f9e8a"), (460, "#f2c94c")]):
            s += '<rect x="%d" y="%d" width="14" height="160" rx="4" fill="%s" transform="rotate(%d %d 250)"/>' % (x, 110, col, (i - 1.5) * 6, x + 7)
        return s
    if pid == "kapselspender":
        s = '<rect x="140" y="120" width="520" height="340" rx="10" fill="#e4dccf"/>'
        for i in range(4):
            x = 260 + i * 70
            s += '<rect x="%d" y="160" width="56" height="260" rx="8" fill="%s"/>' % (x, c) + layers(x, 160, 56, 260, c, 8)
            for j in range(5):
                s += '<ellipse cx="%d" cy="%d" rx="20" ry="9" fill="%s"/>' % (x + 28, 190 + j * 44, ["#c9a24c", "#7a3e8c", "#2f7fbf", "#3e9c6b"][i])
        return s
    if pid == "namensschild-wunschtext":
        return ('<rect x="200" y="230" width="400" height="150" rx="18" fill="%s"/>' % c + layers(200, 230, 400, 150, c, 9) +
                '<rect x="214" y="244" width="372" height="122" rx="12" fill="none" stroke="%s" stroke-width="4"/>' % a +
                '<text x="400" y="298" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="700" font-size="40" fill="%s">Familie Berger</text>' % a +
                '<text x="400" y="340" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="600" font-size="22" fill="%s">Bitte klingeln</text>' % a +
                '<circle cx="228" cy="258" r="5" fill="#9aa0a6"/><circle cx="572" cy="258" r="5" fill="#9aa0a6"/><circle cx="228" cy="352" r="5" fill="#9aa0a6"/><circle cx="572" cy="352" r="5" fill="#9aa0a6"/>')
    return box(300, 250, 200, 180, 60, c)


import sys as _sys; _sys.path.insert(0, os.path.dirname(__file__))
from logo import mark as _mark
LOGO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">' + _mark(True, uid="fav", small=True) + '</svg>'


def compose_cutout(obj, out_path, W=1200, H=900, anordnung=None):
    """Freigestelltes Objekt mittig auf den hellen Shop-Hintergrund setzen, mit weichem Schatten."""
    from PIL import Image, ImageFilter, ImageDraw
    obj = obj.crop(obj.getbbox())
    small = Image.new("RGB", (60, 45)); px = small.load()
    for y in range(45):
        for x in range(60):
            d = ((x - 30) / 30) ** 2 + ((y - 18) / 22) ** 2
            f = min(1.0, d ** 0.5)
            c1, c2 = (252, 250, 245), (236, 231, 221)
            px[x, y] = tuple(int(c1[k] + (c2[k] - c1[k]) * f) for k in range(3))
    bg = small.resize((W, H), Image.BICUBIC).convert("RGBA")
    base_scale = min((W * 0.62) / obj.width, (H * 0.74) / obj.height)
    items = anordnung or [(0.5, 0.84, 1.0)]
    # hintere (kleinere, höher stehende) zuerst zeichnen
    for cx, by, f in sorted(items, key=lambda a: a[1]):
        sc = base_scale * f
        o = obj.resize((int(obj.width * sc), int(obj.height * sc)), Image.LANCZOS)
        x = int(W * cx - o.width / 2); y = int(H * by) - o.height
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse((x + o.width * 0.08, y + o.height - 28 * f, x + o.width * 0.92, y + o.height + 36 * f), fill=(30, 25, 15, 95))
        shadow = shadow.filter(ImageFilter.GaussianBlur(22 * f))
        bg.alpha_composite(shadow); bg.alpha_composite(o, (x, y))
    bg.convert("RGB").save(out_path, "WEBP", quality=86, method=6)


def main():
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp()
    jobs = []
    for p in PRODUKTE:
        if p.get("entwurf"):
            stale = os.path.join(OUT, p["id"] + ".webp")
            if os.path.exists(stale): os.remove(stale)
            continue
        if p.get("foto"):
            src = os.path.join(os.path.dirname(__file__), "fotos", p["id"] + ".jpg")
            from PIL import ImageOps
            cut = os.path.join(os.path.dirname(__file__), "fotos", p["id"] + "-cut.png")
            if p.get("freistellen") and not os.path.exists(cut):
                # einmalig freistellen (rembg), Ergebnis wird als -cut.png gespeichert
                from rembg import remove, new_session
                base = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
                if p.get("crop"): base = base.crop(p["crop"])
                remove(base, session=new_session("isnet-general-use"), alpha_matting=True,
                       alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=15,
                       alpha_matting_erode_size=8).save(cut)
            if p.get("anordnung"):
                srccut = os.path.join(os.path.dirname(__file__), "fotos", p.get("foto_quelle", p["id"]) + "-cut.png")
                compose_cutout(Image.open(srccut).convert("RGBA"), os.path.join(OUT, p["id"] + ".webp"), anordnung=p["anordnung"])
                continue
            if os.path.exists(cut):
                compose_cutout(Image.open(cut).convert("RGBA"), os.path.join(OUT, p["id"] + ".webp"))
                continue
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            if p.get("crop"):
                im = im.crop(p["crop"])
            w, h = im.size
            if w / h > 4 / 3:
                nw = int(h * 4 / 3); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else:
                nh = int(w * 3 / 4); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
            im = im.resize((1200, 900), Image.LANCZOS)
            im.save(os.path.join(OUT, p["id"] + ".webp"), "WEBP", quality=84, method=6)
            continue
        svg = frame(draw(p))
        path = os.path.join(tmp, p["id"] + ".svg")
        with open(path, "w") as f:
            f.write(svg)
        jobs.append({"svg": path, "png": os.path.join(tmp, p["id"] + ".png"), "w": W, "h": H})
    # Hero-Foto der Startseite (echtes Werkstattfoto, quadratisch)
    hero_src = os.path.join(os.path.dirname(__file__), "fotos", HERO["quelle"] + ".jpg")
    if os.path.exists(hero_src):
        from PIL import ImageOps
        h = ImageOps.exif_transpose(Image.open(hero_src)).convert("RGB").crop(HERO["crop"])
        h = h.resize((1200, 1200), Image.LANCZOS)
        h.save(os.path.join(ROOT, "assets", "img", "hero.webp"), "WEBP", quality=82, method=6)
    # Gutschein-Karte
    gs = frame('<rect x="190" y="170" width="420" height="270" rx="18" fill="#1f4d3a"/>'
               '<rect x="190" y="170" width="420" height="270" rx="18" fill="none" stroke="#f1e6d2" stroke-opacity=".35" stroke-width="2" stroke-dasharray="6 6" transform="translate(10 10) scale(.952)"/>'
               '<g transform="translate(214 194) scale(1.0)">' + _mark(False, uid="gs") + '</g>'
               '<text x="300" y="235" font-family="Inter,Arial,sans-serif" font-weight="700" font-size="22" fill="#f1ede4">Schicht<tspan fill="#d9a06b">atelier</tspan></text>'
               '<text x="220" y="330" font-family="Inter,Arial,sans-serif" font-weight="600" font-size="16" fill="#f1ede4" fill-opacity=".8" letter-spacing="3">GESCHENKGUTSCHEIN</text>'
               '<text x="220" y="395" font-family="Inter,Arial,sans-serif" font-weight="700" font-size="54" fill="#f1ede4">20 €</text>'
               '<text x="560" y="412" text-anchor="end" font-family="Inter,Arial,sans-serif" font-size="14" fill="#f1ede4" fill-opacity=".7">3 Jahre gültig</text>')
    gp = os.path.join(tmp, "gutschein.svg"); open(gp, "w").write(gs)
    jobs.append({"svg": gp, "png": os.path.join(tmp, "gutschein.png"), "w": W, "h": H})
    # Favicon
    fav = os.path.join(tmp, "favicon.svg")
    with open(fav, "w") as f:
        f.write(LOGO_SVG.replace('width="64" height="64"', 'width="512" height="512"', 1))
    jobs.append({"svg": fav, "png": os.path.join(tmp, "favicon.png"), "w": 512, "h": 512})
    jobfile = os.path.join(tmp, "jobs.json")
    with open(jobfile, "w") as f:
        json.dump(jobs, f)
    render = os.path.join(os.path.dirname(__file__), "render.js")
    subprocess.run(["node", render, jobfile], check=True)
    for j in jobs[:-1]:
        im = Image.open(j["png"]).convert("RGB")
        name = os.path.basename(j["png"]).replace(".png", ".webp")
        im.save(os.path.join(OUT, name), "WEBP", quality=82, method=6)
    im = Image.open(jobs[-1]["png"]).convert("RGBA")
    im.resize((180, 180), Image.LANCZOS).save(os.path.join(ROOT, "apple-touch-icon.png"))
    im.resize((192, 192), Image.LANCZOS).save(os.path.join(ROOT, "icon-192.png"))
    im.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "icon-512.png"))
    im.save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    print("Bilder erzeugt:", len([p for p in PRODUKTE if not p.get("entwurf")]), "+ Gutschein")


if __name__ == "__main__":
    main()
