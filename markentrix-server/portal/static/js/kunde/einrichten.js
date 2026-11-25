import { h, api, melde } from '../common.js';
import { V, zeige } from './kern.js';

/** Schritt-für-Schritt-Assistent: zeigt immer nur den nächsten offenen Schritt mit genau einer Aufgabe. */
const REIHE = ['empfaenger', 'logo', 'signatur', 'testmail', 'anfrage'];
const KURZ = { seite: 'Website online', empfaenger: 'Mailadresse', logo: 'Logo', signatur: 'Signatur', testmail: 'Testmail', anfrage: 'Testanfrage' };
const uebersprungen = new Set();

const mailBody = (m, ueber) => ({ aktiv: m.aktiv, empfaenger: m.empfaenger, betreff: m.betreff, name: m.name, signatur: m.signatur, bewertung: false, facebook: m.facebook, instagram: m.instagram, hinweis: m.hinweis, ...ueber });
const alsBase64 = (datei) => new Promise((ok, nein) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1] || ''); r.onerror = () => nein(new Error('Die Datei konnte nicht gelesen werden.')); r.readAsDataURL(datei); });

function schritt(code, d, meld) {
  const m = d.mail, weiter = () => zeige();
  const speichernKnopf = (text, tun) => h('button', { class: 'btn', onclick: async (e) => { const b = e.target; b.disabled = true; melde(meld, ''); try { await tun(); weiter(); } catch (x) { melde(meld, x.message); b.disabled = false; } } }, text);
  if (code === 'empfaenger') {
    const emp = h('input', { type: 'text', value: m.empfaenger, placeholder: 'info@deinefirma.de', maxlength: 400, 'aria-label': 'E-Mail-Adresse für Anfragen', autocomplete: 'email' });
    return { titel: 'Wohin sollen Anfragen von deiner Website geschickt werden?', text: 'Trag die E-Mail-Adresse ein, die du im Betrieb täglich ansiehst. Mehrere Adressen trennst du mit Komma.', inhalt: [emp], knopf: speichernKnopf('Speichern und weiter', async () => {
      if (!/.+@.+\..+/.test(emp.value)) throw new Error('Bitte eine gültige E-Mail-Adresse eintragen.');
      await api('/api/kunde/website-dienste/mail', { method: 'PUT', body: mailBody(m, { aktiv: true, empfaenger: emp.value }) });
    }) };
  }
  if (code === 'logo') {
    const datei = h('input', { type: 'file', accept: 'image/png,image/jpeg', 'aria-label': 'Logo auswählen' });
    return { titel: 'Dein Logo für die E-Mails', text: 'Es erscheint oben in den Mails, die deine Kunden von dir bekommen. Geeignet sind PNG oder JPG bis 400 KB, am besten mit weißem oder durchsichtigem Hintergrund.', inhalt: [datei], knopf: speichernKnopf('Logo hochladen und weiter', async () => {
      const f = datei.files && datei.files[0];
      if (!f) throw new Error('Bitte zuerst eine Datei auswählen.');
      if (f.size > 400 * 1024) throw new Error('Die Datei ist zu groß (maximal 400 KB).');
      await api('/api/kunde/website-dienste/logo', { method: 'PUT', body: { logo_base64: await alsBase64(f) } });
    }) };
  }
  if (code === 'signatur') {
    const sig = h('textarea', { rows: 6, maxlength: 600, 'aria-label': 'Signatur für Mails an deine Gäste' }, m.signatur || m.signatur_vorschlag || '');
    return { titel: 'Dein Abschluss unter jeder Mail', text: 'Wir haben aus deinen Firmendaten einen Vorschlag gemacht. Du kannst ihn so lassen oder ändern.', inhalt: [sig], knopf: speichernKnopf('Speichern und weiter', async () => {
      if (!sig.value.trim()) throw new Error('Bitte eine Signatur eintragen.');
      await api('/api/kunde/website-dienste/mail', { method: 'PUT', body: mailBody(m, { signatur: sig.value }) });
    }) };
  }
  if (code === 'testmail') {
    const an = (m.empfaenger || '').split(/[,;\s]+/)[0];
    return { titel: 'Eine Testmail an dich', text: 'Wir schicken eine Probe-Mail an ' + (an || 'deine Adresse') + '. Schau danach in deinen Posteingang und in den Spam-Ordner.', inhalt: [], knopf: speichernKnopf('Testmail senden', async () => {
      if (!an) throw new Error('Bitte zuerst die E-Mail-Adresse eintragen.');
      await api('/api/kunde/website-dienste/mail/test', { method: 'POST', body: { an } });
      uebersprungen.delete('testmail');
    }) };
  }
  const dom = (d.domains || [])[0];
  return { titel: 'Letzter Schritt: eine Testanfrage', text: 'Öffne deine Website, fülle das Kontaktformular einmal selbst aus und sende es ab. Sobald die Anfrage unter „Anfragen“ erscheint, ist alles fertig.', inhalt: [],
    knopf: h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' }, dom ? h('a', { class: 'btn', href: 'https://' + dom, target: '_blank', rel: 'noopener' }, 'Meine Website öffnen') : '', h('a', { class: 'btn sec', href: '#anfragen' }, 'Anfragen ansehen')) };
}

V.einrichten = async () => {
  const d = await api('/api/kunde/website-dienste'), s = d.start, meld = h('div');
  const status = Object.fromEntries(s.punkte.map(p => [p.code, p.erledigt]));
  const offen = REIHE.filter(c => c in status && !status[c]);
  const aktuell = offen.find(c => !uebersprungen.has(c)) || offen[0];
  const kopf = h('div', { class: 'top' }, h('h1', {}, 'Website einrichten'));
  if (!aktuell && s.fertig) return h('div', { class: 'stack' }, kopf, h('div', { class: 'card' }, h('h2', {}, 'Alles eingerichtet'), h('p', {}, 'Deine Website ist startklar: Anfragen kommen an, Mails sehen gut aus und die Testmail hat geklappt.'), h('a', { class: 'btn', href: '#anfragen' }, 'Zu den Anfragen')));
  const punkte = REIHE.filter(c => c in status);
  const leiste = h('ol', { class: 'small', style: 'display:flex;gap:6px;flex-wrap:wrap;list-style:none;padding:0;margin:0 0 10px' }, punkte.map(c => h('li', {}, h('span', { class: 'pill ' + (status[c] ? 'ok' : c === aktuell ? 'warn' : '') }, (status[c] ? '✓ ' : '') + KURZ[c]))));
  const seiteOk = status.seite;
  const hinweisSeite = seiteOk === false ? h('p', { class: 'msg info' }, 'Deine Website ist noch nicht veröffentlicht oder nicht erreichbar. Das übernimmt das Team von Markentrix. Die Schritte unten kannst du schon erledigen.') : '';
  if (!aktuell) return h('div', { class: 'stack' }, kopf, hinweisSeite, h('div', { class: 'card' }, h('p', {}, 'Für die Einrichtung ist nichts mehr zu tun. Das Team von Markentrix prüft den Rest.'), h('a', { class: 'btn sec', href: '#dienste' }, 'Alle Einstellungen')));
  const nr = punkte.indexOf(aktuell) + 1, st = schritt(aktuell, d, meld);
  return h('div', { class: 'stack' }, kopf, hinweisSeite,
    h('div', { class: 'card' }, leiste, h('p', { class: 'small muted' }, 'Schritt ' + nr + ' von ' + punkte.length),
      h('h2', {}, st.titel), h('p', {}, st.text), ...st.inhalt, meld,
      h('div', { class: 'row', style: 'margin-top:10px;gap:8px;flex-wrap:wrap' }, st.knopf,
        offen.length > 1 ? h('button', { class: 'btn sec', onclick: () => { uebersprungen.add(aktuell); zeige(); } }, 'Später') : ''),
      h('p', { class: 'small muted', style: 'margin-top:10px' }, h('a', { href: '#dienste' }, 'Alle Einstellungen für Formulare & Buchung'))));
};
