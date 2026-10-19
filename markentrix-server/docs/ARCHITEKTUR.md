# Architektur (für Entwickler und Betrieb)

## Überblick
Ein Hetzner-Server, alle Dienste als Docker-Container hinter Caddy (TLS). Verwaltung per `mkctl` (siehe `mkctl help`), Updates per `git pull` + `bash install.sh`.

| Container | Aufgabe |
|---|---|
| `mk-portal` | FastAPI-Anwendung (Admin-, Kunden-, Vertriebsportal, öffentliche Schnittstellen) und statische Oberfläche |
| `mk-db` | PostgreSQL mit Row-Level-Security (Mandantentrennung) |
| `mk-n8n`, `mk-n8n-db` | Automatisierungen (Workflows) |
| `mk-panel` | Server-Dashboard (Status der Container) |

Zusätzlich auf dem Host (cron): `worker.py` (jede Minute, Websites veröffentlichen), `watchdog.sh` (alle 5 Minuten), `backup.sh` (täglich), `offsite.sh`, `restore-test.sh` (wöchentlich).

## Portal (portal/app)
- `main.py`: Router-Registrierung, Sicherheits-Header (CSP ohne Inline-Skripte), CSRF-Schutz (Header `X-MK: 1`, Webhooks unter `/api/webhook/` prüfen selbst per Geheimnis), Fehler-Alarm.
- `db.py`: `tx("kunde", id)`, `tx("admin")`, `tx("system")`. Kunden sehen per RLS nur eigene Zeilen. `system` umgeht die Kunden-RLS, dort immer ausdrücklich filtern.
- `security.py`: Anmeldung, Rollen, Admin-Teilrechte (`_BEREICH`: Unterbereich → Recht), Rate-Limits, Audit-Protokoll.
- `routes_*.py`: je Fachbereich eine Datei (Belege, Leads, Zahlung, Telefon, Push, Dashboard …). Neue Routen unter `/api/admin/…` brauchen einen Eintrag in `_BEREICH`, sonst gilt das Recht „einstellungen".
- `jobs.py`: Hintergrundjobs (Mails, Erinnerungen, Löschfristen, Geschäftszahlen). Einmal-je-Tag-Jobs nutzen `_marker(schluessel)`.
- `push.py`: Web-Push (VAPID, aes128gcm) ohne Fremdbibliothek außer `cryptography`; speichert zusätzlich die Glocke (`benachrichtigungen`).
- Nur Pakete aus `portal/requirements.txt` sind im Container vorhanden. **Nie** Pakete importieren, die nur in der Testumgebung installiert sind (Beispiel: `httpx`).

## Oberfläche (portal/static)
Reines JavaScript (ES-Module), kein Build-Schritt. `common.js` (Hilfen, Glocke, Suche, Barrierefreiheits-Helfer), `admin.js` (Router) und `admin/*.js` (Seiten je Bereich; `kern.js` = gemeinsame Bausteine), `kunde.js`, `vertrieb.js`. Neue Admin-Seite: Datei in `admin/` anlegen, `V.seitenname = async () => …` setzen, in `admin.js` importieren und in `kern.js` zur `NAV` hinzufügen.

## Datenbank (db/)
Nummerierte SQL-Dateien, werden beim Update der Reihe nach angewendet. Neue Tabellen mit `rls_intern('tabelle')` (nur intern) oder `rls_kunde('tabelle', kunde_schreibt)` absichern, Rechte in `999_rechte.sql`.

## Tests (tests/run.sh)
`sudo bash tests/run.sh` baut eine eigene Test-Datenbank und prüft: t4–t29 (Funktionen), t27 (Browser: Kernabläufe, Handy-Ansicht, Barrierefreiheit), t28 (Sicherheits-Sweep über alle Routen), ESLint und Typprüfung der Oberfläche, pyflakes, Shell-Syntax. Einzelne Gruppen: `TESTS="t29" bash tests/run.sh`. Vor jedem Push muss „ALLES OK" stehen.

## Sicherheits-Grundsätze
Keine Geheimnisse im Klartext in der Datenbank (`einstellungen.*` verschlüsselt), IBAN verschlüsselt, Passwörter gehasht, Sitzungstoken nur als Hash, Rate-Limits auf Anmeldung und öffentlichen Schnittstellen, Abhängigkeiten regelmäßig mit `pip-audit -r portal/requirements.txt` prüfen.
