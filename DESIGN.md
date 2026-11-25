# Gestaltung – PS Schneider, Kfz-Sachverständiger in Celle

Diese Datei liegt neben `website-fertig/` und gehört nicht in den Upload.

## Kernidee

**Vermessung.** Ein Sachverständiger nimmt ein Fahrzeug auf, markiert den Schaden, misst und belegt. Die Seite arbeitet genauso: Sie zeigt eine technische Zeichnung statt eines Stockfotos, setzt Maßlinien statt Dekor und benutzt Rot nur dort, wo etwas beschädigt ist oder sofort gehandelt werden muss.

**Ideensatz:** Auf dieser Seite wird die Schadensaufnahme des Sachverständigen (Fahrzeug von der Seite, Schaden rot eingekreist, Bremsspur, Beschriftungen mit Leitlinien) zur Navigation: Jede Stelle am Fahrzeug führt zum passenden Gutachten.

Austauschtest: Der Betrieb zwei Straßen weiter ist ein Autohaus oder eine Werkstatt. Eine Zeichnung, in der Bremsspur, Schadenszone und Radachse auf Gutachten-Arten zeigen, passt nur zu einem Sachverständigen. Der Test ist bestanden.

**Lebendige Sache:** die Schadenszeichnung im Kopfbereich. Ab Tablet-Breite führt jede Beschriftung zur Leistungsseite, der rote Kreis wird beim Laden einmal gezeichnet (nur ohne reduzierte Bewegung). Ohne Skript und auf dem Handy folgt die gleiche Auswahl als Liste direkt darunter. Dazu die Unfall-Checkliste, deren Haken im Browser bleiben.

## Verworfene Richtungen

| Richtung | Grund |
| --- | --- |
| „Prüfprotokoll“: schwarze Bänder, diagonale Schnitte, schräge Schmalschrift in Versalien, Prüfstempel | Sah aus wie jede Auto-Vorlage mit Schwarz und Rot. Die Diagonalen und der Stempel waren Dekor ohne Aussage. |
| Fahrzeugschein-Raster (Feldnummern wie in der Zulassungsbescheinigung) | Zu verspielt, die Feldnummern würden Zahlen ohne echte Reihenfolge einführen. |
| Plakatseite mit Vollflächen in Rot | Rot verliert seine Bedeutung, wenn es überall steht. |
| Telefonnummer als Kennzeichen | Gimmick, der von der Aufgabe (anrufen) ablenkt. |

## Farben

Ableitung: Das Logo ist Schwarz und Rot. Ein Sachverständiger arbeitet neutral, deshalb sind die Flächen neutral. Rot kommt aus dem Logo und bleibt für Befund und Alarm reserviert. Verteilung grob 70 / 25 / 5.

| Name | Wert | Rolle |
| --- | --- | --- |
| Papier | `#FFFFFF` | Grund der Seite |
| Grundierung | `#ECEDEF` | Bühne der Zeichnung, abgesetzte Abschnitte, Hinweisflächen |
| Tinte | `#101114` | Text, Linien, Zeichnung, dunkle Flächen |
| Befund-Rot | `#D71A21` | Schadenszone, Hauptknopf, Notruf-Fläche, kleine Marker |
| Rot, dunkel | `#B5141A` | Rot als Text auf hellem Grund, Hover des Knopfes |
| Grau, Text | `#494C53` | Einleitungen, Beschriftungen |

Der Dunkelmodus (Systemeinstellung des Besuchers) tauscht Grund und Tinte, Rot wird heller. Ein fester Dunkelmodus ohne Grund ist nicht eingebaut.

## Schriften

Eine Familie, lokal als woff2: **Epilogue** in 400, 600 und 800. Überschriften in Groß- und Kleinschreibung, 800, eng gesetzt (−0,035 bis −0,045 em). Fließtext 400, Beschriftungen und Knöpfe 600. Zahlen mit Tabellenziffern. Lange Fachwörter werden an Silbengrenzen getrennt (`soften()` in `build/build.py`).

Typo-Skala: Hero-Überschrift bis 90 px, Seitenüberschrift bis 78 px, Abschnittsüberschrift 28 bis 54 px, Zwischenüberschrift 21 bis 27 px, Einleitung 18 bis 21 px, Text 17 px, Beschriftung 13 bis 15 px.

## Layout

Zwölf Spalten bei 1240 px, Ränder 18 bis 44 px. Jeder Abschnitt hat eine andere Komposition als sein Nachbar:

```
Kopf        Überschrift groß links | Einleitung + Knöpfe rechts
Bühne       grauer Streifen über volle Breite: Fahrzeug von der Seite, 6 Beschriftungen mit Leitlinien
Leistungen  Tabelle: Art | Leistung | Beschreibung, dicke Linie oben, Hover tönt die Zeile
Ablauf      Maßkette: vier Stationen auf einer Linie, Nummer = echte Reihenfolge
Gründe      dunkle Fläche: Überschrift links (klebt), drei Begründungen rechts
Über mich   Porträt mit Maßstab am Rand | Datenblatt mit fünf Zeilen
Unfall      Liste der ersten Schritte | rote Notruf-Fläche mit 110 und 112
Ratgeber    Zeilen: Titel links, Kurztext rechts
Fragen      Überschrift links (klebt) | Fragen rechts
Gebiet      Ringschema 25 und 50 km | Ortsliste
Kontakt     dunkel, Telefonnummer in Schriftgröße bis 148 px, darunter Angaben und Wege
Fuß         Schriftfeld wie auf einer technischen Zeichnung, vier Felder
```

Unterseiten: Brotkrumen, Überschrift über die volle Breite (bis 78 px, höchstens zwei Zeilen), darunter Einleitung links und Verfasserzeile rechts, dicke Linie. Danach Text mit Zwischenüberschriften (dicke Linie darüber) und rechts der dunkle Kontaktkasten, am Ende ein dunkles Band.

Handy: Menü in einer oder zwei Zeilen unter dem Logo, alle Punkte sichtbar. Die Zeichnung wird größer gezogen und beschnitten, die Beschriftungen entfallen, darunter folgt die Leistungsliste. Aktionsleiste unten mit Anrufen, WhatsApp und Anfrage.

## Signatur

Die Schadenszeichnung: Pkw von der Seite mit zerknitterter Front (gestrichelt die unbeschädigte Kontur), roter Schraffur, mit rotem Stift eingekreist, und Bremsspur auf der Fahrbahn. Gezeichnet im Code (`build/artwork.py`), keine Bilddatei. Alles drumherum bleibt ruhig: Text, Linien, Tabellen.

Zweite, kleinere Handschrift: das Schriftfeld im Fuß und der Maßstab am Porträt, beide aus der technischen Zeichnung.

## Gestaltungssysteme

- Hero-Komposition: eigene, nahe an F (Überschrift mit Bild als Bühne darunter): große Überschrift, Zeichnung als Bühne über die volle Breite, Beleg („Wer zahlt?“) direkt darunter.
- Schatten: keine. Tiefe entsteht durch Flächen (Grundierung, Tinte).
- Radien: 0. Alle Ecken eckig, ohne Ausnahme.
- Linien: drei Stärken mit Bedeutung. 3 px für Abschnitts- und Tabellenköpfe, 1 px für Zeilentrenner innerhalb von Listen, 2 px für Zeichnung und Schriftfeld.
- Bildform: Porträt als Rechteck mit Maßstab. Es gibt nur ein echtes Foto.
- Belege im ersten Bildschirm: Kostenfrage („Wer zahlt?“), Rufnummer im Kopf, die sechs Gutachten als Beschriftungen.

## Haupt-Conversion

Anrufen (`tel:`), Nebenwege WhatsApp und Formular. Der Knopf „Jetzt anrufen“ ist der einzige rote Knopf im Kopfbereich. Rückmeldung nach dem Formular: eigene Seite `danke.html` mit Vorgangsnummer und, falls Fotos nicht angenommen wurden, Hinweis auf WhatsApp.

## Vertrauensbelege

Aus dem Auftrag und der alten Website: Kfz-Techniker-Meister, über 30 Jahre im Kraftfahrzeugwesen, 17 Jahre als Sachverständiger in Deutschlands größter Sachverständigenorganisation, Unabhängigkeit von Versicherungen und Werkstätten. Alles steht im Datenblatt der Über-mich-Fläche, keine erfundenen Zahlen, keine Siegel, keine Kundenstimmen.

## Bewegung

Eine einzige: der rote Kreis wird beim Laden in gut einer Sekunde gezeichnet. Er zeigt, wohin der Blick gehen soll. Mit reduzierter Bewegung steht er sofort. Das Plus bei den Fragen dreht sich, sonst gibt es nur Farbwechsel beim Darüberfahren (nur mit Maus). Kein Einblenden von Abschnitten, kein Zählen von Zahlen.

## Ausnahmen von der Verbotsliste

- Rot und Schwarz als Grundpalette: Es sind die Farben des Logos (Vorrang der Kunden-CI).
- Eine Rot-Fläche (Notruf) trägt weißen Text: Rot bedeutet hier Alarm, wie im Straßenverkehr.
- Die Überschrift der Startseite hat zwei Zeilen und kein hervorgehobenes Wort.

## Technik

Eine Stylesheet-Datei `website-fertig/assets/site.css`, alle Farben und Maße als Variablen am Anfang. Keine Verläufe, keine Schatten, keine Fremdschriften. Hover nur in `@media (hover: hover) and (pointer: fine)`. Zeichnungen aus `build/artwork.py` (Fahrzeug, Maßstab), das Ringschema des Einsatzgebiets aus `build/build.py`. Vorschaubild: `node build/make-og.js`.
