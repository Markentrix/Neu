# Portal-Anbindung des Schichtatelier-Shops (Stand der Website)

Maßgeblich ist die Vorgabe „Website mit Portal“ (Variante B, Modul „Online-Shop“). Dieses Dokument beschreibt, was die Website davon nutzt.
Getestet wurde gegen einen nachgebauten Portal-Server, nicht gegen das echte Portal.

Voraussetzung im Portal: Modul „Online-Shop“ ist für den Kunden gebucht und eingeschaltet, Artikel sind angelegt und aktiv.

## Genutzte Endpunkte

| Endpunkt | Verwendung auf der Website |
|---|---|
| `GET /api/produkte` | Katalog für Shop, Startseite, Warenkorb. Zeitlimit 4 s, 10 Minuten im Browser zwischengespeichert. Fehlt oder scheitert der Endpunkt, gilt die eingebaute Liste (`assets/js/produkte.js`). Leerer Katalog zeigt eine Hinweisbox mit Telefon und E-Mail. |
| `GET /api/produkte/{id}` | Allgemeine Produktseite `produkt.html?id=…`. Antwort 404 mit `ok:false` heißt „Artikel nicht gefunden“, jede andere Störung fällt auf den Katalog zurück. |
| `GET /api/gutschein` | Beträge, Min/Max, Zustellarten, `einloesen`. `aktiv:false` oder HTTP 404 blendet Gutscheinkarte und Formular aus, das Einlösefeld erscheint nur bei `einloesen:true`. |
| `POST /api/gutschein/pruefen` | Nur auf Knopfdruck „Einlösen“. Gültig: Guthaben wird abgezogen, Zeilen „Gutschein“ und „Zu zahlen“. Ungültig: neutrale Meldung. 429: „Bitte später noch einmal.“ |
| `POST /api/anfrage` | `typ=kontakt`, `widerruf`, `gutschein` (Betrag als Zahl), `bestellung` (Positionen, Adresse, Lieferart, Zahlungsart, Summen, optional `gutscheincode`). Antwort `ref`, optional `paypalUrl` und `gutschein{abgezogen,rest,zuZahlen}`. |
| `POST /api/e` | Besucherzahl per `sendBeacon`, ohne Cookies. |
| Bausteine | `data-mk="bewertungen"` (Startseite, Block erscheint erst bei Inhalt) und `data-mk="cookies"` (Footer). |

Farben und Kategorien kommen aus der Katalogantwort (`farben`, `kategorien`), Filter und Farbfelder werden daraus gebaut.

## Verhalten bei Abweichungen

- Kennt das Portal `typ=bestellung` nicht (HTTP 400/404/501 oder 422 auf `typ`), geht die Bestellung einmal als `typ=kontakt` mit Freitext raus.
- 422 auf `summe` oder `positionen`: Katalog neu laden, Warenkorb neu berechnen, Hinweis „Preise haben sich geändert“.
- `paypalUrl` wird nur als Zahlknopf gezeigt, wenn sie mit `https://paypal.com/…`, `https://www.paypal.com/…` oder `https://paypal.me/…` beginnt, nicht bei Abholung, nicht wenn der Gutschein alles deckt.
- Texte aus dem Portal werden maskiert, Bild-URLs relativ oder mit führendem `/`, Bildmaße und Alt-Text aus dem Katalog.
- Menge je Position 1 bis 99.

## Produktseiten und Suchmaschinen

Das Portal erzeugt keine Seiten. Artikel, die im Generator stehen, haben eine eigene statische Seite mit strukturierten Daten und Eintrag in der Sitemap.
Neue Artikel aus dem Portal erscheinen sofort im Shop und öffnen `produkt.html?id=…`; diese Seite ist auf `noindex` gesetzt.
Für eine eigene, auffindbare Seite pro Artikel muss der Artikel in `build/produkte.py` ergänzt und die Website neu hochgeladen werden.

## Was das Portal nicht tut

Das Portal erstellt keine Rechnung und prüft keine PayPal-Zahlung. Der Betrieb setzt den Status „bezahlt“ selbst. Die Website verspricht nichts anderes.
