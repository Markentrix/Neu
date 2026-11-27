import { h, api, datum, melde } from '../common.js';
import { V, zeige } from './kern.js';

const tagText = (d) => new Date(d + 'T12:00:00').toLocaleDateString('de-DE', { weekday: 'long', day: '2-digit', month: 'long' });
const wann = (iso) => new Date(iso).toLocaleString('de-DE', { weekday: 'long', day: '2-digit', month: 'long', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Berlin' }) + ' Uhr';

/** Beratungsgespräch mit Markentrix selbst buchen: freie Zeiten wählen, Bestätigung und Kalendereinladung kommen per Mail. */
V.beratung = async () => {
  const d = await api('/api/kunde/beratung'), m = h('div');
  if (d.meine.length) {
    return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Ihr Beratungsgespräch'),
      d.meine.map(g => h('p', {}, h('b', {}, wann(g.start)), h('br'), h('span', { class: 'muted small' }, d.ort), h('br'),
        h('a', { class: 'btn sec small', href: g.absagen }, 'Termin absagen'))),
      h('p', { class: 'small muted' }, 'Die Bestätigung mit Kalendereinladung haben Sie per E-Mail bekommen.')));
  }
  if (!d.aktiv || !d.tage.length) return h('div', { class: 'card' }, h('h2', {}, 'Beratungsgespräch'), h('p', { class: 'muted' }, 'Im Moment sind keine freien Zeiten da. Bitte schreiben Sie uns kurz eine Nachricht, wir melden uns.'), h('p', {}, h('a', { class: 'btn', href: '#nachrichten' }, 'Nachricht schreiben')));
  const text = h('textarea', { rows: 2, maxlength: 1500, placeholder: 'Worum soll es gehen? (optional)', 'aria-label': 'Worum soll es gehen' });
  const buchen = async (s, b) => {
    b.disabled = true; melde(m, '');
    try { const r = await api('/api/kunde/beratung', { method: 'POST', body: { start: s.start, nachricht: text.value || null } }); melde(m, 'Vielen Dank, Ihr Termin am ' + r.wann + ' ist gebucht. Die Bestätigung kommt per E-Mail.', 'ok'); setTimeout(zeige, 1500); }
    catch (x) { melde(m, x.message); b.disabled = false; if (/nicht mehr frei/.test(x.message)) setTimeout(zeige, 1200); }
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Beratungsgespräch buchen'), h('p', { class: 'muted' }, `Ca. ${d.dauer} Minuten. ${d.ort}`), text, m,
    d.tage.map(t => h('div', {}, h('p', { style: 'margin:14px 0 6px;font-weight:600' }, tagText(t.datum)),
      h('div', { class: 'row', style: 'flex-wrap:wrap;gap:6px' }, t.slots.map(s => h('button', { class: 'btn sec small', type: 'button', onclick: (e) => buchen(s, e.currentTarget) }, s.uhr))))));
};

/** Alle Unterlagen von Markentrix an einem Ort, mit Suche und Filter. */
V.ablage = async () => {
  const liste = await api('/api/kunde/ablage');
  const q = h('input', { type: 'search', placeholder: 'Suchen: Rechnungsnummer, Titel …', 'aria-label': 'Unterlagen durchsuchen' });
  const arten = [...new Set(liste.map(x => x.art))];
  const art = h('select', { 'aria-label': 'Art der Unterlage' }, h('option', { value: '' }, 'Alle Arten'), arten.map(a => h('option', { value: a }, a)));
  const box = h('div', { class: 'stack' });
  const zeichnen = () => {
    const s = q.value.trim().toLowerCase(), a = art.value;
    const treffer = liste.filter(x => (!a || x.art === a) && (!s || (x.titel + ' ' + x.art).toLowerCase().includes(s)));
    box.replaceChildren(...(treffer.length ? treffer.map(x => h('div', { class: 'row', style: 'align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--line,#e5e7eb)' },
      h('span', { class: 'pill' }, x.art), h('div', { class: 'grow' }, x.titel, h('div', { class: 'small muted' }, x.datum ? datum(x.datum) : '')),
      h('a', { class: 'btn sec small', href: x.link, target: '_blank', rel: 'noopener' }, 'Öffnen'))) : [h('p', { class: 'muted' }, liste.length ? 'Nichts gefunden.' : 'Noch keine Unterlagen vorhanden.')]));
  };
  q.addEventListener('input', zeichnen); art.addEventListener('change', zeichnen); zeichnen();
  return h('div', { class: 'card' }, h('h2', {}, 'Dokumente von Markentrix'), h('div', { class: 'row', style: 'gap:8px;margin-bottom:10px' }, h('div', { class: 'grow' }, q), art), box);
};
