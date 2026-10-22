import { h, nutzung, leerZustand, themeKnopf, navGruppen, dialog, abmelden, sparkline, rechtFuss, glocke } from '../common.js';
import { hilfeSuche } from '../hilfe.js';
import { installBanner } from '../anleitung.js';

export const root = document.getElementById('app');
export let start = null;
export const setzeStart = (s) => { start = s; };
export const hat = (c) => start.module.some(m => m.code === c);

const SEITEN = [
  ['willkommen', 'So geht’s', null],
  ['heute', 'Heute', null],
  ['uebersicht', 'Übersicht', null],
  ['status', 'Status', null],
  ['briefing', 'Briefing', null],
  ['nachrichten', 'Nachrichten', null],
  ['freigaben', 'Freigaben', null],
  ['assistent', 'KI-Assistent', 'ki_chat'],
  ['wissen', 'Mein Wissen für den Assistenten', 'ki_chat'],
  ['anfragen', 'Anfragen', 'anfragen_termine'],
  ['termine', 'Termine', 'anfragen_termine'],
  ['kalender', 'Kalender', 'anfragen_termine'],
  ['stamm', 'Stammkunden', 'anfragen_termine'],
  ['bewertungen', 'Bewertungen', 'anfragen_termine'],
  ['kontakte', 'Kontakte', 'kontakte_angebote_vertraege'],
  ['dokumente', 'Meine Angebote an Kunden', 'kontakte_angebote_vertraege'],
  ['unterlagen', 'Dateien & Unterlagen', null],
  ['auswertung', 'Auswertung', null],
  ['berichte', 'Monatsberichte', null],
  ['belege', 'Rechnungen von Markentrix', null],
  ['anrufe', 'Anrufe', null],
  ['website', 'Website & Landingpages', 'website'],
  ['dienste', 'Website-Dienste', 'website'],
  ['wochenangebote', 'Wochenangebote', 'wochenangebote'],
  ['werbung', 'Werbung & Berichte', 'werbung_berichte'],
  ['automationen', 'Automationen', 'automationen'],
  ['avv', 'Datenschutz-Vertrag', null],
  ['vertraege', 'Referenzvertrag', null],
  ['team', 'Team', null],
  ['hilfe', 'Hilfe', null],
  ['einstellungen', 'Einstellungen', null],
];
/** Menügruppen: Täglich und Verstehen sind offen, selten Gebrauchtes klappt zu. */
/** @type {[string, string[], boolean][]} */
const GRUPPEN = [
  ['Täglich', ['heute', 'anfragen', 'termine', 'kalender', 'stamm', 'bewertungen', 'nachrichten', 'freigaben', 'anrufe'], true],
  ['Verstehen', ['uebersicht', 'status', 'briefing', 'auswertung', 'berichte'], true],
  ['Mein Betrieb', ['assistent', 'wissen', 'website', 'dienste', 'wochenangebote', 'werbung', 'automationen', 'kontakte', 'dokumente', 'unterlagen'], false],
  ['Verwaltung', ['willkommen', 'belege', 'avv', 'vertraege', 'team', 'hilfe', 'einstellungen'], false],
];
export const inhaber = () => start.kunden_rolle === 'inhaber';
const EMPFANG = ['heute', 'anfragen', 'termine', 'kalender', 'stamm', 'nachrichten', 'hilfe', 'einstellungen'];
export const sichtbar = () => SEITEN.filter(s => (!s[2] || hat(s[2])) && (!['belege', 'team', 'avv', 'dienste', 'vertraege', 'wissen'].includes(s[0]) || inhaber()) && (s[0] !== 'vertraege' || (start.badges && start.badges.vertraege_da > 0)) && (start.kunden_rolle !== 'empfang' || EMPFANG.includes(s[0])) && (s[0] !== 'stamm' || !start.personengebunden));

const zaehler = (id) => (start.badges && (id === 'nachrichten' ? start.badges.nachrichten : id === 'freigaben' ? start.badges.freigaben : id === 'briefing' ? start.badges.briefing : id === 'avv' ? start.badges.avv : id === 'vertraege' ? start.badges.vertraege : 0)) || 0;

/** Feste Leiste unten am Handy: die drei wichtigsten Seiten und „Mehr“ mit dem ganzen Menü. */
function tabbar(aktiv) {
  const ids = sichtbar().map(x => x[0]), feste = ['heute', ids.includes('anfragen') ? 'anfragen' : 'nachrichten', ids.includes('termine') ? 'termine' : 'uebersicht'];
  const ICON = { heute: '⌂', anfragen: '✉', termine: '▦', nachrichten: '✉', uebersicht: '◔' };
  const rest = ids.filter(i => !feste.includes(i)), mehrZahl = rest.reduce((n, i) => n + zaehler(i), 0);
  const mehr = () => dialog('Menü', h('div', { class: 'mehrblatt' }, navGruppen(GRUPPEN.map(([titel, g]) => [titel, sichtbar().filter(x => g.includes(x[0])).map(x => [x[0], x[1], zaehler(x[0])]), true]), aktiv, 'kunde-mehr'),
    h('div', { class: 'brandzeile', style: 'margin-top:10px' }, themeKnopf()), h('button', { class: 'btn sec', style: 'width:100%;margin-top:10px', onclick: () => abmelden() }, 'Abmelden')));
  return h('nav', { class: 'tabbar', 'aria-label': 'Schnellzugriff' },
    feste.map(id => h('a', { href: '#' + id, class: id === aktiv ? 'on' : '', 'aria-current': id === aktiv ? 'page' : null }, h('span', { class: 'ic', 'aria-hidden': 'true' }, ICON[id] || '•'), h('span', {}, (SEITEN.find(x => x[0] === id) || [id, id])[1].replace('Angebote & Rechnungen', 'Rechnungen')))),
    h('button', { type: 'button', class: !feste.includes(aktiv) ? 'on' : '', onclick: mehr }, h('span', { class: 'ic', 'aria-hidden': 'true' }, '☰', mehrZahl ? h('span', { class: 'badge' }, mehrZahl) : ''), h('span', {}, 'Mehr')));
}

export function gerüst(aktiv, inhalt) {
  const k = start.kunde;
  return h('div', { class: 'shell mobilleiste' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, k.logo_vorhanden ? h('img', { class: 'kundenlogo', src: '/api/kunde/logo', alt: '' }) : h('div', { class: 'logo' }, 'M'), k.logo_vorhanden ? k.firma : 'Markentrix'),
      h('div', { class: 'brandzeile' }, glocke(), themeKnopf()),
      navGruppen(GRUPPEN.map(([titel, ids, offen]) => [titel, sichtbar().filter(s => ids.includes(s[0])).map(s => [s[0], s[1], zaehler(s[0])]), offen]), aktiv, 'kunde'),
      h('div', { class: 'grow' }),
      h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' },
      h('div', { class: 'top' },
        h('h1', {}, k.firma),
        h('span', { class: 'pill' }, 'Kundennr. ' + k.kundennummer),
        h('span', { class: 'pill ok' }, '● Online')),
      hilfeSuche('kunde'), installBanner(), inhalt, rechtFuss()),
    tabbar(aktiv));
}

export function karten() {
  const a = h('div', { class: 'card' }, h('h3', {}, 'Anfragen'),
    h('div', { class: 'stat' }, h('b', {}, start.neue_anfragen), h('span', { class: 'muted small' }, 'neu · letzte 14 Tage')),
    sparkline(start.anfragen_14d, '#28C7F7'));
  const t = h('div', { class: 'card' }, h('h3', {}, 'Termine'),
    h('div', { class: 'stat' }, h('b', {}, start.kommende_termine), h('span', { class: 'muted small' }, 'kommend · nächste 14 Tage')),
    sparkline(start.termine_14d, '#8B5CF6'));
  const w = start.website;
  const web = h('div', { class: 'card' }, h('h3', {}, 'Website & Landingpages'),
    w ? h('p', {}, w.domain, ' ', h('span', { class: 'pill ' + (w.status === 'live' ? 'ok' : 'warn') }, w.status)) : h('p', { class: 'muted small' }, 'Noch keine Website verknüpft.'));
  return [hat('anfragen_termine') && a, hat('anfragen_termine') && t, hat('website') && web];
}

export function tabelle(spalten, zeilen, leer = 'Noch nichts vorhanden.') {
  if (!zeilen.length) return leerZustand(leer);
  return h('div', { class: 'tablewrap' }, h('table', {},
    h('thead', {}, h('tr', {}, spalten.map(s => h('th', {}, s[0])))),
    h('tbody', {}, zeilen.map(z => h('tr', {}, spalten.map(s => h('td', {}, s[1](z))))))));
}
export const statusPill = (s) => h('span', { class: 'pill ' + (['neu', 'geplant'].includes(s) ? 'warn' : ['erledigt', 'veroeffentlicht', 'bestaetigt', 'beantwortet'].includes(s) ? 'ok' : ['fehler', 'abgesagt', 'spam'].includes(s) ? 'bad' : '') }, String(s).replace('_', ' '));

// ------------------------------------------------------------- Seiten
export const V = {};
let aufruf = 0;
export async function zeige() {
  const dieser = ++aufruf;
  const [id, param] = (location.hash || '#').slice(1).split('/');
  const erlaubt = sichtbar().map(s => s[0]);
  const seite = erlaubt.includes(id) ? id : 'heute';
  nutzung(seite);
  let inhalt;
  try { inhalt = await V[seite](param); } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  if (dieser !== aufruf) return;   // inzwischen wurde eine andere Seite geöffnet
  root.replaceChildren(gerüst(seite, inhalt));
}

