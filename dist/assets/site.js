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
    on(d, 'keydown', function (e) { if (e.key === 'Escape') dds.forEach(function (dd) { if (dd.hasAttribute('open')) { dd.removeAttribute('open'); var sm = $('summary', dd); if (sm && dd.contains(d.activeElement)) sm.focus(); } }); });
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
  /* Herkunft der Anfrage: Kampagnenparameter (utm_*) aus der Adresse, sonst die verweisende Domain.
     Über Seitenwechsel hinweg wird nur nach Einwilligung in die Reichweitenmessung in der Sitzung gemerkt. */
  function consentOk() { try { var c = JSON.parse(localStorage.getItem('mx-consent')); return !!(c && c.analytics); } catch (e) { return false; } }
  function utmFromUrl() {
    var o = {}, q = location.search.replace(/^\?/, '').split('&');
    q.forEach(function (kv) { var p = kv.split('='), k = p[0], v = ''; try { v = decodeURIComponent((p[1] || '').replace(/\+/g, ' ')); } catch (e) { } if (/^utm_(source|medium|campaign)$/.test(k) && /^[\w .\-]{1,60}$/.test(v)) o[k] = v; });
    return o;
  }
  function campaign() {
    var u = utmFromUrl(), keep = null;
    try { keep = JSON.parse(sessionStorage.getItem('mx-utm') || 'null'); } catch (e) { }
    if (Object.keys(u).length) { if (consentOk()) { try { sessionStorage.setItem('mx-utm', JSON.stringify(u)); } catch (e) { } } } else if (keep && consentOk()) u = keep;
    if (!Object.keys(u).length && d.referrer) { try { var h = new URL(d.referrer).hostname; if (h && h !== location.hostname) u = { utm_referrer: h.replace(/^www\./, '') }; } catch (e) { } }
    return u;
  }
  function initCampaign() { if (consentOk()) campaign(); }
  function postLead(payload) {
    payload.seite = location.pathname; payload.zeit = new Date().toISOString();
    var cp = campaign(); Object.keys(cp).forEach(function (k) { payload[k] = cp[k]; });
    if (w.__mxCheck && payload.quelle === 'Website-Check') { payload.website_check = w.__mxCheck.host + ' (' + w.__mxCheck.score + ' von 100)'; payload.bericht_token = w.__mxCheck.token; }
    else if (w.__mxCheck) payload.website_check = w.__mxCheck.host + ' (' + w.__mxCheck.score + ' von 100)';
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
        payload.nachricht = Object.keys(payload).filter(function (k) { return ['name', 'email', 'tel', 'firma', 'thema', 'budget', 'bedarf', 'status', 'zeitplan', 'branche', 'aktion', 'empfehlung', 'wunschtermin', 'kanal', 'nachricht_text'].indexOf(k) >= 0 && payload[k]; })
          .map(function (k) { return k + ': ' + payload[k]; }).join('\n');
        busy = true; var orig = btn ? btn.innerHTML : '';
        if (btn) { btn.classList.add('is-loading'); btn.innerHTML = 'Wird gesendet …'; }
        track('form_submit', { location: payload.quelle });
        postLead(payload).then(function (res) {
          busy = false; if (btn) { btn.classList.remove('is-loading'); btn.innerHTML = orig; }
          if (res.ok) { form.reset(); if (cal) cal.reset(); if (form.__wizard) form.__wizard.reset(); showOk(); track('generate_lead', { location: payload.quelle, channel: payload.kanal || payload.utm_source || payload.utm_referrer || 'direkt' }); if (form.hasAttribute('data-no-redirect')) { d.dispatchEvent(new CustomEvent('mx:lead', { detail: { quelle: payload.quelle, email: payload.email } })); } else setTimeout(function () { location.href = '/danke?form=' + encodeURIComponent(form.getAttribute('name') || 'anfrage'); }, 700); }
          else if (msg) { msg.className = 'form-msg is-error'; msg.textContent = res.timeout ? 'Die Verbindung hat zu lange gedauert. Bitte versuchen Sie es erneut oder schreiben Sie an info@markentrix.de.' : 'Ihre Anfrage konnte nicht übermittelt werden. Bitte versuchen Sie es erneut oder schreiben Sie an info@markentrix.de.'; }
        });
        function showOk() {
          if (msg) { msg.className = 'form-msg is-success'; msg.textContent = 'Vielen Dank. Ihre Anfrage ist eingegangen. Wir melden uns werktags innerhalb von 24 Stunden.'; msg.setAttribute('tabindex', '-1'); msg.focus(); }
          var done = form.getAttribute('data-success'); if (done) { var box = $(done); if (box) { form.hidden = true; box.hidden = false; box.setAttribute('tabindex', '-1'); box.focus(); } }
        }
      });
    });
  }

  /* ── Website-Check: ruft /api/check.php auf und zeigt das Ergebnis (nur textContent, kein HTML aus der Antwort) ── */
  function initCheck() {
    var form = $('form[data-check]'); if (!form) return;
    var pre = (location.search.match(/[?&]url=([^&]+)/) || [])[1];
    var input = $('input[name=url]', form), btn = $('[type=submit]', form), msg = $('.chk-msg', form), out = $('[data-check-result]'), gate = $('[data-check-gate]'), found = $('[data-check-findings]'), last = null, busy = false;
    var LABEL = { ok: 'In Ordnung', warn: 'Auffällig', bad: 'Mangelhaft', info: 'Hinweis' };
    var MSG = { url: 'Bitte geben Sie eine gültige Adresse an, zum Beispiel www.ihre-seite.de.', rate: 'Sie haben in kurzer Zeit viele Prüfungen gestartet. Bitte versuchen Sie es in ein paar Minuten erneut.', busy: 'Gerade laufen viele Prüfungen. Bitte versuchen Sie es in einer Minute erneut.', server: 'Der Check ist gerade nicht erreichbar. Bitte versuchen Sie es später erneut.', origin: 'Der Check ist nur über markentrix.de nutzbar.' };
    function el(tag, cls, text) { var e = d.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
    function fail(t) { msg.className = 'chk-msg is-error'; msg.textContent = t; }
    var IMPACT = { high: 'Gewicht: hoch', mid: 'Gewicht: mittel', low: 'Gewicht: gering' };
    var HEAD = { stark: 'Starke Grundlagen, wenige Lücken.', gut: 'Solide, aber mit spürbaren Lücken.', mittel: 'Mittelmaß: hier bleiben Anfragen liegen.', schwach: 'Erheblicher Rückstand bei Auffindbarkeit und Vertrauen.' };
    function renderFindings(r) {
      found.textContent = '';
      var order = { bad: 0, warn: 1, ok: 2, info: 3 };
      r.categories.forEach(function (g) {
        var sec = el('section', 'chk-group'); sec.appendChild(el('h3', null, g.title));
        var ul = el('ul', 'chk-list');
        g.items.slice().sort(function (a, b) { return order[a.status] - order[b.status]; }).forEach(function (it) {
          var li = el('li', 'chk-item is-' + it.status);
          li.appendChild(el('span', 'chk-badge', LABEL[it.status] || ''));
          var body = el('div'); body.appendChild(el('b', null, it.title)); body.appendChild(el('p', null, it.detail));
          if (it.status === 'bad' || it.status === 'warn') body.appendChild(el('span', 'chk-impact', IMPACT[it.impact] || ''));
          li.appendChild(body); ul.appendChild(li);
        });
        sec.appendChild(ul); found.appendChild(sec);
      });
      var cta = el('div', 'card card--lg card--soft chk-cta');
      cta.appendChild(el('h3', null, 'Ergebnis gemeinsam einordnen?'));
      cta.appendChild(el('p', 'muted', 'Im kostenlosen Potenzial-Check besprechen wir, was davon für Ihren Betrieb wirklich zählt. Unverbindlich, Rückmeldung werktags innerhalb von 24 Stunden.'));
      var row = el('div', 'row mt-2'); var a = el('a', 'btn btn--primary btn--lg', 'Potenzial-Check anfragen'); a.href = '/kontakt'; a.setAttribute('data-open-modal', ''); a.setAttribute('data-aktion', 'website-check'); row.appendChild(a);
      var b2 = el('a', 'btn btn--secondary btn--lg', 'SEO und GEO ansehen'); b2.href = '/leistungen/seo-geo'; row.appendChild(b2); cta.appendChild(row); found.appendChild(cta);
      var smp = (r.sample && r.sample.length) ? ' Stichprobe interner Seiten: ' + r.sample.map(function (x) { return x.path; }).join(', ') + '.' : '';
      found.appendChild(el('p', 'tiny mt-3', 'Geprüft wurden Startseite, robots.txt, Sitemap, llms.txt, eine nicht vorhandene Adresse und eine Stichprobe interner Seiten, einmalig und ohne Speicherung, in ' + r.seconds + ' Sekunden.' + smp + ' Nicht geprüft werden Rankings, die tatsächliche Ladezeit auf dem Smartphone, Texte, Backlinks, Google-Bewertungen und die rechtliche Vollständigkeit von Impressum und Datenschutzerklärung.'));
      found.hidden = false;
    }
    on(d, 'mx:lead', function (e) { if (e.detail && e.detail.quelle === 'Website-Check' && last) { renderFindings(last); if (found.scrollIntoView) found.scrollIntoView({ behavior: d.documentElement.classList.contains('reduced') ? 'auto' : 'smooth', block: 'start' }); } });
    function render(r) {
      out.textContent = '';
      var score = r.score, tone = score >= 80 ? 'good' : score >= 55 ? 'mid' : 'low';
      var head = el('div', 'chk-head chk-' + tone);
      var ring = el('div', 'chk-ring'); ring.style.setProperty('--p', score); ring.appendChild(el('b', null, String(score))); ring.appendChild(el('span', null, 'von 100'));
      var ht = el('div', 'chk-head-text');
      ht.appendChild(el('span', 'eyebrow', 'Ergebnis für ' + r.host));
      ht.appendChild(el('h2', null, HEAD[r.grade] || ''));
      ht.appendChild(el('p', 'muted', r.checks + ' Merkmale geprüft: ' + r.counts.ok + ' in Ordnung, ' + r.counts.warn + ' auffällig, ' + r.counts.bad + ' mangelhaft. Die Punktzahl ist ein Orientierungswert, keine Messung von Rankings.'));
      if (r.cap) ht.appendChild(el('p', 'chk-cap', 'Gedeckelt wegen: ' + r.cap));
      head.appendChild(ring); head.appendChild(ht); out.appendChild(head);
      var bars = el('div', 'chk-bars');
      r.categories.forEach(function (c) {
        var row = el('div', 'chk-bar ' + (c.score >= 80 ? 'is-good' : c.score >= 55 ? 'is-mid' : 'is-low'));
        row.appendChild(el('span', 'chk-bar-t', c.title)); var tr = el('span', 'chk-bar-track'); var f = el('i'); f.style.width = c.score + '%'; tr.appendChild(f); row.appendChild(tr);
        row.appendChild(el('b', null, c.score + ' / 100')); bars.appendChild(row);
      });
      out.appendChild(bars);
      last = r; found.textContent = ''; found.hidden = true;
      if (gate) { var gf = $('form', gate), ok = $('#chk-danke', gate); if (gf) { gf.hidden = false; gf.reset(); } if (ok) ok.hidden = true; var offer = $('[data-check-offer]', gate); if (offer) offer.hidden = !(r.score < 100); gate.hidden = false; }
      out.hidden = false; out.focus({ preventScroll: true });
      if (out.scrollIntoView) out.scrollIntoView({ behavior: d.documentElement.classList.contains('reduced') ? 'auto' : 'smooth', block: 'start' });
    }
    on(form, 'submit', function (e) {
      e.preventDefault(); if (busy) return;
      var v = input.value.trim(); msg.className = 'chk-msg'; msg.textContent = '';
      if (!v || v.indexOf('.') < 0 && !/^https?:\/\//i.test(v)) { fail(MSG.url); input.focus(); return; }
      busy = true; var orig = btn.textContent; btn.textContent = 'Prüfe …'; btn.disabled = true; form.setAttribute('aria-busy', 'true'); out.hidden = true;
      msg.textContent = 'Wir prüfen Ihre Seite gründlich. Das dauert bis zu 20 Sekunden.';
      var ctrl = ('AbortController' in w) ? new AbortController() : null, timer = ctrl && setTimeout(function () { ctrl.abort(); }, 45000);
      fetch('/api/check.php', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: v }), signal: ctrl ? ctrl.signal : undefined })
        .then(function (r) { return r.json().catch(function () { return { ok: false, error: 'server' }; }).then(function (j) { j.__status = r.status; return j; }); })
        .then(function (j) {
          if (j && j.ok) { msg.textContent = ''; w.__mxCheck = { host: j.host, score: j.score, token: j.token }; render(j); track('website_check', { score: j.score >= 80 ? 'hoch' : j.score >= 55 ? 'mittel' : 'niedrig' }); }
          else fail((j && j.message) || MSG[j && j.error] || MSG.server);
        })
        .catch(function () { fail('Die Prüfung hat zu lange gedauert oder die Verbindung ist abgebrochen. Bitte versuchen Sie es erneut.'); })
        .then(function () { clearTimeout(timer); busy = false; btn.textContent = orig; btn.disabled = false; form.removeAttribute('aria-busy'); });
    });
    if (pre) { try { input.value = decodeURIComponent(pre.replace(/\+/g, ' ')).slice(0, 300); } catch (e) { } if (input.value) setTimeout(function () { form.dispatchEvent(new Event('submit', { cancelable: true })); }, 300); }
  }

  /* Partnerseite: Klick auf „bewerben“ wählt die Rolle im Formular vor */
  function initPartner() {
    var sel = $('#b-rolle'); if (!sel) return;
    $$('a[data-rolle]').forEach(function (a) { on(a, 'click', function () { sel.value = a.getAttribute('data-rolle'); }); });
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
      var grid = d.createElement('div'); grid.className = 'cal-grid';
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
        var sum = $('[data-cal-sum]', form); if (sum) sum.textContent = state.time ? api.label() : (state.date ? 'Uhrzeit wählen' : 'Keinen gewählt');
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
    function open(branche, bedarf, aktion) { var pb = $('.burger'); if (pb && pb.getAttribute('aria-expanded') === 'true') pb.click(); modal.hidden = false; modal.classList.add('is-open'); var wf = $('form[data-wizard]', modal); var ak = wf && $('input[name=aktion]', wf); if (ak) ak.value = aktion || ''; if (wf && wf.__wizard) { if (branche || bedarf) wf.__wizard.preset(branche, bedarf); else wf.__wizard.show(wf.__wizard.current()); } d.body.classList.add('menu-open'); last = d.activeElement; var f = $('input,select,textarea,button', box); if (f) f.focus(); track('modal_open'); }
    function close() { modal.classList.remove('is-open'); modal.hidden = true; d.body.classList.remove('menu-open'); if (last && last.focus) last.focus(); }
    on(d, 'click', function (e) {
      var t = e.target.closest('[data-open-modal]'); if (t) { e.preventDefault(); open(t.getAttribute('data-branche'), t.getAttribute('data-bedarf'), t.getAttribute('data-aktion')); return; }
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
    var result = $('[data-wz-result]', form), reco = $('input[name=empfehlung]', form), branche = $('input[name=branche]', form), cur = 0;
    var PAIN = { handwerk: 'Für Handwerk und Bau heißt das: Kunden suchen „Elektriker Celle“ oder „Dachdecker in der Nähe“ und entscheiden auf dem Handy in Sekunden. Eine Leistungsseite je Gewerk und Ort ist deshalb Teil des Konzepts.',
      praxis: 'Für Praxen und Kanzleien heißt das: Neue Patienten und Mandanten vergleichen Website, Bewertungen und Öffnungszeiten, oft außerhalb der Sprechzeiten. Terminanfrage und Antworten auf die häufigsten Fragen gehören auf die Seite.',
      gastro: 'Für Gastronomie und Handel heißt das: Gäste suchen Karte, Öffnungszeiten und Reservierung auf dem Handy. Wer das nicht in zehn Sekunden findet, geht weiter.',
      sonstige: 'Interessenten suchen online, vergleichen und melden sich dann. Die Website entscheidet, ob daraus eine Anfrage wird.' };
    var BEDARF = { landingpage: '<b>Passendes Paket: LANDING, 2.290 € einmalig, Pflege 59 € im Monat.</b> Ein Conversion-Onepager mit Texten, Bildern und Terminbuchung für ein Angebot. Wenn Sie Texte und Bilder selbst liefern, geht LANDING START auf Vorlagenbasis ab 1.290 €.',
      website: '<b>Passendes Paket: BUSINESS WEB, 4.490 € einmalig, Pflege 89 € im Monat.</b> Bis sieben Inhaltsseiten mit Struktur, Texten und Bildern, zum Beispiel eine Leistungsseite je Gewerk oder Ort.',
      relaunch: '<b>Passendes Paket: je nach Umfang LANDING (2.290 €) oder BUSINESS WEB (4.490 €).</b> Wir prüfen zuerst, was von der bestehenden Seite bleibt: Domain, Inhalte, Bewertungen. Darauf entsteht die neue Struktur.',
      funnel: '<b>Passendes Paket: WEB + FUNNEL, 6.990 € einmalig, Pflege 129 € im Monat.</b> Bis zwölf Seiten mit einer Anfrage- oder Verkaufsstrecke, die Besucher Schritt für Schritt zur Anfrage führt.',
      unklar: '<b>Noch offen, das ist in Ordnung.</b> Die meisten Betriebe starten mit LANDING (2.290 €) für ein konkretes Angebot. Im Erstgespräch klären wir in rund 30 Minuten, was zuerst Sinn ergibt.' };
    var STATUS = { keine: 'Ohne Website entscheidet heute allein das Google-Profil, ob jemand anfragt. Eine erste Seite mit Leistungen, Ort und Anfrageweg ändert das.',
      veraltet: 'Eine veraltete Seite kostet Vertrauen, besonders auf dem Handy. Domain und brauchbare Inhalte übernehmen wir, der Rest wird neu aufgebaut.',
      keineanfragen: 'Eine Seite ohne Anfragen hat meist kein klares Angebot und keinen klaren Anfrageweg. Genau das prüfen wir als Erstes.',
      gut: 'Gute Basis. Dann geht es um Erweiterung: Leistungsseiten je Ort, eine Landingpage je Angebot, ein sauberer Anfrageweg.' };
    var ZEIT = { schnell: 'Live in der Regel 5 bis 15 Werktage nach Freigabe der Inhalte. Je schneller Texte, Bilder und Freigaben vorliegen, desto früher.',
      quartal: 'Das passt zum üblichen Ablauf: Erstgespräch, Angebot, 5 bis 15 Werktage Umsetzung, Freigabegespräch, Livegang.',
      offen: 'Kein Druck. Das Erstgespräch ist unverbindlich, das Angebot hat einen Festpreis. Sie entscheiden in Ruhe.' };
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
      var f = $('input:not([type=hidden]):not([type=radio]), input[type=radio]:checked, input[type=radio]', steps[i]); if (f && changed) f.focus({ preventScroll: true });
    }
    function valid(i) {
      var req = steps[i].getAttribute('data-require'); if (!req) return true;
      var ok = !!$('input[name=' + req + ']:checked', form); var err = $('.error', steps[i]); if (err) err.style.display = ok ? '' : 'block';
      return ok;
    }
    function buildResult() {
      var b = val('bedarf') || 'unklar', st = val('status'), z = val('zeitplan'), br = branche ? branche.value : '';
      var items = [BEDARF[b]]; if (STATUS[st]) items.push(STATUS[st]); if (ZEIT[z]) items.push(ZEIT[z]); if (PAIN[br]) items.push(PAIN[br]);
      var html = '<b>Kurz zusammengefasst</b><ul>' + items.map(function (t) { return '<li>' + t + '</li>'; }).join('') + '</ul><p class="tiny">Erste Einschätzung ohne Zusicherung. Alle Preise netto zzgl. USt., Preisliste vom 1. Oktober 2026. Das verbindliche Angebot folgt nach dem Erstgespräch.</p>';
      if (result) result.innerHTML = html;
      if (reco) reco.value = 'Bedarf: ' + (label('bedarf') || 'offen') + ' | Ausgangslage: ' + (label('status') || 'offen') + ' | Zeitplan: ' + (label('zeitplan') || 'offen') + (br ? ' | Branche: ' + br : '');
    }
    on(nextB, 'click', function () { if (valid(cur)) show(cur + 1); });
    on(prevB, 'click', function () { show(Math.max(0, cur - 1)); });
    on(form, 'keydown', function (e) { if (e.key === 'Enter' && cur < steps.length - 1 && e.target.tagName !== 'TEXTAREA') { e.preventDefault(); nextB.click(); } });
    $$('.choice input', form).forEach(function (r) { on(r, 'change', function () { if (cur < steps.length - 1) setTimeout(function () { nextB.click(); }, 160); }); });
    form.__wizard = { show: show, current: function () { return cur; }, reset: function () { if (branche) branche.value = ''; show(0); }, preset: function (b, bd) { if (branche) branche.value = b || ''; var r = bd && $('input[name=bedarf][value="' + bd + '"]', form); if (r) { r.checked = true; show(1); } else show(0); } };
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

  /* ── Systemkarten: Pulse nur im Sichtfeld laufen lassen ─────────────── */
  function initSysmaps() {
    var maps = $$('.sysmap'); if (!maps.length) return;
    maps.forEach(function (m) { try { m.pauseAnimations(); } catch (e) { } });
    if (!('IntersectionObserver' in w)) { maps.forEach(function (m) { try { m.unpauseAnimations(); } catch (e) { } }); return; }
    var io = new IntersectionObserver(function (entries) { entries.forEach(function (en) { try { if (en.isIntersecting) en.target.unpauseAnimations(); else en.target.pauseAnimations(); } catch (e) { } }); }, { threshold: 0.05 });
    maps.forEach(function (m) { io.observe(m); });
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
        var start = performance.now(), dur = 800;
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
    var tog = $('.device-toggle'); if (!tog) return;
    var mini = $('[data-mini]'), browser = $('.browser'), target = mini || browser; if (!target) return;
    var img = browser && $('.browser-body img', browser), mode = 'desktop', auto = null, busy = false;
    var srcD = img && img.getAttribute('src'), srcM = img && img.getAttribute('data-mobile'), setD = (img && img.getAttribute('srcset')) || ''; if (img && !srcM) img = null;
    function set(next) {
      if (busy || next === mode) return; busy = true; mode = next;
      $$('button', tog).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-device') === mode ? 'true' : 'false'); });
      target.classList.add('is-switching');
      setTimeout(function () {
        target.classList.toggle('is-mobile', mode === 'mobile');
        if (img) {
          if (mode === 'mobile') img.removeAttribute('srcset'); else if (setD) img.setAttribute('srcset', setD);
          img.setAttribute('src', mode === 'mobile' ? srcM : srcD);
          img.setAttribute('width', mode === 'mobile' ? '600' : '1200'); img.setAttribute('height', mode === 'mobile' ? '1200' : '790');
        }
        target.classList.remove('is-switching'); busy = false; w.dispatchEvent(new Event('resize'));
      }, mini ? 0 : 350);
    }
    on(tog, 'click', function (e) { var b = e.target.closest('button[data-device]'); if (!b) return; if (auto) { clearInterval(auto); auto = null; } set(b.getAttribute('data-device')); });
    if (mini && w.innerWidth <= 720) set('mobile');
    if (!mini && !d.documentElement.classList.contains('reduced') && w.innerWidth > 900) { auto = setInterval(function () { if (d.hidden) return; set(mode === 'desktop' ? 'mobile' : 'desktop'); }, 7000); }
  }

  /* Live-Miniatur: Desktop-Ansicht zeigt die ganze Seite ohne Scrollbalken */
  function miniFull(fr, f) {
    function size() { try { var h = f.contentDocument.body.offsetHeight; if (h > 300) { fr.style.setProperty('--ph', h); fr.classList.add('is-full'); } } catch (e) { /* fremde Herkunft: Ausschnitt bleibt */ } }
    try { f.contentDocument.querySelectorAll('img[loading=lazy]').forEach(function (i) { i.loading = 'eager'; }); } catch (e) { /* ohne Zugriff */ }
    size();
    try { if ('ResizeObserver' in f.contentWindow) new f.contentWindow.ResizeObserver(size).observe(f.contentDocument.body); } catch (e) { /* ohne Beobachter */ }
    setTimeout(size, 1200);
  }

  function initMiniToggle() {
    $$('[data-mini]').forEach(function (mini) {
      var btn = $('[data-mini-toggle]', mini); if (!btn) return;
      if (/^\/referenzen/.test(w.location.pathname)) { btn.parentNode.hidden = true; return; }
      mini.classList.add('is-collapsed');
      on(btn, 'click', function () {
        var open = mini.classList.toggle('is-collapsed') === false;
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        btn.textContent = open ? 'Weniger anzeigen' : 'Ganze Seite ansehen';
        if (!open) { var top = mini.getBoundingClientRect().top; if (top < 0) mini.scrollIntoView({ block: 'start' }); }
      });
    });
  }

  function initMini() {
    var frames = $$('.mini-frame'); if (!frames.length) return;
    var ready = false;
    function load(fr) { var f = $('iframe', fr); if (!f || f.getAttribute('src')) return; f.onload = function () { fr.classList.add('is-live'); miniFull(fr, f); }; f.setAttribute('src', f.getAttribute('data-src')); }
    function fit(fr) { var base = +fr.getAttribute('data-base') || 1280, wdt = fr.clientWidth; if (wdt > 0) { fr.style.setProperty('--s', (wdt / base).toFixed(4)); if (ready) load(fr); } }
    function all() { frames.forEach(fit); }
    all();
    if ('ResizeObserver' in w) { var ro = new ResizeObserver(all); frames.forEach(function (f) { ro.observe(f); }); } else on(w, 'resize', all);
    function go() { ready = true; all(); }
    if (d.readyState === 'complete') setTimeout(go, 400); else on(w, 'load', function () { setTimeout(go, 400); });
  }

  /* Live-Miniatur: zwischen Beispielseiten umschalten (Handwerk, Praxis, Gastronomie) */
  function initMiniTabs() {
    $$('.mini-tabs').forEach(function (bar) {
      var mini = bar.closest('[data-mini]'); if (!mini) return;
      var scope = mini.parentElement || mini;
      on(bar, 'click', function (e) {
        var b = e.target.closest('button[data-demo]'); if (!b || b.getAttribute('aria-pressed') === 'true') return;
        var slug = b.getAttribute('data-demo'), name = b.getAttribute('data-name') || '';
        $$('button', bar).forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        $$('.mini-frame', mini).forEach(function (fr) {
          var f = $('iframe', fr); if (!f) return;
          var src = (f.getAttribute('data-src') || '').replace(/[a-z]+-muster/, slug), mobile = fr.classList.contains('mini-frame--m');
          f.setAttribute('data-src', src); f.setAttribute('title', 'Beispiel-Landingpage ' + name + ', ' + (mobile ? 'Smartphone' : 'Desktop') + '-Ansicht');
          if (f.getAttribute('src')) { fr.classList.remove('is-live'); f.onload = function () { fr.classList.add('is-live'); miniFull(fr, f); }; f.setAttribute('src', src); }
        });
        var url = $('.browser-bar .url', mini); if (url) url.textContent = b.getAttribute('data-url');
        $$('a[data-demo-link]', scope).forEach(function (a) { a.setAttribute('href', (a.getAttribute('href') || '').replace(/[a-z]+-muster/, slug)); });
      });
    });
  }

  /* Hero: Lichtschein folgt dem Zeiger */
  function initGlow() {
    var hero = $('.hero'); if (!hero || d.documentElement.classList.contains('reduced') || !w.matchMedia('(hover:hover) and (pointer:fine)').matches) return;
    on(hero, 'pointermove', function (e) { var r = hero.getBoundingClientRect(); hero.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100).toFixed(1) + '%'); hero.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100).toFixed(1) + '%'); hero.classList.add('has-glow'); });
    on(hero, 'pointerleave', function () { hero.classList.remove('has-glow'); });
  }

  /* Seitenwechsel: kurzes Ausblenden bei internen Links */
  function initTransitions() {
    if (d.documentElement.classList.contains('reduced')) return;
    on(d, 'click', function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest('a[href]'); if (!a || a.hasAttribute('data-open-modal') || a.target || a.hasAttribute('download')) return;
      var href = a.getAttribute('href'); if (!href || href.charAt(0) === '#' || /^(mailto|tel):/.test(href) || a.origin !== location.origin) return;
      if (a.pathname === location.pathname && a.hash) return;
      e.preventDefault(); d.body.classList.add('is-leaving'); setTimeout(function () { location.href = a.href; }, 170);
    });
    on(w, 'pageshow', function () { d.body.classList.remove('is-leaving'); });
  }

  /* Preise: Paket wählen */
  function initPick() {
    var root = $('[data-pick]'); if (!root) return;
    var P = { landing: { name: 'LANDING', price: '2.290 €', care: '59 € im Monat', bedarf: 'landingpage', text: 'Conversion-Onepager mit Texten, Bildern und Terminbuchung. Struktur, Texte und Bildauswahl entstehen bei uns.', hint: 'Texte und Bilder selbst liefern? LANDING START auf Vorlagenbasis ab 1.290 €.' },
      business: { name: 'BUSINESS WEB', price: '4.490 €', care: '89 € im Monat', bedarf: 'website', text: 'Bis sieben Inhaltsseiten mit Struktur, Texten und Bildern, zum Beispiel eine Leistungsseite je Gewerk oder Ort.', hint: 'Kombivorteil: 500 € Nachlass bei Website und KI-Kommunikation zusammen, ab Paket BUSINESS.' },
      funnel: { name: 'WEB + FUNNEL', price: '6.990 €', care: '129 € im Monat', bedarf: 'funnel', text: 'Bis zwölf Seiten mit Anfrage- oder Verkaufsstrecke, die Besucher Schritt für Schritt zur Anfrage führt.', hint: 'Abweichender Umfang wird vorab schriftlich vereinbart.' } };
    var outs = {}; $$('[data-pick-out]', root).forEach(function (el) { outs[el.getAttribute('data-pick-out')] = el; });
    function choose(k) {
      var p = P[k] || P.landing;
      $$('[data-pick-btn]', root).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-pick-btn') === k ? 'true' : 'false'); });
      if (outs.name) outs.name.textContent = p.name; if (outs.price) outs.price.textContent = p.price; if (outs.care) outs.care.textContent = p.care;
      if (outs.text) outs.text.textContent = p.text; if (outs.hint) outs.hint.textContent = p.hint;
      if (outs.cta) { outs.cta.textContent = p.name + ' anfragen'; outs.cta.setAttribute('data-bedarf', p.bedarf); }
      $$('.price-card[data-pkg]').forEach(function (c) { c.classList.toggle('is-chosen', c.getAttribute('data-pkg') === k); });
    }
    on(root, 'click', function (e) { var b = e.target.closest('[data-pick-btn]'); if (b) choose(b.getAttribute('data-pick-btn')); });
    choose('landing');
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
    var main = $('main'), sections = $$('.has-rail'), first = sections[0], last = sections[sections.length - 1], rail = null, fill = null, railTop = 0, railH = 0, mainTop = 0, ticking = false;
    if (d.body.classList.contains('page-home') && first && last && w.matchMedia('(min-width:1340px)').matches) {
      rail = d.createElement('div'); rail.className = 'rail'; fill = d.createElement('div'); fill.className = 'rail-fill'; rail.appendChild(fill); main.style.position = 'relative'; main.appendChild(rail);
    }
    function layout() {
      if (!rail) return;
      var wr = $('.wrap', first).getBoundingClientRect(), mr = main.getBoundingClientRect();
      rail.style.left = (wr.left - mr.left - 52) + 'px';
      railTop = first.getBoundingClientRect().top - mr.top + 60; railH = Math.max(0, last.getBoundingClientRect().bottom - mr.top - railTop - 80);
      rail.style.top = railTop + 'px'; rail.style.height = railH + 'px'; mainTop = mr.top + w.scrollY;
    }
    var mcta = $('.mobile-cta');
    function update() {
      if (mcta) mcta.classList.toggle('is-on', w.scrollY > 320 && !d.body.classList.contains('menu-open'));
      var max = d.documentElement.scrollHeight - w.innerHeight; bar.style.width = (max > 0 ? Math.min(100, w.scrollY / max * 100) : 0) + '%';
      header.classList.toggle('is-scrolled', w.scrollY > 24);
      if (rail) { var y = w.scrollY + w.innerHeight * 0.55 - (mainTop + railTop); fill.style.height = Math.max(0, Math.min(railH, y)) + 'px'; }
    }
    function onScroll() { if (ticking) return; ticking = true; requestAnimationFrame(function () { update(); ticking = false; }); }
    on(w, 'scroll', onScroll, { passive: true }); on(w, 'resize', function () { layout(); update(); }); on(w, 'load', function () { layout(); update(); });
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
    ['missed', 'order', 'recover', 'sched', 'wage', 'pkg'].forEach(function (k) { f[k] = $('[name=' + k + ']', root); });
    var o = {};
    ['pkg', 'pkgPrice', 'pkgNote', 'lost', 'recovered', 'hours', 'payback', 'paybackNote'].forEach(function (k) { o[k] = $('[data-out=' + k + ']', root); });
    var PK = { landing: { name: 'LANDING', price: 2290, care: 59, note: 'Conversion-Onepager mit Texten, Bildern und Terminbuchung, Pflege 59 € im Monat' },
      business: { name: 'BUSINESS WEB', price: 4490, care: 89, note: 'Bis sieben Inhaltsseiten mit Struktur, Texten und Bildern, Pflege 89 € im Monat' },
      funnel: { name: 'WEB + FUNNEL', price: 6990, care: 129, note: 'Bis zwölf Seiten mit Anfrage- oder Verkaufsstrecke, Pflege 129 € im Monat' } };
    function paint(inp, fmt) { if (!inp || inp.type !== 'range') return; var pct = (inp.value - inp.min) / (inp.max - inp.min) * 100; inp.style.setProperty('--pct', pct + '%'); var out = $('output[for=' + inp.id + ']', root); if (out) out.textContent = fmt(inp.value); }
    function calc() {
      paint(f.missed, function (v) { return v; }); paint(f.order, fmtEUR); paint(f.recover, function (v) { return v + ' %'; });
      paint(f.sched, function (v) { return v + ' h'; }); paint(f.wage, function (v) { return v + ' €'; });
      var missed = +f.missed.value, order = +f.order.value, rec = +f.recover.value / 100, sched = +f.sched.value, wage = +f.wage.value;
      var pk = PK[f.pkg.value] || PK.landing;
      var lost = missed * 4.33 * 0.2 * order;                 // entgangener Umsatz je Monat
      var recovered = lost * rec;                              // davon zurückholbar
      var hours = sched * 4.33 * 0.5;                          // vermeidbare Stunden je Monat
      var gain = recovered + hours * wage - pk.care;           // monatlicher Gewinn gegenüber Pflege
      o.pkg.textContent = pk.name; o.pkgPrice.textContent = fmtEUR(pk.price); o.pkgNote.textContent = pk.note;
      tween(o.lost, lost, fmtEUR); tween(o.recovered, recovered, fmtEUR);
      tween(o.hours, Math.round(hours), function (v) { return Math.round(v) + ' h'; });
      if (gain > 0) { var m = Math.ceil(pk.price / gain); o.payback.textContent = m + (m === 1 ? ' Monat' : ' Monaten'); o.paybackNote.textContent = 'bei ' + fmtEUR(Math.round(gain)) + ' Gewinn je Monat nach Pflege'; }
      else { o.payback.textContent = 'offen'; o.paybackNote.textContent = 'Mit diesen Angaben trägt sich das Paket nicht über zurückgeholte Anfragen. Im Erstgespräch prüfen wir andere Hebel.'; }
    }
    Object.keys(f).forEach(function (k) { if (f[k]) { on(f[k], 'input', calc); on(f[k], 'change', calc); } });
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

  /* Aufklappbare Details: mobil zu, ab 721 px offen */
  function initMore() {
    var els = $$('details.more'); if (!els.length) return;
    var mq = w.matchMedia('(max-width:720px)');
    function apply() { els.forEach(function (el) { if (mq.matches) el.removeAttribute('open'); else el.setAttribute('open', ''); }); }
    apply(); if (mq.addEventListener) mq.addEventListener('change', apply); else mq.addListener(apply);
  }
  /* Wischleisten: Punkte als Positionsanzeige */
  function initSwipe() {
    $$('[data-swipe]').forEach(function (row) {
      var cards = [].slice.call(row.children); if (cards.length < 2) return;
      var dots = d.createElement('div'); dots.className = 'swipe-dots'; dots.setAttribute('aria-hidden', 'true');
      cards.forEach(function () { dots.appendChild(d.createElement('i')); }); row.parentNode.insertBefore(dots, row.nextSibling);
      function mark() { var x = row.scrollLeft + row.clientWidth / 2, idx = 0; cards.forEach(function (c, k) { if (c.offsetLeft <= x) idx = k; }); [].forEach.call(dots.children, function (i, k) { i.classList.toggle('is-on', k === idx); }); }
      function focusable() { var sc = row.scrollWidth > row.clientWidth + 1; if (sc) { row.setAttribute('tabindex', '0'); row.setAttribute('role', 'group'); row.setAttribute('aria-label', 'Karten, mit den Pfeiltasten seitlich scrollbar'); } else { row.removeAttribute('tabindex'); row.removeAttribute('role'); row.removeAttribute('aria-label'); } }
      mark(); focusable(); on(row, 'scroll', mark, { passive: true }); on(w, 'resize', function () { mark(); focusable(); });
    });
  }
  /* Website-Checkliste: Zähler der erfüllten Punkte */
  function initChecklist() {
    var root = $('[data-checklist]'); if (!root) return;
    var boxes = $$('input[type=checkbox]', root), out = $('[data-checklist-out]', root), total = boxes.length;
    function upd() { var n = boxes.filter(function (b) { return b.checked; }).length; if (out) out.textContent = n + ' von ' + total + ' Punkten erfüllt'; root.setAttribute('data-done', n === total ? 'all' : (n ? 'some' : 'none')); }
    boxes.forEach(function (b) { on(b, 'change', upd); }); upd();
  }
  function init() { initNav(); initChecklist(); initMini(); initMiniToggle(); initMiniTabs(); initGlow(); initTransitions(); initPick(); initMore(); initSwipe(); initReveal(); initCampaign(); initForms(); initCheck(); initPartner(); initCalendar(); initWizard(); initModal(); initQuickCheck(); initRoi(); initBlogFilter(); initA11y(); initTabbar(); initYear(); initCountUp(); initSysmaps(); initSequence(); initDeviceToggle(); initSeoProof(); initAccordion(); initScroll(); }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', init); else init();
})();
