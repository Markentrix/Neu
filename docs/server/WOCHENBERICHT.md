# Wochenbericht per E-Mail (einmalig einrichten)

Jeden Montag früh schickt der Server eine Zusammenfassung der letzten sieben Tage an `info@markentrix.de`: Anfragen insgesamt und je Quelle (Kontakt, Potenzial-Check, Website-Check, Bewerbung), Vergleich zur Vorwoche, ausdrückliche Kontaktwünsche aus dem Website-Check, Herkunft (Angabe im Formular, Link-Parameter, Verweis), meistgenutzte Seiten, Bewerbungen nach Rolle und die einzelnen Eingänge mit Name, E-Mail und Wertung. Konnte eine Anfrage nicht per Mail zugestellt werden, steht oben „ACHTUNG“ und der Betreff trägt den Zusatz „Zustellfehler“.

Die Mail kommt immer, auch bei null Anfragen. Bleibt sie aus, läuft der Server oder der Versand nicht.

Die Auswertung liest nur das vorhandene Protokoll `/srv/markentrix-daten/anfragen.log`. Es entstehen keine neuen Daten, es kommt kein Dienst eines Dritten hinzu. Versand über denselben Gmail-Zugang wie die Anfragen.

## Voraussetzung

Die ZIP ist eingespielt (Schritt 1 in `EINSPIELEN.md`). Sie enthält `api/wochenbericht.php` und `api/mx-mail.php`. Caddy braucht keine Änderung: Die Datei ist von außen nicht erreichbar (Caddy reicht nur `anfrage.php` und `check.php` durch, das Skript bricht außerhalb der Kommandozeile mit 404 ab).

## Testen

Auf dem Server (`ssh deploy@5.75.146.212`):

```
cd /opt/neu/server
sudo docker compose exec -T php php /srv/sites/markentrix/api/wochenbericht.php --dry
```

Zeigt den Berichtstext, sendet nichts. Danach ein echter Versand:

```
sudo docker compose exec -T php php /srv/sites/markentrix/api/wochenbericht.php
```

Erwartet: „Wochenbericht gesendet an info@markentrix.de (N Anfragen).“ und kurz danach die Mail im Postfach. Anderer Zeitraum: `--tage=14` (1 bis 60 Tage).

## Jeden Montag automatisch

Als root-Cronjob auf dem Server:

```
sudo crontab -e
```

Zeile am Ende einfügen und speichern:

```
0 7 * * 1 cd /opt/neu/server && docker compose exec -T php php /srv/sites/markentrix/api/wochenbericht.php >> /srv/markentrix-daten/wochenbericht.log 2>&1
```

Das heißt: montags um 7:00 Uhr Serverzeit. Prüfen mit `sudo crontab -l`. Fehlermeldungen (zum Beispiel „Versand fehlgeschlagen“) stehen in `/srv/markentrix-daten/wochenbericht.log`. Rückgabecodes: 0 gesendet, 2 Versand fehlgeschlagen, 1 Protokollpfad nicht gesetzt.

## Hinweise

- Der Bericht enthält Namen und E-Mail-Adressen der Anfragenden. Vertraulich behandeln, nicht weiterleiten, und mit dem Protokoll zusammen löschen, wenn die Fristen aus der Datenschutzerklärung greifen.
- Das Protokoll wächst mit jeder Anfrage. Bei normalem Aufkommen unkritisch. Einmal im Jahr alte Einträge sichern und kürzen (Löschfristen beachten).
- Ändert sich die Empfängeradresse, in `docker-compose.yml` den Wert `MX_MAIL_TO` ändern und `sudo docker compose up -d php` ausführen.
