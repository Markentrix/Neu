import { h, api, zeit } from './common.js';

const ART = { erinnerung: 'Erinnerung', mahnung: 'Mahnung', rechnung: 'Rechnung', angebot: 'Angebot', termin: 'Termin', zugang: 'Zugang', bericht: 'Bericht', vertrag: 'Vertrag', website: 'Website', freigabe: 'Freigabe', anfrage: 'Anfrage', ticket: 'Ticket', system: 'Sonstiges' };

/** Karte „Gesendete E-Mails“: Anzahl, Aufteilung nach Art (z. B. wie oft erinnert wurde) und die letzten Mails mit Zustellstatus. `url` liefert { mails, arten, gesamt, fehler }. */
export async function mailKarte(url) {
  const d = await api(url).catch(() => null);
  if (!d) return '';
  const erinnerungen = d.arten.filter(a => ['erinnerung', 'mahnung'].includes(a.art)).reduce((s, a) => s + a.n, 0);
  const kopf = h('div', { class: 'row', style: 'align-items:center;gap:8px;flex-wrap:wrap' }, h('h2', { class: 'grow', style: 'margin:0' }, 'Gesendete E-Mails (' + d.gesamt + ')'),
    erinnerungen ? h('span', { class: 'pill warn' }, erinnerungen + ' Erinnerung' + (erinnerungen === 1 ? '' : 'en') + '/Mahnung' + (erinnerungen === 1 ? '' : 'en')) : '',
    d.fehler ? h('span', { class: 'pill bad' }, d.fehler + ' nicht zugestellt') : '');
  if (!d.gesamt) return h('div', { class: 'card' }, kopf, h('p', { class: 'small muted' }, 'Bisher wurde keine E-Mail über das Portal verschickt.'));
  const zusammen = h('p', { class: 'small muted' }, d.arten.map(a => (ART[a.art] || a.art) + ' ' + a.n + (a.fehler ? ' (' + a.fehler + ' fehlgeschlagen)' : '')).join(' · ') + ' · zuletzt ' + zeit(d.mails[0].zeit));
  const tab = h('table', {}, h('thead', {}, h('tr', {}, ['Datum', 'Art', 'Betreff', 'Status'].map(t => h('th', {}, t)))),
    h('tbody', {}, d.mails.map(x => h('tr', {}, h('td', {}, zeit(x.zeit)), h('td', {}, ART[x.art] || x.art), h('td', {}, x.betreff || '', h('div', { class: 'small muted' }, x.an || '')),
      h('td', {}, x.ok ? h('span', { class: 'pill ok' }, 'gesendet') : h('span', { class: 'pill bad', title: x.fehler || '' }, 'fehlgeschlagen'))))));
  return h('div', { class: 'card' }, kopf, zusammen, h('details', {}, h('summary', {}, 'Alle anzeigen'), h('div', { class: 'tablewrap' }, tab)));
}
