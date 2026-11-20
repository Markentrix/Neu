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
| Ofenruß | `#1a1612` | Text, Linien, dunkler Vollbreite-Block (30 %) |
| Tomate | `#b3202c` | **Hauptfarbe, einzige Farbe für Handlung:** Knöpfe, Reservierungsband, Fehlertexte, Fokusrahmen |
| Zypresse | `#1d5a38` | **nur Zustand und Kennzeichnung:** "geöffnet", vegetarisch/vegan, Häkchen, ein Drittel des Trikolore-Streifens |
| Butter | `#f0d28a` | **nur der Preisaufkleber im Hero** |
| Zettelgrau | `#5b544b` | Fließtext zweiter Ordnung |
| Hilfsflächen | `#f3ecdd`, `#e4dccb`, `#cfc6b3` | Hover, feine Linien, Rahmen von Fotos |

Gegenüber der ersten Runde bewusst gedämpft: Das Rot ist von Signalrot zu einem tieferen Pomodoro-Ton gegangen, das Grün von Flaggengrün zu Zypresse. Es bleibt Italien (Grün, Weiß, Rot), wirkt aber nach Trattoria, nicht nach Fahne.

Kontraste (WCAG): Ruß auf Papier 17,7:1, Zettelgrau auf Papier 7,3:1, Weiß auf Tomate 6,7:1, Tomate auf Papier 6,5:1, Zypresse auf Papier 8,0:1, Weiß auf Ruß 18,0:1, Ruß auf Butter 12,2:1.

Regeln: Eine Hauptfarbe (Rot) mit klarer Aufgabe. Rot und Grün haben ähnliche Helligkeit, deshalb steht jeder Zustand zusätzlich als Text. Keine losen Hex-Werte im CSS: jede Farbe steht einmal in `:root`.

## Schriften (lokal, woff2)
- Display: **Bodoni Moda** (variabel, Gewicht 500 bis 600). Giambattista Bodoni kam aus Parma; die Antiqua mit feinen Haarlinien gibt der Seite Ruhe und Herkunft. Nur für Schlagzeile, Kategorietitel, Abschnittsüberschriften und Logo, nie für Fließtext oder Kleingedrucktes. **Lesbarkeit:** Die optische Größe ist fest auf `opsz 14` gesetzt und das Gewicht auf 600. Die automatische Einstellung macht bei großen Größen die Haarlinien so dünn, dass sich Buchstaben am Handy auflösen.
- Text: **Instrument Sans** (400 bis 600), Zeilenlänge 55 bis 70 Zeichen.
- Skala (Mobil / Desktop): Hero 2,3 / 3,9 rem, Abschnittstitel 1,9 / 2,8 rem, Gericht 1,0 / 1,08 rem, Beschreibung 0,88 / 0,92 rem, Beschriftungen 0,75 rem.
- Die Schlagzeile ist einfarbig, ohne einzelnes hervorgehobenes Wort (Vorgabe der Verboten-Liste).

## Layout-Konzept
Reihenfolge nach den Fragen eines Gastes: Was gibt es, kann ich reservieren, was kostet es, wo ist es.

```
+--------------------------------------------------+
| Pizzeria Molise   Karte  Mitnehmen  Anfahrt  [Tisch reservieren]
+--------------------------------------------------+
| Pizza, Pasta und                    +----------+  |  Hero: Schlagzeile in Bodoni,
| Flammkuchen in der                  |  Abzug   |  |  rechts das Foto als Abzug
| Celler Altstadt                     +----(5,50)+  |  mit Preisaufkleber
| Lead-Satz.   o Jetzt geöffnet bis 20 Uhr          |
+--------------------------------------------------+
| Tisch reservieren   [Tag] [Gäste]   [Weiter]      |  schlanke Leiste, danach Zeit-Chips
+--------------------------------------------------+
| Pizza   Pasta   Flammkuchen   Salate   Antipasti  |  haftende Textleiste, aktive Kategorie unterstrichen
| Anzeigen: [Alle] [Vegetarisch] [Vegan]            |
| ===============================================  |  doppelte Linie je Kategorie
| Pizza            | Margherita ........... 5,50    |
| [Foto, Rahmen]   | Funghi ............... 6,50    |
| ###### DUNKEL, ZARTER TERRAZZO, VOLLE BREITE ###### |  Pizza zum Mitnehmen + Zeichnung
| Anfahrt | Öffnungszeiten | Gut zu wissen (FAQ)    |
+--------------------------------------------------+
```

Rhythmus: Hero mit viel Luft, Reservierung als schmale Leiste, die Karte lang und ruhig mit Führungspunkten, ein dunkler Vollbreite-Moment, Fuß luftig.

## Signatur (genau eine)
Der **Foto-Abzug**: Das Hero-Foto liegt leicht schräg (1,2 Grad) mit weißem Passepartout und feiner Linie, ein runder Preisaufkleber nennt die Margherita. Kategoriebilder tragen denselben Rahmen, aber gerade und flach, damit die Signatur einmalig bleibt.

## Linien, Schatten, Radius
- Linien sind 1 px (Ruß für Bedienelemente, helles Beige für Trennlinien). Kategorien trennt eine doppelte Haarlinie.
- Schatten gibt es nur für den Foto-Abzug (weich, tief, ein Mal). Knöpfe, Karten, Chips und Rahmen sind flach.
- Radius: 2 px für Knöpfe, Chips und Felder, 4 px für die Reservierungskarte, Kreis nur für den Aufkleber.

## Zeichnungen
Straßenfenster und Gastraum sind einfarbige Linienzeichnungen (Quellen: `layouts/restaurant/art/*.svg`) mit Farbe nur an Markise, Lampen und Tischdecken. Sie ersetzen die frühere flache Illustration und werden durch echte Fotos abgelöst. Kategorien-Fotos sind KI-Platzhalter (siehe OFFEN).

## Terrazzo
Im dunklen Mitnehmen-Block liegen feine Terrazzo-Punkte (Tomate, Zypresse, Papier, geringe Deckkraft), nur oben und unten sichtbar, in der Textzone ausgeblendet. Reines CSS, kein Bild.

## Bewegung
Ein ruhiger Einstieg beim Laden (Schlagzeile, Lead, Status steigen nacheinander ein, Abzug landet, Aufkleber blendet ein), Rückmeldung bei Aktionen (Reservierung klappt aus, Häkchen), Einblenden der Kategorien beim Scrollen mit Sicherung (nach 4 s alles sichtbar). Kein Aufpoppen, kein Federn. `prefers-reduced-motion` schaltet alles ab.

## Prüfung gegen die Verboten-Liste
| Muster | Befund | Entscheidung |
|---|---|---|
| Pill-Badge über der H1 | Der Status war früher eine Pille über der Schlagzeile | Entfernt. Der Status ist jetzt eine einfache Textzeile mit Punkt unter dem Lead und zeigt einen echten Zustand (Uhrzeit, Ruhetag). |
| Einzelnes farbiges Wort in der Headline | "Pizza" war rot | Entfernt, Schlagzeile einfarbig. |
| ALL-CAPS-Label über Überschriften | Frühere Plakatschrift in Großbuchstaben | Entfernt. Großbuchstaben nur noch bei kleinen Beschriftungen (Feldnamen, Kennzeichen, "Anzeigen") mit 0,75 rem. |
| Dreier-Slogans, "Mehr erfahren" | Standen früher im Text | Entfernt. Knöpfe nennen die Handlung. |
| Schatten und Rahmen überall | Harte Versatzschatten, 2-px-Rahmen | Entfernt. 1-px-Linien, ein weicher Schatten nur am Foto-Abzug. |
| Meta-Zeile "A · B · C" | Fußzeile | Ersetzt durch Zeilen. |
| Zentrierter Hero, Glow, Verläufe, Glas | Nicht vorhanden | Asymmetrischer Hero, keine Effekte. |
| Standard-Reihenfolge Hero, Logos, Features … | Nicht vorhanden | Abschnitte nach Gästefragen. |
| Gleiches Fade-up überall, Bounce, `transition: all` | Nicht vorhanden | Ruhiger Einstieg, Einblenden mit Sicherung, kein Federn. |
| KI-Fotos | Speisefotos sind KI-generiert (keine Personen) | Platzhalter, unter OFFEN gemeldet. |
| Austauschtest | Name gegen Pizzeria in anderer Stadt getauscht | Passt nur mit Piltzergasse, Straßenfenster und italienischer Trikolore. Echte Fotos machen es eindeutiger. |
