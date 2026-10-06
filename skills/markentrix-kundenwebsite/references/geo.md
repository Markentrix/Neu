# GEO: Generative Engine Optimization (Auffindbarkeit in KI-Antworten)

Ziel: Kunden-Websites werden von ChatGPT, Perplexity, Google AI Overviews und Claude **verstanden, korrekt wiedergegeben und zitiert**. Grundlage ist klassisches SEO, dazu kommen Klarheit, Fakten und Autorität.

## Bausteine
1. **Eindeutige Entität:** Name, Adresse, Telefon, Inhaber, Leistungen, Einzugsgebiet überall identisch (Seite, Impressum, Schema, Google-Unternehmensprofil, Verzeichnisse). Schreibvarianten des Namens als `alternateName`.
2. **Kurzantwort am Seitenanfang:** ein bis zwei Sätze, die die Frage der Seite vollständig und ohne Marketing beantworten („Kurz erklärt“). KI-Systeme zitieren solche Passagen.
3. **Faktenblock „Auf einen Blick“:** Name, Art, Standort, Inhaber, Angebot, Leistungen, Kontakt, Stand/Datum. Als Definitionsliste (`dl`), maschinenlesbar und schnell erfassbar.
4. **FAQ in natürlicher Frageform,** wie Menschen KI fragen („Wo kann ich in Celle mein Motorrad überwintern?“). Antworten kurz, vollständig, mit Ortsbezug. Dieselben Fragen als `FAQPage` (nur wenn Antwort sichtbar und ohne Platzhalter).
5. **Tabellen und Listen** für Eckdaten (Spezifikationen, Preise, Ablauf), saubere Überschriften als Fragen/Themen, ein Thema pro Abschnitt.
6. **`llms.txt`** im Root: Kurzbeschreibung, Kontakt, wichtigste Seiten, aktuelle Datensätze (z. B. Bestand mit Preis). Aktuell halten, Stand-Datum nennen. Kein Ersatz für gutes HTML, sondern Ergänzung.
7. **Belegbare Autorität (E-E-A-T):** echte Inhaber-/Teamangaben, Gründungs- und Erfahrungsfakten vom Kunden, Impressum, Bewertungen nur echt (Google-Profil), Ratgeber mit Datum und Freigabe durch den Fachmann. Keine erfundenen Zahlen oder Zitate.
8. **Frische:** sichtbares Aktualisierungsdatum, `dateModified`, Sitemap-`lastmod`, Bestands-/Preispflege. Veraltete Daten führen zu falschen KI-Antworten.
9. **Zugang für KI-Crawler:** `robots.txt` erlaubt Such- und Antwort-Bots (OAI-SearchBot, ChatGPT-User, PerplexityBot, Claude-SearchBot). Training (GPTBot, Google-Extended, CCBot) ist eine Entscheidung des Inhabers, im Hand-off ansprechen.
10. **Externe Signale:** Google-Unternehmensprofil, Bing Places, Apple Business Connect, Branchenverzeichnisse, Fachportale, lokale Erwähnungen. KI-Antworten stützen sich stark auf mehrere übereinstimmende Quellen.

## Messen
Monatlich 5–10 feste Testfragen in ChatGPT, Perplexity, Google und Claude stellen (Beispiele: `demos/motorradhandel-celle/SEO-GEO.md`), Nennung und Verlinkung notieren, Abweichungen (falsche Preise, Zeiten, Adresse) an der Quelle korrigieren. Dazu Search Console (Impressionen, Klicks, Abfragen).

## Grenzen
Keine Garantie auf Nennung. Keine versteckten Texte, kein Keyword-Stuffing, keine Aussagen nur für Maschinen, die Besucher nicht sehen (nur sichtbare Inhalte auszeichnen).
