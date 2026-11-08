#!/usr/bin/env python3
"""Erzeugt die beiden Checklisten-PDFs (Website, SEO) im Markentrix-Design aus den Quellseiten.

Quelle der Punkte: src/pages/website-checkliste.html und src/pages/seo-checkliste.html (Elemente .cl-item).
Schriften: static/fonts/*.woff2 (werden zur Laufzeit nach TTF umgewandelt, nur im Arbeitsspeicher-Ordner).
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

NAVY, CYAN, BLUE, VIOLET = HexColor('#0B1020'), HexColor('#28C7F7'), HexColor('#1E9BFF'), HexColor('#8B5CF6')
INK, MUTED, LINE, SOFT = HexColor('#2C3446'), HexColor('#5B6478'), HexColor('#DDE3EE'), HexColor('#F4F6FA')

tmp = tempfile.mkdtemp()
for name, f in (('SG700', 'space-grotesk-700'), ('SG600', 'space-grotesk-600'), ('IN400', 'inter-400'), ('IN600', 'inter-600')):
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


def logo(c, x, y, s):
    """Wortbildmarke: M mit Pfeil (vereinfachte Vektorform nach favicon.svg), Verlauf Cyan zu Violett in zwei Teilen."""
    k = s / 48.0
    def pt(px, py): return (x + px * k, y + (48 - py) * k)
    c.setLineWidth(5.6 * k); c.setLineCap(1); c.setLineJoin(1)
    c.setStrokeColor(CYAN)
    p = c.beginPath(); p.moveTo(*pt(11, 38)); p.lineTo(*pt(11, 13.5)); p.lineTo(*pt(23.5, 26.5)); c.drawPath(p, stroke=1, fill=0)
    c.setStrokeColor(BLUE)
    p = c.beginPath(); p.moveTo(*pt(23.5, 26.5)); p.lineTo(*pt(31, 18.5)); c.drawPath(p, stroke=1, fill=0)
    c.setStrokeColor(VIOLET)
    p = c.beginPath(); p.moveTo(*pt(31, 38)); p.lineTo(*pt(31, 18.5)); c.drawPath(p, stroke=1, fill=0)
    c.setLineWidth(5 * k)
    p = c.beginPath(); p.moveTo(*pt(31, 18.5)); p.lineTo(*pt(37, 12.5)); p.moveTo(*pt(37, 12.5)); p.lineTo(*pt(30.5, 12.5)); p.moveTo(*pt(37, 12.5)); p.lineTo(*pt(37, 19)); c.drawPath(p, stroke=1, fill=0)


def header(c, label):
    c.setFillColor(NAVY); c.rect(0, H - 74, W, 74, stroke=0, fill=1)
    c.setFillColor(CYAN); c.rect(0, H - 78, W / 2, 4, stroke=0, fill=1)
    c.setFillColor(VIOLET); c.rect(W / 2, H - 78, W / 2, 4, stroke=0, fill=1)
    logo(c, M, H - 58, 34)
    c.setFillColor(white); c.setFont('SG700', 17); c.drawString(M + 44, H - 46, 'markentrix')
    c.setFillColor(CYAN); c.setFont('IN600', 8.5); c.drawRightString(W - M, H - 44, label.upper())


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
            c.setFillColor(HexColor('#6D3FD1')); c.setFont('IN600', 9); c.drawString(M, H - 112, label.upper())
            c.setFillColor(NAVY); c.setFont('SG700', 30)
            ty = H - 150
            for ln in wrap(c, title, 'SG700', 30, W - 2 * M):
                c.drawString(M, ty, ln); ty -= 34
            c.setFillColor(INK); c.setFont('IN400', 11)
            for ln in wrap(c, intro, 'IN400', 11, W - 2 * M):
                c.drawString(M, ty - 6, ln); ty -= 16
            # Auswertung
            ty -= 14
            c.setFillColor(SOFT); c.setStrokeColor(LINE); c.roundRect(M, ty - 28, W - 2 * M, 34, 8, stroke=1, fill=1)
            c.setFillColor(NAVY); c.setFont('IN600', 10)
            c.drawString(M + 14, ty - 15, 'Ihr Ergebnis:   ______ von %d Punkten erfüllt' % len(items))
            y = ty - 52
        for (head, body), hh in page:
            c.setStrokeColor(NAVY); c.setLineWidth(1.4); c.roundRect(M, y - 13, 15, 15, 3, stroke=1, fill=0)
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
    c.setFillColor(HexColor('#F1EBFF')); c.setStrokeColor(HexColor('#DCD0F7')); c.roundRect(M, y - 136, W - 2 * M, 140, 12, stroke=1, fill=1)
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
