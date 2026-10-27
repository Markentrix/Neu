import { api, melde, el, passkeyGeht, passkeyAnmelden, zielFuerRolle } from './common.js';
const f = el('f'), m = el('m'), b = el('b');
api('/api/me', { leise: true }).then(u => { location.href = zielFuerRolle(u.rolle); }).catch(() => {});
f.addEventListener('submit', async (ev) => {
  ev.preventDefault(); b.disabled = true; melde(m, '');
  try {
    const cw = el('cw');
    const r = await api('/api/login', { method: 'POST', body: { email: el('e').value, password: el('p').value, code: cw.hidden ? null : el('c').value, bleiben: el('bl').checked } });
    if (r.zwei_faktor) { cw.hidden = false; el('c').focus(); melde(m, 'Bitte den Code aus deiner Authenticator-App eingeben.', 'info'); b.disabled = false; return; }
    location.href = r.ziel;
  } catch (e) { melde(m, e.message); b.disabled = false; }
});

const f2 = el('f2'), m2 = el('m2');
el('v').addEventListener('click', (e) => { e.preventDefault(); f.hidden = true; f2.hidden = false; });
el('z').addEventListener('click', (e) => { e.preventDefault(); f2.hidden = true; f.hidden = false; });
f2.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b2 = el('b2'); b2.disabled = true; melde(m2, '');
  try { const r = await api('/api/passwort-vergessen', { method: 'POST', body: { email: el('e2').value } }); melde(m2, r.hinweis, 'ok'); }
  catch (e) { melde(m2, e.message); }
  b2.disabled = false;
});

const f3 = el('f3'), m3 = el('m3');
el('l').addEventListener('click', (e) => { e.preventDefault(); f.hidden = true; f3.hidden = false; });
el('z3').addEventListener('click', (e) => { e.preventDefault(); f3.hidden = true; f.hidden = false; });
f3.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b3 = el('b3'); b3.disabled = true; melde(m3, '');
  try { const r = await api('/api/login-link', { method: 'POST', body: { email: el('e3').value } }); melde(m3, r.hinweis, 'ok'); }
  catch (e) { melde(m3, e.message); }
  b3.disabled = false;
});

// „Angemeldet bleiben“ nur, wenn der Admin es erlaubt hat (Einstellungen → Sicherheit)
api('/api/public/login-optionen', { leise: true }).then(o => { el('bw').hidden = !o.bleiben; }).catch(() => {});

// Anmeldung ohne Passwort (Passkey); am Handy steht sie ganz oben
if (passkeyGeht()) {
  el('pkw').hidden = false;
  if (matchMedia('(pointer: coarse)').matches) { const erst = f.querySelector('label[for=e]'); if (erst) f.insertBefore(el('pkw'), erst); }
  el('pk').addEventListener('click', async () => {
    el('pk').disabled = true; melde(m, '');
    try { location.href = await passkeyAnmelden(el('bl').checked); } catch (e) { melde(m, e.message); el('pk').disabled = false; }
  });
}
