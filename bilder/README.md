# Bilder für www.mobilvet-celle.de

14 KI-generierte Fotos (Higgsfield Soul 2) im Stil der Seite: ruhig, natürliches Licht, dezentes Grün.
Jedes Motiv liegt in drei Dateien vor:

- `NAME-1600.webp`: Desktop
- `NAME-800.webp`: Mobil
- `NAME-1600.jpg`: Fallback und og:image-tauglich

Alle Dateien werden vom eigenen Server geladen, sie passen also zur CSP `img-src 'self'`.

## Zuordnung

| Datei | Seite / Platz | Format | Alt-Text |
|---|---|---|---|
| `hero-hausbesuch` | index.html (Hero) | 16:9 | Tierärztin untersucht einen Golden Retriever beim Hausbesuch im Wohnzimmer |
| `hausbesuche-ankunft` | hausbesuche.html | 3:2 | Tierärztin mit Arzttasche wird an der Haustür von einer Halterin mit Hund begrüßt |
| `praxismobil` | hausbesuche.html, anfahrt.html | 3:2 | Tierärztin holt Ausrüstung aus dem Praxiswagen am Heiderand |
| `leistungen-untersuchung` | leistungen.html | 3:2 | Tierärztin hört eine Katze mit dem Stethoskop ab |
| `impfungen` | impfungen.html | 3:2 | Beagle-Welpe wird ruhig auf dem Behandlungstisch geimpft |
| `kastration-nachsorge` | kastration.html | 3:2 | Katze schläft nach dem Eingriff entspannt im Körbchen |
| `zahnbehandlung` | zahnbehandlung.html | 3:2 | Tierärztin kontrolliert Zähne und Zahnfleisch eines Golden Retrievers |
| `notfall` | notfall.html | 3:2 | Halterin ruft mit ihrem geschwächten Hund an der Seite die Tierärztin an |
| `senior-hund` | senior-hund.html | 3:2 | Älterer Labrador mit grauer Schnauze wird von seinem Halter gestreichelt |
| `abschied` | abschied-zu-hause.html | 3:2 | Alte Katze schläft geborgen auf dem Schoß, im Hintergrund eine Kerze |
| `ratgeber-kleintiere` | ratgeber.html | 3:2 | Kaninchen fressen Löwenzahn im Freigehege |
| `praxis-behandlungsraum` | praxis.html | 3:2 | Heller Behandlungsraum der Kleintierpraxis mit Blick ins Grüne |
| `kontakt-telefon` | kontakt.html | 3:2 | Frau vereinbart telefonisch einen Termin, ihre Katze sitzt daneben |
| `anfahrt-heide` | anfahrt.html | 16:9 | Heidelandschaft mit Sandweg und Kiefernwald bei Celle |

## Einbau-Beispiel

```html
<picture>
  <source type="image/webp"
          srcset="bilder/hausbesuche-ankunft-800.webp 800w, bilder/hausbesuche-ankunft-1600.webp 1600w"
          sizes="(max-width: 900px) 100vw, 50vw">
  <img src="bilder/hausbesuche-ankunft-1600.jpg" width="1600" height="1067"
       alt="Tierärztin mit Arzttasche wird an der Haustür von einer Halterin mit Hund begrüßt"
       loading="lazy" decoding="async" style="width:100%;height:auto;border-radius:16px">
</picture>
```

Maße: Bilder im Format 3:2 sind 1600×1067 groß, Bilder im Format 16:9 sind 1600×900.
Beim Hero-Bild `loading="lazy"` weglassen und `fetchpriority="high"` setzen.

## Wichtig

- Die Personen sind generiert. Sie zeigen **nicht** Dr. Voelzke und dürfen nicht als ihr Porträt ausgegeben werden.
  Für „Über Dr. Voelzke“ ein echtes Foto verwenden.
- Die Platzhalter in anfahrt.html für das Praxisgebäude und die Einfahrt bleiben echten Fotos vorbehalten.
  `praxismobil` ist nur ein Stimmungsbild und zeigt nicht den echten Wagen. Die Bildunterschrift entsprechend anpassen.
