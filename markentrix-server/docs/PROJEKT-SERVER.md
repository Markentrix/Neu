# Projekt „Server“: Arbeitsgrundlage für Claude und Christian (Stand 22.10.2026)

Zweck: Alles, was man wissen muss, um am Markentrix-Server und am Portal sauber weiterzuarbeiten. **Hier stehen keine Passwörter und Schlüssel**, nur wo sie liegen. Details: `ANLEITUNG.md`, `docs/ARCHITEKTUR.md`, `docs/WEBSITE-API.md`, `docs/WEBSITE-PROMPT.md`.

## 1. Arbeitsweise (immer einhalten)
- Sprache: Deutsch, kurz und konkret. Zuerst das Ergebnis, dann Details.
- Mails und Dokumente im Namen von Markentrix nie mit einem KI-Namen unterschreiben. Unterschrift: „Ihr Markentrix-Team“ oder „Markentrix“. Ein neutraler Hinweis „Dieser Text wurde mit KI-Unterstützung vorbereitet“ ist erlaubt.
- Nichts als erledigt melden, was nicht getestet ist. Was nur aus Code abgeleitet ist, ausdrücklich so benennen.
- Entscheidungen, die Geld, Provisionen, Rechtliches oder Kundendaten betreffen (z. B. automatische Lead-Verteilung, Preise für Vertriebler), nicht ohne Rückfrage ändern. Standard ist „aus“.
- Rechtliche Bewertungen (DSGVO, UWG, AVV, Sperrliste) gehören zum Anwalt (`docs/ANWALT-CHECKLISTE.md`).
- Christian nutzt häufig die Hetzner-Webkonsole mit US-Tastatur: `:` wird `;`, `_` wird `-`, `&&` wird `77`. Befehle zum Kopieren geben, wenn möglich ohne Sonderzeichen, oder besser per SSH (`ssh root@5.75.146.212`) arbeiten.

## 2. Überblick
- Markentrix: Einzelunternehmen von Christian Wien, Celle. KI-Automatisierung für lokale Betriebe (Handwerk, Werkstätten).
- Server: Hetzner, Nürnberg, IPv4 `5.75.146.212`, Hostname „Markentrix“. Hauptdomain `markentrix.de`, Portal unter `https://portal.markentrix.de` (Admin `/admin`, Kunden `/app`, Vertrieb `/vertrieb`). Kundendomains bei INWX bzw. IONOS.
- Stack: FastAPI-Portal (`mk-portal`), PostgreSQL mit Row-Level-Security (`mk-db`), n8n (`mk-n8n`, `mk-n8n-db`), Dashboard (`mk-panel`), Docker-Socket-Proxy. Webserver: ein bereits vorhandener Caddy (`server-caddy-1`, Domain-Dateien in `/srv/caddy-sites`); `install.sh` erkennt ihn und trägt die Einstellungen ein. Oberfläche: reines JavaScript (ES-Module), kein Build-Schritt.
- Mail-Versand: eigener SMTP-Zugang (smtp.gmail.com), im Admin unter Einstellungen → E-Mail.
- Beispiel einer Kunden-Website auf dem Server: `elbdetail.de`.

## 3. Wo was liegt
| Was | Wo |
|---|---|
| Code (GitHub) | Repository `Markentrix/Neu`, Branch **`server-paket`**, Unterordner `markentrix-server/` |
| Klon auf dem Server | `/root/Neu` (Installationsordner danach `/root/Neu/markentrix-server`) |
| Laufende Installation | `/opt/markentrix` (Compose-Datei, `.env`, `bin/`, `db/`, Sicherungen in `backups/`) |
| Zugangsdaten, Schlüssel | `/opt/markentrix/.env` (nur root lesbar). `PORTAL_SECRET` verschlüsselt gespeicherte Einstellungen: **nie ändern oder verlieren**, sonst sind SMTP-, KI- und Kalenderdaten unlesbar. Sicherung der `.env` getrennt aufbewahren. |
| Einstellungen im Portal | Admin → Einstellungen (SMTP, KI, Firma, Zahlung …). Werte verschlüsselt in der Datenbank. |
| Kunden-Websites | `/srv/sites/<domain>` (Upload per Admin → Websites & Demos) |
| Logs | `docker logs mk-portal --tail 100`, `/var/log/markentrix-*.log` |
| Sicherungen | `/opt/markentrix/backups`, täglich 03:15, Wiederherstellungstest wöchentlich |

## 4. Wichtige Befehle auf dem Server (als root)
- `mkctl status`: Container, Speicher, letzte Sicherung.
- `mkctl selbsttest`: prüft Container, Portal, Anmeldung, Datenbank, Mail, Jobs, Sicherung, Zertifikat. Soll „alles in Ordnung“ melden.
- `mkctl update`: Sicherung, Neubau, Migrationen. `mkctl migrate`: nur Datenbank-Migrationen.
- `mkctl backup`, `mkctl restore-test`, `mkctl offsite-setup` / `offsite-test` (externes Backup, noch nicht eingerichtet).
- `mkctl logs`, `mkctl psql`, `mkctl restart`, `mkctl site-list`, `mkctl n8n-version <x.y.z>` (n8n gezielt wechseln; die laufende Version ist in `.env` festgehalten).
- Update einspielen (Standard): `cd /root/Neu`, `git pull origin server-paket`, `cd markentrix-server`, `sudo bash install.sh`, `sudo mkctl selbsttest`. Der Hinweis „Es läuft schon ein Caddy“ am Ende von `install.sh` ist normal.

## 5. Entwickeln und testen
- Änderungen im Repo-Ordner `markentrix-server/`, nie direkt auf dem Server editieren.
- Tests: `bash tests/run.sh` (komplett, ca. 25 Minuten, baut eine eigene Test-Datenbank) oder gezielt `TESTS="t74 t76" bash tests/run.sh`. Der Lauf enthält pyflakes, ESLint und Typprüfung. Unbenutzte Importe lassen den Lauf scheitern. Während eines Volllaufs keine Frontend-Dateien ändern (die Browser-Tests lesen sie).
- Browser-Tests (Playwright, Handy 390 px und Desktop 1280 px): `t36` (Kunden- und Vertriebsportal), `t76` (Admin komplett und neue Masken). Sie prüfen Barrierefreiheit (axe), seitliches Überlaufen und JavaScript-Fehler.
- Neue Tests bekommen die nächste Nummer (aktuell bis `t76`) und werden in die Liste in `tests/run.sh` eingetragen. Testdaten eindeutig machen (Telefon, Firma), weil das Portal Dubletten und die Sperrliste prüft.
- Neue Datenbank-Tabellen: Nummerierte SQL-Datei in `db/`, mit RLS (`rls_intern` / `rls_kunde`), Rechte in `999_rechte.sql`. Migrationen laufen in einer Transaktion.
- Neue Admin-Routen brauchen einen Eintrag in `security._BEREICH`, sonst gilt das Recht „einstellungen“.
- Im Portal-Code nur Pakete aus `portal/requirements.txt` verwenden.
- Veröffentlichen: Commit auf `server-paket`, Push, dann auf dem Server `git pull` + `install.sh`.

## 6. Was schon da ist (Funktionsstand)
- **Admin:** Kunden, Onboarding, Verträge/AVV, Angebote und Rechnungen, Preise, Pakete-Katalog, Websites & Demos (ZIP-Upload), Postfach, Freigaben, Aufgaben, Kennzahlen, Protokoll, Systemstatus (Ampel).
- **Vertrieb:** Leads mit Wiedervorlagen, Löschfrist, Kontakt-Ergebnissen, Verlustgründen, Ansprache-Grundlage, **Sperrliste**, Dublettenprüfung, Import, Angebot an Leads mit Online-Annahme, „Zum Kunden machen“-Assistent, Erstgespräch-Buchung, Provisionen, Pipeline, Auswertung. Steuerung (Admin → Leads): automatische Verteilung (Standard **aus**), Reaktionszeit, Preise für Vertriebler (Standard **aus**).
- **Kundenportal:** Heute, Übersicht mit Startkarte („wer ist am Zug“), Briefing, Nachrichten (mit Anhang, Entwurfsspeicher), Freigaben (mit Datum und Bestätigung), Anfragen, Termine, Bewertungen, Dokumente, Rechnungen, Datenschutz-Vertrag, Website-Dienste, Push und Glocke.
- **Website-Anbindung:** Bausteine (`site.js`) und Website-API (`/api/…`), Kontaktformular, Terminbuchung mit Leistungen/Mitarbeitern, PayPal, Google-Bewertungen, Statistik ohne Cookies. Siehe `docs/WEBSITE-API.md` und den Prompt `docs/WEBSITE-PROMPT.md`.
- **Betrieb:** Hintergrundjobs mit Fehlerzähler und Ampel, Veröffentlichungs-Alarm, Upload-Prüfung und Kontingent (500 MB je Kunde), Sitzungen enden bei Passwortwechsel, Wachdienst alle 5 Minuten, tägliche Sicherung.

## 7. Offene Punkte (Stand heute)
1. **Externes Backup** einrichten (z. B. Hetzner Storage Box, dann `mkctl offsite-setup`). Ohne das sind bei Serverausfall auch die Sicherungen weg. Ampel zeigt dort Gelb.
2. **Externer Uptime-Monitor** (der interne Alarm fällt mit dem Server aus).
3. **Anwaltsprüfung:** Sperrliste/Ansprache-Grundlage (Art. 14 DSGVO, UWG), AVV, Löschkonzept, KI-Kennzeichnung.
4. **Pilotbetrieb** mit 2 bis 3 Kunden und einem Vertriebler; Terminbuchung im Lead mit echten Einstellungen einmal durchspielen (im Test nur ohne echte Buchungseinstellungen geprüft).
5. Nicht gebaut: Upload-Grenzen je Datei; Zahlungsart auf der Startkarte; Rechnungen/Verträge für weitere Kundenrollen (bewusst nur Inhaber); Feinschliff bei Anfragen/Termine/leere Zustände im Kundenportal.
6. Nicht geändert: `--forwarded-allow-ips "*"` im Portal-Container (Port nur an `127.0.0.1` gebunden; Änderung könnte Client-IPs kippen). Docker-Images sind auf Hauptversionen fixiert (Postgres 16, Caddy 2, n8n über `.env`).
7. Der n8n-Anschluss (MCP) war in der letzten Sitzung nicht verbunden; n8n-Arbeiten brauchen eine funktionierende Verbindung.

## 8. Bekannte Stolpersteine
- `mkctl selbsttest` meldete früher „Portal antwortet (Status 0)“, weil es im Container den Port 8090 statt 8000 ansprach. Behoben (Commit 3379030). Tritt es wieder auf: Container und `docker logs mk-portal` prüfen.
- Kunden-Websites: Domain muss in der Domainverwaltung stehen, sonst meldet die Website-API „Unbekannte Website“ (404) oder „Herkunft nicht erlaubt“ (403).
- Terminzeiten auf der Website müssen zu den „Festen Uhrzeiten“ im Portal passen.
- Passwörter und Schlüssel nie in Chats, Tickets oder Commits einfügen.
