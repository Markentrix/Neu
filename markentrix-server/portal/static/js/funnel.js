// Öffentliche Anmeldeseite einer Lead-Kampagne (/f/<name>), ohne Cookies. Gibt UTM-Angaben und den Empfehlungscode an das Portal weiter.
import { api, melde, h, el } from './common.js';
import { messungFragen, leadMelden } from './messung.js';
const slug = decodeURIComponent(location.pathname.split('/')[2] || '');
const q = new URLSearchParams(location.search);
const m = el('m'), f = /** @type {HTMLFormElement} */ (el('f'));
const input = (id) => /** @type {HTMLInputElement} */ (el(id));
let kamp = null;
async function laden() {
  try {
    kamp = await api('/api/public/funnel/' + encodeURIComponent(slug), { leise: true });
  } catch (e) {
    el('titel').textContent = 'Diese Seite ist nicht erreichbar';
    melde(m, 'Die Seite gibt es nicht oder sie ist gerade nicht freigeschaltet.', 'info'); return;
  }
  document.title = kamp.titel || kamp.name;
  el('titel').textContent = kamp.titel || kamp.name;
  el('untertitel').textContent = kamp.untertitel || '';
  el('nutzen').replaceChildren(...kamp.nutzen.map(n => h('li', {}, n)));
  el('ew').textContent = kamp.einwilligung_text;
  el('b').textContent = kamp.button;
  input('t').required = !!kamp.telefon_pflicht;
  el('tl').textContent = kamp.telefon_pflicht ? 'Telefon' : 'Telefon (optional)';
  el('webBox').hidden = !kamp.website_abfragen;
  f.hidden = false;
  if (kamp.tracking) messungFragen(kamp.tracking);
}
f.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b = /** @type {HTMLButtonElement} */ (el('b')); b.disabled = true; melde(m, '');
  /** @type {Record<string,string>} */ const utm = {};
  for (const [k, v] of q.entries()) if (/^(utm_[a-z]+|gclid|fbclid)$/.test(k)) utm[k] = v;
  try {
    const r = await api('/api/public/funnel/' + encodeURIComponent(slug), { method: 'POST', body: {
      name: input('n').value, firma: input('fi').value || null, email: input('e').value, telefon: input('t').value || null,
      website: kamp.website_abfragen ? (input('w').value || null) : null, einwilligung: input('c').checked, ref: q.get('ref'), utm, zweitfeld: input('z').value || null } });
    f.hidden = true; el('untertitel').hidden = true; el('nutzen').hidden = true;
    el('titel').textContent = kamp.danke_titel; el('dt').hidden = true; el('dx').textContent = kamp.danke_text;
    leadMelden(kamp.tracking);
    el('tp').hidden = !r.termin; el('danke').hidden = false;
  } catch (z) { melde(m, z.message); b.disabled = false; }
});
laden();
