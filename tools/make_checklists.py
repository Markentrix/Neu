#!/usr/bin/env python3
"""Erzeugt die beiden Checklisten-PDFs (Website, SEO) im Markentrix-Design aus den Quellseiten.

Quelle der Punkte: src/pages/website-checkliste.html und src/pages/seo-checkliste.html (Elemente .cl-item).
Schriften (Markenhandbuch 3.0, Archivo und Source Sans 3): static/fonts/*.woff2 (werden zur Laufzeit nach TTF umgewandelt, nur im Arbeitsspeicher-Ordner).
Logo: static/favicon.svg ohne weißen Hintergrund, gezeichnet als Vektor.
Aufruf: python3 tools/make_checklists.py   (schreibt nach static/downloads/)
"""
import html as htmlmod
import os
import re
import tempfile

from fontTools.ttLib import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'static', 'downloads')
os.makedirs(OUT, exist_ok=True)

TIEF, PFAU, KUPFER, LEINEN, KREIDE = HexColor('#0C2128'), HexColor('#045268'), HexColor('#C67432'), HexColor('#EAE2D3'), HexColor('#F7F4EE')
NAVY, CYAN, BLUE, VIOLET = TIEF, PFAU, PFAU, KUPFER
INK, MUTED, LINE, SOFT = TIEF, HexColor('#4E5C5F'), LEINEN, KREIDE

tmp = tempfile.mkdtemp()
for name, f in (('SG700', 'archivo-800'), ('SG600', 'archivo-700'), ('IN400', 'source-sans-3-400'), ('IN600', 'source-sans-3-600')):
    t = TTFont(os.path.join(ROOT, 'static', 'fonts', f + '.woff2'))
    t.flavor = None
    p = os.path.join(tmp, f + '.ttf')
    t.save(p)
    pdfmetrics.registerFont(RLFont(name, p))

W, H = A4
M = 52  # Seitenrand


def parse(page):
    s = open(os.path.join(ROOT, 'src', 'pages', page), encoding='utf-8').read()
    items = []
    for m in re.finditer(r'<label class="cl-item"><input type="checkbox"><span><b>(.*?)</b>(.*?)</span></label>', s, re.S):
        clean = lambda x: htmlmod.unescape(re.sub(r'<[^>]+>', '', x)).strip()
        items.append((clean(m.group(1)), clean(m.group(2))))
    return items


def wrap(c, text, font, size, width):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if c.stringWidth(t, font, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def _svgpath(c, d, ox=0.0, oy=0.0, sc=1.0, H=0.0):
    """Zeichnet einen absoluten SVG-Pfad (M, L, C, Z) als gefüllte Form; y wird gespiegelt."""
    toks = re.findall(r'[MLCZ]|-?\d*\.?\d+', d)
    p = c.beginPath(); i = 0; cmd = None
    f = lambda x, y: (ox + x * sc, H - (oy + y * sc))
    while i < len(toks):
        t = toks[i]
        if t in 'MLCZ':
            cmd = t; i += 1
            if t == 'Z': p.close()
            continue
        if cmd == 'M': p.moveTo(*f(float(toks[i]), float(toks[i + 1]))); i += 2; cmd = 'L'
        elif cmd == 'L': p.lineTo(*f(float(toks[i]), float(toks[i + 1]))); i += 2
        elif cmd == 'C':
            x1, y1, x2, y2, x3, y3 = [float(v) for v in toks[i:i + 6]]
            p.curveTo(*f(x1, y1), *f(x2, y2), *f(x3, y3)); i += 6
    c.drawPath(p, stroke=0, fill=1)

LOGO_SVG = open(os.path.join(ROOT, 'static', 'img', 'logo', 'markentrix-logo-farbe-hell.svg'), encoding='utf-8').read()
WORD = re.findall(r'<path d="([^"]+)"/>', LOGO_SVG)
LW, LH = 420.577, 69.126


def logo(c, x, y, w):
    """CI-Logo (Farbe auf Hell) als Vektor, linke untere Ecke (x, y), Breite w."""
    k = w / LW
    c.saveState()
    # Wortmarke: Pfade liegen in Seitenkoordinaten, der Ursprung der Gesamtmarke ist (45.023, 182.224)
    c.setFillColor(TIEF)
    for d in WORD:
        _svgpath(c, d, ox=x - 45.023 * k, oy=-182.224 * k, sc=k, H=y + LH * k)
    # Bildmarke (Einheiten 522 x 447, Maßstab 0.153973 bzw. 0.15434)
    m = 0.153973 * k
    def line(pts, col, width):
        c.setStrokeColor(col); c.setLineWidth(width * m); c.setLineCap(1); c.setLineJoin(1)
        p = c.beginPath()
        for n, (px, py) in enumerate(pts):
            X, Y = x + px * m, y + LH * k - (py * 0.15434 * k)
            p.moveTo(X, Y) if n == 0 else p.lineTo(X, Y)
        c.drawPath(p, stroke=1, fill=0)
    line([(40.998, 406.003), (40.998, 107.505), (227.49, 277.508)], TIEF, 82)
    line([(414.008, 107.505), (414.008, 406.003)], TIEF, 82)
    line([(227.49, 277.508), (414.008, 107.505)], PFAU, 82)
    line([(414.008, 107.505), (494.988, 26.996)], PFAU, 54)
    line([(414.997, 26.996), (494.988, 26.996), (494.988, 107.505)], PFAU, 54)
    c.restoreState()


def header(c, label):
    logo(c, M, H - 66, 150)
    c.setFillColor(PFAU); c.setFont('IN600', 8.5); c.drawRightString(W - M, H - 50, label.upper())
    c.setStrokeColor(LEINEN); c.setLineWidth(0.8); c.line(M, H - 78, W - M, H - 78)


def footer(c, n, total):
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, 46, W - M, 46)
    c.setFillColor(MUTED); c.setFont('IN400', 8)
    c.drawString(M, 32, 'Markentrix · Christian Wien · Celle · markentrix.de · info@markentrix.de · 0176 20370429')
    c.drawRightString(W - M, 32, 'Seite %d von %d' % (n, total))


def build(fname, label, title, intro, items, closing_head, closing_text, note):
    path = os.path.join(OUT, fname)
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle(title + ' · Markentrix'); c.setAuthor('Markentrix · Christian Wien'); c.setSubject(label)
    # Seitenaufteilung vorab berechnen
    pages = [[]]
    n_t = len(wrap(c, title, 'SG700', 30, W - 2 * M)); n_i = len(wrap(c, intro, 'IN400', 11, W - 2 * M))
    y_first = (H - 150 - 34 * n_t) - 16 * n_i - 14 - 52
    y_next = H - 120
    y = y_first
    heights = []
    for it in items:
        lines = wrap(c, it[1], 'IN400', 9.6, W - 2 * M - 48)
        heights.append(18 + 13.2 * len(lines) + 12)
    for it, hh in zip(items, heights):
        if y - hh < 64:
            pages.append([]); y = y_next
        pages[-1].append((it, hh)); y -= hh
    total = len(pages) + (0)  # Schlussteil steht auf der letzten Seite, falls Platz, sonst eigene Seite
    # Platz für Schluss: etwa 150 pt
    need_extra = (y - 152 < 64)
    if need_extra:
        total += 1
    for pi, page in enumerate(pages):
        header(c, label)
        y = H - 120
        if pi == 0:
            c.setFillColor(PFAU); c.setFont('IN600', 9); c.drawString(M, H - 112, label.upper())
            c.setFillColor(NAVY); c.setFont('SG700', 30)
            ty = H - 150
            tl = wrap(c, title, 'SG700', 30, W - 2 * M)
            for n, ln in enumerate(tl):
                c.drawString(M, ty, ln)
                if n == len(tl) - 1:      # Kupferstrich unter der letzten Zeile (Erkennungszeichen 1)
                    c.setStrokeColor(KUPFER); c.setLineWidth(4.2); c.setLineCap(0)
                    c.line(M, ty - 4, M + c.stringWidth(ln, 'SG700', 30), ty - 4)
                    c.setFillColor(NAVY)
                ty -= 34
            c.setFillColor(INK); c.setFont('IN400', 11)
            for ln in wrap(c, intro, 'IN400', 11, W - 2 * M):
                c.drawString(M, ty - 6, ln); ty -= 16
            # Auswertung
            ty -= 14
            c.setFillColor(SOFT); c.setStrokeColor(LINE); c.roundRect(M, ty - 28, W - 2 * M, 34, 4, stroke=1, fill=1)
            c.setFillColor(NAVY); c.setFont('IN600', 10)
            c.drawString(M + 14, ty - 15, 'Ihr Ergebnis:   ______ von %d Punkten erfüllt' % len(items))
            y = ty - 52
        for (head, body), hh in page:
            c.setStrokeColor(NAVY); c.setLineWidth(1.4); c.roundRect(M, y - 13, 15, 15, 2, stroke=1, fill=0)
            c.setFillColor(NAVY); c.setFont('SG600', 11.2); c.drawString(M + 28, y - 10, head)
            c.setFillColor(INK); c.setFont('IN400', 9.6)
            yy = y - 25
            for ln in wrap(c, body, 'IN400', 9.6, W - 2 * M - 48):
                c.drawString(M + 28, yy, ln); yy -= 13.2
            c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(M + 28, y - hh + 8, W - M, y - hh + 8)
            y -= hh
        last = (pi == len(pages) - 1)
        if last and not need_extra:
            closing(c, y, closing_head, closing_text, note)
        footer(c, pi + 1, total)
        c.showPage()
    if need_extra:
        header(c, label)
        closing(c, H - 130, closing_head, closing_text, note)
        footer(c, total, total)
        c.showPage()
    c.save()
    return path


def closing(c, y, head, text, note):
    y -= 12
    c.setFillColor(KREIDE); c.setStrokeColor(LEINEN); c.roundRect(M, y - 136, W - 2 * M, 140, 8, stroke=1, fill=1)
    c.setFillColor(NAVY); c.setFont('SG700', 14); c.drawString(M + 18, y - 24, head)
    c.setFillColor(INK); c.setFont('IN400', 10)
    yy = y - 44
    for ln in wrap(c, text, 'IN400', 10, W - 2 * M - 36):
        c.drawString(M + 18, yy, ln); yy -= 14
    c.setFillColor(MUTED); c.setFont('IN400', 8.2)
    yy -= 6
    for ln in wrap(c, note, 'IN400', 8.2, W - 2 * M - 36):
        c.drawString(M + 18, yy, ln); yy -= 11


web = parse('website-checkliste.html')
seo = parse('seo-checkliste.html')
assert len(web) == 12 and len(seo) == 15, (len(web), len(seo))
NOTE = 'Die Punkte sind Grundlagen zum Selbstprüfen, keine Messwerte und keine Garantie für Anfragen oder Platzierungen. Stand: November 2026.'
p1 = build('Markentrix-Website-Checkliste.pdf', 'Checkliste · 10 Minuten', 'Bringt Ihre Website Anfragen? Zwölf Punkte zum Selbstprüfen.',
           'Öffnen Sie Ihre Website auf dem Handy, wie Ihre Kunden es abends tun, und gehen Sie die Punkte durch. Jeder Haken steht für etwas, das Besucher vor Ort erwarten. Jeder fehlende Haken ist ein Grund, warum Anfragen ausbleiben.',
           web, 'Weniger als neun Haken?', 'Dann lohnt sich ein Blick auf Struktur und Anfrageweg. Wenn Sie möchten, sehen wir gemeinsam in einem kostenlosen Erstgespräch von rund 30 Minuten auf Ihre Seite, ehrlich und ohne Verkaufsdruck. Termin buchen unter markentrix.de/kontakt oder telefonisch unter 0176 20370429.', NOTE)
p2 = build('Markentrix-SEO-Checkliste.pdf', 'SEO-Checkliste · lokal', 'SEO-Checkliste für kleine Websites: 15 Punkte zum Selbstprüfen.',
           'Gehen Sie die Punkte in Ruhe durch, am besten mit Ihrer Website auf dem Bildschirm. Jeder Haken ist eine Grundlage dafür, dass Kunden Sie bei Google und in KI-Antworten überhaupt finden können.',
           seo, 'Viele Lücken gefunden?', 'Das ist normal und meist gut zu beheben. Wenn Sie möchten, besprechen wir im kostenlosen Erstgespräch von rund 30 Minuten, was für Ihren Betrieb zuerst sinnvoll ist. Termin buchen unter markentrix.de/kontakt oder telefonisch unter 0176 20370429.', NOTE)
print(p1, os.path.getsize(p1) // 1024, 'KB')
print(p2, os.path.getsize(p2) // 1024, 'KB')
