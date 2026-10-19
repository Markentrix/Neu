import { h, api, datum, zeit, euro, groesse, melde, abmelden, sparkline, zweiFaktorKarte, rechtFuss } from './common.js';

const root = document.getElementById('app');
let start = null;
const hat = (c) => start.module.some(m => m.code === c);

const SEITEN = [
  ['uebersicht', 'Übersicht', null],
  ['status', 'Status', null],
  ['briefing', 'Briefing', null],
  ['nachrichten', 'Nachrichten', null],
  ['freigaben', 'Freigaben', null],
  ['assistent', 'KI-Assistent', 'ki_chat'],
  ['anfragen', 'Anfragen', 'anfragen_termine'],
  ['termine', 'Termine', 'anfragen_termine'],
  ['kontakte', 'Kontakte', 'kontakte_angebote_vertraege'],
  ['dokumente', 'Angebote & Verträge', 'kontakte_angebote_vertraege'],
  ['unterlagen', 'Dokumente', null],
  ['auswertung', 'Auswertung', null],
  ['berichte', 'Monatsberichte', null],
  ['belege', 'Angebote & Rechnungen', null],
  ['website', 'Website & Landingpages', 'website'],
  ['wochenangebote', 'Wochenangebote', 'wochenangebote'],
  ['werbung', 'Werbung & Berichte', 'werbung_berichte'],
  ['automationen', 'Automationen', 'automationen'],
  ['avv', 'Datenschutz-Vertrag', null],
  ['team', 'Team', null],
  ['hilfe', 'Hilfe', null],
  ['einstellungen', 'Einstellungen', null],
];
const inhaber = () => start.kunden_rolle === 'inhaber';
const sichtbar = () => SEITEN.filter(s => (!s[2] || hat(s[2])) && (!['belege', 'team', 'avv'].includes(s[0]) || inhaber()));

const zaehler = (id) => (start.badges && (id === 'nachrichten' ? start.badges.nachrichten : id === 'freigaben' ? start.badges.freigaben : id === 'briefing' ? start.badges.briefing : id === 'avv' ? start.badges.avv : 0)) || 0;

function gerüst(aktiv, inhalt) {
  const k = start.kunde;
  return h('div', { class: 'shell' },
    h('aside', { class: 'side' },
      h('div', { class: 'brand' }, k.logo_vorhanden ? h('img', { class: 'kundenlogo', src: '/api/kunde/logo', alt: '' }) : h('div', { class: 'logo' }, 'M'), k.logo_vorhanden ? k.firma : 'Markentrix'),
      sichtbar().map(s => h('a', { class: 'nav' + (s[0] === aktiv ? ' on' : ''), href: '#' + s[0] }, s[1], zaehler(s[0]) ? h('span', { class: 'badge' }, zaehler(s[0])) : '')),
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

function startKarte(sl) {
  if (!sl.aktiv) return '';
  const pct = sl.gesamt ? Math.round(100 * sl.fertig / sl.gesamt) : 0;
  return h('div', { class: 'card' }, h('h2', {}, 'Dein Start bei Markentrix'),
    h('p', { class: 'small muted' }, sl.fertig + ' von ' + sl.gesamt + ' Schritten erledigt. Wir kümmern uns um die meisten, ein paar brauchen deine Hilfe.'),
    h('div', { class: 'fortschritt' }, h('div', { style: 'width:' + pct + '%' })),
    sl.punkte.map(p => h('div', { class: 'row', style: 'padding:6px 0;border-bottom:1px solid var(--line)' },
      h('span', { style: 'width:22px' }, p.fertig ? '✅' : '⬜'), h('span', { class: 'grow' + (p.fertig ? ' muted' : '') }, p.titel),
      p.seite ? h('a', { class: 'btn small', href: '#' + p.seite }, p.aktion) : '')));
}

V.uebersicht = async () => {
  const [z, sl] = await Promise.all([api('/api/kunde/kennzahlen'), api('/api/kunde/startliste')]);
  const karte = (titel, zahl, text, link) => h('a', { class: 'card', href: link, style: 'text-decoration:none;color:inherit' }, h('h3', {}, titel), h('div', { class: 'stat' }, h('b', {}, zahl), h('span', { class: 'muted small' }, text)));
  const zusatz = [
    karte('Nachrichten', z.nachrichten_offen, z.wartet_auf_dich ? z.wartet_auf_dich + ' warten auf dich' : 'offen', '#nachrichten'),
    karte('Freigaben', z.freigaben_wartend, z.freigaben_wartend ? 'warten auf deine Entscheidung' : 'nichts offen', '#freigaben'),
    karte('Anfragen', z.anfragen_30d, 'letzte 30 Tage', '#anfragen'),
    z.antwortzeit_h !== null ? h('div', { class: 'card' }, h('h3', {}, 'Antwortzeit des Teams'), h('div', { class: 'stat' }, h('b', {}, String(z.antwortzeit_h).replace('.', ',') + ' h'), h('span', { class: 'muted small' }, 'im Schnitt, letzte 90 Tage'))) : '',
  ];
  return h('div', { class: 'stack' }, startKarte(sl), start.badges && start.badges.briefing && !sl.aktiv ? h('div', { class: 'card' }, h('h2', {}, 'Dein Briefing fehlt noch'), h('p', { class: 'small muted' }, 'Mit ein paar Angaben zu deinem Unternehmen können wir deine Website und Texte viel schneller fertigstellen. Es dauert etwa 10 Minuten.'), h('a', { class: 'btn', href: '#briefing' }, 'Jetzt ausfüllen')) : '', z.bewertung_faellig ? zufriedenheitKarte() : '', h('div', { class: 'grid3' }, karten(), zusatz));
};

function zufriedenheitKarte() {
  const m = h('div'), kom = h('input', { placeholder: 'Möchtest du uns etwas mitgeben? (freiwillig)', maxlength: 1000 }); let wahl = null;
  const knoepfe = Array.from({ length: 11 }, (_, i) => h('button', { class: 'btn sec small', type: 'button', onclick: (e) => { wahl = i; knoepfe.forEach(b => b.classList.remove('gewaehlt')); e.target.classList.add('gewaehlt'); } }, String(i)));
  return h('div', { class: 'card' }, h('h2', {}, 'Wie zufrieden bist du mit uns?'), h('p', { class: 'small muted' }, 'Von 0 (gar nicht) bis 10 (sehr). Dauert 10 Sekunden und hilft uns, besser zu werden.'), m,
    h('div', { class: 'row punkte' }, knoepfe), h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, kom),
      h('button', { class: 'btn', onclick: async () => { if (wahl === null) { melde(m, 'Bitte wähle eine Zahl.'); return; }
        try { await api('/api/kunde/zufriedenheit', { method: 'POST', body: { punkte: wahl, kommentar: kom.value } }); location.reload(); } catch (x) { melde(m, x.message); } } }, 'Senden')));
}

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

// ------------------------------------------------------------- Nachrichten und Aufträge
const ARTEN = { frage: 'Frage', auftrag: 'Auftrag', aenderung: 'Änderungswunsch', problem: 'Problem', modul: 'Zusatzmodul' };
const STATUS_TXT = { offen: 'offen', in_arbeit: 'in Arbeit', wartet_auf_kunde: 'wartet auf dich', erledigt: 'erledigt' };
const tstatus = (s) => h('span', { class: 'pill ' + (s === 'erledigt' ? 'ok' : s === 'wartet_auf_kunde' ? 'warn' : '') }, STATUS_TXT[s] || s);
const darfSchreiben = () => start.kunden_rolle !== 'nur_lesen';

function dateiLinks(liste) {
  return liste.length ? h('div', { class: 'small', style: 'margin-top:6px' }, liste.map(d => h('a', { class: 'dateilink', href: '/api/kunde/dateien/' + d.id, target: '_blank', rel: 'noopener' }, '📎 ' + d.name + ' (' + groesse(d.groesse) + ')'))) : '';
}

V.nachrichten = async (id) => {
  if (id) return nachrichtDetail(id);
  const liste = await api('/api/kunde/tickets'), m = h('div');
  const betreff = h('input', { name: 'betreff', required: true, maxlength: 200, placeholder: 'Worum geht es?' });
  const art = h('select', { name: 'art' }, ...Object.entries(ARTEN).filter(([v]) => v !== 'modul').map(([v, t]) => h('option', { value: v }, t)));
  const text = h('textarea', { name: 'text', rows: 5, required: true, maxlength: 10000, placeholder: 'Beschreibe dein Anliegen. Je genauer, desto schneller können wir helfen.' });
  const form = h('form', { onsubmit: async (e) => { e.preventDefault();
    try { const r = await api('/api/kunde/tickets', { method: 'POST', body: { betreff: betreff.value, art: art.value, text: text.value } }); location.hash = '#nachrichten/' + r.id; } catch (x) { melde(m, x.message); } } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Betreff'), betreff), h('div', {}, h('label', {}, 'Art'), art)),
    h('label', {}, 'Nachricht'), text, h('p', {}, h('button', { class: 'btn' }, 'Absenden')));
  return h('div', { class: 'stack' },
    darfSchreiben() ? h('div', { class: 'card' }, h('h2', {}, 'Neue Nachricht an Markentrix'), h('p', { class: 'small muted' }, 'Fragen, Aufträge oder Änderungswünsche, z. B. neue Öffnungszeiten, ein Foto für die Website, ein Problem. Wir antworten hier und per E-Mail.'), m, form) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Deine Nachrichten'),
      tabelle([['Nr.', z => h('a', { href: '#nachrichten/' + z.id }, z.nr)], ['Betreff', z => h('a', { href: '#nachrichten/' + z.id }, (z.kunde_ungelesen ? '● ' : '') + z.betreff)], ['Art', z => ARTEN[z.art] || z.art], ['Status', z => tstatus(z.status)], ['Zuletzt', z => zeit(z.geaendert_am)]], liste, 'Noch keine Nachrichten.')));
};

async function nachrichtDetail(id) {
  const t = await api('/api/kunde/tickets/' + id), m = h('div');
  const bubbles = t.nachrichten.map(n => h('div', { class: 'bub ' + (n.von === 'kunde' ? 'kunde' : 'team') }, h('div', { class: 'small wer' }, (n.von === 'kunde' ? (n.autor_name || 'Du') : (n.autor_name || 'Markentrix-Team')) + ' · ' + zeit(n.erstellt_am)), n.text));
  const text = h('textarea', { rows: 4, maxlength: 10000, placeholder: t.status === 'erledigt' ? 'Noch etwas offen? Schreibe hier, dann öffnen wir die Anfrage wieder.' : 'Deine Antwort …' });
  const datei = h('input', { type: 'file', accept: '.pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx,.pptx,.txt,.csv,.zip' });
  { const hash = location.hash, anzahl = t.nachrichten.length;   // Chat-Gefühl: neue Nachrichten alle 12 s holen, nur wenn nichts getippt wird
    const iv = setInterval(async () => { if (location.hash !== hash) return clearInterval(iv); if (document.hidden) return;
      try { const n = await api('/api/kunde/tickets/' + id); if (n.nachrichten.length !== anzahl && !text.value.trim()) { clearInterval(iv); location.reload(); } } catch (e) { /* nächster Versuch */ } }, 12000); }
  const senden = async () => {
    try {
      if (text.value.trim()) await api('/api/kunde/tickets/' + id + '/nachricht', { method: 'POST', body: { text: text.value } });
      if (datei.files[0]) { const f = new FormData(); f.append('datei', datei.files[0]); await api('/api/kunde/tickets/' + id + '/dateien', { method: 'POST', body: f }); }
      if (!text.value.trim() && !datei.files[0]) { melde(m, 'Bitte schreibe etwas oder wähle eine Datei.'); return; }
      zeige();
    } catch (x) { melde(m, x.message); }
  };
  let bewertung = '';
  if (t.status === 'erledigt') {
    if (t.bewertung) bewertung = h('p', { class: 'small muted' }, 'Deine Bewertung: ' + t.bewertung.punkte + ' von 10. Danke!');
    else if (darfSchreiben()) {
      const mb = h('div'), kom = h('input', { placeholder: 'Kommentar (freiwillig)', maxlength: 1000 }); let wahl = null;
      const kn = Array.from({ length: 11 }, (_, i) => h('button', { class: 'btn sec small', type: 'button', onclick: (e) => { wahl = i; kn.forEach(b => b.classList.remove('gewaehlt')); e.target.classList.add('gewaehlt'); } }, String(i)));
      bewertung = h('div', { class: 'card' }, h('h3', {}, 'Wie zufrieden warst du mit der Bearbeitung?'), mb, h('div', { class: 'row punkte' }, kn),
        h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, kom), h('button', { class: 'btn', onclick: async () => { if (wahl === null) { melde(mb, 'Bitte wähle eine Zahl von 0 bis 10.'); return; }
          try { await api('/api/kunde/tickets/' + id + '/zufriedenheit', { method: 'POST', body: { punkte: wahl, kommentar: kom.value } }); zeige(); } catch (x) { melde(mb, x.message); } } }, 'Bewerten')));
    }
  }
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('div', { class: 'row' }, h('a', { href: '#nachrichten' }, '← Alle Nachrichten'), h('span', { class: 'grow' }), tstatus(t.status)),
      h('h2', { style: 'margin-top:10px' }, t.nr + ' · ' + t.betreff), h('p', { class: 'small muted' }, (ARTEN[t.art] || t.art) + ' · eröffnet am ' + zeit(t.erstellt_am)),
      h('div', { class: 'chatlog thread' }, bubbles), dateiLinks(t.dateien)),
    bewertung,
    darfSchreiben() ? h('div', { class: 'card' }, h('h3', {}, 'Antworten'), m, text, h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, h('label', { style: 'margin:0 0 4px' }, 'Datei anhängen (max. 8 MB, optional)'), datei), h('button', { class: 'btn', onclick: senden }, 'Senden'))) : '');
}

// ------------------------------------------------------------- Briefing
V.briefing = async () => {
  const d = await api('/api/kunde/briefing'), m = h('div'), eingaben = {};
  const feld = (f) => {
    const wert = d.daten[f.key] || '';
    const el = f.art === 'lang' ? h('textarea', { rows: 3, maxlength: 3000 }, wert)
      : f.art.startsWith('wahl:') ? h('select', {}, h('option', { value: '' }, '– bitte wählen –'), f.art.slice(5).split('|').map(o => h('option', { value: o, selected: o === wert }, o)))
      : h('input', { maxlength: 3000, value: wert });
    if (f.art === 'lang') el.value = wert;
    eingaben[f.key] = el;
    return h('div', {}, h('label', {}, f.frage + (f.pflicht ? ' *' : '')), el);
  };
  const sammeln = () => Object.fromEntries(Object.entries(eingaben).map(([k, el]) => [k, el.value]));
  const los = async (abschicken) => {
    try { await api('/api/kunde/briefing', { method: 'PUT', body: { daten: sammeln(), abschicken } }); if (abschicken) { alert('Danke! Dein Briefing ist beim Markentrix-Team angekommen.'); location.hash = '#uebersicht'; location.reload(); } else melde(m, 'Gespeichert. Du kannst jederzeit weitermachen.', 'ok'); } catch (x) { melde(m, x.message); }
  };
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Briefing'),
    h('p', { class: 'small muted' }, 'Mit diesen Angaben bauen wir deine Website, Texte und Auswertungen. Du kannst zwischenspeichern und später weitermachen. Pflichtfelder sind mit * markiert. Logo und Bilder lädst du unter „Dokumente“ hoch.'),
    d.status === 'abgeschickt' ? h('div', { class: 'msg ok' }, 'Abgeschickt am ' + zeit(d.abgeschickt_am) + '. Du kannst unten jederzeit Änderungen vornehmen und erneut abschicken.') : '', m),
    d.struktur.map(a => h('div', { class: 'card' }, h('h3', {}, a.abschnitt), h('div', { class: 'stack' }, a.felder.map(feld)))),
    darfSchreiben() ? h('div', { class: 'row' }, h('button', { class: 'btn sec', onclick: () => los(false) }, 'Zwischenspeichern'), h('button', { class: 'btn', onclick: () => los(true) }, d.status === 'abgeschickt' ? 'Änderungen abschicken' : 'Abschicken')) : h('p', { class: 'muted small' }, 'Mit deinem Zugang kannst du nur ansehen.'));
};

// ------------------------------------------------------------- Auswertung
const delta = (neu, alt) => alt ? ((neu - alt) / alt * 100) : null;
const pfeil = (p) => p === null ? '' : (p >= 0 ? '▲ +' : '▼ ') + Math.round(p) + ' % zum Vormonat';
V.auswertung = async () => {
  const d = await api('/api/kunde/auswertung'), z = d.dieser, v = d.letzter;
  const karte = (titel, wert, alt, einheit = '') => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, titel), h('b', {}, String(wert) + einheit), alt !== undefined ? h('span', { class: 'small ' + (delta(wert, alt) >= 0 ? 'ok' : 'muted') }, pfeil(delta(wert, alt))) : '');
  const quellen = Object.entries(z.anfragen.nach_quelle);
  const maxq = Math.max(1, ...quellen.map(q => q[1]));
  const QN = { website: 'Website', email: 'E-Mail', telefon: 'Telefon', chat: 'Chat', whatsapp: 'WhatsApp', sonstiges: 'Sonstiges' };
  const ext = d.extern.length ? d.extern[d.extern.length - 1] : null;
  const anrufe = Object.values(z.anrufe).reduce((a, b) => a + b.anzahl, 0);
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Auswertung ' + d.monat_name), h('p', { class: 'small muted' }, 'Die Zahlen aktualisieren sich laufend. Den Vergleich zeigen wir gegen ' + d.vormonat_name + ' (ganzer Monat).')),
    h('div', { class: 'grid3' },
      karte('Anfragen', z.anfragen.gesamt, v.anfragen.gesamt), karte('Termine', z.termine.gesamt, v.termine.gesamt), karte('Anrufe', anrufe),
      karte('Fragen an den Agenten', z.chat_fragen), karte('Automatische Abläufe', z.automatische_ablaeufe), karte('Bewertungsbitten verschickt', z.bewertungsanfragen)),
    h('div', { class: 'card' }, h('h3', {}, 'Anfragen pro Woche (12 Wochen)'), sparkline(d.wochen.map(w => w.anfragen)), h('p', { class: 'small muted' }, 'Zuletzt: ' + d.wochen.map(w => w.anfragen).join(' · '))),
    h('div', { class: 'card' }, h('h3', {}, 'Anfragen und Termine pro Monat'), tabelle([['Monat', r => r.monat], ['Anfragen', r => r.anfragen], ['Termine', r => r.termine]], d.monate)),
    quellen.length ? h('div', { class: 'card' }, h('h3', {}, 'Woher kommen die Anfragen (' + d.monat_name + ')'), quellen.map(([q, n]) => h('div', { class: 'row', style: 'margin:6px 0' }, h('span', { style: 'width:110px' }, QN[q] || q), h('div', { style: 'height:14px;border-radius:7px;background:#8B5CF6;width:' + Math.max(4, n / maxq * 100) + '%;max-width:70%' }), h('b', {}, n)))) : '',
    h('div', { class: 'card' }, h('h3', {}, 'Website und Google'), ext ? h('div', { class: 'grid3' },
      ext.besucher !== null ? karte('Website-Besucher (' + ext.monat + ')', ext.besucher) : '', ext.google_aufrufe !== null ? karte('Google-Aufrufe', ext.google_aufrufe) : '',
      ext.google_sterne !== null ? karte('Google-Sterne', String(ext.google_sterne).replace('.', ','), undefined, ' ★ (' + (ext.google_bewertungen ?? '–') + ' Bewertungen)') : '') : h('p', { class: 'muted' }, 'Besucher- und Google-Zahlen trägt das Markentrix-Team monatlich ein. Sobald sie vorliegen, erscheinen sie hier.'),
      d.extern.length > 1 ? tabelle([['Monat', r => r.monat], ['Besucher', r => r.besucher ?? '–'], ['Google-Aufrufe', r => r.google_aufrufe ?? '–'], ['Sterne', r => r.google_sterne ?? '–'], ['Bewertungen', r => r.google_bewertungen ?? '–']], d.extern) : ''));
};

// ------------------------------------------------------------- Hilfe
const HILFE = [
  ['Start', 'Wie melde ich mich an und ändere mein Passwort?', 'Du meldest dich mit deiner E-Mail-Adresse und deinem Passwort an. Unter Einstellungen kannst du dein Passwort ändern und die Zwei-Faktor-Anmeldung einschalten. Das macht dein Konto deutlich sicherer.'],
  ['Start', 'Ich habe mein Passwort vergessen.', 'Klicke auf der Anmeldeseite auf „Passwort vergessen“ und folge dem Link in der E-Mail. Kommt keine E-Mail an, melde dich direkt bei uns, wir setzen dein Passwort zurück.'],
  ['Start', 'Was muss ich am Anfang tun?', 'Fülle das Briefing aus (Menü „Briefing“). Lade dein Logo und wichtige Unterlagen unter „Dokumente“ hoch. So können wir sofort loslegen.'],
  ['Zusammenarbeit', 'Wie erreiche ich das Markentrix-Team?', 'Schreib uns unter „Nachrichten“. Wähle eine Art (Frage, Auftrag, Änderungswunsch, Problem), beschreibe dein Anliegen und hänge bei Bedarf eine Datei an. Wir antworten dort und per E-Mail.'],
  ['Zusammenarbeit', 'Was sind Freigaben?', 'Bevor wir etwas veröffentlichen, zum Beispiel einen Beitrag oder Text, zeigen wir es dir unter „Freigaben“. Du kannst freigeben oder eine Änderung wünschen (mit kurzem Kommentar). Deine Entscheidung wird mit Datum und Uhrzeit festgehalten.'],
  ['Zusammenarbeit', 'Wo lade ich Logos, Verträge und Bilder hoch?', 'Unter „Dokumente“. Wähle die Art (zum Beispiel Logo oder Briefing) und die Datei. Erlaubt sind PDF, Bilder, Word, Excel, PowerPoint, Text, CSV und ZIP bis 8 MB. Bitte lade dort keine Passwörter hoch.'],
  ['Auswertung', 'Was zeigt die Auswertung?', 'Anfragen, Termine, Anrufe und die Arbeit des Agenten im laufenden Monat, im Vergleich zum Vormonat, dazu der Verlauf über 12 Wochen. Website-Besucher und Google-Zahlen trägt das Team monatlich ein.'],
  ['Auswertung', 'Wo finde ich den Monatsbericht?', 'Unter „Monatsberichte“. Dort steht für jeden Monat ein Bericht, den du als PDF herunterladen kannst.'],
  ['Funktionen', 'Wie bearbeite ich Anfragen und Termine?', 'Unter „Anfragen“ siehst du alle Anfragen und setzt den Status (zum Beispiel beantwortet oder erledigt). Unter „Termine“ findest du die kommenden Termine.', 'anfragen_termine'],
  ['Funktionen', 'Was kann der Assistent?', 'Du kannst dem Assistenten Fragen zu deinen Anfragen, Terminen und zum Portal stellen. Er gibt keine Rechts-, Steuer- oder Preisauskunft. Dafür schreib dem Team.', 'ki_chat'],
  ['Funktionen', 'Wie ändere ich Angebote, Öffnungszeiten oder „heute geschlossen“ auf meiner Website?', 'Unter „Wochenangebote“ lädst du eine Datei hoch und legst Angebote mit Preis, Events, Hinweise und „Heute geschlossen“ an. Mit „Aus Deutsch übersetzen“ füllt der Agent die anderen Sprachen aus. Bitte lies die Übersetzung kurz durch und speichere dann. Die Seite aktualisiert sich sofort.', 'wochenangebote'],
  ['Funktionen', 'Welche Zusatzfunktionen gibt es?', 'Unter „Automationen“ siehst du, was für dich aktiv ist. Mit „Anfragen“ bei einer Funktion erreicht uns deine Nachricht, wir melden uns mit Details und Preis.', 'automationen'],
  ['Konto', 'Wie lade ich Mitarbeiter ein?', 'Unter „Team“ (nur für Inhaber). Wähle die Rolle: Inhaber, Mitarbeiter oder Nur ansehen. Die Person bekommt einen Einladungslink.'],
  ['Konto', 'Wie ändere ich meine Anschrift oder E-Mail-Einstellungen?', 'Unter „Einstellungen“. Die Rechnungsanschrift änderst du als Inhaber selbst. Firmenname und Rechtsform ändern wir für dich: Schreib uns dazu unter Nachrichten.'],
  ['Konto', 'Wo finde ich Rechnungen und Angebote?', 'Unter „Angebote & Rechnungen“ (nur für Inhaber). Dort kannst du Angebote annehmen und Rechnungen als PDF laden.'],
  ['Datenschutz', 'Wo liegen meine Daten und kann ich sie mitnehmen?', 'Deine Daten liegen auf einem eigenen Server von Markentrix bei Hetzner. Den Auftragsverarbeitungsvertrag findest du unter „Datenschutz-Vertrag“. Bei Vertragsende bekommst du einen vollständigen Export deiner Daten.'],
];
V.hilfe = async () => {
  const such = h('input', { type: 'search', placeholder: 'Wonach suchst du? Zum Beispiel „Passwort“ oder „Angebot“', style: 'width:100%' }), box = h('div', { class: 'stack' });
  const zeichne = () => {
    const q = such.value.trim().toLowerCase();
    const liste = HILFE.filter(e => (!e[3] || hat(e[3])) && (!q || (e[1] + ' ' + e[2] + ' ' + e[0]).toLowerCase().includes(q)));
    box.replaceChildren(...(liste.length ? liste.map(e => h('details', { class: 'card hilfe' }, h('summary', {}, h('b', {}, e[1]), ' ', h('span', { class: 'pill' }, e[0])), h('p', {}, e[2]))) : [h('div', { class: 'card' }, h('p', { class: 'muted' }, 'Dazu haben wir nichts gefunden. Schreib uns einfach, wir helfen gern.'))]));
  };
  such.oninput = zeichne; zeichne();
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Hilfe'), h('p', { class: 'small muted' }, 'Antworten auf die häufigsten Fragen.'), such), box,
    h('div', { class: 'card' }, h('h3', {}, 'Nichts gefunden?'), h('p', { class: 'small muted' }, 'Wir helfen dir persönlich weiter.'), h('a', { class: 'btn', href: '#nachrichten' }, 'Nachricht an das Team')));
};

// ------------------------------------------------------------- Freigaben
const FART = { social: 'Social Media', text: 'Text', angebot: 'Angebot', design: 'Design', website: 'Website', sonstiges: 'Sonstiges' };
V.freigaben = async () => {
  const liste = await api('/api/kunde/freigaben');
  const wartend = liste.filter(f => f.status === 'wartet'), erledigt = liste.filter(f => f.status !== 'wartet');
  const karte = (f) => {
    const m = h('div'), kom = h('textarea', { rows: 2, maxlength: 2000, placeholder: 'Kommentar (bei „Änderung wünschen“ bitte kurz beschreiben, was angepasst werden soll)' });
    const los = async (entscheidung) => { try { await api('/api/kunde/freigaben/' + f.id + '/entscheiden', { method: 'POST', body: { entscheidung, kommentar: kom.value } }); zeige(); } catch (x) { melde(m, x.message); } };
    return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h3', { style: 'margin:0' }, f.titel), h('span', { class: 'pill' }, FART[f.art] || f.art), h('span', { class: 'grow' }),
      h('span', { class: 'pill ' + (f.status === 'freigegeben' ? 'ok' : f.status === 'abgelehnt' ? 'bad' : f.status === 'wartet' ? 'warn' : '') }, f.status === 'wartet' ? 'wartet auf dich' : f.status === 'freigegeben' ? 'freigegeben' : f.status === 'abgelehnt' ? 'Änderung gewünscht' : 'zurückgezogen')),
      h('p', { class: 'small muted' }, 'Angefragt am ' + zeit(f.angefragt_am)), f.inhalt ? h('div', { class: 'freitext' }, f.inhalt) : '',
      f.dateien.length ? h('div', { class: 'small' }, f.dateien.map(d => h('a', { class: 'dateilink', href: '/api/kunde/dateien/' + d.id, target: '_blank', rel: 'noopener' }, '📎 ' + d.name + ' (' + groesse(d.groesse) + ')'))) : '',
      f.status === 'wartet' ? (darfSchreiben() ? h('div', {}, m, kom, h('div', { class: 'row', style: 'margin-top:10px' }, knopf('Freigeben', () => los('freigegeben'), 'btn'), knopf('Änderung wünschen', () => los('abgelehnt'), 'btn sec'))) : h('p', { class: 'small muted' }, 'Mit deinem Zugang kannst du nur ansehen.'))
        : h('p', { class: 'small muted' }, (f.entschieden_name ? f.entschieden_name + ' am ' : 'Am ') + zeit(f.entschieden_am) + (f.kommentar ? ' · „' + f.kommentar + '“' : '')));
  };
  const knopf = (t, fn, c) => h('button', { class: c, onclick: fn }, t);
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Freigaben'), h('p', { class: 'small muted' }, 'Hier zeigen wir dir Beiträge, Texte und Entwürfe, bevor sie veröffentlicht werden. Mit deiner Freigabe wird Datum, Uhrzeit und dein Name festgehalten.')),
    wartend.length ? wartend.map(karte) : h('div', { class: 'card' }, h('p', { class: 'muted' }, 'Aktuell wartet nichts auf deine Freigabe.')),
    erledigt.length ? h('div', { class: 'stack' }, h('h3', {}, 'Bisherige Entscheidungen'), erledigt.map(karte)) : '');
};

// ------------------------------------------------------------- Dokumentenablage
V.unterlagen = async () => {
  const d = await api('/api/kunde/unterlagen'), m = h('div');
  const kat = h('select', {}, ...Object.entries(d.kategorien).map(([v, t]) => h('option', { value: v }, t)));
  const datei = h('input', { type: 'file', accept: '.pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx,.pptx,.txt,.csv,.zip' });
  const hoch = async () => { if (!datei.files[0]) { melde(m, 'Bitte wähle zuerst eine Datei.'); return; }
    const f = new FormData(); f.append('datei', datei.files[0]); f.append('kategorie', kat.value);
    try { await api('/api/kunde/unterlagen', { method: 'POST', body: f }); zeige(); } catch (x) { melde(m, x.message); } };
  const weg = async (z) => { if (!confirm('Datei "' + z.name + '" wirklich löschen?')) return; try { await api('/api/kunde/unterlagen/' + z.id, { method: 'DELETE' }); zeige(); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Dokumente'), h('p', { class: 'small muted' }, 'Verträge, Briefings, Logos und Material an einem sicheren Ort, für dich und das Markentrix-Team. Bitte lade hier keine Passwörter hoch, die schickst du uns nicht per Datei.'),
      darfSchreiben() ? h('div', {}, m, h('div', { class: 'row' }, kat, datei, h('button', { class: 'btn', onclick: hoch }, 'Hochladen'))) : '',
      tabelle([['Datei', z => h('a', { href: '/api/kunde/dateien/' + z.id, target: '_blank', rel: 'noopener' }, z.name)], ['Art', z => d.kategorien[z.kategorie] || '–'], ['Größe', z => groesse(z.groesse)], ['Von', z => z.von === 'team' ? 'Markentrix' : 'Dir'], ['Datum', z => zeit(z.erstellt_am)],
        ['', z => darfSchreiben() && z.von === 'kunde' ? h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen') : '']], d.dateien, 'Noch keine Dokumente.')));
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

const IART = { angebot: 'Angebot', event: 'Event', hinweis: 'Hinweis', geschlossen: 'Heute geschlossen' };
async function inhalteKarte() {
  const d = await api('/api/kunde/angebots-inhalte'), m = h('div');
  const art = h('select', {}, Object.entries(IART).map(([v, t]) => h('option', { value: v }, t)));
  const titel = {}, text = {};
  const felder = d.sprachen.map(sp => {
    titel[sp] = h('input', { maxlength: 200, placeholder: 'Titel (' + d.sprachnamen[sp] + ')' + (sp === 'de' ? ', Pflicht' : ', freiwillig'), dir: sp === 'ar' ? 'rtl' : 'ltr' });
    text[sp] = h('textarea', { rows: 2, maxlength: 2000, placeholder: 'Beschreibung (' + d.sprachnamen[sp] + '), freiwillig', dir: sp === 'ar' ? 'rtl' : 'ltr' });
    return h('div', { class: 'sprachblock' }, h('label', {}, d.sprachnamen[sp] + (sp === 'de' ? ' (Hauptsprache)' : '')), titel[sp], text[sp]);
  });
  const preis = h('input', { maxlength: 40, placeholder: 'Preis, z. B. 1,99 € / kg (freiwillig)' }), von = h('input', { type: 'date' }), bis = h('input', { type: 'date' });
  const nachher = (r) => { if (r.hinweis) alert(r.hinweis); zeige(); };
  const ziele = d.sprachen.filter(x => x !== 'de');
  const uebersetzen = async (e) => {
    const texte = {}; if (titel.de.value.trim()) texte.titel = titel.de.value; if (text.de.value.trim()) texte.text = text.de.value;
    if (!Object.keys(texte).length) { melde(m, 'Bitte schreibe zuerst den deutschen Titel oder Text.'); return; }
    const b = e.target; b.disabled = true; b.textContent = 'Übersetze …'; melde(m, '');
    try {
      const r = await api('/api/kunde/angebots-inhalte/uebersetzen', { method: 'POST', body: { texte, ziele } }); let n = 0;
      ziele.forEach(sp => { if (r.uebersetzungen.titel && r.uebersetzungen.titel[sp] && !titel[sp].value.trim()) { titel[sp].value = r.uebersetzungen.titel[sp]; n++; } if (r.uebersetzungen.text && r.uebersetzungen.text[sp] && !text[sp].value.trim()) { text[sp].value = r.uebersetzungen.text[sp]; n++; } });
      melde(m, n ? r.hinweis : 'Die anderen Felder sind schon ausgefüllt. Leere sie, wenn du neu übersetzen lassen willst.', n ? 'ok' : 'info');
    } catch (x) { melde(m, x.message); }
    b.disabled = false; b.textContent = 'Aus Deutsch übersetzen';
  };
  const speichern = async () => {
    const t = {}, x = {}; d.sprachen.forEach(sp => { t[sp] = titel[sp].value; x[sp] = text[sp].value; });
    try { nachher(await api('/api/kunde/angebots-inhalte', { method: 'POST', body: { art: art.value, titel: t, text: x, preis: preis.value || null, gueltig_von: von.value || null, gueltig_bis: bis.value || null } })); } catch (e) { melde(m, e.message); }
  };
  const umschalten = async (z) => { try { nachher(await api('/api/kunde/angebots-inhalte/' + z.id, { method: 'PATCH', body: { aktiv: !z.aktiv } })); } catch (e) { melde(m, e.message); } };
  const weg = async (z) => { if (!confirm('Eintrag wirklich löschen?')) return; try { nachher(await api('/api/kunde/angebots-inhalte/' + z.id, { method: 'DELETE' })); } catch (e) { melde(m, e.message); } };
  const name = (z) => (z.titel.de || Object.values(z.titel)[0] || (z.art === 'geschlossen' ? 'Heute geschlossen' : '–'));
  return h('div', { class: 'card' }, h('h2', {}, 'Texte, Events und Hinweise'),
    h('p', { class: 'small muted' }, 'Zusätzlich zur Datei: Angebote mit Preis, Veranstaltungen, Hinweise und „heute geschlossen“. Sprachen auf deiner Website: ' + d.sprachen.map(s => d.sprachnamen[s]).join(', ') + '. Ist eine Übersetzung leer, zeigen wir den deutschen Text.'),
    m, h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Art'), art), h('div', {}, h('label', {}, 'Preis'), preis), h('div', {}, h('label', {}, 'Gültig von (leer = sofort)'), von), h('div', {}, h('label', {}, 'Gültig bis (leer = unbegrenzt)'), bis)),
    h('div', { class: 'stack', style: 'margin-top:10px' }, felder),
    h('div', { class: 'row', style: 'margin-top:10px' }, ziele.length ? h('button', { class: 'btn sec', type: 'button', onclick: uebersetzen }, 'Aus Deutsch übersetzen') : '', h('button', { class: 'btn', onclick: speichern }, 'Speichern und veröffentlichen')),
    ziele.length ? h('p', { class: 'small muted' }, 'Tipp: Deutsch ausfüllen, auf „Aus Deutsch übersetzen“ klicken, kurz prüfen, dann speichern. Die Übersetzung erstellt der Agent automatisch, bitte lies sie kurz durch.') : '',
    h('h3', {}, 'Aktuelle Einträge'),
    tabelle([['Art', z => IART[z.art]], ['Titel', name], ['Preis', z => z.preis || ''], ['Gültig', z => [z.gueltig_von ? datum(z.gueltig_von) : '', z.gueltig_bis ? ' – ' + datum(z.gueltig_bis) : ''].join('')], ['Sprachen', z => Object.keys(z.titel).concat(Object.keys(z.text)).filter((v, i, a) => a.indexOf(v) === i).join(', ')],
      ['Status', z => h('span', { class: 'pill ' + (z.aktiv ? 'ok' : '') }, z.aktiv ? 'sichtbar' : 'ausgeblendet')],
      ['', z => h('div', { class: 'row' }, h('button', { class: 'btn sec small', onclick: () => umschalten(z) }, z.aktiv ? 'Ausblenden' : 'Einblenden'), h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen'))]], d.inhalte, 'Noch keine Einträge.'));
}

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
    await inhalteKarte(),
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
        h('div', { class: 'stat' }, h('b', {}, x.automatische_ablaeufe), h('span', { class: 'muted small' }, 'Automatische Abläufe'))),
      b.einordnung ? h('div', { style: 'margin-top:14px' }, h('h3', {}, 'Einordnung'), h('p', {}, b.einordnung)) : '',
      b.schritte && b.schritte.length ? h('div', {}, h('h3', {}, 'Unsere nächsten Schritte'), h('ul', {}, b.schritte.map(z => h('li', {}, z)))) : '');
  }));
};

V.automationen = async () => {
  const d = await api('/api/kunde/automationen');
  return h('div', { class: 'card' }, h('h2', {}, 'Automationen'),
    d.map(a => h('div', { class: 'modul' }, h('div', { class: 'grow' }, h('b', {}, a.name), h('div', { class: 'small muted' }, a.beschreibung)), h('span', { class: 'pill ' + (a.aktiv ? 'ok' : '') }, a.aktiv ? 'aktiv' : 'nicht gebucht'), !a.aktiv && inhaber() ? h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('Wir melden uns bei dir mit Details und Preis. Anfrage senden?')) return; try { const r = await api('/api/kunde/modul-anfrage', { method: 'POST', body: { modul_code: a.code } }); location.hash = '#nachrichten/' + r.id; } catch (x) { alert(x.message); } } }, 'Anfragen') : '')),
    h('p', { class: 'muted small' }, 'Mit „Anfragen“ erhält das Markentrix-Team deine Nachricht und meldet sich mit Details und Preis.'));
};

function anschriftKarte(k) {
  const m = h('div');
  const f = h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault();
    try { await api('/api/kunde/stammdaten', { method: 'PATCH', body: Object.fromEntries(new FormData(e.target)) }); melde(m, 'Gespeichert. Das Markentrix-Team wurde informiert und nutzt die Anschrift ab der nächsten Rechnung.', 'ok'); } catch (x) { melde(m, x.message); } } },
    h('div', {}, h('label', {}, 'Straße und Nr.'), h('input', { name: 'strasse', value: k.strasse || '' })),
    h('div', {}, h('label', {}, 'PLZ'), h('input', { name: 'plz', value: k.plz || '' })),
    h('div', {}, h('label', {}, 'Ort'), h('input', { name: 'ort', value: k.ort || '' })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Rechnungsanschrift'), h('p', { class: 'small muted' }, 'Firmenname oder Rechtsform ändern wir für dich: Schreib uns dazu unter Nachrichten.'), m, f);
}

V.einstellungen = async () => {
  const p = await api('/api/kunde/profil');
  const m1 = h('div'), m2 = h('div'), m3 = h('div');
  const k = p.kunde; const sw = { benachr_anfragen: k.benachr_anfragen, benachr_termine: k.benachr_termine, benachr_bericht: k.benachr_bericht, benachr_nachrichten: k.benachr_nachrichten };
  const kb = (label, key) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', checked: sw[key], style: 'width:auto', onchange: (e) => { sw[key] = e.target.checked; } }), label);
  const f3 = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/kunde/profil', { method: 'PATCH', body: { ...sw, benachr_email: e.target.benachr_email.value } }); melde(m3, 'Gespeichert.', 'ok'); } catch (x) { melde(m3, x.message); } } },
    h('div', {}, h('label', {}, 'Benachrichtigungen an (leer = deine Kontakt-E-Mail)'), h('input', { name: 'benachr_email', type: 'email', value: k.benachr_email || '' })),
    kb('Bei neuen Anfragen', 'benachr_anfragen'), kb('Erinnerung vor Terminen', 'benachr_termine'), kb('Monatsbericht per E-Mail', 'benachr_bericht'), kb('Antworten und Freigabe-Bitten vom Team', 'benachr_nachrichten'), h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
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
    inhaber() ? anschriftKarte(k) : '',
    h('div', { class: 'card' }, h('h2', {}, 'E-Mail-Benachrichtigungen'), h('p', { class: 'small muted' }, 'Wir schreiben dir, wenn etwas Wichtiges passiert.'), m3, f3),
    h('div', { class: 'card' }, h('h2', {}, 'Passwort'), m2, f2), zweiFaktorKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'Gebuchte Leistungen'), tabelle([['Leistung', z => z.name], ['Status', z => statusPill(z.status)], ['Beginn', z => datum(z.beginn)], ['Mindestlaufzeit bis', z => datum(z.mindestlaufzeit_ende)]], p.buchungen, 'Noch nichts gebucht.')));
};

V.status = async () => {
  const d = await api('/api/kunde/status');
  const farbe = (st) => st === 'erledigt' ? 'ok' : st === 'wartet_auf_kunde' ? 'warn' : '';
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Wartet auf dich'),
      d.wartet_auf_dich.length ? d.wartet_auf_dich.map(w => h('div', { class: 'row', style: 'padding:6px 0;border-bottom:1px solid var(--line)' }, h('span', { class: 'grow' }, w.text), h('a', { class: 'btn small', href: '#' + w.seite }, 'Ansehen'))) : h('p', { class: 'muted' }, 'Nichts offen. Alles läuft bei uns.')),
    h('div', { class: 'card' }, h('h2', {}, 'Deine Aufträge'),
      tabelle([['Nr.', z => z.nummer], ['Betreff', z => h('a', { href: '#nachrichten/' + z.id }, z.betreff)], ['Stand', z => h('span', { class: 'pill ' + farbe(z.status) }, z.status_text)], ['Zuletzt', z => zeit(z.geaendert_am)], ['Fällig', z => z.faellig_am ? datum(z.faellig_am) : '']], d.auftraege, 'Noch keine Aufträge.')),
    h('div', { class: 'card' }, h('h2', {}, 'Website'),
      tabelle([['Domain', z => z.domain], ['Status', z => h('span', { class: 'pill ' + (z.status === 'live' ? 'ok' : 'warn') }, z.status)], ['Erreichbar', z => z.erreichbar ? (z.erreichbar.ok ? '✅ ja' : '⚠ gerade nicht') : '–'], ['Zuletzt veröffentlicht', z => z.letzte_veroeffentlichung ? datum(z.letzte_veroeffentlichung) : '–']], d.websites, 'Noch keine Website verknüpft.')),
    h('div', { class: 'card' }, h('h2', {}, 'Deine Module'), d.module.length ? h('p', {}, d.module.join(' · ')) : h('p', { class: 'muted' }, 'Noch keine Module aktiv.')));
};

V.avv = async () => {
  const [d, offen] = await Promise.all([api('/api/kunde/avv'), api('/api/kunde/avv-offen')]), m = h('div');
  const bestaetigen = (z) => { const name = h('input', { placeholder: 'Vor- und Nachname', maxlength: 200 }), ok = h('input', { type: 'checkbox', style: 'width:auto' });
    return h('div', { class: 'card' }, h('h2', {}, 'Vertrag zur Auftragsverarbeitung bestätigen'),
      h('p', { class: 'small muted' }, 'Der Vertrag regelt, wie Markentrix personenbezogene Daten in deinem Auftrag verarbeitet (Art. 28 DSGVO). Bitte lies ihn und bestätige ihn dann mit einem Klick. Drucken und Unterschreiben ist nicht nötig.'), m,
      h('p', {}, h('a', { class: 'btn sec', href: '/api/kunde/avv-offen/' + z.id + '/vorlage.pdf', target: '_blank', rel: 'noopener' }, 'Vertrag lesen (PDF)')),
      h('label', {}, 'Dein Name'), name,
      h('label', { style: 'display:flex;gap:8px;align-items:flex-start;color:inherit;font-size:14px;margin-top:12px' }, ok, 'Ich habe den Vertrag gelesen und bestätige ihn im Namen meines Unternehmens. Ich bin dazu berechtigt.'),
      h('p', {}, h('button', { class: 'btn', onclick: async () => { try { await api('/api/kunde/avv-offen/' + z.id + '/bestaetigen', { method: 'POST', body: { name: name.value, akzeptiert: ok.checked } }); location.reload(); } catch (x) { melde(m, x.message); } } }, 'Vertrag bestätigen'))); };
  return h('div', { class: 'stack' }, offen.map(bestaetigen), h('div', { class: 'card' }, h('h2', {}, 'Vertrag zur Auftragsverarbeitung (AVV)'),
    h('p', { class: 'small muted' }, 'Hier liegt der bestätigte oder unterschriebene Vertrag, der regelt, wie Markentrix personenbezogene Daten in deinem Auftrag verarbeitet (Art. 28 DSGVO).'),
    tabelle([['Bestätigt / unterschrieben am', z => datum(z.unterschrieben_am)], ['Datei', z => z.datei_name || 'AVV'], ['', z => h('a', { class: 'btn sec small', href: '/api/kunde/avv/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Ansehen / Herunterladen')]], d, offen.length ? 'Noch nicht bestätigt.' : 'Noch kein Vertrag abgelegt.')));
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
  const [id, param] = (location.hash || '#').slice(1).split('/');
  const erlaubt = sichtbar().map(s => s[0]);
  const seite = erlaubt.includes(id) ? id : (hat('ki_chat') ? 'assistent' : 'uebersicht');
  let inhalt;
  try { inhalt = await V[seite](param); } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
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
