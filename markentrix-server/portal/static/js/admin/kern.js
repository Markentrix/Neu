import { h, api, euro, melde, abmelden, rechtFuss, glocke, sucheKnopf, neuKnopf } from '../common.js';


export const NAV = [['uebersicht', 'Übersicht'], ['postfach', 'Nachrichten'], ['freigaben', 'Freigaben'], ['aufgaben', 'Aufgaben'], ['kennzahlen', 'Kennzahlen'], ['kunden', 'Kunden'], ['neu', 'Neuer Kunde'], ['vertrieb', 'Vertriebler'], ['leads', 'Leads'], ['auswertung', 'Vertriebs-Auswertung'], ['websites', 'Websites & Demos'], ['belege', 'Angebote & Rechnungen'], ['preise', 'Preise & Konditionen'], ['compliance', 'Datenschutz & Qualität'], ['katalog', 'Pakete (Katalog)'], ['einstellungen', 'Einstellungen'], ['protokoll', 'Protokoll']];
export let paketListe = [], ich = null;
export const zaehlerAdmin = {};

export const NAV_RECHT = { postfach: 'nachrichten', freigaben: 'kunden', kennzahlen: 'finanzen', kunden: 'kunden', neu: 'kunden', vertrieb: 'leads', leads: 'leads', auswertung: 'leads', websites: 'kunden', belege: 'finanzen', preise: 'finanzen', compliance: 'einstellungen', katalog: 'finanzen', einstellungen: 'einstellungen', protokoll: 'einstellungen' };
export const erlaubt = (seite) => !ich || !ich.admin_rechte || !NAV_RECHT[seite] || ich.admin_rechte.includes(NAV_RECHT[seite]);

/** Aktionen für die Befehlspalette, nur für Bereiche, für die das Konto Rechte hat. */
function befehle() {
  const ziele = [['Neuer Kunde', 'neu', true], ['Neue Rechnung oder neues Angebot', 'belege', true], ['Lead anlegen oder importieren', 'leads', true], ['Aufgabe anlegen', 'aufgaben', true], ['Vertriebler einladen', 'vertrieb', true],
    ['Zur Übersicht', 'uebersicht', false], ['Nachrichten', 'postfach', false], ['Kennzahlen', 'kennzahlen', false], ['Einstellungen', 'einstellungen', false], ['Protokoll', 'protokoll', false]];
  return [...ziele.filter(([, s]) => erlaubt(s)).map(([titel, s, neu]) => ({ titel: String(titel), text: neu ? 'Anlegen' : 'Öffnen', link: '#' + s, neu: !!neu })), { titel: 'Abmelden', text: 'Sitzung beenden', aktion: () => abmelden() }];
}

export function gerüst(aktiv, inhalt) {
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Admin'),
      h('div', { class: 'brandzeile' }, sucheKnopf(befehle()), glocke()),
      h('div', { class: 'neuzeile' }, neuKnopf()),
      NAV.filter(n => erlaubt(n[0])).map(n => h('a', { class: 'nav' + (n[0] === aktiv ? ' on' : ''), href: '#' + n[0] }, n[1], zaehlerAdmin[n[0]] ? h('span', { class: 'badge' }, zaehlerAdmin[n[0]]) : '')),
      h('a', { class: 'nav', href: location.origin.replace('//portal.', '//panel.'), target: '_blank', rel: 'noopener' }, 'Server-Dashboard ↗'),
      h('div', { class: 'grow' }),
      h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' }, ich && !ich.zwei_faktor ? h('div', { class: 'msg info' }, 'Dein Admin-Konto hat noch keine Zwei-Faktor-Anmeldung. ', h('a', { href: '#einstellungen' }, 'Jetzt einrichten'), '.') : '', inhalt, rechtFuss()));
}
export function tabelle(spalten, zeilen, leer = 'Nichts vorhanden.') {
  if (!zeilen.length) return h('p', { class: 'muted' }, leer);
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
