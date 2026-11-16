# Lohnunternehmen Linneweh – Website-Redesign

Modernes, animiertes Redesign von lu-linneweh.com als statische Website (kein Framework, keine externen Abhängigkeiten, keine Cookies, Schriften lokal eingebunden).

## Aufbau

- `content/site.mjs` – Texte, Navigation, Leistungen, News, Team (Inhalte der Originalseite)
- `content/services.json` – Maschinen und technische Daten der Leistungs-Detailseiten
- `content/legal.json` – Impressum, AGB und Datenschutz (unverändert übernommen)
- `build.mjs` – Seitengenerator, erzeugt alle 39 Seiten nach `site/`
- `site/assets/` – CSS, JavaScript, Bilder (WebP) und Schriften

## Befehle

```bash
node build.mjs                          # Seiten neu erzeugen
cd site && python3 -m http.server 8080  # lokale Vorschau: http://localhost:8080
```

Veröffentlicht wird der Ordner `site/` (für Netlify liegt `netlify.toml` bei).
