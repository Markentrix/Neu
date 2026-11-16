# DESIGN.md · Waldtierheim Celle (Verein aktiver Tierfreunde e.V.)

Relaunch von tierfreunde-celle.de. Flächen-Modus: Startseite und Tierseiten "Persuade", Formular "Operate", Satzung/Rechtstexte "Read".

## Briefing
- Hauptziel: Tiere aus dem Waldtierheim vermitteln. Nebenziele: Besuch in den Öffnungszeiten, Spenden, Paten, Mitglieder, Gassi-Geher.
- Zielgruppe: Menschen in Celle und Umgebung, die einen Hund oder eine Katze aufnehmen wollen; Unterstützer.
- Haupt-Conversion: Kennenlern-Anfrage zu einem bestimmten Tier (Formular am Steckbrief). Startseite führt mit einem Button dorthin ("Tiere kennenlernen"). Anruf ist am Handy immer erreichbar.
- Rückmeldung nach der Aktion: Weiterleitung auf danke.html mit Vorgangsnummer.
- Einwände: "Ist das Tier noch da?", "Wann darf ich kommen?", "Passt das Tier zu mir?" Antwort: Steckbrief mit Datum, Öffnungszeiten live, ehrliche Beschreibung im Wortlaut des Tierheims.
- Vertrauensbelege (alle von der bisherigen Website): Gründung 23.01.1992, Waldtierheim seit 2003, Eintrag Amtsgericht Celle, Mitglied im Verband Niedersächsischer Tierschutzvereine, 380 dokumentierte Vermittlungen im Archiv, 68 Grüße vom neuen Zuhause (Originalbriefe).

## Inventar (nur dieser Betrieb)
1. Ein Tierheim im Wald: 9 Hektar Waldgrundstück am Rand von Altencelle.
2. Adresse "Im Sande 3": Sandboden und Kiefern auf jedem Foto.
3. Zufahrt Richtung Osterloh.
4. Zwei Öffnungsfenster am Tag, nachmittags nur Mo, Mi, Fr, So.
5. Gründung 1992 als Katzen-Kastrationsinitiative, zehn "Nomadenjahre" ohne Heim.
6. Die "Wilden": scheue Katzen, für die Höfe gesucht werden.
7. Archiv "Koffer gepackt und ausgezogen" und die "Dosenöffner".
8. Tiere mit Geschichte: Ernie und Bert (Doggen-Brüder), Cora (vier Jahre Tierheim in Rumänien), Bruce (im Steckbrief seit März 2022).
9. Logo: Nachtblau mit grünem, umkreistem "aktiver".
10. Mitgliedschaft ab 20 € im Jahr, Patenschaftsvertrag als PDF, Gassi-Geher melden sich vor Ort.
11. Tag der offenen Tür jedes Jahr im September; Hochwasser-Sicherung mit Sandsäcken Ende 2023.

## Richtungen
- A "Zwingerschild im Sand" (gewählt): Jedes Tier trägt sein Schild wie am Zwinger: Name, Rasse, Geburtsjahr und die Zahl der Tage, seit denen es ein Zuhause sucht. Farben vom Gelände.
- B "Koffer gepackt" (verworfen): Reiseanhänger-Motiv vom Happy End her gedacht. Niedlich, stellt aber die schon vermittelten Tiere vor die wartenden.
- C "Vereinsblatt" (verworfen): Zeitungsoptik. Passt nicht zum Inhalt und wäre ein Kostüm.

## Kernidee
Die Seite zeigt, wie lange jedes Tier schon wartet.

Ideensatz: Auf dieser Seite wird das Zwingerschild aus dem Waldtierheim Im Sande zur Karte jedes Tieres, und das Datum des Steckbriefs wird zur groß gesetzten Zahl der Wartetage.

Austauschtest: Das Datum je Steckbrief, die Sand- und Kiefernfarben, die zwei Öffnungsfenster und die Namen sind nur hier richtig. Ein anderes Tierheim müsste Daten, Ort und Palette neu liefern.

Signatur: die Wartetage als große Zahl auf dem Schild (z. B. Bruce). Alles andere bleibt ruhig.

Live-Element: (1) Wartetage werden im Browser aus dem echten Steckbrief-Datum gerechnet, ohne Skript steht das Datum da. (2) Wochenplan der Öffnungszeiten mit Markierung "jetzt geöffnet / öffnet wieder um". Ohne Skript steht der Plan als Tabelle da.

## Farben (60/30/10)
Auf Kundenwunsch reduziert (16.11.2026): drei Farbtöne, alles andere sind Tonstufen davon.
| Name | Hex | Rolle |
|---|---|---|
| Sand | #EADFC8 | Grund (60) |
| Heller Sand | #F7F1E2 | Schilder, Flächen, Formular |
| Dunkler Sand | #CFBD96 | nur Pfotenabdrücke im Sand |
| Nachtblau | #14104F | Tinte, dunkle Flächen Besuch und Footer (30, aus dem Logo) |
| Maigrün | #9BD43A | Akzent: nur Aktion und Sittich (10, aus dem Logo) |

Nebentext: #4B4878 (aufgehelltes Nachtblau). Kiefergrün, Rinde und die grüne Hilfe-Fläche sind entfallen. Keine Verläufe.

## Zeichen (Kundenwunsch)
- Hundepfote (mit Krallen) und Katzenpfote (rund, ohne Krallen) als Vektoren in `zeichen.svg`: Spur im Hero, Katzenspur im Happy End, Symbol an den Reitern Hunde/Katzen. Die Abdrücke stehen im Ton "Dunkler Sand": Pfoten im Sand, passend zur Adresse Im Sande.
- Wellensittich als Vektor in Nachtblau, Maigrün und hellem Sand: einer sitzt auf dem Hero-Schild, einer auf dem Namen im Footer, ein Paar auf einem Ast bei "Kurz gefragt".
- Ausnahme von der VERBOTEN-Liste (Deko-Formen): ausdrücklich vom Kunden gewünscht.

## Schriften (lokal, 3 Schnitte)
- Display: Bricolage Grotesque 800. Wirkt wie ein gemaltes Schild, nur für Überschriften und die Wartetage.
- Text: Source Sans 3 400/700. Ruhig und gut lesbar für eine gemischte Altersgruppe. Zahlen mit tabular-nums. (Atkinson Hyperlegible verworfen: die durchgestrichene Null wirkt in Daten und Telefonnummern technisch.)
- Skala: 15 / 19 / 24 / clamp(32–60) / Hero bis 180 px.

## Layout
```
Desktop                                   Handy
+--------------------------------------+  +----------------+
| Wortmarke        Tiere Besuch Hilfe  |  | Wortmarke  Menü|
| WALDTIERHEIM CELLE                   |  | WALDTIERHEIM   |
| ZUHAUSE GESUCHT          [ Foto    ] |  | CELLE ...      |
| Stützsatz                [ Schild  ] |  | Stützsatz      |
| [Tiere kennenlernen] Tel [ 43 Tage ] |  | [Button]       |
+--------------------------------------+  | [Foto+Schild]  |
| Wer gerade wartet: großes Schild +   |  | ...            |
| kleinere Schilder                    |  +----------------+
| KIEFER: Wochenplan live | Anfahrt    |  | Anrufen | Tiere|
| Happy End: Zahl + Originalbrief      |  +----------------+
| MAIGRÜN: vier Wege zu helfen (Zeilen)|
| Verein 1992 → 2003 → heute           |
| Aktuelles (Zeilen) · Kurz gefragt    |
| NACHTBLAU: Name groß, Zeiten, Pflicht|
+--------------------------------------+
```
Buttons eckig, eine Füllfarbe (Maigrün, Schrift Nachtblau). Keine Schatten, keine Rahmenlinien: Trennung über Tonstufen und Abstand.

## Bewegung (fünf Stellen)
1. Seitenaufbau im Hero (einziger orchestrierter Moment): Zeilen und Foto decken sich per clip-path auf, 60 ms Staffel. Zweck: Erstbesuch.
2. Seitenwechsel Liste → Steckbrief: Foto wandert per View Transition an seinen Platz. Zweck: Raumbezug.
3. Sortierung der Tierliste: Karten ordnen sich per View Transition um. Zweck: Zustand erklären.
4. Menü am Handy: Schublade, 240 ms. Zweck: harter Wechsel.
5. Druck-Rückmeldung an Buttons (scale .97) und Sendezustand im Formular.
Alles nur transform/opacity/clip-path, reduced motion schaltet Bewegung ab.

## Ausnahmen von der VERBOTEN-Liste
- "Kurz gefragt" (FAQ) auf der Startseite: enthält die Antworten, nach denen Menschen und KI-Suchen fragen (Zeiten, Ablauf, Kosten). Jede Antwort stammt aus der bisherigen Website; dient GEO (FAQPage-Markup).
- Eine einzelne große Zahl im Happy-End-Abschnitt (380): echte Anzahl der archivierten Vermittlungs-Steckbriefe, keine gerundete Statistik-Leiste.
- Logo: Die Wortmarke ist in Schrift nachgebaut (grünes "aktiver" wie im Logo), weil das Original nur als 392-px-GIF vorliegt.

## Überarbeitung 16.11.2026: bildgeführte Startseite (Kundenwunsch, Vorbild Linneweh-Entwurf)
- Hero: vollflächiges Foto von Hündin Cora (einziges Tierfoto in 2048 px), gespiegelt, damit links Platz für die Überschrift bleibt. Nachtblauer Scrim, Schild "Das ist Cora" mit Wartetagen unten rechts.
- Laufband mit den Namen der wartenden Tiere und Pfoten (Ausnahme von "Marquee als Deko": echte Namen, Kundenwunsch).
- "Diese Tiere warten am längsten" als Foto-Mosaik mit Name und Wartetagen auf dem Bild.
- Fotostreifen mit vermittelten Tieren im Happy-End-Abschnitt.
- Fotoband über "Vier Wege, wie du hilfst": Freiwillige beim Hochwasser-Einsatz 2023. Vereinsabschnitt mit Foto vom Tag der offenen Tür 2024.
- Bewegung zusätzlich: Bilder decken sich beim Scrollen auf und Fotobänder gleiten leicht (nur CSS, scroll-gesteuert; ohne Unterstützung oder bei reduzierter Bewegung stehen die Bilder einfach da). Leichter Zoom am Mosaik-Hover.
- Performance-Hinweis: das Helfer-Foto ist als 1920-px-Fassung 435 KB groß (über dem 150-KB-Ziel), lädt aber erst beim Scrollen.

## Überarbeitung 16.11.2026: weißer Grund (Kundenwunsch)
- Grund ist jetzt Weiß (#FFFFFF). Heller Sand (#F4EFE3) bleibt als Fläche für Schilder, Formular und Geschichte, Dunkler Sand (#D8CBA9) nur für Pfotenabdrücke. Nachtblau und Maigrün unverändert.
- Grund für den Wechsel: Fotos wirken klarer, die Seite insgesamt ruhiger.

## Überarbeitung 16.11.2026: kürzer und weniger Blau (Kundenwunsch)
- Nachtblau nur noch für Schrift, Knöpfe, Footer und die Handy-Leiste. Besuch-Abschnitt, Spendenkasten und Laufband sind nicht mehr blau; das Laufband entfällt. Scrims auf Fotos sind neutral dunkel statt blau.
- Startseite: Hero, Tiere (am Handy drei Kacheln), Ernie und Bert (ein Foto, ein Zitat), Happy End (Zahl und Fotostreifen), Spenden (Text, Kasten, drei Links), Besuch (drei Zeilen), fünf Fragen. Alle zehn Fragen stehen mit FAQ-Markup auf der Kontaktseite.
- Länge am Handy rund 5.900 px (vorher 9.100), am Desktop rund 5.900 px (vorher 8.300).
