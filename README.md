# PS Schneider – Website

Website von Patric Schneider, Sachverständiger für Fahrzeugtechnik in Celle. Statische Seiten für das **Markentrix-Portal**: kein eigenes Backend, kein PHP, keine Cookies, keine externen Einbindungen. Anfragen laufen über die Portal-Schnittstelle `/api/anfrage`.

Die Gestaltung ist in `DESIGN.md` beschrieben, die offenen Punkte stehen unten.

## Bauen und abgeben

```
python3 build/build.py            # Entwurf nach website-fertig/ (mit Markentrix-Vermerk)
python3 build/build.py --final    # Endversion ohne Vermerk
python3 build/check.py            # prüft Links, Titel, Sprachen, Export-Regeln
```

Hochgeladen wird der **Ordner `website-fertig/`** (mit `index.html` direkt darin). Daneben liegen und gehören nicht in den Upload: `DESIGN.md`, `WEITERLEITUNGEN.md`, `tools/`, `build/`, `selfhost-archiv/`.

- `{{SITE_URL}}` steht in `sitemap.xml`, `robots.txt`, Canonical, hreflang, `og:url`, `og:image` und im JSON-LD. Der Uploader ersetzt es durch die Live-Adresse. Sonst kommt der Platzhalter nirgends vor, das prüft `check.py`.
- Nur erlaubte Dateitypen, keine versteckten Dateien, keine absoluten Pfade, keine Schriften oder Skripte von Fremdservern.
- Sicherheitsheader (Content-Security-Policy usw.), HTTPS und Kompression stellt das Portal beziehungsweise der Server ein. Die Seite braucht dafür keinen Inline-Code, eine strenge Richtlinie `default-src 'self'` funktioniert.

## Entwurfsmodus und Urheberrecht (Markentrix)

Standardmäßig wird ein **Entwurf** gebaut: Banner „Entwurf · © Markentrix“, Wasserzeichen, Vermerk im Quelltext, `noindex` und `robots.txt` mit Sperre, Hürden gegen Kopieren und Drucken. Eingabefelder bleiben nutzbar. Die **Endversion** (`--final`) enthält nichts davon. `check.py` meldet, wenn Entwurfsdateien oder das Wort „Markentrix“ (außer als Hoster in der Datenschutzerklärung) in der Endversion liegen.

Ein technischer Vollschutz ist bei Webseiten nicht möglich, siehe `COPYRIGHT.md`.

## Aufbau der Adressen

| Adresse | Inhalt |
| --- | --- |
| `/` | Startseite |
| `/leistungen/` und `/leistungen/…` | Übersicht und sechs Leistungsseiten |
| `/einsatzgebiet/` und `/einsatzgebiet/…` | Landkreis Celle und 50 km, acht Ortsseiten |
| `/ratgeber/` und `/ratgeber/…` | fünf Ratgeber-Artikel |
| `/gruende-fuer-ein-gutachten/`, `/unfall-checkliste/`, `/kontakt/` | weitere Inhalte |
| `/impressum.html`, `/datenschutz.html`, `/danke.html`, `/404.html` | Pflichtseiten, nicht in Suchmaschinen |
| `/en/…` | englische Fassung aller Seiten (`/en/legal-notice.html`, `/en/privacy.html`, `/en/thank-you.html`) |

## Kontaktformular über das Portal

Variante B des Portals: eigene Oberfläche, Versand per `POST /api/anfrage` als JSON.

- Pflichtfelder wie im Vertrag: `typ` = `kontakt`, `name`, `email`, `nachricht`, `einwilligung` = `ja`, dazu das unsichtbare Lockfeld `website` (muss leer bleiben). Freie Zusatzfelder: `anliegen`, `telefon`, `kennzeichen`, `versicherung`, `antwort` (E-Mail oder Rückruf), `sprache`, `fotos`.
- Bei Rückruf ist die Telefonnummer Pflicht (im Formular geprüft).
- Erfolg: Weiterleitung auf `danke.html?typ=kontakt&ref=<Vorgangsnummer>`. Die Nummer wird nur als Text eingesetzt.
- Fehler 422 erscheinen am Feld, die Eingaben bleiben. 429 meldet „später noch einmal“. Bei Ausfall steht ein Ausweichkontakt (Telefon, E-Mail) da. Der Senden-Knopf ist während des Sendens gesperrt.
- **Fotos:** Bis zu fünf Fotos werden im Browser auf höchstens 1280 Pixel verkleinert und neu als JPEG gespeichert (dabei fallen Aufnahmeort und andere Metadaten weg) und als Datenfeld `fotos` (Liste von Bilddaten) mitgesendet. Das Feld gehört nicht zum festen Vertrag des Portals. Damit der Kunde die Fotos im Portal sieht, muss das Portal `fotos` speichern und als Bild anzeigen. Lehnt das Portal die Anfrage mit Fotos ab (zu groß, 413, 400 oder Fehler am Feld `fotos`), sendet das Formular sie automatisch noch einmal ohne Fotos und die Danke-Seite bittet, die Fotos per WhatsApp zu schicken.

## Tests

Alles in `tools/`, Voraussetzung Node.js und Playwright (`npm i -g playwright`, `NODE_PATH` auf `npm root -g`).

```
node tools/mock.mjs                      # Mock-Server http://localhost:8787 (MOCK_FOTOS=ablehnen: Fotos ablehnen)
node tools/formtest.mjs /kontakt/        # Formulartest (auch /en/contact/)
node tools/fototest.mjs [ablehnen]       # Foto-Weg
node tools/pruefe.mjs                    # Überlauf, Überschriften, Tippziele, Kontrast, Fremdabrufe auf allen Seiten und Breiten
```

Der Mock und die Tests laufen nur lokal und nie gegen eine Live-Seite.

## Weiterleitungen von der alten Website

Siehe `WEITERLEITUNGEN.md` (wird erzeugt). Der Server richtet sie als 301 ein, die Seite selbst enthält keine.

## Gestaltung

Siehe `DESIGN.md`. Kurz: Schwarz und Rot nach dem Logo, schräg gestellte Schrift, diagonale Flächen, Schadenskizze und Prüfstempel als gezeichnete Elemente (`build/artwork.py`, keine Bilddateien). Alle Farben und Maße stehen als Variablen am Anfang von `website-fertig/assets/site.css`, der Dunkelmodus ist eingebaut.

- Schriften lokal (`website-fertig/assets/fonts/`): Barlow 400 und 600, Barlow Condensed 700 kursiv und 800 kursiv.
- Bilder: Porträt und Logos als AVIF, WebP und Ersatzformat (`python3 build/make-images.py`, braucht Pillow). Vorschaubild für soziale Netzwerke: `node build/make-og.js`.
- Dateien in `assets/` erhalten beim Bauen eine Prüfsumme in der Adresse (`site.css?v=…`), damit Änderungen sofort ankommen und lange gecacht werden dürfen.

## Zweisprachig: Deutsch und Englisch

Deutsch im Wurzelverzeichnis, Englisch unter `/en/`. Texte: Deutsch in `build/content.py`, Englisch in `build/content_en.py`, Texte im Code als Paar `T("deutsch", "english")` in `build/build.py`. Der Sprachumschalter führt immer zur gleichen Seite, `hreflang` und Sitemap verweisen gegenseitig. Es gibt bewusst keine automatische Weiterleitung nach Browsersprache. Die englischen Rechtstexte sind Übersetzungen zur Orientierung, maßgeblich ist die deutsche Fassung. `check.py` prüft Sprache, Umschalter, `hreflang` und Fremdsprachentext.

## Vor dem Livegang

Impressum und Datenschutzerklärung enthalten keine Platzhalter. Was fehlt, muss geklärt und in `build/build.py` (`build_impressum`, `build_datenschutz`) ergänzt werden. Rechtliche Prüfung empfohlen.

- Impressum: USt-IdNr., Wirtschafts-IdNr., zuständige Kammer oder Aufsichtsbehörde (falls es sie gibt), Hinweis nach § 36 VSBG nach Angabe des Betriebs, Bildnachweis.
- Datenschutz: Anschrift von Markentrix als Hoster und Vertrag zur Auftragsverarbeitung, Speicherdauer der Anfragen und Protokolle im Portal, eingesetzte Kalkulationssysteme und Restwertbörsen.
- Portal: `fotos` speichern und anzeigen (siehe oben), Weiterleitungen einrichten, Sicherheitsheader prüfen. Statistik und Einwilligungsbanner kommen vom Portal, die Datenschutzerklärung muss dann ergänzt werden.
- Inhalte: Öffnungszeiten (fehlen), mehr echte Fotos (nur das Porträt liegt vor), Adresse klären (Startseite „Im Röthel 43“, altes Impressum „Am Röthel 43“), Google-Unternehmensprofil mit denselben Angaben.
- Fachlich prüfen: alle fünf Ratgeber-Artikel (Wertminderung, Wiederbeschaffungsaufwand, Faustregel von etwa 130 Prozent, Mietwagen und Nutzungsausfall, Honorar nach Schadenhöhe, Oldtimer), das Zahlenbeispiel im Artikel zum Totalschaden und die Unterseite „Unfallanalytisches Gutachten“.

## Eigener Server (Archiv)

Der frühere Weg mit eigenem Server liegt in `selfhost-archiv/`: PHP-Endpunkt mit Fotoverarbeitung, SMTP-Versand und Tests, dazu eine nginx-Vorlage. Er gehört nicht zum Export und wird vom Bauskript nicht mehr verwendet.
