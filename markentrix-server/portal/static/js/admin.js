import { h, api, datum, zeit, euro, melde, abmelden } from './common.js';

const root = document.getElementById('app');
const NAV = [['uebersicht', 'Übersicht'], ['kunden', 'Kunden'], ['neu', 'Neuer Kunde'], ['katalog', 'Pakete & Preise'], ['protokoll', 'Protokoll']];
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

V.protokoll = async () => {
  const d = await api('/api/admin/audit');
  return h('div', {}, kopf('Protokoll'), h('div', { class: 'card' }, tabelle([['Zeit', z => zeit(z.zeit)], ['Benutzer', z => z.email || 'System'], ['Kunde', z => z.kundennummer || ''], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d)));
};

const STATI = ['onboarding', 'aktiv', 'pausiert', 'gekuendigt', 'beendet'];
const DATEN_TABS = [['anfragen', 'Anfragen'], ['termine', 'Termine'], ['kontakte', 'Kontakte'], ['angebote', 'Angebote'], ['vertraege', 'Verträge'], ['projekte', 'Projekte'], ['berichte', 'Berichte'], ['wochenangebote_uploads', 'Uploads'], ['chat_verlauf', 'Chat']];

async function kundeDetail(kid) {
  const d = await api('/api/admin/kunden/' + kid), k = d.kunde;
  const neu = () => { const s = location.hash; location.hash = ''; setTimeout(() => { location.hash = s; }, 0); };
  const mk = h('div'), mz = h('div'), mb = h('div'), mw = h('div'), mdaten = h('div');

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
    h('div', { class: 'card' }, h('h2', {}, 'Module des Kunden (Schalter)'), h('p', { class: 'small muted' }, 'Was hier aktiv ist, sieht der Kunde in seinem Portal.'), mz, module),
    h('div', { class: 'card' }, h('h2', {}, 'Portal-Zugang'), zugaenge, h('div', { class: 'row', style: 'margin-top:12px' }, h('div', { class: 'grow' }, mail), einladen), linkbox),
    h('div', { class: 'card' }, h('h2', {}, 'Buchungen'), mb, buchungen, h('h3', { style: 'margin-top:18px' }, 'Neue Buchung'), bform),
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), mw, webs, h('div', { style: 'height:10px' }), wform,
      h('p', { class: 'small muted' }, 'Danach auf dem Server einmal: mkctl site-add <domain>, damit Ordner und Webserver bereit sind.')),
    h('div', { class: 'card' }, h('h2', {}, 'Daten des Kunden'), tabs, mdaten));
}

async function zeige() {
  const hash = (location.hash || '#uebersicht').slice(1);
  let seite = hash.split('/')[0], inhalt;
  try {
    if (seite === 'kunde') inhalt = await kundeDetail(hash.split('/')[1]);
    else if (V[seite]) inhalt = await V[seite]();
    else { seite = 'uebersicht'; inhalt = await V.uebersicht(); }
  } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  root.replaceChildren(gerüst(seite === 'kunde' ? 'kunden' : seite, inhalt));
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
