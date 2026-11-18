import { h, api, melde } from '../common.js';

const lokalWert = (iso) => { const d = new Date(iso), p = (n) => String(n).padStart(2, '0'); return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':' + p(d.getMinutes()); };
const anzeige = (iso) => new Date(iso).toLocaleString('de-DE', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) + ' Uhr';

/** Bis zu 3 Terminvorschläge für ein Beratungsgespräch am Angebot.
 *  `belegId` gesetzt und `eigenerKnopf`: eigener Speichern-Knopf (für schon ausgestellte Angebote); sonst speichert der Aufrufer über `speichern(id)`. */
export function terminFelder({ vorhanden = [], gebucht = null, belegId = null, eigenerKnopf = false } = {}) {
  const m = h('div');
  const felder = [0, 1, 2].map((i) => h('input', { type: 'datetime-local', step: 900, 'aria-label': 'Terminvorschlag ' + (i + 1), value: vorhanden[i] ? lokalWert(vorhanden[i]) : '', disabled: !!gebucht }));
  const werte = () => felder.map(f => f.value).filter(Boolean).map(v => new Date(v).toISOString());
  const speichern = async (id) => api('/api/admin/belege/' + id + '/termine', { method: 'PUT', body: { termine: werte() } });
  const kopf = h('summary', {}, 'Terminvorschläge für ein Beratungsgespräch (optional)');
  const inhalt = gebucht
    ? [h('div', { class: 'msg ok' }, 'Beratungsgespräch gebucht: ' + anzeige(gebucht.start) + '. Der Termin steht im Kalender.')]
    : [h('p', { class: 'small muted' }, 'Der Empfänger wählt im Angebots-Link einen Termin. Er landet sofort im Kalender, die Kalendereinladung geht per Mail raus. Belegte Zeiten werden abgelehnt.'),
      h('div', { class: 'form2' }, felder.map(f => h('div', {}, f))), m,
      eigenerKnopf && belegId ? h('p', {}, h('button', { class: 'btn sec small', type: 'button', onclick: async () => {
        try { await speichern(belegId); melde(m, 'Terminvorschläge gespeichert.', 'ok'); } catch (x) { melde(m, x.message); }
      } }, 'Terminvorschläge speichern')) : ''];
  const el = h('details', { class: 'terminfelder', open: !!(vorhanden.length || gebucht) }, kopf, ...inhalt);
  return { el, werte, speichern, gebucht: !!gebucht };
}
