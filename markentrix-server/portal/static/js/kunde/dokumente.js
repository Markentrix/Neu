import { h, api, datum, zeit, euro, groesse, melde } from '../common.js';
import { tabelle, statusPill, zeige, V } from './kern.js';
import { darfSchreiben } from './postfach.js';
import { FART } from './auswertung.js';

V.freigaben = async () => {
  const liste = await api('/api/kunde/freigaben');
  const wartend = liste.filter(f => f.status === 'wartet'), erledigt = liste.filter(f => f.status !== 'wartet');
  const karte = (f) => {
    const m = h('div'), kom = h('textarea', { rows: 2, maxlength: 2000, placeholder: 'Kommentar (bei „Änderung wünschen“ bitte kurz beschreiben, was angepasst werden soll)' });
    const los = async (entscheidung) => { try { await api('/api/kunde/freigaben/' + f.id + '/entscheiden', { method: 'POST', body: { entscheidung, kommentar: kom.value } }); zeige(); } catch (x) { melde(m, x.message); } };
    return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h3', { style: 'margin:0' }, f.titel + (f.version > 1 ? ' (Version ' + f.version + ')' : '')), h('span', { class: 'pill' }, FART[f.art] || f.art), h('span', { class: 'grow' }),
      h('span', { class: 'pill ' + (f.status === 'freigegeben' ? 'ok' : f.status === 'abgelehnt' ? 'bad' : f.status === 'wartet' ? 'warn' : '') }, f.status === 'wartet' ? 'wartet auf dich' : f.status === 'freigegeben' ? 'freigegeben' : f.status === 'abgelehnt' ? 'Änderung gewünscht' : 'zurückgezogen')),
      h('p', { class: 'small muted' }, 'Angefragt am ' + zeit(f.angefragt_am) + (f.veroeffentlichung_am ? ' · geplante Veröffentlichung: ' + datum(f.veroeffentlichung_am) : '')), f.vorgaenger_kommentar ? h('div', { class: 'msg info' }, 'Dein Änderungswunsch zur vorherigen Version: „' + f.vorgaenger_kommentar + '“') : '', f.inhalt ? h('div', { class: 'freitext' }, f.inhalt) : '',
      f.dateien.filter(d => String(d.mime).startsWith('image/')).map(d => h('img', { src: '/api/kunde/dateien/' + d.id, alt: d.name, style: 'max-width:100%;border-radius:10px;display:block;margin:6px 0' })),
      f.dateien.length ? h('div', { class: 'small' }, f.dateien.map(d => h('a', { class: 'dateilink', href: '/api/kunde/dateien/' + d.id, target: '_blank', rel: 'noopener' }, '📎 ' + d.name + ' (' + groesse(d.groesse) + ')'))) : '',
      f.status === 'wartet' ? (darfSchreiben() ? h('div', {}, m, kom, h('div', { class: 'row', style: 'margin-top:10px' }, zweiStufig('Freigeben', 'Ja, jetzt freigeben' + (f.veroeffentlichung_am ? ' (Veröffentlichung ' + datum(f.veroeffentlichung_am) + ')' : ''), () => los('freigegeben')), knopf('Änderung wünschen', () => los('abgelehnt'), 'btn sec'))) : h('p', { class: 'small muted' }, 'Mit deinem Zugang kannst du nur ansehen.'))
        : h('p', { class: 'small muted' }, (f.entschieden_name ? f.entschieden_name + ' am ' : 'Am ') + zeit(f.entschieden_am) + (f.kommentar ? ' · „' + f.kommentar + '“' : '')));
  };
  const knopf = (t, fn, c) => h('button', { class: c, onclick: fn }, t);
  const zweiStufig = (t, bestaetigung, fn) => { const b = h('button', { class: 'btn', onclick: () => { if (b.dataset.bereit) { b.disabled = true; fn(); return; } b.dataset.bereit = '1'; b.textContent = bestaetigung; setTimeout(() => { delete b.dataset.bereit; b.textContent = t; }, 6000); } }, t); return b; };
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Freigaben'), h('p', { class: 'small muted' }, 'Hier zeigen wir dir Beiträge, Texte und Entwürfe, bevor sie veröffentlicht werden. Mit deiner Freigabe wird Datum, Uhrzeit und dein Name festgehalten.')),
    wartend.length ? wartend.map(karte) : h('div', { class: 'card' }, h('p', { class: 'muted' }, 'Aktuell wartet nichts auf deine Freigabe.')),
    erledigt.length ? h('div', { class: 'stack' }, h('h3', {}, 'Bisherige Entscheidungen'), erledigt.map(karte)) : '');
};

// ------------------------------------------------------------- Dokumentenablage
V.unterlagen = async () => {
  const d = await api('/api/kunde/unterlagen'), m = h('div');
  const kat = h('select', {}, ...Object.entries(d.kategorien).map(([v, t]) => h('option', { value: v }, t)));
  const datei = h('input', { type: 'file', accept: '.pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx,.pptx,.txt,.csv,.zip' });
  const hoch = async () => { if (!datei.files[0]) { melde(m, 'Bitte wähle zuerst eine Datei.'); return; }
    const f = new FormData(); f.append('datei', datei.files[0]); f.append('kategorie', kat.value);
    try { await api('/api/kunde/unterlagen', { method: 'POST', body: f }); zeige(); } catch (x) { melde(m, x.message); } };
  const weg = async (z) => { if (!confirm('Datei "' + z.name + '" wirklich löschen?')) return; try { await api('/api/kunde/unterlagen/' + z.id, { method: 'DELETE' }); zeige(); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Dokumente'), h('p', { class: 'small muted' }, 'Verträge, Briefings, Logos und Material an einem sicheren Ort, für dich und das Markentrix-Team. Bitte lade hier keine Passwörter hoch, die schickst du uns nicht per Datei.'),
      darfSchreiben() ? h('div', {}, m, h('div', { class: 'row' }, kat, datei, h('button', { class: 'btn', onclick: hoch }, 'Hochladen'))) : '',
      tabelle([['Datei', z => h('a', { href: '/api/kunde/dateien/' + z.id, target: '_blank', rel: 'noopener' }, z.name)], ['Art', z => d.kategorien[z.kategorie] || '–'], ['Größe', z => groesse(z.groesse)], ['Von', z => z.von === 'team' ? 'Markentrix' : 'Dir'], ['Datum', z => zeit(z.erstellt_am)],
        ['', z => darfSchreiben() && z.von === 'kunde' ? h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen') : '']], d.dateien, 'Noch keine Dokumente.')));
};

V.dokumente = async () => {
  const d = await api('/api/kunde/dokumente');
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('h2', {}, 'Angebote'), tabelle([['Nummer', z => z.nummer], ['Titel', z => z.titel], ['Betrag', z => euro(z.betrag_cent)], ['Gültig bis', z => datum(z.gueltig_bis)], ['Status', z => statusPill(z.status)]], d.angebote, 'Keine Angebote.')),
    h('div', { class: 'card' }, h('h2', {}, 'Verträge'), tabelle([['Titel', z => z.titel], ['Beginn', z => datum(z.beginn)], ['Ende', z => datum(z.ende)], ['Status', z => statusPill(z.status)]], d.vertraege, 'Keine Verträge.')));
};
