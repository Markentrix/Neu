# Portal-Schnittstelle für den Schichtatelier-Shop

Ziel: Artikel, Farben, Bilder und Bestellungen werden im Markentrix-Portal gepflegt. Die Website bleibt statisch
und holt alles Dynamische wie bisher über relative JSON-Endpunkte derselben Domain (kein eigenes Backend).

Heute vorhanden und genutzt: `POST /api/anfrage`, `POST /api/e`, Bausteine `data-mk="bewertungen"` und `data-mk="cookies"`.
Neu nötig: fünf Lese-Endpunkte für den Katalog und ein strukturierter Bestelltyp.

## 1. Katalog (lesend, öffentlich, cachebar)

### `GET /api/produkte`
Alle **aktiven** Artikel in Anzeigereihenfolge. Entwürfe werden nicht ausgeliefert.

```json
{
  "stand": "2026-10-29T10:00:00Z",
  "versand": { "pauschale": 4.90, "versandfreiAb": 49.00, "abholung": true },
  "kategorien": [ { "key": "wohnen", "name": "Wohnen & Deko", "sort": 1 } ],
  "farben": [ { "key": "orange-silk", "name": "Orange Silk (glänzend)", "hex": "#e07a2a" } ],
  "produkte": [
    {
      "id": "kuerbis-mini",
      "name": "Kleiner Kürbis",
      "kategorie": "wohnen",
      "preis": 0.99,
      "kurz": "Lächelnder Mini-Kürbis aus glänzendem Silk-PLA …",
      "lang": "Der kleine Kürbis kommt mit geschnitztem Gesicht …",
      "material": "PLA+ Silk (glänzend)",
      "masse": "ca. 3,5 cm hoch",
      "gewicht": "ca. 6 g",
      "farben": ["orange-silk"],
      "tags": ["neu", "bestseller"],
      "personalisierbar": false,
      "textlabel": null,
      "textmax": 0,
      "bilder": [ { "url": "/media/produkte/kuerbis-mini-1.webp", "w": 1200, "h": 900, "alt": "Kleiner Kürbis in Orange Silk" } ],
      "sort": 10,
      "aktiv": true,
      "geaendert": "2026-10-29T09:12:00Z"
    }
  ]
}
```

Regeln:
- Preise als Zahl in Euro (Endpreis). Bild-URLs relativ (`/media/…`), WebP, Hauptbild 4:3 mit 1200 × 900.
- `farben` je Artikel verweist auf die zentrale Farbliste. Erster Eintrag = Vorauswahl und Farbe für den Schnellkauf.
- `tags`: `neu`, `bestseller`, `personalisiert`, frei erweiterbar. `personalisierbar: true` erzwingt das Wunschtext-Feld.
- Header `Cache-Control: public, max-age=300` und `ETag`, damit die Seite den Katalog nicht bei jedem Aufruf neu lädt.

### `GET /api/produkte/{id}`
Ein einzelner Artikel in derselben Struktur, inklusive `verwandt: ["kuerbis-trio", …]` für „Oft zusammen bestellt“.
Antwort 404 `{ "ok": false }`, wenn inaktiv oder unbekannt.

### `GET /api/farben`
Zentrale Farbliste (identisch zum Block in `/api/produkte`), damit das Portal Farben nur einmal pflegt.

### `GET /api/kategorien`
Kategorien mit Sortierung. Leere Kategorien sollen weggelassen werden.

### `GET /api/gutschein`
Konfiguration des Geschenkgutscheins: `{ "aktiv": true, "betraege": [10,20,30,50], "min": 10, "max": 500, "gueltigkeitMonate": 36, "zustellung": ["E-Mail (PDF)", "Post (Karte)"] }`.

## 2. Bestellungen (schreibend, wie bisher über `/api/anfrage`)

Heute schickt der Warenkorb `typ="kontakt"` mit `art="bestellung"` und der Bestellung als Text. Damit das Portal
Bestellungen als Vorgang mit Positionen, Status und Rechnung führen kann, braucht es einen eigenen Typ:

### `POST /api/anfrage` mit `typ="bestellung"`

```json
{
  "typ": "bestellung",
  "name": "Max Muster", "email": "max@example.org", "telefon": "",
  "einwilligung": "ja", "agb": "ja", "website": "",
  "lieferart": "versand",
  "adresse": { "strasse": "Musterweg 1", "plz": "29227", "ort": "Celle", "land": "DE" },
  "zahlungsart": "paypal",
  "positionen": [
    { "id": "kuerbis-trio", "name": "Kürbis-Trio", "farbe": "orange-silk", "text": "", "menge": 2, "einzelpreis": 2.79 }
  ],
  "zwischensumme": 5.58, "versand": 4.90, "summe": 10.48,
  "anmerkung": ""
}
```

Antwort wie bisher `{ "ok": true, "ref": "SA-2026-0042" }`, zusätzlich optional `"paypalUrl"`: ein fertiger PayPal.Me-Link
mit Betrag, den die Danke-Seite sofort als Zahlknopf zeigt. Validierungsfehler als 422 mit `errors` je Feld,
Preisabweichung zwischen Website und Portal als 422 auf `summe` (das Portal rechnet mit seinen Preisen nach).

`lieferart`: `versand` oder `abholung` (dann keine Adresse nötig, Versand = 0). `zahlungsart`: `paypal` oder `abholung`.

### `POST /api/anfrage` mit `typ="gutschein"` (vorhanden)
Felder, die die Website bereits sendet: `betrag`, `zustellung`, `empfaenger`, `absender`, `gutscheintext`, `anschrift`, `name`, `email`, `einwilligung`.

## 3. Was das Portal als Oberfläche braucht (kein Website-Thema, aber Voraussetzung)

- Artikel anlegen und bearbeiten: Name, Kategorie, Preis, Kurz- und Langtext, Material, Maße, Gewicht, Farben (Mehrfachauswahl), Tags, personalisierbar mit Feldbezeichnung und Zeichenlimit, Sortierung, aktiv/Entwurf.
- Bilder hochladen: automatisch auf 4:3 schneiden, WebP erzeugen, optional Hintergrund freistellen (wie beim Kürbis).
- Farben und Kategorien zentral pflegen.
- Bestellungen: Liste mit Status (eingegangen, bestätigt, bezahlt, im Druck, versendet/abgeholt), Bestätigungs-Mail mit Rechnung und PayPal-Link, Sendungsnummer eintragen, Abholtermin.
- Gutscheine: Code erzeugen nach Zahlungseingang, Restguthaben, Ablauf.
- Einstellungen: Versandpauschale, versandkostenfrei ab, Abholung ja/nein, Produktionszeit, Lieferzeit.

## 4. Was sich auf der Website ändert, sobald die Endpunkte da sind

1. `shop.js` lädt beim Start `GET /api/produkte`. Antwortet das Portal nicht, bleibt die eingebaute Liste (`produkte.js`) als Fallback.
   Shop-Raster, Filter, Warenkorb, Cross-Selling und Schnellkauf arbeiten dann mit den Portaldaten.
2. Produktseiten: Für Suchmaschinen bleibt pro Artikel eine eigene HTML-Datei mit JSON-LD die beste Lösung. Empfehlung:
   Das Portal erzeugt beim Speichern eines Artikels die Datei `produkt/<id>.html` aus einer Vorlage (die aktuelle Seite dient als Muster)
   und aktualisiert `sitemap.xml`. Alternative mit weniger Aufwand: eine generische `produkt.html?id=…`, die den Artikel per
   `GET /api/produkte/{id}` lädt; dann aber ohne eigene URL je Artikel in der Google-Suche.
3. Kasse sendet `typ="bestellung"` mit Positionen statt Freitext.
4. Danke-Seite zeigt `paypalUrl` aus der Antwort als Zahlknopf.

Bis dahin funktioniert alles wie jetzt: Artikel in `build/produkte.py`, Bilder in `build/fotos/`, Bestellungen als Kontakt-Anfrage mit Bestelltext.
