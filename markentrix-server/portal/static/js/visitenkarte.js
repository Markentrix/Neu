// Digitale Visitenkarte des Markentrix-Teams (Admin und Vertrieb): bearbeiten, als .vcf per Mail, über „Teilen“ (WhatsApp) oder als Datei verschicken.
import { h, api, melde, dialog } from './common.js';

/** Holt die eigene Karte als Datei. */
async function dateiHolen(basis) {
  const r = await fetch(basis + '/visitenkarte.vcf', { headers: { 'X-MK': '1' }, credentials: 'same-origin' });
  if (!r.ok) throw new Error('Die Visitenkarte konnte nicht geladen werden.');
  const m = /filename="([^"]+)"/.exec(r.headers.get('content-disposition') || '');
  return new File([await r.blob()], m ? m[1] : 'Visitenkarte.vcf', { type: 'text/vcard' });
}

function herunterladen(datei) {
  const a = h('a', { href: URL.createObjectURL(datei), download: datei.name });
  document.body.append(a); a.click(); a.remove();
}

/** Telefonnummer für wa.me (nur Ziffern, 0… wird zu 49…). */
function wa(telefon) {
  let z = String(telefon || '').replace(/[^\d+]/g, '');
  if (z.startsWith('+')) z = z.slice(1); else if (z.startsWith('00')) z = z.slice(2); else if (z.startsWith('0')) z = '49' + z.slice(1);
  return z.length >= 8 ? z : '';
}

/** Knopf „Visitenkarte senden“ für die Lead-Ansicht.
 * @param {string} basis '/api/vertrieb' oder '/api/admin'
 * @param {any} l der Lead */
export function visitenkarteKnopf(basis, lid, l, klasse = 'btn sec small') {
  return h('button', { class: klasse, onclick: () => dialogOeffnen(basis, lid, l) }, 'Visitenkarte senden');
}

function dialogOeffnen(basis, lid, l) {
  const m = h('div'), an = h('input', { type: 'email', value: l.email || '', 'aria-label': 'E-Mail-Adresse', placeholder: 'E-Mail-Adresse' });
  const vermerk = (kanal) => api(basis + '/leads/' + lid + '/visitenkarte', { method: 'POST', body: { kanal } });
  const mail = h('button', { class: 'btn', onclick: async (e) => {
    e.target.disabled = true;
    try {
      const r = await api(basis + '/leads/' + lid + '/visitenkarte', { method: 'POST', body: { kanal: 'mail', an: an.value.trim() || null } });
      melde(m, r.gesendet ? 'Visitenkarte per E-Mail an ' + r.an + ' gesendet.' : 'Nicht gesendet: ' + (r.grund || 'unbekannter Fehler'), r.gesendet ? 'ok' : 'err');
    } catch (x) { melde(m, x.message); }
    e.target.disabled = false;
  } }, 'Per E-Mail senden');
  const teilen = h('button', { class: 'btn', onclick: async () => {
    try {
      const datei = await dateiHolen(basis), nav = /** @type {any} */ (navigator);
      const text = 'Hier ist meine Visitenkarte. Antippen und im Adressbuch speichern.';
      if (nav.canShare && nav.canShare({ files: [datei] })) {
        await nav.share({ files: [datei], text });   // Teilen-Menü des Handys: WhatsApp, Signal, Nachrichten …
        await vermerk('teilen'); melde(m, 'Geteilt und im Verlauf vermerkt.', 'ok'); return;
      }
      herunterladen(datei);   // Computer: Datei speichern, dann in WhatsApp Web anhängen
      const nr = wa(l.telefon);
      await vermerk('whatsapp');
      if (nr) window.open('https://wa.me/' + nr + '?text=' + encodeURIComponent(text), '_blank', 'noopener');
      melde(m, 'Die Datei wurde gespeichert. Bitte in WhatsApp als Anhang einfügen.', 'ok');
    } catch (x) { if (x && x.name !== 'AbortError') melde(m, x.message); }
  } }, 'Per WhatsApp / Teilen');
  const datei = h('button', { class: 'btn sec', onclick: async () => { try { herunterladen(await dateiHolen(basis)); await vermerk('datei'); melde(m, 'Datei gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } } }, 'Als Datei speichern');
  dialog('Visitenkarte senden', h('div', { class: 'stack' },
    h('p', { class: 'small muted' }, 'Die Visitenkarte ist eine .vcf-Datei. Wer sie öffnet, kann alle Daten mit einem Klick im Adressbuch speichern (Outlook, iPhone, Android). Der Versand wird im Verlauf des Leads vermerkt. Sie geht nur an Leads, bei denen eine Ansprache zulässig ist.'),
    h('label', {}, 'E-Mail-Adresse'), an, h('div', { class: 'row', style: 'flex-wrap:wrap;gap:8px' }, mail, teilen, datei),
    h('p', { class: 'small muted' }, 'WhatsApp: Auf dem Handy öffnet „Teilen“ direkt WhatsApp mit der Karte. Am Computer wird die Datei gespeichert und WhatsApp Web geöffnet; dort die Datei anhängen.'), m));
}

/** Karte zum Bearbeiten der eigenen Visitenkarte (Konto bzw. Einstellungen). */
export async function visitenkarteKarte(basis) {
  const box = h('div', { class: 'card' }), m = h('div');
  const d = await api(basis + '/visitenkarte'), k = d.karte;
  const feldEl = (name, label, wert, extra = {}) => [h('label', { for: 'vk_' + name }, label), h('input', { id: 'vk_' + name, name, value: wert || '', ...extra })];
  const f = h('form', { class: 'form2', onsubmit: async (e) => {
    e.preventDefault();
    try { await api(basis + '/visitenkarte', { method: 'PUT', body: Object.fromEntries(new FormData(/** @type {HTMLFormElement} */ (e.target))) }); melde(m, 'Visitenkarte gespeichert.', 'ok'); } catch (x) { melde(m, x.message); }
  } },
  ...feldEl('anzeigename', 'Name auf der Karte', k.anzeigename, { required: true, maxlength: 120 }), ...feldEl('funktion', 'Funktion', k.funktion, { maxlength: 120 }),
  ...feldEl('telefon', 'Telefon', k.telefon, { type: 'tel', maxlength: 60 }), ...feldEl('mobil', 'Mobil', k.mobil, { type: 'tel', maxlength: 60 }),
  ...feldEl('email', 'E-Mail', k.email, { type: 'email', maxlength: 254 }), ...feldEl('web', 'Internetseite', k.web, { maxlength: 200 }),
  h('div', {}, h('button', { class: 'btn' }, 'Speichern'), ' ', h('button', { type: 'button', class: 'btn sec', onclick: async () => { try { herunterladen(await dateiHolen(basis)); } catch (x) { melde(m, x.message); } } }, 'Karte herunterladen')));
  box.append(h('h2', {}, 'Meine Visitenkarte'),
    h('p', { class: 'small muted' }, 'Firma (' + d.firma + ') und Anschrift kommen aus den Firmendaten. Die Karte schickst du aus dem Lead heraus per E-Mail oder WhatsApp. Eine Karte für Kunden gibt es nicht, sie ist nur für das Markentrix-Team.'), f, m);
  return box;
}
