import { h, api, dialog, melde, zeit } from '../common.js';
import { knopf } from './kern.js';
import { terminvorschlagKarte } from './terminvorschlag.js';

/** Mögliche Dubletten zu diesem Lead zeigen; „Hierher zusammenführen“ übernimmt Verlauf, Angebote und Termine des anderen Leads und löscht ihn. */
export async function dublettenDialog(lid, firma) {
  const liste = await api('/api/admin/leads/' + lid + '/dubletten');
  const m = h('div');
  const grund = (z) => [z.gleiche_mail ? 'gleiche E-Mail' : '', z.gleiche_nummer ? 'gleiche Nummer' : '', z.gleiche_firma ? 'gleiche Firma und PLZ' : ''].filter(Boolean).join(', ');
  const inhalt = liste.length ? h('div', { class: 'stack' }, h('p', { class: 'small muted' }, 'Behalten wird „' + firma + '“. Der andere Lead wird eingearbeitet und danach gelöscht. Leere Felder werden ergänzt. Das lässt sich nicht rückgängig machen.'),
    ...liste.map(z => h('div', { class: 'card' }, h('b', {}, z.firma), ' ', h('span', { class: 'pill' }, z.status), h('div', { class: 'small muted' }, [z.ansprechpartner, z.email, z.telefon, z.ort].filter(Boolean).join(' · ')),
      h('div', { class: 'small' }, 'Treffer: ' + grund(z) + ' · angelegt ' + zeit(z.erstellt_am) + ' · ' + z.eintraege + ' Verlaufseinträge'),
      h('p', {}, knopf('Hierher zusammenführen', async () => {
        if (!confirm('„' + z.firma + '“ in „' + firma + '“ zusammenführen und löschen?')) return;
        try { await api('/api/admin/leads/' + lid + '/zusammenfuehren', { method: 'POST', body: { mit: z.id } }); location.reload(); } catch (x) { melde(m, x.message); }
      }, 'small')))))
    : h('p', {}, 'Keine Dubletten gefunden (geprüft wurden E-Mail, Telefonnummer sowie Firma mit PLZ).');
  dialog('Dubletten prüfen', h('div', { class: 'stack' }, inhalt, m));
}

/** Terminvorschläge senden aus einem Dialog (z. B. direkt nach einem Anruf). */
export async function terminDialog(lid, email) {
  dialog('Termine vorschlagen', await terminvorschlagKarte({ lead_id: lid }, email));
}
