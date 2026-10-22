"""Vertragsvorlagen (ausfüllbare PDF-Formulare) mit Daten vorausfüllen: Referenzvertrag (Kunde) und Handelsvertretervertrag (Vertriebspartner).
Der Wortlaut der Verträge bleibt unverändert, es werden nur die Formularfelder gefüllt. Haken setzt immer der Vertragspartner selbst (Referenz) bzw. der Partner (Anlage 3)."""
import io
from datetime import date
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

DIR = Path(__file__).parent / "vorlagen"
VORLAGEN = {"referenz": "referenzvertrag.pdf", "handelsvertreter": "handelsvertretervertrag.pdf"}
DATEINAME = {"referenz": "Referenzvertrag-Markentrix", "handelsvertreter": "Handelsvertretervertrag-Markentrix"}


def felder(art: str) -> dict:
    return PdfReader(DIR / VORLAGEN[art]).get_fields() or {}


def ausfuellen(art: str, werte: dict, haken: list | tuple = ()) -> bytes:
    """Füllt die Formularfelder. werte: Feldname -> Text; haken: Feldnamen von Kontrollkästchen, die angekreuzt werden. Unbekannte Felder sind ein Fehler."""
    r = PdfReader(DIR / VORLAGEN[art])
    alle = r.get_fields() or {}
    unbekannt = [k for k in list(werte) + list(haken) if k not in alle]
    if unbekannt:
        raise ValueError("Unbekannte Formularfelder: " + ", ".join(unbekannt))
    w = PdfWriter(clone_from=r)
    setzen = {k: (v or "") for k, v in werte.items() if v not in (None, "")}
    for k in haken:
        zustaende = [s for s in (alle[k].get("/_States_") or []) if s != "/Off"]
        setzen[k] = NameObject(zustaende[0] if zustaende else "/Yes")
    for seite in w.pages:
        if "/Annots" not in seite:
            continue
        w.update_page_form_field_values(seite, setzen, auto_regenerate=False)
    w.set_need_appearances_writer(True)
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def datum_de(d: date | None = None) -> str:
    d = d or date.today()
    return d.strftime("%d.%m.%Y")


def feldwerte(art: str, pdf: bytes) -> dict:
    """Gelesene Werte eines ausgefüllten Formulars (für Tests und Kontrolle)."""
    return {k: v.get("/V") for k, v in (PdfReader(io.BytesIO(pdf)).get_fields() or {}).items()}


# ---------------------------------------------------------------- Online-Bestätigung im Portal
import hashlib  # noqa: E402
import json  # noqa: E402

REF_ELEMENTE = {"name": "Name und Firma", "logo": "Firmenlogo und Kennzeichen", "abb": "Abbildungen des öffentlichen Projektergebnisses", "link": "Link auf das Projekt",
                "kurz": "Kurzbeschreibung", "kenn": "Ergebnisangaben und Kennzahlen", "zitat": "Kundenstimme (Zitat)"}
REF_KANAELE = {"web": "Website von Markentrix", "social": "Social-Media-Profile von Markentrix", "ang": "Angebote, Präsentationen und Pitches", "print": "Print (z. B. Flyer, Broschüren)",
               "verz": "Branchenverzeichnisse und Bewertungsportale", "news": "Newsletter von Markentrix"}
HV_JANEIN = {"hilfspersonen": "Ich beschäftige Hilfspersonen oder Arbeitnehmer", "einziger_auftraggeber": "Markentrix ist voraussichtlich auf Dauer mein einziger Auftraggeber"}
HV_HAKEN = {"gewerbe": "Mein Gewerbe ist angemeldet", "steuer_erfasst": "Ich bin steuerlich erfasst", "betriebsmittel": "Ich setze eigene Betriebsmittel ein",
            "andere_auftraggeber": "Ich bin auch für andere Auftraggeber tätig oder darf dies sein", "versichert": "Ich bin ausreichend kranken- und pflegeversichert und sorge selbst für meine Altersvorsorge",
            "weisungsfrei": "Ich bestimme Zeit, Ort und Art meiner Tätigkeit selbst und unterliege keinen Weisungen", "statusfeststellung": "Mir ist das Statusfeststellungsverfahren (§ 7a SGB IV) bekannt",
            "nebenberuf": "Ich übe die Vermittlung neben einem anderen Hauptberuf aus", "arbeitgeber": "Mein Arbeitgeber hat zugestimmt oder es ist nicht zustimmungspflichtig",
            "konkurrenz": "Meine anderweitige Tätigkeit betrifft keine direkt konkurrierenden Leistungen"}


def _t(s, n=200):
    return " ".join(str(s or "").split())[:n]


def referenz_online(a: dict, ort: str, name: str) -> tuple:
    """Antworten des Kunden (Anlage 1) -> Formularwerte und Haken. Nichts wird vorausgewählt; unbekannte Codes werden ignoriert."""
    werte, haken, sauber = {}, [], {"elemente": {}, "kanaele": []}
    for code, el in (a.get("elemente") or {}).items():
        if code not in REF_ELEMENTE or not isinstance(el, dict) or not el.get("an"):
            continue
        text = _t(el.get("text"), 600)
        sauber["elemente"][code] = text
        haken.append(f"b_{code}_ck")
        if text:
            werte[f"b_{code}"] = text
    for code in a.get("kanaele") or []:
        if code in REF_KANAELE and code not in sauber["kanaele"]:
            sauber["kanaele"].append(code)
            haken.append(f"c_{code}_ck")
    sauber["personen_zeigen"] = bool(a.get("personen_zeigen"))
    sauber["personen_unkenntlich"] = bool(a.get("personen_unkenntlich"))
    if sauber["personen_zeigen"]:
        haken.append("d_zeigen_ck")
        sauber["personen_namen"] = _t(a.get("personen_namen"), 300)
        if sauber["personen_namen"]:
            werte["d_namen"] = sauber["personen_namen"]
    if sauber["personen_unkenntlich"]:
        haken.append("d_unkenntlich_ck")
    sauber["einschraenkungen"] = _t(a.get("einschraenkungen"), 1500)
    werte["e_text"] = sauber["einschraenkungen"] or "keine"
    werte["sig_k_name"] = name
    werte["sig_k_ortdatum"] = f"{ort}, {datum_de()} (elektronisch bestätigt)"
    return werte, haken, sauber


def handelsvertreter_online(a: dict, ort: str, name: str) -> tuple:
    werte, haken, sauber = {}, [], {}
    for k, feld in (("rechtsform", "pt_rechtsform"), ("strasse", "pt_strasse"), ("ort_anschrift", "pt_ort"), ("steuer", "pt_steuer"), ("gew_seit", "a3_gew_seit"), ("gew_amt", "a3_gew_amt"), ("steuer_nr", "a3_steuer")):
        v = _t(a.get(k), 120)
        sauber[k] = v
        if v:
            werte[feld] = v
    sauber["beauftragung"] = a.get("beauftragung") if a.get("beauftragung") in ("haupt", "neben") else ""
    haken.append("beauftragung_Hauptberuf" if sauber["beauftragung"] == "haupt" else "beauftragung_Nebenberuf")
    sauber["haken"] = [c for c in HV_HAKEN if a.get("haken", {}).get(c)] if isinstance(a.get("haken"), dict) else []
    haken += ["a3_" + c for c in sauber["haken"]]
    sauber["janein"] = {}
    for c in HV_JANEIN:
        v = (a.get("janein") or {}).get(c) if isinstance(a.get("janein"), dict) else None
        if v in ("ja", "nein"):
            sauber["janein"][c] = v
            haken.append(f"a3_{c}_{v}")
    werte["vertrag_pt_name"] = name
    werte["vertrag_pt_ort_datum"] = f"{ort}, {datum_de()} (elektronisch bestätigt)"
    werte["a3_ort_datum"] = f"{ort}, {datum_de()}"
    return werte, haken, sauber


def pruefsumme(art: str, werte: dict, haken: list) -> str:
    vorlage = hashlib.sha256((DIR / VORLAGEN[art]).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps({"art": art, "vorlage": vorlage, "werte": werte, "haken": sorted(haken)}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def mit_protokoll(pdf: bytes, art: str, firma: dict, name: str, email: str, zeit: str, ip: str, hashwert: str) -> bytes:
    """Hängt dem ausgefüllten Vertrag eine Seite mit dem Bestätigungsprotokoll an."""
    from . import pdf as pdflib
    titel = {"referenz": "Referenzvertrag", "handelsvertreter": "Handelsvertretervertrag"}[art]
    inhalt = [pdflib.p("Elektronische Bestätigung", pdflib.H1), pdflib.Spacer(1, 6),
              pdflib.p(f"Der Vertrag „{titel}“ wurde von der unten genannten Person im Portal gelesen, ausgefüllt und bestätigt (einfache elektronische Signatur)."), pdflib.Spacer(1, 8),
              pdflib.tabelle(["Angabe", "Wert"], [["Bestätigt von", name], ["Angemeldetes Konto", email], ["Zeitpunkt", zeit], ["IP-Adresse", ip], ["Prüfsumme (SHA-256)", hashwert]], breiten=[130, 350]),
              pdflib.Spacer(1, 8), pdflib.p("Die Prüfsumme ergibt sich aus dem Vertragstext und allen eingetragenen Angaben. Wird nachträglich etwas verändert, stimmt sie nicht mehr überein.", pdflib.KLEIN)]
    zusatz = PdfReader(io.BytesIO(pdflib.dokument("Bestätigungsprotokoll", titel, inhalt, firma)))
    w = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf)))
    for s in zusatz.pages:
        w.add_page(s)
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()
