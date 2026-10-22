"""Quittung (Zahlungsbestätigung) über eine erhaltene Anzahlung, ausgestellt im Namen des Kunden-Betriebs.
Das ist keine Rechnung mit Umsatzsteuerausweis; ob der Betrieb steuerlich eine Anzahlungsrechnung braucht, klärt seine Steuerberatung."""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer

from . import pdf


def quittung_pdf(betrieb: dict, gast: str, termin: str, leistung: str, betrag: float, erhalten, ref: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm, bottomMargin=20 * mm, title="Quittung " + ref)
    adr = ", ".join(x for x in [betrieb.get("strasse"), " ".join(y for y in [betrieb.get("plz"), betrieb.get("ort")] if y)] if x)
    teile = [pdf.p(betrieb.get("firma") or "", pdf.H1), pdf.p(adr, pdf.KLEIN), Spacer(1, 10 * mm),
             pdf.p("Quittung über eine Anzahlung", pdf.H2), Spacer(1, 3 * mm),
             pdf.p(f"Erhalten von: {gast}"),
             pdf.p(f"Betrag: {pdf.euro(round(betrag * 100))}"),
             pdf.p(f"Zahlungseingang: {pdf.datum(erhalten)}"),
             pdf.p("Für: " + (leistung + ", " if leistung else "") + f"Termin am {termin}"),
             pdf.p(f"Vorgang: {ref}"), Spacer(1, 8 * mm),
             pdf.p("Wir bestätigen den Erhalt der oben genannten Anzahlung. Sie wird auf den Preis der Leistung angerechnet.", pdf.TXT), Spacer(1, 4 * mm),
             pdf.p("Dies ist eine Zahlungsbestätigung und keine Rechnung mit Umsatzsteuerausweis.", pdf.KLEIN)]
    doc.build(teile)
    return buf.getvalue()
