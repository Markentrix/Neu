import { h, api, datum, zeit, euro, groesse, melde, abmelden, zweiFaktorKarte, rechtFuss } from './common.js';

const root = document.getElementById('app');
const NAV = [['uebersicht', 'Übersicht'], ['postfach', 'Nachrichten'], ['freigaben', 'Freigaben'], ['aufgaben', 'Aufgaben'], ['kennzahlen', 'Kennzahlen'], ['kunden', 'Kunden'], ['neu', 'Neuer Kunde'], ['vertrieb', 'Vertriebler'], ['leads', 'Leads'], ['websites', 'Websites & Demos'], ['belege', 'Angebote & Rechnungen'], ['preise', 'Preise & Konditionen'], ['compliance', 'Datenschutz & Qualität'], ['katalog', 'Pakete (Katalog)'], ['einstellungen', 'Einstellungen'], ['protokoll', 'Protokoll']];
let paketListe = [], ich = null;
const zaehlerAdmin = {};

function gerüst(aktiv, inhalt) {
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, h('div', { class: 'logo' }, 'M'), 'Admin'),
      NAV.map(n => h('a', { class: 'nav' + (n[0] === aktiv ? ' on' : ''), href: '#' + n[0] }, n[1], zaehlerAdmin[n[0]] ? h('span', { class: 'badge' }, zaehlerAdmin[n[0]]) : '')),
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
    h('div', { class: 'grid3' },
      h('a', { class: 'card stat', href: '#postfach', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Nachrichten offen (' + d.zusammenarbeit.tickets_ungelesen + ' ungelesen)'), h('b', {}, d.zusammenarbeit.tickets_offen)),
      h('a', { class: 'card stat', href: '#freigaben', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Freigaben warten auf Kunden'), h('b', {}, d.zusammenarbeit.freigaben_wartend)),
      h('a', { class: 'card stat', href: '#aufgaben', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Aufgaben offen (' + d.zusammenarbeit.aufgaben_ueberfaellig + ' überfällig)'), h('b', {}, d.zusammenarbeit.aufgaben_offen))),
    d.avv_fehlt.length ? h('div', { class: 'card' }, h('h2', {}, 'AVV fehlt bei ' + d.avv_fehlt.length + (d.avv_fehlt.length === 1 ? ' Kunde' : ' Kunden')), h('p', { class: 'small muted' }, 'Ohne unterschriebenen Auftragsverarbeitungsvertrag sollten keine Kundendaten verarbeitet werden.'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Status', z => pill(z.status)]], d.avv_fehlt)) : '',
    ob.length ? h('div', { class: 'card' }, h('h2', {}, 'Neue Kunden im Onboarding'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Fortschritt', z => z.fertig + ' von ' + z.gesamt]], ob)) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Letzte Aktionen'), tabelle([['Zeit', z => zeit(z.zeit)], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d.letzte_aktionen)));
};

const modulZelle = (z) => {
  const wrap = h('div', { class: 'modul-zelle' }), panel = h('div', { class: 'small', style: 'display:none;margin-top:6px' });
  const kopf = h('a', { href: '#', onclick: (e) => { e.preventDefault(); panel.style.display = panel.style.display === 'none' ? 'block' : 'none'; } });
  const zeige = () => {
    const akt = z.module.filter(m => m.aktiv);
    kopf.replaceChildren(akt.length + ' von ' + z.module.length + ' ▾');
    chips.replaceChildren(...(akt.length ? akt.map(m => h('span', { class: 'pill ok', style: 'margin:1px 2px 1px 0' }, m.name)) : [h('span', { class: 'muted' }, 'keine aktiv')]));
  };
  const chips = h('div', { style: 'margin-top:4px' });
  panel.append(...z.module.map(m => {
    const cb = h('input', { type: 'checkbox', checked: m.aktiv, style: 'width:auto', onchange: async (e) => {
      try { await api('/api/admin/kunden/' + z.id + '/module/' + m.code, { method: 'PUT', body: { aktiv: e.target.checked } }); m.aktiv = e.target.checked; zeige(); }
      catch (x) { e.target.checked = !e.target.checked; alert(x.message); }
    } });
    return h('label', { style: 'display:flex;gap:6px;align-items:center;margin:2px 0;white-space:nowrap' }, cb, m.name, ' ', h('span', { class: 'pill' }, m.art === 'agent' ? 'Agent' : 'Portal'));
  }));
  zeige(); wrap.append(kopf, chips, panel); return wrap;
};

V.kunden = async () => {
  const q = h('input', { placeholder: 'Suchen nach Firma, Nummer, E-Mail …' });
  const box = h('div'), nurRef = h('input', { type: 'checkbox', style: 'width:auto', onchange: () => lade() });
  const lade = async () => {
    let d = await api('/api/admin/kunden?q=' + encodeURIComponent(q.value));
    if (nurRef.checked) d = d.filter(z => z.referenzkunde);
    box.replaceChildren(tabelle([
      ['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => h('span', {}, z.firma, z.referenzkunde ? [' ', h('span', { class: 'pill warn' }, 'Referenz')] : '')], ['Paket', z => z.paket || '–'],
      ['Status', z => pill(z.status)], ['Module', z => modulZelle(z)], ['Zugang', z => z.zugang_aktiv ? 'ja' : 'nein'], ['AVV', z => z.avv_ok ? h('span', { class: 'pill ok' }, 'ja') : h('span', { class: 'pill warn' }, 'fehlt')], ['Domain', z => z.domain]], d, 'Noch keine Kunden.'));
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
    zweiFaktorKarte(), await websiteCheckKarte(), await firmaKarte(), await benachrKarte(), await rechtKarte(), await avvEinstKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'KI-Assistent im Kunden-Chat'), h('p', { class: 'small muted' }, d.ki.key_gesetzt ? 'API-Key ist hinterlegt – der Chat antwortet direkt über das Portal.' : 'Noch kein API-Key – der Chat nutzt den n8n-Webhook, falls eingerichtet. Den Key gibt es in der Anthropic-Konsole (console.anthropic.com), getrennt vom Claude-Abo.'), m2, fk), m3);
};

const kk = (label, wert, set) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', checked: wert, style: 'width:auto', onchange: (e) => set(e.target.checked) }), label);
async function websiteCheckKarte() {
  const d = await api('/api/admin/website-check'), m = h('div'), box = h('div');
  const erzeugen = async () => {
    if (d.aktiv && !confirm('Es gibt schon einen Schlüssel. Ein neuer ersetzt ihn, die Website muss dann den neuen bekommen. Fortfahren?')) return;
    try { const r = await api('/api/admin/website-check/schluessel', { method: 'POST', body: {} }); box.replaceChildren(h('div', { class: 'msg info' }, 'Neuer Schlüssel (wird nur jetzt angezeigt, bitte kopieren): ', h('br'), h('code', { style: 'word-break:break-all' }, r.schluessel))); } catch (x) { melde(m, x.message); }
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Website-Check → Leads'), h('p', { class: 'small muted' }, 'Wer den Website-Check auf markentrix.de nutzt, landet hier als Lead (mit Ergebnis). Adresse für die Website: ', h('code', {}, d.adresse), '. Status: ', d.aktiv ? h('span', { class: 'pill ok' }, 'Schlüssel gesetzt') : h('span', { class: 'pill warn' }, 'noch nicht eingerichtet')),
    m, box, h('p', {}, h('button', { class: 'btn sec', onclick: erzeugen }, d.aktiv ? 'Neuen Schlüssel erzeugen' : 'Schlüssel erzeugen')));
}

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
async function avvEinstKarte() {
  const r = await api('/api/admin/einstellungen/avv'), m = h('div');
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/admin/einstellungen/avv', { method: 'PUT', body: Object.fromEntries(new FormData(e.target)) }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('label', {}, 'Unterauftragsverarbeiter im AVV (eine Zeile je Firma: Name | Leistung | Sitz). Leer lassen = Standardliste.'),
    h('textarea', { name: 'unterauftragnehmer', rows: 6, placeholder: r.standard }, r.unterauftragnehmer || ''),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'AVV: Unterauftragsverarbeiter'),
    h('p', { class: 'small muted' }, 'Diese Liste steht in Anlage 2 jedes AVV. Bitte vollständig und aktuell halten (z. B. E-Mail-Anbieter, Telefonie-Dienst) und den Vertragstext einmal juristisch prüfen lassen.'), m, form);
}

async function avvKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/avv'), m = h('div');
  const neu = async () => { try { await api('/api/admin/kunden/' + kid + '/avv', { method: 'POST' }); location.reload(); } catch (x) { fehler(m, x); } };
  const hoch = (z) => { const datei = h('input', { type: 'file', accept: 'application/pdf,image/png,image/jpeg' }), tag = h('input', { type: 'date', value: new Date().toISOString().slice(0, 10), style: 'max-width:160px' });
    return h('span', { class: 'row' }, datei, tag, knopf('Ablegen', () => { const f = datei.files[0]; if (!f) return fehler(m, { message: 'Bitte zuerst die unterschriebene Datei wählen.' });
      const r = new FileReader(); r.onload = async () => { try { await api('/api/admin/avv/' + z.id + '/upload', { method: 'POST', body: { datei_base64: r.result, datei_name: f.name, unterschrieben_am: tag.value } }); location.reload(); } catch (x) { fehler(m, x); } }; r.readAsDataURL(f); }, 'btn')); };
  const aktion = (z) => h('span', { class: 'row' },
    h('a', { class: 'btn sec small', href: '/api/admin/avv/' + z.id + '/vorlage.pdf', target: '_blank', rel: 'noopener' }, 'Vertrag (PDF)'),
    knopf('Per Mail senden', async () => { if (confirm('AVV jetzt per E-Mail an den Kunden senden?')) { try { await api('/api/admin/avv/' + z.id + '/senden', { method: 'POST' }); melde(m, 'Gesendet.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } } }, 'sec small'),
    z.hat_datei ? h('a', { class: 'btn sec small', href: '/api/admin/avv/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Unterschrieben ansehen') : knopf('Entwurf löschen', async () => { if (confirm('Entwurf löschen?')) { try { await api('/api/admin/avv/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { fehler(m, x); } } }, 'bad small'));
  return h('div', { class: 'card' }, h('h2', {}, 'Auftragsverarbeitungsvertrag (AVV) ', d.vorhanden ? h('span', { class: 'pill ok' }, 'liegt vor') : h('span', { class: 'pill warn' }, 'fehlt')),
    h('p', { class: 'small muted' }, 'Ablauf: Vertrag erstellen, per Mail an den Kunden senden, unterschrieben zurückbekommen und hier ablegen. Der Kunde sieht die abgelegte Fassung in seinem Portal.'), m,
    tabelle([['Erstellt', z => datum(z.erstellt_am)], ['Gesendet', z => z.gesendet_am ? datum(z.gesendet_am) : '–'], ['Unterschrieben am', z => z.unterschrieben_am ? datum(z.unterschrieben_am) : '–'],
      ['Datei', z => z.hat_datei ? z.datei_name : 'noch nicht abgelegt'], ['', aktion]], d.liste, 'Noch kein AVV erstellt.'),
    d.liste.filter(z => !z.hat_datei).length ? h('div', { style: 'margin-top:12px' }, h('p', { class: 'small muted' }, 'Unterschriebene Fassung zum neuesten Entwurf ablegen:'), hoch(d.liste.find(z => !z.hat_datei))) : '',
    h('p', { style: 'margin-top:12px' }, knopf('Neuen AVV erstellen', neu, 'btn')));
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

function offboardingKarte(kid, k) {
  const m = h('div'); const beendet = ['gekuendigt', 'beendet'].includes(k.status);
  if (k.geloescht_am) return h('div', { class: 'card' }, h('h2', {}, 'Vertragsende'), h('p', {}, 'Die Inhalte dieses Kunden wurden am ' + datum(k.geloescht_am) + ' gelöscht. Stammdaten und Belege bleiben wegen Aufbewahrungspflichten erhalten.'));
  const best = h('input', { placeholder: 'Kundennummer ' + k.kundennummer + ' zur Bestätigung', style: 'max-width:300px' });
  const haken = h('input', { type: 'checkbox', style: 'width:auto' });
  return h('div', { class: 'card' }, h('h2', {}, 'Vertragsende: Datenexport und Löschung'),
    h('p', { class: 'small muted' }, 'Zum Vertragsende bekommt der Kunde seine Daten (Pflicht laut AVV) und danach werden seine Inhalte gelöscht. Stammdaten, Rechnungen, Verträge, Buchungen und der AVV bleiben wegen Aufbewahrungspflichten erhalten, die Kontaktdaten der Ansprechperson werden entfernt. Sicherungen enthalten die Daten noch bis zu 14 Tage.'), m,
    h('p', {}, h('a', { class: 'btn', href: '/api/admin/kunden/' + kid + '/export.zip' }, 'Datenexport als ZIP herunterladen')),
    beendet ? h('div', { class: 'stack', style: 'margin-top:12px' },
      h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, haken, 'Der Datenexport wurde an den Kunden übergeben'), best,
      h('p', {}, knopf('Inhalte endgültig löschen', async () => { if (!confirm('Alle Inhalte dieses Kunden endgültig löschen? Das kann nicht rückgängig gemacht werden.')) return;
        try { await api('/api/admin/kunden/' + kid + '/loeschen', { method: 'POST', body: { bestaetigung: best.value, export_uebergeben: haken.checked } }); melde(m, 'Gelöscht.', 'ok'); setTimeout(() => location.reload(), 1200); } catch (x) { fehler(m, x); } }, 'bad')))
      : h('p', { class: 'small muted' }, 'Löschen ist erst möglich, wenn der Status des Kunden „gekündigt“ oder „beendet“ ist.'));
}

async function kostenKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/kosten'), m = h('div');
  const dienst = h('input', { placeholder: 'z. B. telefonie, domain, werbung', maxlength: 40 }), betrag = h('input', { type: 'number', step: '0.01', min: '0.01', placeholder: 'Betrag in €' }), tag = h('input', { type: 'date' });
  const speichern = knopf('Kosten eintragen', async () => { try { await api('/api/admin/kunden/' + kid + '/kosten', { method: 'POST', body: { dienst: dienst.value, betrag_eur: Number(betrag.value), datum: tag.value || null } }); location.reload(); } catch (x) { fehler(m, x); } }, 'btn');
  return h('div', { class: 'card' }, h('h2', {}, 'Kosten pro Monat'),
    h('p', { class: 'small muted' }, 'Monatlicher Umsatz laut aktiven Buchungen: ' + fmtEuro(d.umsatz_monat_cent) + '. KI-Kosten werden automatisch aus den Tokens berechnet, alle anderen Kosten (Telefonie, Domain, Werbung …) trägst du hier von Hand ein.'),
    tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Tokens', z => z.tokens], ['Kosten gesamt', z => fmtEuro(Math.round(z.kosten_cent))], ['Anteil am Umsatz', z => d.umsatz_monat_cent ? (z.kosten_cent / d.umsatz_monat_cent * 100).toFixed(1).replace('.', ',') + ' %' : '–']], d.monate, 'Noch keine Kosten erfasst.'),
    d.dienste.length ? h('div', {}, h('h3', {}, 'Aufgeteilt nach Kostenart'), tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Kostenart', z => z.dienst], ['Kosten', z => fmtEuro(Math.round(z.kosten_cent))]], d.dienste)) : '',
    h('h3', {}, 'Kosten von Hand eintragen'), m, h('div', { class: 'row' }, dienst, betrag, tag, speichern));
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

async function abgleichKarte() {
  const m = h('div'), erg = h('div'); let csvText = '';
  const datei = h('input', { type: 'file', accept: '.csv,.txt,text/csv', onchange: (e) => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => { csvText = String(r.result); }; r.readAsText(f, 'utf-8'); } });
  const zeige = (j, gebucht) => {
    erg.replaceChildren(
      h('p', {}, j.zeilen + ' Zeilen gelesen. ', gebucht ? h('b', {}, j.gebucht + ' Rechnung(en) als bezahlt gebucht.') : 'Das ist erst eine Vorschau, es wurde noch nichts gebucht.'),
      h('h3', {}, 'Passt genau (' + j.sicher.length + ')'), tabelle([['Rechnung', z => z.nummer], ['Kunde', z => z.firma], ['Betrag', z => fmtEuro(z.eingang_cent)], ['Datum', z => z.datum ? datum(z.datum) : '']], j.sicher, 'Keine eindeutigen Treffer.'),
      h('h3', {}, 'Bitte prüfen: Betrag weicht ab (' + j.abweichend.length + ')'), tabelle([['Rechnung', z => z.nummer], ['Kunde', z => z.firma], ['Rechnung', z => z.rechnung_cent == null ? '–' : fmtEuro(z.rechnung_cent)], ['Eingang', z => fmtEuro(z.eingang_cent)]], j.abweichend, 'Keine.'),
      h('p', { class: 'small muted' }, 'Diese werden nie automatisch gebucht – bitte in der Rechnung selbst als bezahlt eintragen, wenn es stimmt.'),
      h('h3', {}, 'Nicht zugeordnet (' + j.unbekannt.length + ')'), tabelle([['Datum', z => z.datum ? datum(z.datum) : ''], ['Betrag', z => fmtEuro(z.eingang_cent)], ['Verwendungszweck', z => z.text]], j.unbekannt, 'Keine.'));
    if (!gebucht && j.sicher.length) erg.append(h('p', {}, knopf(j.sicher.length + ' Treffer als bezahlt buchen', () => los(true), 'btn')));
  };
  const los = async (anwenden) => { if (!csvText) { fehler(m, new Error('Bitte zuerst die CSV-Datei auswählen.')); return; }
    try { const j = await api('/api/admin/belege/zahlungsabgleich', { method: 'POST', body: { csv: csvText, anwenden } }); m.replaceChildren(); zeige(j, anwenden); } catch (x) { fehler(m, x); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Zahlungseingänge abgleichen'),
    h('p', { class: 'small muted' }, 'Kontoauszug als CSV-Datei aus dem Online-Banking exportieren und hier auswählen. Gebucht wird nur, wenn Rechnungsnummer im Verwendungszweck steht und der Betrag genau stimmt. Zuerst siehst du eine Vorschau.'),
    m, h('div', { class: 'row' }, datei, knopf('Vorschau', () => los(false))), erg);
}

V.belege = async () => {
  const q = new URLSearchParams(location.hash.split('?')[1] || '');
  const art = q.get('art') || '', status = q.get('status') || '';
  const d = await api('/api/admin/belege?art=' + art + '&status=' + status), s = d.summen;
  const f = (a, st, l) => h('button', { class: (art === a && status === st) ? 'on' : '', onclick: () => { location.hash = '#belege?art=' + a + '&status=' + st; } }, l);
  return h('div', { class: 'stack' }, kopf('Angebote & Rechnungen'),
    h('p', { class: 'small' }, h('a', { href: '/api/admin/belege-export.csv', target: '_blank', rel: 'noopener' }, 'Rechnungen als CSV exportieren (Buchhaltung/sevDesk)')),
    await abgleichKarte(),
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
    d.checks && d.checks.length ? h('div', { class: 'card' }, h('h2', {}, 'Website-Check'), d.checks.map(c => h('details', { style: 'margin:6px 0' }, h('summary', {}, zeit(c.erstellt_am) + ' · ' + (c.website || 'ohne Website') + ' · ' + (c.score === null ? '–' : c.score + ' von 100')),
      h('div', { class: 'freitext' }, JSON.stringify(c.ergebnis, null, 2))))) : '',
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

// ------------------------------------------------------------- Nachrichten (Postfach)
const T_ART = { frage: 'Frage', auftrag: 'Auftrag', aenderung: 'Änderungswunsch', problem: 'Problem', modul: 'Zusatzmodul' };
const T_ST = ['offen', 'in_arbeit', 'wartet_auf_kunde', 'erledigt'];
const T_ST_TXT = { offen: 'offen', in_arbeit: 'in Arbeit', wartet_auf_kunde: 'wartet auf Kunde', erledigt: 'erledigt' };
const tPill = (st) => h('span', { class: 'pill ' + (st === 'erledigt' ? 'ok' : st === 'offen' ? 'warn' : '') }, T_ST_TXT[st] || st);
const dateiLink = (d) => h('a', { class: 'dateilink', href: '/api/admin/dateien/' + d.id, target: '_blank', rel: 'noopener' }, '📎 ' + d.name + ' (' + groesse(d.groesse) + ')');

V.postfach = async (param) => {
  if (param && param.startsWith('neu')) return ticketNeu(param.split('/')[1]);
  if (param) return ticketDetail(param);
  const f = new URLSearchParams((location.hash.split('?')[1] || '')), status = f.get('status') || 'offene';
  const liste = await api('/api/admin/tickets?status=' + status);
  const tab = (st, t) => h('a', { href: '#postfach?status=' + st, class: 'tab' + (status === st ? ' on' : '') }, t);
  return h('div', {}, kopf('Nachrichten'), h('div', { class: 'tabs' }, tab('offene', 'Offen'), tab('offen', 'Neu'), tab('in_arbeit', 'In Arbeit'), tab('wartet_auf_kunde', 'Wartet auf Kunde'), tab('erledigt', 'Erledigt'), tab('', 'Alle')),
    h('div', { class: 'card' }, tabelle([['Nr.', z => h('a', { href: '#postfach/' + z.id }, z.nr)], ['Kunde', z => h('a', { href: '#kunde/' + z.kunden_id }, z.firma)], ['Betreff', z => h('a', { href: '#postfach/' + z.id }, (z.team_ungelesen ? '● ' : '') + z.betreff)],
      ['Art', z => T_ART[z.art] || z.art], ['Prio', z => z.prioritaet === 'hoch' ? h('span', { class: 'pill bad' }, 'hoch') : ''], ['Status', z => tPill(z.status)], ['Fällig', z => z.faellig_am ? datum(z.faellig_am) : ''], ['Zuletzt', z => zeit(z.geaendert_am)]], liste, 'Keine Nachrichten in dieser Ansicht.')));
};

async function ticketDetail(id) {
  const t = await api('/api/admin/tickets/' + id), m = h('div');
  const bubbles = t.nachrichten.map(n => h('div', { class: 'bub ' + (n.intern ? 'intern' : n.von === 'kunde' ? 'kunde' : 'team') }, h('div', { class: 'small wer' }, (n.intern ? 'Interne Notiz · ' : '') + (n.autor_name || (n.von === 'kunde' ? 'Kunde' : 'Team')) + ' · ' + zeit(n.erstellt_am)), n.text));
  const text = h('textarea', { rows: 5, maxlength: 10000, placeholder: 'Antwort an den Kunden …' });
  const intern = h('input', { type: 'checkbox', style: 'width:auto' });
  const stSel = h('select', {}, h('option', { value: '' }, 'Status unverändert'), T_ST.map(x => h('option', { value: x }, T_ST_TXT[x])));
  const datei = h('input', { type: 'file' });
  const senden = async () => {
    try {
      if (text.value.trim()) await api('/api/admin/tickets/' + id + '/nachricht', { method: 'POST', body: { text: text.value, intern: intern.checked, status: stSel.value || null } });
      else if (stSel.value) await api('/api/admin/tickets/' + id, { method: 'PATCH', body: { status: stSel.value } });
      if (datei.files[0]) { const f = new FormData(); f.append('datei', datei.files[0]); await api('/api/admin/tickets/' + id + '/dateien', { method: 'POST', body: f }); }
      if (!text.value.trim() && !stSel.value && !datei.files[0]) { melde(m, 'Nichts zu senden.'); return; }
      zeige();
    } catch (x) { melde(m, x.message); }
  };
  const mp = h('div'), zu = h('input', { value: t.zustaendig || '', placeholder: 'Zuständig (E-Mail oder Name)' }), faellig = h('input', { type: 'date', value: t.faellig_am ? String(t.faellig_am).slice(0, 10) : '' });
  const prio = h('select', {}, ['normal', 'hoch'].map(x => h('option', { value: x, selected: x === t.prioritaet }, x)));
  const speichern = async () => { try { const b = { prioritaet: prio.value, zustaendig: zu.value || null }; if (faellig.value) b.faellig_am = faellig.value; else b.faellig_loeschen = true; await api('/api/admin/tickets/' + id, { method: 'PATCH', body: b }); melde(mp, 'Gespeichert.', 'ok'); } catch (x) { melde(mp, x.message); } };
  const aufg = async () => { const titel = prompt('Aufgabe zu dieser Nachricht (Titel):', t.betreff); if (!titel) return; try { await api('/api/admin/aufgaben', { method: 'POST', body: { titel, kunden_id: t.kunden_id, ticket_id: t.id, zustaendig: zu.value || null, faellig_am: faellig.value || null } }); melde(mp, 'Aufgabe angelegt.', 'ok'); } catch (x) { melde(mp, x.message); } };
  return h('div', { class: 'stack' }, kopf(t.nr + ' · ' + t.betreff, h('a', { class: 'btn sec small', href: '#postfach' }, '← Alle Nachrichten')),
    h('div', { class: 'card' }, h('p', { class: 'small muted' }, h('a', { href: '#kunde/' + t.kunden_id }, t.firma + ' (' + t.kundennummer + ')'), ' · ' + (T_ART[t.art] || t.art) + ' · von ' + (t.ersteller_name || '–') + ' · eröffnet ' + zeit(t.erstellt_am) + (t.erste_antwort_am ? ' · erste Antwort ' + zeit(t.erste_antwort_am) : ' · noch nicht beantwortet')),
      tPill(t.status), h('div', { class: 'chatlog thread' }, bubbles), t.dateien.length ? h('div', { class: 'small' }, t.dateien.map(dateiLink)) : '',
      t.bewertung ? h('p', { class: 'small' }, 'Bewertung: ' + t.bewertung.punkte + ' / 10' + (t.bewertung.kommentar ? ' · „' + t.bewertung.kommentar + '“' : '')) : ''),
    h('div', { class: 'card' }, h('h3', {}, 'Antworten'), m, text, h('div', { class: 'row', style: 'margin-top:10px' }, h('label', { style: 'display:flex;gap:6px;align-items:center;margin:0;color:inherit' }, intern, 'Nur intern (Kunde sieht es nicht)'), stSel, datei, h('span', { class: 'grow' }), h('button', { class: 'btn', onclick: senden }, 'Senden'))),
    h('div', { class: 'card' }, h('h3', {}, 'Bearbeitung'), mp, h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Zuständig'), zu), h('div', {}, h('label', {}, 'Fällig am'), faellig), h('div', {}, h('label', {}, 'Priorität'), prio)),
      h('div', { class: 'row', style: 'margin-top:10px' }, h('button', { class: 'btn', onclick: speichern }, 'Speichern'), h('button', { class: 'btn sec', onclick: aufg }, 'Aufgabe daraus machen'))));
}

async function ticketNeu(kid) {
  const m = h('div'), betreff = h('input', { required: true, maxlength: 200 }), text = h('textarea', { rows: 5, maxlength: 10000 });
  const art = h('select', {}, ['auftrag', 'frage', 'aenderung', 'problem'].map(x => h('option', { value: x }, T_ART[x])));
  return h('div', { class: 'stack' }, kopf('Nachricht an Kunden', h('a', { class: 'btn sec small', href: '#kunde/' + kid }, '← Zurück')),
    h('div', { class: 'card' }, m, h('label', {}, 'Betreff'), betreff, h('label', {}, 'Art'), art, h('label', {}, 'Nachricht an den Kunden'), text,
      h('p', {}, h('button', { class: 'btn', onclick: async () => { try { const r = await api('/api/admin/kunden/' + kid + '/tickets', { method: 'POST', body: { betreff: betreff.value, art: art.value, text: text.value } }); location.hash = '#postfach/' + r.id; } catch (x) { melde(m, x.message); } } }, 'Senden'))));
}

// ------------------------------------------------------------- Freigaben
const F_ART = { social: 'Social Media', text: 'Text', angebot: 'Angebot', design: 'Design', website: 'Website', sonstiges: 'Sonstiges' };
const fPill = (st) => h('span', { class: 'pill ' + (st === 'freigegeben' ? 'ok' : st === 'abgelehnt' ? 'bad' : st === 'wartet' ? 'warn' : '') }, st === 'abgelehnt' ? 'Änderung gewünscht' : st === 'wartet' ? 'wartet' : st);

async function freigabeNeuKarte(kid) {
  const m = h('div'), titel = h('input', { maxlength: 200, placeholder: 'z. B. Instagram-Beitrag Wochenangebote KW 43' }), inhalt = h('textarea', { rows: 4, maxlength: 20000, placeholder: 'Text bzw. Beschreibung, den der Kunde prüfen soll' });
  const art = h('select', {}, Object.entries(F_ART).map(([v, t]) => h('option', { value: v }, t))), datei = h('input', { type: 'file' });
  return h('div', { class: 'card' }, h('h2', {}, 'Neue Freigabe-Bitte'), h('p', { class: 'small muted' }, 'Der Kunde bekommt eine E-Mail und entscheidet im Portal. Datum, Uhrzeit, Name und IP werden festgehalten.'), m,
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Titel'), titel), h('div', {}, h('label', {}, 'Art'), art)), h('label', {}, 'Inhalt'), inhalt,
    h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, h('label', { style: 'margin:0 0 4px' }, 'Datei anhängen (Bild, PDF, optional)'), datei),
      h('button', { class: 'btn', onclick: async () => { try { const r = await api('/api/admin/kunden/' + kid + '/freigaben-kunden', { method: 'POST', body: { titel: titel.value, art: art.value, inhalt: inhalt.value || null } });
        if (datei.files[0]) { const f = new FormData(); f.append('datei', datei.files[0]); await api('/api/admin/freigaben-kunden/' + r.id + '/dateien', { method: 'POST', body: f }); }
        zeige(); } catch (x) { melde(m, x.message); } } }, 'Anfragen')));
}

V.freigaben = async () => {
  const f = new URLSearchParams((location.hash.split('?')[1] || '')), status = f.get('status') || '';
  const liste = await api('/api/admin/freigaben-kunden?status=' + status), m = h('div');
  const tab = (st, t) => h('a', { href: '#freigaben' + (st ? '?status=' + st : ''), class: 'tab' + (status === st ? ' on' : '') }, t);
  const zurueck = async (z) => { if (!confirm('Diese Bitte zurückziehen?')) return; try { await api('/api/admin/freigaben-kunden/' + z.id + '/zurueckziehen', { method: 'POST', body: {} }); zeige(); } catch (x) { melde(m, x.message); } };
  return h('div', {}, kopf('Freigaben'), m, h('p', { class: 'small muted' }, 'Neue Freigabe-Bitten legst du beim jeweiligen Kunden an (Kunden → Kunde öffnen → Freigaben).'),
    h('div', { class: 'tabs' }, tab('', 'Alle'), tab('wartet', 'Wartet'), tab('freigegeben', 'Freigegeben'), tab('abgelehnt', 'Änderung gewünscht')),
    h('div', { class: 'card' }, tabelle([['Kunde', z => h('a', { href: '#kunde/' + z.kunden_id }, z.firma)], ['Titel', z => z.titel + ' (' + (F_ART[z.art] || z.art) + ')'], ['Status', z => fPill(z.status)], ['Angefragt', z => zeit(z.angefragt_am)],
      ['Entscheidung', z => z.entschieden_am ? zeit(z.entschieden_am) + ' · ' + (z.entschieden_name || '') + (z.entschieden_ip ? ' · IP ' + z.entschieden_ip : '') + (z.kommentar ? ' · „' + z.kommentar + '“' : '') : ''],
      ['', z => z.status === 'wartet' ? h('button', { class: 'btn sec small', onclick: () => zurueck(z) }, 'Zurückziehen') : '']], liste, 'Keine Freigaben.')));
};

async function freigabenKundeKarte(kid, k) {
  const alle = await api('/api/admin/freigaben-kunden'), liste = alle.filter(z => z.kunden_id === kid);
  return h('div', { class: 'stack' }, await freigabeNeuKarte(kid), liste.length ? h('div', { class: 'card' }, h('h3', {}, 'Bisherige Freigaben'), tabelle([['Titel', z => z.titel], ['Status', z => fPill(z.status)], ['Angefragt', z => zeit(z.angefragt_am)], ['Entscheidung', z => z.entschieden_am ? zeit(z.entschieden_am) + ' · ' + (z.entschieden_name || '') + (z.kommentar ? ' · „' + z.kommentar + '“' : '') : '']], liste)) : '');
}

// ------------------------------------------------------------- Dokumente pro Kunde
async function unterlagenKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/unterlagen'), m = h('div');
  const kat = h('select', {}, Object.entries(d.kategorien).map(([v, t]) => h('option', { value: v }, t))), datei = h('input', { type: 'file' });
  const sicht = h('input', { type: 'checkbox', checked: true, style: 'width:auto' });
  const hoch = async () => { if (!datei.files[0]) { melde(m, 'Bitte Datei wählen.'); return; } const f = new FormData(); f.append('datei', datei.files[0]); f.append('kategorie', kat.value); f.append('sichtbar_kunde', sicht.checked ? 'true' : 'false');
    try { await api('/api/admin/kunden/' + kid + '/unterlagen', { method: 'POST', body: f }); zeige(); } catch (x) { melde(m, x.message); } };
  const weg = async (z) => { if (!confirm('Datei "' + z.name + '" löschen?')) return; try { await api('/api/admin/unterlagen/' + z.id, { method: 'DELETE' }); zeige(); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Dokumente'), m,
    tabelle([['Datei', z => h('a', { href: '/api/admin/dateien/' + z.id, target: '_blank', rel: 'noopener' }, z.name)], ['Art', z => d.kategorien[z.kategorie] || '–'], ['Größe', z => groesse(z.groesse)], ['Von', z => z.von === 'team' ? 'Team' : 'Kunde'], ['Kunde sieht es', z => z.sichtbar_kunde ? 'ja' : 'nein'], ['Datum', z => zeit(z.erstellt_am)], ['', z => h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen')]], d.dateien, 'Noch keine Dokumente.'),
    h('div', { class: 'row', style: 'margin-top:12px' }, kat, datei, h('label', { style: 'display:flex;gap:6px;align-items:center;margin:0;color:inherit' }, sicht, 'für Kunden sichtbar'), h('button', { class: 'btn', onclick: hoch }, 'Hochladen')));
}

async function nachrichtenKundeKarte(kid, k) {
  const liste = await api('/api/admin/tickets?kunde=' + encodeURIComponent(k.kundennummer));
  return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { style: 'margin:0' }, 'Nachrichten'), h('span', { class: 'grow' }), h('a', { class: 'btn small', href: '#postfach/neu/' + kid }, 'Neue Nachricht / Auftrag')),
    tabelle([['Nr.', z => h('a', { href: '#postfach/' + z.id }, z.nr)], ['Betreff', z => (z.team_ungelesen ? '● ' : '') + z.betreff], ['Status', z => tPill(z.status)], ['Zuletzt', z => zeit(z.geaendert_am)]], liste, 'Noch keine Nachrichten.'));
}

// ------------------------------------------------------------- Aufgaben
V.aufgaben = async () => {
  const f = new URLSearchParams((location.hash.split('?')[1] || '')), status = f.get('status') || 'offen';
  const liste = await api('/api/admin/aufgaben?status=' + status), m = h('div');
  const tab = (st, t) => h('a', { href: '#aufgaben?status=' + st, class: 'tab' + (status === st ? ' on' : '') }, t);
  const titel = h('input', { maxlength: 200, placeholder: 'Neue Aufgabe …' }), zu = h('input', { placeholder: 'Zuständig (leer = ich)' }), fa = h('input', { type: 'date' });
  const neu = async () => { try { await api('/api/admin/aufgaben', { method: 'POST', body: { titel: titel.value, zustaendig: zu.value || null, faellig_am: fa.value || null } }); zeige(); } catch (x) { melde(m, x.message); } };
  const setz = async (z, st) => { try { await api('/api/admin/aufgaben/' + z.id, { method: 'PATCH', body: { status: st } }); zeige(); } catch (x) { melde(m, x.message); } };
  const weg = async (z) => { if (!confirm('Aufgabe löschen?')) return; try { await api('/api/admin/aufgaben/' + z.id, { method: 'DELETE' }); zeige(); } catch (x) { melde(m, x.message); } };
  return h('div', {}, kopf('Aufgaben'), m,
    h('div', { class: 'card' }, h('div', { class: 'row' }, h('div', { class: 'grow' }, titel), zu, fa, h('button', { class: 'btn', onclick: neu }, 'Anlegen'))),
    h('div', { class: 'tabs' }, tab('offen', 'Offen'), tab('erledigt', 'Erledigt'), tab('alle', 'Alle')),
    h('div', { class: 'card' }, h('p', { class: 'small muted' }, 'Aufgaben mit „auto“ legt das System selbst an, z. B. bei unbeantworteten Nachrichten, wartenden Freigaben oder überfälligen Rechnungen.'),
      tabelle([['Aufgabe', z => (z.ueberfaellig ? '⚠ ' : '') + z.titel + (z.quelle === 'auto' ? ' (auto)' : '')], ['Kunde', z => z.kunden_id ? h('a', { href: '#kunde/' + z.kunden_id }, z.firma) : ''], ['Zuständig', z => z.zustaendig || ''], ['Fällig', z => z.faellig_am ? datum(z.faellig_am) : ''],
        ['', z => h('div', { class: 'row' }, z.ticket_id ? h('a', { class: 'btn sec small', href: '#postfach/' + z.ticket_id }, 'Nachricht') : '', z.status === 'offen' ? h('button', { class: 'btn small', onclick: () => setz(z, 'erledigt') }, 'Erledigt') : h('button', { class: 'btn sec small', onclick: () => setz(z, 'offen') }, 'Wieder öffnen'), z.quelle === 'manuell' ? h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen') : '')]], liste, 'Keine Aufgaben.')));
};

// ------------------------------------------------------------- Kennzahlen
V.kennzahlen = async () => {
  const z = await api('/api/admin/kennzahlen'), st = (t, w, link) => h(link ? 'a' : 'div', { class: 'card stat', href: link, style: link ? 'text-decoration:none;color:inherit' : '' }, h('span', { class: 'muted small' }, t), h('b', {}, w));
  const hh = (v) => v === null || v === undefined ? '–' : String(v).replace('.', ',') + ' h';
  return h('div', { class: 'stack' }, kopf('Kennzahlen'),
    h('div', { class: 'grid3' }, st('Nachrichten offen', z.tickets_offen, '#postfach'), st('davon ungelesen', z.tickets_ungelesen, '#postfach'), st('überfällig', z.tickets_ueberfaellig, '#postfach'),
      st('Freigaben warten', z.freigaben_wartend, '#freigaben'), st('Aufgaben offen', z.aufgaben_offen, '#aufgaben'), st('Aufgaben überfällig', z.aufgaben_ueberfaellig, '#aufgaben')),
    h('div', { class: 'card' }, h('h2', {}, 'Reaktionsgeschwindigkeit (90 Tage)'), h('div', { class: 'grid3' }, st('Erste Antwort im Schnitt', hh(z.antwortzeit_h)), st('Bis erledigt im Schnitt', hh(z.erledigungszeit_h)), st('Freigabe-Dauer im Schnitt', hh(z.freigabedauer_h)))),
    h('div', { class: 'card' }, h('h2', {}, 'Zufriedenheit (90 Tage)'), h('div', { class: 'grid3' }, st('Bewertungen', z.bewertungen), st('Durchschnitt (0–10)', z.bewertung_durchschnitt === null ? '–' : String(z.bewertung_durchschnitt).replace('.', ',')), st('NPS', z.nps === null ? '–' : z.nps)),
      h('p', { class: 'small muted' }, 'NPS = Anteil Promoter (9–10) minus Anteil Kritiker (0–6), in Prozentpunkten. Über 0 ist gut, über 50 sehr gut.')),
    h('div', { class: 'card' }, h('h2', {}, 'Pro Kunde'), tabelle([['Kunde', c => h('a', { href: '#kunde/' + c.id }, c.firma)], ['Status', c => pill(c.status)], ['Nachrichten offen', c => c.tickets_offen], ['Freigaben wartend', c => c.freigaben_wartend], ['Bewertung (180 T.)', c => c.bewertung === null ? '–' : String(c.bewertung).replace('.', ',')], ['Letzte Aktivität', c => c.letzte_aktivitaet ? zeit(c.letzte_aktivitaet) : '–']], z.kunden)),
    z.kommentare.length ? h('div', { class: 'card' }, h('h2', {}, 'Kommentare von Kunden'), tabelle([['Kunde', c => c.firma], ['Punkte', c => c.punkte], ['Kommentar', c => c.kommentar], ['Datum', c => zeit(c.erstellt_am)]], z.kommentare)) : '');
};

// ------------------------------------------------------------- Briefing und externe Zahlen (Kunde öffnen)
async function briefingKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/briefing');
  const inhalt = d.struktur.map(a => [h('h3', {}, a.abschnitt), a.felder.map(f => h('div', { style: 'margin:6px 0' }, h('div', { class: 'small muted' }, f.frage), h('div', { class: 'freitext' }, d.daten[f.key] || '–')))]);
  return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { style: 'margin:0' }, 'Briefing'), d.status === 'abgeschickt' ? h('span', { class: 'pill ok' }, 'abgeschickt ' + zeit(d.abgeschickt_am)) : h('span', { class: 'pill warn' }, Object.keys(d.daten).length ? 'in Arbeit' : 'noch leer')),
    Object.keys(d.daten).length ? h('details', {}, h('summary', {}, 'Antworten anzeigen'), inhalt) : h('p', { class: 'small muted' }, 'Der Kunde hat das Briefing noch nicht ausgefüllt. Es erscheint in seinem Portal unter „Briefing“.'));
}

async function externKarte(kid) {
  const liste = await api('/api/admin/kunden/' + kid + '/kennzahlen-extern'), m = h('div');
  const jetzt = new Date(), monat = h('input', { type: 'month', value: jetzt.getFullYear() + '-' + String(jetzt.getMonth() + 1).padStart(2, '0') });
  const zahl = (ph, step = '1') => h('input', { type: 'number', min: '0', step, placeholder: ph });
  const bes = zahl('Website-Besucher'), auf = zahl('Google-Aufrufe'), anz = zahl('Google-Bewertungen (Anzahl)'), ste = h('input', { type: 'number', min: '1', max: '5', step: '0.1', placeholder: 'Google-Sterne (1 bis 5)' });
  const n = (el) => el.value === '' ? null : Number(el.value);
  return h('div', { class: 'card' }, h('h2', {}, 'Zahlen für die Auswertung (Besucher, Google)'), h('p', { class: 'small muted' }, 'Trage monatlich ein, was du aus Statistik und Google-Profil ablesen kannst. Der Kunde sieht es in seiner Auswertung. Gleicher Monat nochmal speichern überschreibt.'), m,
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Monat'), monat), h('div', {}, h('label', {}, 'Besucher'), bes), h('div', {}, h('label', {}, 'Google-Aufrufe'), auf), h('div', {}, h('label', {}, 'Bewertungen'), anz), h('div', {}, h('label', {}, 'Sterne'), ste)),
    h('p', {}, h('button', { class: 'btn', onclick: async () => { try { await api('/api/admin/kunden/' + kid + '/kennzahlen-extern', { method: 'PUT', body: { monat: monat.value, besucher: n(bes), google_aufrufe: n(auf), google_bewertungen: n(anz), google_sterne: n(ste) } }); zeige(); } catch (x) { melde(m, x.message); } } }, 'Speichern')),
    tabelle([['Monat', z => z.monat], ['Besucher', z => z.besucher ?? '–'], ['Google-Aufrufe', z => z.google_aufrufe ?? '–'], ['Bewertungen', z => z.google_bewertungen ?? '–'], ['Sterne', z => z.google_sterne ?? '–']], liste, 'Noch keine Zahlen.'));
}

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
  const SPR = { de: 'Deutsch', tr: 'Türkisch', en: 'Englisch', ar: 'Arabisch' };
  const sprachWahl = (z) => { const boxen = Object.entries(SPR).map(([c, n]) => { const i = h('input', { type: 'checkbox', checked: (z.sprachen || ['de']).includes(c), disabled: c === 'de', style: 'width:auto', 'data-c': c }); return h('label', { style: 'display:inline-flex;gap:4px;align-items:center;margin-right:10px;color:inherit' }, i, n); });
    return h('div', { class: 'row' }, boxen, h('button', { class: 'btn sec small', onclick: async (e) => { const liste = ['de'].concat(boxen.map(b => b.firstChild).filter(i => i.checked && i.dataset.c !== 'de').map(i => i.dataset.c)); try { await api('/api/admin/websites/' + z.id + '/sprachen', { method: 'PUT', body: { sprachen: liste } }); e.target.textContent = 'Gespeichert'; } catch (x) { melde(mw, x.message); } } }, 'Speichern')); };
  const webs = tabelle([['Domain', z => z.domain], ['Art', z => z.art], ['Status', z => pill(z.status)], ['Sprachen der Angebotsseite', sprachWahl], ['Zuletzt', z => zeit(z.letzte_veroeffentlichung)]], d.websites, 'Keine Website.');

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
    await avvKarte(kid),
    h('div', { class: 'card' }, h('h2', {}, 'Vertriebler'), mv, h('div', { class: 'row' }, h('div', { class: 'grow' }, h('select', { id: 'vsel' }, h('option', { value: '' }, '– kein Vertriebler –'), partnerListe.map(p => h('option', { value: p.id, selected: p.id === k.vertriebspartner_id }, p.name + (p.status !== 'aktiv' ? ' (' + p.status + ')' : ''))))),
      knopf('Zuordnen', async () => { try { await api('/api/admin/kunden/' + kid + '/partner', { method: 'PUT', body: { partner_id: document.getElementById('vsel').value || null } }); melde(mv, 'Gespeichert.', 'ok'); } catch (x) { melde(mv, x.message); } }))),
    h('div', { class: 'card' }, h('h2', {}, 'Module des Kunden (Schalter)'), h('p', { class: 'small muted' }, 'Was hier aktiv ist, sieht der Kunde in seinem Portal.'), mz, module),
    h('div', { class: 'card' }, h('h2', {}, 'Portal-Zugang'), zugaenge, h('div', { class: 'row', style: 'margin-top:12px' }, h('div', { class: 'grow' }, mail), einladen), linkbox),
    h('div', { class: 'card' }, h('h2', {}, 'Buchungen'), mb, buchungen, h('h3', { style: 'margin-top:18px' }, 'Neue Buchung'), bform),
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), mw, webs, h('div', { style: 'height:10px' }), wform,
      h('p', { class: 'small muted' }, 'Danach auf dem Server einmal: mkctl site-add <domain>, damit Ordner und Webserver bereit sind.')),
    await belegeKarte(kid, k.referenzkunde),
    await briefingKarte(kid),
    await nachrichtenKundeKarte(kid, k),
    await freigabenKundeKarte(kid, k),
    await unterlagenKarte(kid),
    await berichteKarte(kid),
    await externKarte(kid),
    await kostenKarte(kid),
    brandingKarte(kid, k),
    offboardingKarte(kid, k),
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
    else if (V[seite]) inhalt = await V[seite](hash.split('?')[0].split('/').slice(1).join('/') || undefined);
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
    try { const z = (await api('/api/admin/uebersicht')).zusammenarbeit; zaehlerAdmin.postfach = z.tickets_ungelesen; zaehlerAdmin.freigaben = z.freigaben_wartend; zaehlerAdmin.aufgaben = z.aufgaben_ueberfaellig; } catch (e) { /* Zähler sind optional */ }
  } catch (e) { return; }
  window.addEventListener('hashchange', zeige);
  zeige();
})();
