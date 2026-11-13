# Markentrix · CI-Paket 2026, Version 3.0

| Datei | Inhalt |
|---|---|
| `Markentrix_CI_2026_v3.pdf` | Das Markenhandbuch, 27 Seiten |
| `Markentrix_Bild-CI_ChatGPT.md` | Stilblock, Ausschlussblock und Vorlagen für KI-Bilder |
| `logo/svg/` | Alle Logo-Varianten als Vektor, für Web und Druck |
| `logo/png/` | Alle Logo-Varianten als PNG mit transparentem Grund |
| `assets/` | Aufwärtslinie für helle und dunkle Flächen |
| `tokens.css` | Farben, Schrift, Abstände, Radien, Schatten als CSS-Variablen |
| `src/` | Quelle des Handbuchs, der Logos und die Schriftdateien |
| `vorschlag/` | Entstehung: Vorschläge, Farbanalyse, Farbsuche |

## Palette

| Ton | HEX | Aufgabe |
|---|---|---|
| Kreide | `#F7F4EE` | Papierton, Grund |
| Tiefsee | `#0C2128` | Tintenton: Text, dunkle Flächen |
| Pfauenblau | `#045268` | Hauptfarbe |
| Leinen | `#EAE2D3` | Flächenfarbe, Rahmen |
| Kupfer | `#C67432` | Akzent |

Schriften: Archivo (Überschriften, Wortmarke) und Source Sans 3 (Text), beide unter der SIL Open Font License. Die Lizenztexte liegen in `src/fonts/`.

## Handbuch neu bauen

```
cd ci/src
node build.js
```

Voraussetzung: Node mit Playwright und Chromium. Die Seiten liegen in `src/parts/`, das Gerüst in `src/template.html`.

## Logos neu erzeugen

```
python3 src/build_logo.py src/wortmarke-archivo-extrabold.json logo/svg
```

Die Bildmarke ist aus der früheren Bilddatei vermessen. Die Wortmarke ist Archivo ExtraBold mit −2 % Laufweite, in Kurven umgewandelt.

## Farbwerte nachrechnen

`vorschlag/farblabor/` enthält die Werkzeuge der Farbsuche: Kontrast, Simulation von Farbfehlsicht und Druck-Simulation mit PSO Coated v3 und PSO Uncoated v3. `spezifikation.py` gibt alle Werte der Palette aus.
