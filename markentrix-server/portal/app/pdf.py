"""PDF-Erzeugung (reportlab). Gemeinsame Bausteine für Monatsbericht, Angebot, Rechnung und Provisionsabrechnung."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: F401

import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Markentrix-CI 2026 v3: Source Sans 3 (Text), Archivo (Überschriften), Tiefsee, Pfauenblau, Leinen, Kupfer nur als kleiner Akzent
_FD = os.path.join(os.path.dirname(__file__), "fonts")
try:
    pdfmetrics.registerFont(TTFont("MX-Text", os.path.join(_FD, "SourceSans3-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("MX-Fett", os.path.join(_FD, "SourceSans3-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("MX-Titel", os.path.join(_FD, "Archivo-ExtraBold.ttf")))
    pdfmetrics.registerFont(TTFont("MX-Titel2", os.path.join(_FD, "Archivo-Bold.ttf")))
    F_TEXT, F_FETT, F_TITEL, F_TITEL2 = "MX-Text", "MX-Fett", "MX-Titel", "MX-Titel2"
except Exception:  # Schriftdateien fehlen: Standardschrift statt Absturz
    F_TEXT, F_FETT, F_TITEL, F_TITEL2 = "Helvetica", "Helvetica-Bold", "Helvetica-Bold", "Helvetica-Bold"

NAVY = colors.HexColor("#0C2128")      # Tiefsee
AKZENT = colors.HexColor("#045268")    # Pfauenblau
KUPFER = colors.HexColor("#C67432")
GRAU = colors.HexColor("#4E5C5F")      # Nebentext
HELL = colors.HexColor("#F7F4EE")      # Kreide (Tabellenstreifen)
LEINEN = colors.HexColor("#EAE2D3")
NEBEL = colors.HexColor("#E1F0F6")
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

_ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_ss["Heading1"], fontName=F_TITEL, fontSize=21, leading=25, textColor=NAVY, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontName=F_TITEL2, fontSize=12.5, leading=16, textColor=AKZENT, spaceBefore=14, spaceAfter=6, keepWithNext=1)
TXT = ParagraphStyle("txt", parent=_ss["BodyText"], fontName=F_TEXT, fontSize=9.5, leading=14, textColor=NAVY)
KLEIN = ParagraphStyle("klein", parent=TXT, fontSize=8.5, leading=11, textColor=GRAU)
RECHTS = ParagraphStyle("rechts", parent=TXT, alignment=TA_RIGHT)
RECHTS_FETT = ParagraphStyle("rechts_fett", parent=RECHTS, fontName=F_FETT)


def esc(t) -> str:
    return str(t if t is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")


def p(text, stil=TXT):
    return Paragraph(esc(text), stil)


def euro(cent) -> str:
    v = int(cent or 0)
    s = f"{abs(v) / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s + " €"


def datum(d) -> str:
    return d.strftime("%d.%m.%Y") if d else ""


def monat_name(d) -> str:
    return f"{MONATE[d.month - 1]} {d.year}"


def tabelle(kopf: list, zeilen: list, breiten=None, rechts_ab=None, summe: list | None = None):
    daten = [[p(c, ParagraphStyle("th", parent=TXT, fontName=F_FETT, textColor=colors.white, fontSize=9)) for c in kopf]]
    for z in zeilen:
        daten.append([c if hasattr(c, "wrap") else p(c) for c in z])
    if summe:
        daten.append([c if hasattr(c, "wrap") else p(c, ParagraphStyle("sum", parent=TXT, fontName=F_FETT)) for c in summe])
    t = Table(daten, colWidths=breiten, repeatRows=1)
    stil = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1 if not summe else -2), [colors.white, HELL]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, LEINEN), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if summe:
        stil += [("LINEABOVE", (0, -1), (-1, -1), 0.8, NAVY)]
    if rechts_ab is not None:
        stil.append(("ALIGN", (rechts_ab, 0), (-1, -1), "RIGHT"))
    t.setStyle(TableStyle(stil))
    return t


def kacheln(paare: list, spalten=4):
    """Kennzahlen als Raster: [(Beschriftung, Wert), ...]"""
    zellen = []
    for b, w in paare:
        zellen.append([Paragraph(f'<font size="17"><b>{esc(w)}</b></font>', TXT), Paragraph(esc(b), KLEIN)])
    reihen = [zellen[i:i + spalten] for i in range(0, len(zellen), spalten)]
    daten = []
    for r in reihen:
        r = r + [[""] for _ in range(spalten - len(r))]
        daten.append([[c[0], c[1]] if len(c) == 2 else "" for c in r])
    t = Table(daten, colWidths=[(170 * mm) / spalten] * spalten)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HELL), ("BOX", (0, 0), (-1, -1), 0.5, colors.white), ("INNERGRID", (0, 0), (-1, -1), 3, colors.white),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    return t


def kaestchen(angekreuzt: bool, einzug: float = 0):
    """Kleines Ankreuzfeld für Vertragsanlagen."""
    from reportlab.graphics.shapes import Drawing, PolyLine, Rect
    d = Drawing((4.6 + einzug) * mm, 4.6 * mm)
    x0 = einzug * mm
    d.add(Rect(x0 + 0.3 * mm, 0.3 * mm, 4 * mm, 4 * mm, fillColor=colors.white, strokeColor=NAVY, strokeWidth=0.8))
    if angekreuzt:
        d.add(PolyLine([x0 + 0.9 * mm, 2.4 * mm, x0 + 2 * mm, 1.2 * mm, x0 + 3.8 * mm, 3.8 * mm], strokeColor=NAVY, strokeWidth=1.3, strokeLineCap=1, strokeLineJoin=1))
    return d


def leistungsbox(titel: str, punkte: list):
    """„Das bekommen Sie“: getönte Karte mit Häkchen vor jedem Punkt; Zeilen mit „## “ sind Zwischenüberschriften."""
    from reportlab.graphics.shapes import Circle, Drawing, PolyLine
    def haken():
        d = Drawing(5 * mm, 5 * mm)
        d.add(Circle(2.5 * mm, 2.5 * mm, 2.3 * mm, fillColor=AKZENT, strokeColor=None))
        d.add(PolyLine([1.5 * mm, 2.6 * mm, 2.3 * mm, 1.7 * mm, 3.7 * mm, 3.6 * mm], strokeColor=colors.white, strokeWidth=1.2, strokeLineCap=1, strokeLineJoin=1))
        return d
    sub = ParagraphStyle("lsub", parent=TXT, fontName=F_FETT, textColor=AKZENT, spaceBefore=4)
    zeilen = [[p(titel, H2), ""]]
    for x in punkte:
        x = str(x)
        zeilen.append([p(x[3:].strip(), sub), ""] if x.startswith("## ") else [haken(), p(x)])
    t = Table(zeilen, colWidths=[8 * mm, 162 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NEBEL), ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#bcd9e4")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("LEFTPADDING", (0, 0), (0, -1), 8), ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, -1), (-1, -1), 9)]
                          + [("SPAN", (0, i), (1, i)) for i, z in enumerate(zeilen) if z[1] == ""]))
    return t


def _logo_zeichnen(c, x, y, hoehe) -> bool:
    """Zeichnet das Markentrix-Logo (helle Variante für dunklen Grund) aus static/brand unverändert, nur proportional skaliert."""
    try:
        import re
        import xml.etree.ElementTree as ET
        pfad = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "brand", "markentrix-logo-farbe-dunkel.svg")
        wurzel = ET.parse(pfad).getroot()
        _, _, vw, vh = [float(v) for v in wurzel.get("viewBox").split()]
        k = hoehe / vh
        ns = "{http://www.w3.org/2000/svg}"
        c.saveState()
        c.translate(x, y); c.scale(k, k)          # SVG-Ursprung oben links, y nach unten
        c.translate(0, vh); c.scale(1, -1)
        for g in wurzel.iter(ns + "g"):
            tr = g.get("transform"); fill = g.get("fill")
            c.saveState()
            if tr:
                m = re.match(r"translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+) ([-\d.]+)\)", tr)
                if m:
                    c.translate(float(m.group(1)), float(m.group(2))); c.scale(float(m.group(3)), float(m.group(4)))
            for pa in g.findall(ns + "path"):
                pt = c.beginPath(); _svg_pfad(pt, pa.get("d"), pa.get("transform"))
                if fill and fill != "none":
                    c.setFillColor(colors.HexColor(fill)); c.drawPath(pt, stroke=0, fill=1, fillMode=1)
                else:
                    c.setStrokeColor(colors.HexColor(pa.get("stroke"))); c.setLineWidth(float(pa.get("stroke-width"))); c.setLineCap(1); c.setLineJoin(1)
                    c.drawPath(pt, stroke=1, fill=0)
            c.restoreState()
        c.restoreState()
        return True
    except Exception:
        return False


def _svg_pfad(pt, d, transform=None):
    import re
    dx = 0.0
    if transform:
        m = re.match(r"translate\(([-\d.]+)\)", transform)
        dx = float(m.group(1)) if m else 0.0
    zeichen = re.findall(r"([MmLlHhVvQqCcZz])|(-?\d*\.?\d+(?:e-?\d+)?)", d)
    i, cmd, x, y, sx, sy = 0, None, 0.0, 0.0, 0.0, 0.0
    toks = [(a, b) for a, b in zeichen]
    def num():
        nonlocal i
        v = float(toks[i][1]); i += 1
        return v
    while i < len(toks):
        if toks[i][0]:
            cmd = toks[i][0]; i += 1
            if cmd in "Zz":
                pt.close(); x, y = sx, sy
                continue
        rel = cmd.islower(); C = cmd.upper()
        if C == "M":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            pt.moveTo(x + dx, y); sx, sy = x, y; cmd = "l" if rel else "L"
        elif C == "L":
            nx, ny = num(), num(); x, y = (x + nx, y + ny) if rel else (nx, ny); pt.lineTo(x + dx, y)
        elif C == "H":
            nx = num(); x = x + nx if rel else nx; pt.lineTo(x + dx, y)
        elif C == "V":
            ny = num(); y = y + ny if rel else ny; pt.lineTo(x + dx, y)
        elif C == "Q":
            cx, cy, nx, ny = num(), num(), num(), num()
            if rel:
                cx, cy, nx, ny = x + cx, y + cy, x + nx, y + ny
            pt.curveTo(x + 2 / 3 * (cx - x) + dx, y + 2 / 3 * (cy - y), nx + 2 / 3 * (cx - nx) + dx, ny + 2 / 3 * (cy - ny), nx + dx, ny); x, y = nx, ny
        elif C == "C":
            a1, b1, a2, b2, nx, ny = num(), num(), num(), num(), num(), num()
            if rel:
                a1, b1, a2, b2, nx, ny = x + a1, y + b1, x + a2, y + b2, x + nx, y + ny
            pt.curveTo(a1 + dx, b1, a2 + dx, b2, nx + dx, ny); x, y = nx, ny
        else:
            break


def dokument(titel: str, kopfzeile: str, inhalt: list, firma: dict, fuss_extra: str = "") -> bytes:
    puffer = BytesIO()
    name = firma.get("name") or "Markentrix"
    fuss = " · ".join(x for x in [name, firma.get("strasse"), f"{firma.get('plz', '')} {firma.get('ort', '')}".strip(), firma.get("email"), firma.get("telefon")] if x)

    def seite(c, doc):
        c.saveState()
        c.setFillColor(NAVY); c.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, stroke=0, fill=1)
        c.setFillColor(KUPFER); c.rect(0, A4[1] - 14.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)   # kleiner Kupfer-Akzent unter dem Kopf
        if not _logo_zeichnen(c, 20 * mm, A4[1] - 10.6 * mm, 7.2 * mm):
            c.setFillColor(colors.white); c.setFont(F_TITEL, 12); c.drawString(20 * mm, A4[1] - 9 * mm, name)
        c.setFont(F_TEXT, 8.5); c.setFillColor(LEINEN); c.drawRightString(A4[0] - 20 * mm, A4[1] - 8.7 * mm, kopfzeile)
        c.setFillColor(GRAU); c.setFont(F_TEXT, 7.5)
        c.drawString(20 * mm, 12 * mm, fuss[:120]); c.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Seite {doc.page}")
        if fuss_extra:
            c.drawString(20 * mm, 8 * mm, fuss_extra[:140])
        c.restoreState()

    doc = SimpleDocTemplate(puffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=26 * mm, bottomMargin=20 * mm, title=titel, author=name)
    doc.build(inhalt, onFirstPage=seite, onLaterPages=seite)
    return puffer.getvalue()



# von anderen Modulen als pdf.PageBreak usw. benutzt
_REEXPORT = (KeepTogether, PageBreak, Spacer)
