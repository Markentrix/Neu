# Checkliste für die Rechtsberatung (vor dem ersten zahlenden Kunden)

Das Paket enthält Vorlagen und technische Umsetzung, aber **keine geprüften Rechtstexte**. Bitte von einem Anwalt (IT-/Datenschutzrecht) prüfen lassen:

1. **Hauptvertrag und AGB** für Kunden (Leistung, Laufzeit, Kündigung, Haftung, Preise, Zahlungsziel, Mahnwesen, Referenzkunden-Klausel, Rabatte).
2. **Auftragsverarbeitungsvertrag (AVV)**: Vorlage in `docs/AVV-Vorlage.md`; Unterauftragnehmer (Hetzner, E-Mail-Anbieter, Anthropic, Telefonie-Anbieter …) mit Standort und Drittlandübermittlung vollständig und aktuell halten.
3. **Datenschutzerklärung** und **Impressum** des Portals und der Kunden-Websites (Texte kommen aus den Firmendaten; prüfen, ob Inhalte und Cookies/Tools stimmen).
4. **KI-Kennzeichnung**: Entwurf in `docs/KI-KENNZEICHNUNG.md`.
5. **Vertriebler-/Handelsvertretervertrag** einschließlich Provisionsregeln, Rückbuchung/Stornohaftung und Ausgleichsanspruch nach § 89b HGB; Abgrenzung freie Mitarbeit/Scheinselbständigkeit.
6. **Rechnungen**: Pflichtangaben, Kleinunternehmer/Umsatzsteuer, **E-Rechnung** (schrittweise Pflicht ab 2025/2027/2028; PDF allein reicht dann für B2B nicht mehr, Lösung mit Steuerberatung festlegen).
7. **Aufbewahrung und Löschung**: Fristen für Rechnungen/Verträge, was beim Vertragsende gelöscht wird (siehe Offboarding in ANLEITUNG.md), Löschkonzept.
8. **Verzeichnis der Verarbeitungstätigkeiten**, technische und organisatorische Maßnahmen (TOM, Anlage der AVV), ggf. Datenschutz-Folgenabschätzung für den Telefon-/Chat-Assistenten.
9. **Zweiter Faktor, Zugriffsrechte, Protokollierung** (vorhanden) als Teil der TOM beschreiben lassen.
10. **AVV per Klick bestätigen**: Reicht die elektronische Bestätigung im Portal (Textform, Nachweis mit Name, Zeit, IP, Prüfsumme) für Art. 28 Abs. 9 DSGVO und für deine Kundengruppe, oder soll zusätzlich unterschrieben werden? Wortlaut des Bestätigungsvermerks prüfen lassen.
11. **Drittlandübermittlung**: Anthropic, Google, Meta (Irland, Konzernmutter USA): Rechtsgrundlage (Standardvertragsklauseln / EU-US Data Privacy Framework) und Folgen für die Unterauftragnehmer-Liste prüfen. Telefon-Assistent: Anbieter in der EU (Famulor) mit eigener Unterauftragnehmer-Liste, Aufzeichnungs- und Ansagepflichten klären.
12. **Leads aus Website-Check und Kontaktformular**: Speicherung im CRM, Löschfrist (12 Monate), Nachfassen per Mail oder Telefon (UWG § 7), Hinweise in der Datenschutzerklärung (Abschnitt Website-Check und Kontaktformular) ergänzen.
13. **Folgemails und Terminbuchung**: Automatische Nachfass-Mails (UWG § 7, Einwilligungstext, Abmeldelink) und Einwilligung bei der Terminbuchung prüfen, bevor die Folgemails eingeschaltet werden.
14. **SEPA-Lastschrift und Mahnwesen**: Mandatstext im Kundenportal (Online-Erteilung, Nachweis mit Zeit und IP), Ankündigungsfrist (Standard 3 Tage, vertraglich vereinbaren), automatische Zahlungserinnerungen/Mahnungen (Fristen, Mahntexte, B2B/B2C). Die Einzugsdatei vor dem ersten Echteinsatz mit der eigenen Bank testen (Format pain.008.001.02).
15. **Anrufprotokoll und Push-Nachrichten**: Telefon-Assistent als Auftragsverarbeitung, Hinweispflicht ggü. Anrufern (KI, Aufzeichnung), Löschfrist 180 Tage für Nummern und Zusammenfassungen; Push-Nachrichten enthalten keine Personendaten.

