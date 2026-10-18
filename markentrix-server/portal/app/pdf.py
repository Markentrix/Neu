"""PDF-Erzeugung (reportlab). Gemeinsame Bausteine für Monatsbericht, Angebot, Rechnung und Provisionsabrechnung."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AKZENT = colors.HexColor("#4F46E5")
GRAU = colors.HexColor("#6B7280")
HELL = colors.HexColor("#F3F4F6")
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

_ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_ss["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#111827"), spaceAfter=4)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=AKZENT, spaceBefore=14, spaceAfter=6)
TXT = ParagraphStyle("txt", parent=_ss["BodyText"], fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#111827"))
KLEIN = ParagraphStyle("klein", parent=TXT, fontSize=8.5, leading=11, textColor=GRAU)
RECHTS = ParagraphStyle("rechts", parent=TXT, alignment=TA_RIGHT)
RECHTS_FETT = ParagraphStyle("rechts_fett", parent=RECHTS, fontName="Helvetica-Bold")


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
    daten = [[p(c, ParagraphStyle("th", parent=TXT, fontName="Helvetica-Bold", textColor=colors.white, fontSize=9)) for c in kopf]]
    for z in zeilen:
        daten.append([c if hasattr(c, "wrap") else p(c) for c in z])
    if summe:
        daten.append([c if hasattr(c, "wrap") else p(c, ParagraphStyle("sum", parent=TXT, fontName="Helvetica-Bold")) for c in summe])
    t = Table(daten, colWidths=breiten, repeatRows=1)
    stil = [("BACKGROUND", (0, 0), (-1, 0), AKZENT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1 if not summe else -2), [colors.white, HELL]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if summe:
        stil += [("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#111827"))]
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


def dokument(titel: str, kopfzeile: str, inhalt: list, firma: dict, fuss_extra: str = "") -> bytes:
    puffer = BytesIO()
    name = firma.get("name") or "Markentrix"
    fuss = " · ".join(x for x in [name, firma.get("strasse"), f"{firma.get('plz', '')} {firma.get('ort', '')}".strip(), firma.get("email"), firma.get("telefon")] if x)

    def seite(c, doc):
        c.saveState()
        c.setFillColor(AKZENT); c.rect(0, A4[1] - 12 * mm, A4[0], 12 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10); c.drawString(20 * mm, A4[1] - 8 * mm, name)
        c.setFont("Helvetica", 9); c.drawRightString(A4[0] - 20 * mm, A4[1] - 8 * mm, kopfzeile)
        c.setFillColor(GRAU); c.setFont("Helvetica", 7.5)
        c.drawString(20 * mm, 12 * mm, fuss[:120]); c.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Seite {doc.page}")
        if fuss_extra:
            c.drawString(20 * mm, 8 * mm, fuss_extra[:140])
        c.restoreState()

    doc = SimpleDocTemplate(puffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=22 * mm, bottomMargin=20 * mm, title=titel, author=name)
    doc.build(inhalt, onFirstPage=seite, onLaterPages=seite)
    return puffer.getvalue()


# bequemer Zugriff aus anderen Modulen
from reportlab.platypus import Spacer  # noqa: E402,F401
