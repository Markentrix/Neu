# Änderungsprotokoll · 05.10.2026

Alle Änderungen in `dist/`. Layout, Design-System, Farben, Schriften, Dark Mode, Bedienhilfen-Leiste, Einwilligungsbanner und Skip-Link unverändert.

## Änderungsliste

### Startseite (dist/index.html)
- Head: `meta keywords`, `geo.region`, `geo.placename`, `geo.position`, `ICBM` entfernt. Preload für Space Grotesk 700 und Inter 400.
- H1: "Mehr Anfragen. Weniger Routine. Ein System." → "KI-Agentur in Celle: Website und KI-Assistent für Ihren Betrieb". Alte Zeile ist jetzt Unterzeile.
- Hero-Text: ergänzt "Persönliche Rückmeldung erfolgt werktags." Kennzahl "KI aktiv" → "KI nimmt Anfragen an".
- "Anfragen 24/7 annehmen" → "rund um die Uhr annehmen". Block "Erreichbar: Auch abends, am Wochenende und an Feiertagen." → "Anfragen-Annahme: Die KI nimmt Anfragen rund um die Uhr an, persönliche Rückmeldung werktags."
- "Immer eine echte Person erreichbar" → "Ein fester Ansprechpartner" (auch ueber-uns.html).
- "DSGVO-konform & sicher" → "Datenschutz mit AVV und dokumentierter Verarbeitung".
- Formular-Popup: Datenschutz-Satz verlinkt jetzt auf /datenschutz.
- Technologien-Laufband: Markennamen und Logos entfernt, neutrale Begriffe, nur ein Element-Set (kein doppeltes DOM), Animation aus bei prefers-reduced-motion.
- Neuer Abschnitt "Aktuelles Projekt" (Pony Club Lila) nach den Anwendungsszenarien, Link mit rel="noopener" im neuen Tab.
- Weitere Infos/Footer: Städteliste, Fließtext-Absatz, versteckter Städte-Absatz und Spalte "Regionen" entfernt; Regionenlinks entfernt. Satz "Sitz in Celle, Projekte bundesweit, komplett remote möglich."
- Öffnungszeiten im Footer: "Mo–Do 09:00–17:00 Uhr, Fr 09:00–15:00 Uhr" (ebenso Kontaktseite und Footer der Unterseiten mit großem Footer).
- Slogan vereinheitlicht: "Automatisierung · Werbung · Wachstum" (Footer-Zeile), zweiter Slogan "Wachstum. Automatisiert." entfernt.
- FAQ in Hauptnavigation (alle Seiten mit Navigation).
- "Marketing-Check" → "Potenzial-Check" auf allen Seiten.
- Bild Christian Wien: width/height gesetzt.

### Strukturierte Daten
- Startseite: Typ Organization + LocalBusiness + ProfessionalService, Öffnungszeiten (Mo–Do 09:00–17:00, Fr 09:00–15:00), sameAs um Google-Bewertungslink ergänzt, Slogan, knowsAbout bereinigt, Breadcrumb auf Startseite.
- Alle Unterseiten: WebPage + BreadcrumbList; FAQ: FAQPage (12 Fragen); Leistungsseiten: Service. Fehlende Canonicals (Impressum, AGB, Datenschutz) ergänzt.
- Blog: Article, Person (Autor), Organization, FAQPage, BreadcrumbList je Artikel; Blog + BreadcrumbList auf der Übersicht.

### Referenzen
- Hotlink auf ponyclublila.de entfernt; neutrale Karte mit Projektname, Branche, Ort und Link. Auskommentierter Bild-Slot (WebP, 1200×628, Alt-Text). Auskommentierte Fallstudien-Vorlage.

### Blog
- Pro Artikel: Autorenbox, Veröffentlicht/Aktualisiert, Inhaltsverzeichnis, Praxisbeispiel, Inline-FAQ, Quellenliste.
- Übersicht: Kategorienfilter (Alle, SEO/GEO, Website, KI-Automatisierung) mit `assets/blog.js`.
- KI-Markennamen aus dem SEO/GEO-Artikel entfernt.

### Rechtliches
- Datenschutz: Abschnitt "4b Entgeltliche Weitergabe an Vertriebspartner" gelöscht; Halbsatz in Abschnitt 4 gestrichen; Stand "5. Oktober 2026". Abschnitt 4a Kundenportal unverändert.
- Kontakt: Partner-Checkbox, Partnerliste, Anker #partner und `partnerConsent` im Skript entfernt.
- AGB: Absatz (5) zu Lead-Erwerb durch Vertriebspartner entfernt.
- Impressum: USt-IdNr. als Kommentarblock vorbereitet, nichts Sichtbares geändert.

### Barrierefreiheit/Technik
- Kontaktformular: Labels mit Feldern verknüpft (for/id). Bildmaße ergänzt (prozess, ueber-uns).
- Sicherheits-Header: nur Vorschlag in `SICHERHEITS-HEADER-VORSCHLAG.md`.

## Offene TODOs (nur als Code-Kommentar)
1. Pony-Club-Lila-Screenshot als lokales WebP: `dist/referenzen.html`, Kommentar "TODO: lokales Projektbild" im Projektkasten.
2. USt-IdNr.: `dist/impressum.html`, Kommentar nach der Anschrift in Abschnitt "Angaben gemäß § 5 DDG".
3. Fallstudien-Kennzahlen und Zitat: `dist/referenzen.html`, Kommentar "Vorlage für spätere Fallstudien" vor "Beispielrechnung".
4. Portal-Domain: Link "Kunden-Login" (markentrix.netlify.app) in jeder Navigation und im Startseiten-Footer; Datenschutz Abschnitt 4a. Kein Kommentar gesetzt, da Link und Abschnitt unverändert bleiben sollten.

## Nicht ohne Sie entschieden
- **Abschnitt-Nummer:** Der Partner-Abschnitt hieß im Dokument "4b" (intern `s4c`), nicht 4a. Gelöscht wurde dieser; "4a Kundenportal" bleibt, Nummerierung ist lückenlos.
- **Regionenseiten** (Celle, Hannover, Gifhorn, Braunschweig): vollständig neu geschrieben mit eigenem Aufbau, Einzugsgebiet, Beispielszenario (fiktiv) und eigener FAQ je Stadt. Gleiche Navigation, Footer und Skripte wie die übrigen Unterseiten. Links auf Startseite und im Footer wieder aufgenommen. Bitte prüfen: Aussage "Termin vor Ort nach Absprache" (Hannover, Braunschweig) und die genannten Stadtteile/Orte.
- **Lead-Quelle:** `quelle: 'Marketing-Check Modal'` im Webhook heißt jetzt "Potenzial-Check Modal". Falls n8n danach filtert, anpassen.
- **Weitere "DSGVO-konform"-Aussagen** auf Leistungs-, Regionen- und Datenschutz-Meta-Seiten blieben unverändert.
- **Anbieter-/Plattformnamen** wie Meta, Google (Ads, Unternehmensprofil), WhatsApp stehen weiter als Leistungs- bzw. Kanalbezeichnung. Auch Social-Links (Facebook, Instagram, LinkedIn) im JSON-LD sind unverifiziert übernommen.
- **Bilder in WebP/AVIF:** konnte hier nicht erzeugt werden; Konvertierung von `christian-wien-480.jpg` und `ki-agent-dashboard-1600.jpg` offen.
- **PageSpeed/Lighthouse/axe-Ziele:** nicht gemessen. Nach Deployment mit PageSpeed Insights und axe prüfen.
- **Quellenlinks im Blog** (Google, web.dev, Gesetze, schema.org, llmstxt.org) bitte einmal im Browser prüfen.
- **Quelldatei `Markentrix Website.dc.html`** ist nicht mit `dist/index.html` synchron; `dist/` ist maßgeblich.

## Audit 05.10.2026 (SEO/GEO, Struktur, Links)
- Titel einzeln, ≤ 62 Zeichen, mit Thema statt nur Seitenname. Meta-Descriptions ≤ 165 Zeichen, eindeutig. og:title/og:description entsprechen Titel/Description auf allen indexierbaren Seiten; fehlende OG-/Twitter-Tags auf Unterseiten ergänzt.
- Genau eine H1 pro Seite; keine übersprungenen Überschriftsebenen mehr (Footer-Spaltenüberschriften sind jetzt Ebene 2 statt h4).
- H1 angepasst: Über uns ("Markentrix: KI-Agentur aus Celle."), FAQ, Referenzen ("Referenzen und Projekte."), KI-Automatisierung ("… Auch außerhalb der Geschäftszeiten.").
- Canonical auf allen Seiten korrekt (404 bewusst ohne). Alle internen Links und Anker, Skripte, Styles, Bilder aufgelöst; alle JSON-LD-Blöcke parsebar.
- Alt-Texte: alle 3 Bilder haben Alt-Text und Maße. Ein Bild-Slot in Referenzen ist als Kommentar vorbereitet.
- Impressum, AGB und Datenschutz sind indexierbar (noindex entfernt) und stehen in der Sitemap; nur die KI-Checkliste bleibt noindex. Sitemap: 22 URLs, lastmod 2026-10-05.
- Regionalseiten: "Termin vor Ort oder Online-Call" als Wahl für Kunden formuliert.
- llms.txt aktualisiert.
- Nicht prüfbar: externe Quellenlinks im Blog (kein Netzzugriff auf diese URLs).


## Nachtrag 07.10.2026
- Preise gegen Preisliste 01.10.2026 geprüft: Seite stimmt überein (keine Änderung).
- Kontrast: Violett #8B5CF6 → #7C3AED auf allen Seiten.
- H2-Überschriften ergänzt: FAQ, Kontakt (unsichtbar), Prozess (5 Schritte), Über uns (2), ROI-Rechner (2).
- Sitemap: lastmod je Seite (07.10. für geänderte, sonst 05.10.).
- Pilotangebot (2 Plätze), LANDING START bis 31.12.2026, Werbebudget-Hinweis, Leistungsseiten mit Grundlagen und Preisen.
- Offen: Portal-URL (Hetzner), USt-IdNr., CLS auf Preise und Städteseiten, Unterstreichung/Linkhöhe, testadresse noindex.
