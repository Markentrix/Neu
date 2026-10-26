import { listenKnopf, h, api, csvLaden, datum, dialog, zeit, euro, melde, formular, el, rueckgaengig } from '../common.js';
import { belegeKarte } from './belege.js';
import { V, auswahl, fehler, feld, filterKarte, fmtEuro, knopf, kopf, leerzu, mailHinweis, paketListe, pill, select, sicher, tabelle, zeige } from './kern.js';
import { erklaerungBox } from './fehlerhilfe.js';
import { DATEN_TABS, STATI, freigabenKundeKarte, nachrichtenKundeKarte, unterlagenKarte } from './postfach.js';
import { zeitachseKarte } from './start.js';
import { referenzKarte } from './vertraege.js';
import { qrKarte } from '../anleitung.js';
import { leistungsKarte, wissenKarte } from './wissen.js';

export const modulZelle = (z) => {
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

/** Dialog für Sammelaktionen: Aufgabe, Mail (mit Vorlage) oder Aufgabenpaket für mehrere Kunden. */
async function kundenSammelDialog(aktion, ids) {
  const m = h('div'), inhalt = h('div'), d = dialog({ aufgabe: 'Aufgabe für ' + ids.length + ' Kunden anlegen', mail: 'Mail an ' + ids.length + ' Kunden', aufgabenpaket: 'Aufgabenpaket für ' + ids.length + ' Kunden' }[aktion], inhalt);
  const vorlagen = await api('/api/admin/textvorlagen', { leise: true }).catch(() => []);
  const senden = async (body, ok) => { try { const r = await api('/api/admin/kunden/bulk', { method: 'POST', body: { ids, aktion, ...body } }); m.replaceChildren(h('div', { class: 'msg ' + (r.fehler && r.fehler.length ? 'err' : 'ok') }, ok(r)));
      if (r.sammel_id) rueckgaengig(r.angelegt + ' Aufgaben angelegt.', async () => { const u = await api('/api/admin/kunden/bulk/rueckgaengig', { method: 'POST', body: { sammel_id: r.sammel_id } }); m.replaceChildren(h('div', { class: 'msg ok' }, u.entfernt + ' Aufgaben wieder entfernt.')); }, 15);
    } catch (x) { fehler(m, x); } };
  if (aktion === 'aufgabe') {
    const titel = h('input', { maxlength: 200, placeholder: 'z. B. Rückruf wegen Briefing' }), faellig = h('input', { type: 'date' });
    inhalt.replaceChildren(h('label', {}, 'Titel'), titel, h('label', {}, 'Fällig am (optional)'), faellig, m, h('p', {}, knopf('Aufgaben anlegen', () => senden({ titel: titel.value, faellig_am: faellig.value || null }, r => r.angelegt + ' Aufgaben angelegt (jeweils beim Kunden, dir zugewiesen).'), 'btn')));
  } else if (aktion === 'aufgabenpaket') {
    const pakete = vorlagen.filter(v => v.art === 'aufgaben'), sel = select('v', pakete.map(v => [v.id, v.name + ' (' + v.aufgaben.length + ' Aufgaben)']), pakete[0] && pakete[0].id);
    inhalt.replaceChildren(pakete.length ? h('div', {}, h('label', {}, 'Aufgabenpaket'), sel, m, h('p', {}, knopf('Paket anwenden', () => senden({ vorlage_id: sel.value }, r => r.angelegt + ' Aufgaben angelegt. Bereits vorhandene werden nicht doppelt angelegt.'), 'btn'))) : h('p', { class: 'muted' }, 'Noch kein Aufgabenpaket vorhanden (Einstellungen → Textvorlagen).'));
  } else {
    const mv = vorlagen.filter(v => v.art === 'mail'), betreff = h('input', { maxlength: 200 }), text = h('textarea', { rows: 9, maxlength: 8000 });
    const vsel = h('select', { 'aria-label': 'Vorlage', onchange: (e) => { const v = mv.find(x => x.id === e.target.value); if (v) { betreff.value = v.betreff || ''; text.value = v.text || ''; } } }, h('option', { value: '' }, '– Vorlage wählen (optional) –'), mv.map(v => h('option', { value: v.id }, v.name)));
    inhalt.replaceChildren(h('p', { class: 'small muted' }, 'Platzhalter: {firma}, {name}, {kundennummer}, {ort}. Jeder Kunde bekommt seine eigene Mail. Höchstens 40 Kunden pro Sammelmail. Nur für Informationen zur laufenden Zusammenarbeit, keine Werbung.'),
      h('label', {}, 'Vorlage'), vsel, h('label', {}, 'Betreff'), betreff, h('label', {}, 'Text'), text, m,
      h('p', {}, knopf('Mails senden', () => { if (confirm('Jetzt ' + ids.length + ' Mails senden?')) senden({ betreff: betreff.value, text: text.value }, r => r.gesendet + ' von ' + r.kunden + ' Mails verschickt' + (r.ohne_mail ? ', ' + r.ohne_mail + ' ohne E-Mail-Adresse' : '') + (r.fehler.length ? '. Fehler: ' + r.fehler.map(f => f.firma + ' (' + f.grund + ')').join('; ') : '') + '.'); }, 'btn')));
  }
  return d;
}

V.kunden = async () => {
  const P = new URLSearchParams(location.hash.split('?')[1] || '');
  const q = h('input', { placeholder: 'Suchen nach Firma, Nummer, E-Mail …', value: P.get('q') || '', 'aria-label': 'Suche' });
  const status = select('status', [['', 'Alle Status'], 'onboarding', 'aktiv', 'pausiert', 'gekuendigt', 'beendet'], P.get('status') || '', { 'aria-label': 'Status', onchange: () => lade() });
  const avv = select('avv', [['', 'AVV egal'], ['fehlt', 'AVV fehlt']], P.get('avv') || '', { 'aria-label': 'AVV', onchange: () => lade() });
  const nurRef = h('input', { type: 'checkbox', style: 'width:auto', checked: P.get('ref') === '1', onchange: () => lade() });
  const box = h('div'), leiste = h('div', { class: 'sammelleiste', hidden: true });
  let aktuell = [];
  const sel = auswahl((g) => {
    leiste.hidden = !g.size;
    const ids = [...g], gewaehlt = aktuell.filter(z => g.has(z.id));
    leiste.replaceChildren(h('b', {}, g.size + ' ausgewählt'), knopf('Aufgabe anlegen', () => kundenSammelDialog('aufgabe', ids), 'sec'), knopf('Mail senden', () => kundenSammelDialog('mail', ids), 'sec'),
      knopf('Aufgabenpaket', () => kundenSammelDialog('aufgabenpaket', ids), 'sec'),
      knopf('Als CSV', () => csvLaden('kunden-auswahl.csv', ['Nr.', 'Firma', 'Ansprechpartner', 'E-Mail', 'Status', 'Paket', 'AVV'], gewaehlt.map(z => [z.kundennummer, z.firma, z.ansprechpartner, z.email, z.status, z.paket, z.avv_ok ? 'ja' : 'fehlt'])), 'sec'),
      knopf('Auswahl aufheben', () => sel.leeren(), 'sec'));
  });
  const lade = async () => {
    const n = new URLSearchParams();
    if (q.value.trim()) n.set('q', q.value.trim()); if (status.value) n.set('status', status.value); if (avv.value) n.set('avv', avv.value); if (nurRef.checked) n.set('ref', '1');
    history.replaceState(null, '', '#kunden' + (n.toString() ? '?' + n.toString() : ''));   // Adresse = Filter (Kurzlink), ohne die Seite neu zu zeichnen
    let d = await api('/api/admin/kunden?q=' + encodeURIComponent(q.value.trim()));
    if (nurRef.checked) d = d.filter(z => z.referenzkunde);
    if (status.value) d = d.filter(z => z.status === status.value);
    if (avv.value === 'fehlt') d = d.filter(z => !z.avv_ok);
    aktuell = d; sel.leeren();
    box.replaceChildren(h('p', { class: 'small muted' }, d.length + (d.length === 1 ? ' Kunde' : ' Kunden')), tabelle([
      [sel.alle, z => sel.haken(z.id)],
      ['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => h('span', {}, z.firma, z.referenzkunde ? [' ', h('span', { class: 'pill warn' }, 'Referenz')] : '')], ['Paket', z => z.paket || '–'],
      ['Status', z => h('span', {}, pill(z.status), z.onboarding ? h('div', { class: 'small muted' }, 'Start: ' + z.onboarding.fertig + ' von ' + z.onboarding.gesamt) : '')], ['Module', z => modulZelle(z)], ['Zugang', z => z.zugang_aktiv ? 'ja' : 'nein'], ['AVV', z => z.avv_ok ? h('span', { class: 'pill ok' }, 'ja') : h('span', { class: 'pill warn' }, 'fehlt')], ['Domain', z => z.domain]], d, 'Keine Kunden zu diesem Filter.'));
  };
  let t; q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(lade, 250); });
  await lade();
  return h('div', {}, kopf('Kunden', h('a', { class: 'btn', href: '#neu' }, '+ Neuer Kunde')), h('div', { class: 'card' }, q,
    h('details', { class: 'filterklapp', open: !!(P.get('status') || P.get('avv') || P.get('ref')) }, h('summary', { class: 'small' }, 'Filter und gespeicherte Ansichten' + (P.get('status') || P.get('avv') || P.get('ref') ? ' (aktiv)' : '')),
      await filterKarte('kunden'), h('div', { class: 'filterzeile' }, status, avv),
      h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin-top:8px' }, nurRef, 'Nur Referenzkunden')),
    h('div', { style: 'height:12px' }), leiste, box));
};

V.neu = async () => {
  const m = h('div');
  const paket = h('select', { name: 'paket_code' }, h('option', { value: '' }, '– kein Paket –'), paketListe.map(p => h('option', { value: p.code }, p.name)));
  const einl = h('input', { type: 'checkbox', name: 'einladen', checked: true, style: 'width:auto' });
  const ref = h('input', { type: 'checkbox', style: 'width:auto' }), refd = h('input', { type: 'checkbox', style: 'width:auto' });
  const f = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const d = leerzu(formular(e.target)); d.einladen = einl.checked; d.referenzkunde = ref.checked; d.referenz_nennen_erlaubt = ref.checked && refd.checked;
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

export async function historieKarte(kid) {
  const l = await api('/api/admin/kunden/' + kid + '/historie');
  return h('div', { class: 'card' }, h('h2', {}, 'Änderungshistorie'), h('p', { class: 'small muted' }, 'Wer hat wann was bei diesem Kunden geändert (letzte 150 Einträge).'),
    tabelle([['Zeit', z => zeit(z.zeit)], ['Von', z => z.name || z.email || 'System'], ['Aktion', z => z.aktion.replace(/_/g, ' ')], ['Details', z => h('span', { class: 'small muted' }, JSON.stringify(z.details).slice(0, 160))]], l, 'Noch keine Einträge.'));
}

/** Aufgabenpaket (z. B. „Neuer Kunde: 8 Schritte“) mit einem Klick beim Kunden anlegen. */
export function aufgabenpaketKarte(kid) {
  const m = h('div'), box = h('div');
  api('/api/admin/textvorlagen?art=aufgaben').then(liste => {
    if (!liste.length) { box.replaceChildren(h('p', { class: 'small muted' }, 'Noch kein Aufgabenpaket (Einstellungen → Textvorlagen).')); return; }
    const sel = select('v', liste.map(v => [v.id, v.name + ' (' + v.aufgaben.length + ' Aufgaben)']), liste[0].id);
    box.replaceChildren(h('div', { class: 'row' }, sel, knopf('Paket anlegen', async () => {
      try { const r = await api('/api/admin/kunden/' + kid + '/aufgabenpaket', { method: 'POST', body: { vorlage_id: sel.value } }); melde(m, r.angelegt ? r.angelegt + ' Aufgaben angelegt (dir zugewiesen, mit Fälligkeit).' : 'Dieses Paket wurde hier schon angelegt, nichts doppelt.', r.angelegt ? 'ok' : 'info'); } catch (x) { fehler(m, x); }
    }, 'btn')));
  }).catch(x => fehler(m, x));
  return h('div', { class: 'card' }, h('h2', {}, 'Aufgabenpaket'), h('p', { class: 'small muted' }, 'Legt eine feste Reihe von Aufgaben mit Fälligkeiten an, etwa für jeden neuen Kunden.'), m, box);
}

export function vorlagenKarte(kid, k) {
  const m = h('div'), box = h('div');
  const laden = async () => {
    if (k.vorlage) { box.replaceChildren(h('p', {}, 'Angewendet: ', h('b', {}, k.vorlage), ' (' + datum(k.vorlage_am) + ')')); return; }
    const liste = await api('/api/admin/vorlagen');
    const sel = select('code', liste.map(v => [v.code, v.name + ' – ' + v.beschreibung]), liste[0].code);
    box.replaceChildren(h('div', { class: 'row' }, sel, knopf('Vorlage anwenden', async () => {
      if (!confirm('Die Vorlage legt Wissenseinträge (inaktiv), Beitrags-Entwürfe und Aufgaben an. Fortfahren?')) return;
      try { const r = await api('/api/admin/kunden/' + kid + '/vorlage', { method: 'POST', body: { code: sel.value } }); melde(m, r.name + ': ' + r.wissen + ' Wissenseinträge (inaktiv, bitte prüfen), ' + r.beitraege + ' Beitrags-Entwürfe, ' + r.aufgaben + ' Aufgaben angelegt.', 'ok'); box.replaceChildren(); } catch (x) { fehler(m, x); } }, '')));
  };
  laden().catch(x => fehler(m, x));
  const bm = h('div'), bbox = h('div');
  api('/api/admin/buchungsvorlagen').then(liste => {
    const sel = select('code', liste.map(v => [v.code, v.name + ' – ' + v.leistungen.join(', ')]), liste[0].code);
    bbox.replaceChildren(h('div', { class: 'row' }, sel, knopf('Buchungsvorlage anwenden', async () => {
      if (!confirm('Legt typische Leistungen (inaktiv, ohne Preis), Zusatzfragen und Arbeitszeiten an. Geht nur bei einem Kunden ohne Leistungen. Fortfahren?')) return;
      try { const r = await api('/api/admin/kunden/' + kid + '/buchungsvorlage', { method: 'POST', body: { code: sel.value } }); melde(bm, r.name + ': ' + r.leistungen + ' Leistungen angelegt (inaktiv). Bitte Preise eintragen und die Leistungen im Kundenportal oder hier aktivieren.', 'ok'); } catch (x) { fehler(bm, x); } }, '')));
  }).catch(x => fehler(bm, x));
  return h('div', { class: 'card' }, h('h2', {}, 'Branchenvorlage'), h('div', { class: 'card' }, h('h3', {}, 'Buchung: Leistungen und Arbeitszeiten'), h('p', { class: 'small muted' }, 'Startpaket für die Terminbuchung: typische Leistungen mit Dauer und Zusatzfragen, Arbeitszeiten mit Pausen. Alles startet inaktiv und ohne Preise.'), bm, bbox), h('p', { class: 'small muted' }, 'Startpaket für typische Branchen: Wissenseinträge für den Assistenten (zunächst inaktiv, mit Platzhaltern zum Ausfüllen), Entwürfe für Beiträge und eine Aufgabenliste. Es wird nichts veröffentlicht.'), m, box);
}

const AVV_MODULE = [['portal', 'Portal (Basis): Kontaktverwaltung, Anfragen, Berichte', 0], ['website', 'Website: Hosting und Kontaktformular', 0], ['automationen', 'Automationen: Workflows (n8n)', 0],
  ['email', 'E-Mail-Kommunikation', 0], ['email_auftragnehmer', 'über das Konto des Auftragnehmers (Google)', 1], ['email_eigen', 'über das eigene Konto des Kunden (keine Unterauftragsverarbeitung)', 1],
  ['termin', 'Terminbuchung und Kalender', 0], ['termin_auftragnehmer', 'über das Konto des Auftragnehmers (Google)', 1], ['termin_eigen', 'über das eigene Konto des Kunden (keine Unterauftragsverarbeitung)', 1],
  ['ki_chat', 'KI-Assistent (Chat)', 0], ['telefon', 'Telefon-Assistent / KI-Sprachagent (Famulor)', 0], ['whatsapp', 'WhatsApp-Kommunikation (Meta)', 0], ['domain', 'Domainverwaltung (INWX)', 0], ['sonstiges', 'Sonstiges', 0]];

/** Dialog: gebuchte Module und Angaben für den AVV (Anlage 1). aid gesetzt = bestehenden Entwurf ändern. */
async function avvDialog(kid, aid) {
  const info = aid ? await api('/api/admin/avv/' + aid + '/pruefen') : { anlage: (await api('/api/admin/avv-vorschlag/' + kid)).anlage, offen: [] };
  const a = info.anlage, m = h('div'), boxen = {};
  const feldEin = (name, label, typ = 'text') => { const i = h('input', { type: typ, value: a[name] || '', maxlength: 300 }); return [i, h('label', {}, label, i)]; };
  const [leist, fLeist] = feldEin('leistung', 'Leistung laut Hauptvertrag'), [dat, fDat] = feldEin('hauptvertrag_datum', 'Datum des Hauptvertrags', 'date'),
    [wn, fWn] = feldEin('weisung_name', 'Weisungsberechtigt beim Kunden: Name'), [we, fWe] = feldEin('weisung_email', 'Weisungsberechtigt beim Kunden: E-Mail', 'email'),
    [dom, fDom] = feldEin('domain', 'Domain(s), nur bei „Domainverwaltung“'), [son, fSon] = feldEin('sonstiges', 'Beschreibung, nur bei „Sonstiges“');
  const zeilen = AVV_MODULE.map(([k, text, e]) => { const cb = h('input', { type: 'checkbox', checked: a.module.includes(k) || k === 'portal', disabled: k === 'portal', style: 'width:auto' }); boxen[k] = cb;
    return h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin-left:' + Number(e) * 24 + 'px' }, cb, text); });
  const bodyBauen = () => ({ module: Object.keys(boxen).filter(k => boxen[k].checked), leistung: leist.value, hauptvertrag_datum: dat.value, weisung_name: wn.value, weisung_email: we.value, domain: dom.value, sonstiges: son.value });
  const vorschau = async () => {
    try {
      const r = await fetch('/api/admin/avv-vorschau/' + kid, { method: 'POST', headers: { 'X-MK': '1', 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify(bodyBauen()) });
      if (!r.ok) { const d = await r.json().catch(() => null); throw new Error(d && typeof d.detail === 'string' ? d.detail : 'Die Vorschau ist nicht möglich. Bitte die Eingaben prüfen.'); }
      window.open(URL.createObjectURL(await r.blob()), '_blank');
    } catch (x) { fehler(m, x); } };
  const speichern = async () => {
    const body = bodyBauen();
    try { if (aid) await api('/api/admin/avv/' + aid + '/anlage', { method: 'PUT', body }); else await api('/api/admin/kunden/' + kid + '/avv', { method: 'POST', body }); location.reload(); } catch (x) { fehler(m, x); } };
  dialog(aid ? 'AVV-Angaben prüfen' : 'Neuen AVV erstellen', h('div', { class: 'stack' },
    info.offen.length ? h('div', { class: 'msg warn' }, h('b', {}, 'Vor dem Versand fehlt noch:'), h('ul', {}, info.offen.map(o => h('li', {}, o)))) : '',
    h('p', { class: 'small muted' }, 'Kreuze an, welche Module der Kunde gebucht hat. Daraus entstehen Anlage 1 und die Liste der Unterauftragsverarbeiter in Anlage 3. Der Vertragstext selbst ist feststehend (Version 2).'),
    ...zeilen, fLeist, fDat, fWn, fWe, fDom, fSon, m, h('div', { class: 'row' }, knopf(aid ? 'Speichern' : 'Entwurf erstellen', speichern, 'btn'), knopf('Vorschau (PDF)', vorschau, 'sec'))), true);
}

export async function avvKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/avv'), m = h('div');
  const neu = () => avvDialog(kid).catch(x => fehler(m, x));
  const hoch = (z) => { const datei = h('input', { type: 'file', accept: 'application/pdf,image/png,image/jpeg' }), tag = h('input', { type: 'date', value: new Date().toISOString().slice(0, 10), style: 'max-width:160px' });
    return h('span', { class: 'row' }, datei, tag, knopf('Ablegen', () => { const f = datei.files[0]; if (!f) return fehler(m, { message: 'Bitte zuerst die unterschriebene Datei wählen.' });
      const r = new FileReader(); r.onload = async () => { try { await api('/api/admin/avv/' + z.id + '/upload', { method: 'POST', body: { datei_base64: r.result, datei_name: f.name, unterschrieben_am: tag.value } }); location.reload(); } catch (x) { fehler(m, x); } }; r.readAsDataURL(f); }, 'btn')); };
  const aktion = (z) => h('span', { class: 'row' },
    h('a', { class: 'btn sec small', href: '/api/admin/avv/' + z.id + '/vorlage.pdf', target: '_blank', rel: 'noopener' }, 'Vertrag (PDF)'),
    !z.hat_datei && !z.portal_freigabe_am ? knopf('Module & Angaben prüfen', () => avvDialog(kid, z.id).catch(x => fehler(m, x)), 'sec small') : '',
    !z.hat_datei ? knopf(z.portal_freigabe_am ? 'Erneut zur Bestätigung freigeben' : 'Im Portal zur Bestätigung freigeben', async () => { if (confirm('Der Kunde bekommt eine Mail und kann den Vertrag im Portal mit einem Klick bestätigen. Fortfahren?')) { try { await api('/api/admin/avv/' + z.id + '/portal-freigeben', { method: 'POST' }); melde(m, 'Freigegeben, der Kunde wurde benachrichtigt.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } } }, 'small') : '',
    knopf('Per Mail senden', async () => { if (confirm('AVV jetzt per E-Mail an den Kunden senden?')) { try { await api('/api/admin/avv/' + z.id + '/senden', { method: 'POST' }); melde(m, 'Gesendet.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } } }, 'sec small'),
    z.hat_datei ? h('a', { class: 'btn sec small', href: '/api/admin/avv/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Unterschrieben ansehen') : knopf('Entwurf löschen', async () => { if (confirm('Entwurf löschen?')) { try { await api('/api/admin/avv/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { fehler(m, x); } } }, 'bad small'));
  return h('div', { class: 'card' }, h('h2', {}, 'Auftragsverarbeitungsvertrag (AVV) ', d.vorhanden ? h('span', { class: 'pill ok' }, 'liegt vor') : h('span', { class: 'pill warn' }, 'fehlt')),
    d.veraltet ? h('div', { class: 'msg warn' }, 'Dieser Kunde hat noch die alte Fassung des AVV (Version 1). ', d.veraltet.entwurf_id ? 'Ein Entwurf der neuen Fassung (Version 2) liegt bereit, siehe unten.' : [knopf('Neue Fassung (Version 2) vorbereiten', () => avvDialog(kid).catch(x => fehler(m, x)), 'btn small')]) : '',
    h('p', { class: 'small muted' }, 'Ablauf A (empfohlen): Vertrag erstellen, im Portal zur Bestätigung freigeben, der Kunde bestätigt per Klick. Ablauf B: per Mail senden, unterschrieben zurückbekommen und hier ablegen. Der Kunde sieht die abgelegte Fassung in seinem Portal.'), m,
    tabelle([['Erstellt', z => datum(z.erstellt_am)], ['Gesendet', z => z.gesendet_am ? datum(z.gesendet_am) : '–'], ['Unterschrieben am', z => z.unterschrieben_am ? datum(z.unterschrieben_am) : '–'],
      ['Datei', z => z.hat_datei ? z.datei_name + (z.online_bestaetigt_am ? ' (online bestätigt von ' + z.online_bestaetigt_name + ', ' + datum(z.online_bestaetigt_am) + ')' : '') : (z.portal_freigabe_am ? 'im Portal freigegeben, wartet auf Bestätigung' : 'noch nicht abgelegt')], ['', aktion]], d.liste, 'Noch kein AVV erstellt.'),
    d.liste.filter(z => !z.hat_datei).length ? h('div', { style: 'margin-top:12px' }, h('p', { class: 'small muted' }, 'Unterschriebene Fassung zum neuesten Entwurf ablegen:'), hoch(d.liste.find(z => !z.hat_datei))) : '',
    h('p', { style: 'margin-top:12px' }, knopf('Neuen AVV erstellen', neu, 'btn')));
}

export async function onboardingKarte(kid) {
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
    h('div', { class: 'row', style: 'margin-bottom:10px' }, knopf('Startpaket auslösen', async () => { if (!confirm('Aufgaben für das Team anlegen, Checkliste ergänzen und (einmalig) die Willkommensmail mit den Wünschen an den Kunden senden?')) return; try { const r = await api('/api/admin/kunden/' + kid + '/startpaket', { method: 'POST' }); melde(m, r.aufgaben + ' Aufgaben angelegt' + (r.mail ? ', Willkommensmail gesendet.' : ' (Willkommensmail war schon raus oder keine E-Mail hinterlegt).'), 'ok'); } catch (x) { melde(m, x.message); } }, 'sec small'), h('span', { class: 'small muted' }, 'Legt die ersten Aufgaben und die Willkommensmail an. Mehrfach klickbar, nichts doppelt.')),
    h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, neu), knopf('Punkt hinzufügen', async () => { if (!neu.value.trim()) return; try { await api('/api/admin/kunden/' + kid + '/onboarding', { method: 'POST', body: { titel: neu.value } }); location.reload(); } catch (x) { fehler(m, x); } })));
}

export function brandingKarte(kid, k) {
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

/** Website-Dienste eines Kunden: Status und fertiger Einbau-Code. Zugangsdaten sieht der Admin bewusst nie. */
export async function diensteKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/website-dienste');
  const ja = (x, t) => h('span', { class: 'pill ' + (x ? 'ok' : '') }, t + (x ? ': an' : ': aus'));
  const st = (art) => { const e = d.status[art]; return e ? (e.ok || 0) + ' ok' + (e.fehler ? ', ' + e.fehler + ' Fehler' : '') + (e.letzte && !e.letzte.ok ? ' (zuletzt: ' + e.letzte.hinweis + ')' : '') : '–'; };
  const code = (d.mail.aktiv ? '<div data-mk="kontakt"></div>\n' : '') + (d.kalender.aktiv ? '<div data-mk="termin"></div>\n' : '') + (d.bewertungen.aktiv ? '<div data-mk="bewertungen"></div>\n' : '') +
    (d.paypal.aktiv ? '<div data-mk="paypal" data-betrag="49,90" data-titel="Gutschein"></div>\n' : '') + (d.analytics.aktiv ? '<span data-mk="cookies"></span>  <!-- Link „Statistik-Einstellungen“, z. B. im Footer neben Datenschutz -->\n' : '');
  const skript = '<script src="' + d.basis + '/static/js/site.js" data-site="' + d.site_id + '" defer></script>';
  const kopieren = (t) => knopf('Kopieren', async () => { try { await navigator.clipboard.writeText(t); } catch { /* ältere Browser */ } }, 'sec small');
  return h('div', { class: 'card' }, h('h2', {}, 'Website-Dienste'),
    h('p', { class: 'small muted' }, 'Was der Kunde im Portal eingetragen hat. Zugangsdaten (Passwörter, Kalender-Adresse) sind verschlüsselt und für uns nicht lesbar. Der Kunde kann sie nur ersetzen.'),
    d.start ? h('div', { style: 'margin:8px 0' }, h('b', {}, 'Start-Checkliste: ' + d.start.erledigt + ' von ' + d.start.gesamt + (d.start.fertig ? ' (fertig)' : '')),
      d.start.punkte.map(p => h('div', { class: 'small' }, h('span', { class: 'pill ' + (p.erledigt ? 'ok' : 'warn') }, p.erledigt ? 'ok' : 'offen'), ' ' + p.titel + (p.erledigt ? '' : ' – ' + p.hinweis)))) : '',
    h('div', { class: 'row', style: 'flex-wrap:wrap;gap:6px' }, ja(d.mail.aktiv, 'Formular'), ja(d.mail.smtp.gesetzt, 'Eigenes Postfach'), ja(d.kalender.aktiv, 'Termine'), ja(d.kalender.ical_gesetzt, 'Kalender verbunden'), ja(d.paypal.aktiv, 'PayPal'), ja(d.bewertungen.aktiv, 'Bewertungen'), ja(d.analytics.aktiv, 'Analytics')),
    h('p', { class: 'small' }, 'Erlaubte Seiten: ', d.domains.length ? d.domains.join(', ') : 'noch keine (Domain oben eintragen, sonst lehnt der Server die Website ab)'),
    h('p', { class: 'small' }, 'Formular: ' + st('kontakt') + ' · Termine: ' + st('termin') + ' · Bewertungen: ' + st('bewertungen') + ' · Test: ' + st('test')),
    h('h3', {}, 'Einbau in die Website'),
    h('p', { class: 'small muted' }, '1. Skript einmal vor </body> einfügen. 2. Die Bausteine dort platzieren, wo sie erscheinen sollen.'),
    h('pre', { class: 'code', style: 'white-space:pre-wrap;overflow-wrap:anywhere' }, skript), kopieren(skript),
    code ? [h('pre', { class: 'code', style: 'white-space:pre-wrap' }, code), kopieren(code)] : h('p', { class: 'small muted' }, 'Noch kein Dienst eingeschaltet. Sobald der Kunde einen Dienst aktiviert, erscheinen hier die Bausteine.'));
}

export async function domainKarte(kid) {
  const liste = await api('/api/admin/kunden/' + kid + '/domains'), m = h('div');
  const dialogDomain = (z) => {
    const f = h('form', { class: 'stack', onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); o.auto_verlaengern = e.target.auto_verlaengern.checked; o.preis_jahr_eur = o.preis_jahr_eur === '' ? null : Number(o.preis_jahr_eur);
        try { await api(z ? '/api/admin/domains/' + z.id : '/api/admin/kunden/' + kid + '/domains', { method: z ? 'PUT' : 'POST', body: o }); location.reload(); } catch (x) { melde(fm, x.message); } } },
      h('div', { class: 'form2' }, feld('Domain', 'domain', z ? z.domain : '', { required: true, placeholder: 'firma.de' }), feld('Registrar', 'registrar', z ? z.registrar : 'INWX'),
        h('div', {}, h('label', {}, 'Inhaber der Domain'), h('select', { name: 'inhaber' }, h('option', { value: 'markentrix', selected: !z || z.inhaber === 'markentrix' }, 'Markentrix (wir verwalten)'), h('option', { value: 'kunde', selected: z && z.inhaber === 'kunde' }, 'Kunde (eigener Registrar-Account)'))),
        feld('Name des Inhabers', 'inhaber_name', z ? z.inhaber_name || '' : ''), feld('Kontakt des Inhabers', 'inhaber_kontakt', z ? z.inhaber_kontakt || '' : ''),
        feld('Registriert am', 'registriert_am', z ? String(z.registriert_am || '').slice(0, 10) : '', { type: 'date' }), feld('Läuft ab am', 'ablauf_am', z ? String(z.ablauf_am || '').slice(0, 10) : '', { type: 'date' }),
        feld('Preis pro Jahr in €', 'preis_jahr_eur', z && z.preis_jahr_cent != null ? (z.preis_jahr_cent / 100).toFixed(2) : '', { type: 'number', step: '0.01', min: '0' }),
        h('div', {}, h('label', {}, 'Status'), h('select', { name: 'status' }, [['aktiv', 'aktiv'], ['transfer', 'wird übertragen'], ['gekuendigt', 'gekündigt']].map(([v, t]) => h('option', { value: v, selected: z && z.status === v }, t))))),
      h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', name: 'auto_verlaengern', checked: !z || z.auto_verlaengern, style: 'width:auto' }), 'verlängert sich automatisch'),
      h('label', {}, 'Notiz (keine Passwörter oder Auth-Codes!)'), h('textarea', { name: 'notiz', rows: 2, maxlength: 500 }, z ? z.notiz || '' : ''), h('div', {}), h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
    const fm = h('div'); dialog(z ? 'Domain bearbeiten' : 'Domain eintragen', h('div', {}, fm, f), true);
  };
  const tage = (d) => d ? Math.ceil((new Date(String(d).slice(0, 10)).getTime() - new Date(new Date().toISOString().slice(0, 10)).getTime()) / 864e5) : null;
  return h('div', { class: 'card' }, h('h2', {}, 'Domains'), m,
    h('p', { class: 'small muted' }, 'Wem gehört die Domain, wo liegt sie, wann läuft sie ab? Ablauf in den nächsten 60 Tagen erzeugt automatisch eine Aufgabe. Auth-Codes und Passwörter bitte nur im Passwortmanager speichern.'),
    tabelle([['Domain', z => z.domain], ['Registrar', z => z.registrar], ['Inhaber', z => z.inhaber === 'kunde' ? 'Kunde' : 'Markentrix'],
      ['Läuft ab', z => { const t = tage(z.ablauf_am); return z.ablauf_am ? datum(z.ablauf_am) + (t !== null && t <= 60 && z.status === 'aktiv' ? ' (' + (t < 0 ? 'abgelaufen' : 'in ' + t + ' Tagen') + ')' : '') : '–'; }],
      ['Preis/Jahr', z => z.preis_jahr_cent != null ? fmtEuro(z.preis_jahr_cent) : '–'], ['Status', z => z.status === 'aktiv' ? 'aktiv' : z.status === 'transfer' ? 'wird übertragen' : 'gekündigt'],
      ['', z => h('span', { class: 'row' }, knopf('Bearbeiten', () => dialogDomain(z), 'sec small'), knopf('Löschen', async () => { if (confirm('Domain ' + z.domain + ' aus der Liste entfernen?')) { try { await api('/api/admin/domains/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { fehler(m, x); } } }, 'bad small'))]], liste, 'Noch keine Domain eingetragen.'),
    h('p', { style: 'margin-top:12px' }, knopf('Domain eintragen', () => dialogDomain(null), 'btn')));
}

/** Wartungsverträge: wiederkehrende Rechnungen (monatlich bis jährlich), automatisch erzeugt und auf Wunsch versendet. */
export async function abrechnungKarte(kid) {
  const m = h('div'), box = h('div');
  const INT = { 1: 'monatlich', 3: 'vierteljährlich', 6: 'halbjährlich', 12: 'jährlich' };
  const laden = async () => {
    const d = await api('/api/admin/kunden/' + kid + '/abrechnungsplaene');
    box.replaceChildren(tabelle([['Titel', p => p.titel], ['Turnus', p => INT[p.intervall_monate]], ['Inhalt', p => p.aus_buchungen ? 'aus den Buchungen' : p.positionen.map(x => x.text + ' ' + fmtEuro(x.preis_cent)).join('; ')],
      ['Nächste Rechnung', p => datum(p.naechste_am) + (p.enddatum ? ' (bis ' + datum(p.enddatum) + ')' : '')], ['Versand', p => p.auto_senden ? 'automatisch' : 'von Hand'], ['Status', p => p.aktiv ? 'aktiv' : 'pausiert'],
      ['', p => h('span', { class: 'row' },
        knopf('Jetzt erzeugen', async () => { if (!confirm('Die nächste Rechnung jetzt erzeugen und ausstellen?')) return; try { const r = await api('/api/admin/abrechnungsplaene/' + p.id + '/jetzt', { method: 'POST', body: {} }); melde(m, 'Rechnung ' + r.nummer + ' (' + r.zeitraum + ') ausgestellt. Sie liegt unter Belege zum Versand bereit.', 'ok'); laden(); } catch (x) { fehler(m, x); } }, 'sec small'),
        knopf(p.aktiv ? 'Pausieren' : 'Fortsetzen', async () => { try { await api('/api/admin/abrechnungsplaene/' + p.id, { method: 'PUT', body: { aktiv: !p.aktiv } }); laden(); } catch (x) { fehler(m, x); } }, 'sec small'),
        knopf('Löschen', async () => { if (!confirm('Plan löschen? Bereits erzeugte Rechnungen bleiben.')) return; try { await api('/api/admin/abrechnungsplaene/' + p.id, { method: 'DELETE' }); laden(); } catch (x) { fehler(m, x); } }, 'bad small'))]], d.plaene, 'Noch kein Wartungsvertrag.'));
  };
  const neu = () => {
    const titel = h('input', { value: 'Wartung & Betrieb', maxlength: 200 }), turnus = select('turnus', Object.entries(INT), '1');
    const buch = h('input', { type: 'checkbox', style: 'width:auto', checked: true }), text = h('input', { placeholder: 'z. B. Wartung Website', maxlength: 300 }), preis = h('input', { placeholder: 'Preis netto je Zeitraum, z. B. 49,00' });
    const start = h('input', { type: 'date', value: new Date().toISOString().slice(0, 10) }), ende = h('input', { type: 'date' }), auto = h('input', { type: 'checkbox', style: 'width:auto' });
    const speichern = async () => {
      const body = { titel: titel.value, intervall_monate: Number(turnus.value), aus_buchungen: buch.checked, naechste_am: start.value, enddatum: ende.value || null, auto_senden: auto.checked, positionen: [] };
      if (!buch.checked) body.positionen = [{ text: text.value, menge: 1, einheit: '', preis_cent: Math.round(parseFloat(String(preis.value).replace(',', '.')) * 100) || 0 }];
      try { await api('/api/admin/kunden/' + kid + '/abrechnungsplaene', { method: 'POST', body }); melde(m, 'Wartungsvertrag angelegt.', 'ok'); formBox.replaceChildren(); laden(); } catch (x) { fehler(m, x); }
    };
    formBox.replaceChildren(h('div', { class: 'form2' }, feld('Titel der Rechnung', titel), feld('Turnus', turnus), feld('Erste Rechnung am (Beginn des Zeitraums)', start), feld('Endet am (leer = unbefristet)', ende),
      h('label', { class: 'row' }, buch, ' Positionen aus den aktiven Buchungen übernehmen (monatlicher Preis mal Turnus)'),
      feld('Oder feste Position', text), feld('Preis netto', preis), h('label', { class: 'row' }, auto, ' Rechnung automatisch per E-Mail an den Kunden senden')),
      h('p', {}, knopf('Anlegen', speichern, 'btn')));
  };
  const formBox = h('div');
  await laden();
  return h('div', { class: 'card' }, h('h2', {}, 'Wartungsvertrag & wiederkehrende Rechnungen'),
    h('p', { class: 'small muted' }, 'Zum Stichtag erzeugt der Server die Rechnung im Voraus für den Zeitraum, stellt sie aus und sendet sie auf Wunsch. Ohne automatischen Versand bekommst du eine Meldung. Wird der Kunde gekündigt, endet der Plan zum Vertragsende.'),
    m, box, formBox, h('p', { style: 'margin-top:8px' }, knopf('Neuer Wartungsvertrag', neu, 'btn')));
}

/** Gelöschte Datensätze eines einzelnen Kunden aus der nächtlichen Datenbanksicherung zurückholen (nur fehlende Zeilen, nichts wird überschrieben). */
export async function auszugKarte(kid) {
  const sich = await api('/api/admin/datensicherungen').catch(() => ({ tage: [] })), m = h('div'), ergebnis = h('div');
  const tag = h('select', {}, sich.tage.map(t => h('option', { value: t }, t.slice(8, 10) + '.' + t.slice(5, 7) + '.' + t.slice(0, 4) + ' ' + t.slice(11, 13) + ':' + t.slice(13))));
  let uid = null;
  const anzeigen = async () => {
    let a; try { a = await api('/api/admin/kunden/auszug/' + uid); } catch (x) { fehler(m, x); return; }
    if (a.status === 'laeuft') { ergebnis.replaceChildren(h('p', { class: 'small muted' }, 'Der Server liest die Sicherung … (dauert einige Minuten)')); setTimeout(anzeigen, 6000); return; }
    if (a.status === 'fehler') { ergebnis.replaceChildren(h('div', { class: 'msg err' }, a.text)); return; }
    const haken = {};
    const zeilen = a.tabellen.map(z => { const c = h('input', { type: 'checkbox', style: 'width:auto', checked: z.fehlt_jetzt > 0, disabled: z.fehlt_jetzt === 0 }); haken[z.tabelle] = c; return { ...z, c }; });
    ergebnis.replaceChildren(
      h('p', { class: 'small muted' }, 'Stand der Sicherung vom ' + a.tag.slice(0, 10) + '. „Fehlt jetzt“ sind Zeilen, die damals da waren und heute nicht mehr. Zurückgespielt werden nur diese; vorhandene Daten bleiben unverändert.'),
      tabelle([['Zurückholen', z => z.c], ['Bereich', z => z.tabelle], ['In Sicherung', z => z.in_sicherung], ['Fehlt jetzt', z => z.fehlt_jetzt]], zeilen, 'Zu diesem Kunden enthält die Sicherung keine Daten.'),
      a.ohne_dateiinhalt.length ? h('p', { class: 'small muted' }, 'Nicht enthalten (Dateien/Dokumente): ' + a.ohne_dateiinhalt.join(', ') + '.') : '',
      zeilen.length ? h('p', {}, knopf('Ausgewählte Zeilen zurückholen', async () => {
        const wahl = zeilen.filter(z => z.c.checked).map(z => z.tabelle); if (!wahl.length) return;
        if (!confirm('Fehlende Zeilen aus ' + wahl.length + ' Bereich(en) zurückspielen?')) return;
        try { const r = await api('/api/admin/kunden/auszug/' + uid + '/zurueckspielen', { method: 'POST', body: { tabellen: wahl } });
          melde(m, Object.entries(r.ergebnis).map(([t, v]) => t + ': ' + v.zurueck + ' zurück' + (v.uebrig ? ', ' + v.uebrig + ' nicht möglich' : '')).join(' · '), 'ok'); await api('/api/admin/kunden/auszug/' + uid, { method: 'DELETE' }); ergebnis.replaceChildren(); } catch (x) { fehler(m, x); } }, 'btn')) : '');
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Daten aus der Sicherung zurückholen'),
    h('p', { class: 'small muted' }, 'Hat dieser Kunde versehentlich etwas gelöscht? Wähle eine Sicherung, sieh dir an, was fehlt, und hole nur das zurück. Die Datenbank der anderen Kunden wird nicht angefasst.'),
    m, sich.tage.length ? [h('div', { class: 'row' }, tag, knopf('Sicherung prüfen', async () => {
      try { const r = await api('/api/admin/kunden/' + kid + '/auszug', { method: 'POST', body: { tag: tag.value } }); uid = r.id; ergebnis.replaceChildren(h('p', { class: 'small muted' }, r.hinweis)); setTimeout(anzeigen, 5000); } catch (x) { fehler(m, x); } }, 'btn')), ergebnis]
      : h('p', { class: 'small muted' }, 'Noch keine Datenbanksicherung gefunden (die erste entsteht nachts).'));
}

export function offboardingKarte(kid, k, domains = []) {
  const m = h('div'); const beendet = ['gekuendigt', 'beendet'].includes(k.status);
  if (k.geloescht_am) return h('div', { class: 'card' }, h('h2', {}, 'Vertragsende'), h('p', {}, 'Die Inhalte dieses Kunden wurden am ' + datum(k.geloescht_am) + ' gelöscht. Stammdaten und Belege bleiben wegen Aufbewahrungspflichten erhalten.'));
  const best = h('input', { placeholder: 'Kundennummer ' + k.kundennummer + ' zur Bestätigung', style: 'max-width:300px' });
  const haken = h('input', { type: 'checkbox', style: 'width:auto' });
  return h('div', { class: 'card' }, h('h2', {}, 'Vertragsende: Datenexport und Löschung'),
    h('p', { class: 'small muted' }, 'Zum Vertragsende bekommt der Kunde seine Daten (Pflicht laut AVV) und danach werden seine Inhalte gelöscht. Stammdaten, Rechnungen, Verträge, Buchungen und der AVV bleiben wegen Aufbewahrungspflichten erhalten, die Kontaktdaten der Ansprechperson werden entfernt. Sicherungen enthalten die Daten noch bis zu 30 Tage.'), m,
    domains.filter(z => z.inhaber === 'markentrix' && z.status !== 'gekuendigt').length ? h('div', { class: 'msg warn' }, 'Diese Domains gehören uns und müssen dem Kunden übergeben werden (Transfer zum Registrar des Kunden, Inhaberwechsel): ' + domains.filter(z => z.inhaber === 'markentrix' && z.status !== 'gekuendigt').map(z => z.domain).join(', ') + '. Danach Status auf „wird übertragen“ bzw. „gekündigt“ setzen.') : '',
    h('p', {}, h('a', { class: 'btn', href: '/api/admin/kunden/' + kid + '/export.zip' }, 'Datenexport als ZIP herunterladen')),
    beendet ? h('div', { class: 'stack', style: 'margin-top:12px' },
      h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, haken, 'Der Datenexport wurde an den Kunden übergeben'), best,
      h('p', {}, knopf('Inhalte endgültig löschen', async () => { if (!confirm('Alle Inhalte dieses Kunden endgültig löschen? Das kann nicht rückgängig gemacht werden.')) return;
        try { await api('/api/admin/kunden/' + kid + '/loeschen', { method: 'POST', body: { bestaetigung: best.value, export_uebergeben: haken.checked } }); melde(m, 'Gelöscht.', 'ok'); setTimeout(() => location.reload(), 1200); } catch (x) { fehler(m, x); } }, 'bad')))
      : h('p', { class: 'small muted' }, 'Löschen ist erst möglich, wenn der Status des Kunden „gekündigt“ oder „beendet“ ist.'));
}

export async function kostenKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/kosten'), m = h('div');
  const dienst = h('input', { placeholder: 'z. B. telefonie, domain, werbung', maxlength: 40 }), betrag = h('input', { type: 'number', step: '0.01', min: '0.01', placeholder: 'Betrag in €' }), tag = h('input', { type: 'date' });
  const speichern = knopf('Kosten eintragen', async () => { try { await api('/api/admin/kunden/' + kid + '/kosten', { method: 'POST', body: { dienst: dienst.value, betrag_eur: Number(betrag.value), datum: tag.value || null } }); location.reload(); } catch (x) { fehler(m, x); } }, 'btn');
  return h('div', { class: 'card' }, h('h2', {}, 'Kosten pro Monat'),
    h('p', { class: 'small muted' }, 'Monatlicher Umsatz laut aktiven Buchungen: ' + fmtEuro(d.umsatz_monat_cent) + '.' + (d.domains_jahr_cent ? ' Domains, die wir bezahlen: ' + fmtEuro(d.domains_jahr_cent) + ' pro Jahr (' + fmtEuro(Math.round(d.domains_jahr_cent / 12)) + ' pro Monat, noch nicht in den Kosten unten enthalten).' : '') + ' KI-Kosten werden automatisch aus den Tokens berechnet, alle anderen Kosten (Telefonie, Domain, Werbung …) trägst du hier von Hand ein.'),
    tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Tokens', z => z.tokens], ['Kosten gesamt', z => fmtEuro(Math.round(z.kosten_cent))], ['Anteil am Umsatz', z => d.umsatz_monat_cent ? (z.kosten_cent / d.umsatz_monat_cent * 100).toFixed(1).replace('.', ',') + ' %' : '–']], d.monate, 'Noch keine Kosten erfasst.'),
    d.dienste.length ? h('div', {}, h('h3', {}, 'Aufgeteilt nach Kostenart'), tabelle([['Monat', z => String(z.monat).slice(0, 7)], ['Kostenart', z => z.dienst], ['Kosten', z => fmtEuro(Math.round(z.kosten_cent))]], d.dienste)) : '',
    h('h3', {}, 'Kosten von Hand eintragen'), m, h('div', { class: 'row' }, dienst, betrag, tag, speichern));
}

export async function berichtTexte(id, m) {
  const b = await api('/api/admin/berichte/' + id);
  const ein = h('textarea', { rows: 5, maxlength: 3000 }, b.einordnung), sch = h('textarea', { rows: 5 }, b.schritte.join('\n'));
  const f = h('div', { class: 'card', style: 'border:1px solid var(--line)' }, h('h3', {}, b.titel + ': Einordnung und nächste Schritte'),
    h('p', { class: 'small muted' }, b.angepasst ? 'Von dir angepasst.' : 'Automatisch aus den Zahlen erzeugt. Du kannst ihn ändern, bevor der Bericht an den Kunden geht.'),
    h('label', {}, 'Einordnung'), ein, h('label', {}, 'Nächste Schritte (eine Zeile je Schritt)'), sch,
    h('div', { class: 'row', style: 'margin-top:10px' },
      knopf('KI-Entwurf', async () => { try { const k = await api('/api/admin/berichte/' + id + '/ki-entwurf', { method: 'POST' }); ein.value = k.einordnung; sch.value = k.schritte.join('\n'); melde(m, 'Entwurf eingesetzt. Bitte prüfen und speichern.', 'info'); } catch (x) { fehler(m, x); } }, 'sec small'),
      knopf('Zurück auf automatisch', () => { ein.value = ''; sch.value = ''; melde(m, 'Leer speichern setzt die automatische Einordnung wieder ein.', 'info'); }, 'sec small'),
      h('span', { class: 'grow' }),
      knopf('Speichern', async () => { try { await api('/api/admin/berichte/' + id, { method: 'PUT', body: { einordnung: ein.value, schritte: sch.value.split('\n') } }); melde(m, 'Gespeichert. Das PDF und die Kundenansicht zeigen jetzt diese Texte.', 'ok'); } catch (x) { fehler(m, x); } }, 'btn'),
      knopf('Speichern und erneut senden', async () => { if (!confirm('Bericht mit diesen Texten erneut an den Kunden senden?')) return; try { await api('/api/admin/berichte/' + id, { method: 'PUT', body: { einordnung: ein.value, schritte: sch.value.split('\n') } }); const r = await api('/api/admin/berichte/' + id + '/senden', { method: 'POST' }); melde(m, r.gesendet ? 'Gesendet.' : 'Nicht gesendet: ' + (r.grund || 'unbekannt'), r.gesendet ? 'ok' : 'info'); } catch (x) { fehler(m, x); } }, 'sec small')));
  m.after(f);
}

export async function berichteKarte(kid) {
  const liste = await api('/api/admin/kunden/' + kid + '/berichte'), m = h('div');
  const monate = []; const jetzt = new Date();
  for (let i = 1; i <= 12; i++) { const d = new Date(jetzt.getFullYear(), jetzt.getMonth() - i, 1); monate.push([d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'), d.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })]); }
  const sel = select('monat', monate, monate[0][0]);
  const los = async (senden) => { try { const r = await api('/api/admin/kunden/' + kid + '/bericht', { method: 'POST', body: { monat: sel.value, senden } });
    melde(m, senden ? (r.gesendet ? 'Bericht erstellt und per E-Mail gesendet.' : 'Bericht erstellt, aber nicht gesendet: ' + (r.grund || 'unbekannt')) : 'Bericht erstellt.', r.gesendet || !senden ? 'ok' : 'info'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Monatsberichte'), h('p', { class: 'small muted' }, 'Wird jeden Monat automatisch erstellt und an den Kunden gemailt (wenn der Versand eingerichtet ist). Hier kannst du einen Monat von Hand erstellen oder erneut senden.'), m,
    tabelle([['Monat', z => z.titel], ['Gesendet', z => z.versendet_am ? zeit(z.versendet_am) : 'nein'], ['PDF', z => h('a', { href: '/api/admin/berichte/' + z.id + '/pdf', target: '_blank', rel: 'noopener' }, 'Öffnen')], ['', z => knopf('Einordnung bearbeiten', () => berichtTexte(z.id, m), 'sec small')]], liste, 'Noch keine Berichte.'),
    h('div', { class: 'row', style: 'margin-top:12px' }, sel, knopf('Erstellen', () => los(false)), knopf('Erstellen und per Mail senden', () => los(true), 'btn')));
}

// ------------------------------------------------------------- Briefing und externe Zahlen (Kunde öffnen)
export async function briefingKarte(kid) {
  const d = await api('/api/admin/kunden/' + kid + '/briefing');
  const inhalt = d.struktur.map(a => [h('h3', {}, a.abschnitt), a.felder.map(f => h('div', { style: 'margin:6px 0' }, h('div', { class: 'small muted' }, f.frage), h('div', { class: 'freitext' }, d.daten[f.key] || '–')))]);
  return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { style: 'margin:0' }, 'Briefing'), d.status === 'abgeschickt' ? h('span', { class: 'pill ok' }, 'abgeschickt ' + zeit(d.abgeschickt_am)) : h('span', { class: 'pill warn' }, Object.keys(d.daten).length ? 'in Arbeit' : 'noch leer')),
    Object.keys(d.daten).length ? h('details', {}, h('summary', {}, 'Antworten anzeigen'), inhalt) : h('p', { class: 'small muted' }, 'Der Kunde hat das Briefing noch nicht ausgefüllt. Es erscheint in seinem Portal unter „Briefing“.'));
}

export async function externKarte(kid) {
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

/** Gestörte Websites: genauer Fehler, Ursache und Lösungsschritte (kommt von „Öffnen“ in der Kunden-Ampel). */
async function websiteProblemKarte(kid) {
  let liste = [];
  try { liste = await api('/api/admin/kunden/' + kid + '/website-probleme', { leise: true }); } catch { return ''; }
  if (!liste.length) return '';
  return h('div', { class: 'card', id: 'website-probleme' }, h('h2', {}, 'Website-Problem'),
    liste.map(p => h('div', { style: 'margin:8px 0' },
      h('div', { class: 'small muted' }, 'Seit ' + zeit(p.seit) + ' · zuletzt geprüft ' + zeit(p.geprueft_am)),
      p.erklaerung.map(erklaerungBox),
      h('div', { class: 'small muted', style: 'word-break:break-word' }, 'Technische Meldung: ' + (p.fehler || 'keine')))));
}

export async function kundeDetail(kid) {
  const d = await api('/api/admin/kunden/' + kid), k = d.kunde;
  const neu = () => { const s = location.hash; location.hash = ''; setTimeout(() => { location.hash = s; }, 0); };
  const mk = h('div'), mz = h('div'), mb = h('div'), mw = h('div'), mdaten = h('div'), mv = h('div');
  const partnerListe = await api('/api/admin/vertrieb/partnerliste');

  const refK = h('input', { type: 'checkbox', checked: k.referenzkunde, style: 'width:auto' }), refE = h('input', { type: 'checkbox', checked: k.referenz_nennen_erlaubt, style: 'width:auto' });
  const stamm = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const o = formular(e.target);
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
  const zugaenge = tabelle([['E-Mail', z => z.email], ['Rolle', z => ({ inhaber: 'Inhaber', mitarbeiter: 'Mitarbeiter', nur_lesen: 'Nur ansehen', empfang: 'Empfang' })[z.kunden_rolle] || z.kunden_rolle], ['Passwort', z => z.hat_passwort ? 'gesetzt' : 'offen'], ['2FA', (z) => z.totp_aktiv ? knopf('2FA zurücksetzen', async () => { if (confirm('Zwei-Faktor-Anmeldung dieses Zugangs ausschalten?')) { try { await api('/api/admin/benutzer/' + z.id + '/2fa-zuruecksetzen', { method: 'POST' }); location.reload(); } catch (x) { alert(x.message); } } }) : '–'], ['Letzter Login', z => zeit(z.letzter_login)],
    ['Zugang', z => h('button', { class: 'btn small ' + (z.aktiv ? 'bad' : 'sec'), onclick: async () => { try { await api('/api/admin/benutzer/' + z.id + '/aktiv', { method: 'POST', body: { aktiv: !z.aktiv } }); neu(); } catch (x) { alert(x.message); } } }, z.aktiv ? 'Sperren' : 'Freigeben')]], d.benutzer, 'Noch kein Zugang.');

  const prod = h('select', { name: 'produkt_code' }, paketListe.map(p => h('option', { value: p.code }, p.name + ' (' + p.code + ')')));
  const bform = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    const o = leerzu(formular(e.target)); o.rabatt_cent = Math.round(Number(o.rabatt_euro || 0) * 100); delete o.rabatt_euro;
    try { await api('/api/admin/kunden/' + kid + '/buchungen', { method: 'POST', body: o }); neu(); } catch (x) { melde(mb, x.message); }
  } }, h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Produkt'), prod), feld('Beginn', 'beginn', '', { type: 'date' }), feld('Rabatt in € / Monat', 'rabatt_euro', '', { type: 'number', step: '0.01', min: '0' }), feld('Rabatt-Grund', 'rabatt_grund'), feld('Standort', 'standort'), feld('Notiz', 'notiz')),
    h('p', {}, h('button', { class: 'btn' }, 'Buchung anlegen (Preis wird festgehalten)')));
  const bst = (z) => h('select', { onchange: async (e) => { try { await api('/api/admin/buchungen/' + z.id, { method: 'PATCH', body: { status: e.target.value } }); } catch (x) { alert(x.message); } } },
    ['angefragt', 'beauftragt', 'in_einrichtung', 'aktiv', 'pausiert', 'gekuendigt', 'beendet'].map(s => h('option', { value: s, selected: s === z.status }, s.replace('_', ' '))));
  const buchungen = tabelle([['Produkt', z => z.name], ['Einrichtung', z => euro(z.einrichtung_cent)], ['Monatlich', z => euro(z.monatlich_cent)], ['Rabatt', z => euro(z.rabatt_cent)], ['Beginn', z => datum(z.beginn)], ['Mindestlaufzeit bis', z => datum(z.mindestlaufzeit_ende)], ['Status', bst]], d.buchungen, 'Noch keine Buchungen.');

  const wform = h('form', { class: 'row', onsubmit: async (e) => {
    e.preventDefault(); try { await api('/api/admin/kunden/' + kid + '/websites', { method: 'POST', body: formular(e.target) }); neu(); } catch (x) { melde(mw, x.message); }
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
    kopf(k.firma, h('span', { class: 'pill' }, k.kundennummer), pill(k.status), k.referenzkunde ? h('span', { class: 'pill warn' }, 'Referenzkunde') : '', status, listenKnopf('kunden')),
    await websiteProblemKarte(kid),
    await zeitachseKarte(kid),
    h('div', { class: 'card' }, h('h2', {}, 'Stammdaten'), mk, stamm),
    await onboardingKarte(kid),
    await avvKarte(kid),
    await referenzKarte(kid, k),
    h('div', { class: 'card' }, h('h2', {}, 'Vertriebler'), mv, h('div', { class: 'row' }, h('div', { class: 'grow' }, h('select', { id: 'vsel' }, h('option', { value: '' }, '– kein Vertriebler –'), partnerListe.map(p => h('option', { value: p.id, selected: p.id === k.vertriebspartner_id }, p.name + (p.status !== 'aktiv' ? ' (' + p.status + ')' : ''))))),
      knopf('Zuordnen', async () => { try { await api('/api/admin/kunden/' + kid + '/partner', { method: 'PUT', body: { partner_id: el('vsel').value || null } }); melde(mv, 'Gespeichert.', 'ok'); } catch (x) { melde(mv, x.message); } }))),
    h('div', { class: 'card' }, h('h2', {}, 'Module des Kunden (Schalter)'), h('p', { class: 'small muted' }, 'Was hier aktiv ist, sieht der Kunde in seinem Portal.'), mz, module),
    h('div', { class: 'card' }, h('h2', {}, 'Portal-Zugang'), zugaenge, h('div', { class: 'row', style: 'margin-top:12px' }, h('div', { class: 'grow' }, mail), einladen), linkbox),
    h('div', { class: 'card' }, h('h2', {}, 'Buchungen'), mb, buchungen, h('h3', { style: 'margin-top:18px' }, 'Neue Buchung'), bform),
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), mw, webs, h('div', { style: 'height:10px' }), wform,
      h('p', { class: 'small muted' }, 'Domain ohne „www.“ eintragen (Hauptadresse). Danach auf dem Server einmal: mkctl site-add <domain>, damit Ordner und Webserver bereit sind.')),
    await sicher(() => belegeKarte(kid, k.referenzkunde)),
    await briefingKarte(kid),
    await sicher(() => nachrichtenKundeKarte(kid, k)),
    await freigabenKundeKarte(kid, k),
    await unterlagenKarte(kid),
    await berichteKarte(kid),
    await externKarte(kid),
    await domainKarte(kid),
    await diensteKarte(kid),
    await qrKarte('kunde', (k.ansprechpartner || '').split(' ')[0]),
    await kostenKarte(kid),
    brandingKarte(kid, k),
    await abrechnungKarte(kid),
    await auszugKarte(kid),
    offboardingKarte(kid, k, await api('/api/admin/kunden/' + kid + '/domains')),
    await historieKarte(kid),
    vorlagenKarte(kid, k),
    wissenKarte(kid),
    leistungsKarte(kid),
    aufgabenpaketKarte(kid),
    h('div', { class: 'card' }, h('h2', {}, 'Daten des Kunden'), tabs, mdaten));
}

