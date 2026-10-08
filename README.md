# Pizzeria Molise Celle

Statische Website im Restaurant-Layout (Essen und schlanke Reservierung im Vordergrund).

    node layouts/restaurant/build.js    # baut die komplette Seite nach site/

- Inhalte: `layouts/restaurant/config.json` (Name, Adresse, Zeiten, Karte, FAQ, SEO-Texte)
- Design: `layouts/restaurant/style.css`, Verhalten der Reservierung: `layouts/restaurant/app.js`
- Bilder: `site/assets/img/<name>.webp` (aktuell KI-generierte Platzhalter, bitte durch echte Fotos ersetzen; gleiche Dateinamen)
- Deployment: `site/` als Publish-Verzeichnis (Netlify; Reservierung über Netlify Forms)

## Vor dem Livegang
Domain (`base` in der config), Öffnungszeiten, Adresse, Preise, WhatsApp-Nummer prüfen. Impressum und Datenschutz sind Platzhalter.
Für ein anderes Lokal: config ändern, Bilder tauschen, neu bauen.
