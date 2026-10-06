# Pizzeria Molise Celle

Statische Landingpage. Quellen in `src/` und `build.js`, Ausgabe in `site/`.

    node build.js     # baut site/ neu (CSS wird inline eingebettet)

Deployment: `site/` als Publish-Verzeichnis (Netlify; das Reservierungsformular nutzt Netlify Forms).
Vor dem Livegang: Domain in `build.js` (BASE), Öffnungszeiten, Adresse, Preise, Impressum und Datenschutz prüfen.
