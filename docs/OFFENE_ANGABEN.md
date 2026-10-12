# Offene Angaben vor Veröffentlichung

## Stand 23.09.2026 — geklärt
- #1 Hosting: Hetzner Online GmbH, Rechenzentrum DE (Datenschutz 2a). AVV im Hetzner-Konto abschließen!
- #2 Umsatzsteuer: regelbesteuert, keine Kleinunternehmerregelung. USt-IdNr. eintragen, sobald vorhanden.
- #4 KI-Anbieter: OpenAI, Anthropic (Claude), Retell AI (Datenschutz 5a). AVVs/DPAs mit allen dreien abschließen, Transkript-Löschfrist intern festlegen.
- #6 AGB: erstellt (AGB.dc.html), anwaltliche Prüfung empfohlen.
- #7 Frist 31.12.2026: bestätigt.
- #8 BFSG: 1 Person, ca. 110.000 € Umsatz → Kleinstunternehmen; Ausnahme für Dienstleistungen (§ 3 Abs. 3 BFSG) greift.
- #9 Lizenzen: bestätigt.
- Offen: #3 n8n-Region/AVV, #10 Aussage „DSGVO-konform“ nach Abschluss aller AVVs.


Diese Punkte wurden bewusst **nicht** erfunden. Ohne diese Angaben darf die Seite nicht live gehen.

## Rechtlich / datenschutzrechtlich zu klären

| # | Frage | Wo es einzutragen ist | Wer |
| --- | --- | --- | --- |
| 1 | Wer ist der endgültige Hoster, an welchem Standort stehen die Server, und liegt ein AVV nach Art. 28 DSGVO vor? Findet eine Drittlandübermittlung statt und auf welcher Grundlage nach Art. 44 ff. DSGVO? | `Datenschutz.dc.html`, Abschnitt 2a (Platzhalterbox) | DSB |
| 2 | Existiert eine Umsatzsteuer-Identifikationsnummer, oder gilt die Kleinunternehmerregelung nach § 19 UStG? | `Impressum.dc.html` — der Abschnitt wurde entfernt und ist bei vorhandener USt-IdNr. wieder einzufügen | Steuerberater |
| 3 | In welcher Region läuft die n8n-Cloud-Instanz tatsächlich, und liegt dafür ein AVV vor? | `Datenschutz.dc.html`, Abschnitt 4 (Aussage „gehostet in der EU“ derzeit unbelegt) | DSB |
| 4 | Welches KI-Modell und welcher Anbieter stehen hinter den Agenten? Werden Eingaben zum Training verwendet? Wie lange werden Telefontranskripte gespeichert? Findet eine Drittlandübermittlung statt? | `Datenschutz.dc.html`, Abschnitt 5a — derzeit nur allgemein formuliert | DSB |
| 5 | Werden Verträge ausschließlich mit Unternehmern geschlossen? Die Seite ist jetzt durchgehend als B2B-Angebot gekennzeichnet — das muss der tatsächlichen Praxis entsprechen, sonst greifen PAngV, Widerrufsrecht und Informationspflichten. | Preis-Sektion, Footer, FAQ, Meta-Daten | Anwalt |
| 6 | AGB und Leistungsbeschreibung für 12-Monats-Laufzeit, Einrichtungsgebühren, Minutenpreise und Fair-Use fehlen vollständig. | neue Seite `/agb`, Verlinkung im Footer | Anwalt |
| 7 | Ist die Aktionsfrist „Einführungskonditionen bis 31.12.2026“ real, und gelten danach tatsächlich andere Preise? | Preis-Sektion; erst danach `priceValidUntil` im JSON-LD setzen | Geschäftsführung |
| 8 | Mitarbeiterzahl und Jahresumsatz — entscheidend für die Kleinstunternehmen-Ausnahme des BFSG (§ 3 Nr. 9 BFSG) und § 36 VSBG. | Bewertung der BFSG-Pflicht | Anwalt |
| 9 | Rechte am Hero-Video und Weblizenzen der eingesetzten Schriften (Inter, Space Grotesk). | Nachweis zu den Akten | Geschäftsführung |
| 10 | Ist die Werbeaussage „DSGVO-konform“ nach Klärung von Punkt 1, 3 und 4 haltbar? | Meta-Daten, Hero, FAQ | Anwalt |

## Technisch außerhalb dieses Editors zu erledigen

| # | Aufgabe | Ziel |
| --- | --- | --- |
| A | Hero-Video `videos/markentrix_hero_background.webm` neu kodieren | derzeit 4,59 MB → unter 1,5 MB (z. B. `ffmpeg -c:v libvpx-vp9 -crf 40 -b:v 0 -an`) |
| B | Schriften nach WOFF2 konvertieren und auf Latin subsetten | fünf TTF-Dateien, Inter 400 allein 335 KB → je unter 40 KB; danach `fonts/fonts.css` auf `.woff2` umstellen |
| C | MP4-Fallback erzeugen (optional) | die tote `<source>`-Zeile wurde entfernt; WebM deckt alle aktuellen Browser ab |
| D | n8n-Workflow absichern | serverseitige Feldvalidierung, Rate-Limit pro IP, Signatur- oder Token-Prüfung am Webhook `markentrix-anfrage` |
| E | Messungen am Live-System | Lighthouse mobil (LCP/INP/CLS), `curl -I` für Header, NVDA- oder VoiceOver-Durchgang, Zoom 200 % auf echtem Gerät |


## Nachgetragen 07.10.2026 (entfernte Quellcode-Kommentare)
- USt-IdNr.: Zeile in dist/impressum.html nach "Deutschland" ergänzen: `Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: DE…` (§ 5 Abs. 1 Nr. 6 DDG).
- Fallstudien-Vorlage (Ausgangslage, Vorgehen, Ergebnis mit Kennzahlen und Zeitraum, Zitat nur mit schriftlicher Freigabe) in dist/referenzen.html, sobald ein Projekt freigegeben ist.
