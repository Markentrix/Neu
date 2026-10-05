# Animation & Motion

Zweck: führen, Zustand erklären, Hochwertigkeit zeigen. Nie Selbstzweck. Premium = ruhig, präzise, kurz. Kein Neon-Glow, kein Parallax-Overkill, kein Dauer-Geflimmer.

## Regeln
1. **CSS first.** JS nur für Scroll-Orchestrierung, Zustände, Zählwerke. Kein GSAP/Lottie ohne klaren Nutzen und Budget (JS ≤ 60 KB gzip).
2. Nur `transform` und `opacity` animieren (GPU, kein Layout/Paint). Nie `width/height/top/left/margin/box-shadow` animieren. `will-change` nur kurz und gezielt.
3. Dauer: Mikro 120–200 ms, Elemente 250–450 ms, Sektionen max. 600 ms. Easing: Eintritt `cubic-bezier(.22,1,.36,1)`, Austritt `cubic-bezier(.4,0,1,1)`. Kein linear außer bei Dauerbewegung.
4. Stagger 40–80 ms, max. 6 Elemente, Gesamt < 700 ms.
5. **Nichts darf Inhalt verstecken, wenn JS/Animation fehlt.** Startzustand `opacity:0` nur unter `.js` + `@media (prefers-reduced-motion: no-preference)` setzen.
6. **`prefers-reduced-motion: reduce` respektieren:** Bewegung entfernen (Fades dürfen bleiben, kurz), keine Autoplay-Videos, Zählwerke direkt auf Endwert.
7. Above-the-fold-Inhalt (LCP) nie hinter Animation verstecken. Hero erscheint sofort, höchstens subtile Zusatzbewegung.
8. Nie blinken > 3×/s; Autoplay-Bewegung > 5 s braucht Pause-Möglichkeit (WCAG 2.2.2).
9. Max. EIN dominantes Bewegungselement pro Sektion (CI-Signature: Wachstumskurve).
10. Hover-Effekte nur ergänzend, Fokus-Zustand gleichwertig. Touch hat kein Hover.

## Rezepte
**Reveal beim Scrollen (IntersectionObserver, ~15 Zeilen, siehe Starter `main.js`):**
```css
@media (prefers-reduced-motion: no-preference) {
  .js [data-reveal] { opacity:0; transform:translateY(16px);
    transition: opacity .5s var(--ease-out), transform .5s var(--ease-out); }
  .js [data-reveal].is-in { opacity:1; transform:none; }
}
```
**Wachstumskurve zeichnen (SVG-Linie, CSS only):**
```css
.curve path { stroke-dasharray: 1; stroke-dashoffset: 1; }
@media (prefers-reduced-motion: no-preference) {
  .curve.is-in path { animation: draw 1.2s var(--ease-out) forwards; }
}
@keyframes draw { to { stroke-dashoffset: 0; } }
/* path mit pathLength="1" */
@media (prefers-reduced-motion: reduce) { .curve path { stroke-dashoffset: 0; } }
```
**Scroll-Driven Animation (modern, kein JS, Progressive Enhancement):**
```css
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .card { animation: rise linear both; animation-timeline: view(); animation-range: entry 0% cover 30%; }
  }
}
@keyframes rise { from { opacity:0; transform: translateY(24px);} to { opacity:1; transform:none; } }
```
**Button-Feedback:** `transform: translateY(-1px)` + Schatten-Opacity auf Pseudo-Element, `:active` zurück. Verlauf-Shift per `background-position`, nicht per Farbwechsel-Repaint-Spam.
**Zählwerk (Kennzahlen):** nur für **freigegebene** Zahlen. `aria-label` mit Endwert, `prefers-reduced-motion` → direkt Endwert.
**Seitenübergang:** `@view-transition { navigation: auto; }` (optional), Reduced-Motion aus.
**Hintergrund:** statische oder sehr langsame (> 20 s) Verlaufsbewegung, per Opacity; `animation-play-state` pausiert, wenn Tab/Section nicht sichtbar.

## Globaler Not-Aus
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important;
    transition-duration:.01ms !important; scroll-behavior:auto !important; }
}
```

## Test
Mit gedrosselter CPU (4×) im Performance-Panel: keine Frames < 50 fps, kein Layout-Shift durch Animation, Reduced-Motion-Modus per DevTools-Rendering-Panel, Tastatur-Fokus während Animationen weiterhin sichtbar.
