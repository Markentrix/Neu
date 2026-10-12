/* PS Schneider – kleine Helfer, kein Tracking, keine externen Aufrufe */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  /* Texte in der Sprache der Seite (html lang) */
  var EN = document.documentElement.lang === 'en';
  var TXT = EN
    ? { copied: 'copied', copy: 'copy', done: ' done', of: ' of ', well: '. Well done.' }
    : { copied: 'kopiert', copy: 'kopieren', done: ' erledigt', of: ' von ', well: '. Gut gemacht.' };

  /* Jahr im Footer */
  $$('[data-year]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });

  /* Auf schmalen Bildschirmen sind alle Fragen zunächst zugeklappt, das verkürzt die Seite */
  if (window.matchMedia && window.matchMedia('(max-width: 820px)').matches) {
    $$('.faq details[open]').forEach(function (d) { d.removeAttribute('open'); });
  }

  /* Kopieren-Buttons */
  $$('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || '';
      var done = function () {
        btn.textContent = TXT.copied;
        setTimeout(function () { btn.textContent = TXT.copy; }, 1600);
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
      if (progress) progress.textContent = n + TXT.of + boxes.length + TXT.done + (n === boxes.length ? TXT.well : '');
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
