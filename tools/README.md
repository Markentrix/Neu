# Build-Werkzeuge (nicht Teil der Abgabe)

Die fertige, statische Website liegt in `website-fertig/` und wird so hochgeladen.

- `build/build.py` erzeugt alle HTML-Seiten in `website-fertig/` neu (Python 3, keine Abhängigkeiten):
  `python3 tools/build/build.py`
- `mock-portal.py` startet einen lokalen Testserver, der `website-fertig/` ausliefert und die Portal-API
  (`/api/verfuegbarkeit`, `/api/slots`, `/api/anfrage`, `/api/e`) simuliert:
  `python3 tools/mock-portal.py ok 8765` (oder `down` für den Offline-Fall)
- `test-mobile.js` prüft mit Playwright alle Seiten bei 390 px Breite und spielt die Buchung durch:
  `node tools/test-mobile.js http://127.0.0.1:8765 /tmp/shots`
