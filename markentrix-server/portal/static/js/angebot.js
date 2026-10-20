import { api, melde, h, el, euro, datum } from './common.js';
const token = new URLSearchParams(location.search).get('t') || '';
const m = el('m'), inhalt = el('inhalt'), titel = el('titel');

function positionen(d) {
  const zeile = (p) => h('tr', {}, h('td', {}, p.text), h('td', { class: 'tzahl nowrap' }, String(p.menge).replace('.', ',') + (p.einheit ? ' ' + p.einheit : '')), h('td', { class: 'tzahl nowrap' }, euro(p.preis_cent)), h('td', { class: 'tzahl nowrap' }, euro(Math.round(p.menge * p.preis_cent))));
  return h('div', { class: 'tablewrap' }, h('table', {},
    h('thead', {}, h('tr', {}, ['Leistung', 'Menge', 'Einzelpreis', 'Gesamt'].map(t => h('th', {}, t)))),
    h('tbody', {}, d.positionen.map(zeile),
      h('tr', {}, h('td', { colspan: 3 }, 'Zwischensumme (netto)'), h('td', { class: 'tzahl nowrap' }, euro(d.netto_cent))),
      d.kleinunternehmer ? '' : h('tr', {}, h('td', { colspan: 3 }, 'Umsatzsteuer ' + String(d.ust_satz).replace('.', ',') + ' %'), h('td', { class: 'tzahl nowrap' }, euro(d.ust_cent))),
      h('tr', {}, h('td', { colspan: 3 }, h('b', {}, 'Gesamtbetrag')), h('td', { class: 'tzahl nowrap' }, h('b', {}, euro(d.brutto_cent)))))));
}

function zeigen(d) {
  titel.textContent = 'Angebot ' + d.nummer;
  const teile = [h('p', { class: 'muted small', style: 'text-align:center;margin-top:-6px' }, 'von ' + d.anbieter + ' für ' + d.empfaenger)];
  if (d.betreff) teile.push(h('h2', {}, d.betreff));
  if (d.einleitung) teile.push(h('p', { style: 'white-space:pre-line' }, d.einleitung));
  teile.push(positionen(d));
  if (d.schluss) teile.push(h('p', { style: 'white-space:pre-line;margin-top:14px' }, d.schluss));
  teile.push(h('p', { class: 'small muted' }, 'Gültig bis ' + datum(d.gueltig_bis) + '. ', h('a', { href: '/api/angebot/' + encodeURIComponent(token) + '/pdf', target: '_blank', rel: 'noopener' }, 'Als PDF öffnen')));
  if (d.status === 'angenommen') {
    teile.push(h('div', { class: 'msg ok' }, 'Dieses Angebot wurde am ' + datum(d.angenommen_am) + ' angenommen. Vielen Dank! Wir melden uns bei Ihnen zum nächsten Schritt.'));
  } else if (d.status === 'abgelehnt') {
    teile.push(h('div', { class: 'msg info' }, 'Dieses Angebot wurde abgelehnt. Falls sich etwas ändert, melden Sie sich gern bei uns.'));
  } else if (d.abgelaufen) {
    teile.push(h('div', { class: 'msg info' }, 'Dieses Angebot ist abgelaufen. Schreiben Sie uns kurz, dann senden wir Ihnen gern ein neues.' + (d.kontakt.email ? ' ' + d.kontakt.email : '')));
  } else {
    const name = h('input', { id: 'name', required: true, minlength: 2, maxlength: 120, autocomplete: 'name', placeholder: 'Ihr Name' });
    const ok = h('input', { type: 'checkbox', id: 'ok', style: 'width:auto;margin-top:3px' });
    const ja = h('button', { class: 'btn', style: 'width:100%', type: 'submit' }, 'Angebot verbindlich annehmen');
    const form = h('form', { onsubmit: async (e) => {
      e.preventDefault(); ja.disabled = true; melde(m, '');
      try { await api('/api/angebot/' + encodeURIComponent(token) + '/annehmen', { method: 'POST', body: { name: name.value, bestaetigt: ok.checked } }); await laden(); }
      catch (x) { melde(m, x.message); ja.disabled = false; }
    } },
      h('label', { for: 'name' }, 'Zur Annahme geben Sie bitte Ihren Namen ein'), name,
      h('label', { style: 'display:flex;gap:8px;align-items:flex-start;color:inherit;font-size:13px;margin:10px 0', for: 'ok' }, ok, h('span', {}, 'Ich nehme das Angebot ' + d.nummer + ' im Namen von ' + d.empfaenger + ' verbindlich an.')),
      h('p', {}, ja));
    const nein = h('details', { class: 'small', style: 'margin-top:10px' }, h('summary', {}, 'Kein Interesse oder Rückfragen?'),
      h('p', {}, 'Rückfragen beantworten wir gern' + (d.kontakt.email ? ' unter ' + d.kontakt.email : '') + (d.kontakt.telefon ? ' oder ' + d.kontakt.telefon : '') + '.'),
      h('button', { class: 'btn sec small', type: 'button', onclick: async () => { if (!confirm('Angebot ablehnen?')) return; try { await api('/api/angebot/' + encodeURIComponent(token) + '/ablehnen', { method: 'POST', body: { grund: '' } }); await laden(); } catch (x) { melde(m, x.message); } } }, 'Angebot ablehnen'));
    teile.push(form, nein);
  }
  inhalt.replaceChildren(...teile);
}

async function laden() {
  try { zeigen(await api('/api/angebot/' + encodeURIComponent(token), { leise: true })); }
  catch (x) { titel.textContent = 'Angebot'; inhalt.replaceChildren(); melde(m, x.message); }
}
laden();
