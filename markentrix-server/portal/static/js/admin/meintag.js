import { h, api, datum } from '../common.js';
import { erinnerungsDialog } from './belege.js';
import { V, ich, kopf, sicherApi, zeige } from './kern.js';
import { betriebsKarte } from './start.js';

/** „Mein Tag“: alles, was heute für dich ansteht, an einem Ort, plus deine gespeicherten Filter. */
V.meintag = async () => {
  const sys = await sicherApi('/api/admin/systemstatus'), heute = await api('/api/admin/heute'), filter = (await sicherApi('/api/admin/meine-filter')) || [];
  const meine = ((await sicherApi('/api/admin/aufgaben?status=offen&zustaendig=' + encodeURIComponent((ich && ich.email) || '__')) || [])
    .filter(a => !a.faellig_am || String(a.faellig_am).slice(0, 10) <= new Date().toISOString().slice(0, 10)));
  const tag = new Date().toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long' });
  const nichts = [];
  const block = (titel, liste, zeile, leer, kurz) => { if (!liste.length) { nichts.push(kurz || titel); return ''; } return h('div', { class: 'tagblock' }, h('h3', {}, titel, h('span', { class: 'badge', style: 'margin-left:8px' }, liste.length)), h('ul', { class: 'prio' }, liste.map(zeile))); };
  const zeile = (titel, text, aktion, knopfText) => h('li', {}, h('span', { class: 'punkt', 'aria-hidden': 'true' }), h('div', { class: 'pt' }, h('b', {}, titel), h('span', { class: 'small muted' }, text)),
    typeof aktion === 'function' ? h('button', { class: 'btn sec small', onclick: aktion }, knopfText) : h('a', { class: 'btn sec small', href: aktion }, knopfText));
  const erledigt = async (a) => { try { await api('/api/admin/aufgaben/' + a.id, { method: 'PATCH', body: { status: 'erledigt' } }); zeige(); } catch (x) { alert(x.message); } };
  const bezahlt = async (z) => { if (!confirm('Zahlungseingang für Rechnung ' + z.nummer + ' (' + z.firma + ') in voller Höhe bestätigen?')) return; try { await api('/api/admin/belege/' + z.id + '/bezahlt', { method: 'POST', body: {} }); zeige(); } catch (x) { alert(x.message); } };
  const BEREICH = { leads: 'Leads', kunden: 'Kunden', belege: 'Rechnungen' };
  const summe = (heute.gespraeche || []).length + (heute.vorschlaege || []).length + meine.length + heute.wiedervorlagen.length + heute.nachrichten.length + heute.rechnungen.length + heute.freigaben.length + heute.avv_fehlt.length;
  const blocke = [
      block('Meine Aufgaben', meine, a => zeile(a.titel, (a.firma ? a.firma + ' · ' : '') + (a.faellig_am ? 'fällig ' + datum(a.faellig_am) : 'ohne Datum'), () => erledigt(a), 'Erledigt'), 'Keine fälligen Aufgaben für dich.', 'Aufgaben'),
      block('Beratungsgespräche heute und morgen', heute.gespraeche || [], z => zeile(z.firma, new Date(z.start).toLocaleString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) + ' Uhr', z.lead_id ? '#lead/' + z.lead_id : z.kunden_id ? '#kunde/' + z.kunden_id : '#kalender', 'Öffnen'), 'Keine Gespräche in den nächsten 36 Stunden.', 'Gespräche'),
      block('Terminvorschläge ohne Antwort', heute.vorschlaege || [], z => zeile(z.name, 'seit ' + z.tage + (z.tage === 1 ? ' Tag' : ' Tagen') + (z.nachfass_anzahl ? ' · ' + z.nachfass_anzahl + '× nachgefasst' : ''), async (e) => {
        if (!confirm('Erinnerungsmail an ' + z.name + ' senden?')) return;
        e.target.disabled = true;
        try { await api('/api/admin/terminvorschlaege/' + z.id + '/nachfassen', { method: 'POST' }); zeige(); } catch (x) { e.target.disabled = false; alert(x.message); }
      }, 'Nachfassen'), 'Keine offenen Terminvorschläge.', 'Terminvorschläge'),
      block('Anrufen und nachfassen', heute.wiedervorlagen, z => zeile(z.firma, 'Wiedervorlage ' + datum(z.wiedervorlage_am) + (z.vertriebler ? ' · ' + z.vertriebler : ''), '#lead/' + z.id, 'Lead öffnen'), 'Keine Wiedervorlagen fällig.', 'Anrufe'),
      block('Nachrichten, die auf Antwort warten', heute.nachrichten, z => zeile(z.firma, z.betreff, '#postfach/' + z.id, 'Antworten'), 'Keine ungelesenen Nachrichten.', 'Nachrichten'),
      block('Überfällige Rechnungen', heute.rechnungen, z => { const li = zeile(z.firma, 'Rechnung ' + z.nummer, () => erinnerungsDialog(undefined, z.id), 'Erinnerung prüfen'); li.append(h('button', { class: 'btn small', title: 'Zahlungseingang in voller Höhe bestätigen', onclick: () => bezahlt(z) }, 'Bezahlt')); return li; }, 'Keine Rechnung überfällig.', 'Rechnungen'),
      block('Freigaben, die beim Kunden hängen', heute.freigaben, z => zeile(z.firma, z.titel, '#kunde/' + z.kunden_id, 'Öffnen'), 'Keine Freigabe wartet länger als 3 Tage.', 'Freigaben'),
      block('Verträge (AVV) fehlen', heute.avv_fehlt, z => zeile(z.firma, 'AVV fehlt', '#kunde/' + z.id, 'Öffnen'), 'Bei allen Kunden liegt eine AVV vor.', 'Verträge'),
  ];
  const meinFilter = h('details', { class: 'card einkl' }, h('summary', {}, h('h2', {}, 'Meine Filter')),
      filter.length ? h('ul', { class: 'prio' }, filter.map(f => zeile(f.name, BEREICH[f.bereich] || f.bereich, '#' + f.bereich + (f.abfrage ? '?' + f.abfrage : ''), 'Öffnen')))
        : h('p', { class: 'small muted' }, 'Noch keine gespeicherten Filter. In den Listen Kunden, Leads und Rechnungen kannst du eine Auswahl mit „Aktuelle Auswahl speichern“ ablegen und hier mit einem Klick öffnen.'));
  const ampel = sys && sys.ampel ? (sys.gesamt === 'ok' ? h('p', { class: 'small' }, h('span', { class: 'pill ok' }, '● System in Ordnung'), ' ', h('a', { href: '#uebersicht' }, 'Details')) : betriebsKarte(sys)) : '';
  return h('div', { class: 'stack' }, kopf('Mein Tag'), ampel,
    h('div', { class: 'card' }, h('h2', {}, 'Heute'), h('p', { class: 'muted' }, tag + ' · ' + (summe ? summe + (summe === 1 ? ' Ding steht' : ' Dinge stehen') + ' an.' : 'Alles erledigt. Gute Gelegenheit für Neukunden. 🎉')),
      blocke,
      nichts.length && summe ? h('p', { class: 'small muted', style: 'margin:10px 0 0' }, '✓ Nichts offen bei: ' + nichts.join(', ') + '.') : '',
      heute.leads_gesamt ? h('p', {}, h('a', { class: 'btn small', href: '#leads?status=neu' }, heute.leads_gesamt + ' neue Leads ansehen')) : ''),
    meinFilter);
};
