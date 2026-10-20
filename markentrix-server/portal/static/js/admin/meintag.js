import { h, api, datum } from '../common.js';
import { erinnerungsDialog } from './belege.js';
import { V, ich, kopf, sicherApi, zeige } from './kern.js';

/** „Mein Tag“: alles, was heute für dich ansteht, an einem Ort, plus deine gespeicherten Filter. */
V.meintag = async () => {
  const heute = await api('/api/admin/heute'), filter = (await sicherApi('/api/admin/meine-filter')) || [];
  const meine = ((await sicherApi('/api/admin/aufgaben?status=offen&zustaendig=' + encodeURIComponent((ich && ich.email) || '__')) || [])
    .filter(a => !a.faellig_am || String(a.faellig_am).slice(0, 10) <= new Date().toISOString().slice(0, 10)));
  const tag = new Date().toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' });
  const block = (titel, liste, zeile, leer) => !liste.length ? h('p', { class: 'small muted', style: 'margin:6px 0' }, '✓ ' + titel + ': ' + leer) : h('div', { class: 'tagblock' }, h('h3', {}, titel, liste.length ? h('span', { class: 'badge', style: 'margin-left:8px' }, liste.length) : ''),
    liste.length ? h('ul', { class: 'prio' }, liste.map(zeile)) : h('p', { class: 'small muted' }, leer));
  const zeile = (titel, text, aktion, knopfText) => h('li', {}, h('span', { class: 'punkt', 'aria-hidden': 'true' }), h('div', { class: 'pt' }, h('b', {}, titel), h('span', { class: 'small muted' }, text)),
    typeof aktion === 'function' ? h('button', { class: 'btn sec small', onclick: aktion }, knopfText) : h('a', { class: 'btn sec small', href: aktion }, knopfText));
  const erledigt = async (a) => { try { await api('/api/admin/aufgaben/' + a.id, { method: 'PATCH', body: { status: 'erledigt' } }); zeige(); } catch (x) { alert(x.message); } };
  const BEREICH = { leads: 'Leads', kunden: 'Kunden', belege: 'Rechnungen' };
  const summe = meine.length + heute.wiedervorlagen.length + heute.nachrichten.length + heute.rechnungen.length + heute.freigaben.length + heute.avv_fehlt.length;
  return h('div', { class: 'stack' }, kopf('Mein Tag'),
    h('div', { class: 'card' }, h('h2', {}, 'Heute'), h('p', { class: 'muted' }, tag + ' · ' + (summe ? summe + ' Dinge stehen an.' : 'Nichts Dringendes. Gute Gelegenheit für Neukunden. 🎉')),
      block('Meine Aufgaben', meine, a => zeile(a.titel, (a.firma ? a.firma + ' · ' : '') + (a.faellig_am ? 'fällig ' + datum(a.faellig_am) : 'ohne Datum'), () => erledigt(a), 'Erledigt'), 'Keine fälligen Aufgaben für dich.'),
      block('Anrufen und nachfassen', heute.wiedervorlagen, z => zeile(z.firma, 'Wiedervorlage ' + datum(z.wiedervorlage_am) + (z.vertriebler ? ' · ' + z.vertriebler : ''), '#lead/' + z.id, 'Lead öffnen'), 'Keine Wiedervorlagen fällig.'),
      block('Nachrichten, die auf Antwort warten', heute.nachrichten, z => zeile(z.firma, z.betreff, '#postfach/' + z.id, 'Antworten'), 'Keine ungelesenen Nachrichten.'),
      block('Überfällige Rechnungen', heute.rechnungen, z => zeile(z.firma, 'Rechnung ' + z.nummer, () => erinnerungsDialog(undefined, z.id), 'Erinnerung prüfen'), 'Keine Rechnung überfällig.'),
      block('Freigaben, die beim Kunden hängen', heute.freigaben, z => zeile(z.firma, z.titel, '#kunde/' + z.kunden_id, 'Öffnen'), 'Keine Freigabe wartet länger als 3 Tage.'),
      block('Verträge (AVV) fehlen', heute.avv_fehlt, z => zeile(z.firma, 'AVV fehlt', '#kunde/' + z.id, 'Öffnen'), 'Bei allen Kunden liegt eine AVV vor.'),
      heute.leads_gesamt ? h('p', {}, h('a', { class: 'btn small', href: '#leads?status=neu' }, heute.leads_gesamt + ' neue Leads ansehen')) : ''),
    h('div', { class: 'card' }, h('h2', {}, 'Meine Filter'),
      filter.length ? h('ul', { class: 'prio' }, filter.map(f => zeile(f.name, BEREICH[f.bereich] || f.bereich, '#' + f.bereich + (f.abfrage ? '?' + f.abfrage : ''), 'Öffnen')))
        : h('p', { class: 'small muted' }, 'Noch keine gespeicherten Filter. In den Listen Kunden, Leads und Rechnungen kannst du eine Auswahl mit „Aktuelle Auswahl speichern“ ablegen und hier mit einem Klick öffnen.')));
};
