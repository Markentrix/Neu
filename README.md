# AJ Atelier – Website mit Online-Terminbuchung & PayPal

Website für **AJ Atelier – Hair & Beauty**, Friseur in der Hauptstraße 64, 30938 Burgwedel-Wettmar.

- Website mit 26 Seiten (Leistungen, Preise, Gutscheine, Ratgeber, Ortsseiten …), ausgeliefert als statischer Ordner `dist/` wie alle Markentrix-Kundenseiten
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

## Aufbau: statische Seiten + Buchungsdienst

Wie bei allen Markentrix-Kundenseiten wird **nur `dist/` veröffentlicht** (fertige HTML-Dateien:
`index.html`, `preise.html`, `leistungen/balayage.html` …). Zusätzlich läuft ein kleiner
**Buchungsdienst** (Container `aj-atelier`, PHP + SQLite) für alles, was der Server rechnen
oder speichern muss. Caddy leitet nur diese Adressen an den Container:

| Adresse | Zweck |
|---|---|
| `/api/*` | Freie Zeiten, Buchung, PayPal, Gutscheine, Kontaktformular, Storno |
| `/admin/` | Terminverwaltung & Gutscheine einlösen |
| `/gutschein-pdf`, `/termin-stornieren` | Links aus den E-Mails |

Alles andere liefert Caddy direkt aus `/srv/sites/kunden/<Kundennummer>` (Baustein `kunden_site`).

### `dist/` neu bauen (nach Text-, Preis- oder Domainänderungen)

```bash
php tools/build-static.php --url=https://www.aj-atelier-wettmar.de
```

Texte, Preise und Öffnungszeiten werden in `app/` gepflegt (siehe unten), **nicht direkt in `dist/`**,
denn Navigation, Footer, Preise und strukturierte Daten stehen auf vielen Seiten gleichzeitig.
Die buchbaren Tage und der PayPal-Status werden im Browser live vom Buchungsdienst geladen,
`dist/` veraltet also nicht.

## Online stellen auf dem Markentrix-Server (Hetzner)

**1. Buchungsdienst einmalig einrichten** (per SSH als `deploy`):

```bash
sudo mkdir -p /srv/apps && sudo chown deploy:deploy /srv/apps
git clone -b ccr-2f7c4155-wki5dk https://github.com/Markentrix/Neu.git /srv/apps/aj-atelier
cd /srv/apps/aj-atelier
cp app/config.local.example.php app/config.local.php
docker run --rm php:8.3-cli php -r "echo password_hash('IHR-PASSWORT', PASSWORD_DEFAULT), PHP_EOL;"
nano app/config.local.php          # siteUrl, Admin-Passwort, PayPal, SMTP eintragen
docker compose up -d --build       # Container „aj-atelier“ im Netz „web“
```

**2. Domain einrichten** – statt `kunde-anlegen.sh` dieses Skript verwenden (gleiches Schema, plus Weiterleitung zum Buchungsdienst):

```bash
deploy/einrichten.sh MX-XXXX mx-xxxx.vorschau.markentrix.de --vorschau --passwort   # Vorschau (noindex + Passwort)
deploy/einrichten.sh MX-XXXX aj-atelier-wettmar.de                                  # später live
```

**3. Seiten hochladen** – wie bei jeder Kundenseite: den Ordner `dist/` mit
`pc/kunde-veroeffentlichen.bat` hochladen (Kundennummer MX-XXXX). Vorher `dist/` mit der richtigen Domain bauen.

**Updates des Buchungsdienstes:** `cd /srv/apps/aj-atelier && git pull && docker compose up -d --build`

**Backup:** Das Server-Backup sichert `/srv/sites` und `/srv/caddy-sites`. Für die Termine zusätzlich (`crontab -e` als deploy):
`45 3 * * * /srv/apps/aj-atelier/deploy/backup.sh >> /var/log/backup.log 2>&1`
→ täglich `/srv/backups/daily/aj-atelier-DATUM.sqlite`, 14 Tage aufbewahrt.

### Automatische Aufgaben (Cron) – einmal einrichten

`crontab -e` als `deploy`, Domain anpassen:

```
# Erinnerungen & Bewertungsbitten (stündlich, verschickt nur tagsüber)
5 * * * *    docker exec aj-atelier php /var/www/site/app/cron.php >> /var/log/aj-atelier-cron.log 2>&1
# Sicherung der Termine (täglich)
45 3 * * *   /srv/apps/aj-atelier/deploy/backup.sh >> /var/log/aj-atelier-backup.log 2>&1
# Überwachung (alle 5 Minuten)
*/5 * * * *  /srv/apps/aj-atelier/deploy/monitor.sh https://aj-atelier-wettmar.de >> /var/log/aj-atelier-monitor.log 2>&1
# Backup-Prüfung mit Ergebnis-Mail (montags 7:10 Uhr)
10 7 * * 1   /srv/apps/aj-atelier/deploy/backup-check.sh >> /var/log/aj-atelier-backup.log 2>&1
```

Warnungen gehen an `alertEmail` in `app/config.local.php` (sonst an `salonEmail`).

| Aufgabe | Was passiert |
|---|---|
| **Terminerinnerung** | ca. 24 Std. vor dem Termin, mit Adresse und Storno-Link. Gehört zum Termin, keine Einwilligung nötig. Nicht bei Buchungen, die jünger als 6 Std. sind. |
| **Folgetermin-Erinnerung** | nur mit Häkchen bei der Buchung, einmalig, nach `rebookWeeks` der Leistung (`app/config.php`, z. B. Herrenschnitt 4, Ansatz 5, Balayage 14 Wochen). Entfällt, wenn schon ein neuer Termin gebucht ist. |
| **Bitte um Google-Bewertung** | nur mit Häkchen und eingetragenem `reviewUrl`, am Tag nach dem Termin. |
| **Überwachung** | prüft Startseite und `/api/health.php` (Datenbank, Speicher, Konfiguration, Mailversand der letzten Stunde, Cron). Nach 2 Fehlschlägen in Folge eine Warnmail, einmal pro Störung, plus Entwarnung. |
| **Backup-Prüfung** | prüft, ob die letzte Sicherung jünger als 26 Std. und lesbar ist, und schickt das Ergebnis jede Woche per Mail, auch wenn alles in Ordnung ist. |

### Updates sicher einspielen

```bash
cd /srv/apps/aj-atelier
deploy/update.sh                                        # nur Buchungsdienst
deploy/update.sh MX-XXXX https://aj-atelier-wettmar.de  # zusätzlich dist/ bauen und veröffentlichen
```

Das Skript holt die neue Version, **testet sie zuerst** (`tests/run.php`, ca. 80 Prüfungen: Buchung, Doppelbuchung,
Storno, Admin, Gutscheine, Erinnerungen, Überwachung, Build) und schaltet nur um, wenn alles grün ist.
Sonst läuft die bisherige Version weiter und es kommt eine Warnmail.
Auf GitHub laufen dieselben Tests bei jedem Push (Reiter „Actions“).

### E-Mail auf Hetzner

Hetzner sperrt bei neuen Servern ausgehenden Port 25, d. h. PHP `mail()` kommt meist nicht an.
Deshalb in `config.local.php` unter `mail.smtp` die SMTP-Daten eines echten Postfachs eintragen
(z. B. Hetzner-Webhosting-Postfach `mail.your-server.de`, Port 587, oder Google Workspace/IONOS/Strato).
Absender (`mail.from`) = dieses Postfach, damit die Mails nicht im Spam landen.

### Alternative: klassischer Webspace / Hosting-Panel

Läuft auch ohne Docker auf jedem Webspace mit PHP 8.1+ (`pdo_sqlite`, `curl`, `mbstring`) und Apache:
Dateien hochladen, Document Root auf `public/` stellen, `app/config.local.php` anlegen, SSL aktivieren.
Der Ordner `app/data/` muss für PHP beschreibbar sein. `app/` ist zusätzlich per `.htaccess` gesperrt.

## Google-Bewertungen & Google-Profil

1. Im **Google-Unternehmensprofil** unter „Mehr Rezensionen erhalten“ den Link kopieren (`https://g.page/r/…/review`)
   und in `app/config.php` bei `salon.reviewUrl` eintragen. Erst dann erscheint im Buchungsformular die
   freiwillige Einwilligung für die Bewertungs-Mail. Ohne Einwilligung wird nie eine Mail verschickt (BGH: Werbung).
2. Im Google-Profil unter **Buchungen / Terminlink** die Adresse `https://<domain>/termin` hinterlegen.
   Dann zeigt Google Maps einen „Termin buchen“-Knopf.
3. Name, Adresse und Telefon im Profil exakt so schreiben wie auf der Website.

## Gutscheine

- Kauf unter `/gutscheine`, Bezahlung nur per PayPal. Betrag frei wählbar (Grenzen in `config.php` → `vouchers`).
- Nach der Zahlung: Gutschein-PDF per E-Mail an die Käufer:in, Kopie der Info an `salonEmail`, Download-Link bleibt gültig.
- Gültigkeit: bis Jahresende + 3 Jahre (gesetzliche Verjährung).
- Einlösen in der Verwaltung `/admin/` → Tab **Gutscheine**: Code suchen, Betrag eintragen. Teilbeträge sind möglich,
  das Restguthaben wird angezeigt. Dort lässt sich das PDF auch erneut zusenden.

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
php tests/run.php                                   # Testsuite (nur PHP nötig)
php -S localhost:8000 -t public dev-router.php     # komplette Seite inkl. Buchung
php tools/build-static.php --url=http://localhost:8000   # dist/ erzeugen
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
| `/gutscheine` | Gutscheine online kaufen (PayPal, PDF per Mail) |
| `/ratgeber` + 3 Artikel | Pflege- und Farbtipps (BlogPosting-Schema) |
| `/friseur-burgwedel`, `/friseur-isernhagen`, `/friseur-langenhagen`, `/friseur-hannover` | Ortsseiten mit echter Anfahrtszeit (OpenStreetMap) |
| `/impressum`, `/datenschutz` | Rechtliches (noindex) |
| `/sitemap.xml`, `/robots.txt`, `/llms.txt` | werden automatisch aus den Inhalten erzeugt |

**SEO & GEO je Seite:** eigener Titel und Beschreibung, Canonical, Brotkrumen (`BreadcrumbList`), `HairSalon` mit Geo-Koordinaten
und Öffnungszeiten, `Service` mit Preisen auf Leistungsseiten, `FAQPage` wo Fragen stehen, Geo-Meta-Tags, `llms.txt` für KI-Suche.

**Texte ändern:** Leistungsseiten in `app/content/leistungen.php`, Ortsseiten in `app/content/orte.php`, Ratgeber in `app/content/ratgeber.php`,
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
dist/                     fertige HTML-Seiten (wird veröffentlicht, mit tools/build-static.php erzeugt)
tools/build-static.php    baut dist/ aus app/
public/                   Buchungsdienst (Container) + Quelle für CSS/JS/Bilder
  index.php               Front-Controller (lokales Testen, Links aus E-Mails)
  api/                    availability, booking, paypal-order, cancel, contact, admin
  admin/                  Terminverwaltung
  css/ js/ fonts/ img/
```
