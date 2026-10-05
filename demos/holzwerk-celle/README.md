# Demo: HOLZWERK GmbH, Celle (Redesign-Vorschlag)

Entwurf von Markentrix nach Skill `markentrix-kundenwebsite`. **Nicht veröffentlichen**, solange nicht freigegeben: `noindex`, Demo-Leiste, kein Tracking, keine Drittanbieter, Formular ohne Funktion.

Start lokal: `python3 -m http.server 8765` im Ordner, dann `http://127.0.0.1:8765/`.

## Grundlage
Inhalte, Kontaktdaten, Leistungen, Referenzen, Einzugsgebiet, Logo und Fotos stammen von der bisherigen Website holzwerk-celle.de (Stand 05.10.2026). Texte sind gekürzte Vorschläge, kein Wortlaut vom Kunden freigegeben.

## Bisherige Seite (Befund)
Adobe-GoLive-Tabellenlayout, ISO-8859-1, GIF-Banner, 12-px-Text, keine Responsive-Darstellung, externes Cookie-Plugin (valao.de), YouTube-Einbettung, viele Unterseiten mit kleinen Bildergalerien.

## Redesign
Ein Onepager (Hero, Leistungen, Referenzen mit Vorher/Nachher-Reglern, Ablauf, Über uns, Kontakt), mobil zuerst. Farben aus dem Logo (Lindgrün #89BD38, Fast-Schwarz #1C1C1A) plus Olivgrün #3A5017 für Text auf Hell. Schriften Fraunces und Inter (OFL, selbst gehostet, Latin-Subset). Alle Bilder als WebP. Animationen nur transform/opacity, `prefers-reduced-motion` respektiert.

## Messung (Lighthouse 12, mobil, gedrosselt Slow 4G + 4x CPU, Live-Variante ohne Demo-Leiste und ohne noindex)
Performance 100 · Barrierefreiheit 100 · Best Practices 100 · SEO 100 · FCP 1,1 s · LCP 1,1 s · CLS 0,032 · TBT 10–20 ms. Seitengewicht initial ca. 250 KB. Labordaten, kein Feldwert. Die Demo selbst zeigt wegen `noindex` und Platzhalter-Canonical SEO 58 (gewollt).

## Offen vor einer Veröffentlichung (Kunde klären)
1. **Bildrechte:** Fotos Jägerstraße (Roman Thomas, Celle; Architektur bussemas architekten, Lage) und alle Referenzfotos: Nutzungsrecht und Einwilligung der Eigentümer prüfen, Kfz-Kennzeichen und Personen unkenntlich halten. Das Foto der Zimmerer in Tracht: Urheber/Herkunft klären.
2. **Angaben bestätigen:** „Seit 2002“, „über 40 Mitarbeiter“, „Meisterbetrieb“, Einzugsgebiet, Titel der Vorher/Nachher-Beispiele.
3. **Logo als Vektor (SVG)** anfordern. Aktuell nur ein 760-px-GIF, die Unterzeile ist darin klein.
4. **Rechtstexte** (Impressum, Datenschutz, AGB) liefert der Kunde. Die Platzhalterseiten enthalten nur die Angaben der alten Seite. Anschrift, Register, USt-IdNr. vom Kunden.
5. **Öffnungs-/Erreichbarkeitszeiten** und Antwortzeit-Zusage nur nach Kundenangabe.
6. **Nicht übernommen:** Heißluftballon-Team (eigener Geschäftsbereich, Entscheidung offen), Stellenanzeige, Sponsoring-Aktionen (Rudern gegen Krebs, Wasa-Lauf, veraltet, Personenfotos), Partnerfirmen-Liste, YouTube-Video (wäre nur per Zwei-Klick-Lösung zulässig), Fotogalerie mit rund 70 Bildern (Galerie-Seite wäre ein nächster Ausbauschritt).
7. **Weiterleitungen:** Bei Relaunch alte URLs (z. B. `/leistungen/fachwerk.html`) per 301 auf die neuen Abschnitte/Seiten leiten.
8. Formular anbinden (Zustellung beim Kunden, SPF/DKIM prüfen), Domain/DNS laut Anlage „Domain und Technik“.
