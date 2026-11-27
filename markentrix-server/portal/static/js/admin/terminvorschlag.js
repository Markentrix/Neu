import { h, api, melde, zeit } from '../common.js';
import { terminFelder } from './terminfelder.js';

const STATUS = { offen: 'wartet auf Antwort', gewaehlt: 'bestätigt', zurueckgezogen: 'zurückgezogen' };
const anzeige = (iso) => new Date(iso).toLocaleString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) + ' Uhr';

/** Terminvorschläge ohne Angebot: bis zu 3 Zeiten per Mail an einen Kunden oder Lead. Ein Klick des Empfängers legt den Termin in den Kalender.
 *  `ziel` = { kunden_id } oder { lead_id }, `email` = hinterlegte Adresse (änderbar). */
export async function terminvorschlagKarte(ziel, email = '') {
  const abfrage = ziel.kunden_id ? 'kunden_id=' + ziel.kunden_id : 'lead_id=' + ziel.lead_id;
  const alt = await api('/api/admin/terminvorschlaege?' + abfrage).catch(() => []);
  const m = h('div'), tf = terminFelder({}); tf.el.open = true;
  const an = h('input', { type: 'email', value: email || '', placeholder: 'E-Mail des Empfängers', 'aria-label': 'E-Mail des Empfängers' });
  const text = h('textarea', { rows: 2, maxlength: 1500, placeholder: 'Kurze Nachricht (optional), z. B. „Gern sprechen wir über …“', 'aria-label': 'Nachricht' });
  const senden = h('button', { class: 'btn', type: 'button', onclick: async (e) => {
    const z = tf.werte();
    if (!z.length) { melde(m, 'Bitte mindestens einen Termin eintragen.'); return; }
    e.target.disabled = true;
    try {
      const r = await api('/api/admin/terminvorschlaege', { method: 'POST', body: { ...ziel, zeiten: z, nachricht: text.value, an_email: an.value || null } });
      if (r.gesendet) { melde(m, 'Terminvorschläge sind per E-Mail raus.', 'ok'); setTimeout(() => location.reload(), 900); }
      else { melde(m, 'Die Vorschläge sind gespeichert, aber die Mail ging nicht raus: ' + (r.grund || 'unbekannter Fehler')); e.target.disabled = false; }
    } catch (x) { e.target.disabled = false; melde(m, x.message); }
  } }, 'Terminvorschläge senden');
  const verlauf = alt.length ? h('div', { class: 'stack', style: 'margin-top:12px' }, h('h3', {}, 'Bisher gesendet'), ...alt.map(v => h('div', { class: 'small' },
    h('b', {}, zeit(v.erstellt_am)), ' · ', STATUS[v.status] || v.status, !v.gesendet && v.status === 'offen' ? ' · Mail nicht zugestellt' : '',
    v.gewaehlt ? ' · Termin: ' + anzeige(v.gewaehlt) + (v.gespraech_status === 'abgesagt' ? ' (abgesagt)' : '') : ' · ' + (v.zeiten || []).map(anzeige).join(' / '),
    v.status === 'offen' ? [' ', h('button', { class: 'btn sec small', type: 'button', onclick: async () => { try { await api('/api/admin/terminvorschlaege/' + v.id, { method: 'DELETE' }); location.reload(); } catch (x) { melde(m, x.message); } } }, 'Zurückziehen')] : ''))) : '';
  return h('div', { class: 'card' }, h('h2', {}, 'Terminvorschläge senden'),
    h('p', { class: 'small muted' }, 'Bis zu 3 Zeiten für ein Beratungsgespräch, ohne Angebot. Der Empfänger klickt in der Mail auf einen Termin und bestätigt. Danach steht er im Kalender, beide bekommen die Einladung, die Erinnerungen laufen automatisch. Ein neuer Versand zieht offene Vorschläge zurück.'),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'An'), an)), tf.el, h('label', {}, 'Nachricht'), text, m, h('p', {}, senden), verlauf);
}
