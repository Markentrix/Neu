"""Angebote und Rechnungen: Berechnung, Nummernvergabe, PDF, Texte.
Eine ausgestellte Rechnung wird nie geändert; Korrekturen laufen über eine Storno-Rechnung."""
import logging
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import segno
from fastapi import HTTPException
from reportlab.platypus import Flowable, KeepTogether

from . import pdf, rechtstexte, zugferd

KLEIN_HINWEIS = "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."


def runden(x) -> int:
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def positionen_pruefen(pos) -> list:
    if not isinstance(pos, list) or len(pos) > 60:
        raise HTTPException(400, "Bitte höchstens 60 Positionen angeben.")
    out = []
    for p in pos:
        try:
            text = str(p.get("text", "")).strip()[:500]
            menge = Decimal(str(p.get("menge", 1)))
            preis = int(p.get("preis_cent", 0))
        except Exception:
            raise HTTPException(400, "Eine Position ist ungültig.")
        if not text:
            raise HTTPException(400, "Jede Position braucht eine Beschreibung.")
        if menge <= 0 or menge > 100000 or abs(preis) > 100_000_000:
            raise HTTPException(400, "Menge oder Preis einer Position ist ungültig.")
        out.append({"text": text, "menge": float(menge), "einheit": str(p.get("einheit", ""))[:20], "preis_cent": preis})
    return out


def summen(positionen: list, ust_satz, kleinunternehmer: bool) -> dict:
    netto = sum(runden(Decimal(str(p["menge"])) * p["preis_cent"]) for p in positionen)
    satz = Decimal(0) if kleinunternehmer else Decimal(str(ust_satz))
    ust = runden(Decimal(netto) * satz / 100)
    return {"netto_cent": netto, "ust_satz": satz, "ust_cent": ust, "brutto_cent": netto + ust}


def naechste_nummer(cur, art: str, prefix: str) -> str:
    jahr = date.today().year
    cur.execute("""INSERT INTO nummernkreise (art, jahr, zaehler) VALUES (%s,%s,1)
                   ON CONFLICT (art, jahr) DO UPDATE SET zaehler = nummernkreise.zaehler + 1 RETURNING zaehler""", (art, jahr))
    return f"{prefix}-{jahr}-{cur.fetchone()['zaehler']:04d}"


def empfaenger_von(cur, kid) -> dict:
    cur.execute("SELECT kundennummer, firma, ansprechpartner, strasse, plz, ort, email FROM kunden WHERE id=%s", (kid,))
    return cur.fetchone()


def firmendaten_pruefen(f: dict):
    fehlt = []
    if not (f["name"] and f["strasse"] and f["plz"] and f["ort"]):
        fehlt.append("Firmenname und Anschrift")
    if not (f["steuernummer"] or f["ustid"]):
        fehlt.append("Steuernummer oder USt-IdNr.")
    if fehlt:
        raise HTTPException(400, "Bitte zuerst unter Einstellungen → Firmendaten eintragen: " + ", ".join(fehlt) + ".")


def _epc_text(f: dict, beleg: dict):
    """Inhalt des GiroCodes (EPC-QR, Version 002, UTF-8) für die Banking-App."""
    iban = "".join((f.get("iban") or "").split()).upper()
    if not iban or beleg["brutto_cent"] <= 0:
        return None
    return "\n".join(["BCD", "002", "1", "SCT", "".join((f.get("bic") or "").split()).upper(), (f.get("name") or "")[:70], iban,
                      f"EUR{beleg['brutto_cent'] / 100:.2f}", "", "", f"Rechnung {beleg['nummer']}"[:140]])


class GiroCode(Flowable):
    """GiroCode als Vektorgrafik mit Ruhezone (4 Module): bleibt in jedem PDF-Programm scharf und scannt zuverlässig."""

    def __init__(self, inhalt: str, groesse):
        super().__init__()
        self.matrix = [list(z) for z in segno.make(inhalt, error="m", micro=False).matrix]
        self.groesse = groesse
        self.width = self.height = groesse

    def draw(self):
        n = len(self.matrix)
        k = self.groesse / (n + 8)
        c = self.canv
        c.setFillColor(pdf.colors.white); c.rect(0, 0, self.groesse, self.groesse, stroke=0, fill=1)
        c.setFillColor(pdf.colors.black)
        for y, zeile in enumerate(self.matrix):
            x = 0
            while x < n:
                if zeile[x]:
                    start = x
                    while x < n and zeile[x]:
                        x += 1
                    c.rect((4 + start) * k, self.groesse - (5 + y) * k, (x - start) * k + 0.02, k + 0.02, stroke=0, fill=1)
                else:
                    x += 1


def _lade(cur, bid, f: dict | None, empfaenger: dict | None):
    cur.execute("SELECT * FROM belege WHERE id=%s", (bid,))
    b = cur.fetchone()
    if not b:
        raise LookupError("Beleg nicht gefunden")
    f = f or rechtstexte.firma(cur)
    emp = empfaenger if (empfaenger and not b["empfaenger"]) else (b["empfaenger"] or (empfaenger_von(cur, b["kunden_id"]) if b["kunden_id"] else {}))
    storno_nr = storno_datum = None
    if b["storno_von"] is not None:
        cur.execute("SELECT nummer, datum FROM belege WHERE id=%s", (b["storno_von"],))
        r = cur.fetchone()
        storno_nr, storno_datum = r and r["nummer"], r and r["datum"]
    return b, f, emp, storno_nr, storno_datum


def e_rechnung_xml(cur, bid, f: dict | None = None) -> tuple[bytes | None, list[str]]:
    """ZUGFeRD-/Factur-X-XML einer ausgestellten Rechnung; ohne XML steht in der Liste, was fehlt."""
    b, f, emp, storno_nr, storno_datum = _lade(cur, bid, f, None)
    if b["art"] != "rechnung":
        return None, ["Nur Rechnungen sind E-Rechnungen."]
    fehlt = zugferd.pruefen(b, f, emp or {})
    if fehlt:
        return None, fehlt
    return zugferd.xml_erzeugen(b, f, emp, storno_nr, storno_datum), []


def beleg_pdf(cur, bid, f: dict | None = None, empfaenger: dict | None = None, e_rechnung: bool = True) -> tuple[bytes, str]:
    b, f, emp, storno_nr, storno_datum = _lade(cur, bid, f, empfaenger)
    ist_re = b["art"] == "rechnung"
    if ist_re and b["status"] == "entwurf" and not b["faellig_am"]:   # Entwurf: Zahlungsfrist schon in der Vorschau zeigen (festgeschrieben wird sie erst beim Ausstellen)
        tage = f.get("zahlungsziel_tage") if b["zahlungsziel_tage"] is None else b["zahlungsziel_tage"]
        if tage is not None:
            b = dict(b); b["zahlungsziel_tage"] = tage; b["faellig_am"] = (b["datum"] or date.today()) + timedelta(days=int(tage))
    storno = b["storno_von"] is not None
    titel = ("Stornorechnung" if storno else "Rechnung") if ist_re else "Angebot"
    nr = b["nummer"] or "Entwurf"
    inhalt = []
    absender = " · ".join(x for x in [f["name"] + (" · " + f["inhaber"] if f.get("inhaber") else ""), f["strasse"], f"{f['plz']} {f['ort']}".strip()] if x)
    inhalt += [pdf.p(titel.upper() + (f" ZU {storno_nr}" if storno_nr else ""), pdf.H1), pdf.p(absender, pdf.KLEIN), pdf.Spacer(1, 14)]
    adr = "\n".join(x for x in [emp.get("firma"), emp.get("ansprechpartner"), emp.get("strasse"), f"{emp.get('plz') or ''} {emp.get('ort') or ''}".strip()] if x)
    info = ([["Kundennummer", emp["kundennummer"]]] if emp.get("kundennummer") else []) + [[f"{titel}snummer" if ist_re else "Angebotsnummer", nr], [f"{titel}sdatum" if ist_re else "Angebotsdatum", pdf.datum(b["datum"] or date.today())]]
    if b["leistungszeitraum"]:
        info.append(["Leistungsdatum / -zeitraum", b["leistungszeitraum"]])
    sofort = ist_re and b.get("zahlungsziel_tage") == 0
    if ist_re and b["faellig_am"]:
        info.append(["Zahlbar", "sofort, ohne Abzug"] if sofort else ["Zahlbar bis", pdf.datum(b["faellig_am"])])
    if not ist_re and b["faellig_am"]:
        info.append(["Gültig bis", pdf.datum(b["faellig_am"])])
    if ist_re and b.get("kaeufer_referenz"):
        info.append(["Ihre Referenz / Leitweg-ID", b["kaeufer_referenz"]])
    if f.get("steuernummer"):
        info.append(["Steuernummer", f["steuernummer"]])
    if f.get("ustid"):
        info.append(["USt-IdNr.", f["ustid"]])
    from reportlab.platypus import Table, TableStyle
    label = pdf.ParagraphStyle("lab", parent=pdf.KLEIN, fontName=pdf.F_FETT, fontSize=7.5, leading=10, textColor=pdf.AKZENT, spaceBefore=6)
    wert = pdf.ParagraphStyle("wert", parent=pdf.TXT, leading=12)
    rechts = []
    for k, v in info:
        rechts += [pdf.Paragraph(pdf.esc(k), label), pdf.p(v, wert)]
    kopf = Table([[[pdf.Paragraph(("RECHNUNGSEMPFÄNGER" if ist_re else "ANGEBOTSEMPFÄNGER"), label), pdf.p(adr)], rechts]], colWidths=[102 * pdf.mm, 68 * pdf.mm])
    kopf.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    inhalt += [kopf, pdf.Spacer(1, 16), pdf.p(b["betreff"] or ("Abrechnung der vereinbarten Leistungen" if ist_re else "Unser Angebot"), pdf.H2)]
    if b["einleitung"]:
        inhalt += [pdf.p(b["einleitung"]), pdf.Spacer(1, 8)]
    zeilen = []
    for i, p in enumerate(b["positionen"], 1):
        gesamt = runden(Decimal(str(p["menge"])) * p["preis_cent"])
        menge = (f"{p['menge']:g}".replace(".", ",")) + (" " + p["einheit"] if p.get("einheit") else "")
        zeilen.append([str(i), pdf.p(p["text"]), menge, pdf.euro(p["preis_cent"]), pdf.euro(gesamt)])
    inhalt += [pdf.tabelle(["Pos.", "Leistung / Leistungsumfang", "Menge", "Einzelpreis netto", "Gesamt netto"], zeilen, breiten=[12 * pdf.mm, 78 * pdf.mm, 24 * pdf.mm, 28 * pdf.mm, 28 * pdf.mm], rechts_ab=2)]
    summen_zeilen = [["Nettobetrag", pdf.euro(b["netto_cent"])]]
    if not b["kleinunternehmer"]:
        summen_zeilen.append([f"Umsatzsteuer {float(b['ust_satz']):g} %".replace(".", ","), pdf.euro(b["ust_cent"])])
    summen_zeilen.append((("Rechnungsbetrag (brutto)" if ist_re else "Gesamtbetrag (brutto)") if not b["kleinunternehmer"] else "Gesamtbetrag (ohne USt)", pdf.euro(b["brutto_cent"])))
    t = Table([[pdf.p(a, pdf.RECHTS_FETT if i == len(summen_zeilen) - 1 else pdf.RECHTS), pdf.p(c, pdf.RECHTS_FETT if i == len(summen_zeilen) - 1 else pdf.RECHTS)] for i, (a, c) in enumerate(summen_zeilen)], colWidths=[130 * pdf.mm, 40 * pdf.mm], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, -1), (-1, -1), pdf.LEINEN), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    inhalt += [pdf.Spacer(1, 6), t]
    if b["kleinunternehmer"]:
        inhalt += [pdf.Spacer(1, 6), pdf.p(KLEIN_HINWEIS, pdf.KLEIN)]
    if b.get("leistungen") and not ist_re:
        inhalt += [pdf.Spacer(1, 14), pdf.leistungsbox("Das bekommen Sie", b["leistungen"])]
    if ist_re and not storno:
        epc = _epc_text(f, b)
        zahl = [("Zahlbar sofort, ohne Abzug" if b.get("zahlungsziel_tage") == 0 else "Zahlbar bis: " + pdf.datum(b["faellig_am"])) + " · Verwendungszweck: " + nr if b["faellig_am"] else "Verwendungszweck: " + nr,
                "Bitte überweisen Sie den Rechnungsbetrag auf die unten angegebene Bankverbindung." if f.get("iban") else "Bitte überweisen Sie den Rechnungsbetrag unter Angabe der Rechnungsnummer."] + (["Den GiroCode rechts scannen Sie in der Banking-App Ihrer Bank (nicht mit der Kamera)."] if epc else [])
        qr = GiroCode(epc, 26 * pdf.mm) if epc else ""
        zt = Table([[pdf.p("\n".join(zahl)), qr]], colWidths=[130 * pdf.mm, 40 * pdf.mm])
        zt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
        inhalt += [pdf.Spacer(1, 12), KeepTogether([pdf.p("Zahlungsinformationen", pdf.H2), zt])]
    if storno:
        inhalt += [pdf.Spacer(1, 8), pdf.p("Diese Stornorechnung hebt die genannte Rechnung auf.", pdf.KLEIN)]
    if b["schluss"]:
        inhalt += [pdf.Spacer(1, 10), pdf.p(b["schluss"])]
    if not ist_re and (f.get("angebotsbedingungen") or "").strip():
        inhalt += [pdf.Spacer(1, 10), pdf.p("Bedingungen", pdf.H2), pdf.p(f["angebotsbedingungen"].strip(), pdf.KLEIN)]
    if not ist_re:
        inhalt += [pdf.Spacer(1, 10), pdf.p("Zur Annahme öffnen Sie bitte den Link in unserer E-Mail oder antworten Sie uns kurz per E-Mail." if (b.get("lead_id") and not b["kunden_id"]) else "Zur Annahme dieses Angebots bestätigen Sie es bitte im Kundenportal oder per E-Mail.", pdf.KLEIN)]
    if f.get("fusszeile"):
        inhalt += [pdf.Spacer(1, 10), pdf.p(f["fusszeile"], pdf.KLEIN)]
    steuer = f"Steuernummer: {f['steuernummer']}" if f.get("steuernummer") else ""
    ust = f"USt-IdNr.: {f['ustid']}" if f.get("ustid") else ""
    daten = pdf.dokument(f"{titel} {nr}", f"{titel} {nr}", inhalt, f, " · ".join(x for x in [steuer, ust] if x))
    if ist_re and b["nummer"] and e_rechnung and not zugferd.pruefen(b, f, emp or {}):
        try:   # Rechnungen tragen ihre Daten maschinenlesbar mit (ZUGFeRD); bei einem Fehler geht das normale PDF raus
            daten = zugferd.einbetten(daten, zugferd.xml_erzeugen(b, f, emp, storno_nr, storno_datum), f"{titel} {nr}", f["name"])
        except Exception:
            logging.getLogger(__name__).exception("E-Rechnung konnte nicht eingebettet werden (%s)", nr)
    return daten, f"{titel}-{nr}.pdf".replace(" ", "_")


def mahn_pdf(cur, bid, stufe: int) -> tuple[bytes, str]:
    cur.execute("SELECT * FROM belege WHERE id=%s AND art='rechnung'", (bid,))
    b = cur.fetchone()
    if not b:
        raise LookupError("Rechnung nicht gefunden")
    f = rechtstexte.firma(cur)
    emp = b["empfaenger"]
    titel = {1: "Zahlungserinnerung", 2: "1. Mahnung", 3: "2. Mahnung"}.get(stufe, "Mahnung")
    frist = date.today() + timedelta(days=7)
    adr = "\n".join(x for x in [emp.get("firma"), emp.get("ansprechpartner"), emp.get("strasse"), f"{emp.get('plz') or ''} {emp.get('ort') or ''}".strip()] if x)
    offen = b["brutto_cent"] - (b["bezahlt_cent"] or 0)
    inhalt = [pdf.p(adr), pdf.Spacer(1, 16), pdf.p(titel, pdf.H1), pdf.p(f"zu Rechnung {b['nummer']} vom {pdf.datum(b['datum'])}", pdf.KLEIN), pdf.Spacer(1, 12)]
    einl = {1: "vielleicht ist es untergegangen: Zu der oben genannten Rechnung konnten wir bisher keinen Zahlungseingang feststellen.",
            2: "trotz unserer Zahlungserinnerung konnten wir zu der oben genannten Rechnung bisher keinen Zahlungseingang feststellen.",
            3: "leider ist die oben genannte Rechnung trotz Erinnerung und Mahnung weiterhin offen."}.get(stufe, "die oben genannte Rechnung ist weiterhin offen.")
    inhalt += [pdf.p("Guten Tag,"), pdf.Spacer(1, 6), pdf.p(einl), pdf.Spacer(1, 10),
               pdf.tabelle(["Rechnung", "Fällig seit", "Offener Betrag"], [[b["nummer"], pdf.datum(b["faellig_am"]), pdf.euro(offen)]], breiten=[60 * pdf.mm, 55 * pdf.mm, 55 * pdf.mm], rechts_ab=2),
               pdf.Spacer(1, 10), pdf.p(f"Bitte überweisen Sie den offenen Betrag bis zum {pdf.datum(frist)} auf folgendes Konto:"),
               pdf.p(f"{f['name']}\nIBAN: {f.get('iban') or '–'}" + (f"\nBIC: {f['bic']}" if f.get("bic") else "") + f"\nVerwendungszweck: {b['nummer']}"), pdf.Spacer(1, 10),
               pdf.p("Sollte sich Ihre Zahlung mit diesem Schreiben überschnitten haben, betrachten Sie es bitte als gegenstandslos." if stufe == 1 else "Bitte melden Sie sich bei Rückfragen oder wenn es ein Problem mit der Rechnung gibt.")]
    return pdf.dokument(titel, f"{titel} {b['nummer']}", inhalt, f, " · ".join(x for x in [f"Steuernummer: {f['steuernummer']}" if f.get("steuernummer") else "", f"USt-IdNr.: {f['ustid']}" if f.get("ustid") else ""] if x)), f"{titel}-{b['nummer']}.pdf".replace(" ", "_")
