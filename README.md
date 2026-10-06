# Bar Zeitreise Celle – Redesign

Statische Website, kein Build nötig. Alle Dateien in dasselbe Verzeichnis des Webspace hochladen (Startseite: `index.html`).

## Inhalt
- `index.html`, `styles.css`, `app.js` – One-Pager mit Party-Modus, Jahrzehnt-Umschalter, Live-Öffnungsstatus, Kontaktkarten (Telefon, Instagram, Facebook), FAQ – keine Anfragen über die Website
- `impressum.html`, `datenschutz.html` – Texte der alten Seite (Datenschutz um den Abschnitt zu lokal eingebundenen Schriften ergänzt)
- `img/` – echte Fotos der Originalseite als WebP (640/1200 px) + `og-bar-zeitreise-celle.jpg`
- `fonts/` – selbst gehostete Schriften (kein Google-Fonts-Aufruf, DSGVO)
- SEO/GEO: `robots.txt`, `sitemap.xml`, `llms.txt`, `manifest.webmanifest`, Schema.org JSON-LD (BarOrPub, FAQPage, ReserveAction …), Geo-Meta-Tags, `404.html`
- `.htaccess` – Kompression, Caching, Sicherheits-Header (nur Apache)

## Events eintragen
Termine stehen in `events.json` (Liste, Standard: leer `[]`). Beispiel:
```json
[
  {
    "title": "80er Neon-Party",
    "date": "2026-10-23",
    "start": "20:00",
    "end": "01:00",
    "tag": "Motto-Party",
    "description": "Kurzer Text zum Abend.",
    "url": "https://www.instagram.com/p/…",
    "image": "img/mein-event-foto.webp",
    "image_alt": "Beschreibung des Fotos"
  }
]
```
Pflicht: `title`, `date` (JJJJ-MM-TT). Alles andere optional (Standard 20:00–01:00 Uhr). Danach `bash tools/build.sh` ausführen: erzeugt die Event-Karten und die Google-Event-Daten (Schema.org). Vergangene Termine blendet die Seite automatisch aus; ohne Termine erscheint ein Hinweis auf Instagram. Ohne Node.js: `events.json` einfach an den Entwickler schicken.

## Weiterentwickeln
Quelldateien: `styles.css`, `app.js`, `fonts/fonts.css`. Nach Änderungen `bash tools/build.sh` ausführen (Node.js nötig): erzeugt `app.min.js`, `styles.min.css` und bindet das CSS in `index.html` ein.

## Nach dem Livegang
1. Domain in Google Search Console eintragen, `sitemap.xml` einreichen
2. Google-Unternehmensprofil (Name, Adresse, Telefon, Zeiten) identisch zur Website pflegen
3. Schema prüfen: https://search.google.com/test/rich-results
