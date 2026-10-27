// Terminbestätigung an einen Lead: vorgeschriebener Text per WhatsApp, SMS oder E-Mail (öffnet die jeweilige App; gesendet wird dort).
import { h, api, melde, dialog } from './common.js';

/** Telefonnummer für wa.me (nur Ziffern, 0… wird zu 49…). */
function nummer(telefon, plus) {
  let z = String(telefon || '').replace(/[^\d+]/g, '');
  if (z.startsWith('+')) z = z.slice(1); else if (z.startsWith('00')) z = z.slice(2); else if (z.startsWith('0')) z = '49' + z.slice(1);
  return z.length >= 8 ? (plus ? '+' : '') + z : '';
}

/**
 * Knopf „Bestätigung senden“, nur wenn ein Termin feststeht.
 * @param {string} basis '/api/vertrieb' oder '/api/admin'
 * @param {any} l der Lead
 * @param {{start: string, art: string}|null} termin
 * @param {string} absender Name unter der Nachricht
 */
export function bestaetigungKnopf(basis, lid, l, termin, absender) {
  if (!termin) return '';
  return h('button', { class: 'btn sec small', onclick: () => oeffnen(basis, lid, l, termin, absender) }, '✉ Bestätigung senden');
}

function oeffnen(basis, lid, l, termin, absender) {
  const d = new Date(termin.start);
  const tag = d.toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'Europe/Berlin' });
  const uhr = d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Berlin' });
  const anrede = l.ansprechpartner ? 'Guten Tag ' + l.ansprechpartner + ',' : 'Guten Tag,';
  const was = termin.art === 'erstgespraech' ? 'unser Gespräch ist am ' + tag + ' um ' + uhr + ' Uhr. Ich rufe Sie dann an.' : 'wie besprochen rufe ich Sie am ' + tag + ' um ' + uhr + ' Uhr an.';
  const text = h('textarea', { rows: 6, 'aria-label': 'Nachricht', maxlength: 1000 }, anrede + '\n' + was + ' Passt das noch? Falls nicht, antworten Sie mir einfach kurz.\n\nViele Grüße\n' + (absender || 'Ihr Markentrix-Team') + '\nMarkentrix');
  const m = h('div');
  const vermerk = (kanal) => api(basis + '/leads/' + lid + '/aktivitaet', { method: 'POST', body: { art: 'notiz', inhalt: 'Terminbestätigung per ' + kanal + ' vorbereitet (' + tag + ', ' + uhr + ' Uhr)' } }).catch(() => {});
  const los = (kanal, url) => { window.open(url, '_blank', 'noopener'); vermerk(kanal); melde(m, kanal + ' wurde geöffnet. Dort noch auf „Senden“ tippen. Im Verlauf vermerkt.', 'ok'); };
  const wa = nummer(l.telefon, false), sms = nummer(l.telefon, true);
  dialog('Terminbestätigung', h('div', { class: 'stack' },
    h('p', { class: 'small muted' }, 'Termin: ' + tag + ', ' + uhr + ' Uhr. Den Text kannst du ändern. Gesendet wird erst in der geöffneten App. Nur an Leads schicken, mit denen du schon gesprochen hast.'),
    text,
    h('div', { class: 'row', style: 'flex-wrap:wrap;gap:8px' },
      wa ? h('button', { class: 'btn', onclick: () => los('WhatsApp', 'https://wa.me/' + wa + '?text=' + encodeURIComponent(text.value)) }, 'WhatsApp') : '',
      sms ? h('button', { class: 'btn', onclick: () => los('SMS', 'sms:' + sms + '?&body=' + encodeURIComponent(text.value)) }, 'SMS') : '',
      l.email ? h('button', { class: 'btn', onclick: () => los('E-Mail', 'mailto:' + l.email + '?subject=' + encodeURIComponent('Unser Telefontermin') + '&body=' + encodeURIComponent(text.value)) }, 'E-Mail') : ''),
    !wa && !l.email ? h('p', { class: 'small muted' }, 'Für diesen Lead fehlen Telefonnummer und E-Mail-Adresse.') : '', m));
}
