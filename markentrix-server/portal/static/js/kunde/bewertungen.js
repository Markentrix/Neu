import { h, api, datum, melde, dialog, delta } from '../common.js';
import { V, tabelle } from './kern.js';
import { kanalKnoepfe } from './heute.js';

const ST = { geplant: 'Entwurf', gesendet: 'Von dir gesendet', abgelehnt: 'Verworfen', bewertet: 'Bewertet', fehler: 'Fehler' };

/** Entwurf prüfen, im eigenen Programm absenden, danach als gesendet markieren. */
function bitteDialog(b, kontakt, fertig) {
  const m = h('div'), text = h('textarea', { rows: 6, maxlength: 1500, 'aria-label': 'Text der Bitte' }); text.value = b.text;
  const frei = async (kanal) => { try { await api('/api/kunde/bewertungen/' + b.id + '/freigeben', { method: 'POST', body: { kanal, text: text.value } }); d.zu(); fertig(); } catch (x) { melde(m, x.message); } };
  const d = dialog('Bewertungsbitte an ' + (b.name || 'Kunde'), h('div', {}, h('p', { class: 'small muted' }, 'Prüfe den Text. Das Portal verschickt nichts: Die Schaltfläche öffnet dein eigenes Programm. Erst danach gilt die Bitte als gesendet.'),
    h('label', {}, 'Text'), text, m,
    h('div', { class: 'heuteknoepfe' }, kanalKnoepfe(kontakt, 'Kurze Bitte um Ihre Bewertung', text, frei),
      h('button', { class: 'btn sec', onclick: async () => { try { await api('/api/kunde/bewertungen/' + b.id, { method: 'DELETE' }); d.zu(); fertig(); } catch (x) { melde(m, x.message); } } }, 'Verwerfen'))), true);
}

V.bewertungen = async () => {
  const d = await api('/api/kunde/bewertungen'), m = h('div'), neu = () => { location.reload(); };
  const link = h('input', { type: 'url', value: d.link || '', placeholder: 'https://g.page/r/…/review', 'aria-label': 'Bewertungslink', maxlength: 500 });
  const txt = h('textarea', { rows: 4, maxlength: 1000, 'aria-label': 'Text der Bitte' }); txt.value = d.text;
  const einst = h('div', { class: 'card' }, h('h2', {}, 'Dein Bewertungslink'),
    h('p', { class: 'small muted' }, 'Den Link findest du in deinem Google-Unternehmensprofil unter „Bewertungen einholen“. Im Text steht {link} für den Link, {name} für den Namen und {firma} für deinen Betrieb.'),
    h('label', {}, 'Link'), link, h('label', {}, 'Text'), txt,
    h('p', { class: 'row' }, h('button', { class: 'btn', onclick: async () => { try { await api('/api/kunde/bewertungen/einstellung', { method: 'PUT', body: { link: link.value, text: txt.value === d.standard_text ? null : txt.value } }); melde(m, 'Gespeichert.', 'ok'); setTimeout(neu, 600); } catch (x) { melde(m, x.message); } } }, 'Speichern')));
  const neueBitte = async (name, kontakt, ausloeser) => { try { const r = await api('/api/kunde/bewertungen/bitte', { method: 'POST', body: { name, kontakt, ausloeser: ausloeser || null } }); bitteDialog({ id: r.id, name, text: r.text }, kontakt, neu); } catch (x) { melde(m, x.message); } };
  const vor = h('div', { class: 'card' }, h('h2', {}, 'Wen könntest du bitten?'),
    d.vorschlaege.length ? tabelle([['Kunde', z => z.name], ['Auftrag', z => z.titel], ['Wann', z => datum(z.beginn)], ['', z => z.kontakt ? h('button', { class: 'btn small', onclick: () => neueBitte(z.name, z.kontakt, z.titel) }, 'Bitte vorbereiten') : h('span', { class: 'small muted' }, 'Kontakt fehlt (im Termin ergänzen)')]], d.vorschlaege)
      : h('p', { class: 'muted' }, 'Hier erscheinen Kunden aus erledigten Terminen der letzten 30 Tage. Du kannst auch selbst jemanden eintragen:'));
  const fname = h('input', { placeholder: 'Name', maxlength: 120, 'aria-label': 'Name' }), fk = h('input', { placeholder: 'E-Mail oder Handynummer', maxlength: 200, 'aria-label': 'Kontakt' });
  const manuell = h('div', { class: 'card' }, h('h2', {}, 'Jemanden eintragen'), h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Name'), fname), h('div', {}, h('label', {}, 'E-Mail oder Handynummer'), fk), h('div', {}, h('label', {}, ' '), h('button', { class: 'btn', onclick: () => { if (!fname.value.trim() || !fk.value.trim()) { melde(m, 'Bitte Name und Kontakt eintragen.'); return; } neueBitte(fname.value, fk.value, null); } }, 'Bitte vorbereiten'))));
  const liste = h('div', { class: 'card' }, h('h2', {}, 'Bisherige Bitten'), tabelle([['Wann', z => datum(z.erstellt_am)], ['An', z => z.name], ['Weg', z => z.kanal || '–'], ['Status', z => h('span', { class: 'pill ' + (z.status === 'gesendet' || z.status === 'bewertet' ? 'ok' : z.status === 'geplant' ? 'warn' : '') }, ST[z.status] || z.status)],
    ['', z => z.status === 'geplant' ? h('button', { class: 'btn small sec', onclick: () => bitteDialog(z, z.kontakt, neu) }, 'Öffnen') : '']], d.liste, 'Noch keine Bitten.'));
  const g = d.google, kopf = h('div', { class: 'card' }, h('h2', {}, 'Bewertungen im Blick'),
    h('p', {}, h('b', {}, d.gesendet_30d), ' Bitten in den letzten 30 Tagen von dir gesendet.'),
    g.jetzt && g.jetzt.google_bewertungen !== null ? h('p', {}, 'Google ' + (g.jetzt.google_sterne ? g.jetzt.google_sterne.toString().replace('.', ',') + ' Sterne, ' : '') + g.jetzt.google_bewertungen + ' Bewertungen (Stand ' + g.jetzt.monat + ') ', g.vorher && g.vorher.google_bewertungen !== null ? delta(g.jetzt.google_bewertungen, g.vorher.google_bewertungen, true) : '')
      : h('p', { class: 'small muted' }, 'Die Google-Zahlen trägt dein Markentrix-Team monatlich ein, sobald sie vorliegen.'));
  const regeln = h('div', { class: 'card' }, h('h2', {}, 'Wichtig: so bleibt es sauber'),
    h('ul', {}, h('li', {}, 'Bitte nur Kunden fragen, mit denen du wirklich Kontakt hattest.'), h('li', {}, 'Die Bitte ist freiwillig. Keine Gegenleistung, kein Rabatt, kein Druck.'), h('li', {}, 'Bitte nicht nur zufriedene Kunden aussuchen: Der Link gilt für alle.'), h('li', {}, 'Per Mail ist eine Bewertungsbitte rechtlich heikler (Werbung). Persönlich, per WhatsApp oder SMS an Kunden, die dir ihre Nummer gegeben haben, ist üblicher. Im Zweifel frag deine Rechtsberatung.'), h('li', {}, 'Dieselbe Person wird innerhalb von 90 Tagen nur einmal vorgeschlagen.')));
  return h('div', { class: 'stack' }, h('div', {}, m), kopf, d.link ? vor : '', d.link ? manuell : '', einst, liste, regeln);
};
