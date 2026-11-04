import { h, api, melde, toast, dialog } from '../common.js';
import { V, kopf } from './kern.js';

const TZ = 'Europe/Berlin', WT = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
const heuteTag = () => new Date().toLocaleDateString('sv-SE', { timeZone: TZ });
const addTage = (tag, n) => { const d = new Date(tag + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const wochentag = (tag) => new Date(tag + 'T12:00:00Z').getUTCDay();
const montag = (tag) => addTage(tag, -((wochentag(tag) + 6) % 7));
const lokal = (iso) => new Date(iso).toLocaleString('sv-SE', { timeZone: TZ });             // „2026-11-05 14:30:00“
const tagVon = (iso) => lokal(iso).slice(0, 10), uhrVon = (iso) => lokal(iso).slice(11, 16);
const eingabe = (iso) => lokal(iso).slice(0, 16).replace(' ', 'T');                          // für <input type=datetime-local>
const kurz = (tag) => WT[wochentag(tag)] + ', ' + tag.slice(8, 10) + '.' + tag.slice(5, 7) + '.';
const feld = (label, el, tipp) => h('div', {}, h('label', {}, label), el, tipp ? h('div', { class: 'small muted' }, tipp) : '');

/** Ein Kalender-Ereignis in einheitlicher Form: { tag, sort, text, art, klick } */
function ereignisse(d, offen) {
  const liste = [];
  for (const g of d.gespraeche) liste.push({ tag: tagVon(g.start), sort: uhrVon(g.start), text: uhrVon(g.start) + ' ' + g.name, art: 'gespraech', klick: () => offen('gespraech', g) });
  for (const e of d.eintraege) {
    // Mehrtägige Einträge erscheinen an jedem Tag
    const von = tagVon(e.start), bis = addTage(tagVon(new Date(new Date(e.ende).getTime() - 1000).toISOString()), 0);
    for (let t = von, n = 0; t <= bis && n < 130; t = addTage(t, 1), n++) {
      liste.push({ tag: t, sort: e.ganztag ? '00:00' : (t === von ? uhrVon(e.start) : '00:00'), text: (e.ganztag ? 'ganztägig ' : t === von ? uhrVon(e.start) + ' ' : '') + e.titel, art: e.art, klick: () => offen('eintrag', e) });
    }
  }
  for (const l of d.wiedervorlagen) liste.push({ tag: l.wiedervorlage_am, sort: '99:99', text: '↻ ' + l.name, art: 'wv', klick: () => { location.hash = '#lead/' + l.id; } });
  return liste.sort((a, b) => a.sort.localeCompare(b.sort));
}
const ART = { gespraech: ['Erstgespräch', '#0e7490'], termin: ['Eigener Termin', '#4338ca'], sperre: ['Gesperrt', '#b42318'], wv: ['Wiedervorlage', '#475467'] };
const chip = (ev, voll) => h('button', { class: 'kalchip', type: 'button', onclick: ev.klick, style: 'border-left:4px solid ' + ART[ev.art][1], title: ART[ev.art][0] + ': ' + ev.text, 'aria-label': ART[ev.art][0] + ': ' + ev.text }, voll ? ev.text : ev.text.slice(0, 22));

function eintragDialog(e, danach) {
  const neu = !e.id, m = h('div'), ganz = h('input', { type: 'checkbox', style: 'width:auto', checked: !!e.ganztag });
  const art = h('select', {}, h('option', { value: 'termin', selected: e.art !== 'sperre' }, 'Eigener Termin (z. B. Anruf, Besprechung)'), h('option', { value: 'sperre', selected: e.art === 'sperre' }, 'Sperre (z. B. Urlaub, nicht erreichbar)'));
  const titel = h('input', { value: e.titel || '', maxlength: 200, required: true, 'aria-label': 'Titel' });
  const typ = () => ganz.checked ? 'date' : 'datetime-local';
  const von = h('input', { type: typ(), value: e.von || '', required: true, 'aria-label': 'Beginn' }), bis = h('input', { type: typ(), value: e.bis || '', required: true, 'aria-label': 'Ende' });
  const notiz = h('textarea', { rows: 2, maxlength: 1000, 'aria-label': 'Notiz' }, e.notiz || '');
  ganz.onchange = () => { const t = typ(); for (const i of [von, bis]) { const w = i.value.slice(0, 10); i.type = t; i.value = t === 'date' ? w : w ? w + (i === von ? 'T09:00' : 'T10:00') : ''; } };
  const dlg = dialog(neu ? 'Neuer Eintrag' : 'Eintrag bearbeiten', h('form', { onsubmit: async (ev) => {
    ev.preventDefault();
    const s = ganz.checked ? von.value + 'T00:00' : von.value, z = ganz.checked ? bis.value + 'T00:00' : bis.value;
    try {
      await api('/api/admin/kalender/eintraege' + (neu ? '' : '/' + e.id), { method: neu ? 'POST' : 'PUT', body: { art: art.value, titel: titel.value, start: s, ende: z, ganztag: ganz.checked, notiz: notiz.value || null } });
      dlg.zu(); toast('Gespeichert.', 'ok'); danach();
    } catch (x) { melde(m, x.message); }
  } }, m, feld('Art', art), feld('Titel', titel),
  h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, ganz, 'Ganztägig (mehrere Tage möglich)'),
  h('div', { class: 'form2' }, feld('Von', von), feld('Bis', bis)), feld('Notiz (freiwillig)', notiz),
  h('p', { class: 'small muted' }, 'In dieser Zeit sind auf der Website keine Erstgespräche buchbar.'),
  h('p', { class: 'row' }, h('button', { class: 'btn' }, 'Speichern'),
    neu ? '' : h('button', { class: 'btn danger', type: 'button', onclick: async () => { try { await api('/api/admin/kalender/eintraege/' + e.id, { method: 'DELETE' }); dlg.zu(); toast('Gelöscht.', 'ok'); danach(); } catch (x) { melde(m, x.message); } } }, 'Löschen'))));
}

function gespraechDialog(g, danach) {
  const m = h('div'), mail = h('input', { type: 'checkbox', checked: true, style: 'width:auto' });
  const neu = h('input', { type: 'datetime-local', value: eingabe(g.start), 'aria-label': 'Neuer Termin' }), grund = h('textarea', { rows: 2, maxlength: 500, placeholder: 'Kurze Erklärung für den Interessenten (freiwillig)', 'aria-label': 'Grund der Absage' });
  const mailBox = h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, mail, 'Interessenten per Mail informieren (mit neuer Kalendereinladung)');
  const dlg = dialog('Erstgespräch', h('div', {}, m,
    h('p', {}, h('b', {}, g.name), ' · ', kurz(tagVon(g.start)) + ', ' + uhrVon(g.start) + ' Uhr'),
    h('p', { class: 'small' }, h('a', { href: 'mailto:' + g.email }, g.email), g.telefon ? ' · ' : '', g.telefon ? h('a', { href: 'tel:' + g.telefon }, g.telefon) : ''),
    g.nachricht ? h('p', { class: 'small muted' }, '„' + g.nachricht + '“') : '',
    g.lead_id ? h('p', {}, h('a', { class: 'btn sec small', href: '#lead/' + g.lead_id, onclick: () => dlg.zu() }, 'Lead öffnen')) : '',
    h('h3', {}, 'Verschieben'), feld('Neuer Termin', neu), mailBox,
    h('p', {}, h('button', { class: 'btn', type: 'button', onclick: async () => {
      try { const r = await api('/api/admin/gespraeche/' + g.id + '/verschieben', { method: 'POST', body: { start: neu.value, mail: mail.checked } }); dlg.zu(); toast('Verschoben auf ' + r.wann + '.', 'ok'); danach(); } catch (x) { melde(m, x.message); }
    } }, 'Verschieben')),
    h('h3', {}, 'Absagen'), grund,
    h('p', {}, h('button', { class: 'btn danger', type: 'button', onclick: async () => {
      if (!confirm('Dieses Gespräch wirklich absagen?')) return;
      try { await api('/api/admin/gespraeche/' + g.id + '/absagen', { method: 'POST', body: { mail: mail.checked, grund: grund.value || null } }); dlg.zu(); toast('Abgesagt.', 'ok'); danach(); } catch (x) { melde(m, x.message); }
    } }, 'Gespräch absagen'))), true);
}

V.kalender = async () => {
  const p = new URLSearchParams(location.hash.split('?')[1] || '');
  let ansicht = p.get('a') === 'woche' ? 'woche' : 'monat', anker = /^\d{4}-\d{2}-\d{2}$/.test(p.get('t') || '') ? p.get('t') : heuteTag();
  const wurzel = h('div');
  const bereich = () => {
    if (ansicht === 'woche') { const v = montag(anker); return [v, addTage(v, 6)]; }
    const erster = anker.slice(0, 8) + '01'; const v = montag(erster); return [v, addTage(v, 41)];
  };
  const titel = () => {
    if (ansicht === 'woche') { const [v, b] = bereich(); return kurz(v) + ' bis ' + kurz(b) + v.slice(0, 4); }
    return MONATE[Number(anker.slice(5, 7)) - 1] + ' ' + anker.slice(0, 4);
  };
  const springe = (n) => {
    if (ansicht === 'woche') anker = addTage(anker, 7 * n);
    else { const d = new Date(anker.slice(0, 8) + '01T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() + n); anker = d.toISOString().slice(0, 10); }
    zeichnen();
  };
  async function zeichnen() {
    const [v, b] = bereich();
    let d;
    try { d = await api('/api/admin/kalender?von=' + v + '&bis=' + b); } catch (x) { wurzel.replaceChildren(kopf('Kalender'), h('div', { class: 'msg err' }, x.message)); return; }
    const offen = (art, x) => art === 'gespraech' ? gespraechDialog(x, zeichnen) : eintragDialog({ ...x, von: x.ganztag ? tagVon(x.start) : eingabe(x.start), bis: x.ganztag ? tagVon(new Date(new Date(x.ende).getTime() - 1000).toISOString()) : eingabe(x.ende) }, zeichnen);
    const evs = ereignisse(d, offen), heute = heuteTag();
    const proTag = (t) => evs.filter(e => e.tag === t);
    const knoepfe = h('div', { class: 'row', style: 'flex-wrap:wrap;gap:8px;align-items:center' },
      h('button', { class: 'btn sec small', type: 'button', 'aria-label': 'Zurück', onclick: () => springe(-1) }, '‹'),
      h('button', { class: 'btn sec small', type: 'button', onclick: () => { anker = heuteTag(); zeichnen(); } }, 'Heute'),
      h('button', { class: 'btn sec small', type: 'button', 'aria-label': 'Weiter', onclick: () => springe(1) }, '›'),
      h('b', { style: 'min-width:150px', role: 'status' }, titel()),
      h('span', { style: 'flex:1' }),
      h('button', { class: 'btn small' + (ansicht === 'monat' ? '' : ' sec'), type: 'button', 'aria-pressed': String(ansicht === 'monat'), onclick: () => { ansicht = 'monat'; zeichnen(); } }, 'Monat'),
      h('button', { class: 'btn small' + (ansicht === 'woche' ? '' : ' sec'), type: 'button', 'aria-pressed': String(ansicht === 'woche'), onclick: () => { ansicht = 'woche'; zeichnen(); } }, 'Woche'),
      h('button', { class: 'btn small', type: 'button', onclick: () => eintragDialog({ art: 'termin', von: anker + 'T09:00', bis: anker + 'T10:00' }, zeichnen) }, '+ Eintrag'));
    const legende = h('p', { class: 'small muted' }, ...Object.values(ART).flatMap(([n, f]) => [h('span', { style: 'border-left:4px solid ' + f + ';padding-left:6px;margin-right:14px' }, n)]),
      d.buchung.aktiv ? 'Online-Buchung ist eingeschaltet.' : h('span', {}, 'Online-Buchung ist aus (', h('a', { href: '#einstellungen' }, 'Einstellungen'), ').'));
    let inhalt;
    if (ansicht === 'woche') {
      inhalt = h('div', { class: 'kalwoche' }, ...Array.from({ length: 7 }, (_, i) => {
        const t = addTage(v, i), l = proTag(t);
        return h('section', { class: 'card kaltag' + (t === heute ? ' heute' : ''), 'aria-label': kurz(t) },
          h('h3', { style: 'margin:0 0 6px' }, kurz(t)), l.length ? h('div', { class: 'kalliste' }, ...l.map(e => chip(e, true))) : h('p', { class: 'small muted' }, 'Nichts eingetragen.'));
      }));
    } else {
      const monat = anker.slice(0, 7);
      inhalt = h('div', { class: 'kalmonat', role: 'group', 'aria-label': 'Monatsübersicht' }, ...['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'].map(w => h('div', { class: 'kalkopf' }, w)),
        ...Array.from({ length: 42 }, (_, i) => {
          const t = addTage(v, i), l = proTag(t);
          return h('div', { class: 'kalzelle' + (t.slice(0, 7) !== monat ? ' fremd' : '') + (t === heute ? ' heute' : '') },
            h('button', { class: 'kalnr', type: 'button', 'aria-label': kurz(t) + ', ' + l.length + ' Einträge, Woche öffnen', onclick: () => { anker = t; ansicht = 'woche'; zeichnen(); } }, String(Number(t.slice(8)))),
            ...l.slice(0, 3).map(e => chip(e, false)), l.length > 3 ? h('button', { class: 'kalmehr', type: 'button', onclick: () => { anker = t; ansicht = 'woche'; zeichnen(); } }, '+' + (l.length - 3) + ' weitere') : '');
        }));
    }
    wurzel.replaceChildren(kopf('Kalender'), h('p', { class: 'small muted' }, 'Gebuchte Erstgespräche, eigene Termine, Sperren und Wiedervorlagen. Eigene Termine und Sperren blockieren die Online-Buchung.'), knoepfe, legende, inhalt);
  }
  await zeichnen();
  return wurzel;
};
