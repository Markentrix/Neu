import { h } from './common.js';

/** Karte „Nächster Schritt“ für einen Lead. `aktionen` = { anrufen: href|fn, terminvorschlag: fn, mail: fn } je nach Oberfläche; fehlt eine, steht nur der Text da. */
export function schrittKarte(s, aktionen = {}) {
  if (!s) return '';
  const symbol = { anrufen: '📞', mail: '✉️', terminvorschlag: '📅', kalender: '🗓️', daten: '📝', warten: '⏳' }[s.aktion] || '➡️';
  const a = aktionen[s.aktion];
  const knopf = a ? (typeof a === 'string'
    ? h('a', { class: 'btn', href: a }, s.aktion === 'anrufen' ? 'Jetzt anrufen' : 'Öffnen')
    : h('button', { class: 'btn', type: 'button', onclick: a }, s.aktion === 'terminvorschlag' ? 'Termine vorschlagen' : 'Weiter')) : '';
  return h('div', { class: 'card', style: 'border-left:4px solid var(--accent,#2563eb)' },
    h('div', { class: 'row', style: 'align-items:center;gap:12px' }, h('span', { 'aria-hidden': 'true', style: 'font-size:24px' }, symbol),
      h('div', { class: 'grow' }, h('div', { class: 'small muted' }, 'Nächster Schritt'), h('b', {}, s.text), h('div', { class: 'small muted' }, s.grund)), knopf));
}
