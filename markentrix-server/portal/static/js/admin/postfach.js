import { h, api, datum, zeit, groesse, melde } from '../common.js';
import { V, kopf, tabelle, zeige } from './kern.js';

export const STATI = ['onboarding', 'aktiv', 'pausiert', 'gekuendigt', 'beendet'];
export const DATEN_TABS = [['anfragen', 'Anfragen'], ['termine', 'Termine'], ['kontakte', 'Kontakte'], ['angebote', 'Angebote'], ['vertraege', 'Verträge'], ['projekte', 'Projekte'], ['berichte', 'Berichte'], ['wochenangebote_uploads', 'Uploads'], ['chat_verlauf', 'Chat']];

// ------------------------------------------------------------- Nachrichten (Postfach)
export const T_ART = { frage: 'Frage', auftrag: 'Auftrag', aenderung: 'Änderungswunsch', problem: 'Problem', modul: 'Zusatzmodul' };
export const T_ST = ['offen', 'in_arbeit', 'wartet_auf_kunde', 'erledigt'];
export const T_ST_TXT = { offen: 'offen', in_arbeit: 'in Arbeit', wartet_auf_kunde: 'wartet auf Kunde', erledigt: 'erledigt' };
export const tPill = (st) => h('span', { class: 'pill ' + (st === 'erledigt' ? 'ok' : st === 'offen' ? 'warn' : '') }, T_ST_TXT[st] || st);
export const dateiLink = (d) => h('a', { class: 'dateilink', href: '/api/admin/dateien/' + d.id, target: '_blank', rel: 'noopener' }, '📎 ' + d.name + ' (' + groesse(d.groesse) + ')');

V.postfach = async (param) => {
  if (param && param.startsWith('neu')) return ticketNeu(param.split('/')[1]);
  if (param) return ticketDetail(param);
  const f = new URLSearchParams((location.hash.split('?')[1] || '')), status = f.get('status') || 'offene';
  const liste = await api('/api/admin/tickets?status=' + status);
  const tab = (st, t) => h('a', { href: '#postfach?status=' + st, class: 'tab' + (status === st ? ' on' : '') }, t);
  const kunden = await api('/api/admin/kunden');
  const wahl = h('select', { style: 'width:auto;min-width:220px' }, h('option', { value: '' }, 'Neue Nachricht an …'), kunden.filter(k => !['beendet', 'gekuendigt'].includes(k.status)).map(k => h('option', { value: k.id }, k.firma + ' (' + k.kundennummer + ')')));
  wahl.onchange = () => { if (wahl.value) location.hash = '#postfach/neu/' + wahl.value; };
  return h('div', {}, kopf('Nachrichten', wahl), h('div', { class: 'tabs' }, tab('offene', 'Offen'), tab('offen', 'Neu'), tab('in_arbeit', 'In Arbeit'), tab('wartet_auf_kunde', 'Wartet auf Kunde'), tab('erledigt', 'Erledigt'), tab('', 'Alle')),
    h('div', { class: 'card' }, tabelle([['Nr.', z => h('a', { href: '#postfach/' + z.id }, z.nr)], ['Kunde', z => h('a', { href: '#kunde/' + z.kunden_id }, z.firma)], ['Betreff', z => h('a', { href: '#postfach/' + z.id }, (z.team_ungelesen ? '● ' : '') + z.betreff)],
      ['Art', z => T_ART[z.art] || z.art], ['Prio', z => z.prioritaet === 'hoch' ? h('span', { class: 'pill bad' }, 'hoch') : ''], ['Status', z => tPill(z.status)], ['Fällig', z => z.faellig_am ? datum(z.faellig_am) : ''], ['Zuletzt', z => zeit(z.geaendert_am)]], liste, 'Keine Nachrichten in dieser Ansicht.')));
};

// Chat-Gefühl: alle 12 Sekunden prüfen, ob neue Nachrichten da sind; neu laden nur, wenn gerade nichts getippt wird
export function chatAktuell(url, anzahl, feld) {
  const hash = location.hash;
  const iv = setInterval(async () => {
    if (location.hash !== hash) return clearInterval(iv);
    if (document.hidden) return;
    try { const t = await api(url); if (t.nachrichten.length !== anzahl && !feld.value.trim()) { clearInterval(iv); location.reload(); } } catch (e) { /* nächster Versuch */ }
  }, 12000);
}

export async function ticketDetail(id) {
  const t = await api('/api/admin/tickets/' + id), m = h('div');
  const bubbles = t.nachrichten.map(n => h('div', { class: 'bub ' + (n.intern ? 'intern' : n.von === 'kunde' ? 'kunde' : 'team') }, h('div', { class: 'small wer' }, (n.intern ? 'Interne Notiz · ' : '') + (n.autor_name || (n.von === 'kunde' ? 'Kunde' : 'Team')) + ' · ' + zeit(n.erstellt_am)), n.text));
  const text = h('textarea', { rows: 5, maxlength: 10000, placeholder: 'Antwort an den Kunden …' });
  chatAktuell('/api/admin/tickets/' + id, t.nachrichten.length, text);
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

export async function ticketNeu(kid) {
  const m = h('div'), betreff = h('input', { required: true, maxlength: 200 }), text = h('textarea', { rows: 5, maxlength: 10000 });
  const art = h('select', {}, ['auftrag', 'frage', 'aenderung', 'problem'].map(x => h('option', { value: x }, T_ART[x])));
  return h('div', { class: 'stack' }, kopf('Nachricht an Kunden', h('a', { class: 'btn sec small', href: '#kunde/' + kid }, '← Zurück')),
    h('div', { class: 'card' }, m, h('label', {}, 'Betreff'), betreff, h('label', {}, 'Art'), art, h('label', {}, 'Nachricht an den Kunden'), text,
      h('p', {}, h('button', { class: 'btn', onclick: async () => { try { const r = await api('/api/admin/kunden/' + kid + '/tickets', { method: 'POST', body: { betreff: betreff.value, art: art.value, text: text.value } }); location.hash = '#postfach/' + r.id; } catch (x) { melde(m, x.message); } } }, 'Senden'))));
}

// ------------------------------------------------------------- Freigaben
export const F_ART = { social: 'Social Media', text: 'Text', angebot: 'Angebot', design: 'Design', website: 'Website', sonstiges: 'Sonstiges' };
export const fPill = (st) => h('span', { class: 'pill ' + (st === 'freigegeben' ? 'ok' : st === 'abgelehnt' ? 'bad' : st === 'wartet' ? 'warn' : '') }, st === 'abgelehnt' ? 'Änderung gewünscht' : st === 'wartet' ? 'wartet' : st);

export async function freigabeNeuKarte(kid) {
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

export async function freigabenKundeKarte(kid, k) {
  const alle = await api('/api/admin/freigaben-kunden'), liste = alle.filter(z => z.kunden_id === kid);
  return h('div', { class: 'stack' }, await freigabeNeuKarte(kid), liste.length ? h('div', { class: 'card' }, h('h3', {}, 'Bisherige Freigaben'), tabelle([['Titel', z => z.titel], ['Status', z => fPill(z.status)], ['Angefragt', z => zeit(z.angefragt_am)], ['Entscheidung', z => z.entschieden_am ? zeit(z.entschieden_am) + ' · ' + (z.entschieden_name || '') + (z.kommentar ? ' · „' + z.kommentar + '“' : '') : '']], liste)) : '');
}

// ------------------------------------------------------------- Dokumente pro Kunde
export async function unterlagenKarte(kid) {
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

export async function nachrichtenKundeKarte(kid, k) {
  const liste = await api('/api/admin/tickets?kunde=' + encodeURIComponent(k.kundennummer));
  return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { style: 'margin:0' }, 'Nachrichten'), h('span', { class: 'grow' }), h('a', { class: 'btn small', href: '#postfach/neu/' + kid }, 'Neue Nachricht / Auftrag')),
    tabelle([['Nr.', z => h('a', { href: '#postfach/' + z.id }, z.nr)], ['Betreff', z => (z.team_ungelesen ? '● ' : '') + z.betreff], ['Status', z => tPill(z.status)], ['Zuletzt', z => zeit(z.geaendert_am)]], liste, 'Noch keine Nachrichten.'));
}

