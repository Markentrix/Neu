# ElbDetail – Website

Verkaufsorientierte Website für **ElbDetail – Premium Fahrzeugaufbereitung in Celle**, mit Online-Terminbuchung, Gutscheinanfrage, Firmenkunden-Anfragen, Ratgeber, AGB und Widerruf. Die Website ist rein statisch und läuft beim **Markentrix-Portal**: Formulare, Termine, Bewertungen, Statistik und Cookie-Hinweis kommen von dort.

## Was drin ist

| Bereich | Inhalt |
|---|---|
| **Website** | Kompakte Startseite mit Richtpreis-Rechner, Preisseite mit Vergleich je Fahrzeugklasse, Kontaktseite mit Formular und Karte, Über-uns-Seite, ElbDetail Care, 7 Leistungsseiten (inkl. Keramikversiegelung und Lederaufbereitung), Online-Terminbuchung in 5 Schritten, Gutschein-Konfigurator mit Live-Vorschau, Firmenkunden-Seite, Winter-Aktionsseite, Ratgeber mit 10 Artikeln, Impressum, Datenschutz, 404, Danke-Seite |
| **SEO** | LocalBusiness/AutoDetailing-, Service-, FAQ-, BlogPosting-, Breadcrumb- und Product-Schema, Sitemap, RSS, Canonicals, Open Graph, sprechende Titel und Beschreibungen, interne Verlinkung |
| **GEO (KI-Suche)** | `llms.txt` und `llms-full.txt`, KI-Crawler in `robots.txt` erlaubt, „Das Wichtigste in Kürze“ in jedem Artikel, Faktenblock, zitierfähige FAQ |
| **Conversion** | Buchungsassistent mit Live-Preis und Sperrtagen, WhatsApp-Weg mit vorausgefüllter Nachricht, Gutscheinverkauf, Firmenanfrage, Danke-Seite, mobile Aktionsleiste |
| **Markentrix-Portal** | Anfragen über `/api/anfrage`, freie Tage und Uhrzeiten über `/api/verfuegbarkeit` und `/api/slots`, Bausteine `bewertungen` und `cookies`, Statistik über `/api/e` (siehe `docs/portal-upload.md`) |
| **Datenschutz** | Schriften lokal, keine Fremd-CDNs, kein eigenes Tracking, Cookie-Hinweis vom Portal, Google-Karte erst nach Klick |
| **Qualität** | Generator-Tests mit den Upload-Regeln des Portals, Browser-Tests (Desktop und Mobil, axe-Barrierefreiheit) gegen eine Attrappe der Portal-Schnittstelle |

## Projektstruktur

```
content/         Inhalte als JSON und Markdown (Texte, Preise, Bilder, Angebote, Ratgeber)
static/          CSS, JavaScript, Schriften, Logo, Icons
build/           Website-Generator (Python, Standardbibliothek + Pillow für Bilder), läuft nur beim Bauen
website-fertig/  fertige Website zum Hochladen (wird erzeugt, nicht im Repository)
tests/           Generator-Tests (unittest), Browser-Tests (Playwright) und Portal-Attrappe für die Tests
docs/            Upload, Livegang-Checkliste, Marketing-Unterlagen
```

## Bauen und prüfen

```bash
pip install -r requirements.txt && npm ci
python3 build/build.py          # → website-fertig/
npm test                        # Upload-Regeln, Seiten, Formulare, Barrierefreiheit
```

Hochladen: Ordner `website-fertig/` als ZIP ins Markentrix-Portal, Anleitung in [`docs/portal-upload.md`](docs/portal-upload.md).

## Dokumente

- [Upload ins Markentrix-Portal](docs/portal-upload.md)
- [Livegang-Checkliste](docs/livegang-checkliste.md)
- [Markenleitfaden](docs/markenleitfaden.md)
- [Google-Unternehmensprofil-Kit](docs/google-unternehmensprofil.md)
- [Branchenverzeichnisse & lokale Backlinks](docs/branchenverzeichnisse.md)
- [Bewertungs-Prozess](docs/bewertungs-prozess.md)
- [Foto- und Video-Shotlist](docs/foto-und-video-shotlist.md)
- [Anzeigen-Kit Google & Meta](docs/anzeigen-kit.md)
