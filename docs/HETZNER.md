# Italia Camper 24 – Shop auf dem Hetzner-Server betreiben

Der Shop besteht aus **einem Docker-Container** (Node.js 22 + SQLite, enthält Seiten, Kasse, Kundenkonto, Admin) und **Caddy** (automatisches HTTPS).
Alles liegt auf eurem Hetzner-Server; Daten (Datenbank, Bestellungen, E-Mail-Log) im Docker-Volume `shopdata`.

## 0. Voraussetzungen
- Hetzner Cloud Server (z. B. **CX22**, Ubuntu 24.04, 2 vCPU/4 GB reichen), Zugriff per SSH
- Domain `italiacamper24.de` (DNS bei euch) – **A-Record** (und AAAA) von `www` und der nackten Domain auf die Server-IP
- SMTP-Zugang für E-Mails (z. B. eure Mailbox, Brevo, Mailbox.org)
- Konten: **Stripe** (Karte/Apple Pay/Google Pay) und **PayPal Business** (Live-App mit Client-ID/Secret)

## 1. Server vorbereiten (einmalig)
```bash
ssh root@SERVER-IP
adduser shop && usermod -aG sudo shop           # eigener Benutzer
rsync --archive --chown=shop:shop ~/.ssh /home/shop # SSH-Key übernehmen
# Root-Login & Passwort-Login abschalten: in /etc/ssh/sshd_config  PermitRootLogin no / PasswordAuthentication no ; systemctl restart ssh
ufw allow OpenSSH && ufw allow 80,443/tcp && ufw allow 443/udp && ufw enable
apt update && apt -y upgrade && apt -y install ca-certificates curl git unattended-upgrades
curl -fsSL https://get.docker.com | sh && usermod -aG docker shop
```
Neu einloggen als `shop`.

## 2. Shop installieren
```bash
git clone https://github.com/markentrix/neu.git shop && cd shop
git checkout claude/epic-sagan-h0ihsv          # bzw. main nach dem Merge
cp .env.example .env && nano .env
```
In `.env` ausfüllen (siehe Kommentare in der Datei): `DOMAIN`, `SESSION_SECRET` (`openssl rand -hex 32`), `ADMIN_EMAIL`/`ADMIN_PASSWORD` (≥ 12 Zeichen), SMTP, Bankdaten, Stripe, PayPal.
```bash
docker compose up -d --build
docker compose logs -f app     # sollte "Shop läuft auf https://…" zeigen
```
Prüfen: `https://www.italiacamper24.de` (Shop) · `https://www.italiacamper24.de/admin/` (Admin) · `/healthz`.

## 3. Zahlungen einrichten
### Stripe (Karte, Apple Pay, Google Pay)
1. Dashboard → Entwickler → API-Schlüssel → **Geheimer Schlüssel** (`sk_live_…`) in `.env` → `STRIPE_SECRET_KEY`.
2. Einstellungen → Zahlungsmethoden: **Karten, Apple Pay, Google Pay** aktivieren. Für Apple Pay die Domain unter *Zahlungsmethoden → Apple Pay → Domains* registrieren.
3. Entwickler → Webhooks → Endpunkt hinzufügen: `https://www.italiacamper24.de/api/webhooks/stripe`, Ereignisse: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`. **Signing secret** (`whsec_…`) → `STRIPE_WEBHOOK_SECRET`.
4. `docker compose up -d` (lädt .env neu). Erst mit Testschlüsseln (`sk_test_…`) und Karte `4242 4242 4242 4242` testen, dann auf Live wechseln.

### PayPal
1. developer.paypal.com → Apps & Credentials → **Live** → App erstellen → Client-ID und Secret in `.env` (`PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_ENV=live`).
2. Zum Testen `PAYPAL_ENV=sandbox` mit Sandbox-Schlüsseln und einem Sandbox-Käuferkonto.
3. Der Betrag wird bei Rückkehr des Kunden eingezogen (Capture); es ist kein Webhook nötig.

### Überweisung (Vorkasse) & Rechnung
- Bankdaten in `.env` (`BANK_*`). Bestellungen mit Vorkasse stehen auf „Wartet auf Zahlung“; im Admin unter der Bestellung **„Zahlungseingang bestätigen“** klicken → Kunde bekommt Mail, Rechnung wird nummeriert.
- **Rechnungskauf** landet auf „Rechnung: Prüfung“. Ihr prüft den Kunden und setzt den Status auf „In Bearbeitung/Versendet“. Maximalbetrag und Verfügbarkeit stellt ihr unter *Einstellungen* ein.

## 4. Täglicher Betrieb (Admin `/admin/`)
- **Übersicht**: neue Bestellungen, Umsatz, offene Anfragen, Warnungen zu fehlender Konfiguration.
- **Bestellungen**: Status ändern; bei „Versendet“ + Sendungsnummer geht automatisch die Versandmail raus und die Rechnung (PDF) wird erzeugt. Erstattung für Karte/PayPal per Knopfdruck.
- **Produkte & Preise**: Preise/Verfügbarkeit ändern → danach **„Shop-Seiten neu generieren“**, damit die Anzeige im Shop stimmt. (Beim Bezahlen gilt immer der Preis aus der Datenbank.)
- **Anfragen**, **Kunden**, **Gutscheine**, **Einstellungen**, **E-Mail-Log** (inkl. Fehler beim Versand).

## 5. Sicherung & Updates
```bash
crontab -e
0 3 * * * /home/shop/shop/deploy/backup.sh >> /home/shop/backup.log 2>&1   # täglich 3 Uhr
```
Sicherungen liegen in `/data/backup` (Container) – zusätzlich per `rsync` auf eine **Hetzner Storage Box** kopieren (Beispiel in `deploy/backup.sh`) und die Hetzner-Server-Snapshots aktivieren.
Update: `git pull && docker compose up -d --build` (Daten bleiben im Volume).

## 6. Vor dem Go-Live (Checkliste)
- [ ] Testbestellung je Zahlart (Stripe-Testmodus, PayPal-Sandbox, Vorkasse, Rechnung) inkl. E-Mails und Rechnungs-PDF
- [ ] Bankverbindung, USt-IdNr. und Impressum geprüft; AGB/Widerruf/Datenschutz mit dem Rechtsanwalt oder Händlerbund-Texten abgeglichen (Zahlarten Karte/Apple/Google Pay/Rechnung ergänzen, Datenschutz: Stripe, PayPal, Hetzner als Auftragsverarbeiter)
- [ ] Button „Zahlungspflichtig bestellen“ ist vorhanden (Button-Lösung) ✔
- [ ] **Umsatzsteuer Österreich**: Lieferungen an Privatkunden nach AT unterliegen ab Überschreiten der Lieferschwelle der österreichischen USt (OSS) – mit der Steuerberatung klären. Der Shop berechnet derzeit 19 % MwSt. für DE und AT.
- [ ] DNS/HTTPS, `/healthz`, Backup-Wiederherstellung einmal getestet
- [ ] In der Google Search Console die Sitemap `https://www.italiacamper24.de/sitemap.xml` einreichen; alte Jimdo-URLs per 301 umleiten (Liste der Altseiten liegt in der Sitemap der alten Seite)

## 7. Technik im Überblick
- `server/` Node.js (Express, `node:sqlite`, Nodemailer, PDFKit); `src/` Seitengenerator (Python) + Katalog; `site/` fertige Seiten.
- Preise werden **nur serverseitig** berechnet; Webhook-Signaturen werden geprüft; Passwörter mit scrypt; Sitzungs-Cookies HttpOnly/SameSite; CSRF-Header, Rate-Limits, strenge CSP.
- Tests: `cd server && npm test` (11 End-to-End-Tests mit simulierten Stripe-/PayPal-Servern).
