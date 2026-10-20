import { h, api } from '../common.js';
import { V, kopf } from './kern.js';

V.onboarding = async () => {
  const d = await api('/api/admin/onboarding/board');
  const gesamt = d.spalten.reduce((a, s) => a + s.kunden.length, 0);
  const karte = (k) => h('div', { class: 'kkarte', style: 'cursor:default' }, h('a', { href: '#kunde/' + k.id }, k.firma),
    h('div', { class: 'small muted' }, k.kundennummer + ' · seit ' + k.tage + (k.tage === 1 ? ' Tag' : ' Tagen')),
    h('div', { class: 'fortschritt', role: 'progressbar', 'aria-valuenow': String(k.fertig), 'aria-valuemax': String(k.gesamt), 'aria-label': 'Fortschritt ' + k.firma }, h('div', { style: 'width:' + Math.round(100 * k.fertig / Math.max(1, k.gesamt)) + '%' })),
    h('div', { class: 'small' }, k.fertig + ' von ' + k.gesamt + (k.naechster ? ' · als Nächstes: ' + k.naechster : '')),
    k.haengt ? h('span', { class: 'pill warn' }, 'hängt am Start') : '');
  return h('div', { class: 'stack' }, kopf('Onboarding'),
    h('div', { class: 'card' }, h('p', { class: 'small muted' }, gesamt ? gesamt + (gesamt === 1 ? ' Kunde' : ' Kunden') + ' im Onboarding. Die Phase ergibt sich automatisch aus der Checkliste im Kunden (erste Phase mit einem offenen Punkt), Karten werden deshalb nicht von Hand verschoben.' : 'Keine Kunden im Onboarding.')),
    h('div', { class: 'kanban' }, d.spalten.filter(s => s.schluessel !== 'fertig' || s.kunden.length).map(s => h('div', { class: 'kspalte', role: 'group', 'aria-label': s.titel }, h('h2', {}, s.titel, h('span', { class: 'badge' }, s.kunden.length)),
      s.kunden.length ? s.kunden.map(karte) : h('p', { class: 'small muted' }, 'Leer')))));
};
