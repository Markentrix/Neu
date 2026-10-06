# Italia Camper 24 – Shop-Redesign (Tricolore)

Statischer Multi-Page-Shop mit dem **kompletten Sortiment** von italiacamper24.de (338 Produktseiten, 46 Ersatzteile, 16 Kategorien),
Fahrzeugfinder (8 Basisfahrzeuge × Baureihen, 32 Wohnmobil-Hersteller), Warenkorb/Kasse (Demo), Ratgeber, Bewertungen, Rechtstexte.

    python3 src/build.py                      # baut site/ neu (Sitemap, JSON-LD, llms.txt, Suchindex)
    python3 tools/extract.py <crawl>          # liest gecrawlte Originalseiten aus
    python3 tools/normalize.py <crawl>        # -> src/catalog.json (Kategorien, Fahrzeug-Zuordnung)
    python3 tools/fetch_images.py             # lädt/komprimiert Produktbilder (WebP)

Offen für den Live-Betrieb: Anbindung von Kasse/Zahlung an ein Shop-System, Prüfung der automatischen Fahrzeug-Zuordnung (Baureihen) durch den Betreiber.
