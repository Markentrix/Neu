# ENTWURF: aktualisierter Skill „markentrix-eigene-website“

Dies ist der bestehende Skill-Text (Stand 13.11.2026) mit vier Änderungen: (1) CI auf Markenhandbuch 3.1 (Archivo, Source Sans 3, Salz/Reif/Tiefsee/Pfauenblau/Kupfer), (2) Verweis auf Repository, Regeln und Gate, (3) neuer Abschnitt „PFLICHTREGELN AUS DER PRAXIS“, (4) Gate und Browser-Tests im Abschnitt TESTS.
Der Skill liegt bei Claude in der Skill-Verwaltung und lässt sich von hier nicht ändern. **Bitte den Text unterhalb der Linie in den Skill einfügen** (Einstellungen → Skills → markentrix-eigene-website, vorhandenen Inhalt ersetzen). Eine offene Abweichung: Der alte Skill verbot „Eyebrow-Labels“, die Seite nutzt sie bewusst; das ist im Text geblieben und sollte entschieden werden.

---

---
name: "markentrix-eigene-website"
description: "Die bestehende eigene Markentrix-Website (markentrix.de) prüfen oder verbessern: Design, Conversion, SEO/Indexierung, Performance. Nur wenn ausdrücklich die Markentrix-Seite gemeint ist, nicht für Kundenwebsites."
---

MARKENTRIX – EIGENE WEBSITE VERBESSERN

GELTUNG
Gilt nur für die bestehende eigene Markentrix-Website markentrix.de. Für Kundenwebsites gilt der Skill "website-mit-portal"; dessen Exportvorgaben (website-fertig/, statischer Uploader, Kundenportal-API-Endpunkte, "kein Docker", "keine Serverfunktionen") gelten hier NICHT. Die Kundenportal-APIs sind nicht automatisch die APIs der Markentrix-Website. Dieser Skill ist eigenständig; "website-mit-portal" wird nur für das Prüfskript gebraucht (siehe TESTS).
Grundsatz: Anpassung, kein Neubau. Bestehendes verbessern, nichts aufbrechen.

STECKBRIEF (Stand der bisherigen Festlegungen; weicht die Live-Seite ab, nachfragen statt annehmen)
- Adresse: markentrix.de und www. Die Seite wurde mit Claude Code erstellt.
- Betreiber: Markentrix, Einzelunternehmen von Christian Wien, Geschäftsstelle Heinrich-Hüdig-Str. 1, Celle. Fehlende Impressumsangaben (PLZ, USt-IdNr.) sind "OFFEN:", nie ergänzen.
- Zielgruppe: lokale kleine und mittlere Betriebe, vor allem Handwerk und Werkstätten.
- Hosting: Die Seite liegt auf dem Markentrix-Hetzner-Server. Auf demselben Server laufen das Kundenportal und die Kundenwebsites: nichts neu starten oder umkonfigurieren, was sie mitbetrifft. Die Domain ist bei Squaredance registriert; DNS-Änderungen laufen dort und nur nach ausdrücklicher Freigabe.
- Ablage und Ausrollen: zu Beginn feststellen, wo der Code liegt (Repository), wie ausgerollt wird und ob es eine Testadresse gibt. Das Ergebnis in den Bericht schreiben.
- CI laut Markenhandbuch 3.1 (Farbwelt D, seit November 2026; die frühere Welt mit Space Grotesk, Inter, Navy, Cyan und Violett gilt NICHT mehr): Archivo (Überschriften) und Source Sans 3 (Text), lokal ausgeliefert. Farben: Salz #F4F6F7, Reif #E0E6E9, Tiefsee #0C2128, Pfauenblau #045268, Kupfer #C67432 (als Text nur ab 24 px, auf Dunkel #F1A268), Nebentext #465A62. Die genauen Werte für Knöpfe, Abstände und Radien aus dem vorhandenen CSS (static/assets/mx.css) ablesen und als Tokens weiterverwenden, nie schätzen oder neu erfinden.
- Code und Regeln: Repository markentrix/neu, Generator tools/build.py, Regeln in docs/QUALITAETSREGELN.md und CLAUDE.md. Vor jedem Paket: python3 tools/qa.py (muss 0 Fehler melden).
- Live-Anbindungen, die erhalten bleiben müssen: Schema.org LocalBusiness, Terminbuchung über den Kalender im Markentrix-Portal (nicht Google Calendar), Kontaktformular (sendet an einen Webhook), eingebettete Kundenkarte aus dem Kundenportal (zeigt nur echte Kunden, Daten kommen automatisch aus dem Portal). Vor jeder Änderung prüfen, ob es weitere gibt.
- Inhaltliche Festlegungen: keine erfundenen Referenzen, Kennzahlen oder Kundenstimmen; Referenzen nur so, wie freigegeben (ohne Kennzahlen und Zitate, solange keine vorliegen); in Kundentexten "der Agent", nie "die KI"; Preise, Pakete, Pilotplätze und Vertragsbedingungen nur nach ausdrücklicher Freigabe ändern.

PRIORITÄTEN
1. Datensicherheit, bestehende Live-Funktionen, DSGVO, konkrete Vorgaben des Auftrags.
2. Vorhandene Architektur, echte Routen und Integrationen bewahren.
3. Bestehende Markentrix-CI (Markenhandbuch 3.1: Archivo, Source Sans 3, Salz/Tiefsee/Pfauenblau/Kupfer) wird nicht unter dem Vorwand "KI-Look" ausgetauscht.
4. Conversion, Lesbarkeit, Barrierefreiheit, Performance vor Animation und Dekoration.

ARBEITSWEISE
1. Lesende Bestandsaufnahme zuerst: git status, Branch-/Commit-Zustand, Konfigurationsinventar, geänderte Dateien, vorhandene Tests, mögliche Nebenwirkungen. Bestehende Routen durch Codeanalyse erfassen, keine Pfade erfinden.
2. Keine Secrets ausgeben. Keine Datenbank löschen, keine fremden Dienste neu konfigurieren, keine Live-Container ohne gesonderte Freigabe neu starten.
3. Server-, Deployment- oder Datenbankkonfiguration nur nach Freigabe und mit Rollback ändern. Bei riskanten Eingriffen: Diagnose → Änderungsplan → Backup- und Rollback-Nachweis → ausdrückliche Freigabe.
4. Änderungen bevorzugt lokal oder auf einer Testadresse, dann Tests, visuelle Abnahme und erst nach Freigabe produktiver Rollout. Bestehende Infrastruktur (zum Beispiel Docker Compose) nicht "modernisieren", wenn kein konkreter Bedarf nachgewiesen ist.
5. Reversible Verbesserungen schrittweise umsetzen, ohne funktionierende Teile aufzubrechen. Erklärungen in einfachen, kleinen Schritten; vor allem, was sich nicht rückgängig machen lässt, nachfragen.
6. Braucht es etwas Neues auf dem Server oder im Portal (APIs, Endpunkte), eine kurze MD-Datei für den zuständigen Chat erstellen, in der auch steht, was zurückgemeldet werden muss.
7. Fehlt ein Skill oder Skript, keine Ergebnisse erfinden; mit dem Verfügbaren arbeiten und die Einschränkung dokumentieren.

DESIGN-HANDWERK (innerhalb der bestehenden CI)
- Tokens: jede Farbe, Schrift, jeder Abstand und Radius als CSS-Variable; keine losen Werte. Alle Seiten nutzen dieselben Tokens, Navigation und Footer.
- Typografie: Headline zu Fließtext mindestens 3×, höchstens fünf Größen; Überschriften höchstens zwei Zeilen bei jeder Breite; Fließtext 16–20 px, Zeilenhöhe 1,45–1,6, 45–75 Zeichen je Zeile, Kontrast mind. 4,5:1 (großer Text 3:1). Auf Navy heller Text in voller Stärke, kein Grau.
- Farbe: Tiefsee trägt (Text, dunkle Flächen), Pfauenblau ist die Markenfarbe für Links und Flächen, Kupfer ist die Handlungsfarbe für Hauptknöpfe und das hervorgehobene Wort (nur große Schrift), Salz und Reif sind die hellen Flächen. Keine Cremetöne (wirken wie Standard-KI-Seiten).
- Layout: erster Bildschirm zeigt wer, was, für wen, welcher Vorteil, was jetzt zu tun ist; genau eine Haupt-Conversion je Seite; Abschnitte unterschiedlich aufgebaut; keine Reihen identischer Icon-Karten, keine Statistik-Leisten mit runden Zahlen, keine Eyebrow-Labels, keine Deko-Nummern.
- Texte: konkret und belegbar; Knöpfe als Verb plus Gegenstand; verboten sind "Ihr Partner für", "maßgeschneidert", "innovativ", "ganzheitlich", "nahtlos", "auf das nächste Level", Dreier-Slogans und unbelegte Superlative.
- Bewegung: ein orchestrierter Moment je Seite plus Rückmeldung auf Aktionen; nur transform und opacity; unter 300 ms; ease-out beim Erscheinen, nie ease-in; nie transition: all; prefers-reduced-motion beachten; Hover nur in @media (hover: hover) and (pointer: fine).
- Handy: Eingabefelder mindestens 16 px, Tippziele mindestens 44 px, nie 100vh (Hero 100svh), Zoom nie sperren, Hauptaktion ständig erreichbar.
- Zustände: Hover, sichtbarer Fokus, Laden, Fehler, leer; alles per Tastatur bedienbar; Ziel WCAG 2.2 AA.
- Datenschutz: Schriften lokal, keine Fremd-CDNs, Einbettungen Dritter nur mit Zwei-Klick-Lösung oder über die bestehende Einwilligung.

PFLICHTREGELN AUS DER PRAXIS (Stand 21.11.2026; automatisch geprüft von tools/qa.py, Einzelheiten in docs/QUALITAETSREGELN.md)
- Überschriften: genau eine H1, Suchbegriff (Thema, bei Ortsseiten mit Ort) zuerst, höchstens 70 Zeichen; Unterzeile nie im H1-Element; keine Ebene überspringen; Zwischenüberschriften mit Themenwort statt "Passend dazu".
- Suchbegriffe: je Begriff eine Zielseite, Begriff in Title, H1 und erstem Absatz; nicht zwei Seiten auf denselben Begriff.
- Titel höchstens 65 Zeichen, Description 70 bis 160; Startseite überall mit Schrägstrich (Canonical, og:url, Sitemap).
- Links: Karten verlinken nur die Überschrift (Build-Funktion card_links); Linktext höchstens 70 Zeichen, eindeutig; interne Links mit Parameter mit rel="nofollow"; externe Links regelmäßig prüfen.
- Bilder: Alt-Text, Breite und Höhe; Zierbilder als CSS-Hintergrund statt img mit leerem alt.
- Pflichtlinks Impressum und Datenschutz auf JEDER Seite, auch Beispielseiten und Karte.
- Formulare (Kontakt, Rückruf, Website-Check, Bewerbung): Pflicht-Bestätigung "Unternehmer nach § 14 BGB", serverseitig geprüft; Preise mit "netto zzgl. USt., nur für Unternehmer" direkt am Preis.
- Einwilligung: Gültigkeit nur über window.mxConsent (consent.js); Optionales (Statistik, Herkunftsdaten) nur mit gültiger Einwilligung; Test: tools/browser_tests/einwilligung.mjs und tracking.mjs.
- Datenschutztext darf nur Gemessenes oder Belegtes behaupten (Cookie-Laufzeit, Speicherobjekte, Fristen). Unbekanntes als OFFEN in die Doku, nicht in die Seite.
- Wortwahl: keine Zusagen wie rechtssicher, rund um die Uhr, 24/7, DSGVO-konform, jederzeit an einen Menschen; keine pauschale "Haftung für Links"; Leistungsversprechen nur mit Umfang.
- Befristete Angebote (data-deal-until) entfernt der Build nach Fristende; ab dem Folgetag neu bauen und einspielen.
- Barrierefreiheit: axe WCAG 2.2 AA auf allen Seiten bei 390 und 1440 px ohne Verstoß, bevor ein Paket entsteht.
- Vor einem externen Prüflauf: prüfen, was live liegt (curl), sonst sieht der Bericht einen Zwischenstand.

CONVERSION
Prüfe insbesondere die Wege Startseite → Preisseite → Anfrage, Startseite → Website-Check und Startseite → Kontakt. Existieren die Routen anders, die tatsächlich gefundenen verwenden. Preis- und Leistungsdarstellung erklärt Unterschiede, Umfang und Folgekosten. Vertrauensbelege nur aus realen Referenzen und belegbaren Angaben; nichts erfinden, Fehlendes als "OFFEN:".

SEO / INDEXIERUNG
URL- und Indexierungs-Matrix für alle echten Seiten: HTTP-Status, robots, Meta-Robots, Canonical, Sitemap-Aufnahme, interne Links, beabsichtigte Indexierung. Dazu title, description, H1, semantische Struktur, strukturierte Daten (nur wenn zutreffend und belegbar), Bild-ALT, Mobile-Rendering, interne Linktiefe.
Search Console: Es gibt keinen direkten Zugriff. Christian lädt den Export des Seiten-Berichts (CSV oder XLSX) in den Chat. Liegt keiner vor, einmal danach fragen; ohne Export nur öffentlich Prüfbares bewerten und diese Grenze im Bericht ausdrücklich nennen.
Mit Export: Ursachen für "gefunden, derzeit nicht indexiert" und "gecrawlt, derzeit nicht indexiert" klären. Unterscheiden: bewusst gesetztes noindex, Canonical-Duplikate, Redirects, Soft-404, SSR/JS-Rendering, schwache oder doppelte Inhalte. Serverantworten des laufenden Systems nur lesend prüfen. Keine pauschale Freigabe aller Seiten.

MESSUNG
Bestehende Consent-/Tracking-Architektur prüfen und respektieren. 3–5 Conversions definieren mit Event-Name, Auslöser, Erfolgskriterium, Ziel-URL und Validierung, ohne doppelte Events. Keine Conversion-Rate ohne echte Besucher- und Abschlussdaten behaupten.

TESTS
- Gate: python3 tools/qa.py im Repository (Pflicht), dazu tools/browser_tests/ (axe, Einwilligung, Tracking, Formulare).
- Prüfskript: pruefe.mjs aus "website-mit-portal" (Abschnitt 18) verwenden, mit der Adresse der Seite in der Umgebungsvariable BASE, zum Beispiel BASE=https://<testadresse> node pruefe.mjs /preise. Es liest nur und misst bei 1440, 768, 390 und 320 px. Fremdabrufe, die zur bestehenden, eingewilligten Architektur gehören, als begründet vermerken.
- Formulare: formtest.mjs NIE gegen die Live-Seite oder eine Testadresse mit echtem Webhook laufen lassen, es sendet eine echte Anfrage. Formulare lokal mit abgefangenem Versand prüfen oder von Hand mit einer als Test gekennzeichneten Anfrage nach Freigabe.
- Von Hand: Navigationswege, CTAs, Fehler- und Erfolgszustände; Tastatur, Fokus, reduced motion; interne Links, Sitemap/robots, Canonical-Logik; Terminbuchung und Kundenkarte laden und funktionieren.
- Performance: LCP <= 2,5 s, INP <= 200 ms, CLS <= 0,1; Laborwerte als solche kennzeichnen. Visuelle Regression: Vorher-Nachher-Screenshots der geänderten Seiten.
- Sicherung/Changelog, Dateiliste und reproduzierbare Prüfschritte festhalten. Jeder Punkt: PASS, FAIL, NICHT TESTBAR oder BEWUSST AUSGENOMMEN. Nie Ungetestetes als PASS melden.

BERICHT
A. Ziel, tatsächlicher Tech-Stack, Hosting und Ablage (wie festgestellt).
B. Bestand, belegte Daten, "OFFEN:".
C. Designrichtung, CI-Abgleich, Haupt-Conversion.
D. Audit-Ergebnisse nach Kritisch/Hoch/Mittel/Niedrig mit Wirkung und Aufwand.
E. Konkrete Änderungen mit Dateipfaden.
F. Testergebnisse mit Status und Messwerten.
G. Vorhandene Live-Integrationen und Datenflüsse.
H. Risiken, ausstehende Freigaben, Rollback.
I. Nächste 3 Maßnahmen nach erwarteter Geschäftswirkung.
Keine pauschale Perfektion behaupten.