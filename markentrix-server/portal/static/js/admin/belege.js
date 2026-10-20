import { h, api, csvLaden, datum, dialog, euro, melde } from '../common.js';
import { lastschriftKarte } from './einstellungen.js';
import { neukundenAngebot } from './leadangebot.js';
import { V, auswahl, fehler, filterKarte, fmtEuro, knopf, kopf, sicher, tabelle } from './kern.js';

// ---------------------------------------------------------------- Angebote und Rechnungen
export const BELEG_ST = { entwurf: '', gestellt: 'warn', versendet: 'warn', angenommen: 'ok', abgelehnt: 'bad', bezahlt: 'ok', storniert: 'bad' };
export const belegPill = (z) => h('span', { class: 'pill ' + (z.ueberfaellig ? 'bad' : BELEG_ST[z.status] || '') }, z.ueberfaellig ? 'überfällig' : z.status);
export const belegArt = (z) => z.storno_von ? 'Storno' : z.art === 'rechnung' ? 'Rechnung' : 'Angebot';
export const eurIn = (v) => { const n = Math.round(parseFloat(String(v).replace(/\./g, '').replace(',', '.')) * 100); return Number.isFinite(n) ? n : 0; };
export const eurOut = (c) => (c / 100).toFixed(2).replace('.', ',');

/**
 * Zahlungserinnerungen und Mahnungen: zeigt zu jeder überfälligen Rechnung die nächste Stufe mit fertigem Mailtext.
 * Nichts wird automatisch verschickt: Du prüfst und bearbeitest den Text, dann sendest du die Ausgewählten.
 * @param {string[]} [nurIds] nur diese Rechnungen anzeigen
 * @param {string} [fokus] diese Rechnung vormarkieren und nach oben stellen
 */
export async function erinnerungsDialog(nurIds, fokus) {
  const inhalt = h('div', {}, h('p', { class: 'small muted' }, 'Lade …')), d = dialog('Zahlungserinnerungen prüfen', inhalt, true);
  try {
    let liste = await api('/api/admin/mahnvorschlaege');
    if (nurIds && nurIds.length) liste = liste.filter(z => nurIds.includes(z.id));
    if (fokus) liste.sort((a, b) => Number(b.id === fokus) - Number(a.id === fokus));
    const m = h('div'), zeilen = [];
    const senden = async () => {
      const eintraege = zeilen.filter(z => z.cb.checked).map(z => ({ id: z.v.id, stufe: z.v.stufe, text: z.text.value }));
      if (!eintraege.length) { melde(m, 'Bitte mindestens eine Rechnung auswählen.'); return; }
      if (!confirm(eintraege.length + ' Mail(s) mit PDF-Anhang jetzt an die Kunden senden?')) return;
      try {
        const r = await api('/api/admin/mahnungen/senden', { method: 'POST', body: { eintraege } });
        const fehlerListe = r.ergebnis.filter(x => !x.gesendet);
        m.replaceChildren(h('div', { class: 'msg ' + (fehlerListe.length ? 'err' : 'ok') }, r.gesendet + ' von ' + eintraege.length + ' verschickt.' + (fehlerListe.length ? ' Nicht verschickt: ' + fehlerListe.map(x => (liste.find(v => v.id === x.id) || {}).nummer + ' (' + x.grund + ')').join('; ') : '')));
        if (r.gesendet) setTimeout(() => { d.zu(); if (location.hash.startsWith('#belege') || location.hash.startsWith('#uebersicht') || location.hash === '#meintag') location.reload(); }, 1600);
      } catch (x) { fehler(m, x); }
    };
    inhalt.replaceChildren(
      h('p', { class: 'small muted' }, 'Es wird nichts automatisch verschickt. Prüfe die Texte, ändere sie bei Bedarf und sende dann die ausgewählten Mails. Die PDF der jeweiligen Stufe hängt automatisch an.'),
      ...(liste.length ? liste.map(v => {
        const text = h('textarea', { rows: 9, 'aria-label': 'Mailtext ' + v.nummer, hidden: true }, v.text || '');
        const cb = h('input', { type: 'checkbox', style: 'width:auto', checked: v.moeglich && !v.warnung && (!fokus || v.id === fokus), disabled: !v.moeglich, 'aria-label': 'Rechnung ' + v.nummer + ' auswählen' });
        zeilen.push({ v, cb, text });
        return h('div', { class: 'mahnzeile' + (v.moeglich ? '' : ' aus') },
          h('div', { class: 'kopfz' }, cb, h('div', { class: 'grow' }, h('b', {}, v.firma), ' ', h('span', { class: 'small muted' }, v.nummer + ' · ' + euro(v.brutto_cent) + ' · seit ' + v.tage + ' Tagen überfällig')),
            v.stufe ? h('span', { class: 'pill warn' }, v.titel) : h('span', { class: 'pill bad' }, 'nicht möglich'),
            v.moeglich ? knopf('Text ansehen / ändern', () => { text.hidden = !text.hidden; }, 'sec') : ''),
          v.warnung ? h('div', { class: 'small', style: 'color:var(--warnfg);margin-top:4px' }, '⚠ ' + v.warnung) : '', !v.moeglich ? h('div', { class: 'small muted', style: 'margin-top:4px' }, v.grund) : '',
          v.moeglich ? h('div', { class: 'small muted', style: 'margin-top:4px' }, 'An: ' + v.email + ' · Betreff: ' + v.betreff) : '', text);
      }) : [h('p', { class: 'muted' }, 'Keine überfälligen Rechnungen. Alles bezahlt oder noch nicht fällig. ✅')]),
      m, liste.length ? h('p', {}, knopf('Ausgewählte senden', senden, 'btn')) : '');
  } catch (x) { inhalt.replaceChildren(h('div', { class: 'msg err' }, x.message)); }
}

export async function abgleichKarte() {
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
  const leiste = h('div', { class: 'sammelleiste', hidden: true });
  const sel = auswahl((g) => {
    leiste.hidden = !g.size;
    const ausgewaehlt = d.belege.filter(z => g.has(z.id));
    leiste.replaceChildren(h('b', {}, g.size + ' ausgewählt'),
      knopf('Erinnerungen dazu prüfen', () => erinnerungsDialog([...g]), 'sec'),
      knopf('Auswahl als CSV', () => csvLaden('belege-auswahl.csv', ['Nummer', 'Art', 'Kunde', 'Betreff', 'Datum', 'Fällig', 'Brutto (EUR)', 'Status'], ausgewaehlt.map(z => [z.nummer || 'Entwurf', belegArt(z), z.kundennummer + ' ' + z.firma, z.betreff, z.datum, z.faellig_am, (z.brutto_cent / 100).toFixed(2).replace('.', ','), z.status])), 'sec'),
      knopf('Auswahl aufheben', () => sel.leeren(), 'sec'));
  });
  if (q.get('erinnerung')) setTimeout(() => erinnerungsDialog(), 200);
  return h('div', { class: 'stack' }, kopf('Angebote & Rechnungen', knopf('+ Angebot an Neukunden', () => neukundenAngebot(), 'btn'), s.ueberfaellig_n ? knopf('Zahlungserinnerungen prüfen (' + s.ueberfaellig_n + ')', () => erinnerungsDialog(), 'btn') : ''),
    h('p', { class: 'small' }, h('a', { href: '/api/admin/belege-export.csv', target: '_blank', rel: 'noopener' }, 'Rechnungen als CSV exportieren (Buchhaltung/sevDesk)')),
    await abgleichKarte(),
    await sicher(lastschriftKarte),
    h('div', { class: 'grid3' },
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Offen'), h('b', {}, euro(s.offen))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Überfällig (' + s.ueberfaellig_n + ')'), h('b', {}, euro(s.ueberfaellig))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Bezahlt diesen Monat'), h('b', {}, euro(s.bezahlt_monat)))),
    h('div', { class: 'card' }, await filterKarte('belege'), h('div', { class: 'tabs' }, f('', '', 'Alle'), f('rechnung', '', 'Rechnungen'), f('angebot', '', 'Angebote'), f('rechnung', 'gestellt', 'Offen'), f('rechnung', 'bezahlt', 'Bezahlt'), f('', 'entwurf', 'Entwürfe')),
      leiste, tabelle([[sel.alle, z => sel.haken(z.id)], ['Nr.', z => h('a', { href: z.kunden_id ? '#beleg/' + z.id : '#lead/' + z.lead_id }, z.nummer || 'Entwurf')], ['Art', belegArt], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Betreff', z => z.betreff], ['Datum', z => datum(z.datum)], ['Fällig/gültig bis', z => datum(z.faellig_am)], ['Betrag', z => fmtEuro(z.brutto_cent)], ['Status', belegPill]], d.belege, 'Noch keine Belege. Anlegen im jeweiligen Kunden.')),
    h('p', { class: 'small muted' }, 'Hinweis: Rechnungen werden hier als PDF erstellt. Ab 2027/2028 gelten für Rechnungen zwischen Unternehmen schrittweise Pflichten zur E-Rechnung (z. B. ZUGFeRD/XRechnung). Das ist hier noch nicht umgesetzt; bitte mit der Steuerberatung abstimmen.'));
};

export async function belegEditor(id, kid, art) {
  let b, k, vorschlag = [];
  if (id) { const r = await api('/api/admin/belege/' + id); b = r.beleg; k = r.kunde; if (!k && b.lead_id) { location.hash = '#lead/' + b.lead_id; return h('div'); } }
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

export async function belegeKarte(kid, referenz) {
  const liste = await api('/api/admin/kunden/' + kid + '/belege');
  return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { class: 'grow', style: 'margin:0' }, 'Angebote & Rechnungen'),
    h('a', { class: 'btn sec small', href: '#neubeleg/' + kid + '/angebot' }, '+ Angebot'), referenz ? '' : h('a', { class: 'btn small', href: '#neubeleg/' + kid + '/rechnung' }, '+ Rechnung')),
    tabelle([['Nr.', z => h('a', { href: '#beleg/' + z.id }, z.nummer || 'Entwurf')], ['Art', belegArt], ['Betreff', z => z.betreff], ['Datum', z => datum(z.datum)], ['Betrag', z => fmtEuro(z.brutto_cent)], ['Status', belegPill]], liste, referenz ? 'Referenzkunde: keine Rechnungen, Angebote sind möglich.' : 'Noch keine Belege.'));
}

