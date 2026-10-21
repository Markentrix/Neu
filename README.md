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

## Voraussetzungen

Jeder normale Webspace / Server mit Hosting-Portal (Plesk, cPanel, KAS, ISPConfig …):

- PHP **8.1 oder neuer** mit den Erweiterungen `pdo_sqlite`, `curl`, `mbstring` (bei fast allen Hostern Standard)
- Apache (für `.htaccess`) – für nginx siehe unten
- E-Mail-Versand über PHP `mail()` (im Portal meist aktiv)

Es wird **keine** MySQL-Datenbank benötigt – die Termine liegen in einer SQLite-Datei.

## Installation

1. **Dateien hochladen** – den kompletten Ordner (`app/` und `public/`) auf den Server.
2. **Document Root** der Domain im Portal auf den Ordner `public/` stellen.
   (Plesk: *Hosting-Einstellungen → Dokumentenstamm*, cPanel: *Domains → Document Root*).
   Der Ordner `app/` liegt dann außerhalb des Webs. Geht das nicht, ist `app/` zusätzlich per `.htaccess` gesperrt.
3. **Konfiguration**: `app/config.local.example.php` nach `app/config.local.php` kopieren und ausfüllen:
   - `siteUrl` – z. B. `https://www.aj-atelier-wettmar.de`
   - `adminPasswordHash` – erzeugen mit
     `php -r "echo password_hash('IHR-PASSWORT', PASSWORD_DEFAULT), PHP_EOL;"`
     (oder online in einem PHP-Werkzeug des Portals)
   - `paypal` – Client-ID & Secret, siehe unten
   - `mail.from` – Absender **mit der eigenen Domain** (sonst landen Mails im Spam), `mail.salonEmail` – Empfänger neuer Buchungen
4. Der Ordner `app/data/` muss für PHP **beschreibbar** sein (wird automatisch angelegt).
5. **SSL** im Portal aktivieren (Let's Encrypt). Die `.htaccess` leitet auf HTTPS um.
6. Testbuchung durchführen und unter `https://ihre-domain.de/admin/` prüfen.

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
