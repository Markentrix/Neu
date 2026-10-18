import { h, api, datum, zeit, euro, melde, abmelden, zweiFaktorKarte, rechtFuss } from './common.js';

const root = document.getElementById('app');
const NAV = [['uebersicht', 'Übersicht'], ['kunden', 'Kunden'], ['neu', 'Neuer Kunde'], ['vertrieb', 'Vertriebler'], ['leads', 'Leads'], ['websites', 'Websites & Demos'], ['belege', 'Angebote & Rechnungen'], ['preise', 'Preise & Konditionen'], ['compliance', 'Datenschutz & Qualität'], ['katalog', 'Pakete (Katalog)'], ['einstellungen', 'Einstellungen'], ['protokoll', 'Protokoll']];
let paketListe = [], ich = null;

function gerüst(aktiv, inhalt) {
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Admin'),
      NAV.map(n => h('a', { class: 'nav' + (n[0] === aktiv ? ' on' : ''), href: '#' + n[0] }, n[1])),
      h('a', { class: 'nav', href: location.origin.replace('//portal.', '//panel.'), target: '_blank', rel: 'noopener' }, 'Server-Dashboard ↗'),
      h('div', { class: 'grow' }),
      h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' }, ich && !ich.zwei_faktor ? h('div', { class: 'msg info' }, 'Dein Admin-Konto hat noch keine Zwei-Faktor-Anmeldung. ', h('a', { href: '#einstellungen' }, 'Jetzt einrichten'), '.') : '', inhalt, rechtFuss()));
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
  const d = await api('/api/admin/uebersicht'), ob = await api('/api/admin/onboarding/offen');
  const s = d.kunden_status, summe = Object.values(s).reduce((a, b) => a + b, 0);
  return h('div', {}, kopf('Übersicht'),
    h('div', { class: 'grid3' },
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Kunden gesamt'), h('b', {}, summe)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Aktiv'), h('b', {}, s.aktiv || 0)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Im Onboarding'), h('b', {}, s.onboarding || 0)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Monatlich (gebucht)'), h('b', {}, euro(d.monatlich_cent))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Referenzkunden (unbezahlt)'), h('b', {}, d.referenzkunden)),
      h('a', { class: 'card stat', href: '#belege', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Offene Rechnungen' + (d.rechnungen_ueberfaellig ? ' (' + d.rechnungen_ueberfaellig + ' überfällig)' : '')), h('b', {}, euro(d.rechnungen_offen_cent))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Neue Anfragen'), h('b', {}, d.neue_anfragen)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Uploads (7 Tage)'), h('b', {}, d.uploads_7d))),
    ob.length ? h('div', { class: 'card' }, h('h2', {}, 'Neue Kunden im Onboarding'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Fortschritt', z => z.fertig + ' von ' + z.gesamt]], ob)) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Letzte Aktionen'), tabelle([['Zeit', z => zeit(z.zeit)], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d.letzte_aktionen)));
};

V.kunden = async () => {
  const q = h('input', { placeholder: 'Suchen nach Firma, Nummer, E-Mail …' });
  const box = h('div'), nurRef = h('input', { type: 'checkbox', style: 'width:auto', onchange: () => lade() });
  const lade = async () => {
    let d = await api('/api/admin/kunden?q=' + encodeURIComponent(q.value));
    if (nurRef.checked) d = d.filter(z => z.referenzkunde);
    box.replaceChildren(tabelle([
      ['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => h('span', {}, z.firma, z.referenzkunde ? [' ', h('span', { class: 'pill warn' }, 'Referenz')] : '')], ['Paket', z => z.paket || '–'],
      ['Status', z => pill(z.status)], ['Module', z => z.module_aktiv], ['Zugang', z => z.zugang_aktiv ? 'ja' : 'nein'], ['Domain', z => z.domain]], d, 'Noch keine Kunden.'));
  };
  let t; q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(lade, 250); });
  await lade();
  return h('div', {}, kopf('Kunden', h('a', { class: 'btn', href: '#neu' }, '+ Neuer Kunde')), h('div', { class: 'card' }, q, h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin-top:8px' }, nurRef, 'Nur Referenzkunden'), h('div', { style: 'height:12px' }), box));
};

V.neu = async () => {
  const m = h('div');
  const paket = h('select', { name: 'paket_code' }, h('option', { value: '' }, '– kein Paket –'), paketListe.map(p => h('option', { value: p.code }, p.name)));
  const einl = h('input', { type: 'checkbox', name: 'einladen', checked: true, style: 'width:auto' });
  const ref = h('input', { type: 'checkbox', style: 'width:auto' }), refd = h('input', { type: 'checkbox', style: 'width:auto' });
  const f = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const d = leerzu(Object.fromEntries(new FormData(e.target))); d.einladen = einl.checked; d.referenzkunde = ref.checked; d.referenz_nennen_erlaubt = ref.checked && refd.checked;
    if (!ref.checked) delete d.referenz_leistung;
    try {
      const r = await api('/api/admin/kunden', { method: 'POST', body: d });
      m.replaceChildren(h('div', { class: 'msg ok' }, 'Kunde ' + r.kundennummer + ' angelegt.'),
        r.einladungslink ? h('div', { class: 'msg info' }, 'Einladungslink (7 Tage gültig): ', h('br'), r.einladungslink) : '', mailHinweis(r.mail),
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
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, ref, 'Referenzkunde (zahlt nichts, wird aber normal betreut)'),
    h('div', { id: 'refbox' }, h('label', {}, 'Was bekommt der Referenzkunde? (z. B. Website, KI-Telefonassistent)'), h('textarea', { name: 'referenz_leistung', rows: 2 }),
      h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, refd, 'Darf als Referenz genannt werden (schriftliches Einverständnis liegt vor)')),
    h('p', {}, h('button', { class: 'btn' }, 'Kunde anlegen')));
  const refbox = f.querySelector('#refbox'); refbox.hidden = true; ref.addEventListener('change', () => { refbox.hidden = !ref.checked; });
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

const mailHinweis = (mail) => !mail ? '' : h('div', { class: 'msg ' + (mail.gesendet ? 'ok' : 'info') }, mail.gesendet ? 'Die Einladung wurde per E-Mail verschickt.' : 'Nicht per E-Mail verschickt: ' + mail.grund);

// ---------------------------------------------------------------- Einstellungen
V.einstellungen = async () => {
  const d = await api('/api/admin/einstellungen');
  const m1 = h('div'), m2 = h('div'), m3 = h('div');
  const fs = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); o.port = Number(o.port);
    try { await api('/api/admin/einstellungen/smtp', { method: 'PUT', body: o }); melde(m1, 'Gespeichert.', 'ok'); } catch (x) { fehler(m1, x); } } },
    h('div', { class: 'form2' }, feld('Server (SMTP-Host) *', 'host', d.smtp.host, { required: true, placeholder: 'z. B. smtp.ionos.de' }), feld('Port *', 'port', d.smtp.port, { type: 'number', required: true }),
      h('div', {}, h('label', {}, 'Verschlüsselung'), select('sicherung', [['starttls', 'STARTTLS (Port 587)'], ['ssl', 'SSL (Port 465)'], ['keine', 'keine']], d.smtp.sicherung)),
      feld('Benutzername', 'benutzer', d.smtp.benutzer, { autocomplete: 'off' }),
      feld(d.smtp.passwort_gesetzt ? 'Passwort (leer lassen = unverändert)' : 'Passwort', 'passwort', '', { type: 'password', autocomplete: 'new-password' }),
      feld('Absender-Adresse *', 'absender', d.smtp.absender, { type: 'email', required: true, placeholder: 'info@markentrix.de' }), feld('Absender-Name', 'absender_name', d.smtp.absender_name)),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  const t = h('input', { type: 'email', placeholder: 'Testmail an …', style: 'max-width:280px' });
  const ft = h('div', { class: 'row' }, t, knopf('Testmail senden', async () => { try { await api('/api/admin/einstellungen/testmail', { method: 'POST', body: { an: t.value } }); melde(m1, 'Testmail wurde versendet.', 'ok'); } catch (x) { fehler(m1, x); } }));
  const fk = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); o.tageslimit = Number(o.tageslimit); o.preis_ein_eur = Number(o.preis_ein_eur); o.preis_aus_eur = Number(o.preis_aus_eur);
    try { await api('/api/admin/einstellungen/ki', { method: 'PUT', body: o }); melde(m2, 'Gespeichert.', 'ok'); e.target.api_key.value = ''; } catch (x) { fehler(m2, x); } } },
    h('div', { class: 'form2' }, feld(d.ki.key_gesetzt ? 'API-Key (leer lassen = unverändert)' : 'API-Key', 'api_key', '', { type: 'password', autocomplete: 'new-password', placeholder: 'sk-ant-…' }),
      feld('Modell', 'modell', d.ki.modell), feld('Nachrichten pro Kunde und Tag', 'tageslimit', d.ki.tageslimit, { type: 'number', min: 1, max: 1000 }),
        feld('Preis Eingabe, € je 1 Mio. Tokens', 'preis_ein_eur', d.ki.preis_ein_eur, { type: 'number', step: '0.01', min: 0 }), feld('Preis Ausgabe, € je 1 Mio. Tokens', 'preis_aus_eur', d.ki.preis_aus_eur, { type: 'number', step: '0.01', min: 0 })),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'stack' }, kopf('Einstellungen'),
    !d.geheimnis_ok ? h('div', { class: 'msg err' }, 'Das Server-Geheimnis (PORTAL_SECRET) fehlt. Bitte install.sh erneut ausführen, sonst können keine Zugangsdaten gespeichert werden.') : '',
    h('div', { class: 'card' }, h('h2', {}, 'E-Mail-Versand (SMTP)'), h('p', { class: 'small muted' }, 'Zugangsdaten deines Postfachs. Damit verschickt das Portal Einladungen und Passwort-Links automatisch. Das Passwort wird verschlüsselt gespeichert und nie wieder angezeigt.'), m1, fs, ft),
    zweiFaktorKarte(), await firmaKarte(), await benachrKarte(), await rechtKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'KI-Assistent im Kunden-Chat'), h('p', { class: 'small muted' }, d.ki.key_gesetzt ? 'API-Key ist hinterlegt – der Chat antwortet direkt über das Portal.' : 'Noch kein API-Key – der Chat nutzt den n8n-Webhook, falls eingerichtet. Den Key gibt es in der Anthropic-Konsole (console.anthropic.com), getrennt vom Claude-Abo.'), m2, fk), m3);
};

const kk = (label, wert, set) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', checked: wert, style: 'width:auto', onchange: (e) => set(e.target.checked) }), label);
async function firmaKarte() {
  const f = await api('/api/admin/einstellungen/firma'), m = h('div'); let klein = f.kleinunternehmer;
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); o.kleinunternehmer = klein; o.zahlungsziel_tage = Number(o.zahlungsziel_tage); o.mwst_satz = Number(o.mwst_satz);
    try { await api('/api/admin/einstellungen/firma', { method: 'PUT', body: o }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' }, feld('Firmenname', 'name', f.name), feld('Inhaber', 'inhaber', f.inhaber), feld('Straße', 'strasse', f.strasse), feld('PLZ', 'plz', f.plz), feld('Ort', 'ort', f.ort),
      feld('E-Mail', 'email', f.email), feld('Telefon', 'telefon', f.telefon), feld('Website', 'website', f.website), feld('USt-IdNr.', 'ustid', f.ustid), feld('Steuernummer', 'steuernummer', f.steuernummer),
      feld('IBAN', 'iban', f.iban), feld('BIC', 'bic', f.bic), feld('Bank', 'bank', f.bank), feld('Zahlungsziel (Tage)', 'zahlungsziel_tage', f.zahlungsziel_tage, { type: 'number', min: 0, max: 90 }),
      feld('Umsatzsteuer (%)', 'mwst_satz', f.mwst_satz, { type: 'number', min: 0, max: 30 }), feld('Rechnungs-Kürzel', 'rechnungsprefix', f.rechnungsprefix), feld('Angebots-Kürzel', 'angebotsprefix', f.angebotsprefix)),
    kk('Kleinunternehmer (§ 19 UStG, keine Umsatzsteuer auf Rechnungen)', klein, (v) => { klein = v; }),
    h('label', {}, 'Zusatztext unten auf Rechnungen und Angeboten (optional)'), h('textarea', { name: 'fusszeile', rows: 2 }, f.fusszeile || ''),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Firmendaten'), h('p', { class: 'small muted' }, 'Werden für Impressum, Datenschutz, Angebote, Rechnungen und Berichte verwendet. Bitte Angaben zu Steuern mit deiner Steuerberatung abstimmen.'), m, form);
}
async function rechtKarte() {
  const r = await api('/api/admin/einstellungen/recht'), m = h('div');
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/admin/einstellungen/recht', { method: 'PUT', body: Object.fromEntries(new FormData(e.target)) }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('label', {}, 'Impressum (leer lassen = Standardtext aus den Firmendaten)'), h('textarea', { name: 'impressum', rows: 6, placeholder: r.impressum_standard }, r.impressum || ''),
    h('label', {}, 'Datenschutzerklärung (leer lassen = Standardvorlage)'), h('textarea', { name: 'datenschutz', rows: 10, placeholder: r.datenschutz_standard }, r.datenschutz || ''),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern'), ' ', h('a', { class: 'btn sec', href: '/impressum', target: '_blank' }, 'Impressum ansehen'), ' ', h('a', { class: 'btn sec', href: '/datenschutz', target: '_blank' }, 'Datenschutz ansehen')));
  return h('div', { class: 'card' }, h('h2', {}, 'Impressum und Datenschutz'), h('p', { class: 'small muted' }, 'Die Standardtexte sind eine Vorlage und ersetzen keine Rechtsberatung. Bitte einmal von einem Anwalt oder Datenschutzbeauftragten prüfen lassen und bei Bedarf hier überschreiben. Die Links erscheinen automatisch auf der Anmeldeseite.'), m, form);
}

async function onboardingKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/onboarding'), m = h('div');
  const pct = d.gesamt ? Math.round(d.fertig / d.gesamt * 100) : 0;
  const zeilen = d.punkte.map(p => {
    const cb = h('input', { type: 'checkbox', checked: p.fertig, disabled: p.automatisch, style: 'width:auto', onchange: async (e) => { try { await api('/api/admin/kunden/' + kid + '/onboarding/' + p.code, { method: 'PATCH', body: { erledigt: e.target.checked } }); location.reload(); } catch (x) { fehler(m, x); e.target.checked = !e.target.checked; } } });
    return h('div', { class: 'modul' }, cb, h('div', { class: 'grow' }, h('b', {}, p.titel), p.automatisch ? [' ', h('span', { class: 'pill ok' }, 'automatisch erkannt')] : '', p.hilfe ? h('div', { class: 'small muted' }, p.hilfe) : '', p.erledigt_am ? h('div', { class: 'small muted' }, 'erledigt am ' + datum(p.erledigt_am)) : ''));
  });
  const neu = h('input', { placeholder: 'Eigener Punkt, z. B. „Flyer drucken“' });
  return h('div', { class: 'card' }, h('h2', {}, 'Onboarding-Checkliste ', h('span', { class: 'pill ' + (pct === 100 ? 'ok' : 'warn') }, d.fertig + ' von ' + d.gesamt)),
    h('div', { class: 'bar', style: 'margin:6px 0 12px' }, h('i', { style: 'width:' + pct + '%' })), m, zeilen,
    pct === 100 && d.status === 'onboarding' ? h('div', { class: 'msg ok' }, 'Alles erledigt. ', knopf('Kunde auf „aktiv“ setzen', async () => { try { await api('/api/admin/kunden/' + kid + '/status', { method: 'POST', body: { status: 'aktiv' } }); location.reload(); } catch (x) { fehler(m, x); } }, 'btn')) : '',
    h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, neu), knopf('Punkt hinzufügen', async () => { if (!neu.value.trim()) return; try { await api('/api/admin/kunden/' + kid + '/onboarding', { method: 'POST', body: { titel: neu.value } }); location.reload(); } catch (x) { fehler(m, x); } })));
}

function brandingKarte(kid, k) {
  const m = h('div'); let logoB64 = null;
  const datei = h('input', { type: 'file', accept: 'image/png,image/jpeg', onchange: (e) => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => { logoB64 = r.result; }; r.readAsDataURL(f); } });
  const farbe = h('input', { type: 'color', value: k.branding_farbe || '#4f46e5', style: 'width:60px;padding:2px' });
  let farbeGesetzt = !!k.branding_farbe;
  farbe.addEventListener('input', () => { farbeGesetzt = true; });
  const senden = async (extra) => { try { await api('/api/admin/kunden/' + kid + '/branding', { method: 'PUT', body: { farbe: farbeGesetzt ? farbe.value : null, logo_base64: logoB64, ...extra } }); melde(m, 'Gespeichert. Der Kunde sieht es beim nächsten Laden.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Branding im Kundenportal'),
    h('p', { class: 'small muted' }, 'Logo (PNG oder JPG, max. 400 KB) und Akzentfarbe, die der Kunde in seinem Portal sieht.'), m,
    k.logo_vorhanden ? h('p', {}, h('img', { src: '/api/admin/kunden/' + kid + '/logo', style: 'max-height:48px;background:#fff;border-radius:8px' })) : h('p', { class: 'small muted' }, 'Noch kein Logo.'),
    h('div', { class: 'row' }, datei, h('span', { class: 'small muted' }, 'Farbe'), farbe, knopf('Speichern', () => senden({}), 'btn'), k.logo_vorhanden && knopf('Logo entfernen', () => confirm('Logo entfernen?') && senden({ logo_entfernen: true }), 'bad'),
      k.branding_farbe && knopf('Farbe zurücksetzen', async () => { farbeGesetzt = false; senden({}); }, 'sec')));
}

async function kostenKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/kosten');
  return h('div', { class: 'card' }, h('h2', {}, 'Kosten (KI-Chat) pro Monat'),
    h('p', { class: 'small muted' }, 'Monatlicher Umsatz laut aktiven Buchungen: ' + fmtEuro(d.umsatz_monat_cent) + '. Die Kosten werden aus den Tokens und den Preisen unter Einstellungen berechnet.'),
    tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Tokens', z => z.tokens], ['Kosten', z => fmtEuro(Math.round(z.kosten_cent))], ['Anteil am Umsatz', z => d.umsatz_monat_cent ? (z.kosten_cent / d.umsatz_monat_cent * 100).toFixed(1).replace('.', ',') + ' %' : '–']], d.monate, 'Noch keine Kosten erfasst.'));
}

async function berichteKarte(kid) {
  const liste = await api('/api/admin/kunden/' + kid + '/berichte'), m = h('div');
  const monate = []; const jetzt = new Date();
  for (let i = 1; i <= 12; i++) { const d = new Date(jetzt.getFullYear(), jetzt.getMonth() - i, 1); monate.push([d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'), d.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })]); }
  const sel = select('monat', monate, monate[0][0]);
  const los = async (senden) => { try { const r = await api('/api/admin/kunden/' + kid + '/bericht', { method: 'POST', body: { monat: sel.value, senden } });
    melde(m, senden ? (r.gesendet ? 'Bericht erstellt und per E-Mail gesendet.' : 'Bericht erstellt, aber nicht gesendet: ' + (r.grund || 'unbekannt')) : 'Bericht erstellt.', r.gesendet || !senden ? 'ok' : 'info'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Monatsberichte'), h('p', { class: 'small muted' }, 'Wird jeden Monat automatisch erstellt und an den Kunden gemailt (wenn der Versand eingerichtet ist). Hier kannst du einen Monat von Hand erstellen oder erneut senden.'), m,
    tabelle([['Monat', z => z.titel], ['Gesendet', z => z.versendet_am ? zeit(z.versendet_am) : 'nein'], ['PDF', z => h('a', { href: '/api/admin/berichte/' + z.id + '/pdf', target: '_blank', rel: 'noopener' }, 'Öffnen')]], liste, 'Noch keine Berichte.'),
    h('div', { class: 'row', style: 'margin-top:12px' }, sel, knopf('Erstellen', () => los(false)), knopf('Erstellen und per Mail senden', () => los(true), 'btn')));
}

async function benachrKarte() {
  const c = await api('/api/admin/einstellungen/benachrichtigung'), m = h('div'); const v = { ...c };
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); o.termin_stunden = Number(o.termin_stunden);
    Object.assign(o, { anfrage_mails: v.anfrage_mails, termin_erinnerung: v.termin_erinnerung, monatsbericht: v.monatsbericht });
    try { await api('/api/admin/einstellungen/benachrichtigung', { method: 'PUT', body: o }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' }, feld('Alarm-E-Mail für dich (leer = erster Admin)', 'alarm_email', c.alarm_email, { type: 'email' }), feld('Terminerinnerung (Stunden vorher)', 'termin_stunden', c.termin_stunden, { type: 'number', min: 1, max: 168 })),
    kk('Kunden per Mail über neue Anfragen informieren', c.anfrage_mails, (x) => { v.anfrage_mails = x; }),
    kk('Kunden an Termine erinnern', c.termin_erinnerung, (x) => { v.termin_erinnerung = x; }),
    kk('Monatsbericht automatisch am Monatsanfang an Kunden senden', c.monatsbericht, (x) => { v.monatsbericht = x; }),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Benachrichtigungen'), h('p', { class: 'small muted' }, 'Jeder Kunde kann diese Mails in seinem Portal unter Einstellungen einzeln abschalten. Für dich: Fehler in Automationen und Server-Alarme kommen an die Alarm-E-Mail.'), m, form);
}

// ---------------------------------------------------------------- Angebote und Rechnungen
const BELEG_ST = { entwurf: '', gestellt: 'warn', versendet: 'warn', angenommen: 'ok', abgelehnt: 'bad', bezahlt: 'ok', storniert: 'bad' };
const belegPill = (z) => h('span', { class: 'pill ' + (z.ueberfaellig ? 'bad' : BELEG_ST[z.status] || '') }, z.ueberfaellig ? 'überfällig' : z.status);
const belegArt = (z) => z.storno_von ? 'Storno' : z.art === 'rechnung' ? 'Rechnung' : 'Angebot';
const eurIn = (v) => { const n = Math.round(parseFloat(String(v).replace(/\./g, '').replace(',', '.')) * 100); return Number.isFinite(n) ? n : 0; };
const eurOut = (c) => (c / 100).toFixed(2).replace('.', ',');

V.belege = async () => {
  const q = new URLSearchParams(location.hash.split('?')[1] || '');
  const art = q.get('art') || '', status = q.get('status') || '';
  const d = await api('/api/admin/belege?art=' + art + '&status=' + status), s = d.summen;
  const f = (a, st, l) => h('button', { class: (art === a && status === st) ? 'on' : '', onclick: () => { location.hash = '#belege?art=' + a + '&status=' + st; } }, l);
  return h('div', { class: 'stack' }, kopf('Angebote & Rechnungen'),
    h('p', { class: 'small' }, h('a', { href: '/api/admin/belege-export.csv', target: '_blank', rel: 'noopener' }, 'Rechnungen als CSV exportieren (Buchhaltung/sevDesk)')),
    h('div', { class: 'grid3' },
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Offen'), h('b', {}, euro(s.offen))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Überfällig (' + s.ueberfaellig_n + ')'), h('b', {}, euro(s.ueberfaellig))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Bezahlt diesen Monat'), h('b', {}, euro(s.bezahlt_monat)))),
    h('div', { class: 'card' }, h('div', { class: 'tabs' }, f('', '', 'Alle'), f('rechnung', '', 'Rechnungen'), f('angebot', '', 'Angebote'), f('rechnung', 'gestellt', 'Offen'), f('rechnung', 'bezahlt', 'Bezahlt'), f('', 'entwurf', 'Entwürfe')),
      tabelle([['Nr.', z => h('a', { href: '#beleg/' + z.id }, z.nummer || 'Entwurf')], ['Art', belegArt], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Betreff', z => z.betreff], ['Datum', z => datum(z.datum)], ['Fällig/gültig bis', z => datum(z.faellig_am)], ['Betrag', z => fmtEuro(z.brutto_cent)], ['Status', belegPill]], d.belege, 'Noch keine Belege. Anlegen im jeweiligen Kunden.')),
    h('p', { class: 'small muted' }, 'Hinweis: Rechnungen werden hier als PDF erstellt. Ab 2027/2028 gelten für Rechnungen zwischen Unternehmen schrittweise Pflichten zur E-Rechnung (z. B. ZUGFeRD/XRechnung). Das ist hier noch nicht umgesetzt; bitte mit der Steuerberatung abstimmen.'));
};

async function belegEditor(id, kid, art) {
  let b, k, vorschlag = [];
  if (id) { const r = await api('/api/admin/belege/' + id); b = r.beleg; k = r.kunde; }
  else {
    const r = await api('/api/admin/kunden/' + kid), v = await api('/api/admin/kunden/' + kid + '/belege-vorlage');
    k = { kundennummer: r.kunde.kundennummer, firma: r.kunde.firma, email: r.kunde.email, referenzkunde: r.kunde.referenzkunde };
    vorschlag = v.positionen;
    b = { art, status: 'entwurf', betreff: '', einleitung: '', schluss: '', leistungszeitraum: '', positionen: vorschlag, kunden_id: kid };
  }
  const frei = b.status === 'entwurf', m = h('div');
  const zeilen = [...b.positionen];
  const box = h('div'), sum = h('div', { class: 'small muted', style: 'text-align:right' });
  const feldB = (name, wert, extra = {}) => h('input', { name, value: wert ?? '', disabled: !frei, ...extra });
  const betreff = feldB('betreff', b.betreff, { placeholder: 'z. B. Website-Paket' }), zeitraum = feldB('leistungszeitraum', b.leistungszeitraum, { placeholder: 'z. B. November 2026' });
  const einl = h('textarea', { rows: 3, disabled: !frei }, b.einleitung || ''), schluss = h('textarea', { rows: 3, disabled: !frei }, b.schluss || '');
  const rechne = () => { const n = zeilen.reduce((a, z) => a + Math.round(Number(z.menge || 0) * (z.preis_cent || 0)), 0); sum.textContent = 'Zwischensumme netto: ' + euro(n) + (frei ? ' (Umsatzsteuer wird beim Ausstellen nach den Firmendaten berechnet)' : ''); };
  const zeichne = () => {
    box.replaceChildren(...zeilen.map((z, i) => h('div', { class: 'row', style: 'margin-bottom:6px;align-items:center' },
      h('div', { class: 'grow' }, h('input', { value: z.text, placeholder: 'Beschreibung', disabled: !frei, oninput: (e) => { z.text = e.target.value; } })),
      h('div', { style: 'width:80px' }, h('input', { value: String(z.menge).replace('.', ','), disabled: !frei, oninput: (e) => { z.menge = parseFloat(e.target.value.replace(',', '.')) || 0; rechne(); } })),
      h('div', { style: 'width:80px' }, h('input', { value: z.einheit || '', placeholder: 'Einheit', disabled: !frei, oninput: (e) => { z.einheit = e.target.value; } })),
      h('div', { style: 'width:110px' }, h('input', { value: eurOut(z.preis_cent), disabled: !frei, oninput: (e) => { z.preis_cent = eurIn(e.target.value); rechne(); } })),
      frei ? knopf('✕', () => { zeilen.splice(i, 1); zeichne(); }, 'sec') : ''))); rechne();
  };
  zeichne();
  const daten = () => ({ betreff: betreff.value, einleitung: einl.value, schluss: schluss.value, leistungszeitraum: zeitraum.value, positionen: zeilen.map(z => ({ text: z.text, menge: z.menge, einheit: z.einheit || '', preis_cent: z.preis_cent })) });
  const aktion = (text, pfad, body, ok, art = 'sec', bestaetigen) => knopf(text, async () => {
    if (bestaetigen && !confirm(bestaetigen)) return;
    try { const r = await api(pfad, { method: 'POST', body }); if (ok) ok(r); } catch (x) { fehler(m, x); } }, art);
  const speichern = knopf('Entwurf speichern', async () => { try {
    if (id) { await api('/api/admin/belege/' + id, { method: 'PUT', body: daten() }); melde(m, 'Gespeichert.', 'ok'); }
    else { const r = await api('/api/admin/kunden/' + kid + '/belege', { method: 'POST', body: { art, ...daten() } }); location.hash = '#beleg/' + r.id; }
  } catch (x) { fehler(m, x); } }, 'btn');
  const neu = () => location.reload();
  const knoepfe = [];
  if (id) {
    knoepfe.push(h('a', { class: 'btn sec small', href: '/api/admin/belege/' + id + '/pdf', target: '_blank', rel: 'noopener' }, 'PDF ansehen'));
    if (b.status === 'entwurf') knoepfe.push(speichern, aktion('Ausstellen', '/api/admin/belege/' + id + '/ausstellen', {}, (r) => { melde(m, 'Ausgestellt als ' + r.nummer + '.', 'ok'); setTimeout(neu, 700); }, 'btn',
      'Beleg jetzt ausstellen? Danach bekommt er eine feste Nummer und kann nicht mehr geändert werden.'),
      knopf('Entwurf löschen', async () => { if (confirm('Entwurf löschen?')) { try { await api('/api/admin/belege/' + id, { method: 'DELETE' }); location.hash = '#belege'; } catch (x) { fehler(m, x); } } }, 'bad'));
    if (['gestellt', 'versendet'].includes(b.status)) knoepfe.push(aktion(b.versendet_am ? 'Erneut per Mail senden' : 'Per Mail an Kunden senden', '/api/admin/belege/' + id + '/senden', {}, (r) => { melde(m, r.gesendet ? 'Per E-Mail gesendet.' : 'Nicht gesendet: ' + r.grund, r.gesendet ? 'ok' : 'err'); if (r.gesendet) setTimeout(neu, 800); }, 'btn'));
    if (b.art === 'rechnung' && ['gestellt', 'versendet'].includes(b.status)) {
      knoepfe.push(aktion('Als bezahlt markieren', '/api/admin/belege/' + id + '/bezahlt', {}, neu, 'sec', 'Zahlungseingang in voller Höhe bestätigen?'));
      if (new Date(b.faellig_am) < new Date()) for (const st of [1, 2, 3]) if (st > b.mahnstufe) knoepfe.push(aktion({ 1: 'Zahlungserinnerung senden', 2: '1. Mahnung senden', 3: '2. Mahnung senden' }[st], '/api/admin/belege/' + id + '/mahnung', { stufe: st, senden: true }, (r) => { melde(m, r.gesendet ? 'Gesendet.' : 'Nicht gesendet: ' + r.grund, r.gesendet ? 'ok' : 'err'); if (r.gesendet) setTimeout(neu, 800); }, 'sec', 'Schreiben jetzt per E-Mail an den Kunden senden?'));
    }
    if (b.art === 'rechnung' && !b.storno_von && ['gestellt', 'versendet', 'bezahlt'].includes(b.status)) knoepfe.push(aktion('Stornieren', '/api/admin/belege/' + id + '/stornieren', {}, (r) => { location.hash = '#beleg/' + r.id; }, 'bad', 'Rechnung stornieren? Es wird eine Stornorechnung mit eigener Nummer erzeugt.'));
    if (b.art === 'angebot' && ['gestellt', 'versendet'].includes(b.status)) knoepfe.push(aktion('Angenommen', '/api/admin/belege/' + id + '/angebot-status', { status: 'angenommen' }, neu), aktion('Abgelehnt', '/api/admin/belege/' + id + '/angebot-status', { status: 'abgelehnt' }, neu, 'sec'));
    if (b.art === 'angebot' && ['gestellt', 'versendet', 'angenommen'].includes(b.status) && !k.referenzkunde) knoepfe.push(aktion('Rechnung daraus erstellen', '/api/admin/belege/' + id + '/rechnung', {}, (r) => { location.hash = '#beleg/' + r.id; }, 'sec'));
  } else knoepfe.push(speichern);
  const titel = (b.storno_von ? 'Stornorechnung' : art === 'rechnung' || b.art === 'rechnung' ? 'Rechnung' : 'Angebot') + (b.nummer ? ' ' + b.nummer : ' (Entwurf)');
  return h('div', { class: 'stack' }, kopf(titel, belegPill(b), h('a', { class: 'btn sec small', href: '#kunde/' + (b.kunden_id || kid) }, '← ' + k.firma)),
    k.referenzkunde && (b.art || art) === 'rechnung' ? h('div', { class: 'msg err' }, 'Das ist ein Referenzkunde – Rechnungen sind für Referenzkunden gesperrt.') : '', m,
    h('div', { class: 'card' }, h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Betreff'), betreff), h('div', {}, h('label', {}, 'Leistungszeitraum'), zeitraum)),
      h('label', {}, 'Einleitung (optional)'), einl, h('h3', { style: 'margin-top:16px' }, 'Positionen'), h('div', { class: 'small muted' }, 'Beschreibung · Menge · Einheit · Einzelpreis netto in €'), box,
      frei ? knopf('+ Position', () => { zeilen.push({ text: '', menge: 1, einheit: '', preis_cent: 0 }); zeichne(); }) : '', sum,
      !frei ? h('div', { style: 'text-align:right;margin-top:8px' }, h('div', {}, 'Netto ' + fmtEuro(b.netto_cent)), b.kleinunternehmer ? h('div', { class: 'small muted' }, 'Kleinunternehmer – keine Umsatzsteuer') : h('div', {}, 'USt ' + Number(b.ust_satz) + ' % ' + fmtEuro(b.ust_cent)), h('div', {}, h('b', {}, 'Gesamt ' + fmtEuro(b.brutto_cent)))) : '',
      h('label', {}, 'Schlusstext (optional)'), schluss,
      !frei ? h('p', { class: 'small muted', style: 'margin-top:10px' }, 'Datum ' + datum(b.datum) + ' · ' + (b.art === 'rechnung' ? 'zahlbar bis ' : 'gültig bis ') + datum(b.faellig_am) + (b.versendet_am ? ' · gesendet am ' + datum(b.versendet_am) : '') + (b.bezahlt_am ? ' · bezahlt am ' + datum(b.bezahlt_am) : '') + (b.mahnstufe ? ' · Mahnstufe ' + b.mahnstufe : '')) : ''),
    h('div', { class: 'row' }, knoepfe));
}

async function belegeKarte(kid, referenz) {
  const liste = await api('/api/admin/kunden/' + kid + '/belege');
  return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { class: 'grow', style: 'margin:0' }, 'Angebote & Rechnungen'),
    h('a', { class: 'btn sec small', href: '#neubeleg/' + kid + '/angebot' }, '+ Angebot'), referenz ? '' : h('a', { class: 'btn small', href: '#neubeleg/' + kid + '/rechnung' }, '+ Rechnung')),
    tabelle([['Nr.', z => h('a', { href: '#beleg/' + z.id }, z.nummer || 'Entwurf')], ['Art', belegArt], ['Betreff', z => z.betreff], ['Datum', z => datum(z.datum)], ['Betrag', z => fmtEuro(z.brutto_cent)], ['Status', belegPill]], liste, referenz ? 'Referenzkunde: keine Rechnungen, Angebote sind möglich.' : 'Noch keine Belege.'));
}

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
  const mb = h('div'), mon = h('input', { type: 'month', value: new Date().toISOString().slice(0, 7), style: 'max-width:200px' }), erg = h('div');
  const rechne = async (vorschau) => { try { const r = await api('/api/admin/vertrieb/provisionen/berechnen', { method: 'POST', body: { monat: mon.value, vorschau } });
    if (vorschau) { const sum = r.zeilen.reduce((a, z) => a + Number(z.betrag_cent), 0);
      erg.replaceChildren(h('p', { class: 'small muted' }, r.zeilen.length + ' Posten, Summe ' + fmtEuro(sum) + (r.schon_vorhanden ? ' – für diesen Monat gibt es schon ' + r.schon_vorhanden + ' Einträge (werden nicht doppelt angelegt).' : '')),
        tabelle([['Vertriebler', z => z.partner], ['Kunde', z => z.kundennummer], ['Vertragsmonat', z => z.vm], ['Basis', z => fmtEuro(z.basis_cent)], ['%', z => z.prozent], ['Betrag', z => fmtEuro(z.betrag_cent)]], r.zeilen, 'Für diesen Monat entstehen keine Provisionen.'));
    } else { erg.replaceChildren(); melde(mb, r.angelegt + ' Provisionen angelegt, ' + r.uebersprungen + ' schon vorhanden.', 'ok'); } } catch (x) { fehler(mb, x); } };
  const berechnen = h('div', { class: 'card' }, h('h2', {}, 'Provisionen berechnen'), h('p', { class: 'small muted' }, 'Rechnet für alle aktiven Vertriebler die laufende Provision des gewählten Monats nach den freigegebenen Regeln. Erst Vorschau ansehen, dann anlegen. Die Vertriebler sehen ihre Beträge sofort im Partnerportal.'), mb,
    h('div', { class: 'row' }, mon, knopf('Vorschau', () => rechne(true)), knopf('Anlegen', () => confirm('Provisionen für ' + mon.value + ' jetzt anlegen?') && rechne(false), 'btn')), erg);
  return h('div', { class: 'stack' }, kopf('Vertriebler', h('span', { class: 'pill ok' }, aktiv + ' aktiv')),
    h('div', { class: 'card' }, tabelle([['Name', z => h('a', { href: '#partner/' + z.id }, z.name)], ['Firma', z => z.firma], ['Status', z => pill(z.status)], ['Kunden', z => z.kunden], ['Offene Leads', z => z.offene_leads], ['Provision offen', z => fmtEuro(z.offen_cent)], ['IBAN', z => z.iban_hinterlegt ? 'ja' : 'nein']], d, 'Noch keine Vertriebler.')),
    berechnen, h('div', { class: 'card' }, h('h2', {}, 'Neuer Vertriebler'), m, f));
};

function abrechnungsZeile(pid, liste, mp) {
  const monate = [...new Set(liste.map(z => String(z.monat).slice(0, 7)))];
  if (!monate.length) return h('span');
  const sel = h('select', {}, ...monate.map(x => h('option', { value: x }, x)));
  return h('div', { class: 'row', style: 'margin-top:10px' }, h('span', { class: 'small muted' }, 'Abrechnung als PDF:'), sel,
    knopf('Öffnen', () => window.open('/api/admin/vertrieb/' + pid + '/abrechnung/' + sel.value, '_blank', 'noopener')),
    knopf('Verlängerung erfassen', async () => { const bid = prompt('Buchungs-ID der verlängerten Buchung (steht in der Kundenakte):'); if (!bid) return; const mon = prompt('Abrechnungsmonat (JJJJ-MM)', sel.value);
      if (mon) bestaetigt(mp, () => api('/api/admin/vertrieb/provisionen/verlaengerung', { method: 'POST', body: { buchung_id: bid.trim(), monat: mon } })); }));
}

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
    z.status === 'ausgezahlt' && z.art !== 'rueckbuchung' && knopf('Zurückbuchen', async () => { const mon = prompt('In welchem Monat verrechnen? (JJJJ-MM)', new Date().toISOString().slice(0, 7)); if (mon) bestaetigt(mp, () => api('/api/admin/vertrieb/provisionen/' + z.id + '/rueckbuchung', { method: 'POST', body: { monat: mon } })); }, 'bad'),
    ['berechnet', 'freigegeben'].includes(z.status) && knopf('Stornieren', () => confirm('Provision stornieren?') && bestaetigt(mp, () => api('/api/admin/vertrieb/provisionen/' + z.id + '/status', { method: 'POST', body: { status: 'storniert' } })), 'bad'));
  const summe = d.provisionen.filter(z => ['berechnet', 'freigegeben'].includes(z.status)).reduce((a, z) => a + z.betrag_cent, 0);
  const mz = h('div'), mail = h('input', { type: 'email', value: p.email || '', placeholder: 'E-Mail des Vertrieblers' }), perMail = h('input', { type: 'checkbox', checked: true, style: 'width:auto' });
  const zugang = h('div', { class: 'card' }, h('h2', {}, 'Portal-Zugang'), h('p', { class: 'small muted' }, 'Der Vertriebler bekommt einen Link, legt damit selbst sein Passwort an und sieht danach seine Kunden, Leads und Provisionen unter /vertrieb.'), mz,
    tabelle([['E-Mail', z => z.email], ['Passwort', z => z.hat_passwort ? 'gesetzt' : 'offen'], ['2FA', (z) => z.totp_aktiv ? knopf('2FA zurücksetzen', async () => { if (confirm('Zwei-Faktor-Anmeldung dieses Zugangs ausschalten?')) { try { await api('/api/admin/benutzer/' + z.id + '/2fa-zuruecksetzen', { method: 'POST' }); location.reload(); } catch (x) { alert(x.message); } } }) : '–'], ['Letzter Login', z => zeit(z.letzter_login)],
      ['', z => knopf(z.aktiv ? 'Sperren' : 'Freigeben', async () => { try { await api('/api/admin/vertrieb/zugang/' + z.id + '/aktiv', { method: 'POST', body: { aktiv: !z.aktiv } }); location.reload(); } catch (x) { fehler(mz, x); } }, z.aktiv ? 'bad' : 'sec')]], d.zugaenge, 'Noch kein Zugang.'),
    h('div', { class: 'row', style: 'margin-top:12px' }, mail, h('label', { class: 'small', style: 'display:flex;gap:6px;align-items:center;white-space:nowrap' }, perMail, 'per E-Mail senden'),
      knopf('Einladung erzeugen', async () => { try { const r = await api('/api/admin/vertrieb/partner/' + pid + '/einladung', { method: 'POST', body: { email: mail.value, per_mail: perMail.checked } });
        mz.replaceChildren(h('div', { class: 'msg info' }, 'Einladungslink (' + r.gueltig_tage + ' Tage gültig): ', h('br'), r.einladungslink), mailHinweis(r.mail)); } catch (x) { fehler(mz, x); } }, 'btn')));
  return h('div', { class: 'stack' }, kopf(p.name, pill(p.status), h('a', { class: 'btn sec small', href: '#vertrieb' }, '← Liste')),
    h('div', { class: 'card' }, h('h2', {}, 'Stammdaten'), m, stamm), zugang,
    h('div', { class: 'card' }, h('h2', {}, 'Zugeordnete Kunden (' + d.kunden.length + ')'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Paket', z => z.paket || '–'], ['Status', z => pill(z.status)], ['Monatlich', z => fmtEuro(z.monatlich_cent)]], d.kunden, 'Noch keine Kunden. Zuordnung im Kunden unter Stammdaten (Feld Vertriebler).')),
    h('div', { class: 'card' }, h('h2', {}, 'Provisionen'), h('p', { class: 'small muted' }, 'Offen (berechnet/freigegeben): ' + fmtEuro(summe)), mp,
      tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Art', z => ({ laufend: 'Laufend', verlaengerung: 'Verlängerung', rueckbuchung: 'Rückbuchung' })[z.art] || z.art], ['Vertragsmonat', z => z.vertragsmonat || '–'], ['Basis', z => fmtEuro(z.basis_cent)], ['%', z => z.prozent], ['Betrag', z => fmtEuro(z.betrag_cent)], ['Status', z => pill(z.status)], ['', provAktion]], d.provisionen, 'Noch keine Provisionen berechnet.'),
      abrechnungsZeile(pid, d.provisionen, mp)),
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

  const refK = h('input', { type: 'checkbox', checked: k.referenzkunde, style: 'width:auto' }), refE = h('input', { type: 'checkbox', checked: k.referenz_nennen_erlaubt, style: 'width:auto' });
  const stamm = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const o = Object.fromEntries(new FormData(e.target));
    o.referenzkunde = refK.checked; o.referenz_nennen_erlaubt = refK.checked && refE.checked;
    try { await api('/api/admin/kunden/' + kid, { method: 'PATCH', body: o }); melde(mk, 'Gespeichert.', 'ok'); setTimeout(() => location.reload(), 600); } catch (x) { melde(mk, x.message); }
  } }, h('div', { class: 'form2' },
    feld('Firma', 'firma', k.firma), feld('Rechtsform', 'rechtsform', k.rechtsform), feld('Ansprechpartner', 'ansprechpartner', k.ansprechpartner),
    feld('E-Mail', 'email', k.email), feld('Telefon', 'telefon', k.telefon), feld('Branche', 'branche', k.branche),
    feld('Straße', 'strasse', k.strasse), feld('PLZ', 'plz', k.plz), feld('Ort', 'ort', k.ort), feld('Domain', 'domain', k.domain),
    h('div', {}, h('label', {}, 'Paket'), h('select', { name: 'paket_code' }, h('option', { value: '' }, '–'), paketListe.map(p => h('option', { value: p.code, selected: p.code === k.paket_code }, p.name))))),
    h('label', {}, 'Notizen'), h('textarea', { name: 'notizen', rows: 3 }, k.notizen || ''),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, refK, 'Referenzkunde (zahlt nichts, wird aber normal betreut; zählt nicht in Umsatz und Provision)'),
    h('label', {}, 'Was bekommt der Referenzkunde?'), h('textarea', { name: 'referenz_leistung', rows: 2 }, k.referenz_leistung || ''),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, refE, 'Darf als Referenz genannt werden (Einverständnis liegt vor)'),
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
    try { const r = await api('/api/admin/kunden/' + kid + '/einladung', { method: 'POST', body: { email: mail.value, per_mail: true } });
      linkbox.replaceChildren(h('div', { class: 'msg info' }, 'Einladungslink (' + r.gueltig_tage + ' Tage gültig): ', h('br'), r.einladungslink), mailHinweis(r.mail)); } catch (x) { melde(linkbox, x.message); }
  } }, 'Einladungslink erzeugen');
  const zugaenge = tabelle([['E-Mail', z => z.email], ['Rolle', z => ({ inhaber: 'Inhaber', mitarbeiter: 'Mitarbeiter', nur_lesen: 'Nur ansehen' })[z.kunden_rolle] || z.kunden_rolle], ['Passwort', z => z.hat_passwort ? 'gesetzt' : 'offen'], ['2FA', (z) => z.totp_aktiv ? knopf('2FA zurücksetzen', async () => { if (confirm('Zwei-Faktor-Anmeldung dieses Zugangs ausschalten?')) { try { await api('/api/admin/benutzer/' + z.id + '/2fa-zuruecksetzen', { method: 'POST' }); location.reload(); } catch (x) { alert(x.message); } } }) : '–'], ['Letzter Login', z => zeit(z.letzter_login)],
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
    kopf(k.firma, h('span', { class: 'pill' }, k.kundennummer), pill(k.status), k.referenzkunde ? h('span', { class: 'pill warn' }, 'Referenzkunde') : '', status, h('a', { class: 'btn sec small', href: '#kunden' }, '← Liste')),
    h('div', { class: 'card' }, h('h2', {}, 'Stammdaten'), mk, stamm),
    await onboardingKarte(kid),
    h('div', { class: 'card' }, h('h2', {}, 'Vertriebler'), mv, h('div', { class: 'row' }, h('div', { class: 'grow' }, h('select', { id: 'vsel' }, h('option', { value: '' }, '– kein Vertriebler –'), partnerListe.map(p => h('option', { value: p.id, selected: p.id === k.vertriebspartner_id }, p.name + (p.status !== 'aktiv' ? ' (' + p.status + ')' : ''))))),
      knopf('Zuordnen', async () => { try { await api('/api/admin/kunden/' + kid + '/partner', { method: 'PUT', body: { partner_id: document.getElementById('vsel').value || null } }); melde(mv, 'Gespeichert.', 'ok'); } catch (x) { melde(mv, x.message); } }))),
    h('div', { class: 'card' }, h('h2', {}, 'Module des Kunden (Schalter)'), h('p', { class: 'small muted' }, 'Was hier aktiv ist, sieht der Kunde in seinem Portal.'), mz, module),
    h('div', { class: 'card' }, h('h2', {}, 'Portal-Zugang'), zugaenge, h('div', { class: 'row', style: 'margin-top:12px' }, h('div', { class: 'grow' }, mail), einladen), linkbox),
    h('div', { class: 'card' }, h('h2', {}, 'Buchungen'), mb, buchungen, h('h3', { style: 'margin-top:18px' }, 'Neue Buchung'), bform),
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), mw, webs, h('div', { style: 'height:10px' }), wform,
      h('p', { class: 'small muted' }, 'Danach auf dem Server einmal: mkctl site-add <domain>, damit Ordner und Webserver bereit sind.')),
    await belegeKarte(kid, k.referenzkunde),
    await berichteKarte(kid),
    await kostenKarte(kid),
    brandingKarte(kid, k),
    h('div', { class: 'card' }, h('h2', {}, 'Daten des Kunden'), tabs, mdaten));
}

async function zeige() {
  const hash = (location.hash || '#uebersicht').slice(1);
  let seite = hash.split('/')[0].split('?')[0], inhalt;
  try {
    if (seite === 'kunde') inhalt = await kundeDetail(hash.split('/')[1]);
    else if (seite === 'partner') inhalt = await partnerDetail(hash.split('/')[1]);
    else if (seite === 'lead') inhalt = await leadDetail(hash.split('/')[1]);
    else if (seite === 'beleg') inhalt = await belegEditor(hash.split('/')[1]);
    else if (seite === 'neubeleg') inhalt = await belegEditor(null, hash.split('/')[1], hash.split('/')[2]);
    else if (V[seite]) inhalt = await V[seite]();
    else { seite = 'uebersicht'; inhalt = await V.uebersicht(); }
  } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  root.replaceChildren(gerüst(seite === 'kunde' ? 'kunden' : seite === 'partner' ? 'vertrieb' : seite === 'lead' ? 'leads' : (seite === 'beleg' || seite === 'neubeleg') ? 'belege' : seite, inhalt));
}

(async () => {
  try {
    const me = await api('/api/me');
    if (me.rolle !== 'admin') { location.href = '/app'; return; }
    ich = me;
    paketListe = (await api('/api/admin/katalog')).produkte;
  } catch (e) { return; }
  window.addEventListener('hashchange', zeige);
  zeige();
})();
