import { h, api, datum, euro } from '../common.js';
import { BELEG_ST } from './belege.js';
import { tabelle } from './kern.js';

/** Alle Rechnungen eines Jahres: Umsatz je Monat, Liste, Export für die Steuerberatung (ZIP mit PDFs und Rechnungsliste). */
export async function rechnungenJahrKarte() {
  const huelle = h('div', { class: 'card' });
  const zeige = async (jahr, monat = 0) => {
    const d = await api('/api/admin/rechnungen-jahr' + (jahr ? '?jahr=' + jahr : ''));
    const s = d.summe;
    const kachel = (t, w, sub) => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, t), h('b', {}, w), sub ? h('span', { class: 'small muted' }, sub) : '');
    const jahrWahl = h('select', { 'aria-label': 'Jahr', onchange: () => zeige(Number(jahrWahl.value), 0) }, d.jahre.map(j => h('option', { value: j, selected: j === d.jahr }, j)));
    const monatWahl = h('select', { 'aria-label': 'Monat für den Export' }, h('option', { value: 0 }, 'ganzes Jahr'), d.monate.map(m => h('option', { value: m.monat, selected: m.monat === monat }, m.name)));
    const zip = h('a', { class: 'btn', href: '#', target: '_blank', rel: 'noopener' }, 'Export für Steuerberater (ZIP)');
    const link = () => { zip.href = '/api/admin/belege-export.zip?jahr=' + d.jahr + (Number(monatWahl.value) ? '&monat=' + monatWahl.value : ''); };
    monatWahl.onchange = link; link();
    const mit = d.monate.filter(m => m.anzahl);
    huelle.replaceChildren(
      h('h2', {}, 'Rechnungen nach Jahr'),
      h('div', { class: 'row', style: 'align-items:center;gap:8px;flex-wrap:wrap' }, h('label', { class: 'small' }, 'Jahr '), jahrWahl, h('label', { class: 'small' }, ' Export für '), monatWahl, zip),
      h('p', { class: 'small muted' }, 'Das ZIP enthält den Ordner „Rechnungen ' + d.jahr + '“ mit allen Rechnungen als PDF (mit eingebetteter E-Rechnung) und eine Rechnungsliste als CSV. Stornorechnungen mindern den Umsatz.'),
      h('div', { class: 'grid3' }, kachel('Umsatz netto ' + d.jahr, euro(s.netto_cent), s.anzahl + ' Rechnungen'), kachel('Umsatzsteuer', euro(s.ust_cent), 'brutto ' + euro(s.brutto_cent)),
        kachel('Bezahlt / offen', euro(s.bezahlt_cent), euro(s.offen_cent) + ' noch offen')),
      mit.length ? h('div', { class: 'tablewrap' }, h('table', {}, h('thead', {}, h('tr', {}, ['Monat', 'Rechnungen', 'Netto', 'USt', 'Brutto'].map(t => h('th', {}, t)))),
        h('tbody', {}, mit.map(m => h('tr', {}, h('td', {}, m.name), h('td', {}, m.anzahl), h('td', {}, euro(m.netto_cent)), h('td', {}, euro(m.ust_cent)), h('td', {}, euro(m.brutto_cent))))))) : '',
      h('details', {}, h('summary', {}, 'Alle Rechnungen ' + d.jahr + ' (' + d.rechnungen.length + ')'),
        tabelle([['Nr.', z => h('a', { href: '#beleg/' + z.id }, z.nummer)], ['Datum', z => datum(z.datum)], ['Kunde', z => z.kunde], ['Brutto', z => euro(z.brutto_cent)],
          ['Status', z => h('span', { class: 'pill ' + (BELEG_ST[z.status] || '') }, z.storno ? 'Storno' : z.status)], ['Datei', z => h('span', { class: 'small muted' }, z.datei)]], d.rechnungen, 'Keine Rechnungen in diesem Jahr.')));
  };
  await zeige(0);
  return huelle;
}
