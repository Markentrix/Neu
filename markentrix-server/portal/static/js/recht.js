import { h, api } from './common.js';
const art = location.pathname.includes('datenschutz') ? 'datenschutz' : 'impressum';
document.getElementById('t').textContent = art === 'datenschutz' ? 'Datenschutz' : 'Impressum';
document.title = 'Markentrix – ' + (art === 'datenschutz' ? 'Datenschutz' : 'Impressum');
api('/api/recht', { leise: true }).then(d => {
  document.getElementById('txt').replaceChildren(...d[art].split(/\n{2,}/).map(p => h('p', { style: 'white-space:pre-line' }, p.trim())));
}).catch(() => { document.getElementById('txt').textContent = 'Der Text konnte nicht geladen werden.'; });
