# PS Schneider – Website

Website von Patric Schneider, Sachverständiger für Fahrzeugtechnik in Celle (https://psschneider.de).
Statische Seiten ohne Datenbank, ohne Cookies, ohne Tracking, ohne externe Einbindungen.

## Auf den eigenen Server legen

1. Den **Inhalt des Ordners `public/`** in das Webroot des Servers kopieren (die Datei `.htaccess` ist versteckt, bitte mitkopieren).
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
python3 build/build.py     # erzeugt alle Seiten in public/
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
| `/gruende-fuer-ein-gutachten/` | Vergleich Kostenvoranschlag und Gutachten |
| `/unfall-checkliste/` | Interaktive Checkliste |
| `/kontakt/` | Kontaktformular und Daten |
| `/impressum/`, `/datenschutz/` | Rechtliches, nicht in Suchmaschinen indexiert |

Technisch enthalten: eigene Titel und Beschreibungen pro Seite, Canonical, Open-Graph-Vorschaubild, strukturierte Daten (Unternehmen, Person, Leistungen, FAQ, Brotkrumen), `sitemap.xml`, `robots.txt`, Favicons, eigene 404-Seite, strenge Sicherheitsrichtlinie (kein Inline-Code), selbst gehostete Schriften.

Das Vorschaubild neu erzeugen: `node build/make-og.js` (braucht Playwright).

## Vor dem Livegang ausfüllen und prüfen

**Pflicht**
- `build/build.py`, Funktion `build_impressum`: USt-ID, W-IdNr., Handwerkskammer eintragen oder Absätze entfernen. Hinweisbox löschen.
- `build/build.py`, Funktion `build_datenschutz`: Betreiber des Servers und eingesetzte Kalkulationssysteme eintragen. Hinweisbox löschen. Rechtliche Prüfung empfohlen.
- Adresse klären: Startseite „Im Röthel 43“, altes Impressum „Am Röthel 43“.

**Inhalte, die nicht von der alten Website stammen, bitte fachlich prüfen**
- Unterseite „Unfallanalytisches Gutachten“ und ihr Umfang.
- Aussage zu Bagatellschäden (etwa 750 bis 1.000 Euro) auf der Haftpflicht-Seite und im Vergleich.
- Einsatzgebiet „Celle und Umgebung“ und „Besichtigung nach Absprache“.
- Tipps unter „In den Tagen danach“ auf der Checklisten-Seite.
- Hinweise zu Wertgutachten (Kauf, Verkauf, Oldtimer) und zur Totalschaden-Definition.
- Autorenzeile „Von Patric Schneider“ auf den Unterseiten.

**Für bessere Auffindbarkeit (außerhalb des Codes)**
- Google-Unternehmensprofil mit Kategorie „Kfz-Gutachter“ anlegen und mit Adresse, Telefon, Öffnungszeiten und Website pflegen.
- Kundenbewertungen sammeln.
- Branchenverzeichnisse mit identischem Namen, Adresse und Telefonnummer.
- Danach in `build/build.py` Öffnungszeiten und Geokoordinaten in die strukturierten Daten aufnehmen.

## Kontaktformular

Das Formular öffnet das E-Mail-Programm des Besuchers mit fertigem Text. Es sendet selbst nichts an einen Server. Für Versand ohne E-Mail-Programm braucht es ein Formular-Skript auf dem Server (z. B. PHP mit Spam-Schutz). Dann muss auch die Datenschutzerklärung angepasst werden.
