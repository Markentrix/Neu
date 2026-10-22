(function () {
  'use strict';
  var API = '/api/';
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function getJSON(p) {
    return fetch(API + p, { headers: { Accept: 'application/json' } }).then(function (r) {
      if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      return r.json();
    });
  }
  function iso(d) { var m = d.getMonth() + 1, t = d.getDate(); return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (t < 10 ? '0' : '') + t; }
  function qs(o) { var a = []; Object.keys(o).forEach(function (k) { if (o[k]) a.push(k + '=' + encodeURIComponent(o[k])); }); return a.length ? '?' + a.join('&') : ''; }

  /* Danke-Seite: Vorgangsnummer aus der Adresse anzeigen */
  if ($('#danke')) {
    var p = new URLSearchParams(location.search), ref = p.get('ref'), typ = p.get('typ');
    if (ref) { $('#danke-nr').textContent = ref.slice(0, 40); $('#danke-ref').hidden = false; }
    if (typ === 'termin') $('#danke-text').textContent = 'Ihr Terminwunsch ist bei uns eingegangen. Wir bestätigen ihn per E-Mail, bei Rückfragen melden wir uns telefonisch.';
  }

  var form = $('#termin-form'); if (!form) return;
  var st = { avail: null, leistungen: [], mitarbeiter: [], busy: false };
  var el = {
    fsL: $('#fs-leistung'), chips: $('#leistung-chips'), fldM: $('#fld-mitarbeiter'), selM: $('#mitarbeiter'),
    datum: $('#datum'), fsZ: $('#fs-zeit'), slots: $('#slots'), msg: $('#termin-msg'), btn: $('#termin-btn'),
    hint: $('#termin-hint'), fb: $('#api-fallback'), title: $('#termin-title')
  };
  var today = new Date(); today.setHours(0, 0, 0, 0);
  el.datum.min = iso(today);

  function setErr(name, text) { var s = $('[data-err="' + name + '"]', form); if (s) s.textContent = text || ''; }
  function clearErrs() { $$('[data-err]', form).forEach(function (s) { s.textContent = ''; }); el.msg.textContent = ''; el.msg.classList.remove('is-err'); }
  function showMsg(t, isErr) { el.msg.textContent = t; el.msg.classList.toggle('is-err', !!isErr); }
  function showFallback() { el.fb.hidden = false; }
  function sel() { var c = $('input[name="leistung"]:checked', form); return { leistung: c ? c.value : '', mitarbeiter: el.selM.value }; }

  function buildLeistungen() {
    if (!st.leistungen.length) return;
    el.chips.innerHTML = '';
    st.leistungen.forEach(function (l, i) {
      var lab = document.createElement('label'); lab.className = 'chip';
      var inp = document.createElement('input'); inp.type = 'radio'; inp.name = 'leistung'; inp.value = l.key; if (i === 0) inp.checked = true;
      var sp = document.createElement('span'); sp.textContent = l.name;
      if (l.beschreibung) lab.title = l.beschreibung;
      lab.appendChild(inp); lab.appendChild(sp); el.chips.appendChild(lab);
    });
    el.fsL.hidden = false;
  }
  function buildMitarbeiter() {
    if (st.mitarbeiter.length < 2) return;
    var s = sel().leistung;
    el.selM.innerHTML = '<option value="">Egal</option>';
    st.mitarbeiter.forEach(function (m) {
      if (s && m.leistungen && m.leistungen.length && m.leistungen.indexOf(s) < 0) return;
      var o = document.createElement('option'); o.value = m.key; o.textContent = m.name; el.selM.appendChild(o);
    });
    el.fldM.hidden = false;
  }
  function labelFor() {
    var self = st.avail && st.avail.selfBooking;
    el.btn.textContent = self ? 'Termin buchen' : 'Terminwunsch senden';
    el.title.textContent = self ? 'Termin buchen' : 'Termin anfragen';
  }
  function loadAvail() {
    var s = sel();
    return getJSON('verfuegbarkeit' + qs(s)).then(function (a) {
      st.avail = a; labelFor();
      if (a.nextFree && !el.datum.value) { el.datum.value = a.nextFree; loadSlots(); }
      else if (el.datum.value) checkDay();
    });
  }
  function dayClosed(d) {
    var a = st.avail; if (!a) return '';
    var dt = new Date(d + 'T00:00:00');
    if (isNaN(dt)) return '';
    if (dt < today) return 'Bitte wählen Sie einen Tag ab heute.';
    if ((a.closedWeekdays || []).indexOf(dt.getDay()) >= 0) return 'An diesem Wochentag ist geschlossen.';
    if ((a.blocked || []).indexOf(d) >= 0) return 'An diesem Tag sind keine Termine möglich.' + (a.nextFree ? ' Nächster freier Tag: ' + a.nextFree.split('-').reverse().join('.') + '.' : '');
    return '';
  }
  function checkDay() {
    setErr('datum', '');
    var d = el.datum.value; if (!d) { el.fsZ.hidden = true; return false; }
    var why = dayClosed(d);
    if (why) { setErr('datum', why); el.fsZ.hidden = true; el.slots.innerHTML = ''; return false; }
    return true;
  }
  function loadSlots() {
    if (!checkDay()) return;
    var s = sel(), d = el.datum.value;
    getJSON('slots' + qs({ tag: d, leistung: s.leistung, mitarbeiter: s.mitarbeiter })).then(function (r) {
      el.slots.innerHTML = ''; var any = false;
      (r.slots || []).forEach(function (x) {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = x.zeit; b.setAttribute('aria-pressed', 'false');
        if (!x.frei) { b.disabled = true; b.title = 'Belegt'; } else any = true;
        b.addEventListener('click', function () {
          $$('button', el.slots).forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
          el.slots.setAttribute('data-wert', x.zeit); setErr('uhrzeit', '');
        });
        el.slots.appendChild(b);
      });
      el.slots.removeAttribute('data-wert');
      if (!any) { var n = document.createElement('span'); n.className = 'times-empty'; n.textContent = 'Für diesen Tag sind keine Zeiten frei. Bitte wählen Sie einen anderen Tag.'; el.slots.appendChild(n); }
      el.fsZ.hidden = false;
    }).catch(function () { showFallback(); });
  }

  /* Start: Verfügbarkeit ist Pflicht, Leistungen und Mitarbeiter sind optional */
  Promise.all([
    getJSON('verfuegbarkeit'),
    getJSON('leistungen').catch(function () { return { leistungen: [] }; }),
    getJSON('mitarbeiter').catch(function () { return { mitarbeiter: [] }; })
  ]).then(function (r) {
    st.avail = r[0]; st.leistungen = r[1].leistungen || []; st.mitarbeiter = r[2].mitarbeiter || [];
    buildLeistungen(); buildMitarbeiter(); labelFor();
    if (st.avail.nextFree) { el.datum.value = st.avail.nextFree; loadSlots(); }
  }).catch(function () { showFallback(); });

  el.datum.addEventListener('change', loadSlots);
  el.chips.addEventListener('change', function () { buildMitarbeiter(); loadAvail().then(loadSlots).catch(showFallback); });
  el.selM.addEventListener('change', function () { loadAvail().then(loadSlots).catch(showFallback); });

  function val() {
    var ok = true; clearErrs();
    function need(n, t) { var f = form.elements[n]; if (!f || !String(f.value).trim()) { setErr(n, t); ok = false; } }
    need('name', 'Bitte geben Sie Ihren Namen an.');
    need('telefon', 'Bitte geben Sie eine Telefonnummer an.');
    need('email', 'Bitte geben Sie Ihre E-Mail-Adresse an, dorthin senden wir die Bestätigung.');
    if (form.elements.email.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.elements.email.value)) { setErr('email', 'Bitte prüfen Sie die E-Mail-Adresse.'); ok = false; }
    need('datum', 'Bitte wählen Sie einen Wunschtag.');
    if (form.elements.datum.value && !checkDay()) ok = false;
    if (!form.elements.einwilligung.checked) { setErr('einwilligung', 'Bitte stimmen Sie der Datenschutzerklärung zu.'); ok = false; }
    if (!ok) { var f = $('.err:not(:empty)', form); if (f) { var inp = f.parentNode.querySelector('input,select,textarea,button'); if (inp) inp.focus(); } }
    return ok;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault(); if (st.busy) return;
    if (!val()) return;
    var s = sel(), f = form.elements;
    var payload = {
      typ: 'termin', name: f.name.value.trim(), telefon: f.telefon.value.trim(), email: f.email.value.trim(),
      datum: f.datum.value, uhrzeit: el.slots.getAttribute('data-wert') || '', nachricht: f.nachricht.value.trim(),
      fahrzeug: f.fahrzeug.value.trim(), leistung: s.leistung, mitarbeiter: s.mitarbeiter,
      einwilligung: 'ja', website: f.website.value
    };
    st.busy = true; el.btn.disabled = true; var old = el.btn.textContent; el.btn.textContent = 'Wird gesendet …';
    fetch(API + 'anfrage', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, body: j }; }); })
      .then(function (r) {
        if (r.status === 200 && r.body && r.body.ok) { location.href = 'danke.html?typ=termin&ref=' + encodeURIComponent(r.body.ref || ''); return; }
        if (r.status === 422 && r.body && r.body.errors) {
          Object.keys(r.body.errors).forEach(function (k) { setErr(k, r.body.errors[k]); });
          if (r.body.errors.uhrzeit) { showMsg('Diese Uhrzeit ist inzwischen vergeben. Bitte wählen Sie eine andere.', true); loadSlots(); }
          else showMsg('Bitte prüfen Sie die markierten Felder.', true);
        } else if (r.status === 429) { showMsg('Bitte versuchen Sie es später noch einmal.', true); }
        else { showMsg('Das Senden hat nicht geklappt. Eingaben bleiben erhalten.', true); showFallback(); }
      })
      .catch(function () { showMsg('Keine Verbindung. Ihre Eingaben bleiben erhalten.', true); showFallback(); })
      .then(function () { st.busy = false; el.btn.disabled = false; el.btn.textContent = old; });
  });
})();
