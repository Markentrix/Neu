# Verkaufsorientierte Seiten (Händler mit Bestand: Motorrad, Kfz, Handel)

Erstes Beispiel: `demos/motorradhandel-celle/`. Ziel solcher Seiten: Besucher in Anfragen, Anrufe und Probefahrten verwandeln, nicht „schön informieren“.

## Muster
1. **Bestand zuerst.** Fahrzeuge und Preise sind der Hauptinhalt. Start: Suchfilter im Hero (Marke, Art, Preis bis), Preis-Kacheln („Bis 4.000 €“), Highlights, Link auf den ganzen Bestand.
2. **Bestandsseite mit Filter und Sortierung.** Karten stehen als HTML in der Seite (funktioniert ohne JS und für Suchmaschinen), JS blendet nur aus/ein und sortiert. Filter per URL teilbar (`?marke=Honda&preis=4000`). Zähler mit `aria-live`, Leer-Zustand mit Wunschsuche-CTA.
3. **Detailseite je Fahrzeug** (Verkaufsstrecke): Galerie, Preis groß, Eckdaten, drei CTAs (Probefahrt, Anrufen, WhatsApp), Anfrageformular mit Fahrzeug vorbelegt, Inzahlungnahme- und Finanzierungs-Häkchen (nie vorangekreuzt), ähnliche Fahrzeuge. Schema.org `Product`/`Offer` mit echtem Preis.
4. **Immer erreichbar:** Anrufen und Probefahrt im Header, mobil feste Aktionsleiste unten (Anrufen, WhatsApp, Probefahrt).
5. **Zweite Strecke: Ankauf/Inzahlungnahme.** Eigene Seite und Band auf der Startseite, Formular mit den Eckdaten (Modell, EZ, KM, TÜV, Preisvorstellung, Fotos, PLZ).
6. **Ehrliche Dringlichkeit:** „Zwischenverkauf vorbehalten, bitte Verfügbarkeit telefonisch bestätigen“, Status-Feld (verfügbar/reserviert/verkauft) im Datensatz. **Keine** erfundene Verknappung, keine Fake-Zähler, keine erfundenen Bewertungen.
7. **Einwände beantworten** (FAQ): Probefahrt, Inzahlungnahme, Finanzierung, Verfügbarkeit, Wunschsuche, Gewährleistung (Formulierung immer vom Kunden).
8. **Preise** nur wie vom Händler angegeben (VB, brutto/Differenzbesteuerung klären, PAngV beachten), Stand nennen.

## Daten und Pflege
Bestand liegt als Datensatz (`assets/bestand.json` bzw. Liste im Build-Skript). Für den Livebetrieb Pflegeweg vereinbaren (Tabelle/CMS, Händler-Import, Export nach Mobile.de-Format), sonst veraltet der Bestand und die Seite verkauft nichts. Als Zusatzleistung anbieten.

## Fotos entscheiden über Verkauf
Alte Händlerfotos sind oft klein und uneinheitlich. Empfehlung: einheitliches Fotoset je Fahrzeug (min. 1600 px breit, 6–10 Bilder, gleiche Perspektiven, ruhiger Hintergrund). Fotoshooting ist Zusatzleistung (Preis vorab vereinbaren). Nicht hochskalieren, kleine Fotos in kleinen Kacheln zeigen.

## Messung
Mobil gedrosselt (Slow 4G, 4x CPU): Performance, Barrierefreiheit, Best Practices je 100, LCP 1,0–1,9 s, CLS ≤ 0,04. Bei Bildlisten nur die ersten drei Bilder eager, das erste mit `fetchpriority="high"`; Überschriften-Reihenfolge beachten (Karten direkt unter H1 als H2).

## Paket
Bestand mit Detailseiten, zwei Anfragestrecken und Danke-Seite passt zu **WEB + FUNNEL** (bis zwölf Seiten mit Anfrage- oder Verkaufsstrecke). Detailseiten gelten als Datenbankseiten, bei großem Bestand mit Pflegeweg gesondert kalkulieren.
