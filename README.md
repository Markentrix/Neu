# Pizzeria Molise Celle

Statische Website für das Markentrix-Portal. Abgabeordner: `website-fertig/` (index.html direkt darin, ohne Build-Skripte).

    node layouts/restaurant/build.js    # baut website-fertig/ neu

- `DESIGN.md`: Design-Richtung (Kernidee, Farben, Schriften, Signatur, Prüfung gegen die Verboten-Liste)
- `layouts/restaurant/config.json`: Inhalte (Zeiten, Karte, FAQ, SEO-Texte). `base` leer lassen, solange die Domain nicht feststeht
- Reservierung: Variante B (Website-API des Portals): `/api/verfuegbarkeit`, `/api/slots`, `/api/anfrage` (typ "termin")
- Schriften und Bilder liegen lokal (woff2, webp); keine Fremd-Dienste, kein Cookie-Banner, kein eigenes Analytics
- Statistik/Einwilligung: `<span data-mk="cookies">` im Footer, das Portal fügt das Skript beim Upload ein

## OFFEN
- Hausnummer (Quellen: Piltzergasse 1 oder 4-5), bestätigte Öffnungszeiten, Preise (Stand März 2024)
- Betreiber, Anschrift, E-Mail, USt-ID/Steuernummer für Impressum und Datenschutz (Entwürfe mit eckigen Klammern)
- Hoster-Angaben und Löschfrist für die Datenschutzerklärung
- Echte Fotos (Essen, Fenster, Gastraum, Team), Logo; aktuell KI-Platzhalter und zwei Illustrationen (fenster, raum)
- WhatsApp-Nummer prüfen (aktuell die Festnetznummer)
- Domain: nach Festlegung `base` in config.json setzen (Canonical, Sitemap, strukturierte Daten)
- Google-Bewertungen: erst nach Freischaltung im Portal als `<div data-mk="bewertungen">` einbauen, keine erfundenen Zitate
