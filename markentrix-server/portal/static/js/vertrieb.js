import { kontaktKarte, skriptKarte, h, api, datum, zeit, euro, melde, abmelden, zweiFaktorKarte, pushKarte, rechtFuss, glocke } from './common.js';

const root = document.getElementById('app');
let start = null;
const NAV = [['heute', 'Heute anrufen'], ['uebersicht', 'Übersicht'], ['kunden', 'Meine Kunden'], ['leads', 'Meine Leads'], ['provisionen', 'Provisionen'], ['konto', 'Konto']];

function gerüst(aktiv, inhalt) {
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' }, h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Partnerportal'),
      h('div', { class: 'brandzeile' }, glocke()),
      NAV.map(n => h('a', { class: 'nav' + (n[0] === aktiv ? ' on' : ''), href: '#' + n[0] }, n[1])),
      h('div', { class: 'grow' }), h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' }, h('div', { class: 'top' }, h('h1', {}, start.partner.name), h('span', { class: 'pill ' + (start.partner.status === 'aktiv' ? 'ok' : 'warn') }, start.partner.status)), inhalt, rechtFuss()));
}
function tabelle(spalten, zeilen, leer) {
  if (!zeilen.length) return h('p', { class: 'muted' }, leer);
  return h('div', { class: 'tablewrap' }, h('table', {}, h('thead', {}, h('tr', {}, spalten.map(s => h('th', {}, s[0])))), h('tbody', {}, zeilen.map(z => h('tr', {}, spalten.map(s => h('td', {}, s[1](z))))))));
}
const pill = (s) => h('span', { class: 'pill ' + (['aktiv', 'ausgezahlt', 'gewonnen'].includes(s) ? 'ok' : ['onboarding', 'berechnet', 'freigegeben', 'neu'].includes(s) ? 'warn' : ['verloren', 'storniert', 'gekuendigt', 'beendet'].includes(s) ? 'bad' : '') }, String(s).replace(/_/g, ' '));
const feld = (label, name, extra = {}) => h('div', {}, h('label', {}, label), h('input', { name, ...extra }));
const V = {};

V.heute = async () => {
  const d = await api('/api/vertrieb/heute');
  const TEMP = { kalt: '❄', warm: '☀', heiss: '🔥' };
  const zeile = (z) => h('div', { class: 'row', style: 'padding:8px 0;border-bottom:1px solid var(--line);flex-wrap:nowrap' },
    h('div', { class: 'grow' }, h('a', { href: '#lead/' + z.id, style: 'font-weight:600;text-decoration:none' }, (TEMP[z.temperatur] || '') + ' ' + z.firma),
      h('div', { class: 'small muted' }, [z.ansprechpartner, z.gruppe || z.branche, z.ort].filter(Boolean).join(' · ') + (z.wiedervorlage_am ? ' · Wiedervorlage ' + datum(z.wiedervorlage_am) : ''))),
    z.telefon ? h('a', { class: 'btn small', href: 'tel:' + z.telefon.replace(/[^+\d]/g, '') }, '📞 ' + z.telefon) : h('span', { class: 'small muted' }, 'keine Nummer'),
    h('a', { class: 'btn sec small', href: '#lead/' + z.id }, 'Öffnen'));
  const block = (titel, liste, leer) => h('div', { class: 'card' }, h('h2', {}, titel, liste.length ? h('span', { class: 'badge', style: 'margin-left:8px' }, liste.length) : ''), liste.length ? liste.map(zeile) : h('p', { class: 'muted' }, leer));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('p', {}, 'Heute schon ', h('b', {}, d.anrufe_heute), ' Anrufe festgehalten. ', d.gesamt ? 'Noch ' + d.gesamt + ' Leads auf deiner Liste.' : 'Deine Liste ist leer, melde dich bei Markentrix für neue Leads.'),
      d.termine.length ? h('p', { class: 'small' }, '📅 Gebuchte Gespräche in den nächsten 3 Tagen: ' + d.termine.map(t => t.name + ' (' + zeit(t.start) + ')').join(', ')) : ''),
    block('Wiedervorlage fällig', d.wiedervorlagen, 'Keine Wiedervorlagen für heute.'),
    block('🔥 Heiße Leads, noch nicht angerufen', d.heiss, 'Keine heißen Leads offen.'),
    block('Neu zugewiesen', d.neu, 'Keine neuen Leads.'));
};

V.uebersicht = async () => {
  const s = start.summen, l = start.leads;
  const offeneLeads = Object.entries(l).filter(([k]) => !['gewonnen', 'verloren', 'tot', 'gesperrt'].includes(k)).reduce((a, [, n]) => a + n, 0);
  return h('div', {}, h('div', { class: 'grid3' },
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Provision offen'), h('b', {}, euro(s.offen_cent))),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Dieser Monat'), h('b', {}, euro(s.dieser_monat_cent))),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Ausgezahlt dieses Jahr'), h('b', {}, euro(s.ausgezahlt_jahr_cent))),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Meine Kunden'), h('b', {}, start.kunden.length)),
    h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Offene Leads'), h('b', {}, offeneLeads))),
    h('div', { class: 'card' }, h('p', { class: 'muted small' }, '„Offen" ist alles, was berechnet oder freigegeben, aber noch nicht ausgezahlt ist. Die Auszahlung erfolgt durch Markentrix.')));
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
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); Object.keys(o).forEach(k => { if (o[k] === '') delete o[k]; });
    try { await api('/api/vertrieb/leads', { method: 'POST', body: o }); location.reload(); } catch (x) { melde(m, x.message); } } },
    h('div', { class: 'form2' }, feld('Firma *', 'firma', { required: true }), feld('Ansprechpartner', 'ansprechpartner'), feld('E-Mail', 'email'), feld('Telefon', 'telefon'), feld('Branche', 'branche'), feld('PLZ', 'plz'), feld('Ort', 'ort'), feld('Website', 'website')),
    h('label', {}, 'Notiz'), h('textarea', { name: 'notiz', rows: 2 }), h('p', {}, h('button', { class: 'btn' }, 'Lead speichern')));
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Meine Leads'),
    tabelle([['Firma', z => h('a', { href: '#lead/' + z.id }, z.firma)], ['Ort', z => z.ort], ['Branche', z => z.branche], ['Status', z => pill(z.status)], ['Einstufung', z => ({ kalt: '❄ Cold', warm: '☀ Warm', heiss: '🔥 HOT' })[z.temperatur] || ''], ['Wiedervorlage', z => z.wiedervorlage_am ? datum(z.wiedervorlage_am) : ''], ['Zuletzt kontaktiert', z => z.letzter_kontakt_am ? datum(z.letzter_kontakt_am) : '–'], ['Angelegt', z => datum(z.erstellt_am)]], d, 'Noch keine Leads.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Lead'), h('p', { class: 'small muted' }, 'Bitte nur Kontakte eintragen, bei denen eine geschäftliche Ansprache zulässig ist.'), m, f));
};

async function leadDetail(lid) {
  const d = await api('/api/vertrieb/leads/' + lid), l = d.lead, m = h('div');
  const gesperrt = ['gewonnen', 'gesperrt', 'consent_ausstehend'].includes(l.status);
  const st = h('select', { style: 'width:auto', disabled: gesperrt, onchange: async (e) => { try { await api('/api/vertrieb/leads/' + lid + '/status', { method: 'POST', body: { status: e.target.value } }); location.reload(); } catch (x) { melde(m, x.message); } } },
    (gesperrt ? [l.status] : ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'verloren']).map(s => h('option', { value: s, selected: s === l.status }, s.replace(/_/g, ' '))));
  const akt = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/vertrieb/leads/' + lid + '/aktivitaet', { method: 'POST', body: Object.fromEntries(new FormData(e.target)) }); location.reload(); } catch (x) { melde(m, x.message); } } },
    h('div', { class: 'row' }, h('div', { style: 'width:170px' }, h('select', { name: 'art' }, ['notiz', 'anruf', 'mail_gesendet', 'antwort', 'termin'].map(a => h('option', { value: a }, a.replace(/_/g, ' '))))),
      h('div', { class: 'grow' }, h('input', { name: 'inhalt', placeholder: 'Was ist passiert?', required: true })), h('button', { class: 'btn' }, 'Eintragen')));
  return h('div', { class: 'stack' }, h('div', { class: 'top' }, h('h1', {}, l.firma), st, h('a', { class: 'btn sec small', href: '#leads' }, '← Liste')), m,
    h('div', { class: 'card' }, h('div', { class: 'form2' }, [['Ansprechpartner', l.ansprechpartner], ['E-Mail', l.email], ['Telefon', l.telefon], ['Website', l.website], ['Branche', l.branche], ['Ort', [l.plz, l.ort].filter(Boolean).join(' ')]].map(([a, b]) => h('div', {}, h('div', { class: 'small muted' }, a), h('div', {}, b || '–')))), l.notiz && h('p', { class: 'muted' }, l.notiz)),
    kontaktKarte(d.kontakt_optionen, '/api/vertrieb/leads/' + lid + '/kontakt', l.wiedervorlage_am),
    skriptKarte(l.skript, l.skript_am, '/api/vertrieb/leads/' + lid + '/skript'),
    h('div', { class: 'card' }, h('h2', {}, 'Verlauf'), akt, h('div', { style: 'height:10px' }), tabelle([['Wann', z => zeit(z.zeit)], ['Art', z => z.art.replace(/_/g, ' ')], ['Inhalt', z => z.inhalt]], d.aktivitaeten, 'Noch keine Einträge.')));
}

V.konto = async () => {
  const m = h('div');
  const f = h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault(); try { await api('/api/vertrieb/passwort', { method: 'POST', body: Object.fromEntries(new FormData(e.target)) }); melde(m, 'Passwort geändert.', 'ok'); e.target.reset(); } catch (x) { melde(m, x.message); } } },
    feld('Aktuelles Passwort', 'alt', { type: 'password', required: true, autocomplete: 'current-password' }), feld('Neues Passwort (mind. 10 Zeichen)', 'neu', { type: 'password', required: true, minlength: 10, autocomplete: 'new-password' }),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Passwort ändern')));
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Passwort ändern'), m, f), pushKarte('vertrieb'), zweiFaktorKarte());
};

async function zeige() {
  const hash = (location.hash || '#heute').slice(1), seite = hash.split('/')[0];
  let inhalt;
  try { inhalt = seite === 'lead' ? await leadDetail(hash.split('/')[1]) : await (V[seite] || V.heute)(); } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  root.replaceChildren(gerüst(seite === 'lead' ? 'leads' : (V[seite] ? seite : 'heute'), inhalt));
}
(async () => {
  try { const me = await api('/api/me'); if (me.rolle !== 'vertrieb') { location.href = me.rolle === 'admin' ? '/admin' : '/app'; return; } start = await api('/api/vertrieb/start'); } catch (e) { return; }
  window.addEventListener('hashchange', zeige); zeige();
})();
