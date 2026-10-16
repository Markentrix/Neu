# ElbDetail Foto- und Video-Shotlist

Briefing für Fotoshooting und Videodreh. Stand: 16.10.2026 (Keramikversiegelung und Lederreparatur ergänzt).

**Platzhalter:** Alles in `[PLATZHALTER: …]` muss der Betrieb vor dem Shooting entscheiden.

Bildstil, Farben und Logo-Regeln: siehe `docs/markenleitfaden.md`, Abschnitt 8.

---

## 1. Eckdaten

| Punkt | Angabe |
|---|---|
| Ort | Lachtehäuser Straße 1, 29223 Celle |
| Datum, Uhrzeit | `[PLATZHALTER: Shooting-Tag(e), Beginn]` |
| Fotograf / Videograf | `[PLATZHALTER: Name, Kontakt]` |
| Fahrzeuge | `[PLATZHALTER: Möglichst je ein Fahrzeug Kompakt, Limousine/Kombi und SUV/Van. Eines mit sichtbaren Swirls im Lack, eines mit verschmutztem Innenraum, gern mit Hundehaaren. Ein Fahrzeug, das eine Keramikversiegelung bekommt (dunkler Lack zeigt Glanz und Abperleffekt am besten). Ein Ledersitz oder Lenkrad mit Abrieb für die Colourlock-Reparatur. Schriftliche Einwilligung des Halters.]` |
| Arbeitsbereich | `[PLATZHALTER: Halle oder überdachter Platz mit konstantem Licht vorhanden? Außenfläche für Tageslicht-Aufnahmen?]` |
| Ansprechpartner vor Ort | René (Inhaber) `[PLATZHALTER: oder Vertretung]` |
| Ziel | Echte Bilder für Website (Hero, Vorher/Nachher-Slider, Leistungsseiten, Galerie), Social Media und Anzeigen |

---

## 2. Technische Vorgaben

### 2.1 Foto

| Punkt | Vorgabe |
|---|---|
| Aufnahmeformat | RAW, zusätzlich JPEG als Sicherung |
| Objektive | Standardzoom ca. 24 bis 70 mm, Makro ca. 90 bis 105 mm, optional Festbrennweite 35 oder 50 mm |
| Belichtung | Manuell. ISO so niedrig wie möglich. Blende außen f/5,6 bis f/8, Makro f/8 bis f/11 |
| Weißabgleich | Manuell auf Kelvin fixiert, kein Auto-Weißabgleich |
| Filter | Polfilter außen gegen Spiegelungen. Bei Vorher/Nachher Drehung des Filters nicht verändern |
| Stativ | Pflicht für Vorher/Nachher, Punktlicht und Makro |
| Farbraum Export | sRGB |
| Master | Volle Auflösung, mindestens 3200 px lange Kante |

### 2.2 Video

| Punkt | Vorgabe |
|---|---|
| Querformat | 3840 × 2160 (4K UHD), 25 fps |
| Hochformat | Nativ hochkant drehen, mindestens 1080 × 1920, besser 2160 × 3840, 25 fps |
| Zeitlupe | 50 oder 100 fps (Wasserperlen, Schaum, Pad auf Lack) |
| Zeitraffer | Intervall ca. 5 Sekunden, Kamera fest montiert |
| Codec | H.264 oder H.265, hohe Bitrate |
| Ton | Originalton separat aufnehmen (Maschine, Sauger, Wasser). Sprachaufnahmen mit Ansteckmikrofon |
| Clip-Länge | Pro Einstellung mindestens 10 Sekunden ruhig halten, plus 2 Sekunden Vor- und Nachlauf |

### 2.3 Exportformate nach Einsatz

| Einsatz | Seitenverhältnis | Exportgröße | Dateiformat |
|---|---|---|---|
| Website Hero | 16:9 | 2560 × 1440 px | WebP oder JPEG, Qualität ca. 80 |
| Website Vorher/Nachher-Slider | **4:3** | 1600 × 1200 px (Master 3200 × 2400 px) | WebP oder JPEG, Qualität ca. 80 |
| Website Galerie, Leistungsseiten | 4:3 | 1600 × 1200 px | WebP oder JPEG |
| Social-Preview (Link-Vorschau) | 1,91:1 | 1200 × 630 px | JPEG |
| Social Feed quadratisch | 1:1 | 1080 × 1080 px | JPEG |
| Social Feed hoch (bevorzugt Instagram) | 4:5 | 1080 × 1350 px | JPEG |
| Reels, TikTok, Stories, Shorts | **9:16** | 1080 × 1920 px | MP4 (H.264) |
| Video Website / YouTube | 16:9 | 1920 × 1080 oder 3840 × 2160 px | MP4 (H.264) |

**Bildaufbau für mehrere Formate:** Hauptmotiv mittig mit Luft an allen Seiten fotografieren. So funktioniert aus einem Bild ein 16:9-, 4:3-, 4:5- und 1:1-Ausschnitt. Beim Hero links oder rechts Freiraum für Text lassen.

`[PLATZHALTER: Prüfen, ob das Verwaltungsportal Bilder automatisch verkleinert oder bestimmte Maximalgrößen verlangt]`

### 2.4 Dateinamen-Schema

```
elbdetail_<gruppe>_<motiv>_<fahrzeug>_<jjjjmmtt>_<nr>[_vorher|_nachher].<endung>
```

**Regeln:** nur Kleinbuchstaben, keine Leerzeichen, keine Umlaute (ä = ae, ö = oe, ü = ue, ß = ss). Bindestrich innerhalb eines Teils, Unterstrich zwischen den Teilen. Nummer zweistellig.

| Gruppe | Kürzel |
|---|---|
| Hero | `hero` |
| Außenaufbereitung | `aussen` |
| Innenraum | `innen` |
| Lackpolitur | `lack` |
| Keramikversiegelung | `keramik` |
| Lederaufbereitung und Lederreparatur | `leder` |
| Detail-Makro | `makro` |
| Standort/Werkstatt | `standort` |
| Inhaber bei der Arbeit | `arbeit` |
| Abnahme mit Kunde | `abnahme` |
| Social-Clip | `clip` |

**Beispiele:**

```
elbdetail_innen_fahrersitz_kombi_20261020_01_vorher.jpg
elbdetail_innen_fahrersitz_kombi_20261020_01_nachher.jpg
elbdetail_lack_motorhaube-punktlicht_kompakt_20261020_03_vorher.jpg
elbdetail_hero_front-34_suv_20261021_01.jpg
elbdetail_clip_wasserperlen-zeitlupe_kompakt_20261021_02.mp4
```

Vorher und Nachher eines Paares unterscheiden sich **nur** in der Endung `_vorher` / `_nachher`.

Fahrzeug im Dateinamen nur als Klasse (`kompakt`, `kombi`, `limousine`, `suv`, `van`), nicht mit Kennzeichen oder Kundennamen.

---

## 3. Vorher/Nachher-Regeln

Vorher/Nachher-Bilder sind der wichtigste Beweis. Sie müssen ehrlich und vergleichbar sein.

1. **Vorher zuerst.** Vorher-Fotos entstehen, bevor jemand das Fahrzeug reinigt oder Türen, Sitze und Lenkrad verstellt.
2. **Stativ ist Pflicht.** Kein Vorher/Nachher aus der Hand.
3. **Markierung am Boden.** Positionen der drei Stativbeine mit Klebeband markieren. Bei Außenaufnahmen zusätzlich die Position der Vorderreifen mit Klebeband oder Kreide markieren, damit das Auto exakt gleich steht.
4. **Gleiche Höhe.** Höhe der Mittelsäule und Neigung des Stativkopfes notieren oder markieren.
5. **Gleiche Brennweite.** Festbrennweite nutzen oder den Zoomring mit Klebeband fixieren. Brennweite notieren.
6. **Gleiche Kameraeinstellungen.** Blende, Zeit, ISO und Weißabgleich manuell und identisch. Kein Automatikmodus.
7. **Gleiches Licht.** Innen: gleiche Leuchten an gleicher Position. Außen: möglichst unter konstantem Licht (Halle, überdacht oder gleichmäßig bedeckter Himmel). Uhrzeit notieren.
8. **Punktlicht bei Lack.** Leuchte an gleicher Position (Boden markieren), gleicher Winkel, gleicher Abstand. Raum gleich abgedunkelt.
9. **Gleicher Zustand drumherum.** Türstellung, Sitzposition, Lenkrad, Fußmatten, Fensterhöhe identisch.
10. **Gleiche Bearbeitung.** Ein Preset für beide Bilder, synchron angewendet. **Keine Retusche, kein Wegstempeln von Schmutz oder Kratzern.**
11. **Gleicher Ausschnitt.** In 4:3 fotografieren oder beide Bilder mit identischen Werten auf 4:3 zuschneiden.
12. **Kennzeichen** in beiden Bildern gleich unkenntlich machen.
13. **Protokoll** pro Paar: Dateinummer, Brennweite, Blende, Zeit, ISO, Kelvin, Uhrzeit, Bemerkung.

---

## 4. Shotlist

Format-Kürzel: 16:9, 4:3, 4:5, 1:1, 9:16. V/N = Vorher/Nachher-Paar nach Abschnitt 3. Einwilligung: P = Person erkennbar (Model Release nötig), H = Halter-Einwilligung für Fahrzeug, K = Kennzeichen unkenntlich machen.

### 4.1 Hero

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 01 | Frisch aufbereitetes Fahrzeug, 3/4-Front | Scheinwerferhöhe, ca. 35 bis 50 mm, Freiraum für Text | Bedeckter Himmel oder Abendlicht | 16:9, 4:5 | Startseite Hero | H, K |
| 02 | Gleiches Fahrzeug im Seitenprofil mit klarer Spiegelung im Lack | Kniehöhe, ca. 50 mm | Weiches Tageslicht | 16:9 | Leistungsseite Außenaufbereitung | H, K |
| 03 | Hände führen Poliermaschine über Motorhaube | Seitlich flach, ca. 35 mm | Punktlicht, Raum abgedunkelt | 16:9, 9:16 | Leistungsseite Lackpolitur | |
| 04 | Fertiger Innenraum durch offene Fahrertür | Leicht erhöht, ca. 24 mm | Gleichmäßig, Aufhelllicht | 16:9, 4:3 | Leistungsseite Innenaufbereitung | H |
| 05 | Abnahme: zwei Personen von hinten vor dem fertigen Auto | Halbtotale, ca. 35 mm | Tageslicht | 16:9 | Startseite Ablauf, Aktion | H, K, P falls erkennbar |
| 06 | Video-Loop: Wasser perlt von versiegeltem Lack | Makro, Zeitlupe 100 fps, 10 Sekunden | Tageslicht, Gegenlicht | 16:9 Video | Aktion Winterschutz | |

### 4.2 Außenaufbereitung

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 07 | Zwei Eimer nebeneinander (Wasch- und Spüleimer) | Bodennah, ca. 35 mm | Tageslicht | 4:5, 1:1 | Beweis Zwei-Eimer-Methode | |
| 08 | Vorreinigung des Fahrzeugs, so wie tatsächlich gearbeitet wird | Totale, ca. 24 mm | Tageslicht | 16:9, 9:16 | Außenaufbereitung, Reel | H, K |
| 09 | Waschhandschuh gleitet über Lack | Nah, ca. 50 mm | Weiches Licht | 4:5 | Social, Außenaufbereitung | |
| 10 | Felge vorher und nachher | Frontal auf Nabenhöhe, Stativ, ca. 50 mm | Konstant | 4:3 V/N | Vorher/Nachher-Slider | H |
| 11 | Felgenreinigung mit Pinsel zwischen den Speichen | Makro, ca. 100 mm | Seitenlicht | 4:5, 9:16 | Social | |
| 12 | Trocknen mit Mikrofasertuch | Nah, ca. 50 mm | Weiches Licht | 4:5 | Social | |
| 13 | Scheibenreinigung, Blick durch klare Scheibe | Halbnah, ca. 35 mm | Tageslicht | 4:3 | Außenaufbereitung | |
| 14 | Ganzes Fahrzeug seitlich vorher und nachher | Stativ, Reifen markiert, ca. 35 mm | Konstant oder bedeckt | 4:3 V/N | Vorher/Nachher-Slider | H, K |
| 15 | Einstiegsleiste und Türfalz vorher und nachher | Nah, Stativ, ca. 50 mm | Aufhelllicht | 4:3 V/N | Galerie | H |

### 4.3 Innenraum

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 16 | Fahrersitz vorher und nachher | Durch offene Tür, Stativ, ca. 24 mm | Gleichmäßig, gleiche Leuchten | 4:3 V/N | Vorher/Nachher-Slider | H |
| 17 | Fußraum Fahrer vorher und nachher | Von oben, Stativ, ca. 24 mm | Aufhelllicht | 4:3 V/N | Innenaufbereitung, Galerie | H |
| 18 | Kofferraum mit Hundehaaren vorher und nachher | Durch Heckklappe, Stativ, ca. 24 mm | Gleichmäßig | 4:3 V/N, 9:16 | Meta-Kampagne Innenraum/Hund | H |
| 19 | Polsterreinigung mit dem tatsächlich genutzten Gerät | Nah, ca. 35 mm | Seitenlicht | 4:5, 9:16 | Social, Innenaufbereitung | |
| 20 | Lederpflege mit Applikator auf Sitzwange | Makro, ca. 100 mm | Weiches Seitenlicht | 4:5 | Lederpflege | |
| 21 | Pinsel in Lüftungsgitter | Makro, ca. 100 mm | Taschenlampe als Akzent | 1:1, 9:16 | Social | |
| 22 | Mittelkonsole und Getränkehalter vorher und nachher | Von oben, Stativ, ca. 35 mm | Gleichmäßig | 4:3 V/N | Galerie | H |
| 23 | Fugendüse saugt Sitzfuge aus | Nah, ca. 50 mm | Seitenlicht | 9:16 | Reel | |
| 24 | Geruchsneutralisation, Mittel oder Gerät wie tatsächlich verwendet | Halbnah, ca. 35 mm | Gleichmäßig | 4:5 | Innenaufbereitung, Geruchsentfernung | |
| 25 | Fertiger Innenraum als Totale von hinten | Rückbank, ca. 16 bis 24 mm | Gleichmäßig | 16:9, 4:3 | Leistungsseite Innen | H |

### 4.4 Lackpolitur mit Punktlicht

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 26 | Lackschichtdickenmessgerät auf Lack, Display lesbar | Nah, ca. 50 bis 100 mm | Weiches Licht, Display ohne Reflex | 4:5, 9:16 | Beweis Messung, Lackpolitur | |
| 27 | Swirls und Hologramme unter Punktlicht (vorher) | Stativ, Leuchte markiert, ca. 50 mm | Punktlicht, Raum dunkel | 4:3 V/N | Vorher/Nachher-Slider Lack | H |
| 28 | Gleiche Stelle nach der Politur (nachher) | Identisch zu 27 | Identisch zu 27 | 4:3 V/N | Vorher/Nachher-Slider Lack | H |
| 29 | 50/50-Fläche: halb poliert, Trennlinie mit Klebeband | Stativ, ca. 50 mm | Punktlicht | 4:3, 9:16 | Reel, Lackpolitur | |
| 30 | Poliermaschine in Bewegung, leichte Bewegungsunschärfe | Seitlich, ca. 35 mm, 1/15 s | Punktlicht | 16:9, 9:16 | Hero-Alternative, Reel | |
| 31 | Politur auf Pad, Koch-Chemie-Flasche im Hintergrund unscharf | Makro, ca. 100 mm | Seitenlicht | 4:5 | Beweis Koch-Chemie | |
| 32 | Auftragen der Lackversiegelung | Nah, ca. 50 mm | Weiches Licht | 4:5 | Lackversiegelung | |
| 33 | Wasserperlen auf versiegelter Motorhaube | Makro, ca. 100 mm | Gegenlicht | 1:1, 4:5, 9:16 | Winterschutz, Lackversiegelung | |
| 34 | Spiegelung im polierten Lack (Himmel, Baum oder Halle) | Flach über Lack, ca. 35 mm | Tageslicht | 4:5, 16:9 | Lackpolitur, Social | H |

### 4.5 Detail-Makros

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 35 | Felgenspeiche mit Bremssattel dahinter, sauber | Makro, ca. 100 mm | Seitenlicht | 1:1, 4:5 | Social | |
| 36 | Scheinwerfer nach Reinigung | Nah, ca. 100 mm | Weiches Licht | 4:5 | Social | |
| 37 | Ledernaht am Lenkrad | Makro, ca. 100 mm | Seitenlicht | 1:1 | Lederpflege | |
| 38 | Wasserperlen auf versiegelter Scheibe | Makro, ca. 100 mm | Gegenlicht | 4:5 | Scheibenversiegelung, Winterschutz | |
| 39 | Gefaltete Mikrofasertücher, sortiert | Von oben, ca. 50 mm | Gleichmäßig | 1:1 | Social, Ratgeber | |
| 40 | Pedale und Fußmatte nach Reinigung | Nah, ca. 35 mm | Aufhelllicht | 4:5 | Innenaufbereitung | |
| 41 | Türgriffmulde vorher und nachher | Makro, Stativ, ca. 100 mm | Konstant | 4:3 V/N | Galerie | H |

### 4.6 Standort und Werkstatt

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 42 | Außenansicht Standort Lachtehäuser Straße 1 | Totale, ca. 24 mm | Tageslicht | 16:9, 4:3 | Kontakt, Anfahrt | `[PLATZHALTER: Schild/Logo am Gebäude vorhanden?]` |
| 43 | Zufahrt und Abstellfläche, so wie Kunden ankommen | Augenhöhe, ca. 24 mm | Tageslicht | 4:3 | Termin-Seite, Anfahrt | Fremde Kennzeichen K |
| 44 | Arbeitsplatz aufgeräumt als Totale | Ecke des Raums, ca. 16 bis 24 mm | Arbeitslicht | 16:9 | Firmenkunden, Startseite | |
| 45 | Produktregal mit Produkten von C²Coating, Koch-Chemie und Colourlock | Halbnah, ca. 35 mm | Gleichmäßig | 4:5, 1:1 | Beweis Profi-Produkte | |
| 46 | Arbeitswagen mit Werkzeug, Pads, Pinseln | Halbnah, ca. 35 mm | Gleichmäßig | 4:5 | Social | |
| 47 | Arbeitsplatz am Abend, Licht an, Auto auf der Fläche | Totale, ca. 24 mm | Mischlicht | 16:9, 9:16 | Social, Hero-Alternative | H, K |

### 4.7 Inhaber bei der Arbeit

Gesicht nur mit unterschriebenem Model Release. Ohne Einwilligung: nur Hände, Rücken, Silhouette.

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 48 | Hände mit Waschhandschuh, Wasser tropft | Nah, ca. 50 mm | Gegenlicht | 4:5, 9:16 | Social | |
| 49 | Hände setzen Messgerät auf Kotflügel | Nah, ca. 50 mm | Weiches Licht | 4:5 | Lackpolitur | |
| 50 | Blick über die Schulter: Lackprüfung mit Taschenlampe | Hinter der Person, ca. 35 mm | Punktlicht | 16:9, 9:16 | Lackpolitur, Reel | |
| 51 | Porträt Inhaber am fertigen Fahrzeug | Halbtotale, ca. 50 bis 85 mm | Weiches Tageslicht | 4:5, 4:3 | Startseite "Warum ElbDetail", Google Business Profile | P |
| 52 | Inhaber konzentriert bei der Arbeit, Blick auf die Arbeit | Halbnah, ca. 85 mm | Arbeitslicht | 16:9, 4:5 | Startseite "Warum ElbDetail" | P |
| 53 | Video: Inhaber erklärt in 20 Sekunden die Lackschichtdickenmessung | Halbnah, Stativ, Ansteckmikrofon | Weiches Licht | 9:16, 16:9 | Reel, Leistungsseite | P |

### 4.8 Abnahme mit Kunde

Nur mit echtem Kunden und schriftlicher Einwilligung. Keine gestellten Szenen mit Personen, die keine Kunden sind, ohne Hinweis.

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 54 | Gemeinsamer Rundgang um das Auto bei Tageslicht, von hinten | Totale, ca. 35 mm | Tageslicht | 16:9, 4:5 | Ablauf, Beweis Abnahme | H, K, P falls erkennbar |
| 55 | Kunde zeigt auf ein Detail, nur Hände und Fahrzeug | Nah, ca. 50 mm | Tageslicht | 4:5 | Social | H |
| 56 | Schlüsselübergabe, nur Hände | Nah, ca. 50 mm | Tageslicht | 1:1, 4:5 | Gutscheine, Social | |
| 57 | Kunde mit seinem Fahrzeug, Porträt | Halbtotale, ca. 50 mm | Tageslicht | 4:5 | Social, Bewertungs-Post | P, H, K |
| 58 | Video: Kunde öffnet die Tür und sieht den Innenraum | Über die Schulter, 9:16 | Tageslicht | 9:16 | Reel | P, H |

### 4.9 Social-Clips

| Nr. | Motiv | Perspektive / Technik | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 59 | Zeitraffer der gesamten Aufbereitung | Fest montiert, erhöht, Intervall 5 s | Konstant | 9:16, 16:9 | Reel, Website | H, K |
| 60 | Sauger zieht saubere Bahn in den Teppich | Nah, 9:16 | Seitenlicht | 9:16 | Reel "satisfying" | |
| 61 | Punktlicht schwenkt über Lack und deckt Swirls auf | Nah, 9:16, langsamer Schwenk | Dunkel, Punktlicht | 9:16 | Reel Hook | |
| 62 | Übergang: Hand wischt vor der Linse, Schnitt auf Nachher | Stativ, gleiche Position | Konstant | 9:16 | Reel Transition | H |
| 63 | POV mit Kopf- oder Brustkamera bei der Felgenreinigung | POV, Weitwinkel | Tageslicht | 9:16 | Reel, TikTok | |
| 64 | Display des Messgeräts zeigt Wert, Schnitt auf Politur | Nah, 9:16 | Weiches Licht | 9:16 | Reel | |
| 65 | Tür öffnen und Innenraum zeigen (Reveal) | Gimbal, 9:16 | Gleichmäßig | 9:16 | Reel | H |

### 4.10 Keramikversiegelung

Keramik ist der Schwerpunkt von ElbDetail. Diese Motive haben beim Shooting Vorrang. Nur zeigen, wie René tatsächlich arbeitet. Aushärtezeiten der Produkte beachten: Abperl-Aufnahmen erst, wenn die Versiegelung laut Hersteller belastbar ist, oder an einem bereits versiegelten Fahrzeug.

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 66 | Video: Wasser perlt in Zeitlupe von keramikversiegelter Motorhaube | Makro, Zeitlupe 100 fps, 10 Sekunden | Gegenlicht | 16:9 Video, 9:16 | Leistungsseite Keramik, Reel, Anzeigen AG6 | |
| 67 | Abperleffekt in Ruhe: runde Wasserperlen auf Lack | Makro, ca. 100 mm | Gegenlicht | 1:1, 4:5 | Keramik, Google-Beitrag | |
| 68 | Glanz nach dem Coating: Spiegelung von Himmel oder Halle im Lack | Flach über Lack, ca. 35 mm | Tageslicht | 16:9, 4:5 | Hero-Alternative, Keramik | H |
| 69 | Vorbereitung: Lackdekontamination (Flugrost- oder Teerentferner, Knete), wie tatsächlich verwendet | Nah, ca. 50 mm | Weiches Licht | 4:5, 9:16 | Keramik, Ratgeber | |
| 70 | Vorbereitung: Lack entfetten mit Tuch vor dem Auftrag | Nah, ca. 50 mm | Weiches Licht | 4:5 | Keramik "Vorbereitung" | |
| 71 | Auftrag von Hand: Applikator gleitet im Kreuzgang über den Lack | Nah, seitlich, ca. 50 mm | Prüflicht oder Seitenlicht | 4:5, 9:16 | Keramik, Reel | |
| 72 | Rückstände abnehmen mit Mikrofasertuch unter Prüflicht | Nah, ca. 50 mm | Punktlicht | 4:5, 9:16 | Keramik | |
| 73 | IR-Trocknung: Infrarotstrahler vor der versiegelten Fläche | Halbnah, ca. 35 mm | Mischlicht | 16:9, 4:5 | Keramik `[PLATZHALTER: Nutzt René IR-Trocknung? Sonst streichen.]` | |
| 74 | Urkunde "C²Coating Excellence Partner", gut lesbar, ohne Spiegelung | Frontal, Stativ, ca. 50 mm | Gleichmäßig, Polfilter | 4:5, 1:1 | Über uns, Google-Profil, Keramik | P, falls René die Urkunde hält |
| 75 | C²Coating-Produkte auf dem Arbeitswagen, Etiketten lesbar | Halbnah, ca. 50 mm | Gleichmäßig | 4:5, 1:1 | Beweis C²Coating | |
| 76 | Wasser perlt von keramikversiegelter Frontscheibe | Makro, ca. 100 mm | Gegenlicht | 4:5, 9:16 | Keramik Glas | |
| 77 | Wasser perlt von keramikversiegelter Felge, Speiche im Detail | Makro, ca. 100 mm | Seitenlicht | 1:1, 4:5 | Keramik Felgen | |
| 78 | Video: Pflegewäsche eines keramikversiegelten Fahrzeugs, Schaum läuft ab | Totale und Nah, 9:16 | Tageslicht | 9:16, 16:9 | Pflege keramikversiegelter Fahrzeuge, ElbDetail Care | H, K |

### 4.11 Lederreparatur mit Colourlock

Vorher/Nachher nach den Regeln aus Abschnitt 3. Keine Retusche am Leder. Nur Reparaturen zeigen, die René wirklich gemacht hat.

| Nr. | Motiv | Perspektive / Brennweite | Licht | Format | Einsatz | Einwill. |
|---|---|---|---|---|---|---|
| 79 | Sitzwange mit Abrieb, Rissen oder Farbverlust (vorher) | Nah, Stativ, ca. 50 bis 100 mm | Weiches Seitenlicht, Leuchte markiert | 4:3 V/N | Leistungsseite Leder, Google-Beitrag | H |
| 80 | Gleiche Stelle nach der Colourlock-Reparatur (nachher) | Identisch zu 79 | Identisch zu 79 | 4:3 V/N | Leistungsseite Leder, Vorher/Nachher-Slider | H |
| 81 | Lenkrad abgegriffen vorher und nachher | Nah, Stativ, ca. 50 mm | Weiches Licht | 4:3 V/N | Leder, Galerie | H |
| 82 | Reinigung mit Colourlock-Lederreiniger und Bürste, Schaum auf dem Leder | Makro, ca. 100 mm | Seitenlicht | 4:5, 9:16 | Leder, Reel | |
| 83 | Reparatur: Farbe oder Füller wird aufgetragen, so wie tatsächlich gearbeitet wird | Nah, ca. 50 mm | Weiches Licht | 4:5, 9:16 | Leder | |
| 84 | Colourlock-Produkte im Arbeitskontext am Sitz | Halbnah, ca. 35 mm | Gleichmäßig | 4:5, 1:1 | Beweis Colourlock | |

---

## 5. Reel- und Short-Ideen

Für Instagram Reels, TikTok, Facebook Reels und YouTube Shorts. Länge 15 bis 30 Sekunden. Text-Overlay in Inter 650 (Akzentwort in Instrument Serif kursiv), Weiß auf Anthrazit-Fläche, sichere Zone beachten (oben ca. 250 px und unten ca. 400 px frei). Musik nur aus der kommerziell freigegebenen Bibliothek der Plattform oder lizenzfrei.

| Nr. | Titel | Hook (0 bis 2 Sekunden) | Ablauf | Text-Overlay | Motive |
|---|---|---|---|---|---|
| 1 | Erst messen | Messgerät setzt auf Lack, Zahl erscheint | Messung an 3 Stellen, Schnitt auf Politur, Ergebnis unter Punktlicht | "Wie viel Lack hat Ihr Auto noch?" dann "Erst messen. Dann polieren." | 26, 49, 64, 30 |
| 2 | Swirl-Reveal | Punktlicht geht an, Hologramme leuchten auf | Schwenk über Motorhaube, Politur, gleicher Schwenk nachher | "Das sieht man nur mit Punktlicht." dann "Und jetzt?" | 61, 27, 28 |
| 3 | Hund an Bord | Nahaufnahme Hundehaare im Kofferraum | Saugen, Bürsten, Kofferraum-Totale nachher | "Hund an Bord?" dann "Kofferraum wieder frei." | 18, 60, 23 |
| 4 | Warum zwei Eimer | Zwei Eimer werden hingestellt, Klopfen | Handschuh in Wascheimer, Lack, Spüleimer, wieder Wascheimer | "Warum wir zwei Eimer nehmen" dann "Schmutz bleibt im Spüleimer. Nicht auf Ihrem Lack." | 07, 09, 48 |
| 5 | Winterfest | Wasser trifft versiegelten Lack in Zeitlupe | Perlen, Felge, Scheibe, Auto in der Totale | "Bereit für Salz und Matsch?" dann "Winter-Lackschutz in Celle" | 06, 33, 38 |
| 6 | 50/50 | Klebeband wird abgezogen | Punktlicht über die Trennlinie, langsam | "Links vorher. Rechts nachher." | 29, 61 |
| 7 | Saubere Linie | Sauger zieht eine Bahn in den Teppich | 3 Bahnen, Fußraum-Totale, Fußmatte | "Kurz zuschauen. Lohnt sich." | 60, 17, 40 |
| 8 | Abnahme bei Tageslicht | Fahrzeug fährt ins Tageslicht | Rundgang, Kunde zeigt Detail, Schlüssel | "Zum Schluss: gemeinsame Abnahme bei Tageslicht." | 54, 55, 56 |
| 9 | Preis vorab | Smartphone zeigt WhatsApp mit 3 Fotos (Demo-Chat ohne echte Kundendaten) | Fotos senden, Antwort mit Preis, Terminbestätigung | "3 Fotos per WhatsApp." dann "Verbindlicher Preis vor dem Termin." dann "+49 172 7613807" | Demo-Screen, 01 |
| 10 | Leasingrückgabe | Kalender mit markiertem Rückgabetermin | Rundgang mit Taschenlampe, Messung, Politur, Innenraum, Abnahme | "Leasingrückgabe steht an?" dann "Gepflegt in die Übergabe." | 50, 26, 30, 25, 54 |
| 11 | Keramik in 20 Sekunden | Wasser trifft keramikversiegelten Lack, Perlen springen ab | Dekontamination, Entfetten, Auftrag von Hand, Abnehmen, Abperleffekt, Urkunde | "Was passiert vor dem Coating?" dann "Vorbereitung. Auftrag. Glanz." dann "C²Coating Excellence Partner in Celle" | 66, 69, 70, 71, 72, 74 |
| 12 | Leder gerettet | Finger fährt über die abgeriebene Sitzwange | Reinigung, Reparatur mit Colourlock, gleiche Stelle nachher | "Abrieb am Ledersitz?" dann "Reparatur mit Colourlock." | 79, 82, 83, 80 |

**Hinweise:**
- In den ersten 2 Sekunden kein Logo-Intro. Sofort das Motiv.
- Am Ende 2 Sekunden Endkarte: Logo, "Termin per WhatsApp: +49 172 7613807", elbdetail.de.
- Untertitel für gesprochenen Text immer einblenden.
- Keine Versprechen ins Overlay, die nicht in den Fakten stehen (keine Garantien, keine Haltbarkeit in Jahren bei Keramik, keine Ersparnis bei Leasingrückgabe, keine Preise für Keramik).

---

## 6. Einwilligungen und Datenschutz

Diese Hinweise ersetzen keine Rechtsberatung. `[PLATZHALTER: Vorlagen für Model Release und Halter-Einwilligung rechtlich prüfen lassen]`

### 6.1 Model Release (erkennbare Personen)

Vor der Aufnahme schriftlich einholen. Inhalt:

- Name, Datum, Ort des Shootings
- Welche Aufnahmen (Foto, Video, Ton)
- Zweck und Kanäle: Website elbdetail.de, Instagram, TikTok, Facebook, Google Business Profile, bezahlte Anzeigen (Google, Meta), Druck
- Dauer der Nutzung `[PLATZHALTER: unbefristet oder befristet]`
- Vergütung `[PLATZHALTER: unentgeltlich oder Gegenleistung]`
- Widerrufsrecht und wie widerrufen wird (E-Mail an info@elbdetail.de). Hinweis, dass bereits gedruckte Medien und geschaltete Anzeigen ggf. nicht sofort zurückgeholt werden können
- Bei Minderjährigen: Unterschrift aller Sorgeberechtigten
- Unterschrift, Kopie an die Person

Gilt auch für den Inhaber selbst, für Aushilfen und für Kunden bei der Abnahme.

### 6.2 Halter-Einwilligung (Kundenfahrzeuge)

- Schriftliche Zustimmung des Halters, dass sein Fahrzeug fotografiert und gezeigt werden darf
- Ausdrücklich auch für Vorher-Bilder (die zeigen den Zustand vor der Aufbereitung)
- Option: "Nur ohne Kennzeichen und ohne erkennbare persönliche Gegenstände"

### 6.3 Kennzeichen und persönliche Daten

- **Kennzeichen** im Shooting mit neutraler Abdeckung verdecken (nur auf dem Betriebsgelände, nie im Straßenverkehr) oder in der Nachbearbeitung unkenntlich machen (deckende Fläche, kein schwacher Weichzeichner)
- Fremde Fahrzeuge im Hintergrund ebenfalls unkenntlich machen
- Vor dem Vorher-Foto entfernen oder abdecken: Briefe, Rechnungen, Parkausweise, Fahrzeugschein, Kindersitz mit Namen, Fotos, Navi- und Infotainment-Display mit Adressen oder Kontakten, Schlüsselanhänger mit Namen
- Bildschirme im Video (WhatsApp-Demo) nur mit Demo-Daten

### 6.4 Ablage

- Unterschriebene Einwilligungen digital und im Original ablegen `[PLATZHALTER: Ablageort]`
- Pro Bild nachvollziehbar, welche Einwilligung gilt (Dateinummer im Formular notieren)
- Bei Widerruf: Bild aus Website-Galerie und Social Media entfernen

---

## 7. Einsatz auf der Website

**Hochladen:** Verwaltungsportal → Galerie hochladen. `[PLATZHALTER: Feldnamen im Portal prüfen, z. B. Titel, Alternativtext, Kategorie, Vorher/Nachher-Zuordnung]`

| Bereich | Seite | Format | Motive aus der Shotlist |
|---|---|---|---|
| Hero Startseite | `/index.html` | 16:9 | 01, Alternativen 30, 47 |
| Vorher/Nachher-Slider | `/index.html` (Abschnitt Vorher/Nachher) | 4:3, Paare | 14, 16, 27/28, Reserve 10, 17, 18 |
| Warum ElbDetail / Ablauf | `/index.html` | 4:3, 16:9 | 05, 26, 52, 54 |
| Außenaufbereitung | `/leistungen/aussenaufbereitung-celle.html` | 16:9, 4:3 | 02, 08, 10, 13, 14 |
| Innenaufbereitung | `/leistungen/innenaufbereitung-celle.html` | 16:9, 4:3 | 04, 16, 17, 18, 25 |
| Lackpolitur | `/leistungen/lackpolitur-celle.html` | 16:9, 4:3 | 03, 26, 27/28, 29, 34 |
| Lackversiegelung | `/leistungen/lackversiegelung-celle.html` | 4:3 | 32, 33, 38 |
| Keramikversiegelung | `/leistungen/keramikversiegelung-celle.html` | 16:9, 4:3 | 66 bis 78, Hero-Alternative 68 |
| Lederaufbereitung | `/leistungen/lederaufbereitung-celle.html` | 16:9, 4:3 | 79/80, 81, 82 bis 84, 20, 37 |
| ElbDetail Care | `/elbdetail-care.html` | 16:9, 4:3 | 78, 44, 47 |
| Über uns | `/ueber-uns.html` | 4:5, 4:3 | 51, 52, 53, 74 |
| Leasingrückgabe / Verkauf | `/leistungen/leasingrueckgabe-gebrauchtwagen-celle.html` | 4:3 | 14, 50, 54 |
| Winter-Lackschutz | `/aktion/winterschutz.html` | 16:9, 4:3 | 06, 33, 35, 38 |
| Gutscheine | `/gutscheine.html` | 4:3 | 56, 01 |
| Firmenkunden & Flotten | `/firmenkunden.html` | 16:9 | 44, 47, 68 |
| Termin | `/termin.html` | 4:3 | 42, 43 |
| Ratgeber | `/ratgeber/index.html` | 4:3 | 07, 26, 39 |
| Galerie | Galerie im Verwaltungsportal | 4:3 | alle freigegebenen V/N-Paare und Details |

**Alternativtexte** sachlich beschreiben, ohne Kennzeichen oder Namen. Beispiele:
- "Vorher: Fahrersitz eines Kombis mit Krümeln und Flecken"
- "Nachher: derselbe Fahrersitz nach der Innenraum-Tiefenreinigung"
- "Lackschichtdickenmessung an der Motorhaube vor der Politur"
- "Wasser perlt von einer keramikversiegelten Motorhaube"
- "Vorher: Ledersitz mit Abrieb an der Sitzwange"

**Reihenfolge Vorher/Nachher:** immer vorher links bzw. zuerst, nachher rechts bzw. danach.

---

## 8. Ablauf am Shooting-Tag (Vorschlag)

| Schritt | Inhalt | Motive |
|---|---|---|
| 1 | Aufbau, Bodenmarkierungen, Stativpositionen, Protokoll vorbereiten | |
| 2 | Einwilligungen unterschreiben lassen, Kennzeichen abdecken, persönliche Gegenstände entfernen | |
| 3 | Alle Vorher-Bilder, bevor gearbeitet wird | 10, 14, 15, 16, 17, 18, 22, 27, 41, 79, 81 |
| 4 | Zeitraffer-Kamera starten | 59 |
| 5 | Arbeit begleiten: außen, innen, Lack, Makros, Hände | 07 bis 13, 19 bis 24, 26, 29 bis 33, 48 bis 50, 82 bis 84 |
| 5a | Keramikversiegelung begleiten: Vorbereitung, Auftrag, Abnehmen, ggf. IR-Trocknung. Oft eigener Termin, weil das Coating Zeit zum Aushärten braucht | 69 bis 73, 75 |
| 6 | Alle Nachher-Bilder mit identischen Einstellungen | Gegenstücke aus Schritt 3, 28, 80 |
| 7 | Hero, Spiegelung, Wasserperlen, Details | 01 bis 06, 34 bis 40, 66 bis 68, 76 bis 78 (an einem ausgehärteten Fahrzeug) |
| 8 | Standort, Porträt, Erklärvideo, Urkunde | 42 bis 47, 51 bis 53, 74 |
| 9 | Abnahme mit Kunde bei Tageslicht | 54 bis 58 |
| 10 | Social-Clips und Reel-Hooks gezielt nachdrehen | 60 bis 65 |
| 11 | Datensicherung doppelt, Dateinamen nach Schema | |
