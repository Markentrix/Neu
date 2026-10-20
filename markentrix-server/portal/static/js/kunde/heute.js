import { h, api, melde, dialog } from '../common.js';
import { V } from './kern.js';

/** Telefonnummer für wa.me: nur Ziffern, deutsche Nummern mit 0 am Anfang bekommen 49. */
export function whatsappNummer(nr) {
  const roh = String(nr || '').trim(); let z = roh.replace(/[^\d]/g, '');
  if (roh.startsWith('+')) return z;
  if (z.startsWith('00')) return z.slice(2);
  if (z.startsWith('0')) return '49' + z.slice(1);
  return z;
}
export const telLink = (nr) => 'tel:' + String(nr || '').replace(/[^+\d]/g, '');

/** Öffnet einen Entwurf im eigenen Mail-/SMS-/WhatsApp-Programm. Das Portal versendet nichts. */
export function kanalKnoepfe(kontakt, betreff, text, nachher) {
  const mail = String(kontakt || '').includes('@');
  const t = () => text.value;
  const knopf = (beschriftung, href, kanal, art = 'btn') => h('a', { class: art, href: '#', onclick: (e) => { e.preventDefault(); const url = href(); window.open(url, '_blank', 'noopener'); nachher(kanal); } }, beschriftung);
  if (mail) return [knopf('✉ Im Mailprogramm öffnen', () => 'mailto:' + encodeURIComponent(String(kontakt).trim()) + '?subject=' + encodeURIComponent(betreff) + '&body=' + encodeURIComponent(t()), 'mail')];
  return [knopf('WhatsApp öffnen', () => 'https://wa.me/' + whatsappNummer(kontakt) + '?text=' + encodeURIComponent(t()), 'whatsapp'),
    knopf('SMS öffnen', () => 'sms:' + String(kontakt).replace(/[^+\d]/g, '') + '?body=' + encodeURIComponent(t()), 'sms', 'btn sec')];
}

/** Dialog „Antworten“: Vorlage wählen, Text anpassen, im eigenen Programm absenden. */
export async function antwortDialog(aid, danach) {
  let d;
  try { d = await api('/api/kunde/anfragen/' + aid + '/entwuerfe'); } catch (x) { alert(x.message); return; }
  const a = d.anfrage, m = h('div'), text = h('textarea', { rows: 7, maxlength: 1500, 'aria-label': 'Antworttext' });
  text.value = d.vorlagen[0].text;
  const waehler = h('select', { 'aria-label': 'Vorlage', onchange: () => { text.value = d.vorlagen.find(v => v.code === waehler.value).text; } }, d.vorlagen.map(v => h('option', { value: v.code }, v.name + (v.eigene ? ' (eigene)' : ''))));
  const markieren = async (kanal) => { try { await api('/api/kunde/anfragen/' + aid + '/beantwortet', { method: 'POST', body: { kanal } }); dlg.zu(); if (danach) danach(); } catch (x) { melde(m, x.message); } };
  const dlg = dialog('Antworten: ' + (a.name || 'Anfrage'), h('div', {},
    h('p', { class: 'small muted' }, '„' + (a.nachricht || '') + '“'),
    h('p', { class: 'small' }, 'Kontakt: ', h('b', {}, a.kontakt || 'keine Angabe')),
    h('label', {}, 'Vorlage'), waehler, h('label', {}, 'Text (kannst du anpassen)'), text, m,
    h('p', { class: 'small muted' }, 'Das Portal verschickt nichts. Die Schaltflächen öffnen dein eigenes Mail-, WhatsApp- oder SMS-Programm mit dem Text. Danach wird die Anfrage als beantwortet markiert.'),
    h('div', { class: 'heuteknoepfe' },
      a.kontakt ? kanalKnoepfe(a.kontakt, 'Ihre Anfrage', text, markieren) : '',
      a.kontakt && !String(a.kontakt).includes('@') ? h('a', { class: 'btn sec', href: telLink(a.kontakt), onclick: () => { markieren('telefon'); } }, '📞 Anrufen') : '',
      h('button', { class: 'btn sec', onclick: async () => { try { await navigator.clipboard.writeText(text.value); melde(m, 'Text kopiert.', 'ok'); } catch { text.select(); } } }, 'Text kopieren'),
      h('button', { class: 'btn sec', onclick: () => markieren('sonst') }, 'Nur als beantwortet markieren'))), true);
}

const wartet = (hh) => hh === null || hh === undefined ? '' : (hh < 1 ? 'gerade eben' : hh < 24 ? 'seit ' + Math.floor(hh) + ' Std.' : 'seit ' + Math.floor(hh / 24) + ' Tg.');

V.heute = async () => {
  const d = await api('/api/kunde/heute');
  const meld = h('div'), karteAnfragen = h('div', { class: 'card' }), karteTermine = h('div', { class: 'card' });
  const erledigt = (zeile, text) => { zeile.remove(); melde(meld, text, 'ok'); setTimeout(() => meld.replaceChildren(), 3000); };
  const anfrageZeile = (a) => {
    const z = h('div', { class: 'heutezeile' });
    z.append(h('div', { class: 'heutekopf' }, h('div', { class: 'grow' }, h('b', {}, a.name || 'Unbekannt'), a.quelle === 'telefon' ? h('span', { class: 'pill warn', style: 'margin-left:6px' }, 'Rückruf') : '', h('div', { class: 'small muted' }, (a.kontakt || '') + ' · ' + wartet(a.wartet_h))),
      a.kontakt && !String(a.kontakt).includes('@') ? h('a', { class: 'btn small', href: telLink(a.kontakt) }, '📞 Anrufen') : ''),
      a.nachricht ? h('p', { class: 'small' }, a.nachricht) : '',
      h('div', { class: 'heuteknoepfe' },
        h('button', { class: 'btn small', onclick: () => antwortDialog(a.id, () => erledigt(z, 'Als beantwortet markiert.')) }, 'Antworten'),
        h('button', { class: 'btn sec small', onclick: async () => { try { await api('/api/kunde/anfragen/' + a.id, { method: 'PATCH', body: { status: 'erledigt' } }); erledigt(z, 'Erledigt.'); } catch (x) { melde(meld, x.message); } } }, 'Erledigt'),
        h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('Als Spam markieren?')) return; try { await api('/api/kunde/anfragen/' + a.id, { method: 'PATCH', body: { status: 'spam' } }); erledigt(z, 'Als Spam markiert.'); } catch (x) { melde(meld, x.message); } } }, 'Spam')));
    return z;
  };
  const terminZeile = (t, heute) => {
    const z = h('div', { class: 'heutezeile' }), setze = async (status, text) => { try { await api('/api/kunde/termine/' + t.id, { method: 'PATCH', body: { status } }); erledigt(z, text); } catch (x) { melde(meld, x.message); } };
    z.append(h('div', { class: 'heutekopf' }, h('div', { class: 'grow' }, h('b', {}, new Date(t.beginn).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr · ' + t.titel), h('div', { class: 'small muted' }, (t.kontakt_name || '') + (t.status === 'bestaetigt' ? ' · bestätigt' : ''))),
      t.kontakt_info && !String(t.kontakt_info).includes('@') ? h('a', { class: 'btn small', href: telLink(t.kontakt_info) }, '📞 Anrufen') : ''),
      h('div', { class: 'heuteknoepfe' },
        t.status !== 'bestaetigt' ? h('button', { class: 'btn small', onclick: () => setze('bestaetigt', 'Termin bestätigt.') }, 'Bestätigen') : '',
        heute ? h('button', { class: 'btn sec small', onclick: () => setze('erledigt', 'Termin erledigt.') }, 'Erledigt') : '',
        heute ? h('button', { class: 'btn sec small', onclick: () => setze('nicht_erschienen', 'Als nicht erschienen markiert.') }, 'Nicht erschienen') : '',
        h('button', { class: 'btn sec small', onclick: () => { if (confirm('Termin absagen?')) setze('abgesagt', 'Termin abgesagt.'); } }, 'Absagen')));
    return z;
  };
  const offenA = d.anfragen.length;
  karteAnfragen.append(h('h2', {}, 'Anfragen und Rückrufe', offenA ? h('span', { class: 'badge', style: 'margin-left:8px' }, offenA) : ''),
    ...(d.modul ? (offenA ? d.anfragen.map(anfrageZeile) : [ h('p', { class: 'muted' }, 'Alles beantwortet. Neue Anfragen erscheinen hier.')]) : [h('p', { class: 'muted' }, 'Das Modul „Anfragen & Termine“ ist für dein Konto nicht freigeschaltet.')]));
  karteTermine.append(h('h2', {}, 'Termine heute'), ...(d.termine_heute.length ? d.termine_heute.map(t => terminZeile(t, true)) : [h('p', { class: 'muted' }, 'Heute stehen keine Termine an.')]),
    ...(d.termine_morgen.length ? [h('h3', {}, 'Morgen'), ...d.termine_morgen.map(t => terminZeile(t, false))] : []));
  const entscheidungen = d.freigaben || d.nachrichten ? h('div', { class: 'card' }, h('h2', {}, 'Wartet auf dich'),
    d.freigaben ? h('p', {}, h('a', { class: 'btn', href: '#freigaben' }, d.freigaben + (d.freigaben === 1 ? ' Freigabe' : ' Freigaben') + ' prüfen')) : '',
    d.nachrichten ? h('p', {}, h('a', { class: 'btn sec', href: '#nachrichten' }, d.nachrichten + (d.nachrichten === 1 ? ' Nachricht' : ' Nachrichten') + ' vom Team lesen')) : '') : '';
  const bew = d.bewertung_vorschlaege ? h('div', { class: 'card' }, h('h2', {}, 'Bewertungen'), h('p', {}, d.bewertung_vorschlaege + (d.bewertung_vorschlaege === 1 ? ' Kunde war' : ' Kunden waren') + ' kürzlich bei dir. Du kannst höflich um eine Bewertung bitten.'), h('a', { class: 'btn sec', href: '#bewertungen' }, 'Bitten vorbereiten')) : '';
  const kopf = h('div', { class: 'card' }, h('h2', {}, 'Heute'), h('p', {}, offenA ? h('span', {}, h('b', {}, offenA), (offenA === 1 ? ' Anfrage wartet' : ' Anfragen warten') + ' auf eine Antwort. ') : 'Keine offenen Anfragen. ',
    d.termine_heute.length ? h('span', {}, h('b', {}, d.termine_heute.length), d.termine_heute.length === 1 ? ' Termin heute.' : ' Termine heute.') : 'Heute keine Termine.'),
    d.rueckrufe.length ? h('p', { class: 'small' }, '📞 ' + d.rueckrufe.length + (d.rueckrufe.length === 1 ? ' Rückruf' : ' Rückrufe') + ' vom Telefon-Assistenten warten auf dich.') : '');
  return h('div', { class: 'stack' }, kopf, meld, karteAnfragen, karteTermine, entscheidungen, bew);
};
