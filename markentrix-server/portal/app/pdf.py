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

# Markentrix-CI: Inter (Text), Space Grotesk (Überschriften), Navy, Verlauf Cyan -> Violett
_FD = os.path.join(os.path.dirname(__file__), "fonts")
try:
    pdfmetrics.registerFont(TTFont("MX-Text", os.path.join(_FD, "Inter-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("MX-Fett", os.path.join(_FD, "Inter-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("MX-Titel", os.path.join(_FD, "SpaceGrotesk-Bold.ttf")))
    F_TEXT, F_FETT, F_TITEL = "MX-Text", "MX-Fett", "MX-Titel"
except Exception:  # Schriftdateien fehlen: Standardschrift statt Absturz
    F_TEXT, F_FETT, F_TITEL = "Helvetica", "Helvetica-Bold", "Helvetica-Bold"

NAVY = colors.HexColor("#0B1020")
CYAN = colors.HexColor("#28C7F7")
VIOLETT = colors.HexColor("#8B5CF6")
AKZENT = colors.HexColor("#6D3FE0")   # Violett, auf Weiß lesbar
GRAU = colors.HexColor("#6B7390")
HELL = colors.HexColor("#EEF1FA")
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

_ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_ss["Heading1"], fontName=F_TITEL, fontSize=21, leading=25, textColor=NAVY, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontName=F_TITEL, fontSize=12.5, leading=16, textColor=AKZENT, spaceBefore=14, spaceAfter=6, keepWithNext=1)
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
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E6E9F3")), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
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
        d.add(Circle(2.5 * mm, 2.5 * mm, 2.3 * mm, fillColor=colors.HexColor("#DCEBFF"), strokeColor=None))
        d.add(PolyLine([1.5 * mm, 2.6 * mm, 2.3 * mm, 1.7 * mm, 3.7 * mm, 3.6 * mm], strokeColor=AKZENT, strokeWidth=1.2, strokeLineCap=1, strokeLineJoin=1))
        return d
    sub = ParagraphStyle("lsub", parent=TXT, fontName=F_FETT, textColor=AKZENT, spaceBefore=4)
    zeilen = [[p(titel, H2), ""]]
    for x in punkte:
        x = str(x)
        zeilen.append([p(x[3:].strip(), sub), ""] if x.startswith("## ") else [haken(), p(x)])
    t = Table(zeilen, colWidths=[8 * mm, 162 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F1FF")), ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E4DCFF")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("LEFTPADDING", (0, 0), (0, -1), 8), ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, -1), (-1, -1), 9)]
                          + [("SPAN", (0, i), (1, i)) for i, z in enumerate(zeilen) if z[1] == ""]))
    return t


def dokument(titel: str, kopfzeile: str, inhalt: list, firma: dict, fuss_extra: str = "") -> bytes:
    puffer = BytesIO()
    name = firma.get("name") or "Markentrix"
    fuss = " · ".join(x for x in [name, firma.get("strasse"), f"{firma.get('plz', '')} {firma.get('ort', '')}".strip(), firma.get("email"), firma.get("telefon")] if x)

    def seite(c, doc):
        c.saveState()
        c.setFillColor(NAVY); c.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, stroke=0, fill=1)
        c.saveState(); pf = c.beginPath(); pf.rect(0, A4[1] - 15.2 * mm, A4[0], 1.2 * mm); c.clipPath(pf, stroke=0, fill=0)
        c.linearGradient(0, 0, A4[0], 0, (CYAN, VIOLETT)); c.restoreState()  # Verlaufslinie unter dem Kopf
        c.setFillColor(colors.white); c.setFont(F_TITEL, 12); c.drawString(20 * mm, A4[1] - 9 * mm, name)
        c.setFont(F_TEXT, 8.5); c.setFillColor(colors.HexColor("#C9CFE6")); c.drawRightString(A4[0] - 20 * mm, A4[1] - 8.7 * mm, kopfzeile)
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
