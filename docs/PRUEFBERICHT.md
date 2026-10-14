# Prüfbericht und Überarbeitung · markentrix.de · 12.10.2026

Geprüft wurde der Claude-Design-Export `Markentrix.zip` (Ordner `dist/`, identisch mit der Live-Seite vom 1.10.2026, 23 Seiten) gegen die CI „White / Light Premium“ (`docs/brand/Markentrix_CI_2026_White_Light_Premium_MASTER.pdf`), die Preisliste vom 1.10.2026 und die Standardseitenstruktur der CI (Hero, Problem, Lösung, Leistungen, Prozess, Case, CTA). Ergebnis: Die Seite wurde vollständig neu aufgebaut. Alle Inhalte, Preise, Rechtstexte, Meta-Daten und strukturierten Daten wurden übernommen, die Technik und Gestaltung sind neu.

## 1. Befund der alten Seite

### Gestaltung und CI
| # | Befund | CI-Regel | Status |
|---|---|---|---|
| 1 | Startseite mit animiertem Partikel-Canvas, Rasterlinien, Leuchtflächen („Aura“), Cursor-Effekten, Laufband und „Typed“-Text | „unruhige Hintergründe“ und „übertriebene Neon-Effekte“ vermeiden, Ruhe ist Teil der Marke | behoben: ruhige weiße Flächen, eine Signatur-Kurve als einziges Signature-Element |
| 2 | Hero-Headline komplett in Violett-Verlauf, Headline-Hierarchie unklar (H1 zweizeilig, dann drei weitere Sublines) | eine dominante Botschaft, Violet nur als Akzent | behoben: Sales-Claim „Mehr Anfragen. Weniger Aufwand.“ als H1 in Navy, Unterzeile im Verlauf |
| 3 | Dark-Mode-Umschalter und Hochkontrast-Buttons (A−, A+, ◐) prominent in der Hauptnavigation | Dark nur als bewusste Kontrastfläche, nicht als Standard; Navigation klar | behoben: Dark-Mode entfernt, Anzeigeoptionen (Schrift, Kontrast) in den Footer verlegt, Kontrastfläche nur als Abschluss-CTA in Navy |
| 4 | Zwei konkurrierende primäre Handlungen je Modul (z. B. Hero mit Cyan-Button, Kontaktleiste, Sticky-Leiste, Badge) | genau eine primäre CTA je Modul | behoben |
| 5 | 70 KB Inline-CSS plus Inline-Styles in jedem Element, drei verschiedene Stile für Karten, Buttons, Eyebrows auf Unter- und Startseite | ein System, feste Raster | behoben: ein Design-System `assets/mx.css` (Tokens aus der CI), keine Inline-Styles |
| 6 | Violett `#8B5CF6` als Textfarbe (Kontrast 3,3:1 auf Weiß), Grautext `#667085` mit 300er Schnitt | starke Kontraste, barrierearm | behoben: Textvarianten `#6D3FD1` / `#0B63C6` (≥ 4,5:1), Fließtext 400 |
| 7 | JetBrains Mono als dritte Schrift (Labels), nicht in der CI | nur Space Grotesk und Inter | behoben |
| 8 | Logo-Verlauf Cyan→Violett `#7C3AED` statt CI-Violett `#8B5CF6` | Original-Logo unverändert | behoben |
| 9 | Harte Schatten, Glassmorphism-Flächen, 3D-Karten-Effekt | helle Cards mit feinem 1-px-Rahmen, keine harten Schatten | behoben |
| 10 | Mobile: Hero mit 10.500 px Seitenhöhe, Kennzahlen überlappen, Kontaktleiste verdeckt Inhalte | mobile-first | behoben, geprüft bei 390 px |

### Technik
| # | Befund | Status |
|---|---|---|
| 11 | Startseite 198 KB, davon 57 KB Inline-JavaScript mit eigener Mini-Laufzeit („DCLogic“), Unterseiten mit zweiter Laufzeit `mx.js` | Startseite jetzt 55 KB; eine Laufzeit `site.js` (22 KB, ohne Framework), ein Stylesheet `mx.css` (47 KB) für alle Seiten, beide langlebig gecacht |
| 12 | Keine Content-Security-Policy möglich (Inline-Skripte) | strikte CSP in `_headers` (script-src 'self' + Analytics-Hosts), getestet |
| 13 | Doppelte `<meta charset>`/`viewport`, `X-UA-Compatible` | bereinigt |
| 14 | Mobile Navigation wurde per JavaScript aus der Desktop-Navigation „abgeleitet“ (fehleranfällig) | eigenes, statisches Mobile-Menü mit Fokusführung, Escape, aria-expanded |
| 15 | Potenzial-Check-Modal nur auf der Startseite; Unterseiten verlinkten auf /kontakt | Modal auf allen Seiten im Gerüst, gleiches Webhook-Format |
| 16 | Bilder als JPG, teils ohne Maße; OG-Bild als Logo | WebP mit Maßen, Logo als PNG, eigenes `favicon.svg` |
| 17 | Fonts: Preload und lokale WOFF2 bereits korrekt | übernommen |
| 18 | Relative Pfade (`../assets`) je Ordner, `.html`-Links im Code | root-absolute Pfade, sprechende URLs |
| 19 | Reveal-Animationen ohne Fallback (Inhalt bleibt bei blockiertem Observer unsichtbar) | Fallback nach 4 s, `prefers-reduced-motion` respektiert |
| 20 | Sitemap von Hand gepflegt, `lastmod` uneinheitlich | wird im Build aus dem Front-Matter erzeugt |

### Inhalt und Recht (unverändert übernommen, geprüft)
- Preise entsprechen der Preisliste vom 1.10.2026 (ONE 349 € + 1.490 €, BUSINESS 699 € + 2.490 €, KOMPLETT 1.190 € + 3.490 €, Websites 1.290/2.290/4.490/6.990 €, CI 1.290/2.490/4.490 €, Social 749 €, Local 449 €, Personal Branding 690/1.690/3.490 €, Lead-Agent 890 €, Google-Ads-Agent 599 €; alle netto). Keine Abweichungen gefunden.
- B2B-Hinweis (§ 14 BGB), Netto-Hinweis, Laufzeiten, Pilotangebot, AVV-Aussage: auf allen Seiten konsistent.
- Impressum, Datenschutz (inkl. Anker `#s5` für das Cookie-Banner), AGB: wortgetreu übernommen. Offen bleibt die USt-IdNr. (Kommentar im Impressum).
- Keine Tool- oder Modellnamen in sichtbaren Texten (Markenregel). Keine CI-Beispielzahlen, keine erfundenen Kundenstimmen.
- Blog: drei Artikel mit Autorenbox, Inhaltsverzeichnis, FAQ und Quellen übernommen.

## 2. Was neu ist

**Design-System** `static/assets/mx.css`: CI-Tokens (Navy, Cyan, Blue, Violet, Soft White, Cool/Muted Gray), Typografie (Space Grotesk Bold/SemiBold, Inter Regular/Medium), Raster (1180 px, 8-px-Basis), Komponenten (Header, Footer, Hero, Karten, Preise, Schritte, FAQ, Formulare, Kalender, Modal, Hinweise, Kontrastfläche, Blog, Rechtstexte, Demo-Darstellungen), Reveal, Hochkontrast-Modus, Druck.

**Laufzeit** `static/assets/site.js`: Navigation, Reveal, Formulare an den n8n-Webhook (gleiche Felder wie zuvor plus `firma`, `budget`, `seite`, `zeit`), Wunschtermin-Kalender (Mo–Fr, ab morgen), Potenzial-Check-Modal mit Fokusfalle, Kurzcheck und Sparrechner, Blog-Filter, Anzeigeoptionen.

**Build** `tools/build.py`: Gerüst + Seiten → `dist/`, Sitemap, Linkcheck (Ziele, Anker, eine h1, Titel-/Description-Länge). Konventionen in `docs/SEITENBAU.md`.

**Startseite** nach CI-Standardstruktur: Hero (Claim, Systemablauf-Karte, Kennzahlen) → Problem → Lösung (ein System, drei Schritte) → Leistungen (vier Bereiche) → Beweis (eigener Betrieb, Projekt Pony Club Lila) → Prozess (Zeitleiste) → Kurzcheck → Warum Markentrix (Gründer) → Pilotangebot → Abschluss-CTA auf Navy mit Wachstumskurve.

**Signature-System (Nachtrag 12.10.2026, zweite Runde)**: Eigenes Icon-Set in der Linienlogik der Wortmarke (jedes Icon trägt genau einen gefüllten Datenpunkt), drei animierte Systemkarten (Knoten + Verbindungslinien im CI-Verlauf) für Marketing, Webdesign und KI-Automatisierung, ein durchlaufender Wachstumspfad mit nummerierten Datenpunkten auf der Startseite (ab 1340 px), zwei Typografie-Statements aus den CI-Markenbotschaften, Brancheneinstiege (Handwerk, Praxis, Gastro/Handel) mit vorbelegtem Potenzial-Check, Hover-Verbindungslinie zwischen Bausteinen und ein Datenpunkte-Muster in Footer und Kontrastfläche. Der Potenzial-Check ist jetzt ein Dialog: Branche, Kanal, Anfragen pro Woche, dann eine Ersteinschätzung (nur Aussagen aus Preisliste und CI-Allowlist, keine Ergebnisversprechen), erst danach Name und E-Mail. Der Webhook erhält zusätzlich `branche`, `kanal`, `anfragen`, `empfehlung`.

**Positionierung (Nachtrag 12.10.2026, dritte Runde)**: Kernangebot sind jetzt Websites und Landingpages mit SEO und GEO. Startseite, Titel, Description, strukturierte Daten, Navigation, Footer, Preisseite (Reihenfolge: Websites zuerst, KI zuletzt) und `llms.txt` sind darauf umgestellt. KI-Assistenten werden als „ab November 2026“ mit Pilotplätzen angekündigt (Startseite, Leistungsnavigation, KI-Seite, Preisseite). Neue visuelle Bausteine: Browser-Mockup mit dem Pony-Club-Lila-Projekt im Hero, Beispieldarstellung „lokale Suche und KI-Antwort“ (fiktiver Betrieb, ohne Platzierungsversprechen) auf Startseite und Webdesign-Seite, SEO/GEO-Abschnitt auf der Webdesign-Seite. Der Potenzial-Check fragt jetzt nach dem Punkt, an dem Interessenten abspringen (Website, Sichtbarkeit, Anfragewege, Telefon/WhatsApp).

**Alle 23 Seiten** mit gleichem Gerüst, Breadcrumbs, Abschluss-CTA, strukturierten Daten (WebPage, BreadcrumbList, FAQPage, Service, Article, OfferCatalog) und sauberer Überschriftenhierarchie.

## 3. Prüfung des Ergebnisses
- Build mit Linkcheck: alle internen Links und Anker aufgelöst, genau eine h1 je Seite, Titel ≤ 65 und Description ≤ 165 Zeichen.
- HTML-Validierung (html-validate, recommended): ohne Fehler.
- Funktionstests (Chromium): Consent-Banner, Footer-Link „Cookie-Einstellungen“, Mobile-Menü, Dropdown, Modal (Validierung, Versand, Escape, Fokus), Kontaktformular mit Wunschtermin, Kurzcheck, Sparrechner, Blog-Filter, Anzeigeoptionen, kein horizontales Scrollen bei 390 px.
- CSP-Test mit echtem Header: Consent, GA4 und Metricool laden nur nach Einwilligung und ohne CSP-Fehler, Webhook erreichbar, Fonts lokal.
- Screenshots Desktop (1440) und Mobil (390) aller Seiten gesichtet.

## 4. Redaktionelle Hinweise aus der Migration
- **Über uns** sagt „Serverstandort Deutschland“, Startseite „Hostingregion projektbezogen“, KI-Seite „EU-Server“. Alle drei Aussagen stammen aus der alten Seite; bitte auf eine Formulierung festlegen (Datenschutz nennt Hetzner, Rechenzentrum DE).
- **KI-Checkliste** (noindex): Die Altangaben „Einführungspreise bis 31.12.2026“, „30/60 Minuten Anpassungsbudget“ und „verbrauchsbasierte API-Abrechnung“ wurden am 14.10.2026 durch die Konditionen der Preisliste ersetzt (Pilotangebot 50 % auf die Einrichtung, Mehrverbrauch 0,55/0,49 € je Minute, Start im November 2026).
- **FAQ** nennt „Google Calendar“ als Kanalbezeichnung (wortgleich mit dem FAQPage-JSON-LD). Erlaubt als Leistungsbezeichnung, kein Toolname im Markensinn.
- **Datenschutz, Abschnitt 5**: Der Eintrag zum Dark-Mode-Speicher `mk-theme` wurde gestrichen, weil es den Umschalter nicht mehr gibt. Die Einträge `mx-consent`, `mx-a11y-scale`, `mx-a11y-contrast` bleiben korrekt. Abschnitt 5a nennt die KI-Anbieter namentlich; das ist als Pflichtangabe richtig und keine Werbung.
- **Webdesign**: Der alte Hinweis „Angebot bis 31.12.2026: LANDING START“ wurde zu „nur als Angebot“ (wie auf /preise). Falls die Frist gelten soll, auf beiden Seiten ergänzen.
- **Regionalseiten** (14.10.2026 neu geschrieben): Celle, Hannover, Gifhorn und Braunschweig führen jetzt mit Website, Leistungsseite je Ort und Google-Profil; der KI-Assistent steht als Ausblick „ab November 2026“ in einer eigenen Karte. Beispielszenarien sind als fiktiv gekennzeichnet und ohne Kennzahlen. Die URLs `/ki-marketing-*` bleiben wegen bestehender Verlinkung unverändert.
- **FAQ** (14.10.2026 neu geschrieben): zwölf Fragen in vier Gruppen (Website und Pflege, SEO/GEO und Sichtbarkeit, KI-Assistent ab November 2026, Datenschutz und Regionen), alle Preise aus der Preisliste, FAQPage-JSON-LD aus denselben Texten erzeugt.

## 5. Offen (braucht Entscheidung oder Material)
1. **USt-IdNr.** im Impressum eintragen, sobald vorhanden (Kommentar in `src/pages/impressum.html`). Die Nummer liegt nicht vor, der Satz „beantragt“ bleibt deshalb stehen.
2. **Netlify**: Repository mit dem Netlify-Projekt „markentrix-website“ verbinden (Branch `main`, `publish = dist`, kein Build-Befehl) oder `dist/` per Drag-and-drop deployen. Nach dem Deploy die Abnahmetests aus `docs/DEPLOY.md` ausführen und die Sitemap in der Search Console neu einreichen.
3. **Formularversand (geprüft am 14.10.2026)**: Die n8n-Cloud-Instanz `markentrix.app.n8n.cloud` existiert nicht mehr („404 – No instance here“). Damit scheitert jede Anfrage über das bisherige Live-Formular. Die neue Seite sendet deshalb an einen **eigenen Endpunkt auf dem Hetzner-Server** (`dist/api/anfrage.php`, gleiche Domain, kein CORS, E-Mail an info@markentrix.de, optional Weiterleitung an einen neuen Webhook). Auf dem Server müssen PHP-FPM und Mailversand eingerichtet sein (siehe `docs/DEPLOY.md`, nginx-Block in `docs/nginx-markentrix.conf`). **Datenschutz (angepasst am 14.10.2026)**: Abschnitt 4 beschreibt jetzt die Verarbeitung auf dem eigenen Hetzner-Server (Skript, E-Mail an info@markentrix.de, Eingangsprotokoll außerhalb des Webverzeichnisses, gekürzter IP-Hash zur Ratenbegrenzung, Potenzial-Check-Felder); der n8n-Absatz ist gestrichen. Abschnitt 5a gilt ausdrücklich „ab November 2026“. Stand der Erklärung: 14. Oktober 2026. Sollte später ein Webhook in `anfrage.php` eingetragen werden, muss Abschnitt 4 um diesen Empfänger ergänzt werden. Eine Prüfung durch eine datenschutzrechtlich beratende Person bleibt empfohlen.
4. **Social-Links** (Facebook, Instagram, LinkedIn) in den strukturierten Daten sind weiterhin unverifiziert übernommen.
5. **Fallstudie und Kennzahlen** Pony Club Lila erst nach schriftlicher Freigabe der Kundin ergänzen (Vorlage in `src/pages/referenzen.html`). Seit 14.10.2026 erscheint Pony Club Lila nur noch auf der Referenzseite (als „Live“ gekennzeichnet) und im Blogbeitrag „Warum ist eine Website wichtig“; Startseite und Webdesign-Seite zeigen stattdessen eine CSS-Skizze eines fiktiven Betriebs (`src/partials/mock-site.html`). Der frühere Abschnitt 06 „Beweis statt Behauptung“ der Startseite ist entfernt, die Abschnitte sind auf 08 durchnummeriert.
6. **Hero-Video** bleibt deaktiviert (CI: ruhige Flächen). Das Quellvideo liegt im Claude-Design-Projekt unter `_archive/`.
7. Lighthouse und PageSpeed nach dem Deploy messen; lokal gibt es keine Netzwerkbedingungen.
