# Vertrag zur Auftragsverarbeitung (Vorlage)

> **Wichtig:** Das ist eine Arbeitsvorlage, keine Rechtsberatung. Bitte einmal von einer Anwältin / einem Anwalt oder einer Datenschutzbeauftragten prüfen lassen, bevor sie mit Kunden verwendet wird. Eckige Klammern [ ] ausfüllen.

zwischen

**[Name und Anschrift des Kunden]** – nachfolgend „Auftraggeber“ –

und

**Markentrix, Inhaber Christian Wien, [Straße, PLZ Celle]** – nachfolgend „Auftragnehmer“ –

## 1. Gegenstand und Dauer
(1) Der Auftragnehmer verarbeitet im Auftrag des Auftraggebers personenbezogene Daten im Rahmen der vereinbarten Leistungen (z. B. Website-Anfragen, Terminverwaltung, KI-Assistent, Kontakte, Berichte) über das Markentrix-Portal und die zugehörigen Automatisierungen.
(2) Die Dauer entspricht der Laufzeit des Hauptvertrags.

## 2. Art und Zweck der Verarbeitung, Datenarten, Betroffene
- **Zweck:** Bearbeitung von Kundenanfragen und Terminen, Kommunikation, Berichte, Betrieb des Portals.
- **Datenarten:** Kontaktdaten (Name, E-Mail, Telefon), Nachrichteninhalte, Termindaten, ggf. Angaben zur Anfrage.
- **Betroffene:** Kundinnen und Kunden, Interessenten und Mitarbeitende des Auftraggebers.

## 3. Weisungen
Der Auftragnehmer verarbeitet Daten nur auf dokumentierte Weisung des Auftraggebers. Der Hauptvertrag und dieser Vertrag sind die Weisung. Weitere Weisungen erfolgen in Textform. Hält der Auftragnehmer eine Weisung für rechtswidrig, weist er unverzüglich darauf hin.

## 4. Pflichten des Auftragnehmers
(1) Vertraulichkeit: Alle Personen mit Zugriff sind zur Vertraulichkeit verpflichtet.
(2) Technische und organisatorische Maßnahmen gemäß **Anlage 1**.
(3) Unterstützung bei Betroffenenrechten (Auskunft, Berichtigung, Löschung) und bei Pflichten nach Art. 32–36 DSGVO.
(4) Meldung von Verletzungen des Schutzes personenbezogener Daten unverzüglich nach Bekanntwerden.
(5) Nach Vertragsende werden die Daten nach Wahl des Auftraggebers herausgegeben oder gelöscht, soweit keine gesetzliche Aufbewahrungspflicht entgegensteht.

## 5. Unterauftragsverarbeiter
Der Auftraggeber stimmt dem Einsatz der in **Anlage 2** genannten Unterauftragsverarbeiter zu. Änderungen teilt der Auftragnehmer vorab in Textform mit; der Auftraggeber kann aus wichtigem Grund widersprechen.

## 6. Kontrollrechte
Der Auftraggeber kann sich nach Voranmeldung von der Einhaltung dieses Vertrags überzeugen, in der Regel durch Auskunft und Nachweise.

## 7. Haftung, Schlussbestimmungen
Es gelten die gesetzlichen Regelungen. Änderungen bedürfen der Textform. Es gilt deutsches Recht.

Ort, Datum: ________  Auftraggeber: ________________  Auftragnehmer: ________________

---

## Anlage 1 – Technische und organisatorische Maßnahmen (Stand der Umsetzung im Markentrix-Portal)

| Bereich | Maßnahme |
|---|---|
| Zutritt | Betrieb auf Servern der Hetzner Online GmbH (Rechenzentrum Deutschland); Zutrittskontrolle durch den Rechenzentrumsbetreiber |
| Zugang | Passwort-Pflicht (mind. 10 Zeichen), Sperre nach Fehlversuchen, optionale Zwei-Faktor-Anmeldung, Sitzungen laufen ab, Server-Zugang nur per Schlüssel / Konsole |
| Zugriff | Rollen (Admin, Kunde, Vertrieb); Datenbank-Trennung pro Kunde (Row-Level-Security), jeder Kunde sieht nur seine Daten |
| Weitergabe | Verschlüsselte Übertragung (HTTPS/TLS); Zugangsdaten und Schlüssel verschlüsselt gespeichert |
| Eingabe | Protokollierung wichtiger Aktionen (Audit-Log), unveränderlich |
| Auftragskontrolle | Verarbeitung nur nach Weisung; Unterauftragnehmer vertraglich gebunden |
| Verfügbarkeit | Tägliche Sicherung, verschlüsselte Kopie an externem Ort, regelmäßiger Wiederherstellungstest, Überwachung mit Alarm |
| Trennung | Getrennte Mandanten, getrennte Umgebungen für Test und Betrieb |
| Löschung | Aufbewahrungs- und Löschregeln; Löschung nach Vertragsende |

## Anlage 2 – Unterauftragsverarbeiter

| Unternehmen | Leistung | Sitz / Verarbeitungsort |
|---|---|---|
| Hetzner Online GmbH | Server-Hosting | Deutschland |
| Anthropic (KI-Dienst) | Beantwortung von Chat-Nachrichten im KI-Assistenten, nur wenn das Modul gebucht ist | [Standort laut Vertrag ergänzen, ggf. USA – Garantien prüfen] |
| [E-Mail-Anbieter] | Versand von E-Mails | [ergänzen] |
| [weitere, z. B. Telefonie-/Voice-Dienst] | [ergänzen] | [ergänzen] |
