# Build-Werkzeuge (nicht Teil der Abgabe)

Die fertige, statische Website liegt in `website-fertig/` und wird so hochgeladen.

- `build/build.py` erzeugt alle HTML-Seiten in `website-fertig/` neu (Python 3, keine Abhängigkeiten):
  `python3 tools/build/build.py`
- `mock-portal.py` startet einen lokalen Testserver, der `website-fertig/` ausliefert und die Portal-API
  (`/api/verfuegbarkeit`, `/api/slots`, `/api/anfrage`, `/api/e`) simuliert:
  `python3 tools/mock-portal.py ok 8765` (oder `down` für den Offline-Fall)
- `test-mobile.js` prüft mit Playwright alle Seiten bei 390 px Breite und spielt die Buchung durch:
  `node tools/test-mobile.js http://127.0.0.1:8765 /tmp/shots`
- `js/` enthält die lesbaren Skripte; `website-fertig/assets/js/` bekommt die mit terser minifizierten Fassungen:
  `npx terser@5.31.0 tools/js/main.js -c -m -o website-fertig/assets/js/main.js --comments false` (ebenso buchen.js)
- `mock-portal-gzip.py` ist der Testserver mit gzip wie bei einem echten Hoster (für Lighthouse-Messungen).
- Demo-Version mit Markentrix-Wasserzeichen, noindex und gesperrter robots.txt (zum Zeigen beim Kunden):
  `DEMO=1 python3 tools/build/build.py` erzeugt `website-demo/`; ZIP: `cd website-demo && zip -r -X ../celler-kartbahn-demo.zip . -x ".*"`
- `css/style.css` ist die CSS-Quelle; sie wird beim Build minifiziert in jede Seite eingebettet (keine separate CSS-Datei im Upload).
