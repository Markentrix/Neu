import { h, api, datum, dialog, zeit, euro, melde, zweiFaktorKarte, pushKarte, formular } from '../common.js';
import { V, fehler, feld, ich, knopf, kopf, pill, select, tabelle } from './kern.js';

// ---------------------------------------------------------------- Einstellungen
V.einstellungen = async () => {
  const d = await api('/api/admin/einstellungen');
  const m1 = h('div'), m2 = h('div'), m3 = h('div');
  const fs = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); o.port = Number(o.port);
    try { await api('/api/admin/einstellungen/smtp', { method: 'PUT', body: o }); melde(m1, 'Gespeichert.', 'ok'); } catch (x) { fehler(m1, x); } } },
    h('div', { class: 'form2' }, feld('Server (SMTP-Host) *', 'host', d.smtp.host, { required: true, placeholder: 'z. B. smtp.ionos.de' }), feld('Port *', 'port', d.smtp.port, { type: 'number', required: true }),
      h('div', {}, h('label', {}, 'Verschlüsselung'), select('sicherung', [['starttls', 'STARTTLS (Port 587)'], ['ssl', 'SSL (Port 465)'], ['keine', 'keine']], d.smtp.sicherung)),
      feld('Benutzername', 'benutzer', d.smtp.benutzer, { autocomplete: 'off' }),
      feld(d.smtp.passwort_gesetzt ? 'Passwort (leer lassen = unverändert)' : 'Passwort', 'passwort', '', { type: 'password', autocomplete: 'new-password' }),
      feld('Absender-Adresse *', 'absender', d.smtp.absender, { type: 'email', required: true, placeholder: 'info@markentrix.de' }), feld('Absender-Name', 'absender_name', d.smtp.absender_name)),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  const t = h('input', { type: 'email', placeholder: 'Testmail an …', style: 'max-width:280px' });
  const ft = h('div', { class: 'row' }, t, knopf('Testmail senden', async () => { try { await api('/api/admin/einstellungen/testmail', { method: 'POST', body: { an: t.value } }); melde(m1, 'Testmail wurde versendet.', 'ok'); } catch (x) { fehler(m1, x); } }));
  const fk = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); o.tageslimit = Number(o.tageslimit); o.preis_ein_eur = Number(o.preis_ein_eur); o.preis_aus_eur = Number(o.preis_aus_eur);
    try { await api('/api/admin/einstellungen/ki', { method: 'PUT', body: o }); melde(m2, 'Gespeichert.', 'ok'); e.target.api_key.value = ''; } catch (x) { fehler(m2, x); } } },
    h('div', { class: 'form2' }, feld(d.ki.key_gesetzt ? 'API-Key (leer lassen = unverändert)' : 'API-Key', 'api_key', '', { type: 'password', autocomplete: 'new-password', placeholder: 'sk-ant-…' }),
      feld('Modell', 'modell', d.ki.modell), feld('Nachrichten pro Kunde und Tag', 'tageslimit', d.ki.tageslimit, { type: 'number', min: 1, max: 1000 }),
        feld('Preis Eingabe, € je 1 Mio. Tokens', 'preis_ein_eur', d.ki.preis_ein_eur, { type: 'number', step: '0.01', min: 0 }), feld('Preis Ausgabe, € je 1 Mio. Tokens', 'preis_aus_eur', d.ki.preis_aus_eur, { type: 'number', step: '0.01', min: 0 })),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'stack' }, kopf('Einstellungen'),
    !d.geheimnis_ok ? h('div', { class: 'msg err' }, 'Das Server-Geheimnis (PORTAL_SECRET) fehlt. Bitte install.sh erneut ausführen, sonst können keine Zugangsdaten gespeichert werden.') : '',
    h('div', { class: 'card' }, h('h2', {}, 'E-Mail-Versand (SMTP)'), h('p', { class: 'small muted' }, 'Zugangsdaten deines Postfachs. Damit verschickt das Portal Einladungen und Passwort-Links automatisch. Das Passwort wird verschlüsselt gespeichert und nie wieder angezeigt.'), m1, fs, ft),
    await zustellungKarte(), await vertragKarte(), zweiFaktorKarte(), await sicherheitKarte(), pushKarte('admin'), await textvorlagenKarte(), await leitfadenKarte(), await zahlungKarte(), await telefonKarte(), await websiteCheckKarte(), await placesKarte(), await firmaKarte(), await benachrKarte(), await rechtKarte(), await avvEinstKarte(), await uavAenderungKarte(), await folgemailsKarte(), await buchungKarte(), ...(ich && ich.admin_rechte ? [] : [await mitarbeiterKarte()]),
    h('div', { class: 'card' }, h('h2', {}, 'KI-Assistent im Kunden-Chat'), h('p', { class: 'small muted' }, d.ki.key_gesetzt ? 'API-Key ist hinterlegt – der Chat antwortet direkt über das Portal.' : 'Noch kein API-Key – der Chat nutzt den n8n-Webhook, falls eingerichtet. Den Key gibt es in der Anthropic-Konsole (console.anthropic.com), getrennt vom Claude-Abo.'), m2, fk), m3);
};

export const kk = (label, wert, set) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', checked: wert, style: 'width:auto', onchange: (e) => set(e.target.checked) }), label);
export async function placesKarte() {
  const d = await api('/api/admin/einstellungen/places'), m = h('div');
  const key = h('input', { type: 'password', placeholder: d.key_gesetzt ? 'leer lassen = unverändert' : 'API-Schlüssel', autocomplete: 'new-password', maxlength: 300 });
  const speichern = async () => { try { await api('/api/admin/einstellungen/places', { method: 'PUT', body: { api_key: key.value } }); key.value = ''; melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Google-Bewertungen (Places API)'),
    h('p', { class: 'small muted' }, d.key_gesetzt ? 'Schlüssel ist hinterlegt. Die Kunden-Websites können ihre Google-Bewertungen anzeigen.' : 'Noch kein Schlüssel. Ohne ihn tragen Kunden Sterne und Anzahl von Hand ein. Schlüssel: Google Cloud → „Places API (New)“ aktivieren → API-Schlüssel erstellen, auf diese API beschränken. Abgerufen wird je Kunde höchstens alle 12 Stunden, nicht pro Besucher.'),
    m, h('div', { class: 'row' }, key, h('button', { class: 'btn', onclick: speichern }, 'Speichern')));
}

export async function websiteCheckKarte() {
  const d = await api('/api/admin/website-check'), m = h('div'), box = h('div');
  const erzeugen = async () => {
    if (d.aktiv && !confirm('Es gibt schon einen Schlüssel. Ein neuer ersetzt ihn, die Website muss dann den neuen bekommen. Fortfahren?')) return;
    try { const r = await api('/api/admin/website-check/schluessel', { method: 'POST', body: {} }); box.replaceChildren(h('div', { class: 'msg info' }, 'Neuer Schlüssel (wird nur jetzt angezeigt, bitte kopieren): ', h('br'), h('code', { style: 'word-break:break-all' }, r.schluessel))); } catch (x) { melde(m, x.message); }
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Website-Check → Leads'), h('p', { class: 'small muted' }, 'Wer den Website-Check auf markentrix.de nutzt, landet hier als Lead (mit Ergebnis). Adresse für die Website: ', h('code', {}, d.adresse), '. Status: ', d.aktiv ? h('span', { class: 'pill ok' }, 'Schlüssel gesetzt') : h('span', { class: 'pill warn' }, 'noch nicht eingerichtet')),
    m, box, h('p', {}, h('button', { class: 'btn sec', onclick: erzeugen }, d.aktiv ? 'Neuen Schlüssel erzeugen' : 'Schlüssel erzeugen')));
}

export async function firmaKarte() {
  const f = await api('/api/admin/einstellungen/firma'), m = h('div'); let klein = f.kleinunternehmer;
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); o.kleinunternehmer = klein; o.zahlungsziel_tage = Number(o.zahlungsziel_tage); o.mwst_satz = Number(o.mwst_satz);
    try { await api('/api/admin/einstellungen/firma', { method: 'PUT', body: o }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' }, feld('Firmenname', 'name', f.name), feld('Inhaber', 'inhaber', f.inhaber), feld('Straße', 'strasse', f.strasse), feld('PLZ', 'plz', f.plz), feld('Ort', 'ort', f.ort),
      feld('E-Mail', 'email', f.email), feld('Telefon', 'telefon', f.telefon), feld('Website', 'website', f.website), feld('USt-IdNr.', 'ustid', f.ustid), feld('Steuernummer', 'steuernummer', f.steuernummer),
      feld('IBAN', 'iban', f.iban), feld('BIC', 'bic', f.bic), feld('Bank', 'bank', f.bank), feld('Zahlungsziel (Tage)', 'zahlungsziel_tage', f.zahlungsziel_tage, { type: 'number', min: 0, max: 90 }),
      feld('Umsatzsteuer (%)', 'mwst_satz', f.mwst_satz, { type: 'number', min: 0, max: 30 }), feld('Rechnungs-Kürzel', 'rechnungsprefix', f.rechnungsprefix), feld('Angebots-Kürzel', 'angebotsprefix', f.angebotsprefix)),
    kk('Kleinunternehmer (§ 19 UStG, keine Umsatzsteuer auf Rechnungen)', klein, (v) => { klein = v; }),
    h('label', {}, 'Zusatztext unten auf Rechnungen und Angeboten (optional)'), h('textarea', { name: 'fusszeile', rows: 2 }, f.fusszeile || ''),
    h('label', {}, 'Bedingungen unter jedem Angebot (optional)'), h('textarea', { name: 'angebotsbedingungen', rows: 4, maxlength: 1500, placeholder: 'z. B. Es gelten unsere AGB. Preise netto zzgl. USt. Mindestlaufzeit und Kündigung gemäß Vertrag.' }, f.angebotsbedingungen || ''),
    h('p', { class: 'small muted' }, 'Erscheint im PDF und auf der Online-Angebotsseite. Den Text bitte selbst festlegen und rechtlich prüfen lassen (AGB, Laufzeit, Kündigung, Zahlungsbedingungen).'),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Firmendaten'), h('p', { class: 'small muted' }, 'Werden für Impressum, Datenschutz, Angebote, Rechnungen und Berichte verwendet. Bitte Angaben zu Steuern mit deiner Steuerberatung abstimmen.'), m, form);
}
export async function avvEinstKarte() {
  const r = await api('/api/admin/einstellungen/avv'), m = h('div');
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/admin/einstellungen/avv', { method: 'PUT', body: formular(e.target) }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('label', {}, 'Unterauftragsverarbeiter im AVV (eine Zeile je Firma: Name | Leistung | Modul | Verarbeitungsort | Grundlage Drittland). Leer lassen = Standardliste, die nach den gebuchten Modulen des Kunden gefiltert wird. Eine eigene Liste ersetzt sie vollständig.'),
    h('textarea', { name: 'unterauftragnehmer', rows: 6, placeholder: r.standard }, r.unterauftragnehmer || ''),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'AVV: Unterauftragsverarbeiter'),
    h('p', { class: 'small muted' }, 'Diese Liste steht in Anlage 3 jedes AVV. Bitte vollständig und aktuell halten (z. B. E-Mail-Anbieter, Telefonie-Dienst) und den Vertragstext einmal juristisch prüfen lassen.'), m, form);
}

const MODUL_NAMEN = { '': 'alle Kunden mit AVV', automationen: 'Automationen', email_auftragnehmer: 'E-Mail über Auftragnehmer-Konto', termin_auftragnehmer: 'Termine über Auftragnehmer-Konto', ki_chat: 'KI-Chat', telefon: 'Telefon-Assistent', whatsapp: 'WhatsApp', domain: 'Domainverwaltung', website: 'Website' };

/** Änderung bei Unterauftragsverarbeitern ankündigen: Mail an betroffene Kunden mit vier Wochen Vorlauf (AVV Ziff. 5 Abs. 2). */
export async function uavAenderungKarte() {
  const liste = await api('/api/admin/uav-aenderungen'), m = h('div');
  const frueh = new Date(Date.now() + 28 * 864e5).toISOString().slice(0, 10);
  const form = h('form', { class: 'stack', onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target);
    if (!confirm('Alle betroffenen Kunden bekommen jetzt eine Mail. Fortfahren?')) return;
    try { const r = await api('/api/admin/uav-aenderungen', { method: 'POST', body: o }); melde(m, r.kunden + ' Kunden betroffen, ' + r.gesendet + ' Mails gesendet' + (r.ohne_mail ? ', ' + r.ohne_mail + ' ohne E-Mail-Adresse oder Versandfehler' : '') + '. Bitte die Liste oben erst ab dem Datum ändern.', 'ok'); setTimeout(() => location.reload(), 2500); } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' },
      h('div', {}, h('label', {}, 'Art'), h('select', { name: 'art' }, h('option', { value: 'neu' }, 'neuer Anbieter'), h('option', { value: 'ersetzt' }, 'Anbieter wird ersetzt'))),
      h('div', {}, h('label', {}, 'Unternehmen'), h('input', { name: 'name', required: true, maxlength: 200 })),
      h('div', {}, h('label', {}, 'Leistung'), h('input', { name: 'leistung', required: true, maxlength: 400 })),
      h('div', {}, h('label', {}, 'Betrifft Modul'), h('select', { name: 'modul' }, Object.entries(MODUL_NAMEN).map(([k, t]) => h('option', { value: k }, t)))),
      h('div', {}, h('label', {}, 'Verarbeitungsort'), h('input', { name: 'ort', maxlength: 200 })),
      h('div', {}, h('label', {}, 'Geplant ab (mind. 4 Wochen)'), h('input', { name: 'wirksam_ab', type: 'date', min: frueh, value: frueh, required: true }))),
    h('label', {}, 'Hinweis für die Kunden (optional)'), h('textarea', { name: 'hinweis', rows: 3, maxlength: 1500 }),
    h('p', {}, h('button', { class: 'btn' }, 'Kunden informieren')));
  return h('div', { class: 'card' }, h('h2', {}, 'AVV: Änderung bei Unterauftragsverarbeitern ankündigen'),
    h('p', { class: 'small muted' }, 'Laut AVV musst du neue oder wechselnde Anbieter mindestens vier Wochen vorher in Textform ankündigen. Das Portal verschickt die Mail, merkt sich Zeitpunkt und Empfänger und nimmt Widersprüche der Kunden entgegen. Die Anbieterliste oben änderst du erst zum angekündigten Datum.'), m, form,
    liste.length ? tabelle([['Angekündigt', z => datum(z.erstellt_am)], ['Anbieter', z => z.name + (z.art === 'ersetzt' ? ' (Ersatz)' : '')], ['Ab', z => datum(z.wirksam_ab)], ['Kunden informiert', z => z.gesendet + ' von ' + z.kunden],
      ['Widersprüche', z => z.widersprueche ? h('span', { class: 'pill bad' }, z.widersprueche + ': ' + z.widerspruch_liste.map(w => w.firma).join(', ')) : '–']], liste) : h('p', { class: 'small muted' }, 'Bisher keine Änderung angekündigt.'));
}

export async function mitarbeiterKarte() {
  const d = await api('/api/admin/mitarbeiter'), m = h('div');
  const bereiche = Object.entries(d.bereiche);
  const boxen = (vor) => bereiche.map(([k, t]) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:4px 0' }, h('input', { type: 'checkbox', 'data-r': k, checked: vor === null || vor.includes(k), style: 'width:auto' }), t));
  const gew = (el) => [...el.querySelectorAll('input[data-r]')].filter(i => i.checked).map(i => i.dataset.r);
  const neuBoxen = h('div', {}, ...boxen([]));
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const x = e.target;
    try { const r = await api('/api/admin/mitarbeiter', { method: 'POST', body: { email: x.email.value, name: x.name.value || null, rechte: gew(neuBoxen) } }); melde(m, 'Eingeladen. Einladungslink (falls keine Mail ankommt): ' + r.link, 'ok'); } catch (z) { fehler(m, z); } } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'E-Mail'), h('input', { name: 'email', type: 'email', required: true })), h('div', {}, h('label', {}, 'Name'), h('input', { name: 'name' }))),
    h('label', {}, 'Darf zugreifen auf'), neuBoxen, h('p', {}, h('button', { class: 'btn' }, 'Mitarbeiter einladen')));
  const zeile = (b) => {
    if (b.admin_rechte === null) return h('span', { class: 'small muted' }, 'voller Zugriff');
    const bx = h('div', {}, ...boxen(b.admin_rechte));
    return h('div', {}, bx, h('span', { class: 'row' }, knopf('Rechte speichern', async () => { try { await api('/api/admin/mitarbeiter/' + b.id, { method: 'PATCH', body: { rechte: gew(bx) } }); melde(m, 'Gespeichert.', 'ok'); } catch (z) { fehler(m, z); } }, 'small'),
      knopf(b.aktiv ? 'Sperren' : 'Entsperren', async () => { try { await api('/api/admin/mitarbeiter/' + b.id, { method: 'PATCH', body: { aktiv: !b.aktiv } }); location.reload(); } catch (z) { fehler(m, z); } }, 'sec small')));
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Mitarbeiter & Rechte'), h('p', { class: 'small muted' }, 'Mitarbeiter bekommen nur die Bereiche, die du freigibst. Übersicht, Heute zu tun und Aufgaben sehen alle. Alle Änderungen landen im Protokoll.'), m,
    tabelle([['Name', b => b.name || '–'], ['E-Mail', b => b.email + (b.aktiv ? '' : ' (gesperrt)')], ['Rechte', zeile]], d.liste), h('h3', { style: 'margin-top:16px' }, 'Neuen Mitarbeiter einladen'), f);
}

export async function buchungKarte() {
  const d = await api('/api/admin/einstellungen/buchung'), liste = await api('/api/admin/gespraeche'), m = h('div');
  const tageN = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
  const cb = (n, w, t) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:6px 0' }, h('input', { type: 'checkbox', name: n, checked: w, style: 'width:auto' }), t);
  const wt = h('div', { class: 'row' }, ...tageN.map((t, i) => h('label', { style: 'display:flex;gap:4px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', 'data-wt': i + 1, checked: d.wochentage.includes(i + 1), style: 'width:auto' }), t)));
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const x = e.target;
    try { await api('/api/admin/einstellungen/buchung', { method: 'PUT', body: { aktiv: x.aktiv.checked, dauer: Number(x.dauer.value), tage: Number(x.tage.value), von: x.von.value, bis: x.bis.value,
      wochentage: [...wt.querySelectorAll('input')].filter(i => i.checked).map(i => Number(i.dataset.wt)), vorlauf_std: Number(x.vorlauf.value), ort: x.ort.value } }); melde(m, 'Gespeichert.', 'ok'); } catch (z) { fehler(m, z); } } },
    cb('aktiv', d.aktiv, 'Terminbuchung einschalten (öffentliche Seite: ' + location.origin + '/buchen)'),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Dauer (Minuten)'), h('input', { name: 'dauer', type: 'number', min: 15, max: 120, step: 5, value: d.dauer })), h('div', {}, h('label', {}, 'Wie viele Tage im Voraus'), h('input', { name: 'tage', type: 'number', min: 1, max: 60, value: d.tage }))),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Von (Uhr)'), h('input', { name: 'von', type: 'time', value: d.von })), h('div', {}, h('label', {}, 'Bis (Uhr)'), h('input', { name: 'bis', type: 'time', value: d.bis }))),
    h('label', {}, 'Wochentage'), wt,
    h('label', {}, 'Frühestens in (Stunden)'), h('input', { name: 'vorlauf', type: 'number', min: 0, max: 240, value: d.vorlauf_std }),
    h('label', {}, 'Ort / Hinweis in der Bestätigung'), h('input', { name: 'ort', value: d.ort }),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Terminbuchung'), h('p', { class: 'small muted' }, 'Interessenten buchen selbst ein Erstgespräch. Der Lead wird automatisch angelegt oder auf „Termin“ gesetzt, ihr bekommt eine Mail mit Kalendereinladung. Zeiten gelten für Deutschland.'), m, f,
    h('h3', { style: 'margin-top:16px' }, 'Kommende Gespräche'),
    tabelle([['Wann', g => datum(g.start) + ' ' + zeit(g.start)], ['Name', g => g.name], ['Kontakt', g => g.email + (g.telefon ? ' · ' + g.telefon : '')], ['Status', g => pill(g.status === 'gebucht' ? 'aktiv' : 'pausiert')], ['Nachricht', g => g.nachricht || '–']], liste, 'Noch keine Gespräche gebucht.'));
}

// ---------------------------------------------------------------- Zahlung, Telefon, Vorlagen, Frühwarnung
export async function zahlungKarte() {
  const d = await api('/api/admin/einstellungen/zahlung'), m = h('div'), l = d.lastschrift, w = d.mahnwesen;
  const cb = (n, v, t) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:6px 0' }, h('input', { type: 'checkbox', name: n, checked: v, style: 'width:auto' }), t);
  const num = (n, v, min, max) => h('input', { name: n, type: 'number', min, max, value: v });
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const x = e.target;
    try { await api('/api/admin/einstellungen/zahlung', { method: 'PUT', body: { glaeubiger_id: x.glaeubiger_id.value, vorab_tage: Number(x.vorab_tage.value), mahn_aktiv: x.mahn_aktiv.checked,
      tage_1: Number(x.tage_1.value), tage_2: Number(x.tage_2.value), tage_3: Number(x.tage_3.value), verzug_tage: Number(x.verzug_tage.value), verzug_dienste: x.verzug_dienste.checked } }); melde(m, 'Gespeichert.', 'ok'); } catch (z) { fehler(m, z); } } },
    h('h3', {}, 'SEPA-Lastschrift'),
    l.iban_da ? '' : h('div', { class: 'msg info' }, 'Bitte unter „Firmendaten“ deine IBAN eintragen, sie wird als Einzugskonto gebraucht.'),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Gläubiger-Identifikationsnummer'), h('input', { name: 'glaeubiger_id', value: l.glaeubiger_id, placeholder: 'DE98ZZZ09999999999' })),
      h('div', {}, h('label', {}, 'Ankündigung (Tage vor Einzug)'), num('vorab_tage', l.vorab_tage, 2, 14))),
    h('p', { class: 'small muted' }, 'Die Gläubiger-ID beantragst du kostenlos bei der Bundesbank (glaeubiger-id.bundesbank.de). Erst wenn sie eingetragen ist, können Kunden im Portal ein Mandat erteilen.'),
    h('h3', {}, 'Automatische Zahlungserinnerungen'),
    cb('mahn_aktiv', w.aktiv, 'Erinnerung und Mahnungen automatisch per Mail verschicken (werktags, nicht bei angekündigtem Einzug und nicht bei Referenzkunden)'),
    h('div', { class: 'form3' }, h('div', {}, h('label', {}, 'Zahlungserinnerung nach (Tagen)'), num('tage_1', w.tage_1, 1, 90)), h('div', {}, h('label', {}, '1. Mahnung nach'), num('tage_2', w.tage_2, 2, 120)), h('div', {}, h('label', {}, '2. Mahnung nach'), num('tage_3', w.tage_3, 3, 180))),
    h('h3', {}, 'Bei langem Zahlungsverzug'),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Wartungsplan pausieren, wenn eine Rechnung so viele Tage nach der 2. Mahnung noch offen ist (0 = nie)'), num('verzug_tage', w.verzug_tage || 0, 0, 180))),
    cb('verzug_dienste', w.verzug_dienste, 'Zusätzlich Formular und Terminbuchung der Kunden-Website pausieren (die Seite selbst bleibt online)'),
    h('p', { class: 'small muted' }, 'Sobald nichts Überfälliges mehr offen ist, wird automatisch alles wieder freigegeben. Du bekommst jedes Mal eine Meldung. Vertraglich vorher prüfen lassen, ob eine Pause zulässig ist.'),
    h('p', { class: 'small muted' }, 'Die Tage zählen ab dem Fälligkeitsdatum. Mahngebühren und Verzugszinsen werden nicht automatisch berechnet. Vor dem Einschalten bitte rechtlich prüfen lassen.'),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Zahlung & Mahnwesen'), m, f);
}

function telefonKunde(d, m) {
  const nr = h('input', { placeholder: 'Kundennummer', 'aria-label': 'Kundennummer', style: 'width:auto' }), aus = h('div');
  const schalter = h('input', { type: 'checkbox', id: 'tel-nur', checked: d.nur_pro_kunde });
  schalter.addEventListener('change', async () => {
    if (schalter.checked && !confirm('Danach funktionieren nur noch die Adressen je Kunde. Alle Telefon-Anbieter müssen vorher auf ihre eigene Adresse umgestellt sein. Fortfahren?')) { schalter.checked = false; return; }
    try { await api('/api/admin/einstellungen/telefon/nur-pro-kunde', { method: 'POST', body: { aktiv: schalter.checked } }); } catch (x) { schalter.checked = !schalter.checked; fehler(m, x); } });
  return h('div', { class: 'small', style: 'margin:8px 0' }, h('b', {}, 'Eigene Adresse je Kunde (empfohlen): '),
    'Jeder Kunde bekommt ein eigenes Geheimnis. Wird eine Adresse bekannt, gilt sie nur für diesen Kunden. ', nr, ' ',
    knopf('Adresse zeigen', async () => { try { const r = await api('/api/admin/kunden/' + encodeURIComponent(nr.value.trim()) + '/telefon-adresse'); aus.replaceChildren(h('code', {}, r.url)); } catch (x) { fehler(m, x); } }), aus,
    h('div', {}, schalter, ' ', h('label', { for: 'tel-nur' }, 'Gemeinsames Geheimnis abschalten (nur noch Adressen je Kunde)')));
}

export async function telefonKarte() {
  const d = await api('/api/admin/einstellungen/telefon'), m = h('div'), box = h('div');
  return h('div', { class: 'card' }, h('h2', {}, 'Telefon-Assistent (Anrufprotokoll)'),
    h('p', { class: 'small muted' }, 'Der Anbieter des Telefon-Assistenten (z. B. Famulor) schickt nach jedem Gespräch eine Nachricht an das Portal. Eingehende Anrufe erscheinen beim Kunden unter „Anrufe“ und als Anfrage. Gesprächsaufzeichnungen und Texte werden nicht gespeichert, nur eine Zusammenfassung. Nummern und Namen werden nach 180 Tagen entfernt.'),
    m, h('p', { class: 'small' }, 'Webhook-Adresse (KUNDENNUMMER ersetzen): ', h('code', {}, d.url + '?s=GEHEIMNIS')), h('p', { class: 'small muted' }, d.geheimnis_gesetzt ? 'Ein Geheimnis ist gesetzt. Ein neues macht das alte ungültig.' : 'Noch kein Geheimnis gesetzt.'),
    d.letzte_nachricht ? h('div', { class: 'small', style: 'margin:8px 0' }, h('b', {}, 'Letzte Nachricht des Anbieters: '), zeit(d.letzte_nachricht.zeit), ' (Kunde ' + d.letzte_nachricht.kunde + ')',
      h('div', {}, 'Erkannt: ', Object.entries(d.letzte_nachricht.erkannt).map(([k, v]) => k + ' ← ' + v).join(', ') || 'nichts'),
      h('div', { class: d.letzte_nachricht.nicht_erkannt.length ? 'muted' : '' }, 'Nicht gefunden: ' + (d.letzte_nachricht.nicht_erkannt.join(', ') || 'nichts')),
      h('details', {}, h('summary', {}, 'Alle gesendeten Feldnamen'), h('code', {}, d.letzte_nachricht.felder.join(', ')))) : h('p', { class: 'small muted' }, 'Es ist noch keine Nachricht eingegangen. Nach einem Testanruf siehst du hier, welche Felder der Anbieter sendet (nur Feldnamen, keine Inhalte).'),
    d.geheimnis_gesetzt ? telefonKunde(d, m) : null,
    h('p', {}, knopf(d.geheimnis_gesetzt ? 'Neues Geheimnis erzeugen' : 'Geheimnis erzeugen', async () => {
      if (d.geheimnis_gesetzt && !confirm('Das alte Geheimnis wird ungültig. Alle Webhooks müssen angepasst werden. Fortfahren?')) return;
      try { const r = await api('/api/admin/einstellungen/telefon/neues-geheimnis', { method: 'POST' }); box.replaceChildren(h('div', { class: 'msg ok' }, 'Dein Geheimnis (wird nur jetzt angezeigt): ', h('code', {}, r.geheimnis))); } catch (x) { fehler(m, x); } })), box);
}

export async function lastschriftKarte() {
  const d = await api('/api/admin/lastschrift'), m = h('div');
  if (!d.konfiguriert && !d.bereit.length && !d.angekuendigt.length) return h('div', { class: 'card' }, h('h2', {}, 'Lastschrift-Einzug'), h('p', { class: 'muted small' }, 'Noch nicht eingerichtet: Gläubiger-ID unter Einstellungen → Zahlung & Mahnwesen und IBAN in den Firmendaten eintragen. Danach können Kunden im Portal ein Mandat erteilen.'));
  const gewaehlt = new Set(d.bereit.map(z => z.id));
  const morgen = new Date(Date.now() + (d.vorab_tage + 1) * 864e5); while ([0, 6].includes(morgen.getDay())) morgen.setDate(morgen.getDate() + 1);
  const tag = h('input', { type: 'date', value: morgen.toISOString().slice(0, 10), style: 'width:auto' });
  const export_ = async () => {
    if (!gewaehlt.size) { melde(m, 'Bitte mindestens eine Rechnung auswählen.'); return; }
    try {
      const r = await fetch('/api/admin/lastschrift/export', { method: 'POST', headers: { 'X-MK': '1', 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify({ beleg_ids: [...gewaehlt], einzug_am: tag.value }) });
      if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.detail || 'Fehler ' + r.status); }
      const a = h('a', { href: URL.createObjectURL(await r.blob()), download: 'lastschrift-' + tag.value + '.xml' }); document.body.append(a); a.click(); a.remove();
      melde(m, 'Datei erstellt. Bitte im Online-Banking als SEPA-Sammellastschrift hochladen. Die Kunden bekommen die Ankündigung per Mail.', 'ok'); setTimeout(() => location.reload(), 2500);
    } catch (x) { fehler(m, x); }
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Lastschrift-Einzug'), m,
    h('p', { class: 'small muted' }, 'Rechnungen von Kunden mit Mandat. Du erstellst eine Datei (pain.008), lädst sie im Online-Banking hoch, und der Kontoauszug-Abgleich bucht den Zahlungseingang. Die Kunden werden mindestens ' + d.vorab_tage + ' Tage vorher informiert.'),
    d.bereit.length ? [tabelle([['', z => h('input', { type: 'checkbox', checked: true, style: 'width:auto', onchange: (e) => { e.target.checked ? gewaehlt.add(z.id) : gewaehlt.delete(z.id); } })], ['Rechnung', z => z.nummer], ['Kunde', z => z.kundennummer + ' ' + z.firma], ['Fällig', z => datum(z.faellig_am)], ['Betrag', z => euro(z.offen_cent)], ['Konto', z => '…' + z.iban_ende]], d.bereit),
      h('div', { class: 'row', style: 'margin-top:10px' }, h('label', { style: 'margin:0' }, 'Einzug am'), tag, knopf('Einzugsdatei erstellen', export_, ''))] : h('p', { class: 'muted' }, 'Keine offenen Rechnungen mit Mandat.'),
    d.angekuendigt.length ? [h('h3', { style: 'margin-top:16px' }, 'Angekündigt'), tabelle([['Rechnung', z => z.nummer], ['Kunde', z => z.firma], ['Einzug am', z => datum(z.einzug_am)], ['Betrag', z => euro(z.offen_cent)],
      ['', z => knopf('Zurücksetzen', async () => { if (confirm('Einzug zurücksetzen (z. B. bei Rücklastschrift)?')) { try { await api('/api/admin/lastschrift/zuruecksetzen', { method: 'POST', body: { beleg_id: z.id } }); location.reload(); } catch (x) { fehler(m, x); } } })]], d.angekuendigt)] : '');
}

export async function folgemailsKarte() {
  const d = await api('/api/admin/einstellungen/folgemails'), m = h('div');
  const feld_ = (n, w, o = {}) => h('input', { name: n, value: w, ...o }), area = (n, w, r = 6) => h('textarea', { name: n, rows: r }, w);
  const cb = (n, w, t) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:6px 0' }, h('input', { type: 'checkbox', name: n, checked: w, style: 'width:auto' }), t);
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const x = e.target;
    try { await api('/api/admin/einstellungen/folgemails', { method: 'PUT', body: { aktiv: x.aktiv.checked, kunden_feedback: x.kunden_feedback.checked, tage_1: Number(x.tage_1.value), tage_2: Number(x.tage_2.value),
      betreff_1: x.betreff_1.value, text_1: x.text_1.value, betreff_2: x.betreff_2.value, text_2: x.text_2.value } }); melde(m, 'Gespeichert.', 'ok'); } catch (z) { fehler(m, z); } } },
    cb('aktiv', d.aktiv, 'Folgemails an Leads automatisch senden (nur an Leads mit Einwilligung, die noch nicht geantwortet oder einen Termin gebucht haben)'),
    cb('kunden_feedback', d.kunden_feedback, 'Kunden 30 Tage nach Start um Feedback bitten (eine Mail)'),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, '1. Mail nach (Tagen)'), feld_('tage_1', d.tage_1, { type: 'number', min: 1, max: 30 })), h('div', {}, h('label', {}, '2. Mail nach (Tagen)'), feld_('tage_2', d.tage_2, { type: 'number', min: 2, max: 60 }))),
    h('label', {}, 'Betreff der 1. Mail'), feld_('betreff_1', d.betreff_1), h('label', {}, 'Text der 1. Mail (Platzhalter: {name}, {firma}, {buchen})'), area('text_1', d.text_1),
    h('label', {}, 'Betreff der 2. Mail'), feld_('betreff_2', d.betreff_2), h('label', {}, 'Text der 2. Mail'), area('text_2', d.text_2),
    h('p', { class: 'small muted' }, 'Jede Mail enthält automatisch deine Grußformel und einen Abmeldelink. Standardmäßig ist alles aus. Vor dem Einschalten bitte rechtlich prüfen lassen (UWG § 7, siehe Anwalts-Checkliste).'),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Folgemails'), m, f);
}

export async function rechtKarte() {
  const r = await api('/api/admin/einstellungen/recht'), m = h('div');
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); try { await api('/api/admin/einstellungen/recht', { method: 'PUT', body: formular(e.target) }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('label', {}, 'Impressum (leer lassen = Standardtext aus den Firmendaten)'), h('textarea', { name: 'impressum', rows: 6, placeholder: r.impressum_standard }, r.impressum || ''),
    r.nutzung_fehlt ? h('div', { class: 'msg err' }, 'Deine eigene Datenschutzerklärung nennt die Nutzungsstatistik noch nicht (Seitenzählung ohne Inhalte). ', h('button', { type: 'button', class: 'btn small', onclick: (e) => { const t = e.target.closest('form').querySelector('textarea[name=datenschutz]'); t.value = t.value.trimEnd() + '\n\n' + r.nutzung_satz; t.focus(); e.target.disabled = true; } }, 'Satz am Ende einfügen'), ' Danach bitte speichern.') : '',
    h('label', {}, 'Datenschutzerklärung (leer lassen = Standardvorlage)'), h('textarea', { name: 'datenschutz', rows: 10, placeholder: r.datenschutz_standard }, r.datenschutz || ''),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern'), ' ', h('a', { class: 'btn sec', href: '/impressum', target: '_blank' }, 'Impressum ansehen'), ' ', h('a', { class: 'btn sec', href: '/datenschutz', target: '_blank' }, 'Datenschutz ansehen')));
  return h('div', { class: 'card' }, h('h2', {}, 'Impressum und Datenschutz'), h('p', { class: 'small muted' }, 'Die Standardtexte sind eine Vorlage und ersetzen keine Rechtsberatung. Bitte einmal von einem Anwalt oder Datenschutzbeauftragten prüfen lassen und bei Bedarf hier überschreiben. Die Links erscheinen automatisch auf der Anmeldeseite.'), m, form);
}

export async function benachrKarte() {
  const c = await api('/api/admin/einstellungen/benachrichtigung'), m = h('div'); const v = { ...c };
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); o.termin_stunden = Number(o.termin_stunden);
    Object.assign(o, { anfrage_mails: v.anfrage_mails, termin_erinnerung: v.termin_erinnerung, monatsbericht: v.monatsbericht });
    try { await api('/api/admin/einstellungen/benachrichtigung', { method: 'PUT', body: o }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' }, feld('Alarm-E-Mail für dich (leer = erster Admin)', 'alarm_email', c.alarm_email, { type: 'email' }), feld('Terminerinnerung (Stunden vorher)', 'termin_stunden', c.termin_stunden, { type: 'number', min: 1, max: 168 })),
    kk('Kunden per Mail über neue Anfragen informieren', c.anfrage_mails, (x) => { v.anfrage_mails = x; }),
    kk('Kunden an Termine erinnern', c.termin_erinnerung, (x) => { v.termin_erinnerung = x; }),
    kk('Monatsbericht automatisch am Monatsanfang an Kunden senden', c.monatsbericht, (x) => { v.monatsbericht = x; }),
    h('p', {}, h('button', { class: 'btn' }, 'Speichern')));
  return h('div', { class: 'card' }, h('h2', {}, 'Benachrichtigungen'), h('p', { class: 'small muted' }, 'Jeder Kunde kann diese Mails in seinem Portal unter Einstellungen einzeln abschalten. Für dich: Fehler in Automationen und Server-Alarme kommen an die Alarm-E-Mail.'), m, form);
}



/** Textvorlagen: Mails mit Platzhaltern und Aufgabenpakete, die bei Antworten, Sammelmails und Kunden benutzt werden. */
export async function textvorlagenKarte() {
  const box = h('div'), m = h('div');
  const bearbeiten = (v) => {
    const art = v ? v.art : 'mail', fm = h('div');
    const name = h('input', { maxlength: 80, value: v ? v.name : '', 'aria-label': 'Name' }), betreff = h('input', { maxlength: 200, value: v && v.betreff || '', 'aria-label': 'Betreff' });
    const text = h('textarea', { rows: 10, maxlength: 8000, 'aria-label': 'Text' }, v && v.text || '');
    const aufg = h('textarea', { rows: 10, 'aria-label': 'Aufgaben' }, v && v.aufgaben ? v.aufgaben.map(a => a.titel + ' | ' + a.tage).join('\n') : '');
    const artSel = h('select', { 'aria-label': 'Art', disabled: !!v, onchange: () => { felder(); } }, h('option', { value: 'mail', selected: art === 'mail' }, 'Mail-Vorlage'), h('option', { value: 'aufgaben', selected: art === 'aufgaben' }, 'Aufgabenpaket'));
    const mailFelder = h('div', {}, h('label', {}, 'Betreff'), betreff, h('label', {}, 'Text (Platzhalter: {firma}, {name}, {kundennummer}, {ort})'), text);
    const aufgFelder = h('div', {}, h('label', {}, 'Aufgaben (eine pro Zeile, danach „| Tage bis fällig“)'), aufg);
    const felder = () => { mailFelder.hidden = artSel.value !== 'mail'; aufgFelder.hidden = artSel.value !== 'aufgaben'; };
    felder();
    const d = dialog(v ? 'Vorlage bearbeiten' : 'Neue Vorlage', h('div', {}, h('label', {}, 'Art'), artSel, h('label', {}, 'Name'), name, mailFelder, aufgFelder, fm,
      h('p', { class: 'row' }, knopf('Speichern', async () => {
        const body = { art: artSel.value, name: name.value, betreff: betreff.value || null, text: text.value || null,
          aufgaben: aufg.value.split('\n').map(z => z.trim()).filter(Boolean).map(z => { const [t, tage] = z.split('|'); return { titel: t.trim(), tage: parseInt((tage || '0').trim(), 10) || 0 }; }) };
        if (body.art === 'aufgaben') { body.text = null; body.betreff = null; } else body.aufgaben = [];
        try { await api('/api/admin/textvorlagen' + (v ? '/' + v.id : ''), { method: v ? 'PUT' : 'POST', body }); d.zu(); laden(); } catch (x) { fehler(fm, x); }
      }, 'btn'), v ? knopf('Löschen', async () => { if (!confirm('Vorlage „' + v.name + '“ löschen?')) return; try { await api('/api/admin/textvorlagen/' + v.id, { method: 'DELETE' }); d.zu(); laden(); } catch (x) { fehler(fm, x); } }, 'sec') : '')));
  };
  const laden = async () => {
    try {
      const liste = await api('/api/admin/textvorlagen');
      box.replaceChildren(tabelle([['Name', z => z.name], ['Art', z => z.art === 'mail' ? 'Mail' : 'Aufgabenpaket (' + z.aufgaben.length + ')'], ['', z => knopf('Bearbeiten', () => bearbeiten(z), 'sec')]], liste, 'Noch keine Vorlagen.'));
    } catch (x) { fehler(m, x); }
  };
  await laden();
  return h('div', { class: 'card' }, h('h2', {}, 'Textvorlagen'),
    h('p', { class: 'small muted' }, 'Mail-Vorlagen (z. B. Willkommen, Rückfrage, Terminbestätigung) kannst du bei Nachrichten-Antworten und Sammelmails einfügen. Aufgabenpakete legst du beim Kunden mit einem Klick an. Platzhalter wie {firma} und {name} werden automatisch ersetzt.'),
    m, box, h('p', {}, knopf('+ Neue Vorlage', () => bearbeiten(null), 'btn')));
}

/** Gesprächsleitfaden für den Vertrieb: Standardtext, anpassbar im einfachen Textformat. */
export async function leitfadenKarte() {
  const m = h('div');
  let d;
  try { d = await api('/api/admin/einstellungen/leitfaden'); } catch (x) { fehler(m, x); return h('div', { class: 'card' }, h('h2', {}, 'Gesprächsleitfaden'), m); }
  const text = h('textarea', { rows: 18, 'aria-label': 'Leitfaden-Text', style: 'font-family:ui-monospace,monospace;font-size:13px' });
  text.value = d.text;
  const speichern = async (body, ok) => { try { await api('/api/admin/einstellungen/leitfaden', { method: 'PUT', body }); text.value = (await api('/api/admin/einstellungen/leitfaden')).text; melde(m, ok, 'ok'); } catch (x) { fehler(m, x); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Gesprächsleitfaden für den Vertrieb'),
    h('p', { class: 'small muted' }, (d.angepasst ? 'Angepasste Fassung ist aktiv. ' : 'Standardfassung ist aktiv. ') + 'Aufbau: „[Abschnitt] Titel“ mit Zeilen „- Punkt“, „[Einwand] Text“ mit Antwort darunter, „[Branche] kuerzel | Name“ mit „- Tipp“ und „[Mail] Betreff“ mit dem Mailtext (Platzhalter {firma}, {name}, {vertriebler}). Bitte keine Preise oder Zusagen aufnehmen und rechtliche Formulierungen prüfen lassen.'),
    m, text, h('p', { class: 'row' }, knopf('Speichern', () => speichern({ text: text.value }, 'Leitfaden gespeichert.'), 'btn'),
      knopf('Auf Standard zurücksetzen', () => { if (confirm('Den angepassten Leitfaden verwerfen und die Standardfassung verwenden?')) speichern({ standard: true }, 'Standard wiederhergestellt.'); }, 'sec')));
}


export async function zustellungKarte() {
  const d = await api('/api/admin/zustellung').catch(() => null), m = h('div');
  if (!d) return '';
  const TXT = { ok: ['ok', 'in Ordnung'], warn: ['warn', 'prüfen'], fehlt: ['bad', 'fehlt'], unbekannt: ['', 'unbekannt'] };
  const chips = (dns) => h('span', {}, ['spf', 'dkim', 'dmarc'].map(n => h('span', { class: 'pill ' + TXT[dns[n]][0], style: 'margin-right:6px', title: (dns.details || {})[n] || '' }, n.toUpperCase() + ': ' + TXT[dns[n]][1])));
  const k = d.kennzahlen;
  const pruefen = async (e) => { e.target.disabled = true; try { await api('/api/admin/zustellung/pruefen', { method: 'POST', body: {} }); location.reload(); } catch (x) { fehler(m, x); e.target.disabled = false; } };
  return h('div', { class: 'card' }, h('h2', {}, 'Mail-Zustellbarkeit'),
    h('p', { class: 'small muted' }, 'Ohne SPF und DKIM landen Mails von deiner Domain häufiger im Spam. Täglich um etwa 5 Uhr wird geprüft; bei Problemen mit deiner Absender-Domain bekommst du eine Push-Nachricht. Hinweis: Rückläufer, die der Zielserver erst später meldet, sieht das Portal nicht, nur was der Versandserver sofort zurückgibt.'),
    m, d.system ? h('p', {}, h('b', {}, d.system.domain + ': '), chips(d.system), h('span', { class: 'small muted' }, ' geprüft ' + zeit(d.system.geprueft_am))) : h('p', { class: 'small muted' }, 'Noch keine Absender-Adresse eingerichtet.'),
    d.system ? ['spf', 'dkim', 'dmarc'].filter(n => d.system[n] === 'fehlt' || d.system[n] === 'warn').map(n => h('p', { class: 'small' }, (d.system.details || {})[n])) : '',
    h('p', {}, 'Letzte 7 Tage: ', h('b', {}, String(k.gesamt)), ' Mails, ', h('b', {}, String(k.fehler)), ' Fehler' + (k.adresse ? ' (' + k.adresse + ' ungültige Empfänger)' : '') + (k.technisch ? ', ' + k.technisch + ' technische' : '') + '.'),
    k.letzte_fehler.length ? h('details', {}, h('summary', {}, 'Letzte Fehler'), k.letzte_fehler.map(f => h('p', { class: 'small' }, zeit(f.zeit) + ' · ' + f.art + ' · ' + (f.an_domain || '') + ' · ' + (f.fehler || '')))) : '',
    d.kunden.length ? h('div', {}, h('h3', {}, 'Eigene Postfächer der Kunden'), tabelle([['Kunde', z => z.firma], ['Absender', z => z.absender], ['Einträge', z => z.dns ? chips(z.dns) : ''], ['30 Tage', z => z.fehler30 + ' Fehler von ' + z.gesamt30]], d.kunden)) : '',
    h('p', {}, h('button', { class: 'btn sec', onclick: pruefen }, 'Jetzt neu prüfen')));
}


export async function vertragKarte() {
  const d = await api('/api/admin/einstellungen/vertrag').catch(() => null), m = h('div');
  if (!d) return '';
  const frist = h('input', { type: 'number', min: 0, max: 365, value: d.kuendigungsfrist_tage, style: 'max-width:120px' });
  return h('div', { class: 'card' }, h('h2', {}, 'Kündigung durch Kunden'),
    h('p', { class: 'small muted' }, 'Kunden kündigen im Portal verbindlich. Das Vertragsende ist das Monatsende nach Ablauf dieser Frist, frühestens am Ende der Mindestlaufzeit (aus der Buchung). Zum Vertragsende setzt der Server den Kunden automatisch auf „gekündigt“. Die Frist muss zu deinen AGB passen.'),
    m, h('div', { class: 'row' }, h('label', {}, 'Kündigungsfrist in Tagen'), frist,
      knopf('Speichern', async () => { try { await api('/api/admin/einstellungen/vertrag', { method: 'PUT', body: { kuendigungsfrist_tage: Number(frist.value) } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } }, 'btn')));
}


/** Wer hat die Zwei-Faktor-Anmeldung? Für Vertriebs-Zugänge lässt sie sich zur Pflicht machen (bei Admins ist sie es immer). */
async function sicherheitKarte() {
  const d = await api('/api/admin/sicherheit'), m = h('div');
  const pflicht = h('input', { type: 'checkbox', style: 'width:auto', checked: d.vertrieb_pflicht });
  pflicht.addEventListener('change', async () => {
    if (pflicht.checked && !confirm('Vertriebs-Zugänge ohne Zwei-Faktor-Anmeldung kommen danach nicht mehr ins Partnerportal, bis sie die App eingerichtet haben. Jetzt zur Pflicht machen?')) { pflicht.checked = false; return; }
    try { await api('/api/admin/sicherheit', { method: 'PUT', body: { vertrieb_2fa: pflicht.checked } }); melde(m, pflicht.checked ? 'Für Vertriebs-Zugänge ist die Zwei-Faktor-Anmeldung jetzt Pflicht.' : 'Gespeichert.', 'ok'); }
    catch (x) { pflicht.checked = !pflicht.checked; melde(m, x.message); }
  });
  const ohne = d.konten.filter(k => !k.totp_aktiv);
  return h('div', { class: 'card' }, h('h2', {}, 'Sicherheit: Zwei-Faktor-Anmeldung'),
    h('p', { class: 'small muted' }, 'Admin-Zugänge brauchen sie immer' + (d.admin_pflicht ? '' : ' (hier per Server-Einstellung abgeschaltet)') + '. Für Vertriebs-Zugänge kannst du sie vorschreiben.'),
    ohne.length ? h('p', {}, h('span', { class: 'pill warn' }, ohne.length + ' ohne 2FA'), ' ' + ohne.map(k => k.email).join(', ')) : h('p', {}, h('span', { class: 'pill ok' }, 'alle Konten geschützt')),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;margin:8px 0' }, pflicht, 'Zwei-Faktor-Anmeldung für Vertriebs-Zugänge verpflichtend'), m,
    h('div', { class: 'tablewrap' }, h('table', {}, h('thead', {}, h('tr', {}, ['E-Mail', 'Rolle', '2FA', 'Letzter Login'].map(t => h('th', {}, t)))),
      h('tbody', {}, d.konten.map(k => h('tr', {}, h('td', {}, k.email), h('td', {}, k.rolle === 'admin' ? 'Admin' : 'Vertrieb'), h('td', {}, h('span', { class: 'pill ' + (k.totp_aktiv ? 'ok' : 'warn') }, k.totp_aktiv ? 'aktiv' : 'fehlt')), h('td', {}, k.letzter_login ? zeit(k.letzter_login) : '–')))))));
}
