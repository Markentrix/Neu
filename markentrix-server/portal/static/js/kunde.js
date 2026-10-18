import { h, api, datum, zeit, euro, groesse, melde, abmelden, sparkline, zweiFaktorKarte, rechtFuss } from './common.js';

const root = document.getElementById('app');
let start = null;
const hat = (c) => start.module.some(m => m.code === c);

const SEITEN = [
  ['uebersicht', 'Übersicht', null],
  ['assistent', 'KI-Assistent', 'ki_chat'],
  ['anfragen', 'Anfragen', 'anfragen_termine'],
  ['termine', 'Termine', 'anfragen_termine'],
  ['kontakte', 'Kontakte', 'kontakte_angebote_vertraege'],
  ['dokumente', 'Angebote & Verträge', 'kontakte_angebote_vertraege'],
  ['berichte', 'Monatsberichte', null],
  ['belege', 'Angebote & Rechnungen', null],
  ['website', 'Website & Landingpages', 'website'],
  ['wochenangebote', 'Wochenangebote', 'wochenangebote'],
  ['werbung', 'Werbung & Berichte', 'werbung_berichte'],
  ['automationen', 'Automationen', 'automationen'],
  ['avv', 'Datenschutz-Vertrag', null],
  ['team', 'Team', null],
  ['einstellungen', 'Einstellungen', null],
];
const inhaber = () => start.kunden_rolle === 'inhaber';
const sichtbar = () => SEITEN.filter(s => (!s[2] || hat(s[2])) && (!['belege', 'team', 'avv'].includes(s[0]) || inhaber()));

function gerüst(aktiv, inhalt) {
  const k = start.kunde;
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, k.logo_vorhanden ? h('img', { class: 'kundenlogo', src: '/api/kunde/logo', alt: '' }) : h('div', { class: 'logo' }, 'M'), k.logo_vorhanden ? k.firma : 'Markentrix'),
      sichtbar().map(s => h('a', { class: 'nav' + (s[0] === aktiv ? ' on' : ''), href: '#' + s[0] }, s[1])),
      h('div', { class: 'grow' }),
      h('a', { class: 'nav', href: '#', onclick: (e) => { e.preventDefault(); abmelden(); } }, 'Abmelden')),
    h('main', { class: 'main' },
      h('div', { class: 'top' },
        h('h1', {}, k.firma),
        h('span', { class: 'pill' }, 'Kundennr. ' + k.kundennummer),
        h('span', { class: 'pill ok' }, '● Online')),
      inhalt, rechtFuss()));
}

function karten() {
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

function tabelle(spalten, zeilen, leer = 'Noch nichts vorhanden.') {
  if (!zeilen.length) return h('p', { class: 'muted' }, leer);
  return h('div', { class: 'tablewrap' }, h('table', {},
    h('thead', {}, h('tr', {}, spalten.map(s => h('th', {}, s[0])))),
    h('tbody', {}, zeilen.map(z => h('tr', {}, spalten.map(s => h('td', {}, s[1](z))))))));
}
const statusPill = (s) => h('span', { class: 'pill ' + (['neu', 'geplant'].includes(s) ? 'warn' : ['erledigt', 'veroeffentlicht', 'bestaetigt', 'beantwortet'].includes(s) ? 'ok' : ['fehler', 'abgesagt', 'spam'].includes(s) ? 'bad' : '') }, String(s).replace('_', ' '));

// ------------------------------------------------------------- Seiten
const V = {};

V.uebersicht = async () => h('div', { class: 'grid3' }, karten());

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
    const d = Object.fromEntries(new FormData(e.target));
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
    const d = Object.fromEntries(new FormData(e.target)); Object.keys(d).forEach(k => { if (d[k] === '') delete d[k]; });
    try { await api('/api/kunde/kontakte', { method: 'POST', body: d }); location.reload(); } catch (x) { melde(m, x.message); }
  } },
    ['name:Name', 'firma:Firma', 'email:E-Mail', 'telefon:Telefon', 'notiz:Notiz'].map(s => { const [n, l] = s.split(':'); return h('div', {}, h('label', {}, l), h('input', { name: n, required: n === 'name' })); }),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Kontakt speichern')));
  const loesch = (z) => h('button', { class: 'btn small bad', onclick: async () => { if (!confirm('Kontakt löschen?')) return; try { await api('/api/kunde/kontakte/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { alert(x.message); } } }, 'Löschen');
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Kontakte'), tabelle([['Name', z => z.name], ['Firma', z => z.firma], ['E-Mail', z => z.email], ['Telefon', z => z.telefon], ['Notiz', z => z.notiz], ['', loesch]], daten, 'Noch keine Kontakte.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Kontakt'), m, f));
};

V.dokumente = async () => {
  const d = await api('/api/kunde/dokumente');
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Angebote'), tabelle([['Nummer', z => z.nummer], ['Titel', z => z.titel], ['Betrag', z => euro(z.betrag_cent)], ['Gültig bis', z => datum(z.gueltig_bis)], ['Status', z => statusPill(z.status)]], d.angebote, 'Keine Angebote.')),
    h('div', { class: 'card' }, h('h2', {}, 'Verträge'), tabelle([['Titel', z => z.titel], ['Beginn', z => datum(z.beginn)], ['Ende', z => datum(z.ende)], ['Status', z => statusPill(z.status)]], d.vertraege, 'Keine Verträge.')));
};

V.website = async () => {
  const d = await api('/api/kunde/website');
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), tabelle([['Domain', z => h('a', { href: 'https://' + z.domain, target: '_blank', rel: 'noopener' }, z.domain)], ['Art', z => z.art], ['Status', z => statusPill(z.status)], ['Zuletzt aktualisiert', z => zeit(z.letzte_veroeffentlichung)]], d.websites, 'Noch keine Website.')),
    h('div', { class: 'card' }, h('h2', {}, 'Projekte'), tabelle([['Titel', z => z.titel], ['Art', z => z.art], ['Status', z => statusPill(z.status)], ['Link', z => z.url && h('a', { href: z.url, target: '_blank', rel: 'noopener' }, 'Öffnen')]], d.projekte, 'Keine Projekte.')));
};

V.wochenangebote = async () => {
  const d = await api('/api/kunde/wochenangebote');
  const m = h('div'), dat = h('input', { type: 'file', name: 'datei', accept: '.pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png', required: true });
  const knopf = h('button', { class: 'btn' }, 'Hochladen und veröffentlichen');
  const f = h('form', { onsubmit: async (e) => {
    e.preventDefault(); knopf.disabled = true; melde(m, '');
    try {
      const r = await api('/api/kunde/wochenangebote', { method: 'POST', body: new FormData(e.target) });
      if (r.status === 'veroeffentlicht') melde(m, 'Veröffentlicht: ' + r.adresse, 'ok'); else melde(m, r.hinweis || 'Gespeichert.', r.status === 'fehler' ? 'err' : 'info');
      setTimeout(() => location.reload(), 2500);
    } catch (x) { melde(m, x.message); knopf.disabled = false; }
  } },
    h('div', { class: 'drop' }, h('p', {}, 'PDF, JPG oder PNG – bis 10 MB'), dat),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Gültig von (optional)'), h('input', { type: 'date', name: 'gueltig_von' })), h('div', {}, h('label', {}, 'Gültig bis (optional)'), h('input', { type: 'date', name: 'gueltig_bis' }))),
    h('p', {}, knopf));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Wochenangebote hochladen'),
      h('p', { class: 'muted small' }, d.website ? 'Die Datei erscheint sofort auf ' + d.website + '/angebote/. Das alte Angebot wandert ins Archiv.' : 'Noch keine Website verknüpft – Dateien werden gespeichert und vom Team veröffentlicht.'), m, f),
    h('div', { class: 'card' }, h('h2', {}, 'Bisherige Uploads'), tabelle([['Datum', z => zeit(z.erstellt_am)], ['Datei', z => z.dateiname], ['Größe', z => groesse(z.groesse)], ['Gültig', z => [datum(z.gueltig_von), z.gueltig_bis ? ' – ' + datum(z.gueltig_bis) : ''].join('')], ['Status', z => [statusPill(z.status), z.fehlertext && h('div', { class: 'small muted' }, z.fehlertext)]]], d.uploads, 'Noch keine Uploads.')));
};

V.werbung = async () => {
  const d = await api('/api/kunde/berichte');
  return h('div', { class: 'card' }, h('h2', {}, 'Werbung & Berichte'), tabelle([['Zeitraum', z => [datum(z.zeitraum_von), ' – ', datum(z.zeitraum_bis)].join('')], ['Titel', z => z.titel], ['Art', z => z.art], ['Erstellt', z => datum(z.erstellt_am)]], d, 'Noch keine Berichte.'));
};

V.belege = async () => {
  const d = await api('/api/kunde/belege'), m = h('div');
  const art = (z) => z.storno_von ? 'Storno' : z.art === 'rechnung' ? 'Rechnung' : 'Angebot';
  const st = (z) => h('span', { class: 'pill ' + (z.ueberfaellig ? 'bad' : ['bezahlt', 'angenommen'].includes(z.status) ? 'ok' : ['abgelehnt', 'storniert'].includes(z.status) ? 'bad' : 'warn') }, z.ueberfaellig ? 'überfällig' : z.status === 'gestellt' || z.status === 'versendet' ? (z.art === 'rechnung' ? 'offen' : 'wartet auf Annahme') : z.status);
  const aktion = (z) => h('span', { class: 'row' }, h('a', { class: 'btn sec small', href: '/api/kunde/belege/' + z.id + '/pdf' }, 'PDF'),
    z.art === 'angebot' && ['gestellt', 'versendet'].includes(z.status) ? h('button', { class: 'btn small', onclick: async () => { if (!confirm('Angebot ' + z.nummer + ' verbindlich annehmen?')) return; try { await api('/api/kunde/belege/' + z.id + '/annehmen', { method: 'POST' }); melde(m, 'Danke! Das Angebot ist angenommen.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { melde(m, x.message); } } }, 'Annehmen') : '');
  return h('div', { class: 'card' }, h('h2', {}, 'Angebote & Rechnungen'), m, tabelle([['Nummer', z => z.nummer], ['Art', art], ['Betreff', z => z.betreff], ['Datum', z => datum(z.datum)], ['Fällig/gültig bis', z => datum(z.faellig_am)], ['Betrag', z => euro(z.brutto_cent)], ['Status', st], ['', aktion]], d, 'Noch keine Angebote oder Rechnungen.'));
};

V.berichte = async () => {
  const d = await api('/api/kunde/monatsberichte');
  if (!d.length) return h('div', { class: 'card' }, h('h2', {}, 'Monatsberichte'), h('p', { class: 'muted' }, 'Hier erscheint jeden Monat dein Bericht: Anfragen, Termine und was deine Automatisierungen für dich erledigt haben. Der erste kommt am Anfang des nächsten Monats.'));
  return h('div', { class: 'stack' }, d.map(b => {
    const x = b.daten, a = x.anfragen;
    return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { class: 'grow', style: 'margin:0' }, b.titel), h('a', { class: 'btn small', href: '/api/kunde/monatsberichte/' + b.id + '/pdf' }, 'PDF herunterladen')),
      h('div', { class: 'grid3', style: 'margin-top:12px' },
        h('div', { class: 'stat' }, h('b', {}, a.gesamt), h('span', { class: 'muted small' }, 'Anfragen (Vormonat ' + a.vormonat + ')')),
        h('div', { class: 'stat' }, h('b', {}, x.termine.gesamt), h('span', { class: 'muted small' }, 'Termine')),
        h('div', { class: 'stat' }, h('b', {}, x.automatische_ablaeufe), h('span', { class: 'muted small' }, 'Automatische Abläufe'))));
  }));
};

V.automationen = async () => {
  const d = await api('/api/kunde/automationen');
  return h('div', { class: 'card' }, h('h2', {}, 'Automationen'),
    d.map(a => h('div', { class: 'modul' }, h('div', { class: 'grow' }, h('b', {}, a.name), h('div', { class: 'small muted' }, a.beschreibung)), h('span', { class: 'pill ' + (a.aktiv ? 'ok' : '') }, a.aktiv ? 'aktiv' : 'nicht gebucht'))),
    h('p', { class: 'muted small' }, 'Weitere Automationen buchst du über dein Markentrix-Team.'));
};

V.einstellungen = async () => {
  const p = await api('/api/kunde/profil');
  const m1 = h('div'), m2 = h('div'), m3 = h('div');
  const k = p.kunde; const sw = { benachr_anfragen: k.benachr_anfragen, benachr_termine: k.benachr_termine, benachr_bericht: k.benachr_bericht };
  const kb = (label, key) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', checked: sw[key], style: 'width:auto', onchange: (e) => { sw[key] = e.target.checked; } }), label);
  const f3 = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/kunde/profil', { method: 'PATCH', body: { ...sw, benachr_email: e.target.benachr_email.value } }); melde(m3, 'Gespeichert.', 'ok'); } catch (x) { melde(m3, x.message); } } },
    h('div', {}, h('label', {}, 'Benachrichtigungen an (leer = deine Kontakt-E-Mail)'), h('input', { name: 'benachr_email', type: 'email', value: k.benachr_email || '' })),
    kb('Bei neuen Anfragen', 'benachr_anfragen'), kb('Erinnerung vor Terminen', 'benachr_termine'), kb('Monatsbericht per E-Mail', 'benachr_bericht'), h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  const f1 = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault();
    try { await api('/api/kunde/profil', { method: 'PATCH', body: Object.fromEntries(new FormData(e.target)) }); melde(m1, 'Gespeichert.', 'ok'); } catch (x) { melde(m1, x.message); }
  } },
    h('div', {}, h('label', {}, 'Ansprechpartner'), h('input', { name: 'ansprechpartner', value: k.ansprechpartner || '' })),
    h('div', {}, h('label', {}, 'E-Mail (Kontakt)'), h('input', { name: 'email', type: 'email', value: k.email || '' })),
    h('div', {}, h('label', {}, 'Telefon'), h('input', { name: 'telefon', value: k.telefon || '' })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Speichern')));
  const f2 = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault(); const d = Object.fromEntries(new FormData(e.target));
    try { await api('/api/kunde/passwort', { method: 'POST', body: d }); melde(m2, 'Passwort geändert.', 'ok'); e.target.reset(); } catch (x) { melde(m2, x.message); }
  } },
    h('div', {}, h('label', {}, 'Aktuelles Passwort'), h('input', { name: 'alt', type: 'password', autocomplete: 'current-password', required: true })),
    h('div', {}, h('label', {}, 'Neues Passwort (mind. 10 Zeichen)'), h('input', { name: 'neu', type: 'password', autocomplete: 'new-password', minlength: 10, required: true })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Passwort ändern')));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Dein Konto'), h('p', {}, 'Kundennummer ', h('b', {}, k.kundennummer), ' · Paket ', h('b', {}, k.paket || '–'), ' · Login ', h('b', {}, p.login))),
    h('div', { class: 'card' }, h('h2', {}, 'Kontaktdaten'), m1, f1),
    h('div', { class: 'card' }, h('h2', {}, 'E-Mail-Benachrichtigungen'), h('p', { class: 'small muted' }, 'Wir schreiben dir, wenn etwas Wichtiges passiert.'), m3, f3),
    h('div', { class: 'card' }, h('h2', {}, 'Passwort'), m2, f2), zweiFaktorKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'Gebuchte Leistungen'), tabelle([['Leistung', z => z.name], ['Status', z => statusPill(z.status)], ['Beginn', z => datum(z.beginn)], ['Mindestlaufzeit bis', z => datum(z.mindestlaufzeit_ende)]], p.buchungen, 'Noch nichts gebucht.')));
};

V.avv = async () => {
  const d = await api('/api/kunde/avv');
  return h('div', { class: 'card' }, h('h2', {}, 'Vertrag zur Auftragsverarbeitung (AVV)'),
    h('p', { class: 'small muted' }, 'Hier liegt der unterschriebene Vertrag, der regelt, wie Markentrix personenbezogene Daten in deinem Auftrag verarbeitet (Art. 28 DSGVO).'),
    tabelle([['Unterschrieben am', z => datum(z.unterschrieben_am)], ['Datei', z => z.datei_name || 'AVV'], ['', z => h('a', { class: 'btn sec small', href: '/api/kunde/avv/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Ansehen / Herunterladen')]], d, 'Noch kein unterschriebener Vertrag abgelegt. Das Markentrix-Team meldet sich dazu bei dir.'));
};

V.team = async () => {
  const d = await api('/api/kunde/team'), m = h('div');
  const ROLLE = { inhaber: 'Inhaber (alles)', mitarbeiter: 'Mitarbeiter (ohne Team und Rechnungen)', nur_lesen: 'Nur ansehen' };
  const neu = h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault(); const o = Object.fromEntries(new FormData(e.target));
    try { const r = await api('/api/kunde/team/einladen', { method: 'POST', body: o }); melde(m, r.gemailt ? 'Einladung wurde per E-Mail versendet.' : 'Einladung erstellt. Bitte diesen Link weitergeben: ' + r.einladungslink, 'ok'); setTimeout(zeige, r.gemailt ? 900 : 8000); } catch (x) { melde(m, x.message); } } },
    h('div', {}, h('label', {}, 'E-Mail'), h('input', { name: 'email', type: 'email', required: true })),
    h('div', {}, h('label', {}, 'Name'), h('input', { name: 'name' })),
    h('div', {}, h('label', {}, 'Rolle'), h('select', { name: 'kunden_rolle' }, ...Object.entries(ROLLE).map(([v, t]) => h('option', { value: v, selected: v === 'mitarbeiter' }, t)))),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Einladen')));
  const aend = async (z, body) => { try { await api('/api/kunde/team/' + z.id, { method: 'PATCH', body }); zeige(); } catch (x) { melde(m, x.message); } };
  const rolleWahl = (z) => h('select', { onchange: (e) => aend(z, { kunden_rolle: e.target.value }) }, ...Object.entries(ROLLE).map(([v, t]) => h('option', { value: v, selected: v === z.kunden_rolle }, t)));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Team'), h('p', { class: 'small muted' }, 'Hier lädst du Kolleginnen und Kollegen ein. Jeder bekommt einen eigenen Zugang mit eigenem Passwort.'), m,
      tabelle([['Name', z => z.name || '–'], ['E-Mail', z => z.email], ['Rolle', rolleWahl], ['Status', z => h('span', { class: 'pill ' + (!z.aktiv ? 'bad' : z.angemeldet ? 'ok' : 'warn') }, !z.aktiv ? 'gesperrt' : z.angemeldet ? 'aktiv' : 'eingeladen')],
        ['Letzter Login', z => z.letzter_login ? zeit(z.letzter_login) : 'noch nie'], ['', z => h('button', { class: 'btn sec small', onclick: () => aend(z, { aktiv: !z.aktiv }) }, z.aktiv ? 'Sperren' : 'Entsperren')]], d, 'Noch keine Zugänge.')),
    h('div', { class: 'card' }, h('h2', {}, 'Neuen Zugang einladen'), neu));
};

async function zeige() {
  const id = (location.hash || '#').slice(1);
  const erlaubt = sichtbar().map(s => s[0]);
  const seite = erlaubt.includes(id) ? id : (hat('ki_chat') ? 'assistent' : 'uebersicht');
  let inhalt;
  try { inhalt = await V[seite](); } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  root.replaceChildren(gerüst(seite, inhalt));
}

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
(async () => {
  try {
    const me = await api('/api/me');
    if (me.rolle === 'admin') { location.href = '/admin'; return; }
    start = await api('/api/kunde/start');
    if (start.kunde.branding_farbe) { const f = start.kunde.branding_farbe; document.documentElement.style.setProperty('--grad', f); document.documentElement.style.setProperty('--violet', f); }
  } catch (e) { return; }
  window.addEventListener('hashchange', zeige);
  zeige();
})();
