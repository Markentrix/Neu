# Markentrix Server-Paket: Anleitung

Dieses Paket richtet auf deinem Hetzner-Server alles Neue mit **einem Befehl** ein:

- **PostgreSQL-Datenbank** mit fertiger Struktur (66 Tabellen): Kunden mit Kundennummer, Zugänge, Preiskatalog (Preisliste Stand September 2026) und Buchungen, Kundenbereich, Konfiguration und Prompts, Wissensbasis und Agentenläufe, Vertrieb, Akquise und Lead-Finder, Kommunikation, Datenschutz (Einwilligungen, Auskunft, Löschung) und Qualität (Befunde, Maßnahmen, Ausnahmeregister, Alarme). Jeder Kunde sieht nur seine eigenen Daten (getestet). Kein Supabase.
- **n8n** (deine Workflows), mit eigener Datenbank
- **Server-Dashboard** unter `panel.deine-domain.de` (nur lesend): zeigt Dienste, Websites, Demos, Speicher und Sicherungen
- **Tägliche Sicherung** um 03:15 Uhr, 14 Tage Aufbewahrung
- **mkctl**: kleines Werkzeug für Demos, Kunden-Websites, Updates und Sicherungen
- **Caddy** (HTTPS) nur, wenn noch keiner läuft. Ein vorhandener Caddy wird **nicht verändert**.

## Schritt 1: DNS-Einträge anlegen

Bei deinem Domain-Anbieter (aktuell Squarespace) vier neue **A-Einträge** anlegen, Ziel ist die IP deines Servers (5.75.146.212):

`n8n`, `panel`, `portal`, `demo` (also z. B. `n8n.markentrix.de`)

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

Das Skript erkennt das, lässt ihn unverändert und schreibt die nötigen Zeilen in die Datei `/opt/markentrix/caddy-zusatz-fuer-bestehenden-caddy.txt`. Diese drei Blöcke müssen in die vorhandene Caddyfile kopiert werden, danach Caddy neu laden. Das machen wir dann gemeinsam, bevor du etwas veränderst.

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

## Das Portal benutzen

**Admin (du):** `https://portal.deine-domain.de`, Login mit der E-Mail aus der Installation. Das Passwort steht am Ende der Installation. Neues Passwort jederzeit: `mkctl admin-reset deine@mail.de`.

Kunde anlegen: *Neuer Kunde* → Firma, E-Mail, Paket → „Einladungslink erzeugen". Den Link schickst du dem Kunden (7 Tage gültig). Er legt damit sein Passwort fest und sieht nur seine eigenen Daten.

Im Kunden stellst du per **Schalter** ein, welche Module er sieht (KI-Assistent, Anfragen & Termine, Wochenangebote ...). Unter *Buchungen* hältst du gebuchte Pakete samt Preis fest.

**Wochenangebote:** Bei einem Kunden mit Website: Website im Admin anlegen und einmal auf dem Server `mkctl site-add kunde.de` ausführen. Modul „Wochenangebote" einschalten. Der Kunde lädt PDF/JPG/PNG hoch, danach liegt es sofort unter `https://kunde.de/angebote/`.

**KI-Chat anbinden (später):** In `/opt/markentrix/.env` `CHAT_WEBHOOK_URL` (n8n-Webhook) und `CHAT_WEBHOOK_SECRET` eintragen, dann `mkctl restart portal`.

**Vertriebler:** Menü *Vertriebler* → anlegen, Kunden im Kunden unter „Vertriebler" zuordnen, Provisionen freigeben und als ausgezahlt markieren. Leads: Menü *Leads*, Status pflegen, einem Vertriebler geben, „Zum Kunden machen".

**Preise:** Menü *Preise & Konditionen*: neue Preise gelten ab einem Datum, alte Buchungen behalten ihren Preis. Provisionsregeln stehen als Entwurf da und gelten erst nach deiner Freigabe.

**Datenschutz & Qualität:** offene Alarme, Freigaben, DSGVO-Anfragen, Workflow-Fehler und Befunde an einem Ort.

## Was noch offen ist

1. **E-Mail-Versand:** Einladungen laufen über Links, die du selbst verschickst. „Passwort vergessen" per Mail braucht einen SMTP-Zugang.
2. **n8n-Workflows:** Aus n8n Cloud exportieren und im neuen n8n importieren, Zugangsdaten neu verbinden.
3. **markentrix-core:** Im Repo liegt noch kein Code, deshalb nicht Teil dieses Pakets.
4. **Provisionen berechnen:** Die Berechnung läuft noch nicht automatisch (kommt über n8n). Das Portal zeigt und verwaltet sie.
5. **Kopie der Sicherungen außerhalb des Servers** (z. B. Hetzner Storage Box).

## E-Mail-Versand, KI-Chat, Vertriebler-Login, Provisionen

**Einstellungen** (Admin → Einstellungen)
- *E-Mail-Versand (SMTP)*: Server, Port, Verschlüsselung (meist STARTTLS/587), Benutzername, Passwort und Absender deines Postfachs (z. B. info@markentrix.de) eintragen, speichern, dann „Testmail senden". Danach gehen Einladungen und „Passwort vergessen"-Mails automatisch raus. Das Passwort wird verschlüsselt gespeichert.
- *KI-Assistent*: API-Key aus der Anthropic-Konsole (console.anthropic.com) eintragen. Modell ist vorgegeben (günstig), dazu ein Tageslimit pro Kunde. Ohne Key nutzt der Chat weiter den n8n-Webhook (falls eingerichtet). Abgerechnet wird pro Nutzung direkt bei Anthropic.

**Vertriebler-Login**: Admin → Vertriebler → Name anklicken → „Portal-Zugang" → E-Mail eintragen → „Einladung erzeugen". Der Vertriebler bekommt die Mail, legt sein Passwort selbst fest und meldet sich unter portal.markentrix.de an (landet automatisch im Partnerportal). Er sieht nur seine eigenen Kunden, Leads und Provisionen. Sperren/Freigeben geht am selben Ort.

**Provisionen**: Zuerst unter Preise & Konditionen die Provisionsregel(n) „laufend" freigeben. Dann Admin → Vertriebler → „Provisionen berechnen": Monat wählen → Vorschau → Anlegen. Doppelte Einträge werden nie angelegt. Der Vertriebler sieht seine Beträge sofort; Freigeben/Auszahlen markierst du beim Vertriebler.
