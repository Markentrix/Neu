# Kunden-Design-System (Phase 2)

Ziel: erkennbar die Marke des Kunden, hochwertig, konsistent, zugänglich, schnell.

## Token-Ableitung aus Kunden-CI
0. **Keine CI vorhanden?** Mini-CI nur als Vorschlag für Demo/Website; Logo/Farb-/Schriftwelt als Leistung anbieten (CI BASIC 1.290 €, CI BUSINESS 2.490 €, CI PREMIUM 4.490 €; 500 € Kombivorteil mit Website laut Preisliste).
1. **Primärfarbe** vom Kunden. Kontrast prüfen: als Textfarbe auf Weiß ≥ 4.5:1, sonst abdunkeln (`--brand-ink`). Als Button-Fläche: Textfarbe (weiß oder dunkel) mit ≥ 4.5:1 wählen.
2. **Neutralskala** (Hintergründe, Linien, Text) aus der Primärfarbe oder neutral ableiten, 8–10 Stufen. Text nie reines Schwarz auf reinem Weiß, aber ≥ 7:1 für Fließtext anstreben.
3. **Akzent** sparsam (≤ 10 %) für CTA/Highlights. Status: Erfolg, Fehler (≥ 4.5:1).
4. **Typo:** Kundenschrift, wenn lizenziert und Web-Lizenz vorhanden; sonst passende OFL-Schrift (selbst gehostet, WOFF2, variabel, Subset). Max. 2 Familien, Skala per `clamp()`, Zeilenlänge 65–75 Zeichen.
5. **Raster/Abstände:** 8-pt, Container 1120–1280 px, Sektionsabstand `clamp()`.
6. **Radius/Schatten/Linien:** ein Radius-Set, wenige weiche Schatten, Branchencharakter (Handwerk: robust; Praxis: ruhig; Gastro: warm).
7. **Dark-Modus** nur auf Wunsch; sonst `color-scheme: light`.

Alle Werte als CSS-Custom-Properties in `tokens.css` (siehe Starter). Eine Quelle der Wahrheit.

## Komponenten-Set (pro Projekt benötigt)
Header/Nav (mobil Menü barrierefrei), Hero, Leistungskarte, Prozess-Schritte, Referenz-Galerie (Lightbox barrierefrei), Testimonial (nur echt), Team-Karte, FAQ (`details`), Kontaktformular, Kontaktleiste (Telefon/Maps/Zeiten), CTA-Band, Footer, Cookie-Dialog, Danke-/404-Seite.

## Bildsprache
Echte Fotos vom Betrieb vor Stock. Einheitlicher Zuschnitt/Farbton, Menschen lächeln nicht gestellt, Arbeit zeigen. KI-Bilder: nur mit Kundenfreigabe, nie als „echtes Team/Referenz“, bei realistischen Personen kennzeichnen. Lizenznachweis je Bild in der Doku. Personenfotos nur mit Einwilligung. Icons als Inline-SVG-Set, einheitlicher Stil.

## Moodboard-Check vor Umsetzung
Passt zur Zielgruppe? Hebt sich vom lokalen Wettbewerb ab? Erlaubt Kontrast/Lesbarkeit? Vom Kunden freigegeben?
