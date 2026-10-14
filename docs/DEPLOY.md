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
- **Formulare (eigener Endpunkt auf dem Hetzner-Server)**: `dist/api/anfrage.php` nimmt Kontaktformular und Potenzial-Check per JSON entgegen, prüft Honeypot, Pflichtfelder und Ratenbegrenzung, mailt an info@markentrix.de (Absender website@markentrix.de, Reply-To = Absender der Anfrage) und schreibt optional ein Protokoll `anfragen.log` eine Ebene über dem Webroot. Voraussetzungen auf dem Server: PHP-FPM und ein funktionierender Mailversand (`sendmail`/postfix oder msmtp; SPF/DKIM für website@markentrix.de beim Hoster eintragen). nginx-Block für `/api/anfrage.php` siehe `docs/nginx-markentrix.conf`. Ein Webhook (z. B. neues n8n) wird in `$CONFIG['webhook']` eingetragen.
- Stand 14.10.2026: Der frühere n8n-Webhook `markentrix.app.n8n.cloud/webhook/markentrix-anfrage` antwortet mit „404 – No instance here“ (Instanz existiert nicht mehr). Deshalb versendet auch die bisherige Live-Seite keine Anfragen.
- Testanfrage über /kontakt und über das Potenzial-Check-Modal → Eingang im Postfach info@markentrix.de prüfen; bei Fehlern `anfragen.log` und das PHP-Fehlerprotokoll des Servers ansehen.
- Cookie-Banner: „Nur notwendige“ → keine Verbindung zu Google/Metricool (Netzwerk-Tab).
- Lighthouse mobil, Rich-Results-Test (JSON-LD), Sitemap in der Search Console einreichen.
