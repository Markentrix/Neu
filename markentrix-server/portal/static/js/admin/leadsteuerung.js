// Steuerung der Lead-Verteilung, Sperrliste und Assistent „Lead zum Kunden machen“.
import { h, api, datum, melde, dialog } from '../common.js';
import { knopf, tabelle } from './kern.js';

/** Einstellungen für Eingänge und die Sperrliste (Kontakte, die nicht angesprochen werden dürfen). */
export async function steuerungKarte() {
  const [s, sp] = await Promise.all([api('/api/admin/vertrieb/steuerung'), api('/api/admin/vertrieb/sperrliste')]);
  const m = h('div'), liste = h('div');
  const auto = h('input', { type: 'checkbox', checked: !!s.auto_zuweisung, id: 'st_auto' });
  const preise = h('input', { type: 'checkbox', checked: !!s.preise_sichtbar, id: 'st_preise' });
  const std = h('input', { type: 'number', min: 1, max: 168, value: s.reaktionsstunden || 24, style: 'width:90px', 'aria-label': 'Reaktionszeit in Stunden' });
  const speichern = async () => {
    try { await api('/api/admin/vertrieb/steuerung', { method: 'PUT', body: { auto_zuweisung: auto.checked, preise_sichtbar: preise.checked, reaktionsstunden: Number(std.value) } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); }
  };
  const zeigen = (eintraege) => liste.replaceChildren(tabelle([['Seit', z => datum(z.erstellt_am)], ['Art', z => z.art || ''], ['Grund', z => (z.grund || '').replace(/_/g, ' ')], ['Eintrag', z => z.wert || '–'], ['', z => knopf('Entfernen', async () => {
    if (!window.confirm('Eintrag von der Sperrliste nehmen? Der Kontakt darf dann wieder angesprochen werden.')) return;
    try { await api('/api/admin/vertrieb/sperrliste/' + z.id, { method: 'DELETE' }); zeigen(eintraege.filter(x => x.id !== z.id)); } catch (x) { melde(m, x.message); }
  })]], eintraege, 'Die Sperrliste ist leer.'));
  zeigen(sp.eintraege || sp);
  const neu = h('form', { class: 'row', style: 'flex-wrap:wrap;gap:8px', onsubmit: async (e) => {
    e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); Object.keys(o).forEach(k => { if (!o[k]) delete o[k]; });
    try { await api('/api/admin/vertrieb/sperrliste', { method: 'POST', body: { ...o, grund: 'manuell' } }); location.reload(); } catch (x) { melde(m, x.message); }
  } }, h('input', { name: 'email', placeholder: 'E-Mail', 'aria-label': 'E-Mail' }), h('input', { name: 'telefon', placeholder: 'Telefon', 'aria-label': 'Telefon' }), h('input', { name: 'website', placeholder: 'Website', 'aria-label': 'Website' }), h('button', { class: 'btn small' }, 'Sperren'));
  return h('div', { class: 'card' }, h('h2', {}, 'Steuerung und Sperrliste'), m,
    h('label', { class: 'row' }, auto, ' Neue Anfragen automatisch auf aktive Vertriebler verteilen'),
    h('label', { class: 'row' }, preise, ' Vertriebler sehen die Paketpreise'),
    h('div', { class: 'row' }, h('span', {}, 'Heiße Anfragen eskalieren nach'), std, h('span', {}, 'Stunden ohne Kontakt')),
    h('p', {}, h('button', { class: 'btn', onclick: speichern }, 'Speichern')),
    h('h3', {}, 'Sperrliste'), h('p', { class: 'small muted' }, 'Wer hier steht, wird beim Import und beim Anlegen abgewiesen. Eingehende Anfragen werden trotzdem angenommen.'), neu, liste);
}

/** Assistent: Kunde, Paket, Buchung und Einladung aus dem Lead in einem Schritt. */
export async function zuKundeDialog(lid, danach) {
  const v = await api('/api/admin/leads/' + lid + '/zu-kunde-vorschlag'), m = h('p', { role: 'status' });
  const paket = h('select', { 'aria-label': 'Paket' }, h('option', { value: '' }, 'ohne Paket'), (v.pakete || []).map(p => h('option', { value: p.code, selected: p.code === v.vorschlag }, p.name)));
  const beginn = h('input', { type: 'date', value: new Date().toISOString().slice(0, 10), 'aria-label': 'Beginn' });
  const einl = h('input', { type: 'checkbox', checked: !!v.lead.email });
  const d = dialog('Zum Kunden machen', h('div', { class: 'stack' },
    v.angebot && h('p', { class: 'small' }, 'Angenommenes Angebot ' + v.angebot.nummer + ' (' + (v.angebot.brutto_cent / 100).toFixed(2).replace('.', ',') + ' € brutto).'),
    h('label', {}, 'Paket'), paket, h('label', {}, 'Beginn der Buchung'), beginn,
    h('label', { class: 'row' }, einl, ' Einladung zum Kundenportal gleich verschicken' + (v.lead.email ? '' : ' (keine E-Mail hinterlegt)')), m,
    h('button', { class: 'btn', onclick: async (e) => {
      e.target.disabled = true;
      try { const k = await api('/api/admin/leads/' + lid + '/zu-kunde', { method: 'POST', body: { paket_code: paket.value || null, beginn: paket.value ? beginn.value : null, einladen: einl.checked && !!v.lead.email } }); d.zu(); if (danach) danach(k); } catch (x) { e.target.disabled = false; melde(m, x.message); }
    } }, 'Kunde anlegen')));
}
