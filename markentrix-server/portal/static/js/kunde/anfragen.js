import { h, api, zeit, melde, formular } from '../common.js';
import { tabelle, V, karten } from './kern.js';

V.assistent = async () => {
  const log = h('div', { class: 'chatlog' });
  const verlauf = await api('/api/kunde/chat');
  const blase = (m) => h('div', { class: 'bub ' + m.absender }, m.text);
  if (!verlauf.length) log.append(blase({ absender: 'agent', text: 'Hallo! Ich bin dein Markentrix-Assistent. Frag mich zu Anfragen, Terminen oder deiner Website.' }));
  verlauf.forEach(m => log.append(blase(m)));
  const eingabe = h('input', { placeholder: 'Nachricht schreiben …', maxlength: 2000, required: true });
  const knopf = h('button', { class: 'btn' }, 'Senden');
  const form = h('form', { class: 'chatform', onsubmit: async (e) => {
    e.preventDefault();
    const text = eingabe.value.trim(); if (!text) return;
    eingabe.value = ''; knopf.disabled = true;
    log.append(blase({ absender: 'kunde', text }));
    const warte = h('div', { class: 'bub agent muted' }, '…'); log.append(warte); log.scrollTop = log.scrollHeight;
    try { const r = await api('/api/kunde/chat', { method: 'POST', body: { text } }); warte.replaceWith(blase(r)); }
    catch (err) { warte.replaceWith(h('div', { class: 'msg err' }, err.message)); }
    knopf.disabled = false; log.scrollTop = log.scrollHeight; eingabe.focus();
  } }, eingabe, knopf);
  setTimeout(() => { log.scrollTop = log.scrollHeight; });
  const chat = h('div', { class: 'card chat' }, h('h2', {}, 'KI-Assistent'), h('p', { class: 'small muted' }, 'Hinweis: Du schreibst hier mit einer KI, nicht mit einem Menschen. Bitte gib keine Passwörter oder besonders sensible Daten ein. Antworten können Fehler enthalten.'), log, form);
  return h('div', { class: 'cols' }, chat, h('div', { class: 'stack' }, karten()));
};

V.anfragen = async () => {
  const daten = await api('/api/kunde/anfragen');
  const box = h('div');
  const status = (z) => h('select', { onchange: async (e) => { try { await api('/api/kunde/anfragen/' + z.id, { method: 'PATCH', body: { status: e.target.value } }); } catch (x) { alert(x.message); } } },
    ['neu', 'in_bearbeitung', 'beantwortet', 'erledigt', 'spam'].map(s => h('option', { value: s, selected: s === z.status }, s.replace('_', ' '))));
  box.append(tabelle([['Eingang', z => zeit(z.erstellt_am)], ['Name', z => z.name], ['Kontakt', z => z.kontakt], ['Nachricht', z => z.nachricht], ['Quelle', z => z.quelle], ['Status', status]], daten, 'Noch keine Anfragen.'));
  return h('div', { class: 'card' }, h('h2', {}, 'Anfragen'), box);
};

V.termine = async () => {
  const daten = await api('/api/kunde/termine');
  const m = h('div');
  const f = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault();
    const d = formular(e.target);
    Object.keys(d).forEach(k => { if (d[k] === '') delete d[k]; });
    if (d.beginn) d.beginn = new Date(d.beginn).toISOString();
    if (d.ende) d.ende = new Date(d.ende).toISOString();
    try { await api('/api/kunde/termine', { method: 'POST', body: d }); location.reload(); } catch (x) { melde(m, x.message); }
  } },
    h('div', {}, h('label', {}, 'Titel'), h('input', { name: 'titel', required: true })),
    h('div', {}, h('label', {}, 'Beginn'), h('input', { name: 'beginn', type: 'datetime-local', required: true })),
    h('div', {}, h('label', {}, 'Ende'), h('input', { name: 'ende', type: 'datetime-local' })),
    h('div', {}, h('label', {}, 'Name Kontakt'), h('input', { name: 'kontakt_name' })),
    h('div', {}, h('label', {}, 'Notiz'), h('input', { name: 'notiz' })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Termin anlegen')));
  const status = (z) => h('select', { onchange: async (e) => { try { await api('/api/kunde/termine/' + z.id, { method: 'PATCH', body: { status: e.target.value } }); } catch (x) { alert(x.message); } } },
    ['geplant', 'bestaetigt', 'abgesagt', 'erledigt', 'nicht_erschienen'].map(s => h('option', { value: s, selected: s === z.status }, s.replace('_', ' '))));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Termine'), tabelle([['Wann', z => zeit(z.beginn)], ['Titel', z => z.titel], ['Kontakt', z => z.kontakt_name], ['Notiz', z => z.notiz], ['Status', status]], daten, 'Keine Termine.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Termin'), m, f));
};

V.kontakte = async () => {
  const daten = await api('/api/kunde/kontakte');
  const m = h('div');
  const f = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault();
    const d = formular(e.target); Object.keys(d).forEach(k => { if (d[k] === '') delete d[k]; });
    try { await api('/api/kunde/kontakte', { method: 'POST', body: d }); location.reload(); } catch (x) { melde(m, x.message); }
  } },
    ['name:Name', 'firma:Firma', 'email:E-Mail', 'telefon:Telefon', 'notiz:Notiz'].map(s => { const [n, l] = s.split(':'); return h('div', {}, h('label', {}, l), h('input', { name: n, required: n === 'name' })); }),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Kontakt speichern')));
  const loesch = (z) => h('button', { class: 'btn small bad', onclick: async () => { if (!confirm('Kontakt löschen?')) return; try { await api('/api/kunde/kontakte/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { alert(x.message); } } }, 'Löschen');
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Kontakte'), tabelle([['Name', z => z.name], ['Firma', z => z.firma], ['E-Mail', z => z.email], ['Telefon', z => z.telefon], ['Notiz', z => z.notiz], ['', loesch]], daten, 'Noch keine Kontakte.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Kontakt'), m, f));
};

// ------------------------------------------------------------- Nachrichten und Aufträge
export const ARTEN = { frage: 'Frage', auftrag: 'Auftrag', aenderung: 'Änderungswunsch', problem: 'Problem', modul: 'Zusatzmodul' };
export const STATUS_TXT = { offen: 'offen', in_arbeit: 'in Arbeit', wartet_auf_kunde: 'wartet auf dich', erledigt: 'erledigt' };
