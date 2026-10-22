import { h, api, melde, datum, toast } from '../common.js';
import { V, zeige } from './kern.js';

const STATUS = { offen: ['warn', 'wird geprüft'], uebernommen: ['ok', 'übernommen'], abgelehnt: ['bad', 'abgelehnt'], zurueckgezogen: ['', 'zurückgezogen'] };
const AKTION = { neu: 'Neues Wissen', aendern: 'Änderung', ausschalten: 'Ausschalten' };

/** Das Wissen, das der KI-Assistent des Kunden nutzt. Der Kunde schlägt vor, das Team prüft und übernimmt. */
V.wissen = async () => {
  const r = await api('/api/kunde/wissen');
  const m = h('div'), editor = h('div');
  const neu = () => zeige();
  const senden = async (body, ok) => { try { await api('/api/kunde/wissen/vorschlaege', { method: 'POST', body }); toast(ok, 'ok'); neu(); } catch (x) { melde(m, x.message); } };
  const titel = h('input', { maxlength: 120, placeholder: 'Titel, z. B. Öffnungszeiten im Winter', 'aria-label': 'Titel' });
  const text = h('textarea', { rows: 6, maxlength: 200000, placeholder: 'Was soll der Assistent wissen?', 'aria-label': 'Text' });
  const datei = h('input', { type: 'file', accept: '.txt,.md,.pdf,text/plain,application/pdf', 'aria-label': 'Datei auswählen' });
  const hoch = async (ev) => {
    const f = datei.files[0]; if (!f) { melde(m, 'Bitte zuerst eine Datei auswählen.'); return; }
    const b = ev.target; b.disabled = true;
    const fd = new FormData(); fd.append('datei', f);
    try { await api('/api/kunde/wissen/vorschlaege/datei', { method: 'POST', body: fd }); toast('Datei gesendet. Das Team prüft sie.', 'ok'); neu(); } catch (x) { melde(m, x.message); b.disabled = false; }
  };
  const aendern = (e) => {
    const t = h('textarea', { rows: 10, maxlength: 200000, 'aria-label': 'Neuer Text' }, e.wert);
    editor.replaceChildren(h('div', { class: 'card', style: 'margin-top:8px' }, h('h3', {}, e.schluessel), e.gekuerzt ? h('p', { class: 'msg info' }, 'Der Text ist lang und hier gekürzt. Für große Änderungen lade bitte eine neue Datei hoch.') : '', t,
      h('div', { class: 'row', style: 'margin-top:6px' }, h('button', { class: 'btn', disabled: !!e.gekuerzt, onclick: () => senden({ aktion: 'aendern', wissen_id: e.id, wert: t.value }, 'Änderung gesendet. Das Team prüft sie.') }, 'Änderung vorschlagen'),
        h('button', { class: 'btn sec', onclick: () => editor.replaceChildren() }, 'Abbrechen'))));
    editor.scrollIntoView({ block: 'nearest' });
  };
  const offen = new Set(r.vorschlaege.filter(v => v.status === 'offen').map(v => v.schluessel));
  return h('div', { class: 'stack' }, h('div', { class: 'top' }, h('h1', {}, 'Mein Wissen für den Assistenten')),
    h('div', { class: 'card' }, h('p', {}, 'Hier steht, was dein KI-Assistent über deinen Betrieb weiß: Leistungen, Preise, Öffnungszeiten und häufige Fragen. Haben sich Preise oder Zeiten geändert, schlage es hier vor. Das Team prüft jede Änderung und schaltet sie frei, damit dein Assistent nichts Falsches weitergibt.'), m),
    h('div', { class: 'card' }, h('h2', {}, 'Neues Wissen vorschlagen'), h('div', { class: 'stack' }, titel, text,
      h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' }, h('button', { class: 'btn', onclick: () => senden({ aktion: 'neu', schluessel: titel.value, wert: text.value }, 'Gesendet. Das Team prüft es.') }, 'Vorschlag senden')),
      h('p', { class: 'small muted' }, 'Oder eine Datei (TXT oder PDF, z. B. Preisliste) senden:'), h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' }, datei, h('button', { class: 'btn sec', onclick: hoch }, 'Datei senden')))),
    r.vorschlaege.length ? h('div', { class: 'card' }, h('h2', {}, 'Meine Vorschläge'), ...r.vorschlaege.map(v => h('div', { style: 'margin:8px 0' },
      h('p', {}, h('span', { class: 'pill ' + STATUS[v.status][0] }, STATUS[v.status][1]), ' ', h('b', {}, AKTION[v.aktion] + ': ' + v.schluessel), ' · ' + datum(v.erstellt_am)),
      v.notiz ? h('p', { class: 'small' }, 'Antwort vom Team: ' + v.notiz) : '',
      v.status === 'offen' ? h('button', { class: 'btn sec small', onclick: async () => { try { await api('/api/kunde/wissen/vorschlaege/' + v.id, { method: 'DELETE' }); neu(); } catch (x) { melde(m, x.message); } } }, 'Zurückziehen') : ''))) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Aktuell gespeichert'), r.eintraege.length ? h('div', {}, ...r.eintraege.map(e => h('div', { style: 'margin:10px 0;border-top:1px solid var(--linie, #e5e7eb);padding-top:8px' },
      h('p', {}, h('b', {}, e.schluessel), ' ', h('span', { class: 'pill ' + (e.aktiv ? 'ok' : '') }, e.aktiv ? 'aktiv' : 'aus'), ' ', h('span', { class: 'small muted' }, e.bereich + ' · ' + e.laenge + ' Zeichen')),
      h('p', { class: 'small' }, e.vorschau + (e.laenge > 240 ? ' …' : '')),
      e.quelle === 'system' ? h('p', { class: 'small muted' }, 'Dieser Eintrag entsteht automatisch aus deinen Leistungen und Preisen. Ändere sie unter Website-Dienste → Leistungen.') : offen.has(e.schluessel) ? h('p', { class: 'small muted' }, 'Es wartet ein Vorschlag auf Prüfung.') : h('div', { class: 'row', style: 'gap:6px' },
        h('button', { class: 'btn sec small', onclick: () => aendern(e) }, 'Ändern vorschlagen'),
        e.aktiv ? h('button', { class: 'btn sec small', onclick: () => { if (confirm('Soll der Assistent „' + e.schluessel + '“ nicht mehr nutzen? Das Team prüft den Wunsch.')) senden({ aktion: 'ausschalten', wissen_id: e.id }, 'Gesendet. Das Team prüft es.'); } }, 'Nicht mehr nutzen') : ''))))
      : h('p', { class: 'small muted' }, 'Noch nichts gespeichert. Das Team füllt das mit dir im Aufbau.')), editor);
};
