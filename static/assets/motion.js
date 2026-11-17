/* Bewegung und kleine interaktive Bausteine der Startseite (Vorher-nachher-Regler, Tiefenwirkung der Bildbänder).
   Alles läuft im Browser, nichts wird gesendet. Bei reduzierter Bewegung gibt es keine Animation, die Bausteine bleiben bedienbar. */
(function () {
  'use strict';
  var d = document, w = window, root = d.documentElement;
  function reduced() { return root.classList.contains('reduced') || (w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches); }
  function track(name, params) { try { if (typeof w.gtag === 'function') w.gtag('event', name, params || {}); } catch (e) { } }

  /* ── Vorher und nachher ── */
  (function () {
    var ba = d.querySelector('[data-ba]'); if (!ba) return;
    var range = ba.querySelector('[data-ba-range]'); if (!range) return;
    var used = false;
    function set(v) { ba.style.setProperty('--p', v + '%'); }
    set(range.value);
    range.addEventListener('input', function () { used = true; set(range.value); });
    range.addEventListener('change', function () { track('before_after_use', { location: w.location.pathname }); });
    /* Einladung: beim ersten Sichtkontakt fährt der Regler einmal sanft hin und her */
    if (reduced() || !('IntersectionObserver' in w)) return;
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { io.disconnect(); hint(); } });
    }, { threshold: 0.6 });
    io.observe(ba);
    function hint() {
      var t0 = null, dur = 2200;
      function f(ts) {
        if (used) return;
        if (t0 === null) t0 = ts;
        var k = Math.min(1, (ts - t0) / dur);
        var v = 50 + Math.sin(k * Math.PI * 2) * 30 * (1 - k);
        range.value = String(Math.round(v)); set(range.value);
        if (k < 1) w.requestAnimationFrame(f); else { range.value = '50'; set('50'); }
      }
      w.requestAnimationFrame(f);
    }
  })();

  /* ── Tiefenwirkung der Bildbänder (nur breite Bildschirme, nicht bei reduzierter Bewegung) ── */
  (function () {
    if (reduced() || !w.matchMedia || !w.matchMedia('(min-width: 900px)').matches) return;
    var imgs = [].slice.call(d.querySelectorAll('.photo-band-img')); if (!imgs.length) return;
    var tick = false;
    function upd() {
      tick = false; var vh = w.innerHeight;
      imgs.forEach(function (im) {
        var b = im.parentElement.getBoundingClientRect(); if (b.bottom < -60 || b.top > vh + 60) return;
        var p = (b.top + b.height / 2 - vh / 2) / (vh / 2 + b.height / 2);
        im.style.setProperty('--py', (Math.max(-1, Math.min(1, p)) * -26).toFixed(1) + 'px');
      });
    }
    function req() { if (!tick) { tick = true; w.requestAnimationFrame(upd); } }
    w.addEventListener('scroll', req, { passive: true }); w.addEventListener('resize', req); upd();
    root.classList.add('has-parallax');
  })();
})();
