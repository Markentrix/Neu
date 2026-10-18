"""Impressum und Datenschutzerklärung des Portals. Standardtexte aus den Firmendaten; im Admin-Bereich überschreibbar.
Die Standardtexte sind eine Vorlage und ersetzen keine Rechtsberatung."""
from . import einstellungen
from .db import tx

LEER = {"name": "", "inhaber": "", "strasse": "", "plz": "", "ort": "", "email": "", "telefon": "", "website": "",
        "ustid": "", "steuernummer": "", "kleinunternehmer": False, "iban": "", "bic": "", "bank": "",
        "zahlungsziel_tage": 14, "mwst_satz": 19, "rechnungsprefix": "RE", "angebotsprefix": "AN", "fusszeile": ""}


def firma(cur) -> dict:
    return {**LEER, **einstellungen.lesen(cur, "firma")}


def _adresse(f) -> str:
    return "\n".join(x for x in [f["name"], f["inhaber"] and "Inhaber: " + f["inhaber"], f["strasse"], f"{f['plz']} {f['ort']}".strip()] if x)


def impressum_standard(f: dict) -> str:
    teile = ["Angaben gemäß § 5 DDG", _adresse(f) or "(Firmendaten bitte unter Einstellungen eintragen)"]
    kontakt = [x for x in [f["telefon"] and "Telefon: " + f["telefon"], f["email"] and "E-Mail: " + f["email"], f["website"] and "Internet: " + f["website"]] if x]
    if kontakt:
        teile.append("Kontakt\n" + "\n".join(kontakt))
    if f["ustid"]:
        teile.append("Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: " + f["ustid"])
    return "\n\n".join(teile)


def datenschutz_standard(f: dict) -> str:
    v = _adresse(f) or "(Firmendaten bitte unter Einstellungen eintragen)"
    mail = f["email"] or "(E-Mail-Adresse eintragen)"
    return f"""Datenschutzerklärung für das Markentrix-Portal

1. Verantwortlicher
{v}
E-Mail: {mail}

2. Wofür wir Daten verarbeiten
Das Portal dient Kundinnen, Kunden und Vertriebspartnern von Markentrix zur Nutzung der gebuchten Leistungen (Anfragen, Termine, Berichte, Dokumente, Assistent) und zur Abrechnung. Wir verarbeiten dazu Ihre Anmelde- und Kontaktdaten sowie die Inhalte, die Sie oder Ihre Systeme im Portal ablegen. Rechtsgrundlage ist die Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO) sowie unser berechtigtes Interesse am sicheren Betrieb (Art. 6 Abs. 1 lit. f DSGVO).

3. Cookies
Wir setzen ausschließlich ein technisch notwendiges Sitzungs-Cookie ein, das Sie angemeldet hält. Es gibt keine Werbe- oder Analyse-Cookies. Eine Einwilligung ist dafür nicht erforderlich.

4. Hosting und Protokolle
Das Portal läuft auf Servern der Hetzner Online GmbH in Deutschland. Beim Aufruf werden technisch notwendige Verbindungsdaten (z. B. IP-Adresse, Zeitpunkt) kurzzeitig protokolliert, um den Betrieb abzusichern und Missbrauch zu erkennen. Wichtige Aktionen im Portal werden zur Nachvollziehbarkeit in einem Protokoll gespeichert.

5. E-Mail-Versand
Einladungen, Passwort-Links, Benachrichtigungen und Berichte versenden wir über unseren E-Mail-Server.

6. KI-Assistent
Wenn der Assistent im Portal genutzt wird, werden Ihre Nachrichten und die zur Beantwortung nötigen Angaben aus Ihrem Konto an einen KI-Dienstleister (Anthropic) übermittelt und dort verarbeitet. Dabei kann eine Übermittlung in ein Land außerhalb der EU stattfinden; wir stützen uns hierfür auf die vom Dienstleister angebotenen vertraglichen Garantien. Sie werden im Chat ausdrücklich darauf hingewiesen, dass Sie mit einer KI schreiben. Bitte geben Sie keine besonders sensiblen Daten in den Chat ein.

7. Speicherdauer
Wir speichern Daten, solange das Vertragsverhältnis besteht und gesetzliche Aufbewahrungspflichten (z. B. für Rechnungen) es verlangen. Danach werden sie gelöscht.

8. Ihre Rechte
Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Wenden Sie sich dazu an {mail}. Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, zum Beispiel bei der Landesbeauftragten für den Datenschutz Niedersachsen.

9. Auftragsverarbeitung
Verarbeiten wir im Auftrag von Kunden personenbezogene Daten (z. B. deren Anfragen oder Kontakte), geschieht das auf Grundlage eines Vertrags zur Auftragsverarbeitung."""


def lesen(cur) -> dict:
    f = firma(cur)
    r = einstellungen.lesen(cur, "recht")
    return {"impressum": (r.get("impressum") or "").strip() or impressum_standard(f),
            "datenschutz": (r.get("datenschutz") or "").strip() or datenschutz_standard(f)}


def firma_system() -> dict:
    """Firmendaten für Ausgaben, die im Kundenkontext erzeugt werden (Kunden dürfen die Einstellungen sonst nicht lesen)."""
    with tx("system") as cur:
        return firma(cur)
