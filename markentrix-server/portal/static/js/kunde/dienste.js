import { h, api, melde, datum, zeit, toast } from '../common.js';
import { V, zeige } from './kern.js';

/** @param {string} t @param {Element[]|string[]} inhalt */
const hilfe = (t, ...inhalt) => h('details', { class: 'hilfe' }, h('summary', {}, t), h('div', { class: 'small', style: 'margin-top:6px' }, ...inhalt));
const feld = (label, el, tipp) => h('div', {}, h('label', {}, label), el, tipp ? h('div', { class: 'small muted' }, tipp) : '');
const schalter = (an, text) => { const c = h('input', { type: 'checkbox', checked: an, style: 'width:auto' }); return { c, el: h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-weight:600' }, c, text) }; };
const ZEIT = (x) => (x ? zeit(x) : '');

/** Kleine Statuszeile je Dienst: letzte Nutzung und Fehler der letzten 30 Tage. */
function statusZeile(s, art, wort) {
  const e = (s || {})[art];
  if (!e || (!e.ok && !e.fehler)) return h('p', { class: 'small muted' }, 'Noch nichts über die Website gelaufen.');
  const letzte = e.letzte;
  return h('p', { class: 'small' }, h('span', { class: 'pill ' + (e.fehler ? 'warn' : 'ok') }, e.fehler ? e.fehler + ' Fehler' : 'läuft'), ' ',
    (e.ok || 0) + ' ' + wort + ' in 30 Tagen. ' + (letzte && !letzte.ok && letzte.hinweis ? 'Zuletzt: ' + letzte.hinweis : ''));
}

V.dienste = async () => {
  const d = await api('/api/kunde/website-dienste');
  const neu = () => zeige();
  return h('div', { class: 'stack' },
    h('div', { class: 'top' }, h('h1', {}, 'Website-Dienste')),
    h('div', { class: 'card' }, h('p', {}, 'Hier trägst du ein, was deine Website braucht: wohin Anfragen gehen, welcher Kalender gilt, dein PayPal und deine Google-Bewertungen. Wir bauen es in deine Website ein und die Dienste laufen über unseren Server.'),
      h('p', { class: 'small muted' }, 'Deine Zugangsdaten werden verschlüsselt gespeichert. Sie sind danach nirgends mehr lesbar, auch nicht für uns. Du kannst sie jederzeit ersetzen oder löschen. Deine Website selbst bekommt nie ein Passwort.'),
      d.domains.length ? h('p', { class: 'small' }, 'Aktiv für: ', d.domains.join(', ')) : h('p', { class: 'msg info' }, 'Für dich ist noch keine Website-Adresse hinterlegt. Wir tragen sie ein, sobald deine Seite online geht.')),
    await domainKarte(), mailKarte(d, neu), await zustellKarte(), kalenderKarte(d, neu), await teamKarte(d, neu), await buchungenKarte(d, neu), await gutscheineKarte(neu), await sperrtageKarte(d), paypalKarte(d, neu), bewertungKarte(d, neu), analyticsKarte(d), await statistikKarte(d));
};

// ---------------------------------------------------------------- Domain-Stand
/** Wo steht meine Website? Wartet sie noch auf die Domain-Umstellung, steht hier in einfachen Worten, was zu tun ist. */
async function domainKarte() {
  let z; try { z = (await api('/api/kunde/website-dienste/domains')).domains; } catch { return ''; }
  if (!z.length) return '';
  const farbe = { live: 'ok', zertifikat: 'warn', wartet_dns: 'warn', neu: 'warn', gestoert: 'bad' };
  return h('div', { class: 'card', id: 'domain-stand' }, h('h2', {}, 'Meine Website-Adresse'),
    ...z.map(x => h('div', { style: 'margin:10px 0' },
      h('p', {}, h('span', { class: 'pill ' + (farbe[x.stand] || 'warn') }, x.titel), ' ', h('b', {}, x.domain)),
      h('p', { class: 'small' }, x.text),
      x.stand === 'wartet_dns' && x.schritte.length ? h('div', {}, h('p', { class: 'small' }, h('b', {}, 'Das ist zu tun' + (x.dns_anbieter ? ' (Verwaltung der Domain bei ' + x.dns_anbieter + ')' : '') + ':')), h('ol', { class: 'small' }, ...x.schritte.map(t => h('li', {}, t))),
        h('p', { class: 'small muted' }, 'Das ändert nur, wohin die Adresse zeigt. Deine E-Mails und andere Einträge bleiben unverändert. Bei Fragen helfen wir gern.')) : '',
      x.stand === 'live' && x.seit ? h('p', { class: 'small muted' }, 'Online seit ' + datum(x.seit)) : '')));
}

// ---------------------------------------------------------------- E-Mail
function mailKarte(d, neu) {
  const m = h('div'), mm = h('div');
  const an = schalter(d.mail.aktiv, 'Kontaktformular einschalten');
  const emp = h('input', { value: d.mail.empfaenger, placeholder: 'info@deinefirma.de, zweite@…', maxlength: 400 });
  const betreff = h('input', { value: d.mail.betreff, placeholder: 'Neue Anfrage über die Website', maxlength: 120 });
  const name = h('input', { value: d.mail.name, placeholder: 'Absendername, z. B. deine Firma', maxlength: 80 });
  const speichern = async () => {
    try { await api('/api/kunde/website-dienste/mail', { method: 'PUT', body: { aktiv: an.c.checked, empfaenger: emp.value, betreff: betreff.value, name: name.value } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); }
  };
  const test = async (e) => {
    const b = e.target; b.disabled = true; melde(m, '');
    try { const r = await api('/api/kunde/website-dienste/mail/test', { method: 'POST', body: { an: emp.value.split(/[,;\s]+/)[0] } }); melde(m, 'Testmail gesendet' + (r.ueber === 'eigen' ? ' (über dein Postfach).' : ' (über Markentrix).') + ' Schau in deinem Posteingang und im Spam-Ordner nach.', 'ok'); } catch (x) { melde(m, x.message); }
    b.disabled = false;
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Kontaktformular: Anfragen per E-Mail'),
    h('p', { class: 'small muted' }, 'Wer das Formular auf deiner Website ausfüllt, landet hier im Portal unter „Anfragen“ und bekommt zusätzlich per E-Mail bei dir an. Wenn du antwortest, geht die Antwort direkt an die Person.'),
    m, an.el, h('div', { class: 'form2', style: 'margin-top:8px' }, feld('Wohin sollen die Anfragen? *', emp, 'Bis zu 5 Adressen, mit Komma getrennt.'), feld('Betreff der E-Mail', betreff), feld('Absendername', name)),
    h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { class: 'btn', onclick: speichern }, 'Speichern'), h('button', { class: 'btn sec', onclick: test }, 'Testmail senden')),
    statusZeile(d.status, 'kontakt', 'Anfragen'),
    smtpBereich(d, mm, neu), mm);
}

function smtpBereich(d, mm, neu) {
  const s = d.mail.smtp || {};
  const absender = h('input', { type: 'email', value: s.absender || '', placeholder: 'info@deinefirma.de', maxlength: 200 });
  const host = h('input', { value: s.host || '', placeholder: 'smtp.deinanbieter.de', maxlength: 253 });
  const port = h('input', { type: 'number', value: s.port || 587 });
  const sich = h('select', {}, [['starttls', 'STARTTLS (meist Port 587)'], ['ssl', 'SSL (meist Port 465)']].map(([v, t]) => h('option', { value: v, selected: (s.sicherung || 'starttls') === v }, t)));
  const benutzer = h('input', { value: s.benutzer || '', placeholder: 'meist deine komplette Adresse', maxlength: 200, autocomplete: 'off' });
  const pw = h('input', { type: 'password', placeholder: s.gesetzt ? 'leer lassen = unverändert' : 'Passwort oder App-Passwort', autocomplete: 'new-password', maxlength: 300 });
  const tipp = h('div', { class: 'msg info', style: 'display:none' });
  const vorschlag = async () => {
    if (!/.+@.+\..+/.test(absender.value)) return;
    try {
      const v = await api('/api/kunde/website-dienste/anbieter?email=' + encodeURIComponent(absender.value));
      if (v.host) { host.value = v.host; port.value = v.port; sich.value = v.sicherung; }
      if (!benutzer.value) benutzer.value = v.benutzer || absender.value;
      tipp.style.display = v.hinweis ? '' : 'none'; tipp.textContent = (v.anbieter ? v.anbieter + ': ' : '') + (v.hinweis || '');
    } catch { /* Vorschlag ist nur eine Hilfe */ }
  };
  absender.addEventListener('change', vorschlag);
  const speichern = async (e) => {
    const b = e.target; b.disabled = true; b.textContent = 'Prüfe Verbindung …'; melde(mm, '');
    try { await api('/api/kunde/website-dienste/smtp', { method: 'PUT', body: { absender: absender.value, host: host.value, port: Number(port.value), sicherung: sich.value, benutzer: benutzer.value, passwort: pw.value } }); melde(mm, 'Verbindung geprüft und gespeichert. Ab jetzt versenden wir die Anfragen über dein Postfach.', 'ok'); setTimeout(neu, 1200); }
    catch (x) { melde(mm, x.message); b.disabled = false; b.textContent = 'Prüfen und speichern'; }
  };
  const weg = async () => { if (!confirm('Eigenes Postfach entfernen? Die Mails laufen dann wieder über Markentrix.')) return; try { await api('/api/kunde/website-dienste/smtp', { method: 'DELETE' }); neu(); } catch (x) { melde(mm, x.message); } };
  return h('details', { class: 'hilfe', open: !!s.gesetzt, style: 'margin-top:12px' }, h('summary', {}, s.gesetzt ? 'Eigenes Postfach: eingerichtet (' + s.absender + ')' : 'Optional: Mails über dein eigenes Postfach senden (Gmail, GMX, IONOS …)'),
    h('div', { style: 'margin-top:8px' },
      h('p', { class: 'small muted' }, 'Ohne diese Einstellung verschicken wir die Anfragen über Markentrix. Das funktioniert sofort und zuverlässig. Wenn die Mails aus deinem eigenen Postfach kommen sollen (und in deinem „Gesendet“-Ordner stehen), trage es hier ein. Wir prüfen die Verbindung, bevor wir speichern. Klappt später etwas nicht, springen wir automatisch auf Markentrix zurück.'),
      feld('Deine E-Mail-Adresse', absender, 'Wir füllen Server und Port passend zu deinem Anbieter aus.'), tipp,
      h('div', { class: 'form2' }, feld('Server (SMTP)', host), feld('Port', port), feld('Verschlüsselung', sich), feld('Benutzername', benutzer), feld('Passwort', pw)),
      h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { class: 'btn', onclick: speichern }, 'Prüfen und speichern'), s.gesetzt ? h('button', { class: 'btn sec', onclick: weg }, 'Entfernen') : ''),
      s.gesetzt && s.geprueft_am ? h('p', { class: 'small muted' }, 'Zuletzt geprüft: ' + datum(s.geprueft_am) + ' ' + ZEIT(s.geprueft_am)) : '',
      hilfe('Wo finde ich das Passwort? (Google, GMX, Telekom …)',
        h('p', {}, h('b', {}, 'Google Mail: '), 'Google-Konto → Sicherheit → „Bestätigung in zwei Schritten“ einschalten → „App-Passwörter“ → neues erstellen. Das 16-stellige Passwort hier eintragen, nicht dein normales.'),
        h('p', {}, h('b', {}, 'GMX / WEB.DE: '), 'Im Postfach unter Einstellungen → „POP3 und IMAP“ den Zugriff für externe Programme erlauben.'),
        h('p', {}, h('b', {}, 'Telekom: '), 'Im Kundencenter ein eigenes „E-Mail-Passwort“ für externe Programme anlegen.'),
        h('p', {}, h('b', {}, 'Microsoft 365 / Outlook: '), 'Microsoft sperrt das oft. Dann lass es einfach bei Markentrix, das klappt immer.'),
        h('p', {}, h('b', {}, 'IONOS, STRATO, Hetzner & Co.: '), 'Meist reichen deine normale Adresse und das Postfach-Passwort.'))));
}

// ---------------------------------------------------------------- Kalender
const TAGE = [[1, 'Mo'], [2, 'Di'], [3, 'Mi'], [4, 'Do'], [5, 'Fr'], [6, 'Sa'], [7, 'So']];
function kalenderKarte(d, neu) {
  const k = d.kalender, m = h('div');
  const an = schalter(k.aktiv, 'Online-Terminbuchung einschalten');
  const url = h('input', { placeholder: k.ical_gesetzt ? 'Adresse ist gespeichert (zum Ersetzen neu einfügen)' : 'https://calendar.google.com/calendar/ical/…/basic.ics', maxlength: 1500, autocomplete: 'off' });
  const dauer = h('input', { type: 'number', min: 10, max: 240, value: k.dauer });
  const tage = h('input', { type: 'number', min: 1, max: 90, value: k.tage });
  const von = h('input', { type: 'time', value: k.von }), bis = h('input', { type: 'time', value: k.bis });
  const vorlauf = h('input', { type: 'number', min: 0, max: 240, value: k.vorlauf_std });
  const ort = h('input', { value: k.ort, placeholder: 'z. B. Praxis, Hauptstr. 1 – oder „Videocall, Link folgt“', maxlength: 300 });
  const emp = h('input', { value: k.empfaenger, placeholder: 'leer = wie beim Kontaktformular', maxlength: 400 });
  const zeiten = h('input', { value: k.zeiten, placeholder: 'leer = Raster aus Von, Bis und Dauer; sonst z. B. 08:00, 10:00, 13:30', maxlength: 300 });
  const kap = h('input', { type: 'number', min: 0, max: 200, value: k.kapazitaet });
  const halte = h('input', { type: 'number', min: 1, max: 336, value: k.halte_std });
  const frei = schalter(k.freigabe, 'Ich bestätige jede Buchung selbst (sonst ist sie sofort gültig)');
  const erin = schalter(k.erinnerung !== false, 'Besucher per E-Mail an den Termin erinnern (mit Absage-Link)');
  const erin1 = h('input', { type: 'number', min: 0, max: 168, value: k.erinnerung_std1 ?? 24 }), erin2 = h('input', { type: 'number', min: 0, max: 48, value: k.erinnerung_std2 ?? 2 });
  const wt = TAGE.map(([n, t]) => ({ n, c: h('input', { type: 'checkbox', checked: k.wochentage.includes(n), style: 'width:auto' }), t }));
  const speichern = async () => {
    melde(m, '');
    try {
      await api('/api/kunde/website-dienste/kalender', { method: 'PUT', body: { aktiv: an.c.checked, ical_url: url.value, dauer: Number(dauer.value), tage: Number(tage.value), von: von.value, bis: bis.value, wochentage: wt.filter(x => x.c.checked).map(x => x.n), vorlauf_std: Number(vorlauf.value), ort: ort.value, empfaenger: emp.value, zeiten: zeiten.value, kapazitaet: Number(kap.value), freigabe: frei.c.checked, halte_std: Number(halte.value), erinnerung: erin.c.checked, erinnerung_std1: Number(erin1.value), erinnerung_std2: Number(erin2.value) } });
      melde(m, 'Gespeichert.', 'ok'); if (url.value) setTimeout(neu, 1000);
    } catch (x) { melde(m, x.message); }
  };
  const test = async (e) => {
    const b = e.target; b.disabled = true; melde(m, '');
    try { const r = await api('/api/kunde/website-dienste/kalender/test', { method: 'POST', body: {} }); melde(m, (r.belegt === null ? 'Kein Kalender verbunden. ' : 'Dein Kalender wurde gelesen (' + r.belegt + ' belegte Zeiten in den nächsten Tagen). ') + r.freie + ' freie Termine werden angeboten' + (r.beispiele.length ? ', zum Beispiel ' + r.beispiele.join(', ') : '') + '.', 'ok'); } catch (x) { melde(m, x.message); }
    b.disabled = false;
  };
  const weg = async () => { if (!confirm('Kalender-Adresse löschen? Dann werden nur noch über die Website gebuchte Termine berücksichtigt.')) return; try { await api('/api/kunde/website-dienste/kalender-adresse', { method: 'DELETE' }); neu(); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Terminbuchung mit deinem Kalender'),
    h('p', { class: 'small muted' }, 'Besucher wählen auf deiner Website einen freien Termin. Zeiten, in denen du laut Kalender belegt bist, werden nicht angeboten. Beide Seiten bekommen eine E-Mail mit Kalender-Einladung, der Termin steht bei dir unter „Heute“.'),
    m, an.el,
    h('div', { class: 'form2', style: 'margin-top:8px' }, feld('Geheime Kalender-Adresse (iCal)', url, k.ical_gesetzt ? 'Gespeichert' + (k.ical_geprueft_am ? ' am ' + datum(k.ical_geprueft_am) : '') + '. Aus Sicherheitsgründen zeigen wir sie nicht mehr an.' : 'Funktioniert mit Google, Outlook, Apple, IONOS und vielen mehr. Anleitung unten.'),
      feld('Termin dauert (Minuten)', dauer), feld('Von', von), feld('Bis', bis), feld('So viele Tage im Voraus buchbar', tage), feld('Frühestens in … Stunden', vorlauf),
      feld('Ort / Hinweis in der Einladung', ort), feld('Benachrichtigung an', emp),
      feld('Feste Uhrzeiten (optional)', zeiten, 'Zum Beispiel für Fahrzeugabgabe oder feste Termine. Muss zu den Uhrzeiten auf deiner Website passen.'),
      feld('Höchstens so viele Buchungen pro Tag (0 = unbegrenzt)', kap), feld('Unbestätigte Reservierung hält … Stunden', halte)),
    h('div', { style: 'margin:8px 0' }, frei.el),
    h('div', { style: 'margin:8px 0' }, erin.el),
    h('div', { class: 'form2' }, feld('Erste Erinnerung … Stunden vorher (0 = aus)', erin1), feld('Zweite Erinnerung … Stunden vorher (0 = aus)', erin2)),
    h('div', { class: 'row', style: 'gap:12px;margin:8px 0;flex-wrap:wrap' }, h('span', { class: 'small' }, 'Buchbar an:'), wt.map(x => h('label', { style: 'display:flex;gap:4px;align-items:center;color:inherit' }, x.c, x.t))),
    h('div', { class: 'row' }, h('button', { class: 'btn', onclick: speichern }, 'Speichern'), h('button', { class: 'btn sec', onclick: test }, 'Kalender testen'), k.ical_gesetzt ? h('button', { class: 'btn sec', onclick: weg }, 'Adresse löschen') : ''),
    k.offene_termine ? h('p', { class: 'small' }, k.offene_termine + ' kommende Termine über die Website gebucht.') : '',
    statusZeile(d.status, 'termin', 'Ereignisse'),
    hilfe('Wo finde ich die Kalender-Adresse?',
      h('p', {}, h('b', {}, 'Google Kalender (am Computer): '), 'calendar.google.com → links beim Kalender auf die drei Punkte → „Einstellungen und Freigabe“ → ganz unten „Integrieren“ → ', h('b', {}, '„Geheime Adresse im iCal-Format“'), ' kopieren und oben einfügen.'),
      h('p', {}, h('b', {}, 'Outlook: '), 'Einstellungen → Kalender → Freigegebene Kalender → Kalender veröffentlichen → „ICS“-Link kopieren.'),
      h('p', {}, h('b', {}, 'Apple iCloud: '), 'Kalender-App → Kalender teilen → „Öffentlicher Kalender“ → Link kopieren (webcal://…).'),
      h('p', {}, h('b', {}, 'Anderer Anbieter: '), 'Suche in den Kalender-Einstellungen nach „iCal“, „ICS“ oder „Abonnieren“.'),
      h('p', { class: 'muted' }, 'Tipp: Wer die Adresse kennt, kann deinen Kalender lesen. Gib sie niemandem weiter. Sie lässt sich bei Google jederzeit zurücksetzen.')));
}

// ---------------------------------------------------------------- PayPal
function paypalKarte(d, neu) {
  const p = d.paypal, m = h('div');
  const an = schalter(p.aktiv, 'PayPal auf der Website anbieten');
  const cid = h('input', { value: p.client_id, placeholder: 'AaBb…', maxlength: 140, autocomplete: 'off' });
  const waehr = h('select', {}, ['EUR', 'CHF', 'USD', 'GBP', 'PLN', 'CZK', 'DKK', 'SEK', 'NOK'].map(w => h('option', { value: w, selected: w === p.waehrung }, w)));
  const link = h('input', { value: p.me_link, placeholder: 'https://paypal.me/deinname', maxlength: 200 });
  const speichern = async () => { try { await api('/api/kunde/website-dienste/paypal', { method: 'PUT', body: { aktiv: an.c.checked, client_id: cid.value, waehrung: waehr.value, me_link: link.value } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'card' }, h('h2', {}, 'PayPal'),
    h('p', { class: 'small muted' }, 'Das Geld geht direkt auf dein PayPal-Konto. Wir verarbeiten keine Zahlungen und sehen kein Geld. PayPal schickt dir und deinen Kunden die übliche Zahlungsmail.'),
    m, an.el, h('div', { class: 'form2', style: 'margin-top:8px' }, feld('Dein PayPal.Me-Link', link, 'Reicht völlig aus. Dein normales PayPal-Konto genügt.'), feld('Währung', waehr)),
    hilfe('Wo finde ich meinen PayPal.Me-Link? (1 Minute)',
      h('p', {}, 'PayPal-App öffnen → unten auf „Profil“ bzw. oben auf dein Profilbild → „PayPal.Me“ → Link kopieren und oben einfügen. Er sieht so aus: ', h('b', {}, 'https://paypal.me/deinname'), '.'),
      h('p', {}, 'Falls du noch keinen hast: dort auf „PayPal.Me-Link erstellen“ tippen und einen Namen wählen.'),
      h('p', { class: 'muted' }, 'Auf der Website steht dann ein Knopf „Mit PayPal zahlen“. Ist ein Betrag hinterlegt (z. B. beim Gutschein), ist er schon eingetragen, sonst gibt der Zahler ihn selbst ein.')),
    hilfe('Erweitert: PayPal-Knopf direkt auf der Seite (nur mit Geschäftskonto)',
      feld('Client-ID (Live)', cid, 'Die Zeichenfolge aus deiner PayPal-App. Ein Secret brauchen wir nicht.'),
      h('p', {}, 'developer.paypal.com → anmelden → „Apps & Credentials“ → oben auf ', h('b', {}, '„Live“'), ' stellen → „Create App“ → Name vergeben → die ', h('b', {}, 'Client-ID'), ' kopieren. Ist sie eingetragen, bezahlen Besucher direkt auf der Seite, ohne zu PayPal zu wechseln.')),
    h('p', {}, h('button', { class: 'btn', onclick: speichern }, 'Speichern')));
}

// ---------------------------------------------------------------- Bewertungen
function anfrageBlock(b) {
  const m = h('div'), an = schalter(b.nach_termin, 'Nach einem erschienenen Termin um eine Bewertung bitten');
  const std = h('input', { type: 'number', min: 1, max: 72, value: b.verzoegerung_std ?? 3, style: 'width:80px' });
  const sp = async () => { try { await api('/api/kunde/website-dienste/bewertungen/anfrage', { method: 'PUT', body: { aktiv: an.c.checked, verzoegerung_std: Number(std.value) } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } };
  return h('div', { style: 'margin-top:14px;border-top:1px solid var(--line,#ddd);padding-top:10px' }, h('h3', {}, 'Bewertungen anfragen'),
    h('p', { class: 'small muted' }, 'Wenn du einen Termin als „erschienen“ markierst, bekommt der Besucher nach der gewählten Zeit eine freundliche Mail mit deinem Bewertungs-Link. Jede Mail enthält einen Abmeldelink. Schalte das nur ein, wenn deine Besucher bei der Buchung damit rechnen können (Hinweis in deiner Datenschutzerklärung).'),
    m, an.el, h('div', { class: 'row', style: 'margin-top:6px' }, h('span', {}, 'Mail nach'), std, h('span', {}, 'Stunden'), h('button', { class: 'btn', onclick: sp }, 'Speichern')));
}

function bewertungKarte(d, neu) {
  const b = d.bewertungen, m = h('div');
  const an = schalter(b.aktiv, 'Google-Bewertungen auf der Website zeigen');
  const pid = h('input', { value: b.place_id, placeholder: 'ChIJ…', maxlength: 200, autocomplete: 'off' });
  const sterne = h('input', { type: 'number', step: '0.1', min: 1, max: 5, value: b.sterne ?? '' });
  const anzahl = h('input', { type: 'number', min: 0, value: b.anzahl ?? '' });
  const link = h('input', { value: b.link, placeholder: 'https://g.page/r/…/review', maxlength: 400 });
  const body = () => ({ aktiv: an.c.checked, place_id: pid.value, sterne: sterne.value ? Number(sterne.value) : null, anzahl: anzahl.value ? Number(anzahl.value) : null, link: link.value });
  const speichern = async () => { try { await api('/api/kunde/website-dienste/bewertungen', { method: 'PUT', body: body() }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } };
  const test = async (e) => {
    const bt = e.target; bt.disabled = true; melde(m, '');
    try { await api('/api/kunde/website-dienste/bewertungen', { method: 'PUT', body: body() }); const r = await api('/api/kunde/website-dienste/bewertungen/test', { method: 'POST', body: {} }); melde(m, 'Google meldet ' + String(r.sterne).replace('.', ',') + ' Sterne aus ' + r.anzahl + ' Bewertungen.', 'ok'); } catch (x) { melde(m, x.message); }
    bt.disabled = false;
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Google-Bewertungen'),
    h('p', { class: 'small muted' }, 'Deine Sterne und die neuesten Bewertungen erscheinen auf der Website, dazu ein Knopf „Jetzt bewerten“. Die Daten holen wir regelmäßig bei Google, die Besucher laden nichts direkt von Google.'),
    d.places_verfuegbar ? '' : h('p', { class: 'msg info' }, 'Die automatische Anzeige schalten wir gerade frei. Bis dahin kannst du Sterne und Anzahl von Hand eintragen.'),
    m, an.el,
    h('div', { class: 'form2', style: 'margin-top:8px' }, feld('Place-ID deines Google-Profils', pid, 'Für die automatische Anzeige.'), feld('Link „Rezension schreiben“', link, 'Nur nötig, wenn du keine Place-ID eintragen kannst.'),
      feld('Oder von Hand: Sterne (z. B. 4,8)', sterne), feld('Anzahl der Bewertungen', anzahl)),
    h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { class: 'btn', onclick: speichern }, 'Speichern'), h('button', { class: 'btn sec', onclick: test }, 'Bei Google abfragen')),
    anfrageBlock(b),
    b.stand ? h('p', { class: 'small muted' }, 'Zuletzt von Google geholt: ' + datum(b.stand) + ' ' + ZEIT(b.stand)) : '',
    hilfe('Wo finde ich die Place-ID?',
      h('p', {}, 'Öffne den „Place ID Finder“ von Google (suche im Netz nach „Google Place ID Finder“), gib den Namen deiner Firma ein und kopiere die Kennung, die mit ', h('b', {}, 'ChIJ'), ' beginnt.'),
      h('p', {}, 'Den Link „Rezension schreiben“ findest du in Google Maps bei deinem Profil unter „Bewertungen“ → „Bewertungen anfordern“ bzw. in deinem Google-Unternehmensprofil.')));
}

// ---------------------------------------------------------------- Google Analytics
function analyticsKarte(d) {
  const a = d.analytics, m = h('div');
  const an = schalter(a.aktiv, 'Besucher-Statistik (Google Analytics) einschalten');
  const gid = h('input', { value: a.id, placeholder: 'G-AB12CD34EF', maxlength: 20, autocomplete: 'off' });
  const speichern = async () => { try { await api('/api/kunde/website-dienste/analytics', { method: 'PUT', body: { aktiv: an.c.checked, id: gid.value } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Google Analytics'),
    h('p', { class: 'small muted' }, 'Zeigt dir, wie viele Besucher auf deine Website kommen und woher. Auf der Website erscheint automatisch eine Abfrage („Statistik erlauben?“). Nur wer zustimmt, wird gezählt. Vorher wird nichts an Google gesendet.'),
    m, an.el, h('div', { class: 'form2', style: 'margin-top:8px' }, feld('Mess-ID', gid, 'Beginnt mit „G-“.')),
    h('p', {}, h('button', { class: 'btn', onclick: speichern }, 'Speichern')),
    hilfe('Wo finde ich die Mess-ID?',
      h('p', {}, 'analytics.google.com → unten links „Verwalten“ (Zahnrad) → „Datenstreams“ → „Web“ → deinen Stream öffnen → oben rechts steht die ', h('b', {}, 'Mess-ID'), ' (G-…).'),
      h('p', {}, 'Noch kein Konto? Dort „Messung starten“ wählen, ein Konto und eine „Property“ anlegen und einen Web-Datenstream mit der Adresse deiner Website erstellen. Das dauert etwa 5 Minuten. Wenn du magst, machen wir das gemeinsam am Telefon.')));
}

// ---------------------------------------------------------------- Gutscheine
const GUT_STATUS = { angefragt: ['warn', 'neu'], zahlungslink_gesendet: ['warn', 'wartet auf Zahlung'], gesendet: ['ok', 'Code gesendet'], storniert: ['', 'storniert'] };

/** Gutschein-Anfragen der Website: Zahlungslink (PayPal.Me) senden, nach dem Zahlungseingang den Code senden. */
async function gutscheineKarte(neu) {
  let r; try { r = await api('/api/kunde/website-dienste/gutscheine'); } catch { return ''; }
  if (!r.gutscheine.length) return '';
  const m = h('div');
  const zeile = (g) => {
    const betrag = h('input', { placeholder: 'Betrag in €', value: g.betrag.replace('.', ','), style: 'max-width:130px', maxlength: 20, 'aria-label': 'Betrag in Euro' });
    const code = h('input', { placeholder: 'Code', value: g.code, style: 'max-width:200px', maxlength: 40, 'aria-label': 'Gutschein-Code' });
    const tun = async (pfad, body, ok) => { try { await api('/api/kunde/website-dienste/gutscheine/' + g.id + '/' + pfad, { method: 'POST', body }); toast(ok, 'ok'); neu(); } catch (x) { melde(m, x.message); } };
    const offen = g.status === 'angefragt' || g.status === 'zahlungslink_gesendet';
    const st = GUT_STATUS[g.status] || ['', g.status];
    return h('div', { class: 'card', style: 'margin:8px 0' },
      h('p', {}, h('b', {}, g.name), ' ', h('span', { class: 'pill ' + st[0] }, st[1]), g.betrag ? ' · ' + g.betrag.replace('.', ',') + ' €' : ' · Betrag fehlt noch'),
      h('p', { class: 'small' }, (g.email || 'keine E-Mail') + (g.telefon ? ' · ' + g.telefon : '') + ' · ' + g.ref + ' · ' + datum(g.erstellt_am)),
      g.empfaenger || g.widmung ? h('p', { class: 'small muted' }, [g.empfaenger ? 'Für: ' + g.empfaenger : '', g.widmung ? 'Widmung: ' + g.widmung : ''].filter(Boolean).join(' · ')) : '',
      g.zahlungslink_am ? h('p', { class: 'small muted' }, 'Zahlungslink gesendet am ' + datum(g.zahlungslink_am)) : '',
      g.gesendet_am ? h('p', { class: 'small muted' }, 'Code ' + g.code + ' gesendet am ' + datum(g.gesendet_am)) : '',
      g.status !== 'storniert' && g.email ? h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;margin-top:6px' },
        offen ? [betrag, h('button', { class: 'btn', disabled: !r.paypal_bereit, onclick: () => tun('zahlungslink', { betrag: betrag.value }, 'Zahlungslink gesendet.') }, g.status === 'angefragt' ? 'Zahlungslink senden' : 'Zahlungslink erneut senden')] : '',
        [code, h('button', { class: 'btn ' + (offen ? 'sec' : ''), onclick: () => tun('code', { code: code.value }, 'Gutschein gesendet.') }, g.status === 'gesendet' ? 'Gutschein erneut senden' : 'Gutschein senden')],
        offen ? h('button', { class: 'btn sec', onclick: () => { if (confirm('Diese Anfrage stornieren?')) tun('storno', {}, 'Storniert.'); } }, 'Stornieren') : '') : '');
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Gutschein-Anfragen'),
    h('p', { class: 'small muted' }, 'So läuft es: 1. „Zahlungslink senden“ schickt dem Kunden deinen PayPal.Me-Link mit dem Betrag. 2. Sobald das Geld bei dir angekommen ist, trägst du einen Code ein und klickst „Gutschein senden“. Das Portal sieht deine PayPal-Zahlungen nicht, deshalb prüfst du den Eingang selbst.'),
    r.paypal_bereit ? '' : h('p', { class: 'msg info' }, 'Für den Zahlungslink trägst du unten bei PayPal deinen PayPal.Me-Link ein und schaltest PayPal ein.'),
    m, r.gutscheine.map(zeile));
}

// ---------------------------------------------------------------- Buchungsanfragen bestätigen
async function buchungenKarte(d, neu) {
  if (!d.kalender.aktiv) return '';
  const r = await api('/api/kunde/website-dienste/buchungen');
  const m = h('div');
  const zeile = (b) => {
    const betrag = h('input', { placeholder: 'Anzahlung in € (optional)', style: 'max-width:200px', maxlength: 20 });
    const info = Object.entries(b.details).filter(([k]) => k !== 'leistung' && k !== 'mitarbeiter').map(([k, v]) => k.replace(/_/g, ' ') + ': ' + (Array.isArray(v) ? v.join(', ') : v)).join(' · ');
    const tun = async (pfad, body) => { try { await api('/api/kunde/website-dienste/buchungen/' + b.id + '/' + pfad, { method: 'POST', body }); neu(); } catch (x) { melde(m, x.message); } };
    return h('div', { class: 'card', style: 'margin:8px 0' },
      h('p', {}, h('b', {}, ZEIT(b.start)), ' · ' + b.name, ' ', h('span', { class: 'pill ' + (b.status === 'reserviert' ? 'warn' : 'ok') }, b.status === 'reserviert' ? 'wartet auf dich' : 'bestätigt')),
      (b.leistung || b.mitarbeiter) ? h('p', { class: 'small' }, [b.leistung, b.mitarbeiter ? 'bei ' + b.mitarbeiter : ''].filter(Boolean).join(' · ')) : '',
      h('p', { class: 'small' }, b.email + (b.telefon ? ' · ' + b.telefon : '') + (b.ref ? ' · ' + b.ref : '')),
      info ? h('p', { class: 'small muted' }, info) : '', b.nachricht ? h('p', { class: 'small' }, b.nachricht) : '',
      b.anzahlung ? h('p', { class: 'small' }, 'Anzahlung: ' + b.anzahlung.replace('.', ',') + ' €') : '',
      h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' },
        b.status === 'reserviert' ? [betrag, h('button', { class: 'btn', onclick: () => tun('bestaetigen', { anzahlung: betrag.value }) }, 'Bestätigen')] : '',
        h('button', { class: 'btn sec', onclick: () => { const g = prompt('Kurze Begründung für die Absage (optional):', ''); if (g !== null) tun('ablehnen', { grund: g }); } }, b.status === 'reserviert' ? 'Ablehnen' : 'Absagen')));
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Buchungen über die Website'),
    h('p', { class: 'small muted' }, r.freigabe
      ? 'Neue Wünsche sind für den Kunden vorgemerkt, bis du sie bestätigst. Mit „Bestätigen“ bekommt er eine E-Mail mit Kalender-Einladung, auf Wunsch mit PayPal-Link für die Anzahlung.'
      : 'Buchungen sind sofort gültig. Hier siehst du die kommenden und kannst absagen.'),
    m, r.buchungen.length ? r.buchungen.map(zeile) : h('p', { class: 'small muted' }, 'Keine kommenden Buchungen.'),
    r.vergangen.length ? h('div', {}, h('h3', {}, 'Vergangene Termine – hat es geklappt?'),
      h('p', { class: 'small muted' }, 'Ein Klick genügt. So siehst du, wer öfter nicht kommt, und die Statistik zeigt deine Nichterschienen-Quote.'),
      r.vergangen.map(b => {
        const set = async (erg) => { try { await api('/api/kunde/website-dienste/buchungen/' + b.id + '/ergebnis', { method: 'POST', body: { ergebnis: erg } }); neu(); } catch (x) { melde(m, x.message); } };
        return h('div', { class: 'card', style: 'margin:8px 0' }, h('p', {}, h('b', {}, ZEIT(b.start)), ' · ' + b.name,
          b.fehlt_bisher ? h('span', { class: 'pill warn', style: 'margin-left:6px' }, b.fehlt_bisher + '× nicht erschienen') : ''),
          h('div', { class: 'row', style: 'gap:8px' }, h('button', { class: 'btn', onclick: () => set('erschienen') }, 'Ist gekommen'), h('button', { class: 'btn sec', onclick: () => set('nicht_erschienen') }, 'Nicht erschienen')));
      })) : '');
}

// ---------------------------------------------------------------- Sperrtage
async function sperrtageKarte(d) {
  const r = await api('/api/kunde/website-dienste/sperrtage');
  const team = d.kalender.aktiv ? await api('/api/kunde/website-dienste/team') : { mitarbeiter: [] };
  const m = h('div');
  const von = h('input', { type: 'date' }), bis = h('input', { type: 'date' }), grund = h('input', { placeholder: 'z. B. Urlaub', maxlength: 80 });
  const wer = h('select', {}, h('option', { value: '' }, 'Ganzer Betrieb'), team.mitarbeiter.map(x => h('option', { value: x.id }, x.name)));
  const liste = h('div');
  const laden = async () => { const n = await api('/api/kunde/website-dienste/sperrtage'); zeigen(n.tage); };
  const zeigen = (tage) => { liste.replaceChildren(...(tage.length ? tage.map(t => h('span', { class: 'pill', style: 'margin:2px;cursor:pointer', title: 'Zum Entfernen anklicken', onclick: async () => { try { await api('/api/kunde/website-dienste/sperrtage/' + t.tag + (t.mitarbeiter_id ? '?mitarbeiter=' + t.mitarbeiter_id : ''), { method: 'DELETE' }); await laden(); } catch (x) { melde(m, x.message); } } }, datum(t.tag) + (t.mitarbeiter ? ' · ' + t.mitarbeiter : '') + (t.grund ? ' · ' + t.grund : '') + ' ×')) : [h('span', { class: 'small muted' }, 'Keine Sperrtage eingetragen.')])); };
  zeigen(r.tage);
  const add = async () => { melde(m, ''); try { await api('/api/kunde/website-dienste/sperrtage', { method: 'POST', body: { von: von.value, bis: bis.value, grund: grund.value, mitarbeiter_id: wer.value } }); await laden(); von.value = ''; bis.value = ''; grund.value = ''; } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Urlaub und Sperrtage'),
    h('p', { class: 'small muted' }, 'An diesen Tagen kann nicht gebucht werden: für den ganzen Betrieb oder nur für eine Person (z. B. Urlaub).'), m,
    h('div', { class: 'form2' }, feld('Von', von), feld('Bis (optional)', bis), feld('Gilt für', wer), feld('Grund (nur für dich)', grund)),
    h('p', {}, h('button', { class: 'btn', onclick: add }, 'Sperren')), liste);
}

// ---------------------------------------------------------------- Leistungen und Mitarbeiter
async function teamKarte(d, neu) {
  if (!d.kalender.aktiv) return '';
  const t = await api('/api/kunde/website-dienste/team');
  const m = h('div');
  const melden = (x) => melde(m, x.message);
  const leistungZeile = (l) => {
    const name = h('input', { value: l.name, maxlength: 80 }), dauer = h('input', { type: 'number', min: 5, max: 720, value: l.dauer_min, style: 'max-width:90px' });
    const puffer = h('input', { type: 'number', min: 0, max: 240, value: l.puffer_min, style: 'max-width:90px' }), preis = h('input', { value: l.preis, maxlength: 40, placeholder: 'z. B. 45 €', style: 'max-width:110px' });
    const an = schalter(l.aktiv, 'aktiv');
    const body = () => ({ name: name.value, schluessel: l.schluessel, dauer_min: Number(dauer.value), puffer_min: Number(puffer.value), preis: preis.value, aktiv: an.c.checked });
    return h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;align-items:end;margin:6px 0' }, feld('Leistung', name, 'Name auf der Website: ' + l.schluessel), feld('Dauer (Min.)', dauer), feld('Pause danach', puffer), feld('Preis (Anzeige)', preis), an.el,
      h('button', { class: 'btn sec', onclick: async () => { try { await api('/api/kunde/website-dienste/leistungen/' + l.id, { method: 'PUT', body: body() }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melden(x); } } }, 'Speichern'),
      h('button', { class: 'btn sec', onclick: async () => { if (!confirm('Leistung „' + l.name + '“ löschen?')) return; try { await api('/api/kunde/website-dienste/leistungen/' + l.id, { method: 'DELETE' }); neu(); } catch (x) { melden(x); } } }, 'Löschen'));
  };
  const nName = h('input', { placeholder: 'z. B. Damenhaarschnitt', maxlength: 80 }), nDauer = h('input', { type: 'number', min: 5, max: 720, value: 30, style: 'max-width:90px' }), nPuffer = h('input', { type: 'number', min: 0, max: 240, value: 0, style: 'max-width:90px' }), nPreis = h('input', { maxlength: 40, placeholder: 'z. B. 45 €', style: 'max-width:110px' });
  const neuL = async () => { try { await api('/api/kunde/website-dienste/leistungen', { method: 'POST', body: { name: nName.value, dauer_min: Number(nDauer.value), puffer_min: Number(nPuffer.value), preis: nPreis.value } }); neu(); } catch (x) { melden(x); } };
  const aktive = t.leistungen;
  const maBlock = (ma) => {
    const name = h('input', { value: ma ? ma.name : '', maxlength: 80, placeholder: 'Name' });
    const an = schalter(ma ? ma.aktiv : true, 'nimmt Termine an');
    const wt = TAGE.map(([n, tx]) => ({ n, c: h('input', { type: 'checkbox', checked: ma ? ma.wochentage.includes(n) : false, style: 'width:auto' }), tx }));
    const von = h('input', { type: 'time', value: ma ? ma.von : '' }), bis = h('input', { type: 'time', value: ma ? ma.bis : '' });
    const zeiten = h('input', { value: ma ? ma.zeiten : '', maxlength: 300, placeholder: 'leer = wie der Betrieb' });
    const url = h('input', { maxlength: 1500, autocomplete: 'off', placeholder: ma && ma.ical_gesetzt ? 'Kalender ist gespeichert (zum Ersetzen neu einfügen)' : 'Eigener Kalender (iCal), optional' });
    const ls = aktive.map(l => ({ id: l.id, c: h('input', { type: 'checkbox', checked: ma ? ma.leistungen.includes(l.id) : false, style: 'width:auto' }), n: l.name }));
    const body = () => ({ name: name.value, aktiv: an.c.checked, wochentage: wt.filter(x => x.c.checked).map(x => x.n), von: von.value, bis: bis.value, zeiten: zeiten.value, leistungen: ls.filter(x => x.c.checked).map(x => x.id), ical_url: url.value });
    const speichern = async () => { try { await api('/api/kunde/website-dienste/mitarbeiter' + (ma ? '/' + ma.id : ''), { method: ma ? 'PUT' : 'POST', body: body() }); neu(); } catch (x) { melden(x); } };
    return h('details', { class: 'hilfe', open: !ma }, h('summary', {}, ma ? ma.name + (ma.aktiv ? '' : ' (pausiert)') : '+ Mitarbeiter hinzufügen'),
      h('div', { style: 'margin-top:6px' },
        h('div', { class: 'form2' }, feld('Name', name, ma ? 'Name auf der Website: ' + ma.schluessel : ''), feld('Eigener Kalender (iCal)', url, 'Belegte Zeiten in diesem Kalender werden nicht angeboten.'), feld('Arbeitet von', von), feld('bis', bis), feld('Feste Uhrzeiten (optional)', zeiten)),
        an.el,
        h('div', { class: 'row', style: 'gap:12px;margin:8px 0;flex-wrap:wrap' }, h('span', { class: 'small' }, 'Arbeitstage (leer = wie der Betrieb):'), wt.map(x => h('label', { style: 'display:flex;gap:4px;align-items:center;color:inherit' }, x.c, x.tx))),
        ls.length ? h('div', { class: 'row', style: 'gap:12px;margin:8px 0;flex-wrap:wrap' }, h('span', { class: 'small' }, 'Bietet an (nichts angehakt = alles):'), ls.map(x => h('label', { style: 'display:flex;gap:4px;align-items:center;color:inherit' }, x.c, x.n))) : '',
        h('div', { class: 'row', style: 'gap:8px' }, h('button', { class: 'btn', onclick: speichern }, ma ? 'Speichern' : 'Anlegen'),
          ma && ma.ical_gesetzt ? h('button', { class: 'btn sec', onclick: async () => { try { await api('/api/kunde/website-dienste/mitarbeiter/' + ma.id + '/kalender-adresse', { method: 'DELETE' }); neu(); } catch (x) { melden(x); } } }, 'Kalender-Adresse löschen') : '',
          ma ? h('button', { class: 'btn sec', onclick: async () => { if (!confirm(ma.name + ' löschen? Bestehende Termine bleiben erhalten.')) return; try { await api('/api/kunde/website-dienste/mitarbeiter/' + ma.id, { method: 'DELETE' }); neu(); } catch (x) { melden(x); } } }, 'Löschen') : '')));
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Leistungen und Mitarbeiter'),
    h('p', { class: 'small muted' }, 'Optional, zum Beispiel für Friseur, Kosmetik oder Praxis: Jede Leistung hat ihre eigene Dauer. Wer Mitarbeiter einträgt, bei dem wird ein Termin nur angeboten, wenn die gewünschte Person (oder irgendjemand, wenn der Besucher „egal“ wählt) für die ganze Dauer Zeit hat. Ohne Einträge gilt die Dauer aus der Terminbuchung oben.'), m,
    h('h3', {}, 'Leistungen'), t.leistungen.map(leistungZeile),
    h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;align-items:end;margin:6px 0' }, feld('Neue Leistung', nName), feld('Dauer (Min.)', nDauer), feld('Pause danach', nPuffer), feld('Preis (Anzeige)', nPreis), h('button', { class: 'btn', onclick: neuL }, 'Hinzufügen')),
    h('h3', {}, 'Mitarbeiter'), t.mitarbeiter.map(maBlock), maBlock(null));
}

// ---------------------------------------------------------------- Besucher-Statistik (ohne Cookies, ohne Einwilligung)
async function statistikKarte(d) {
  const s = await api('/api/kunde/website-dienste/statistik?tage=30');
  const w = (await api('/api/kunde/website-dienste/wacht').catch(() => ({ seiten: [] }))).seiten;
  const m = h('div');
  const an = schalter(d.analytics.statistik, 'Einfache Besucherzahlen auf unserem Server mitzählen');
  an.c.addEventListener('change', async () => { try { await api('/api/kunde/website-dienste/statistik-schalter', { method: 'PUT', body: { aktiv: an.c.checked } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } });
  const kachel = (z, t) => h('div', { class: 'card', style: 'text-align:center;min-width:110px' }, h('div', { style: 'font-size:26px;font-weight:700' }, String(z)), h('div', { class: 'small muted' }, t));
  return h('div', { class: 'card' }, h('h2', {}, 'Besucher der letzten 30 Tage'),
    h('p', { class: 'small muted' }, 'Gezählt ohne Cookies und ohne IP-Adresse (anonym, nur auf unserem Server). Das ist keine Google-Statistik. Sie gilt nur für Websites, die dieses Zählen eingebaut haben.'),
    m, an.el,
    w.map(x => h('p', { class: 'small' }, h('span', { class: 'pill ' + (x.ok ? 'ok' : 'warn') }, x.ok ? 'erreichbar' : 'gestört'), ' ' + x.domain + (x.ms ? ' · ' + x.ms + ' ms' : '') + (x.prozent != null ? ' · ' + String(x.prozent).replace('.', ',') + ' % in 30 Tagen' : '') + (x.cert_tage != null ? ' · Zertifikat noch ' + x.cert_tage + ' Tage' : '') + (x.qualitaet ? ' · typische Ladezeit ' + x.qualitaet.median_ms + ' ms · ' + (x.qualitaet.tote.length ? x.qualitaet.tote.length + ' tote Verweise' : 'keine toten Verweise') + (x.qualitaet.langsam.length ? ' · ' + x.qualitaet.langsam.length + ' langsame Seiten' : '') : ''))),
    h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;margin:8px 0' }, kachel(s.besucher, 'Besucher'), kachel(s.aufrufe, 'Seitenaufrufe'), kachel(s.anfragen, 'Anfragen'), kachel(s.whatsapp, 'WhatsApp-Klicks'), kachel(s.anrufe, 'Anruf-Klicks'), s.erschienen + s.nicht_erschienen ? kachel(s.nicht_erschienen + ' von ' + (s.erschienen + s.nicht_erschienen), 'Nicht erschienen') : '', s.erreichbarkeit != null ? kachel(String(s.erreichbarkeit).replace('.', ',') + ' %', 'Erreichbarkeit') : ''),
    s.seiten.length ? h('p', { class: 'small' }, h('b', {}, 'Beliebteste Seiten: '), s.seiten.slice(0, 5).map(x => x.pfad + ' (' + x.aufrufe + ')').join(' · ')) : '',
    s.quellen.length ? h('p', { class: 'small' }, h('b', {}, 'Woher: '), s.quellen.slice(0, 5).map(x => x.quelle + ' (' + x.besucher + ')').join(' · ')) : '');
}


// ---------------------------------------------------------------- Zustellung der Mails
const DNS_TXT = { ok: ['ok', 'in Ordnung'], warn: ['warn', 'prüfen'], fehlt: ['bad', 'fehlt'], unbekannt: ['', 'unbekannt'] };
export function dnsZeile(dns) {
  return h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' }, ['spf', 'dkim', 'dmarc'].map(n => h('span', { class: 'pill ' + DNS_TXT[dns[n]][0], title: (dns.details || {})[n] || '' }, n.toUpperCase() + ': ' + DNS_TXT[dns[n]][1])));
}
async function zustellKarte() {
  const z = await api('/api/kunde/website-dienste/zustellung').catch(() => null);
  if (!z || (!z.eigenes_postfach && !z.kennzahlen.gesamt)) return '';
  const m = h('div');
  const k = z.kennzahlen;
  const neuPruefen = async (e) => { e.target.disabled = true; try { await api('/api/kunde/website-dienste/zustellung/pruefen', { method: 'POST', body: {} }); location.reload(); } catch (x) { melde(m, x.message); e.target.disabled = false; } };
  return h('div', { class: 'card' }, h('h2', {}, 'Kommen die Mails an?'),
    h('p', { class: 'small muted' }, 'Wir zeigen, was der Mailserver beim Versand meldet. Landet eine Mail beim Empfänger im Spam, sieht das niemand – deshalb prüfen wir bei einem eigenen Postfach die Absender-Einträge (SPF, DKIM, DMARC) deiner Domain.'),
    m, h('p', {}, k.gesamt ? [h('b', {}, k.gesamt - k.fehler + ' von ' + k.gesamt), ' Mails der letzten 30 Tage wurden angenommen.', k.fehler ? ' ' + k.fehler + ' nicht' + (k.adresse ? ' (davon ' + k.adresse + ' wegen ungültiger Empfänger-Adresse)' : '') + '.' : ''] : 'In den letzten 30 Tagen wurden keine Mails verschickt.'),
    z.eigenes_postfach && z.dns ? [h('p', { class: 'small' }, 'Absender: ' + z.absender + ' · geprüft ' + zeit(z.dns.geprueft_am)), dnsZeile(z.dns),
      ...['spf', 'dkim', 'dmarc'].filter(n => z.dns[n] === 'fehlt' || z.dns[n] === 'warn').map(n => h('p', { class: 'small' }, (z.dns.details || {})[n])),
      h('p', {}, h('button', { class: 'btn sec', onclick: neuPruefen }, 'Jetzt neu prüfen'))] : '',
    k.letzte_fehler.length ? h('details', {}, h('summary', {}, 'Letzte Fehler'), k.letzte_fehler.map(f => h('p', { class: 'small' }, zeit(f.zeit) + ' · ' + (f.an_domain || '') + ' · ' + (f.fehler || '')))) : '');
}
