# DESIGN.md: Pizzeria Molise, Celle

Stand: Redesign-Runde für die Portal-Anbindung. Ausgabeordner: `website-fertig/`. Quellen: `layouts/restaurant/`.

## Kernidee (ein Satz)
Die Pizzeria Molise ist ein Lokal mit Straßenfenster in der Celler Altstadt: Wer vorbeikommt, sieht eine grün-weiß-rote Markise, ein Stück Pizza und ein Preisschild. Die Seite soll sich wie dieser Zettel am Fenster anfühlen: wenig Wörter, große Schrift, ein Preis, ein Foto.

## Material (ehrlich)
- Vorhanden: Name, Ort, Straße (ohne Hausnummer), Telefon, Speisekarte mit Preisen (Fremdquelle, Stand März 2024), Zeiten Mo bis Sa 11 bis 20 Uhr (eine Quelle).
- Nicht vorhanden: eigene Fotos, Logo, Betreiber, Geschichte, bestätigte Hausnummer. Die Speisefotos sind KI-generierte Platzhalter (keine Personen), `fenster` und `raum` sind gezeichnete Platzhalter. Alles steht in der OFFEN-Liste.

## Farben (60 / 30 / 10)
| Name | Hex | Rolle |
|---|---|---|
| Papier | `#fffdf8` | Grund (60 %) |
| Ofenruß | `#1a1612` | Text, Rahmen, Linien (30 %) |
| Tomate | `#cd212a` | Hauptfarbe für Handlung: Knöpfe, Hervorhebung der Schlagzeile |
| Basilikum | `#00793c` | Fläche "Zum Mitnehmen", Status "geöffnet", vegetarisch/vegan (Text auf Weiß 5,6:1) |
| Butter | `#ffd66b` | Preisaufkleber und Hinweisflächen, sonst nichts |
| Zettelgrau | `#5b544b` | Fließtext zweiter Ordnung (auf Papier 7,3:1) |

Herkunft: Fahne Italiens (Grün, Weiß, Rot) für einen Italiener, gebrochen durch Papier und Ruß, damit es nach Zettel und nicht nach Flagge aussieht. Verlauf, Glow oder Glas kommen nicht vor.

## Schriften (lokal, woff2)
- Display: **Anton** (Plakatschrift, nur Überschriften, Großbuchstaben, sparsam: eine Überschrift pro Block).
- Text: **Instrument Sans** (400 bis 600), Zeilenlänge 55 bis 70 Zeichen.
- Skala (Mobil / Desktop): Hero 2,7 / 6,2 rem, Abschnittstitel 1,9 / 4 rem, Gericht 1,0 / 1,1 rem, Beschreibung 0,84 / 0,94 rem. Hero mindestens das Dreifache des Fließtexts.
- Begründung Großbuchstaben: Plakat- und Fensterzettel-Anmutung ist die Idee. Kleine Großbuchstaben-Label über Überschriften gibt es nicht.

## Layout-Konzept
Die Seite folgt dem, was ein Gast entscheiden muss: Was gibt es (Foto, Preis), kann ich reservieren, was kostet es, wo ist es.

```
+--------------------------------------------------+
| Kopf: Name   Speisekarte  Mitnehmen  Anfahrt  Tel |  Trikolore-Band
+--------------------------------------------------+
| [Status heute]                      __________    |
| HEUTE SCHON                        |  Foto    |   |  Hero: Text links,
| PIZZA                              |  Pizza   |(5,50) Foto-Abzug mit
| GEHABT?                            |__________|   |  Preisaufkleber
+--------------------------------------------------+
| TISCH RESERVIEREN  [Tag][Uhrzeit][Gäste] [Weiter] |  schlanke Leiste
+==================================================+
| Pizza | Pasta | Flammkuchen | Salate | Antipasti  |  haftende Kategorienleiste
| PIZZA                  | Margherita ........ 5,50 |  je Kategorie: Foto links,
| [Foto]                 | Funghi  ........... 6,50 |  Preisliste rechts
| ...                                               |
+--------------------------------------------------+
| ################ VOLLE BREITE, GRÜN ############# |  Vollbreite-Moment
| PIZZA ZUM MITNEHMEN            [Foto Fenster]     |
+--------------------------------------------------+
| Anfahrt | Öffnungszeiten | Gut zu wissen (FAQ)    |
+--------------------------------------------------+
```

Rhythmus: Hero dicht und hoch, Reservierung als schmale Leiste, Karte lang und ruhig, grüner Vollbreite-Block als Bruch, Fuß luftig. Auf dem Handy wird aus der Reihe eine kompakte Karte, die Kategorien bleiben in einer Zeile.

## Signatur (genau eine)
Der **Foto-Abzug mit Preisaufkleber**: das Pizzafoto liegt leicht schräg wie ein Abzug am Fenster, ein gelber runder Aufkleber nennt den Preis der Margherita. Er kehrt im Mitnehmen-Block nicht wieder, damit er einmalig bleibt. Alles andere ist ruhig und flach.

## Schatten, Rahmen, Radius (Hierarchie)
- Schweben dürfen nur: Foto-Abzug im Hero (harter Versatzschatten), Preisaufkleber, Reservierungsleiste.
- Alles andere (Knöpfe, Karten, Kategoriebilder) ist flach: 2 px Rahmen in Ofenruß, keine Schatten.
- Radius: Knöpfe und Chips rund, Fotos 8 px, Karte 12 px.

## Bewegung
Ein orchestrierter Moment beim Laden (Hero-Text steigt nacheinander ein, Foto-Abzug landet, Aufkleber poppt). Rückmeldung bei Aktionen (Reservierungszeile klappt aus, Häkchen beim Absenden, Einblenden der Kategorien nur am Desktop). `prefers-reduced-motion` schaltet alles ab.

## Prüfung gegen die Verboten-Liste
| Muster | Befund | Entscheidung |
|---|---|---|
| Pill-Badge über der H1 | Status "Jetzt geöffnet bis 20 Uhr" steht über der Schlagzeile | Bleibt, weil es ein echter Zustand ist (Uhrzeit, Ruhetag), kein Zierchip. |
| Großbuchstaben | Überschriften in Anton | Bewusste Plakat-Idee, siehe oben, keine Label über Überschriften. |
| Dreier-Slogans, "Mehr erfahren" | Fanden sich im Text | Entfernt. Knöpfe nennen die Handlung. |
| Schatten überall | Waren auf Knöpfen und Bildern | Entfernt, nur drei schwebende Elemente behalten. |
| Meta-Zeile "A · B · C" | Fußzeile | Ersetzt durch Zeilen. |
| KI-Fotos | Speisefotos sind KI-generiert | Platzhalter, unter OFFEN gemeldet. Keine KI-Personen. |
| Standard-Reihenfolge Hero, Logos, Features … | Nicht vorhanden | Abschnitte nach Gästefragen. |
| Gleiche Fade-ups, Bounce, `transition: all` | Nicht vorhanden | Einmaliger Einstieg, Rest ist Rückmeldung. |
| Austauschtest | Name gegen Pizzeria in anderer Stadt getauscht | Passt nur mit Piltzergasse, Fensterverkauf und Trikolore-Markise. Mit echten Fotos wird es eindeutiger. |
