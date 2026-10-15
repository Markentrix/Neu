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

## Hetzner / Caddy (tatsächlicher Live-Server, Stand 15.10.2026)
Caddy 2 läuft als Docker-Container (`/opt/neu/server/docker-compose.yml`), Webroot `/srv/sites/markentrix`, Domain-Dateien in `/srv/caddy-sites/`. Upload per `docs/server/veroeffentlichen.bat` aus einer mit `tools/paket.sh` erzeugten `markentrix-website.zip` (Anleitung `docs/server/AENDERN-UND-VEROEFFENTLICHEN.md`). Formular-Endpunkt über einen PHP-FPM-Container, Mailversand per SMTP über Google Workspace. Komplette Anleitung mit allen Dateien: `docs/server/EINSPIELEN.md`. Die nginx-Datei unten bleibt als Alternative für einen anderen Server.

## Hetzner / nginx
`docs/nginx-markentrix.conf` (HTTPS, www → ohne www, try_files für `.html`-lose URLs, 301 alte Pfade, Header, Caching).
Upload: `rsync -a --delete dist/ user@server:/var/www/markentrix/`

### Schritt für Schritt (Ubuntu/Debian, Zugang per SSH als root oder mit sudo)

1. Voraussetzungen prüfen: nginx, PHP-FPM und ein Let's-Encrypt-Zertifikat müssen vorhanden sein.
   ```
   nginx -v
   ls /run/php/            # zeigt z. B. php8.2-fpm.sock
   ls /etc/letsencrypt/live/markentrix.de/
   ```
   Fehlt PHP-FPM: `apt install php-fpm`. Fehlt das Zertifikat: `apt install certbot python3-certbot-nginx` und `certbot certonly --nginx -d markentrix.de -d www.markentrix.de`.
2. Webroot anlegen und Dateien hochladen (vom eigenen Rechner aus, aus dem entpackten Ordner `markentrix-website/`):
   ```
   ssh root@SERVER "mkdir -p /var/www/markentrix"
   rsync -a --delete markentrix-website/ root@SERVER:/var/www/markentrix/
   ```
3. Konfiguration hochladen und aktivieren:
   ```
   scp nginx-markentrix.conf root@SERVER:/etc/nginx/sites-available/markentrix.de
   ssh root@SERVER
   ln -s /etc/nginx/sites-available/markentrix.de /etc/nginx/sites-enabled/markentrix.de
   rm -f /etc/nginx/sites-enabled/default     # nur falls die Standardseite noch aktiv ist
   ```
4. Zwei Stellen in der Datei prüfen (`nano /etc/nginx/sites-available/markentrix.de`): `root /var/www/markentrix;` muss zum Upload-Ordner passen, `fastcgi_pass unix:/run/php/php8.2-fpm.sock;` muss zur Ausgabe von `ls /run/php/` passen.
5. Testen und neu laden. `nginx -t` muss „syntax is ok“ und „test is successful“ melden, erst dann neu laden:
   ```
   nginx -t
   systemctl reload nginx
   ```
6. Rechte für das Formularprotokoll: `anfrage.php` schreibt nach `/var/www/anfragen.log` (eine Ebene über dem Webroot). Der PHP-Benutzer braucht Schreibrecht:
   ```
   touch /var/www/anfragen.log
   chown www-data:www-data /var/www/anfragen.log
   chmod 640 /var/www/anfragen.log
   ```
7. Kontrolle von außen (vom eigenen Rechner):
   ```
   curl -I https://markentrix.de/preise          # erwartet: 200 und X-Frame-Options: SAMEORIGIN
   curl -I https://markentrix.de/preise.html     # erwartet: 301 auf /preise
   curl -I https://www.markentrix.de/            # erwartet: 301 auf https://markentrix.de/
   curl -I https://markentrix.de/Preise.dc.html  # erwartet: 301 auf /preise
   ```
   Dann im Browser die Startseite öffnen: Die Miniatur muss die Beispiel-Landingpage zeigen, und eine Testanfrage über das Kontaktformular muss per Mail ankommen.

Bei jedem späteren Update reicht Schritt 2. Die nginx-Datei bleibt unverändert.

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
- **Auswertung ohne Cookies**: `python3 tools/anfragen-report.py /pfad/zu/anfragen.log --monate 6` zählt Anfragen je Monat nach Herkunft (Kontaktformular, Potenzial-Check), Bedarf, Leistung und Seite. Das Protokoll liegt eine Ebene über dem Webroot und enthält personenbezogene Daten: nur auf dem Server auswerten, nicht kopieren, nach der gesetzlichen Frist löschen.
- Testanfrage über /kontakt und über das Potenzial-Check-Modal → Eingang im Postfach info@markentrix.de prüfen; bei Fehlern `anfragen.log` und das PHP-Fehlerprotokoll des Servers ansehen.
- Cookie-Banner: „Nur notwendige“ → keine Verbindung zu Google/Metricool (Netzwerk-Tab).
- Lighthouse mobil, Rich-Results-Test (JSON-LD), Sitemap in der Search Console einreichen.
