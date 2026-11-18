# DESIGN.md – Burnout Celler-Kartbahn (Relaunch, Skill website-mit-portal V4.2)

## Kernidee
Die Seite ist wie die Bahn gebaut: eine Zeitnahme-Tafel über Asphalt. Alles, was Zahlen trägt (Preise, Zeiten, Streckendaten, Startzeiten), steht in Tabellenziffern wie auf dem Zeitenmonitor; jede Bildkante ist „gebankt“ wie die Steilkurve in sechs Metern Höhe.

**Ideensatz:** Auf dieser Seite wird die Steilkurve der 2. Ebene (6 m Höhe, 2023, einzigartig in Norddeutschland) zur Bildform: Jedes Foto und jede Fläche hat eine um ca. 6° geneigte, abgeschnittene Kante (Banking), und die Zeitnahme der Bahn (Ampelstart, Rundenzeit, Startliste) ordnet Inhalte und Buchung.

**Austauschtest:** Mit anderem Namen und Logo funktioniert die Seite nicht, weil Banking-Kante, Höhenmarke „+6 m“, die Startliste mit echten Preisen und der Ampelstart in der Buchung nur zu dieser Bahn passen.

**Signatur:** Die Banking-Kante (clip-path mit geneigter Schnittlinie) an Hero, Bildern und dem Preis-Check. Alles andere ist ruhig: keine Rahmen, keine Icons in Kacheln, keine Dekoanimation.

**Lebendige Sachen:** 1) Öffnungsstatus live im Hero („Heute ab 15 Uhr geöffnet“ / „Jetzt geöffnet, Open End“), aus den echten Öffnungszeiten berechnet, ohne Skript steht der statische Text. 2) Preis-Check mit den echten Preisen, Übergabe an die Buchung. 3) Buchung mit Startampel: rot → rot → rot → grün, aus /api/verfuegbarkeit und /api/slots.

**Verworfene Richtungen:**
- „Zeitungs-Rennbericht“ (Broadsheet, Serif, Haarlinien): verboten, und es passt nicht zu einer Indoor-Halle mit roten Stahlträgern.
- „Streckenplan als Navigation“: es liegt kein Streckenplan vor; alles Erfundene wäre falsch. Als Idee für später notiert (OFFEN).
- „Helle Seite mit viel Weiß“: die echten Fotos sind dunkle Hallenbilder mit Rot; auf Weiß stehen sie schlecht.

## Farben (Kunden-CI aus Logo, Karts, Halle)
Grund dunkel ist durch die CI begründet (Logo auf Schwarz, schwarze Halle, rote Stahlträger, rote Karts) – Ausnahme von „Dauer-Dark-Mode“.
- `--asphalt` #0C0C0E – Grund (60 %)
- `--asphalt-2` #16161A – Fläche, Karten ohne Rahmen (Tonstufe)
- `--asphalt-3` #202026 – zweite Tonstufe, Eingabefelder, Zeilen
- `--kreide` #F6F5F2 – Tinte (Überschriften, Fließtext in voller Tinte) (30 %)
- `--kreide-2` #D4D2CC – Nebennotizen (Kontrast 10,7:1 auf Grund)
- `--signal` #E10600 – Akzent, nur Hauptaktion und Höhenmarke (10 %)
- `--signal-hell` #FF4A43 – Linktext auf Dunkel (Kontrast 5,4:1 auf Grund)
- `--gruen` #2FC06A – nur Ampel „grün“ und Erfolg (Zustand, kein Akzent)
Fließtext nie grau: Fließtext in `--kreide`, nur Fußnoten in `--kreide-2`.

## Schriften (zwei Familien, drei Schnitte, lokal, OFL)
- Display: Barlow Condensed 800 (H1, H2, H3, große Zahlen; der Schnitt deckt 700–800 ab, damit kein zweiter Download und kein Layout-Sprung entsteht). Laufweite -0,02em, Zeilenhöhe 0,92–1,0. Sparsam.
- Text: Barlow 400 (Fließtext 17–18 px, Zeilenhöhe 1,55), 600 (Labels, Buttons, Tabellenköpfe).
- Zahlen: `font-variant-numeric: tabular-nums` überall, wo Zahlen untereinander stehen.
- Typo-Skala (Desktop): 88 / 48 / 28 / 18 / 14 px. Headline zu Fließtext 4,9×.

## Layout
Hero-Komposition **E** (Dunkles Vollbild, Text links, Vorschaukarte rechts, Unterkante als Leiste). Grund: dunkle Hallenfotos mit Rennlinie, Hauptaktion muss oben links stehen, die Vorschaukarte zeigt die 2. Ebene als nächstes Thema. Gegenkandidat A (Wort hinter Motiv) verworfen: kein Foto mit freier Silhouette in ausreichender Auflösung.

```
Desktop                                      Handy
┌──────────────────────────────────────────┐ ┌──────────────┐
│ BURNOUT   Preise Kinder Firmen … [Buchen]│ │ BURNOUT   ≡  │
│                                          │ │ (Foto, 62svh)│
│ Celle · heute ab 15 Uhr geöffnet (live)  │ │ Etikett      │
│ 600 METER                                │ │ 600 METER    │
│ VOLLGAS IN CELLE                         │ │ VOLLGAS …    │
│ Stützsatz …                  ┌─────────┐ │ │ Stützsatz    │
│ [Fahrten reservieren]        │Vorschau │ │ │ [Buchen]     │
│ Preise ansehen               │2. Ebene │ │ │ Belege …     │
├──────────────────────────────┴─────────┤ │ └──────────────┘
│ seit 2009 · Waldweg 100     f  WhatsApp │ │ (Aktionsleiste)
└──────────────────────────────────────────┘
```
Abschnittsfolge Start: Hero (E) → Startliste der Angebote (Tabelle, kein Kartenraster) → Vollbreite-Moment „2. Ebene“ mit Höhenmarke → Preise kurz + Öffnungszeiten als Zeitentafel → Aktuell (eine Fläche in Signalrot) → Bistro/Clubraum (Split) → Bewertungen (Baustein) → Anfahrt (Split mit Karte) → Footer als gestalteter Abschluss (Wortmarke groß).
Jede Sektion hat eine andere Komposition als ihre Nachbarn. Außenränder gleich, Abschnittsabstand 120–160 px Desktop.

## Gestaltungssysteme
- Ebenen: Ebene 0 Fläche ohne Schatten; Ebene 1 `--shadow-1` nur für die Vorschaukarte im Hero und den Preis-Check-Ergebnisblock; Ebene 2 `--shadow-2` nur für Mobilmenü. Schatten aus der Tinte getönt, zweilagig.
- Radien: `--r-s` 2px (Etiketten, Eingaben), `--r-m` 6px (Karten, Ergebnisblock), `--r-l` 10px (Bilder). Voll runde Elemente: keine außer Ampel-Lichtern.
- Buttons: eckig (`--r-s`), eine Füllfarbe (Signal) für die Hauptaktion, Zweitaktion als Textlink mit Unterstrich. Druck: `:active{transform:scale(.97)}`.
- Bildform: Banking-Kante – `clip-path: polygon(0 6%, 100% 0, 100% 100%, 0 100%)`, auf allen Seiten gleich.
- Belege im ersten Bildschirm (Quelle: alte Website, Impressum): „Familienbetrieb seit 2009“, „ca. 600 m Strecke“, „Steilkurve in 6 m Höhe“.
- Etikett über der Headline nur mit Information: Ort und Öffnungsstatus.

## Haupt-Conversion
Startseite: „Fahrten reservieren“ (buchen.html). Preise: Preis-Check → „Diese Auswahl reservieren“. Kinder: „Kidsparty buchen“. Firmen: „Event anfragen“. Rückmeldung: danke.html mit Vorgangsnummer, Ampel wird grün. Nebenaktionen (Anruf, WhatsApp) in der Handy-Leiste.

## Bewegung (ein Moment + Rückmeldung)
- Der eine Moment: Hero-Aufbau beim ersten Laden (Headline-Zeilen und Vorschaukarte, 320 ms, ease-out, Staffel 60 ms).
- Rückmeldung: Buttons `:active` 120 ms; Buchungsschritte und neu geladene Startzeiten blenden 200 ms ein; Ampel-Licht wechselt 250 ms; FAQ öffnet 250 ms; Seitenwechsel 200 ms (View Transitions, nur wo unterstützt).
- Gestrichen: Laufband, hochzählende Zahlen, Sektions-Reveal, Lesefortschritt, Lichtkante, Ken-Burns, Mauslicht, Header-Schrumpfen.
- Hover nur in `@media (hover:hover) and (pointer:fine)`, nur Farbe, 150 ms. reduced-motion: alle Bewegungen aus.

## Ausnahmen von der VERBOTEN-Liste
- Dunkler Grund: Kunden-CI (Logo, Halle, Karts).
- Ein Etikett über der Hero-Headline: trägt Ort und Live-Öffnungsstatus.
- „Statistik“-ähnliche Streckendaten: echte Werte aus der alten Website (600 m, 6 m, 9 PS, 13 Kinderkarts), nicht hochgezählt, als Datenblatt statt Leiste.
