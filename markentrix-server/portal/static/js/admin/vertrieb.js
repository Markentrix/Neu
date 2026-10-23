import { angebotDialog, leadAngebotKarte } from './leadangebot.js';
import { steuerungKarte, zuKundeDialog } from './leadsteuerung.js';
import { qrKarte } from '../anleitung.js';
import { einarbeitungKarte, handelsvertreterKarte } from './vertraege.js';
import { kontaktKarte, skriptKarte, h, api, datum, zeit, melde, formular, dialog } from '../common.js';
import { filterKarte, V, bestaetigt, bestaetigtOhneReload, fehler, feld, fmtEuro, knopf, kopf, leerzu, mailHinweis, pill, select, tabelle } from './kern.js';

// ---------------------------------------------------------------- Vertriebler
V.vertrieb = async () => {
  const d = await api('/api/admin/vertrieb/partner');
  const m = h('div');
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = leerzu(formular(e.target));
    o.einladen = e.target.einladen.checked;
    try { const r = await api('/api/admin/vertrieb/partner', { method: 'POST', body: o }); melde(m, r.mail ? (r.mail.gesendet ? 'Vertriebler angelegt, Einladung per E-Mail gesendet.' : 'Vertriebler angelegt. Mail nicht gesendet (' + r.mail.grund + '). Einladungslink: ' + r.einladungslink) : 'Vertriebler angelegt.', r.mail && !r.mail.gesendet ? 'info' : 'ok'); setTimeout(() => location.reload(), r.mail && !r.mail.gesendet ? 15000 : 1800); } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' }, feld('Name *', 'name', '', { required: true }), feld('Firma', 'firma'), feld('E-Mail', 'email', '', { type: 'email' }), feld('Telefon', 'telefon'),
      h('div', {}, h('label', {}, 'Status'), select('status', ['aktiv', 'anfrage', 'pausiert', 'beendet'], 'aktiv'))),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:8px 0' }, h('input', { type: 'checkbox', name: 'einladen', style: 'width:auto', checked: true }), 'Gleich eine Einladung zum Vertriebsportal per E-Mail senden (E-Mail-Adresse nötig)'),
    h('p', {}, h('button', { class: 'btn' }, 'Vertriebler anlegen')));
  const zugangZelle = (z) => h('div', {}, h('span', { class: 'pill ' + (z.zugang === 'aktiv' ? 'ok' : z.zugang === 'keiner' ? '' : 'warn') }, { aktiv: 'Zugang aktiv', eingeladen: 'eingeladen', abgelaufen: 'Einladung abgelaufen', keiner: 'kein Zugang' }[z.zugang] || z.zugang),
    z.zugang === 'aktiv' ? '' : h('div', { style: 'margin-top:4px' }, knopf(z.zugang === 'keiner' ? 'Einladung senden' : 'Erneut einladen', async () => {
      let mail = z.email; if (!mail) mail = prompt('E-Mail-Adresse von ' + z.name + ':'); if (!mail) return;
      try { const r = await api('/api/admin/vertrieb/partner/' + z.id + '/einladung', { method: 'POST', body: { email: mail, per_mail: true } });
        const ok = r.mail && r.mail.gesendet; melde(m, ok ? 'Einladung an ' + mail + ' gesendet.' : 'Nicht per Mail gesendet (' + (r.mail ? r.mail.grund : '') + '). Link: ' + r.einladungslink, ok ? 'ok' : 'info'); setTimeout(() => location.reload(), ok ? 1800 : 15000); } catch (x) { fehler(m, x); } }, 'small')));
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
    h('div', { class: 'card' }, tabelle([['Name', z => h('a', { href: '#partner/' + z.id }, z.name)], ['Firma', z => z.firma], ['Status', z => pill(z.status)], ['Portal-Zugang', zugangZelle], ['Kunden', z => z.kunden], ['Offene Leads', z => z.offene_leads], ['Provision offen', z => fmtEuro(z.offen_cent)], ['IBAN', z => z.iban_hinterlegt ? 'ja' : 'nein']], d, 'Noch keine Vertriebler.')),
    berechnen, h('div', { class: 'card' }, h('h2', {}, 'Neuer Vertriebler'), m, f));
};

export function abrechnungsZeile(pid, liste, mp) {
  const monate = [...new Set(liste.map(z => String(z.monat).slice(0, 7)))];
  if (!monate.length) return h('span');
  const sel = h('select', {}, ...monate.map(x => h('option', { value: x }, x)));
  return h('div', { class: 'row', style: 'margin-top:10px' }, h('span', { class: 'small muted' }, 'Abrechnung als PDF:'), sel,
    knopf('Öffnen', () => window.open('/api/admin/vertrieb/' + pid + '/abrechnung/' + sel.value, '_blank', 'noopener')),
    knopf('Verlängerung erfassen', async () => { const bid = prompt('Buchungs-ID der verlängerten Buchung (steht in der Kundenakte):'); if (!bid) return; const mon = prompt('Abrechnungsmonat (JJJJ-MM)', sel.value);
      if (mon) bestaetigt(mp, () => api('/api/admin/vertrieb/provisionen/verlaengerung', { method: 'POST', body: { buchung_id: bid.trim(), monat: mon } })); }));
}

/** Aktivität eines Vertrieblers: Tagesbalken, Summen, letzte Einträge. */
async function aktivitaetKarte(pid) {
  const box = h('div', { class: 'card' });
  const lade = async (tage) => {
    const d = await api('/api/admin/vertrieb/partner/' + pid + '/aktivitaet?tage=' + tage), s = d.summe;
    const max = Math.max(1, ...d.verlauf.map(v => Number(v.anrufe) + Number(v.termine) + Number(v.notizen) + Number(v.mails)));
    const ART = { anruf: 'Anruf', termin: 'Termin', notiz: 'Notiz', mail_gesendet: 'Mail', antwort: 'Antwort' };
    const kachel = (t, w) => h('div', { class: 'card stat', style: 'margin:0' }, h('span', { class: 'muted small' }, t), h('b', {}, String(w)));
    box.replaceChildren(h('h2', {}, 'Aktivität'),
      h('div', { class: 'row', role: 'group', 'aria-label': 'Zeitraum' }, [7, 30, 90].map(t => h('button', { class: 'btn small' + (t === d.tage ? '' : ' sec'), 'aria-pressed': String(t === d.tage), onclick: () => lade(t) }, t + ' Tage'))),
      h('div', { class: 'stats', style: 'display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:12px 0' },
        kachel('Leads bearbeitet', s.leads_bearbeitet), kachel('Anrufe (erreicht)', s.anrufe + ' (' + s.erreicht + ')'), kachel('Termine', s.termine), kachel('Notizen', s.notizen), kachel('Aktive Tage', s.aktive_tage + ' von ' + d.tage),
        kachel('Neue Leads', s.neue_leads), kachel('Neue Kunden', s.neue_kunden), kachel('Offene Leads', s.offene_leads)),
      h('div', { role: 'img', 'aria-label': 'Tägliche Aktivität der letzten ' + d.tage + ' Tage', style: 'display:flex;align-items:flex-end;gap:2px;height:80px;margin:8px 0' },
        d.verlauf.map(v => { const n = Number(v.anrufe) + Number(v.termine) + Number(v.notizen) + Number(v.mails); return h('div', { title: datum(v.tag) + ': ' + v.anrufe + ' Anrufe, ' + v.termine + ' Termine, ' + v.notizen + ' Notizen', style: 'flex:1;min-width:2px;background:' + (n ? 'var(--primary,#8B5CF6)' : 'var(--border,#ddd)') + ';height:' + (n ? Math.max(6, Math.round(n / max * 80)) : 2) + 'px;border-radius:2px' }); })),
      h('p', { class: 'small muted' }, 'Gezählt wird, was der Vertriebler im Portal festgehalten hat. Was nicht eingetragen ist, taucht hier nicht auf.'),
      d.letzte.length ? tabelle([['Wann', z => zeit(z.zeit)], ['Art', z => ART[z.art] || z.art], ['Lead', z => h('a', { href: '#lead/' + z.lead_id }, z.firma)], ['Inhalt', z => z.inhalt]], d.letzte) : h('p', { class: 'small muted' }, 'Noch keine Einträge.'));
  };
  try { await lade(30); } catch (x) { box.replaceChildren(h('h2', {}, 'Aktivität'), h('div', { class: 'msg err' }, x.message)); }
  return box;
}

export async function partnerDetail(pid) {
  const d = await api('/api/admin/vertrieb/partner/' + pid), p = d.partner, m = h('div'), mp = h('div');
  const stamm = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); o.iban_hinterlegt = e.target.iban.checked; if (!o.vereinbarung_am) delete o.vereinbarung_am; delete o.iban;
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
    h('div', { class: 'card' }, h('h2', {}, 'Stammdaten'), m, stamm), await aktivitaetKarte(pid), await handelsvertreterKarte(pid, p), await einarbeitungKarte(pid), zugang, await qrKarte('vertrieb', (p.name || '').split(' ')[0]),
    h('div', { class: 'card' }, h('h2', {}, 'Zugeordnete Kunden (' + d.kunden.length + ')'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Paket', z => z.paket || '–'], ['Status', z => pill(z.status)], ['Monatlich', z => fmtEuro(z.monatlich_cent)]], d.kunden, 'Noch keine Kunden. Zuordnung im Kunden unter Stammdaten (Feld Vertriebler).')),
    h('div', { class: 'card' }, h('h2', {}, 'Provisionen'), h('p', { class: 'small muted' }, 'Offen (berechnet/freigegeben): ' + fmtEuro(summe)), mp,
      tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Art', z => ({ laufend: 'Laufend', verlaengerung: 'Verlängerung', rueckbuchung: 'Rückbuchung' })[z.art] || z.art], ['Vertragsmonat', z => z.vertragsmonat || '–'], ['Basis', z => fmtEuro(z.basis_cent)], ['%', z => z.prozent], ['Betrag', z => fmtEuro(z.betrag_cent)], ['Status', z => pill(z.status)], ['', provAktion]], d.provisionen, 'Noch keine Provisionen berechnet.'),
      abrechnungsZeile(pid, d.provisionen, mp)),
    h('div', { class: 'card' }, h('h2', {}, 'Leads'), tabelle([['Firma', z => h('a', { href: '#lead/' + z.id }, z.firma)], ['Ort', z => z.ort], ['Status', z => pill(z.status)], ['Angelegt', z => datum(z.erstellt_am)]], d.leads, 'Keine Leads zugeordnet.')));
}

// ---------------------------------------------------------------- Leads
export const TEMPS = [['', '–'], ['kalt', '❄ Cold'], ['warm', '☀ Warm'], ['heiss', '🔥 HOT']];
export const tempWahl = (z, m) => select('t', TEMPS, z.temperatur || '', { onchange: async (e) => {
  try { await api('/api/admin/leads/' + z.id, { method: 'PATCH', body: { temperatur: e.target.value } }); z.temperatur = e.target.value; melde(m, 'Einstufung gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } });
export const leadLoeschen = (z, m, danach) => knopf('Löschen', () => confirm('Lead "' + z.firma + '" endgültig löschen (inkl. Verlauf und Website-Check)?') &&
  bestaetigt(m, async () => { await api('/api/admin/leads/' + z.id, { method: 'DELETE' }); danach(); }, 'Lead gelöscht.'), 'sec');
export const LEAD_ST = ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'gewonnen', 'verloren', 'gesperrt', 'consent_ausstehend', 'tot'];
export const PARTNER = ['anfrage', 'aktiv', 'pausiert', 'beendet'];
V.leads = async () => {
  const P = new URLSearchParams(location.hash.split('?')[1] || ''), g = (k) => P.get(k) || '';
  const filter = g('status');
  const [d, partner] = await Promise.all([api('/api/admin/leads?' + P.toString()), api('/api/admin/vertrieb/partnerliste')]);
  const m = h('div');
  const setze = (k, w) => { const n = new URLSearchParams(P); if (k !== 'seite') n.delete('seite'); if (w) n.set(k, w); else n.delete(k); const t = n.toString(); location.hash = '#leads' + (t ? '?' + t : ''); };
  const tabs = h('div', { class: 'tabs' }, h('button', { class: filter === '' ? 'on' : '', onclick: () => setze('status', '') }, 'Alle'),
    LEAD_ST.filter(s => d.zaehler[s]).map(s => h('button', { class: filter === s ? 'on' : '', onclick: () => setze('status', s) }, s.replace(/_/g, ' ') + ' (' + d.zaehler[s] + ')')));
  const fsel = (k, opt, w) => select('f_' + k, opt, w, { 'aria-label': 'Filter ' + k.replace(/_/g, ' '), onchange: (e) => setze(k, e.target.value) });
  const suche = h('input', { placeholder: 'Suchen: Firma, Ort, E-Mail, Telefon, Branche, Notiz …', value: g('q'), onkeydown: (e) => { if (e.key === 'Enter') setze('q', e.target.value.trim()); } });
  const filterLeiste = h('div', { class: 'lfilter' },
    h('div', { class: 'lsuche' }, suche, knopf('Suchen', () => setze('q', suche.value.trim()), 'small')),
    fsel('quelle', [['', 'Alle Quellen'], 'manuell', 'empfehlung', 'lead_finder', 'website', 'akquise', 'messe'], g('quelle')),
    fsel('temperatur', [['', 'Alle Einstufungen'], ['heiss', '🔥 HOT'], ['warm', '☀ Warm'], ['kalt', '❄ Cold'], ['keine', 'Ohne Einstufung']], g('temperatur')),
    fsel('vertriebler', [['', 'Alle Vertriebler'], ['keiner', 'Nicht zugeordnet'], ...partner.map(p => [p.id, p.name])], g('vertriebler')),
    d.gruppen.length ? fsel('gruppe', [['', 'Alle Branchengruppen'], ...d.gruppen.map(l => [l.gruppe, l.gruppe + ' (' + l.n + ')'])], g('gruppe')) : '',
    d.listen.length ? fsel('liste', [['', 'Alle Importlisten'], ...d.listen.map(l => [l.liste, l.liste.replace(/^.* · /, '') + ' (' + l.n + ')'])], g('liste')) : '',
    ['status', 'q', 'quelle', 'temperatur', 'vertriebler', 'gruppe', 'liste'].some(k => g(k)) ? knopf('Filter zurücksetzen', () => { location.hash = '#leads'; }, 'sec small') : '');
  const zuordnen = (z) => select('p', [['', '– niemand –'], ...partner.map(p => [p.id, p.name])], z.vertriebler ? (partner.find(p => p.name === z.vertriebler) || {}).id : '', { onchange: async (e) => {
    try { await api('/api/admin/leads/' + z.id, { method: 'PATCH', body: e.target.value ? { vertriebspartner_id: e.target.value } : { zuordnung_loeschen: true } }); melde(m, 'Zugeordnet.', 'ok'); } catch (x) { fehler(m, x); } } });
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = leerzu(formular(e.target));
    bestaetigt(m, () => api('/api/admin/leads', { method: 'POST', body: o }), 'Lead angelegt.'); } },
    h('div', { class: 'form2' }, feld('Firma *', 'firma', '', { required: true }), feld('Ansprechpartner', 'ansprechpartner'), feld('E-Mail', 'email'), feld('Telefon', 'telefon'), feld('Website', 'website'), feld('Branche', 'branche'), feld('PLZ', 'plz'), feld('Ort', 'ort'),
      h('div', {}, h('label', {}, 'Quelle'), select('quelle', ['manuell', 'empfehlung', 'lead_finder', 'website', 'akquise', 'messe'], 'manuell')),
      h('div', {}, h('label', {}, 'Vertriebler'), select('vertriebspartner_id', [['', '– niemand –'], ...partner.map(p => [p.id, p.name])], ''))),
    h('p', {}, h('button', { class: 'btn' }, 'Lead anlegen')));
  const gewaehlt = new Set(); let alleTreffer = false;
  const leiste = h('div', { class: 'lbulk', hidden: true });
  const filterObj = () => Object.fromEntries(['status', 'q', 'quelle', 'temperatur', 'vertriebler', 'gruppe', 'liste'].filter(k => g(k)).map(k => [k, g(k)]));
  const bulk = async (aktion, wert, text) => {
    const n = alleTreffer ? d.gesamt : gewaehlt.size;
    if (!n || !confirm(n + ' Leads: ' + text + '?')) return;
    try { const r = await api('/api/admin/leads/bulk', { method: 'POST', body: { aktion, wert, ids: alleTreffer ? null : [...gewaehlt], alle_gefilterten: alleTreffer, filter: filterObj() } }); melde(m, r.geaendert + ' Leads geändert.', 'ok'); setTimeout(() => location.reload(), 700); } catch (x) { fehler(m, x); }
  };
  const aktualisiere = () => {
    leiste.hidden = !gewaehlt.size && !alleTreffer;
    const n = alleTreffer ? d.gesamt : gewaehlt.size;
    const wahl = (name, opt, aktion, text) => select(name, [['__', text], ...opt], '__', { onchange: (e) => { const v = e.target.value; e.target.value = '__'; if (v !== '__') bulk(aktion, v, text + ' → ' + (opt.find(o => o[0] === v) || [0, v])[1]); } });
    leiste.replaceChildren(h('b', {}, n + ' ausgewählt'),
      !alleTreffer && d.gesamt > d.leads.length ? knopf('Alle ' + d.gesamt + ' Treffer des Filters auswählen', () => { alleTreffer = true; aktualisiere(); }, 'sec small') : '',
      wahl('b_t', [['', 'ohne Einstufung'], ['kalt', '❄ Cold'], ['warm', '☀ Warm'], ['heiss', '🔥 HOT']], 'temperatur', 'Einstufung setzen'),
      wahl('b_v', [['', 'niemand'], ...partner.map(p => [p.id, p.name])], 'vertriebler', 'Vertriebler zuordnen'),
      wahl('b_s', ['neu', 'kontaktiert', 'antwort', 'termin', 'angebot', 'verloren', 'tot'].map(x => [x, x]), 'status', 'Status setzen'),
      knopf('Löschen', () => bulk('loeschen', null, 'endgültig löschen (inkl. Verlauf; bereits angelegte Kunden bleiben)'), 'bad small'),
      knopf('Auswahl aufheben', () => { gewaehlt.clear(); alleTreffer = false; document.querySelectorAll('.leadtab input[type=checkbox]').forEach((/** @type {any} */ c) => { c.checked = false; }); aktualisiere(); }, 'sec small'));
  };
  const haken = (z) => h('input', { type: 'checkbox', style: 'width:auto', 'aria-label': 'Lead auswählen', onchange: (e) => { if (e.target.checked) gewaehlt.add(z.id); else { gewaehlt.delete(z.id); alleTreffer = false; } aktualisiere(); } });
  const alleHaken = h('input', { type: 'checkbox', style: 'width:auto', title: 'Alle auf dieser Seite', onchange: (e) => { document.querySelectorAll('.leadtab tbody input[type=checkbox]').forEach((/** @type {any} */ c) => { if (c.checked !== e.target.checked) c.click(); }); } });
  const heute = new Date().toISOString().slice(0, 10);
  const zeilen = d.leads.map(z => h('tr', {},
    h('td', { class: 'ck' }, haken(z)),
    h('td', {}, h('a', { href: '#lead/' + z.id, class: 'lfirma' }, z.firma), h('div', { class: 'small muted', title: 'Quelle: ' + z.quelle + (z.liste ? ' · Liste: ' + z.liste : '') }, [z.gruppe || z.branche, z.ort].filter(Boolean).join(' · '))),
    h('td', { class: 'nowrap' }, z.telefon ? h('div', {}, h('a', { href: 'tel:' + z.telefon.replace(/[^+\d]/g, '') }, z.telefon)) : '', z.email ? h('div', { class: 'small muted' }, z.email) : '', !z.telefon && !z.email ? h('span', { class: 'muted' }, '–') : ''),
    h('td', {}, tempWahl(z, m)),
    h('td', {}, pill(z.status), z.wiedervorlage_am ? h('div', { class: 'small ' + (z.wiedervorlage_am.slice(0, 10) <= heute ? 'wv-faellig' : 'muted') }, 'WV ' + datum(z.wiedervorlage_am)) : ''),
    h('td', {}, zuordnen(z)),
    h('td', { class: 'small muted nowrap' }, datum(z.erstellt_am)),
    h('td', {}, leadLoeschen(z, m, () => {}))));
  const seiten = Math.max(1, Math.ceil(d.gesamt / d.pro_seite));
  const blaettern = seiten > 1 ? h('div', { class: 'row', style: 'justify-content:center;margin-top:12px' },
    knopf('← Zurück', () => setze('seite', d.seite > 2 ? String(d.seite - 1) : ''), 'sec small'), h('span', { class: 'small muted' }, 'Seite ' + d.seite + ' von ' + seiten),
    knopf('Weiter →', () => setze('seite', String(d.seite + 1)), 'sec small')) : '';
  if (d.seite > 1 && !d.leads.length) { setze('seite', ''); }
  return h('div', { class: 'stack' }, kopf('Leads'), m, h('div', { class: 'card' }, await filterKarte('leads'), tabs, filterLeiste,
    h('p', { class: 'small muted', style: 'margin:10px 0 6px' }, d.gesamt + ' Leads' + (['status', 'q', 'quelle', 'temperatur', 'vertriebler', 'gruppe', 'liste'].some(k => g(k)) ? ' passen zum Filter' : '')), leiste,
    d.leads.length ? h('div', { class: 'tablewrap' }, h('table', { class: 'leadtab' }, h('thead', {}, h('tr', {}, h('th', { class: 'ck' }, alleHaken), ['Firma', 'Kontakt', 'Einstufung', 'Status', 'Vertriebler', 'Angelegt', ''].map(t => h('th', {}, t)))), h('tbody', {}, zeilen))) : h('p', { class: 'muted' }, 'Keine Leads.'), blaettern),
    await leadImportKarte(partner),
    await steuerungKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'Neuer Lead'), f));
};

V.auswertung = async () => {
  const [d, rg] = await Promise.all([api('/api/admin/vertrieb/auswertung'), api('/api/admin/vertrieb/rangliste-einstellung')]), rm = h('div');
  const rgA = h('input', { type: 'checkbox', checked: rg.aktiv, style: 'width:auto' }), rgN = h('input', { type: 'checkbox', checked: rg.namen, style: 'width:auto' });
  const rgKarte = h('div', { class: 'card' }, h('h2', {}, 'Rangliste im Partnerportal'), h('p', { class: 'small muted' }, 'Zeigt den Vertrieblern ihre Monatsplatzierung bei Anrufen, Terminen und Abschlüssen (Top 5 plus eigene Position). Ohne Namen heißen die anderen „Vertriebler 2“ usw.'), rm,
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, rgA, 'Rangliste einschalten'), h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, rgN, 'Vornamen der anderen zeigen'),
    h('p', {}, knopf('Speichern', async () => { try { await api('/api/admin/vertrieb/rangliste-einstellung', { method: 'PUT', body: { aktiv: rgA.checked, namen: rgN.checked } }); melde(rm, 'Gespeichert.', 'ok'); } catch (x) { fehler(rm, x); } })));
  const proz = (a, b) => b ? Math.round(a * 100 / b) + ' %' : '–';
  const tab = (titel, liste, extra = []) => h('div', { class: 'card' }, h('h2', {}, titel), tabelle([['', z => h('b', {}, z.name)], ['Leads', z => z.leads], ['Bearbeitet', z => z.bearbeitet + ' (' + proz(z.bearbeitet, z.leads) + ')'],
    ['Erreicht / Antwort', z => z.erreicht + ' (' + proz(z.erreicht, z.bearbeitet) + ')'], ['Termine', z => z.termine + ' (' + proz(z.termine, z.bearbeitet) + ')'], ['Kunden', z => h('b', {}, z.kunden)], ['Verloren', z => z.verloren], ...extra], liste, 'Noch keine Daten.'));
  const g = d.gesamt || { leads: 0, bearbeitet: 0, erreicht: 0, termine: 0, kunden: 0 };
  const stufe = (t, n, von) => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, t), h('b', {}, n), von !== undefined ? h('span', { class: 'small muted' }, proz(n, von) + ' der Vorstufe') : '');
  return h('div', { class: 'stack' }, kopf('Vertriebs-Auswertung'), rgKarte,
    h('p', { class: 'small muted' }, 'So viele Leads sind auf welcher Stufe angekommen. „Bearbeitet“ heißt: mindestens ein Kontakt festgehalten. Die Quoten zeigen, welche Liste, Branche und welcher Vertriebler wirklich Termine und Kunden bringt. Ein Lead zählt auf der höchsten Stufe, die er erreicht hat.'),
    h('div', { class: 'grid3' }, stufe('Leads', g.leads), stufe('Bearbeitet', g.bearbeitet, g.leads), stufe('Erreicht / Antwort', g.erreicht, g.bearbeitet), stufe('Termine', g.termine, g.erreicht), stufe('Kunden', g.kunden, g.termine),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Gebuchte Gespräche (kommend)'), h('b', {}, d.gebuchte_gespraeche))),
    tab('Je Vertriebler', d.je_vertriebler, [['Anrufe heute', z => z.anrufe_heute], ['Anrufe 7 Tage', z => z.anrufe_7t]]), tab('Je Importliste', d.je_liste), tab('Je Branche', d.je_gruppe), tab('Je Quelle', d.je_quelle));
};

export async function leadImportKarte(partner) {
  const m = h('div'), erg = h('div');
  const datei = h('input', { type: 'file', accept: '.xlsx,.xlsm,.csv,.txt' });
  const liste = h('input', { placeholder: 'optional, sonst der Dateiname' });
  const quelle = select('quelle', [['lead_finder', 'lead_finder (Lead-Finder / Recherche)'], 'akquise', 'messe', 'empfehlung', 'manuell'], 'lead_finder');
  const temp = select('temperatur', [['', 'ohne Einstufung'], ['kalt', 'Kalt'], ['warm', 'Warm'], ['heiss', 'Heiß']], '');
  const vt = select('vt', [['', 'niemand'], ...partner.map(p => [p.id, p.name])], '');
  let auswahl = null;
  const lesen = () => new Promise((res, rej) => { const f = datei.files[0]; if (!f) return rej(new Error('Bitte zuerst eine Excel- oder CSV-Datei wählen.')); const r = new FileReader(); r.onload = () => res([f.name, r.result]); r.onerror = () => rej(new Error('Datei nicht lesbar.')); r.readAsDataURL(f); });
  datei.addEventListener('change', () => { auswahl = null; erg.replaceChildren(); });
  const senden = async (nurPruefen) => {
    try {
      const [name, b64] = await lesen();
      const r = await api('/api/admin/leads/import', { method: 'POST', body: { datei_base64: b64, datei_name: name, liste: liste.value || null, quelle: quelle.value, temperatur: temp.value || null, vertriebspartner_id: vt.value || null, blaetter: auswahl, nur_pruefen: nurPruefen } });
      if (auswahl === null) auswahl = r.blaetter.filter(b => b.gewaehlt).map(b => b.name);
      melde(m, '');
      const boxen = r.blaetter.map(b => h('label', { style: 'display:flex;gap:8px;align-items:flex-start;color:inherit;font-size:14px;margin:6px 0' },
        h('input', { type: 'checkbox', checked: auswahl.includes(b.name), disabled: r.importiert, style: 'width:auto;margin-top:3px', onchange: (e) => { auswahl = e.target.checked ? [...auswahl, b.name] : auswahl.filter(x => x !== b.name); } }),
        h('span', {}, h('b', {}, b.name), ': ' + b.zeilen + ' Zeilen, ', h('b', {}, b.neu + ' neu'), ', ' + b.doppelt + ' Dubletten, ' + b.ungueltig + ' ungültig',
          h('br'), h('span', { class: 'small muted' }, 'Spalten: ' + Object.entries(b.erkannt).map(([k, v]) => v).join(', ')))));
      const vorschau = r.blaetter.find(b => auswahl.includes(b.name) && b.vorschau.length);
      erg.replaceChildren(
        h('div', { class: 'msg ' + (r.importiert ? 'ok' : 'info') }, r.importiert ? r.neu + ' Leads importiert.' : 'Vorschau: ' + r.neu + ' neue Leads aus den gewählten Blättern.'),
        h('p', { class: 'small muted' }, r.importiert ? 'Importiert wurden:' : 'Welche Blätter importiert werden sollen:'), ...boxen,
        vorschau ? [h('p', { class: 'small muted' }, 'Beispiele aus „' + vorschau.name + '“:'), tabelle([['Firma', z => z.firma], ['Einstufung', z => z.temperatur || ''], ['Branche', z => z.branche || ''], ['Telefon', z => z.telefon || ''], ['Ort', z => [z.plz, z.ort].filter(Boolean).join(' ')]], vorschau.vorschau)] : '',
        r.importiert ? '' : h('p', { class: 'row' }, knopf('Auswahl neu prüfen', () => senden(true), 'sec small'), knopf('Jetzt importieren', async () => { await senden(false); setTimeout(() => location.reload(), 2500); }, 'btn')));
    } catch (x) { erg.replaceChildren(); fehler(m, x); }
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Leads aus Excel oder CSV importieren'),
    h('p', { class: 'small muted' }, 'Mehrere Tabellenblätter werden erkannt, du wählst, welche importiert werden. Überschriften in der ersten Zeile: Firma/Firmenname (Pflicht), Ansprechpartner, E-Mail, Telefon, Website, Branche, Branchengruppe, Adresse, PLZ, Ort, Prio, km, Bewertung, Hinweis. Prio A, B, C wird zu Heiß, Warm, Kalt. Dubletten (E-Mail, Telefon oder Firma + PLZ) werden übersprungen. Importierte Leads haben keine Einwilligung, es gehen also keine automatischen Mails raus. Kaltakquise per Mail oder Telefon ist rechtlich heikel (siehe Anwalts-Checkliste).'), m,
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Datei'), datei), h('div', {}, h('label', {}, 'Listenname'), liste),
      h('div', {}, h('label', {}, 'Quelle'), quelle), h('div', {}, h('label', {}, 'Einstufung, falls keine Prio-Spalte'), temp), h('div', {}, h('label', {}, 'Vertriebler zuordnen'), vt)),
    h('p', {}, knopf('Datei prüfen (Vorschau)', () => { auswahl = null; return senden(true); }, 'btn')), erg);
}

const ANFRAGE_ST = [['angefragt', 'Angefragt'], ['in_pruefung', 'In Prüfung'], ['angebot_raus', 'Angebot ist raus'], ['angenommen', 'Angenommen'], ['abgelehnt', 'Abgelehnt']];
function anfragenKarte(liste) {
  if (!liste.length) return '';
  return h('div', { class: 'card' }, h('h2', {}, 'Angebotsanfragen vom Vertrieb'), h('p', { class: 'small muted' }, 'Bei jeder Statusänderung bekommt der Vertriebler eine Mitteilung. Der Hinweis ist für ihn sichtbar.'),
    liste.map(a => { const m = h('div'), st = select('status', ANFRAGE_ST, a.status, { 'aria-label': 'Status' }), hin = h('input', { value: a.admin_notiz || '', maxlength: 1000, placeholder: 'Hinweis an den Vertriebler (freiwillig)', 'aria-label': 'Hinweis' });
      return h('div', { class: 'heutezeile' }, h('div', {}, h('b', {}, a.paket || 'Paket offen'), ' · ' + (a.vertriebler || 'unbekannt') + ' · ' + zeit(a.erstellt_am)), a.notiz ? h('p', { class: 'muted' }, a.notiz) : '',
        h('div', { class: 'row', style: 'flex-wrap:wrap;align-items:flex-end' }, st, h('div', { class: 'grow' }, hin), knopf('Speichern', () => bestaetigtOhneReload(m, async () => { await api('/api/admin/angebotsanfragen/' + a.id, { method: 'PATCH', body: { status: st.value, admin_notiz: hin.value || null } }); melde(m, 'Gespeichert.', 'ok'); }), 'btn')), m); }));
}

export async function leadDetail(lid) {
  const [d, anfragen] = await Promise.all([api('/api/admin/leads/' + lid), api('/api/admin/leads/' + lid + '/angebotsanfragen')]), l = d.lead, m = h('div');
  const st = h('select', { onchange: (e) => bestaetigt(m, () => api('/api/admin/leads/' + lid, { method: 'PATCH', body: { status: e.target.value } }), 'Status geändert.') }, LEAD_ST.map(s => h('option', { value: s, selected: s === l.status }, s.replace(/_/g, ' '))));
  st.style.width = 'auto';
  const akt = h('form', { onsubmit: (e) => { e.preventDefault(); const o = formular(e.target); bestaetigt(m, () => api('/api/admin/leads/' + lid + '/aktivitaet', { method: 'POST', body: o }), 'Eingetragen.'); } },
    h('div', { class: 'row' }, h('div', { style: 'width:170px' }, select('art', ['notiz', 'anruf', 'mail_gesendet', 'antwort', 'termin'], 'notiz')), h('div', { class: 'grow' }, h('input', { name: 'inhalt', placeholder: 'Was ist passiert?', required: true })), h('button', { class: 'btn' }, 'Eintragen')));
  const zuK = l.kunden_id ? h('a', { class: 'btn sec small', href: '#kunde/' + l.kunden_id }, 'Zum Kunden') : knopf('Zum Kunden machen', () => zuKundeDialog(lid, (k) => { location.hash = '#kunde/' + (k.kunden_id || k.id); }));
  const gesperrt = ['gesperrt', 'consent_ausstehend', 'tot', 'verloren'].includes(l.status);
  const ang = gesperrt ? '' : h('button', { class: 'btn small', onclick: () => angebotDialog(lid, () => location.reload()) }, 'Angebot senden');
  return h('div', { class: 'stack' }, kopf(l.firma, st, tempWahl(l, m), ang, zuK, leadLoeschen(l, m, () => { location.hash = '#leads'; }), h('a', { class: 'btn sec small', href: '#leads' }, '← Liste')), m,
    h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { class: 'grow' }, 'Daten'), h('button', { class: 'btn sec small', onclick: () => leadDatenDialog(lid, l) }, 'Daten bearbeiten')), h('div', { class: 'form2' }, [['Ansprechpartner', l.ansprechpartner], ['E-Mail', l.email], ['Telefon', l.telefon], ['Website', l.website], ['Branche', l.branche], ['Ort', [l.plz, l.ort].filter(Boolean).join(' ')], ['Quelle', l.quelle], ['Vertriebler', l.vertriebler || '–'], ['Score', l.score ?? '–']].map(([a, b]) => h('div', {}, h('div', { class: 'small muted' }, a), h('div', {}, b || '–')))), l.notiz && h('p', { class: 'muted' }, l.notiz)),
    anfragenKarte(anfragen),
    await leadAngebotKarte(lid, l, m),
    kontaktKarte(d.kontakt_optionen, '/api/admin/leads/' + lid + '/kontakt', l.wiedervorlage_am, { verlustgruende: d.verlustgruende }),
    skriptKarte(l.skript, l.skript_am, '/api/admin/leads/' + lid + '/skript'),
    d.checks && d.checks.length ? h('div', { class: 'card' }, h('h2', {}, 'Website-Check'), d.checks.map(c => h('details', { style: 'margin:6px 0' }, h('summary', {}, zeit(c.erstellt_am) + ' · ' + (c.website || 'ohne Website') + ' · ' + (c.score === null ? '–' : c.score + ' von 100')),
      h('div', { class: 'freitext' }, JSON.stringify(c.ergebnis, null, 2))))) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Verlauf'), akt, h('div', { style: 'height:10px' }), tabelle([['Wann', z => zeit(z.zeit)], ['Art', z => z.art.replace(/_/g, ' ')], ['Inhalt', z => z.inhalt], ['Von', z => z.von]], d.aktivitaeten, 'Noch keine Einträge.')));
}


/** Kontaktdaten eines Leads ändern (z. B. E-Mail ergänzen, bevor ein Angebot rausgeht). */
function leadDatenDialog(lid, l) {
  const FELDER = [['Firma', 'firma'], ['Ansprechpartner', 'ansprechpartner'], ['E-Mail', 'email', 'email'], ['Telefon', 'telefon', 'tel'], ['Website', 'website'], ['Branche', 'branche'], ['PLZ', 'plz'], ['Ort', 'ort']];
  const f = h('form', { class: 'stack' }, FELDER.map(([label, name, type]) => h('div', {}, h('label', {}, label), h('input', { name, type: type || 'text', value: l[name] || '', autocomplete: 'off', required: name === 'firma' }))));
  const m = h('p', { class: 'small', role: 'status' });
  const dlg = dialog('Daten bearbeiten', h('div', { class: 'stack' }, f, m, h('button', { class: 'btn', onclick: async (e) => {
    const d = Object.fromEntries(new FormData(f)); if (!String(d.firma).trim()) { melde(m, 'Die Firma darf nicht leer sein.'); return; }
    e.target.disabled = true;
    try { await api('/api/admin/leads/' + lid, { method: 'PATCH', body: d }); dlg.zu(); location.reload(); } catch (x) { e.target.disabled = false; melde(m, x.message); }
  } }, 'Speichern')));
}
