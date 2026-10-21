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
11. **Wächter einrichten:** prüft alle 5 Minuten Website (über HTTPS), Speicherplatz, Alter der letzten Sicherung und Zertifikat. Ist die Website zweimal hintereinander nicht erreichbar, startet er App und Caddy neu. Bei jeder Störung kommt eine E-Mail an `NOTIFY_TO` (höchstens alle 6 Stunden pro Störung).
    ```bash
    crontab -e
    */5 * * * * /opt/elbdetail/deploy/watchdog.sh >> /var/log/elbdetail-watchdog.log 2>&1
    ```
    Zusätzlich hat der App-Container einen Docker-Healthcheck (`docker compose ps` zeigt `healthy`).

## E-Mail-Versand

Benachrichtigungen bei neuen Anfragen und Eingangsbestätigungen an Kund:innen laufen über das bestehende Postfach (`info@elbdetail.de`) per SMTP. Die Zugangsdaten stehen beim E-Mail-Anbieter. Typische Werte: Port 587 mit `SMTP_TLS=starttls` oder Port 465 mit `SMTP_TLS=ssl`. Hetzner sperrt ausgehenden Port 25 bei neuen Konten, 587 und 465 funktionieren. Im Portal unter Einstellungen gibt es einen Knopf „Test-E-Mail senden“.

## Online-Terminbuchung, Google Kalender und PayPal

So läuft eine Online-Buchung ab:

1. Der Kunde wählt Paket, Fahrzeug, Tag und Abgabezeit (8, 9 oder 10 Uhr). Die Uhrzeit ist danach für ihn vorgemerkt (Status „Reserviert“).
2. René prüft im Portal unter **Postausgang** die E-Mail an den Kunden:
   - Er kann die Anzahlung ändern. Ohne Festpreis, etwa bei Sport- und Luxusfahrzeugen, Wohnmobilen oder ElbDetail Care, legt er sie selbst fest.
   - Er kann den Text anpassen und die E-Mail dann freigeben.
3. Erst mit dem Versand startet die Reservierungsfrist von 24 Stunden. Gibt René eine Buchung nicht innerhalb von 3 Tagen frei, verfällt sie.
4. Der Kunde leistet über den Link die Anzahlung per PayPal. Ohne PayPal-Zugang bestätigt er per Klick.
7. Danach ist der Termin bestätigt:
   - Der Kunde bekommt die Bestätigung mit dem Hinweis, dass René anruft und das Fahrzeug vorab ansieht, dazu eine Kalenderdatei.
   - René bekommt eine Benachrichtigung.
   - Der Termin steht im Google Kalender.
5. Die Bestätigung und die Erinnerungen (24 und 6 Stunden vorher) legt das System ebenfalls im Postausgang ab. Erinnerungen gehen nach der Freigabe zum geplanten Zeitpunkt raus. Nicht rechtzeitig freigegebene Erinnerungen entfallen.
6. Welche E-Mail-Arten eine Freigabe brauchen, stellt René unten im Postausgang ein. Standard: alle.
8. Nicht bestätigte Reservierungen verfallen automatisch, die Uhrzeit wird wieder frei.

Voraussetzungen:

- **E-Mail-Versand (SMTP)** muss eingerichtet sein. Ohne ihn kommen Terminwünsche wie früher als Anfrage, und René bestätigt im Portal.
- **Abgabezeiten, Reservierungsdauer, Erinnerungen und Anzahlung (%)** stehen im Portal unter Inhalte → Grunddaten → `booking`.

**Google Kalender einrichten (einmalig, ca. 15 Minuten):**

1. In der [Google Cloud Console](https://console.cloud.google.com/) ein Projekt anlegen und die „Google Calendar API“ aktivieren.
2. Den OAuth-Zustimmungsbildschirm (extern) mit dem eigenen Google-Konto als Testnutzer anlegen. Für Dauerbetrieb den Status auf „In Produktion“ stellen, sonst läuft die Freigabe nach 7 Tagen ab.
3. Unter Anmeldedaten einen OAuth-Client vom Typ „Webanwendung“ anlegen. Autorisierte Weiterleitungs-URI: `https://www.elbdetail.de/admin/api/google/callback`.
4. Client-ID und Client-Secret als `GOOGLE_CLIENT_ID` und `GOOGLE_CLIENT_SECRET` in `.env` eintragen und `docker compose up -d` ausführen.
5. Im Portal unter Kalender „Mit Google Kalender verbinden“ klicken und mit Renés Google-Konto zustimmen.

Ab dann gilt:
- Bestätigte Termine erscheinen als „Abgabe: Name · Paket“.
- Private Termine in Renés Kalender sperren die passenden Uhrzeiten auf der Website.

Ohne diese Einrichtung gibt es im Portal eine Abo-Adresse (iCal). Sie lässt sich in Google Kalender unter „Weitere Kalender → Per URL“ hinzufügen. Google aktualisiert solche Abos aber nur alle paar Stunden.

**PayPal-Anzahlung einrichten:**

1. Im [PayPal Developer Dashboard](https://developer.paypal.com/) mit dem PayPal-Geschäftskonto eine App anlegen („Live“).
2. Client-ID und Secret als `PAYPAL_CLIENT_ID` und `PAYPAL_SECRET` in `.env` eintragen. Zum Ausprobieren erst `PAYPAL_MODE=sandbox` mit Sandbox-Zugangsdaten nutzen, dann auf `live` umstellen.
3. `docker compose up -d`. Im Portal unter Kalender steht dann „PayPal-Anzahlung aktiv“.

Das System schlägt die Anzahlung vor:
- 15 % vom Richtpreis des gewählten Pakets und der Fahrzeugklasse.
- Bei der Keramik 15 % vom Einstiegspreis.
- Bei Buchungen über die Winter-Aktion 15 % vom Winter-Special-Preis (329 €).

Ohne Festpreis legt René den Betrag im Postausgang fest. 0 bedeutet keine Anzahlung, dann bestätigt der Kunde per Klick. Erstattungen lösen Sie im Portal in der Anfrage mit „Anzahlung über PayPal erstatten“ aus.

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
| Wächter-Protokoll | `tail -50 /var/log/elbdetail-watchdog.log` |
| Alarm-E-Mail testen | `docker compose run --rm --no-deps app python3 /app/server/app.py alarm "Test"` |

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
