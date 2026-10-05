# Performance & Ladezeiten

Ziele und Budget stehen im SKILL (Abschnitt 6). Hier die Rezepte. Immer erst messen, dann optimieren.

## Messen
- Lab: Lighthouse (mobil, gedrosselt), WebPageTest. Feld: PageSpeed Insights/CrUX, Search Console (Core Web Vitals). Lab ≠ Feld, getrennt berichten.
- Chrome DevTools: Performance-Panel für INP/Long Tasks, Network-Panel für Requests (0 Drittanbieter vor Consent).

## LCP (Largest Contentful Paint)
- LCP-Element identifizieren (meist Hero-Bild oder Headline). Hero-Bild: `fetchpriority="high"`, **nicht** lazy, per `<link rel="preload" as="image" imagesrcset=… imagesizes=…>` wenn es per CSS geladen wird.
- Bildgrößen exakt (`srcset` + `sizes`), AVIF → WebP → JPG, Qualität 60–75, Ziel Hero ≤ 100 KB mobil. Alternative: reine CSS/SVG-Grafik (Wachstumskurve als Inline-SVG).
- Kein Render-Blocking: kritisches CSS inline, Rest `media="print" onload` oder `rel=preload`. Keine blockierenden Skripte im `<head>`.
- TTFB: statisches Hosting/CDN in der EU, Brotli, HTTP/2/3, Caching (`Cache-Control: public, max-age=31536000, immutable` für gehashte Assets, HTML kurz oder `no-cache` mit ETag).
- Fonts: WOFF2, variable, Subset Latin (+ nötige Sonderzeichen: ä ö ü ß „ “ € –), `font-display: swap`, nur 1–2 Dateien preloaden (`crossorigin`), `size-adjust`/Fallback-Metriken gegen Layout-Shift.

## CLS (Layout-Shift)
- `width`/`height` oder `aspect-ratio` an allen Bildern/Videos/Iframes/Platzhaltern.
- Platz für Banner, Embeds, späte Inhalte reservieren; Banner als Overlay am unteren Rand, nicht Inhalt nach unten schieben.
- Keine Inhalte über bestehende Inhalte einfügen; Animationen nur `transform`/`opacity`.
- Font-Fallback abgleichen.

## INP (Interaktion)
- Wenig JS (Budget ≤ 60 KB gzip), keine Hydration ganzer Seiten für statische Inhalte.
- Lange Tasks (> 50 ms) aufteilen (`scheduler.yield()`/`setTimeout`), Event-Handler schlank, `passive: true` für Scroll/Touch.
- Scroll-Effekte per `IntersectionObserver` oder CSS Scroll-Driven Animations statt `scroll`-Event-Handler.
- Third-Party erst nach Consent und nach Idle laden (`requestIdleCallback`).

## Ressourcen
- Ein CSS-File (+ inline kritisch), ein JS-Module-File, `defer`. Kein jQuery, keine Icon-Fonts: Inline-SVG-Sprite.
- `loading="lazy"` + `decoding="async"` für Bilder unter dem Fold; Videos: `preload="none"` + Poster, kein Autoplay-Hintergrundvideo mobil (Datenschutz egal, Datenvolumen und Akku zählen); wenn Video, ≤ 1 MB, H.264+WebM, `playsinline muted loop`, Pause-Button, Reduced-Motion → Poster.
- `content-visibility: auto` + `contain-intrinsic-size` für lange Sektionen unter dem Fold.
- Preconnect nur zu Hosts, die wirklich vorher gebraucht werden (bei 0 Drittanbietern: keiner).
- Speculation Rules / `<link rel="prefetch">` für den wahrscheinlichen nächsten Schritt (Danke-Seite) optional.

## Build-Pipeline (Empfehlung)
Bilder: `sharp`/Squoosh → AVIF/WebP/JPG in 3–4 Breiten. CSS/JS minifizieren (esbuild/lightningcss), Hash im Dateinamen. HTML minifizieren. Fonts: `pyftsubset`/glyphhanger. Prüfen: `scripts/audit.sh`.

## Header-Vorlage (Hosting/Netlify `_headers` o. ä.)
```
/*
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
/assets/*
  Cache-Control: public, max-age=31536000, immutable
```
CSP an Formularziel/Consent-Tool anpassen (`form-action`, `connect-src`), Drittquellen nur nach Freigabe ergänzen. Inline-Style des kritischen CSS ggf. per Hash/Nonce statt `unsafe-inline`.
