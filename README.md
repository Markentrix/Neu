# Schichtwerk – Online-Shop für 3D-Druck-Artikel

Statischer Shop (ca. 20 Artikel) für das Hosting auf dem Markentrix-Server mit Anbindung an das Markentrix-Portal.
Kein eigenes Backend: Bestellungen, Anfragen, Widerrufe, Google-Bewertungen, Cookie-Einstellung und Besucherzählung laufen über das Portal.

## Ordner

- `website-fertig/` – der fertige Upload (index.html liegt direkt darin). Nur diesen Ordner als ZIP hochladen.
- `build/` – Generator. `config.py` (Firmendaten), `produkte.py` (Artikel, Preise, Farben), `build.py` (Seiten), `images.py` (Illustrationen).

## Vor dem Hochladen

1. `build/config.py` ausfüllen: Inhaber, Anschrift, Telefon, E-Mail, Steuernummer, Kleinunternehmer ja/nein, PayPal.Me-Link.
2. `python3 build/build.py` ausführen (erzeugt alle Seiten neu).
3. Produktfotos: Datei `website-fertig/assets/img/produkte/<artikel-id>.webp` (800×600) ersetzen, sonst nichts ändern.
4. Im Portal den Shop als eigenen Kunden/Site „Schichtwerk“ mit eigenen Daten anlegen (eigene Absender-Mail, eigener Google-Bewertungslink).

## Portal-Funktionen

| Funktion | Variante | Wo |
|---|---|---|
| Bestellung (Warenkorb) | API, `POST /api/anfrage`, `typ=kontakt`, Feld `art=bestellung` + `bestellung`, `summe`, `lieferadresse`, `zahlungsart` | warenkorb.html |
| Anfrage eigenes Modell | API, `typ=kontakt`, Feld `projekt` | kontakt.html |
| Widerruf | API, `typ=widerruf` | widerruf.html |
| Google-Bewertungen | Baustein `data-mk="bewertungen"` | index.html |
| Statistik-Einstellung | Baustein `data-mk="cookies"` | Footer |
| Besucherzahl | `POST /api/e` per sendBeacon | alle Seiten |
| Zahlung | PayPal.Me-Link (aus config) auf danke.html, sonst Vorkasse | danke.html |

Artikel ändern: `build/produkte.py` bearbeiten, dann `python3 build/images.py` (nur bei neuen Artikeln) und `python3 build/build.py`.
