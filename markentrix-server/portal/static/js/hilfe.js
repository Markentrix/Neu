import { h, dialog, api } from './common.js';
/** Artikel kommen vom Server (app/hilfe/<rolle>.json), dieselbe Quelle wie die PDF-Anleitung. */
const ARTIKEL = {};
async function laden(rolle) {
  if (!ARTIKEL[rolle]) { try { ARTIKEL[rolle] = (await api('/api/hilfe/artikel?rolle=' + rolle, { leise: true })).artikel || []; } catch { ARTIKEL[rolle] = []; } }
  return ARTIKEL[rolle];
}
const norm = (t) => String(t).toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss').replace(/[^a-z0-9 ]/g, ' ');
const STOPP = new Set(['wie', 'wo', 'was', 'ich', 'mein', 'meine', 'meinen', 'meinem', 'meiner', 'muss', 'kann', 'ein', 'eine', 'einen', 'der', 'die', 'das', 'den', 'dem', 'und', 'oder', 'fuer', 'von', 'zu', 'im', 'in', 'ist', 'mit', 'wofuer', 'welche', 'wann', 'wird', 'bei', 'auf', 'an']);
const woerter = (t) => norm(t).split(/\s+/).filter(w => w.length > 1 && !STOPP.has(w));
/** Prefix-Vergleich beidseitig, damit „anlegen“ auch „angelegt“, „Leads“ auch „Lead“ trifft. */
const passt = (w, x) => w === x || (w.length >= 4 && x.length >= 4 && (x.startsWith(w.slice(0, Math.max(4, w.length - 2))) || w.startsWith(x.slice(0, Math.max(4, x.length - 2)))));

export function suchen(rolle, frage) {
  const q = woerter(frage);
  if (!q.length) return [];
  return (ARTIKEL[rolle] || []).map(a => {
    const titel = woerter(a.t), kw = woerter(a.k), text = woerter(a.wo + ' ' + a.s.join(' ') + ' ' + (a.n || []).join(' '));
    let punkte = 0, treffer = 0;
    for (const w of q) {
      const p = titel.some(x => passt(w, x)) ? 5 : kw.some(x => passt(w, x)) ? 3 : text.some(x => passt(w, x)) ? 1 : 0;
      if (p) treffer++; punkte += p;
    }
    return { a, punkte: treffer === q.length ? punkte * 2 : punkte };
  }).filter(x => x.punkte > 0).sort((x, y) => y.punkte - x.punkte).map(x => x.a);
}

function artikelKarte(a, frage) {
  return h('div', { class: 'stack' },
    h('p', { class: 'small muted' }, 'Wo: ' + a.wo),
    a.bild ? h('figure', { style: 'margin:0' }, h('img', { src: a.bild, alt: 'So sieht die Seite „' + a.t + '“ aus (Beispieldaten)', loading: 'lazy', style: 'max-width:100%;border:1px solid var(--line);border-radius:10px', onerror: (e) => e.target.closest('figure').remove() }), h('figcaption', { class: 'small muted' }, 'So sieht die Seite aus (Beispieldaten).')) : '',
    h('ol', {}, a.s.map(x => h('li', { style: 'margin:6px 0' }, x))),
    a.n && a.n.length ? h('div', { class: 'msg' }, h('b', {}, 'Gut zu wissen'), h('ul', {}, a.n.map(x => h('li', {}, x)))) : '',
    a.l ? h('p', {}, h('a', { class: 'btn', href: a.l }, 'Dorthin gehen')) : '', rueckfrage(frage, a.t));
}

/** „Hat das geholfen?“ Bei Nein geht die Frage mit Text an den Admin. */
function rueckfrage(frage, artikel, direkt = false) {
  const box = h('div', { class: 'card', style: 'margin-top:12px' });
  const senden = async (geloest, text) => {
    try { await api('/api/hilfe/rueckmeldung', { method: 'POST', body: { frage, artikel: artikel || null, geloest, text: text || null } }); return true; }
    catch (x) { box.append(h('div', { class: 'msg err' }, x.message)); return false; }
  };
  const start = () => box.replaceChildren(h('b', {}, 'Ist dein Problem damit gelöst?'),
    h('p', {}, h('button', { class: 'btn', onclick: async () => { if (await senden(true)) box.replaceChildren(h('div', { class: 'msg ok' }, 'Schön, danke für die Rückmeldung.')); } }, 'Ja, gelöst'), ' ',
      h('button', { class: 'btn sec', onclick: nein }, 'Nein, noch nicht')));
  const nein = () => {
    const t = h('textarea', { rows: 3, style: 'width:100%', 'aria-label': 'Was klappt nicht?', placeholder: 'Was klappt nicht? Bitte kurz beschreiben, dann meldet sich das Team.' });
    box.replaceChildren(h('b', {}, 'Das tut uns leid.'), h('p', { class: 'small muted' }, 'Wir geben deine Frage direkt an das Markentrix-Team weiter.'), t,
      h('p', {}, h('button', { class: 'btn', onclick: async () => { if (await senden(false, t.value)) box.replaceChildren(h('div', { class: 'msg ok' }, 'Danke, das Team wurde informiert und meldet sich bei dir.')); } }, 'An das Team senden')));
  };
  if (direkt) nein(); else start();
  return box;
}

/** Schwebender „?“-Knopf auf jeder Seite: öffnet die Anleitung (mit Bild) zur gerade offenen Seite, sonst die Suche. */
function hilfeKnopf(rolle) {
  if (typeof document === 'undefined' || document.getElementById('hilfeknopf')) return;
  const knopf = h('button', { id: 'hilfeknopf', class: 'hilfeknopf', type: 'button', 'aria-label': 'Hilfe zu dieser Seite', title: 'Hilfe zu dieser Seite', onclick: async () => {
    const liste = await laden(rolle), seite = location.hash.replace(/^#/, '').split('/')[0] || 'heute';
    const passend = liste.filter(a => (a.l || '').replace(/^#/, '') === seite);
    if (passend.length === 1) { dialog(passend[0].t, artikelKarte(passend[0], passend[0].t)); return; }
    const feld = h('input', { type: 'search', placeholder: 'Wobei brauchst du Hilfe?', 'aria-label': 'Hilfe durchsuchen' }), ergebnis = h('div', { class: 'stack' });
    const zeige = () => {
      const t = feld.value.trim() ? suchen(rolle, feld.value) : passend;
      ergebnis.replaceChildren(...(t.length ? t.slice(0, 8).map(a => h('button', { class: 'btn sec', style: 'display:block;width:100%;text-align:left', onclick: () => { d.zu(); dialog(a.t, artikelKarte(a, feld.value.trim() || a.t)); } }, a.t))
        : [h('p', { class: 'small muted' }, 'Dazu habe ich keine Anleitung gefunden. Versuche ein anderes Wort.')]));
    };
    feld.addEventListener('input', zeige);
    const d = dialog('Hilfe' + (passend.length ? ' zu dieser Seite' : ''), h('div', { class: 'stack' }, feld, ergebnis, h('p', { class: 'small' }, h('a', { href: '/api/hilfe/anleitung.pdf?rolle=' + rolle, target: '_blank', rel: 'noopener' }, '📄 Ganze Anleitung als PDF'))));
    zeige(); feld.focus();
  } }, '?');
  document.body.append(knopf);
}

/** Suchfeld für die Kopfzeile eines Portals. rolle: 'vertrieb' | 'kunde' | 'admin'. */
export function hilfeSuche(rolle) {
  laden(rolle); hilfeKnopf(rolle);
  const feld = h('input', { type: 'search', placeholder: 'Hilfe: Frage eingeben, z. B. „Leads anlegen“', 'aria-label': 'Hilfe durchsuchen', style: 'width:100%' });
  const liste = h('div', { class: 'hilfetreffer', role: 'list' });
  const pdfLinks = (rolle === 'admin' ? [['vertrieb', 'Vertrieb'], ['kunde', 'Kunden'], ['admin', 'Admin']] : [[rolle, '']])
    .map(([r, n]) => h('a', { href: '/api/hilfe/anleitung.pdf?rolle=' + r, target: '_blank', rel: 'noopener', style: 'margin-right:12px' }, '📄 Anleitung' + (n ? ' ' + n : '') + ' als PDF'));
  const box = h('div', { class: 'hilfesuche', style: 'position:relative;margin:0 0 12px' }, feld, liste, h('p', { class: 'small', style: 'margin:4px 0 0' }, pdfLinks));
  const zeigeArtikel = (a) => { const frage = feld.value.trim(); liste.replaceChildren(); feld.value = ''; dialog(a.t, artikelKarte(a, frage || a.t)); };
  feld.addEventListener('input', async () => {
    await laden(rolle);
    const t = suchen(rolle, feld.value);
    if (!feld.value.trim()) { liste.replaceChildren(); return; }
    liste.replaceChildren(h('div', { class: 'card', style: 'padding:6px;margin-top:4px' },
      t.length ? t.slice(0, 6).map(a => h('button', { class: 'btn sec', style: 'display:block;width:100%;text-align:left;margin:3px 0', onclick: () => zeigeArtikel(a) }, a.t))
        : h('div', { style: 'margin:6px' }, h('p', { class: 'small muted' }, 'Dazu habe ich keine Anleitung gefunden. Versuche ein anderes Wort oder gib die Frage direkt an das Team.'),
          h('button', { class: 'btn small', onclick: () => { const frage = feld.value.trim(); liste.replaceChildren(); feld.value = ''; dialog('Frage an das Team', h('div', { class: 'stack' }, h('p', {}, h('b', {}, frage)), rueckfrage(frage, null, true))); } }, 'Frage an das Team senden'))));
  });
  feld.addEventListener('keydown', async (e) => { if (e.key === 'Enter') { await laden(rolle); const t = suchen(rolle, feld.value); if (t[0]) zeigeArtikel(t[0]); } if (e.key === 'Escape') { feld.value = ''; liste.replaceChildren(); } });
  return box;
}
