# Prüfbericht vom 21.11.2026: Stand der Umsetzung

Grundlage: „ElbDetail Prüfbericht & Arbeitsauftrag“ (Version 1.0). Keine anwaltliche Freigabe. Geänderte Rechtstexte sind Entwürfe und müssen vor dem Livegang anwaltlich geprüft werden.

| Punkt | Prio | Stand | Was geändert wurde bzw. was fehlt |
|---|---|---|---|
| A01 Zahlungspflicht benennen | P1 | **umgesetzt** | Gutschein-Knopf „Zahlungspflichtig bestellen“ (EN „Order with obligation to pay“). Direkt darüber eine Bestellübersicht: Gutscheinart, Leistung, Fahrzeugklasse (bei Paket), Zustellung, Gesamtpreis, Hinweis § 19 UStG, Gültigkeit, Zahlungsweg. Sie folgt jeder Auswahl. Dateien: `build/conversion.py`, `static/script.js`, `static/styles.css`. |
| A02 Fahrzeugklasse Paketgutscheine | P2 | **umgesetzt** | Auswahl zeigt jetzt „Refresh (Kleinwagen, Wert 79 €)“ usw. statt „Kompakt“. Preis, Vorschau, Übersicht und AGB § 11 nennen einheitlich den Kleinwagen. Übermittelt wird wie bisher der Paket-Schlüssel. |
| A03 Vertragsschluss und Anzahlung | P2 | **offene Entscheidung** | Siehe unten. Nichts am Ablauf geändert. |
| A04 Analytics-Widerruf | P1 | **Portal-Aufgabe** | Ursache liegt im gemeinsamen Portal-Skript. Befund und Code-Vorschlag in `docs/portal-aufgaben.md`, Abschnitt 1. Wirkt auf alle Kundenwebsites. |
| A05 Datenschutz an Dienste anpassen | P1 | **umgesetzt, 3 Angaben offen** | Neuer Abschnitt 4 „Google Analytics (nur mit Einwilligung)“: Anbieter, Zweck, Daten, Cookies `_ga`/`_ga_…` (bis 2 Jahre, Standard von gtag.js), Empfänger, USA/Data Privacy Framework, Widerruf. Abschnitt 4a „Zählung ohne Cookies“ ohne „anonym“, mit IP-Hinweis. Abschnitt 3 ohne die falsche Aussage „keine Skripte von Drittanbietern“, Speicherort auf Website/Portal begrenzt. Offen (erscheinen automatisch, sobald in `content/site.json → legal` gesetzt): `avContract` (AV-Vertrag mit Markentrix), `analyticsDpa` (Datenverarbeitungsbedingungen in GA akzeptiert), `analyticsRetentionMonths` (2 oder 14). Bis dahin nennt die Seite diese Punkte nicht. |
| A06 Widerruf ohne Einwilligung | P1 | **umgesetzt, Portal muss mitziehen** | Kein Einwilligungs-Häkchen mehr, dafür Datenschutzhinweis (Art. 6 Abs. 1 lit. c). Vorgangsnummer **oder** Beschreibung des Vertrags genügt, Name und E-Mail bleiben Pflicht. Portal muss `typ=widerruf` ohne `einwilligung` annehmen und die Bestätigung mit Inhalt, Datum und Uhrzeit senden (`docs/portal-aufgaben.md`, Abschnitt 2). |
| A07 Einwilligungsmodell der Formulare | P2 | **umgesetzt** | Häkchen-Text jetzt „Datenschutzhinweise zur Kenntnis genommen …“ statt Einwilligung; Datenschutz Abschnitt 5 erklärt das. Feldname `einwilligung` bleibt, weil das Portal ihn erwartet. Keine Werbe- oder Bewertungs-Einwilligung vorhanden. |
| A08 Kontaktwege und Datentransfers | P2 | **umgesetzt** | WhatsApp, Google-Links (Route, Bewertungen), PayPal und soziale Netzwerke: Unterschied zwischen Anzeige des Links, Klick (Verbindungsdaten) und Nachricht. |
| A09 Geschuldeter Leistungserfolg | P2 | **Entwurf, Anwalt** | AGB § 2 Abs. 2: Pauschale „Ergebnis nur bei ausdrücklicher Vereinbarung“ ersetzt durch: fachgerechte Ausführung des Pakets mit dem beim Ausgangszustand erreichbaren Ergebnis, Hinweis auf erkannte Grenzen vor Arbeitsbeginn, Mängelrechte bleiben. |
| A10 Ausfallpauschale | P2 | **offene Entscheidung** | Klausel unverändert. Siehe unten. |
| A11 Haftungsverweise Impressum | P2 | **umgesetzt** | Blöcke „Haftung für Inhalte“ (§§ 7–10 DDG) und „Haftung für Links“ entfernt. Name, Anschrift, Kontakt, § 19 UStG, § 18 MStV bleiben. |
| A12 Aufbewahrung und Leistungsdauer | P2 | **umgesetzt** | Datenschutz: Buchungsbelege 8 Jahre, Handels- und Geschäftsbriefe 6 Jahre (§ 147 AO, § 257 HGB), danach Löschung. Scheibenkeramik: FAQ auf der Preisseite und AGB § 7 nennen jetzt etwa 1 Stunde statt 3 Tage. |
| A13 Nachweise | P3 | **offen (Betreiber)** | Siehe unten. |
| A14 Barrierefreiheitspflichten | P3 | **offen (Betreiber)** | Siehe unten. |

Alle Änderungen gelten auch für die englische Fassung (`content/i18n/en/legal-2026-11.json`, Varianten für die drei Schalter in `varianten-datenschutz.json`).

## Offene Entscheidungen

**A03 Vertragsschluss und Anzahlung.** Heute: Das Portal meldet `selfBooking: false`, der Knopf heißt „Terminwunsch senden“. AGB § 3: Vertrag kommt mit unserer Terminbestätigung zustande. AGB § 5 und Danke-Seite: Der PayPal-Link für die Anzahlung kommt **direkt nach dem Absenden**, also vor der Bestätigung („sichern Sie sich Ihren Termin“). Das passt nicht zusammen. Zwei saubere Wege:
1. *Vorschlag aus dem Prüfbericht:* Anfrage → Angebot mit Preis → ausdrückliche Annahme → erst dann Anzahlung. Dann zeigt die Danke-Seite keinen Zahlungslink mehr, René schickt ihn mit der Bestätigung. AGB § 5 Satz 2 entsprechend.
2. Direkte Buchung (`selfBooking: true`) mit Vertragsschluss beim Absenden. Dann Knopf „Zahlungspflichtig buchen“, Preis und Anzahlung vorher verbindlich, AGB § 3 anpassen.
Bitte entscheiden. Die Website setzt danach Texte, Danke-Seite und AGB einheitlich um.

**A10 Ausfallpauschale.** Für die Höhe (einbehaltene Anzahlung von 15 % des Richtpreises) fehlen Angaben: üblicher tatsächlicher Ausfall (frei gehaltene Zeit, Wiederbelegung, ersparte Material- und Arbeitskosten), typischer Vorlauf von Absagen. Bitte von René erfragen und mit dem Anwalt prüfen.

## Nachweise beim Betreiber (A13)

- Nutzungsrechte: Herstellerbilder C²Coating (Hero, Keramik), Logos der 5 Referenzfirmen (Freigabe liegt laut René vor, bitte schriftlich ablegen), Porträt René, Vorher/Nachher-Bilder.
- Partnerschaft „C²Coating Excellence Partner“ und Koch-Chemie-Schulungen: Zertifikate liegen vor, Stand prüfen.
- Bewertungszitate: Herkunft (Google-Profil) und Wortlaut belegbar halten, Echtheitshinweis bleibt.
- Haltbarkeitsangaben (bis 100.000 km, bis 15.000 km): Herstellerangaben belegen. Durchgestrichene Preise der Scheiben-Aktion (149 € → 99 €, 179 € → 114 €): laut Betreiber am 21.11.2026 belegbar, Durchstreichung bleibt. Belege (Rechnungen oder Preisliste mit Datum) ablegen. Nach § 11 PAngV muss der gestrichene Preis der niedrigste Preis der 30 Tage vor Aktionsbeginn (21.10.2026) sein.
- AV-Vertrag mit Markentrix, Datenverarbeitungsbedingungen in Google Analytics, Speicherdauer in GA (siehe A05).

## Barrierefreiheit (A14)

Ob das Barrierefreiheitsstärkungsgesetz gilt, hängt von Beschäftigtenzahl und Umsatz ab (Ausnahme für Kleinstunternehmen unter 10 Beschäftigten und höchstens 2 Mio. € Umsatz oder Bilanzsumme). Die Kleinunternehmerregelung nach § 19 UStG ist etwas anderes. Bitte die Zahlen von René erfragen. Unabhängig davon prüfen die Browser-Tests Tastaturbedienung, Fokus, Feldbeschriftungen und axe-Regeln (WCAG 2.1 AA) auf den geänderten Seiten.
