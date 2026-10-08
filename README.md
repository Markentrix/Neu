# ElbDetail – Website

Statische, verkaufsorientierte Website für **ElbDetail – Premium Fahrzeugaufbereitung Celle**.
Kein Build-Schritt, kein Framework, kein Tracking: Die Dateien können direkt auf jedes Hosting
(Netlify, IONOS, Strato, all-inkl …) hochgeladen werden.

## Struktur

| Datei / Ordner | Zweck |
| --- | --- |
| `index.html` | Startseite: Hero mit Richtpreis-Rechner, Anlässe, Leistungen, Pakete & Preise, Vorher/Nachher, Warum ElbDetail, Ablauf, Bewertungen, Einzugsgebiet, FAQ, Kontakt |
| `leistungen/*.html` | 5 SEO-Landingpages (Außen, Innen, Lackpolitur, Lackversiegelung, Leasingrückgabe/Verkauf) mit eigenem Service-, FAQ- und Breadcrumb-Schema |
| `impressum.html`, `datenschutz.html` | Rechtsseiten mit markierten Platzhaltern |
| `404.html` | Fehlerseite |
| `styles.css`, `script.js` | Design und Interaktion (Rechner, Preis-Umschalter, Vorher/Nachher-Slider, Formular, FAQ, Menü) |
| `robots.txt`, `sitemap.xml` | Suchmaschinen |
| `llms.txt`, `llms-full.txt` | Fakten für KI-Suchmaschinen (GEO) |
| `og-image.png`, `apple-touch-icon.png`, `favicon.svg`, `site.webmanifest` | Social Preview, Icons |
| `netlify.toml`, `.htaccess` | Security-Header, Caching, HTTPS/www-Redirect, 404 (je nach Hosting eine der beiden Dateien) |

## Vor dem Livegang ausfüllen / prüfen

1. **Impressum & Datenschutz**: alle blau markierten Platzhalter (Inhaber, USt-IdNr., Hosting-Anbieter) ausfüllen und rechtlich prüfen lassen.
2. **Preisfaktoren**: In `script.js` oben stehen die Richtpreise (79 / 179 / 349 €) und die Zuschlagsfaktoren für Limousine/Kombi (+15 %) und SUV/Van (+30 %). Bei Bedarf anpassen.
3. **Öffnungszeiten im Schema**: `index.html` enthält `openingHoursSpecification` Mo–Sa 08:00–18:00 als Rahmen für „Termine nach Vereinbarung“. Anpassen, falls anders.
4. **Vorher/Nachher-Fotos**: In `index.html` im Abschnitt `#vorher-nachher` die drei `<svg class="ba-art">`-Platzhalter durch `<img class="ba-art" src="…" alt="…">` (vorher) und `<img class="ba-art ba-after" …>` (nachher) ersetzen, Format 4:3.
5. **Google-Bewertungen**: Zahl (19) und Zitate bei Änderungen in `index.html`, `llms.txt` und im JSON-LD aktualisieren.
6. **Domain**: Alle absoluten URLs zeigen auf `https://www.elbdetail.de/`.
7. **Google Business Profile** mit identischer Adresse/Telefon pflegen und die Website dort verlinken.
8. Nach dem Livegang: Google Search Console einrichten, `sitemap.xml` einreichen, Rich-Results-Test für Startseite und eine Leistungsseite durchführen.

## Formular

Das Kontaktformular speichert nichts auf einem Server. Beim Absenden öffnet sich WhatsApp (Standard)
oder das E-Mail-Programm mit vorausgefüllter Anfrage. Soll später ein Server-Versand ergänzt werden,
bietet sich Netlify Forms oder ein Dienst wie Formspree an.
