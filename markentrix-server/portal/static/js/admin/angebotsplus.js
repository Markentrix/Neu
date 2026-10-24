import { h, api, euro, melde } from '../common.js';

/** Pflege der Standard-Leistungstexte je Paket („Das bekommen Sie“). Sie füllen neue Angebote vor und lassen sich dort noch ändern. */
export async function leistungstextKarte() {
  const liste = await api('/api/admin/katalog/leistungstexte');
  const zeile = (p) => {
    const t = h('textarea', { rows: Math.max(4, (p.leistungen || []).length + 1), 'aria-label': 'Leistungen ' + p.name, maxlength: 6000 }); t.value = (p.leistungen || []).join('\n');
    const m = h('span', { class: 'small', role: 'status' });
    return h('details', { style: 'margin:6px 0' }, h('summary', {}, h('b', {}, p.name), ' ', h('span', { class: 'small muted' }, (p.leistungen || []).length + ' Punkte')),
      h('p', { class: 'small muted' }, 'Eine Zeile pro Punkt. „## “ davor = Zwischenüberschrift.'), t,
      h('p', {}, h('button', { class: 'btn small', onclick: async () => {
        try { const r = await api('/api/admin/katalog/leistungstexte/' + encodeURIComponent(p.code), { method: 'PUT', body: { leistungen: t.value.split('\n').map(x => x.trim()).filter(Boolean) } }); melde(m, 'Gespeichert (' + r.anzahl + ' Punkte).', 'ok'); } catch (x) { melde(m, x.message); }
      } }, 'Speichern'), ' ', m));
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Leistungstexte der Pakete'), h('p', { class: 'small muted' }, 'Das steht im Angebot unter „Das bekommen Sie“. Prüfe die Texte, bevor sie an Kunden gehen. Änderungen gelten für neue Angebote, versendete bleiben unverändert.'), liste.map(zeile));
}

/** Annahmequote, Zeit bis zur Annahme, beliebteste Pakete. */
export async function angebotsAuswertungKarte() {
  const d = await api('/api/admin/belege-auswertung');
  const kachel = (titel, wert, sub) => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, titel), h('b', {}, wert), sub ? h('span', { class: 'small muted' }, sub) : '');
  return h('div', { class: 'card' }, h('h2', {}, 'Angebote: Auswertung'), h('p', { class: 'small muted' }, 'Letzte ' + d.tage + ' Tage, nur verschickte Angebote.'),
    d.gesendet ? [h('div', { class: 'grid3' },
      kachel('Verschickt', d.gesendet, d.angesehen + ' davon angesehen'),
      kachel('Angenommen', d.angenommen, d.quote === null ? '' : 'Quote ' + d.quote + ' %'),
      kachel('Zeit bis zur Annahme', d.tage_bis_annahme === null ? '–' : String(d.tage_bis_annahme).replace('.', ',') + ' Tage', d.angenommen ? euro(d.summe_angenommen_cent) + ' angenommen (brutto)' : '')),
      h('p', { class: 'small muted' }, d.offen + ' noch offen · ' + d.abgelehnt + ' abgelehnt · ' + d.abgelaufen + ' abgelaufen'),
      d.gruende && d.gruende.length ? [h('h3', {}, 'Woran Angebote scheitern'), h('table', {}, h('thead', {}, h('tr', {}, ['Grund', 'Angebote'].map(t => h('th', {}, t)))), h('tbody', {}, d.gruende.map(g => h('tr', {}, h('td', {}, g.name), h('td', {}, g.anzahl)))))] : h('p', { class: 'small muted' }, 'Tipp: Mit „Grund festhalten“ am Angebot siehst du hier, woran Angebote scheitern.'),
      d.pakete.length ? h('table', {}, h('thead', {}, h('tr', {}, ['Paket', 'Angebote', 'Angenommen'].map(t => h('th', {}, t)))), h('tbody', {}, d.pakete.map(p => h('tr', {}, h('td', {}, p.name), h('td', {}, p.angebote), h('td', {}, p.angenommen))))) : '']
      : h('p', { class: 'muted' }, 'Noch keine verschickten Angebote.'));
}
