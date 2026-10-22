import { h, api, datum, zeit, groesse, melde, toast } from '../common.js';
import { tabelle, statusPill, zeige, V } from './kern.js';

V.website = async () => {
  const d = await api('/api/kunde/website');
  const domainKarte = h('details', { class: 'card' }, h('summary', {}, h('b', {}, 'Meine Domain auf Markentrix umstellen')),
    h('p', {}, 'Damit deine Website unter deiner eigenen Adresse erreichbar ist, muss bei deinem Domain-Anbieter (z. B. IONOS, Strato, GoDaddy) der Eintrag geändert werden. Das dauert etwa 10 Minuten.'),
    h('ol', {}, h('li', {}, 'Melde dich bei deinem Domain-Anbieter an und öffne die DNS-Einstellungen deiner Domain.'), h('li', {}, 'Wir schicken dir die genauen Werte (A-Eintrag für „@“ und „www“) auf Wunsch per Nachricht.'), h('li', {}, 'Trage sie dort ein und gib uns Bescheid. Die Umstellung kann bis zu einigen Stunden dauern, wir prüfen sie automatisch.')),
    h('p', {}, h('a', { class: 'btn', href: '#nachrichten' }, 'Anleitung anfordern oder Hilfe holen')), h('p', { class: 'small muted' }, 'Du kannst dich auch einfach melden, dann übernehmen wir das gemeinsam am Telefon.'));
  return h('div', { class: 'stack' }, domainKarte,
    h('div', { class: 'card' }, h('h2', {}, 'Websites'), tabelle([['Domain', z => h('a', { href: 'https://' + z.domain, target: '_blank', rel: 'noopener' }, z.domain)], ['Art', z => z.art], ['Status', z => statusPill(z.status)], ['Zuletzt aktualisiert', z => zeit(z.letzte_veroeffentlichung)]], d.websites, 'Noch keine Website.')),
    h('div', { class: 'card' }, h('h2', {}, 'Projekte'), tabelle([['Titel', z => z.titel], ['Art', z => z.art], ['Status', z => statusPill(z.status)], ['Link', z => z.url && h('a', { href: z.url, target: '_blank', rel: 'noopener' }, 'Öffnen')]], d.projekte, 'Keine Projekte.')));
};

const IART = { angebot: 'Angebot', event: 'Event', hinweis: 'Hinweis', geschlossen: 'Heute geschlossen' };
async function inhalteKarte() {
  const d = await api('/api/kunde/angebots-inhalte'), m = h('div');
  const art = h('select', {}, Object.entries(IART).map(([v, t]) => h('option', { value: v }, t)));
  const titel = {}, text = {};
  const felder = d.sprachen.map(sp => {
    titel[sp] = h('input', { maxlength: 200, placeholder: 'Titel (' + d.sprachnamen[sp] + ')' + (sp === 'de' ? ', Pflicht' : ', freiwillig'), dir: sp === 'ar' ? 'rtl' : 'ltr' });
    text[sp] = h('textarea', { rows: 2, maxlength: 2000, placeholder: 'Beschreibung (' + d.sprachnamen[sp] + '), freiwillig', dir: sp === 'ar' ? 'rtl' : 'ltr' });
    return h('div', { class: 'sprachblock' }, h('label', {}, d.sprachnamen[sp] + (sp === 'de' ? ' (Hauptsprache)' : '')), titel[sp], text[sp]);
  });
  const preis = h('input', { maxlength: 40, placeholder: 'Preis, z. B. 1,99 € / kg (freiwillig)' }), von = h('input', { type: 'date' }), bis = h('input', { type: 'date' });
  const nachher = (r) => { if (r.hinweis) toast(r.hinweis); zeige(); };
  const ziele = d.sprachen.filter(x => x !== 'de');
  const uebersetzen = async (e) => {
    const texte = {}; if (titel.de.value.trim()) texte.titel = titel.de.value; if (text.de.value.trim()) texte.text = text.de.value;
    if (!Object.keys(texte).length) { melde(m, 'Bitte schreibe zuerst den deutschen Titel oder Text.'); return; }
    const b = e.target; b.disabled = true; b.textContent = 'Übersetze …'; melde(m, '');
    try {
      const r = await api('/api/kunde/angebots-inhalte/uebersetzen', { method: 'POST', body: { texte, ziele } }); let n = 0;
      ziele.forEach(sp => { if (r.uebersetzungen.titel && r.uebersetzungen.titel[sp] && !titel[sp].value.trim()) { titel[sp].value = r.uebersetzungen.titel[sp]; n++; } if (r.uebersetzungen.text && r.uebersetzungen.text[sp] && !text[sp].value.trim()) { text[sp].value = r.uebersetzungen.text[sp]; n++; } });
      melde(m, n ? r.hinweis : 'Die anderen Felder sind schon ausgefüllt. Leere sie, wenn du neu übersetzen lassen willst.', n ? 'ok' : 'info');
    } catch (x) { melde(m, x.message); }
    b.disabled = false; b.textContent = 'Aus Deutsch übersetzen';
  };
  const speichern = async () => {
    const t = {}, x = {}; d.sprachen.forEach(sp => { t[sp] = titel[sp].value; x[sp] = text[sp].value; });
    try { nachher(await api('/api/kunde/angebots-inhalte', { method: 'POST', body: { art: art.value, titel: t, text: x, preis: preis.value || null, gueltig_von: von.value || null, gueltig_bis: bis.value || null } })); } catch (e) { melde(m, e.message); }
  };
  const umschalten = async (z) => { try { nachher(await api('/api/kunde/angebots-inhalte/' + z.id, { method: 'PATCH', body: { aktiv: !z.aktiv } })); } catch (e) { melde(m, e.message); } };
  const weg = async (z) => { if (!confirm('Eintrag wirklich löschen?')) return; try { nachher(await api('/api/kunde/angebots-inhalte/' + z.id, { method: 'DELETE' })); } catch (e) { melde(m, e.message); } };
  const name = (z) => (z.titel.de || Object.values(z.titel)[0] || (z.art === 'geschlossen' ? 'Heute geschlossen' : '–'));
  return h('div', { class: 'card' }, h('h2', {}, 'Texte, Events und Hinweise'),
    h('p', { class: 'small muted' }, 'Zusätzlich zur Datei: Angebote mit Preis, Veranstaltungen, Hinweise und „heute geschlossen“. Sprachen auf deiner Website: ' + d.sprachen.map(s => d.sprachnamen[s]).join(', ') + '. Ist eine Übersetzung leer, zeigen wir den deutschen Text.'),
    m, h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Art'), art), h('div', {}, h('label', {}, 'Preis'), preis), h('div', {}, h('label', {}, 'Gültig von (leer = sofort)'), von), h('div', {}, h('label', {}, 'Gültig bis (leer = unbegrenzt)'), bis)),
    h('div', { class: 'stack', style: 'margin-top:10px' }, felder),
    h('div', { class: 'row', style: 'margin-top:10px' }, ziele.length ? h('button', { class: 'btn sec', type: 'button', onclick: uebersetzen }, 'Aus Deutsch übersetzen') : '', h('button', { class: 'btn', onclick: speichern }, 'Speichern und veröffentlichen')),
    ziele.length ? h('p', { class: 'small muted' }, 'Tipp: Deutsch ausfüllen, auf „Aus Deutsch übersetzen“ klicken, kurz prüfen, dann speichern. Die Übersetzung erstellt der Agent automatisch, bitte lies sie kurz durch.') : '',
    h('h3', {}, 'Aktuelle Einträge'),
    tabelle([['Art', z => IART[z.art]], ['Titel', name], ['Preis', z => z.preis || ''], ['Gültig', z => [z.gueltig_von ? datum(z.gueltig_von) : '', z.gueltig_bis ? ' – ' + datum(z.gueltig_bis) : ''].join('')], ['Sprachen', z => Object.keys(z.titel).concat(Object.keys(z.text)).filter((v, i, a) => a.indexOf(v) === i).join(', ')],
      ['Status', z => h('span', { class: 'pill ' + (z.aktiv ? 'ok' : '') }, z.aktiv ? 'sichtbar' : 'ausgeblendet')],
      ['', z => h('div', { class: 'row' }, h('button', { class: 'btn sec small', onclick: () => umschalten(z) }, z.aktiv ? 'Ausblenden' : 'Einblenden'), h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen'))]], d.inhalte, 'Noch keine Einträge.'));
}

V.wochenangebote = async () => {
  const d = await api('/api/kunde/wochenangebote');
  const m = h('div'), dat = h('input', { type: 'file', name: 'datei', accept: '.pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png', required: true });
  const knopf = h('button', { class: 'btn' }, 'Hochladen und veröffentlichen');
  const f = h('form', { onsubmit: async (e) => {
    e.preventDefault(); knopf.disabled = true; melde(m, '');
    try {
      const r = await api('/api/kunde/wochenangebote', { method: 'POST', body: new FormData(e.target) });
      if (r.status === 'veroeffentlicht') melde(m, 'Veröffentlicht: ' + r.adresse, 'ok'); else melde(m, r.hinweis || 'Gespeichert.', r.status === 'fehler' ? 'err' : 'info');
      setTimeout(() => location.reload(), 2500);
    } catch (x) { melde(m, x.message); knopf.disabled = false; }
  } },
    h('div', { class: 'drop' }, h('p', {}, 'PDF, JPG oder PNG – bis 10 MB'), dat),
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Gültig von (optional)'), h('input', { type: 'date', name: 'gueltig_von' })), h('div', {}, h('label', {}, 'Gültig bis (optional)'), h('input', { type: 'date', name: 'gueltig_bis' }))),
    h('p', {}, knopf));
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Wochenangebote hochladen'),
      h('p', { class: 'muted small' }, d.website ? 'Die Datei erscheint sofort auf ' + d.website + '/angebote/. Das alte Angebot wandert ins Archiv.' : 'Noch keine Website verknüpft – Dateien werden gespeichert und vom Team veröffentlicht.'), m, f),
    await inhalteKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'Bisherige Uploads'), tabelle([['Datum', z => zeit(z.erstellt_am)], ['Datei', z => z.dateiname], ['Größe', z => groesse(z.groesse)], ['Gültig', z => [datum(z.gueltig_von), z.gueltig_bis ? ' – ' + datum(z.gueltig_bis) : ''].join('')], ['Status', z => [statusPill(z.status), z.fehlertext && h('div', { class: 'small muted' }, z.fehlertext)]]], d.uploads, 'Noch keine Uploads.')));
};

V.werbung = async () => {
  const d = await api('/api/kunde/berichte');
  return h('div', { class: 'card' }, h('h2', {}, 'Werbung & Berichte'), tabelle([['Zeitraum', z => [datum(z.zeitraum_von), ' – ', datum(z.zeitraum_bis)].join('')], ['Titel', z => z.titel], ['Art', z => z.art], ['Erstellt', z => datum(z.erstellt_am)]], d, 'Noch keine Berichte.'));
};
