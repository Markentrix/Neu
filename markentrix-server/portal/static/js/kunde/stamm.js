import { h, api, melde, toast, datum } from '../common.js';
import { V, zeige } from './kern.js';
import { manuellDialog } from './kalender.js';

/** Stammkunden: wer kommt wie oft, mit eigener Notiz je Person. Aus den Terminen zusammengestellt. */
V.stamm = async () => {
  const stand = V.stamm.stand || (V.stamm.stand = { q: '' });
  const r = await api('/api/kunde/website-dienste/stamm?q=' + encodeURIComponent(stand.q));
  const m = h('div');
  const suche = h('input', { type: 'search', value: stand.q, placeholder: 'Name, E-Mail oder Telefon suchen', 'aria-label': 'Stammkunden suchen', maxlength: 80 });
  suche.addEventListener('keydown', (e) => { if (e.key === 'Enter') { stand.q = suche.value.trim(); zeige(); } });
  const karte = (p) => {
    const notiz = h('textarea', { rows: 2, maxlength: 1000, placeholder: 'Notiz, z. B. Allergie, Wunschfarbe, Fahrzeug', 'aria-label': 'Notiz zu ' + p.name }, p.notiz);
    const speichern = async () => { try { await api('/api/kunde/website-dienste/stamm/notiz', { method: 'PUT', body: { schluessel: p.schluessel, notiz: notiz.value } }); toast('Notiz gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } };
    return h('div', { class: 'card', style: 'margin:8px 0' },
      h('p', {}, h('b', {}, p.name), ' ', p.nicht_erschienen ? h('span', { class: 'pill warn' }, p.nicht_erschienen + '× nicht erschienen') : '', p.kommend ? h('span', { class: 'pill ok', style: 'margin-left:6px' }, 'nächster Termin ' + datum(p.naechster)) : ''),
      h('p', { class: 'small' }, [p.telefon, p.email].filter(Boolean).join(' · ') || 'keine Kontaktdaten'),
      h('p', { class: 'small muted' }, p.besuche + ' Besuch' + (p.besuche === 1 ? '' : 'e') + (p.letzter ? ', zuletzt ' + datum(p.letzter) : '') + (p.abgesagt ? ' · ' + p.abgesagt + ' abgesagt' : '')),
      notiz,
      h('div', { class: 'row', style: 'gap:8px;margin-top:6px' }, h('button', { class: 'btn sec', onclick: speichern }, 'Notiz speichern'),
        h('button', { class: 'btn', onclick: () => manuellDialog({ name: p.name, telefon: p.telefon, email: p.email }, zeige) }, 'Termin eintragen')));
  };
  return h('div', { class: 'stack' }, h('div', { class: 'top' }, h('h1', {}, 'Stammkunden')),
    h('p', { class: 'small muted' }, 'Alle Personen, die bei dir gebucht haben, aus den Terminen zusammengestellt (gleiche E-Mail oder Telefonnummer = dieselbe Person). Die Notizen siehst nur du und dein Team.'),
    m, h('div', { class: 'row', style: 'gap:8px' }, suche, h('button', { class: 'btn', onclick: () => { stand.q = suche.value.trim(); zeige(); } }, 'Suchen')),
    r.personen.length ? r.personen.map(karte) : h('p', { class: 'muted' }, stand.q ? 'Niemand gefunden.' : 'Noch keine Buchungen. Sobald jemand bei dir bucht oder du einen Termin einträgst, erscheint die Person hier.'),
    r.gesamt > r.personen.length ? h('p', { class: 'small muted' }, 'Es werden die ersten ' + r.personen.length + ' von ' + r.gesamt + ' angezeigt. Mit der Suche findest du alle.') : '');
};
