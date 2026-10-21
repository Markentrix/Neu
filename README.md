# AJ Atelier – Website mit Online-Terminbuchung & PayPal

Website für **AJ Atelier – Hair & Beauty**, Friseur in der Hauptstraße 64, 30938 Burgwedel-Wettmar.

- Einseitige Website (Leistungen, Preisliste, Über uns, FAQ, Kontakt/Öffnungszeiten)
- **Buchungssystem**: Leistungen wählen (mehrere) → freien Termin wählen → Daten → Zahlung
  - Freie Zeiten werden live aus Öffnungszeiten, Dauer der Leistungen, vorhandenen Buchungen und Blockern berechnet
  - Feiertage Niedersachsen, Heiligabend/Silvester automatisch geschlossen
  - Doppelbuchungen sind per Datenbank-Transaktion ausgeschlossen
  - Bestätigungs-Mail an Kund:in + Benachrichtigung an den Salon, Kalender-Datei (.ics)
  - Kostenfreie Online-Stornierung bis 24 h vorher (mit automatischer PayPal-Erstattung)
- **PayPal**: Festpreise werden komplett bezahlt, bei „ab“-Preisen eine Anzahlung. Der Betrag wird nur auf dem Server berechnet und nach der Zahlung geprüft – Manipulation im Browser ist nicht möglich.
- **Terminverwaltung** unter `/admin/`: Wochenansicht, Zeiten blockieren (Pause, Telefon-Termine, Urlaub), Termine absagen (optional mit Erstattung und Mail)
- **SEO & GEO**: strukturierte Daten (`HairSalon` mit Adresse, Geo-Koordinaten, Öffnungszeiten, kompletter Preisliste, Buchungs-Aktion; `FAQPage`), Geo-Meta-Tags, Open-Graph-Bild, `sitemap.xml`, `robots.txt` (KI-Crawler erlaubt), `llms.txt` für ChatGPT/Claude/Perplexity, schnelle Ladezeit ohne Frameworks
- **DSGVO**: keine Cookies für Besucher:innen, kein Tracking, Schriften lokal, PayPal wird erst bei Auswahl geladen, Karten nur als Link

## Installation auf dem eigenen Hetzner-Server (empfohlen: Docker)

Die Website ist komplett eigenständig: **kein Supabase, kein n8n, keine externe Datenbank**.
Termine liegen in einer SQLite-Datei auf dem Server, HTTPS-Zertifikate holt Caddy automatisch.

**Einmalig auf dem Server** (Ubuntu/Debian, per SSH als root):

```bash
# 1. Docker installieren (falls noch nicht vorhanden)
curl -fsSL https://get.docker.com | sh

# 2. Projekt holen
git clone https://github.com/Markentrix/Neu.git /opt/aj-atelier
cd /opt/aj-atelier

# 3. Konfiguration
cp deploy/.env.example deploy/.env                    # DOMAIN=… eintragen
cp app/config.local.example.php app/config.local.php  # Passwort, PayPal, SMTP eintragen
php -r "echo password_hash('IHR-PASSWORT', PASSWORD_DEFAULT), PHP_EOL;"   # oder:
docker run --rm php:8.3-cli php -r "echo password_hash('IHR-PASSWORT', PASSWORD_DEFAULT), PHP_EOL;"

# 4. Starten
docker compose up -d --build
```

Vorher im DNS der Domain **A-Records für `domain.de` und `www.domain.de` auf die IP des Hetzner-Servers** setzen
und in der Hetzner-Firewall die Ports **80 und 443** freigeben.

**Updates einspielen:**

```bash
cd /opt/aj-atelier && git pull && docker compose up -d --build
```

Die Termine liegen im Docker-Volume `bookings` und bleiben bei Updates erhalten.
Tägliche Sicherung per Cron: `15 3 * * * /opt/aj-atelier/deploy/backup.sh` (legt 30 Tage Backups in `backups/` ab).

**Laufen auf dem Server schon andere Websites** mit eigenem nginx/Caddy/Traefik auf Port 80/443?
Dann den `caddy`-Dienst in `docker-compose.yml` weglassen, beim `web`-Dienst `ports: ["127.0.0.1:8081:80"]` ergänzen
und im vorhandenen Proxy die Domain auf `http://127.0.0.1:8081` weiterleiten (mit Header `X-Forwarded-Proto: https`).

### E-Mail auf Hetzner

Hetzner sperrt bei neuen Servern ausgehenden Port 25, d. h. PHP `mail()` kommt meist nicht an.
Deshalb in `config.local.php` unter `mail.smtp` die SMTP-Daten eines echten Postfachs eintragen
(z. B. Hetzner-Webhosting-Postfach `mail.your-server.de`, Port 587, oder Google Workspace/IONOS/Strato).
Absender (`mail.from`) = dieses Postfach, damit die Mails nicht im Spam landen.

### Alternative: klassischer Webspace / Hosting-Panel

Läuft auch ohne Docker auf jedem Webspace mit PHP 8.1+ (`pdo_sqlite`, `curl`, `mbstring`) und Apache:
Dateien hochladen, Document Root auf `public/` stellen, `app/config.local.php` anlegen, SSL aktivieren.
Der Ordner `app/data/` muss für PHP beschreibbar sein. `app/` ist zusätzlich per `.htaccess` gesperrt.

## PayPal einrichten

1. Auf <https://developer.paypal.com/dashboard/applications> mit dem PayPal-**Geschäftskonto** anmelden.
2. Unter *Sandbox* eine App anlegen → Client-ID und Secret in `config.local.php` eintragen, `env` = `sandbox`.
3. Mit einem Sandbox-Käuferkonto testen.
4. Danach unter *Live* eine App anlegen, Live-Zugangsdaten eintragen und `env` = `live` setzen.

Ohne PayPal-Daten funktioniert die Buchung weiterhin – dann nur mit „Vor Ort bezahlen“.

## Preise, Zeiten, Urlaub ändern

Alles steht in **`app/config.php`** – Website, Preisliste, Google-Daten, `llms.txt` und Buchungssystem übernehmen Änderungen automatisch:

- `categories` – Leistungen, Preise, Dauer in Minuten, Anzahlung (`deposit`) für „ab“-Preise
- `hours` – Öffnungszeiten je Wochentag
- `closedDates` – Urlaubstage, z. B. `['2026-12-28', '2026-12-29']`
- `booking.capacity` – wie viele Kund:innen gleichzeitig (Anzahl Stylist:innen)
- `booking.leadTime`, `horizonDays`, `freeCancelHours` – Vorlauf, Buchungszeitraum, Stornofrist

Einzelne Zeiten (Pause, Arzttermin, telefonisch vergebener Termin) blockiert man in der Verwaltung unter `/admin/`.

## Vor dem Livegang erledigen

- [ ] Testbuchung durchführen und unter `https://ihre-domain.de/admin/` prüfen, Test-Mail kontrollieren
- [ ] Platzhalter in **Impressum** und **Datenschutz** ausfüllen (gelb markiert) und rechtlich prüfen lassen
- [ ] Domain `www.aj-atelier-wettmar.de` ist ein Platzhalter – echte Domain in `config.local.php` (`siteUrl`) eintragen
- [ ] Dauer der Leistungen in `app/config.php` mit dem Salon abstimmen
- [ ] **Google Unternehmensprofil** anlegen/prüfen: exakt gleiche Schreibweise von Name, Adresse, Telefon (NAP) wie auf der Website, Website-Link + Buchungslink `https://…/#termin` hinterlegen
- [ ] Website in der **Google Search Console** und **Bing Webmaster Tools** anmelden, `sitemap.xml` einreichen
- [ ] Website-Link in der Instagram-Bio hinterlegen
- [ ] Echte Salon-/Arbeitsfotos ergänzen (stärkt Vertrauen und lokale Suche)

## nginx statt Apache

```nginx
root /pfad/zu/public;
index index.php;
location ^~ /app/ { deny all; }
location = /robots.txt  { rewrite ^ /robots.php last; }
location = /sitemap.xml { rewrite ^ /sitemap.php last; }
location = /llms.txt    { rewrite ^ /llms.php last; }
error_page 404 /404.php;
location ~ \.php$ { include fastcgi_params; fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name; fastcgi_pass unix:/run/php/php8.3-fpm.sock; }
```

## Lokal testen

```bash
php -S localhost:8000 -t public dev-router.php
```

## Aufbau

```
app/                      nicht öffentlich
  config.php              Salon-Daten, Preise, Öffnungszeiten (hier pflegen)
  config.local.php        Passwörter & Zugangsdaten (nicht im Git)
  lib.php                 Terminlogik, Datenbank, PayPal, E-Mail
  layout.php              Seitenkopf/-fuß, strukturierte Daten
  data/                   SQLite-Datenbank (nicht im Git)
public/                   Document Root
  index.php               Startseite inkl. Buchung
  api/                    availability, booking, paypal-order, cancel, admin
  admin/                  Terminverwaltung
  css/ js/ fonts/ img/
```
