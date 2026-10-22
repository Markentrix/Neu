/* Nur Vorschau. Simuliert die Portal-Schnittstellen und -Bausteine, damit die Vorlage ohne Portal bedienbar ist.
   Gehört NICHT zu website-fertig: Im Portal liefern /api/* und das Baustein-Skript diese Funktionen.
   Mit ?offline=1 in der Adresse lässt sich der Ausfall der Schnittstelle (Ausweichweg) ansehen. */
(function () {
  'use strict';
  var offline = /[?&]offline=1/.test(location.search);
  var real = window.fetch.bind(window);
  var LEIST = [
    { key: 'inspektion', name: 'Inspektion', beschreibung: 'Wartung nach Herstellervorgabe', preis: 'ab 129 €', dauer: 120 },
    { key: 'reifen', name: 'Reifenwechsel', beschreibung: 'Wechsel und Auswuchten', preis: 'ab 39 €', dauer: 45 },
    { key: 'bremsen', name: 'Bremsen', beschreibung: 'Prüfung und Austausch', preis: 'nach Prüfung', dauer: 90 },
    { key: 'klima', name: 'Klimaservice', beschreibung: 'Prüfung und Wartung', preis: 'ab 89 €', dauer: 60 },
    { key: 'hu', name: 'HU-Vorbereitung', beschreibung: 'Vorabprüfung', preis: 'ab 49 €', dauer: 60 }
  ];
  var MA = [
    { key: 'anna', name: 'Anna (Meisterin)', leistungen: ['inspektion', 'bremsen', 'hu', 'klima'] },
    { key: 'jonas', name: 'Jonas', leistungen: ['reifen', 'inspektion', 'klima'] }
  ];
  var TIMES = ['08:00', '09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00'];
  var booked = {};
  function iso(d) { var m = d.getMonth() + 1, t = d.getDate(); return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (t < 10 ? '0' : '') + t; }
  function hash(s) { var h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
  function nextFree() { var d = new Date(); d.setHours(0, 0, 0, 0); for (var i = 1; i < 30; i++) { d.setDate(d.getDate() + 1); if (d.getDay() > 0 && d.getDay() < 6) return iso(d); } return null; }
  function blocked() { var a = []; var d = new Date(); d.setDate(d.getDate() + 9); a.push(iso(d)); return a; }
  function json(status, body) { return Promise.resolve(new Response(JSON.stringify(body), { status: status, headers: { 'Content-Type': 'application/json' } })); }
  function q(url) { var u = new URL(url, location.origin); var o = {}; u.searchParams.forEach(function (v, k) { o[k] = v; }); return { path: u.pathname, p: o }; }
  function slots(tag, leistung, ma) {
    return TIMES.map(function (t) {
      var key = tag + '|' + t + '|' + ma;
      var frei = (hash(tag + t + (leistung || '')) % 5 !== 0) && !booked[key];
      return { zeit: t, frei: frei };
    });
  }
  window.fetch = function (url, opt) {
    if (typeof url !== 'string' || url.indexOf('/api/') !== 0) return real(url, opt);
    if (offline) return Promise.reject(new TypeError('offline'));
    var r = q(url), m = (opt && opt.method) || 'GET';
    return new Promise(function (res) { setTimeout(res, 250); }).then(function () {
      if (r.path === '/api/verfuegbarkeit') return json(200, { blocked: blocked(), closedWeekdays: [0, 6], nextFree: nextFree(), selfBooking: true, slotTimes: TIMES });
      if (r.path === '/api/leistungen') return json(200, { leistungen: LEIST });
      if (r.path === '/api/mitarbeiter') return json(200, { mitarbeiter: MA });
      if (r.path === '/api/slots') return json(200, { tag: r.p.tag, slots: slots(r.p.tag || '', r.p.leistung, r.p.mitarbeiter || '') });
      if (r.path === '/api/anfrage' && m === 'POST') {
        var b = {}; try { b = JSON.parse(opt.body); } catch (e) { /* leer */ }
        if (b.website) return json(200, { ok: true, ref: 'X-0' });
        var err = {};
        if (!b.name) err.name = 'Bitte geben Sie Ihren Namen an.';
        if (!b.telefon) err.telefon = 'Bitte geben Sie eine Telefonnummer an.';
        if (!b.email) err.email = 'Bitte geben Sie Ihre E-Mail-Adresse an.';
        if (b.einwilligung !== 'ja') err.einwilligung = 'Bitte stimmen Sie der Datenschutzerklärung zu.';
        if (b.typ === 'termin' && !b.datum) err.datum = 'Bitte wählen Sie einen Wunschtag.';
        if (/konflikt/i.test(b.nachricht || '')) err.uhrzeit = 'Diese Uhrzeit ist bereits vergeben.';
        if (/limit/i.test(b.nachricht || '')) return json(429, { ok: false });
        if (Object.keys(err).length) return json(422, { ok: false, errors: err });
        if (b.uhrzeit) booked[b.datum + '|' + b.uhrzeit + '|' + (b.mitarbeiter || '')] = 1;
        return json(200, { ok: true, ref: 'W-' + (10000 + hash(b.email + Date.now()) % 89999) });
      }
      return json(404, { ok: false });
    });
  };
  document.addEventListener('DOMContentLoaded', function () {
    var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = 'assets/vorschau.css'; document.head.appendChild(l);
    var a = document.createElement('aside'); a.className = 'vp-ribbon'; a.setAttribute('aria-label', 'Hinweis zur Vorschau');
    a.innerHTML = 'Vorschau einer portalfähigen Kundenvorlage (fiktiv). Schnittstellen und Portal-Bausteine sind hier simuliert. <a href="?offline=1">Ausfall der Schnittstelle ansehen</a>';
    document.body.insertBefore(a, document.body.firstChild);
    var k = document.querySelector('[data-mk="kontakt"]');
    if (k) {
      k.innerHTML = '<form class="mk-box" novalidate><span class="vp-badge">Portal-Baustein „Kontaktformular“ (Vorschau)</span><label>Name<input name="name" autocomplete="name"></label><label>E-Mail<input name="email" type="email" autocomplete="email"></label><label>Nachricht<textarea name="nachricht" rows="3"></textarea></label><label style="display:flex;gap:8px;align-items:flex-start;font-weight:400"><input type="checkbox" style="width:20px;margin-top:3px"><span>Ich stimme der Datenschutzerklärung zu.</span></label><button type="submit">Nachricht senden</button><p class="mk-ok" role="status"></p></form>';
      k.querySelector('form').addEventListener('submit', function (e) { e.preventDefault(); k.querySelector('.mk-ok').textContent = 'Vorschau: Im Portal geht die Nachricht jetzt an den Inhaber und Sie erhalten eine Bestätigung.'; });
    }
    var bw = document.querySelector('[data-mk="bewertungen"]');
    if (bw) bw.innerHTML = '<span class="vp-badge">Portal-Baustein „Google-Bewertungen“ (Vorschau)</span><div class="mk-rev"><div><span class="stars" aria-hidden="true">☆☆☆☆☆</span><b>Platz für Ihre Bewertungen</b><span>Hier erscheinen echte Google-Bewertungen Ihrer Kunden, sobald der Dienst im Portal eingeschaltet ist.</span></div><div><span class="stars" aria-hidden="true">☆☆☆☆☆</span><b>Nur echte Stimmen</b><span>Es werden keine Bewertungen erfunden oder nachgebaut.</span></div><div><span class="stars" aria-hidden="true">☆☆☆☆☆</span><b>Einwilligung zuerst</b><span>Die Bewertungen laden erst nach Zustimmung.</span></div></div>';
    var c = document.querySelector('[data-mk="cookies"]');
    if (c) c.innerHTML = '<a href="datenschutz.html#statistik">Statistik-Einstellungen</a>';
  });
})();
