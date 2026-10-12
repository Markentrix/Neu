# Deployment Markentrix · Stand 12.10.2026

## Prinzip
Quelle sind `src/` und `static/`. `python3 tools/build.py --check` erzeugt `dist/`. Veröffentlicht wird **nur `dist/`**. `dist/` liegt mit im Repository, damit Netlify ohne Build-Schritt auskommt (`netlify.toml` → `publish = "dist"`).

Änderung → bauen → prüfen → `dist/` mit committen → pushen. Netlify deployt den Branch `main` automatisch, sobald er verbunden ist.

## Inhalt von dist/
```
index.html, preise.html, kontakt.html, … (22 indexierbare Seiten + 404.html + ki-checkliste.html)
leistungen/*.html · blog/*.html
assets/mx.css · assets/site.js · assets/consent.js
fonts/ (lokale WOFF2, DSGVO-konform) · img/ (WebP) · favicon.svg · apple-touch-icon.png · og-image.png
_headers · robots.txt · sitemap.xml (wird generiert) · llms.txt
```
Nicht enthalten: `src/`, `docs/`, `tools/`.

## Netlify
`publish = "dist"`, sprechende URLs ohne `.html` (Netlify Pretty URLs), 301-Weiterleitungen alter `.dc.html`-Pfade in `netlify.toml`. `404.html` wird automatisch als Fehlerseite verwendet. Sicherheits- und Cache-Header in `dist/_headers`.

## Hetzner / nginx
`docs/nginx-markentrix.conf` (HTTPS, www → ohne www, try_files für `.html`-lose URLs, 301 alte Pfade, Header, Caching).
Upload: `rsync -a --delete dist/ user@server:/var/www/markentrix/`

## Abnahmetests nach Deploy
```
curl -I https://markentrix.de/                  → 200
curl -I https://markentrix.de/preise            → 200
curl -I https://markentrix.de/Preise.dc.html    → 301 → /preise
curl -I https://markentrix.de/gibtsnicht        → 404 (eigene Seite)
curl -I https://markentrix.de/assets/mx.css     → 200, Cache-Control immutable
```
- Ohne JavaScript: alle Texte, Preise und Rechtstexte lesbar. Formulare, Rechner und Kalender brauchen JavaScript.
- Testanfrage über /kontakt und über das Potenzial-Check-Modal → Eingang im n8n-Workflow `markentrix-anfrage` prüfen (Felder: `quelle, name, firma, email, tel, thema, budget, nachricht_text, wunschtermin, termin_iso, nachricht, seite, zeit`).
- Cookie-Banner: „Nur notwendige“ → keine Verbindung zu Google/Metricool (Netzwerk-Tab).
- Lighthouse mobil, Rich-Results-Test (JSON-LD), Sitemap in der Search Console einreichen.
