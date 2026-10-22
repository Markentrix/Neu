import { pipelineBoard } from './pipeline.js';
import { stapelTabellen } from './common.js';
stapelTabellen();
import { nutzung, navGruppen, leerZustand, themeKnopf, kontaktKarte, skriptKarte, wiedervorlageWahl, dialog, delta, h, api, datum, zeit, euro, melde, abmelden, zweiFaktorKarte, pushKarte, rechtFuss, glocke, formular, mobilLeiste } from './common.js';
import { anleitungSeite, erstStart, installBanner } from './anleitung.js';

const root = document.getElementById('app');
let start = null;
const NAV = [['willkommen', 'So geht’s'], ['heute', 'Heute anrufen'], ['uebersicht', 'Meine Zahlen'], ['leads', 'Meine Leads'], ['pipeline', 'Pipeline'], ['angebote', 'Angebotsanfragen'], ['leitfaden', 'Leitfaden'], ['kunden', 'Meine Kunden'], ['provisionen', 'Provisionen'], ['konto', 'Konto']];

/** @type {[string, string[]][]} */
const NAV_GRUPPEN = [['Mein Tag', ['heute', 'leads', 'pipeline', 'angebote']], ['Zahlen & Wissen', ['uebersicht', 'leitfaden']], ['Kunden & Geld', ['kunden', 'provisionen', 'konto', 'willkommen']]];

function gerüst(aktiv, inhalt) {
  const gruppen = NAV_GRUPPEN.map(([titel, ids]) => [titel, NAV.filter(n => ids.includes(n[0])), true]);
  return h('div', { class: 'shell mobilleiste kompakt' },
    h('aside', { class: 'side' }, h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Partnerportal'),
      h('div', { class: 'brandzeile' }, glocke(), themeKnopf()),
      navGruppen(gruppen, aktiv, 'vertrieb'),
      h('div', { class: 'grow' }), h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' }, h('div', { class: 'top' }, h('h1', {}, start.partner.name), h('span', { class: 'pill ' + (start.partner.status === 'aktiv' ? 'ok' : 'warn') }, start.partner.status)), installBanner(), inhalt, rechtFuss()),
    mobilLeiste({ aktiv, gruppen, feste: ['heute', 'leads', 'pipeline', 'uebersicht'], icons: { heute: '☎', leads: '☰', pipeline: '▦', uebersicht: '▥' }, kurz: { heute: 'Anrufe', leads: 'Leads', uebersicht: 'Zahlen' }, schluessel: 'vertrieb' }));
}
function tabelle(spalten, zeilen, leer) {
  if (!zeilen.length) return leerZustand(leer);
  return h('div', { class: 'tablewrap' }, h('table', {}, h('thead', {}, h('tr', {}, spalten.map(s => h('th', {}, s[0])))), h('tbody', {}, zeilen.map(z => h('tr', {}, spalten.map(s => h('td', {}, s[1](z))))))));
}
const pill = (s) => h('span', { class: 'pill ' + (['aktiv', 'ausgezahlt', 'gewonnen', 'angenommen', 'angebot_raus'].includes(s) ? 'ok' : ['onboarding', 'berechnet', 'freigegeben', 'neu', 'angefragt', 'in_pruefung'].includes(s) ? 'warn' : ['verloren', 'storniert', 'gekuendigt', 'beendet', 'abgelehnt'].includes(s) ? 'bad' : '') }, String(s).replace(/_/g, ' '));
const feld = (label, name, extra = {}) => h('div', {}, h('label', {}, label), h('input', { name, ...extra }));
const V = {};

const fortschrittBalken = (ist, ziel) => h('div', { class: 'fortschritt', role: 'progressbar', 'aria-valuenow': String(ist), 'aria-valuemax': String(ziel), 'aria-label': 'Wochenziel' }, h('div', { style: 'width:' + Math.min(100, Math.round(100 * ist / Math.max(1, ziel))) + '%' }));

/** Dialog: Ergebnis eines Gesprächs mit Notiz und Wiedervorlage festhalten, ohne die Liste zu verlassen. */
function gespraechDialog(z, optionen, vorwahl, fertig) {
  const m = h('div'), wv = wiedervorlageWahl(), notiz = h('textarea', { rows: 3, maxlength: 1500, placeholder: 'Kurze Notiz (freiwillig)', 'aria-label': 'Notiz' });
  const sel = h('select', { 'aria-label': 'Ergebnis', onchange: () => vorbelegen() }, optionen.map(o => h('option', { value: o.code, selected: o.code === vorwahl }, o.text)));
  const vorbelegen = () => { const o = optionen.find(x => x.code === sel.value); wv.tag.value = o && o.wiedervorlage_tage ? new Date(Date.now() + o.wiedervorlage_tage * 864e5).toISOString().slice(0, 10) : ''; };
  vorbelegen();
  const d = dialog(z.firma, h('div', {}, h('label', {}, 'Was ist passiert?'), sel, h('label', {}, 'Notiz'), notiz, wv.el, m,
    h('p', {}, h('button', { class: 'btn', onclick: async () => {
      try { const r = await api('/api/vertrieb/leads/' + z.id + '/kontakt', { method: 'POST', body: { ergebnis: sel.value, notiz: notiz.value || null, wiedervorlage: wv.tag.value || null } }); d.zu(); fertig(r); } catch (x) { melde(m, x.message); }
    } }, 'Festhalten'))));
}

V.heute = async () => {
  const [d, z] = await Promise.all([api('/api/vertrieb/heute'), api('/api/vertrieb/zahlen')]);
  const TEMP = { kalt: '❄', warm: '☀', heiss: '🔥' }, opt = d.kontakt_optionen;
  let heuteAnrufe = d.anrufe_heute, woche = z.anrufe_woche, offen = d.gesamt;
  const kopfKarte = h('div', { class: 'card' }), meldung = h('div');
  const kopfNeu = () => kopfKarte.replaceChildren(
    h('p', {}, 'Heute schon ', h('b', {}, heuteAnrufe), ' Anrufe festgehalten. ', offen ? 'Noch ' + offen + ' Leads auf deiner Liste.' : 'Deine Liste ist leer, melde dich bei Markentrix für neue Leads.'),
    fortschrittBalken(woche, z.wochenziel), h('p', { class: 'small muted' }, 'Diese Woche ' + woche + ' von ' + z.wochenziel + ' Anrufen (dein Wochenziel).'),
    d.termine.length ? h('p', { class: 'small' }, '📅 Gebuchte Gespräche in den nächsten 3 Tagen: ' + d.termine.map(t => t.name + ' (' + zeit(t.start) + ')').join(', ')) : '');
  kopfNeu();
  const erledigt = (zeile, r, anruf) => {
    zeile.remove(); offen = Math.max(0, offen - 1); if (anruf) { heuteAnrufe++; woche++; } kopfNeu();
    meldung.replaceChildren(h('div', { class: 'msg ok' }, 'Festgehalten.' + (r && r.wiedervorlage_am ? ' Wiedervorlage am ' + datum(r.wiedervorlage_am) + '.' : '')));
    setTimeout(() => meldung.replaceChildren(), 4000);
  };
  const schnell = async (lead, code, zeile, anruf = true) => { try { erledigt(zeile, await api('/api/vertrieb/leads/' + lead.id + '/kontakt', { method: 'POST', body: { ergebnis: code } }), anruf); } catch (x) { melde(meldung, x.message); } };
  const zeile = (l) => {
    const el = h('div', { class: 'heutezeile' });
    el.append(
      h('div', { class: 'heutekopf' }, h('div', { class: 'grow' }, h('a', { href: '#lead/' + l.id, style: 'font-weight:600;text-decoration:none' }, (TEMP[l.temperatur] || '') + ' ' + l.firma),
        h('div', { class: 'small muted' }, [l.ansprechpartner, l.gruppe || l.branche, l.ort].filter(Boolean).join(' · ') + (l.wiedervorlage_am ? ' · Wiedervorlage ' + datum(l.wiedervorlage_am) : ''))),
        l.telefon ? h('a', { class: 'btn small', href: 'tel:' + l.telefon.replace(/[^+\d]/g, '') }, '📞 ' + l.telefon) : h('span', { class: 'small muted' }, 'keine Nummer')),
      h('div', { class: 'heuteknoepfe' },
        h('button', { class: 'btn sec small', onclick: () => schnell(l, 'anruf_nicht_erreicht', el) }, 'Nicht erreicht'),
        h('button', { class: 'btn sec small', onclick: () => gespraechDialog(l, opt.filter(o => o.code !== 'anruf_nicht_erreicht'), 'anruf_erreicht', (r) => erledigt(el, r, true)) }, 'Gesprochen …'),
        h('button', { class: 'btn sec small', onclick: () => gespraechDialog(l, opt, 'termin', (r) => erledigt(el, r, false)) }, 'Termin …'),
        h('button', { class: 'btn sec small', onclick: () => { if (confirm(l.firma + ': Kein Interesse eintragen? Der Lead wird nicht mehr angerufen.')) schnell(l, 'kein_interesse', el); } }, 'Kein Interesse'),
        h('a', { class: 'btn sec small', href: '#lead/' + l.id }, 'Öffnen')));
    return el;
  };
  const block = (titel, liste, leer) => h('div', { class: 'card' }, h('h2', {}, titel, liste.length ? h('span', { class: 'badge', style: 'margin-left:8px' }, liste.length) : ''), liste.length ? liste.map(zeile) : h('p', { class: 'muted' }, leer));
  return h('div', { class: 'stack' }, kopfKarte, meldung,
    block('Wiedervorlage fällig', d.wiedervorlagen, 'Keine Wiedervorlagen für heute.'),
    block('🔥 Heiße Leads, noch nicht angerufen', d.heiss, 'Keine heißen Leads offen.'),
    block('Neu zugewiesen', d.neu, 'Keine neuen Leads.'));
};

/** „Meine Woche“: Anrufe, Erreicht, Termine, Abschlüsse mit Wochenziel; dazu Quoten und Provisions-Rechenbeispiel. */
function zahlenKarte(z) {
  const kachel = (t, w, extra) => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, t), h('b', {}, w), extra || '');
  const p = z.provision, q = (x) => x === null ? '–' : x + ' %';
  const ziel = async () => {
    const v = prompt('Wochenziel: Wie viele Anrufe pro Woche?', String(z.wochenziel)); if (v === null) return;
    const n = parseInt(v, 10); if (!Number.isFinite(n) || n < 1 || n > 500) { alert('Bitte eine Zahl zwischen 1 und 500 eingeben.'); return; }
    try { await api('/api/vertrieb/ziel', { method: 'PUT', body: { anrufe: n } }); location.reload(); } catch (x) { alert(x.message); }
  };
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Meine Woche'), fortschrittBalken(z.anrufe_woche, z.wochenziel),
      h('p', { class: 'small muted' }, z.anrufe_woche + ' von ' + z.wochenziel + ' Anrufen ', h('button', { class: 'btn sec small', onclick: ziel }, 'Wochenziel ändern'))),
    h('div', { class: 'grid3' }, kachel('Anrufe diese Woche', z.anrufe_woche, delta(z.anrufe_woche, z.anrufe_vorwoche, true, undefined, 'Vorwoche')),
      kachel('Davon erreicht', z.erreicht_woche), kachel('Termine vereinbart', z.termine_woche), kachel('Neue Kunden', z.abschluesse_woche, h('span', { class: 'small muted' }, z.abschluesse_monat + ' diesen Monat'))),
    h('div', { class: 'card' }, h('h2', {}, 'Quoten diesen Monat'),
      h('p', {}, h('b', {}, q(z.quote_erreicht)), ' der Anrufe haben jemanden erreicht (' + z.erreicht_monat + ' von ' + z.anrufe_monat + '). ', h('b', {}, q(z.quote_termin)), ' der Gespräche führten zu einem Termin (' + z.termine_monat + ' von ' + z.erreicht_monat + ').'),
      h('p', { class: 'small muted' }, 'Ein Anruf zählt, sobald du ihn bei einem Lead festgehalten hast.')),
    h('div', { class: 'card' }, h('h2', {}, 'Provision im Blick'),
      h('p', {}, 'Bereits berechnet für diesen Monat: ', h('b', {}, euro(p.monat_cent)), ' · noch nicht ausgezahlt: ', h('b', {}, euro(p.offen_cent))),
      p.rechenbeispiel_cent ? h('p', { class: 'small muted' }, 'Rechenbeispiel: ' + p.offene_angebote + (p.offene_angebote === 1 ? ' Lead steht' : ' Leads stehen') + ' im Status „Angebot“. Würden alle abschließen, wären das bei durchschnittlich ' + euro(p.schnitt_je_kunde_cent) + ' je Kunde etwa ' + euro(p.rechenbeispiel_cent) + ' pro Monat zusätzlich. Das ist nur ein Rechenbeispiel, keine Zusage.')
        : h('p', { class: 'small muted' }, p.offene_angebote ? 'Sobald die erste Provision berechnet wurde, siehst du hier ein Rechenbeispiel für deine offenen Angebote.' : 'Sobald Leads im Status „Angebot“ stehen, siehst du hier ein Rechenbeispiel.')));
}

V.uebersicht = async () => {
  const z = await api('/api/vertrieb/zahlen');
  const s = start.summen, l = start.leads;
  const offeneLeads = Object.entries(l).filter(([k]) => !['gewonnen', 'verloren', 'tot', 'gesperrt'].includes(k)).reduce((a, [, n]) => a + n, 0);
  return h('div', { class: 'stack' }, zahlenKarte(z), h('div', { class: 'grid3' },
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Provision offen'), h('b', {}, euro(s.offen_cent))),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Dieser Monat'), h('b', {}, euro(s.dieser_monat_cent))),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Ausgezahlt dieses Jahr'), h('b', {}, euro(s.ausgezahlt_jahr_cent))),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Meine Kunden'), h('b', {}, start.kunden.length)),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Offene Leads'), h('b', {}, offeneLeads))),
    h('div', { class: 'card' }, h('p', { class: 'muted small' }, '„Offen" ist alles, was berechnet oder freigegeben, aber noch nicht ausgezahlt ist. Die Auszahlung erfolgt durch Markentrix.')));
};

V.pipeline = async () => {
  const lade = () => api('/api/vertrieb/pipeline');
  let board;
  board = pipelineBoard(await lade(), {
    ziele: ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'verloren'], link: (l) => '#lead/' + l.id,
    verschieben: (l, status) => api('/api/vertrieb/leads/' + l.id + '/status', { method: 'POST', body: { status } }),
    neuLaden: async () => { board.neuZeichnen(await lade()); },
  });
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Meine Pipeline'), h('p', { class: 'small muted' }, 'Alle deine Leads nach Stand. „Gewonnen“ setzt Markentrix, sobald der Kunde angelegt ist.')), board);
};

V.willkommen = () => anleitungSeite('vertrieb');
V.leitfaden = async () => {
  const d = await api('/api/vertrieb/leitfaden');
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Telefonleitfaden Kaltakquise (PDF)'), h('p', { class: 'small muted' }, 'Der ausführliche Leitfaden von Markentrix zum Ansehen, Ausdrucken und Nachschlagen. Darunter die Kurzfassung mit Einwänden und Antworten.'),
      h('p', {}, h('a', { class: 'btn', href: '/api/vertrieb/telefonleitfaden.pdf', target: '_blank', rel: 'noopener' }, 'Leitfaden öffnen'), ' ', h('a', { class: 'btn sec', href: '/api/vertrieb/telefonleitfaden.pdf', download: 'Markentrix-Telefonleitfaden.pdf' }, 'Herunterladen'))),
    h('div', { class: 'card' }, h('h2', {}, 'Gesprächsleitfaden'), h('p', { class: 'small muted' }, 'Zum Üben und Nachschlagen, nicht zum Ablesen. Bei jedem Lead gibt es zusätzlich einen persönlichen Vorschlag (KI-Entwurf) und, wenn die Branche passt, einen Branchenhinweis.')),
    d.abschnitte.map(a => h('div', { class: 'card' }, h('h2', {}, a.titel), h('ul', {}, a.punkte.map(p => h('li', {}, p))))),
    h('div', { class: 'card' }, h('h2', {}, 'Wenn der Kunde sagt …'), d.einwaende.map(e => h('details', { style: 'margin:8px 0' }, h('summary', {}, h('b', {}, '„' + e.einwand + '“')), h('p', {}, e.antwort)))),
    h('div', { class: 'card' }, h('h2', {}, 'Branchen-Hinweise'), Object.values(d.branchen).map(b => h('details', { style: 'margin:8px 0' }, h('summary', {}, h('b', {}, b.name)), h('ul', {}, b.tipps.map(t => h('li', {}, t)))))));
};

V.angebote = async () => {
  const d = await api('/api/vertrieb/angebotsanfragen');
  const TXT = { angefragt: 'Angefragt', in_pruefung: 'In Prüfung', angebot_raus: 'Angebot ist raus', angenommen: 'Angenommen', abgelehnt: 'Abgelehnt' };
  return h('div', { class: 'card' }, h('h2', {}, 'Meine Angebotsanfragen'), h('p', { class: 'small muted' }, 'Eine Anfrage stellst du im jeweiligen Lead mit „Angebot anfragen“. Hier siehst du, wie weit Markentrix ist.'),
    tabelle([['Firma', z => h('a', { href: '#lead/' + z.lead_id }, z.firma)], ['Paket', z => z.paket || 'offen'], ['Status', z => h('span', { class: 'pill ' + (['angenommen', 'angebot_raus'].includes(z.status) ? 'ok' : z.status === 'abgelehnt' ? 'bad' : 'warn') }, TXT[z.status])], ['Hinweis von Markentrix', z => z.admin_notiz || ''], ['Stand', z => datum(z.geaendert_am)]], d, 'Noch keine Anfragen.'));
};

V.kunden = async () => h('div', { class: 'card' }, h('h2', {}, 'Meine Kunden'),
  tabelle([['Nr.', z => z.kundennummer], ['Firma', z => z.firma], ['Paket', z => z.paket || '–'], ['Status', z => pill(z.status)], ['Seit', z => datum(z.erstellt_am)]], start.kunden, 'Noch keine Kunden zugeordnet.'));

V.provisionen = async () => {
  const d = await api('/api/vertrieb/provisionen');
  const nachMonat = {};
  d.filter(z => z.status !== 'storniert').forEach(z => { const k = String(z.monat).slice(0, 7); nachMonat[k] = (nachMonat[k] || 0) + z.betrag_cent; });
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Pro Monat'), tabelle([['Monat', z => z[0]], ['Summe', z => euro(z[1])], ['Abrechnung', z => h('a', { href: '/api/vertrieb/abrechnung/' + z[0], target: '_blank', rel: 'noopener' }, 'PDF')]], Object.entries(nachMonat), 'Noch keine Provisionen.')),
    h('div', { class: 'card' }, h('h2', {}, 'Einzelposten'), tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Art', z => ({ laufend: 'Laufend', verlaengerung: 'Verlängerung', rueckbuchung: 'Rückbuchung' })[z.art] || z.art], ['Vertragsmonat', z => z.vertragsmonat || '–'], ['Basis', z => euro(z.basis_cent)], ['%', z => z.prozent], ['Betrag', z => euro(z.betrag_cent)], ['Status', z => pill(z.status)]], d, 'Noch keine Provisionen.')));
};

V.leads = async () => {
  const d = await api('/api/vertrieb/leads'), m = h('div');
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); Object.keys(o).forEach(k => { if (o[k] === '') delete o[k]; });
    try { await api('/api/vertrieb/leads', { method: 'POST', body: o }); location.reload(); } catch (x) { melde(m, x.message); } } },
    h('div', { class: 'form2' }, feld('Firma *', 'firma', { required: true }), feld('Ansprechpartner', 'ansprechpartner'), feld('E-Mail', 'email'), feld('Telefon', 'telefon'), feld('Branche', 'branche'), feld('PLZ', 'plz'), feld('Ort', 'ort'), feld('Website', 'website')),
    h('label', {}, 'Notiz'), h('textarea', { name: 'notiz', rows: 2 }), h('p', {}, h('button', { class: 'btn' }, 'Lead speichern')));
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Meine Leads'),
    tabelle([['Firma', z => h('a', { href: '#lead/' + z.id }, z.firma)], ['Ort', z => z.ort], ['Branche', z => z.branche], ['Status', z => pill(z.status)], ['Einstufung', z => ({ kalt: '❄ Cold', warm: '☀ Warm', heiss: '🔥 HOT' })[z.temperatur] || ''], ['Wiedervorlage', z => z.wiedervorlage_am ? datum(z.wiedervorlage_am) : ''], ['Zuletzt kontaktiert', z => z.letzter_kontakt_am ? datum(z.letzter_kontakt_am) : '–'], ['Angelegt', z => datum(z.erstellt_am)]], d, 'Noch keine Leads.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Lead'), h('p', { class: 'small muted' }, 'Bitte nur Kontakte eintragen, bei denen eine geschäftliche Ansprache zulässig ist.'), m, f));
};

/** Springt zum nächsten Lead der „Heute“-Liste, sonst zurück zur Liste. */
async function naechsterLead(aktuell) {
  try {
    const d = await api('/api/vertrieb/heute');
    const n = [...d.wiedervorlagen, ...d.heiss, ...d.neu].find(x => x.id !== aktuell);
    location.hash = n ? '#lead/' + n.id : '#heute';
  } catch { location.hash = '#heute'; }
}

function branchenKarte(lid) {
  const k = h('div');
  api('/api/vertrieb/leads/' + lid + '/branchenhinweis', { leise: true }).then(r => {
    if (r && r.tipps) k.replaceChildren(h('div', { class: 'card' }, h('h2', {}, 'Branchenhinweis: ' + r.name), h('ul', {}, r.tipps.map(t => h('li', {}, t))), h('p', { class: 'small' }, h('a', { href: '#leitfaden' }, 'Ganzen Leitfaden öffnen'))));
  }).catch(() => {});
  return k;
}

function angebotKarte(lid, l) {
  const k = h('div', { class: 'card' }), m = h('div');
  const TXT = { angefragt: 'Angefragt', in_pruefung: 'In Prüfung', angebot_raus: 'Angebot ist raus', angenommen: 'Angenommen', abgelehnt: 'Abgelehnt' };
  const laden = async () => {
    const [pk, liste] = await Promise.all([api('/api/vertrieb/pakete'), api('/api/vertrieb/leads/' + lid + '/angebotsanfragen')]);
    const offen = liste.some(a => ['angefragt', 'in_pruefung'].includes(a.status));
    const paket = h('select', { name: 'paket_code', 'aria-label': 'Paket' }, h('option', { value: '' }, 'Noch offen, Markentrix berät'), pk.map(p => h('option', { value: p.code }, p.name)));
    const notiz = h('textarea', { rows: 2, maxlength: 1500, 'aria-label': 'Notiz für Markentrix', placeholder: 'Was hat der Kunde gesagt? Besonderheiten, Wunschtermin …' });
    k.replaceChildren(h('h2', {}, 'Angebot anfragen'),
      liste.length ? h('ul', {}, liste.map(a => h('li', {}, h('span', { class: 'pill ' + (['angenommen', 'angebot_raus'].includes(a.status) ? 'ok' : a.status === 'abgelehnt' ? 'bad' : 'warn') }, TXT[a.status]), ' ' + (a.paket || 'Paket offen') + ' · ' + datum(a.erstellt_am) + (a.admin_notiz ? ' · ' + a.admin_notiz : '')))) : '',
      m,
      ['gewonnen', 'verloren', 'gesperrt', 'consent_ausstehend'].includes(l.status) ? h('p', { class: 'small muted' }, 'Für diesen Lead ist keine Anfrage mehr möglich.')
        : offen ? h('p', { class: 'small muted' }, 'Es läuft bereits eine Anfrage. Markentrix meldet sich, sobald sich der Status ändert.')
          : h('div', {}, h('label', {}, 'Paket'), paket, h('label', {}, 'Notiz'), notiz, h('p', {}, h('button', { class: 'btn', onclick: async () => {
            try { await api('/api/vertrieb/leads/' + lid + '/angebotsanfrage', { method: 'POST', body: { paket_code: paket.value || null, notiz: notiz.value || null } }); await laden(); melde(m, 'Anfrage ist bei Markentrix angekommen.', 'ok'); } catch (x) { melde(m, x.message); }
          } }, 'Angebot anfragen'))));
  };
  laden().catch(x => k.replaceChildren(h('h2', {}, 'Angebot anfragen'), h('div', { class: 'msg err' }, x.message)));
  return k;
}

function nachgespraechKarte(lid) {
  const m = h('div');
  const oeffnen = async () => {
    try {
      const r = await api('/api/vertrieb/leads/' + lid + '/nachgespraech');
      const betreff = h('input', { value: r.betreff, 'aria-label': 'Betreff' }), text = h('textarea', { rows: 10, 'aria-label': 'Text' }, r.text);
      text.value = r.text;
      const d = dialog('Mail nach dem Gespräch', h('div', {}, h('p', { class: 'small muted' }, 'Entwurf zum Anpassen. Das Portal verschickt nichts: „In Mail-Programm öffnen“ startet dein eigenes Mailprogramm.'),
        h('label', {}, 'An'), h('input', { value: r.an || '', readonly: true, 'aria-label': 'Empfänger' }), h('label', {}, 'Betreff'), betreff, h('label', {}, 'Text'), text,
        h('p', { class: 'row', style: 'gap:8px;flex-wrap:wrap' },
          r.an ? h('a', { class: 'btn', href: 'mailto:' + encodeURIComponent(r.an) + '?subject=' + encodeURIComponent(betreff.value) + '&body=' + encodeURIComponent(text.value), onclick: (e) => { e.currentTarget.href = 'mailto:' + encodeURIComponent(r.an) + '?subject=' + encodeURIComponent(betreff.value) + '&body=' + encodeURIComponent(text.value); } }, 'In Mail-Programm öffnen') : h('span', { class: 'small muted' }, 'Keine E-Mail-Adresse beim Lead hinterlegt.'),
          h('button', { class: 'btn sec', onclick: async () => { try { await navigator.clipboard.writeText(betreff.value + '\n\n' + text.value); melde(m, 'Kopiert.', 'ok'); } catch { text.select(); } } }, 'Text kopieren'))), true);
      void d;
    } catch (x) { melde(m, x.message); }
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Nach dem Gespräch'), h('p', { class: 'small muted' }, 'Kurze Dankes-Mail mit Zusammenfassung als Entwurf.'), m, h('button', { class: 'btn sec', onclick: oeffnen }, 'Mail-Entwurf öffnen'));
}

async function leadDetail(lid) {
  const d = await api('/api/vertrieb/leads/' + lid), l = d.lead, m = h('div');
  const gesperrt = ['gewonnen', 'gesperrt', 'consent_ausstehend'].includes(l.status);
  const st = h('select', { style: 'width:auto', disabled: gesperrt, onchange: async (e) => { try { await api('/api/vertrieb/leads/' + lid + '/status', { method: 'POST', body: { status: e.target.value } }); location.reload(); } catch (x) { melde(m, x.message); } } },
    (gesperrt ? [l.status] : ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'verloren']).map(s => h('option', { value: s, selected: s === l.status }, s.replace(/_/g, ' '))));
  const akt = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/vertrieb/leads/' + lid + '/aktivitaet', { method: 'POST', body: formular(e.target) }); location.reload(); } catch (x) { melde(m, x.message); } } },
    h('div', { class: 'row' }, h('div', { style: 'width:170px' }, h('select', { name: 'art' }, ['notiz', 'anruf', 'mail_gesendet', 'antwort', 'termin'].map(a => h('option', { value: a }, a.replace(/_/g, ' '))))),
      h('div', { class: 'grow' }, h('input', { name: 'inhalt', placeholder: 'Was ist passiert?', required: true })), h('button', { class: 'btn' }, 'Eintragen')));
  return h('div', { class: 'stack' }, h('div', { class: 'top' }, h('h1', {}, l.firma), st, h('a', { class: 'btn sec small', href: '#leads' }, '← Liste')), m,
    h('div', { class: 'card' }, h('div', { class: 'form2' }, [['Ansprechpartner', l.ansprechpartner], ['E-Mail', l.email], ['Telefon', l.telefon], ['Website', l.website], ['Branche', l.branche], ['Ort', [l.plz, l.ort].filter(Boolean).join(' ')]].map(([a, b]) => h('div', {}, h('div', { class: 'small muted' }, a), h('div', {}, b || '–')))), l.notiz && h('p', { class: 'muted' }, l.notiz)),
    kontaktKarte(d.kontakt_optionen, '/api/vertrieb/leads/' + lid + '/kontakt', l.wiedervorlage_am, { naechster: () => naechsterLead(lid) }),
    branchenKarte(lid), angebotKarte(lid, l), nachgespraechKarte(lid),
    skriptKarte(l.skript, l.skript_am, '/api/vertrieb/leads/' + lid + '/skript'),
    h('div', { class: 'card' }, h('h2', {}, 'Verlauf'), akt, h('div', { style: 'height:10px' }), tabelle([['Wann', z => zeit(z.zeit)], ['Art', z => z.art.replace(/_/g, ' ')], ['Inhalt', z => z.inhalt]], d.aktivitaeten, 'Noch keine Einträge.')));
}

V.konto = async () => {
  const m = h('div');
  const f = h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault(); try { await api('/api/vertrieb/passwort', { method: 'POST', body: formular(e.target) }); melde(m, 'Passwort geändert.', 'ok'); e.target.reset(); } catch (x) { melde(m, x.message); } } },
    feld('Aktuelles Passwort', 'alt', { type: 'password', required: true, autocomplete: 'current-password' }), feld('Neues Passwort (mind. 10 Zeichen)', 'neu', { type: 'password', required: true, minlength: 10, autocomplete: 'new-password' }),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Passwort ändern')));
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Passwort ändern'), m, f), pushKarte('vertrieb'), zweiFaktorKarte());
};

let aufruf = 0;
async function zeige() {
  const dieser = ++aufruf;
  const hash = (location.hash || '#heute').slice(1), seite = hash.split('/')[0];
  nutzung(V[seite] || seite === 'lead' ? seite : 'heute');
  let inhalt;
  try { inhalt = seite === 'lead' ? await leadDetail(hash.split('/')[1]) : await (V[seite] || V.heute)(); } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  if (dieser !== aufruf) return;   // inzwischen wurde eine andere Seite geöffnet
  root.replaceChildren(gerüst(seite === 'lead' ? 'leads' : (V[seite] ? seite : 'heute'), inhalt));
}
(async () => {
  try { const me = await api('/api/me'); if (me.rolle !== 'vertrieb') { location.href = me.rolle === 'admin' ? '/admin' : '/app'; return; }
    if (me.zwei_faktor_pflicht) { root.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;margin:40px auto' }, h('h1', {}, 'Zwei-Faktor-Anmeldung einrichten'), h('p', {}, 'Für Vertriebs-Zugänge ist die Zwei-Faktor-Anmeldung Pflicht. Bitte jetzt mit einer Authenticator-App einrichten, danach geht es direkt weiter.'), zweiFaktorKarte(), h('p', {}, h('button', { class: 'btn', onclick: () => location.reload() }, 'Weiter zum Portal')))); return; }
    start = await api('/api/vertrieb/start'); } catch (e) { return; }
  window.addEventListener('hashchange', zeige); zeige(); erstStart().catch(() => {});
})();
