import { leistungstextKarte } from './angebotsplus.js';
import { h, api, datum, zeit, euro, melde, formular } from '../common.js';
import { V, bestaetigt, cent, feld, fmtEuro, knopf, kopf, pill, tabelle } from './kern.js';

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


// ---------------------------------------------------------------- Preise und Konditionen
V.preise = async () => {
  const d = await api('/api/admin/preise'), m = h('div'), mk = h('div'), mr = h('div');
  const heute = new Date().toISOString().slice(0, 10);
  const pform = h('form', { onsubmit: (e) => { e.preventDefault(); const o = formular(e.target);
    const body = { produkt_code: o.produkt_code, gueltig_ab: o.gueltig_ab, einrichtung_cent: cent(o.einrichtung), monatlich_cent: cent(o.monatlich), projekt_cent: cent(o.projekt), ab_preis: !!e.target.ab.checked };
    bestaetigt(m, () => api('/api/admin/preise', { method: 'POST', body }), 'Neuer Preis gespeichert. Bestehende Buchungen behalten ihren Preis.'); } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Produkt'), h('select', { name: 'produkt_code' }, d.aktuell.map(p => h('option', { value: p.code }, p.name + ' (' + p.code + ')')))),
      feld('Gültig ab', 'gueltig_ab', heute, { type: 'date', required: true }), feld('Einrichtung in €', 'einrichtung', '', { type: 'number', step: '0.01', min: '0' }), feld('Monatlich in €', 'monatlich', '', { type: 'number', step: '0.01', min: '0' }), feld('Projekt in €', 'projekt', '', { type: 'number', step: '0.01', min: '0' })),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', name: 'ab', style: 'width:auto' }), '„ab"-Preis'),
    h('p', {}, h('button', { class: 'btn' }, 'Neuen Preis anlegen')));
  const kond = (z) => { const i = h('input', { value: z.wert_zahl ?? z.wert_text ?? '' }); return h('div', { class: 'row' }, h('div', { class: 'grow' }, i),
    knopf('Speichern', () => { const v = i.value.trim(); const body = /^-?\d+$/.test(v) ? { wert_zahl: Number(v) } : { wert_text: v }; bestaetigt(mk, () => api('/api/admin/konditionen/' + encodeURIComponent(z.schluessel), { method: 'PUT', body })); })); };
  const regelBtn = (z) => z.status === 'entwurf' ? knopf('Freigeben', () => confirm('Regel "' + z.name + '" (' + z.prozent + ' %) freigeben?') && bestaetigt(mr, () => api('/api/admin/provisionsregeln/' + z.id + '/freigeben', { method: 'POST' }), 'Freigegeben.')) : '';
  const lt = await leistungstextKarte().catch(() => '');
  return h('div', { class: 'stack' }, kopf('Preise & Konditionen'), m,
    h('div', { class: 'card' }, h('h2', {}, 'Aktuelle Preise'), tabelle([['Produkt', z => z.name], ['Einrichtung', z => (z.ab_preis ? 'ab ' : '') + fmtEuro(z.einrichtung_cent)], ['Monatlich', z => fmtEuro(z.monatlich_cent)], ['Projekt', z => fmtEuro(z.projekt_cent)], ['Gültig ab', z => datum(z.gueltig_ab)]], d.aktuell)),
    h('div', { class: 'card' }, h('h2', {}, 'Preis ändern (neue Version)'), h('p', { class: 'small muted' }, 'Alte Preise bleiben im Verlauf. Bestehende Buchungen behalten den Preis, der bei der Buchung galt.'), pform), lt,
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
  const vs = await api('/api/admin/vertragsstand').catch(() => null);
  const stand = vs ? h('div', { class: 'card' }, h('h2', {}, 'Stand der AVV-Zusagen ', h('span', { class: 'pill ' + ({ ok: 'ok', warn: 'warn', bad: 'bad' }[vs.gesamt] || '') }, vs.gesamt === 'ok' ? 'alles eingehalten' : vs.gesamt === 'bad' ? 'Handlungsbedarf' : vs.gesamt === 'warn' ? 'bitte prüfen' : 'teils unbekannt')),
    h('p', { class: 'small muted' }, 'Zeigt, ob das, was im Vertrag steht (Anlage 2), im Betrieb gerade stimmt. Als Nachweis bei Rückfragen von Kunden.'),
    tabelle([['', z => h('span', { class: 'pill ' + ({ ok: 'ok', warn: 'warn', bad: 'bad' }[z.status] || '') }, { ok: 'ok', warn: 'prüfen', bad: 'Problem', unbekannt: '?' }[z.status])], ['Punkt', z => z.titel], ['Stand', z => z.detail]], vs.punkte)) : '';
  return h('div', { class: 'stack' }, kopf('Datenschutz & Qualität', h('span', { class: 'pill ' + (offen ? 'warn' : 'ok') }, offen ? offen + ' offen' : 'alles erledigt')), stand, m,
    sektion('Alarme', d.alarme, [['Zeit', z => zeit(z.zeit)], ['Stufe', z => stufe(z.stufe)], ['Quelle', z => z.quelle], ['Titel', z => z.titel], ['', z => knopf('Bestätigen', () => tun(() => post('/alarme/' + z.id + '/bestaetigen')))]], 'Keine offenen Alarme.'),
    sektion('Freigaben (Agenten)', d.freigaben, [['Eingang', z => zeit(z.erstellt_am)], ['Kunde', z => z.kundennummer || ''], ['Art', z => z.art], ['Vorschau', z => z.vorschau], ['', entscheid('freigaben', 'Freigeben', 'freigegeben', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Freigaben.'),
    sektion('Änderungsfreigaben', d.aenderungen, [['Seit', z => datum(z.beantragt_am)], ['Art', z => z.art], ['Gegenstand', z => z.gegenstand], ['Beschreibung', z => z.beschreibung], ['Von', z => z.beantragt_von], ['', entscheid('aenderungsfreigaben', 'Freigeben', 'freigegeben', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Anträge.'),
    sektion('Auskunfts- und Löschanfragen (DSGVO)', d.auskunft, [['Eingang', z => datum(z.eingang_am)], ['Frist', z => datum(z.frist_bis)], ['Art', z => z.art], ['Person', z => z.person_ref], ['Status', z => pill(z.status)], ['', entscheid('auskunftsanfragen', 'Erledigt', 'erledigt', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Anfragen.'),
    sektion('Workflow-Fehler', d.workflow_fehler, [['Zeit', z => zeit(z.zeit)], ['Workflow', z => z.workflow_name], ['Knoten', z => z.knoten], ['Fehler', z => z.fehlertext], ['', z => knopf('Behoben', () => tun(() => post('/workflow-fehler/' + z.id + '/behoben')))]], 'Keine offenen Fehler.'),
    sektion('Befunde (Qualität)', d.befunde, [['Gefunden', z => datum(z.gefunden_am)], ['Schwere', z => stufe(z.schwere === 'kritisch' ? 'kritisch' : z.schwere === 'wesentlich' ? 'warnung' : 'info')], ['Titel', z => z.titel], ['Status', z => pill(z.status)], ['', entscheid('befunde', 'Behoben', 'behoben', '', '')]], 'Keine offenen Befunde.'),
    sektion('Maßnahmen', d.massnahmen, [['Fällig', z => datum(z.faellig_am)], ['Maßnahme', z => z.beschreibung], ['Verantwortlich', z => z.verantwortlich], ['Status', z => pill(z.status)], ['', entscheid('massnahmen', 'Umgesetzt', 'umgesetzt', '', '')]], 'Keine offenen Maßnahmen.'));
};

/** Nutzungsmessung: welche Seiten werden gebraucht, wer ist aktiv. Nur Seitennamen und Zähler, keine Inhalte. */
const ALLE_SEITEN = { kunde: 'heute uebersicht status briefing nachrichten freigaben assistent anfragen termine bewertungen kontakte dokumente unterlagen auswertung berichte belege anrufe website wochenangebote werbung automationen avv team hilfe einstellungen'.split(' '),
  vertrieb: 'heute uebersicht leads pipeline angebote leitfaden kunden provisionen konto'.split(' ') };
const ROLLE = { kunde: 'Kunden', vertrieb: 'Vertriebler', admin: 'Admin' };
async function nutzungsKarte() {
  const d = await api('/api/admin/nutzung?tage=30');
  const tageGemessen = d.messung_seit ? Math.floor((Date.now() - new Date(d.messung_seit).getTime()) / 864e5) : 0, genug = tageGemessen >= 14;
  const block = (rolle) => {
    const z = d.seiten.filter(x => x.rolle === rolle), max = Math.max(1, ...z.map(x => x.aufrufe)), selten = z.filter(x => x.aufrufe < 3), nie = (ALLE_SEITEN[rolle] || []).filter(sid => !z.some(x => x.seite === sid));
    return h('div', { style: 'margin:10px 0' }, h('h3', {}, ROLLE[rolle] + ': ' + (d.aktiv[rolle] || 0) + ' von ' + (d.konten[rolle] || 0) + ' Konten aktiv (7 Tage: ' + (d.aktiv_7_tage[rolle] || 0) + ')'),
      z.length ? h('div', { class: 'dtrichter' }, z.slice(0, 8).map(x => h('div', { class: 'tstufe' }, h('span', { class: 'tname' }, x.seite), h('div', { class: 'tbalken' }, h('div', { style: 'height:100%;border-radius:10px;background:var(--grad);width:' + Math.max(3, Math.round(x.aufrufe / max * 100)) + '%' })), h('span', { class: 'tzahl' }, x.aufrufe)))) : h('p', { class: 'small muted' }, 'Noch keine Aufrufe.'),
      !genug ? '' : [nie.length ? h('p', { class: 'small' }, h('b', {}, 'Nie geöffnet (30 Tage): '), nie.join(', '), h('span', { class: 'muted' }, ' – Kandidaten zum Ausblenden oder Entfernen.')) : '',
        selten.length ? h('p', { class: 'small muted' }, 'Selten (unter 3 Aufrufe): ' + selten.map(x => x.seite).join(', ')) : ''] );
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Nutzung (30 Tage)'),
    h('p', { class: 'small muted' }, 'Gezählt werden nur Seitenname, Tag und Rolle, dazu wer an einem Tag aktiv war. Keine Inhalte, nach 180 Tagen gelöscht. ' + (d.messung_seit ? 'Messung seit ' + datum(d.messung_seit) + '.' : 'Die Messung beginnt mit dem ersten Aufruf.')),
    genug ? '' : h('p', { class: 'msg info' }, 'Die Messung läuft erst seit ' + tageGemessen + ' Tagen. Aussagen zu ungenutzten Seiten gibt es ab 14 Tagen, vorher wäre das Zufall.'),
    d.tour.alle ? h('p', { class: 'small' }, 'Erststart-Tour gesehen: ' + d.tour.gesehen + ' von ' + d.tour.alle + ' Kundenkonten.') : '',
    ['kunde', 'vertrieb', 'admin'].map(block));
}

V.protokoll = async () => {
  const d = await api('/api/admin/audit');
  return h('div', {}, kopf('Protokoll'), await nutzungsKarte().catch(() => ''), h('div', { class: 'card' }, tabelle([['Zeit', z => zeit(z.zeit)], ['Benutzer', z => z.email || 'System'], ['Kunde', z => z.kundennummer || ''], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d)));
};

