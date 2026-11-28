import { h, api } from '../common.js';

/** Kurzer Check, ob die Stammdaten des Kunden gepflegt sind. Nur Hinweise, bearbeitet wird unter „Stammdaten“. */
export async function stammdatenKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/stammdaten-check');
  const fehlt = d.punkte.filter(p => !p.ok);
  const farbe = !fehlt.length ? 'ok' : fehlt.some(p => ['email', 'email_funktioniert'].includes(p.feld)) ? 'bad' : 'warn';
  return h('div', { class: 'card' }, h('div', { class: 'row', style: 'align-items:center;gap:8px' }, h('h2', { class: 'grow', style: 'margin:0' }, 'Stammdaten-Check'),
    h('span', { class: 'pill ' + farbe }, d.ok + ' von ' + d.gesamt + ' gepflegt')),
  fehlt.length ? h('ul', { class: 'small', style: 'margin:8px 0 0 18px' }, fehlt.map(p => h('li', {}, p.text))) : h('p', { class: 'small muted' }, 'Alle wichtigen Angaben sind vorhanden.'));
}
