# Seitenbau-Konventionen · Markentrix Website 2026

Verbindlich für alle Seiten in `src/pages/`. Grundlage: `docs/brand/Markentrix_CI_2026_White_Light_Premium_MASTER.pdf`.

## Aufbau des Projekts
```
src/layout.html        Gerüst: Head, Header, Footer, Mobile-Navigation, Potenzial-Check-Modal
src/pages/**/*.html    eine Datei je Seite = Front-Matter + Inhalt von <main>
src/partials/*.html    Bausteine: {{> icons}} (SVG-Sprite), {{> signature}} (Wachstumskurve)
static/                wird 1:1 nach dist/ kopiert (assets/mx.css, assets/site.js, fonts, img, …)
tools/build.py         python3 tools/build.py --check   → baut dist/ und prüft Links, Anker, h1
```
Bauen immer mit Sperre, damit sich parallele Builds nicht überschreiben:
`flock /tmp/mx-build.lock python3 tools/build.py --check`

## Front-Matter (Pflicht)
```
---
title: Seitentitel ≤ 62 Zeichen | Markentrix
description: 120–160 Zeichen, eindeutig je Seite.
path: /pfad            (Startseite: / · Unterordner: /leistungen/webdesign)
lastmod: 2026-10-12
robots: noindex, nofollow      (nur wenn nötig, z. B. 404, KI-Checkliste)
sitemap: false                 (nur 404)
og_type: article               (nur Blogartikel)
ld: |
  {"@context":"https://schema.org", … }   (ein JSON-Objekt, eine Zeile, gültiges JSON)
---
```
Danach folgt direkt der Inhalt von `<main>` (ohne `<main>`-Tag). Erste Zeile: `{{> icons}}`, wenn Icons benutzt werden.

## Regeln
1. **Keine Inline-Styles**, kein `<style>`, kein `<script>` in Seiten. Alles kommt aus `mx.css` und `site.js`. Fehlt eine Komponente: in `mx.css` ergänzen (Abschnitt passend wählen, Tokens benutzen).
2. **Genau eine `<h1>`** je Seite, Überschriftsebenen nicht überspringen. Lange h1 auf Unterseiten: `class="h1--md"`.
3. **Links root-absolut**: `/preise`, `/leistungen/webdesign`, `/img/…`, `/datenschutz#s5`. Keine `.html`-Endungen, keine `../`.
4. **Texte und Aussagen bleiben inhaltlich erhalten.** Keine neuen Versprechen, keine Zahlen ohne Quelle, keine Kundennamen. Preise nur wie in `/preise` (Stand 01.10.2026, netto). Sprache: direkt, fachlich, nutzenorientiert. Keine Floskeln („innovativ“, „ganzheitlich“, „Gamechanger“), keine Superlative. Keine Gedankenstriche als Satzzeichen, stattdessen Punkt oder Komma. Anrede „Sie“.
5. **Meta, Canonical, JSON-LD** jeder alten Seite übernehmen und auf die neuen URLs/Pfade anpassen (`ld:` im Front-Matter). JSON muss parsebar sein (der Build prüft das).
6. **Bilder** mit `width`, `height`, `alt`, `loading="lazy"` (außer Hero). Vorhandene Bilder: `/img/christian-wien-480.webp` (480×480), `/img/christian-wien-640.webp`, `/img/ki-agent-dashboard-1600.webp` (1600×640), `/img/ki-agent-dashboard-960.webp` (960×384), `/img/pony-club-lila-1200.webp` (1200×628). Keine externen Bilder, keine Hotlinks.
7. **Farben**: nur CSS-Variablen aus `mx.css`. Navy für Headlines, Cyan→Blue nur für die primäre CTA (`btn--primary`), Violet nur als Akzent (`pill--violet`, `card-icon--violet`, `eyebrow`). Pro Abschnitt genau eine primäre Handlung.
8. **Dunkle Fläche** nur als bewusste Kontrastfläche: `.band` einmal je Seite als Abschluss-CTA (Vorlage in `src/pages/preise.html`).
9. **Barrierefreiheit**: `aria-labelledby` an Sections, Formfelder mit `label for`, Buttons mit Text oder `aria-label`, Fokus sichtbar (kommt aus dem System).
10. **Kein Dark-Mode-Umschalter, keine Partikel-/Canvas-Hintergründe, keine Marquee-Animationen.** Ruhe ist Teil der Marke.

## Komponenten (Auszug, alle in `static/assets/mx.css`)
| Zweck | Markup |
|---|---|
| Seitenkopf | `<section class="sec sec--white"><div class="wrap"><ol class="breadcrumb">…</ol><div class="sec-head"><span class="eyebrow">…</span><h1>…</h1><p class="lead">…</p></div></div></section>` |
| Abschnitt | `<section class="sec" aria-labelledby="id"><div class="wrap"><div class="sec-head [center]"><span class="eyebrow">…</span><h2 id="id">…</h2><p class="lead">…</p></div> … </div></section>` |
| Raster | `grid grid--2` / `grid--3` / `grid--4` / `grid--split` (50/50, vertikal zentriert) / `grid--sidebar` (breit + schmal) / `grid--sidebar-left` |
| Karte | `<div class="card [card--hover] [card--accent] [card--violet] [card--soft] [card--lg] reveal"><span class="card-icon [card-icon--violet|--navy]"><svg><use href="#i-phone"/></svg></span><h3>…</h3><p class="muted">…</p><a class="link-arrow" href="…">Mehr</a></div>` (auch als `<a class="card card--hover">`) |
| Schritt-Label | `<span class="card-step">Schritt 1</span>` · Badge `<span class="pill [pill--violet|--soft|--navy|--ok|--live]">…</span>` |
| Buttons | `btn btn--primary` (eine je Modul) · `btn--secondary` · `btn--ghost` · `btn--navy` · Größen `btn--lg` / `btn--sm` / `btn--block`. Potenzial-Check-Modal öffnen: `href="/kontakt" data-open-modal` |
| Listen | `<ul class="checks [checks--violet|checks--x]">` · `<div class="feat"><span class="card-icon">…</span><div><b>Titel</b><p>Text</p></div></div>` · `<dl class="dl dl--lined"><dt>…</dt><dd>…</dd></dl>` |
| Kennzahlen | `<div class="stats"><div><b>24<sup>/7</sup></b><span>…</span></div>…</div>` (4 Felder) · `<div class="kpi"><b class="blue">5–15</b><span>…</span></div>` |
| Prozess | `<ol class="steps"><li class="step"><h3>Titel <span class="pill pill--soft">Dauer</span></h3><p>…</p><p class="result">Sie erhalten: …</p></li></ol>` · kompakt: `<ol class="timeline"><li><b>Schritt</b>Text</li>…</ol>` (6 Einträge) |
| FAQ | `<details class="faq"><summary>Frage</summary><div class="faq-body"><p>Antwort</p></div></details>` · neutraler Aufklapper: `details.details` + `.details-body` |
| Hinweis | `<div class="note [note--violet|note--warn|note--navy]"><svg><use href="#i-info"/></svg><div><b>…</b> …</div></div>` · Zitat `<blockquote class="quote">… <cite>…</cite></blockquote>` |
| Preise | `price-card [price-card--featured]` mit `.pill`, `.price` (+`<small>/Monat</small>`), `.price-setup`, `.price-limit` |
| Formular | `<form class="form" data-lead="Quelle" novalidate>` + `.form-row` + `.field` (`label for` + `input name`) + `.check` + `.hp` (Honeypot) + `.form-msg` + Submit. Pflichtfelder `required`. Optional Wunschtermin: `<div data-calendar></div>`. Senden übernimmt `site.js` (n8n-Webhook, Felder `name,email,tel,firma,thema,budget,nachricht_text,einwilligung`). |
| Rechner (ROI) | Container `data-roi`; Eingaben `input[type=range]` mit `name` = `calls, msgs, sched, wage, missed, order` + `id` und `<output for="id">`; Ausgaben `data-out` = `manual, lost, pkg, pkgPrice, hours, net, pkgNote`. Kopf je Regler: `<div class="range-head"><label for="id">…</label><output for="id">…</output></div>` |
| Blog-Übersicht | Filter `<div class="filter" data-filter><button aria-pressed="true" data-cat="alle">Alle</button>…</div>`; Beiträge `<a class="post-card" data-cat="seo" href="…"><div class="post-meta"><b>SEO/GEO</b><span>01.10.2026</span><span>6 Min.</span></div><h2>…</h2><p>…</p></a>` |
| Blogartikel | `wrap wrap--narrow`, `<ol class="breadcrumb">`, `.post-meta`, `<div class="toc">`, `<article class="prose">`, `<div class="author">`, FAQ mit `details.faq`, Quellen als `<ol>` |
| Rechtstext | `<div class="wrap wrap--narrow"><article class="legal">…</article></div>`; Anker-IDs der alten Seite beibehalten (z. B. `#s5` in der Datenschutzerklärung, wird vom Consent-Banner verlinkt) |
| Demo-Darstellungen | `.demo` + `.demo-tag` („Beispieldarstellung“), `.bubble` / `.bubble--ai`, `.chips`, `.week` |
| Abschluss-CTA | `<div class="band"><div class="wrap-inner"><span class="eyebrow">…</span><h2>…</h2><p class="lead">…</p><div class="row mt-3"><a class="btn btn--primary btn--lg" href="/kontakt" data-open-modal>…</a><a class="btn btn--secondary btn--lg" href="…">…</a></div></div></div>` |
| Animation | `class="reveal"` (+ `data-delay="1|2|3"`) an Karten, nicht an Text-Abschnitten |
| Abstände | `mt-1…mt-5`, `mb-1…mb-4`, `center`, `small`, `tiny`, `muted`, `measure` |

Icons im Sprite (`{{> icons}}`): `i-phone i-chat i-mail i-calendar i-bolt i-globe i-target i-chart i-shield i-user i-clock i-check i-info i-layout i-cpu i-pin i-star i-arrow i-euro i-pen i-search i-book`.

## Qualitätskontrolle je Seite
1. `flock /tmp/mx-build.lock python3 tools/build.py --check` ohne Fehler für die eigene Seite.
2. Screenshot Desktop (1440) und Mobil (390) ansehen: kein horizontales Scrollen, keine überlappenden Elemente, eine h1, Kontrast ok.
3. Alle alten Inhalte vorhanden (Texte, Preise, Rechtstexte vollständig).
