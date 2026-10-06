# SEO und GEO: Motorradhandel-Celle

GEO = Generative Engine Optimization: Auffindbarkeit und Zitierfähigkeit in KI-Antworten (ChatGPT, Perplexity, Google AI Overviews, Claude). Beides baut auf sauberer Technik, klaren Fakten und lokaler Autorität auf.

**Ehrliche Einordnung:** Technik, Daten und Inhalt sind geprüft und fehlerfrei umgesetzt. Platz 1 bei Google oder Nennung in jeder KI-Antwort lässt sich nicht garantieren: Das hängt von Wettbewerb, Bewertungen, Verlinkungen und Pflege ab. Dieses Dokument zeigt, was fertig ist und was nach dem Livegang noch zu tun ist.

## 1. Was umgesetzt ist (geprüft)
**Technik**
- Eigene Title (≤ 60 Zeichen) und Description (110–160) je Seite, genau eine H1, saubere Überschriften-Reihenfolge, selbstreferenzielle Canonicals (absolut), Open Graph und Twitter-Cards mit eigenem 1200×630-Bild je Fahrzeug, `lang="de"`.
- `sitemap.xml` (mit Bild-Sitemap für Fahrzeuge), `robots.txt` (Live: alles erlaubt, `danke` gesperrt, KI-Such-Bots ausdrücklich zugelassen), `_redirects` mit 301-Weiterleitungen von allen 26 alten Seiten (`Seite32.html` → neue Fahrzeugseite), `404.html`, `_headers` (Sicherheits-Header, Caching).
- Core Web Vitals im Grünen (Lighthouse mobil gedrosselt: Performance, Barrierefreiheit, Best Practices, SEO je 100; LCP 1,1–1,8 s, CLS ≤ 0,04).
- Interne Verlinkung: sichtbare Brotkrumen, Marken- und Arten-Seiten, Ratgeber, Querverweise (Überwintern ↔ Ankauf ↔ Bestand), Footer-Navigation.

**Strukturierte Daten (JSON-LD, Schema.org, miteinander verknüpft über `@id`)**
`MotorcycleDealer`/`LocalBusiness` (Adresse, Telefon, Einzugsgebiet, Leistungskatalog, Inhaber), `WebSite`, `WebPage` je Seitentyp (`CollectionPage`, `ItemPage`, `AboutPage`, `ContactPage`), `BreadcrumbList`, `ItemList` (Bestand), `Product`/`Motorcycle` mit `Offer` je Fahrzeug (Preis, Erstzulassung, Kilometerstand, gebraucht), `Service` (Winterlager, Ankauf), `FAQPage` (nur sichtbare, vollständig beantwortete Fragen), `Article` (Ratgeber).

**GEO (für KI-Antworten)**
- `llms.txt`: kompakte, faktische Beschreibung des Betriebs mit Links auf alle wichtigen Seiten und den aktuellen Bestand.
- Kurzantworten („Kurz erklärt“) am Seitenanfang, „Auf einen Blick“-Faktenblock mit Name, Ort, Inhaber, Leistungen, Kontakt und Stand des Bestands, eindeutige und konsistente Angaben (Name, Adresse, Telefon überall gleich).
- FAQ in natürlicher Frageform („Wo kann ich in Celle mein Motorrad überwintern?“), Fahrzeugseiten mit zitierfähigem Kurzsatz und Eckdatentabelle, zwei Ratgeber (Checklisten) mit Datum und Quelle.
- Mehr suchstarke Seiten: 5 Marken- und 4 Arten-Seiten mit echten Bestandsdaten, 16 Fahrzeugseiten, Winterlager-Seite.

## 2. Keyword-Zuordnung (Vorschlag, Suchvolumen mit Search Console oder Keyword-Tool prüfen)
| Seite | Hauptthema | Suchabsicht |
|---|---|---|
| Start | Motorrad kaufen Celle, Motorradhändler Celle | kaufen, Händler finden |
| Motorräder und Marken-/Arten-Seiten | gebrauchte Motorräder Celle, Honda/Kawasaki/Yamaha gebraucht Celle, Sportler/Naked Bike gebraucht | vergleichen |
| Fahrzeugseiten | Modellname + gebraucht + Celle | konkretes Fahrzeug |
| Überwintern | Motorrad überwintern Celle, Winterlager | Dienstleistung, saisonal |
| Verkaufen | Motorrad verkaufen Celle, Motorrad Ankauf, in Zahlung geben | verkaufen |
| Service | Motorrad Finanzierung, Inzahlungnahme | Konditionen |
| Ratgeber | gebrauchtes Motorrad kaufen Checkliste, Motorrad einwintern | informieren, Vertrauen |
| Kontakt | Probefahrt Motorrad Celle | Anfrage |

## 3. Vor dem Livegang (Pflicht)
1. Alle gelben Platzhalter ersetzen (Live-Build zeigt sie: `python3 build/build.py --live`, Prüfer meldet sie), besonders Gewährleistung, Zeiten, Winterlager-Konditionen, Einzugsgebiet, Ratgeber-Freigabe.
2. Schema-Angaben ergänzen, sobald vom Kunden bestätigt: Öffnungszeiten (`openingHoursSpecification`), Geokoordinaten, Logo (Datei), Profile für `sameAs` (Google-Unternehmensprofil, Facebook, Instagram, mobile.de, Kleinanzeigen).
3. Live-Ordner `live/` deployen (inkl. `_redirects`, `_headers`), DNS laut Anlage „Domain und Technik“, HTTPS und Weiterleitung `www`.
4. `python3 build/check_seo.py live --live` ohne FAIL, Lighthouse mobil auf Start, Bestand, Fahrzeug, Überwintern.

## 4. Nach dem Livegang (laufend)
- **Google Search Console** (Domain-Property per DNS-TXT) und **Bing Webmaster Tools**: Sitemap einreichen, Indexierung und Core Web Vitals beobachten, Weiterleitungen kontrollieren.
- **Google-Unternehmensprofil** (wichtigster lokaler Hebel): Kategorie „Motorradhändler“, Adresse, Telefon, Zeiten, Fotos, Leistungen, Website-Link, regelmäßige Beiträge (jetzt: Winterlager), Fragen und Antworten, Bewertungen aktiv einholen und beantworten. Dazu Bing Places und Apple Business Connect.
- **Einträge und Verlinkungen:** Branchenverzeichnisse (Das Örtliche, Gelbe Seiten, 11880), mobile.de und Kleinanzeigen-Inserate mit Link auf die Fahrzeugseite, lokale Partner. Name, Adresse, Telefon überall identisch.
- **Bestandspflege:** Verkaufte Fahrzeuge entfernen oder als „verkauft“ kennzeichnen, neue Fahrzeuge zeitnah aufnehmen, Stand-Datum aktualisieren (steht in Seite, Schema und `llms.txt`). Veralteter Bestand schadet Ranking und KI-Zitaten.
- **Inhalte:** je Quartal 1 neuer Ratgeber oder Saisonthema (Saisonstart, HU-Termin, Winter-Check), Winterkampagne im Frühjahr abschalten.
- **KI-Sichtbarkeit messen:** einmal im Monat dieselben Fragen in ChatGPT, Perplexity, Google (AI-Übersicht) und Claude stellen und notieren, ob Motorradhandel-Celle genannt oder verlinkt wird:
  1. Wo kann ich in Celle mein Motorrad überwintern?
  2. Welcher Motorradhändler in Celle verkauft gebrauchte Motorräder?
  3. Wo kann ich in Celle mein Motorrad verkaufen oder in Zahlung geben?
  4. Gebrauchte Kawasaki Z 1000 in Celle kaufen
  5. Motorradhandel Celle Altenhagen Öffnungszeiten und Adresse
  6. Worauf achte ich beim Kauf eines gebrauchten Motorrads vom Händler?
  7. Gibt es in der Region Celle einen Händler mit Motorrad-Winterlager?
- **KI-Crawler:** `robots.txt` erlaubt Such- und Antwort-Bots. Wer nicht möchte, dass Inhalte zum Training genutzt werden, sperrt `GPTBot`, `Google-Extended`, `CCBot` (Entscheidung des Inhabers).

## 5. Was nicht in unserer Hand liegt
Rankingpositionen, Bewertungsanzahl, fremde Verlinkungen und ob eine KI den Betrieb nennt. Wir schaffen die beste technische und inhaltliche Grundlage und zeigen mit den Testfragen, wo es steht.
