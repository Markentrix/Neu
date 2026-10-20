"""Auftragsverarbeitungsvertrag (AVV) Version 2: Vertragstext (aus avv_text.py) und PDF. Der Text ist eine Vorlage und muss juristisch geprüft werden."""
import hashlib
import json
from datetime import date

from . import avv_text, pdf
from .pdf import H1, H2, KLEIN, Spacer, p, tabelle

VERSION = "2"
STAND = "20.10.2026"

# Anlage 1: (Schlüssel, eingerückt). Reihenfolge und Texte entsprechen avv_text.MODULTEXTE.
MODULE = [("portal", 0), ("website", 0), ("automationen", 0), ("email", 0), ("email_auftragnehmer", 1), ("email_eigen", 1), ("termin", 0), ("termin_auftragnehmer", 1),
          ("termin_eigen", 1), ("ki_chat", 0), ("telefon", 0), ("whatsapp", 0), ("domain", 0), ("sonstiges", 0)]
MODUL_KEYS = [m[0] for m in MODULE]

# Welcher Unterauftragsverarbeiter gehört zu welchem Modul (Reihenfolge wie avv_text.UNTERAUFTRAGSVERARBEITER); None = immer
UAV_MODULE = [None, ["automationen"], ["email_auftragnehmer", "termin_auftragnehmer"], ["ki_chat"], ["telefon"], ["whatsapp"], ["domain"]]

STANDARD_ANLAGE = {"module": ["portal"], "domain": "", "sonstiges": "", "leistung": "Markentrix-Portal und Automatisierungen", "hauptvertrag_datum": "", "weisung_name": "", "weisung_email": ""}


def anlage_bereinigen(a: dict | None) -> dict:
    """Nur bekannte Schlüssel, Portal (Basis) ist immer dabei, Unterpunkte nur mit Hauptpunkt."""
    a = {**STANDARD_ANLAGE, **(a or {})}
    mods = {m for m in a.get("module", []) if m in MODUL_KEYS} | {"portal"}
    for unter, haupt in (("email_auftragnehmer", "email"), ("email_eigen", "email"), ("termin_auftragnehmer", "termin"), ("termin_eigen", "termin")):
        if unter in mods:
            mods.add(haupt)
    a["module"] = [k for k in MODUL_KEYS if k in mods]
    for k in ("domain", "sonstiges", "leistung", "hauptvertrag_datum", "weisung_name", "weisung_email"):
        a[k] = str(a.get(k) or "").strip()[:300]
    return a


def anlage_pruefen(a: dict) -> str | None:
    """Fehlertext, wenn eine Pflichtangabe zu einem angekreuzten Modul fehlt."""
    if "domain" in a["module"] and not a["domain"]:
        return "Bitte die Domain(s) eintragen oder das Modul „Domainverwaltung“ abwählen."
    if "sonstiges" in a["module"] and not a["sonstiges"]:
        return "Bitte „Sonstiges“ beschreiben oder abwählen."
    for haupt, unter in (("email", ("email_auftragnehmer", "email_eigen")), ("termin", ("termin_auftragnehmer", "termin_eigen"))):
        if haupt in a["module"] and not any(u in a["module"] for u in unter):
            return "Bitte bei E-Mail und Terminbuchung festlegen, über wessen Konto sie laufen (Auftragnehmer oder eigenes Konto des Kunden)."
    return None


def unterauftragnehmer(text: str | None, anlage: dict | None = None) -> list:
    """Anlage 3: Standardliste nach gebuchten Modulen. Eigene Liste aus den Einstellungen ('Name | Leistung | Modul | Ort | Grundlage' je Zeile) ersetzt sie ungefiltert."""
    zeilen = []
    for z in (text or "").splitlines():
        t = [x.strip() for x in z.split("|")]
        if t[0]:
            zeilen.append((t + [""] * 5)[:5])
    if zeilen:
        return zeilen
    mods = set(anlage_bereinigen(anlage)["module"])
    return [list(u) for u, schluessel in zip(avv_text.UNTERAUFTRAGSVERARBEITER, UAV_MODULE) if schluessel is None or mods & set(schluessel)]


def offene_punkte(kunde: dict, firma: dict, anlage: dict | None = None) -> list:
    """Angaben, die vor dem Versand noch fehlen (im PDF stünde sonst ein Platzhalter in eckigen Klammern)."""
    a = anlage_bereinigen(anlage)
    o = []
    if not kunde.get("firma") or not kunde.get("strasse") or not kunde.get("ort"):
        o.append("Firma und Anschrift des Kunden sind unvollständig (Kundenakte ergänzen).")
    if not a["hauptvertrag_datum"]:
        o.append("Datum des Hauptvertrags fehlt.")
    if not (a["weisung_name"] or kunde.get("ansprechpartner")) or not (a["weisung_email"] or kunde.get("email")):
        o.append("Weisungsberechtigte Person (Name, E-Mail) beim Kunden fehlt.")
    if not firma.get("inhaber") or not firma.get("email"):
        o.append("Firmendaten (Inhaber, E-Mail) unter Einstellungen → Firmendaten ergänzen – sie erscheinen als Weisungsempfänger.")
    fehler = anlage_pruefen(a)
    if fehler:
        o.append(fehler)
    return o


def standard_unterauftragnehmer_text() -> str:
    return "\n".join(" | ".join(u) for u in avv_text.UNTERAUFTRAGSVERARBEITER)


def _adresse(k: dict) -> str:
    teile = [k.get("firma"), "" if (k.get("rechtsform") or "-") in (k.get("firma") or "") else k.get("rechtsform"), f"vertreten durch / Inhaber: {k['ansprechpartner']}" if k.get("ansprechpartner") else "", k.get("strasse"),
             f"{k.get('plz') or ''} {k.get('ort') or ''}".strip(), f"E-Mail: {k['email']}" if k.get("email") else "", f"Telefon: {k['telefon']}" if k.get("telefon") else ""]
    return ", ".join(t for t in teile if t)


def _firmenadresse(f: dict) -> str:
    name = f.get("name") or "Markentrix"
    inhaber = f"Inhaber {f['inhaber']}" if f.get("inhaber") else ""
    return ", ".join(t for t in [name, inhaber, f.get("strasse"), f"{f.get('plz') or ''} {f.get('ort') or ''}".strip(),
                                 f"E-Mail: {f['email']}" if f.get("email") else "", f"Telefon: {f['telefon']}" if f.get("telefon") else ""] if t)


def _de(d: str) -> str:
    try:
        return date.fromisoformat(d).strftime("%d.%m.%Y")
    except ValueError:
        return d


def text_hash(kunde: dict, firma: dict, unter: list, anlage: dict | None = None) -> str:
    """Prüfsumme über Parteien, Anlage 1, Unterauftragsverarbeiter, Version und den gesamten Vertragstext."""
    roh = json.dumps([VERSION, _adresse(kunde), _firmenadresse(firma), anlage_bereinigen(anlage), [list(u) for u in unter],
                      avv_text.ABSCHNITTE, avv_text.DATENARTEN, avv_text.TOM, avv_text.MODULTEXTE], ensure_ascii=False, default=str)
    return hashlib.sha256(roh.encode()).hexdigest()


def avv_pdf(kunde: dict, firma: dict, unter: list, bestaetigung: dict | None = None, anlage: dict | None = None) -> bytes:
    a = anlage_bereinigen(anlage)
    fett = pdf.RECHTS_FETT.clone("fett_links", alignment=0)
    inhalt = [p("Vertrag zur Auftragsverarbeitung gemäß Art. 28 DSGVO", H1), p(f"{firma.get('name') or 'Markentrix'} · Version {VERSION} · Stand {STAND}", KLEIN), Spacer(1, 8),
              p("Vertragsparteien", H2), p("zwischen"), p(_adresse(kunde) or "[Auftraggeber]", fett), p("– nachfolgend „Auftraggeber“ –"), Spacer(1, 4),
              p("und"), p(_firmenadresse(firma), fett), p("– nachfolgend „Auftragnehmer“ –"), Spacer(1, 4)]
    haupt = avv_text.HAUPTVERTRAG.replace("[Leistungsbezeichnung, z. B. Markentrix-Portal und Automatisierungen]", a["leistung"] or "Markentrix-Portal und Automatisierungen")
    if a["hauptvertrag_datum"]:
        haupt = haupt.replace("[Datum]", _de(a["hauptvertrag_datum"]))
    inhalt += [p(" ".join(haupt.split()))]
    weisung = ", ".join(x for x in [a["weisung_name"] or kunde.get("ansprechpartner"), a["weisung_email"] or kunde.get("email")] if x) or "[Name, E-Mail]"
    empfaenger = ", ".join(x for x in [firma.get("inhaber"), firma.get("email")] if x)
    for titel, absaetze in avv_text.ABSCHNITTE:
        inhalt.append(p(titel, H2))
        for t in absaetze:
            if t == "{{DATENARTEN}}":
                inhalt += [tabelle(["Datenart", "Beispiele"], avv_text.DATENARTEN, breiten=[45 * pdf.mm, 125 * pdf.mm]), Spacer(1, 4)]
                continue
            t = t.replace("[Name, E-Mail]", weisung)
            if empfaenger:
                t = t.replace("Christian Wien, info@markentrix.de", empfaenger)
            inhalt += [p(t), Spacer(1, 3)]
    if bestaetigung:
        inhalt += [Spacer(1, 22), p("Elektronische Bestätigung", H2),
                   p(f"Der Auftraggeber hat diesen Vertrag am {bestaetigung['zeit']} im Markentrix-Portal elektronisch bestätigt "
                     f"(bestätigt durch {bestaetigung['name']}, angemeldet als {bestaetigung['email']}). "
                     "Der Auftragnehmer hat den Vertrag durch Bereitstellung im Portal angeboten und erkennt die Bestätigung an."),
                   Spacer(1, 4), p(f"Prüfsumme des bestätigten Vertragstextes (SHA-256): {bestaetigung['hash']}", KLEIN)]
    else:
        ort = firma.get("ort") or "Celle"
        inhalt += [Spacer(1, 26), tabelle(["", "Auftraggeber", "Auftragnehmer"], [["Ort, Datum", "\n\n", f"{ort}, \n\n"], ["Name", kunde.get("ansprechpartner") or "", firma.get("inhaber") or ""], ["Unterschrift", "\n\n\n", "\n\n\n"]],
                                          breiten=[30 * pdf.mm, 70 * pdf.mm, 70 * pdf.mm])]
    # Anlage 1: gebuchte Module mit Ankreuzfeldern
    inhalt += [pdf.PageBreak(), p("Anlage 1: Gebuchte Module", H1), Spacer(1, 4), p(avv_text.EINLEITUNG_MODULE), Spacer(1, 6)]
    from reportlab.platypus import Table, TableStyle
    zeilen = []
    for (schluessel, einzug), text in zip(MODULE, avv_text.MODULTEXTE):
        if schluessel == "domain":
            text = text.replace("[Domain]", a["domain"] or "[Domain]")
        if schluessel == "sonstiges":
            text = text.replace("[Beschreibung]", a["sonstiges"] or "[Beschreibung]")
        zeilen.append([pdf.kaestchen(schluessel in a["module"], 6 * einzug), p(text)])
    t = Table(zeilen, colWidths=[12 * pdf.mm, 158 * pdf.mm], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LINEBELOW", (0, 0), (-1, -1), 0.25, pdf.colors.HexColor("#E6E9F3"))]
                          + [("LEFTPADDING", (0, 0), (0, -1), 0)]))
    inhalt.append(t)
    inhalt += [pdf.PageBreak(), p("Anlage 2: Technische und organisatorische Maßnahmen (Art. 32 DSGVO)", H1), Spacer(1, 6),
               tabelle(["Bereich", "Maßnahme"], avv_text.TOM, breiten=[38 * pdf.mm, 132 * pdf.mm])]
    inhalt += [Spacer(1, 18), p("Anlage 3: Unterauftragsverarbeiter", H1), Spacer(1, 4), p(avv_text.EINLEITUNG_UAV.replace("[Datum]", date.today().strftime("%d.%m.%Y"))), Spacer(1, 6),
               tabelle(["Unternehmen", "Leistung", "Modul", "Verarbeitungsort", "Grundlage Drittland"], [list(u) for u in unter], breiten=[32 * pdf.mm, 36 * pdf.mm, 24 * pdf.mm, 40 * pdf.mm, 38 * pdf.mm])]
    return pdf.dokument("Auftragsverarbeitungsvertrag", f"AVV Version {VERSION}", inhalt, firma, fuss_extra=f"Vertrag zur Auftragsverarbeitung (Art. 28 DSGVO), Version {VERSION}")
