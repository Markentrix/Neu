import { api, melde } from './common.js';
const f = document.getElementById('f'), m = document.getElementById('m'), b = document.getElementById('b');
api('/api/me', { leise: true }).then(u => { location.href = u.rolle === 'admin' ? '/admin' : '/app'; }).catch(() => {});
f.addEventListener('submit', async (ev) => {
  ev.preventDefault(); b.disabled = true; melde(m, '');
  try {
    const cw = document.getElementById('cw');
    const r = await api('/api/login', { method: 'POST', body: { email: document.getElementById('e').value, password: document.getElementById('p').value, code: cw.hidden ? null : document.getElementById('c').value } });
    if (r.zwei_faktor) { cw.hidden = false; document.getElementById('c').focus(); melde(m, 'Bitte den Code aus deiner Authenticator-App eingeben.', 'info'); b.disabled = false; return; }
    location.href = r.ziel;
  } catch (e) { melde(m, e.message); b.disabled = false; }
});

const f2 = document.getElementById('f2'), m2 = document.getElementById('m2');
document.getElementById('v').addEventListener('click', (e) => { e.preventDefault(); f.hidden = true; f2.hidden = false; });
document.getElementById('z').addEventListener('click', (e) => { e.preventDefault(); f2.hidden = true; f.hidden = false; });
f2.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b2 = document.getElementById('b2'); b2.disabled = true; melde(m2, '');
  try { const r = await api('/api/passwort-vergessen', { method: 'POST', body: { email: document.getElementById('e2').value } }); melde(m2, r.hinweis, 'ok'); }
  catch (e) { melde(m2, e.message); }
  b2.disabled = false;
});

const f3 = document.getElementById('f3'), m3 = document.getElementById('m3');
document.getElementById('l').addEventListener('click', (e) => { e.preventDefault(); f.hidden = true; f3.hidden = false; });
document.getElementById('z3').addEventListener('click', (e) => { e.preventDefault(); f3.hidden = true; f.hidden = false; });
f3.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b3 = document.getElementById('b3'); b3.disabled = true; melde(m3, '');
  try { const r = await api('/api/login-link', { method: 'POST', body: { email: document.getElementById('e3').value } }); melde(m3, r.hinweis, 'ok'); }
  catch (e) { melde(m3, e.message); }
  b3.disabled = false;
});
