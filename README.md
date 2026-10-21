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

## Installation auf dem Markentrix-Server (Hetzner)

Passend zum bestehenden Server-Setup (`/opt/neu/server`, Branch `claude/hetzner-server-setup-p0bxzs`):
ein gemeinsamer Caddy für alle Domains, Apps als Container im Docker-Netz `web`.
Die Website ist komplett eigenständig: **kein Supabase, kein n8n**. Termine liegen in einer SQLite-Datei im Container-Volume.

Weil die Seite PHP braucht (Buchung, PayPal), läuft sie **nicht** als statischer Ordner unter `/srv/sites/kunden/…`,
sondern als App-Container `aj-atelier`, an den Caddy per `reverse_proxy` weiterleitet.

**Einmalig, per SSH als `deploy`** (`ssh deploy@5.75.146.212`):

```bash
# 1. Code holen
sudo mkdir -p /srv/apps && sudo chown deploy:deploy /srv/apps
git clone -b ccr-2f7c4155-wki5dk https://github.com/Markentrix/Neu.git /srv/apps/aj-atelier
cd /srv/apps/aj-atelier

# 2. Konfiguration (Admin-Passwort, PayPal, SMTP) – Datei bleibt nur auf dem Server
cp app/config.local.example.php app/config.local.php
docker run --rm php:8.3-cli php -r "echo password_hash('IHR-PASSWORT', PASSWORD_DEFAULT), PHP_EOL;"
nano app/config.local.php

# 3. Container bauen und starten (hängt sich ins Netz "web")
docker compose up -d --build

# 4a. Vorschau für den Kunden (noindex + Passwort, Benutzer "vorschau")
deploy/einrichten.sh MX-XXXX mx-xxxx.vorschau.markentrix.de --vorschau --passwort

# 4b. Später live (DNS-A-Eintrag von domain.de und www.domain.de vorher auf 5.75.146.212)
deploy/einrichten.sh MX-XXXX aj-atelier-wettmar.de
```

`MX-XXXX` = Kundennummer von AJ Atelier aus dem CRM. `einrichten.sh` legt wie `kunde-anlegen.sh`
eine Datei `/srv/caddy-sites/kunde-MX-XXXX-<domain>.caddy` an, prüft die Caddy-Konfiguration und lädt sie neu.
Nach dem Live-Schalten in `app/config.local.php` die `siteUrl` auf die echte Domain setzen und `docker compose restart` ausführen.

**Updates einspielen:** `cd /srv/apps/aj-atelier && git pull && docker compose up -d --build`

**Backup:** Das Server-Backup sichert nur `/srv/sites` und `/srv/caddy-sites`. Für die Termine zusätzlich einen Cron-Eintrag anlegen
(`crontab -e` als deploy):
`45 3 * * * /srv/apps/aj-atelier/deploy/backup.sh >> /var/log/backup.log 2>&1`
→ täglich `/srv/backups/daily/aj-atelier-DATUM.sqlite`, 14 Tage aufbewahrt.

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

## Ohne Docker: nginx statt Apache

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

## Seiten

| Adresse | Inhalt |
|---|---|
| `/` | Startseite mit Leistungen, Preisauszug, Online-Buchung, FAQ, Kontakt |
| `/leistungen` | Übersicht aller Leistungen |
| `/leistungen/balayage`, `/babylights`, `/damenhaarschnitt`, `/hochsteckfrisuren`, `/herren`, `/farbe`, `/pflege`, `/augenbrauen-wimpern` | Leistungsseiten mit Ablauf, Preisen, Dauer, FAQ und Direktbuchung |
| `/preise` | Komplette Preisliste + Zahlungsarten |
| `/termin` | Online-Terminbuchung (`/termin?leistung=f-balayage` wählt die Leistung vor) |
| `/ueber-uns`, `/kontakt` (mit Formular), `/faq` | Salon-Seiten |
| `/friseur-burgwedel`, `/friseur-isernhagen`, `/friseur-langenhagen`, `/friseur-hannover` | Ortsseiten mit echter Anfahrtszeit (OpenStreetMap) |
| `/impressum`, `/datenschutz` | Rechtliches (noindex) |
| `/sitemap.xml`, `/robots.txt`, `/llms.txt` | werden automatisch aus den Inhalten erzeugt |

**SEO & GEO je Seite:** eigener Titel und Beschreibung, Canonical, Brotkrumen (`BreadcrumbList`), `HairSalon` mit Geo-Koordinaten
und Öffnungszeiten, `Service` mit Preisen auf Leistungsseiten, `FAQPage` wo Fragen stehen, Geo-Meta-Tags, `llms.txt` für KI-Suche.

**Texte ändern:** Leistungsseiten in `app/content/leistungen.php`, Ortsseiten in `app/content/orte.php`,
allgemeine FAQ in `app/routes.php` (`general_faq`). Preise und Dauer immer nur in `app/config.php`.

## Aufbau

```
app/                      nicht öffentlich
  config.php              Salon-Daten, Preise, Öffnungszeiten (hier pflegen)
  config.local.php        Passwörter & Zugangsdaten (nicht im Git)
  content/                Texte der Leistungs- und Ortsseiten
  pages/                  Seitenvorlagen
  routes.php              Seitenverzeichnis, Weiterleitungen, allgemeine FAQ
  partials.php            Bausteine (Preisliste, Buchung, FAQ, Karten …)
  layout.php              Kopf, Navigation, Footer, strukturierte Daten
  lib.php                 Terminlogik, Datenbank, PayPal, E-Mail
  data/                   SQLite-Datenbank (nicht im Git)
public/                   Document Root
  index.php               Front-Controller für saubere URLs
  api/                    availability, booking, paypal-order, cancel, contact, admin
  admin/                  Terminverwaltung
  css/ js/ fonts/ img/
```
