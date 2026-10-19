import { api, melde, el } from './common.js';
const token = new URLSearchParams(location.search).get('token') || '';
const m = el('m'), b = el('b');
api('/api/einladung/' + encodeURIComponent(token)).then(d => { el('who').textContent = 'Konto: ' + d.email; })
  .catch(e => { melde(m, e.message); b.disabled = true; });
el('f').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const p = el('p').value;
  if (p !== el('p2').value) return melde(m, 'Die Passwörter sind nicht gleich.');
  b.disabled = true;
  try { await api('/api/einladung', { method: 'POST', body: { token, password: p } }); melde(m, 'Gespeichert. Du wirst weitergeleitet …', 'ok'); setTimeout(() => { location.href = '/'; }, 1200); }
  catch (e) { melde(m, e.message); b.disabled = false; }
});
