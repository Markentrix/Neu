import { api, melde } from './common.js';
const m = document.getElementById('m'), b = document.getElementById('b');
const t = new URLSearchParams(location.search).get('t');
if (!t) { b.disabled = true; melde(m, 'Dieser Link ist unvollständig. Bitte fordern Sie auf der Anmeldeseite einen neuen an.'); }
b.addEventListener('click', async () => {
  b.disabled = true; melde(m, '');
  try { const r = await api('/api/login-link/einloesen', { method: 'POST', body: { token: t }, leise: true }); location.href = r.ziel; }
  catch (e) { melde(m, e.message); }
});
