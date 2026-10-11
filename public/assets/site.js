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

  /* Kontaktformular: prüft die Eingaben und öffnet das E-Mail-Programm mit fertigem Text */
  var form = $('#contact-form');
  if (form) {
    var status = $('#form-status'), preview = $('#form-preview');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = $('#f-name').value.trim();
      var email = $('#f-email').value.trim();
      var phone = $('#f-phone').value.trim();
      var subject = $('#f-subject').value;
      var message = $('#f-message').value.trim();
      var consent = $('#f-consent').checked;
      var missing = [];
      if (!name) missing.push('Name');
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) missing.push('gültige E-Mail');
      if (!subject) missing.push('Anliegen');
      if (!message) missing.push('Nachricht');
      if (!consent) missing.push('Zustimmung zur Datenschutzerklärung');
      if (missing.length) {
        status.className = 'form-status err';
        status.textContent = 'Bitte ergänzen: ' + missing.join(', ') + '.';
        return;
      }
      var body = 'Anliegen: ' + subject + '\n' + 'Name: ' + name + '\n' + 'E-Mail: ' + email + '\n' +
        (phone ? 'Telefon: ' + phone + '\n' : '') + '\n' + message;
      var href = 'mailto:info@psschneider.de?subject=' + encodeURIComponent('Anfrage: ' + subject) +
        '&body=' + encodeURIComponent(body);
      preview.textContent = 'An: info@psschneider.de\nBetreff: Anfrage: ' + subject + '\n\n' + body;
      preview.setAttribute('data-show', 'true');
      status.className = 'form-status ok';
      status.textContent = 'Ihr E-Mail-Programm öffnet sich mit der fertigen Anfrage. Falls nicht, kopieren Sie den Text unten und senden ihn an info@psschneider.de.';
      window.location.href = href;
    });
  }
})();
