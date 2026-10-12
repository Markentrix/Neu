# Markentrix – Launch-Plan (Stand 28.09.2026)

**Status:** Phase 1 umgesetzt (dist/, Routen, kein CDN) · Phase 2 umgesetzt (Preise vereinheitlicht) · Phase 3 offen (wartet auf Material)

Reihenfolge ist verbindlich: Phase 2 und 3 laufen erst, wenn Phase 1 abgenommen ist.

---

## Phase 1 – Technische Veröffentlichung (Launch-Blocker)

**Befund (geprüft)**
- Kein `index.html`, `/` hat keine Route. Es gibt nur eine 301-Weiterleitung von der Startseiten-Datei auf `/`, dort liegt aber nichts → Startseite nicht erreichbar.
- `netlify.toml`: `publish = "."` veröffentlicht den ganzen Projektordner (uploads, _archive, _ds, .md). Die 404-Regeln sind nur eine Notlösung.
- `support.js` lädt React, ReactDOM und Babel von unpkg.com und blendet den Inhalt aus, bis diese Laufzeit gestartet ist. Ist das CDN blockiert oder langsam, bleibt die Seite leer. Zusätzlich gibt es einen US-Drittanbieter-Abruf, der nicht in der Datenschutzerklärung steht.

**Umsetzung**
1. **Statischer Export** (empfohlen): Jede der 18 Seiten wird einmal gerendert und als fertiges, reines HTML in `dist/` gespeichert.
   - Kein React, kein CDN und kein Ausblenden → der Inhalt ist sofort sichtbar und für Suchmaschinen und KI-Crawler vollständig lesbar.
   - Interaktive Teile (ROI-Rechner, FAQ-Akkordeon, Mobilmenü, Pilot-Formular) bekommen ein kleines Vanilla-JS, das lokal liegt.
   - *Alternative B (schneller, schwächer):* React lokal unter `dist/vendor/` ablegen und die Adressen in `support.js` umstellen. Damit gibt es kein CDN mehr, der Inhalt ist aber weiterhin erst nach dem JS-Start sichtbar.
2. **Build-Ordner `dist/`** enthält nur: HTML-Seiten, `fonts/`, `videos/`, Bilder, `og-image.jpg`, `robots.txt`, `sitemap.xml`, `llms.txt`, `_headers`, `404.html`. Keine .md-Dateien, kein uploads, kein _archive, kein _ds.
3. **Routen**
   - `dist/index.html` = Startseite.
   - Sprechende URLs als Ordner, z. B. `dist/preise/index.html`. Damit sind keine Rewrite-Regeln nötig und es funktioniert auf Netlify, Hetzner/nginx und Apache gleich.
   - Die alten `.dc.html`-Pfade leiten per 301 auf die neuen URLs um.
4. **netlify.toml** auf `publish = "dist"` umstellen, die 404-Sperrregeln entfernen, die Header behalten.
   - nginx-Konfiguration für Hetzner beilegen (try_files, 301-Weiterleitungen, Header, gzip/brotli, Caching).
5. **Interne Links**: alle `*.dc.html`-Verweise in Navigation, Footer und CTAs auf die sprechenden URLs umstellen. Canonical-Tags, Sitemap und JSON-LD `@id`s abgleichen.
6. **Datenschutz**: Wenn Variante A umgesetzt ist, entfällt unpkg. Andernfalls muss der Abruf offengelegt werden.

**Abnahmetests**
- `/`, alle sprechenden URLs und die 301-Weiterleitungen alter Pfade liefern die richtige Seite.
- Mit unpkg.com in den DevTools blockiert → alle Seiten vollständig sichtbar und bedienbar.
- Mit JavaScript aus → Text, Preise, Impressum und Datenschutz lesbar.
- `/uploads/…`, `/_archive/…` und `/DEPLOY.md` liefern 404, weil sie physisch nicht vorhanden sind.
- Lighthouse Mobil: Performance ≥ 90, SEO 100. Rich-Results-Test für JSON-LD ohne Fehler.
- Keine Anfragen an fremde Domains ohne Einwilligung (Netzwerk-Tab).

---

## Phase 2 – Eine verbindliche Preis- und Leistungsfassung

**Referenz = Preise.dc.html**

| Paket | Monat | Einrichtung | Kanäle | Kontingent |
|---|---|---|---|---|
| ONE | 349 € | 1.490 € | WhatsApp **oder** E-Mail, **kein Telefon** | 1.500 Nachrichten |
| BUSINESS | 699 € | 2.490 € | Telefon + WhatsApp | 600 Min · 3.000 Nachr. |
| KOMPLETT | 1.190 € | 3.490 € | Telefon + WhatsApp + E-Mail | 1.000 Min · 5.000 Nachr. |

Alle Preise netto zzgl. 19 % USt. Pilotprogramm: 50 % auf die Einrichtung für 2 Betriebe.

**Vor der Umsetzung festzulegen (Entscheidung durch dich)**
- Mindestlaufzeit und Kündigungsfrist je Paket
- Preis und Takt für Mehrminuten und Mehrnachrichten
- ob ONE „1 Kanal nach Wahl“ bleibt oder fest „WhatsApp oder E-Mail“ heißt (Preisseite: ohne Telefon)

**Gefundene Abweichungen (alt 199/449/749 €, Einrichtung 690/1.290/1.990 €)**
- `FAQ.dc.html` – Kostenfrage, Frage „einzelner Kanal“ (nennt Telefon bei ONE), FAQPage-JSON-LD
- `KI-Marketing-Celle / -Hannover / -Braunschweig / -Gifhorn` – FAQ „Was kostet …“, „Kurz gefasst“-Box, JSON-LD
- `KI-Checkliste Markentrix.dc.html` – Paketübersicht
- Prüfen: ROI-Rechner (Empfehlungslogik), Startseite (`priceRange`, Offer-Katalog), `llms.txt`, Meta-Descriptions, AGB (Laufzeiten)

**Umsetzung**
1. Preise **einmal** in `preise.json` festhalten. Beim Build werden alle sichtbaren Texte und alle JSON-LD-Blöcke daraus erzeugt, damit es künftig keine Abweichungen mehr gibt.
2. Alle Fundstellen ersetzen. Anschließend eine Suche über `dist/` nach 199|449|690|749|1.290|1.990 im Paketkontext muss 0 Treffer ergeben.
3. Formulierungsregel: „ab 349 €/Monat netto“ überall identisch.

---

## Phase 3 – Beweis am echten Projekt

**3a · Fallstudie Pony Club Lila (Referenzen)**

Aufbau:
1. Kunde und Branche in einem Satz
2. Ausgangslage (Zitat oder Fakten der Kundin)
3. Aufgabe
4. Konkreter Leistungsumfang (Website, Buchung/Anfragen, KI-Assistent – nur was wirklich umgesetzt wurde)
5. Screenshots vorher/nachher, Desktop und Mobil
6. Zeitplan (Kick-off bis Livegang)
7. Ergebnisse **nur wenn gemessen und freigegeben**, sonst ersatzlos weglassen
8. Stimme der Kundin, Link zur Live-Seite

Benötigt von dir:
- eigene Screenshots (die Live-Seite kann ich nicht selbst abfotografieren)
- Freigabe der Kundin (schriftlich, inkl. Name, Logo, Zitat)
- Ausgangslage, Zeitraum, Umfang
- gegebenenfalls erhobene Zahlen mit Quelle und Zeitraum

**3b · Demo „Werkstattanfrage → bestätigter Termin“**
- Interaktiver Ablauf in 4 Schritten:
  1. Kunde schreibt per WhatsApp: „Bremsen quietschen, Termin nächste Woche?“
  2. Der Assistent fragt Fahrzeug und Kennzeichen ab.
  3. Er schlägt 3 freie Slots aus dem Kalender vor.
  4. Er bestätigt den Termin, der Eintrag erscheint im Werkstattkalender und der Betrieb bekommt eine Info.
- Deutlich als **Demo mit fiktivem Betrieb** gekennzeichnet, keine erfundenen Kennzahlen.
- Platzierung: Leistungen → KI-Automatisierung (voll), Startseite (kurzer Teaser mit Link).
- Ohne Anbindung an ein echtes System, reines Frontend, läuft im statischen Build.

---

## Ablauf und Abnahme

1. Phase 1 bauen → du testest die Staging-URL → Freigabe
2. Preisentscheidungen (siehe oben) → Phase 2 → Suche mit 0 Treffern
3. Material Pony Club Lila → Fallstudie → Demo
4. Danach offen, aber außerhalb dieses Plans: AVVs, EU-Region für OpenAI/Claude, Anwaltsprüfung AGB/Datenschutz
