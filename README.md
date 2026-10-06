# Bar Zeitreise Celle – Redesign

Statische Website, kein Build nötig. Alle Dateien in dasselbe Verzeichnis des Webspace hochladen (Startseite: `index.html`).

## Inhalt
- `index.html`, `styles.css`, `app.js` – One-Pager mit Party-Modus, Jahrzehnt-Umschalter, Live-Öffnungsstatus, WhatsApp-Reservierung, FAQ
- `impressum.html`, `datenschutz.html` – Texte der alten Seite (Datenschutz um WhatsApp-Formular und lokale Schriften ergänzt)
- `img/` – echte Fotos der Originalseite als WebP (640/1200 px) + `og-bar-zeitreise-celle.jpg`
- `fonts/` – selbst gehostete Schriften (kein Google-Fonts-Aufruf, DSGVO)
- SEO/GEO: `robots.txt`, `sitemap.xml`, `llms.txt`, `manifest.webmanifest`, Schema.org JSON-LD (BarOrPub, FAQPage, ReserveAction …), Geo-Meta-Tags, `404.html`
- `.htaccess` – Kompression, Caching, Sicherheits-Header (nur Apache)

## Nach dem Livegang
1. Domain in Google Search Console eintragen, `sitemap.xml` einreichen
2. Google-Unternehmensprofil (Name, Adresse, Telefon, Zeiten) identisch zur Website pflegen
3. Schema prüfen: https://search.google.com/test/rich-results
