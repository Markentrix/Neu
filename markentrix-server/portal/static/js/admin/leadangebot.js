import { h, api, datum, zeit, euro, melde, dialog } from '../common.js';
import { knopf } from './kern.js';

const zuCent = (t) => { const z = parseFloat(String(t).trim().replace(/\./g, '').replace(',', '.')); return Number.isFinite(z) ? Math.round(z * 100) : null; };
const alsEuroText = (c) => (c / 100).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const STATUS = { entwurf: ['Entwurf', ''], gestellt: ['Erstellt', 'warn'], versendet: ['Gesendet', 'warn'], angenommen: ['Angenommen', 'ok'], abgelehnt: ['Abgelehnt', 'bad'] };

/** Positionen eines Katalogpakets (mit aktuellem Preis). */
function paketPositionen(p) {
  const out = [];
  if (p.einrichtung_cent) out.push({ text: 'Einrichtung ' + p.name, menge: 1, einheit: '', cent: p.einrichtung_cent });
  if (p.monatlich_cent) out.push({ text: p.name + ' – monatlich', menge: 1, einheit: 'Monat', cent: p.monatlich_cent });
  if (p.projekt_cent) out.push({ text: p.name + ' – Projektpreis', menge: 1, einheit: '', cent: p.projekt_cent });
  return out;
}

/** Der einfache Weg: Paket wählen, prüfen, senden. Der Lead braucht dafür kein Kundenkonto. */
export async function angebotDialog(lid, danach) {
  const v = await api('/api/admin/leads/' + lid + '/angebot-vorlage'), m = h('div');
  if (!v.firma_ok) { dialog('Angebot senden', h('div', {}, h('p', {}, 'Bitte zuerst Name und Anschrift deiner Firma eintragen, sie stehen im Angebot.'), h('a', { class: 'btn', href: '#einstellungen' }, 'Zu den Firmendaten'))); return; }
  let zeilen = [], beleg = v.entwurf_id;
  const liste = h('div'), summe = h('div', { class: 'small', style: 'text-align:right;margin:6px 0' });
  const feldZeile = (z) => {
    const t = h('input', { value: z.text, maxlength: 500, 'aria-label': 'Leistung', placeholder: 'Leistung', oninput: () => { z.text = t.value; } });
    const mg = h('input', { value: String(z.menge).replace('.', ','), 'aria-label': 'Menge', inputmode: 'decimal', style: 'width:70px', oninput: () => { z.menge = parseFloat(mg.value.replace(',', '.')) || 0; rechnen(); } });
    const pr = h('input', { value: alsEuroText(z.cent || 0), 'aria-label': 'Einzelpreis in Euro', inputmode: 'decimal', style: 'width:110px', oninput: () => { z.cent = zuCent(pr.value) ?? 0; rechnen(); } });
    return h('div', { class: 'row', style: 'gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0' }, h('div', { class: 'grow', style: 'min-width:180px' }, t), mg, h('span', { class: 'small muted' }, z.einheit || ''), pr, h('span', { class: 'small muted' }, '€'),
      h('button', { class: 'btn sec small', type: 'button', 'aria-label': 'Position entfernen', onclick: () => { zeilen = zeilen.filter(x => x !== z); zeichnen(); } }, '✕'));
  };
  const rechnen = () => {
    const netto = zeilen.reduce((a, z) => a + Math.round((z.menge || 0) * (z.cent || 0)), 0), ust = v.kleinunternehmer ? 0 : Math.round(netto * v.mwst_satz / 100);
    summe.textContent = 'Netto ' + euro(netto) + (v.kleinunternehmer ? ' (ohne USt nach § 19 UStG)' : ' + ' + String(v.mwst_satz).replace('.', ',') + ' % USt = ' + euro(netto + ust));
  };
  const zeichnen = () => { liste.replaceChildren(...(zeilen.length ? zeilen.map(feldZeile) : [h('p', { class: 'muted small' }, 'Wähle ein Paket oder füge eine eigene Position hinzu.')])); rechnen(); };
  const paketWahl = h('select', { 'aria-label': 'Paket hinzufügen', onchange: () => {
    const p = v.pakete.find(x => x.code === paketWahl.value); paketWahl.value = '';
    if (!p) return;
    const neu = paketPositionen(p);
    if (!neu.length) { melde(m, 'Für dieses Paket ist noch kein Preis hinterlegt (Preise & Konditionen). Du kannst eine eigene Position eintragen.'); return; }
    melde(m, p.ab_preis ? 'Hinweis: Der Katalogpreis von ' + p.name + ' ist ein „ab“-Preis. Bitte den Betrag prüfen.' : '', 'info');
    zeilen.push(...neu); zeichnen();
  } }, h('option', { value: '' }, '+ Paket aus dem Katalog hinzufügen …'), v.pakete.map(p => h('option', { value: p.code }, p.name + (p.nur_auf_anfrage ? ' (auf Anfrage)' : ''))));
  const betreff = h('input', { value: 'Ihr Angebot für ' + v.lead.firma, maxlength: 200, 'aria-label': 'Betreff' });
  const einl = h('textarea', { rows: 4, maxlength: 3000, 'aria-label': 'Einleitung' }); einl.value = v.gruss + '\n\nvielen Dank für Ihr Interesse. Hier ist unser Angebot für ' + v.lead.firma + '.';
  const schluss = h('textarea', { rows: 3, maxlength: 3000, 'aria-label': 'Schlusstext' }); schluss.value = 'Bei Fragen melden Sie sich gern. Wir freuen uns auf die Zusammenarbeit.';
  const gueltig = h('select', { 'aria-label': 'Gültig für' }, [[14, '14 Tage'], [30, '30 Tage'], [60, '60 Tage']].map(([w, t]) => h('option', { value: w, selected: w === 30 }, t)));
  const an = h('input', { type: 'email', value: v.lead.email || '', placeholder: 'E-Mail des Empfängers', 'aria-label': 'E-Mail des Empfängers' });
  const ergebnis = h('div');
  const speichern = async () => {
    const pos = zeilen.filter(z => z.text.trim()).map(z => ({ text: z.text.trim(), menge: z.menge || 1, einheit: z.einheit || '', preis_cent: z.cent || 0 }));
    const r = await api('/api/admin/leads/' + lid + '/angebote', { method: 'POST', body: { beleg_id: beleg, betreff: betreff.value, einleitung: einl.value, schluss: schluss.value, positionen: pos } });
    beleg = r.id; return r;
  };
  const vorschau = knopf('PDF-Vorschau', async () => { try { melde(m, ''); await speichern(); window.open('/api/admin/leads/' + lid + '/angebote/' + beleg + '/pdf', '_blank', 'noopener'); } catch (x) { melde(m, x.message); } }, 'sec');
  const senden = async (nurLink) => {
    try {
      melde(m, ''); await speichern();
      const r = await api('/api/admin/leads/' + lid + '/angebote/' + beleg + '/senden', { method: 'POST', body: { gueltig_tage: Number(gueltig.value), an: an.value || null, nur_link: nurLink } });
      ergebnis.replaceChildren(...fertig(r)); liste.hidden = true; form.hidden = true;
    } catch (x) { melde(m, x.message); }
  };
  const fertig = (r) => {
    const kopieren = h('button', { class: 'btn small', onclick: async () => { try { await navigator.clipboard.writeText(r.link); kopieren.textContent = 'Kopiert ✓'; } catch { feldLink.select(); } } }, 'Link kopieren');
    const feldLink = h('input', { value: r.link, readonly: true, 'aria-label': 'Link zum Angebot', onfocus: (e) => e.target.select() });
    const mailto = 'mailto:' + encodeURIComponent(r.an || '') + '?subject=' + encodeURIComponent(r.betreff) + '&body=' + encodeURIComponent('Guten Tag,\n\nhier ist Ihr Angebot zum Ansehen und Annehmen:\n' + r.link + '\n\nViele Grüße');
    return [h('div', { class: 'msg ' + (r.gesendet || !r.an ? 'ok' : 'err') }, r.gesendet ? 'Angebot ' + r.nummer + ' wurde an ' + r.an + ' gesendet.' : (r.grund ? 'Angebot ' + r.nummer + ' ist erstellt, aber die Mail ging nicht raus: ' + r.grund : 'Angebot ' + r.nummer + ' ist erstellt.')),
      h('p', { class: 'small muted' }, 'Der Empfänger kann es über diesen Link ansehen und online annehmen. Du bekommst dann sofort Bescheid.'), feldLink,
      h('div', { class: 'heuteknoepfe' }, kopieren, !r.gesendet ? h('a', { class: 'btn sec small', href: mailto }, 'Im eigenen Mailprogramm öffnen') : '', h('button', { class: 'btn sec small', onclick: () => { d.zu(); if (danach) danach(); } }, 'Fertig'))];
  };
  const form = h('div', {}, h('label', {}, 'Leistungen'), liste, h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' }, h('div', { class: 'grow', style: 'min-width:200px' }, paketWahl),
    h('button', { class: 'btn sec small', type: 'button', onclick: () => { zeilen.push({ text: '', menge: 1, einheit: '', cent: 0 }); zeichnen(); } }, '+ Eigene Position')), summe,
    h('details', { style: 'margin:10px 0' }, h('summary', {}, 'Texte anpassen'), h('label', {}, 'Betreff'), betreff, h('label', {}, 'Einleitung'), einl, h('label', {}, 'Schluss'), schluss),
    h('div', { class: 'row', style: 'gap:10px;flex-wrap:wrap' }, h('div', { class: 'grow', style: 'min-width:220px' }, h('label', {}, 'An (E-Mail)'), an), h('div', {}, h('label', {}, 'Gültig'), gueltig)),
    m, h('div', { class: 'heuteknoepfe' }, vorschau, v.mail_eingerichtet ? h('button', { class: 'btn', onclick: () => senden(false) }, 'Angebot jetzt senden') : h('button', { class: 'btn', onclick: () => senden(true) }, 'Angebot erstellen und Link kopieren'),
      v.mail_eingerichtet ? h('button', { class: 'btn sec small', onclick: () => senden(true) }, 'Nur Link erstellen (ohne Mail)') : ''),
    v.mail_eingerichtet ? '' : h('p', { class: 'small muted' }, 'Der E-Mail-Versand ist noch nicht eingerichtet (Einstellungen → E-Mail). Du bekommst einen Link und kannst ihn selbst per Mail oder WhatsApp schicken.'));
  const d = dialog('Angebot für ' + v.lead.firma, h('div', {}, form, ergebnis), true);
  const vorschlag = v.pakete.find(p => p.code === v.vorschlag_paket);
  if (vorschlag) zeilen.push(...paketPositionen(vorschlag));
  zeichnen();
}

/** Karte im Lead: alle Angebote mit Stand (gesendet, angesehen, angenommen). */
export async function leadAngebotKarte(lid, lead, m) {
  const liste = await api('/api/admin/leads/' + lid + '/angebote');
  const neuLink = (a) => knopf('Neuen Link erzeugen', async () => {
    if (!confirm('Es wird ein neuer Link erzeugt. Der bisherige Link funktioniert dann nicht mehr. Fortfahren?')) return;
    try { const r = await api('/api/admin/leads/' + lid + '/angebote/' + a.id + '/senden', { method: 'POST', body: { nur_link: true } }); dialog('Link zum Angebot ' + r.nummer, h('div', {}, h('input', { value: r.link, readonly: true, onfocus: (e) => e.target.select(), 'aria-label': 'Link' }), h('p', { class: 'small muted' }, 'Diesen Link kannst du dem Empfänger schicken.'))); } catch (x) { melde(m, x.message); }
  }, 'sec');
  const erneut = (a) => knopf('Erneut per Mail senden', async () => {
    if (!confirm('Angebot ' + a.nummer + ' erneut per Mail an ' + (lead.email || 'den Lead') + ' senden? Dabei wird ein neuer Link erzeugt.')) return;
    try { const r = await api('/api/admin/leads/' + lid + '/angebote/' + a.id + '/senden', { method: 'POST', body: {} }); melde(m, r.gesendet ? 'Erneut gesendet.' : 'Nicht gesendet: ' + (r.grund || ''), r.gesendet ? 'ok' : 'err'); if (r.gesendet) setTimeout(() => location.reload(), 900); } catch (x) { melde(m, x.message); }
  }, 'sec');
  const zeile = (a) => {
    const [t, k] = STATUS[a.status] || [a.status, ''];
    const stand = a.angenommen_am ? 'angenommen am ' + datum(a.angenommen_am) + (a.angenommen_von ? ' von ' + a.angenommen_von : '') : a.abgelehnt_am ? 'abgelehnt am ' + datum(a.abgelehnt_am) : a.angesehen_am ? 'angesehen am ' + zeit(a.angesehen_am) : a.versendet_am ? 'gesendet am ' + datum(a.versendet_am) + ', noch nicht angesehen' : '';
    return h('div', { class: 'heutezeile' }, h('div', { class: 'heutekopf' }, h('div', { class: 'grow' }, h('b', {}, a.nummer || 'Entwurf'), ' ', h('span', { class: 'pill ' + k }, t), h('div', { class: 'small muted' }, euro(a.brutto_cent) + (a.faellig_am ? ' · gültig bis ' + datum(a.faellig_am) : '') + (stand ? ' · ' + stand : '')))),
      h('div', { class: 'heuteknoepfe' }, h('a', { class: 'btn sec small', href: '/api/admin/leads/' + lid + '/angebote/' + a.id + '/pdf', target: '_blank', rel: 'noopener' }, 'PDF'),
        a.status === 'entwurf' ? knopf('Bearbeiten und senden', () => angebotDialog(lid, () => location.reload()), 'btn') : '',
        a.status === 'gestellt' || a.status === 'versendet' ? [erneut(a), neuLink(a)] : '',
        (a.status === 'gestellt' || a.status === 'versendet') ? [knopf('Angenommen (telefonisch)', async () => { if (!confirm('Als angenommen markieren?')) return; try { await api('/api/admin/belege/' + a.id + '/angebot-status', { method: 'POST', body: { status: 'angenommen' } }); location.reload(); } catch (x) { melde(m, x.message); } }, 'sec'),
          knopf('Abgelehnt', async () => { try { await api('/api/admin/belege/' + a.id + '/angebot-status', { method: 'POST', body: { status: 'abgelehnt' } }); location.reload(); } catch (x) { melde(m, x.message); } }, 'sec')] : '',
        a.status === 'angenommen' && !lead.kunden_id ? h('span', { class: 'small' }, 'Nächster Schritt: oben „Zum Kunden machen“.') : '',
        a.status === 'entwurf' ? knopf('Entwurf löschen', async () => { if (!confirm('Entwurf löschen?')) return; try { await api('/api/admin/leads/' + lid + '/angebote/' + a.id, { method: 'DELETE' }); location.reload(); } catch (x) { melde(m, x.message); } }, 'bad') : ''));
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Angebote'), liste.length ? liste.map(zeile) : h('p', { class: 'muted' }, 'Noch kein Angebot. Mit „Angebot senden“ oben geht es in wenigen Klicks.'));
}
