# Website-Check → Lead im Portal

Ablauf: Besucher macht den Check auf markentrix.de/website-check, fordert den Bericht an und setzt
**freiwillig** den Haken „Kontakt gewünscht“ (`kontakt_gewuenscht`). Dann sendet `api/anfrage.php`
(PHP-Container) zusätzlich einen Aufruf an das Portal: `POST https://portal.markentrix.de/api/public/website-check`
mit Header `X-Lead-Secret` und `X-MK: 1`. Das Portal legt Lead (Quelle „website“), Befunde, Einwilligungs-Vermerk,
Folgeaufgabe (+1 Tag) und Mail an das Team an. Fehler dabei blockieren den Besucher nicht.

## Einrichtung
1. Admin → Einstellungen → „Website-Check → Leads“ → „Schlüssel erzeugen“ (wird nur einmal angezeigt).
2. Auf dem Server:
   ``bash bin/lead-key.sh` im Ordner markentrix-server (Schlüssel einfügen, Enter)
   (Alternative: Umgebungsvariable `MX_LEAD_SECRET` im PHP-Container; optional `MX_LEAD_URL`.)
3. Neuen Check mit beiden Haken machen.

## Fehlersuche
- `sudo cat /srv/markentrix-daten/anfragen.log`: Feld `lead` = HTTP-Code (200 ok, 401 falscher Schlüssel, leer = kein Schlüssel/kein Kontaktwunsch).
- `docker logs mk-portal --since 60m 2>&1 | grep website-check`

## Recht
Lead-Speicherung/Nachfassen ist in Datenschutz Abschnitt 4a noch nicht erwähnt → auf die Anwalts-Checkliste.
