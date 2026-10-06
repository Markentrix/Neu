# Umzug von Jimdo auf den eigenen Server – Unabhängigkeit & Checkliste

## 1. Was ist schon unabhängig von Jimdo? (erledigt, im Repository)
| Inhalt | Stand |
|---|---|
| 338 Produktseiten mit Namen, Preisen, Varianten, Montage-Optionen, Texten, technischen Daten | als `src/catalog.json` gesichert, Seiten daraus generiert |
| 46 Ersatzteile | im Katalog |
| ~1.170 Produktbilder + Logo + Blog-Bilder | als WebP unter `site/assets/img/` (eigene Dateien, kein Hotlinking) |
| **88 Montage-/Bedienungsanleitungen (PDF/DOCX, ~210 MB)** | `site/downloads/` – **nicht im Git** (zu groß), liegen in `italiacamper24-downloads.zip`. Auf dem Server nach `/data/site/downloads/` kopieren (siehe unten) |
| 6 Ratgeber-Artikel, 239 Kundenbewertungen | in `src/content/` |
| Impressum, AGB, Datenschutz, Widerruf, Versand-/Zahlungsinfos | Originaltexte in `src/content/legal.json` (vor Go-Live rechtlich prüfen/ergänzen) |
| Schriften | selbst gehostet (kein Google-Fonts-Abruf) |
| 718 alte URLs → neue Seiten (301) | `server/redirects.json` |
| **Rohkopie der kompletten alten Website** (719 HTML-Seiten, Sitemap, Rohdaten) | `italiacamper24-jimdo-snapshot.zip` – zur Archivierung, falls später etwas nachgeschlagen werden muss |

Der laufende Shop lädt **nichts** von Jimdo nach (geprüft: keine Verweise auf jimdo/jimcdn im fertigen Shop). Wenn Jimdo abgeschaltet wird, läuft der neue Shop unverändert weiter.

## 2. Was liegt NUR bei Jimdo und muss VOR der Kündigung gesichert werden?
1. **Bestellungen & Kundendaten** (Jimdo-Shop → Bestellungen → Exportieren als CSV, alle Zeiträume) und **alle Rechnungen/Belege als PDF**. Gesetzliche **Aufbewahrungspflicht: 8 Jahre** (Buchungsbelege/Rechnungen, ab 2025 verkürzt von 10) bzw. 6 Jahre (Geschäftsbriefe) – nicht verlieren!
   → Schickt mir einen Beispiel-Export (ohne echte Kundendaten), dann baue ich den Import in die neue Datenbank.
2. **Domain**: Ist `italiacamper24.de` bei Jimdo registriert? Dann **zuerst die Domain umziehen** (KK-/Auth-Code beim Jimdo-Support anfordern, Transfer zu Hetzner/anderem Registrar, dauert bis ca. 5–7 Tage). **Jimdo erst kündigen, wenn die Domain bei euch liegt.**
3. **E-Mail**: Falls `info@italiacamper24.de` oder andere Postfächer über Jimdo/Jimdo-Mail laufen, vorher auf einen eigenen Mail-Anbieter umziehen (MX-Einträge!) und den SMTP-Zugang in `.env` eintragen. Alte Mails exportieren.
4. **Google-Konten**: Search Console (neue Property für die neue Seite verifizieren, `sitemap.xml` einreichen), Google Business Profil (Website-URL prüfen), Merchant Center/Ads falls vorhanden, Analytics/Tag-Manager-IDs falls genutzt (aktuell nutzt der neue Shop **kein** Tracking).
5. **YouTube-Videos**: 5 eingebettete Videos (IDs LyHiU0dhdMA, ulVxbsOtZ5g, _SkYhGz3fxU, GFjL31ZebXU, TvXPLfesXfQ) liegen bei YouTube, nicht bei Jimdo – prüfen, dass der YouTube-Kanal euch gehört.
6. **Formular-Eingänge/Anfragen** aus dem Jimdo-Postfach exportieren.

## 3. Umzug ohne Ausfall (Empfehlung)
1. Neuen Shop auf dem Hetzner-Server unter einer **Test-Subdomain** (z. B. `neu.italiacamper24.de`, `DOMAIN=` in `.env`) aufbauen und mit allen Zahlarten testen (`docs/HETZNER.md`).
2. Downloads kopieren: `scp italiacamper24-downloads.zip` auf den Server, entpacken nach dem Docker-Volume:
   `docker compose cp downloads/. app:/data/site/downloads/` (oder `docker compose exec app sh -c 'ls /data/site/downloads | wc -l'` zur Kontrolle: 88 Dateien).
3. Zwei Tage vor Umschaltung die **TTL** der DNS-Einträge auf 300 s senken.
4. Umschalten: A-/AAAA-Record von `www` und `@` auf die Hetzner-IP, `DOMAIN=www.italiacamper24.de` setzen, `docker compose up -d` → Caddy holt automatisch das HTTPS-Zertifikat.
5. Am selben Tag prüfen: Startseite, Fahrzeugfinder, Testbestellung, E-Mails, alte Jimdo-URLs (z. B. `/produkte/alu-matic-stützen/` → neue Produktseite), `sitemap.xml`, `robots.txt`.
6. Search Console: Sitemap einreichen, Indexierung beobachten (zwei bis vier Wochen).
7. **Jimdo erst nach 4 Wochen stabilem Betrieb und nach vollständigem Export (Abschnitt 2) kündigen.**

## 4. Dauerhaft selbst betreiben – was dazugehört
- Updates: `git pull && docker compose up -d --build`; Server-Updates (`unattended-upgrades` ist in der Anleitung aktiviert).
- Backups: täglich per Cron (`deploy/backup.sh`) + Hetzner-Snapshots + Kopie auf Storage Box.
- Zugangsdaten (Stripe, PayPal, SMTP) ausschließlich in `.env`, nicht im Git.
- Neue Produkte/Preise: Preise im Admin; neue Produkte derzeit über `src/catalog.json` bzw. Neuimport (auf Wunsch baue ich einen Produkt-Editor im Admin).
