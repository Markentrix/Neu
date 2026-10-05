# Demo: HOLZWERK GmbH, Celle (Redesign-Vorschlag, Paket BUSINESS WEB)

Entwurf von Markentrix nach Skill `markentrix-kundenwebsite`. **Nicht veröffentlichen**, solange nicht freigegeben: `noindex`, Demo-Leiste, kein Tracking, keine Drittanbieter, Formular ohne Funktion.

Online-Vorschau (05.10.2026): Netlify-Projekt `hw-demo-7i85te2dug` im Team „Markentrix“ (Free-Tarif, kein Passwortschutz), unlistbare Adresse, `noindex` per Meta-Tag und Header. Link nur an den Kunden geben. **Löschen nach 30 Tagen ohne Auftrag** (Netlify: Project settings → Delete). Deploy-Inhalt: HTML, `assets/`, `favicon.svg`, `robots.txt`, `_headers` (ohne `build/`, `preview/`, README).

Start lokal: `python3 -m http.server 8765` im Ordner, dann `http://127.0.0.1:8765/`.

## Grundlage
Inhalte, Kontaktdaten, Leistungen, Referenzen, Einzugsgebiet, Logo und Fotos stammen von der bisherigen Website holzwerk-celle.de (Stand 05.10.2026). Texte sind gekürzte Vorschläge, kein Wortlaut vom Kunden freigegeben.

## Bisherige Seite (Befund)
Adobe-GoLive-Tabellenlayout, ISO-8859-1, GIF-Banner, 12-px-Text, keine Responsive-Darstellung, externes Cookie-Plugin (valao.de), YouTube-Einbettung, viele Unterseiten mit kleinen Bildergalerien.

## Redesign (Paket BUSINESS WEB: bis sieben Inhaltsseiten)
Sieben Inhaltsseiten: **Start**, **Leistungen**, **Fachwerk & Altbausanierung**, **Dach & Dachstühle**, **Referenzen**, **Über uns**, **Kontakt**. Dazu Impressum, Datenschutz und 404 (zählen laut Festlegung nicht mit). Mobil zuerst, Navigation mit Menü-Schalter, Vorher/Nachher-Regler, Bildergalerien mit barrierefreier Lightbox (natives `<dialog>`, Tastatur, Esc), Kontaktformular (Demo ohne Funktion). Farben aus dem Logo (Lindgrün #89BD38, Fast-Schwarz #1C1C1A) plus Olivgrün #3A5017 für Text auf Hell. Schriften Fraunces und Inter (OFL, selbst gehostet, Latin-Subset). Alle Bilder WebP (Miniatur 480 px, große Ansicht 1000 px erst beim Klick). Animationen nur transform/opacity, `prefers-reduced-motion` respektiert. Ohne JavaScript bleiben Inhalt und Navigation vollständig nutzbar.

Seiten erzeugen: `python3 build/build.py` (Bausteine, Texte und Bildzuordnung stehen in `build/build.py`, Styles in `assets/main.css`, Skript in `assets/main.js`). Das CSS inklusive Überschrift-Schrift wird in jede Seite eingebettet (schneller Erstaufruf, ca. 55 KB je Seite).

## Messung (Lighthouse 12, mobil, gedrosselt Slow 4G + 4x CPU)
Alle sieben Inhaltsseiten: Performance 99–100 · Barrierefreiheit 100 · Best Practices 100 · FCP 1,1–1,2 s · LCP 1,1–1,8 s · CLS 0–0,03 · TBT 0–10 ms. Seitengewicht initial ca. 100–620 KB (Referenzen mit vielen Miniaturen am höchsten, Bilder erst beim Scrollen). Labordaten, kein Feldwert. SEO zeigt wegen `noindex` in der Demo ca. 61 (gewollt, Live-Variante: 100). Link- und Anker-Check ohne Fehler. Audit-Skript: 0 FAIL.

## Offen vor einer Veröffentlichung (Kunde klären)
1. **Bildrechte:** Fotos Jägerstraße (Roman Thomas, Celle; Architektur bussemas architekten, Lage) und alle Referenzfotos: Nutzungsrecht und Einwilligung der Eigentümer prüfen, Kfz-Kennzeichen und Personen unkenntlich halten. Das Foto der Zimmerer in Tracht: Urheber/Herkunft klären.
2. **Angaben bestätigen:** „Seit 2002“, „über 40 Mitarbeiter“, „Meisterbetrieb“, Einzugsgebiet, Titel der Vorher/Nachher-Beispiele.
3. **Logo als Vektor (SVG)** anfordern. Aktuell nur ein 760-px-GIF, die Unterzeile ist darin klein.
4. **Rechtstexte** (Impressum, Datenschutz, AGB) liefert der Kunde. Die Platzhalterseiten enthalten nur die Angaben der alten Seite. Anschrift, Register, USt-IdNr. vom Kunden.
5. **Öffnungs-/Erreichbarkeitszeiten** und Antwortzeit-Zusage nur nach Kundenangabe.
6. **Partnerfirmen** (Holz-Zentrum Luhmann, Niewerth Gerüstbau, Fassadenfachbetrieb Volkan Kilinc) stehen ohne Links in „Über uns“: Nennung und Verlinkung vom Kunden bestätigen lassen.
7. **Nicht übernommen:** Heißluftballon-Team (eigener Geschäftsbereich, Entscheidung offen), Stellenanzeige, Sponsoring-Aktionen (Rudern gegen Krebs, Wasa-Lauf, veraltet, Personenfotos), Partnerfirmen-Liste, YouTube-Video (wäre nur per Zwei-Klick-Lösung zulässig), Fotogalerie mit rund 70 Bildern (Galerie-Seite wäre ein nächster Ausbauschritt).
8. **Weiterleitungen:** Bei Relaunch alte URLs (z. B. `/leistungen/fachwerk.html`) per 301 auf die neuen Abschnitte/Seiten leiten.
9. Formular anbinden (Zustellung beim Kunden, SPF/DKIM prüfen), Domain/DNS laut Anlage „Domain und Technik“.
