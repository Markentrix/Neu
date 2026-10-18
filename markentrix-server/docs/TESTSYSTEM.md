# Testsystem (Staging)

Neue Funktionen sollten nie zuerst bei echten Kunden laufen. Es gibt zwei einfache Wege.

## Weg 1: Zweiter kleiner Server (empfohlen)

1. In Hetzner einen zweiten, kleinen Server anlegen (CX22 reicht, wenige Euro im Monat, kann bei Nichtgebrauch gelöscht werden).
2. Eine eigene Domain oder Subdomain als Test nutzen, z. B. `test.markentrix.de` mit den gleichen DNS-Einträgen (`portal.test.markentrix.de` usw.).
3. Dort dieselbe Installation wie beim echten Server ausführen (siehe ANLEITUNG.md, Schritt 2 und 3), mit der Test-Domain.
4. **Keine echten Kundendaten** einspielen. Eine echte Sicherung nur nach Rücksprache und wenn sie vorher anonymisiert wurde (DSGVO).
5. SMTP: Testpostfach oder gar keinen Versand einrichten, damit keine Mails an echte Kunden gehen.
6. KI-Key: eigener Key mit niedrigem Ausgabenlimit.

Ablauf bei Änderungen: erst im Testsystem `git pull` und `bash install.sh`, durchklicken, dann auf dem echten Server.

## Weg 2: Test-Kunden im echten System

Für kleine Dinge reicht ein Kunde, den du als **Referenzkunde** anlegst (zählt nicht in Umsatz und Provision). Nicht für Änderungen an der Datenbankstruktur oder an Sicherung/Überwachung geeignet.

## Vor jedem Update auf dem echten Server

1. `mkctl backup` (macht `mkctl update` ohnehin) und prüfen, dass im Server-Panel die Sicherung „OK" ist.
2. Danach `cd /root/Neu`, `git pull`, `cd markentrix-server`, `bash install.sh`.
3. `mkctl status` und im Portal einmal anmelden.
