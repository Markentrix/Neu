# Website ins Markentrix-Portal hochladen

Die Website ist rein statisch. Es gibt keinen eigenen Server, keine Datenbank und kein Docker. Formulare, Termine, Bewertungen, Statistik und Cookie-Hinweis kommen vom Markentrix-Portal.

## Bauen und hochladen

```bash
pip install -r requirements.txt     # einmalig (Pillow für die Bilder)
python3 build/build.py              # erzeugt website-fertig/ mit index.html direkt darin
cd website-fertig && zip -r ../website-fertig.zip . && cd ..
```

`website-fertig.zip` im Markentrix-Portal beim Kunden ElbDetail hochladen. Das Portal-Skript setzt der Upload selbst ein, es steht absichtlich nicht in der Website.

## Was die Website vom Portal nutzt

| Funktion | Weg | Wo |
|---|---|---|
| Kontakt-, Termin-, Gutschein-, Firmen- und Widerrufsformular | eigene Oberfläche, `POST /api/anfrage` (typ `kontakt`, `termin`, `gutschein`, `firma`, `widerruf`) | alle Formulare |
| Freie Tage und nächster freier Termin | `GET /api/verfuegbarkeit` | Startseite, Buchung |
| Freie Uhrzeiten | `GET /api/slots?tag=…` | Buchung, Schritt 4 |
| Direkt buchen oder Terminwunsch | `selfBooking` aus `/api/verfuegbarkeit` schaltet die Texte um | Buchung |
| Besucherzahlen ohne Cookies | `POST /api/e` | alle Seiten |
| Google-Bewertungen | Baustein `<div data-mk="bewertungen">` | Startseite, Abschnitt Bewertungen |
| Cookie-Hinweis und Statistik-Einstellungen | Baustein `<span data-mk="cookies">` | Fußbereich jeder Seite |
| Fotos vom Fahrzeug | `GET /api/foto` (nur bei `aktiv` sichtbar, `max`, `hinweis` mit Löschfrist), Upload je Foto per `POST /api/foto` (im Browser auf 1600 px verkleinert), Tokens im Feld `fotos` bei `/api/anfrage` | Kontaktformular, Buchung Schritt 2 |
| Anzahlung | PayPal.me-Name aus `/api/verfuegbarkeit` (Feld `paypalMe`), Link mit Betrag; leer = kein Zahlungslink | Buchung, Danke-Seite |

Pakete, Preise, Fahrzeugklassen und Zustandszuschläge kennt nur die Website. Das Portal speichert sie als Text in der Anfrage. `/api/leistungen` und `/api/mitarbeiter` braucht ElbDetail nicht, weil nur René bucht.

Ist die Schnittstelle nicht erreichbar, zeigen die Formulare WhatsApp, E-Mail und Telefon als Ausweg.

## Inhalte ändern

Alle Texte, Preise und Bilder liegen in `content/` (JSON und Markdown). Ändern, neu bauen, hochladen. Zeitlich begrenzte Angebote in `content/angebote.json` blenden sich am Ablaufdatum selbst aus. Aktionspreise in `content/pricing.json` (Winterangebot, Scheiben-Aktion) verschwinden erst mit dem nächsten Upload nach Ablauf.

## Englische Fassung

Jede Seite gibt es auch auf Englisch unter `/en/` mit demselben Pfad, z. B. `/en/termin.html`. Oben rechts im Kopf schaltet DE/EN auf dieselbe Seite in der anderen Sprache um. Suchmaschinen finden beide Fassungen über `hreflang` und die Sitemap.

- Die englischen Seiten entstehen beim Bauen aus den deutschen. Die Übersetzungen liegen in `content/i18n/en/*.json` als Paare „deutscher Text“ → „englischer Text“.
- Ändert sich ein deutscher Text, fehlt seine Übersetzung. Der Build meldet das, und die englische Seite zeigt so lange den deutschen Text. `python3 build/i18n_tool.py fehlend` listet alle fehlenden Texte mit Seite, `python3 build/i18n_tool.py pruefen` prüft Platzhalter, Zahlen und Titellängen.
- Anfragen von der englischen Seite kommen mit dem Feld `sprache: en` im Portal an. Paket, Extras und Klassen bleiben als deutsche Werte, damit René sie direkt versteht. Bitte auf Englisch antworten.
- Die englischen Rechtstexte sind eine Übersetzung mit dem Hinweis, dass nur die deutsche Fassung verbindlich ist.
- Fehlermeldungen des Portals sind deutsch. Die englische Seite zeigt dafür eigene englische Hinweise. Den Text zur Löschfrist der Fotos baut sie aus `tage` von `/api/foto`.

## Prüfungen

`npm test` baut die Website und prüft:

- die Upload-Regeln: nur erlaubte Dateitypen, kein localhost, kein http://, keine Google Fonts oder Fremd-CDNs, keine .php-Dateien, eine H1, Titel unter 60 Zeichen, Bilder mit Größe und Alt-Text, Einwilligung und Lockfeld in jedem Formular;
- alle Seiten in Desktop und Mobil (390 px, kein Querscrollen) und die Barrierefreiheit mit axe;
- Buchung, Doppelbuchung, Formulare ohne Schnittstelle, Widerruf und Danke-Seite;
- die englische Fassung: jede Seite vorhanden und vollständig übersetzt, Sprachumschalter, hreflang, Buchung auf Englisch.

Die Browser-Tests nutzen dafür `tests/portal-mock.js`, eine Attrappe der Portal-Schnittstelle. Sie gehört nicht zur Website.
