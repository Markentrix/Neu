# Markentrix Server-Paket: Anleitung

Dieses Paket richtet auf deinem Hetzner-Server alles Neue mit **einem Befehl** ein:

- **PostgreSQL-Datenbank** mit fertiger Struktur: Kunden mit Kundennummer, Zugänge, Pakete (KI ONE, BUSINESS, KOMPLETT), 8 Module, Projekte, Anfragen, Termine, Kontakte, Angebote, Verträge, Wochenangebote-Uploads, Chatverlauf, Berichte. Jeder Kunde sieht nur seine eigenen Daten (Row-Level-Security, getestet). Läuft nur auf deinem Server, kein Supabase.
- **n8n** (deine Workflows), mit eigener Datenbank
- **Server-Dashboard** unter `panel.deine-domain.de` (nur lesend): zeigt Dienste, Websites, Demos, Speicher und Sicherungen
- **Tägliche Sicherung** um 03:15 Uhr, 14 Tage Aufbewahrung
- **mkctl**: kleines Werkzeug für Demos, Kunden-Websites, Updates und Sicherungen
- **Caddy** (HTTPS) nur, wenn noch keiner läuft. Ein vorhandener Caddy wird **nicht verändert**.

## Schritt 1: DNS-Einträge anlegen

Bei deinem Domain-Anbieter (aktuell Squarespace) drei neue **A-Einträge** anlegen, Ziel ist die IP deines Servers (5.75.146.212):

`n8n`, `panel`, `demo` (also z. B. `n8n.markentrix.de`)

Die bestehenden Einträge für markentrix.de und www bleiben, wie sie sind.

## Schritt 2: Paket auf den Server bringen

Auf deinem Computer im Terminal (dort, wo die Datei `markentrix-server.tar.gz` liegt):

```
scp markentrix-server.tar.gz root@5.75.146.212:/root/
ssh root@5.75.146.212
```

## Schritt 3: Installieren

Jetzt auf dem Server:

```
tar xzf markentrix-server.tar.gz
cd markentrix-server
sudo bash install.sh
```

Das Skript fragt zwei Dinge (Hauptdomain, E-Mail für die Zertifikate), dort reicht jeweils Enter, wenn die Vorgabe stimmt. Der erste Start lädt einige GB und dauert 5 bis 15 Minuten.

Am Ende steht eine Zusammenfassung mit Adressen und Passwörtern auf dem Bildschirm. **Speichere sie sofort in einem Passwortmanager.**

Bricht das Skript ab, schick mir einfach die letzten Zeilen. Es kann gefahrlos erneut gestartet werden.

## Wenn schon ein Caddy läuft (z. B. für markentrix.de)

Das Skript erkennt das, lässt ihn unverändert und schreibt die nötigen Zeilen in die Datei `/opt/markentrix/caddy-zusatz-fuer-bestehenden-caddy.txt`. Diese zwei Blöcke müssen in die vorhandene Caddyfile kopiert werden, danach Caddy neu laden. Das machen wir dann gemeinsam, bevor du etwas veränderst.

## Alltag: mkctl

```
mkctl status                              Überblick
mkctl backup                              Sicherung jetzt
mkctl psql                                Datenbank-Konsole
mkctl migrate                             Datenbankstruktur anlegen/aktualisieren
mkctl demo-add anadolu                    neue Demo unter https://demo.markentrix.de/anadolu/
mkctl site-add kunde.de --kunde "Name"    Kunden-Website mit eigener Domain
mkctl update                              Sicherung, dann alles aktualisieren
mkctl help                                alle Befehle
```

Eigene Dateien einer Website kopierst du mit `--from /pfad/zum/ordner` hinein.

## Sicherheit

- Alle Dienste sind nur über HTTPS und Caddy erreichbar. Die Datenbank hört nur auf dem Server selbst.
- Es gibt keine öffentliche Registrierung. Kunden legst du selbst an.
- Empfohlen: In der Hetzner Cloud Console eine **Firewall** anlegen, die nur die Ports 22, 80 und 443 erlaubt.
- `/opt/markentrix/.env` enthält alle Schlüssel. Ohne sie lässt sich nichts wiederherstellen. Die tägliche Sicherung legt eine Kopie ab, die Sicherungen liegen aber auf demselben Server. **Eine Kopie außerhalb des Servers** (z. B. Hetzner Storage Box) fehlt noch.

## Was noch offen ist

1. **Portal-Backend:** Die Datenbank hat die Struktur, aber noch keine Kunden. Login (E-Mail + Passwort), Kundenrechte nach Kundennummer, Upload und Admin-Funktionen baue ich als eigenen kleinen Dienst auf dieser Datenbank (`portal.deine-domain.de`).
2. **E-Mail-Versand für Logins:** Einladungen und „Passwort vergessen" brauchen einen E-Mail-Zugang (SMTP), der dann im Portal-Dienst eingetragen wird.
3. **n8n-Workflows:** Müssen aus n8n Cloud exportiert und in das neue n8n importiert werden. Zugangsdaten (Gmail usw.) werden dort neu verbunden.
4. **markentrix-core:** Im Repo liegt noch kein Code, deshalb ist es nicht Teil dieses Pakets.
5. **Kunden-Dashboard und Admin-Bereich:** Das Design steht, die Anbindung an die neue Datenbank kommt als Nächstes (Adresse `portal.deine-domain.de`).
