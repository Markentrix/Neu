# Pizzeria Molise Celle

Statische Website im Restaurant-Layout (Essen und schlanke Reservierung im Vordergrund).

    node layouts/restaurant/build.js    # baut die komplette Seite nach site/

- Inhalte: `layouts/restaurant/config.json` (Name, Adresse, Zeiten, Karte, FAQ, SEO-Texte)
- Design: `layouts/restaurant/style.css`, Verhalten: `layouts/restaurant/app.js`
- Bilder: `site/assets/img/<name>.webp` plus `<name>-480.webp` und `<name>-720.webp` (für Handys)
- Deployment: Netlify, Publish-Verzeichnis `site/` (siehe `netlify.toml`), Header und Weiterleitungen in `site/_headers` und `site/_redirects` (werden vom Build erzeugt)
- Reservierung: Netlify Forms. Nach dem ersten Deploy unter *Forms → Notifications* eine E-Mail-Benachrichtigung einrichten.

## Vor dem Livegang (Startcheckliste)
1. **Domain:** `base` in `config.json` anpassen, neu bauen (Canonical, Sitemap, Strukturierte Daten).
2. **Betreiberangaben:** Hausnummer (Quellen widersprechen sich: 1 oder 4–5), Öffnungszeiten, Preise, WhatsApp-Nummer prüfen.
3. **Rechtliches:** `impressum.html` und `datenschutz.html` sind Entwürfe mit Platzhaltern in eckigen Klammern; ausfüllen und rechtlich prüfen lassen.
4. **Bilder:** Die Speisefotos sind KI-generierte Platzhalter. Eigene Fotos mit gleichen Dateinamen ersetzen (3:2, 960 × 640 und die beiden kleinen Größen). `fenster.svg` und `raum.svg` sind Illustrationen.
5. **Formular testen:** Einmal live abschicken, Benachrichtigung prüfen.
6. **Google:** Website und Reservierungslink im Google-Unternehmensprofil eintragen, Sitemap in der Search Console einreichen.
