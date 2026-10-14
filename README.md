# Markentrix Website · markentrix.de

Statische Website im Markentrix-Design-System „White / Light Premium“ (CI 2026). Kein Framework, kein CDN, keine Build-Abhängigkeiten außer Python 3.

```
src/layout.html      gemeinsames Gerüst (Head, Header, Footer, Mobile-Navigation, Potenzial-Check-Modal)
src/pages/           eine Datei je Seite: Front-Matter + Inhalt
src/partials/        Icon-Sprite, Wachstumskurve
static/              assets/mx.css (Design-System), assets/site.js (Laufzeit), assets/consent.js, fonts/, img/, robots.txt, _headers, llms.txt
tools/build.py       baut dist/ und prüft Links, Anker, h1, Titel-/Description-Längen
dist/                veröffentlichter Ordner (Netlify: publish = "dist")
docs/                Konventionen (SEITENBAU.md), Prüfbericht, Deployment, Brand-Dateien (CI, Preisliste)
```

## Bauen
```
python3 tools/build.py --check
```
Lokal ansehen: `cd dist && python3 -m http.server 8080` → http://localhost:8080/

## Seiten ändern
Inhalte stehen in `src/pages/**.html`, Gestaltung ausschließlich in `static/assets/mx.css`. Konventionen und Komponentenkatalog: `docs/SEITENBAU.md`. Nach jeder Änderung bauen und `dist/` mit committen.

## Deployment
Produktiv läuft die Seite auf einem Hetzner-Server mit nginx (`docs/nginx-markentrix.conf`, inkl. PHP-Endpunkt für die Formulare). `netlify.toml` bleibt für Vorschau-Deploys. Details: `docs/DEPLOY.md`.
