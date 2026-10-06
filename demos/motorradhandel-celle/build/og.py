"""Erzeugt Open-Graph-/Social-Bilder (1200x630) aus Fahrzeugfotos. Aufruf aus build.py."""
import os, io
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

def _ttf(woff2):
    f = TTFont(woff2); f.flavor = None; b = io.BytesIO(); f.save(b); b.seek(0); return b

def make_all(bikes, eur, kmf):
    os.makedirs('assets/og', exist_ok=True)
    head = _ttf('assets/fonts/barlow-condensed-700-sub.woff2').getvalue(); body = _ttf('assets/fonts/inter-sub-wght.woff2').getvalue()
    F = lambda data, size: ImageFont.truetype(io.BytesIO(data), size)
    W, H = 1200, 630
    def base():
        im = Image.new('RGB', (W, H), (15, 15, 16)); d = ImageDraw.Draw(im)
        d.polygon([(760, 0), (960, 0), (700, 630), (500, 630)], fill=(200, 16, 46))
        d.polygon([(990, 0), (1040, 0), (780, 630), (730, 630)], fill=(150, 40, 40))
        return im, d
    def brand(d):
        d.polygon([(60, 56), (92, 56), (74, 92), (42, 92)], fill=(200, 16, 46))
        d.text((112, 52), 'MOTORRADHANDEL', font=F(head, 44), fill='white'); d.text((114, 98), 'CELLE · ALTENHAGEN', font=F(body, 20), fill=(185, 185, 180))
    # Standard
    im, d = base(); brand(d)
    d.text((60, 190), 'MOTORRAD KAUFEN', font=F(head, 110), fill='white'); d.text((60, 300), 'IN CELLE.', font=F(head, 110), fill=(255, 74, 61))
    d.text((60, 450), 'Gebrauchte Motorräder · Probefahrt · Ankauf · Winterlager', font=F(body, 30), fill=(215, 215, 210))
    d.text((60, 540), 'Lachtehäuserstraße 6 · 29223 Celle · 01520 888 0000', font=F(body, 26), fill=(185, 185, 180))
    im.save('assets/og/default.jpg', quality=88, optimize=True)
    # Winterlager
    im = Image.new('RGB', (W, H), (14, 28, 40)); d = ImageDraw.Draw(im)
    d.polygon([(760, 0), (960, 0), (700, 630), (500, 630)], fill=(28, 74, 104)); brand(d)
    d.text((60, 190), 'MOTORRAD', font=F(head, 110), fill='white'); d.text((60, 300), 'ÜBERWINTERN.', font=F(head, 110), fill=(143, 211, 255))
    d.text((60, 450), 'Winterlager in Celle · Winterplatz anfragen', font=F(body, 30), fill=(214, 230, 242))
    d.text((60, 540), 'Lachtehäuserstraße 6 · 29223 Celle · 01520 888 0000', font=F(body, 26), fill=(160, 190, 210))
    im.save('assets/og/winterlager.jpg', quality=88, optimize=True)
    # je Fahrzeug
    for b in bikes:
        im, d = base(); brand(d)
        ph = Image.open('assets/img/' + b['img'][0]).convert('RGB'); s = 560 / ph.width; ph = ph.resize((560, round(ph.height * s)), Image.LANCZOS)
        im.paste(ph, (600, 140)); d.rectangle((600, 140, 1160, 140 + ph.height), outline=(255, 255, 255), width=3)
        d.text((60, 170), b['brand'].upper(), font=F(head, 56), fill=(255, 74, 61))
        name = b['model'].upper(); fs = 100 if len(name) < 14 else 72
        d.text((60, 235), name, font=F(head, fs), fill='white')
        d.text((60, 370), f"EZ {b['ez']} · {kmf(b['km'])}", font=F(body, 32), fill=(215, 215, 210))
        d.text((60, 430), eur(b['price']) + ' VB', font=F(head, 96), fill='white')
        d.text((60, 560), 'Probefahrt nach Terminabsprache · 01520 888 0000', font=F(body, 24), fill=(185, 185, 180))
        im.save(f"assets/og/{b['slug']}.jpg", quality=86, optimize=True)
