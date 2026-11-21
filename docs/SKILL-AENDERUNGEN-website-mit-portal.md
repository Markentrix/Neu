# Änderungen am Skill „website-mit-portal“ (V4.2 → V4.3), 21.11.2026

Der Skill für Kundenwebsites wurde um die Lehren aus markentrix.de ergänzt, damit Kundenseiten von Anfang an stimmen. Die vollständige Fassung liegt in der lokalen Skill-Datei dieser Umgebung (Sicherungen der alten Fassungen im Scratchpad). Ob die Änderung in Ihr Claude-Konto zurückgespielt wird, ist nicht bestätigt: Bitte in der Skill-Verwaltung prüfen. Die Abschnittsnummern sind unverändert.

| Abschnitt | Neu |
|---|---|
| 3 Datenschutz | Pflichtlinks Impressum und Datenschutz auf **jeder** Seite, Datenschutz-Satz am Absenden-Knopf; Zielgruppe B2B oder B2C vor dem Bau klären (B2B: Pflicht-Checkbox Unternehmer § 14 BGB, „netto“ am Preis; B2C: Bruttopreise, Widerruf, BFSG prüfen lassen); keine pauschale Haftung-für-Links; keine Zusagen („rechtssicher“, „DSGVO-konform“, „rund um die Uhr“, „24/7“, „jederzeit“); Datenaussagen nur gemessen oder belegt; Bewertungen mit Herkunftshinweis und Stand; Referenzen, Personen, Bilder nur mit Nachweis (sonst „OFFEN:“); befristete Angebote mit Ablaufdatum und Neuauslieferung. |
| 7 Lokales SEO | H1 mit Suchbegriff vorn, höchstens 70 Zeichen, Unterzeile nie im H1 (auch Leerzeichen vor `<br>`), keine übersprungenen Ebenen, Zwischenüberschriften mit Themenwort; 5 bis 10 Suchbegriffe, je Begriff eine Zielseite (Tabelle im Bericht); Description 70 bis 160; Startseite einheitlich mit Schrägstrich. |
| 8 Performance und Barrierefreiheit | axe-core (WCAG 2.2 AA, Best Practice) bei 390 und 1440 px; Karten verlinken nur die Überschrift, Linktext höchstens 70 Zeichen und eindeutig, `rel="nofollow"` bei Parametern, externe Verweise prüfen; Bilder mit alt, width, height, Zierbilder per CSS; keine unzulässigen `role` auf Links; `<main>` auf jeder Seite. |
| 12 Prüfliste | Punkt 4 geschärft, neuer Punkt 25 (Qualitäts-Gate). |
| 13 Bericht | E „1–25“; I „OFFEN:“ um Nachweise des Kunden und die B2B/B2C-Entscheidung erweitert. |
| 18 Prüfskript | Zweites, Pflicht-Skript `qa-statisch.py` (Python, ohne Netz) mit 20 Prüfungen. Kopie im Repo: `tools/qa-statisch-kundenseiten.py`. |
| 20 Änderungsauftrag | Gate auch nach Änderungen. |

Getestet wurde `qa-statisch.py` an einer absichtlich fehlerhaften Beispielseite (13 Fehler erkannt) und an einer korrekten (0 Fehler). Ein Fehler im ersten Entwurf (Leerzeichen beim Tag-Entfernen versteckte zusammengeklebte H1-Sätze) wurde dabei gefunden und behoben, ebenso in `tools/qa.py` der eigenen Seite. Nicht getestet: Lauf an einer echten Kundenseite.

Zusätzlich: `website-mit-portal-shop` verweist am Ende auf das Gate.
