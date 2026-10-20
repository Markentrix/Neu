# Wiederherstellung: Wenn etwas schiefgeht

Alle Befehle auf dem Server in der Hetzner-Web-Konsole, Ordner `/opt/markentrix`. Erst lesen, dann tippen. Bei Unsicherheit zuerst einen Hetzner-Server-Snapshot (Hetzner-Konto → Server → Snapshots) machen.

## 1. Update ist schiefgegangen (Portal startet nicht)
1. `mkctl status` ansehen, `docker logs mk-portal --tail 50`.
2. Zuerst einfach neu starten: `cd /opt/markentrix && docker compose up -d`.
3. Hilft das nicht: Fehlermeldung kopieren und im Chat melden. Die Datenbank wird beim Update nur erweitert, nicht verkleinert; Daten gehen dabei nicht verloren. Vor jedem `mkctl update` wird eine Sicherung angelegt.

## 2. Sicherungen ansehen
`ls -la /opt/markentrix/backups` (lokal) und, falls eingerichtet, `mkctl offsite-test`. Das Passwort der externen Sicherung liegt in `/opt/markentrix/offsite/passphrase` und muss zusätzlich im Passwortmanager liegen.

## 3. Kompletten Server verloren
1. Neuen Hetzner-Server (Ubuntu) bestellen, DNS auf die neue IP.
2. Repo holen und `bash install.sh` ausführen wie bei der Erstinstallation.
3. Sicherungsdatei (Datenbank-Dump) vom Storage Box zurückholen, entschlüsseln (Passwort!) und einspielen. Dieser Schritt ist bewusst nicht als Ein-Klick-Befehl gebaut, weil er die Datenbank überschreibt. Bitte vorher gemeinsam durchgehen; die wöchentliche Wiederherstellungsprobe (`mkctl restore-test`) übt genau diesen Weg an einer Wegwerf-Kopie.

## 4. Versehentlich einen Kunden gelöscht
Website-Ordner liegen 14 Tage im Papierkorb. Datenbank-Inhalte nur aus einer Sicherung (Punkt 3 an einer Kopie) holen. Ein gelöschter Kunde kann nicht per Knopfdruck zurückgeholt werden; deshalb verlangt das Löschen Export-Haken und Kundennummer.

## 5. Passwort vergessen (Admin)
`mkctl admin-reset info@markentrix.de` zeigt ein neues Einmalpasswort.

## 6. Probelauf der Wiederherstellung (einmal im Jahr, in Ruhe)
Der **automatische Test** läuft jede Woche (Sonntag 04:30 Uhr, `mkctl restore-test`): Er spielt die neueste Datenbanksicherung in einen Wegwerf-Container ein und vergleicht Tabellen und Kundenzahl. Fehlschläge und ein ausbleibender Test lösen einen Alarm aus (Mail, optional Telegram). Das deckt den AVV-Satz „Wiederherstellungstest mindestens vierteljährlich“ ab, auch ohne dein Zutun.

Einmal im Jahr lohnt sich zusätzlich der **Probelauf auf einem zweiten Server**, damit du den Ernstfall (Punkt 3) einmal geübt hast:
1. Im Hetzner-Konto einen kleinen Test-Server anlegen (ein paar Cent pro Stunde), ohne die echte Domain.
2. Dort Repo holen und `bash install.sh` ausführen.
3. Eine Sicherung vom Storage Box oder aus dem Hetzner-Backup einspielen (Punkt 3), Portal öffnen, anmelden, ein, zwei Kunden und einen Beleg ansehen.
4. Testserver löschen. Notiere dir das Datum und wie lange es gedauert hat.
Wichtig dabei: Das Passwort der externen Sicherung (`/opt/markentrix/offsite/passphrase`) muss im Passwortmanager liegen. Ohne dieses Passwort sind verschlüsselte Sicherungen nicht lesbar.
