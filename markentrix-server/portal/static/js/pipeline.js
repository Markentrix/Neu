// Lead-Pipeline als Spalten (Admin und Vertriebler). Verschieben per Ziehen oder Auswahlfeld (Handy), danach „Rückgängig“.
import { h, datum, euro, melde, rueckgaengig } from './common.js';
import { trichter } from './diagramme.js';

const TEMP = { kalt: '❄', warm: '☀', heiss: '🔥' };
const NAME = { neu: 'Neu', kontaktiert: 'Kontaktiert', antwort: 'Antwort', termin: 'Termin', angebot: 'Angebot', gewonnen: 'Gewonnen', verloren: 'Verloren' };

/**
 * opts: { link(l), verschieben(lead, status) -> Promise, ziele: string[] (erlaubte Zielstatus), neuLaden() -> Promise, filter?: Element }
 * Gibt ein Element zurück, das sich nach Verschieben selbst neu zeichnet.
 */
export function pipelineBoard(d, opts) {
  const box = h('div', { class: 'stack' }), meld = h('div');
  const zeichnen = (daten) => {
    const ziele = opts.ziele;
    const bewegen = async (lead, von, nach) => {
      if (von === nach || !ziele.includes(nach)) return;
      if (nach === 'verloren' && !confirm(lead.firma + ' als verloren markieren?')) { await opts.neuLaden(); return; }
      try { await opts.verschieben(lead, nach); } catch (x) { melde(meld, x.message); await opts.neuLaden(); return; }
      await opts.neuLaden();
      rueckgaengig(lead.firma + ': ' + NAME[von] + ' → ' + NAME[nach], async () => { await opts.verschieben(lead, von); await opts.neuLaden(); });
    };
    const karte = (l, spalte) => {
      const wahl = h('select', { 'aria-label': 'Lead ' + l.firma + ' verschieben nach', onchange: (e) => { if (e.target.value) bewegen(l, spalte.status, e.target.value); } },
        h('option', { value: '' }, 'Verschieben …'), ziele.filter(z => z !== spalte.status).map(z => h('option', { value: z }, NAME[z])));
      const el = h('div', { class: 'kkarte', draggable: ziele.includes(spalte.status) ? 'true' : 'false' },
        h('a', { href: opts.link(l) }, (TEMP[l.temperatur] || '') + ' ' + l.firma),
        h('div', { class: 'small muted' }, [l.ort, l.vertriebler].filter(Boolean).join(' · ') + (l.wiedervorlage_am ? ' · WV ' + datum(l.wiedervorlage_am) : '')),
        ziele.includes(spalte.status) ? wahl : '');
      el.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', JSON.stringify({ id: l.id, von: spalte.status })); el.classList.add('zieht'); });
      el.addEventListener('dragend', () => el.classList.remove('zieht'));
      el._lead = l;
      return el;
    };
    const spaltenEl = daten.spalten.map(sp => {
      const col = h('div', { class: 'kspalte', 'aria-label': NAME[sp.status] + ', ' + sp.anzahl + ' Leads', role: 'group' },
        h('h3', {}, NAME[sp.status], h('span', { class: 'badge' }, sp.anzahl)),
        sp.leads.map(l => karte(l, sp)),
        sp.anzahl > sp.leads.length ? h('p', { class: 'small muted' }, 'und ' + (sp.anzahl - sp.leads.length) + ' weitere, siehe „Leads“ (Liste mit Filter).') : (sp.anzahl ? '' : h('p', { class: 'small muted' }, 'Leer')));
      if (ziele.includes(sp.status)) {
        col.addEventListener('dragover', (e) => { e.preventDefault(); col.classList.add('ziel'); });
        col.addEventListener('dragleave', () => col.classList.remove('ziel'));
        col.addEventListener('drop', (e) => {
          e.preventDefault(); col.classList.remove('ziel');
          try { const { id, von } = JSON.parse(e.dataTransfer.getData('text/plain')); const quelle = daten.spalten.find(s => s.status === von), lead = quelle && quelle.leads.find(x => x.id === id); if (lead) bewegen(lead, von, sp.status); } catch { /* fremdes Objekt gezogen */ }
        });
      }
      return col;
    });
    const stufen = daten.trichter.map(t => ({ name: t.titel + (t.status === 'neu' ? ' (alle)' : ' oder weiter'), wert: t.anzahl }));
    const p = daten.prognose;
    box.replaceChildren(meld,
      opts.filter ? h('div', { class: 'card' }, opts.filter) : '',
      h('div', { class: 'chartgrid' },
        h('div', { class: 'card' }, h('h2', {}, 'Trichter'), trichter(stufen, 'Pipeline-Trichter: ' + stufen.map(s => s.name + ' ' + s.wert).join(', ')),
          h('p', { class: 'small muted' }, 'Jede Stufe zählt alle Leads, die dort oder weiter sind. ' + (daten.quote !== null ? 'Abschlussquote der letzten 180 Tage: ' + String(daten.quote).replace('.', ',') + ' % (' + daten.entschieden + ' entschiedene Leads).' : 'Eine Abschlussquote gibt es erst ab 8 entschiedenen Leads in 180 Tagen.'))),
        p ? h('div', { class: 'card' }, h('h2', {}, 'Prognose'),
          p.erwartet_cent !== null ? h('div', {}, h('p', { class: 'stat' }, h('b', {}, euro(p.erwartet_cent)), h('span', { class: 'muted small' }, ' pro Monat zusätzlich, erwartet')),
            h('p', { class: 'small muted' }, p.angebote + ' offene Angebote × ' + String(p.quote).replace('.', ',') + ' % Abschlussquote × ' + euro(p.schnitt_cent) + ' durchschnittlicher Monatswert je Kunde. Das ist eine Schätzung aus deinen bisherigen Zahlen, keine Zusage.'))
            : h('p', { class: 'muted' }, p.hinweis)) : ''),
      h('p', { class: 'small muted' }, 'Ziehe eine Karte in eine andere Spalte oder wähle „Verschieben …“ (Handy). Jede Änderung lässt sich 10 Sekunden lang rückgängig machen.'),
      h('div', { class: 'kanban' }, spaltenEl));
  };
  zeichnen(d);
  box.neuZeichnen = zeichnen;
  return box;
}
