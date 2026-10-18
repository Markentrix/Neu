import { api, melde } from './common.js';
const token = new URLSearchParams(location.search).get('token') || '';
const m = document.getElementById('m'), b = document.getElementById('b');
api('/api/einladung/' + encodeURIComponent(token)).then(d => { document.getElementById('who').textContent = 'Konto: ' + d.email; })
  .catch(e => { melde(m, e.message); b.disabled = true; });
document.getElementById('f').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const p = document.getElementById('p').value;
  if (p !== document.getElementById('p2').value) return melde(m, 'Die Passwörter sind nicht gleich.');
  b.disabled = true;
  try { await api('/api/einladung', { method: 'POST', body: { token, password: p } }); melde(m, 'Gespeichert. Du wirst weitergeleitet …', 'ok'); setTimeout(() => { location.href = '/'; }, 1200); }
  catch (e) { melde(m, e.message); b.disabled = false; }
});
