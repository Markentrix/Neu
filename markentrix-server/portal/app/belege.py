"""Angebote und Rechnungen: Berechnung, Nummernvergabe, PDF, Texte.
Eine ausgestellte Rechnung wird nie geändert; Korrekturen laufen über eine Storno-Rechnung."""
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO

import segno
from fastapi import HTTPException
from reportlab.platypus import Image, KeepTogether

from . import pdf, rechtstexte

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


def _epc_qr(f: dict, beleg: dict):
    """GiroCode (EPC-QR) zum Bezahlen per Banking-App."""
    iban = "".join((f.get("iban") or "").split()).upper()
    if not iban or beleg["brutto_cent"] <= 0:
        return None
    inhalt = "\n".join(["BCD", "002", "1", "SCT", (f.get("bic") or "").strip(), (f.get("name") or "")[:70], iban,
                        f"EUR{beleg['brutto_cent'] / 100:.2f}", "", "", f"Rechnung {beleg['nummer']}"[:140]])
    puffer = BytesIO()
    segno.make(inhalt, error="m").save(puffer, kind="png", scale=4, border=1)
    puffer.seek(0)
    return puffer


def beleg_pdf(cur, bid, f: dict | None = None, empfaenger: dict | None = None) -> tuple[bytes, str]:
    cur.execute("SELECT * FROM belege WHERE id=%s", (bid,))
    b = cur.fetchone()
    if not b:
        raise LookupError("Beleg nicht gefunden")
    f = f or rechtstexte.firma(cur)
    ist_re = b["art"] == "rechnung"
    storno = b["storno_von"] is not None
    emp = empfaenger if (empfaenger and not b["empfaenger"]) else (b["empfaenger"] or (empfaenger_von(cur, b["kunden_id"]) if b["kunden_id"] else {}))
    storno_nr = None
    if storno:
        cur.execute("SELECT nummer FROM belege WHERE id=%s", (b["storno_von"],))
        r = cur.fetchone()
        storno_nr = r and r["nummer"]
    titel = ("Stornorechnung" if storno else "Rechnung") if ist_re else "Angebot"
    nr = b["nummer"] or "Entwurf"
    inhalt = []
    absender = " · ".join(x for x in [f["name"], f["strasse"], f"{f['plz']} {f['ort']}".strip()] if x)
    inhalt += [pdf.p(absender, pdf.KLEIN)]
    adr = "\n".join(x for x in [emp.get("firma"), emp.get("ansprechpartner"), emp.get("strasse"), f"{emp.get('plz') or ''} {emp.get('ort') or ''}".strip()] if x)
    info = ([["Kundennummer", emp["kundennummer"]]] if emp.get("kundennummer") else []) + [["Nummer", nr], ["Datum", pdf.datum(b["datum"]) or "–"]]
    if ist_re and b["faellig_am"]:
        info.append(["Zahlbar bis", pdf.datum(b["faellig_am"])])
    if not ist_re and b["faellig_am"]:
        info.append(["Gültig bis", pdf.datum(b["faellig_am"])])
    if b["leistungszeitraum"]:
        info.append(["Leistungszeitraum", b["leistungszeitraum"]])
    from reportlab.platypus import Table, TableStyle
    kopf = Table([[pdf.p(adr), Table([[pdf.p(k, pdf.KLEIN), pdf.p(v)] for k, v in info], colWidths=[32 * pdf.mm, 48 * pdf.mm])]], colWidths=[90 * pdf.mm, 80 * pdf.mm])
    kopf.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    inhalt += [pdf.Spacer(1, 8), kopf, pdf.Spacer(1, 18), pdf.p(f"{titel} {nr}" + (f" zu Rechnung {storno_nr}" if storno_nr else ""), pdf.H1)]
    if b["betreff"]:
        inhalt += [pdf.p(b["betreff"], pdf.H2)]
    if b["einleitung"]:
        inhalt += [pdf.p(b["einleitung"]), pdf.Spacer(1, 8)]
    zeilen = []
    for i, p in enumerate(b["positionen"], 1):
        gesamt = runden(Decimal(str(p["menge"])) * p["preis_cent"])
        menge = (f"{p['menge']:g}".replace(".", ",")) + (" " + p["einheit"] if p.get("einheit") else "")
        zeilen.append([str(i), pdf.p(p["text"]), menge, pdf.euro(p["preis_cent"]), pdf.euro(gesamt)])
    inhalt += [pdf.tabelle(["Pos.", "Beschreibung", "Menge", "Einzelpreis", "Gesamt"], zeilen, breiten=[12 * pdf.mm, 78 * pdf.mm, 24 * pdf.mm, 28 * pdf.mm, 28 * pdf.mm], rechts_ab=2)]
    summen_zeilen = [["Zwischensumme (netto)", pdf.euro(b["netto_cent"])]]
    if not b["kleinunternehmer"]:
        summen_zeilen.append([f"Umsatzsteuer {float(b['ust_satz']):g} %".replace(".", ","), pdf.euro(b["ust_cent"])])
    summen_zeilen.append(["Gesamtbetrag" if not b["kleinunternehmer"] else "Gesamtbetrag (ohne USt)", pdf.euro(b["brutto_cent"])])
    t = Table([[pdf.p(a, pdf.RECHTS_FETT if i == len(summen_zeilen) - 1 else pdf.RECHTS), pdf.p(c, pdf.RECHTS_FETT if i == len(summen_zeilen) - 1 else pdf.RECHTS)] for i, (a, c) in enumerate(summen_zeilen)], colWidths=[130 * pdf.mm, 40 * pdf.mm])
    t.setStyle(TableStyle([("LINEABOVE", (0, -1), (-1, -1), 0.8, pdf.colors.HexColor("#111827"))]))
    inhalt += [pdf.Spacer(1, 6), t]
    if b["kleinunternehmer"]:
        inhalt += [pdf.Spacer(1, 6), pdf.p(KLEIN_HINWEIS, pdf.KLEIN)]
    if ist_re and not storno:
        iban = f.get("iban")
        zahl = ["Bitte überweisen Sie den Betrag" + (f" bis zum {pdf.datum(b['faellig_am'])}" if b["faellig_am"] else "") + f" unter Angabe der Rechnungsnummer {nr}."]
        if iban:
            zahl.append(f"Empfänger: {f['name']}\nIBAN: {iban}" + (f"\nBIC: {f['bic']}" if f.get("bic") else "") + (f"\nBank: {f['bank']}" if f.get("bank") else ""))
        links = pdf.p("\n".join(zahl))
        qr = _epc_qr(f, b)
        zelle = [links, Image(qr, 28 * pdf.mm, 28 * pdf.mm) if qr else ""]
        zt = Table([zelle], colWidths=[132 * pdf.mm, 38 * pdf.mm])
        zt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        inhalt += [pdf.Spacer(1, 12), KeepTogether([pdf.p("Zahlung", pdf.H2), zt])]
    if storno:
        inhalt += [pdf.Spacer(1, 8), pdf.p("Diese Stornorechnung hebt die genannte Rechnung auf.", pdf.KLEIN)]
    if b["schluss"]:
        inhalt += [pdf.Spacer(1, 10), pdf.p(b["schluss"])]
    if not ist_re:
        inhalt += [pdf.Spacer(1, 10), pdf.p("Zur Annahme dieses Angebots bestätigen Sie es bitte im Kundenportal oder per E-Mail.", pdf.KLEIN)]
    if f.get("fusszeile"):
        inhalt += [pdf.Spacer(1, 10), pdf.p(f["fusszeile"], pdf.KLEIN)]
    steuer = f"Steuernummer: {f['steuernummer']}" if f.get("steuernummer") else ""
    ust = f"USt-IdNr.: {f['ustid']}" if f.get("ustid") else ""
    daten = pdf.dokument(f"{titel} {nr}", f"{titel} {nr}", inhalt, f, " · ".join(x for x in [steuer, ust] if x))
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
    return pdf.dokument(titel, f"{titel} {b['nummer']}", inhalt, f), f"{titel}-{b['nummer']}.pdf".replace(" ", "_")
