import { h, api, melde, dialog, euro } from '../common.js';
import { V } from './kern.js';

const STATUS = { angefragt: ['warn', 'Angefragt, wird geprüft'], beauftragt: ['ok', 'Bestätigt'], in_einrichtung: ['ok', 'In Einrichtung'], aktiv: ['ok', 'Aktiv'], pausiert: ['', 'Pausiert'] };

function preisText(p) {
  if (p.auf_anfrage) return 'Preis auf Anfrage';
  const teile = [];
  if (p.projekt_cent) teile.push((p.ab_preis ? 'ab ' : '') + euro(p.projekt_cent) + ' einmalig');
  if (p.einrichtung_cent) teile.push(euro(p.einrichtung_cent) + ' Einrichtung');
  if (p.monatlich_cent) teile.push(euro(p.monatlich_cent) + (p.abrechnung === 'projekt_pflege' ? ' Pflege pro Monat' : ' pro Monat'));
  return teile.length ? teile.join(' + ') : 'kostenfrei';
}

function buchenDialog(p, referenz, fertig) {
  const m = h('div'), haken = h('input', { type: 'checkbox', 'aria-label': 'Buchung bestätigen', style: 'width:auto' }), notiz = h('textarea', { rows: 3, maxlength: 1000, 'aria-label': 'Anmerkung (optional)', placeholder: 'Anmerkung (optional)' });
  const dlg = dialog(p.name + ' dazubuchen', h('div', { class: 'stack' },
    h('p', {}, p.beschreibung),
    h('p', {}, h('b', {}, preisText(p)), p.auf_anfrage ? '' : h('span', { class: 'small muted' }, ' (netto, zuzüglich Umsatzsteuer)')),
    referenz && p.regulaer ? h('p', { class: 'small muted' }, 'Als Referenzkunde ist das für dich kostenfrei. Regulärer Preis: ' + preisText({ ...p, ...p.regulaer }) + '.') : '',
    p.nachlaesse && p.nachlaesse.length ? h('p', { class: 'msg info' }, 'Berücksichtigt: ' + p.nachlaesse.map(n => n.text + ' (' + euro(n.cent) + ')').join(', ') + '. Listenpreis: ' + preisText({ ...p, ...p.listenpreis }) + '.') : '',
    p.hinweis ? h('p', { class: 'small muted' }, p.hinweis) : '',
    p.laufzeit_monate ? h('p', { class: 'small' }, 'Mindestlaufzeit: ' + p.laufzeit_monate + ' Monate.') : '',
    h('label', {}, 'Anmerkung'), notiz,
    h('label', { style: 'display:flex;gap:8px;align-items:flex-start;color:inherit;margin-top:8px' }, haken, p.auf_anfrage ? 'Ich möchte ein Angebot für dieses Paket anfragen.' : 'Ich buche dieses Paket verbindlich zu den genannten Konditionen. Markentrix bestätigt die Buchung und meldet sich zur Einrichtung. Bis dahin entstehen keine Kosten.'),
    m, h('p', {}, h('button', { class: 'btn', onclick: async (e) => {
      e.target.disabled = true;
      try { const r = await api('/api/kunde/pakete/' + p.code + '/dazubuchen', { method: 'POST', body: { bestaetigt: haken.checked, notiz: notiz.value } }); dlg.zu(); fertig(r.hinweis); }
      catch (x) { melde(m, x.message); e.target.disabled = false; } } }, p.auf_anfrage ? 'Angebot anfragen' : 'Verbindlich dazubuchen'))));
}

V.pakete = async () => {
  const k = await api('/api/kunde/paketkatalog'), m = h('div');
  const karte = (p) => h('div', { class: 'card', style: 'margin:8px 0' },
    h('div', { style: 'display:flex;gap:8px;flex-wrap:wrap;align-items:center' }, h('b', { class: 'grow' }, p.name),
      p.status ? h('span', { class: 'pill ' + STATUS[p.status][0] }, STATUS[p.status][1]) : ''),
    h('p', { class: 'small' }, p.beschreibung), p.nachlaesse && p.nachlaesse.length ? h('p', { class: 'small' }, h('span', { class: 'pill ok' }, 'Nachlass: ' + p.nachlaesse.map(n => euro(n.cent)).join(' + '))) : '', h('p', {}, h('b', {}, preisText(p)), p.laufzeit_monate ? h('span', { class: 'small muted' }, ' · Mindestlaufzeit ' + p.laufzeit_monate + ' Monate') : ''),
    p.status ? '' : h('button', { class: 'btn small', onclick: () => buchenDialog(p, k.referenzkunde, (t) => { melde(m, t, 'ok'); setTimeout(() => location.reload(), 1800); }) }, p.auf_anfrage ? 'Angebot anfragen' : 'Dazubuchen'));
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Pakete & Zusatzleistungen'),
    h('p', { class: 'small muted' }, 'Hier siehst du unsere Preisliste (alle Preise netto) und kannst Pakete direkt dazubuchen. Markentrix bestätigt jede Buchung, bis dahin entstehen keine Kosten.'),
    h('p', { class: 'small muted' }, k.zusatzkosten), k.referenzkunde ? h('p', { class: 'msg info' }, 'Du bist Referenzkunde: Zusatzpakete sind für dich kostenfrei.') : '', m),
    k.gruppen.map(g => h('div', { class: 'card' }, h('h2', {}, g.titel), g.produkte.map(karte))));
};
