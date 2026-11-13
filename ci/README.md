# Markentrix · CI-Paket 2026, Version 2.0

| Datei | Inhalt |
|---|---|
| `Markentrix_CI_2026_v2.pdf` | Das CI-Handbuch, 28 Seiten |
| `Markentrix_Bild-CI_ChatGPT.md` | Stilblock, Ausschlussblock und Vorlagen für KI-Bilder |
| `logo/svg/` | Alle Logo-Varianten als Vektor, für Web und Druck |
| `logo/png/` | Alle Logo-Varianten als PNG mit transparentem Grund |
| `assets/wachstumskurve.svg` | Signature-Element |
| `tokens.css` | Farben, Schrift, Abstände, Radien, Schatten als CSS-Variablen |
| `src/` | Quelle des Handbuchs und der Logos |

## Handbuch neu bauen

```
cd ci/src
node build.js
```

Voraussetzung: Node mit Playwright und Chromium. Die Seiten liegen in `src/parts/`, das Gerüst in `src/template.html`.

## Logos neu erzeugen

```
python3 src/build_logo.py src/wortmarke-space-grotesk-bold.json logo/svg
```

Die Bildmarke ist aus der gelieferten Bilddatei vermessen. Die Wortmarke ist Space Grotesk Bold, in Kurven umgewandelt.

## Schriften

Space Grotesk und Inter stehen unter der SIL Open Font License. Die Lizenztexte liegen in `src/fonts/`.
