// Gemeinsame Helfer. Es wird nie innerHTML mit Daten benutzt – nur textContent.
export function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'value') e.value = v;
    else if (v === true) e.setAttribute(k, '');
    else e.setAttribute(k, v);
  }
  for (const c of kids.flat()) {
    if (c === null || c === undefined || c === false) continue;
    e.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return e;
}
export async function api(path, opt = {}) {
  const o = { method: opt.method || 'GET', headers: { 'X-MK': '1' }, credentials: 'same-origin' };
  if (opt.body instanceof FormData) o.body = opt.body;
  else if (opt.body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(opt.body); }
  let r;
  try { r = await fetch(path, o); } catch (e) { throw new Error('Keine Verbindung zum Server.'); }
  let d = null;
  try { d = await r.json(); } catch (e) { /* leer */ }
  if (r.status === 401 && !opt.leise && !path.includes('/login')) { location.href = '/'; throw new Error('Bitte neu anmelden.'); }
  if (!r.ok) {
    let t = d && d.detail;
    if (Array.isArray(t)) t = 'Bitte die Eingaben prüfen.';
    throw new Error(t || 'Fehler ' + r.status);
  }
  return d;
}
export const datum = (s) => s ? new Date(s).toLocaleDateString('de-DE') : '';
export const zeit = (s) => s ? new Date(s).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }) : '';
export const euro = (c) => c === null || c === undefined ? '' : (c / 100).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
export const groesse = (b) => b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
export function melde(box, text, art = 'err') {
  box.replaceChildren(text ? h('div', { class: 'msg ' + art }, text) : '');
}
export async function abmelden() {
  try { await api('/api/logout', { method: 'POST' }); } catch (e) { /* egal */ }
  location.href = '/';
}
export function sparkline(werte, farbe = '#8B5CF6') {
  const ns = 'http://www.w3.org/2000/svg', w = 280, hh = 46, max = Math.max(1, ...werte);
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${hh}`); svg.setAttribute('class', 'spark'); svg.setAttribute('preserveAspectRatio', 'none');
  const bw = w / werte.length;
  werte.forEach((v, i) => {
    const r = document.createElementNS(ns, 'rect'), bh = Math.max(2, (v / max) * (hh - 4));
    r.setAttribute('x', i * bw + 2); r.setAttribute('y', hh - bh); r.setAttribute('width', Math.max(2, bw - 4));
    r.setAttribute('height', bh); r.setAttribute('rx', 3); r.setAttribute('fill', farbe); r.setAttribute('opacity', v ? '1' : '.25');
    svg.append(r);
  });
  return svg;
}
