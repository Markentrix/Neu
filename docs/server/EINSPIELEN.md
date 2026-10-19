# Markentrix-Website auf dem Hetzner-Server einspielen · Stand 15.10.2026

Server 5.75.146.212, Benutzer `deploy` (sudo ohne Passwort), Caddy 2 als Docker-Container aus
`/opt/neu/server/docker-compose.yml`, Webroot `/srv/sites/markentrix`, Domain-Dateien in `/srv/caddy-sites/`.

Dateien in diesem Ordner:

| Datei | Ziel auf dem Server |
|---|---|
| `markentrix-site.caddy` | `/opt/neu/server/caddy/snippets/markentrix-site.caddy` (die Domain-Datei `/srv/caddy-sites/markentrix.de.caddy` bleibt unverändert) |
| `docker-compose.yml` | `/opt/neu/server/docker-compose.yml` |
| `veroeffentlichen.bat` | fester Ordner auf dem Windows-Rechner, entpackt `markentrix-website.zip` nach `dist` und lädt hoch |

## 1. Website hochladen (Windows)

`veroeffentlichen.bat` starten, J drücken. Lädt `dist` hoch und entfernt veraltete Dateien auf dem Server.

## 2. Server-Dateien hochladen (Windows, im Ordner docs/server)

```
scp markentrix-site.caddy deploy@5.75.146.212:/tmp/markentrix-site.caddy
scp docker-compose.yml deploy@5.75.146.212:/tmp/docker-compose.yml
```

## 3. Auf dem Server einspielen

```
ssh deploy@5.75.146.212
```

Bisherige Dateien sichern, neue an Ort und Stelle, Protokollordner anlegen, Passwort hinterlegen:

```
mkdir -p ~/sicherung && cp /opt/neu/server/docker-compose.yml /opt/neu/server/caddy/snippets/markentrix-site.caddy ~/sicherung/
mv /tmp/markentrix-site.caddy /opt/neu/server/caddy/snippets/markentrix-site.caddy
mv /tmp/docker-compose.yml /opt/neu/server/docker-compose.yml
sudo mkdir -p /srv/markentrix-daten && sudo chown 82:82 /srv/markentrix-daten
echo "MX_SMTP_PASS=HIER-DAS-16-STELLIGE-APP-PASSWORT" >> /opt/neu/server/.env
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

Falls `validate` einen Fehler meldet: Sicherung zurückspielen (`cp ~/sicherung/markentrix-site.caddy /opt/neu/server/caddy/snippets/`), die Live-Seite läuft bis zum `reload` unverändert weiter.

Dann im Browser: Startseite zeigt die Miniatur, Kontaktformular mit Testanfrage absenden, Mail bei info@markentrix.de prüfen.
Fehlersuche: `sudo docker compose logs --tail 50 php caddy` und `sudo cat /srv/markentrix-daten/anfragen.log`.

## Nachtrag 19.10.2026: Website-Check (einmalig, nur wenn `/website-check` genutzt werden soll)

Der Website-Check braucht den zweiten PHP-Endpunkt `/api/check.php`. Die Datei kommt mit der ZIP (Schritt 1). Zusätzlich muss Caddy ihn an PHP weiterreichen, dafür die neue `markentrix-site.caddy` einspielen. Der PHP-Container braucht nichts Neues (curl und mbstring sind im Standard-Image enthalten).

Auf dem Windows-Rechner (im Ordner docs/server):

```
scp markentrix-site.caddy deploy@5.75.146.212:/tmp/markentrix-site.caddy
```

Auf dem Server (`ssh deploy@5.75.146.212`):

```
cp /opt/neu/server/caddy/snippets/markentrix-site.caddy ~/sicherung/markentrix-site.caddy.vor-check
mv /tmp/markentrix-site.caddy /opt/neu/server/caddy/snippets/markentrix-site.caddy
cd /opt/neu/server
sudo docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
sudo docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
curl -s -o /dev/null -w "%{http_code}\n" https://markentrix.de/api/check.php          # erwartet 405
curl -s -XPOST -d '{"url":"https://example.com"}' https://markentrix.de/api/check.php | head -c 200   # erwartet {"ok":true,...
```

Ohne diesen Schritt bleibt die Seite `/website-check` erreichbar, der Check meldet aber „nicht erreichbar“. Alles andere läuft unverändert. Auslastung: höchstens 8 Prüfungen je IP in 10 Minuten, höchstens 2 gleichzeitig, insgesamt höchstens 24 Sekunden je Prüfung, 1,5 MB je Abruf. Der Check gibt bewusst keine Empfehlungen aus, nur Befunde.

## Nachtrag 19.10.2026: Wochenbericht (einmalig, optional)

Die wöchentliche Lead-Übersicht per Mail braucht nur einen Cronjob auf dem Server. Anleitung, Test und Cron-Zeile: `WOCHENBERICHT.md` (im selben Ordner).

## Bei jedem späteren Update

Nur Schritt 1. Schritte 2 und 3 sind einmalig.
