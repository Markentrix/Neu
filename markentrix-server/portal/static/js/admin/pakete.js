import { h, api } from '../common.js';
import { bestaetigt, cent, feld, knopf, select } from './kern.js';

const KAT = { kombi: 'Kombi-Paket', website: 'Website', ki: 'KI-Assistent', ci: 'Marke und Design (CI)', sichtbarkeit: 'Sichtbarkeit', personal_branding: 'Personal Branding', lead: 'Leads und Werbung' };
const ABR = { monatlich: 'monatlich', projekt: 'einmalig (Projekt)', projekt_pflege: 'Projekt + monatliche Pflege' };
const LAUF = [['', 'keine feste Laufzeit'], ['1', '1 Monat'], ['3', '3 Monate'], ['6', '6 Monate'], ['12', '12 Monate'], ['24', '24 Monate']];
const eur = (c) => c === null || c === undefined ? '–' : (c / 100).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
/** Staffelpreis lesen: je Zeile „Monat: Betrag“, z. B. „1: 149“, „2: 199“, „3: 249“. Leer = fester Monatspreis. */
export const staffelLesen = (t) => {
  const z = t.value.split('\n').map((x) => x.trim()).filter(Boolean);
  if (!z.length) return null;
  return z.map((x) => { const m = x.match(/^(?:ab\s*)?(?:monat\s*)?(\d+)\s*[:=]\s*([\d.,]+)\s*€?$/i); if (!m) throw new Error('Staffel: Zeile „' + x + '“ bitte als „Monat: Betrag“ schreiben, z. B. „2: 199“.'); return { ab_monat: Number(m[1]), cent: Math.round(Number(m[2].replace(',', '.')) * 100) }; });
};
export const staffelFeld = () => h('textarea', { rows: 3, 'aria-label': 'Staffelpreis je Monat', placeholder: 'Optional, eine Zeile pro Stufe:\n1: 149\n2: 199\n3: 249   (gilt ab Monat 3)' });
const zeilen = (t) => t.value.split('\n').map((x) => x.trim()).filter(Boolean);

/** Neues Paket anlegen: Name, Preis, Module, Leistungen. Erscheint danach im Kundenportal und in Angeboten. */
function neuesPaket(d, m) {
  const name = h('input', { name: 'name', required: true, maxlength: 80, placeholder: 'z. B. Website + Google-Anzeige' });
  const kat = select('kategorie', Object.entries(KAT), 'kombi'), abr = select('abrechnung', Object.entries(ABR), 'monatlich');
  const besch = h('input', { name: 'beschreibung', maxlength: 500, placeholder: 'Ein Satz für die Preisliste' });
  const einr = feld('Einrichtung in € (netto)', 'einr', '', { type: 'number', step: '0.01', min: '0' });
  const mon = feld('Monatlich in € (netto)', 'mon', '', { type: 'number', step: '0.01', min: '0' });
  const proj = feld('Einmalig (Projekt) in € (netto)', 'proj', '', { type: 'number', step: '0.01', min: '0' });
  const staffel = staffelFeld();
  const laufzeit = h('select', { 'aria-label': 'Mindestlaufzeit' }, LAUF.map(([v, t]) => h('option', { value: v }, t)));
  const ab = h('input', { type: 'checkbox', style: 'width:auto' }), anfrage = h('input', { type: 'checkbox', style: 'width:auto' }), einzeln = h('input', { type: 'checkbox', checked: true, style: 'width:auto' });
  const leist = h('textarea', { rows: 5, maxlength: 6000, 'aria-label': 'Leistungen', placeholder: 'Eine Zeile pro Punkt, z. B.\n1 Google-Anzeige pro Monat (Einrichtung und Betreuung)\nBerichte monatlich' });
  const mods = d.module.map((x) => ({ x, box: h('input', { type: 'checkbox', style: 'width:auto' }) }));
  const val = (f) => f.querySelector('input').value;
  return h('details', { class: 'card' }, h('summary', {}, h('b', {}, '+ Neues Paket anlegen')),
    h('p', { class: 'small muted' }, 'Zum Beispiel „Website + 1 Google-Anzeige pro Monat“ für 149 € im Monat. Das Paket erscheint wie die festen Pakete im Kundenportal und bei der Paket-Wahl im Angebot. Alle Preise netto. Das Werbebudget zahlt der Kunde direkt an die Plattform.'),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Name'), name), h('div', {}, h('label', {}, 'Kategorie'), kat), h('div', {}, h('label', {}, 'Abrechnung'), abr), h('div', {}, h('label', {}, 'Mindestlaufzeit'), laufzeit), einr, mon, proj),
    h('div', {}, h('label', {}, 'Kurzbeschreibung'), besch),
    h('div', {}, h('label', {}, 'Staffelpreis pro Monat (optional)'), staffel, h('p', { class: 'small muted' }, 'Beispiel: Monat 1 = 149 €, Monat 2 = 199 €, ab Monat 3 = 249 €. Der Betrag der letzten Stufe gilt dauerhaft und ersetzt den Monatspreis oben. Gezählt wird ab Beginn der Buchung. Rechnungen und Provision richten sich nach dem Preis des jeweiligen Monats.')),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, ab, '„ab“-Preis'),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, anfrage, 'Nur auf Anfrage (kein Preis angezeigt)'),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, einzeln, 'Kunden dürfen es im Portal selbst dazubuchen'),
    h('h3', {}, 'Leistungen („Das bekommen Sie“)'), leist,
    h('h3', {}, 'Schaltet diese Portal-Module frei'), h('p', { class: 'small muted' }, 'Nur ankreuzen, was zum Paket gehört. Ohne Haken wird nichts freigeschaltet.'),
    h('div', { class: 'form2' }, mods.map(({ x, box }) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, box, x.name))),
    h('p', {}, knopf('Paket anlegen', () => bestaetigt(m, () => api('/api/admin/pakete', { method: 'POST', body: {
      name: name.value, kategorie: kat.value, abrechnung: abr.value, beschreibung: besch.value, laufzeit_monate: laufzeit.value === '' ? null : Number(laufzeit.value),
      einrichtung_cent: cent(val(einr)), monatlich_cent: cent(val(mon)), staffel: staffelLesen(staffel), projekt_cent: cent(val(proj)), ab_preis: ab.checked, nur_auf_anfrage: anfrage.checked, einzeln_buchbar: einzeln.checked,
      leistungen: zeilen(leist), module: mods.filter((y) => y.box.checked).map((y) => y.x.code) } }), 'Paket angelegt.'), 'btn')));
}

function paketZeile(p, d) {
  const m = h('span', { class: 'small', role: 'status' });
  const eigen = p.eigen;
  const aktiv = p.aktiv ? 'aktiv' : 'ausgeblendet';
  const leist = h('textarea', { rows: Math.max(3, (p.leistungen || []).length + 1), 'aria-label': 'Leistungen ' + p.name }); leist.value = (p.leistungen || []).join('\n');
  const lauf = h('select', { 'aria-label': 'Mindestlaufzeit ' + p.name, disabled: !eigen }, LAUF.map(([v, t]) => h('option', { value: v, selected: String(p.laufzeit_monate || '') === v }, t)));
  const name = h('input', { value: p.name, maxlength: 80, disabled: !eigen }), besch = h('input', { value: p.beschreibung || '', maxlength: 500, disabled: !eigen });
  const mods = d.module.map((x) => ({ x, box: h('input', { type: 'checkbox', checked: p.module.includes(x.code), disabled: !eigen, style: 'width:auto' }) }));
  const speichern = () => bestaetigt(m, () => api('/api/admin/pakete/' + encodeURIComponent(p.code), { method: 'PUT', body: eigen
    ? { name: name.value, beschreibung: besch.value, laufzeit_monate: lauf.value === '' ? 0 : Number(lauf.value), leistungen: zeilen(leist), module: mods.filter((y) => y.box.checked).map((y) => y.x.code) }
    : { leistungen: zeilen(leist) } }));
  const umschalten = () => bestaetigt(m, () => api('/api/admin/pakete/' + encodeURIComponent(p.code), { method: 'PUT', body: { aktiv: !p.aktiv } }), p.aktiv ? 'Ausgeblendet.' : 'Wieder sichtbar.');
  const loeschen = () => confirm('Paket „' + p.name + '“ endgültig löschen? Das geht nur, solange es nie gebucht wurde.') && bestaetigt(m, () => api('/api/admin/pakete/' + encodeURIComponent(p.code), { method: 'DELETE' }), 'Gelöscht.');
  return h('details', { style: 'margin:6px 0' },
    h('summary', {}, h('b', {}, p.name), ' ', h('span', { class: 'small muted' }, (KAT[p.kategorie] || p.kategorie) + (p.laufzeit_monate ? ' · ' + p.laufzeit_monate + ' Monate Laufzeit' : '') + ' · ' + (p.staffel ? p.staffel.map((s, i, a) => (i === a.length - 1 ? 'ab ' : '') + 'Monat ' + s.ab_monat + ': ' + eur(s.cent)).join(', ') : p.monatlich_cent !== null ? eur(p.monatlich_cent) + '/Monat' : p.projekt_cent !== null ? eur(p.projekt_cent) : 'auf Anfrage') + ' · ' + aktiv + (eigen ? ' · eigenes Paket' : ''))),
    h('p', { class: 'small muted' }, p.code + ' · ' + p.buchungen + ' Buchungen · ' + p.kunden + ' Kunden. Preise ändern: weiter unten unter „Preis ändern (neue Version)“.'),
    eigen ? [h('div', {}, h('label', {}, 'Name'), name), h('div', {}, h('label', {}, 'Kurzbeschreibung'), besch), h('div', {}, h('label', {}, 'Mindestlaufzeit'), lauf)] : '',
    h('label', {}, 'Leistungen (eine Zeile pro Punkt)'), leist,
    h('h4', {}, 'Freigeschaltete Module'), eigen ? '' : h('p', { class: 'small muted' }, 'Bei festen Paketen nicht änderbar.'),
    h('div', { class: 'form2' }, mods.map(({ x, box }) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, box, x.name))),
    h('p', {}, knopf('Speichern', speichern, 'btn'), ' ', knopf(p.aktiv ? 'Ausblenden' : 'Einblenden', umschalten), ' ', eigen && !p.buchungen && !p.kunden ? knopf('Löschen', loeschen) : '', ' ', m));
}

export async function paketeKarte() {
  const d = await api('/api/admin/pakete'), m = h('div');
  return h('div', { class: 'stack' }, m, neuesPaket(d, m),
    h('div', { class: 'card' }, h('h2', {}, 'Alle Pakete'), h('p', { class: 'small muted' }, 'Eigene Pakete stehen oben. Gebuchte Pakete lassen sich nicht löschen, nur ausblenden; bestehende Buchungen behalten Preis und Leistungen.'), d.pakete.map((p) => paketZeile(p, d))));
}
