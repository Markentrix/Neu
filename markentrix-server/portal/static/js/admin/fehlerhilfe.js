import { h, api, melde, zeit } from '../common.js';
import { knopf } from './kern.js';

/** Text mit `Befehl` in Backticks: Befehle als Code darstellen (zum Abschreiben/Kopieren). */
const schritt = (t) => h('li', {}, String(t).split('`').map((teil, i) => (i % 2 ? h('code', {}, teil) : teil)));

export function erklaerungBox(e) {
  const wer = { admin: 'Das kannst du im Admin selbst erledigen.', server: 'Das wird auf dem Server erledigt (SSH).', kunde: 'Das muss der Kunde erledigen.' }[e.wer] || '';
  return h('div', { class: 'msg info', style: 'margin:8px 0' },
    h('b', {}, e.titel), h('p', { style: 'margin:4px 0' }, e.ursache),
    h('div', { class: 'small muted' }, 'Das hilft:'), h('ol', { style: 'margin:4px 0 4px 18px' }, e.schritte.map(schritt)),
    wer ? h('div', { class: 'small muted' }, wer) : '');
}

export function fehlerhilfeKarte() {
  const ergebnis = h('div'), erklaerung = h('div'), liste = h('div'), box = h('div');
  const text = h('textarea', { rows: 3, maxlength: 4000, placeholder: 'Fehlermeldung hier einfügen (z. B. aus einer Mail, vom Bildschirm oder aus dem Protokoll) …', 'aria-label': 'Fehlermeldung', style: 'width:100%' });
  const pruefen = knopf('Jetzt alles prüfen', async () => {
    melde(box, 'Prüfe … (das kann bis zu 10 Sekunden dauern)', 'info');
    try {
      const d = await api('/api/admin/fehlerhilfe/pruefen', { method: 'POST', body: {} });
      melde(box, d.ok ? 'Alles in Ordnung.' : 'Es gibt Probleme. Die Vorschläge stehen unten.', d.ok ? 'ok' : 'err');
      ergebnis.replaceChildren(...d.punkte.map(p => h('div', { style: 'margin:6px 0' }, h('span', { class: 'pill ' + (p.ok ? 'ok' : 'bad') }, p.ok ? 'OK' : 'Problem'), ' ', h('b', {}, p.titel), h('span', { class: 'small muted' }, ' – ' + p.detail), p.vorschlag ? erklaerungBox(p.vorschlag) : '')));
    } catch (x) { melde(box, x.message); }
  }, 'pri');
  const erklaeren = knopf('Fehler erklären', async () => {
    if (text.value.trim().length < 3) return melde(box, 'Bitte zuerst die Fehlermeldung einfügen.');
    try { melde(box, ''); erklaerung.replaceChildren(erklaerungBox(await api('/api/admin/fehlerhilfe/erklaeren', { method: 'POST', body: { text: text.value } }))); } catch (x) { melde(box, x.message); }
  });
  api('/api/admin/fehlerhilfe', { leise: true }).then((d) => {
    const offen = d.filter(z => !z.erledigt);
    liste.replaceChildren(h('h3', {}, 'Letzte Fehler' + (offen.length ? ' (' + offen.length + ' offen)' : '')),
      ...(d.length ? d.slice(0, 6).map(z => h('details', { style: 'margin:4px 0' }, h('summary', {}, h('span', { class: 'pill ' + (z.erledigt ? 'ok' : z.stufe === 'kritisch' ? 'bad' : 'warn') }, z.erledigt ? 'erledigt' : z.stufe), ' ', zeit(z.zeit), ' · ', z.titel, z.fehler_nr ? h('span', { class: 'small muted' }, ' (Nr. ' + z.fehler_nr + ')') : ''),
        z.erklaerung ? erklaerungBox(z.erklaerung) : '', z.text ? h('div', { class: 'small muted', style: 'word-break:break-word' }, 'Technischer Text: ' + z.text) : '')) : [h('p', { class: 'small muted' }, 'Keine Fehler protokolliert.')]));
  }).catch(() => liste.replaceChildren());
  return h('div', { class: 'card' }, h('h2', {}, 'Fehler-Hilfe'),
    h('p', { class: 'small muted' }, 'Tritt irgendwo ein Fehler auf, erkennt das Portal die Ursache und schlägt die Lösung vor. Hier kannst du das auch selbst anstoßen.'),
    h('div', { class: 'row', style: 'gap:8px;margin:6px 0' }, pruefen), box, ergebnis,
    h('h3', {}, 'Eine Fehlermeldung erklären lassen'), text, h('div', { style: 'margin:6px 0' }, erklaeren), erklaerung, liste);
}
