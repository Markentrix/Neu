# Aktuelle Google-Bewertungen auf der Website · Stand 04.11.2026

Die Website zeigt auf der Startseite und unter `/referenzen` einen Abschnitt „Google-Bewertungen“, sobald der Server Daten von Google erhält. Ohne Einrichtung bleibt der Abschnitt unsichtbar, es gibt keine Platzhalter.

## Wie es funktioniert

1. Der Browser ruft `/api/bewertungen.php` auf der eigenen Domain auf (kein Google-Aufruf im Browser, keine Besucherdaten an Google, keine Einwilligung nötig).
2. `static/api/bewertungen.php` fragt die **Places API (New)** ab (`GET https://places.googleapis.com/v1/places/<ID>`, Felder `rating`, `userRatingCount`, `googleMapsUri`, `reviews`) und gibt die Daten als JSON zurück.
3. Zwischenspeicher im Temp-Ordner des php-Containers, Standard 1 Stunde (`MX_GOOGLE_CACHE_TTL`, mindestens 300 Sekunden). Antwortet Google nicht, wird der letzte Stand bis 24 Stunden alt weiterverwendet, danach verschwindet der Abschnitt.
4. `site.js` baut die Karten mit `textContent` (kein HTML aus der Antwort).

## Wichtige Grenzen (bitte kennen)

- Google liefert über diese Schnittstelle **höchstens 5 Bewertungen**, in der Regel „relevanteste“, nicht zwingend die neuesten. „Immer die aktuellen“ heißt hier: Gesamtwertung und Anzahl sind aktuell, die Auswahl der Einzelbewertungen bestimmt Google. Alle Bewertungen ohne Begrenzung gibt nur die Google Business Profile API (Antrag auf Zugang nötig).
- Es wird **nicht nach Sternen gefiltert**. Es erscheint, was Google liefert.
- Google-Nutzungsbedingungen: Inhalte unverändert und mit Quellenangabe „Google“ anzeigen (so umgesetzt). Die Bedingungen schränken das Zwischenspeichern von Places-Inhalten ein. Der kurze Zwischenspeicher dient dem Schutz vor Kosten und Ratenlimits; **bitte die aktuellen „Google Maps Platform Service Specific Terms“ prüfen** und bei Bedarf `MX_GOOGLE_CACHE_TTL` auf den Mindestwert 300 setzen.
- Kosten: Das Feld `reviews` gehört zur teureren Abrechnungsstufe. Bei 1 Stunde Zwischenspeicher sind das höchstens 24 Abrufe pro Tag und Seite, bei Ihrem Verkehr im Cent-Bereich. Google verlangt ein Rechnungskonto; ein Budgetlimit in der Cloud Console setzen.
- Es werden keine Fotos der Bewertenden geladen. Namen erscheinen, wie Google sie liefert.

## Einrichtung (einmalig, durch Sie)

1. Google Cloud Console: Projekt anlegen, Rechnungskonto verknüpfen, **Places API (New)** aktivieren.
2. API-Schlüssel erstellen und beschränken: Anwendungsbeschränkung „IP-Adressen“ = Server `5.75.146.212`, API-Beschränkung nur „Places API (New)“. Budgetwarnung einrichten.
3. Place-ID des Unternehmensprofils ermitteln (Place ID Finder von Google: Suche „Markentrix Celle“, ID beginnt meist mit `ChIJ`).
4. Auf dem Server in `/opt/neu/server/.env` ergänzen (nie ins Repository):
   ```
   MX_GOOGLE_API_KEY=…
   MX_GOOGLE_PLACE_ID=ChIJ…
   ```
5. Dateien einspielen wie in `EINSPIELEN.md` (Caddy-Datei und `docker-compose.yml` aus diesem Ordner), danach `sudo docker compose up -d php` und `caddy reload`.
6. Prüfen: `curl -s https://markentrix.de/api/bewertungen.php` muss `{"ok":true,…}` liefern; die Startseite zeigt den Abschnitt nach Strg+F5.

## Rollback

`MX_GOOGLE_API_KEY` in `.env` leeren und `sudo docker compose up -d php`: Der Endpunkt antwortet mit `{"ok":false}`, der Abschnitt verschwindet. Die Website selbst bleibt unverändert.

## Datenschutz

Es werden keine Daten der Besucher an Google übermittelt. Die Abfrage läuft serverseitig ohne Bezug zu Besuchern. Die Namen der Bewertenden sind öffentliche Angaben aus Google. Bitte bei der rechtlichen Prüfung der Datenschutzerklärung mit aufnehmen (Hinweis auf angezeigte Google-Bewertungen).
