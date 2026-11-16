(function () {
  'use strict';
  var d = document, $ = function (s, r) { return (r || d).querySelector(s); }, $$ = function (s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); };
  var TEL = '05141 32900', MAIL = 'info@tierfreunde-celle.de';

  /* Statistik ohne Cookies */
  var gesendet = {};
  function ereignis(t, n) {
    if (n && gesendet[n]) return; if (n) gesendet[n] = 1;
    try { navigator.sendBeacon('/api/e', new Blob([JSON.stringify({ t: t, u: location.pathname, n: n || '', w: innerWidth })], { type: 'application/json' })); } catch (e) {}
  }
  ereignis('pv');
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a');
    if (!a) return;
    var h = a.getAttribute('href') || '';
    if (h.indexOf('tel:') === 0) ereignis('ev', 'anruf_klick');
    else if (h.indexOf('betterplace.org') > -1) ereignis('ev', 'spende_klick');
  });

  /* Wartetage aus dem echten Steckbrief-Datum */
  var zahl = new Intl.NumberFormat('de-DE'), heute = new Date();
  $$('[data-seit]').forEach(function (el) {
    var t = Math.floor((heute - new Date(el.getAttribute('data-seit') + 'T00:00:00')) / 864e5);
    if (!(t >= 0)) return;
    var ziel = $('.tage-zahl', el);
    if (!ziel) return;
    ziel.textContent = zahl.format(t);
    $('small', el).textContent = t === 1 ? 'Tag auf der Suche' : 'Tage auf der Suche';
    el.setAttribute('data-tage', t);
  });

  /* Öffnungszeiten: Mo-Fr 8-11, Sa-So 10-11, Mo/Mi/Fr/So 15-17 */
  var ZEITEN = { 0: [[10, 11], [15, 17]], 1: [[8, 11], [15, 17]], 2: [[8, 11]], 3: [[8, 11], [15, 17]], 4: [[8, 11]], 5: [[8, 11], [15, 17]], 6: [[10, 11]] };
  var TAGE = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
  function berlin() {
    try {
      var p = {}; new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Berlin', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
      return { tag: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(p.weekday), std: (+p.hour % 24) + (+p.minute) / 60 };
    } catch (e) { var n = new Date(); return { tag: n.getDay(), std: n.getHours() + n.getMinutes() / 60 }; }
  }
  (function () {
    var jetzt = berlin(), text = '', offen = false, fenster = -1;
    ZEITEN[jetzt.tag].forEach(function (f, i) { if (jetzt.std >= f[0] && jetzt.std < f[1]) { offen = true; fenster = i; text = 'Jetzt geöffnet bis ' + f[1] + ' Uhr'; } });
    if (!offen) {
      var spaeter = ZEITEN[jetzt.tag].filter(function (f) { return f[0] > jetzt.std; })[0];
      if (spaeter) text = 'Gerade geschlossen. Öffnet heute um ' + spaeter[0] + ' Uhr';
      else { var m = (jetzt.tag + 1) % 7; text = 'Gerade geschlossen. Öffnet morgen, ' + TAGE[m] + ', um ' + ZEITEN[m][0][0] + ' Uhr'; }
    }
    $$('[data-status]').forEach(function (el) { el.textContent = text; el.setAttribute('data-offen', offen ? 'ja' : 'nein'); });
    $$('.woche tr[data-tag="' + jetzt.tag + '"]').forEach(function (tr) {
      tr.classList.add('heute');
      var th = $('th', tr); if (th && !$('.nur-sr', th)) { var s = d.createElement('span'); s.className = 'nur-sr'; s.textContent = ' (heute)'; th.appendChild(s); }
      if (offen) { var td = $$('td', tr)[fenster]; if (td) td.classList.add('jetzt'); }
    });
  })();

  /* Menü am Handy */
  var nav = $('#nav'), mk = $('.menue-knopf');
  function menue(auf) {
    nav.classList.toggle('offen', auf); mk.setAttribute('aria-expanded', auf ? 'true' : 'false');
    if (auf) { var z = $('.nav-zu', nav); if (z) z.focus(); } else mk.focus();
  }
  if (nav && mk) {
    mk.addEventListener('click', function () { menue(!nav.classList.contains('offen')); });
    $$('.nav-zu', nav).forEach(function (b) { b.addEventListener('click', function () { menue(false); }); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && nav.classList.contains('offen')) menue(false); });
  }

  /* Tierliste sortieren */
  $$('[data-sortiere]').forEach(function (b) {
    b.addEventListener('click', function () {
      var liste = $('#' + b.getAttribute('aria-controls')), lang = b.getAttribute('aria-pressed') !== 'true';
      var tun = function () {
        $$('.schild', liste).sort(function (x, y) {
          var a = $('[data-seit]', x), c = $('[data-seit]', y), i = +x.getAttribute('data-nr'), j = +y.getAttribute('data-nr');
          if (!lang) return i - j;
          var s = a ? a.getAttribute('data-seit') : '9', t = c ? c.getAttribute('data-seit') : '9';
          return s < t ? -1 : s > t ? 1 : i - j;
        }).forEach(function (k) { liste.appendChild(k); });
        b.setAttribute('aria-pressed', lang ? 'true' : 'false');
      };
      if (d.startViewTransition && !matchMedia('(prefers-reduced-motion: reduce)').matches) d.startViewTransition(tun); else tun();
    });
  });

  /* Bilder am Steckbrief */
  var haupt = $('.steck-haupt img');
  $$('.leiste button').forEach(function (b) {
    b.addEventListener('click', function () {
      var i = $('img', b);
      haupt.src = i.getAttribute('data-gross'); haupt.removeAttribute('srcset'); haupt.alt = i.alt;
      haupt.width = i.getAttribute('data-w'); haupt.height = i.getAttribute('data-h');
      $$('.leiste button').forEach(function (x) { x.setAttribute('aria-current', x === b ? 'true' : 'false'); });
    });
  });
  var licht = $('dialog.licht');
  if (licht && licht.showModal) $$('[data-licht]').forEach(function (b) {
    b.addEventListener('click', function () {
      var q = $('img', b), z = $('img', licht);
      z.src = q.getAttribute('data-gross') || q.currentSrc || q.src; z.alt = q.alt; licht.showModal();
    });
  });

  /* IBAN kopieren */
  $$('[data-kopiere]').forEach(function (b) {
    var alt = b.textContent;
    b.addEventListener('click', function () {
      var t = b.getAttribute('data-kopiere');
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () {
        b.textContent = 'IBAN ist kopiert'; ereignis('ev', 'iban_kopiert');
        setTimeout(function () { b.textContent = alt; }, 2500);
      }, function () { b.textContent = 'Bitte von Hand markieren'; });
    });
  });

  /* Anfrage-Formular (Portal: POST /api/anfrage) */
  $$('form[data-anfrage]').forEach(function (f) {
    var knopf = $('button[type=submit]', f), meldung = $('.meldung', f), text = knopf.textContent, laeuft = false;
    function fehler(name, t) {
      var feld = f.elements[name], p = $('[data-fehler="' + name + '"]', f);
      if (p) p.textContent = t || '';
      if (feld && feld.setAttribute) feld.setAttribute('aria-invalid', t ? 'true' : 'false');
    }
    function sag(t, mitKontakt) {
      meldung.textContent = t;
      if (mitKontakt) {
        meldung.appendChild(d.createTextNode(' Du erreichst uns auch direkt: '));
        var a = d.createElement('a'); a.href = 'tel:+49514132900'; a.textContent = 'Telefon ' + TEL; meldung.appendChild(a);
        meldung.appendChild(d.createTextNode(' oder '));
        var m = d.createElement('a'); m.href = 'mailto:' + MAIL; m.textContent = MAIL; meldung.appendChild(m);
        meldung.appendChild(d.createTextNode('.'));
      }
    }
    f.setAttribute('novalidate', '');
    f.addEventListener('submit', function (e) {
      e.preventDefault(); if (laeuft) return;
      var ok = true, daten = { typ: f.getAttribute('data-anfrage') };
      $$('input,textarea', f).forEach(function (el) {
        if (!el.name) return;
        var w = el.type === 'checkbox' ? (el.checked ? 'ja' : '') : el.value.trim();
        if (el.name !== 'website') fehler(el.name, '');
        if (el.required && !w) { ok = false; fehler(el.name, el.type === 'checkbox' ? 'Bitte bestätige die Datenschutzerklärung, sonst dürfen wir dir nicht antworten.' : 'Bitte ausfüllen.'); }
        else if (el.type === 'email' && w && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(w)) { ok = false; fehler(el.name, 'Bitte prüfe die E-Mail-Adresse, zum Beispiel name@anbieter.de.'); }
        daten[el.name] = w;
      });
      if (!ok) { sag('Es fehlen noch Angaben. Die Felder sind markiert.'); var erst = $('[aria-invalid=true]', f); if (erst) erst.focus(); return; }
      laeuft = true; knopf.disabled = true; knopf.textContent = 'Wird gesendet …'; sag('');
      var ab = window.AbortController ? new AbortController() : null, uhr = setTimeout(function () { if (ab) ab.abort(); }, 10000);
      fetch('/api/anfrage', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(daten), signal: ab ? ab.signal : undefined })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { s: r.status, j: j }; }); })
        .then(function (r) {
          clearTimeout(uhr);
          if (r.s === 200 && r.j.ok) { ereignis('ev', 'anfrage_gesendet'); location.href = '/danke.html?typ=' + encodeURIComponent(daten.typ) + '&ref=' + encodeURIComponent(r.j.ref || ''); return; }
          laeuft = false; knopf.disabled = false; knopf.textContent = text;
          if (r.s === 422 && r.j.errors) {
            var rest = [];
            Object.keys(r.j.errors).forEach(function (k) { if ($('[data-fehler="' + k + '"]', f)) fehler(k, r.j.errors[k]); else rest.push(r.j.errors[k]); });
            sag(rest.length ? rest.join(' ') : 'Bitte prüfe die markierten Felder.');
            var erst = $('[aria-invalid=true]', f); if (erst) erst.focus();
          } else if (r.s === 429) sag('Gerade kommen zu viele Anfragen an. Bitte versuche es später noch einmal.', true);
          else sag('Die Anfrage konnte nicht gesendet werden. Deine Eingaben sind noch da, du kannst es noch einmal versuchen.', true);
        })
        .catch(function () {
          clearTimeout(uhr); laeuft = false; knopf.disabled = false; knopf.textContent = text;
          sag('Die Verbindung hat nicht geklappt. Deine Eingaben sind noch da, du kannst es noch einmal versuchen.', true);
        });
    });
  });

  /* Danke-Seite: Vorgangsnummer nur als Text einsetzen */
  var ref = $('[data-ref]');
  if (ref) {
    var q = new URLSearchParams(location.search), r = (q.get('ref') || '').slice(0, 40);
    if (r) { ref.textContent = r; $('[data-ref-zeile]').hidden = false; }
  }
})();
