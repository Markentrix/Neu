# Betrieb auf dem eigenen Hetzner-Server

Die Website läuft komplett auf eurem Server. Es gibt keine Fremddienste für Formulare, Statistik oder Inhaltspflege.

## Aufbau

| Baustein | Aufgabe |
|---|---|
| **Caddy** (Container `caddy`) | HTTPS mit automatischen Let's-Encrypt-Zertifikaten, liefert die statische Website aus, setzt Sicherheits-Header, komprimiert (zstd/gzip). |
| **App** (Container `app`) | Python-Server ohne Zusatzbibliotheken: Formulare, Anfragen-Postfach, Terminkalender, Gutscheine, cookielose Statistik, Verwaltungsportal unter `/admin`, Website-Generator. |
| **Volume `data`** | SQLite-Datenbank, Inhalte (Texte, Preise, Ratgeber, Fotos), Sicherungen, Änderungshistorie. |
| **Volume `site`** | Die gebaute Website. Jede Veröffentlichung legt ein neues Release an und schaltet ohne Ausfallzeit um. Die letzten fünf bleiben erhalten. |

Ressourcenbedarf: Ein Hetzner Cloud **CX22** (2 vCPU, 4 GB RAM) reicht mit großem Puffer.

## Ersteinrichtung (ca. 30 Minuten)

1. **Server anlegen:** Hetzner Cloud → Projekt → Server hinzufügen. Standort Falkenstein oder Nürnberg, Image **Ubuntu 24.04**, Typ CX22, eigenen SSH-Schlüssel hinterlegen. Backups im Hetzner-Panel aktivieren (empfohlen).
2. **Firewall:** In der Hetzner-Firewall nur TCP 22, 80, 443 und UDP 443 eingehend erlauben.
3. **DNS:** Beim Domain-Anbieter A-Einträge (und AAAA für IPv6) für `elbdetail.de` und `www.elbdetail.de` auf die Server-IP setzen.
4. **Docker installieren** (als root):
   ```bash
   apt update && apt -y upgrade && apt -y install git unattended-upgrades
   curl -fsSL https://get.docker.com | sh
   ```
5. **Projekt holen:**
   ```bash
   git clone https://github.com/Markentrix/Neu.git /opt/elbdetail
   cd /opt/elbdetail/deploy
   cp .env.example .env
   ```
6. **Zugangsdaten setzen:**
   ```bash
   docker compose build app
   docker compose run --rm app python3 /app/server/app.py passwort   # Ausgabe in .env eintragen
   openssl rand -hex 32                                               # als SECRET_KEY in .env
   nano .env                                                          # Domain, SMTP-Daten, E-Mail eintragen
   ```
7. **Starten:**
   ```bash
   docker compose up -d
   docker compose logs -f app      # "ElbDetail-Server läuft" abwarten, dann Strg+C
   ```
8. **Prüfen:** `https://www.elbdetail.de` öffnen, dann `https://www.elbdetail.de/admin` und anmelden.
9. **Im Portal:** Inhalte → Grunddaten & Kontakt → Rechtliches ausfüllen, Google-Bewertungslink eintragen, Einstellungen → Zahlungshinweis für Gutscheine eintragen, dann **Veröffentlichen**.
10. **Sicherung einrichten:**
    ```bash
    crontab -e
    15 3 * * * /opt/elbdetail/deploy/backup.sh >> /var/log/elbdetail-backup.log 2>&1
    ```
    Den Ordner `/opt/elbdetail-backups` zusätzlich auf eine Hetzner Storage Box spiegeln (z. B. mit `rsync` oder `borg`).

## E-Mail-Versand

Benachrichtigungen bei neuen Anfragen und Eingangsbestätigungen an Kund:innen laufen über das bestehende Postfach (`info@elbdetail.de`) per SMTP. Die Zugangsdaten stehen beim E-Mail-Anbieter. Typische Werte: Port 587 mit `SMTP_TLS=starttls` oder Port 465 mit `SMTP_TLS=ssl`. Hetzner sperrt ausgehenden Port 25 bei neuen Konten, 587 und 465 funktionieren. Im Portal unter Einstellungen gibt es einen Knopf „Test-E-Mail senden“.

## Alltag

| Aufgabe | Befehl |
|---|---|
| Neue Version einspielen | `/opt/elbdetail/deploy/update.sh` (oder in GitHub: Actions → „Auf Server veröffentlichen“) |
| Website neu bauen | im Portal „Veröffentlichen“ oder `docker compose exec app python3 /app/server/app.py build` |
| Neue Ratgeber-Artikel aus Git übernehmen | passiert in `update.sh` automatisch (`inhalte-ergaenzen`, überschreibt nichts) |
| Sicherung sofort | `/opt/elbdetail/deploy/backup.sh` |
| Logs ansehen | `docker compose logs --tail 100 app` |
| Passwort ändern | Schritt 6 wiederholen, dann `docker compose up -d` |
| Status | `docker compose ps` und `curl -s https://www.elbdetail.de/api/health` |

## Wiederherstellen

```bash
cd /opt/elbdetail/deploy
docker compose stop app
docker run --rm -v elbdetail_data:/data -v /opt/elbdetail-backups:/b alpine sh -c \
  "cd /data && tar xzf /b/elbdetail-<datum>.tar.gz && chown -R 1000:1000 /data"
docker compose start app
docker compose exec app python3 /app/server/app.py build
```

Die App muss beim Zurückspielen gestoppt sein (erste Zeile), damit die Datenbank sauber geschlossen ist. Die Sicherung enthält die Datenbank (`elbdetail.db`) und den Ordner `content/` mit allen Texten und Fotos.

## Inhalte: Git oder Portal?

Nach dem ersten Start sind die **Inhalte auf dem Server maßgeblich** (Volume `data/content`). Der Ordner `content/` im Git ist nur die Startvorlage. Neue Dateien aus Git (z. B. weitere Ratgeber-Artikel) werden bei `update.sh` ergänzt, bestehende Dateien werden nie überschrieben. Änderungen an bestehenden Texten daher immer im Portal machen.

## Sicherheit

- Verwaltungsportal nur mit Passwort (PBKDF2-Hash), Sitzungscookie `HttpOnly`, `Secure`, `SameSite=Strict`, Schutz gegen Cross-Site-Anfragen, Login-Sperre nach 8 Fehlversuchen in 15 Minuten.
- Formulare: Spam-Falle (Honeypot), Begrenzung pro IP-Adresse, strenge Prüfung aller Felder, Herkunftsprüfung.
- Strenge Content-Security-Policy: nur eigene Skripte, keine Inline-Skripte, keine Fremd-Server (Ausnahme: Google-Karte nach Klick).
- Keine IP-Adressen in Logs oder Datenbank. Statistik nur mit täglich wechselndem, nach 24 Stunden gelöschtem Zufallswert.
- Automatisches Löschen: unbearbeitete Anfragen nach 365 Tagen, Statistik nach 25 Monaten (in `.env` einstellbar).
- Server-Updates: `unattended-upgrades` aktiv lassen, Docker-Images mit `update.sh` regelmäßig neu bauen.
