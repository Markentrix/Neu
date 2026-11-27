import { api, melde, h, el } from './common.js';
const m = el('m'), liste = el('liste');
const p = new URLSearchParams(location.search);
const t = p.get('t') || '';
let vorauswahl = p.get('s');
const wann = (iso) => new Date(iso).toLocaleString('de-DE', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Berlin' }) + ' Uhr';
const gleich = (a, b) => !!a && !!b && Math.abs(new Date(a).getTime() - new Date(b).getTime()) < 1000;
async function bestaetigen(start) {
  melde(m, '');
  liste.querySelectorAll('button').forEach(b => { b.disabled = true; });
  try {
    const r = await api('/api/public/terminvorschlag', { method: 'POST', body: { t, start } });
    liste.replaceChildren();
    melde(m, `Vielen Dank! Ihr Beratungsgespräch am ${r.wann} ist vereinbart. Eine Bestätigung mit Kalendereinladung ist unterwegs zu Ihnen.`, 'ok');
  } catch (e) { melde(m, e.message); laden(); }
}
async function laden() {
  liste.replaceChildren();
  let d;
  try { d = await api('/api/public/terminvorschlag?t=' + encodeURIComponent(t), { leise: true }); } catch (e) { melde(m, e.message); return; }
  el('info').textContent = `Beratungsgespräch, ca. ${d.dauer} Minuten. ${d.ort || ''}`;
  if (d.status === 'gewaehlt') { melde(m, `Ihr Termin steht: ${wann(d.termin.start)}. Die Bestätigung haben Sie per E-Mail erhalten.`, 'ok'); return; }
  if (d.status !== 'offen') { melde(m, 'Diese Terminvorschläge sind nicht mehr aktuell. Bitte antworten Sie auf unsere E-Mail, wir finden gern einen neuen Termin.', 'info'); return; }
  if (!d.termine.length) { melde(m, 'Leider ist keiner der vorgeschlagenen Termine mehr frei. Bitte antworten Sie auf unsere E-Mail, wir schlagen Ihnen neue vor.', 'info'); return; }
  if (d.nachricht) liste.append(h('p', { style: 'white-space:pre-wrap' }, d.nachricht));
  const gew = vorauswahl && d.termine.find(x => gleich(x, vorauswahl));
  if (gew) {
    liste.append(h('p', {}, 'Sie haben diesen Termin gewählt:'), h('p', { style: 'font-weight:600;font-size:18px' }, wann(gew)),
      h('p', {}, h('button', { class: 'btn', style: 'width:100%', onclick: () => bestaetigen(gew) }, 'Termin verbindlich bestätigen')));
    if (d.termine.length > 1) liste.append(h('p', { class: 'muted small' }, h('a', { href: '#', onclick: (ev) => { ev.preventDefault(); vorauswahl = null; laden(); } }, 'Lieber einen anderen Termin wählen')));
    return;
  }
  liste.append(h('p', {}, 'Bitte wählen Sie einen Termin:'),
    ...d.termine.map(x => h('p', {}, h('button', { class: 'btn sec', style: 'width:100%', onclick: () => { vorauswahl = x; laden(); } }, wann(x)))));
}
laden();
