# Markentrix-Website auf dem Hetzner-Server einspielen · Stand 15.10.2026

Server 5.75.146.212, Benutzer `deploy` (sudo ohne Passwort), Caddy 2 als Docker-Container aus
`/opt/neu/server/docker-compose.yml`, Webroot `/srv/sites/markentrix`, Domain-Dateien in `/srv/caddy-sites/`.

Dateien in diesem Ordner:

| Datei | Ziel auf dem Server |
|---|---|
| `markentrix.de.caddy` | `/srv/caddy-sites/markentrix.de.caddy` |
| `docker-compose.yml` | `/opt/neu/server/docker-compose.yml` |
| `veroeffentlichen.bat` | bleibt auf dem Windows-Rechner neben `dist` |

## 1. Website hochladen (Windows)

`veroeffentlichen.bat` starten, J drücken. Lädt `dist` hoch und entfernt veraltete Dateien auf dem Server.

## 2. Server-Dateien hochladen (Windows, im Ordner docs/server)

```
scp markentrix.de.caddy deploy@5.75.146.212:/tmp/markentrix.de.caddy
scp docker-compose.yml deploy@5.75.146.212:/tmp/docker-compose.yml
```

## 3. Auf dem Server einspielen

```
ssh deploy@5.75.146.212
```

Bisherige Definition von markentrix.de finden und sichern (Caddy verweigert doppelte Domains):

```
grep -l "markentrix.de" /opt/neu/server/caddy/snippets/*.caddy /srv/caddy-sites/*.caddy
mkdir -p ~/sicherung && cp /opt/neu/server/docker-compose.yml /srv/caddy-sites/*.caddy ~/sicherung/
```

Zeigt grep eine Datei in `snippets/` oder eine andere Datei als `markentrix.de.caddy` in `/srv/caddy-sites/`,
dort den Block für markentrix.de und www.markentrix.de entfernen (oder die Datei umbenennen, z. B. auf `.alt`,
damit `import *.caddy` sie nicht mehr lädt).

Neue Dateien an Ort und Stelle, Protokollordner anlegen, Passwort hinterlegen:

```
sudo mv /tmp/markentrix.de.caddy /srv/caddy-sites/markentrix.de.caddy
sudo mv /tmp/docker-compose.yml /opt/neu/server/docker-compose.yml
sudo mkdir -p /srv/markentrix-daten && sudo chown 82:82 /srv/markentrix-daten
echo "MX_SMTP_PASS=HIER-DAS-16-STELLIGE-APP-PASSWORT" | sudo tee -a /opt/neu/server/.env
```

Prüfen und starten:

```
cd /opt/neu/server
sudo docker compose config -q && echo COMPOSE_OK
sudo docker compose up -d
sudo docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
sudo docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## 4. Kontrolle

```
curl -sI https://markentrix.de/ | grep -i -E "x-frame|frame-ancestors"      # erwartet SAMEORIGIN und 'self'
curl -sI https://markentrix.de/preise.html | head -1                         # erwartet 301
curl -s -o /dev/null -w "%{http_code}\n" https://markentrix.de/api/anfrage.php   # erwartet 405 (nicht 404)
curl -s -o /dev/null -w "%{http_code}\n" https://demos.markentrix.de/            # andere Domains weiter erreichbar
```

Dann im Browser: Startseite zeigt die Miniatur, Kontaktformular mit Testanfrage absenden, Mail bei info@markentrix.de prüfen.
Fehlersuche: `sudo docker compose logs --tail 50 php caddy` und `sudo cat /srv/markentrix-daten/anfragen.log`.

## Bei jedem späteren Update

Nur Schritt 1. Schritte 2 und 3 sind einmalig.
