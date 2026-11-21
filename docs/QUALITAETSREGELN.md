# Qualitätsregeln für markentrix.de

Diese Regeln sind aus echten Fehlern und Prüfberichten entstanden (Stand 21.11.2026). Wo es geht, prüft sie `python3 tools/qa.py` automatisch. Ohne grünes Gate wird kein Paket gebaut (`tools/paket.sh`).

## Ablauf vor jeder Auslieferung

1. Ändern, dann `python3 tools/build.py`.
2. `python3 tools/qa.py` (Build, Linkcheck, SEO-Audit, Crawl-Audit, Regeln unten). Muss mit „0 Fehler“ enden. Hinweise ansehen.
3. Browser-Tests, wenn Skripte, Formulare, Einwilligung oder Layout betroffen sind: `tools/browser_tests/` (axe auf allen Seiten, Einwilligung in neun Zuständen, Tracking, Formulare). Aufruf siehe Kopfzeile der Skripte (`PW_DIR`, `AXE_PATH`, `BASE`).
4. Nachtrag in `docs/PRUEFBERICHT.md` (was geändert, was geprüft, was nicht).
5. Commit, dann `tools/paket.sh <Zielordner>`.
6. Ungetestetes ausdrücklich nennen. Nie „rechtssicher“ oder „perfekt“ zusagen.

## Regeln

| Bereich | Regel | Automatisch |
|---|---|---|
| Überschriften | Genau eine H1 je Seite. Das Such-Keyword (Thema, bei Ortsseiten mit Ort) steht am Anfang der H1, höchstens 70 Zeichen. Die Unterzeile gehört **nicht** ins H1-Element (sonst fehlt das Leerzeichen und die H1 wird zu lang), sondern in einen eigenen Absatz. Keine Ebene überspringen. | ja |
| Zwischenüberschriften | Nicht „Passend dazu.“ oder „Kurz beantwortet.“, sondern mit Themenwort („Passend zu SEO und GEO.“). | Hinweis |
| Titel, Beschreibung | Title höchstens 65 Zeichen, Description 70 bis 160. Je Seite eindeutig. Startseite überall mit Schrägstrich: `https://markentrix.de/` (Canonical, `og:url`, Sitemap). | ja |
| Suchbegriffe | Je Suchbegriff eine Zielseite. Der Begriff steht dort in Title, H1 und im ersten Absatz. Liste und Zuordnung in `docs/` pflegen. Zwei Seiten nicht auf denselben Begriff ansetzen. | nein |
| Links | Interne Links mit `?` bekommen `rel="nofollow"`. Linktext höchstens 70 Zeichen und eindeutig (nicht dreimal „Zur Referenz“). Karten verlinken **nur die Überschrift** (macht `card_links` im Build, die ganze Karte bleibt klickbar). Externe Links regelmäßig prüfen (`crawl_audit.py`, Hilfeseiten ändern sich). `target="_blank"` mit `rel="noopener"`. | ja |
| Bilder | Jedes Bild mit Alt-Text sowie Breite und Höhe. Zierbilder nicht als `<img alt="">`, sondern als CSS-Hintergrund. | teils |
| Barrierefreiheit | axe (WCAG 2.2 AA und Best Practice) auf allen Seiten, 390 und 1440 px, ohne Verstoß. Keine `role` auf Links, die der Link nicht erlaubt. Jede eigenständige Seite (auch Einbettungen) mit `<main>`. | Browser-Test |
| Pflichtlinks | **Jede** Seite verlinkt Impressum und Datenschutz, auch Beispielseiten und die Karte. Beispielformulare tragen den Hinweis „Es werden keine Daten gesendet“ mit Link zum Datenschutz. | ja |
| Formulare | Kontakt, Rückruf, Website-Check und Bewerbung haben die Pflicht-Bestätigung „Unternehmer (§ 14 BGB)“, nicht vorangekreuzt. Der Server (`anfrage.php`) lehnt sie ohne ab. Preise tragen „netto zzgl. USt., nur für Unternehmer“ direkt am Preis. | ja |
| Einwilligung | Gültigkeit (Version, Zeitstempel, 6 Monate, Wahrheitswert) nur über `window.mxConsent` aus `consent.js`, nie `localStorage` direkt lesen. Alles Optionale (Statistik, Herkunftsdaten `mx-utm`) nur mit gültiger Einwilligung. Abgelaufen, alt oder beschädigt gilt als keine Entscheidung. Nach jeder Änderung `einwilligung.mjs` und `tracking.mjs`. | ja |
| Datenschutztext | Jede Aussage dort muss dem gemessenen Verhalten entsprechen (Cookie-Laufzeit, Speicherobjekte, Anfragen an Dritte). Nichts behaupten, was nur im Konto eingestellt ist (zum Beispiel Aufbewahrungsdauer), ohne den Wert zu kennen. Stand-Datum bei jeder Änderung anpassen. | nein |
| Wortwahl | Keine Zusagen wie „rechtssicher“, „rund um die Uhr“, „24/7“, „DSGVO-konform“, „jederzeit an einen Menschen“, „nahtlos“, „ganzheitlich“, „maßgeschneidert“, „innovativ“, „Ihr Partner für“. Leistungsversprechen nur mit Umfang („nach vereinbartem Umfang“). Keine pauschale „Haftung für Links“. | ja |
| Befristete Angebote | Das Angebot trägt `data-deal-until`. Der Build entfernt es nach Fristende aus dem HTML. Ab dem Folgetag neu bauen und einspielen. Aktionscodes laufen serverseitig ab. | ja |
| Zahlen und Belege | Gepflegte Zahlen (Bewertungen) mit Stand. Bewertungen mit Hinweis zur Herkunft. Referenzen und Bilder nur mit dokumentierter Freigabe oder Lizenz. | nein |
| Werkzeuge | Kein Paket installieren, kein Dienst starten, nichts an Dritte senden, ohne dass es klar benannt und freigegeben ist. Prüfungen gegen Live nur lesend. | nein |

## Woher diese Regeln kommen (Lehren)

- **H1 mit Unterzeile:** Ein Span ohne Leerzeichen im H1 erzeugte „bringen.Webdesign“ und eine 119 Zeichen lange H1. Regel: Unterzeile als Absatz.
- **Keywords nur im Title:** Hauptseiten hatten Wirkaussagen in der H1, aber nicht das Suchwort. Regel: Suchwort zuerst.
- **Ganze Karten als Link:** 264 Karten erzeugten 200 Zeichen lange Linktexte. Regel: Link auf der Überschrift, zentral im Build gelöst.
- **Einwilligung:** Die Seite prüfte nur „analytics: true“, nicht Ablauf und Version. Regel: eine einzige Gültigkeitsprüfung.
- **Texte vor Messung:** „bis 14 Monate“ für die Cookies war nie gemessen. Regel: erst messen, dann schreiben.
- **Nebenseiten vergessen:** Beispielseiten und die Karte hatten weder Impressum noch Datenschutz. Regel: Pflichtlinks gelten für jede Seite.
- **Zwischenstand geprüft:** Mehrere externe Berichte sahen einen Stand vor dem letzten Einspielen. Regel: vor einem Prüflauf prüfen, was live liegt (`curl`), und im Zweifel neu starten.
- **Veraltete Vorgaben:** Der Skill beschrieb noch die frühere Markenwelt. Regel: Skill und CI-Handbuch nach jeder Markenänderung aktualisieren (Entwurf in `docs/SKILL-ENTWURF-markentrix-eigene-website.md`).
