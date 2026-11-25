# DESIGN.md – PS Schneider, Sachverständiger für Fahrzeugtechnik, Celle

Diese Datei dokumentiert die Gestaltungsentscheidungen. Sie liegt neben dem Webroot `public/` und gehört nicht in den Upload.

## Kernidee

Eine Seite, die aussieht wie ein Gutachten: Schadenskizze, Maßlinie, Prüfstempel. Die Schrift steht schräg wie die Buchstaben im Logo, Flächen werden im selben Winkel diagonal geschnitten.

**Ideensatz:** Auf dieser Seite wird das **Logo des Betriebs (schräg gestelltes Schwarz-Rot) und die Schadenskizze eines Gutachtens** zu **Schrägwinkel, Parallelogramm-Schaltflächen und einer gezeichneten Fahrzeugskizze mit Nummernmarken**.

Austauschtest: Ein anderer Sachverständiger hätte weder dieses Logo noch diese Skizze mit Maßlinie und Schadenszone. Mit getauschtem Namen und Logo wäre die Seite für einen anderen Betrieb sichtbar falsch (Skizze, Stempel, Logo-Winkel).

**Signatur:** die rote Schrägfläche (Parallelogramm, 12 Grad wie die Schrift im Logo). Sie kehrt wieder in der Seitenkopf-Marke, im Porträtrahmen, auf Schaltflächen und Trennern. Alles andere bleibt ruhig.

**Lebendiges Element:** die Schadenskizze im dunklen Band „So läuft es ab“. Sie zeichnet sich beim Sichtbarwerden Linie für Linie (einmal, nur transform- und opacity-nahe Eigenschaften, bei „weniger Bewegung“ sofort fertig).

Verworfene Richtungen: (1) Foto-Vollbild mit riesigem Wort (es gibt nur ein Porträtfoto), (2) helle Handwerker-Seite mit Icon-Karten (Standard, austauschbar).

## Farben (Kunden-CI aus dem Logo)

| Rolle | Hex |
| --- | --- |
| Grund | `#FFFFFF` |
| Flächenwechsel | `#F1F1F2` |
| Tinte und dunkle Flächen | `#0D0E10` |
| Text gedämpft | `#40434A` |
| Akzent (Aktion, Signatur) | `#D71A21` (auf Dunkel `#EF3B42`) |
| Linie | `#DADADD` |

Verteilung etwa 60/30/10: Weiß, Schwarz, Rot. Im Dunkelmodus (nach Systemeinstellung) Grund `#121416`, Flächen `#191B1E`, tiefe Flächen `#050506`.

**Begründete Ausnahme von der VERBOTEN-Liste:** „Fast-Schwarz plus Zinnober“ steht auf der Liste. Hier ist es die echte CI: Das Logo ist schwarz und rot (`#D71A21`). Beige/Creme wurde dagegen entfernt, der Grund ist Reinweiß.

## Schriften (lokal, woff2, vier Schnitte)

- Barlow Condensed Kursiv 800: Überschriften H1/H2 (Großbuchstaben)
- Barlow Condensed Kursiv 700: H3, Schaltflächen, Navigation
- Barlow 400: Fließtext
- Barlow 600: Beschriftungen, Etiketten

Zwei Familien, vier Schnitte. Zahlen mit Tabellenziffern. Fließtext 16,5 bis 17 Pixel, Zeilenhöhe 1,6, Überschrift zu Text mindestens 3:1.

## Layout

Hero (Komposition B): links Text mit zwei Zeilen Headline, Stützsatz und Aktion, rechts das Porträt im Parallelogramm mit rotem Block dahinter. Darunter zwei Belege des Kunden (30 und 17 Jahre).

Danach wechseln die Abschnitte: Leistungsverzeichnis als Zeilen (Überschrift links, Liste rechts), dunkles Band mit Fahrbahnmarkierung und Skizze, Gründe als drei gleich schwere Blöcke, dunkler Abschnitt mit Prüfstempel, helle Schritte mit Notruf-Karte, Ratgeber, Fragen, Einsatzgebiet, Kontakt mit großer Telefonnummer.

Unterseiten: dunkler Kopf mit roter Schrägfläche, helle Textfläche mit Seitenleiste.

## Gestaltungssysteme

- **Ebenen:** alle Flächen flach (Ebene 0). Es gibt genau einen Schattenwert: den harten Fokusschatten an Formularfeldern (`--shadow-1`).
- **Radien:** 0 für alles, 50 % nur für die runde Nummernmarke in der Schadenskizze und in Aufzählungen mit echter Reihenfolge.
- **Bildform:** Parallelogramm (Porträt, Schaltflächen, Chips, Stempel-Block). Auf allen Seiten gleich.
- **Belege:** höchstens zwei im ersten Bildschirm, wie geliefert: „über 30 Jahre Erfahrung“ und „17 Jahre Sachverständiger bei Europas größter Sachverständigenorganisation“ (Quelle: bisherige Website und Angaben des Kunden). Keine Zahlen ohne Quelle.
- **Etiketten über Überschriften:** nur dort, wo sie etwas Eigenes sagen (Leistungsbereich der Leistungsseiten, Einleitungsfrage im Hero). Keine Nummern ohne echte Reihenfolge; Nummern stehen nur beim Ablauf, bei den ersten Schritten und in der Checkliste.
- **Rundes Aktionselement:** keines.
- **Pfeile:** keine Pfeile an Links.

## Haupt-Conversion

Anruf (Telefon `0172 517 81 50`), danach WhatsApp und Anfrageformular mit Schadenfotos. Rückmeldung nach dem Senden: Referenznummer und Bestätigungsmail.

## Bewegung

Ein orchestrierter Moment (die Skizze zeichnet sich). Sonst nur Rückmeldung: Farbe und Fläche bei Hover (nur mit Maus), Druckrückmeldung an Schaltflächen. Alle Übergänge kürzer als 300 ms, nie `transition: all`, bei „weniger Bewegung“ keine Animation.

## Offene Punkte

Siehe README, Abschnitt „Vor dem Livegang ausfüllen und prüfen“, und den Bericht zum Skill-Durchlauf.
