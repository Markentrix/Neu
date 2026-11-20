# DESIGN.md · Waldtierheim Celle (Verein aktiver Tierfreunde e.V.)

Relaunch von tierfreunde-celle.de. Stand 20.11.2026. Dieses Dokument beschreibt den Endstand, nicht den Weg dorthin.

## Ziel
1. Tiere vermitteln und Emotionen erzeugen.
2. Spenden sammeln.

Haupt-Conversion: Kennenlern-Anfrage am Steckbrief (Formular, Portal `POST /api/anfrage`). Die Startseite führt mit „Tiere kennenlernen“ dorthin. Zweite Aktion überall erreichbar: „Spenden und helfen“ (Kopf), „Spenden“ (Handy-Leiste).

## Kernidee
Die Seite zeigt, wie lange jedes Tier schon wartet. Auf jedem Tierfoto steht die Zahl der Tage, seit denen der Steckbrief online ist. Die Zahl wird im Browser aus dem echten Datum gerechnet; ohne Skript steht das Datum im Steckbrief. Auf Startseite und Tierlisten steht ein Satz, der die Zahl erklärt.

Signatur: Wartetage als große Zahl (Bruce: über 1.600 Tage).

## Farben
| Name | Variable | Hex | Rolle |
|---|---|---|---|
| Weiß | `--grund` | #FFFFFF | Seitengrund |
| Hellgrün | `--flaeche` | #E6EFD6 | Flächen: Geschichte, Spenden, Fragen, Formular, Schilder |
| Waldgrün | `--wald` | #143A29 | Schrift, dunkle Knöpfe, Footer, Handy-Leiste |
| Blattgrün | `--blatt` | #8CC63F | Hauptknöpfe (mit waldgrüner Schrift) |
| Pfotengrün | `--pfote` | #BBD292 | nur Pfotenabdrücke |

Nebentext: #47604F auf hell, #C5D9C6 auf dunkel. Fehlerfarbe im Formular: #9C1C1C.
Kontraste: Waldgrün auf Weiß 12,6:1, auf Hellgrün rund 10:1, auf Blattgrün rund 6:1.
Regeln: Blattgrün nie als Schrift oder dünne Linie auf Weiß (zu schwach). Aktiver Menüpunkt und „geöffnet“-Punkt sind waldgrün. Verläufe nur als neutral dunkler Schleier unter Schrift auf Fotos.
Abweichung vom Logo: Das Logo ist nachtblau mit grünem „aktiver“. Die Website ist auf Wunsch grün. Mit dem Verein klären.

## Schriften (lokal, 3 Schnitte)
- Display: Bricolage Grotesque 800, für Überschriften, Namen und Wartetage.
- Text: Source Sans 3 400/700, Zahlen mit tabular-nums.

## Bausteine
- **Foto-Kachel** (`.kachel`): Bild füllt die Fläche, Name und Wartetage stehen auf dem Bild. Gleich auf Startseite (Mosaik, „Alle Hunde/Katzen“) und in allen Tierlisten.
- **Fotowand** (`.wand`): Quadrate mit Namen, ein großes Bild vorn. Startseite und Happy-End-Seite. Klein (`.wand-klein`) in den Archivlisten.
- **Bildbühne** (`.buehne`): vollflächiges Foto mit Schrift, nur im Hero.
- **Kopfbild** (`.seitenbild`): breites Foto unter der Seitenüberschrift (Spenden, Verein).
- **Zeilenliste** (`.zeile`): Datum, Titel, Anriss, kleines Bild (Aktuelles, Feste, Grüße).
- **Schild** (`.schild`): helle Karte „Das ist Cora“ im Hero.
- Knöpfe eckig. Keine Schatten, keine Rahmenlinien.

## Startseite (Reihenfolge)
Hero mit Cora → Tiere, die am längsten warten (Mosaik, Hunde/Katzen) → Ernie und Bert → Happy End (Fotowand) → Spenden → Besuch → fünf Fragen → Footer. 21 Fotos.
Alle zehn Fragen stehen mit FAQ-Markup auf der Kontaktseite.

## Funktionen
- **Merkliste:** Herz an jedem Tierfoto in den Listen und am Steckbrief. Gespeichert nur im Browser des Besuchers (localStorage), kein Konto, keine Übertragung. Seite `merkliste.html` (noindex) baut sich aus `tiere.json`.
- **Filter in der Tierliste:** nach Alter (aus dem Geburtsjahr im Steckbrief), bei Hunden zusätzlich nach Größe (aus der Größenangabe). Ohne Skript bleibt der Filter verborgen und alle Tiere sind sichtbar.
- **Steckbrief:** großes Foto, Infokarte mit Wartetagen und drei Aktionen (Kennenlernen, Pate werden, Merken), darunter Text und Fotogalerie mit Großansicht, Formular, drei weitere Tiere derselben Art.
- **Patenschaft am Tier:** Das Formular fragt „Worum geht es?“ (Kennenlernen oder Patenschaft) und sendet das als Feld `anliegen` an das Portal.
- Ereignisse für die Statistik: `anruf_klick`, `anfrage_gesendet`, `spende_klick`, `iban_kopiert`, `tier_gemerkt`.

## Zeichen (Kundenwunsch)
- Pfoten: Hundespur nach den Tieren, Katzenspur nach der Fotowand, Pfote als Symbol an den Reitern „Hunde“ und „Katzen“.
- Wellensittiche: einer auf dem Cora-Schild (Desktop), einer auf dem Namen im Footer, ein Paar auf einem Ast bei „Kurz gefragt“ und auf der 404-Seite.

## Bewegung
1. Seitenaufbau im Hero: Zeilen und Foto, einmalig.
2. Fotowand deckt sich beim Scrollen auf (nur CSS; ohne Unterstützung steht sie einfach da).
3. Seitenwechsel Liste → Steckbrief: Foto wandert an seinen Platz.
4. Sortieren der Tierliste.
5. Menü am Handy, Druck-Rückmeldung an Knöpfen.
Kein Zoom beim Überfahren. Reduzierte Bewegung schaltet alles ab.

## Ausnahmen von der VERBOTEN-Liste des Skills
- Deko-Formen (Pfoten, Sittiche): ausdrücklicher Kundenwunsch.
- FAQ auf der Startseite: Antworten für Suchmaschinen und KI-Suchen, alle aus der bisherigen Website.
- Wortmarke in Schrift statt Logo-Datei: das Original liegt nur als 392-px-GIF vor.

## Offen
- Rechtstexte sind Entwürfe. Vorstand im Impressum bestätigen.
- Größere Tierfotos (mindestens 1600 px). Nur Coras Foto trägt bisher einen vollflächigen Hero.
- Vorschaubild beim Teilen (og:image) fehlt, weil der Portal-Platzhalter dort nicht erlaubt ist.
