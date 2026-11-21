# Umsetzung Prüfbericht „Website-Prüfung und Arbeitsauftrag“ (M01 bis M16)

Grundlage: `Markentrix_Pruefbericht_Arbeitsauftrag_Claude_Code.pdf`, Prüfstand 21.11.2026, Version 1.0.
Stand dieser Umsetzung: 21.11.2026. Dies ist eine technische und redaktionelle Umsetzung, **keine anwaltliche Freigabe**. Nicht als „jetzt rechtssicher“ zu verstehen. Texte unter „Entwurf“ sind fachlich zu prüfende Vorschläge und **nicht** auf der Website veröffentlicht.

## Übersicht

| Nr. | Prio | Thema | Status |
|---|---|---|---|
| M01 | P1 | Abgelaufene Einwilligung überall beachten | erledigt |
| M02 | P1 | GA4-Cookie-Laufzeit und Datenaufbewahrung trennen | Text erledigt, Kontowert offen (Betreiber) |
| M03 | P2 | Metricool und Widerruf nachweisen | Messung erledigt, Verträge/Fristen offen (Betreiber) |
| M04 | P1 | Abnahmeklausel | Entwurf, Entscheidung offen |
| M05 | P1 | Haftungsgrenze, Freistellung | Entwurf, Entscheidung offen |
| M06 | P2 | Vertragsende, Export, Nutzungsrechte | Entwurf, Entscheidung offen |
| M07 | P1 | Leistungsversprechen begrenzen | erledigt (Texte zur Freigabe), Betriebsabgleich offen |
| M08 | P2 | Aktionspreise eindeutig | Text und Fristende erledigt, Bestätigung offen (Betreiber) |
| M09 | P2 | Impressum aktualisieren | Haftungsblock entfernt, USt-IdNr. offen (Betreiber) |
| M10 | P2 | Widersprüche in Datenschutzangaben | teilweise erledigt, Fristen offen (Betreiber) |
| M11 | P1 | B2B-Akquise kanalbezogen | nur Text (§ 9) und Entscheidungsvorlage; Prozess liegt im Portal |
| M12 | P2 | KI-Datenflüsse belegen | nur Entscheidungsvorlage und Prüfliste |
| M13 | P2 | Formulare und Portal-Check konsistent | Pflichtfeldhinweis erledigt, Portal-Befund offen |
| M14 | P3 | Referenzen und Bewertungen belegen | Anzeige-Stand erledigt, Nachweise offen (Betreiber) |
| M15 | P3 | Website-Check und Rechner einordnen | erledigt |
| M16 | P3 | B2B-Abgrenzung bis Vertragsschluss | nur Entscheidungsvorlage |

## M01 · Einwilligung: Gültigkeit überall prüfen (erledigt)

- Dateien: `static/assets/consent.js`, `static/assets/site.js`.
- Änderung: `read()` in `consent.js` prüft jetzt Version 2, Zeitstempel als Zahl, nicht in der Zukunft, höchstens 6 Monate alt und `analytics` als Wahrheitswert. `site.js` (`consentOk()`) nutzt diese eine Prüfung (`window.mxConsent.analytics()`), ohne eigene zweite Logik. `mx-utm` wird bei Ablehnung, Widerruf, Ablauf, alter Version und beschädigtem Eintrag entfernt. Der abgelaufene Eintrag selbst bleibt als Nachweis der früheren Entscheidung gespeichert (wird nicht mehr als Zustimmung gewertet); das Banner fragt neu.
- Test (lokal, simulierter Browser, 9 Fälle): kein Eintrag, Zustimmung aktuell, Ablehnung, abgelaufen (200 Tage), alte Version, ohne Zeitstempel, Zeitstempel in der Zukunft, `analytics` als Text, beschädigtes JSON. Ergebnis: Nur bei „Zustimmung aktuell“ laden Tracker (4 Anfragen) und werden Herkunftsdaten angehängt. In allen anderen Fällen: Banner sichtbar (außer bei aktueller Ablehnung), 0 Tracker-Anfragen, kein `mx-utm`, keine Herkunftsdaten im Formular. Das Absenden und die notwendigen Funktionen laufen in jedem Fall weiter.
- Verbleibend: Test auf echten Geräten und in Safari/Firefox nicht durchgeführt.

## M02 · GA4-Cookie-Laufzeit und Datenaufbewahrung (Text erledigt)

- Dateien: `static/assets/consent.js` (Banner-Details), `src/pages/datenschutz.html` § 12.
- Messung (Chromium, nach Zustimmung): Cookies `_ga` und `_ga_<ID>` mit rund **400 Tagen** Restlaufzeit. Das ist die Browser-Obergrenze (Chromium begrenzt Cookies auf 400 Tage), nicht die Google-Voreinstellung (zwei Jahre). Andere Browser können weiter kürzen.
- Änderung: Aussage „bis 14 Monate“ ersetzt durch „nach Google-Voreinstellung bis zu zwei Jahre, Browser können die Laufzeit begrenzen (Test mit Chromium rund 400 Tage)“. Die Aussage „Daten werden nach 14 Monaten gelöscht“ ersetzt durch die Aufbewahrungsdauer **im Google-Analytics-Konto** als getrennte Einstellung; aggregierte Standardberichte sind nicht betroffen.
- **Offen (Betreiber):** In GA4 unter Verwaltung → Datenspeicherung die tatsächlich eingestellte Dauer für Ereignisdaten ablesen (2 oder 14 Monate). Sie ist im Text bewusst nicht als Zahl genannt. Wenn Sie den Wert nennen, trage ich ihn ein.
- Nicht getestet: Safari- und Firefox-Laufzeiten.

## M03 · Metricool und Widerruf (Messung erledigt)

Messung (frischer Browser, Chromium), Anfragen an Fremddomains und Speicher:

| Schritt | Anfragen an Dritte | Cookies | Speicher |
|---|---|---|---|
| vor der Entscheidung | keine | keine | `mx-a11y-scale` (lokal) |
| nach „Alle akzeptieren“ | tracker.metricool.com (2), googletagmanager.com, google-analytics.com | `_ga`, `_ga_<ID>` (je ca. 400 Tage) | `mx-consent` |
| Folgeseite mit Zustimmung | tracker.metricool.com (2), googletagmanager.com | wie oben | wie oben |
| nach Widerruf (Statistik aus, Seite neu geladen) | keine | **keine** (GA-Cookies entfernt) | `mx-consent` (Ablehnung) |
| Folgeseite nach Widerruf | keine Tracker (nur `portal.markentrix.de` für den Terminkalender auf `/kontakt`) | keine | wie oben |

- Metricool setzt auf `markentrix.de` keine Cookies und legt keine eigenen Browser-Speichereinträge an (gemessen). Das Skript lädt nur nach Zustimmung und nach Widerruf nicht mehr.
- Änderung: § 12 nennt Speicherdauer-Kriterien (Einstellungen des Metricool-Kontos und Angaben von Metricool) und das Verhalten beim Widerruf.
- **Offen (Betreiber):** Metricool-AVV und Angabe, wo und wie lange die Daten liegen (die Aussage „Verarbeitung innerhalb der EU“ ist nicht belegt), Liste der Unterauftragnehmer von Metricool.
- Nicht getestet: Löschung bereits übermittelter Daten beim Anbieter.

## M04 · Abnahmeklausel (AGB § 7 Abs. 1) — Entwurf, nicht veröffentlicht

Befund: Die Klausel lässt die Abnahme gelten, wenn nicht „wesentliche Mängel“ benannt werden oder die Leistung „produktiv genutzt“ wird. § 640 Abs. 2 BGB verlangt eine angemessene Frist und die Verweigerung unter Angabe **mindestens eines Mangels**; auch die Pflicht zur Abnahme trotz unwesentlicher Mängel (§ 640 Abs. 1 Satz 2 BGB) ist davon zu unterscheiden.

**Entwurf (anwaltlich zu prüfen):**
> (1) Nach Fertigstellung einer Projektleistung teilt Markentrix dem Kunden die Fertigstellung mit und fordert ihn in Textform zur Abnahme auf. Dafür setzt Markentrix eine angemessene Frist, in der Regel 10 Werktage ab Zugang der Aufforderung; bei umfangreichen Projekten eine längere, im Angebot genannte Frist.
> (2) Verweigert der Kunde die Abnahme, hat er innerhalb der Frist in Textform mindestens einen Mangel zu benennen. Ob der Mangel wesentlich ist, prüfen die Parteien anschließend gemeinsam; Markentrix beseitigt berechtigt gemeldete Mängel. Die Abnahme darf wegen unwesentlicher Mängel nicht verweigert werden.
> (3) Benennt der Kunde innerhalb der Frist keinen Mangel und verweigert er die Abnahme nicht, gilt die Leistung als abgenommen. Darauf weist Markentrix in der Aufforderung gesondert hin (§ 640 Abs. 2 BGB).
> (4) Die produktive Nutzung (zum Beispiel Livegang auf Wunsch des Kunden) ersetzt für sich genommen keine Abnahme.

Entscheidung offen: Frist (10 Werktage je Projekt angemessen?), Wortlaut der Aufforderung, Abstimmung mit Angebot, Abnahmeformular, Erinnerung und Fälligkeit der Rechnung. Prozess und Vorlagen im Portal liegen nicht in diesem Repository.

## M05 · Haftung und Freistellung (AGB § 6 Abs. 2, § 14) — Entwurf

Befund: § 14 Abs. 2 begrenzt die Haftung bei leichter Fahrlässigkeit auf „höchstens die Vergütung der letzten 12 Monate“. Bei neuen Verträgen oder typischen Schäden aus Hosting, Datenverarbeitung und KI-Betrieb kann das zu niedrig oder unklar sein. § 6 Abs. 2 (Freistellung) ist weit gefasst. Im B2B-Bereich gilt § 307 BGB über § 310 BGB; §§ 308, 309 BGB nicht schematisch.

Variantenvorschlag (keine Summe erfunden):
- A) Haftungsgrenze **je Schadensfall** mit Untergrenze; der Betrag ist Entscheidung von Ihnen mit Anwalt/Versicherung (zum Beispiel an Ihre Betriebshaftpflichtdeckung angelehnt).
- B) Getrennt nach Leistungsart: Projektleistung (Bezug: Projektvergütung) und laufende Leistung (Bezug: Vergütung der letzten 12 Monate, bei kürzerer Laufzeit die auf 12 Monate hochgerechnete Vergütung).
- Freistellung (§ 6 Abs. 2) einschränken auf Ansprüche, die auf vom Kunden gelieferten Inhalten beruhen, mit Pflicht zur unverzüglichen Mitteilung und Abstimmung der Rechtsverteidigung.
- Gesetzlich zwingende Haftung (Vorsatz, grobe Fahrlässigkeit, Leben/Körper/Gesundheit, Produkthaftung) bleibt wie in § 14 Abs. 1. Wesentliche Vertragspflichten dürfen nicht wirtschaftlich ausgehöhlt werden.

Entscheidung offen: Variante und Betrag. Ein Textentwurf ist ohne diese Angaben nicht sinnvoll; bitte mit Anwalt.

## M06 · Vertragsende, Export, Nutzungsrechte (AGB §§ 9, 11; Preise, Portal) — Entwurf

Befund: § 9 Abs. 4: Deaktivierung, Datenherausgabe „auf Wunsch innerhalb von 30 Tagen“, danach Löschung. Unklar: Anforderungsfrist, Zeitpunkt der Abschaltung, Abgrenzung Kundendaten, Domain, individuelle Website-Dateien und nur während der Laufzeit nutzbare Komponenten (§ 11 Abs. 2).

**Entwurf (anwaltlich zu prüfen):**
> Der Kunde kann bis zum Vertragsende und bis zu 14 Tage danach in Textform den Export seiner Daten verlangen. Markentrix stellt innerhalb von 30 Tagen nach der Anforderung bereit: (a) die Inhalte der Website (Texte, Bilder, Seitenstruktur als Datei-Export), (b) die über die Website eingegangenen Anfragen und Kontakte in einem gängigen Format (CSV), (c) Auftragsverarbeitungsdaten nach Art. 28 DSGVO. Die Domain gehört dem Kunden und wird auf Wunsch umgezogen. Die Systeme werden zum Vertragsende deaktiviert. Nach Bereitstellung oder nach Ablauf der Anforderungsfrist löscht Markentrix die Daten, soweit keine gesetzlichen Aufbewahrungspflichten bestehen.
> Das Nutzungsrecht an den individuell erstellten Arbeitsergebnissen (§ 11 Abs. 1) besteht nach vollständiger Zahlung unabhängig vom Fortbestehen des Hostings. Vorlagen, Workflows, Prompts, Konfigurationen und Werkzeuge (§ 11 Abs. 2) bleiben bei Markentrix und sind nach Vertragsende nicht nutzbar.

Entscheidung offen: Exportumfang, Fristen, ob Zusatzleistungen (Umzug) berechnet werden. Abnahme: Testexport mit fiktiven Daten, vollständig und nutzbar vor endgültiger Löschung; Portal und AGB müssen denselben Umfang beschreiben (liegt im Portal, nicht hier).

## M07 · Leistungsversprechen (erledigt, Texte zur Freigabe)

Geänderte Texte (vorher → nachher):
- `leistungen/webdesign`: „Rechtssicher und barrierefrei – DSGVO-konform … für alle“ → „Impressum, Datenschutz und Lesbarkeit – … Eine rechtliche Prüfung und eine vollständige Barrierefreiheit sind nur im vereinbarten Umfang enthalten.“
- `portal`: Überschrift „Ihre Daten bleiben in Deutschland.“ → „Hosting in Deutschland, Datenschutz nachvollziehbar.“ Ergänzt: Für einzelne Dienste (E-Mail-Versand, KI-Assistenten, Statistik nur mit Einwilligung) können Anbieter beteiligt sein, die auch außerhalb Deutschlands verarbeiten.
- KI-Seiten: „rund um die Uhr“ → „auch abends und am Wochenende“ / „auch außerhalb der Geschäftszeiten“; „jederzeit an eine Person weitergeleitet/übergeben“ → „nach den vereinbarten Regeln …“; „Nahtlose Übergabe … Sensible Anliegen gehen immer an einen Menschen“ → Regeln werden gemeinsam festgelegt; Überschriften „Immer.“ → „Auch nach Feierabend.“, „Kein Anruf geht verloren.“ → „Auch wenn Sie nicht rangehen können.“; Karte „Nichts geht verloren“ → „Anfragen werden erfasst“.
- Nicht geändert: Datenschutzerklärung § 14 („Auf Wunsch werden Sie jederzeit an eine natürliche Person weitergeleitet“): Das ist eine Transparenzaussage zum Einsatz; sie muss mit dem tatsächlich eingerichteten Verhalten übereinstimmen (siehe M12).
- **Offen (Betreiber):** Abgleich mit dem realen Betrieb: Verfügbarkeit der Assistenten (Zeiten), Übergabe an Menschen (wie, wann), Wissensbindung (Fehlerquote), Hosting-Orte. Die Aussage „Hosting auf einem Server in Deutschland (Hetzner)“ ist nicht von mir verifiziert.

## M08 · Aktionspreise und Fristende (erledigt, Bestätigung offen)

- Dateien: `src/partials/deals.html`, `src/partials/deals-lp.html`, `tools/build.py`, `static/assets/site.js`, `static/api/anfrage.php`.
- Text: „der Rest bequem in zwölf Monatsbeträgen“ entfernt. Jetzt: **Einmalpreis für die Erstellung** und **Monatsbetrag für Hosting, Pflege und Kundenportal** mit Mindestlaufzeit 12 Monate ab Livegang; danach läuft der Vertrag weiter und ist mit einer Frist von **einem Monat zum Monatsende** kündbar (so steht es in AGB § 9 Abs. 1 und 2). Zusatz: „der Monatsbetrag bleibt dabei unverändert, sofern im Angebot nichts anderes vereinbart ist“. Die Jahressummen (958,88 € und 1.577,80 €) sind rechnerisch korrekt und unverändert.
- **Offen (Betreiber, bitte bestätigen):** (1) Sind die Monatsbeträge tatsächlich laufende Leistung (Hosting/Pflege) und **keine** Finanzierung/Ratenzahlung des Einmalpreises? (2) Bleibt der Monatsbetrag ab Monat 13 unverändert? Wenn nein, nenne ich den Wert statt des Zusatzes. (3) Pilotplätze (AGB § 10: „zwei Plätze“) und Einrichtungsrabatt tatsächlich dokumentieren.
- Fristende (30.11.2026, Gültigkeit bis einschließlich): Das Angebot wird nach Fristende **schon beim Bauen** aus dem HTML entfernt (Leiste auf der Startseite, Aktionsabschnitt auf Startseite und Landingpages), nicht nur per Browser-Skript. Das Skript bleibt als zweite Sicherung. `MX_TODAY=2026-12-01 python3 tools/build.py` getestet: Aktion, Preise und Leiste fehlen, Linkcheck ok. Aktionscodes (`landingpage-599`, `website-1099`): Das Formular im Browser übernimmt sie nach Fristende nicht mehr; der Server markiert sie nach Fristende als „abgelaufen, kein Aktionspreis“.
- **Wichtig für Sie:** Die Seite ist statisch. Damit die Aktion nach dem 30.11. wirklich verschwindet, muss ab dem 01.12.2026 **einmal neu gebaut und eingespielt** werden (ZIP). Ohne Neueinspielung entfernt nur das Skript im Browser sie.
- Nicht geprüft: Angebotsvorlage und Portal (liegen außerhalb dieses Repositories).

## M09 · Impressum (erledigt, USt-IdNr. offen)

- Datei: `src/pages/impressum.html`.
- Der Absatz „Haftung für Inhalte“ (übernahm frühere TMG-Aussagen zu §§ 7 bis 10 DDG) ist entfernt. „Haftung für Links“, „Urheberrecht“ und „Streitschlichtung“ sind unverändert; Name, Anschrift, Kontakt bleiben erhalten.
- USt-IdNr.: Zeile weiter „beantragt, wird nach Erteilung hier ergänzt“. Keine Nummer erfunden. **Offen (Betreiber):** erteilte USt-IdNr. (oder Wirtschafts-Identifikationsnummer nach § 5 DDG, falls vorhanden) nennen. Persönliche Steuer-ID und allgemeine Steuernummer nicht ersatzweise veröffentlichen.

## M10 · Widersprüche in den Datenschutzangaben (teilweise erledigt)

- Erledigt (Datei `src/pages/datenschutz.html`):
  - § 11: Die Einträge Einwilligung, Schriftgröße und Kontrast bleiben lokal. `mx-utm` ist als Ausnahme getrennt benannt (nur mit Einwilligung angelegt, nur beim Absenden übertragen).
  - § 17: „acht bzw. zehn Jahre“ präzisiert: Rechnungen und Buchungsbelege acht Jahre (§ 147 AO, § 257 HGB), Bücher und Jahresabschlüsse zehn, Handels- und Geschäftsbriefe sechs Jahre, abweichende Fristen im Einzelfall. **Bitte vom Steuerberater bestätigen lassen.**
- **Offen (Betreiber):** Backup-Frist (Text sagt „feste Frist“, nennt sie nicht), Löschlauf für Anfragen (Text: 12 Monate nach letztem Kontakt) und Eingangsprotokoll (`anfragen.log` wird laut Repository nirgends automatisch gekürzt), E-Mail-Kopien im Postfach, Aufbewahrung der KI-Verläufe bei Anbietern. Keine Fristen erfunden. Bitte die tatsächlichen Löschläufe (Cron, Server) abgleichen oder einrichten lassen.

## M11 · B2B-Akquise (nur Text und Entscheidungsvorlage)

- Datenschutz § 9 ergänzt: Die datenschutzrechtliche Grundlage ersetzt nicht die wettbewerbsrechtlichen Voraussetzungen; Telefon- und elektronische Werbung nur, soweit nach § 7 UWG zulässig.
- Nicht umsetzbar im Repository: Sperrlisten, Lead-Herkunft, Kanalprüfung und Blockieren von Werbe-E-Mails und automatischen Anrufsystemen liegen im Portal beziehungsweise bei Vertriebspartnern.
- Entscheidungsvorlage (Kanalmatrix, **zur rechtlichen Prüfung**):

| Kanal | Mindestanforderung (UWG, DSGVO) | Pflicht im Prozess |
|---|---|---|
| Telefon an Unternehmen | § 7 Abs. 2 Nr. 1 UWG: mindestens mutmaßliche Einwilligung mit konkreten Anhaltspunkten (öffentliche Nummer allein genügt nicht); Art. 6 Abs. 1 lit. f DSGVO | Herkunft und Anhaltspunkt je Lead dokumentieren; Sperrliste vor jedem Anruf |
| E-Mail an Unternehmen | § 7 Abs. 2 Nr. 3 UWG: ausdrückliche vorherige Einwilligung (Ausnahme Bestandskunden § 7 Abs. 3 UWG) | Double-Opt-in oder dokumentierte Einwilligung; sonst kein Versand |
| Brief | Art. 6 Abs. 1 lit. f DSGVO, Widerspruchsrecht | Informationen nach Art. 14 DSGVO beifügen |
| Automatische Anrufsysteme / Bewertungsbitten / Newsletter | ausdrückliche Einwilligung | technisch blockieren ohne gespeicherte Einwilligung |

Offen: Rollen externer Vertriebspartner, Zugriffsbeschränkungen, Art.-14-Informationen. Keine Live-Testkampagne.

## M12 · KI-Datenflüsse und Zusagen (nur Entscheidungsvorlage)

Für die in Datenschutz § 14 genannten Dienste (OpenAI, Anthropic, Retell AI) fehlen im Repository Verträge und Einstellungen. Prüfliste (**Betreiber, Belege einholen**): je Dienst Vertragsgesellschaft, AVV (Datum, Dokument), Unterauftragnehmer, Transfergrundlage (DPF-Zertifizierung geprüft?), Aufbewahrung und Trainingsnutzung (Einstellung im Konto), Löschzeiten für Transkripte und Chatverläufe. Praktisch testen (ohne echte Kunden): KI-Hinweis zu Gesprächsbeginn, Einwilligung zur Aufnahme vor dem Tonmitschnitt, Übergabe an Menschen und Rückruf. Einsatzfälle auf Art. 22 und Hochrisiko-Einordnung begrenzen; bei Gesundheitsdaten (Praxen) gesonderte Anforderungen prüfen. Die Aussage in Datenschutz § 14 „Ab November 2026 setzen wir KI-gestützte Assistenzsysteme ein“ muss zum tatsächlichen Stand passen.

## M13 · Formulare und Portal-Check (Pflichtfeldhinweis erledigt)

- `/kontakt`: Hinweis „Pflicht sind nur Name, E-Mail und Einwilligung“ berichtigt: Pflicht sind Name, E-Mail, die Einwilligung in die Datenverarbeitung und die Bestätigung, dass Sie als Unternehmer handeln.
- Website-Check auf `markentrix.de`: Kurzfassung und freiwillige Kontaktaufnahme sind getrennt (unverändert).
- Portal-Check `portal.markentrix.de/f/website-check`: heute **erreichbar** (200). Im öffentlichen HTML sind nur Name, E-Mail und das Einwilligungskästchen als Pflichtfelder markiert; Firma, Website und (soweit erkennbar) Telefon sind freiwillig. Datenschutz § 6 sagt: „Die Angabe von Name, E-Mail-Adresse, Telefonnummer und Website ist für den Check erforderlich.“ **Widerspruch**, wird im Portal-Code entschieden, nicht hier geändert. Ich habe außerdem keine Formulare abgesendet und keine Einwilligungstexte der Seite lesen können (per JavaScript erzeugt).
- Entscheidung offen: Rechtsgrundlage und Kontakt-Einwilligung; Die Einwilligungs-Checkbox im Kontaktformular („Ich stimme der Verarbeitung zu“) und die Rechtsgrundlage Art. 6 Abs. 1 lit. b DSGVO in Datenschutz § 5 passen nicht sauber zusammen. Variante: Checkbox in einen Hinweis zur Verarbeitung umwandeln und nur für freiwillige Zusätze (zum Beispiel Rückruf-Erinnerung) eine Einwilligung abfragen. Der Server verlangt die Einwilligung derzeit für alle Formulare.

## M14 · Referenzen und Bewertungen (Anzeige erledigt)

- Der Bewertungsstreifen nennt die Anzahl jetzt mit **„Stand November 2026“** (`data-rev-asof`), damit sie nicht dauerhaft aktuell wirkt. Bei der nächsten Pflege Anzahl und Stand zusammen ändern.
- **Offen (Betreiber):** Zustimmungen der Referenzkunden (AGB § 15), Bild- und Logolizenzen, Zitatgrundlagen. Prüfen, ob die Darstellung von Kundenbewertungen den Anforderungen des § 5b Abs. 3 UWG genügt (Hinweis zur Echtheitsprüfung), beide Modulzustände (mit und ohne Live-Daten) testen. Live-Bewertungen brauchen den Google-Schlüssel (noch offen).

## M15 · Website-Check und Rechner (erledigt)

- Website-Check: Unter dem Ergebnis steht jetzt: „Die Wertung ist eine Einordnung nach unserem Prüfkatalog, kein Google-Ranking, keine Zertifizierung und keine Prognose von Anfragen oder Umsatz.“ In den Befunden zu Bewertungen heißt es nicht mehr „Rankingfaktor“, sondern dass Bewertungen bei lokalen Suchen eine Rolle spielen können und für Kunden ein Vertrauenssignal sind.
- Rechner: Bezeichnungen „Rechnerisch entgangener Umsatz“, „Davon rechnerisch zurückholbar“ und „Rechenwert je Monat (Umsatz und Zeit, kein Gewinn)“. Die Modellrechnung und „kein Gewinnversprechen“ standen bereits da.

## M16 · B2B-Abgrenzung bis zum Vertragsschluss (nur Entscheidungsvorlage)

Stand im Repository: AGB § 1 Abs. 2 (nur Unternehmer), Unternehmer-Bestätigung (§ 14 BGB) in vier Formularen, Hinweis „netto, nur für Unternehmer“ an Preisen. Es fehlt der Nachweis **im Angebot und bei der Annahme** (im Portal). Entscheidungsvorlage: Bestätigung „Ich schließe den Vertrag als Unternehmer im Sinne des § 14 BGB für meine gewerbliche oder selbständige berufliche Tätigkeit“ als Pflichtfeld im Angebot/Annahmeformular, mit Datum; ungeprüft bleibt, wenn der Unternehmerstatus erkennbar fehlt (kein Vertragsschluss). Die **Online-Terminbuchung** ist ein Baustein vom Portal (`erstgespraech.js`); dort fehlt die Unternehmer-Bestätigung noch. Bei Kundenwebsites mit Shop oder Verbraucherzugang (BFSG, Widerruf, Bestellprozesse) gesondert bewerten.

## Betreiberangaben und Freigaben (Kurzliste)

1. GA4: eingestellte Datenspeicherdauer (2 oder 14 Monate) und Datenaufbewahrung nachtragen.
2. Metricool: AVV, Speicherort und -dauer, Unterauftragnehmer.
3. Bestätigung M08: Monatsbetrag = Hosting/Pflege (keine Finanzierung), Betrag ab Monat 13; Pilotplätze und Einrichtungsrabatt dokumentieren.
4. USt-IdNr. oder Wirtschafts-Identifikationsnummer (M09).
5. Backup-Frist, Löschläufe für Anfragen und Eingangsprotokoll, Mailkopien, KI-Verläufe (M10).
6. Steuerberater: Aufbewahrungsfristen in § 17 (M10).
7. Anwalt: AGB-Entwürfe M04 bis M06, Texte von M07 und M11.
8. Verträge und Einstellungen der KI-Dienste (M12); reale Funktionen der Assistenten (M07).
9. Portal: Pflichtfeld-Widerspruch Check-Formular (M13), Unternehmer-Bestätigung bei Terminbuchung und im Angebot (M16), Sperrlisten (M11).
10. Zustimmungen und Lizenzen zu Referenzen und Bildern (M14), Google-Schlüssel für Live-Bewertungen.
11. **Ab 01.12.2026 neu bauen und einspielen** (Aktionsende, M08).

## Nicht getestet

- Echte Geräte; Safari und Firefox (Cookie-Laufzeiten, Speicherverhalten).
- Echter Mailversand der Formulare (im Test-Container gibt es keinen Mailserver; der Server verarbeitet und protokolliert).
- Eingeloggte Portalbereiche, persönliche Angebotslinks, Servercode außerhalb dieses Repositories, tatsächliche Löschläufe, Verträge.
- Löschung bereits übermittelter Analysedaten bei Google und Metricool.
- Vollständiges Audit aller Blog- und Ortsseiten.
