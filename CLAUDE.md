# markentrix.de (statische Website, Generator `tools/build.py`)

Vor jeder Änderung an Seiten, Skripten oder Texten gilt `docs/QUALITAETSREGELN.md`. Kurzfassung:

- Bauen: `python3 tools/build.py`. Gate vor jedem Paket: `python3 tools/qa.py` muss „0 Fehler“ melden. Paket: `tools/paket.sh <Ordner>` (läuft das Gate selbst).
- Browser-Tests in `tools/browser_tests/` (axe, Einwilligung, Tracking, Formulare), wenn Skripte, Formulare, Einwilligung oder Layout betroffen sind.
- Jede Änderung in `docs/PRUEFBERICHT.md` nachtragen: was geändert, was geprüft, was **nicht** geprüft ist. Nie „rechtssicher“ oder „perfekt“ zusagen.
- Marke (Markenhandbuch 3.1): Farben Salz #F4F6F7, Reif #E0E6E9, Tiefsee #0C2128, Pfauenblau #045268, Kupfer #C67432 (Kupfer als Text nur ab 24 px), Nebentext #465A62. Schriften Archivo (Überschriften) und Source Sans 3 (Text), lokal.
- H1: Suchbegriff zuerst, höchstens 70 Zeichen, Unterzeile als eigener Absatz. Karten verlinken nur die Überschrift. Einwilligung nur über `window.mxConsent`.
- Texte nie erfinden (Betriebsdaten, Fristen, Kennzahlen, Verträge). Offenes als „OFFEN“ in die Doku, nicht in die Seite.
- Nichts installieren oder an Dritte senden, ohne es zu benennen.
