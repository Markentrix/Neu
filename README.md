# Italia Camper 24 – kompletter Shop (Tricolore-Redesign)

Vollwertiger Online-Shop mit **338 Produktseiten** (gesamtes Original-Sortiment), Fahrzeugfinder, Kasse, Kundenkonto, Admin-Bereich,
Zahlung per **PayPal, Kreditkarte/Apple Pay/Google Pay (Stripe), Überweisung und Rechnung**, E-Mails, Rechnungs-PDF – zum Betrieb auf dem **eigenen Hetzner-Server**.

| Ordner | Inhalt |
|---|---|
| `site/` | fertig generierte Seiten (HTML/CSS/JS/Bilder, Sitemap, llms.txt) |
| `src/` | Seitengenerator (`build.py`), Katalog (`catalog.json`), Inhalte |
| `server/` | Shop-Backend (Node 22, SQLite, Express) inkl. Admin (`/admin/`) und 12 E2E-Tests |
| `tools/` | Import vom Original (Crawl → Katalog, Bilder, 301-Weiterleitungen) |
| `deploy/`, `Dockerfile`, `docker-compose.yml` | Betrieb mit Docker + Caddy (automatisches HTTPS) |
| `docs/HETZNER.md` | **Schritt-für-Schritt-Anleitung für den Server** + Go-Live-Checkliste |

## Lokal ausprobieren
```bash
cd server && npm install
cp ../.env.example ../.env     # ADMIN_EMAIL / ADMIN_PASSWORD eintragen
npm start                      # http://localhost:3000   Admin: http://localhost:3000/admin/
npm test                       # 12 End-to-End-Tests (simulierte Stripe/PayPal-Server)
```
Ohne Stripe-/PayPal-Schlüssel werden diese Zahlarten automatisch ausgeblendet; Überweisung und Rechnung funktionieren sofort.

## Seiten neu erzeugen
`python3 src/build.py` (oder im Admin: *Produkte & Preise → Shop-Seiten neu generieren*, berücksichtigt geänderte Preise).
