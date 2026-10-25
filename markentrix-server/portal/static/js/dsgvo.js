// Öffentliches Formular für Datenschutz-Anfragen (Art. 15 bis 21 DSGVO).
import { api, melde, el } from './common.js';
const f = /** @type {HTMLFormElement} */ (el('f')), m = el('m');
const v = (id) => /** @type {HTMLInputElement} */ (el(id)).value;
f.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b = /** @type {HTMLButtonElement} */ (el('b')); b.disabled = true; melde(m, '');
  try {
    await api('/api/public/datenschutz-anfrage', { method: 'POST', body: { art: v('a'), name: v('n'), email: v('e'), nachricht: v('x') || null, zweitfeld: v('z') || null } });
    f.hidden = true; melde(m, 'Vielen Dank. Ihre Anfrage ist eingegangen. Wir melden uns innerhalb eines Monats unter der angegebenen E-Mail-Adresse.', 'ok');
  } catch (z) { melde(m, z.message); b.disabled = false; }
});
