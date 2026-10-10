# PS Schneider – Website-Redesign

Neue Website für Patric Schneider, Sachverständiger für Fahrzeugtechnik in Celle
(Redesign von https://psschneider.de).

## Struktur

| Datei | Inhalt |
| --- | --- |
| `index.html` | Startseite mit allen Inhalten: Leistungen, Vergleich Gutachten/Kostenvoranschlag, Über mich, Unfall-Checkliste, FAQ, Kontakt |
| `impressum.html` | Impressum (offene Felder gelb markiert) |
| `datenschutz.html` | Datenschutzerklärung (offene Felder gelb markiert) |
| `assets/site.css` | Design-Tokens, Layout, Light/Dark Mode |
| `assets/fonts/` | Selbst gehostete Schriften (Barlow, Barlow Condensed, IBM Plex Mono), keine Google-Server |
| `assets/portrait.jpg` | Porträtfoto |
| `assets/logo.png`, `assets/logo-dark.png` | Logo mit transparentem Hintergrund, helle Variante für dunkle Flächen |

## Betrieb

Reine statische Seite ohne Build-Schritt. Alle Dateien auf den Webserver kopieren, fertig.
Keine Cookies, kein Tracking, keine externen Einbindungen; deshalb ist kein Cookie-Banner nötig.

Das Kontaktformular öffnet das E-Mail-Programm des Besuchers mit fertigem Text (`mailto:`).
Soll die Anfrage serverseitig verschickt werden, muss die `action` des Formulars auf ein
Formular-Skript des Hosters oder einen Dienst wie Formspree zeigen.

## Vor Veröffentlichung ausfüllen

- `impressum.html`: USt-ID, W-IdNr., Handwerkskammer
- `datenschutz.html`: Hosting-Anbieter, eingesetzte Kalkulationssysteme
- Adresse prüfen: Startseite sagt „Im Röthel 43“, altes Impressum „Am Röthel 43“
