import { h, api } from '../common.js';
import { V, kopf } from './kern.js';
import { pipelineBoard } from '../pipeline.js';

const ZIELE = ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'gewonnen', 'verloren'];

V.pipeline = async () => {
  const p = new URLSearchParams(location.hash.split('?')[1] || ''), vt = p.get('vertriebler') || '';
  const lade = () => api('/api/admin/pipeline' + (vt ? '?vertriebler=' + encodeURIComponent(vt) : ''));
  const d = await lade();
  const sel = h('select', { 'aria-label': 'Vertriebler filtern', style: 'width:auto', onchange: (e) => { location.hash = '#pipeline' + (e.target.value ? '?vertriebler=' + e.target.value : ''); } },
    h('option', { value: '' }, 'Alle Vertriebler'), d.vertriebler.map(v => h('option', { value: v.id, selected: v.id === vt }, v.name)));
  let board;
  board = pipelineBoard(d, {
    ziele: ZIELE, link: (l) => '#lead/' + l.id, filter: h('div', { class: 'row' }, h('label', { style: 'margin:0' }, 'Anzeigen für'), sel, h('a', { class: 'btn sec small', href: '#leads' }, 'Zur Liste')),
    verschieben: (l, status) => api('/api/admin/leads/' + l.id, { method: 'PATCH', body: { status } }),
    neuLaden: async () => { board.neuZeichnen(await lade()); },
  });
  return h('div', {}, kopf('Pipeline'), board);
};
