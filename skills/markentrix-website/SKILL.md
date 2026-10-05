---
name: "markentrix-website"
description: "Baut CI-konforme, schnelle, barrierefreie und DSGVO-sichere Landingpages und Websites für Markentrix (und Kundenprojekte) – von Briefing, Struktur und Copy über Code, Animation und Performance bis zu Recht-Checks, Audit und Übergabe."
---

# Markentrix Website & Landingpage – Produktionsskill

Verbindliche Markentrix-Schicht für jede Landingpage und Website. Legt fest, WAS gebaut wird (Marke, Aufbau, Copy, Recht) und WIE gebaut und geprüft wird (Leistung, Barrierefreiheit, Datenschutz, Animation). Details stehen in `references/`, ein lauffähiger Start in `assets/starter/`, der automatische Check in `scripts/audit.sh`.

Quellen der Wahrheit (aus dem Projekt „Markentrix“ lesen): CI-Master-PDF, aktuelle Preisliste, `claude/creative-system/`. Bei Widerspruch gilt die aktuelle Projektdatei. Gleiche Marken- und Aussagenregeln wie im Skill `markentrix-werbevideo`.

## 1. Wann
Jede Anfrage nach Landingpage, Website, Onepager, Relaunch, Lead-Seite, Danke-Seite, Impressum/Datenschutz-Seite, Cookie-Banner oder Website-Audit. Eigene Markentrix-Seite = diese CI. Kundenprojekt = Kunden-CI, Branche und Claims erfragen; Abschnitte 3–8 gelten trotzdem.

## 2. Hard Gates (nie verletzen)
1. **Kein Tracking vor Einwilligung.** Keine Meta-Pixel, GA, Tag Manager, Hotjar, eingebettete Videos/Karten von Drittanbietern vor aktivem Opt-in. Standard: gar kein Drittanbieter-Request.
2. **Alles selbst hosten:** Schriften, Icons, Skripte, Bilder. Kein Google Fonts/CDN-Aufruf zur Laufzeit.
3. **Kein erfundener Beweis:** keine erfundenen Kunden, Zitate, Sterne, Fallstudien, Zahlen, Logos. Platzhalter sichtbar als `[PLATZHALTER – Freigabe nötig]`, nie live.
4. **Nur freigegebene Aussagen** (Allowlist des Skills `markentrix-werbevideo`, Abschnitt 5). Kein „garantiert“, „Platz 1“, „24/7“, „spart X Stunden“.
5. **Barrierefrei als Standard:** WCAG 2.2 AA, Tastatur komplett bedienbar, Kontrast geprüft, `prefers-reduced-motion` respektiert.
6. **Performance-Budget** (Abschnitt 6) wird eingehalten oder die Abweichung begründet.
7. **Pflichtseiten vollständig:** Impressum, Datenschutzerklärung, Barrierefreiheitserklärung wo nötig, erreichbar von jeder Seite mit ≤ 1 Klick.
8. **Keine Rechtsberatung:** Rechtstexte aus Generator/Anwalt, Freigabe durch Inhaber. Im Hand-off klar benennen, was juristisch geprüft werden muss.
9. **Nach außen nur Markentrix:** nie Tool-/Modellnamen im Code-Kommentar, Footer, Meta-Tags oder Texten. Keine erfundenen Kontaktdaten: nur markentrix.de · info@markentrix.de · Celle, Niedersachsen (Telefon/Anschrift/USt-ID aus den Projektdaten, sonst Platzhalter).
10. **Kein Dark-Pattern:** Cookie-„Ablehnen“ gleichwertig zu „Akzeptieren“, keine Fake-Countdowns, keine falsche Verknappung, keine vorangekreuzten Häkchen.

## 3. Marke (CI) im Web
- Wirkung: modern, premium, präzise, seriös, messbar. Nie: verspielt, billig, generisch, Neon, Krypto, Dark-First.
- Farben als CSS-Tokens (siehe `assets/starter/tokens.css`): Soft White #F8FAFC / White #FFFFFF (~65 %), Graphite Navy #0B1020 / Black #05070B (~18 %), Cyan #28C7F7 / Blue #1E9BFF (~12 %), Violet #8B5CF6 (~4 %), Magenta #D85CFF (~1 %), Cool Gray #B8C0CC, Muted Gray #667085.
- **Kontrast-Falle:** Cyan #28C7F7 auf Weiß erreicht keine 4.5:1. Cyan/Blue nur für Flächen, große Grafiken, Buttons mit dunklem Text (#0B1020) oder als Verlauf mit Navy-Text. Fließtext/Links auf Weiß: Navy #0B1020 oder Blue abgedunkelt (≥ 4.5:1 prüfen). Muted Gray #667085 auf Weiß ≈ 4.8:1, okay für Text ≥ 16 px, nicht für kleine Hilfstexte auf Grau.
- Typo: Space Grotesk (Headlines), Inter (Text), als selbst gehostete WOFF2, variable Fonts, Subset Latin, `font-display: swap`, Preload nur der kritischen Schnitte. Fluid Type per `clamp()`.
- Signature: Wachstumskurve, max. EIN dominantes Element pro Fläche. Viel Weißraum.
- Logo: nach CI-Regeln (Schutzraum, min. 120 px, nie verzerrt/umgefärbt), als SVG, mit `alt="Markentrix"` bzw. als Link zur Startseite mit zugänglichem Namen.
- CTA: genau ein Primär-CTA pro Seite (Cyan→Blue Verlauf, Navy-Text), Standard „Marketing-Check anfragen“, wiederholt an festen Stellen, immer derselbe Wortlaut.
- Ton: Direkt statt laut. Fachlich statt generisch. Nutzenorientiert. Anrede wie im Videoskill (Du/ihr vs. Sie je Branche, eine Anrede pro Seite).

## 4. Arbeitsablauf
1. **Briefing klären** (nur fehlendes erfragen): Ziel (Anfrage/Termin/Info), Zielgruppe + Branche, Angebot, ein Primär-CTA, Pflichtdaten fürs Impressum, vorhandene Assets, Zielsprache, Tracking gewünscht ja/nein, Hosting.
2. **Struktur & Copy** nach `references/conversion-landingpage.md`: ein Seitenziel, ein Schmerzpunkt, ein CTA. Copy zuerst, dann Design.
3. **Bauen** ab `assets/starter/` (reines HTML/CSS/JS, kein Framework nötig). Framework (Astro bevorzugt für statische Seiten) nur bei Mehrseiten-Projekten mit Content-Pflege; kein SPA-Zwang, kein Client-Rendering für Content.
4. **Animation** nach `references/animation.md` (CSS first, transform/opacity only, Reduced-Motion).
5. **Recht** nach `references/dsgvo-recht.md`: Formular, Consent, Impressum, Datenschutz, Auftragsverarbeiter.
6. **Barrierefreiheit** nach `references/barrierefreiheit.md`.
7. **Performance** nach `references/performance.md`.
8. **Audit:** `bash scripts/audit.sh <ordner>` muss ohne FAIL laufen; danach Lighthouse/PageSpeed (mobil), axe, manueller Tastatur- und Screenreader-Check, Ergebnis im Hand-off.
9. **Hand-off** (Abschnitt 8).

## 5. Technische Standards
- Semantisches HTML5: ein `<h1>`, logische Überschriften, `<header> <nav> <main> <footer>`, Skip-Link, `lang="de"`, `<title>` ≤ 60 Zeichen, Meta-Description 120–155 Zeichen, Canonical, Open-Graph/Twitter-Card, `theme-color`.
- Mobile-first, Breakpoints per Container/`min-width`, kein horizontaler Scroll bei 320 px, Zoom bis 400 % nutzbar, Touch-Ziele ≥ 24×24 px (Ziel 44×44).
- CSS: Custom Properties, `clamp()`, Grid/Flex, `:focus-visible`, `color-scheme`, kein CSS-Framework-Ballast. Kritisches CSS inline (< 14 KB), Rest async.
- JS: minimal, `defer`/Module, keine jQuery, keine Abhängigkeiten ohne Grund, progressive Enhancement (Seite funktioniert ohne JS, nur Animation/Menü verbessern).
- Formulare: native Elemente, sichtbare `<label>`, `autocomplete`, Fehlertexte per `aria-describedby`/`role="alert"`, Spam-Schutz ohne Google reCAPTCHA (Honeypot + Zeitcheck, serverseitiges Rate-Limit, ggf. Cloudflare Turnstile/hCaptcha nur nach Consent-/AVV-Prüfung).
- Sicherheits-Header am Hosting: CSP (kein `unsafe-inline` wo vermeidbar), HSTS, `X-Content-Type-Options`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`. Vorlage in `references/performance.md`.
- Bilder: AVIF/WebP mit Fallback, `width`/`height` gesetzt, `loading="lazy"` außer Hero, `fetchpriority="high"` für das LCP-Bild, sinnvolle `alt`-Texte (dekorativ = `alt=""`).
- Hosting: EU-Region, HTTPS, AVV mit Hoster. Cache-Header, Brotli, HTTP/2+.

## 6. Performance-Budget (mobil, Mittelklasse-Gerät, 4G)
| Metrik | Ziel |
|---|---|
| LCP | ≤ 2,0 s (Grenze 2,5 s) |
| INP | ≤ 150 ms (Grenze 200 ms) |
| CLS | ≤ 0,05 (Grenze 0,1) |
| TTFB | ≤ 0,6 s |
| Lighthouse Mobil | Performance ≥ 95, A11y 100, Best Practices 100, SEO 100 |
| Seitengewicht | ≤ 500 KB initial (ohne Lazy), JS ≤ 60 KB gzip |
| Requests initial | ≤ 20, 0 Drittanbieter |
Messen mit Lighthouse (Lab) und, wenn Daten vorhanden, CrUX/PageSpeed (Feld). Lab-Wert allein beweist nichts für Feldwerte, im Hand-off so benennen.

## 7. Qualitäts-Gate vor Auslieferung
- [ ] `scripts/audit.sh` ohne FAIL
- [ ] Lighthouse mobil gemäß Budget (Screenshot/Werte im Hand-off)
- [ ] axe/WAVE ohne Fehler, Tastatur-Durchlauf, Screenreader-Stichprobe (VoiceOver/NVDA)
- [ ] 320 px, 768 px, 1280 px, 1920 px visuell geprüft, 200 %/400 % Zoom
- [ ] `prefers-reduced-motion` getestet
- [ ] Netzwerk-Tab: 0 Drittanbieter-Requests vor Consent
- [ ] Impressum, Datenschutz, Cookie-/Consent-Lösung, Formular-Hinweise geprüft
- [ ] Alle Aussagen gegen Allowlist, keine Platzhalter live
- [ ] OG-Bild, Favicon-Set, 404-Seite, `robots.txt`, `sitemap.xml`
- [ ] Formular Ende-zu-Ende getestet (Zustellung, Bestätigung, Fehlerfall)

## 8. Hand-off
Kurz und ehrlich: was gebaut ist, Messwerte (Lab vs. Feld getrennt), offene Punkte (Rechtstexte zur anwaltlichen Prüfung, fehlende Kundendaten, Platzhalter), Pflegehinweise (Preise/Claims gegen Preisliste prüfen, Cookie-Liste bei neuem Tool aktualisieren). Absender „Markentrix“.

## 9. Referenzen
- `references/dsgvo-recht.md`: TDDDG/DSGVO, Consent, Impressum, BFSG, Formulare, Tracking, Lead-Ads-Landingpages
- `references/barrierefreiheit.md`: WCAG 2.2 AA Umsetzung + Testplan
- `references/performance.md`: Budget, LCP/INP/CLS-Rezepte, Header, Bilder, Fonts
- `references/animation.md`: Motion-Prinzipien, Rezepte, Reduced-Motion
- `references/conversion-landingpage.md`: Seitenaufbau, Copy-Muster, Vertrauen ohne erfundene Beweise
- `references/seo.md`: Technik-SEO, lokales SEO, strukturierte Daten
