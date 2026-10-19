import { api, melde, h } from './common.js';
const m = document.getElementById('m'), tage = document.getElementById('tage'), f = document.getElementById('f');
let gewaehlt = null;
const tagText = (d) => new Date(d + 'T12:00:00').toLocaleDateString('de-DE', { weekday: 'long', day: '2-digit', month: 'long' });
async function laden() {
  tage.replaceChildren();
  try {
    const d = await api('/api/public/buchung/slots', { leise: true });
    if (!d.aktiv) { melde(m, 'Die Online-Buchung ist gerade nicht verfügbar. Bitte schreiben Sie uns über das Kontaktformular.', 'info'); return; }
    if (!d.tage.length) { melde(m, 'Im Moment sind keine freien Termine da. Bitte schreiben Sie uns über das Kontaktformular.', 'info'); return; }
    document.getElementById('info').textContent = `Erstgespräch, ca. ${d.dauer} Minuten. ${d.ort}`;
    for (const t of d.tage) {
      tage.append(h('p', { style: 'margin:14px 0 6px;font-weight:600' }, tagText(t.datum)),
        h('div', { class: 'row', style: 'flex-wrap:wrap;gap:6px' }, ...t.slots.map(s => h('button', { class: 'btn sec small', type: 'button', onclick: () => {
          gewaehlt = s.start; document.getElementById('wahl').textContent = tagText(t.datum) + ', ' + s.uhr + ' Uhr'; f.hidden = false; f.scrollIntoView({ behavior: 'smooth' }); } }, s.uhr))));
    }
  } catch (e) { melde(m, e.message); }
}
f.addEventListener('submit', async (ev) => {
  ev.preventDefault(); const b = document.getElementById('b'); b.disabled = true; melde(m, '');
  try {
    const r = await api('/api/public/buchung', { method: 'POST', body: { start: gewaehlt, name: n.value, email: e.value, telefon: t.value || null, nachricht: x.value || null, einwilligung: c.checked } });
    f.hidden = true; tage.replaceChildren(); melde(m, `Vielen Dank! Ihr Termin am ${r.wann} ist gebucht. Eine Bestätigung mit Kalendereinladung ist unterwegs zu Ihnen.`, 'ok');
  } catch (z) { melde(m, z.message); b.disabled = false; if (/nicht mehr frei/.test(z.message)) { f.hidden = true; laden(); } }
});
laden();
