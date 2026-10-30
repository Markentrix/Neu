# DESIGN.md – Schichtatelier (Celle)

Gehört neben den Ordner `website-fertig/`, nicht hinein (`.md` ist im Upload nicht erlaubt).

## Kernidee

Schichtatelier ist die Ein-Mann-Werkstatt von Christian Wien in Celle: ein Bambu Lab X1 Carbon druckt kleine Dinge erst nach der Bestellung, Schicht für Schicht.
Man sieht diese Schichten am fertigen Teil. Die Seite zeigt sie offen, statt sie hinter glatter Produktfotografie zu verstecken:
echtes Foto vom Druckbett vorn, Lieferzeit als Druckzeit-Balken, Material mit Temperaturangabe statt Versprechen.

## Material und Bestand (Schritt 1)

Vorhanden und echt: Logo (Wortmarke, Schicht-S, Düse im „i“), ein Foto des Kleinen Kürbis auf dem Druckbett des X1 Carbon, Firmendaten (Impressum Markentrix), Preise der drei Kürbis-Artikel, Gutscheinidee.
Nicht vorhanden: weitere Fotos (Werkstatt, Drucker, Inhaber, weitere Artikel), Kundenstimmen, Zahlen, Texte vom Inhaber. Alles davon steht als OFFEN am Ende der Antwort und wird nicht erfunden.
Entfernt, weil nicht belegt: „Bestseller“, „Das bestellen unsere Kunden am häufigsten“, „ein paar Drucker“, „Filamente von europäischen Herstellern“, „Recycling“, „plastikfreie Verpackung“, „DHL“, „Gefertigt in Deutschland“, Nachbearbeitungs-Leistungen, Farbangaben auf Materialseiten.

## Farben (Rollen, Verteilung 60 / 30 / 10)

| Name | Hex | Rolle | Kontrast |
|---|---|---|---|
| Papier | `#f3f5f1` | Grund, 60 % | Tinte darauf 14,9:1 |
| Tiefgrün | `#1f4d3a` | Hauptfarbe: Hero, Bänder, Footer, Links, 30 % | Creme darauf 8,2:1 |
| Tintengrün | `#15231c` | Text | auf Papier 14,9:1, Sekundärtext `#44544b` 7,3:1 |
| Kupfer | `#9e6230` | einziger Akzent, nur für Handlung (Kaufen, Anfragen, Fokus) | Weiß darauf 4,95:1, auf Papier 4,5:1 |
| Kupfer hell | `#e2ae7c` | derselbe Akzent auf Tiefgrün | auf Tiefgrün über 5:1 |
| Fläche | `#e4eae5` | Bildkacheln, Summenfeld | Tinte darauf 13,3:1 |

Dazu ein Signalton für Fehler (`#b23a2e`, 5,4:1) und das helle Mint `#8fc7ab` ausschließlich im Logo auf dunklem Grund.
Dunkelmodus nur über `prefers-color-scheme`, nicht als Dauerzustand.

Warum das keine KI-Palette ist: Grund ist kühl grünlich-weiß, nicht Creme. Der Akzent ist Bronze (Kupfer-Filament), nicht Terrakotta. Das Grün trägt Flächen, nicht nur einen Button.
Die Farben kommen aus dem Logo des Kunden (Grün, Kupfer) und aus dem Material: Silk-PLA in Kupfer auf dunklem Druckbett.

## Schriften

- **Display: Abril Fatface**, nur für H1, H2, große Preise. Die Wortmarke des Kunden ist eine Fett-Didone mit Kugelenden, Abril kommt ihr am nächsten (gegen Playfair, DM Serif, Bodoni Moda, Gloock, Rozha, Young Serif verglichen).
- **Text: Hanken Grotesk** (variabel 300–800), Fließtext, Menü, Buttons, Kartentitel, Zahlen mit tabellarischen Ziffern.
- Keine Hilfsschrift nötig. Beide Schriften lokal als woff2, SIL OFL.

Skala (Basis 17 px): 14 / 17 / 21 / 28 / 40 / 60 / Hero 52–104 px (clamp). Hero-Headline mindestens 3× Fließtext. Zeilenlänge Text 60–72 Zeichen.
Überschriften ohne Versalien-Labels, ohne kursive oder farbige Einzelwörter.

## Layout-Konzept

Eine Seite für Menschen, die ein kleines, echtes Teil kaufen oder eine Datei drucken lassen wollen. Reihenfolge nach Entscheidung: sehen, kaufen, wissen wann, eigene Datei, Material.

```
┌────────────────────────────────────────────────────────┐
│ Wortmarke (Düse im i)                 Shop  Druck  …  🛒 │  Papier, ruhig, ohne Blur
├───────────────────────────┬────────────────────────────┤
│ Gedruckt in Celle,        │                            │
│ Schicht für Schicht.      │   FOTO: Kürbis auf dem     │  Hero: vollbreit Tiefgrün,
│ 2 Sätze                   │   Druckbett des X1 Carbon  │  Foto bündig bis zum Rand,
│ [Im Shop ansehen]         │   (ohne Rundung)           │  baut sich in 14 Schichten auf
│ Bildunterschrift          │                            │
├──────────────────────┐    └────────────────────────────┤
│                      └──┐  Schichtkante (Treppe)         │
│                         └──┐                            │
├────────────────────────────┴───────────────────────────┤
│ Im Shop        ┌──────────────┬──────────┐              │  1 große Kachel (2×2) + 2 kleine,
│ (schmal links) │  5er-Set     │  Trio    │              │  ungleich, keine 3 gleichen Karten
│                │              ├──────────┤              │
│                │              │  Mini    │              │
├────────────────┴──────────────┴──────────┴──────────────┤
│ Wann es bei Ihnen ist:  [ Bestellung | Druck 2–4 Tage | Versand 2–3 Tage ]  (Balken nach Maßstab) │
├────────────────────────────────────────────────────────┤
│ VOLLBREIT Tiefgrün: „Sie haben eine Datei?“  [Angebot anfordern]                                │
├────────────────────────────────────────────────────────┤
│ Material: PLA   | Dekoration, Halter     | bis 55 °C  → │  Liste statt Karten
│           PETG  | Küche, Bad, Technik    | bis 75 °C  → │
│           ABS / TPU …                                   │
├────────────────────────────────────────────────────────┤
│ Footer Tiefgrün: großes Logo · Kontakt · 2 Linklisten   │  keine 4 Spalten, kein Newsletter
└────────────────────────────────────────────────────────┘
```

Unterseiten nutzen dieselben Tokens, Navigation und Footer. Rhythmus: Hero sehr hoch, Shop weit und asymmetrisch, Zeitleiste flach, Datei-Band vollbreit, Materialliste eng.

## Signatur (genau eine)

**Die Schicht.** Der Seitenaufbau druckt sich Schicht für Schicht: das Hero-Foto erscheint von unten nach oben in 14 harten Stufen (`steps()`), danach steht die Schichtkante als Treppe unter dem Hero.
Dieselbe Idee steckt im Logo (Druckspur-Linie in die Düse) und im Schicht-S. Sonst gibt es keine Effekte; alles andere ist ruhig.
Mit `prefers-reduced-motion` steht das Foto sofort.

## Plan gegen die VERBOTEN-Liste (Schritt 3)

| Befund im ersten Stand | Änderung | Grund |
|---|---|---|
| Fraunces + Inter | Abril Fatface + Hanken Grotesk | beide stehen auf der Reflexliste |
| Creme + Kupfer + Serif | kühles Papier, Bronze, Grün trägt Flächen, andere Schrift | zweite KI-Welle |
| Großbuchstaben-Label über Überschriften | entfernt | verboten |
| kursive Farbwörter in Headlines | entfernt | verboten |
| vier Icon-Karten, drei gleiche Schritt-Karten | Zeitleiste, Liste, Fließtext | verboten |
| Streifen links an Karten, Rahmen um jede Karte, Pill-Buttons | Flächenkacheln ohne Rahmen, Buttons mit 3 px Radius | verboten |
| Check-Icon-Zeilen in Kopf, Shop, Footer | Konditionen als Beschriftungsliste, nur wo sie gebraucht werden | verboten, Wiederholung |
| `backdrop-filter` am Kopf | deckender Kopf | keine Überlagerung nötig |
| „Bestseller“, „Neu“-Chips | entfernt | Status ohne echten Zustand |
| Vier-Spalten-Footer | Kontaktblock + zwei Listen | verboten |
| Standard-Reihenfolge Hero → Features → Testimonials → Zahlen | Hero → Shop → Lieferzeit → Datei → Material | Reihenfolge nach Entscheidung |

Bewusst behalten: Grün und Kupfer als Markenfarben (Logo des Kunden, ausdrücklich so gewählt); Dunkelmodus nur per Systemeinstellung.
Austauschtest: Mit dem Namen einer Bäckerei oder Kanzlei passt nichts davon: Druckbett-Foto, Druckzeit-Balken, Materialtemperaturen und die Schicht als Aufbau gehören zu genau diesem Betrieb.

## Text

Konkret, Hand-Werk-Ton, Siezen. Buttons nennen die Handlung („Im Shop ansehen“, „Angebot für meine Datei anfordern“, „In den Warenkorb“). Keine Gedankenstriche im Fließtext, keine Dreier-Slogans, keine Floskeln der Verbotsliste.
