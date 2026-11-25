"""E-Rechnung: ZUGFeRD / Factur-X (Profil EN 16931) für ausgestellte Rechnungen.

Aus den Rechnungsdaten entsteht ein CII-XML (factur-x.xml). Das normale Rechnungs-PDF wird zu PDF/A-3b und
trägt dieses XML als Anhang: Menschen sehen das gewohnte PDF, Buchhaltungsprogramme lesen die Daten aus dem XML.
Alles läuft mit reportlab und pypdf, die schon im Portal sind (keine zusätzlichen Pakete)."""
import hashlib
import struct
from datetime import date, datetime, timezone
from decimal import Decimal
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ByteStringObject, DecodedStreamObject, DictionaryObject, NameObject,
                           NumberObject, TextStringObject)

PROFIL = "urn:cen.eu:en16931:2017"
XML_NAME = "factur-x.xml"
KLEIN_GRUND = "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."

_EINHEITEN = {"std": "HUR", "std.": "HUR", "h": "HUR", "stunde": "HUR", "stunden": "HUR", "tag": "DAY", "tage": "DAY", "tg": "DAY",
              "monat": "MON", "monate": "MON", "mon": "MON", "km": "KMT", "m": "MTR", "kg": "KGM", "l": "LTR", "m²": "MTK", "qm": "MTK"}


def _einheit(text) -> str:
    return _EINHEITEN.get((text or "").strip().lower(), "C62")


def _d(x) -> str:
    return f"{(x if isinstance(x, date) else date.today()):%Y%m%d}"


def _eur(cent: int) -> str:
    return f"{Decimal(cent) / 100:.2f}"


def _menge(x) -> str:
    t = f"{Decimal(str(x)):.4f}".rstrip("0").rstrip(".")
    return t or "0"


def _e(x) -> str:
    return escape(str(x or "").strip())


def _partei(name, strasse, plz, ort, email=None, kontakt=None, steuer=None, kennung=None) -> str:
    x = (f"<ram:ID>{_e(kennung)}</ram:ID>" if kennung else "") + f"<ram:Name>{_e(name)}</ram:Name>"
    if kontakt and any(kontakt.values()):
        x += "<ram:DefinedTradeContact>"
        if kontakt.get("name"):
            x += f"<ram:PersonName>{_e(kontakt['name'])}</ram:PersonName>"
        if kontakt.get("telefon"):
            x += f"<ram:TelephoneUniversalCommunication><ram:CompleteNumber>{_e(kontakt['telefon'])}</ram:CompleteNumber></ram:TelephoneUniversalCommunication>"
        if kontakt.get("email"):
            x += f"<ram:EmailURIUniversalCommunication><ram:URIID>{_e(kontakt['email'])}</ram:URIID></ram:EmailURIUniversalCommunication>"
        x += "</ram:DefinedTradeContact>"
    x += "<ram:PostalTradeAddress>"
    if plz:
        x += f"<ram:PostcodeCode>{_e(plz)}</ram:PostcodeCode>"
    if strasse:
        x += f"<ram:LineOne>{_e(strasse)}</ram:LineOne>"
    x += f"<ram:CityName>{_e(ort)}</ram:CityName><ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress>"
    if email:
        x += f'<ram:URIUniversalCommunication><ram:URIID schemeID="EM">{_e(email)}</ram:URIID></ram:URIUniversalCommunication>'
    for schema, wert in (steuer or []):
        if wert:
            x += f'<ram:SpecifiedTaxRegistration><ram:ID schemeID="{schema}">{_e(wert)}</ram:ID></ram:SpecifiedTaxRegistration>'
    return x


def pruefen(b: dict, f: dict, emp: dict) -> list[str]:
    """Was für eine gültige E-Rechnung fehlt (Klartext für die Oberfläche)."""
    fehlt = []
    if not (f.get("name") and f.get("strasse") and f.get("plz") and f.get("ort")):
        fehlt.append("Firmenname und Anschrift (Einstellungen → Firma)")
    if not (f.get("ustid") or f.get("steuernummer")):
        fehlt.append("Steuernummer oder USt-IdNr. (Einstellungen → Firma)")
    if not (emp.get("firma") and emp.get("ort")):
        fehlt.append("Name und Ort des Rechnungsempfängers")
    if not b.get("nummer"):
        fehlt.append("Rechnungsnummer (die Rechnung ist noch ein Entwurf)")
    return fehlt


def xml_erzeugen(b: dict, f: dict, emp: dict, storno_nr: str | None = None, storno_datum=None) -> bytes:
    """CII-XML (Profil EN 16931) für eine Rechnung oder Stornorechnung. Stornos gehen als Gutschrift (381) mit positiven Beträgen."""
    storno = b.get("storno_von") is not None
    vz = -1 if storno else 1   # Stornobeträge sind in der Datenbank negativ
    klein = bool(b.get("kleinunternehmer"))
    satz = Decimal(0) if klein else Decimal(str(b.get("ust_satz") or 0))
    kat = "E" if klein else ("S" if satz > 0 else "Z")
    satz_t = f"{satz:.2f}"
    zeilen = ""
    summe = 0
    for i, p in enumerate(b["positionen"], 1):
        menge = Decimal(str(p["menge"]))
        preis = p["preis_cent"] * vz
        gesamt = int((menge * preis).quantize(Decimal("1"), rounding="ROUND_HALF_UP"))
        summe += gesamt
        zeilen += (f"<ram:IncludedSupplyChainTradeLineItem><ram:AssociatedDocumentLineDocument><ram:LineID>{i}</ram:LineID></ram:AssociatedDocumentLineDocument>"
                   f"<ram:SpecifiedTradeProduct><ram:Name>{_e(p['text'])[:200]}</ram:Name></ram:SpecifiedTradeProduct>"
                   f"<ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>{_eur(preis)}</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>"
                   f'<ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="{_einheit(p.get("einheit"))}">{_menge(menge)}</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>'
                   f"<ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:TypeCode>VAT</ram:TypeCode><ram:CategoryCode>{kat}</ram:CategoryCode><ram:RateApplicablePercent>{satz_t}</ram:RateApplicablePercent></ram:ApplicableTradeTax>"
                   f"<ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>{_eur(gesamt)}</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>"
                   "</ram:IncludedSupplyChainTradeLineItem>")
    netto = summe
    ust = int((Decimal(netto) * satz / 100).quantize(Decimal("1"), rounding="ROUND_HALF_UP"))
    brutto = netto + ust

    nr = b["nummer"]
    notiz = ""
    if b.get("leistungszeitraum"):
        notiz += f"<ram:IncludedNote><ram:Content>Leistungszeitraum: {_e(b['leistungszeitraum'])}</ram:Content></ram:IncludedNote>"
    verkaeufer = _partei(f["name"], f.get("strasse"), f.get("plz"), f.get("ort"), f.get("email"),
                         {"name": f.get("inhaber") or f.get("name"), "telefon": f.get("telefon"), "email": f.get("email")},
                         [("VA", f.get("ustid")), ("FC", f.get("steuernummer"))], kennung=None if f.get("ustid") else f.get("steuernummer"))   # BR-CO-26: Kennung oder USt-IdNr. nötig
    kaeufer = _partei(emp.get("firma") or emp.get("ansprechpartner"), emp.get("strasse"), emp.get("plz"), emp.get("ort"), emp.get("email"))
    ref = (b.get("kaeufer_referenz") or "").strip()
    iban = "".join((f.get("iban") or "").split()).upper()
    zahlung = "<ram:SpecifiedTradeSettlementPaymentMeans>" if iban else ""
    if iban:
        zahlung += f"<ram:TypeCode>58</ram:TypeCode><ram:PayeePartyCreditorFinancialAccount><ram:IBANID>{_e(iban)}</ram:IBANID></ram:PayeePartyCreditorFinancialAccount>"
        if f.get("bic"):
            zahlung += f"<ram:PayeeSpecifiedCreditorFinancialInstitution><ram:BICID>{_e(f['bic'].replace(' ', ''))}</ram:BICID></ram:PayeeSpecifiedCreditorFinancialInstitution>"
        zahlung += "</ram:SpecifiedTradeSettlementPaymentMeans>"
    steuer = (f"<ram:ApplicableTradeTax><ram:CalculatedAmount>{_eur(ust)}</ram:CalculatedAmount><ram:TypeCode>VAT</ram:TypeCode>" + (f"<ram:ExemptionReason>{_e(KLEIN_GRUND)}</ram:ExemptionReason>" if klein else "")
              + f"<ram:BasisAmount>{_eur(netto)}</ram:BasisAmount><ram:CategoryCode>{kat}</ram:CategoryCode>"
              f"<ram:RateApplicablePercent>{satz_t}</ram:RateApplicablePercent></ram:ApplicableTradeTax>")
    frist = ""
    if b.get("faellig_am") and not storno:
        frist = f'<ram:SpecifiedTradePaymentTerms><ram:DueDateDateTime><udt:DateTimeString format="102">{_d(b["faellig_am"])}</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms>'
    bezug = ""
    if storno and storno_nr:
        bezug = f"<ram:InvoiceReferencedDocument><ram:IssuerAssignedID>{_e(storno_nr)}</ram:IssuerAssignedID>" + (
            f'<ram:FormattedIssueDateTime><qdt:DateTimeString format="102">{_d(storno_datum)}</qdt:DateTimeString></ram:FormattedIssueDateTime>' if storno_datum else "") + "</ram:InvoiceReferencedDocument>"
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" '
           'xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" '
           'xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" '
           'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">'
           f"<rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter><ram:ID>{PROFIL}</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>"
           f'<rsm:ExchangedDocument><ram:ID>{_e(nr)}</ram:ID><ram:TypeCode>{"381" if storno else "380"}</ram:TypeCode>'
           f'<ram:IssueDateTime><udt:DateTimeString format="102">{_d(b.get("datum"))}</udt:DateTimeString></ram:IssueDateTime>{notiz}</rsm:ExchangedDocument>'
           f"<rsm:SupplyChainTradeTransaction>{zeilen}"
           f"<ram:ApplicableHeaderTradeAgreement>" + (f"<ram:BuyerReference>{_e(ref)}</ram:BuyerReference>" if ref else "")
           + f"<ram:SellerTradeParty>{verkaeufer}</ram:SellerTradeParty><ram:BuyerTradeParty>{kaeufer}</ram:BuyerTradeParty></ram:ApplicableHeaderTradeAgreement>"
           "<ram:ApplicableHeaderTradeDelivery/>"
           f"<ram:ApplicableHeaderTradeSettlement><ram:PaymentReference>{_e(nr)}</ram:PaymentReference><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>"
           f"{zahlung}{steuer}{frist}"
           f"<ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:LineTotalAmount>{_eur(netto)}</ram:LineTotalAmount><ram:TaxBasisTotalAmount>{_eur(netto)}</ram:TaxBasisTotalAmount>"
           f'<ram:TaxTotalAmount currencyID="EUR">{_eur(ust)}</ram:TaxTotalAmount><ram:GrandTotalAmount>{_eur(brutto)}</ram:GrandTotalAmount><ram:DuePayableAmount>{_eur(brutto)}</ram:DuePayableAmount>'
           f"</ram:SpecifiedTradeSettlementHeaderMonetarySummation>{bezug}</ram:ApplicableHeaderTradeSettlement>"
           "</rsm:SupplyChainTradeTransaction></rsm:CrossIndustryInvoice>")
    return xml.encode("utf-8")


# ---------- PDF/A-3 ----------

def _srgb_profil() -> bytes:
    """Kleines sRGB-ICC-Profil (v2), selbst erzeugt, für den PDF/A-Ausgabe-Intent."""
    def s15(v):
        return struct.pack(">i", round(v * 65536))

    def xyz(x, y, z):
        return b"XYZ \0\0\0\0" + s15(x) + s15(y) + s15(z)

    kurve = [round(65535 * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)) for c in (i / 1023 for i in range(1024))]
    curv = b"curv\0\0\0\0" + struct.pack(">I", 1024) + b"".join(struct.pack(">H", v) for v in kurve)
    beschr = b"sRGB IEC61966-2.1"
    desc = b"desc\0\0\0\0" + struct.pack(">I", len(beschr) + 1) + beschr + b"\0" + b"\0" * 4 + b"\0" * 4 + b"\0\0" + b"\0" + b"\0" * 67
    cprt = b"text\0\0\0\0" + b"Public Domain\0"
    tags = [(b"desc", desc), (b"cprt", cprt), (b"wtpt", xyz(0.9642, 1.0, 0.8249)),
            (b"rXYZ", xyz(0.4360747, 0.2225045, 0.0139322)), (b"gXYZ", xyz(0.3850649, 0.7168786, 0.0971045)),
            (b"bXYZ", xyz(0.1430804, 0.0606169, 0.7141733)), (b"rTRC", curv), (b"gTRC", curv), (b"bTRC", curv)]
    kopf_len = 128 + 4 + 12 * len(tags)
    tabelle, daten, off = b"", b"", kopf_len
    for name, d in tags:
        d += b"\0" * (-len(d) % 4)
        tabelle += name + struct.pack(">II", off, len(d))
        daten += d
        off += len(d)
    gesamt = kopf_len + len(daten)
    kopf = (struct.pack(">I", gesamt) + b"\0\0\0\0" + b"\x02\x10\x00\x00" + b"mntr" + b"RGB " + b"XYZ " + struct.pack(">6H", 2026, 1, 1, 0, 0, 0)
            + b"acsp" + b"\0" * 28 + struct.pack(">3i", 63190, 65536, 54061) + b"\0" * 4 + b"\0" * 16 + b"\0" * 28)
    assert len(kopf) == 128
    return kopf + struct.pack(">I", len(tags)) + tabelle + daten


def _pdfdatum(t: datetime) -> str:
    return t.strftime("D:%Y%m%d%H%M%S") + "Z"


def _xmp(titel: str, autor: str, jetzt: datetime) -> bytes:
    iso = jetzt.strftime("%Y-%m-%dT%H:%M:%SZ")
    xmp = f"""<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"><pdfaid:part>3</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance></rdf:Description>
<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title><rdf:Alt><rdf:li xml:lang="x-default">{escape(titel)}</rdf:li></rdf:Alt></dc:title><dc:creator><rdf:Seq><rdf:li>{escape(autor)}</rdf:li></rdf:Seq></dc:creator></rdf:Description>
<rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/"><pdf:Producer>Markentrix Portal</pdf:Producer></rdf:Description>
<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><xmp:CreatorTool>Markentrix Portal</xmp:CreatorTool><xmp:CreateDate>{iso}</xmp:CreateDate><xmp:ModifyDate>{iso}</xmp:ModifyDate></rdf:Description>
<rdf:Description rdf:about="" xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#"><fx:DocumentType>INVOICE</fx:DocumentType><fx:DocumentFileName>{XML_NAME}</fx:DocumentFileName><fx:Version>1.0</fx:Version><fx:ConformanceLevel>EN 16931</fx:ConformanceLevel></rdf:Description>
<rdf:Description rdf:about="" xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/" xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#" xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#">
<pdfaExtension:schemas><rdf:Bag><rdf:li rdf:parseType="Resource"><pdfaSchema:schema>Factur-X PDFA Extension Schema</pdfaSchema:schema><pdfaSchema:namespaceURI>urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#</pdfaSchema:namespaceURI><pdfaSchema:prefix>fx</pdfaSchema:prefix>
<pdfaSchema:property><rdf:Seq>
<rdf:li rdf:parseType="Resource"><pdfaProperty:name>DocumentFileName</pdfaProperty:name><pdfaProperty:valueType>Text</pdfaProperty:valueType><pdfaProperty:category>external</pdfaProperty:category><pdfaProperty:description>name of the embedded XML invoice file</pdfaProperty:description></rdf:li>
<rdf:li rdf:parseType="Resource"><pdfaProperty:name>DocumentType</pdfaProperty:name><pdfaProperty:valueType>Text</pdfaProperty:valueType><pdfaProperty:category>external</pdfaProperty:category><pdfaProperty:description>INVOICE</pdfaProperty:description></rdf:li>
<rdf:li rdf:parseType="Resource"><pdfaProperty:name>Version</pdfaProperty:name><pdfaProperty:valueType>Text</pdfaProperty:valueType><pdfaProperty:category>external</pdfaProperty:category><pdfaProperty:description>The actual version of the Factur-X XML schema</pdfaProperty:description></rdf:li>
<rdf:li rdf:parseType="Resource"><pdfaProperty:name>ConformanceLevel</pdfaProperty:name><pdfaProperty:valueType>Text</pdfaProperty:valueType><pdfaProperty:category>external</pdfaProperty:category><pdfaProperty:description>The conformance level of the embedded Factur-X data</pdfaProperty:description></rdf:li>
</rdf:Seq></pdfaSchema:property></rdf:li></rdf:Bag></pdfaExtension:schemas></rdf:Description>
</rdf:RDF></x:xmpmeta>
<?xpacket end="w"?>"""
    return xmp.encode("utf-8")


def einbetten(pdf_bytes: bytes, xml: bytes, titel: str, autor: str) -> bytes:
    """Macht aus dem Rechnungs-PDF ein PDF/A-3b mit angehängtem factur-x.xml."""
    from io import BytesIO
    jetzt = datetime.now(timezone.utc).replace(microsecond=0)
    w = PdfWriter(clone_from=PdfReader(BytesIO(pdf_bytes)))
    w.add_metadata({"/Title": titel, "/Author": autor, "/Producer": "Markentrix Portal", "/Creator": "Markentrix Portal",
                    "/CreationDate": _pdfdatum(jetzt), "/ModDate": _pdfdatum(jetzt)})
    # XML-Anhang
    anhang = DecodedStreamObject()
    anhang.set_data(xml)
    anhang = anhang.flate_encode()
    anhang.update({NameObject("/Type"): NameObject("/EmbeddedFile"), NameObject("/Subtype"): NameObject("/text/xml"),
                   NameObject("/Params"): DictionaryObject({NameObject("/CheckSum"): ByteStringObject(hashlib.md5(xml).digest()),
                                                            NameObject("/ModDate"): TextStringObject(_pdfdatum(jetzt)),
                                                            NameObject("/Size"): NumberObject(len(xml))})})
    anhang_ref = w._add_object(anhang)
    fname = TextStringObject(XML_NAME)
    spec = w._add_object(DictionaryObject({NameObject("/Type"): NameObject("/Filespec"), NameObject("/F"): fname, NameObject("/UF"): fname,
                                           NameObject("/Desc"): TextStringObject("Factur-X Rechnungsdaten"), NameObject("/AFRelationship"): NameObject("/Data"),
                                           NameObject("/EF"): DictionaryObject({NameObject("/F"): anhang_ref, NameObject("/UF"): anhang_ref})}))
    wurzel = w._root_object
    wurzel[NameObject("/Names")] = DictionaryObject({NameObject("/EmbeddedFiles"): DictionaryObject({NameObject("/Names"): ArrayObject([fname, spec])})})
    wurzel[NameObject("/AF")] = ArrayObject([spec])
    # Metadaten (XMP)
    meta = DecodedStreamObject()
    meta.set_data(_xmp(titel, autor, jetzt))
    meta.update({NameObject("/Type"): NameObject("/Metadata"), NameObject("/Subtype"): NameObject("/XML")})
    wurzel[NameObject("/Metadata")] = w._add_object(meta)
    # Farbprofil
    icc = DecodedStreamObject()
    icc.set_data(_srgb_profil())
    icc = icc.flate_encode()
    icc[NameObject("/N")] = NumberObject(3)
    wurzel[NameObject("/OutputIntents")] = ArrayObject([w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/OutputIntent"), NameObject("/S"): NameObject("/GTS_PDFA1"),
        NameObject("/OutputConditionIdentifier"): TextStringObject("sRGB IEC61966-2.1"), NameObject("/Info"): TextStringObject("sRGB IEC61966-2.1"),
        NameObject("/DestOutputProfile"): w._add_object(icc)}))])
    wurzel[NameObject("/PageMode")] = NameObject("/UseAttachments")
    w._ID = ArrayObject([ByteStringObject(hashlib.md5(pdf_bytes).digest()), ByteStringObject(hashlib.md5(xml).digest())])
    out = BytesIO()
    w.write(out)
    return out.getvalue()
