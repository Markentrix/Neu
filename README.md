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

Technisch enthalten: eigene Titel und Beschreibungen pro Seite, Canonical, Open-Graph-Vorschaubild, strukturierte Daten (Unternehmen, Person, Leistungen, FAQ, Brotkrumen), `sitemap.xml`, `robots.txt`, Favicons, eigene 404-Seite, strenge Sicherheitsrichtlinie (kein Inline-Code), selbst gehostete Schriften.

Das Vorschaubild neu erzeugen: `node build/make-og.js` (braucht Playwright).

## Vor dem Livegang ausfüllen und prüfen

**Pflicht**
- `build/build.py`, Funktion `build_impressum`: USt-ID, W-IdNr., Handwerkskammer eintragen oder Absätze entfernen. Hinweisbox löschen.
- `build/build.py`, Funktion `build_datenschutz`: Betreiber des Servers und eingesetzte Kalkulationssysteme eintragen. Hinweisbox löschen. Rechtliche Prüfung empfohlen.
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

## Kontaktformular

Das Formular öffnet das E-Mail-Programm des Besuchers mit fertigem Text. Es sendet selbst nichts an einen Server. Für Versand ohne E-Mail-Programm braucht es ein Formular-Skript auf dem Server (z. B. PHP mit Spam-Schutz). Dann muss auch die Datenschutzerklärung angepasst werden.
