// Verträge aus dem Portal: Referenzvertrag (beim Kunden) und Handelsvertretervertrag (beim Vertriebler).
// Das Portal füllt das PDF-Formular vor, schickt es per Mail und legt die unterschriebene Fassung ab.
import { h, api, datum, melde } from '../common.js';
import { V, fehler, feld, knopf, kopf, pill, select, tabelle } from './kern.js';

const stand = (z) => z.widerrufen_am ? h('span', { class: 'pill bad' }, 'widerrufen ' + datum(z.widerrufen_am)) : z.unterschrieben_am ? h('span', { class: 'pill ok' }, (z.online_am ? 'online bestätigt ' : 'unterschrieben ') + datum(z.unterschrieben_am)) : z.gesendet_am ? h('span', { class: 'pill warn' }, 'gesendet an ' + z.gesendet_an + ' (' + datum(z.gesendet_am) + ')' + (z.erinnerungen ? ', ' + z.erinnerungen + '× erinnert' : '')) : h('span', { class: 'pill' }, 'nur erstellt');

function ablegen(z, m) {
  const datei = h('input', { type: 'file', accept: 'application/pdf,image/png,image/jpeg' }), tag = h('input', { type: 'date', value: new Date().toISOString().slice(0, 10), style: 'max-width:160px' });
  return h('span', { class: 'row' }, datei, tag, knopf('Unterschrieben ablegen', () => {
    const f = datei.files[0]; if (!f) return fehler(m, { message: 'Bitte zuerst die unterschriebene Datei wählen.' });
    const r = new FileReader();
    r.onload = async () => { try { await api('/api/admin/vertragsdokumente/' + z.id + '/upload', { method: 'POST', body: { datei_base64: r.result, datei_name: f.name, unterschrieben_am: tag.value } }); location.reload(); } catch (x) { fehler(m, x); } };
    r.readAsDataURL(f);
  }, 'btn small'));
}

function liste(zeilen, m, leer) {
  const aktion = (z) => h('span', { class: 'row' },
    h('a', { class: 'btn sec small', href: '/api/admin/vertragsdokumente/' + z.id + '/vorlage.pdf', target: '_blank', rel: 'noopener' }, 'PDF'),
    knopf('Erneut senden', async () => { if (!confirm('Den Vertrag jetzt per E-Mail senden?')) return; try { await api('/api/admin/vertragsdokumente/' + z.id + '/senden', { method: 'POST', body: {} }); melde(m, 'Gesendet.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { fehler(m, x); } }, 'sec small'),
    z.hat_datei ? h('a', { class: 'btn sec small', href: '/api/admin/vertragsdokumente/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Unterschrieben ansehen') : ablegen(z, m),
    knopf('Löschen', async () => { if (!confirm('Eintrag löschen' + (z.hat_datei ? ' (auch die abgelegte unterschriebene Datei)' : '') + '?')) return; try { await api('/api/admin/vertragsdokumente/' + z.id, { method: 'DELETE' }); location.reload(); } catch (x) { fehler(m, x); } }, 'bad small'));
  return tabelle([['Erstellt', z => datum(z.erstellt_am)], ['Stand', stand], ['', aktion]], zeilen, leer);
}

async function absenden(m, pfad, o, senden) {
  try { const r = await api(pfad, { method: 'POST', body: { ...o, senden } }); melde(m, r.gesendet ? 'Vertrag erstellt und per Mail gesendet.' : 'Vertrag erstellt. Du findest ihn in der Liste.', 'ok'); setTimeout(() => location.reload(), 1200); }
  catch (x) { fehler(m, x); }
}

export async function referenzKarte(kid, k) {
  const zeilen = await api('/api/admin/kunden/' + kid + '/vertragsdokumente'), m = h('div');
  const f = { projekt: feld('Projekt', 'projekt', '', { placeholder: 'z. B. Website www.beispiel.de', maxlength: 200 }), vom: feld('Hauptvertrag vom', 'hv', '', { placeholder: 'z. B. 01.10.2026', maxlength: 40 }),
    zeit: feld('Umsetzungszeitraum', 'zeit', '', { placeholder: 'z. B. 01.09.–30.09.2026', maxlength: 80 }), vertreter: feld('Vertreten durch', 'v', k.ansprechpartner || '', { maxlength: 200 }),
    an: feld('E-Mail an', 'an', k.email || '', { maxlength: 200 }) };
  const werte = () => ({ projekt: f.projekt.querySelector('input').value, hauptvertrag_vom: f.vom.querySelector('input').value, zeitraum: f.zeit.querySelector('input').value, vertreter: f.vertreter.querySelector('input').value, an: f.an.querySelector('input').value });
  return h('div', { class: 'card' }, h('h2', {}, 'Referenzvertrag ', zeilen.some(z => z.unterschrieben_am) ? h('span', { class: 'pill ok' }, 'liegt vor') : h('span', { class: 'pill' }, 'optional')),
    h('p', { class: 'small muted' }, 'Erlaubt uns, das Projekt des Kunden als Referenz zu zeigen. Das Portal füllt Firma, Anschrift, Ansprechpartner und Projekt im Formular vor. Welche Punkte freigegeben sind, kreuzt der Kunde selbst in Anlage 1 an (freiwillig, nichts ist vorangekreuzt). Danach unterschreiben lassen und hier ablegen.'), m,
    liste(zeilen, m, 'Noch kein Referenzvertrag erstellt.'),
    h('div', { class: 'form2', style: 'margin-top:10px' }, f.projekt, f.vom, f.zeit, f.vertreter, f.an),
    h('div', { class: 'row', style: 'margin-top:8px' }, knopf('Erstellen und per Mail senden', () => absenden(m, '/api/admin/kunden/' + kid + '/referenzvertrag', werte(), true), 'btn'), knopf('Nur erstellen', () => absenden(m, '/api/admin/kunden/' + kid + '/referenzvertrag', werte(), false), 'sec')));
}

export async function handelsvertreterKarte(pid, p) {
  const zeilen = await api('/api/admin/vertrieb/partner/' + pid + '/vertragsdokumente'), m = h('div');
  const i = (l, n, w = '', e = {}) => feld(l, n, w, { maxlength: 200, ...e });
  const f = { name: i('Name / Firma', 'name', p.firma || p.name), rechtsform: i('Rechtsform', 'rf', '', { placeholder: 'z. B. Einzelunternehmen' }), strasse: i('Straße, Hausnummer', 's'), ort: i('PLZ, Ort', 'o'), mail: i('E-Mail', 'mail', p.email || ''), steuer: i('Steuernummer / USt-IdNr.', 'st'),
    einmal: i('Provision einmalig (%)', 'e', '', { placeholder: 'Vorlage: 20', maxlength: 10 }), monat: i('Provision laufend (%)', 'm', '', { placeholder: 'Vorlage: 15', maxlength: 10 }), praemie: i('Prämie', 'p', '', { placeholder: 'Vorlage: 10', maxlength: 10 }), vorschuss: i('Vorschuss', 'v', '', { placeholder: 'Vorlage: 50', maxlength: 10 }) };
  const art = select('b', [['', 'Partner wählt selbst'], ['haupt', 'Hauptberuf'], ['neben', 'Nebenberuf']], '');
  const w = (n) => f[n].querySelector('input').value;
  const werte = () => ({ name: w('name'), rechtsform: w('rechtsform'), strasse: w('strasse'), ort: w('ort'), mail: w('mail'), steuer: w('steuer'), beauftragung: art.value, einmal: w('einmal'), monat: w('monat'), praemie: w('praemie'), vorschuss: w('vorschuss'), an: w('mail') });
  const pfad = '/api/admin/vertrieb/partner/' + pid + '/handelsvertretervertrag';
  return h('div', { class: 'card' }, h('h2', {}, 'Handelsvertretervertrag ', zeilen.some(z => z.unterschrieben_am) ? h('span', { class: 'pill ok' }, 'liegt vor') : h('span', { class: 'pill warn' }, 'fehlt')),
    h('p', { class: 'small muted' }, 'Das Portal füllt das Vertragsformular mit den Angaben des Vertrieblers vor und schickt es per Mail. Der Vertriebler ergänzt Anlage 3 selbst, unterschreibt und schickt es zurück. Beim Ablegen der unterschriebenen Fassung wird das Datum bei „Vereinbarung“ eingetragen. Leere Provisionsfelder behalten die Werte aus der Vorlage.'), m,
    liste(zeilen, m, 'Noch kein Vertrag erstellt.'),
    h('div', { class: 'form2', style: 'margin-top:10px' }, f.name, f.rechtsform, f.strasse, f.ort, f.mail, f.steuer, h('div', {}, h('label', {}, 'Beauftragung'), art), f.einmal, f.monat, f.praemie, f.vorschuss),
    h('div', { class: 'row', style: 'margin-top:8px' }, knopf('Erstellen und per Mail senden', () => absenden(m, pfad, werte(), true), 'btn'), knopf('Nur erstellen', () => absenden(m, pfad, werte(), false), 'sec')));
}

const STAND = { keins: ['', 'nicht angefragt'], erstellt: ['warn', 'erstellt, nicht gesendet'], gesendet: ['warn', 'wartet auf Antwort'], unterschrieben: ['ok', 'liegt vor'], widerrufen: ['bad', 'widerrufen'] };
const standPill = (x) => h('span', { class: 'pill ' + STAND[x.stand][0] }, STAND[x.stand][1] + (x.am && x.stand === 'gesendet' ? ' seit ' + datum(x.am) : ''));

export async function einarbeitungKarte(pid) {
  const e = await api('/api/admin/vertrieb/partner/' + pid + '/einarbeitung');
  return h('div', { class: 'card' }, h('h2', {}, 'Einarbeitung ', pill(e.punkte.every(x => x.erledigt) ? 'aktiv' : 'neu')),
    h('ul', { style: 'list-style:none;padding:0;margin:0' }, e.punkte.map(x => h('li', { style: 'margin:4px 0' }, (x.erledigt ? '✅ ' : '⬜ ') + x.text))));
}

V.vertraege = async () => {
  const [u, r, rs] = await Promise.all([api('/api/admin/vertragsdokumente/uebersicht'), api('/api/admin/vertragsdokumente/referenzen'), api('/api/admin/referenzseite')]), m = h('div');
  const nurOffen = h('input', { type: 'checkbox', style: 'width:auto' }), kunden = h('div'), partner = h('div');
  const zeichne = () => {
    const k = u.kunden.filter(x => !nurOffen.checked || !x.avv_ok || x.referenz.stand === 'gesendet'), p = u.partner.filter(x => !nurOffen.checked || x.vertrag.stand !== 'unterschrieben' && !x.vereinbarung_am || x.einarbeitung_erledigt < x.einarbeitung_gesamt);
    kunden.replaceChildren(tabelle([['Kunde', x => h('a', { href: '#kunde/' + x.id }, x.firma)], ['AVV', x => x.avv_ok ? h('span', { class: 'pill ok' }, 'liegt vor') : x.avv_im_portal ? h('span', { class: 'pill warn' }, 'im Portal, wartet') : h('span', { class: 'pill bad' }, 'fehlt')], ['Referenzvertrag (freiwillig)', x => standPill(x.referenz)]], k, 'Nichts offen.'));
    partner.replaceChildren(tabelle([['Vertriebler', x => h('a', { href: '#partner/' + x.id }, x.name)], ['Handelsvertretervertrag', x => x.vereinbarung_am ? h('span', { class: 'pill ok' }, 'liegt vor ' + datum(x.vereinbarung_am)) : standPill(x.vertrag)],
      ['Einarbeitung', x => h('span', { class: 'pill ' + (x.einarbeitung_erledigt === x.einarbeitung_gesamt ? 'ok' : 'warn'), title: x.einarbeitung_offen.join(', ') }, x.einarbeitung_erledigt + ' von ' + x.einarbeitung_gesamt)]], p, 'Nichts offen.'));
  };
  nurOffen.addEventListener('change', zeichne); zeichne();
  const widerrufen = (z, an) => knopf(an ? 'Widerruf vermerken' : 'Widerruf zurücknehmen', async () => { if (!confirm(an ? 'Widerruf der Referenz von ' + z.firma + ' vermerken? Danach alle Inhalte entfernen.' : 'Widerruf wirklich zurücknehmen?')) return; try { await api('/api/admin/vertragsdokumente/' + z.id + '/widerruf', { method: 'POST', body: { widerrufen: an } }); location.reload(); } catch (x) { fehler(m, x); } }, 'sec small');
  const frei = (z) => z.strukturiert ? h('div', {}, h('div', { class: 'small' }, z.elemente.map(e => e.name + (e.text ? ' („' + e.text + '“)' : '')).join(' · ') || 'keine Elemente'), h('div', { class: 'small muted' }, 'Kanäle: ' + (z.kanaele.join(', ') || '–') + (z.personen ? ' · Personen erlaubt' : '') + (z.einschraenkungen && z.einschraenkungen !== 'keine' ? ' · Einschränkung: ' + z.einschraenkungen : ''))) : h('span', { class: 'small muted' }, 'laut unterschriebener Datei' + (z.hat_datei ? '' : ''));
  const rsAktiv = h('input', { type: 'checkbox', checked: rs.aktiv, style: 'width:auto' }), rsTitel = h('input', { value: rs.titel, maxlength: 120, 'aria-label': 'Titel' }), rsIntro = h('input', { value: rs.intro, maxlength: 400, 'aria-label': 'Einleitung' });
  const seitenKarte = h('div', { class: 'card' }, h('h2', {}, 'Referenzseite für die Website'),
    h('p', { class: 'small muted' }, 'Zeigt automatisch nur, was Kunden ausdrücklich für „Website von Markentrix“ freigegeben haben und mit Wortlaut angegeben haben (Kurzbeschreibung, Kennzahlen, Zitat). Widerrufene Freigaben verschwinden sofort. Logos und Abbildungen fügst du bei Bedarf von Hand ein. Aktuell würden ' + rs.eintraege.length + ' Einträge erscheinen.'),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, rsAktiv, 'Seite veröffentlichen (öffentlich unter /referenzen)'), h('label', {}, 'Titel'), rsTitel, h('label', {}, 'Einleitung'), rsIntro,
    h('p', {}, knopf('Speichern', async () => { try { await api('/api/admin/referenzseite', { method: 'PUT', body: { aktiv: rsAktiv.checked, titel: rsTitel.value, intro: rsIntro.value } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } }), ' ', rs.aktiv ? h('a', { class: 'btn sec', href: '/referenzen', target: '_blank', rel: 'noopener' }, 'Seite ansehen') : ''));
  return h('div', { class: 'stack' }, kopf('Verträge', h('span', { class: 'pill ' + (u.offen.avv || u.offen.vertrag ? 'warn' : 'ok') }, 'AVV offen: ' + u.offen.avv + ' · HV-Vertrag offen: ' + u.offen.vertrag + ' · Referenz wartet: ' + u.offen.referenz_gesendet)), m,
    h('div', { class: 'card' }, h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, nurOffen, 'Nur Offenes zeigen')),
    h('div', { class: 'card' }, h('h2', {}, 'Kunden'), kunden), h('div', { class: 'card' }, h('h2', {}, 'Vertriebler'), partner),
    h('div', { class: 'card' }, h('h2', {}, 'Referenzen: was darf gezeigt werden?'), h('p', { class: 'small muted' }, 'Nur was hier steht, darf in der Eigenwerbung genutzt werden. Bei einem Widerruf alle Inhalte innerhalb von 7 Tagen entfernen.'),
      tabelle([['Kunde', z => h('a', { href: '#kunde/' + z.kunden_id }, z.firma)], ['Bestätigt', z => z.unterschrieben_am ? datum(z.unterschrieben_am) + (z.online_am ? ' (online)' : '') : '–'], ['Freigegeben', frei], ['', z => h('span', { class: 'row' }, z.hat_datei ? h('a', { class: 'btn sec small', href: '/api/admin/vertragsdokumente/' + z.id + '/datei', target: '_blank', rel: 'noopener' }, 'Vertrag') : '', widerrufen(z, true))]], r.aktiv, 'Noch keine unterschriebenen Referenzverträge.')),
    seitenKarte,
    r.widerrufen.length ? h('div', { class: 'card' }, h('h2', {}, 'Widerrufene Referenzen'), tabelle([['Kunde', z => z.firma], ['Widerrufen am', z => datum(z.widerrufen_am)], ['', z => widerrufen(z, false)]], r.widerrufen)) : '');
};
