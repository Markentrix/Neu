// @ts-nocheck – eigenständiges Skript für fremde Websites, nutzt keine Module
/* Markentrix Website-Dienste: Kontaktformular, Terminbuchung, Google-Bewertungen und PayPal für Kunden-Websites.
   Einbau: <script src="https://portal.…/static/js/site.js" data-site="mk_…" defer></script> und je Dienst ein <div data-mk="kontakt|termin|bewertungen|paypal"></div>.
   Die Seite bekommt nie ein Passwort: alles Vertrauliche liegt verschlüsselt auf dem Markentrix-Server. Alle Inhalte werden als Text eingesetzt (kein innerHTML). */
(function () {
  'use strict';
  var skript = document.currentScript || document.querySelector('script[data-site]');
  if (!skript) return;
  var site = skript.getAttribute('data-site'), basis = new URL(skript.src, location.href).origin;
  if (!site) return;
  var api = basis + '/site/' + encodeURIComponent(site) + '/';

  function el(tag, attrs) {
    var e = document.createElement(tag), i, k = attrs || {};
    Object.keys(k).forEach(function (n) { if (n === 'class') e.className = k[n]; else if (n === 'text') e.textContent = k[n]; else if (k[n] !== null && k[n] !== undefined && k[n] !== false) e.setAttribute(n, k[n] === true ? '' : k[n]); });
    for (i = 2; i < arguments.length; i++) { var c = arguments[i]; if (c === null || c === undefined || c === false) continue; e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); }
    return e;
  }
  function anfrage(methode, pfad, daten) {
    return fetch(api + pfad, { method: methode, credentials: 'omit', headers: methode === 'POST' ? { 'Content-Type': 'text/plain' } : {}, body: methode === 'POST' ? JSON.stringify(daten) : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) { var m = typeof j.detail === 'string' ? j.detail : 'Das hat leider nicht geklappt. Bitte versuchen Sie es später noch einmal.'; var f = new Error(m); f.status = r.status; throw f; } return j; }); });
  }

  var css = '.mk-box{font:inherit;color:inherit;max-width:640px}.mk-box *{box-sizing:border-box}.mk-box label{display:block;font-size:.9em;margin:10px 0 4px}' +
    '.mk-box input,.mk-box textarea{width:100%;font:inherit;padding:10px 12px;border:1px solid rgba(128,128,128,.5);border-radius:8px;background:transparent;color:inherit}' +
    '.mk-box textarea{min-height:110px;resize:vertical}.mk-btn{font:inherit;cursor:pointer;border:0;border-radius:8px;padding:11px 18px;margin-top:14px;background:var(--mk-akzent,#1f6feb);color:#fff;font-weight:600}' +
    '.mk-btn:disabled{opacity:.6;cursor:default}.mk-btn.mk-leise{background:transparent;color:inherit;border:1px solid rgba(128,128,128,.5)}' +
    '.mk-fehler{margin:10px 0;padding:10px 12px;border-radius:8px;background:rgba(220,38,38,.12);border:1px solid rgba(220,38,38,.4)}.mk-ok{margin:10px 0;padding:10px 12px;border-radius:8px;background:rgba(22,163,74,.12);border:1px solid rgba(22,163,74,.4)}' +
    '.mk-falle{position:absolute!important;left:-9999px!important;height:0;overflow:hidden}.mk-check{display:flex!important;gap:8px;align-items:flex-start;font-size:.85em}.mk-check input{width:auto;margin-top:3px}' +
    '.mk-chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.mk-chip{font:inherit;cursor:pointer;padding:8px 12px;border-radius:8px;border:1px solid rgba(128,128,128,.5);background:transparent;color:inherit}' +
    '.mk-chip[aria-pressed=true]{background:var(--mk-akzent,#1f6feb);color:#fff;border-color:transparent}.mk-sterne{font-size:1.6em;letter-spacing:2px;color:#f5a623}' +
    '.mk-fotos{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.mk-foto{position:relative;width:76px;height:76px;border-radius:8px;overflow:hidden;border:1px solid rgba(128,128,128,.5)}.mk-foto img{width:100%;height:100%;object-fit:cover;display:block}.mk-foto button{position:absolute;top:2px;right:2px;width:24px;height:24px;border:0;border-radius:50%;background:rgba(0,0,0,.7);color:#fff;cursor:pointer;line-height:1;font:inherit}.mk-foto.mk-lade{opacity:.5}' +
    '.mk-bew{margin:12px 0;padding:12px 14px;border:1px solid rgba(128,128,128,.35);border-radius:10px}.mk-klein{font-size:.8em;opacity:.7}';
  document.head.appendChild(el('style', { text: css }));

  function box(c) { c.textContent = ''; var b = el('div', { class: 'mk-box' }); c.appendChild(b); return b; }
  function meldung(b, art, text) { var alt = b.querySelector('.mk-msg'); if (alt) alt.remove(); if (text) b.insertBefore(el('div', { class: 'mk-msg ' + (art === 'ok' ? 'mk-ok' : 'mk-fehler'), role: art === 'ok' ? 'status' : 'alert', text: text }), b.firstChild); }
  function feld(label, el_) { return el('div', {}, el('label', { text: label }), el_); }
  function zustimmung(c) {
    var cb = el('input', { type: 'checkbox', required: true });
    var l = el('a', { href: c.getAttribute('data-datenschutz') || '/datenschutz', target: '_blank', rel: 'noopener', text: 'Datenschutzerklärung' });
    return { cb: cb, el: el('label', { class: 'mk-check' }, cb, el('span', {}, 'Ich stimme zu, dass meine Angaben zur Bearbeitung meiner Anfrage verarbeitet werden. Mehr in der ', l, '.')) };
  }
  // ------------------------------------------------------------ Fotos (nur wenn der Betrieb sie im Portal eingeschaltet hat)
  var fotoEinst = { aktiv: false, max: 5, tage: 90 };
  function verkleinern(datei) {
    // Foto im Browser auf höchstens 1600 Pixel verkleinern und als JPEG neu speichern (spart Datenvolumen, entfernt nebenbei Standort und Kameradaten)
    return new Promise(function (ok, nein) {
      var url = URL.createObjectURL(datei), bild = new Image();
      bild.onload = function () {
        var f = Math.min(1, 1600 / Math.max(bild.naturalWidth, bild.naturalHeight)), cv = document.createElement('canvas');
        cv.width = Math.max(1, Math.round(bild.naturalWidth * f)); cv.height = Math.max(1, Math.round(bild.naturalHeight * f));
        cv.getContext('2d').drawImage(bild, 0, 0, cv.width, cv.height); URL.revokeObjectURL(url);
        cv.toBlob(function (b) { if (b) ok(b); else nein(new Error('Das Foto konnte nicht verarbeitet werden.')); }, 'image/jpeg', 0.82);
      };
      bild.onerror = function () { URL.revokeObjectURL(url); nein(new Error('Dieses Foto kann nicht gelesen werden. Bitte ein JPG oder PNG wählen.')); };
      bild.src = url;
    });
  }
  function fotoHochladen(blob) {
    return fetch(api + 'foto', { method: 'POST', credentials: 'omit', headers: { 'Content-Type': 'text/plain' }, body: blob })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : 'Das Foto konnte nicht hochgeladen werden.'); return j.token; }); });
  }
  function fotoFeld(b) {
    if (!fotoEinst.aktiv) return { el: null, tokens: function () { return []; }, bereit: function () { return true; }, zuruecksetzen: function () {} };
    var liste = [], laeuft = 0, vorschau = el('div', { class: 'mk-fotos' }), meld = el('div', { class: 'mk-klein', role: 'status' }),
      eingabe = el('input', { type: 'file', accept: 'image/jpeg,image/png,image/webp,image/*', multiple: true, 'aria-describedby': 'mk-fotohinweis' });
    function zeigen() { meld.textContent = liste.length >= fotoEinst.max ? 'Mehr als ' + fotoEinst.max + ' Fotos sind nicht möglich.' : ''; }
    eingabe.addEventListener('change', function () {
      Array.prototype.slice.call(eingabe.files).forEach(function (datei) {
        if (liste.length + laeuft >= fotoEinst.max) { zeigen(); return; }
        laeuft++;
        var kachel = el('div', { class: 'mk-foto mk-lade' }), bild = el('img', { alt: 'Hochgeladenes Foto' }), weg = el('button', { type: 'button', 'aria-label': 'Foto entfernen', text: '×' });
        kachel.appendChild(bild); kachel.appendChild(weg); vorschau.appendChild(kachel);
        verkleinern(datei).then(function (blob) {
          bild.src = URL.createObjectURL(blob);
          return fotoHochladen(blob);
        }).then(function (token) {
          laeuft--; kachel.classList.remove('mk-lade'); var eintrag = { token: token };
          liste.push(eintrag); weg.addEventListener('click', function () { liste.splice(liste.indexOf(eintrag), 1); kachel.remove(); zeigen(); }); zeigen();
        }).catch(function (er) { laeuft--; kachel.remove(); meldung(b, 'fehler', er.message); });
      });
      eingabe.value = '';
    });
    var hinweis = el('div', { class: 'mk-klein', id: 'mk-fotohinweis', text: 'Optional: bis zu ' + fotoEinst.max + ' Fotos, damit wir Ihre Anfrage besser einschätzen können. Nur wir sehen sie, sie werden nach ' + fotoEinst.tage + ' Tagen automatisch gelöscht.' });
    return { el: el('div', {}, el('label', { text: 'Fotos (freiwillig)' }), eingabe, vorschau, meld, hinweis),
      tokens: function () { return liste.map(function (x) { return x.token; }); }, bereit: function () { return laeuft === 0; },
      zuruecksetzen: function () { liste = []; vorschau.textContent = ''; zeigen(); } };
  }
  function falle() { return el('div', { class: 'mk-falle', 'aria-hidden': 'true' }, el('input', { name: 'hp', tabindex: '-1', autocomplete: 'off' })); }

  // ------------------------------------------------------------ Kontaktformular
  function kontakt(c) {
    var b = box(c), n = el('input', { required: true, maxlength: 120, autocomplete: 'name' }), m = el('input', { type: 'email', required: true, maxlength: 200, autocomplete: 'email' }),
      t = el('input', { type: 'tel', maxlength: 60, autocomplete: 'tel' }), x = el('textarea', { required: true, maxlength: 3000 }), hp = falle(), z = zustimmung(c), knopf = el('button', { class: 'mk-btn', type: 'submit', text: 'Nachricht senden' }), fo = fotoFeld(b);
    var f = el('form', { novalidate: false }, feld('Ihr Name *', n), feld('Ihre E-Mail-Adresse *', m), feld('Telefon (freiwillig)', t), feld('Ihre Nachricht *', x), fo.el, hp, z.el, knopf);
    f.addEventListener('submit', function (e) {
      e.preventDefault(); meldung(b, '', '');
      if (!fo.bereit()) { meldung(b, 'fehler', 'Bitte einen Moment warten, die Fotos werden noch hochgeladen.'); return; }
      knopf.disabled = true;
      anfrage('POST', 'kontakt', { name: n.value, email: m.value, telefon: t.value, nachricht: x.value, einwilligung: z.cb.checked, hp: hp.querySelector('input').value, seite: location.pathname, fotos: fo.tokens() })
        .then(function () { f.reset(); fo.zuruecksetzen(); meldung(b, 'ok', 'Vielen Dank! Ihre Nachricht ist angekommen, wir melden uns bei Ihnen.'); knopf.disabled = false; })
        .catch(function (er) { meldung(b, 'fehler', er.message); knopf.disabled = false; });
    });
    b.appendChild(f);
  }

  // ------------------------------------------------------------ Terminbuchung
  var WT = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  function tagText(iso) { var p = iso.split('-'), d = new Date(+p[0], +p[1] - 1, +p[2]); return WT[d.getDay()] + ', ' + p[2] + '.' + p[1] + '.'; }
  function termin(c) {
    var b = box(c); b.appendChild(el('p', { text: 'Termine werden geladen …' }));
    anfrage('GET', 'termine').then(function (t) {
      b.textContent = '';
      if (!t.aktiv || !t.tage.length) { b.appendChild(el('p', { text: t.aktiv ? 'Zurzeit sind keine freien Termine buchbar. Bitte schreiben Sie uns eine Nachricht.' : 'Die Online-Terminbuchung ist zurzeit nicht verfügbar.' })); return; }
      var tag = null, slot = null, tage = el('div', { class: 'mk-chips', role: 'group', 'aria-label': 'Tag wählen' }), zeiten = el('div', { class: 'mk-chips', role: 'group', 'aria-label': 'Uhrzeit wählen' }), form = el('div');
      b.appendChild(el('p', { class: 'mk-klein', text: 'Dauer: ' + t.dauer + ' Minuten' + (t.ort ? ' · ' + t.ort : '') }));
      b.appendChild(tage); b.appendChild(zeiten); b.appendChild(form);
      function markieren(g, aktiv) { Array.prototype.forEach.call(g.children, function (k) { k.setAttribute('aria-pressed', k === aktiv ? 'true' : 'false'); }); }
      t.tage.forEach(function (d) {
        var k = el('button', { type: 'button', class: 'mk-chip', 'aria-pressed': 'false', text: tagText(d.datum) });
        k.addEventListener('click', function () {
          tag = d; slot = null; markieren(tage, k); zeiten.textContent = ''; form.textContent = '';
          d.slots.forEach(function (s) {
            var z = el('button', { type: 'button', class: 'mk-chip', 'aria-pressed': 'false', text: s.uhr + ' Uhr' });
            z.addEventListener('click', function () { slot = s; markieren(zeiten, z); formular(); }); zeiten.appendChild(z);
          });
        });
        tage.appendChild(k);
      });
      function formular() {
        form.textContent = '';
        var n = el('input', { required: true, maxlength: 120, autocomplete: 'name' }), m = el('input', { type: 'email', required: true, maxlength: 200, autocomplete: 'email' }), tel = el('input', { type: 'tel', maxlength: 60, autocomplete: 'tel' }),
          x = el('textarea', { maxlength: 1500 }), hp = falle(), z = zustimmung(c), knopf = el('button', { class: 'mk-btn', type: 'submit', text: 'Termin verbindlich buchen' }), fo = fotoFeld(b);
        var f = el('form', {}, feld('Ihr Name *', n), feld('Ihre E-Mail-Adresse *', m), feld('Telefon (freiwillig)', tel), feld('Anliegen (freiwillig)', x), fo.el, hp, z.el, knopf);
        f.addEventListener('submit', function (e) {
          e.preventDefault(); meldung(b, '', '');
          if (!fo.bereit()) { meldung(b, 'fehler', 'Bitte einen Moment warten, die Fotos werden noch hochgeladen.'); return; }
          knopf.disabled = true;
          anfrage('POST', 'termin', { start: slot.start, name: n.value, email: m.value, telefon: tel.value, nachricht: x.value, einwilligung: z.cb.checked, hp: hp.querySelector('input').value, fotos: fo.tokens() })
            .then(function (r) { b.textContent = ''; b.appendChild(el('div', { class: 'mk-ok', role: 'status', text: 'Ihr Termin ist gebucht: ' + (r.wann || tagText(tag.datum) + ' ' + slot.uhr + ' Uhr') + '. Sie bekommen eine Bestätigung mit Kalender-Einladung per E-Mail.' })); })
            .catch(function (er) { meldung(b, 'fehler', er.message); knopf.disabled = false; if (er.status === 409) { setTimeout(function () { termin(c); }, 1800); } });
        });
        form.appendChild(f);
      }
    }).catch(function (er) { b.textContent = ''; b.appendChild(el('p', { text: er.message })); });
  }

  // ------------------------------------------------------------ Google-Bewertungen
  function sterne(n) { var v = Math.round(n || 0), s = ''; for (var i = 1; i <= 5; i++) s += i <= v ? '★' : '☆'; return s; }
  function bewertungen(c) {
    anfrage('GET', 'bewertungen').then(function (d) {
      var b = box(c); if (!d.aktiv) { c.textContent = ''; return; }
      if (d.sterne) {
        b.appendChild(el('div', { class: 'mk-sterne', 'aria-hidden': 'true', text: sterne(d.sterne) }));
        b.appendChild(el('p', { text: String(d.sterne).replace('.', ',') + ' von 5' + (d.anzahl ? ' · ' + d.anzahl + ' Bewertungen bei Google' : ' bei Google') }));
      }
      (d.bewertungen || []).forEach(function (r) {
        b.appendChild(el('div', { class: 'mk-bew' }, el('div', { class: 'mk-sterne', style: 'font-size:1.1em', 'aria-hidden': 'true', text: sterne(r.sterne) }), r.text ? el('p', { text: '„' + r.text + '“' }) : null, el('div', { class: 'mk-klein', text: r.autor + (r.wann ? ' · ' + r.wann : '') })));
      });
      if (d.quelle === 'google' && (d.bewertungen || []).length) b.appendChild(el('div', { class: 'mk-klein', text: 'Bewertungen von Google' }));
      if (d.schreiben && /^https:\/\//.test(d.schreiben)) b.appendChild(el('a', { class: 'mk-btn', style: 'display:inline-block;text-decoration:none', href: d.schreiben, target: '_blank', rel: 'noopener', text: 'Jetzt bei Google bewerten' }));
    }).catch(function () { c.textContent = ''; });
  }

  // ------------------------------------------------------------ PayPal
  var sdk = null;
  function paypalLaden(p) {
    if (!sdk) sdk = new Promise(function (ok, nein) {
      var s = el('script', { src: 'https://www.paypal.com/sdk/js?client-id=' + encodeURIComponent(p.client_id) + '&currency=' + encodeURIComponent(p.waehrung) + '&locale=de_DE' });
      s.onload = ok; s.onerror = nein; document.head.appendChild(s);
    });
    return sdk;
  }
  function paypal(c, p) {
    var b = box(c), betrag = (c.getAttribute('data-betrag') || '').trim(), titel = (c.getAttribute('data-titel') || 'Zahlung').slice(0, 120);
    var ok = /^\d{1,6}([.,]\d{1,2})?$/.test(betrag), zahl = ok ? betrag.replace(',', '.') : '';
    if (p.client_id && ok) {
      var ziel = el('div'); b.appendChild(ziel);
      paypalLaden(p).then(function () {
        window.paypal.Buttons({
          createOrder: function (d, a) { return a.order.create({ purchase_units: [{ description: titel, amount: { currency_code: p.waehrung, value: zahl } }] }); },
          onApprove: function (d, a) { return a.order.capture().then(function () { b.textContent = ''; b.appendChild(el('div', { class: 'mk-ok', role: 'status', text: 'Vielen Dank, Ihre Zahlung ist eingegangen.' })); }); },
          onError: function () { meldung(b, 'fehler', 'Die Zahlung konnte nicht abgeschlossen werden. Bitte versuchen Sie es erneut.'); }
        }).render(ziel);
      }).catch(function () { meldung(b, 'fehler', 'PayPal konnte nicht geladen werden.'); });
    } else if (p.me_link && /^https:\/\//.test(p.me_link)) {
      b.appendChild(el('a', { class: 'mk-btn', style: 'display:inline-block;text-decoration:none', href: p.me_link.replace(/\/$/, '') + (ok ? '/' + zahl + p.waehrung : ''), target: '_blank', rel: 'noopener', text: ok ? 'Mit PayPal zahlen (' + zahl.replace('.', ',') + ' ' + p.waehrung + ')' : 'Mit PayPal zahlen' }));
    } else c.textContent = '';
  }

  // ------------------------------------------------------------ Google Analytics (erst nach Einwilligung)
  var SCHLUESSEL = 'mk_statistik:' + site;
  function wahl() { try { return localStorage.getItem(SCHLUESSEL); } catch (e) { return null; } }
  function merke(w) { try { localStorage.setItem(SCHLUESSEL, w); } catch (e) { /* ohne Speicher: Abfrage kommt beim nächsten Besuch erneut */ } }
  function gaLaden(id) {
    if (window.__mkGa) return; window.__mkGa = true;
    window.dataLayer = window.dataLayer || []; window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date()); window.gtag('config', id, { anonymize_ip: true });
    document.head.appendChild(el('script', { async: true, src: 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id) }));
  }
  function banner(id, ds) {
    var b = el('div', { class: 'mk-box', role: 'dialog', 'aria-label': 'Statistik', style: 'position:fixed;left:12px;right:12px;bottom:12px;max-width:560px;margin:0 auto;z-index:2147483000;padding:14px 16px;border-radius:12px;background:#fff;color:#111;box-shadow:0 6px 28px rgba(0,0,0,.28)' });
    var ja = el('button', { class: 'mk-btn', type: 'button', style: 'margin-top:10px', text: 'Erlauben' }), nein = el('button', { class: 'mk-btn mk-leise', type: 'button', style: 'margin:10px 0 0 8px;color:#111', text: 'Ablehnen' });
    ja.addEventListener('click', function () { merke('ja'); b.remove(); gaLaden(id); });
    nein.addEventListener('click', function () { merke('nein'); b.remove(); });
    b.appendChild(el('div', {}, 'Wir möchten anonym zählen, wie viele Besucher unsere Website nutzen (Google Analytics). Dabei werden Daten an Google übertragen. Das geschieht nur mit Ihrer Zustimmung, Sie können sie jederzeit widerrufen. Mehr in der ', el('a', { href: ds, target: '_blank', rel: 'noopener', text: 'Datenschutzerklärung' }), '.'));
    b.appendChild(ja); b.appendChild(nein); document.body.appendChild(b);
  }
  function statistik(cfg) {
    var a = cfg.analytics; if (!a || !a.aktiv) return;
    // Hat die Seite eine eigene Einwilligungsabfrage samt eigenem Analytics (window.ELB.ga4) oder ist es mit data-eigene-einwilligung gekennzeichnet,
    // fragt der Baustein nicht ein zweites Mal (sonst liegen zwei Banner übereinander und Google Analytics würde doppelt geladen).
    if (skript.hasAttribute('data-eigene-einwilligung') || (window.ELB && window.ELB.ga4) || window.__mkGa) return;
    var ds = skript.getAttribute('data-datenschutz') || '/datenschutz', w = wahl();
    if (w === 'ja') gaLaden(a.id); else if (w !== 'nein') banner(a.id, ds);
    Array.prototype.forEach.call(document.querySelectorAll('[data-mk="cookies"]'), function (c) {
      var l = el('a', { href: '#', text: c.getAttribute('data-text') || 'Statistik-Einstellungen' });
      l.addEventListener('click', function (e) { e.preventDefault(); merke('offen'); try { localStorage.removeItem(SCHLUESSEL); } catch (x) { /* egal */ } if (!document.querySelector('[aria-label=Statistik]')) banner(a.id, ds); });
      c.textContent = ''; c.appendChild(l);
    });
  }

  // ------------------------------------------------------------ Preisliste (immer der aktuelle Stand aus dem Portal)
  function preise(c) {
    anfrage('GET', 'leistungen').then(function (d) {
      var l = d.leistungen || [];
      if (!l.length) { c.textContent = ''; return; }
      var b = box(c), ul = el('ul', { class: 'mk-preise' });
      l.forEach(function (x) {
        var li = el('li', { class: 'mk-preis' });
        li.appendChild(el('span', { class: 'mk-preis-name', text: x.name }));
        if (x.beschreibung) li.appendChild(el('span', { class: 'mk-preis-text', text: x.beschreibung }));
        if (x.dauer) li.appendChild(el('span', { class: 'mk-preis-dauer', text: 'ca. ' + x.dauer + ' Min.' }));
        if (x.preis) li.appendChild(el('span', { class: 'mk-preis-betrag', text: x.preis }));
        ul.appendChild(li);
      });
      b.appendChild(ul);
    }).catch(function () { c.textContent = ''; });
  }

  // ------------------------------------------------------------ Sicherheitsnetz für Einblend-Animationen
  // Manche Seiten verstecken Inhalte (.reveal) und blenden sie per IntersectionObserver beim Scrollen ein (.is-visible). Meldet der Beobachter
  // bei einzelnen Elementen nichts (z. B. weil der Browser abgeschnittene Elemente nicht als sichtbar zählt), bleiben ganze Bereiche weiß.
  // Dieses Netz blendet alles ein, was im oder knapp unter dem sichtbaren Bereich liegt, unabhängig vom Beobachter.
  (function () {
    var wartend = false;
    function pruefen() {
      wartend = false;
      if (!document.documentElement.classList.contains('js-anim')) return;
      var liste = document.querySelectorAll('.reveal:not(.is-visible)'), h = window.innerHeight || 800;
      Array.prototype.forEach.call(liste, function (e) {
        var r = e.getBoundingClientRect();
        if (r.bottom > -h && r.top < h * 0.98) e.classList.add('is-visible');
      });
    }
    function planen() { if (wartend) return; wartend = true; (window.requestAnimationFrame || window.setTimeout)(pruefen); }
    window.addEventListener('scroll', planen, { passive: true });
    window.addEventListener('resize', planen);
    window.addEventListener('load', function () { setTimeout(pruefen, 600); });
    setInterval(pruefen, 1500);
  })();

  // ------------------------------------------------------------ Start
  var slots = {};
  Array.prototype.forEach.call(document.querySelectorAll('[data-mk]'), function (c) { var a = c.getAttribute('data-mk'); (slots[a] = slots[a] || []).push(c); });
  anfrage('GET', 'config').then(function (cfg) {
    if (cfg.fotos) fotoEinst = cfg.fotos;
    statistik(cfg);
    (slots.kontakt || []).forEach(function (c) { if (cfg.kontakt) kontakt(c); else c.textContent = ''; });
    (slots.termin || []).forEach(function (c) { if (cfg.termin.aktiv) termin(c); else c.textContent = ''; });
    (slots.bewertungen || []).forEach(function (c) { if (cfg.bewertungen) bewertungen(c); else c.textContent = ''; });
    (slots.preise || []).forEach(function (c) { preise(c); });
    (slots.paypal || []).forEach(function (c) { if (cfg.paypal.aktiv) paypal(c, cfg.paypal); else c.textContent = ''; });
  }).catch(function () { /* Dienst nicht erreichbar: die Seite bleibt ohne die Bausteine nutzbar */ });
})();
