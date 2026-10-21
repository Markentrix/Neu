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


## Website-Dienste (Formular, Terminbuchung, Bewertungen, PayPal)
- Leistungsbeschreibung im AVV um die Verarbeitung von Formular- und Buchungsdaten der Website-Besucher ergänzen (wir verarbeiten sie als Auftragsverarbeiter; Speicherung: Anfragen im Kundenportal, Termine 180 Tage nach dem Termin).
- Anlage 3: Google (Places API, Abruf öffentlicher Bewertungsdaten) und Mailversand über unseren Server aufnehmen.
- Mustertext für die Datenschutzerklärung der Kunden-Websites: Kontaktformular, Online-Terminbuchung (inkl. Kalender-Einladung per E-Mail), PayPal (Zahlung direkt an den Kunden), Google-Bewertungen.
- Eigenes Postfach des Kunden (SMTP): Zugangsdaten verschlüsselt gespeichert, nur zum Versand der Website-Mails genutzt.

## Website-API (Anfragen, Termine, Statistik)
- Datenschutzerklärung der Kunden-Websites: Anfrage- und Terminformular (Zweck, Speicherdauer, Empfänger Hoster/Markentrix als Auftragsverarbeiter), Eingangsbestätigung per E-Mail.
- Besucherstatistik ohne Cookie und ohne IP-Speicherung (täglich wechselnder Hash, Aufbewahrung bis 400 Tage): Formulierung für die Datenschutzerklärung prüfen lassen.
- Terminbuchung mit Anzahlung per PayPal.Me: Hinweise zu Widerruf/Stornierung auf der jeweiligen Website durch den Kunden bzw. dessen Anwalt prüfen lassen.

## Terminerinnerungen und Überwachung der Websites
- Erinnerungs-Mails an Website-Besucher sind Service-Mails zu einer gebuchten Leistung (kein Werbeinhalt, kein Tracking); Hinweis in der Datenschutzerklärung der Kunden-Websites, dass die E-Mail-Adresse für Bestätigung, Erinnerung und Absage-Link genutzt wird.
- Nichterschienen-Vermerk (Name/E-Mail des Besuchers) ist ein personenbezogenes Datum des Kunden: Speicherung bis 180 Tage nach dem Termin, keine Weitergabe; Zweck und Löschfrist im AVV nennen.
- Wachdienst ruft nur die öffentlichen Seiten der Kunden ab und speichert keine Besucherdaten (nur Status, Antwortzeit, Zertifikats-Restlaufzeit).
- Vorschau-Freigabe: Name, Zeit und IP der freigebenden Person werden als Nachweis gespeichert (Berechtigtes Interesse/Vertragsdurchführung), Aufbewahrung wie die übrigen Kundenfreigaben.

## Mail-Protokoll, Datenexport und Wiederherstellung
- Mail-Protokoll speichert nur Zeitpunkt, Art, Empfänger-Domain und Fehlertext (90 Tage); im Verzeichnis der Verarbeitungstätigkeiten und AVV (Anlage 2) aufnehmen.
- Selbstbedienungs-Export (Art. 20 DSGVO): Format ZIP/JSON/PDF, Hinweis in der Datenschutzerklärung; Export wird im Audit-Log festgehalten.
- Kündigung im Portal ist verbindlich (Textform) und wird automatisch bestätigt: AGB/Vertrag müssen die Kündigung per Portal ausdrücklich zulassen, die Kündigungsfrist (Einstellung „Kündigung durch Kunden“, Standard 30 Tage zum Monatsende) und die Mindestlaufzeit nennen. Rücknahme nur innerhalb von 24 Stunden. Bei Verbrauchern zusätzlich Kündigungsbutton nach § 312k BGB prüfen.
- Wiederherstellung einzelner Kundendaten aus der Sicherung: Zugriff nur für Admins, Auszug wird nach spätestens 24 Stunden gelöscht, Vorgang steht im Audit-Log.

## Bewertungsanfragen und Wartungsverträge
- Bewertungsanfrage nach Termin ist eine Werbe-/Kundenpflege-Mail (§ 7 UWG): nur mit Opt-in des Kunden und Hinweis bei der Buchung bzw. in der Datenschutzerklärung der Kundenwebsite; jede Mail enthält einen Abmeldelink, abgemeldete Adressen werden gesperrt gespeichert (nur Kunde und E-Mail-Adresse).
- Wiederkehrende Rechnungen: Leistungszeitraum steht auf der Rechnung; Vertrag/AGB müssen Turnus, Vorauszahlung und automatische Rechnungsstellung regeln. Rechnungsnummern laufen fortlaufend im selben Nummernkreis.
- DNS-/Livegang-Check liest nur öffentliche DNS-Daten und die öffentlichen Seiten der Kunden.

## Statusseite, Preiserhöhung, Zahlungsverzug, Zugänge
- Statusseite: öffentlich nur über geheimen Link, enthält keine personenbezogenen Daten; im Verzeichnis der Verarbeitungstätigkeiten als Betriebstransparenz aufführen.
- Preiserhöhung: Einseitige Preisanpassungen brauchen eine wirksame Preisanpassungsklausel (bei Verbrauchern und AGB strenge Anforderungen) oder die Zustimmung des Kunden. Die Mindestfrist im Portal beträgt 30 Tage, der Vertrag kann mehr verlangen. Ankündigung, Lesebestätigung und Einwand werden mit Zeitpunkt gespeichert (Nachweis).
- Zahlungsverzug: Die Pause von Formular und Terminbuchung (Option) ist eine Leistungsbeschränkung; sie muss im Vertrag/den AGB vorgesehen sein (Zurückbehaltungsrecht, § 320 BGB) und nach Zahlung sofort enden (macht das Portal automatisch). Standardmäßig aus.
- Rolle Empfang und befristete Zugänge: Zugriffsbeschränkung nach dem Erforderlichkeitsprinzip; Enddatum wird erzwungen, Vorgänge stehen im Audit-Log.
