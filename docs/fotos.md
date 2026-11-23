# Fotos auf der Website

Stand 23.11.2026. Quelle: Google-Drive-Ordner von ElbDetail (37 verschiedene Fotos, 34 verwendet).

## Wo welche Fotos stehen

| Ort | Fotos | Datei/Feld |
|---|---|---|
| Startbild | Audi S6 unter dem Wabenlicht (Halle) | `content/site.json → heroImage` |
| Keramik-Abschnitt Startseite | BMW Cabrio mit C²Coating-Flasche | `site.json → spotlightImage` |
| Vorher/Nachher (Regler) | Scheinwerfer Ford Ka, BMW X3, Mercedes C, VW Tiguan | `content/gallery.json` |
| „Frisch aus der Halle“ | 12 Fotos, am Desktop 8 + Knopf | `site.json → workshopPhotos` |
| Leistungsseiten | Titelbild `image`, weitere Fotos `photos` | `content/services/*.json` |
| Über uns | 3 Fotos | `site.json → about.photos` |
| Ratgeber | je ein Bild, auch auf den Karten | `content/ratgeber/*.md → image` |
| Teilen-Vorschau (WhatsApp, Facebook) | `static/og-image.jpg`, Vorlage `docs/vorlagen/og-image.html` | |

Jedes Foto lässt sich antippen und im Vollbild ansehen (Wischen, Pfeiltasten, Esc).

## Bearbeitung

- Verkleinert auf höchstens 2000 px, **ohne EXIF/GPS** (Standortdaten der iPhone-Fotos entfernt).
- Einheitliche, dezente Korrektur: Weißabgleich zur Hälfte Richtung neutral, Tonwerte leicht gespreizt, leicht geschärft. Keine Retusche am Fahrzeug.
- Zuschnitte: Tesla ohne Werkzeugwagen (Energydrink-Dose) und Fremdfahrzeug, Peugeot ohne Werbe-Kühlschrank, Audi Q3 ohne angeschnittene Person, Audi S6 Heck ohne Kühlschrank.
- Zertifikat im Mercedes: Unterschriften unkenntlich gemacht.
- Scheinwerfer Ford Ka: Nachher-Foto gespiegelt (andere Fahrzeugseite, gleicher Tag); steht so in der Bildunterschrift.
- Kennzeichen: bereits geschwärzt oder abgenommen.

## Nicht verwendet

- Mazda (Vorher/Nachher): Fußraum auf dem Nachher-Foto nicht überzeugend sauber.
- VW Tiguan Rückbank (zweites Vorher-Foto, doppelt zum Tierhaar-Foto).

## Neue Fotos aufnehmen (für noch bessere Vorher/Nachher-Regler)

1. Handy auf eine Halterung oder immer an dieselbe Stelle (z. B. Markierung am Boden).
2. Gleicher Winkel, gleiche Brennweite (1×), gleiches Licht, Tür gleich weit offen.
3. Hochformat, Fahrzeug füllt das Bild. Kennzeichen abdecken oder später unkenntlich machen.
4. Einverständnis der Kundin oder des Kunden für die Veröffentlichung einholen.
