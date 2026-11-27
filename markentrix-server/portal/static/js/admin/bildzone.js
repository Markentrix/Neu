import { h, api, melde } from '../common.js';
import { bildVorbereiten } from '../bildlesen.js';

/** Aus Screenshot ausfüllen (Kunde oder Lead): Datei wählen, ins Fenster ziehen oder mit Strg+V einfügen. Das Bild wird nicht gespeichert, die Felder werden nur vorausgefüllt. */
export function bildZone(f, m, was = 'den Kunden') {
  const lesen = async (bild) => {
    if (!bild || !/^image\//.test(bild.type)) { melde(m, 'Bitte ein Bild (Screenshot oder Foto) wählen.'); return; }
    melde(m, 'Das Bild wird gelesen …', 'info');
    try {
      const r = await api('/api/admin/kunden/aus-bild', { method: 'POST', body: { typ: 'image/jpeg', daten: await bildVorbereiten(bild) } });
      for (const [k, w] of Object.entries(r.felder)) {
        const el = /** @type {HTMLInputElement|null} */ (f.elements.namedItem(k) || (k === 'website' ? f.elements.namedItem('domain') : null));
        if (el && w) el.value = /** @type {string} */ (w);
      }
      m.replaceChildren(h('div', { class: 'msg ok' }, r.info), r.hinweis ? h('div', { class: 'msg info' }, 'Achtung: ' + r.hinweis) : '');
      f.scrollIntoView({ behavior: 'smooth' });
    } catch (x) { melde(m, x.message); }
  };
  const datei = /** @type {HTMLInputElement} */ (h('input', { type: 'file', accept: 'image/*', hidden: true, 'aria-label': 'Screenshot wählen' }));
  datei.onchange = async () => { await lesen(datei.files && datei.files[0]); datei.value = ''; };
  const zone = h('div', { class: 'card', style: 'border:2px dashed var(--line,#c8d0dc);text-align:center' },
    h('p', {}, h('b', {}, 'Aus Screenshot ausfüllen')),
    h('p', { class: 'small muted' }, 'Impressum, Visitenkarte oder Webseite: Bild hierher ziehen, mit Strg+V einfügen oder auswählen. Die Felder werden vorausgefüllt, Sie prüfen und legen ' + was + ' selbst an. Das Bild wird nicht gespeichert.'),
    h('p', {}, h('button', { class: 'btn sec', type: 'button', onclick: () => datei.click() }, 'Bild auswählen')), datei);
  zone.addEventListener('dragover', (e) => { e.preventDefault(); });
  zone.addEventListener('drop', (e) => { e.preventDefault(); lesen(e.dataTransfer && e.dataTransfer.files[0]); });
  const einfuegen = (e) => {
    const t = /** @type {HTMLElement} */ (e.target);
    const bild = Array.from((e.clipboardData && e.clipboardData.files) || []).find(x => /^image\//.test(x.type));
    if (bild && !(t && t.tagName === 'TEXTAREA')) { e.preventDefault(); lesen(bild); }
  };
  document.addEventListener('paste', einfuegen);
  window.addEventListener('hashchange', () => document.removeEventListener('paste', einfuegen), { once: true });
  return zone;
}
