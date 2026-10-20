// Einfache SVG-Diagramme ohne Fremdbibliothek (CSP: nur eigene Skripte). Jedes Diagramm hat Textbeschreibung und eine Tabelle als Alternative.
import { h } from './common.js';

const NS = 'http://www.w3.org/2000/svg';
const svg = (tag, attr = {}, ...kinder) => { const e = document.createElementNS(NS, tag); Object.entries(attr).forEach(([k, v]) => e.setAttribute(k, String(v))); kinder.forEach(k => e.append(k)); return e; };
const farbe = (i) => 'var(--c' + (i % 6 + 1) + ')';
const nice = (max) => { if (max <= 4) return 4; const s = Math.pow(10, Math.floor(Math.log10(max / 4))); const f = [1, 2, 5, 10].find(x => x * s * 4 >= max); return f * s * 4; };

export function tabellenAlternative(kopf, zeilen, titel = 'Zahlen als Tabelle') {
  return h('details', { class: 'chartalt' }, h('summary', {}, titel), h('div', { class: 'tablewrap' }, h('table', {}, h('thead', {}, h('tr', {}, kopf.map(k => h('th', {}, k)))), h('tbody', {}, zeilen.map(z => h('tr', {}, z.map(c => h('td', {}, String(c)))))))));
}

/** Liniendiagramm. reihen: [{ name, daten: number[] }], labels: string[] (gleiche Länge). */
export function liniendiagramm(labels, reihen, beschreibung) {
  const W = 640, H = 220, L = 34, R = 10, T = 12, B = 26, max = nice(Math.max(1, ...reihen.flatMap(r => r.daten)));
  const x = (i) => L + (labels.length > 1 ? i * (W - L - R) / (labels.length - 1) : 0), y = (v) => T + (H - T - B) * (1 - v / max);
  const g = svg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img', 'aria-label': beschreibung, preserveAspectRatio: 'xMidYMid meet' }, svg('title', {}, ''));
  g.firstChild.textContent = beschreibung;
  for (let i = 0; i <= 4; i++) { const v = max * i / 4, yy = y(v); g.append(svg('line', { x1: L, x2: W - R, y1: yy, y2: yy, class: 'gitter' }), Object.assign(svg('text', { x: L - 6, y: yy + 4, class: 'achse', 'text-anchor': 'end' }), { textContent: String(Math.round(v * 10) / 10) })); }
  const schritt = Math.max(1, Math.ceil(labels.length / 8));
  labels.forEach((l, i) => { if (i % schritt === 0 || (i === labels.length - 1 && (labels.length - 1) % schritt >= Math.ceil(schritt / 2))) g.append(Object.assign(svg('text', { x: x(i), y: H - 6, class: 'achse', 'text-anchor': i === 0 ? 'start' : i === labels.length - 1 ? 'end' : 'middle' }), { textContent: l })); });
  reihen.forEach((r, k) => {
    const pts = r.daten.map((v, i) => x(i) + ',' + y(v)).join(' ');
    if (k === 0) g.append(svg('polygon', { points: `${x(0)},${y(0)} ${pts} ${x(labels.length - 1)},${y(0)}`, fill: farbe(0), opacity: '.10' }));
    g.append(svg('polyline', { points: pts, fill: 'none', stroke: farbe(k), 'stroke-width': 2.5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', ...(k ? { 'stroke-dasharray': '6 4' } : {}) }));
    const li = r.daten.length - 1; g.append(svg('circle', { cx: x(li), cy: y(r.daten[li]), r: 4, fill: farbe(k) }));
  });
  const legende = h('div', { class: 'legende' }, reihen.map((r, k) => h('span', {}, h('i', { class: 'swatch', style: 'background:' + farbe(k) }), r.name)));
  return h('figure', { class: 'chartbox' }, g, legende);
}

/** Ring. teile: [{ name, wert }]. Legende nennt Zahl und Prozent, Farbe ist nie der einzige Hinweis. */
export function ringdiagramm(teile, beschreibung, mitte = '') {
  const summe = teile.reduce((a, t) => a + t.wert, 0) || 1, R = 15.9155, g = svg('svg', { viewBox: '0 0 42 42', class: 'ring', role: 'img', 'aria-label': beschreibung });
  g.append(svg('circle', { cx: 21, cy: 21, r: R, fill: 'none', stroke: 'var(--line)', 'stroke-width': 6 }));
  let off = 25;
  teile.forEach((t, i) => { const p = 100 * t.wert / summe; if (p > 0) g.append(svg('circle', { cx: 21, cy: 21, r: R, fill: 'none', stroke: farbe(i), 'stroke-width': 6, 'stroke-dasharray': `${Math.max(0, p - 0.6)} ${100 - Math.max(0, p - 0.6)}`, 'stroke-dashoffset': off })); off -= p; });
  if (mitte) g.append(Object.assign(svg('text', { x: 21, y: 22.5, 'text-anchor': 'middle', class: 'ringmitte' }), { textContent: mitte }));
  return h('figure', { class: 'ringbox' }, g, h('ul', { class: 'legende senkrecht' }, teile.map((t, i) => h('li', {}, h('i', { class: 'swatch', style: 'background:' + farbe(i) }), h('span', {}, t.name), h('b', {}, t.wert + ' (' + Math.round(100 * t.wert / summe) + ' %)')))));
}

/** Trichter: Stufen von oben nach unten, mit Anteil zur vorherigen Stufe. stufen: [{ name, wert }] */
export function trichter(stufen, beschreibung) {
  const max = Math.max(1, stufen[0] ? stufen[0].wert : 1);
  return h('div', { class: 'dtrichter', role: 'img', 'aria-label': beschreibung }, stufen.map((s, i) => {
    const vor = i ? stufen[i - 1].wert : null;
    return h('div', { class: 'tstufe' }, h('div', { class: 'tname' }, s.name), h('div', { class: 'tbalken' }, h('div', { style: 'width:' + Math.max(2, 100 * s.wert / max) + '%;background:' + farbe(i === 0 ? 1 : i === stufen.length - 1 ? 3 : 0) })),
      h('div', { class: 'tzahl' }, h('b', {}, s.wert), vor ? h('span', { class: 'small muted' }, ' · ' + (vor ? Math.round(100 * s.wert / vor) : 0) + ' %') : ''));
  }));
}

/** Balken nebeneinander (z. B. Wochentage). */
export function balkendiagramm(labels, daten, beschreibung) {
  const W = 320, H = 130, B = 22, max = Math.max(1, ...daten), bw = W / labels.length;
  const g = svg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart klein', role: 'img', 'aria-label': beschreibung, preserveAspectRatio: 'xMidYMid meet' });
  const top = daten.indexOf(Math.max(...daten));
  daten.forEach((v, i) => { const bh = Math.max(2, (H - B - 14) * v / max); g.append(svg('rect', { x: i * bw + 6, y: H - B - bh, width: bw - 12, height: bh, rx: 4, fill: i === top && v ? farbe(0) : farbe(5), opacity: i === top && v ? 1 : .55 }),
    Object.assign(svg('text', { x: i * bw + bw / 2, y: H - 7, class: 'achse', 'text-anchor': 'middle' }), { textContent: labels[i] }), Object.assign(svg('text', { x: i * bw + bw / 2, y: H - B - bh - 4, class: 'achse', 'text-anchor': 'middle' }), { textContent: String(v) })); });
  return h('figure', { class: 'chartbox' }, g);
}
