# SEO (Technik, lokal, strukturierte Daten)

## Technik
- Eigene `<title>` (≤ 60 Zeichen, Keyword + Marke) und Meta-Description (120–155) je Seite, ein `<h1>`, saubere URLs (klein, Bindestrich, Deutsch), `canonical`, `hreflang` nur bei mehreren Sprachen.
- `robots.txt`, `sitemap.xml`, 404-Seite, 301 für alte URLs bei Relaunch (Redirect-Map vorab!), HTTPS-only, www/non-www vereinheitlicht.
- Crawlbarer Content im HTML (kein Client-Only-Rendering), interne Verlinkung mit sprechenden Linktexten, Breadcrumbs bei Tiefe.
- Landingpages für bezahlte Ads: `noindex` nur wenn gewollt (Duplicate-Content vermeiden), sonst indexierbar.
- Open Graph/Twitter Card + 1200×630 OG-Bild je Seite. Favicon-Set (SVG + 180 px Apple-Touch + 192/512 PWA-PNG).
- Core Web Vitals sind Ranking-Signal: Budget einhalten.

## Lokales SEO (Celle/Region)
- NAP (Name, Adresse, Telefon) überall identisch, mit Google-Unternehmensprofil abgleichen.
- Seite pro Leistung + Ort, nur wenn echter Mehrwert (keine Doorway-Pages).
- `LocalBusiness`/`ProfessionalService` JSON-LD mit echten Daten (Adresse, Öffnungszeiten, `sameAs`), keine erfundenen `aggregateRating`.
- Google-Maps-Einbettung nur per Zwei-Klick/statisch (Datenschutz).

## Strukturierte Daten (JSON-LD, nur zu sichtbarem Inhalt)
Organization (Logo, Name, URL, Kontakt), WebSite, BreadcrumbList, FAQPage (nur wenn FAQ sichtbar), Service/Offer nur mit freigegebenen Preisen. Validieren im Rich-Results-Test. Nie Bewertungen markieren, die nicht real sind.

## Inhalt
Suchintention pro Seite (informativ/kommerziell), Keywords natürlich einbauen, Überschriften beantworten Fragen, Alt-Texte beschreibend, Inhalte aktuell halten (Preise/Stand prüfen), kein KI-Massencontent ohne Mehrwert und Fakten-Check.

## Standard für jede Kundenseite (erweitert nach dem Motorradhandel-Beispiel)
**Build mit zwei Modi:** Demo (noindex, Demo-Leiste) und Live (`--live`: index, follow, sitemap, robots, ohne Demo-Leiste). Platzhalter blockieren den Livegang (Prüfer meldet sie).
**Pflicht je Seite:** Title ≤ 60 Zeichen, Description 110–160, genau eine H1, absolute Self-Canonical, Open Graph + Twitter-Card mit 1200×630-Bild, sichtbare Brotkrumen und `BreadcrumbList`, eindeutige Texte (keine doppelten Titles/Descriptions), beschreibende Linktexte, Alt-Texte, Maße an Bildern.
**Strukturierte Daten** (JSON-LD als `@graph`, verknüpft per `@id`, nur Sichtbares auszeichnen): `LocalBusiness` (oder Unterart wie `MotorcycleDealer`, `HomeAndConstructionBusiness`) mit Adresse, Telefon, Einzugsgebiet, Leistungskatalog, Inhaber; `WebSite`; `WebPage`-Unterarten; `BreadcrumbList`; `ItemList` für Listen; `Product`/`Offer` für Bestand; `Service` für Leistungen; `FAQPage`; `Article` für Ratgeber. Nie erfundene Bewertungen (`aggregateRating`), Öffnungszeiten oder Koordinaten ohne Kundenangabe.
**Dateien:** `sitemap.xml` (+ Bild-Sitemap), `robots.txt`, `llms.txt`, `_redirects` mit **allen alten URLs** (301), `_headers`, 404-Seite, Danke-Seite `noindex`.
**Suchstarke Seiten aus echten Daten:** Kategorie-/Markenseiten mit mindestens zwei Einträgen und echtem Datentext (keine Dünnseiten), Ratgeber mit Datum und Freigabevermerk.
**Prüfen:** `scripts/check_seo.py <ordner> [--live] [--domain=https://kunde.de]` (Title/Description, H1, Canonical, OG, Alt, JSON-LD gültig und verknüpft, Preis im Schema = Preis auf Seite, FAQ sichtbar, Sitemap, Links/Anker, Weiterleitungsziele) plus Lighthouse mobil gedrosselt auf dem **Live-Build**.
**Ehrlich bleiben:** „100“ bezeichnet Lighthouse und Prüfer. Rankings und KI-Nennungen hängen von Wettbewerb, Bewertungen und Verlinkung ab und werden nie zugesagt.
