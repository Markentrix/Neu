import { h, api, datum, zeit, melde, zweiFaktorKarte, pushKarte, formular, dialog } from '../common.js';
import { inhaber, tabelle, statusPill, zeige, V, hat } from './kern.js';
import { anleitungSeite } from '../anleitung.js';

function anschriftKarte(k) {
  const m = h('div');
  const f = h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault();
    try { await api('/api/kunde/stammdaten', { method: 'PATCH', body: formular(e.target) }); melde(m, 'Gespeichert. Das Markentrix-Team wurde informiert und nutzt die Anschrift ab der nächsten Rechnung.', 'ok'); } catch (x) { melde(m, x.message); } } },
    h('div', {}, h('label', {}, 'Straße und Nr.'), h('input', { name: 'strasse', value: k.strasse || '' })),
    h('div', {}, h('label', {}, 'PLZ'), h('input', { name: 'plz', value: k.plz || '' })),
    h('div', {}, h('label', {}, 'Ort'), h('input', { name: 'ort', value: k.ort || '' })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Rechnungsanschrift'), h('p', { class: 'small muted' }, 'Firmenname oder Rechtsform ändern wir für dich: Schreib uns dazu unter Nachrichten.'), m, f);
}

V.willkommen = () => anleitungSeite('kunde', hat);
V.einstellungen = async () => {
  const p = await api('/api/kunde/profil');
  const vt = await api('/api/kunde/vertretung').catch(() => null), mv = h('div');
  const m1 = h('div'), m2 = h('div'), m3 = h('div');
  const k = p.kunde; const sw = { benachr_anfragen: k.benachr_anfragen, benachr_termine: k.benachr_termine, benachr_bericht: k.benachr_bericht, benachr_nachrichten: k.benachr_nachrichten };
  const kb = (label, key) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', checked: sw[key], style: 'width:auto', onchange: (e) => { sw[key] = e.target.checked; } }), label);
  const f3 = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/kunde/profil', { method: 'PATCH', body: { ...sw, benachr_email: e.target.benachr_email.value } }); melde(m3, 'Gespeichert.', 'ok'); } catch (x) { melde(m3, x.message); } } },
    h('div', {}, h('label', {}, 'Benachrichtigungen an (leer = deine Kontakt-E-Mail)'), h('input', { name: 'benachr_email', type: 'email', value: k.benachr_email || '' })),
    kb('Bei neuen Anfragen', 'benachr_anfragen'), kb('Erinnerung vor Terminen', 'benachr_termine'), kb('Monatsbericht per E-Mail', 'benachr_bericht'), kb('Antworten und Freigabe-Bitten vom Team', 'benachr_nachrichten'), h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  const f1 = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault();
    try { await api('/api/kunde/profil', { method: 'PATCH', body: formular(e.target) }); melde(m1, 'Gespeichert.', 'ok'); } catch (x) { melde(m1, x.message); }
  } },
    h('div', {}, h('label', {}, 'Ansprechpartner'), h('input', { name: 'ansprechpartner', value: k.ansprechpartner || '' })),
    h('div', {}, h('label', {}, 'E-Mail (Kontakt)'), h('input', { name: 'email', type: 'email', value: k.email || '' })),
    h('div', {}, h('label', {}, 'Telefon'), h('input', { name: 'telefon', value: k.telefon || '' })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Speichern')));
  const f2 = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault(); const d = formular(e.target);
    try { await api('/api/kunde/passwort', { method: 'POST', body: d }); melde(m2, 'Passwort geändert.', 'ok'); e.target.reset(); } catch (x) { melde(m2, x.message); }
  } },
    h('div', {}, h('label', {}, 'Aktuelles Passwort'), h('input', { name: 'alt', type: 'password', autocomplete: 'current-password', required: true })),
    h('div', {}, h('label', {}, 'Neues Passwort (mind. 10 Zeichen)'), h('input', { name: 'neu', type: 'password', autocomplete: 'new-password', minlength: 10, required: true })),
    h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Passwort ändern')));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Dein Konto'), h('p', {}, 'Kundennummer ', h('b', {}, k.kundennummer), ' · Paket ', h('b', {}, k.paket || '–'), ' · Login ', h('b', {}, p.login))),
    h('div', { class: 'card' }, h('h2', {}, 'Kontaktdaten'), m1, f1),
    inhaber() ? anschriftKarte(k) : '',
    vt ? h('div', { class: 'card' }, h('h2', {}, 'Vertretung (z. B. im Urlaub)'), h('p', { class: 'small muted' }, 'Eine zweite Person bekommt in diesem Zeitraum zusätzlich die E-Mails mit Freigabe-Bitten und Antworten. Sie kann über den Link in der Mail freigeben, ohne Zugang zum Portal.'), mv,
      h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); try { await api('/api/kunde/vertretung', { method: 'PUT', body: o }); melde(mv, 'Gespeichert.', 'ok'); } catch (x) { melde(mv, x.message); } } },
        h('div', {}, h('label', {}, 'Name'), h('input', { name: 'name', value: vt.name || '' })), h('div', {}, h('label', {}, 'E-Mail der Vertretung (leer = keine)'), h('input', { name: 'email', type: 'email', value: vt.email || '' })),
        h('div', {}, h('label', {}, 'Von'), h('input', { name: 'von', type: 'date', value: vt.von ? String(vt.von).slice(0, 10) : '' })), h('div', {}, h('label', {}, 'Bis'), h('input', { name: 'bis', type: 'date', value: vt.bis ? String(vt.bis).slice(0, 10) : '' })),
        h('div', {}, h('label', {}, ' '), h('button', { class: 'btn' }, 'Speichern')))) : '',
    h('div', { class: 'card' }, h('h2', {}, 'E-Mail-Benachrichtigungen'), h('p', { class: 'small muted' }, 'Wir schreiben dir, wenn etwas Wichtiges passiert.'), m3, f3),
    h('div', { class: 'card' }, h('h2', {}, 'Passwort'), m2, f2), pushKarte('kunde'), zweiFaktorKarte(),
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
  const aend = await api('/api/kunde/uav-aenderungen').catch(() => []);
  const widerspruch = (z) => { const grund = h('textarea', { rows: 3, maxlength: 1500, placeholder: 'Wichtiger datenschutzrechtlicher Grund' }), name = h('input', { placeholder: 'Vor- und Nachname', maxlength: 200 }), fm = h('div');
    dialog('Widerspruch einlegen: ' + z.name, h('div', { class: 'stack' }, h('label', {}, 'Begründung'), grund, h('label', {}, 'Dein Name'), name, fm,
      h('p', {}, h('button', { class: 'btn', onclick: async () => { try { await api('/api/kunde/uav-aenderungen/' + z.id + '/widerspruch', { method: 'POST', body: { grund: grund.value, name: name.value } }); location.reload(); } catch (x) { melde(fm, x.message); } } }, 'Widerspruch absenden')))); };
  const aendKarte = aend.length ? h('div', { class: 'card' }, h('h2', {}, 'Änderungen bei Unterauftragsverarbeitern'),
    h('p', { class: 'small muted' }, 'Wenn wir einen Dienstleister hinzufügen oder wechseln, kündigen wir das mindestens vier Wochen vorher an. Du kannst bis zum genannten Datum aus wichtigem datenschutzrechtlichem Grund widersprechen.'),
    tabelle([['Angekündigt', z => datum(z.erstellt_am)], ['Anbieter', z => z.name + ' – ' + z.leistung], ['Geplant ab', z => datum(z.wirksam_ab)],
      ['', z => z.widerspruch_am ? h('span', { class: 'pill warn' }, 'Widerspruch eingelegt') : z.widerspruch_moeglich ? h('button', { class: 'btn sec small', onclick: () => widerspruch(z) }, 'Widerspruch einlegen') : h('span', { class: 'muted small' }, 'Frist abgelaufen')]], aend)) : '';
  return h('div', { class: 'stack' }, offen.map(bestaetigen), aendKarte, h('div', { class: 'card' }, h('h2', {}, 'Vertrag zur Auftragsverarbeitung (AVV)'),
    h('p', { class: 'small muted' }, 'Hier liegt der bestätigte oder unterschriebene Vertrag, der regelt, wie Markentrix personenbezogene Daten in deinem Auftrag verarbeitet (Art. 28 DSGVO).'),
    tabelle([['Bestätigt / unterschrieben am', z => datum(z.unterschrieben_am)], ['Datei', z => z.datei_name || 'AVV'], ['', z => h('a', { class: 'btn sec small', href: '/api/kunde/avv/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Ansehen / Herunterladen')]], d, offen.length ? 'Noch nicht bestätigt.' : 'Noch kein Vertrag abgelegt.')));
};

V.team = async () => {
  const d = await api('/api/kunde/team'), m = h('div');
  const ROLLE = { inhaber: 'Inhaber (alles)', mitarbeiter: 'Mitarbeiter (ohne Team und Rechnungen)', nur_lesen: 'Nur ansehen' };
  const neu = h('form', { class: 'form2', onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target);
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
