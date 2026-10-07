# Pizzeria Molise Celle

Statische Landingpage. Quellen in `src/` und `build.js`, Ausgabe in `site/`.

    node build.js     # baut site/ neu (CSS wird inline eingebettet)

Deployment: `site/` als Publish-Verzeichnis (Netlify; das Reservierungsformular nutzt Netlify Forms).
Vor dem Livegang: Domain in `build.js` (BASE), Öffnungszeiten, Adresse, Preise, Impressum und Datenschutz prüfen.

## Restaurant-Layout (Essen und Reservierung im Vordergrund)

    node layouts/restaurant/build.js   # baut site/gastro.html

Alle Inhalte stehen in `layouts/restaurant/config.json` (Name, Adresse, Zeiten, Gerichte, Karte, FAQ).
Für andere Lokale: config ändern, Bilder in `site/assets/img/` ersetzen (Namen im Feld `img`), `indexable` auf `true` setzen.
Reservierung: Tag, Uhrzeit und Personen per Klick, Sonntag/Ruhetag und vergangene Zeiten gesperrt, Versand über Netlify Forms.
