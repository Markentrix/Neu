# Audit Technische SEO, Conversion, Tracking, Performance · Stand 04.11.2026

Grundlage: Quellcode (`src/`, `static/`, `tools/`, `docs/server/`), gebautes `dist/`, Live-Abruf von https://markentrix.de (nur lesende Anfragen) und die im Auftrag genannten Daten aus Search Console und GA4. Zugang zu Search Console, GA4 und dem Server bestand nicht; Aussagen dazu stützen sich nur auf die genannten Zahlen.

## 1. Architektur (Befund, keine Annahme)

| Punkt | Ist-Zustand |
|---|---|
| Rendering | Statische Seiten. `tools/build.py` erzeugt `dist/` aus `src/pages/*.html` (Front Matter) und `src/partials/`. Kein clientseitiges Routing, kein JavaScript nötig für Inhalte, Meta-Daten und strukturierte Daten. |
| Routen | 96 HTML-Dateien: 85 indexierbar (alle in der Sitemap), 11 bewusst `noindex` (404, `/danke`, `/ki-checkliste`, 8 fiktive Beispielseiten unter `/beispiel/`). Keine dynamischen Routen. |
| Server | Caddy 2 im Docker-Container (`docs/server/markentrix-site.caddy`, `docker-compose.yml`), PHP-FPM nur für `/api/anfrage.php` und `/api/check.php`. Veröffentlichung per `veroeffentlichen.bat` (ZIP aus `tools/paket.sh`). |
| Tracking | GA4 und Metricool laden erst nach Einwilligung (`static/assets/consent.js`), Consent Mode v2 mit Standard „denied“. |
| Tests | Vorhanden: `build.py --check` (Linkcheck, ein h1, Titel- und Description-Länge), Playwright-Skripte außerhalb des Repos. Neu: `tools/seo_audit.py`. |

## 2. Audit-Tabelle

Bewertung: **ok** = geprüft und korrekt, **Fehler** = tatsächlicher Befund, **Hinweis** = Verbesserung ohne Fehler.

| URL / Bereich | Befund | Risiko | Empfehlung / Maßnahme | Priorität | Status |
|---|---|---|---|---|---|
| Alle 85 Sitemap-URLs | Live 200, Canonical stimmt mit der Sitemap-URL überein, kein `X-Robots-Tag: noindex` | – | – | – | ok |
| `http://`, `www` | 308 bzw. 301 auf `https://markentrix.de` (bei `http://www` zwei Schritte über `https://www`) | niedrig | Kette optional auf einen Schritt kürzen (Caddy, braucht Freigabe) | niedrig | ok / Hinweis |
| Nicht vorhandene URL | Echter Status 404 mit Fehlerseite | – | – | – | ok |
| `/preise/` (mit Schrägstrich) | **Live 404**, obwohl die Regel „Schrägstrich → 301“ in `markentrix-site.caddy` (30.10.2026) im Repository steht. Die Datei ist auf dem Server nicht eingespielt. Interne Links nutzen keinen Schrägstrich, Risiko begrenzt auf externe Verlinkung. | mittel | `markentrix-site.caddy` einspielen (Abschnitt 8). **Nicht von mir deployt.** | mittel | **Fehler (Server)** |
| `/preise.html` | 301 auf `/preise` | – | – | – | ok |
| robots.txt | Erlaubt alles außer `/kunden-dashboard` und `/api/`, Sitemap-Zeile vorhanden, keine Sitemap-URL gesperrt | – | `/kunden-dashboard` ist nur eine Weiterleitung auf das alte Portal (`markentrix.netlify.app`). Das Ziel ist veraltet (Portal jetzt `portal.markentrix.de`). Nur mit Freigabe im Caddy ändern. | niedrig | Hinweis |
| Sitemap | Nur kanonische, indexierbare 200-URLs, keine Duplikate, keine Redirects, keine Portale oder Endpunkte | – | – | – | ok |
| Canonical | Auf allen 85 indexierbaren Seiten genau einer, selbstreferenzierend, ohne `.html` und ohne Schrägstrich | – | – | – | ok |
| Meta Robots | Nur 404, danke, ki-checkliste und Beispielseiten `noindex` (bewusst) | – | – | – | ok |
| Titel, Description, h1 | Alle vorhanden, keine Duplikate unter indexierbaren Seiten, genau eine h1, keine übersprungenen Überschriftenebenen | – | – | – | ok |
| Bilder | 68 `img`, alle mit `alt`, `width` und `height`, 43 mit `loading="lazy"` | – | – | – | ok |
| hreflang | Nicht vorhanden, Seite einsprachig | – | – | – | ok |
| Strukturierte Daten | Auf allen Seiten gültiges JSON-LD, alle URLs kanonisch, keine Bewertungsmarkup (keine Bewertungen vorhanden) | – | – | – | ok |
| `/website-check`: FAQ | **Sichtbarer Text und JSON-LD wichen ab.** Die sichtbare Antwort behauptete, die Prüfung „protokolliert nichts“ und „speichert keine Adresse“, obwohl seit 02.11.2026 eine interne E-Mail mit der Adresse versendet wird. Die Frage „vollständigen Bericht“ war veraltet (es gibt eine Kurzfassung). | hoch (Wahrhaftigkeit, Datenschutz-Konsistenz, FAQ-Markup muss sichtbar sein) | Sichtbaren Text an JSON-LD und tatsächliches Verhalten angepasst. Prüfung `tools/seo_audit.py` verhindert die Abweichung künftig. | hoch | **behoben** |
| Kannibalisierung „Webdesign Celle“ | Startseite, `/leistungen/webdesign/webdesign-celle` und `/ki-marketing-celle` trugen alle „Webdesign Celle“ im Titel. Meine Änderung vom 04.11.2026 (Titel von `/ki-marketing-celle` auf „Website erstellen lassen“) hätte zusätzlich mit `/leistungen/webdesign/website-erstellen-lassen` konkurriert. | mittel | Suchabsichten getrennt (Abschnitt 4). | hoch | **behoben** |
| Interne Verlinkung | 12 tiefe Leistungsseiten hatten nur 2 kontextuelle interne Links (Elternseite und eine Nachbarseite), die Startseite verlinkte keine der lokalen Leistungsseiten. Passend zu „Gefunden, zurzeit nicht indexiert“ (29 URLs), ursächlich aber nicht belegbar. | mittel | Links von Startseite, Preisseite und Blogbeiträgen ergänzt (Abschnitt 4). | mittel | **verbessert** |
| GA4: `generate_lead` | Wird nur nach erfolgreichem Versand ausgelöst, genau einmal je Anfrage (Doppelklick durch `busy`-Sperre verhindert, im Test verifiziert). | – | – | – | ok |
| GA4: `form_submit` | Absendeversuch vor der Serverantwort, daher höher als `generate_lead` (18 zu 12 passt dazu) | mittel (Fehlinterpretation) | Als Interaktion kennzeichnen, nicht als Schlüsselereignis | hoch | dokumentiert |
| GA4: `form_start`, `website_check_start` | Fehlten | mittel | Ergänzt | hoch | **behoben** |
| GA4: Schlüsselereignisse | 0 markiert | hoch | Manuell in GA4 (Abschnitt 7) | hoch | offen (manuell) |
| GA4: interner Traffic | Nicht ausgeschlossen | mittel | `?intern=1` setzt `traffic_type=internal`, Datenfilter in GA4 aktivieren | hoch | Code fertig, GA4 manuell |
| GA4: Datenschutz | Keine personenbezogenen Parameter. `channel` kommt aus einer Auswahlliste, `utm_referrer` ist nur eine Domain, `score` nur eine Klasse (hoch, mittel, niedrig). | – | – | – | ok |
| Performance (Labor) | Siehe Abschnitt 5 | – | Keine Änderung nötig | – | ok |
| Header | HSTS, CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, zstd/gzip, Assets `immutable` | – | HTML ohne `Cache-Control` (Browser nutzt Heuristik). Optional `no-cache` für HTML (Caddy, braucht Freigabe). | niedrig | Hinweis |
| Formular, Website-Check, Mail | `static/api/*` unverändert (`git diff` leer) | – | – | – | ok |

## 3. Bewusst nicht indexiert (und warum)

| URL | Grund |
|---|---|
| `/404` | Fehlerseite |
| `/danke` | Bestätigungsseite nach Formular, kein Suchzweck, `noindex, follow` |
| `/ki-checkliste` | Material für laufende Gespräche, bewusst `noindex` |
| `/beispiel/*-muster` (8 Seiten) | Fiktive Betriebe, dünne Duplikatstruktur, nur zur Ansicht in der Startseite |
| `/api/*` | Technische Endpunkte, in robots.txt gesperrt, nur POST |

## 4. Umgesetzte Änderungen (Quellcode)

Suchabsicht je Seite (eine Seite je Absicht):

| Absicht | Seite | Title |
|---|---|---|
| Marke und Überblick, „Webdesign Celle“ (Position 4,1 laut GSC, URL nicht bekannt) | `/` | unverändert: „Webdesign Celle: Websites, Landingpages, SEO“ |
| Lokale Dienstleisterseite Webdesign | `/leistungen/webdesign/webdesign-celle` | unverändert „Webdesign-Agentur Celle“, Lead um „responsive Webdesign“ ergänzt |
| Website erstellen lassen, Kosten | `/leistungen/webdesign/website-erstellen-lassen` | unverändert |
| Pakete und Preise Webdesign (ohne Ortsbezug) | `/leistungen/webdesign` | „Responsives Webdesign: Websites & Landingpages“ |
| SEO Agentur Celle | `/seo-celle` | „SEO Agentur Celle: lokal bei Google gefunden“ (H1 und Description angepasst) |
| KI-Marketing Celle | `/ki-marketing-celle` | „KI-Marketing in Celle: Website, SEO, KI-Assistent“ (H1, Description; KI-Assistent bleibt „ab November 2026“) |
| Website-Check | `/website-check` | unverändert |
| Landingpage erstellen lassen | `/leistungen/landingpage/landingpage-erstellen-lassen` | unverändert, jetzt aus Blogbeiträgen und Startseite verlinkt |

Weitere Änderungen:

- **Startseite:** Hauptaufruf „Kostenlosen Website-Check starten“ (niedrigste Hürde, nur die Adresse), zweiter Aufruf „Erstberatung anfragen“. Der Hauptaufruf ist ab 1024 x 768 und auf dem Handy ohne Scrollen sichtbar. Zeile „In Celle: Webdesign-Agentur Celle · Website erstellen lassen · Landingpage erstellen lassen · SEO Agentur Celle · KI-Marketing Celle“ unter den Leistungen.
- **Anfrage-Dialog:** Erstberatung statt „Potenzial-Check“, Startpreise je Auswahl (aus der Preisliste), Hinweis auf Netto-Preise und Pflege.
- **Preisseite:** Abschnitt „Was in den Paketen steckt, im Detail“ mit Links auf 20 Detailseiten.
- **Blog:** Ankertexte passen zum Linkziel, Verlinkung auf `website-erstellen-lassen`, `webdesign-celle`, `landingpage-erstellen-lassen`, `seo-celle`, `lokale-seo`.
- **Website-Check-Seite:** sichtbare FAQ korrigiert (siehe Tabelle).
- **Tracking** (`static/assets/site.js`, `consent.js`): `generate_lead` mit `lead_type`, neu `form_start`, `website_check_start`, `website_check_error`, `phone_click`, `mail_click`, `wizard_step`; Eigenverkehr-Markierung. Consent-Logik **nicht** verändert.
- **Tests:** `tools/seo_audit.py` (Abschnitt 6), `.gitignore` um `__pycache__/` ergänzt.

Nicht gemacht (bewusst): neue Standortseiten, Texte aufblähen, Referenzen oder Zahlen erfinden, Design ändern, Server-, DNS-, Docker- oder Datenbankänderungen.

## 5. Performance (Messung, lokal)

Chromium, lokaler Server ohne TLS, mobil mit gedrosselter Verbindung (1,6 Mbit/s, 150 ms) und 4-fach gedrosselter CPU. Laborwerte, keine Felddaten (CrUX/PageSpeed Insights ließen sich ohne Zugang nicht abrufen).

| Seite | LCP mobil | CLS | LCP Desktop |
|---|---|---|---|
| Startseite | 2,3 s | 0,000 | 0,25 s |
| Website-Check | 2,0 s | 0,000 | 0,15 s |
| Webdesign Celle | 1,8 s | 0,000 | 0,20 s |
| Website erstellen lassen | 1,8 s | 0,000 | 0,15 s |
| Preise, Kontakt, KI-Marketing, Blog | 1,8 bis 1,9 s | 0,000 | 0,14 bis 0,18 s |

Alle Seiten liegen unter den Google-Schwellen (LCP ≤ 2,5 s, CLS ≤ 0,1). INP wurde nicht gemessen (braucht Felddaten). Assets: `mx.css` 113 KB, `site.js` 62 KB, `consent.js` 9 KB (unkomprimiert, zstd auf dem Server), Schriften lokal, Bilder WebP mit Breitenangaben. Es gab keinen Anlass für Optimierungen mit nachweisbarem Nutzen; die Startseite liegt bei 2,3 s mobil nahe an der Grenze und ist ein Kandidat, falls PageSpeed Insights im Feld Probleme zeigt.

## 6. Tests

`python3 tools/seo_audit.py` (offline, Exit-Code 1 bei Fehlern) und `python3 tools/seo_audit.py --live` (zusätzlich lesende Abrufe der Live-Seite) prüfen: Canonical je Seite, Sitemap gegen Dateien, noindex und robots.txt, Titel, Description, h1 (Duplikate, Anzahl), Bilder ohne `alt`, JSON-LD (gültig, kanonische URLs), FAQ-Markup gegen sichtbaren Text, interne Links (tot, `.html`, `http`, `www`), hreflang, bei `--live` zusätzlich 200 je Sitemap-URL, Canonical im ausgelieferten HTML, Weiterleitungen, 404, Schrägstrich-Regel. `--table` gibt eine Seitentabelle aus.

Ergebnis 04.11.2026: offline **OK**; live **ein Fehler** (`/preise/` liefert 404, Server-Datei nicht eingespielt).

Weitere Prüfungen: `build.py --check` (Linkcheck), html-validate, Playwright-Lauf über alle Seiten (Überlauf, h1, Konsolenfehler), Dialog-Durchlauf mit Versand, Ereignisse im Browser abgefangen (Website-Check: `website_check_start`, `website_check`; Kurzfassung: `form_start`, `form_submit`, genau ein `generate_lead`).

## 7. Manuelle Schritte

**Search Console**
1. Sitemap `https://markentrix.de/sitemap.xml` ist bereits eingereicht (zuletzt 02.11.2026 gelesen, keine Fehler). Nach dem Deploy erneut abrufen lassen.
2. URL-Prüfung und „Indexierung beantragen“ nur für diese URLs (Kontingent begrenzt): `/`, `/website-check`, `/leistungen/webdesign/webdesign-celle`, `/leistungen/webdesign/website-erstellen-lassen`, `/leistungen/landingpage`, `/leistungen/landingpage/landingpage-erstellen-lassen`, `/seo-celle`, `/ki-marketing-celle`, `/leistungen/webdesign`, `/preise`, `/referenzen`, `/referenzen/elbdetail`, `/leistungen/ki-automatisierung`, `/leistungen/ki-automatisierung/ki-telefonassistent`, `/leistungen/website-relaunch`, `/blog`. Reihenfolge: zuerst die vier mit geändertem Titel (`/seo-celle`, `/ki-marketing-celle`, `/leistungen/webdesign`, `/website-check`).
3. Bericht „Seiten“: je Ausschlussgrund die Beispiel-URLs öffnen (die 29 und 15 betroffenen URLs sind von hier aus nicht einsehbar). „Gefunden, zurzeit nicht indexiert“ bedeutet meist nur, dass Google noch nicht gecrawlt hat; „Gecrawlt, zurzeit nicht indexiert“ ist eine Qualitäts- oder Relevanzentscheidung von Google und lässt sich nicht erzwingen.
4. Leistung → Seiten: Suchanfrage „Webdesign Celle“ filtern und prüfen, **welche URL** rankt. Rankt nicht die Startseite, die Titel entsprechend anpassen.
5. Eigenschaften mit `www` und `http` (falls als eigene Properties angelegt) nicht pflegen, die Weiterleitungen funktionieren.

**GA4**
1. Verwaltung → Ereignisse: `generate_lead` als **Schlüsselereignis** markieren, sonst keines. `form_submit`, `form_start`, `website_check`, `phone_click` bleiben normale Ereignisse. Ereignis `danke_aufgerufen` nicht als Schlüsselereignis markieren (doppelte Zählung).
2. Verwaltung → Benutzerdefinierte Definitionen: Ereignisparameter `lead_type` als Dimension anlegen.
3. Datenfilter „Interner Datenverkehr“ von „Testen“ auf „Aktiv“. In jedem eigenen Browser einmal `https://markentrix.de/?intern=1` aufrufen und die Messung zustimmen.
4. Verwaltung → Datenstream → Erweiterte Messung: Scrollen und ausgehende Klicks prüfen (sind GA4-Einstellungen, keine Code-Ereignisse). `page_view` kommt von GA4 selbst.
5. Quellen: `account.squarespace.com` als Verweis deutet auf eine eigene Anmeldung hin (z. B. Zugriffe aus einem Squarespace-Konto); in „Unerwünschte Verweise“ eintragen, wenn es nur Eigenverkehr ist.
6. Auswertung: Untersuchen → Trichter `modal_open` → `wizard_step` (2, 3, 4) → `generate_lead`; getrennt `website_check_start` → `website_check` → `generate_lead` mit `lead_type=website_check_bericht`.

## 8. Deployment, Validierung und Rollback

Nichts davon wurde ausgeführt.

**Deployment (nach Ihrer Freigabe)**
1. Branch `claude/hopeful-bell-fov3tm` prüfen und freigeben. `tools/paket.sh <Ordner>` erzeugt `markentrix-website.zip` (läuft Build mit Linkcheck).
2. Vor dem Upload Sicherung auf dem Server: `sudo cp -a /srv/sites/markentrix /srv/sites/markentrix.bak-2026-11-04`.
3. ZIP neben `veroeffentlichen.bat` legen, Doppelklick, J. Das Skript lädt `dist/` hoch; die drei Prüfzeilen müssen 200, 200 und 405 zeigen.
4. Nur wenn die Schrägstrich-Regel gewünscht ist: `docs/server/markentrix-site.caddy` nach `EINSPIELEN.md` einspielen (Sicherung mit `cp` in `~/sicherung`, `caddy validate`, `caddy reload`). Das ist eine Reverse-Proxy-Änderung und bleibt Ihre Entscheidung.

**Validierung nach dem Deploy**
1. `python3 tools/seo_audit.py --live` muss ohne Fehler enden (ohne Caddy-Einspielung bleibt `/preise/` als bekannter Fehler).
2. Browser: Startseite hart neu laden (Strg+F5), Anfrage-Dialog bis Schritt 4, Website-Check mit eigener Adresse, Kontaktformular (Testanfrage mit Namen „Test“, die E-Mail an `info@markentrix.de` kommt an).
3. GA4 DebugView: `form_start`, `website_check_start`, `generate_lead` mit `lead_type` erscheinen jeweils einmal.
4. Search Console: nach 3 bis 7 Tagen Indexierungsstatus der Liste aus Abschnitt 7 prüfen.

**Rollback**
1. Dateien: `sudo rsync -a --delete /srv/sites/markentrix.bak-2026-11-04/ /srv/sites/markentrix/` (stellt den Stand vor dem Deploy her; Caddy muss nicht neu geladen werden, da nur statische Dateien betroffen sind).
2. Caddy (falls eingespielt): `cp ~/sicherung/markentrix-site.caddy /opt/neu/server/caddy/snippets/markentrix-site.caddy`, danach `caddy validate` und `caddy reload`.
3. Git: Der Branch bleibt unverändert; ein Zurück auf den Stand vor diesem Audit ist `git revert` der Commits ab „Audit-Umsetzung“ (nicht Verlauf umschreiben).
4. Beim Rollback der Titeländerungen kann die Search Console einige Tage den alten Titel anzeigen.

## 9. Nicht verifizierbar (kein Zugang oder keine Daten)

- Aktueller Indexierungsstatus je URL und die Ausschlussgründe der 29 und 15 URLs (Search Console).
- Welche URL für „Webdesign Celle“ auf Position 4,1 rankt, und die Klickrate.
- Felddaten der Core Web Vitals (CrUX) und INP.
- Ob Googlebot beim Abruf Einschränkungen erfährt (die Live-Prüfung der URL in der Search Console zeigt es).
- Interne Tests in GA4: Anteil der 147 Sitzungen und der 12 `generate_lead` an Eigenverkehr; daraus ist keine Conversion-Rate ableitbar.
- Serverseitige Konfiguration außerhalb des Repositorys (tatsächliche Domain-Datei `/srv/caddy-sites/markentrix.de.caddy`, PHP-Container).
- Rechtliche Prüfung der Datenschutzerklärung, insbesondere der Browserspeicher-Eintrag `mx-intern` (nur nach bewusstem Aufruf von `?intern=1`).
