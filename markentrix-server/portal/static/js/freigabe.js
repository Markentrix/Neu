import { api, melde, h, el, zeit } from './common.js';
const token = new URLSearchParams(location.search).get('t') || '';
const m = el('m'), inhalt = el('inhalt'), titel = el('titel');
const ART = { social: 'Social-Media-Beitrag', text: 'Text', angebot: 'Angebot', design: 'Design', website: 'Website', sonstiges: 'Sonstiges' };

function anhaenge(d) {
  if (!d.dateien.length) return '';
  return h('div', { class: 'stack' }, d.dateien.map(x => {
    const url = '/api/freigabe-link/' + encodeURIComponent(token) + '/datei/' + x.id;
    return h('div', {}, String(x.mime).startsWith('image/') ? h('img', { src: url, alt: x.name, style: 'max-width:100%;border-radius:10px;display:block;margin-bottom:6px' }) : '',
      h('a', { class: 'dateilink', href: url, target: '_blank', rel: 'noopener' }, '📎 ' + x.name));
  }));
}

function entscheidung(d) {
  const name = h('input', { placeholder: 'Ihr Vor- und Nachname', maxlength: 200, autocomplete: 'name', 'aria-label': 'Ihr Name' });
  const kom = h('textarea', { rows: 3, maxlength: 2000, placeholder: 'Kommentar (bei „Änderung wünschen“ bitte kurz beschreiben, was angepasst werden soll)', 'aria-label': 'Kommentar' });
  const los = async (e) => { try { await api('/api/freigabe-link/' + encodeURIComponent(token) + '/entscheiden', { method: 'POST', body: { entscheidung: e, name: name.value, kommentar: kom.value } }); laden(); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'stack' }, h('label', {}, 'Ihr Name (wird als Nachweis festgehalten)'), name, kom,
    h('div', { class: 'row' }, h('button', { class: 'btn', onclick: () => los('freigegeben') }, 'Freigeben'), h('button', { class: 'btn sec', onclick: () => los('abgelehnt') }, 'Änderung wünschen')));
}

async function laden() {
  let d;
  try { d = await api('/api/freigabe-link/' + encodeURIComponent(token)); } catch (x) { inhalt.replaceChildren(h('div', { class: 'msg err' }, x.message)); return; }
  m.replaceChildren();
  titel.textContent = d.titel + (d.version > 1 ? ' (Version ' + d.version + ')' : '');
  const teile = [h('p', { class: 'muted small', style: 'text-align:center;margin-top:-6px' }, (ART[d.art] || d.art) + ' · für ' + d.firma + ' · angefragt am ' + zeit(d.angefragt_am))];
  if (d.vorgaenger_kommentar) teile.push(h('div', { class: 'msg info' }, 'Ihr Änderungswunsch zur vorherigen Version: „' + d.vorgaenger_kommentar + '“'));
  if (d.inhalt) teile.push(h('div', { class: 'freitext', style: 'white-space:pre-line' }, d.inhalt));
  teile.push(anhaenge(d));
  if (d.status === 'wartet') teile.push(d.abgelaufen ? h('div', { class: 'msg warn' }, 'Der Link ist abgelaufen. Bitte melden Sie sich im Portal an oder fragen Sie bei uns nach einem neuen Link.') : entscheidung(d));
  else teile.push(h('div', { class: 'msg ' + (d.status === 'freigegeben' ? 'ok' : 'info') }, (d.status === 'freigegeben' ? 'Freigegeben' : d.status === 'abgelehnt' ? 'Änderung gewünscht' : 'Zurückgezogen') + (d.entschieden_am ? ' am ' + zeit(d.entschieden_am) + (d.entschieden_name ? ' von ' + d.entschieden_name : '') : '') + (d.kommentar ? ': „' + d.kommentar + '“' : '') + '. Vielen Dank!'));
  inhalt.replaceChildren(...teile);
}
laden();
