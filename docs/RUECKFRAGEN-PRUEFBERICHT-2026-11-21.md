# Prüfbericht „bericht.pdf“ vom 21.11.2026: Umsetzung und Antworten auf die Rückfragen

Grundlage: automatisierter Website-Prüfbericht (Regelkatalog 0.1.0, 101 Seiten, **0 technische Fehler**, 4 Risiken, 2 Verbesserungen, 16 Rückfragen, 4 Fragen an den Anwalt, 60 Punkte unauffällig). Der Bericht ersetzt keine Rechtsberatung. Diese Datei hält fest, was geändert wurde, was ein Fehlalarm ist und welche Antworten nur Sie geben können.

## Umgesetzt

| Befund | Änderung |
|---|---|
| Risiko: Impressum und Datenschutz nicht von jeder Seite erreichbar (9 Seiten) | Die 8 Beispielseiten (`/beispiel/…`) haben im Fuß jetzt Links auf Impressum und Datenschutz von Markentrix. Die Karte (`/karte`) zeigt beide Links unter der Karte (in der Einbettung auf `/referenzen` bleibt sie ausgeblendet, dort gibt es den Fuß der Seite). |
| Risiko: Datenschutzhinweis am Formular (4 Beispielformulare) | Alle Beispielformulare tragen vor dem Knopf den Hinweis „Beispielformular: Es werden keine Daten gesendet. Datenschutz“ mit Link. Sie senden tatsächlich nichts (`preventDefault`). |
| Risiko: „überholte Angaben: YouTube“ | **Fehlalarm.** Das YouTube-Profil ist im Fuß jeder Seite verlinkt (am Live-Server geprüft), die Datenschutzerklärung nennt es zu Recht in Abschnitt 13a. Keine Änderung. |
| Risiko: Aussagen zu Rechtssicherheit (6 Seiten) | Abgeschwächt: „rechtssicher“ → „Pflichtangaben“ / „datensparsam aufgebaut“ / „im Rahmen der Google-Richtlinien“; „DSGVO-konform“ → „nach den Grundsätzen der DSGVO“; „und rechtlich geprüft“ (Blog Impressum) → „wir empfehlen, die Texte zusätzlich rechtlich prüfen zu lassen“. |
| Verbesserung: interner Link `/karte/` → `/karte` (Weiterleitung) | Link und Einbettung zeigen direkt auf `/karte`. Der Linkcheck des Builds akzeptiert nun Verzeichnisse ohne Schrägstrich. |
| Verbesserung: Überschrift H1 → H3 auf `/karte` | Die Kartenüberschriften sind jetzt H2. |
| Rückfrage Bewertungen: Echtheitsprüfung angegeben? | Unter den Google-Bewertungen steht jetzt: „Die Bewertungen stammen von Google und werden von uns nicht bearbeitet. Ob alle Bewerter Kunden waren, prüfen wir nicht eigenständig.“ (auch im Kurzstreifen ohne Live-Daten). Wenn Sie tatsächlich nur Kunden um Bewertungen bitten, können wir den Satz stärken, sobald Sie das bestätigen. |
| Rückfrage Preise mit Umsatzsteuer: `/kontakt` | Das Feld heißt jetzt „Projektbudget (netto)“. Preise auf Startseite und Landingpages tragen bereits „netto zzgl. USt., Angebot nur für Unternehmer (§ 14 BGB)“. |
| Frage an den Anwalt: Haftungsausschluss im Impressum | Der Absatz „Haftung für Inhalte“ war schon entfernt, jetzt auch die pauschale „Haftung für Links“ (pauschale Distanzierungen gelten als wirkungslos). Übrig sind Urheberrecht und Streitschlichtung; die Überschrift heißt „Urheberrecht und Streitschlichtung“. |
| Rückfrage Schriftlizenzen | Verwendet werden nur Archivo und Source Sans 3 (beide SIL Open Font License). Dokumentiert in `static/fonts/LIZENZEN.md`. Nicht verwendete Altdateien (Inter, Space Grotesk) liegen noch im Ordner. |

## Rückfragen: Antwortvorschläge (bitte prüfen und bestätigen)

1. **Seiten per noindex gesperrt (9):** Das sind die acht Beispielseiten mit fiktiven Betrieben und die Karte. Das ist gewollt, sie sollen nicht bei Google erscheinen.
2. **Ziel-Suchbegriffe (Vorschlag, 10):** webdesign celle · website erstellen lassen celle · landingpage erstellen lassen · seo agentur celle · ki agentur celle · ki telefonassistent celle · whatsapp assistent celle · google unternehmensprofil optimieren · website relaunch ohne rankingverlust · website für handwerker celle. Diese Begriffe stehen in den Titeln, H1 und Beschreibungen der zugehörigen Seiten. Bitte streichen oder ergänzen.
3. **Rechtsform und Name:** Das Impressum nennt „Markentrix, Inhaber: Christian Wien, Rechtsform: Einzelunternehmen“ mit Vor- und Nachname. Das genügt für ein Einzelunternehmen ohne Handelsregister. Der Prüfer erkennt nur Formen wie „e. K.“.
4. **Zielgruppe:** Ausschließlich Unternehmer (AGB § 1 Abs. 2, Pflicht-Bestätigung § 14 BGB in den Formularen).
5. **Verträge zur Auftragsverarbeitung (Hoster, E-Mail-Anbieter, Google Analytics, Metricool):** **Bitte Nachweise bereitstellen** (Dokument und Datum je Dienst ablegen).
6. **Google-Unternehmensprofil (bestätigt, gleiche Daten, aktuelle Fotos?):** Bitte bestätigen.
7. **Registergericht und -nummer:** Nur nötig, wenn ins Handelsregister eingetragen. Bitte bestätigen, dass das nicht der Fall ist (sonst nachtragen).
8. **Aufsichtsbehörde, Kammer, Berufsangaben:** Nur bei erlaubnispflichtiger oder reglementierter Tätigkeit. Webdesign und Marketing sind das in der Regel nicht. Bitte bestätigen.
9. **Referenzen und Kundenstimmen:** Bitte schriftliche Freigaben ablegen (Anadolu Market, Pony Club Lila, ElbDetail, Isabella).
10. **Bild- und Grafiklizenzen (rund 63):** Bitte Liste anlegen (Datei, Quelle, Lizenz oder „eigene Aufnahme“, bei KI-Bildern Tool und Nutzungsbedingungen). Das kann ich auf Wunsch als Vorlage mit allen Dateinamen erzeugen.
11. **Einwilligungen abgebildeter Personen:** Bitte für jede erkennbare Person ablegen (zum Beispiel Isabella, eigenes Porträt).
12. **Tatsächliche Löschfristen:** siehe `docs/RECHTSPRUEFUNG-UMSETZUNG-2026-11-21.md` (M10). Es braucht einen echten Löschlauf, der mit dem Text übereinstimmt.
13. **Erklärung zur Barrierefreiheit / Barrierefreiheitsstärkungsgesetz:** Nur relevant bei Verträgen mit Verbrauchern über die Seite. Das Angebot ist rein B2B, und für Kleinstunternehmen (unter 10 Beschäftigte, höchstens 2 Mio. € Jahresumsatz) gilt bei Dienstleistungen eine Ausnahme. Bitte Beschäftigtenzahl und Umsatzgrenze bestätigen.
14. **Verzeichnis der Verarbeitungstätigkeiten (Art. 30 DSGVO):** Empfehlung: ja führen. Eine Vorlage mit den vorhandenen Verarbeitungen (Formulare, Statistik, Portal, KI, Vertrieb, Bewerbungen) kann ich aus der Datenschutzerklärung ableiten.

## Fragen an den Anwalt (unverändert offen)

- Reicht die Beschränkung auf Unternehmer, um Nettopreise ohne Umsatzsteuer zu nennen?
- Dürfen die jetzt abgeschwächten Aussagen zu Datenschutz und Barrierefreiheit so stehen, oder soll eine andere Formulierung gelten?
- Barrierefreiheitsstärkungsgesetz: Greift bei uns die Ausnahme für Kleinstunternehmen?
- AGB-Entwürfe M04 bis M06 (siehe die andere Dokumentation).
