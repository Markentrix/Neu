# Markentrix Server-Setup (Hetzner)

Stack: Ubuntu 24.04 · Docker · Caddy (automatisches HTTPS, mehrere Domains) · UFW/Fail2ban.
Eigene Website, Kundenwebsites und später CRM-OS/Agenten laufen als Domains hinter demselben Caddy.

## 1. Vorbereitung
- Hetzner-Server mit **Ubuntu 24.04**, SSH-Key beim Anlegen hinterlegen.
- DNS: A-Record (und AAAA) von `markentrix.de` **und** `www` auf die Server-IP.

## 2. Einrichten (einmalig, als root)
```bash
ssh root@<server-ip>
git clone <repo-url> /opt/neu && cd /opt/neu/server
OWN_DOMAIN=markentrix.de ACME_EMAIL=info@markentrix.de bash bootstrap.sh
```
Danach: Login nur noch als `deploy` (Root/Passwort-Login ist aus). Test: `https://markentrix.de`.

## 3. Kundenwebsite anlegen (statisch, nach Kundennummer)
Jeder Kunde hat einen Ordner `/srv/sites/kunden/<Kundennummer>` (z.B. `MX-1007`). Pro Domain gibt es eine
Caddy-Datei; alle nutzen die gemeinsame Vorlage `caddy/snippets/kunden-site.caddy`
(Sicherheits-Header, saubere URLs, versteckte Dateien gesperrt, Caching, eigene 404.html).
```bash
ssh deploy@<server-ip>
cd /opt/neu/server/scripts
./kunde-anlegen.sh MX-1007 mx-1007.vorschau.markentrix.de --vorschau --passwort   # Vorschau: noindex + Passwort
./kunde-anlegen.sh MX-1007 kunde.de                                               # Live-Domain (+ www-Weiterleitung)
./kunden-liste.sh                                                                 # Überblick
./kunde-entfernen.sh MX-1007 mx-1007.vorschau.markentrix.de                       # nur diese Domain (Vorschau) entfernen
./kunde-entfernen.sh MX-1007 --alles                                              # alle Domains + Dateien -> /srv/backups/removed
```
Hochladen vom PC: `pc/kunde-veroeffentlichen.bat` (Ordner der Kundenseite auf die Datei ziehen, Kundennummer eingeben).
Vorher muss der DNS-Eintrag der Domain auf die Server-IP zeigen (sonst kein Zertifikat).
Vorschau-Adressen unter `*.vorschau.markentrix.de` brauchen je einen A-Eintrag (oder einen Wildcard-Eintrag `*.vorschau`).
Zugriffsprotokolle (IP-Adressen) schreibt Caddy in dieser Konfiguration nicht; Kundenverträge (AVV) trotzdem prüfen.
Ohne Kundennummer / für Apps: `scripts/add-site.sh` (siehe unten).

## 4. Apps (CRM-OS, Agenten – nächster Schritt)
Container ins Docker-Netz `web` hängen und veröffentlichen:
`scripts/add-site.sh crm.markentrix.de --proxy crm:3000`

## Betrieb
- Backup: täglich 03:30 nach `/srv/backups/daily` (14 Tage). **Zusätzlich** Hetzner-Backups im Panel aktivieren.
- Zertifikate liegen im Docker-Volume `caddy_data` – nicht löschen.
- Logs: `cd /opt/neu/server && docker compose logs -f caddy`

## Markentrix-Website (statisches `dist/`)
Konfiguration (Weiterleitungen, Header, Caching, 404) steht in `caddy/snippets/markentrix-site.caddy`.
```bash
# Auf dem Server: Domain mit der Website verknüpfen (Test, später Live)
/opt/neu/server/scripts/setup-markentrix-site.sh server.markentrix.de
# Auf dem PC (PowerShell): dist/ hochladen
tar -cf dist.tar -C "C:\Pfad\zu\Markentrix\dist" .
scp dist.tar deploy@<server-ip>:~/
# Auf dem Server:
tar -xf ~/dist.tar -C /srv/sites/markentrix && rm ~/dist.tar
```
