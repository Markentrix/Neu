# AJ Atelier – Website mit Markentrix-Portal

Statische Website für **AJ Atelier – Hair & Beauty**, Friseur in der Hauptstraße 64, 30938 Burgwedel-Wettmar.
Gebaut nach dem Skill **„Website mit Portal“** (Vertrag `mk-api v1`): Die Website hat **kein eigenes Backend**.
Terminbuchung, Anfragen, Bewertungen und Statistik laufen über das Markentrix-Portal.

**Hochgeladen wird nur der Ordner `website-fertig/`** (als ZIP im Portal unter Website → Hochladen).
Die `index.html` liegt direkt darin, alle Seiten liegen flach im Hauptordner, es gibt kein PHP, kein `../` und keine fremden CDNs.

## Was die Website kann

| Funktion | Umsetzung | Portal |
|---|---|---|
| Online-Terminbuchung in 3 Schritten | eigenes Design (Variante B) | `GET /api/leistungen`, `/api/mitarbeiter`, `/api/verfuegbarkeit`, `/api/slots`, `POST /api/anfrage` (typ `termin`) |
| Kontaktformular | eigenes Design (Variante B) | `POST /api/anfrage` (typ `kontakt`) |
| Gutscheine | Anfrage mit Betrag, Empfänger, Widmung; Zahlung per PayPal.Me-Link vom Salon | `POST /api/anfrage` (typ `gutschein`) |
| Google-Bewertungen | Baustein auf der Startseite | `<div data-mk="bewertungen">` (Variante A) |
| Statistik / Einwilligung | Baustein im Footer jeder Seite | `<span data-mk="cookies">` (Variante A) |
| Danke-Seite | `danke.html?typ=…&ref=…` mit Vorgangsnummer und Kalendereintrag | – |

Das Markentrix-Skript (`site.js`) fügt das Portal beim Hochladen selbst in jede Seite ein; es steht bewusst nicht im Code.

**Buchung im Detail**
- Leistungen und Wunschperson kommen live aus dem Portal, nichts ist fest eingetragen. Eine Personenauswahl erscheint nur, wenn mindestens zwei Personen die gewählte Leistung anbieten.
- Ruhetage, Sperrtage (Urlaub) und belegte Zeiten kommen aus dem Portal; angeboten werden nur Uhrzeiten mit `frei:true`.
- Ist im Portal „Ich bestätige jede Buchung selbst“ an (`selfBooking:false`), heißt der Knopf „Terminwunsch senden“.
- Bucht jemand gleichzeitig dieselbe Zeit, springt das Formular mit Hinweis zur Zeitwahl zurück; Eingaben bleiben erhalten.
- Ohne Leistungsliste im Portal fragt das Formular die gewünschte Leistung als Text ab.
- Ist das Portal nicht erreichbar (oder die Seite per Doppelklick geöffnet), erscheinen Telefon und Instagram als Ausweg.
- Links wie `termin.html?leistung=f-balayage` (von den Leistungsseiten) wählen die Leistung vor, **wenn der Kurzname im Portal gleich ist** (Tabelle unten).

**SEO & GEO**: strukturierte Daten (`HairSalon` mit Adresse, Geo-Koordinaten, Öffnungszeiten, Preisliste, Buchungs-Aktion; `FAQPage`, `BreadcrumbList`, `Service`, `BlogPosting`), Geo-Meta-Tags, Open-Graph-Bild, `sitemap.xml` mit sauberen Adressen, `robots.txt` (KI-Crawler erlaubt), `llms.txt`, 8 Leistungs-, 4 Orts- und 3 Ratgeberseiten.

## Im Portal einrichten

1. **Website-Dienste** für den Kunden einschalten: Anfragen, Terminbuchung, Google-Bewertungen, Statistik.
2. **Leistungen** anlegen. Damit die „Buchen“-Links der Leistungsseiten die Leistung vorwählen, als Kurzname (key) genau diese Werte verwenden.
   Dauer bitte mit dem Salon abstimmen:

| Kurzname (key) | Name | Preis | Dauer (Min.) |
|---|---|---|---|
| `d-wsf-kurz` | Waschen, Schneiden & Föhnen – kurz | 55 € | 45 |
| `d-wsf-mittel` | Waschen, Schneiden & Föhnen – mittel | 60 € | 60 |
| `d-wsf-lang` | Waschen, Schneiden & Föhnen – lang | 70 € | 75 |
| `d-wf-kurz` | Waschen & Föhnen – kurz | 35 € | 30 |
| `d-wf-mittel` | Waschen & Föhnen – mittel | 40 € | 40 |
| `d-wf-lang` | Waschen & Föhnen – lang | 50 € | 50 |
| `d-hochstecken` | Hochstecken | ab 55 € | 60 |
| `h-schnitt` | Herrenschnitt inkl. Waschen & Styling | 45 € | 40 |
| `h-maschine` | Maschinenschnitt | 30 € | 20 |
| `h-bart` | Bart schneiden | 20 € | 15 |
| `f-ansatz` | Ansatzfarbe | ab 55 € | 90 |
| `f-faerben` | Färben | ab 50 € | 120 |
| `f-glossing` | Glossing | ab 22 € | 45 |
| `f-balayage` | Balayage | ab 250 € | 210 |
| `f-babylights` | Babylights | ab 250 € | 210 |
| `f-blondierung` | Blondierung | ab 55 € | 120 |
| `f-correction` | Color Correction – Beratungstermin | nach Beratung | 30 |
| `p-haarpflege` | Haarpflege | ab 15 € | 15 |
| `p-bond` | Bond Treatment | ab 20 € | 30 |
| `b-zupfen` | Augenbrauen zupfen | ab 15 € | 15 |
| `b-faerben` | Augenbrauen färben | ab 15 € | 15 |
| `b-wimpern` | Wimpern färben | 16 € | 20 |

3. **Mitarbeiter** anlegen, falls mehrere Personen buchbar sind (Arbeitszeiten, Urlaub, angebotene Leistungen).
4. **Öffnungszeiten / Raster**: Di–Fr 10–18 Uhr, Sa 10–14 Uhr, Raster z. B. 15 oder 30 Minuten; Sperrtage für Urlaub.
5. Optional: **„Ich bestätige jede Buchung selbst“** mit **PayPal.Me-Link**, wenn bei Balayage & Co. eine Anzahlung gewünscht ist.
6. **PayPal.Me-Name** hinterlegen – darüber laufen die Gutschein-Zahlungen.

## Website ändern und neu bauen

Texte, Preise und Öffnungszeiten stehen in `app/` (nicht direkt in `website-fertig/` ändern, sonst ist es beim nächsten Build weg):

| Datei | Inhalt |
|---|---|
| `app/config.php` | Salon-Daten, Domain, Öffnungszeiten, Preisliste, Gutschein-Beträge |
| `app/content/leistungen.php` | 8 Leistungsseiten |
| `app/content/orte.php` | Ortsseiten (Burgwedel, Isernhagen, Langenhagen, Hannover) |
| `app/content/ratgeber.php` | Ratgeber-Artikel |
| `app/pages/*.php` | Seitenvorlagen (Startseite, Termin, Kontakt, Impressum, Datenschutz …) |
| `assets/` | CSS, Schriften (lokal), JavaScript, Bilder – wird 1:1 kopiert |

```bash
php tools/build.php --url=https://www.aj-atelier-wettmar.de   # baut website-fertig/
php tests/run.php                                              # prüft alle Upload-Regeln
```

Danach `website-fertig/` als ZIP packen (Inhalt des Ordners oder den Ordner selbst) und im Portal hochladen.
PHP wird nur beim Bauen auf dem eigenen Rechner gebraucht, nie auf dem Server.

## Testen

- `php tests/run.php` – Upload-Regeln des Portals (Dateitypen, keine versteckten Dateien, kein `../`, kein localhost/http://,
  keine Google Fonts/CDNs, kein eigenes PayPal-Skript), jede Seite (lang, title < 60, description, viewport, genau eine h1,
  Footer-Links, Favicon), tote Links, Sitemap, strukturierte Daten und alle Formulare (Pflichtfelder, Einwilligung, Lockfeld,
  Fehlertexte, Ausweg).
- `tests/browser.cjs` – echter Browser gegen einen Nachbau der Portal-Schnittstelle (`tests/mock-portal.php`):
  Buchung mit Person, Doppelbuchung, Kontakt, Gutschein, Ausfall des Portals, Terminwunsch-Modus, Doppelklick-Vorschau, 390 px.
  ```bash
  php tools/build.php && NODE_PATH=<ordner>/node_modules node tests/browser.cjs
  ```
- Lokale Vorschau mit Beispieldaten: `php -S 127.0.0.1:8080 tests/mock-portal.php` → http://127.0.0.1:8080
- GitHub Actions führt beides bei jedem Push aus.

## Vor dem Livegang offen

- [ ] Impressum und Datenschutz: Name der Inhaberin/des Inhabers, E-Mail, USt-IdNr./Steuernummer, Handwerkskammer + Betriebsnummer, Anschrift Markentrix (gelb markiert)
- [ ] Domain bestätigen (`siteUrl` in `app/config.php` bzw. `--url`), danach neu bauen
- [ ] Im Portal: Leistungen mit obigen Kurznamen, Dauer, Raster, Mitarbeiter, PayPal.Me
- [ ] Klären, ob Google Analytics im Portal eingeschaltet wird (die Datenschutzerklärung nennt es nur mit Einwilligung)
- [ ] Rechtstexte anwaltlich prüfen lassen (siehe ANWALT-CHECKLISTE im Server-Paket)
- [ ] Echte Fotos aus dem Salon (als webp mit width/height)
