// Verträge aus dem Portal: Referenzvertrag (beim Kunden) und Handelsvertretervertrag (beim Vertriebler).
// Das Portal füllt das PDF-Formular vor, schickt es per Mail und legt die unterschriebene Fassung ab.
import { h, api, datum, melde } from '../common.js';
import { fehler, feld, knopf, select, tabelle } from './kern.js';

const stand = (z) => z.unterschrieben_am ? h('span', { class: 'pill ok' }, 'unterschrieben ' + datum(z.unterschrieben_am)) : z.gesendet_am ? h('span', { class: 'pill warn' }, 'gesendet an ' + z.gesendet_an + ' (' + datum(z.gesendet_am) + ')') : h('span', { class: 'pill' }, 'nur erstellt');

function ablegen(z, m) {
  const datei = h('input', { type: 'file', accept: 'application/pdf,image/png,image/jpeg' }), tag = h('input', { type: 'date', value: new Date().toISOString().slice(0, 10), style: 'max-width:160px' });
  return h('span', { class: 'row' }, datei, tag, knopf('Unterschrieben ablegen', () => {
    const f = datei.files[0]; if (!f) return fehler(m, { message: 'Bitte zuerst die unterschriebene Datei wählen.' });
    const r = new FileReader();
    r.onload = async () => { try { await api('/api/admin/vertragsdokumente/' + z.id + '/upload', { method: 'POST', body: { datei_base64: r.result, datei_name: f.name, unterschrieben_am: tag.value } }); location.reload(); } catch (x) { fehler(m, x); } };
    r.readAsDataURL(f);
  }, 'btn small'));
}

function liste(zeilen, m, leer) {
  const aktion = (z) => h('span', { class: 'row' },
    h('a', { class: 'btn sec small', href: '/api/admin/vertragsdokumente/' + z.id + '/vorlage.pdf', target: '_blank', rel: 'noopener' }, 'PDF'),
    knopf('Erneut senden', async () => { if (!confirm('Den Vertrag jetzt per E-Mail senden?')) return; try { await api('/api/admin/vertragsdokumente/' + z.id + '/senden', { method: 'POST', body: {} }); melde(m, 'Gesendet.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } }, 'sec small'),
    z.hat_datei ? h('a', { class: 'btn sec small', href: '/api/admin/vertragsdokumente/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Unterschrieben ansehen') : ablegen(z, m),
    knopf('Löschen', async () => { if (!confirm('Eintrag löschen' + (z.hat_datei ? ' (auch die abgelegte unterschriebene Datei)' : '') + '?')) return; try { await api('/api/admin/vertragsdokumente/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { fehler(m, x); } }, 'bad small'));
  return tabelle([['Erstellt', z => datum(z.erstellt_am)], ['Stand', stand], ['', aktion]], zeilen, leer);
}

async function absenden(m, pfad, o, senden) {
  try { const r = await api(pfad, { method: 'POST', body: { ...o, senden } }); melde(m, r.gesendet ? 'Vertrag erstellt und per Mail gesendet.' : 'Vertrag erstellt. Du findest ihn in der Liste.', 'ok'); setTimeout(() => location.reload(), 1200); }
  catch (x) { fehler(m, x); }
}

export async function referenzKarte(kid, k) {
  const zeilen = await api('/api/admin/kunden/' + kid + '/vertragsdokumente'), m = h('div');
  const f = { projekt: feld('Projekt', 'projekt', '', { placeholder: 'z. B. Website www.beispiel.de', maxlength: 200 }), vom: feld('Hauptvertrag vom', 'hv', '', { placeholder: 'z. B. 01.10.2026', maxlength: 40 }),
    zeit: feld('Umsetzungszeitraum', 'zeit', '', { placeholder: 'z. B. 01.09.–30.09.2026', maxlength: 80 }), vertreter: feld('Vertreten durch', 'v', k.ansprechpartner || '', { maxlength: 200 }),
    an: feld('E-Mail an', 'an', k.email || '', { maxlength: 200 }) };
  const werte = () => ({ projekt: f.projekt.querySelector('input').value, hauptvertrag_vom: f.vom.querySelector('input').value, zeitraum: f.zeit.querySelector('input').value, vertreter: f.vertreter.querySelector('input').value, an: f.an.querySelector('input').value });
  return h('div', { class: 'card' }, h('h2', {}, 'Referenzvertrag ', zeilen.some(z => z.unterschrieben_am) ? h('span', { class: 'pill ok' }, 'liegt vor') : h('span', { class: 'pill' }, 'optional')),
    h('p', { class: 'small muted' }, 'Erlaubt uns, das Projekt des Kunden als Referenz zu zeigen. Das Portal füllt Firma, Anschrift, Ansprechpartner und Projekt im Formular vor. Welche Punkte freigegeben sind, kreuzt der Kunde selbst in Anlage 1 an (freiwillig, nichts ist vorangekreuzt). Danach unterschreiben lassen und hier ablegen.'), m,
    liste(zeilen, m, 'Noch kein Referenzvertrag erstellt.'),
    h('div', { class: 'form2', style: 'margin-top:10px' }, f.projekt, f.vom, f.zeit, f.vertreter, f.an),
    h('div', { class: 'row', style: 'margin-top:8px' }, knopf('Erstellen und per Mail senden', () => absenden(m, '/api/admin/kunden/' + kid + '/referenzvertrag', werte(), true), 'btn'), knopf('Nur erstellen', () => absenden(m, '/api/admin/kunden/' + kid + '/referenzvertrag', werte(), false), 'sec')));
}

export async function handelsvertreterKarte(pid, p) {
  const zeilen = await api('/api/admin/vertrieb/partner/' + pid + '/vertragsdokumente'), m = h('div');
  const i = (l, n, w = '', e = {}) => feld(l, n, w, { maxlength: 200, ...e });
  const f = { name: i('Name / Firma', 'name', p.firma || p.name), rechtsform: i('Rechtsform', 'rf', '', { placeholder: 'z. B. Einzelunternehmen' }), strasse: i('Straße, Hausnummer', 's'), ort: i('PLZ, Ort', 'o'), mail: i('E-Mail', 'mail', p.email || ''), steuer: i('Steuernummer / USt-IdNr.', 'st'),
    einmal: i('Provision einmalig (%)', 'e', '', { placeholder: 'Vorlage: 20', maxlength: 10 }), monat: i('Provision laufend (%)', 'm', '', { placeholder: 'Vorlage: 15', maxlength: 10 }), praemie: i('Prämie', 'p', '', { placeholder: 'Vorlage: 10', maxlength: 10 }), vorschuss: i('Vorschuss', 'v', '', { placeholder: 'Vorlage: 50', maxlength: 10 }) };
  const art = select('b', [['', 'Partner wählt selbst'], ['haupt', 'Hauptberuf'], ['neben', 'Nebenberuf']], '');
  const w = (n) => f[n].querySelector('input').value;
  const werte = () => ({ name: w('name'), rechtsform: w('rechtsform'), strasse: w('strasse'), ort: w('ort'), mail: w('mail'), steuer: w('steuer'), beauftragung: art.value, einmal: w('einmal'), monat: w('monat'), praemie: w('praemie'), vorschuss: w('vorschuss'), an: w('mail') });
  const pfad = '/api/admin/vertrieb/partner/' + pid + '/handelsvertretervertrag';
  return h('div', { class: 'card' }, h('h2', {}, 'Handelsvertretervertrag ', zeilen.some(z => z.unterschrieben_am) ? h('span', { class: 'pill ok' }, 'liegt vor') : h('span', { class: 'pill warn' }, 'fehlt')),
    h('p', { class: 'small muted' }, 'Das Portal füllt das Vertragsformular mit den Angaben des Vertrieblers vor und schickt es per Mail. Der Vertriebler ergänzt Anlage 3 selbst, unterschreibt und schickt es zurück. Beim Ablegen der unterschriebenen Fassung wird das Datum bei „Vereinbarung“ eingetragen. Leere Provisionsfelder behalten die Werte aus der Vorlage.'), m,
    liste(zeilen, m, 'Noch kein Vertrag erstellt.'),
    h('div', { class: 'form2', style: 'margin-top:10px' }, f.name, f.rechtsform, f.strasse, f.ort, f.mail, f.steuer, h('div', {}, h('label', {}, 'Beauftragung'), art), f.einmal, f.monat, f.praemie, f.vorschuss),
    h('div', { class: 'row', style: 'margin-top:8px' }, knopf('Erstellen und per Mail senden', () => absenden(m, pfad, werte(), true), 'btn'), knopf('Nur erstellen', () => absenden(m, pfad, werte(), false), 'sec')));
}
