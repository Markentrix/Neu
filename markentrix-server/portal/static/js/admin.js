import { h, api, datum, zeit, euro, melde, abmelden } from './common.js';

const root = document.getElementById('app');
const NAV = [['uebersicht', 'Übersicht'], ['kunden', 'Kunden'], ['neu', 'Neuer Kunde'], ['vertrieb', 'Vertriebler'], ['leads', 'Leads'], ['websites', 'Websites & Demos'], ['preise', 'Preise & Konditionen'], ['compliance', 'Datenschutz & Qualität'], ['katalog', 'Pakete (Katalog)'], ['protokoll', 'Protokoll']];
let paketListe = [];

function gerüst(aktiv, inhalt) {
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Admin'),
      NAV.map(n => h('a', { class: 'nav' + (n[0] === aktiv ? ' on' : ''), href: '#' + n[0] }, n[1])),
      h('a', { class: 'nav', href: location.origin.replace('//portal.', '//panel.'), target: '_blank', rel: 'noopener' }, 'Server-Dashboard ↗'),
      h('div', { class: 'grow' }),
      h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' }, inhalt));
}
function tabelle(spalten, zeilen, leer = 'Nichts vorhanden.') {
  if (!zeilen.length) return h('p', { class: 'muted' }, leer);
  return h('div', { class: 'tablewrap' }, h('table', {},
    h('thead', {}, h('tr', {}, spalten.map(s => h('th', {}, s[0])))),
    h('tbody', {}, zeilen.map(z => h('tr', {}, spalten.map(s => h('td', {}, s[1](z))))))));
}
const pill = (s) => h('span', { class: 'pill ' + (['aktiv', 'live', 'veroeffentlicht'].includes(s) ? 'ok' : ['pausiert', 'onboarding', 'beauftragt', 'in_einrichtung', 'demo'].includes(s) ? 'warn' : ['gekuendigt', 'beendet', 'fehler'].includes(s) ? 'bad' : '') }, String(s).replace('_', ' '));
const kopf = (t, ...r) => h('div', { class: 'top' }, h('h1', {}, t), r);
const feld = (label, name, wert = '', extra = {}) => h('div', {}, h('label', {}, label), h('input', { name, value: wert || '', ...extra }));
const leerzu = (o) => { Object.keys(o).forEach(k => { if (o[k] === '') delete o[k]; }); return o; };

const V = {};

V.uebersicht = async () => {
  const d = await api('/api/admin/uebersicht');
  const s = d.kunden_status, summe = Object.values(s).reduce((a, b) => a + b, 0);
  return h('div', {}, kopf('Übersicht'),
    h('div', { class: 'grid3' },
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Kunden gesamt'), h('b', {}, summe)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Aktiv'), h('b', {}, s.aktiv || 0)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Im Onboarding'), h('b', {}, s.onboarding || 0)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Monatlich (gebucht)'), h('b', {}, euro(d.monatlich_cent))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Neue Anfragen'), h('b', {}, d.neue_anfragen)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Uploads (7 Tage)'), h('b', {}, d.uploads_7d))),
    h('div', { class: 'card' }, h('h2', {}, 'Letzte Aktionen'), tabelle([['Zeit', z => zeit(z.zeit)], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d.letzte_aktionen)));
};

V.kunden = async () => {
  const q = h('input', { placeholder: 'Suchen nach Firma, Nummer, E-Mail …' });
  const box = h('div');
  const lade = async () => {
    const d = await api('/api/admin/kunden?q=' + encodeURIComponent(q.value));
    box.replaceChildren(tabelle([
      ['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Paket', z => z.paket || '–'],
      ['Status', z => pill(z.status)], ['Module', z => z.module_aktiv], ['Zugang', z => z.zugang_aktiv ? 'ja' : 'nein'], ['Domain', z => z.domain]], d, 'Noch keine Kunden.'));
  };
  let t; q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(lade, 250); });
  await lade();
  return h('div', {}, kopf('Kunden', h('a', { class: 'btn', href: '#neu' }, '+ Neuer Kunde')), h('div', { class: 'card' }, q, h('div', { style: 'height:12px' }), box));
};

V.neu = async () => {
  const m = h('div');
  const paket = h('select', { name: 'paket_code' }, h('option', { value: '' }, '– kein Paket –'), paketListe.map(p => h('option', { value: p.code }, p.name)));
  const einl = h('input', { type: 'checkbox', name: 'einladen', checked: true, style: 'width:auto' });
  const f = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const d = leerzu(Object.fromEntries(new FormData(e.target))); d.einladen = einl.checked;
    try {
      const r = await api('/api/admin/kunden', { method: 'POST', body: d });
      m.replaceChildren(h('div', { class: 'msg ok' }, 'Kunde ' + r.kundennummer + ' angelegt.'),
        r.einladungslink ? h('div', { class: 'msg info' }, 'Einladungslink (7 Tage gültig, einmalig an den Kunden senden): ', h('br'), r.einladungslink) : '',
        h('p', {}, h('a', { class: 'btn', href: '#kunde/' + r.id }, 'Zum Kunden')));
      e.target.reset();
    } catch (x) { melde(m, x.message); }
  } },
    h('div', { class: 'form2' },
      feld('Firma *', 'firma', '', { required: true }), feld('Rechtsform', 'rechtsform'), feld('Ansprechpartner', 'ansprechpartner'),
      feld('E-Mail (zugleich Login)', 'email', '', { type: 'email' }), feld('Telefon', 'telefon'), feld('Branche', 'branche'),
      feld('Straße', 'strasse'), feld('PLZ', 'plz'), feld('Ort', 'ort'), feld('Website-Domain (z. B. firma.de)', 'domain'),
      h('div', {}, h('label', {}, 'Paket'), paket)),
    h('label', {}, 'Notizen'), h('textarea', { name: 'notizen', rows: 3 }),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, einl, 'Einladungslink für das Portal erzeugen'),
    h('p', {}, h('button', { class: 'btn' }, 'Kunde anlegen')));
  return h('div', {}, kopf('Neuer Kunde'), h('div', { class: 'card' }, m, f));
};

V.katalog = async () => {
  const d = await api('/api/admin/katalog');
  return h('div', { class: 'stack' }, kopf('Pakete & Preise'),
    h('div', { class: 'card' }, h('h2', {}, 'Produkte (aktuelle Preise)'),
      tabelle([['Code', z => z.code], ['Name', z => z.name], ['Einrichtung', z => euro(z.einrichtung_cent)], ['Monatlich', z => euro(z.monatlich_cent)], ['Projekt', z => euro(z.projekt_cent)]], d.produkte)),
    h('div', { class: 'card' }, h('h2', {}, 'Module'), tabelle([['Code', z => z.code], ['Name', z => z.name], ['Art', z => z.art], ['Beschreibung', z => z.beschreibung]], d.module)),
    h('p', { class: 'muted small' }, 'Preise ändern: neue Zeile in produkt_preise mit späterem gueltig_ab (mkctl psql). Bestehende Buchungen behalten ihren Preis.'));
};

V.websites = async () => {
  const d = await api('/api/admin/websites');
  const m = h('div');
  const mb = (b) => b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
  const wann = (t) => new Date(t * 1000).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' });
  const loesch = (z) => z.loeschung_laeuft ? h('span', { class: 'pill warn' }, 'wird gelöscht …') :
    h('button', { class: 'btn small bad', onclick: async () => {
      const eingabe = prompt('Zum Löschen den Namen genau eintippen:\n' + z.name + '\n\nDie Seite geht offline und liegt ' + d.aufbewahrung_tage + ' Tage im Papierkorb.');
      if (eingabe === null) return;
      try { const r = await api('/api/admin/websites/loeschen', { method: 'POST', body: { art: z.art, name: z.name, bestaetigung: eingabe } }); melde(m, r.hinweis, 'ok'); setTimeout(() => location.reload(), 1500); }
      catch (x) { melde(m, x.message); }
    } }, 'Löschen');
  const zurueck = (z) => h('button', { class: 'btn small sec', onclick: async () => {
    try { const r = await api('/api/admin/websites/wiederherstellen', { method: 'POST', body: { id: z.id } }); melde(m, r.hinweis, 'ok'); setTimeout(() => location.reload(), 1500); }
    catch (x) { melde(m, x.message); }
  } }, 'Wiederherstellen');
  return h('div', { class: 'stack' }, kopf('Websites & Demos'), m,
    h('div', { class: 'card' }, h('h2', {}, 'Aktiv'),
      tabelle([['Art', z => z.art === 'live' ? 'Live' : 'Demo'], ['Name', z => z.name], ['Kunde', z => z.kunde], ['Größe', z => mb(z.groesse)], ['Dateien', z => z.dateien], ['Zuletzt geändert', z => z.geaendert ? wann(z.geaendert) : ''], ['', loesch]], d.aktiv, 'Noch keine Seiten angelegt (mkctl site-add / demo-add).')),
    h('div', { class: 'card' }, h('h2', {}, 'Papierkorb'), h('p', { class: 'small muted' }, 'Gelöschte Seiten bleiben ' + d.aufbewahrung_tage + ' Tage erhalten und werden dann endgültig entfernt.'),
      tabelle([['Art', z => z.art === 'live' ? 'Live' : 'Demo'], ['Name', z => z.name], ['Gelöscht', z => wann(z.geloescht)], ['Größe', z => mb(z.groesse)], ['', zurueck]], d.papierkorb, 'Papierkorb ist leer.')));
};


const fehler = (m, x) => melde(m, x.message);
const fmtEuro = (c) => euro(c);
const zahlenfeld = (name, label, wert) => feld(label, name, wert === null || wert === undefined ? '' : (wert / 100).toFixed(2), { type: 'number', step: '0.01', min: '0' });
const cent = (v) => v === undefined || v === '' ? null : Math.round(Number(v) * 100);
const knopf = (text, fn, art = 'sec') => h('button', { class: 'btn small ' + art, onclick: fn }, text);
const bestaetigt = async (m, fn, ok = 'Gespeichert.') => { try { await fn(); melde(m, ok, 'ok'); setTimeout(() => location.reload(), 700); } catch (x) { fehler(m, x); } };
const select = (name, optionen, wert, extra = {}) => h('select', { name, ...extra }, optionen.map(o => { const [v, l] = Array.isArray(o) ? o : [o, o]; return h('option', { value: v, selected: v === wert }, String(l).replace(/_/g, ' ')); }));

// ---------------------------------------------------------------- Vertriebler
V.vertrieb = async () => {
  const d = await api('/api/admin/vertrieb/partner');
  const m = h('div');
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = leerzu(Object.fromEntries(new FormData(e.target)));
    bestaetigt(m, () => api('/api/admin/vertrieb/partner', { method: 'POST', body: o }), 'Vertriebler angelegt.'); } },
    h('div', { class: 'form2' }, feld('Name *', 'name', '', { required: true }), feld('Firma', 'firma'), feld('E-Mail', 'email', '', { type: 'email' }), feld('Telefon', 'telefon'),
      h('div', {}, h('label', {}, 'Status'), select('status', ['aktiv', 'anfrage', 'pausiert', 'beendet'], 'aktiv'))),
    h('p', {}, h('button', { class: 'btn' }, 'Vertriebler anlegen')));
  const aktiv = d.filter(p => p.status === 'aktiv').length;
  return h('div', { class: 'stack' }, kopf('Vertriebler', h('span', { class: 'pill ok' }, aktiv + ' aktiv')),
    h('div', { class: 'card' }, tabelle([['Name', z => h('a', { href: '#partner/' + z.id }, z.name)], ['Firma', z => z.firma], ['Status', z => pill(z.status)], ['Kunden', z => z.kunden], ['Offene Leads', z => z.offene_leads], ['Provision offen', z => fmtEuro(z.offen_cent)], ['IBAN', z => z.iban_hinterlegt ? 'ja' : 'nein']], d, 'Noch keine Vertriebler.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Vertriebler'), m, f));
};

async function partnerDetail(pid) {
  const d = await api('/api/admin/vertrieb/partner/' + pid), p = d.partner, m = h('div'), mp = h('div');
  const stamm = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); o.iban_hinterlegt = e.target.iban.checked; if (!o.vereinbarung_am) delete o.vereinbarung_am; delete o.iban;
    bestaetigt(m, () => api('/api/admin/vertrieb/partner/' + pid, { method: 'PATCH', body: o })); } },
    h('div', { class: 'form2' }, feld('Name', 'name', p.name), feld('Firma', 'firma', p.firma), feld('E-Mail', 'email', p.email), feld('Telefon', 'telefon', p.telefon),
      h('div', {}, h('label', {}, 'Status'), select('status', PARTNER, p.status)), feld('Vereinbarung am', 'vereinbarung_am', p.vereinbarung_am ? String(p.vereinbarung_am).slice(0, 10) : '', { type: 'date' })),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', name: 'iban', checked: p.iban_hinterlegt, style: 'width:auto' }), 'Bankverbindung für Auszahlung hinterlegt'),
    h('label', {}, 'Notiz'), h('textarea', { name: 'notiz', rows: 2 }, p.notiz || ''), h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  const naechster = { berechnet: ['freigegeben', 'Freigeben'], freigegeben: ['ausgezahlt', 'Als ausgezahlt'] };
  const provAktion = (z) => h('span', { class: 'row' }, naechster[z.status] && knopf(naechster[z.status][1], () => bestaetigt(mp, () => api('/api/admin/vertrieb/provisionen/' + z.id + '/status', { method: 'POST', body: { status: naechster[z.status][0] } }))),
    ['berechnet', 'freigegeben'].includes(z.status) && knopf('Stornieren', () => confirm('Provision stornieren?') && bestaetigt(mp, () => api('/api/admin/vertrieb/provisionen/' + z.id + '/status', { method: 'POST', body: { status: 'storniert' } })), 'bad'));
  const summe = d.provisionen.filter(z => ['berechnet', 'freigegeben'].includes(z.status)).reduce((a, z) => a + z.betrag_cent, 0);
  return h('div', { class: 'stack' }, kopf(p.name, pill(p.status), h('a', { class: 'btn sec small', href: '#vertrieb' }, '← Liste')),
    h('div', { class: 'card' }, h('h2', {}, 'Stammdaten'), m, stamm),
    h('div', { class: 'card' }, h('h2', {}, 'Zugeordnete Kunden (' + d.kunden.length + ')'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Paket', z => z.paket || '–'], ['Status', z => pill(z.status)], ['Monatlich', z => fmtEuro(z.monatlich_cent)]], d.kunden, 'Noch keine Kunden. Zuordnung im Kunden unter Stammdaten (Feld Vertriebler).')),
    h('div', { class: 'card' }, h('h2', {}, 'Provisionen'), h('p', { class: 'small muted' }, 'Offen (berechnet/freigegeben): ' + fmtEuro(summe)), mp,
      tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Vertragsmonat', z => z.vertragsmonat], ['Basis', z => fmtEuro(z.basis_cent)], ['%', z => z.prozent], ['Betrag', z => fmtEuro(z.betrag_cent)], ['Status', z => pill(z.status)], ['', provAktion]], d.provisionen, 'Noch keine Provisionen berechnet.')),
    h('div', { class: 'card' }, h('h2', {}, 'Leads'), tabelle([['Firma', z => h('a', { href: '#lead/' + z.id }, z.firma)], ['Ort', z => z.ort], ['Status', z => pill(z.status)], ['Angelegt', z => datum(z.erstellt_am)]], d.leads, 'Keine Leads zugeordnet.')));
}

// ---------------------------------------------------------------- Leads
const LEAD_ST = ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'gewonnen', 'verloren', 'gesperrt', 'consent_ausstehend', 'tot'];
const PARTNER = ['anfrage', 'aktiv', 'pausiert', 'beendet'];
V.leads = async () => {
  const filter = new URLSearchParams(location.hash.split('?')[1] || '').get('status') || '';
  const [d, partner] = await Promise.all([api('/api/admin/leads?status=' + encodeURIComponent(filter)), api('/api/admin/vertrieb/partnerliste')]);
  const m = h('div');
  const tabs = h('div', { class: 'tabs' }, h('button', { class: filter === '' ? 'on' : '', onclick: () => { location.hash = '#leads'; } }, 'Alle'),
    LEAD_ST.filter(s => d.zaehler[s]).map(s => h('button', { class: filter === s ? 'on' : '', onclick: () => { location.hash = '#leads?status=' + s; } }, s.replace(/_/g, ' ') + ' (' + d.zaehler[s] + ')')));
  const zuordnen = (z) => select('p', [['', '– niemand –'], ...partner.map(p => [p.id, p.name])], z.vertriebler ? (partner.find(p => p.name === z.vertriebler) || {}).id : '', { onchange: async (e) => {
    try { await api('/api/admin/leads/' + z.id, { method: 'PATCH', body: e.target.value ? { vertriebspartner_id: e.target.value } : { zuordnung_loeschen: true } }); melde(m, 'Zugeordnet.', 'ok'); } catch (x) { fehler(m, x); } } });
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = leerzu(Object.fromEntries(new FormData(e.target)));
    bestaetigt(m, () => api('/api/admin/leads', { method: 'POST', body: o }), 'Lead angelegt.'); } },
    h('div', { class: 'form2' }, feld('Firma *', 'firma', '', { required: true }), feld('Ansprechpartner', 'ansprechpartner'), feld('E-Mail', 'email'), feld('Telefon', 'telefon'), feld('Website', 'website'), feld('Branche', 'branche'), feld('PLZ', 'plz'), feld('Ort', 'ort'),
      h('div', {}, h('label', {}, 'Quelle'), select('quelle', ['manuell', 'empfehlung', 'lead_finder', 'website', 'akquise', 'messe'], 'manuell')),
      h('div', {}, h('label', {}, 'Vertriebler'), select('vertriebspartner_id', [['', '– niemand –'], ...partner.map(p => [p.id, p.name])], ''))),
    h('p', {}, h('button', { class: 'btn' }, 'Lead anlegen')));
  return h('div', { class: 'stack' }, kopf('Leads'), m, h('div', { class: 'card' }, tabs,
    tabelle([['Firma', z => h('a', { href: '#lead/' + z.id }, z.firma)], ['Ort', z => z.ort], ['Quelle', z => z.quelle], ['Status', z => pill(z.status)], ['Score', z => z.score ?? ''], ['Vertriebler', zuordnen], ['Angelegt', z => datum(z.erstellt_am)]], d.leads, 'Keine Leads.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Lead'), f));
};

async function leadDetail(lid) {
  const [d, partner] = await Promise.all([api('/api/admin/leads/' + lid), api('/api/admin/vertrieb/partnerliste')]), l = d.lead, m = h('div');
  const st = h('select', { onchange: (e) => bestaetigt(m, () => api('/api/admin/leads/' + lid, { method: 'PATCH', body: { status: e.target.value } }), 'Status geändert.') }, LEAD_ST.map(s => h('option', { value: s, selected: s === l.status }, s.replace(/_/g, ' '))));
  st.style.width = 'auto';
  const akt = h('form', { onsubmit: (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); bestaetigt(m, () => api('/api/admin/leads/' + lid + '/aktivitaet', { method: 'POST', body: o }), 'Eingetragen.'); } },
    h('div', { class: 'row' }, h('div', { style: 'width:170px' }, select('art', ['notiz', 'anruf', 'mail_gesendet', 'antwort', 'termin'], 'notiz')), h('div', { class: 'grow' }, h('input', { name: 'inhalt', placeholder: 'Was ist passiert?', required: true })), h('button', { class: 'btn' }, 'Eintragen')));
  const zuK = l.kunden_id ? h('a', { class: 'btn sec small', href: '#kunde/' + l.kunden_id }, 'Zum Kunden') : knopf('Zum Kunden machen', () => confirm('Aus diesem Lead einen Kunden anlegen?') && bestaetigt(m, async () => { const k = await api('/api/admin/leads/' + lid + '/zu-kunde', { method: 'POST' }); location.hash = '#kunde/' + k.id; }), 'btn');
  return h('div', { class: 'stack' }, kopf(l.firma, st, zuK, h('a', { class: 'btn sec small', href: '#leads' }, '← Liste')), m,
    h('div', { class: 'card' }, h('h2', {}, 'Daten'), h('div', { class: 'form2' }, [['Ansprechpartner', l.ansprechpartner], ['E-Mail', l.email], ['Telefon', l.telefon], ['Website', l.website], ['Branche', l.branche], ['Ort', [l.plz, l.ort].filter(Boolean).join(' ')], ['Quelle', l.quelle], ['Vertriebler', l.vertriebler || '–'], ['Score', l.score ?? '–']].map(([a, b]) => h('div', {}, h('div', { class: 'small muted' }, a), h('div', {}, b || '–')))), l.notiz && h('p', { class: 'muted' }, l.notiz)),
    h('div', { class: 'card' }, h('h2', {}, 'Verlauf'), akt, h('div', { style: 'height:10px' }), tabelle([['Wann', z => zeit(z.zeit)], ['Art', z => z.art.replace(/_/g, ' ')], ['Inhalt', z => z.inhalt], ['Von', z => z.von]], d.aktivitaeten, 'Noch keine Einträge.')));
}

// ---------------------------------------------------------------- Preise und Konditionen
V.preise = async () => {
  const d = await api('/api/admin/preise'), m = h('div'), mk = h('div'), mr = h('div');
  const heute = new Date().toISOString().slice(0, 10);
  const pform = h('form', { onsubmit: (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target));
    const body = { produkt_code: o.produkt_code, gueltig_ab: o.gueltig_ab, einrichtung_cent: cent(o.einrichtung), monatlich_cent: cent(o.monatlich), projekt_cent: cent(o.projekt), ab_preis: !!e.target.ab.checked };
    bestaetigt(m, () => api('/api/admin/preise', { method: 'POST', body }), 'Neuer Preis gespeichert. Bestehende Buchungen behalten ihren Preis.'); } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Produkt'), h('select', { name: 'produkt_code' }, d.aktuell.map(p => h('option', { value: p.code }, p.name + ' (' + p.code + ')')))),
      feld('Gültig ab', 'gueltig_ab', heute, { type: 'date', required: true }), feld('Einrichtung in €', 'einrichtung', '', { type: 'number', step: '0.01', min: '0' }), feld('Monatlich in €', 'monatlich', '', { type: 'number', step: '0.01', min: '0' }), feld('Projekt in €', 'projekt', '', { type: 'number', step: '0.01', min: '0' })),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', name: 'ab', style: 'width:auto' }), '„ab"-Preis'),
    h('p', {}, h('button', { class: 'btn' }, 'Neuen Preis anlegen')));
  const kond = (z) => { const i = h('input', { value: z.wert_zahl ?? z.wert_text ?? '' }); return h('div', { class: 'row' }, h('div', { class: 'grow' }, i),
    knopf('Speichern', () => { const v = i.value.trim(); const body = /^-?\d+$/.test(v) ? { wert_zahl: Number(v) } : { wert_text: v }; bestaetigt(mk, () => api('/api/admin/konditionen/' + encodeURIComponent(z.schluessel), { method: 'PUT', body })); })); };
  const regelBtn = (z) => z.status === 'entwurf' ? knopf('Freigeben', () => confirm('Regel "' + z.name + '" (' + z.prozent + ' %) freigeben?') && bestaetigt(mr, () => api('/api/admin/provisionsregeln/' + z.id + '/freigeben', { method: 'POST' }), 'Freigegeben.')) : '';
  return h('div', { class: 'stack' }, kopf('Preise & Konditionen'), m,
    h('div', { class: 'card' }, h('h2', {}, 'Aktuelle Preise'), tabelle([['Produkt', z => z.name], ['Einrichtung', z => (z.ab_preis ? 'ab ' : '') + fmtEuro(z.einrichtung_cent)], ['Monatlich', z => fmtEuro(z.monatlich_cent)], ['Projekt', z => fmtEuro(z.projekt_cent)], ['Gültig ab', z => datum(z.gueltig_ab)]], d.aktuell)),
    h('div', { class: 'card' }, h('h2', {}, 'Preis ändern (neue Version)'), h('p', { class: 'small muted' }, 'Alte Preise bleiben im Verlauf. Bestehende Buchungen behalten den Preis, der bei der Buchung galt.'), pform),
    h('div', { class: 'card' }, h('h2', {}, 'Konditionen'), mk, tabelle([['Schlüssel', z => z.schluessel], ['Beschreibung', z => z.beschreibung], ['Wert', kond]], d.konditionen, 'Keine Konditionen.')),
    h('div', { class: 'card' }, h('h2', {}, 'Provisionsregeln'), h('p', { class: 'small muted' }, 'Entwürfe gelten erst nach deiner Freigabe.'), mr, tabelle([['Regel', z => z.name], ['Monate', z => z.von_monat + (z.bis_monat ? '–' + z.bis_monat : '+')], ['%', z => z.prozent], ['Status', z => pill(z.status === 'entwurf' ? 'onboarding' : z.status)], ['', regelBtn]], d.provisionsregeln)),
    h('div', { class: 'card' }, h('h2', {}, 'Preisverlauf'), tabelle([['Gültig ab', z => datum(z.gueltig_ab)], ['Produkt', z => z.produkt_code], ['Einrichtung', z => fmtEuro(z.einrichtung_cent)], ['Monatlich', z => fmtEuro(z.monatlich_cent)], ['Projekt', z => fmtEuro(z.projekt_cent)], ['Freigegeben von', z => z.freigegeben_von]], d.verlauf)));
};

// ---------------------------------------------------------------- Datenschutz und Qualität
V.compliance = async () => {
  const d = await api('/api/admin/compliance'), m = h('div');
  const tun = (fn) => bestaetigt(m, fn, 'Erledigt.');
  const post = (pfad, body) => api('/api/admin' + pfad, { method: 'POST', body });
  const entscheid = (tab, okTxt, okStatus, neinTxt, neinStatus) => (z) => h('span', { class: 'row' },
    knopf(okTxt, () => tun(() => post('/compliance/' + tab + '/' + z.id, { status: okStatus })), 'sec'),
    neinTxt && knopf(neinTxt, () => { const b = prompt('Begründung (kurz):'); if (b !== null) tun(() => post('/compliance/' + tab + '/' + z.id, { status: neinStatus, begruendung: b })); }, 'bad'));
  const sektion = (titel, zeilen, spalten, leer) => h('div', { class: 'card' }, h('h2', {}, titel + ' (' + zeilen.length + ')'), tabelle(spalten, zeilen, leer));
  const stufe = (s) => h('span', { class: 'pill ' + (s === 'kritisch' ? 'bad' : s === 'warnung' ? 'warn' : '') }, s);
  const offen = d.alarme.length + d.freigaben.length + d.aenderungen.length + d.auskunft.length + d.workflow_fehler.length + d.befunde.length + d.massnahmen.length;
  return h('div', { class: 'stack' }, kopf('Datenschutz & Qualität', h('span', { class: 'pill ' + (offen ? 'warn' : 'ok') }, offen ? offen + ' offen' : 'alles erledigt')), m,
    sektion('Alarme', d.alarme, [['Zeit', z => zeit(z.zeit)], ['Stufe', z => stufe(z.stufe)], ['Quelle', z => z.quelle], ['Titel', z => z.titel], ['', z => knopf('Bestätigen', () => tun(() => post('/alarme/' + z.id + '/bestaetigen')))]], 'Keine offenen Alarme.'),
    sektion('Freigaben (Agenten)', d.freigaben, [['Eingang', z => zeit(z.erstellt_am)], ['Kunde', z => z.kundennummer || ''], ['Art', z => z.art], ['Vorschau', z => z.vorschau], ['', entscheid('freigaben', 'Freigeben', 'freigegeben', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Freigaben.'),
    sektion('Änderungsfreigaben', d.aenderungen, [['Seit', z => datum(z.beantragt_am)], ['Art', z => z.art], ['Gegenstand', z => z.gegenstand], ['Beschreibung', z => z.beschreibung], ['Von', z => z.beantragt_von], ['', entscheid('aenderungsfreigaben', 'Freigeben', 'freigegeben', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Anträge.'),
    sektion('Auskunfts- und Löschanfragen (DSGVO)', d.auskunft, [['Eingang', z => datum(z.eingang_am)], ['Frist', z => datum(z.frist_bis)], ['Art', z => z.art], ['Person', z => z.person_ref], ['Status', z => pill(z.status)], ['', entscheid('auskunftsanfragen', 'Erledigt', 'erledigt', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Anfragen.'),
    sektion('Workflow-Fehler', d.workflow_fehler, [['Zeit', z => zeit(z.zeit)], ['Workflow', z => z.workflow_name], ['Knoten', z => z.knoten], ['Fehler', z => z.fehlertext], ['', z => knopf('Behoben', () => tun(() => post('/workflow-fehler/' + z.id + '/behoben')))]], 'Keine offenen Fehler.'),
    sektion('Befunde (Qualität)', d.befunde, [['Gefunden', z => datum(z.gefunden_am)], ['Schwere', z => stufe(z.schwere === 'kritisch' ? 'kritisch' : z.schwere === 'wesentlich' ? 'warnung' : 'info')], ['Titel', z => z.titel], ['Status', z => pill(z.status)], ['', entscheid('befunde', 'Behoben', 'behoben', '', '')]], 'Keine offenen Befunde.'),
    sektion('Maßnahmen', d.massnahmen, [['Fällig', z => datum(z.faellig_am)], ['Maßnahme', z => z.beschreibung], ['Verantwortlich', z => z.verantwortlich], ['Status', z => pill(z.status)], ['', entscheid('massnahmen', 'Umgesetzt', 'umgesetzt', '', '')]], 'Keine offenen Maßnahmen.'));
};

V.protokoll = async () => {
  const d = await api('/api/admin/audit');
  return h('div', {}, kopf('Protokoll'), h('div', { class: 'card' }, tabelle([['Zeit', z => zeit(z.zeit)], ['Benutzer', z => z.email || 'System'], ['Kunde', z => z.kundennummer || ''], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d)));
};

const STATI = ['onboarding', 'aktiv', 'pausiert', 'gekuendigt', 'beendet'];
const DATEN_TABS = [['anfragen', 'Anfragen'], ['termine', 'Termine'], ['kontakte', 'Kontakte'], ['angebote', 'Angebote'], ['vertraege', 'Verträge'], ['projekte', 'Projekte'], ['berichte', 'Berichte'], ['wochenangebote_uploads', 'Uploads'], ['chat_verlauf', 'Chat']];

async function kundeDetail(kid) {
  const d = await api('/api/admin/kunden/' + kid), k = d.kunde;
  const neu = () => { const s = location.hash; location.hash = ''; setTimeout(() => { location.hash = s; }, 0); };
  const mk = h('div'), mz = h('div'), mb = h('div'), mw = h('div'), mdaten = h('div'), mv = h('div');
  const partnerListe = await api('/api/admin/vertrieb/partnerliste');

  const stamm = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const o = Object.fromEntries(new FormData(e.target));
    try { await api('/api/admin/kunden/' + kid, { method: 'PATCH', body: o }); melde(mk, 'Gespeichert.', 'ok'); } catch (x) { melde(mk, x.message); }
  } }, h('div', { class: 'form2' },
    feld('Firma', 'firma', k.firma), feld('Rechtsform', 'rechtsform', k.rechtsform), feld('Ansprechpartner', 'ansprechpartner', k.ansprechpartner),
    feld('E-Mail', 'email', k.email), feld('Telefon', 'telefon', k.telefon), feld('Branche', 'branche', k.branche),
    feld('Straße', 'strasse', k.strasse), feld('PLZ', 'plz', k.plz), feld('Ort', 'ort', k.ort), feld('Domain', 'domain', k.domain),
    h('div', {}, h('label', {}, 'Paket'), h('select', { name: 'paket_code' }, h('option', { value: '' }, '–'), paketListe.map(p => h('option', { value: p.code, selected: p.code === k.paket_code }, p.name))))),
    h('label', {}, 'Notizen'), h('textarea', { name: 'notizen', rows: 3 }, k.notizen || ''),
    h('p', { class: 'row' }, h('button', { class: 'btn' }, 'Speichern')));

  const status = h('select', { style: 'width:auto', onchange: async (e) => {
    if (!confirm('Status ändern auf "' + e.target.value + '"? Bei pausiert/gekündigt/beendet werden die Zugänge gesperrt.')) { e.target.value = k.status; return; }
    try { await api('/api/admin/kunden/' + kid + '/status', { method: 'POST', body: { status: e.target.value } }); neu(); } catch (x) { melde(mk, x.message); }
  } }, STATI.map(s => h('option', { value: s, selected: s === k.status }, s)));

  const module = d.module.map(m => {
    const cb = h('input', { type: 'checkbox', checked: m.aktiv, onchange: async (e) => {
      try { await api('/api/admin/kunden/' + kid + '/module/' + m.code, { method: 'PUT', body: { aktiv: e.target.checked } }); melde(mz, m.name + (e.target.checked ? ' aktiviert.' : ' deaktiviert.'), 'ok'); }
      catch (x) { e.target.checked = !e.target.checked; melde(mz, x.message); }
    } });
    return h('div', { class: 'modul' }, h('label', { class: 'sw', style: 'margin:0' }, cb, h('i')), h('div', { class: 'grow' }, h('b', {}, m.name), ' ', h('span', { class: 'pill' }, m.art === 'agent' ? 'Agent' : 'Portal'), h('div', { class: 'small muted' }, m.beschreibung)));
  });

  const mail = h('input', { type: 'email', placeholder: 'E-Mail für Portal-Zugang', value: k.email || '' });
  const linkbox = h('div');
  const einladen = h('button', { class: 'btn small', onclick: async () => {
    try { const r = await api('/api/admin/kunden/' + kid + '/einladung', { method: 'POST', body: { email: mail.value } });
      linkbox.replaceChildren(h('div', { class: 'msg info' }, 'Einladungslink (' + r.gueltig_tage + ' Tage gültig): ', h('br'), r.einladungslink)); } catch (x) { melde(linkbox, x.message); }
  } }, 'Einladungslink erzeugen');
  const zugaenge = tabelle([['E-Mail', z => z.email], ['Passwort', z => z.hat_passwort ? 'gesetzt' : 'offen'], ['Letzter Login', z => zeit(z.letzter_login)],
    ['Zugang', z => h('button', { class: 'btn small ' + (z.aktiv ? 'bad' : 'sec'), onclick: async () => { try { await api('/api/admin/benutzer/' + z.id + '/aktiv', { method: 'POST', body: { aktiv: !z.aktiv } }); neu(); } catch (x) { alert(x.message); } } }, z.aktiv ? 'Sperren' : 'Freigeben')]], d.benutzer, 'Noch kein Zugang.');

  const prod = h('select', { name: 'produkt_code' }, paketListe.map(p => h('option', { value: p.code }, p.name + ' (' + p.code + ')')));
  const bform = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const o = leerzu(Object.fromEntries(new FormData(e.target))); o.rabatt_cent = Math.round(Number(o.rabatt_euro || 0) * 100); delete o.rabatt_euro;
    try { await api('/api/admin/kunden/' + kid + '/buchungen', { method: 'POST', body: o }); neu(); } catch (x) { melde(mb, x.message); }
  } }, h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Produkt'), prod), feld('Beginn', 'beginn', '', { type: 'date' }), feld('Rabatt in € / Monat', 'rabatt_euro', '', { type: 'number', step: '0.01', min: '0' }), feld('Rabatt-Grund', 'rabatt_grund'), feld('Standort', 'standort'), feld('Notiz', 'notiz')),
    h('p', {}, h('button', { class: 'btn' }, 'Buchung anlegen (Preis wird festgehalten)')));
  const bst = (z) => h('select', { onchange: async (e) => { try { await api('/api/admin/buchungen/' + z.id, { method: 'PATCH', body: { status: e.target.value } }); } catch (x) { alert(x.message); } } },
    ['angefragt', 'beauftragt', 'in_einrichtung', 'aktiv', 'pausiert', 'gekuendigt', 'beendet'].map(s => h('option', { value: s, selected: s === z.status }, s.replace('_', ' '))));
  const buchungen = tabelle([['Produkt', z => z.name], ['Einrichtung', z => euro(z.einrichtung_cent)], ['Monatlich', z => euro(z.monatlich_cent)], ['Rabatt', z => euro(z.rabatt_cent)], ['Beginn', z => datum(z.beginn)], ['Mindestlaufzeit bis', z => datum(z.mindestlaufzeit_ende)], ['Status', bst]], d.buchungen, 'Noch keine Buchungen.');

  const wform = h('form', { class: 'row', onsubmit: async (e) => {
    e.preventDefault(); try { await api('/api/admin/kunden/' + kid + '/websites', { method: 'POST', body: Object.fromEntries(new FormData(e.target)) }); neu(); } catch (x) { melde(mw, x.message); }
  } }, h('input', { class: 'grow', name: 'domain', placeholder: 'domain.de', required: true }), h('select', { name: 'art', style: 'width:auto' }, h('option', { value: 'live' }, 'live'), h('option', { value: 'demo' }, 'demo')), h('button', { class: 'btn' }, 'Website anlegen'));
  const webs = tabelle([['Domain', z => z.domain], ['Art', z => z.art], ['Status', z => pill(z.status)], ['Zuletzt', z => zeit(z.letzte_veroeffentlichung)]], d.websites, 'Keine Website.');

  const tabs = h('div', { class: 'tabs' }, DATEN_TABS.map(([t, l]) => h('button', { onclick: (e) => ladeDaten(t, e.target) }, l + (d.zaehler[t] === undefined ? '' : ' (' + d.zaehler[t] + ')'))));
  async function ladeDaten(t, btn) {
    tabs.querySelectorAll('button').forEach(b => b.classList.remove('on')); btn.classList.add('on');
    try {
      const z = await api('/api/admin/kunden/' + kid + '/daten/' + t);
      const sp = z.length ? Object.keys(z[0]).filter(c => c !== 'id') : [];
      mdaten.replaceChildren(tabelle(sp.map(c => [c, r => { const v = r[c]; return v === null ? '' : /_am$|^zeit$|^beginn$|^ende$/.test(c) && typeof v === 'string' && v.includes('T') ? zeit(v) : String(v); }]), z, 'Keine Einträge.'));
    } catch (x) { melde(mdaten, x.message); }
  }

  return h('div', { class: 'stack' },
    kopf(k.firma, h('span', { class: 'pill' }, k.kundennummer), pill(k.status), status, h('a', { class: 'btn sec small', href: '#kunden' }, '← Liste')),
    h('div', { class: 'card' }, h('h2', {}, 'Stammdaten'), mk, stamm),
    h('div', { class: 'card' }, h('h2', {}, 'Vertriebler'), mv, h('div', { class: 'row' }, h('div', { class: 'grow' }, h('select', { id: 'vsel' }, h('option', { value: '' }, '– kein Vertriebler –'), partnerListe.map(p => h('option', { value: p.id, selected: p.id === k.vertriebspartner_id }, p.name + (p.status !== 'aktiv' ? ' (' + p.status + ')' : ''))))),
      knopf('Zuordnen', async () => { try { await api('/api/admin/kunden/' + kid + '/partner', { method: 'PUT', body: { partner_id: document.getElementById('vsel').value || null } }); melde(mv, 'Gespeichert.', 'ok'); } catch (x) { melde(mv, x.message); } }))),
    h('div', { class: 'card' }, h('h2', {}, 'Module des Kunden (Schalter)'), h('p', { class: 'small muted' }, 'Was hier aktiv ist, sieht der Kunde in seinem Portal.'), mz, module),
    h('div', { class: 'card' }, h('h2', {}, 'Portal-Zugang'), zugaenge, h('div', { class: 'row', style: 'margin-top:12px' }, h('div', { class: 'grow' }, mail), einladen), linkbox),
    h('div', { class: 'card' }, h('h2', {}, 'Buchungen'), mb, buchungen, h('h3', { style: 'margin-top:18px' }, 'Neue Buchung'), bform),
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), mw, webs, h('div', { style: 'height:10px' }), wform,
      h('p', { class: 'small muted' }, 'Danach auf dem Server einmal: mkctl site-add <domain>, damit Ordner und Webserver bereit sind.')),
    h('div', { class: 'card' }, h('h2', {}, 'Daten des Kunden'), tabs, mdaten));
}

async function zeige() {
  const hash = (location.hash || '#uebersicht').slice(1);
  let seite = hash.split('/')[0].split('?')[0], inhalt;
  try {
    if (seite === 'kunde') inhalt = await kundeDetail(hash.split('/')[1]);
    else if (seite === 'partner') inhalt = await partnerDetail(hash.split('/')[1]);
    else if (seite === 'lead') inhalt = await leadDetail(hash.split('/')[1]);
    else if (V[seite]) inhalt = await V[seite]();
    else { seite = 'uebersicht'; inhalt = await V.uebersicht(); }
  } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  root.replaceChildren(gerüst(seite === 'kunde' ? 'kunden' : seite === 'partner' ? 'vertrieb' : seite === 'lead' ? 'leads' : seite, inhalt));
}

(async () => {
  try {
    const me = await api('/api/me');
    if (me.rolle !== 'admin') { location.href = '/app'; return; }
    paketListe = (await api('/api/admin/katalog')).produkte;
  } catch (e) { return; }
  window.addEventListener('hashchange', zeige);
  zeige();
})();
