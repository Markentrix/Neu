# Website-Check auf markentrix.de mit dem Portal verbinden

Jeder Website-Check wird im Portal als **Lead** gespeichert (Admin → Leads, Quelle „website“), mit Ergebnis, Einwilligung, Mail ans Team und einer Aufgabe „Lead nachfassen“. Wiederholt dieselbe E-Mail-Adresse den Check, entsteht kein zweiter Lead, sondern ein weiterer Eintrag im selben Lead.

## Einrichtung (einmalig)
1. Server aktualisieren (`git pull`, `bash install.sh` in `markentrix-server`).
2. Portal → Admin → Einstellungen → Karte „Website-Check → Leads“ → **Schlüssel erzeugen**. Der Schlüssel wird nur einmal angezeigt, bitte kopieren.
3. Den Schlüssel in der Konfiguration des PHP-Containers (`server-php-1`) als Umgebungsvariable `LEAD_SECRET` hinterlegen (nicht in den Website-Dateien ablegen).
4. `check.php` ruft nach dem Check das Portal auf (Beispiel unten).

## Schnittstelle
`POST https://portal.markentrix.de/api/public/website-check`

Header: `Content-Type: application/json`, `X-MK: 1`, `X-Lead-Secret: <Schlüssel>`

Body (JSON):
| Feld | Pflicht | Bedeutung |
|---|---|---|
| email | ja | E-Mail der Person |
| einwilligung | ja, `true` | Ohne Einwilligung wird kein Lead angelegt (Antwort 400) |
| einwilligung_text | nein | Wortlaut der Checkbox, wird protokolliert |
| name, firma, telefon | nein | Kontaktdaten |
| website | nein | die geprüfte Adresse |
| score | nein | Gesamtergebnis 0 bis 100 |
| ergebnis | nein | beliebiges JSON mit den Einzelergebnissen (höchstens 20.000 Zeichen) |

Antwort: `{"ok": true, "neu": true|false}`. Fehler: 401 falscher Schlüssel, 400 Eingabe, 403 Header `X-MK` fehlt, 429 zu viele Anfragen.

## Beispiel in PHP (am Ende von check.php, nur wenn die Person eingewilligt hat)
```php
$payload = json_encode([
  'email' => $email, 'name' => $name, 'firma' => $firma, 'website' => $url,
  'score' => $score, 'ergebnis' => $ergebnis,
  'einwilligung' => true, 'einwilligung_text' => $einwilligungsText,
]);
$ch = curl_init('https://portal.markentrix.de/api/public/website-check');
curl_setopt_array($ch, [
  CURLOPT_POST => true, CURLOPT_POSTFIELDS => $payload, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 5,
  CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'X-MK: 1', 'X-Lead-Secret: ' . getenv('LEAD_SECRET')],
]);
curl_exec($ch); curl_close($ch);   // Fehler hier dürfen den Check für den Besucher nicht blockieren
```

## Datenschutz
- Der Check-Dialog muss die Einwilligung zur Kontaktaufnahme einholen (B2B, Zweck nennen) und in der Datenschutzerklärung stehen.
- Leads werden nach 12 Monaten ohne neue Aktivität gelöscht (Speicherbegrenzung).
