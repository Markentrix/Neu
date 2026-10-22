import { h, api, melde, datum } from '../common.js';
import { fehler, knopf } from './kern.js';

/** Wissensbasis eines Kunden: Dateien (TXT, MD, PDF) hochladen oder Einträge schreiben. Aktive Einträge nutzt der Assistent des Kunden. */
export function wissenKarte(kid) {
  const m = h('div'), liste = h('div'), editor = h('div');
  const pfad = '/api/admin/kunden/' + kid + '/wissen';
  const datei = h('input', { type: 'file', accept: '.txt,.md,.pdf,text/plain,application/pdf', multiple: true, 'aria-label': 'Dateien auswählen' });
  const bereich = h('input', { value: 'dokumente', maxlength: 40, style: 'max-width:180px', 'aria-label': 'Bereich' });
  const laden = async () => {
    const r = await api(pfad);
    if (!r.eintraege.length) { liste.replaceChildren(h('p', { class: 'small muted' }, 'Noch keine Einträge.')); return; }
    liste.replaceChildren(h('div', { class: 'tablewrap' }, h('table', {}, h('thead', {}, h('tr', {}, ['Bereich', 'Titel', 'Umfang', 'Quelle', 'Stand', 'Für den Assistenten', ''].map(t => h('th', {}, t)))),
      h('tbody', {}, r.eintraege.map(e => h('tr', {},
        h('td', {}, e.bereich), h('td', {}, h('b', {}, e.schluessel), h('div', { class: 'small muted' }, e.vorschau.slice(0, 120) + (e.laenge > 120 ? ' …' : ''))),
        h('td', {}, e.laenge + ' Zeichen'), h('td', {}, e.quelle), h('td', {}, datum(e.geaendert_am)),
        h('td', {}, h('label', { style: 'display:flex;gap:6px;align-items:center;color:inherit' }, h('input', { type: 'checkbox', checked: e.aktiv, style: 'width:auto', 'aria-label': 'aktiv: ' + e.schluessel, onchange: async (ev) => {
          try { await api(pfad + '/' + e.id, { method: 'PATCH', body: { aktiv: ev.target.checked } }); } catch (x) { ev.target.checked = !ev.target.checked; fehler(m, x); }
        } }), e.aktiv ? 'an' : 'aus')),
        h('td', {}, h('div', { class: 'row', style: 'gap:6px' }, knopf('Ansehen/Ändern', () => bearbeiten(e.id)), knopf('Löschen', async () => {
          if (!confirm('„' + e.schluessel + '“ wirklich löschen?')) return;
          try { await api(pfad + '/' + e.id, { method: 'DELETE' }); await laden(); } catch (x) { fehler(m, x); }
        })))))))));
  };
  const bearbeiten = async (id) => {
    const e = await api(pfad + '/' + id), t = h('textarea', { rows: 14, maxlength: 200000, 'aria-label': 'Text' }, e.wert);
    editor.replaceChildren(h('div', { class: 'card', style: 'margin-top:8px' }, h('h3', {}, e.schluessel), t,
      h('div', { class: 'row', style: 'margin-top:6px' }, knopf('Speichern', async () => {
        try { await api(pfad + '/' + id, { method: 'PATCH', body: { wert: t.value } }); editor.replaceChildren(); melde(m, 'Gespeichert.', 'ok'); await laden(); } catch (x) { fehler(m, x); }
      }, ''), knopf('Schließen', () => editor.replaceChildren()))));
    editor.scrollIntoView({ block: 'nearest' });
  };
  const hoch = async (ev) => {
    const b = ev.target; const dateien = [...datei.files];
    if (!dateien.length) { melde(m, 'Bitte zuerst eine oder mehrere Dateien auswählen.'); return; }
    b.disabled = true; melde(m, '');
    const ok = [], bad = [];
    for (const f of dateien) {
      const fd = new FormData(); fd.append('datei', f); fd.append('bereich', bereich.value || 'dokumente');
      try { const r = await api(pfad + '/upload', { method: 'POST', body: fd }); ok.push(f.name + ' (' + r.zeichen + ' Zeichen' + (r.ersetzt ? ', ersetzt' : '') + ')'); } catch (x) { bad.push(f.name + ': ' + x.message); }
    }
    b.disabled = false; datei.value = '';
    m.replaceChildren(...[ok.length ? h('div', { class: 'msg ok' }, 'Gelesen und gespeichert: ' + ok.join('; ')) : '', ...bad.map(t => h('div', { class: 'msg bad' }, t))]);
    await laden();
  };
  const titel = h('input', { maxlength: 120, placeholder: 'Titel, z. B. Öffnungszeiten', 'aria-label': 'Titel' });
  const text = h('textarea', { rows: 5, maxlength: 200000, placeholder: 'Text für den Assistenten', 'aria-label': 'Text' });
  const neu = async () => {
    try { await api(pfad, { method: 'POST', body: { bereich: bereich.value || 'allgemein', schluessel: titel.value, wert: text.value } }); titel.value = ''; text.value = ''; melde(m, 'Eintrag gespeichert.', 'ok'); await laden(); } catch (x) { fehler(m, x); }
  };
  laden().catch(x => fehler(m, x));
  return h('div', { class: 'card', id: 'wissen' }, h('h2', {}, 'Wissensbasis für den Assistenten'),
    h('p', { class: 'small muted' }, 'Alles, was hier aktiv ist, darf der Assistent des Kunden nutzen (Leistungen, Preise, Öffnungszeiten, FAQ, Tonalität). Lade Dateien als TXT, MD oder PDF hoch: Wir lesen den Text und speichern ihn. Die Datei selbst wird nicht aufbewahrt. Gescannte PDFs ohne Texterkennung gehen nicht. Gleicher Titel im selben Bereich ersetzt den alten Eintrag. Nichts hochladen, was der Assistent nicht sagen soll.'),
    m, h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;align-items:center' }, datei, h('label', { style: 'color:inherit' }, 'Bereich '), bereich, knopf('Hochladen', hoch, '')),
    h('details', { class: 'hilfe', style: 'margin:8px 0' }, h('summary', {}, 'Eintrag von Hand schreiben'), h('div', { class: 'stack' }, titel, text, h('p', {}, knopf('Eintrag speichern', neu)))),
    liste, editor);
}
