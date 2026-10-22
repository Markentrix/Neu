import { h, api, melde, datum } from '../common.js';
import { fehler, knopf } from './kern.js';

/** Wissensbasis eines Kunden: Dateien (TXT, MD, PDF) hochladen oder Einträge schreiben. Aktive Einträge nutzt der Assistent des Kunden. */
export function wissenKarte(kid) {
  const m = h('div'), liste = h('div'), editor = h('div'), wuensche = h('div');
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
  const vorschlaege = async () => {
    const r = await api('/api/admin/kunden/' + kid + '/wissen-vorschlaege');
    if (!r.vorschlaege.length) { wuensche.replaceChildren(); return; }
    const AK = { neu: 'Neues Wissen', aendern: 'Änderung', ausschalten: 'Ausschalten' };
    const fertig = async () => { await vorschlaege(); await laden(); };
    wuensche.replaceChildren(h('div', { class: 'card', style: 'margin:8px 0' }, h('h3', {}, 'Änderungswünsche des Kunden'), ...r.vorschlaege.map(v => h('div', { style: 'margin:8px 0' },
      h('p', {}, h('span', { class: 'pill ' + (v.status === 'offen' ? 'warn' : v.status === 'uebernommen' ? 'ok' : '') }, v.status === 'offen' ? 'offen' : v.status), ' ', h('b', {}, AK[v.aktion] + ': ' + v.schluessel), ' · ' + datum(v.erstellt_am)),
      v.aktion === 'aendern' ? h('details', {}, h('summary', {}, 'Bisher ansehen'), h('pre', { class: 'small', style: 'white-space:pre-wrap' }, v.alt_wert.slice(0, 3000))) : '',
      v.wert ? h('pre', { class: 'small', style: 'white-space:pre-wrap;max-height:220px;overflow:auto' }, v.wert.slice(0, 3000) + (v.wert.length > 3000 ? ' …' : '')) : '',
      v.notiz ? h('p', { class: 'small muted' }, 'Antwort: ' + v.notiz) : '',
      v.status === 'offen' ? h('div', { class: 'row', style: 'gap:6px' },
        knopf('Übernehmen', async () => { try { await api(pfad.replace('/wissen', '/wissen-vorschlaege') + '/' + v.id + '/uebernehmen', { method: 'POST', body: {} }); await fertig(); } catch (x) { fehler(m, x); } }, ''),
        knopf('Ablehnen', async () => { const n = prompt('Kurze Begründung für den Kunden (optional):', ''); if (n === null) return; try { await api(pfad.replace('/wissen', '/wissen-vorschlaege') + '/' + v.id + '/ablehnen', { method: 'POST', body: { notiz: n } }); await fertig(); } catch (x) { fehler(m, x); } })) : ''))));
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
  laden().catch(x => fehler(m, x)); vorschlaege().catch(x => fehler(m, x));
  return h('div', { class: 'card', id: 'wissen' }, h('h2', {}, 'Wissensbasis für den Assistenten'),
    h('p', { class: 'small muted' }, 'Alles, was hier aktiv ist, darf der Assistent des Kunden nutzen (Leistungen, Preise, Öffnungszeiten, FAQ, Tonalität). Lade Dateien als TXT, MD oder PDF hoch: Wir lesen den Text und speichern ihn. Die Datei selbst wird nicht aufbewahrt. Gescannte PDFs ohne Texterkennung gehen nicht. Gleicher Titel im selben Bereich ersetzt den alten Eintrag. Nichts hochladen, was der Assistent nicht sagen soll.'),
    m, h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;align-items:center' }, datei, h('label', { style: 'color:inherit' }, 'Bereich '), bereich, knopf('Hochladen', hoch, '')),
    h('details', { class: 'hilfe', style: 'margin:8px 0' }, h('summary', {}, 'Eintrag von Hand schreiben'), h('div', { class: 'stack' }, titel, text, h('p', {}, knopf('Eintrag speichern', neu)))),
    wuensche, liste, editor);
}

/** Leistungen und Preise eines Kunden: Freigabepflicht umstellen und Änderungswünsche prüfen. */
export function leistungsKarte(kid) {
  const m = h('div'), box = h('div');
  const pfad = '/api/admin/kunden/' + kid;
  const AK = { neu: 'Neue Leistung', aendern: 'Änderung', loeschen: 'Löschen' };
  const laden = async () => {
    const r = await api(pfad + '/leistungs-aenderungen');
    const cb = h('input', { type: 'checkbox', checked: r.freigabe, style: 'width:auto', onchange: async (e) => {
      try { await api(pfad + '/leistungs-freigabe', { method: 'PUT', body: { freigabe: e.target.checked } }); melde(m, e.target.checked ? 'Änderungen des Kunden brauchen jetzt deine Freigabe.' : 'Änderungen des Kunden gehen sofort live.', 'ok'); } catch (x) { e.target.checked = !e.target.checked; fehler(m, x); }
    } });
    const feld = (v) => (v == null || v === '' ? '–' : String(v));
    box.replaceChildren(h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-weight:600' }, cb, 'Änderungen an Leistungen und Preisen brauchen meine Freigabe'),
      h('p', { class: 'small muted' }, 'Aus: Was der Kunde im Portal ändert, ist sofort auf seiner Website und im Wissen des Assistenten. An: Es erscheint hier als Wunsch, du übernimmst oder lehnst ab.'),
      ...r.aenderungen.map(a => {
        const d = a.daten || {};
        return h('div', { class: 'card', style: 'margin:8px 0' }, h('p', {}, h('span', { class: 'pill ' + (a.status === 'offen' ? 'warn' : a.status === 'uebernommen' ? 'ok' : '') }, a.status), ' ', h('b', {}, AK[a.aktion] + ': ' + a.name), ' · ' + datum(a.erstellt_am)),
          a.aktion !== 'loeschen' ? h('p', { class: 'small' }, 'Neu: Preis ' + feld(d.preis) + ' · Dauer ' + feld(d.dauer_min) + ' Min. · Pause ' + feld(d.puffer_min) + ' · Anzahlung ' + (d.anzahlung_art && d.anzahlung_art !== 'keine' ? d.anzahlung_wert + (d.anzahlung_art === 'prozent' ? ' %' : ' €') : 'keine') + (d.freigabe ? ' · Termin nur nach Bestätigung' : '') + (d.aktiv === false ? ' · ausgeschaltet' : '')) : '',
          a.alt ? h('p', { class: 'small muted' }, 'Bisher: Preis ' + feld(a.alt.preis) + ' · Dauer ' + feld(a.alt.dauer) + ' Min.') : '',
          a.notiz ? h('p', { class: 'small muted' }, 'Antwort: ' + a.notiz) : '',
          a.status === 'offen' ? h('div', { class: 'row', style: 'gap:6px' },
            knopf('Übernehmen', async () => { try { await api(pfad + '/leistungs-aenderungen/' + a.id + '/uebernehmen', { method: 'POST', body: {} }); await laden(); } catch (x) { fehler(m, x); } }, ''),
            knopf('Ablehnen', async () => { const n = prompt('Kurze Begründung für den Kunden (optional):', ''); if (n === null) return; try { await api(pfad + '/leistungs-aenderungen/' + a.id + '/ablehnen', { method: 'POST', body: { notiz: n } }); await laden(); } catch (x) { fehler(m, x); } })) : '');
      }));
  };
  laden().catch(x => fehler(m, x));
  return h('div', { class: 'card', id: 'leistungsfreigabe' }, h('h2', {}, 'Leistungen und Preise: Freigabe'), m, box);
}
