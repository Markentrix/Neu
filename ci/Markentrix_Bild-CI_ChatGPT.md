# Markentrix · Bild-CI für ChatGPT und andere Bildgeneratoren

Stand: CI 2026, Version 2.0. Grundlage ist das CI-Handbuch, Seiten 19 bis 21.

## So wird es benutzt

1. **Einmalig:** Die „Kurzfassung für die Einstellungen“ (Abschnitt 5) in die Projektanweisungen von ChatGPT einfügen.
2. **Je Bild:** Eine Vorlage aus Abschnitt 4 nehmen, das Motiv in den eckigen Klammern ersetzen, dann Stilblock (Abschnitt 2) und Ausschlussblock (Abschnitt 3) darunter einfügen.
3. **Danach:** Bild mit der Abnahmeliste (Abschnitt 6) prüfen. Logo, Text und Wachstumskurve nachträglich einsetzen.

## 1 · Drei feste Regeln

- **Das Logo wird nie von der KI erzeugt.** Es wird nachträglich aus der Logo-Datei eingesetzt. Ein Bild mit erfundenem oder verzerrtem Logo wird verworfen.
- **Text kommt nachträglich ins Bild,** in Canva oder im Layout, mit Space Grotesk und Inter. Die KI liefert das Bild mit Freifläche.
- **Die Wachstumskurve wird nie von der KI gezeichnet.** Sie kommt aus der Datei `assets/wachstumskurve.svg`.

## 2 · Stilblock (immer anhängen)

```
STIL (Markentrix): Helle, hochwertige, realistische Markenfotografie, wie von einem professionellen Fotografen aufgenommen. Natürliches, weiches Tageslicht von der Seite, keine harten Schatten. Helle, aufgeräumte Umgebung mit viel Weißraum: weiße Wände, helles Holz, heller Beton, Glas. Gesamtbild hell und luftig, leicht kühl-neutrale Farben, zurückhaltende Sättigung, kein Farbfilter.
Farbakzente sparsam und nur als echte Gegenstände oder Bildschirminhalte: Cyan #28C7F7 und Blau #1E9BFF, höchstens zwei Akzente im Bild, höchstens ein kleiner violetter Akzent #8B5CF6. Dunkle Elemente in tiefem Navy #0B1020 statt Schwarz.
Menschen: echte, natürlich wirkende Personen aus lokalen Betrieben in Norddeutschland, 25 bis 60 Jahre, echte Arbeitskleidung, natürliche Haut mit Poren, ungestellte Haltung, konzentriert bei der Arbeit oder freundlich im Gespräch, kein Dauerlächeln. Hände anatomisch korrekt.
Aufnahme: Augenhöhe, 35 bis 50 mm Brennweite, Blende f/2.8 bis f/4, scharfes Hauptmotiv, leicht unscharfer, ruhiger Hintergrund. Ein klares Hauptmotiv, mindestens ein Drittel des Bildes als ruhige, helle Freifläche für späteren Text.
Bildschirme im Bild zeigen eine schlichte, helle Oberfläche in Weiß mit einem cyanfarbenen Knopf, ohne lesbaren Text.
```

## 3 · Ausschlussblock (immer anhängen)

```
NICHT IM BILD: dunkle oder schwarze Hintergründe, Neonlicht, Glühen, Lichtreflexe, Hologramme, Roboter, Androiden, leuchtende Gehirne, Schaltkreis-Muster, Datenströme, futuristische Bedienoberflächen, Krypto-Optik, Comic-Stil, 3D-Cartoon-Figuren, Illustration, Regenbogenverläufe, übersättigte Farben, Orange-Türkis-Look, Stockfoto-Händeschütteln, Models im Anzug, glatte Kunsthaut, verzerrte Hände, Logos, Markennamen, das Markentrix-Logo, Wasserzeichen, Schrift oder Fantasietext im Bild.
```

## 4 · Vorlagen

Das Motiv in eckigen Klammern ersetzen. Darunter immer Stilblock und Ausschlussblock einfügen.

### A · Betrieb bei der Arbeit

```
Foto: [Elektriker, etwa 40, prüft mit einem Messgerät einen Sicherungskasten in einem hellen Hausflur]. Format [4:5 hoch]. Ruhige helle Freifläche [im oberen Drittel].
```

### B · Smartphone oder Laptop in der Hand

```
Foto: [Friseurin hält im Salon ein Smartphone], auf dem Display eine helle, schlichte Terminübersicht in Weiß mit einem cyanfarbenen Knopf, ohne lesbaren Text. Fokus auf Hand und Gerät. Format [1:1]. Freifläche [rechts].
```

### C · Ruhiger Hintergrund für Text

```
Foto: [heller Werkstatt-Arbeitstisch von oben, links unten etwas Werkzeug und ein cyanfarbener Zollstock], der Rest des Bildes ist eine leere, helle Fläche. Format [1:1]. Mindestens zwei Drittel Freifläche.
```

### D · Vorher und nachher

```
Foto: Zwei Smartphones nebeneinander auf einem hellen Holztisch. Links [eine veraltete, überladene Website in Grau- und Brauntönen], rechts [eine moderne, helle Website in Weiß mit cyanfarbenem Knopf], beide ohne lesbaren Text. Format [4:5 hoch]. Freifläche oben.
```

### Serien

Für zusammengehörige Bilder zuerst ein Bild freigeben, dann schreiben:

```
Gleicher Stil, gleiches Licht, gleiche Umgebung wie im letzten Bild. Neues Motiv: [...]
```

## 5 · Kurzfassung für die ChatGPT-Einstellungen

```
Alle Bilder im Markentrix-Stil: helle, realistische Markenfotografie, weiches Tageslicht, viel Weißraum, aufgeräumte Umgebung, leicht kühl-neutrale Farben. Akzente sparsam als echte Gegenstände in Cyan #28C7F7 und Blau #1E9BFF, Dunkles in Navy #0B1020. Echte, natürliche Menschen aus lokalen Betrieben, 35–50 mm, leichte Hintergrundunschärfe, ein Drittel helle Freifläche für Text. Niemals: dunkle Hintergründe, Neon, Glühen, Roboter, Hologramme, Comic, 3D-Figuren, Stockfoto-Klischees, Logos, Schrift oder Fantasietext im Bild. Das Markentrix-Logo nie erzeugen.
```

## 6 · Abnahme: sieben Prüfungen

| Nr. | Frage | Bestanden, wenn |
|---|---|---|
| 1 | Hell? | Kein dunkler Hintergrund, mindestens die Hälfte heller als Mittelgrau |
| 2 | Echt? | Hände, Gesichter, Werkzeug und Perspektive sind fehlerfrei |
| 3 | Ruhig? | Ein Hauptmotiv, aufgeräumter Hintergrund, Freifläche vorhanden |
| 4 | Farbtreu? | Höchstens zwei Akzente in Cyan oder Blue, kein Neon |
| 5 | Sauber? | Kein Logo, kein Fantasietext, keine Fremdmarke |
| 6 | Glaubwürdig? | Die Szene könnte so in einem Betrieb in Celle vorkommen |
| 7 | Ehrlich? | Das Bild gibt nicht vor, einen echten Kunden zu zeigen |

Fällt eine Prüfung durch, wird das Bild neu erzeugt.

## 7 · Formate

| Zweck | Erzeugen | Zuschneiden auf |
|---|---|---|
| Beitrag, Karussell | Quadrat 1:1 | 1080 × 1080 px |
| Beitrag hoch | Hochformat 2:3 | 1080 × 1350 px (4:5) |
| Story, Reel | Hochformat 2:3 | 1080 × 1920 px (9:16) |
| Website, Präsentation | Querformat 3:2 | nach Bedarf |

## 8 · Kennzeichnung

KI-Bilder erhalten auf der Website das kleine Abzeichen „KI-Symbolbild“. Sie zeigen nie einen angeblich echten Kunden.

## 9 · Grafiken mit Text

Social-Media-Grafiken mit Überschrift, Knopf und Logo entstehen nicht im Bildgenerator, sondern im Layout (Canva) nach Seite 23 des Handbuchs. Die KI liefert dafür höchstens das Foto oder den Hintergrund nach Vorlage C.

Farben für das Layout: Navy `#0B1020` (Überschrift), Ink `#2C3446` (Text), Cyan `#28C7F7` (Knopf, Marker), Soft White `#F8FAFC` (Grund). Schriften: Space Grotesk Bold für Überschriften, Inter für Text.
