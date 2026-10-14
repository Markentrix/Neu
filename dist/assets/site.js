/* Markentrix · Laufzeit für alle Seiten (kein Framework, kein CDN)
   Module: Navigation, Reveal, Formulare (n8n-Webhook), Potenzial-Check-Modal,
   Wunschtermin-Kalender, Kurzcheck/ROI-Rechner, Blog-Filter, Barrierefreiheit. */
(function () {
  'use strict';
  var d = document, w = window;
  /* Versandweg der Formulare: eigener Endpunkt auf dem Server (dist/api/anfrage.php, gleiche Domain, kein CORS).
     Der Endpunkt mailt an info@markentrix.de und kann zusätzlich an einen Webhook (n8n o. ä.) weiterleiten,
     siehe $CONFIG in static/api/anfrage.php. Hinweis: markentrix.app.n8n.cloud antwortete am 14.10.2026 mit 404. */
  var ENDPOINT = '/api/anfrage.php';
  d.documentElement.classList.remove('no-js');
  if (w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches) d.documentElement.classList.add('reduced');

  function $(sel, root) { return (root || d).querySelector(sel); }
  function $$(sel, root) { return [].slice.call((root || d).querySelectorAll(sel)); }
  function on(el, ev, fn) { if (el) el.addEventListener(ev, fn); }
  function fmtEUR(n) { return Math.round(n).toLocaleString('de-DE') + ' €'; }
  function track(name, params) { try { if (typeof w.gtag === 'function') w.gtag('event', name, params || {}); } catch (e) { } }

  /* ── Navigation ─────────────────────────────────────────────────────── */
  function initNav() {
    var header = $('.site-header'); if (!header) return;
    // aktive Seite markieren
    var path = location.pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '');
    $$('.nav-links a, .mobile-panel a').forEach(function (a) {
      var h = a.getAttribute('href') || '';
      if (h && h !== '/' && path.indexOf(h) === 0) a.setAttribute('aria-current', 'page');
      if (h === '/' && (path === '/' || path === '')) a.setAttribute('aria-current', 'page');
    });
    // Dropdown schließen bei Klick außerhalb / Escape
    var dds = $$('.nav-links details');
    on(d, 'click', function (e) { dds.forEach(function (dd) { if (!dd.contains(e.target)) dd.removeAttribute('open'); }); });
    on(d, 'keydown', function (e) { if (e.key === 'Escape') dds.forEach(function (dd) { dd.removeAttribute('open'); }); });
    // Burger
    var btn = $('.burger'), panel = $('.mobile-panel');
    if (!btn || !panel) return;
    var ICON_OPEN = btn.innerHTML;
    var ICON_CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
    function open() { panel.classList.add('is-open'); d.body.classList.add('menu-open'); btn.setAttribute('aria-expanded', 'true'); btn.setAttribute('aria-label', 'Menü schließen'); btn.innerHTML = ICON_CLOSE; var f = $('a,button', panel); if (f) f.focus({ preventScroll: true }); }
    function close() { if (!panel.classList.contains('is-open')) return; panel.classList.remove('is-open'); d.body.classList.remove('menu-open'); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-label', 'Menü öffnen'); btn.innerHTML = ICON_OPEN; }
    on(btn, 'click', function () { panel.classList.contains('is-open') ? close() : open(); });
    on(panel, 'click', function (e) { if (e.target.closest('a')) close(); });
    on(d, 'keydown', function (e) { if (e.key === 'Escape' && panel.classList.contains('is-open')) { close(); btn.focus(); } });
    on(w, 'resize', function () { if (w.innerWidth > 1060) close(); });
  }

  /* ── Reveal ─────────────────────────────────────────────────────────── */
  function markIn(el) { if (el.classList.contains('is-in')) return; el.classList.add('is-in'); try { el.dispatchEvent(new CustomEvent('mx:in')); } catch (e) { } }
  function initReveal() {
    var els = $$('.reveal, .statement, .band, .proof-seo, .stats, .seq'); if (!els.length) return;
    if (!('IntersectionObserver' in w) || d.documentElement.classList.contains('reduced')) { els.forEach(markIn); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { markIn(en.target); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    els.forEach(function (e) { io.observe(e); });
    setTimeout(function () { els.forEach(markIn); }, 4000); // Sicherheitsnetz
  }

  /* ── Formulare ──────────────────────────────────────────────────────── */
  function postLead(payload) {
    payload.seite = location.pathname; payload.zeit = new Date().toISOString();
    var ctrl = ('AbortController' in w) ? new AbortController() : null;
    var timer = ctrl && setTimeout(function () { ctrl.abort(); }, 12000);
    return fetch(ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { clearTimeout(timer); return { ok: r.ok, status: r.status }; })
      .catch(function (e) { clearTimeout(timer); return { ok: false, status: 0, timeout: e && e.name === 'AbortError' }; });
  }
  function fieldWrap(input) { return input.closest('.field') || input.closest('.check') || input.parentNode; }
  function setError(input, msg) {
    var wrap = fieldWrap(input); if (!wrap) return;
    wrap.classList.add('has-error'); input.setAttribute('aria-invalid', 'true');
    var err = wrap.querySelector('.error'); if (!err) { err = d.createElement('div'); err.className = 'error'; wrap.appendChild(err); }
    err.textContent = msg;
  }
  function clearError(input) { var wrap = fieldWrap(input); if (wrap) wrap.classList.remove('has-error'); input.removeAttribute('aria-invalid'); }
  function validate(form) {
    var first = null;
    $$('[required]', form).forEach(function (inp) {
      clearError(inp);
      var v = inp.type === 'checkbox' ? inp.checked : inp.value.trim();
      var bad = !v;
      if (!bad && inp.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inp.value.trim())) { bad = true; setError(inp, 'Bitte geben Sie eine gültige E-Mail-Adresse an.'); }
      else if (bad) setError(inp, inp.type === 'checkbox' ? 'Bitte bestätigen Sie die Datenschutzhinweise.' : 'Bitte füllen Sie dieses Feld aus.');
      if (bad && !first) first = inp;
    });
    if (first) first.focus();
    return !first;
  }
  function initForms() {
    $$('form[data-lead]').forEach(function (form) {
      var msg = $('.form-msg', form), btn = $('[type=submit]', form), busy = false;
      $$('input,select,textarea', form).forEach(function (i) { on(i, 'input', function () { clearError(i); }); });
      on(form, 'submit', function (e) {
        e.preventDefault(); if (busy) return;
        if (msg) { msg.className = 'form-msg'; msg.textContent = ''; }
        if (!validate(form)) return;
        var hp = $('.hp input', form); if (hp && hp.value) { form.reset(); showOk(); return; } // Spam: still beenden
        var payload = { quelle: form.getAttribute('data-lead') || 'Formular' };
        $$('input,select,textarea', form).forEach(function (i) {
          if (!i.name || i.type === 'submit' || i.closest('.hp')) return;
          if (i.type === 'radio' && !i.checked) return;
          payload[i.name] = i.type === 'checkbox' ? (i.checked ? 'ja' : 'nein') : i.value.trim();
        });
        var cal = form.__cal; if (cal && cal.date && cal.time) { payload.wunschtermin = cal.label(); payload.termin_iso = cal.iso(); }
        payload.nachricht = Object.keys(payload).filter(function (k) { return ['name', 'email', 'tel', 'firma', 'thema', 'budget', 'branche', 'kanal', 'anfragen', 'empfehlung', 'wunschtermin', 'nachricht_text'].indexOf(k) >= 0 && payload[k]; })
          .map(function (k) { return k + ': ' + payload[k]; }).join('\n');
        busy = true; var orig = btn ? btn.innerHTML : '';
        if (btn) { btn.classList.add('is-loading'); btn.innerHTML = 'Wird gesendet …'; }
        track('form_submit', { location: payload.quelle });
        postLead(payload).then(function (res) {
          busy = false; if (btn) { btn.classList.remove('is-loading'); btn.innerHTML = orig; }
          if (res.ok) { form.reset(); if (cal) cal.reset(); if (form.__wizard) form.__wizard.reset(); showOk(); track('generate_lead', { location: payload.quelle }); }
          else if (msg) { msg.className = 'form-msg is-error'; msg.textContent = res.timeout ? 'Die Verbindung hat zu lange gedauert. Bitte versuchen Sie es erneut oder schreiben Sie an info@markentrix.de.' : 'Ihre Anfrage konnte nicht übermittelt werden. Bitte versuchen Sie es erneut oder schreiben Sie an info@markentrix.de.'; }
        });
        function showOk() {
          if (msg) { msg.className = 'form-msg is-success'; msg.textContent = 'Vielen Dank. Ihre Anfrage ist eingegangen. Wir melden uns werktags innerhalb von 24 Stunden.'; msg.setAttribute('tabindex', '-1'); msg.focus(); }
          var done = form.getAttribute('data-success'); if (done) { var box = $(done); if (box) { form.hidden = true; box.hidden = false; box.setAttribute('tabindex', '-1'); box.focus(); } }
        }
      });
    });
  }

  /* ── Wunschtermin-Kalender ──────────────────────────────────────────── */
  function initCalendar() {
    $$('[data-calendar]').forEach(function (root) {
      var form = root.closest('form'); if (!form) return;
      var MON = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
      var DOW = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
      var TIMES = { 1: ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00'], 5: ['09:00', '10:00', '11:00', '13:00', '14:00'] };
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var view = new Date(today.getFullYear(), today.getMonth(), 1);
      var state = { date: null, time: null };
      var head = d.createElement('div'); head.className = 'cal-head';
      var prev = d.createElement('button'); prev.type = 'button'; prev.className = 'cal-nav'; prev.setAttribute('aria-label', 'Vorheriger Monat'); prev.innerHTML = '‹';
      var next = d.createElement('button'); next.type = 'button'; next.className = 'cal-nav'; next.setAttribute('aria-label', 'Nächster Monat'); next.innerHTML = '›';
      var lbl = d.createElement('b'); lbl.setAttribute('aria-live', 'polite');
      head.appendChild(prev); head.appendChild(lbl); head.appendChild(next);
      var grid = d.createElement('div'); grid.className = 'cal-grid'; grid.setAttribute('role', 'grid');
      var times = d.createElement('div'); times.className = 'times'; times.hidden = true;
      var sel = d.createElement('div'); sel.className = 'cal-selected'; sel.hidden = true; sel.setAttribute('aria-live', 'polite');
      root.className = 'cal'; root.appendChild(head); root.appendChild(grid); root.appendChild(times); root.appendChild(sel);
      function isBiz(dt) { var dow = dt.getDay(); return dow >= 1 && dow <= 5; }
      function render() {
        lbl.textContent = MON[view.getMonth()] + ' ' + view.getFullYear();
        grid.innerHTML = DOW.map(function (x) { return '<div class="dow">' + x + '</div>'; }).join('');
        var first = (view.getDay() + 6) % 7, days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
        for (var i = 0; i < first; i++) grid.appendChild(d.createElement('div'));
        for (var day = 1; day <= days; day++) {
          var dt = new Date(view.getFullYear(), view.getMonth(), day);
          var b = d.createElement('button'); b.type = 'button'; b.className = 'cal-day'; b.textContent = day;
          b.setAttribute('aria-label', day + '. ' + MON[dt.getMonth()] + ' ' + dt.getFullYear());
          if (dt <= today || !isBiz(dt)) b.disabled = true;
          if (dt.getTime() === today.getTime()) b.classList.add('is-today');
          if (state.date && dt.getTime() === state.date.getTime()) { b.classList.add('is-selected'); b.setAttribute('aria-pressed', 'true'); }
          (function (dt) { on(b, 'click', function () { state.date = dt; state.time = null; render(); renderTimes(); }); })(dt);
          grid.appendChild(b);
        }
        prev.disabled = view.getFullYear() === today.getFullYear() && view.getMonth() === today.getMonth();
      }
      function renderTimes() {
        times.innerHTML = ''; sel.hidden = true; if (!state.date) { times.hidden = true; return; }
        times.hidden = false;
        var list = TIMES[state.date.getDay() === 5 ? 5 : 1];
        list.forEach(function (t) {
          var b = d.createElement('button'); b.type = 'button'; b.textContent = t + ' Uhr';
          if (state.time === t) { b.classList.add('is-selected'); b.setAttribute('aria-pressed', 'true'); }
          on(b, 'click', function () { state.time = t; renderTimes(); });
          times.appendChild(b);
        });
        if (state.time) { sel.hidden = false; sel.textContent = 'Wunschtermin: ' + api.label() + ' (unverbindlich, wir bestätigen per E-Mail).'; }
      }
      on(prev, 'click', function () { view = new Date(view.getFullYear(), view.getMonth() - 1, 1); render(); });
      on(next, 'click', function () { view = new Date(view.getFullYear(), view.getMonth() + 1, 1); render(); });
      var api = {
        get date() { return state.date; }, get time() { return state.time; },
        label: function () { var dt = state.date; return DOW[(dt.getDay() + 6) % 7] + ', ' + dt.getDate() + '. ' + MON[dt.getMonth()] + ' ' + dt.getFullYear() + ' um ' + state.time + ' Uhr'; },
        iso: function () { var dt = new Date(state.date); var p = state.time.split(':'); dt.setHours(+p[0], +p[1], 0, 0); return dt.toISOString(); },
        reset: function () { state.date = null; state.time = null; render(); renderTimes(); }
      };
      form.__cal = api; render();
    });
  }

  /* ── Modal (Potenzial-Check) ────────────────────────────────────────── */
  function initModal() {
    var modal = $('#mx-modal'); if (!modal) return;
    var box = $('.modal-box', modal), last = null;
    function open(branche) { modal.hidden = false; modal.classList.add('is-open'); var wf = $('form[data-wizard]', modal); if (wf && wf.__wizard) { if (branche) wf.__wizard.preset(branche); else wf.__wizard.show(wf.__wizard.current()); } d.body.classList.add('menu-open'); last = d.activeElement; var f = $('input,select,textarea,button', box); if (f) f.focus(); track('modal_open'); }
    function close() { modal.classList.remove('is-open'); modal.hidden = true; d.body.classList.remove('menu-open'); if (last && last.focus) last.focus(); }
    on(d, 'click', function (e) {
      var t = e.target.closest('[data-open-modal]'); if (t) { e.preventDefault(); open(t.getAttribute('data-branche')); return; }
      if (e.target.closest('[data-close-modal]') || e.target === modal) close();
    });
    on(d, 'keydown', function (e) {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) close();
      if (e.key === 'Tab' && modal.classList.contains('is-open')) {
        var f = $$('a[href],button:not([disabled]),input,select,textarea', box).filter(function (x) { return x.offsetParent !== null; });
        if (!f.length) return; var a = f[0], z = f[f.length - 1];
        if (e.shiftKey && d.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && d.activeElement === z) { e.preventDefault(); a.focus(); }
      }
    });
    if (location.hash === '#potenzial-check') open();
  }


  /* ── Potenzial-Check als Dialog ─────────────────────────────────────── */
  function initWizard() {
    var form = $('form[data-wizard]'); if (!form) return;
    var steps = $$('fieldset[data-step]', form), prog = $$('.wz-progress li', form);
    var prevB = $('[data-wz=prev]', form), nextB = $('[data-wz=next]', form), submitB = $('[type=submit]', form);
    var result = $('[data-wz-result]', form), reco = $('input[name=empfehlung]', form), cur = 0;
    var PAIN = { handwerk: 'Kunden suchen „Elektriker Celle“ oder „Dachdecker in der Nähe“ und entscheiden auf dem Handy in Sekunden. Ihr Telefon klingelt, während Sie auf der Baustelle sind.',
      praxis: 'Neue Patienten und Mandanten vergleichen Website, Bewertungen und Öffnungszeiten, bevor sie anrufen. Oft außerhalb der Sprechzeiten.',
      gastro: 'Gäste suchen Karte, Öffnungszeiten und Reservierung auf dem Handy. Wer sie nicht in zehn Sekunden findet, geht weiter.',
      sonstige: 'Interessenten suchen online, vergleichen und melden sich dann. Die Website entscheidet, ob daraus eine Anfrage wird.' };
    var KANAL = { website: '<b>Website.</b> Der erste Hebel ist eine Landingpage oder Website, die mobil überzeugt und lokal gefunden wird. LANDING ab 2.290 € einmalig (Pflege 59 € im Monat), Unternehmenswebsite BUSINESS WEB 4.490 €. In 5 bis 15 Werktagen live.',
      sichtbarkeit: '<b>Sichtbarkeit.</b> Lokale SEO-Grundlagen und GEO, also gefunden werden in KI-Antworten, gehören bei uns zur Website. Für die laufende Pflege von Google-Unternehmensprofil und Bewertungen: LOCAL VISIBILITY, 449 € im Monat netto.',
      formular: '<b>Anfragewege.</b> Anfragen müssen dort landen, wo sie bearbeitet werden: Terminbuchung im Kalender, Benachrichtigung aufs Handy, klare Antwortzeiten. Das richten wir mit der Website ein (LANDING ab 2.290 €).',
      anfragen: '<b>Telefon und WhatsApp.</b> Sofort hilft eine Landingpage mit Terminbuchung, damit Anfragen nicht warten. Ab November 2026 übernehmen unsere KI-Assistenten Telefon, WhatsApp und E-Mail (Pakete ab 349 € im Monat netto). Pilotplätze können Sie jetzt vormerken.',
      unklar: '<b>Noch unklar.</b> Im Erstgespräch finden wir in rund 30 Minuten den Punkt, an dem bei Ihnen am meisten verloren geht.' };
    function val(name) { var r = $('input[name=' + name + ']:checked', form); return r ? r.value : ''; }
    function label(name) { var r = $('input[name=' + name + ']:checked', form); return r ? (r.closest('.choice').textContent || '').trim() : ''; }
    function show(i) {
      var dir = i > cur ? 'wz-in' : 'wz-back', changed = i !== cur;
      cur = i;
      steps.forEach(function (s, k) { s.hidden = k !== i; s.classList.remove('wz-in', 'wz-back'); if (k === i && changed) s.classList.add(dir); });
      prog.forEach(function (p, k) { p.classList.toggle('is-done', k < i); p.classList.toggle('is-current', k === i); if (k === i) p.setAttribute('aria-current', 'step'); else p.removeAttribute('aria-current'); });
      if (prevB) prevB.hidden = i === 0;
      if (nextB) nextB.hidden = i === steps.length - 1;
      if (submitB) submitB.hidden = i !== steps.length - 1;
      if (i === steps.length - 1) buildResult();
      var f = $('input:not([type=hidden]):not([type=radio]), input[type=radio]:checked, input[type=radio]', steps[i]); if (f && !d.documentElement.classList.contains('reduced')) f.focus({ preventScroll: true });
    }
    function valid(i) {
      var req = steps[i].getAttribute('data-require'); if (!req) return true;
      var ok = !!$('input[name=' + req + ']:checked', form); var err = $('.error', steps[i]); if (err) err.style.display = ok ? '' : 'block';
      return ok;
    }
    function buildResult() {
      var b = val('branche') || 'sonstige', k = val('kanal') || 'unklar', n = +((($('input[name=anfragen]', form) || {}).value) || 0);
      var volume = n < 5 ? 'Bei unter fünf Anfragen pro Woche ist der erste Hebel meist die Sichtbarkeit: Google-Unternehmensprofil, Bewertungen und lokale Suche (LOCAL VISIBILITY, 449 € im Monat netto).'
        : 'Bei rund ' + n + (n >= 100 ? ' und mehr' : '') + ' Anfragen pro Woche zählt jede, die liegen bleibt. Eine Website mit klaren Anfragewegen ist dann der schnellste Hebel. Was eine verpasste Anfrage kostet, zeigt der Sparrechner.';
      var html = '<b>Kurz zusammengefasst</b><ul><li>' + PAIN[b] + '</li><li>' + KANAL[k] + '</li><li>' + volume + '</li></ul><p class="tiny">Keine Zusicherung, alle Preise netto zzgl. USt. Im Erstgespräch prüfen wir, ob und wie sich das in Ihrem Betrieb rechnet.</p>';
      if (result) result.innerHTML = html;
      if (reco) reco.value = 'Branche: ' + (label('branche') || 'offen') + ' | Kanal: ' + (label('kanal') || 'offen') + ' | Anfragen/Woche: ' + n;
    }
    on(nextB, 'click', function () { if (valid(cur)) show(cur + 1); });
    on(prevB, 'click', function () { show(Math.max(0, cur - 1)); });
    on(form, 'keydown', function (e) { if (e.key === 'Enter' && cur < steps.length - 1 && e.target.tagName !== 'TEXTAREA') { e.preventDefault(); nextB.click(); } });
    $$('.choice input', form).forEach(function (r) { on(r, 'change', function () { if (cur < 2) setTimeout(function () { nextB.click(); }, 160); }); });
    var range = $('input[name=anfragen]', form);
    if (range) { var out = $('output[for=' + range.id + ']', form); var paint = function () { var pct = (range.value - range.min) / (range.max - range.min) * 100; range.style.setProperty('--pct', pct + '%'); if (out) out.textContent = range.value + (+range.value === +range.max ? '+' : ''); }; on(range, 'input', paint); paint(); }
    form.__wizard = { show: show, current: function () { return cur; }, reset: function () { show(0); }, preset: function (b) { var r = $('input[name=branche][value="' + b + '"]', form); if (r) { r.checked = true; show(1); } else show(0); } };
    show(0);
  }


  /* ── Hilfsfunktion: Zahl weich zum Zielwert zählen ─────────────────── */
  function tween(el, value, fmt) {
    if (!el) return;
    var reduced = d.documentElement.classList.contains('reduced');
    if (el.__v == null || reduced) { el.__v = value; el.textContent = fmt(value); return; }
    var from = el.__v, start = performance.now(), dur = 420; el.__v = value;
    if (el.__raf) cancelAnimationFrame(el.__raf);
    var host = el.closest('.note, .kpi, .card'); if (host) { host.classList.remove('pulse'); void host.offsetWidth; host.classList.add('pulse'); }
    (function step(t) { var k = Math.min(1, (t - start) / dur); k = 1 - Math.pow(1 - k, 3); el.textContent = fmt(from + (value - from) * k); if (k < 1) el.__raf = requestAnimationFrame(step); })(start);
  }

  /* ── 5 · Kennzahlen zählen hoch ─────────────────────────────────────── */
  function initCountUp() {
    $$('.stats').forEach(function (stats) {
      var jobs = [];
      $$('b', stats).forEach(function (b) {
        var node = null; [].forEach.call(b.childNodes, function (n) { if (!node && n.nodeType === 3 && /\d/.test(n.textContent)) node = n; });
        if (!node) return;
        var m = node.textContent.match(/(\d[\d.]*)/); if (!m) return;
        var target = parseInt(m[1].replace(/\./g, ''), 10); if (!target || target < 2) return;
        jobs.push({ node: node, pre: node.textContent.slice(0, m.index), post: node.textContent.slice(m.index + m[1].length), target: target, dots: m[1].indexOf('.') >= 0 });
        node.textContent = jobs[jobs.length - 1].pre + '0' + jobs[jobs.length - 1].post;
      });
      if (!jobs.length) return;
      function run() {
        if (d.documentElement.classList.contains('reduced')) { jobs.forEach(function (j) { j.node.textContent = j.pre + fmtN(j.target, j.dots) + j.post; }); return; }
        var start = performance.now(), dur = 1100;
        (function step(t) { var k = Math.min(1, (t - start) / dur); k = 1 - Math.pow(1 - k, 3); jobs.forEach(function (j) { j.node.textContent = j.pre + fmtN(Math.round(j.target * k), j.dots) + j.post; }); if (k < 1) requestAnimationFrame(step); })(start);
      }
      function fmtN(v, dots) { return dots ? v.toLocaleString('de-DE') : String(v); }
      if (stats.classList.contains('is-in')) run(); else stats.addEventListener('mx:in', run, { once: true });
    });
  }

  /* ── 1 · Systemablauf als Sequenz ───────────────────────────────────── */
  function initSequence() {
    var seq = $('.seq'); if (!seq) return;
    var items = $$('.seq-item', seq), timers = [];
    function play() { timers.forEach(clearTimeout); timers = []; items.forEach(function (i) { i.classList.remove('is-on'); }); items.forEach(function (it, k) { timers.push(setTimeout(function () { it.classList.add('is-on'); }, 400 + k * 1100)); }); }
    if (d.documentElement.classList.contains('reduced')) { items.forEach(function (i) { i.classList.add('is-on'); }); }
    else if (seq.classList.contains('is-in')) play(); else seq.addEventListener('mx:in', play, { once: true });
    on($('.seq-replay'), 'click', play);
  }

  /* ── 4 · Desktop / Smartphone im Browser-Mockup ─────────────────────── */
  function initDeviceToggle() {
    var tog = $('.device-toggle'), browser = $('.browser'), img = browser && $('.browser-body img', browser); if (!tog || !browser || !img) return;
    var srcD = img.getAttribute('src'), srcM = img.getAttribute('data-mobile'), mode = 'desktop', auto = null, busy = false; if (!srcM) return;
    function set(next) {
      if (busy || next === mode) return; busy = true; mode = next;
      $$('button', tog).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-device') === mode ? 'true' : 'false'); });
      browser.classList.add('is-switching');
      setTimeout(function () {
        browser.classList.toggle('is-mobile', mode === 'mobile');
        img.setAttribute('src', mode === 'mobile' ? srcM : srcD);
        img.setAttribute('width', mode === 'mobile' ? '600' : '1200'); img.setAttribute('height', mode === 'mobile' ? '1200' : '790');
        browser.classList.remove('is-switching'); busy = false;
      }, 350);
    }
    on(tog, 'click', function (e) { var b = e.target.closest('button[data-device]'); if (!b) return; if (auto) { clearInterval(auto); auto = null; } set(b.getAttribute('data-device')); });
    if (!d.documentElement.classList.contains('reduced') && w.innerWidth > 900) { auto = setInterval(function () { if (d.hidden) return; set(mode === 'desktop' ? 'mobile' : 'desktop'); }, 7000); }
  }

  /* ── 2 · Suche und KI-Antwort bauen sich auf ────────────────────────── */
  function initSeoProof() {
    $$('.proof-seo').forEach(function (root) {
      var q = $('.serp .q', root), hits = $$('.serp .hit', root), ans = $('.ai-answer p', root), src = $('.ai-answer .src', root); if (!q || !ans) return;
      if (d.documentElement.classList.contains('reduced')) { hits.concat(src ? [src] : []).forEach(function (h) { h.classList.add('is-on'); }); return; }
      var text = (q.textContent || '').trim(); var icon = $('svg', q); q.textContent = ''; if (icon) q.appendChild(icon);
      var typed = d.createElement('span'); typed.className = 'typed'; var caret = d.createElement('span'); caret.className = 'caret'; q.appendChild(typed); q.appendChild(caret);
      (function wrap(node) { [].slice.call(node.childNodes).forEach(function (n) { if (n.nodeType === 3) { var f = d.createDocumentFragment(); n.textContent.split(/(\s+)/).forEach(function (t) { if (!t) return; if (/^\s+$/.test(t)) f.appendChild(d.createTextNode(t)); else { var sp = d.createElement('span'); sp.className = 'w'; sp.textContent = t; f.appendChild(sp); } }); n.parentNode.replaceChild(f, n); } else if (n.nodeType === 1) wrap(n); }); })(ans);
      var words = $$('.w', ans);
      function run() {
        root.classList.add('is-live'); var i = 0;
        (function type() { if (i <= text.length) { typed.textContent = text.slice(0, i); i++; setTimeout(type, 38); } else { caret.classList.add('is-done'); hits.forEach(function (h, k) { setTimeout(function () { h.classList.add('is-on'); }, 250 + k * 260); }); setTimeout(function () { words.forEach(function (sp, k) { setTimeout(function () { sp.classList.add('is-on'); }, k * 42); }); if (src) setTimeout(function () { src.classList.add('is-on'); }, words.length * 42 + 200); }, 900); } })();
      }
      if (root.classList.contains('is-in')) run(); else root.addEventListener('mx:in', run, { once: true });
    });
  }

  /* ── 7 · Akkordeon mit Höhenübergang ────────────────────────────────── */
  function initAccordion() {
    if (d.documentElement.classList.contains('reduced') || !('animate' in Element.prototype)) return;
    $$('details.faq, details.details').forEach(function (dt) {
      var sum = $('summary', dt), body = $('.faq-body, .details-body', dt); if (!sum || !body) return;
      on(sum, 'click', function (e) {
        e.preventDefault(); if (dt.__anim) return;
        if (dt.open) { var h = body.offsetHeight; dt.__anim = body.animate([{ height: h + 'px', opacity: 1 }, { height: '0px', opacity: 0 }], { duration: 240, easing: 'ease' }); dt.__anim.onfinish = function () { dt.open = false; dt.__anim = null; }; }
        else { dt.open = true; var h2 = body.scrollHeight; dt.__anim = body.animate([{ height: '0px', opacity: 0 }, { height: h2 + 'px', opacity: 1 }], { duration: 300, easing: 'ease' }); dt.__anim.onfinish = function () { dt.__anim = null; }; }
      });
    });
  }

  /* ── 9 + 11 · Scroll-Fortschritt, Wachstumspfad, Header ─────────────── */
  function initScroll() {
    var header = $('.site-header'); if (!header) return;
    var bar = d.createElement('div'); bar.className = 'scroll-progress'; bar.setAttribute('aria-hidden', 'true'); d.body.appendChild(bar);
    var main = $('main'), sections = $$('.has-rail'), first = sections[0], last = sections[sections.length - 1], rail = null, fill = null, railTop = 0, railH = 0;
    if (d.body.classList.contains('page-home') && first && last && w.matchMedia('(min-width:1340px)').matches) {
      rail = d.createElement('div'); rail.className = 'rail'; fill = d.createElement('div'); fill.className = 'rail-fill'; rail.appendChild(fill); main.style.position = 'relative'; main.appendChild(rail);
    }
    function layout() {
      if (!rail) return;
      var wr = $('.wrap', first).getBoundingClientRect(), mr = main.getBoundingClientRect();
      rail.style.left = (wr.left - mr.left - 52) + 'px';
      railTop = first.getBoundingClientRect().top - mr.top + 60; railH = Math.max(0, last.getBoundingClientRect().bottom - mr.top - railTop - 80);
      rail.style.top = railTop + 'px'; rail.style.height = railH + 'px';
    }
    function update() {
      var max = d.documentElement.scrollHeight - w.innerHeight; bar.style.width = (max > 0 ? Math.min(100, w.scrollY / max * 100) : 0) + '%';
      header.classList.toggle('is-scrolled', w.scrollY > 24);
      if (rail) { var mainTop = main.getBoundingClientRect().top + w.scrollY; var y = w.scrollY + w.innerHeight * 0.55 - (mainTop + railTop); fill.style.height = Math.max(0, Math.min(railH, y)) + 'px'; }
    }
    on(w, 'scroll', update, { passive: true }); on(w, 'resize', function () { layout(); update(); }); on(w, 'load', function () { layout(); update(); });
    layout(); update();
  }

  /* ── Kurzcheck (Startseite) ─────────────────────────────────────────── */
  function initQuickCheck() {
    var root = $('[data-quickcheck]'); if (!root) return;
    var missed = $('[name=missed]', root), order = $('[name=order]', root), out = $('[data-out=lost]', root);
    function paint(inp) { var pct = (inp.value - inp.min) / (inp.max - inp.min) * 100; inp.style.setProperty('--pct', pct + '%'); var o = $('output[for=' + inp.id + ']', root); if (o) o.textContent = inp.name === 'order' ? fmtEUR(inp.value) : inp.value; }
    function calc() { paint(missed); paint(order); var lost = missed.value * 4.33 * 0.2 * order.value; tween(out, lost, fmtEUR); }
    on(missed, 'input', calc); on(order, 'input', calc); calc();
  }

  /* ── ROI-Rechner (Unterseite) ───────────────────────────────────────── */
  function initRoi() {
    var root = $('[data-roi]'); if (!root) return;
    var f = {};
    ['calls', 'msgs', 'sched', 'wage', 'missed', 'order'].forEach(function (k) { f[k] = $('[name=' + k + ']', root); });
    var o = {};
    ['manual', 'lost', 'pkg', 'pkgPrice', 'hours', 'net', 'pkgNote'].forEach(function (k) { o[k] = $('[data-out=' + k + ']', root); });
    function paint(inp, fmt) { var pct = (inp.value - inp.min) / (inp.max - inp.min) * 100; inp.style.setProperty('--pct', pct + '%'); var out = $('output[for=' + inp.id + ']', root); if (out) out.textContent = fmt(inp.value); }
    function calc() {
      paint(f.calls, function (v) { return v; }); paint(f.msgs, function (v) { return v; }); paint(f.sched, function (v) { return v + ' h'; });
      paint(f.wage, function (v) { return v + ' €'; }); paint(f.missed, function (v) { return v; }); paint(f.order, function (v) { return fmtEUR(v); });
      var calls = +f.calls.value, msgs = +f.msgs.value, sched = +f.sched.value, wage = +f.wage.value, missed = +f.missed.value, order = +f.order.value;
      // Annahmen: 4 Min je Anruf, 2 Min je Nachricht, 21,7 Arbeitstage, 4,33 Wochen
      var hoursMonth = (calls * 4 + msgs * 2) / 60 * 21.7 + sched * 4.33;
      var manual = hoursMonth * wage;
      var lost = missed * 4.33 * 0.2 * order;
      var pkg = 'ONE', price = 349;
      if (calls > 0 && (calls * 4 * 21.7 > 600 || calls * 21.7 + msgs * 21.7 > 3000)) { pkg = 'KOMPLETT'; price = 1190; }
      else if (calls > 0) { pkg = 'BUSINESS'; price = 699; }
      var automatable = hoursMonth * 0.6; // konservativ: 60 % der Routine automatisierbar
      var net = (automatable * wage + lost) - price;
      tween(o.manual, manual, fmtEUR); tween(o.lost, lost, fmtEUR); o.pkg.textContent = pkg; o.pkgPrice.textContent = fmtEUR(price);
      tween(o.hours, Math.round(automatable), function (v) { return Math.round(v) + ' h'; }); tween(o.net, Math.max(0, net * 12), fmtEUR);
      o.pkgNote.textContent = pkg === 'ONE' ? 'WhatsApp oder E-Mail, ohne Telefonagent' : pkg === 'BUSINESS' ? 'Telefon und WhatsApp, 600 Minuten' : 'Telefon, WhatsApp und E-Mail, 1.000 Minuten';
    }
    Object.keys(f).forEach(function (k) { on(f[k], 'input', calc); });
    calc();
  }

  /* ── Blog-Filter ────────────────────────────────────────────────────── */
  function initBlogFilter() {
    var bar = $('[data-filter]'); if (!bar) return;
    var items = $$('[data-cat]').filter(function (it) { return !bar.contains(it); }); // Filterknöpfe selbst ausnehmen
    on(bar, 'click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      $$('button', bar).forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      var cat = b.getAttribute('data-cat');
      items.forEach(function (it) { it.hidden = !(cat === 'alle' || it.getAttribute('data-cat') === cat); });
    });
  }

  /* ── Barrierefreiheit: Schriftgröße, Kontrast ───────────────────────── */
  function initA11y() {
    var root = d.documentElement, scale = 1;
    try { scale = parseFloat(localStorage.getItem('mx-a11y-scale')) || 1; if (localStorage.getItem('mx-a11y-contrast') === '1') root.classList.add('a11y-contrast'); } catch (e) { }
    function apply() { root.style.setProperty('--a11y-scale', scale); try { localStorage.setItem('mx-a11y-scale', scale); } catch (e) { } }
    apply();
    on($('[data-a11y=minus]'), 'click', function () { scale = Math.max(.85, +(scale - .1).toFixed(2)); apply(); });
    on($('[data-a11y=plus]'), 'click', function () { scale = Math.min(1.4, +(scale + .1).toFixed(2)); apply(); });
    on($('[data-a11y=reset]'), 'click', function () { scale = 1; apply(); });
    var c = $('[data-a11y=contrast]');
    if (c) { c.setAttribute('aria-pressed', root.classList.contains('a11y-contrast') ? 'true' : 'false'); on(c, 'click', function () { var onn = root.classList.toggle('a11y-contrast'); c.setAttribute('aria-pressed', onn ? 'true' : 'false'); try { localStorage.setItem('mx-a11y-contrast', onn ? '1' : '0'); } catch (e) { } }); }
  }

  /* ── Tabbar aktiv (Preise) ──────────────────────────────────────────── */
  function initTabbar() {
    var bar = $('.tabbar'); if (!bar || !('IntersectionObserver' in w)) return;
    var links = $$('a[href^="#"]', bar), secs = links.map(function (a) { return $(a.getAttribute('href')); }).filter(Boolean);
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) links.forEach(function (a) { a.classList.toggle('is-active', a.getAttribute('href') === '#' + en.target.id); }); });
    }, { rootMargin: '-30% 0px -60% 0px' });
    secs.forEach(function (s) { io.observe(s); });
  }

  /* ── Jahr im Footer ─────────────────────────────────────────────────── */
  function initYear() { $$('[data-year]').forEach(function (e) { e.textContent = new Date().getFullYear(); }); }

  function init() { initNav(); initReveal(); initForms(); initCalendar(); initWizard(); initModal(); initQuickCheck(); initRoi(); initBlogFilter(); initA11y(); initTabbar(); initYear(); initCountUp(); initSequence(); initDeviceToggle(); initSeoProof(); initAccordion(); initScroll(); }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', init); else init();
})();
