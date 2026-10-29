# Schichtwerk – Online-Shop für 3D-Druck-Artikel

Statischer Shop (ca. 20 Artikel) für das Hosting auf dem Markentrix-Server mit Anbindung an das Markentrix-Portal.
Kein eigenes Backend: Bestellungen, Anfragen, Widerrufe, Google-Bewertungen, Cookie-Einstellung und Besucherzählung laufen über das Portal.

## Ordner

- `website-fertig/` – der fertige Upload (index.html liegt direkt darin). Nur diesen Ordner als ZIP hochladen.
- `build/` – Generator. `config.py` (Firmendaten), `produkte.py` (Artikel, Preise, Farben), `build.py` (Seiten), `images.py` (Illustrationen).

## Vor dem Hochladen

1. `build/config.py` prüfen: Firmendaten sind wie bei Markentrix eingetragen. Offen: PayPal.Me-Link, USt-IdNr. nach Erteilung, ggf. eigene Shop-E-Mail-Adresse.
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
| Zahlung | PayPal (PayPal.Me-Link aus config auf danke.html, sonst Link per Mail) oder Abholung in Celle mit Zahlung vor Ort | warenkorb.html, danke.html |

Artikel ändern: `build/produkte.py` bearbeiten, dann `python3 build/images.py` (nur bei neuen Artikeln) und `python3 build/build.py`.

## Logo

`brand/` enthält das Logo (Bildmarke: ein S aus Druckschichten in Sand bis Kupfer auf Tannengrün; Wortmarke „Schicht·werk“ in Fraunces als Pfade; dazu ein rundes Siegel für Verpackung und Aufkleber):
SVG hell/dunkel, mit und ohne Kachel, einfarbig, sowie PNG-Exporte (2400 px Logo, 1024 px Marke). Erzeugt mit `python3 build/logo.py`.
Favicon und App-Icons in `website-fertig/` entstehen aus derselben Marke (`python3 build/images.py`).

## Farben

Palette „Warmweiß, Tiefgrün, Kupfer“: Fläche `#f7f4ee`, Text `#1c2a24`, Marke/Struktur Tannengrün `#1f4d3a`, Kaufknopf Kupfer `#9e6230` (nur für Warenkorb und Bestellen), Fehler `#b23a2e`.
Alle Farben sind Tokens in `website-fertig/assets/css/style.css` (`:root`, hell und dunkel). Logo- und Illustrationsfarben stehen in `build/logo.py` und `build/images.py`.

## Beispielartikel und Freischalten

Die 20 Beispielartikel in `build/produkte.py` tragen `entwurf=True` und werden nicht gebaut. Ein Artikel kommt in den Shop, sobald
`entwurf` entfernt ist; Maße, Gewicht, Material und Preis vorher prüfen, Foto wie unten ablegen. Kategorien und Filter erscheinen automatisch nur für Artikel, die es gibt.

## Echte Produktfotos

Foto als JPG unter `build/fotos/<artikel-id>.jpg` ablegen, im Artikel in `build/produkte.py` `foto=True` setzen
(optional `crop=(links, oben, rechts, unten)` in Pixeln des Originals), dann `python3 build/images.py` und `python3 build/build.py`.
Der Generator schneidet auf 4:3 zu, skaliert auf 1200 × 900 und speichert WebP. Artikel ohne `foto` behalten ihre Illustration.
Das Startseiten-Foto (`assets/img/hero.webp`, quadratisch) kommt aus `HERO` in `build/images.py`: Quelle und Zuschnitt dort ändern.
Mit `freistellen=True` wird der Hintergrund einmalig per rembg entfernt (`pip install rembg onnxruntime`), das Ergebnis liegt als `build/fotos/<id>-cut.png` und wird auf den hellen Shop-Hintergrund mit Schatten gesetzt.

## Farben pflegen

Zentrale Farbliste `FARBEN` in `build/produkte.py` (Schlüssel, Anzeigename, Farbwert). Pro Artikel `farben=[...]`, der erste Eintrag ist die
Vorauswahl. `STANDARDFARBEN` für Artikel, die es in allen Farben gibt. Die Karten zeigen „in N Farben“, die Produktseite die Farbfelder.

## Schriften

Überschriften, Produktnamen, Preise und Wortmarke: Fraunces (variabel, SIL OFL), Fließtext und Bedienelemente: Inter. Beide liegen lokal
unter `website-fertig/assets/fonts/`, Lizenzhinweise in `OFL.txt`. Betonte Wörter in Überschriften stehen in `<em>` (kursiv, grün).
