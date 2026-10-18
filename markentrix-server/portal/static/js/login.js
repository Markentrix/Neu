import { api, melde } from './common.js';
const f = document.getElementById('f'), m = document.getElementById('m'), b = document.getElementById('b');
api('/api/me', { leise: true }).then(u => { location.href = u.rolle === 'admin' ? '/admin' : '/app'; }).catch(() => {});
f.addEventListener('submit', async (ev) => {
  ev.preventDefault(); b.disabled = true; melde(m, '');
  try {
    const r = await api('/api/login', { method: 'POST', body: { email: document.getElementById('e').value, password: document.getElementById('p').value } });
    location.href = r.ziel;
  } catch (e) { melde(m, e.message); b.disabled = false; }
});
