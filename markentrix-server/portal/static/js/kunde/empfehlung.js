// Empfehlungsprogramm im Kundenportal: persönlicher Link zum Weitergeben. Erscheint nur, wenn das Programm im Admin eingeschaltet ist.
import { h, api, melde } from '../common.js';

export async function empfehlungKarte() {
  let d;
  try { d = await api('/api/kunde/empfehlung', { leise: true }); } catch (e) { return ''; }
  if (!d || !d.aktiv) return '';
  const m = h('div', { role: 'status' });
  const kopieren = async () => { try { await navigator.clipboard.writeText(d.link); melde(m, 'Link kopiert.', 'ok'); } catch (e) { melde(m, 'Bitte den Link markieren und kopieren.', 'info'); } };
  const teilen = async () => {
    const nav = /** @type {any} */ (navigator);
    if (nav.share) { try { await nav.share({ title: 'Markentrix', text: 'Ich arbeite mit Markentrix und bin zufrieden. Schau dir das mal an:', url: d.link }); return; } catch (e) { return; } }
    window.open(d.whatsapp, '_blank', 'noopener');
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Markentrix weiterempfehlen'),
    h('p', { class: 'small' }, 'Kennst du einen Betrieb, dem wir auch helfen könnten? Schick ihm deinen persönlichen Link. Er trägt sich selbst ein, niemand wird ohne sein Wissen angesprochen.'),
    d.beschreibung ? h('p', { class: 'small' }, d.beschreibung) : '',
    h('input', { value: d.link, readonly: true, 'aria-label': 'Dein Empfehlungslink', onfocus: (e) => e.target.select() }),
    h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { class: 'btn', onclick: teilen }, 'Link teilen'), h('button', { class: 'btn sec', onclick: kopieren }, 'Link kopieren')), m,
    h('p', { class: 'small muted' }, d.gesamt ? `Bisher ${d.gesamt} Empfehlung${d.gesamt === 1 ? '' : 'en'}, davon ${d.kunden} als Kunde gestartet.` : 'Bisher noch keine Empfehlung.'));
}
