/* Buchungs-Baustein für die Website: <div data-mk-erstgespraech></div> + <script src="https://portal.…/static/js/erstgespraech.js" defer></script>
   Zeigt die freien Termine aus dem Portal-Kalender und bucht das kostenlose Erstgespräch. Läuft in einem Shadow-DOM, damit die Seite nichts verstellt. */
(function () {
  var skript = /** @type {HTMLScriptElement | null} */ (document.currentScript);
  var basis = skript && skript.src ? new URL(skript.src).origin : '';
  var CSS = ':host{display:block;font:16px/1.5 "Source Sans 3",system-ui,sans-serif;color:#0C2128}*{box-sizing:border-box}' +
    '.k{background:#fff;border:1px solid #EAE2D3;border-radius:8px;padding:20px;max-width:640px}' +
    'h3{font:800 22px/1.25 Archivo,"Source Sans 3",system-ui,sans-serif;letter-spacing:-.02em;margin:0 0 4px}p{margin:0 0 12px}.m{color:#4E5C5F;font-size:14px}' +
    '.tage{display:flex;gap:8px;overflow-x:auto;padding:4px 0 10px}' +
    '.t,.z{font:inherit;cursor:pointer;border-radius:4px;border:1px solid #8a9496;background:#fff;color:#0C2128;padding:8px 12px;min-height:44px}' +
    '.t{min-width:84px;text-align:center}.t b{display:block;font-size:13px;font-weight:600}.t[aria-pressed=true],.z[aria-pressed=true]{background:#045268;color:#fff;border-color:#045268}' +
    '.zeiten{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 14px}' +
    'label{display:block;font-size:14px;font-weight:600;margin:10px 0 4px}input,textarea{font:inherit;width:100%;padding:10px 12px;border:1px solid #8a9496;border-radius:4px;background:#fff;color:inherit}' +
    '.ck{display:flex;gap:10px;align-items:flex-start;font-weight:400;font-size:13px;color:#4E5C5F}.ck input{width:auto;margin-top:3px}' +
    '.go{font:700 16px "Source Sans 3",system-ui,sans-serif;width:100%;margin-top:14px;padding:13px 18px;border:0;border-radius:4px;color:#fff;cursor:pointer;background:#045268}.go:disabled{opacity:.6;cursor:default}' +
    '.f{color:#B3261E;font-size:14px;margin:10px 0 0}.ok{background:#E1F0F6;border:1px solid #62B2D0;border-radius:8px;padding:14px}a{color:#045268}' +
    ':focus-visible{outline:2px solid #964F08;outline-offset:2px}';
  function h(tag, attr) {
    var e = document.createElement(tag), k;
    for (k in (attr || {})) { if (k === 'onclick') e.onclick = attr[k]; else e.setAttribute(k, attr[k]); }
    for (var i = 2; i < arguments.length; i++) { var c = arguments[i]; if (c != null) e.append(c); }
    return e;
  }
  function tagText(d, kurz) { return new Date(d + 'T12:00:00').toLocaleDateString('de-DE', kurz ? { weekday: 'short', day: '2-digit', month: '2-digit' } : { weekday: 'long', day: '2-digit', month: 'long' }); }
  async function api(pfad, opt) {
    var r = await fetch(basis + pfad, Object.assign({ headers: { 'Content-Type': 'application/json', 'X-MK': '1' } }, opt || {}));
    var d = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Das hat leider nicht geklappt. Bitte versuchen Sie es noch einmal.');
    return d;
  }
  function start(wirt) {
    var wurzel = wirt.attachShadow({ mode: 'open' }), box = h('div', { class: 'k' }), gewaehlt = null, tagWahl = null;
    wurzel.append(h('style', {}, CSS), box);
    var datenschutz = wirt.getAttribute('data-datenschutz') || '/datenschutz.html';
    var fall = wirt.getAttribute('data-alternative') || 'Bitte schreiben Sie uns über das Kontaktformular.';
    box.append(h('p', { class: 'm', role: 'status' }, 'Termine werden geladen …'));
    function leer(text) { box.replaceChildren(h('h3', {}, 'Kostenloses Erstgespräch'), h('p', {}, text)); }
    api('/api/public/buchung/slots').then(function (d) {
      if (!d.aktiv || !d.tage.length) return leer((d.aktiv ? 'Im Moment sind keine freien Termine da. ' : 'Die Online-Buchung ist gerade nicht verfügbar. ') + fall);
      zeichne(d);
    }).catch(function () { leer('Die Terminübersicht ist gerade nicht erreichbar. ' + fall); });

    function zeichne(d) {
      var tage = h('div', { class: 'tage', role: 'group', 'aria-label': 'Tag wählen' }), zeiten = h('div', { class: 'zeiten', role: 'group', 'aria-label': 'Uhrzeit wählen' });
      var form = h('form', { hidden: '' }), fehler = h('p', { class: 'f', role: 'alert' }), wahl = h('p', {}, '');
      var n = h('input', { id: 'n', required: '', minlength: '2', maxlength: '120', autocomplete: 'name' }), e = h('input', { id: 'e', type: 'email', required: '', autocomplete: 'email' });
      var t = h('input', { id: 't', autocomplete: 'tel' }), x = h('textarea', { id: 'x', rows: '3', maxlength: '1500' });
      var c = h('input', { id: 'c', type: 'checkbox', required: '' });
      var knopf = h('button', { class: 'go', type: 'submit' }, 'Termin verbindlich buchen');
      form.append(wahl, h('label', { for: 'n' }, 'Name'), n, h('label', { for: 'e' }, 'E-Mail'), e, h('label', { for: 't' }, 'Telefon (optional)'), t,
        h('label', { for: 'x' }, 'Worum geht es? (optional)'), x,
        h('label', { class: 'ck', for: 'c' }, c, h('span', {}, 'Ich bin einverstanden, dass Markentrix meine Angaben zur Terminvereinbarung verarbeitet. ', h('a', { href: datenschutz, target: '_blank', rel: 'noopener' }, 'Datenschutzerklärung'), '.')),
        fehler, knopf);
      d.tage.forEach(function (tg) {
        var b = h('button', { class: 't', type: 'button', 'aria-pressed': 'false', onclick: function () {
          tage.querySelectorAll('.t').forEach(function (z) { z.setAttribute('aria-pressed', 'false'); }); b.setAttribute('aria-pressed', 'true');
          tagWahl = tg; gewaehlt = null; form.hidden = true; zeiten.replaceChildren();
          tg.slots.forEach(function (s) {
            var zb = h('button', { class: 'z', type: 'button', 'aria-pressed': 'false', onclick: function () {
              zeiten.querySelectorAll('.z').forEach(function (z) { z.setAttribute('aria-pressed', 'false'); }); zb.setAttribute('aria-pressed', 'true');
              gewaehlt = s.start; wahl.replaceChildren(h('b', {}, tagText(tg.datum) + ', ' + s.uhr + ' Uhr')); form.hidden = false;
            } }, s.uhr + ' Uhr');
            zeiten.append(zb);
          });
        } }, h('b', {}, tagText(tg.datum, true).split(',')[0]), tagText(tg.datum, true).split(', ')[1] || '');
        tage.append(b);
      });
      form.addEventListener('submit', function (ev) {
        ev.preventDefault(); if (!gewaehlt) return; knopf.disabled = true; fehler.textContent = '';
        api('/api/public/buchung', { method: 'POST', body: JSON.stringify({ start: gewaehlt, name: n.value, email: e.value, telefon: t.value || null, nachricht: x.value || null, einwilligung: c.checked }) })
          .then(function (r) {
            // Ereignis für Messung (z. B. GA4 generate_lead): ohne persönliche Daten, steigt bis zum document auf
            wirt.dispatchEvent(new CustomEvent('mk-erstgespraech-gebucht', { bubbles: true, composed: true, detail: { wann: r.wann } }));
            box.replaceChildren(h('h3', {}, 'Vielen Dank!'), h('p', { class: 'ok', role: 'status' }, 'Ihr Termin am ' + r.wann + ' ist gebucht. Eine Bestätigung mit Kalendereinladung ist unterwegs zu Ihnen.'));
          }).catch(function (z) {
            fehler.textContent = z.message; knopf.disabled = false;
            if (/nicht mehr frei/.test(z.message)) { form.hidden = true; gewaehlt = null; }
          });
      });
      box.replaceChildren(h('h3', {}, 'Kostenloses Erstgespräch'), h('p', { class: 'm' }, 'Ca. ' + d.dauer + ' Minuten. ' + d.ort), h('p', { class: 'm' }, 'Wählen Sie einen Tag und eine Uhrzeit:'), tage, zeiten, form);
    }
  }
  document.querySelectorAll('[data-mk-erstgespraech]').forEach(function (w) { if (!w.shadowRoot) start(w); });
}());
