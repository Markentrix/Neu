import { h, leerZustand, themeKnopf, navGruppen, api, euro, melde, abmelden, rechtFuss, glocke, sucheKnopf, neuKnopf, mobilLeiste } from '../common.js';
import { hilfeSuche } from '../hilfe.js';


export const NAV = [['uebersicht', 'Übersicht'], ['meintag', 'Mein Tag'], ['postfach', 'Nachrichten'], ['freigaben', 'Freigaben'], ['aufgaben', 'Aufgaben'], ['kennzahlen', 'Kennzahlen'], ['kunden', 'Kunden'], ['onboarding', 'Onboarding'], ['vertraege', 'Verträge'], ['zufriedenheit', 'Zufriedenheit'], ['neu', 'Neuer Kunde'], ['vertrieb', 'Vertriebler'], ['leads', 'Leads'], ['pipeline', 'Pipeline'], ['auswertung', 'Vertriebs-Auswertung'], ['websites', 'Websites & Demos'], ['belege', 'Angebote & Rechnungen'], ['preise', 'Preise & Konditionen'], ['compliance', 'Datenschutz & Qualität'], ['funnel', 'Lead-Funnel'], ['dsgvo', 'Datenschutz-Anfragen'], ['katalog', 'Pakete (Katalog)'], ['einstellungen', 'Einstellungen'], ['protokoll', 'Protokoll']];
/** Menügruppen im Admin; leere Gruppen (fehlende Rechte) verschwinden. */
/** @type {[string, string[], boolean][]} */
const NAV_GRUPPEN = [
  ['Täglich', ['uebersicht', 'meintag', 'postfach', 'freigaben', 'aufgaben'], true],
  ['Kunden', ['kunden', 'onboarding', 'vertraege', 'zufriedenheit', 'neu', 'websites'], true],
  ['Vertrieb', ['vertrieb', 'leads', 'pipeline', 'auswertung', 'funnel'], true],
  ['Geld & Zahlen', ['kennzahlen', 'belege', 'preise', 'katalog'], false],
  ['System', ['compliance', 'dsgvo', 'einstellungen', 'protokoll'], false],
];
export let paketListe = [], ich = null;
export const zaehlerAdmin = {};

export const NAV_RECHT = { postfach: 'nachrichten', freigaben: 'kunden', kennzahlen: 'finanzen', kunden: 'kunden', onboarding: 'kunden', vertraege: 'kunden', zufriedenheit: 'kunden', pipeline: 'leads', neu: 'kunden', vertrieb: 'leads', leads: 'leads', auswertung: 'leads', websites: 'kunden', belege: 'finanzen', preise: 'finanzen', compliance: 'einstellungen', funnel: 'leads', dsgvo: 'einstellungen', katalog: 'finanzen', einstellungen: 'einstellungen', protokoll: 'einstellungen' };
export const erlaubt = (seite) => !ich || !ich.admin_rechte || !NAV_RECHT[seite] || ich.admin_rechte.includes(NAV_RECHT[seite]);

/** Aktionen für die Befehlspalette, nur für Bereiche, für die das Konto Rechte hat. */
function befehle() {
  const ziele = [['Neuer Kunde', 'neu', true], ['Neue Rechnung oder neues Angebot', 'belege', true], ['Lead anlegen oder importieren', 'leads', true], ['Aufgabe anlegen', 'aufgaben', true], ['Vertriebler einladen', 'vertrieb', true],
    ['Zur Übersicht', 'uebersicht', false], ['Mein Tag', 'meintag', false], ['Zahlungserinnerungen prüfen', 'belege?erinnerung=1', false], ['Nachrichten', 'postfach', false], ['Kennzahlen', 'kennzahlen', false], ['Einstellungen', 'einstellungen', false], ['Protokoll', 'protokoll', false]];
  return [...ziele.filter(([, s]) => erlaubt(String(s).split('?')[0])).map(([titel, s, neu]) => ({ titel: String(titel), text: neu ? 'Anlegen' : 'Öffnen', link: '#' + s, neu: !!neu })), { titel: 'Abmelden', text: 'Sitzung beenden', aktion: () => abmelden() }];
}

export function gerüst(aktiv, inhalt) {
  const gruppen = NAV_GRUPPEN.map(([titel, ids, offen]) => [titel, NAV.filter(n => ids.includes(n[0]) && erlaubt(n[0])).map(n => [n[0], n[1], zaehlerAdmin[n[0]] || 0]), offen]);
  return h('div', { class: 'shell mobilleiste kompakt' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Admin'),
      h('div', { class: 'brandzeile' }, sucheKnopf(befehle()), glocke(), themeKnopf()),
      h('div', { class: 'neuzeile' }, neuKnopf()),
      navGruppen(gruppen, aktiv, 'admin'),
      h('a', { class: 'nav', href: location.origin.replace('//portal.', '//panel.'), target: '_blank', rel: 'noopener' }, 'Server-Dashboard ↗'),
      h('div', { class: 'grow' }),
      h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' }, hilfeSuche('admin'), ich && !ich.zwei_faktor ? h('div', { class: 'msg info' }, 'Dein Admin-Konto hat noch keine Zwei-Faktor-Anmeldung. ', h('a', { href: '#einstellungen' }, 'Jetzt einrichten'), '.') : '', inhalt, rechtFuss()),
    mobilLeiste({ aktiv, gruppen, feste: ['uebersicht', 'postfach', 'kunden', 'freigaben'], icons: { uebersicht: '⌂', postfach: '✉', kunden: '▦', freigaben: '✔', aufgaben: '☑' }, kurz: { uebersicht: 'Übersicht', postfach: 'Posteingang' }, schluessel: 'admin' }));
}
export function tabelle(spalten, zeilen, leer = 'Nichts vorhanden.') {
  if (!zeilen.length) return leerZustand(leer);
  return h('div', { class: 'tablewrap' }, h('table', {},
    h('thead', {}, h('tr', {}, spalten.map(s => h('th', {}, s[0])))),
    h('tbody', {}, zeilen.map(z => h('tr', {}, spalten.map(s => h('td', {}, s[1](z))))))));
}
export const pill = (s) => h('span', { class: 'pill ' + (['aktiv', 'live', 'veroeffentlicht'].includes(s) ? 'ok' : ['pausiert', 'onboarding', 'beauftragt', 'in_einrichtung', 'demo'].includes(s) ? 'warn' : ['gekuendigt', 'beendet', 'fehler'].includes(s) ? 'bad' : '') }, String(s).replace('_', ' '));
export const kopf = (t, ...r) => h('div', { class: 'top' }, h('h1', {}, t), r);
export const feld = (label, name, wert = '', extra = {}) => h('div', {}, h('label', {}, label), h('input', { name, value: wert || '', ...extra }));
export const leerzu = (o) => { Object.keys(o).forEach(k => { if (o[k] === '') delete o[k]; }); return o; };

export const V = {};

export const fehler = (m, x) => melde(m, x.message);
export const fmtEuro = (c) => euro(c);
export const zahlenfeld = (name, label, wert) => feld(label, name, wert === null || wert === undefined ? '' : (wert / 100).toFixed(2), { type: 'number', step: '0.01', min: '0' });
export const cent = (v) => v === undefined || v === '' ? null : Math.round(Number(v) * 100);
export const knopf = (text, fn, art = 'sec') => h('button', { class: 'btn small ' + art, onclick: fn }, text);
export const bestaetigt = async (m, fn, ok = 'Gespeichert.') => { try { await fn(); melde(m, ok, 'ok'); setTimeout(() => location.reload(), 700); } catch (x) { fehler(m, x); } };
export const bestaetigtOhneReload = async (m, fn) => { try { await fn(); } catch (x) { fehler(m, x); } };
export const select = (name, optionen, wert, extra = {}) => h('select', { name, ...extra }, optionen.map(o => { const [v, l] = Array.isArray(o) ? o : [o, o]; return h('option', { value: v, selected: v === wert }, String(l).replace(/_/g, ' ')); }));

export const mailHinweis = (mail) => !mail ? '' : h('div', { class: 'msg ' + (mail.gesendet ? 'ok' : 'info') }, mail.gesendet ? 'Die Einladung wurde per E-Mail verschickt.' : 'Nicht per E-Mail verschickt: ' + mail.grund);

export async function sicherApi(u) { try { return await api(u, { leise: true }); } catch (e) { return null; } }
export async function sicher(f) { try { return await f(); } catch (e) { return ''; } }

export let zeige = () => {};
export const setzeZeige = (f) => { zeige = f; };
export const setzeIch = (m) => { ich = m; };
export const setzePakete = (p) => { paketListe = p; };


/** Auswahl-Haken für Tabellen: haken(id) pro Zeile, alle für die Kopfzeile, gewaehlt = Set der IDs. */
export function auswahl(beiAenderung) {
  const gewaehlt = new Set(), boxen = [];
  const haken = (id) => { const c = h('input', { type: 'checkbox', style: 'width:auto', 'aria-label': 'Zeile auswählen', onchange: (e) => { if (e.target.checked) gewaehlt.add(id); else gewaehlt.delete(id); beiAenderung(gewaehlt); } }); boxen.push(c); return c; };
  const alle = h('input', { type: 'checkbox', style: 'width:auto', 'aria-label': 'Alle auswählen', onchange: (e) => { boxen.forEach((/** @type {any} */ c) => { if (c.checked !== e.target.checked) c.click(); }); } });
  const leeren = () => { gewaehlt.clear(); boxen.forEach((/** @type {any} */ c) => { c.checked = false; }); /** @type {any} */ (alle).checked = false; beiAenderung(gewaehlt); };
  return { gewaehlt, haken, alle, leeren };
}

/** Abfrage-Teil der aktuellen Adresse ohne Blätter- und Dialog-Angaben (das, was ein gespeicherter Filter enthält). */
export function aktuelleAbfrage() {
  const p = new URLSearchParams(location.hash.split('?')[1] || '');
  ['seite', 'erinnerung'].forEach(x => p.delete(x));
  return p.toString();
}

/** Gespeicherte Filter für eine Liste: auswählen, aktuelle Auswahl speichern, Link kopieren, löschen. */
export async function filterKarte(bereich) {
  const liste = await api('/api/admin/meine-filter?bereich=' + bereich, { leise: true }).catch(() => []);
  const treffer = liste.find(f => f.abfrage === aktuelleAbfrage());
  const sel = h('select', { 'aria-label': 'Gespeicherte Filter', onchange: (e) => { const f = liste.find(x => x.id === e.target.value); if (f) location.hash = '#' + bereich + (f.abfrage ? '?' + f.abfrage : ''); } },
    h('option', { value: '' }, liste.length ? 'Gespeicherte Filter …' : 'Noch keine gespeicherten Filter'), liste.map(f => h('option', { value: f.id, selected: treffer && treffer.id === f.id }, f.name)));
  const speichern = async () => {
    const jetzt = aktuelleAbfrage();
    if (!jetzt) { alert('Es ist noch kein Filter gesetzt. Wähle zuerst Suche, Status oder Ähnliches aus.'); return; }
    const name = prompt('Name für diesen Filter:', treffer ? treffer.name : '');
    if (!name || !name.trim()) return;
    try { await api('/api/admin/meine-filter', { method: 'POST', body: { bereich, name: name.trim(), abfrage: jetzt } }); zeige(); } catch (x) { alert(x.message); }
  };
  const kopieren = async (e) => { try { await navigator.clipboard.writeText(location.href); e.target.textContent = 'Link kopiert ✓'; } catch (x) { prompt('Link zum Kopieren:', location.href); } };
  const loeschen = async () => { if (!treffer || !confirm('Filter „' + treffer.name + '“ löschen?')) return; try { await api('/api/admin/meine-filter/' + treffer.id, { method: 'DELETE' }); zeige(); } catch (x) { alert(x.message); } };
  return h('div', { class: 'filterzeile' }, sel, knopf('Aktuelle Auswahl speichern', speichern, 'sec'), knopf('Link kopieren', kopieren, 'sec'), treffer ? knopf('Filter löschen', loeschen, 'sec') : '');
}
