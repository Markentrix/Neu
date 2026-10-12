# PS Schneider – Website

Website von Patric Schneider, Sachverständiger für Fahrzeugtechnik in Celle (https://psschneider.de).
Statische Seiten ohne Datenbank, ohne Cookies, ohne Tracking, ohne externe Einbindungen.

## Entwurfsmodus und Urheberrecht (Markentrix)

Die Seite wird standardmäßig als **Entwurf** gebaut. Das ist die Version zum Zeigen:

- Sichtbarer Banner „Entwurf · © Markentrix · Alle Rechte vorbehalten“ und Wasserzeichen über jeder Seite
- Urheberrechtsvermerk im Quelltext, im Metadatenfeld und in der Fußzeile
- Sperre für Suchmaschinen (`noindex`, `robots.txt`, Header), damit der Entwurf nirgends auftaucht
- Hürden für Gelegenheitskopierer: keine Textauswahl, kein Rechtsklick, kein Bildziehen, Zwischenablage zeigt nur den Hinweis, Ausdruck gesperrt. Eingabefelder bleiben normal nutzbar.

**Endversion für den Kunden, ohne jede Kennzeichnung:**

```
python3 build/build.py --final
python3 build/check.py
```

Der Prüfer meldet dann, wenn noch Entwurfsdateien oder das Wort „Markentrix“ im Ordner `public/` liegen. Erst danach den Ordner übergeben.

**Grenzen:** Ein technischer Vollschutz ist bei Webseiten nicht möglich. Quelltext, Entwicklerwerkzeuge, „Seite speichern“ und Screenshots lassen sich nicht verhindern. Der Entwurfsmodus macht Kopieren unbequem und Herkunft nachweisbar. Sicherer ist es, dem Kunden nur den privaten Vorschau-Link oder eine Bildschirmfreigabe zu zeigen und den Code erst nach Zahlung und schriftlicher Rechteübertragung zu übergeben. Siehe `COPYRIGHT.md`.

## Auf den eigenen Server legen

1. Die **Endversion** bauen (`python3 build/build.py --final`) und den **Inhalt des Ordners `public/`** in das Webroot des Servers kopieren (die Datei `.htaccess` ist versteckt, bitte mitkopieren).
2. Die Domain `psschneider.de` auf dieses Webroot zeigen lassen, HTTPS einrichten.
3. **Apache:** `.htaccess` liegt schon im Ordner. `AllowOverride All` muss für das Webroot gesetzt sein. Module: `mod_alias`, `mod_headers`, `mod_expires`, `mod_deflate`.
   **nginx:** Beispiel in `server/nginx.conf.example`, Pfade und Zertifikate anpassen.
4. Nach dem Einrichten von HTTPS in der `.htaccess` den Block „HTTPS und eine Domain erzwingen“ einkommentieren.
5. Nach dem Livegang: Seite in der Google Search Console anmelden und `https://psschneider.de/sitemap.xml` einreichen.

Die Seite muss im **Wurzelverzeichnis der Domain** liegen, nicht in einem Unterordner.

### Weiterleitungen von der alten Website

Die alten Adressen leiten dauerhaft (301) auf die neuen Seiten. So behalten die Seiten ihre bisherigen Google-Platzierungen.

| Alt | Neu |
| --- | --- |
| `/start/` | `/` |
| `/LEISTUNGEN/` | `/leistungen/` |
| `/LEISTUNGEN/Haftpflichtschaden-Gutachten/` | `/leistungen/haftpflichtschaden-gutachten/` |
| `/LEISTUNGEN/Beweissicherungsgutachten/` | `/leistungen/beweissicherungsgutachten/` |
| `/LEISTUNGEN/Leasingruecknahme-Gutachten/` | `/leistungen/leasingruecknahme-gutachten/` |
| `/LEISTUNGEN/Wertgutachten/` | `/leistungen/wertgutachten/` |
| `/LEISTUNGEN/Restwertermittlung/` | `/leistungen/restwertermittlung/` |
| `/Gruende-fuer-ein-Gutachten/` | `/gruende-fuer-ein-gutachten/` |
| `/UNFALL-CHECKLISTE/` | `/unfall-checkliste/` |
| `/kontakt/impressum/` | `/impressum/` |
| `/kontakt/datenschutz/` und `.../index.php/` | `/datenschutz/` |

Getestet mit Apache (alle Weiterleitungen, keine Schleifen, 404-Seite, Header, Komprimierung).

## Inhalte ändern

Alles liegt in `build/`. Texte stehen in `build/content.py`, Aufbau und Seitenvorlagen in `build/build.py`, Design in `public/assets/site.css`.

```
python3 build/build.py     # erzeugt alle Seiten in public/ als Entwurf (mit Markentrix-Vermerk)
python3 build/build.py --final   # Endversion ohne Vermerk, für die Übergabe
python3 build/check.py     # prüft Links, Titel, Überschriften, Sitemap, Inline-Code
```

Beide Skripte brauchen nur Python 3. Nach jeder Änderung `build.py` ausführen und den Ordner `public/` neu hochladen. `check.py` muss „Alles in Ordnung“ melden.

Ändert sich die Domain, in `build/content.py` den Eintrag `domain` anpassen.

## Aufbau

| Adresse | Inhalt |
| --- | --- |
| `/` | Startseite |
| `/leistungen/` | Übersicht aller Leistungen |
| `/leistungen/…` | Sechs Unterseiten, je eine pro Gutachten |
| `/einsatzgebiet/` | Einsatzgebiet Landkreis Celle und Umkreis von 50 Kilometern mit Schema und Ortsliste |
| `/einsatzgebiet/…` | Acht Ortsseiten: Bergen, Hambühren, Wietze, Hannover, Burgdorf, Gifhorn, Walsrode, Soltau |
| `/ratgeber/` | Übersicht der Ratgeber-Artikel |
| `/ratgeber/…` | Fünf Artikel zu Wertminderung, Totalschaden, Mietwagen, Gutachterkosten und Oldtimer |
| `/gruende-fuer-ein-gutachten/` | Vergleich Kostenvoranschlag und Gutachten |
| `/unfall-checkliste/` | Interaktive Checkliste |
| `/kontakt/` | Kontaktformular und Daten |
| `/impressum/`, `/datenschutz/` | Rechtliches, nicht in Suchmaschinen indexiert |
| `/en/…` | Englische Fassung aller Seiten, siehe Abschnitt „Zweisprachig“ |

## Zweisprachig: Deutsch und Englisch

Jede Seite gibt es auch auf Englisch unter `/en/` (zum Beispiel `/en/services/`, `/en/service-area/`, `/en/contact/`). Deutsch bleibt die Hauptsprache im Wurzelverzeichnis, damit die bestehenden Adressen und Weiterleitungen unverändert bleiben.

- Texte: Deutsch in `build/content.py`, Englisch in `build/content_en.py` (gleiche Schlüssel und Struktur). Texte direkt im Code stehen als Paar `T("deutsch", "english")` in `build/build.py`.
- Jede Seite hat einen sprachneutralen `key`. Daraus entstehen der Sprachumschalter DE | EN im Kopfbereich, die `hreflang`-Verweise in jeder Seite und die Sprachverweise in der `sitemap.xml`.
- Der Umschalter führt immer zur gleichen Seite in der anderen Sprache. Es gibt bewusst keine automatische Weiterleitung nach Browsersprache, weil Suchmaschinen sonst Seiten nicht vollständig erfassen.
- Rechtstexte: Die englischen Fassungen von Impressum und Datenschutzerklärung sind Übersetzungen zur Orientierung. Rechtlich maßgeblich ist die deutsche Fassung. Beide Fassungen müssen vor dem Livegang geprüft werden.
- Das Kontaktformular sendet die Sprache mit. Fehlermeldungen kommen in der Sprache der Seite. Die E-Mail an das Postfach bleibt deutsch, trägt bei englischen Anfragen `[EN]` im Betreff und weist darauf hin, dass möglichst auf Englisch geantwortet werden soll.
- Die 404-Seite ist eine Datei für beide Sprachen und verweist auf die englische Startseite.
- `check.py` prüft zusätzlich: `lang` passt zum Pfad, keine Links in die andere Sprache ohne Umschalter, Umschalter und `hreflang` sind gegenseitig, und englische Seiten enthalten keinen deutschen Text.

Technisch enthalten: eigene Titel und Beschreibungen pro Seite, Canonical, Open-Graph-Vorschaubild, strukturierte Daten (Unternehmen, Person, Leistungen, FAQ, Brotkrumen), `sitemap.xml`, `robots.txt`, Favicons, eigene 404-Seite, strenge Sicherheitsrichtlinie (kein Inline-Code), selbst gehostete Schriften.

Das Vorschaubild neu erzeugen: `node build/make-og.js` (braucht Playwright).

## Vor dem Livegang ausfüllen und prüfen

**Pflicht**
- `build/build.py`, Funktion `build_impressum`: USt-ID, W-IdNr., Handwerkskammer eintragen oder Absätze entfernen. Hinweisbox löschen.
- `build/build.py`, Funktion `build_datenschutz`: fünf gelb markierte Stellen klären und eintragen, dann Hinweisbox löschen. Rechtliche Prüfung empfohlen.
  - Standort des Hetzner-Rechenzentrums und Vertrag zur Auftragsverarbeitung (im Hetzner-Kundenkonto abschließen)
  - Anbieter des Postfachs, über das die Anfragen laufen, samt Auftragsverarbeitung
  - Aufbewahrungsdauer der Zugriffsprotokolle (empfohlen 7 Tage) und des Formular-Protokolls (empfohlen 90 Tage), per Logrotate umsetzen
  - eingesetzte Kalkulationssysteme und Restwertbörsen
- Kontaktformular: `private/config.php` auf dem Server ausfüllen und mit `selftest` prüfen, siehe unten. Ein echtes Testformular mit Foto absenden.
- Adresse klären: Startseite „Im Röthel 43“, altes Impressum „Am Röthel 43“.

**Inhalte, die nicht von der alten Website stammen, bitte fachlich prüfen**
- Alle fünf Ratgeber-Artikel, besonders die rechtlichen Aussagen: Wertminderung auch bei fiktiver Abrechnung, Wiederbeschaffungsaufwand, Faustregel von etwa 130 Prozent, Mietwagen und Nutzungsausfall, Honorar nach Schadenhöhe, Versicherer-Anforderungen bei Oldtimern.
- Das Beispiel mit angenommenen Zahlen (8.000 Euro und 2.000 Euro) im Artikel zum Totalschaden.
- Unterseite „Unfallanalytisches Gutachten“ und ihr Umfang.
- Aussage zu Bagatellschäden (etwa 750 bis 1.000 Euro) auf der Haftpflicht-Seite und im Vergleich.
- Einsatzgebiet „Landkreis Celle und Umkreis von 50 Kilometern“, die Ortsliste und die Entfernungen auf den Ortsseiten.
- Aussage „Besichtigung nach Absprache“ und wo Besichtigungen stattfinden.
- Tipps unter „In den Tagen danach“ auf der Checklisten-Seite.
- Hinweise zu Wertgutachten (Kauf, Verkauf, Oldtimer) und zur Totalschaden-Definition.
- Autorenzeile „Von Patric Schneider“ auf den Unterseiten.

**Neue Artikel schreiben:** In `build/content.py` unter `ARTICLES` einen Eintrag nach dem Muster der vorhandenen ergänzen, `build.py` ausführen, fertig. Die Seite landet automatisch in Navigation, Übersicht und Sitemap. Veröffentlichungsdatum fest eintragen.

**Orte ändern:** In `build/content.py` unter `TOWNS` stehen alle Orte. Mit `"page": True` und Koordinaten bekommt ein Ort eine eigene Seite, Entfernung und Himmelsrichtung berechnet der Generator selbst. Der Radius steht unter `AREA`. Entfernungen sind Luftlinie ab Celle und beruhen auf groben Koordinaten.

**Zu viele Ortsseiten schaden:** Seiten, die sich nur im Ortsnamen unterscheiden, bewertet Google schlecht. Deshalb gibt es nur acht. Weitere Orte lohnen sich erst, wenn es echte Inhalte dazu gibt, zum Beispiel Fotos von Einsätzen oder Kundenstimmen aus dem Ort.

**Für bessere Auffindbarkeit (außerhalb des Codes)**
- Google-Unternehmensprofil mit Kategorie „Kfz-Gutachter“ anlegen und mit Adresse, Telefon, Öffnungszeiten und Website pflegen.
- Kundenbewertungen sammeln.
- Branchenverzeichnisse mit identischem Namen, Adresse und Telefonnummer.
- Danach in `build/build.py` Öffnungszeiten und Geokoordinaten in die strukturierten Daten aufnehmen.

## Kontaktformular mit Schadenfotos (Hetzner-Server)

Das Formular auf `/kontakt/` sendet an `public/api/anfrage.php`. Der Endpunkt prüft die Eingaben, verkleinert die Fotos, entfernt dabei den Aufnahmeort und schickt eine E-Mail mit den Fotos als Anhang an das Postfach. Es werden keine Cookies gesetzt und keine Dienste Dritter genutzt.

**Was der Server braucht:** PHP 8.1 oder neuer mit den Erweiterungen `gd`, `fileinfo`, `openssl` (empfohlen auch `exif`, `mbstring`) und einen Postfach-Zugang mit SMTP.

### Einrichtung in sieben Schritten

1. **Pakete (Ubuntu/Debian mit nginx):**
   `apt install nginx php8.3-fpm php8.3-gd php8.3-mbstring`
2. **Ordner anlegen.** Der Webserver zeigt auf `public/`. Die Zugangsdaten liegen daneben in `private/`, außerhalb des Webroots:
   ```
   /var/www/psschneider.de/public/    <- Inhalt des Ordners public/ aus dem Repository
   /var/www/psschneider.de/private/   <- nur config.php, nicht öffentlich
   ```
3. **Konfiguration.** `server/private.example/config.php` nach `private/config.php` kopieren und ausfüllen. Geheimen Schlüssel erzeugen mit `openssl rand -hex 32`. Dann:
   ```
   chown -R www-data:www-data /var/www/psschneider.de/private
   chmod 750 /var/www/psschneider.de/private && chmod 640 /var/www/psschneider.de/private/config.php
   ```
4. **E-Mail-Versand per SMTP.** In `config.php` den SMTP-Zugang des Postfachs eintragen, am besten Port 587 mit `starttls`. Bei Hetzner Cloud ist der ausgehende Port 25 gesperrt, deshalb funktioniert ein lokaler Mailserver ohne weiteres nicht. Beim Postfachanbieter für die Domain SPF und DKIM einrichten, sonst landen die Anfragen im Spam-Ordner. Als Absender eine Adresse verwenden, die der Zugang senden darf.
5. **Webserver.** `server/nginx.conf.example` (wird von `build.py` erzeugt) als Vorlage verwenden. Socket von php-fpm, Zertifikate und den Pfad `PSS_PRIVATE_DIR` anpassen. Die Vorlage erlaubt von außen nur `anfrage.php`, sperrt alle anderen PHP-Dateien und versteckten Dateien, erlaubt Uploads bis 60 MB und kürzt IP-Adressen im Zugriffsprotokoll. Bei Apache liegen die gleichen Regeln in der `.htaccess`.
6. **Prüfen.** Auf dem Server als Webserver-Benutzer:
   ```
   sudo -u www-data env PSS_PRIVATE_DIR=/var/www/psschneider.de/private \
     php /var/www/psschneider.de/public/api/anfrage.php selftest
   ```
   Der Selbsttest prüft PHP-Erweiterungen, Konfiguration, Schreibrechte und ob der Mailserver erreichbar ist. Die Upload-Grenzen zeigt er für die Konsole an. Für den Webserver gelten php-fpm und die mitgelieferte Datei `.user.ini`. Danach ein echtes Testformular mit Foto absenden.
7. **Aufräumen per Cron** (löscht gescheiterte Anfragen nach 14 Tagen und alte Zähler):
   ```
   17 3 * * * www-data env PSS_PRIVATE_DIR=/var/www/psschneider.de/private php /var/www/psschneider.de/public/api/anfrage.php purge
   ```

### Was der Endpunkt tut und was er speichert

| Thema | Verhalten |
| --- | --- |
| Fotos | Höchstens 5, JPG, PNG oder WebP. Werden im Browser und auf dem Server auf 2400 Pixel verkleinert, gedreht und neu gespeichert. Standortdaten und andere Metadaten sind danach weg. Dateien, die keine Bilder sind, werden abgelehnt. |
| Spam | Unsichtbares Köderfeld, zeitlich begrenztes Token, höchstens 5 Anfragen pro Stunde und 15 pro Tag und Verbindung, Prüfung der Herkunft. |
| IP-Adresse | Nur als Hash mit geheimem Schlüssel, nach zwei Tagen gelöscht. Nie im Klartext. |
| Anfragen | Nach erfolgreichem Versand sofort vom Server gelöscht. Bei Versandfehler bleiben sie 14 Tage gesichert in `private/inbox/`, damit nichts verloren geht. |
| Protokoll | `private/logs/anfragen.log`: Zeit, Status, Referenz, Fotozahl. Keine Namen oder Kontaktdaten. Per Logrotate nach 90 Tagen löschen. |

Schlägt der Versand fehl, sieht der Besucher eine Meldung mit Telefon und E-Mail. Im Protokoll steht dann `mail_fehler`. Das sollte jemand beobachten, zum Beispiel per Monitoring auf diese Zeile.

### Felder, Rückruf und Bestätigung

Das Formular fragt zusätzlich freiwillig nach Kennzeichen und Versicherung und lässt wählen, ob per E-Mail geantwortet oder zurückgerufen werden soll. Für den Rückruf ist die Telefonnummer Pflicht. In der Mail an das Postfach stehen diese Angaben, bei Rückruf trägt der Betreff `[RÜCKRUF]`.

Nach dem Senden geht automatisch eine kurze Bestätigung an die angegebene Adresse. Sie enthält nur die Referenznummer und feste Texte, keine Eingaben des Absenders, und ist pro Adresse auf `confirm_per_address_day` begrenzt (Standard 2 pro Tag, höchstens 1 pro Stunde). Ein Fehler beim Versand der Bestätigung lässt die Anfrage nicht scheitern. Abschalten mit `'confirm_customer' => false` in `private/config.php`. Name, Adresse und Telefon in der Signatur stehen dort unter `sign_name`, `sign_address`, `sign_phone`. Die Datenschutzerklärung beschreibt die Bestätigung.

### Bilder und Ladezeit

Porträt und Logos liegen zusätzlich als AVIF und WebP in zwei bis drei Größen vor, das Original bleibt als Ersatz für alte Browser. Neu erzeugen nach einer Änderung von Logo oder Porträt: `pip install pillow` und `python3 build/make-images.py`. Die Startseite lädt damit auf dem Handy rund 30 statt 145 KB Bilder.

`build.py` hängt an Dateien in `assets/` eine Prüfsumme an (`site.css?v=1a2b3c4d`). Geänderte Dateien kommen so sofort bei den Besuchern an, deshalb dürfen sie ein Jahr zwischengespeichert werden. Die mitgelieferte `.htaccess` und die nginx-Vorlage sind darauf eingerichtet. Wer eine eigene Konfiguration nutzt, sollte Adressen mit `?v=` entsprechend lange cachen.

### Tests

```
python3 server/tests/test_form.py
```

Der Test startet einen lokalen PHP-Server und einen Test-Mailserver mit Verschlüsselung und prüft 78 Fälle: normale Anfragen, Fotos mit Standortdaten, getarnte Dateien, zu große Anfragen, Spam-Versuche, Header-Einschleusung, Mengenbegrenzung und Versandfehler. Voraussetzung: `php` mit `gd`, `openssl` und `pip install pillow`.

### Vorschau und Entwurf

In der Vorschau (Artefakt) läuft das Formular im Demo-Modus: Es prüft die Eingaben und zeigt die Fotos an, sendet aber nichts. Auf dem Server ist der Endpunkt aktiv.

## Vergleich alt und neu (für die Vorführung)

Links die bisherige Seite, rechts der neue Entwurf, auf einen Blick und mit gemeinsamem Scrollen:

```
python3 build/build.py --compare ORDNER
```

Der Ordner enthält `vergleich.html` (die Startseite der Ansicht), `neu/` (die komplette neue Seite mit relativen Links) und `alt/` (Bilder der bisherigen Seite). Die Bilder der alten Seite entstehen mit `NODE_PATH=$(npm root -g) node build/compare/capture-old.js` (Playwright und Internet nötig) und liegen in `build/compare/alt/`. Die Zuordnung alter zu neuer Seiten steht in `build/compare/pages.json`. Die Ansicht gehört nicht in den Webroot.
