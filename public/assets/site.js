/* PS Schneider – kleine Helfer, kein Tracking, keine externen Aufrufe */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* Jahr im Footer */
  $$('[data-year]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });

  /* Mobile Navigation */
  var header = $('.site-header'), toggle = $('.nav-toggle');
  if (header && toggle) {
    var setOpen = function (open) {
      header.setAttribute('data-open', open ? 'true' : 'false');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Menü schließen' : 'Menü öffnen');
    };
    toggle.addEventListener('click', function () {
      setOpen(header.getAttribute('data-open') !== 'true');
    });
    $$('.primary-nav a').forEach(function (a) { a.addEventListener('click', function () { setOpen(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  }

  /* Auf schmalen Bildschirmen sind alle Fragen zunächst zugeklappt, das verkürzt die Seite */
  if (window.matchMedia && window.matchMedia('(max-width: 820px)').matches) {
    $$('.faq details[open]').forEach(function (d) { d.removeAttribute('open'); });
  }

  /* Kopieren-Buttons */
  $$('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || '';
      var done = function () {
        btn.textContent = 'kopiert';
        setTimeout(function () { btn.textContent = 'kopieren'; }, 1600);
      };
      var fallback = function () {
        var row = btn.closest('li');
        var el = row && row.querySelector('.v');
        if (el && window.getSelection) {
          var range = document.createRange();
          range.selectNodeContents(el);
          var sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
        }
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else { fallback(); }
    });
  });

  /* Unfall-Checkliste, Haken bleiben im Browser des Besuchers gespeichert */
  var boxes = $$('#checklist input[type="checkbox"]');
  if (boxes.length) {
    var KEY = 'psschneider-checkliste';
    var progress = $('#checklist-progress');
    var load = function () {
      try {
        var s = JSON.parse(localStorage.getItem(KEY) || '{}');
        boxes.forEach(function (b) { b.checked = !!s[b.id]; });
      } catch (e) { /* ohne Speicher weiter */ }
    };
    var save = function () {
      try {
        var s = {};
        boxes.forEach(function (b) { s[b.id] = b.checked; });
        localStorage.setItem(KEY, JSON.stringify(s));
      } catch (e) { /* ohne Speicher weiter */ }
    };
    var update = function () {
      var n = boxes.filter(function (b) { return b.checked; }).length;
      if (progress) progress.textContent = n + ' von ' + boxes.length + ' erledigt' + (n === boxes.length ? '. Gut gemacht.' : '');
    };
    boxes.forEach(function (b) { b.addEventListener('change', function () { save(); update(); }); });
    var reset = $('#checklist-reset');
    if (reset) reset.addEventListener('click', function () {
      boxes.forEach(function (b) { b.checked = false; });
      save(); update();
    });
    load(); update();
  }
})();
