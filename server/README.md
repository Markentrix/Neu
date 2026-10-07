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

## 3. Kundenwebsite anlegen
```bash
ssh deploy@<server-ip>
/opt/neu/server/scripts/add-site.sh kunde.de          # statische Seite, Platzhalter
rsync -av ./build/ deploy@<server-ip>:/srv/sites/kunde.de/   # Inhalte hochladen
```
Vorher DNS des Kunden auf die Server-IP zeigen lassen (sonst kein Zertifikat).
Entfernen: `scripts/remove-site.sh kunde.de`.

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
