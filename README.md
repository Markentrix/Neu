# ElbDetail – Website, Buchung und Verwaltung

Verkaufsorientierte Website für **ElbDetail – Premium Fahrzeugaufbereitung in Celle**, inklusive Online-Terminbuchung, Gutscheinverkauf, Firmenkunden-Anfragen, Ratgeber, Verwaltungsportal und cookieloser Statistik. Alles läuft auf dem eigenen Server (Hetzner), ohne Fremddienste.

## Was drin ist

| Bereich | Inhalt |
|---|---|
| **Website** | Kompakte Startseite mit Richtpreis-Rechner, Preisseite mit Vergleich je Fahrzeugklasse, Kontaktseite mit Formular und Karte, Über-uns-Seite, ElbDetail Care, 7 Leistungsseiten (inkl. Keramikversiegelung und Lederaufbereitung), Online-Terminbuchung in 5 Schritten, Gutschein-Konfigurator mit Live-Vorschau, Firmenkunden-Seite, Winter-Aktionsseite, Ratgeber mit 10 Artikeln, Impressum, Datenschutz, 404, Danke-Seite |
| **SEO** | LocalBusiness/AutoDetailing-, Service-, FAQ-, BlogPosting-, Breadcrumb- und Product-Schema, Sitemap, RSS, Canonicals, Open Graph, sprechende Titel und Beschreibungen, interne Verlinkung |
| **GEO (KI-Suche)** | `llms.txt` und `llms-full.txt`, KI-Crawler in `robots.txt` erlaubt, „Das Wichtigste in Kürze“ in jedem Artikel, Faktenblock, zitierfähige FAQ |
| **Conversion** | Buchungsassistent mit Live-Preis und Sperrtagen, WhatsApp-Weg mit vorausgefüllter Nachricht, Gutscheinverkauf, Firmenanfrage, Danke-Seite, mobile Aktionsleiste |
| **Verwaltungsportal** `/admin` | Übersicht mit Statistik, Anfragen-Postfach mit Antwortvorlagen und Bewertungsanfrage, Gutscheinverwaltung mit Code-Prüfung, Kalender mit Sperrtagen, Inhalts-Editor für Preise, Texte und Ratgeber, Foto-Upload, Veröffentlichen per Knopfdruck |
| **Datenschutz** | Keine Cookies, keine Drittanbieter-Skripte, Statistik ohne IP-Speicherung, Google-Karte erst nach Klick, automatische Löschfristen |
| **Qualität** | 31 Server-Tests, 86 Browser-Tests (Desktop und Mobil, inklusive axe-Barrierefreiheit), Lighthouse 97–99 / 100 / 100 / 100 |

## Projektstruktur

```
content/      Inhalte als JSON und Markdown (Startvorlage, auf dem Server im Portal pflegbar)
static/       CSS, JavaScript, Schriften, Logo, Icons
build/        Website-Generator (Python, nur Standardbibliothek + Pillow für Bilder)
server/       App-Server und Verwaltungsportal (Python-Standardbibliothek)
deploy/       Dockerfile, docker-compose, Caddyfile, .env-Vorlage, Backup- und Update-Skript
tests/        Server-Tests (unittest) und Browser-Tests (Playwright)
docs/         Betrieb, Portal-Anleitung, Livegang-Checkliste, Marketing-Unterlagen
```

## Lokal starten

```bash
python3 build/build.py                         # Website nach dist/ bauen
ADMIN_PASSWORD=test COOKIE_SECURE=0 ELB_SERVE_STATIC=1 python3 server/app.py
# → http://localhost:8080 und http://localhost:8080/admin (Benutzer: admin, Passwort: test)
```

Tests:

```bash
pip install -r requirements.txt && npm ci
npm test
```

## Auf dem Server

Schritt-für-Schritt-Anleitung: [`docs/betrieb-hetzner.md`](docs/betrieb-hetzner.md). Kurzfassung:

```bash
git clone https://github.com/Markentrix/Neu.git /opt/elbdetail && cd /opt/elbdetail/deploy
cp .env.example .env && nano .env
docker compose up -d --build
```

## Dokumente

- [Betrieb auf Hetzner](docs/betrieb-hetzner.md)
- [Verwaltungsportal](docs/verwaltungsportal.md)
- [Livegang-Checkliste](docs/livegang-checkliste.md)
- [Markenleitfaden](docs/markenleitfaden.md)
- [Google-Unternehmensprofil-Kit](docs/google-unternehmensprofil.md)
- [Branchenverzeichnisse & lokale Backlinks](docs/branchenverzeichnisse.md)
- [Bewertungs-Prozess](docs/bewertungs-prozess.md)
- [Foto- und Video-Shotlist](docs/foto-und-video-shotlist.md)
- [Anzeigen-Kit Google & Meta](docs/anzeigen-kit.md)
