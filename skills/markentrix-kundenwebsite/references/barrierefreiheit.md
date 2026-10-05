# Barrierefreiheit – WCAG 2.2 AA Umsetzung

Standard: WCAG 2.2 Level AA, Ziel Lighthouse A11y 100 plus manueller Test (automatische Tools finden nur ca. 30–40 % der Probleme).

## Struktur & Semantik
- `<html lang="de">`, bei fremdsprachigen Passagen `lang` am Element.
- Genau ein `<h1>`, Überschriftenhierarchie ohne Sprünge, Überschriften beschreiben Inhalt (nicht für Optik missbrauchen).
- Landmarks: `header`, `nav` (mit `aria-label` bei mehreren), `main`, `footer`. Skip-Link „Zum Inhalt springen“ als erstes fokussierbares Element.
- Listen als `ul/ol`, Tabellen nur für Daten mit `th scope`.
- ARIA nur wenn natives HTML nicht reicht. Erste Regel: kein ARIA ist besser als falsches ARIA. Button = `<button>`, Link = `<a href>`.

## Wahrnehmbar
- Kontrast: Text ≥ 4.5:1, großer Text (≥ 24 px oder ≥ 18.66 px fett) und UI-Komponenten/Grafiken ≥ 3:1. Zustände (Fokus, Hover, Disabled-Hinweis) ebenso. Cyan auf Weiß fällt durch, siehe SKILL Abschnitt 3.
- Information nie nur über Farbe.
- Text bis 200 % skalierbar ohne Verlust, Reflow bei 320 px ohne horizontales Scrollen (400 % Zoom), Textabstand überschreibbar (kein fixes Höhen-Clipping).
- Bilder: informativ `alt` kurz und konkret, dekorativ `alt=""`, Funktionsbilder (Logo-Link) beschreiben Ziel. Text nicht in Bildern. SVG mit `<title>`/`role="img"` oder `aria-hidden="true"` wenn dekorativ.
- Video: Untertitel, ggf. Transkript, kein Autoplay mit Ton, Autoplay-Stummvideo > 5 s mit Pause-Button. Audio-Inhalte mit Transkript.

## Bedienbar
- Alles per Tastatur erreichbar und bedienbar, logische Fokusreihenfolge = visuelle Reihenfolge, keine Tastaturfalle.
- Sichtbarer Fokus mit `:focus-visible`: mind. 2 px Outline, Kontrast ≥ 3:1, nicht vom sticky Header verdeckt (`scroll-margin-top`/`scroll-padding-top`).
- Zielgröße ≥ 24×24 CSS-px (WCAG 2.2), Ziel 44×44 auf Touch. Abstand zwischen Zielen.
- Dragging nicht als einzige Bedienung (2.5.7), alternative per Klick.
- Menü/Dialog/Accordion: Fokus beim Öffnen in den Dialog, `Escape` schließt, Fokus kehrt zurück, `aria-expanded`, `aria-controls`. Modale Dialoge mit `<dialog>` und `showModal()`.
- Keine zeitlichen Limits ohne Verlängerung, kein Auto-Rotating-Carousel ohne Pause (besser: kein Carousel).
- Bewegung: `prefers-reduced-motion` (siehe animation.md), nichts blinkt > 3×/s.
- Linktexte aussagekräftig („Marketing-Check anfragen“, nicht „hier klicken“), identische Links gleiches Ziel, Link-Ziel `target=_blank` nur mit Hinweis und `rel="noopener"`.
- Hilfe konsistent platziert (3.2.6), keine erneute Dateneingabe derselben Infos im Ablauf (3.3.7), Authentifizierung ohne kognitiven Test (3.3.8).

## Verständlich
- Klare Sprache (Ziel ca. B1–B2), kurze Sätze, Fachbegriffe erklären. Optional Seite „Leichte Sprache“ bei passenden Kundenprojekten.
- Formulare: sichtbares `<label for>`, Pflichtfelder markiert (Text, nicht nur `*`; `required` + `aria-required` nicht doppelt nötig), `autocomplete` (name, email, tel, organization), Eingabehinweise vor dem Feld. Fehler: Text neben dem Feld, mit `aria-describedby` verknüpft, Fehlerzusammenfassung oben mit Fokus, `aria-invalid="true"`. Fehlermeldung nennt Fix („Bitte E-Mail im Format name@firma.de eingeben“).
- Statusmeldungen (Erfolg, Laden) per `role="status"`/`aria-live="polite"`, Fehler `role="alert"`.

## Robust
- Valides HTML (W3C Validator), eindeutige IDs, korrekte Namen/Rollen/Werte für eigene Widgets.
- Funktioniert ohne JS in Grundfunktion.

## Cookie-Banner & Overlays
Tastatur-erreichbar, Fokus-Management, Rolle `dialog` mit Label, verdeckt keine Pflichtinhalte, kein Fokus-Trap beim nicht-modalen Banner.

## Testplan (Pflicht vor Livegang)
1. Lighthouse A11y + axe DevTools: 0 Fehler.
2. Tastatur: Tab/Shift+Tab/Enter/Space/Escape durch die ganze Seite, Fokus immer sichtbar.
3. Screenreader-Stichprobe: NVDA (Windows/Firefox) oder VoiceOver (Mac/Safari): Überschriftenliste, Landmarks, Formular ausfüllen.
4. Zoom 200 % und 400 %, 320 px Breite, Textabstand-Bookmarklet.
5. Kontrast-Check aller Farbpaare (WebAIM Contrast Checker), auch Hover/Fokus/Dark-Flächen.
6. `prefers-reduced-motion: reduce` und `prefers-contrast: more` testen.
7. Ergebnis im Hand-off; bei BFSG-Pflicht Barrierefreiheitserklärung mit Prüfdatum und Feedback-Kontakt.
