"""Auftragsverarbeitungsvertrag (AVV): Vertragstext und PDF. Der Text ist eine Vorlage und muss juristisch geprüft werden."""
from . import pdf
from .pdf import H1, H2, KLEIN, Spacer, p, tabelle

VERSION = "1"

STANDARD_UNTERAUFTRAGNEHMER = [
    ("Hetzner Online GmbH", "Server-Hosting", "Deutschland"),
    ("Anthropic Ireland, Limited / Anthropic PBC", "Beantwortung von Chat-Nachrichten im KI-Assistenten (nur wenn das Modul gebucht ist)", "Irland / USA, Übermittlung auf Grundlage von Standardvertragsklauseln"),
]


def unterauftragnehmer(text: str | None) -> list:
    """Eigene Liste aus den Einstellungen ('Name | Leistung | Sitz' je Zeile), sonst die Standardliste."""
    zeilen = []
    for z in (text or "").splitlines():
        teile = [t.strip() for t in z.split("|")]
        if teile[0]:
            zeilen.append((teile[0], teile[1] if len(teile) > 1 else "", teile[2] if len(teile) > 2 else ""))
    return zeilen or STANDARD_UNTERAUFTRAGNEHMER


def _adresse(k: dict) -> str:
    teile = [k.get("firma"), k.get("rechtsform"), k.get("strasse"), f"{k.get('plz') or ''} {k.get('ort') or ''}".strip()]
    return ", ".join(t for t in teile if t)


def _firmenadresse(f: dict) -> str:
    name = f.get("name") or "Markentrix"
    inhaber = f"Inhaber {f['inhaber']}" if f.get("inhaber") else ""
    return ", ".join(t for t in [name, inhaber, f.get("strasse"), f"{f.get('plz') or ''} {f.get('ort') or ''}".strip()] if t)


def avv_pdf(kunde: dict, firma: dict, unter: list) -> bytes:
    inhalt = [p("Vertrag zur Auftragsverarbeitung", H1), p("gemäß Art. 28 Datenschutz-Grundverordnung (DSGVO)", KLEIN), Spacer(1, 10),
              p("zwischen"), p(_adresse(kunde) or "[Auftraggeber]", pdf.RECHTS_FETT.clone("fett_links", alignment=0)), p("– nachfolgend „Auftraggeber“ –"), Spacer(1, 4),
              p("und"), p(_firmenadresse(firma), pdf.RECHTS_FETT.clone("fett_links2", alignment=0)), p("– nachfolgend „Auftragnehmer“ –")]
    def par(titel, *absaetze):
        inhalt.append(p(titel, H2))
        for a in absaetze:
            inhalt.append(p(a)); inhalt.append(Spacer(1, 3))
    par("1. Gegenstand und Dauer",
        "(1) Der Auftragnehmer verarbeitet im Auftrag des Auftraggebers personenbezogene Daten im Rahmen der vereinbarten Leistungen (z. B. Website-Anfragen, Terminverwaltung, KI-Assistent, Kontakte, Berichte) über das Markentrix-Portal und die zugehörigen Automatisierungen.",
        "(2) Die Dauer dieses Vertrags entspricht der Laufzeit des Hauptvertrags.")
    par("2. Art und Zweck der Verarbeitung, Datenarten, Betroffene",
        "Zweck: Bearbeitung von Kundenanfragen und Terminen, Kommunikation, Berichte, Betrieb des Portals.",
        "Datenarten: Kontaktdaten (Name, E-Mail, Telefon), Nachrichteninhalte, Termindaten, gegebenenfalls Angaben zur Anfrage.",
        "Betroffene: Kundinnen und Kunden, Interessenten und Mitarbeitende des Auftraggebers.")
    par("3. Weisungen",
        "Der Auftragnehmer verarbeitet Daten nur auf dokumentierte Weisung des Auftraggebers. Der Hauptvertrag und dieser Vertrag sind die Weisung. Weitere Weisungen erfolgen in Textform. Hält der Auftragnehmer eine Weisung für rechtswidrig, weist er unverzüglich darauf hin.")
    par("4. Pflichten des Auftragnehmers",
        "(1) Alle Personen mit Zugriff auf die Daten sind zur Vertraulichkeit verpflichtet.",
        "(2) Der Auftragnehmer setzt die technischen und organisatorischen Maßnahmen gemäß Anlage 1 um.",
        "(3) Er unterstützt den Auftraggeber bei Betroffenenrechten (Auskunft, Berichtigung, Löschung) und bei den Pflichten nach Art. 32 bis 36 DSGVO.",
        "(4) Verletzungen des Schutzes personenbezogener Daten meldet er unverzüglich nach Bekanntwerden.",
        "(5) Nach Vertragsende werden die Daten nach Wahl des Auftraggebers herausgegeben oder gelöscht, soweit keine gesetzliche Aufbewahrungspflicht entgegensteht.")
    par("5. Unterauftragsverarbeiter",
        "Der Auftraggeber stimmt dem Einsatz der in Anlage 2 genannten Unterauftragsverarbeiter zu. Änderungen teilt der Auftragnehmer vorab in Textform mit; der Auftraggeber kann aus wichtigem Grund widersprechen.",
        "Werden Daten in einem Land außerhalb des Europäischen Wirtschaftsraums verarbeitet, stellt der Auftragnehmer sicher, dass die Voraussetzungen der Art. 44 ff. DSGVO erfüllt sind (zum Beispiel Angemessenheitsbeschluss oder Standardvertragsklauseln).")
    par("6. Kontrollrechte",
        "Der Auftraggeber kann sich nach Voranmeldung von der Einhaltung dieses Vertrags überzeugen, in der Regel durch Auskunft und Nachweise.")
    par("7. Haftung, Schlussbestimmungen",
        "Es gelten die gesetzlichen Regelungen. Änderungen bedürfen der Textform. Es gilt deutsches Recht.")
    inhalt += [Spacer(1, 26), tabelle(["Ort, Datum", "Auftraggeber", "Auftragnehmer"], [["\n\n\n", "\n\n\n", "\n\n\n"]])]
    inhalt += [pdf.PageBreak(), p("Anlage 1: Technische und organisatorische Maßnahmen", H1), Spacer(1, 6)]
    tom = [("Zutritt", "Betrieb auf Servern der Hetzner Online GmbH (Rechenzentrum in Deutschland); Zutrittskontrolle durch den Rechenzentrumsbetreiber."),
           ("Zugang", "Passwortpflicht (mindestens 10 Zeichen), Sperre nach Fehlversuchen, optionale Zwei-Faktor-Anmeldung, Sitzungen laufen ab, Serverzugang nur per Schlüssel oder Konsole."),
           ("Zugriff", "Rollen (Admin, Kunde, Vertrieb); Datenbank-Trennung pro Kunde (Row-Level-Security), jeder Kunde sieht nur seine eigenen Daten."),
           ("Weitergabe", "Verschlüsselte Übertragung (HTTPS/TLS); Zugangsdaten und Schlüssel werden verschlüsselt gespeichert."),
           ("Eingabe", "Protokollierung wichtiger Aktionen (Audit-Log), nicht veränderbar."),
           ("Auftragskontrolle", "Verarbeitung nur nach Weisung; Unterauftragnehmer sind vertraglich gebunden."),
           ("Verfügbarkeit", "Tägliche Sicherung, verschlüsselte Kopie an externem Ort, regelmäßiger Wiederherstellungstest, Überwachung mit Alarm."),
           ("Trennung", "Getrennte Mandanten, getrennte Umgebungen für Test und Betrieb."),
           ("Löschung", "Aufbewahrungs- und Löschregeln; Löschung nach Vertragsende.")]
    inhalt.append(tabelle(["Bereich", "Maßnahme"], [list(z) for z in tom], breiten=[38 * pdf.mm, 132 * pdf.mm]))
    inhalt += [Spacer(1, 18), p("Anlage 2: Unterauftragsverarbeiter", H1), Spacer(1, 6),
               tabelle(["Unternehmen", "Leistung", "Sitz / Verarbeitungsort"], [list(u) for u in unter], breiten=[50 * pdf.mm, 70 * pdf.mm, 50 * pdf.mm])]
    return pdf.dokument("Auftragsverarbeitungsvertrag", f"AVV Version {VERSION}", inhalt, firma, fuss_extra=f"Vertrag zur Auftragsverarbeitung (Art. 28 DSGVO), Version {VERSION}")
