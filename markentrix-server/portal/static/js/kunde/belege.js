import { h, api, datum, zeit, euro, melde } from '../common.js';
import { inhaber, tabelle, V } from './kern.js';

V.belege = async () => {
  const d = await api('/api/kunde/belege'), m = h('div');
  const art = (z) => z.storno_von ? 'Storno' : z.art === 'rechnung' ? 'Rechnung' : 'Angebot';
  const st = (z) => h('span', { class: 'pill ' + (z.ueberfaellig ? 'bad' : ['bezahlt', 'angenommen'].includes(z.status) ? 'ok' : ['abgelehnt', 'storniert'].includes(z.status) ? 'bad' : 'warn') }, z.ueberfaellig ? 'überfällig' : z.status === 'gestellt' || z.status === 'versendet' ? (z.art === 'rechnung' ? 'offen' : 'wartet auf Annahme') : z.status);
  const aktion = (z) => h('span', { class: 'row' }, h('a', { class: 'btn sec small', href: '/api/kunde/belege/' + z.id + '/pdf' }, 'PDF'),
    z.art === 'angebot' && ['gestellt', 'versendet'].includes(z.status) ? h('button', { class: 'btn small', onclick: async () => { if (!confirm('Angebot ' + z.nummer + ' verbindlich annehmen?')) return; try { await api('/api/kunde/belege/' + z.id + '/annehmen', { method: 'POST' }); melde(m, 'Danke! Das Angebot ist angenommen.', 'ok'); setTimeout(() => location.reload(), 900); } catch (x) { melde(m, x.message); } } }, 'Annehmen') : '');
  const mandat = await mandatKarte();
  return h('div', { class: 'stack' }, mandat, h('div', { class: 'card' }, h('h2', {}, 'Angebote & Rechnungen'), m, tabelle([['Nummer', z => z.nummer], ['Art', art], ['Betreff', z => z.betreff], ['Datum', z => datum(z.datum)], ['Fällig/gültig bis', z => datum(z.faellig_am)], ['Betrag', z => euro(z.brutto_cent)], ['Status', st], ['', aktion]], d, 'Noch keine Angebote oder Rechnungen.')));
};

async function mandatKarte() {
  const d = await api('/api/kunde/lastschrift'), m = h('div');
  if (d.mandat) return h('div', { class: 'card' }, h('h2', {}, 'Bezahlung per Lastschrift'), m,
    h('p', {}, h('span', { class: 'pill ok' }, 'aktiv'), ' Konto auf ', h('b', {}, d.mandat.kontoinhaber), ', IBAN endet auf ', h('b', {}, d.mandat.iban_ende), '. Mandatsreferenz: ', d.mandat.referenz, '.'),
    h('p', { class: 'small muted' }, 'Offene Rechnungen werden von diesem Konto eingezogen. Vorher bekommst du eine Mail mit Betrag und Datum.'),
    h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('Lastschriftmandat wirklich widerrufen? Danach überweist du Rechnungen wieder selbst.')) return; try { await api('/api/kunde/lastschrift', { method: 'DELETE' }); location.reload(); } catch (x) { melde(m, x.message); } } }, 'Mandat widerrufen'));
  if (!d.verfuegbar) return h('div', { class: 'card' }, h('h2', {}, 'Bezahlung'), h('p', { class: 'muted small' }, 'Bitte überweise Rechnungen mit der Rechnungsnummer als Verwendungszweck. Die Bankverbindung und ein QR-Code für dein Banking stehen auf der Rechnung.'));
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const x = e.target;
    try { await api('/api/kunde/lastschrift', { method: 'POST', body: { kontoinhaber: x.inhaber.value, iban: x.iban.value, bic: x.bic.value, zustimmung: x.ok.checked } }); melde(m, 'Danke! Das Mandat ist erteilt. Eine Bestätigung kommt per E-Mail.', 'ok'); setTimeout(() => location.reload(), 1200); } catch (z) { melde(m, z.message); } } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Kontoinhaber'), h('input', { name: 'inhaber', required: true, maxlength: 70 })), h('div', {}, h('label', {}, 'IBAN'), h('input', { name: 'iban', required: true, placeholder: 'DE00 0000 0000 0000 0000 00' }))),
    h('label', {}, 'BIC (optional)'), h('input', { name: 'bic', maxlength: 11 }),
    h('label', { style: 'display:flex;gap:8px;align-items:flex-start;color:inherit;font-size:13px;margin:12px 0' }, h('input', { type: 'checkbox', name: 'ok', style: 'width:auto;margin-top:3px' }), d.text),
    h('p', {}, h('button', { class: 'btn' }, 'Lastschriftmandat erteilen')));
  return h('div', { class: 'card' }, h('h2', {}, 'Bequem per Lastschrift bezahlen'), h('p', { class: 'small muted' }, 'Optional: Du erteilst uns ein SEPA-Mandat, und wir ziehen Rechnungen automatisch ein. Sonst überweist du wie gewohnt. Gläubiger-ID: ' + d.glaeubiger_id), m, f);
}

V.anrufe = async () => {
  const d = await api('/api/kunde/anrufe');
  const dauer = (s) => s ? Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0') + ' min' : '–';
  return h('div', { class: 'stack' },
    h('div', { class: 'grid3' }, h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Anrufe (7 Tage)'), h('b', {}, d.woche)), h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Anrufe (30 Tage)'), h('b', {}, d.monat)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Ø Dauer'), h('b', {}, dauer(d.dauer_sek)))),
    h('div', { class: 'card' }, h('h2', {}, 'Anrufprotokoll'), h('p', { class: 'small muted' }, 'Anrufe, die dein Telefon-Assistent angenommen hat. Eingehende Anrufe erscheinen zusätzlich unter „Anfragen“. Nummern und Namen werden nach 180 Tagen automatisch entfernt.'),
      tabelle([['Zeit', z => datum(z.beginn) + ' ' + zeit(z.beginn)], ['Richtung', z => z.richtung === 'ein' ? 'eingehend' : 'ausgehend'], ['Anrufer', z => [z.name, z.nummer].filter(Boolean).join(' · ') || '–'], ['Dauer', z => dauer(z.dauer_sek)], ['Ergebnis', z => z.ergebnis || '–'], ['Zusammenfassung', z => z.zusammenfassung || '–']], d.anrufe, 'Noch keine Anrufe protokolliert. Sobald dein Telefon-Assistent läuft, erscheinen sie hier.')));
};

V.berichte = async () => {
  const d = await api('/api/kunde/monatsberichte');
  if (!d.length) return h('div', { class: 'card' }, h('h2', {}, 'Monatsberichte'), h('p', { class: 'muted' }, 'Hier erscheint jeden Monat dein Bericht: Anfragen, Termine und was deine Automatisierungen für dich erledigt haben. Der erste kommt am Anfang des nächsten Monats.'));
  return h('div', { class: 'stack' }, d.map(b => {
    const x = b.daten, a = x.anfragen;
    return h('div', { class: 'card' }, h('div', { class: 'row' }, h('h2', { class: 'grow', style: 'margin:0' }, b.titel), h('a', { class: 'btn small', href: '/api/kunde/monatsberichte/' + b.id + '/pdf' }, 'PDF herunterladen')),
      h('div', { class: 'grid3', style: 'margin-top:12px' },
        h('div', { class: 'stat' }, h('b', {}, a.gesamt), h('span', { class: 'muted small' }, 'Anfragen (Vormonat ' + a.vormonat + ')')),
        h('div', { class: 'stat' }, h('b', {}, x.termine.gesamt), h('span', { class: 'muted small' }, 'Termine')),
        h('div', { class: 'stat' }, h('b', {}, x.automatische_ablaeufe), h('span', { class: 'muted small' }, 'Automatische Abläufe'))),
      b.einordnung ? h('div', { style: 'margin-top:14px' }, h('h3', {}, 'Einordnung'), h('p', {}, b.einordnung)) : '',
      b.schritte && b.schritte.length ? h('div', {}, h('h3', {}, 'Unsere nächsten Schritte'), h('ul', {}, b.schritte.map(z => h('li', {}, z)))) : '');
  }));
};

V.automationen = async () => {
  const d = await api('/api/kunde/automationen');
  return h('div', { class: 'card' }, h('h2', {}, 'Automationen'),
    d.map(a => h('div', { class: 'modul' }, h('div', { class: 'grow' }, h('b', {}, a.name), h('div', { class: 'small muted' }, a.beschreibung)), h('span', { class: 'pill ' + (a.aktiv ? 'ok' : '') }, a.aktiv ? 'aktiv' : 'nicht gebucht'), !a.aktiv && inhaber() ? h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('Wir melden uns bei dir mit Details und Preis. Anfrage senden?')) return; try { const r = await api('/api/kunde/modul-anfrage', { method: 'POST', body: { modul_code: a.code } }); location.hash = '#nachrichten/' + r.id; } catch (x) { alert(x.message); } } }, 'Anfragen') : '')),
    h('p', { class: 'muted small' }, 'Mit „Anfragen“ erhält das Markentrix-Team deine Nachricht und meldet sich mit Details und Preis.'));
};
