// Lead-Funnel (Kampagnenseiten), Empfehlungsprogramm und Datenschutz-Anfragen (DSGVO).
import { h, api, datum, melde, dialog } from '../common.js';
import { V, fehler, fmtEuro, knopf, kopf, pill, tabelle } from './kern.js';

const box = (id, label, an) => h('label', { style: 'display:flex;align-items:center;gap:8px' }, h('input', { type: 'checkbox', id, checked: !!an, style: 'width:auto' }), label);
const val = (id) => /** @type {HTMLInputElement} */ (document.getElementById(id));
const centAusEuro = (t) => t === '' ? 0 : Math.round(Number(String(t).replace(',', '.')) * 100);

function kampagneDialog(k, danach) {
  const m = h('div', { role: 'status' }), neu = !k;
  k = k || { slug: '', name: '', titel: '', untertitel: '', nutzen: [], button: 'Kostenlos anfragen', einwilligung_text: '', danke_titel: 'Vielen Dank!', danke_text: 'Wir melden uns in Kürze bei Ihnen.', telefon_pflicht: true, website_abfragen: true, termin_anbieten: true, kosten_cent: 0, rechtlich_geprueft: false, aktiv: false };
  const t = (id, label, wert, extra = {}) => [h('label', { for: id }, label), h('input', { id, value: wert || '', ...extra })];
  const d = dialog(neu ? 'Neue Funnel-Seite' : 'Funnel-Seite bearbeiten', h('div', { class: 'stack' },
    ...(neu ? t('fk_slug', 'Seitenname (wird Teil der Adresse, z. B. werkstatt-2026)', k.slug, { maxlength: 40 }) : [h('p', { class: 'small muted' }, 'Adresse: ' + k.link)]),
    ...t('fk_name', 'Interner Name', k.name), ...t('fk_titel', 'Überschrift auf der Seite', k.titel, { maxlength: 160 }), ...t('fk_unter', 'Unterzeile', k.untertitel, { maxlength: 400 }),
    h('label', { for: 'fk_nutzen' }, 'Vorteile (eine Zeile je Punkt, höchstens 6)'), h('textarea', { id: 'fk_nutzen', rows: 4 }, (k.nutzen || []).join('\n')),
    ...t('fk_button', 'Beschriftung des Knopfs', k.button),
    h('label', { for: 'fk_ew' }, 'Einwilligungstext (neben dem Haken, vom Anwalt prüfen lassen)'), h('textarea', { id: 'fk_ew', rows: 3, maxlength: 800 }, k.einwilligung_text || ''),
    ...t('fk_dt', 'Überschrift nach dem Absenden', k.danke_titel), ...t('fk_dx', 'Text nach dem Absenden', k.danke_text),
    box('fk_tel', 'Telefonnummer ist Pflicht', k.telefon_pflicht), box('fk_web', 'Nach der Website fragen', k.website_abfragen), box('fk_term', 'Nach dem Absenden einen Termin anbieten', k.termin_anbieten),
    ...t('fk_kosten', 'Werbekosten gesamt in € (für „Kosten pro Lead“, freiwillig)', k.kosten_cent ? (k.kosten_cent / 100).toFixed(2).replace('.', ',') : '', { inputmode: 'decimal' }),
    box('fk_geprueft', 'Rechtlich geprüft (Einwilligung, Datenschutz, Impressum)', k.rechtlich_geprueft),
    box('fk_aktiv', 'Seite ist live (nur möglich, wenn rechtlich geprüft)', k.aktiv), m,
    h('button', { class: 'btn', onclick: async (e) => {
      e.target.disabled = true;
      const body = { slug: neu ? val('fk_slug').value.trim() : undefined, name: val('fk_name').value, titel: val('fk_titel').value, untertitel: val('fk_unter').value, nutzen: val('fk_nutzen').value.split('\n').map(x => x.trim()).filter(Boolean),
        button: val('fk_button').value, einwilligung_text: val('fk_ew').value, danke_titel: val('fk_dt').value, danke_text: val('fk_dx').value, telefon_pflicht: val('fk_tel').checked, website_abfragen: val('fk_web').checked,
        termin_anbieten: val('fk_term').checked, kosten_cent: centAusEuro(val('fk_kosten').value), rechtlich_geprueft: val('fk_geprueft').checked, aktiv: val('fk_aktiv').checked };
      try { await api(neu ? '/api/admin/funnel' : '/api/admin/funnel/' + k.id, { method: neu ? 'POST' : 'PUT', body }); d.close(); danach(); } catch (x) { fehler(m, x); e.target.disabled = false; }
    } }, 'Speichern')));
}

V.funnel = async () => {
  const lade = async () => api('/api/admin/funnel'), m = h('div'), wurzel = h('div', { class: 'stack' });
  const zeichne = async () => {
    const [d, em] = await Promise.all([lade(), api('/api/admin/empfehlung/liste')]);
    const e = d.empfehlung, besch = h('textarea', { id: 'em_besch', rows: 3, maxlength: 1000, 'aria-label': 'Text für Kunden' }, e.beschreibung || '');
    wurzel.replaceChildren(kopf('Lead-Funnel', knopf('Neue Seite', () => kampagneDialog(null, zeichne), 'btn')),
      h('div', { class: 'card' }, h('h2', {}, 'So funktioniert es'),
        h('p', { class: 'small muted' }, 'Jede Anzeige führt auf eine eigene Seite mit Formular. Wer sich einträgt, wird als heißer Lead angelegt (mit Einwilligung, Kampagne und UTM-Angaben), das Team bekommt eine Aufgabe „innerhalb einer Stunde anrufen“, der Interessent kann gleich einen Termin wählen. Eine Seite geht erst live, wenn der Rechtstext als geprüft eingetragen ist.')),
      h('div', { class: 'card' }, tabelle([['Seite', z => h('div', {}, h('b', {}, z.name), h('div', { class: 'small muted' }, z.link))], ['Status', z => z.aktiv ? pill('aktiv') : z.rechtlich_geprueft ? h('span', { class: 'pill warn' }, 'aus') : h('span', { class: 'pill bad' }, 'Recht offen')],
        ['Aufrufe', z => z.aufrufe], ['Leads', z => z.leads], ['Termine', z => z.termine], ['Kunden', z => z.kunden], ['Kosten/Lead', z => z.kosten_pro_lead_cent ? fmtEuro(z.kosten_pro_lead_cent) : '–'], ['Kosten/Kunde', z => z.kosten_pro_kunde_cent ? fmtEuro(z.kosten_pro_kunde_cent) : '–'],
        ['', z => h('div', { class: 'row' }, knopf('Bearbeiten', () => kampagneDialog(z, zeichne)), knopf('Link kopieren', async (ev) => { try { await navigator.clipboard.writeText(z.link); ev.target.textContent = 'Kopiert ✓'; } catch (x) { prompt('Link:', z.link); } }),
          z.feste ? '' : knopf('Löschen', async () => { if (confirm('Seite „' + z.name + '“ löschen? Die Leads bleiben erhalten.')) { try { await api('/api/admin/funnel/' + z.id, { method: 'DELETE' }); zeichne(); } catch (x) { fehler(m, x); } } }, 'bad'))]], d.kampagnen.filter(z => !z.feste), 'Noch keine Seite angelegt.')),
      h('div', { class: 'card' }, h('h2', {}, 'Empfehlungsprogramm'),
        h('p', { class: 'small muted' }, 'Kunden bekommen im Portal einen persönlichen Link. Wer darüber eine Anfrage stellt, wird als Empfehlung angelegt. Beträge und Auszahlung legst du je Empfehlung selbst fest, es gibt keine Standardprämie. Zum Einschalten die feste Seite „Empfehlung durch Kunden“ unten prüfen lassen und aktivieren.'),
        tabelle([['Seite', z => z.name], ['Status', z => z.aktiv ? pill('aktiv') : h('span', { class: 'pill warn' }, 'aus')], ['Aufrufe', z => z.aufrufe], ['Leads', z => z.leads], ['Kunden', z => z.kunden], ['', z => knopf('Bearbeiten', () => kampagneDialog(z, zeichne))]], d.kampagnen.filter(z => z.feste)),
        box('em_aktiv', 'Empfehlungsprogramm für Kunden eingeschaltet', e.aktiv),
        h('label', { for: 'em_besch' }, 'Was Kunden als Dankeschön erhalten (Text im Kundenportal, z. B. Prämie oder Gutschrift; nur eintragen, wenn du es zugesagt hast)'), besch,
        h('p', {}, knopf('Speichern', async () => { try { await api('/api/admin/empfehlung', { method: 'PUT', body: { aktiv: val('em_aktiv').checked, beschreibung: val('em_besch').value } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } }, 'btn')),
        m, h('h3', {}, 'Eingegangene Empfehlungen'),
        tabelle([['Datum', z => datum(z.erstellt_am)], ['Empfohlen', z => z.lead_firma], ['Von Kunde', z => h('a', { href: '#kunde/' + z.geber_id }, z.geber)], ['Stand', z => z.kunden_id ? pill('aktiv') : z.status],
          ['Prämie', z => z.praemie_status ? z.praemie_status + (z.betrag_cent !== null ? ' · ' + fmtEuro(z.betrag_cent) : '') : '–'],
          ['', z => knopf('Prämie', () => {
            const st = h('select', { 'aria-label': 'Status' }, ...['offen', 'ausgezahlt', 'verworfen'].map(s => h('option', { value: s, selected: s === z.praemie_status }, s)));
            const bt = h('input', { inputmode: 'decimal', placeholder: 'Betrag in €', value: z.betrag_cent !== null && z.betrag_cent !== undefined ? (z.betrag_cent / 100).toFixed(2).replace('.', ',') : '' }), nt = h('input', { placeholder: 'Notiz', value: z.notiz || '' }), dm = h('div');
            const dd = dialog('Prämie für ' + z.geber, h('div', { class: 'stack' }, h('p', { class: 'small muted' }, 'Empfohlen: ' + z.lead_firma), st, bt, nt, dm, h('button', { class: 'btn', onclick: async () => {
              try { await api('/api/admin/empfehlung/' + z.lead_id, { method: 'PUT', body: { status: st.value, betrag_cent: bt.value ? centAusEuro(bt.value) : null, notiz: nt.value || null } }); dd.close(); zeichne(); } catch (x) { fehler(dm, x); } } }, 'Speichern')));
          })]], em.eintraege, 'Noch keine Empfehlungen.')));
  };
  await zeichne();
  return wurzel;
};

const ART = { auskunft: 'Auskunft', loeschung: 'Löschung', berichtigung: 'Berichtigung', widerspruch: 'Widerspruch', einschraenkung: 'Einschränkung', uebertragung: 'Übertragung', sonstiges: 'Sonstiges' };

function dsgvoDialog(a, danach) {
  const m = h('div', { role: 'status' }), treffer = h('div', { class: 'stack' });
  const st = h('select', { 'aria-label': 'Status' }, ...[['neu', 'neu'], ['in_arbeit', 'in Arbeit'], ['erledigt', 'erledigt'], ['abgelehnt', 'abgelehnt']].map(([v, l]) => h('option', { value: v, selected: v === a.status }, l)));
  const idc = h('input', { type: 'checkbox', checked: a.identitaet_geprueft, style: 'width:auto' }), nt = h('textarea', { rows: 3, maxlength: 3000, 'aria-label': 'Notiz' }, a.notiz || '');
  const suchen = async () => {
    try {
      const t = await api('/api/admin/datenschutz-anfragen/' + a.id + '/suche');
      const wahl = new Set(t.leads.map(l => l.id)), sperr = h('input', { type: 'checkbox', checked: true, style: 'width:auto' });
      treffer.replaceChildren(h('h3', {}, 'Gefundene Daten'),
        t.leads.length ? h('div', {}, h('p', { class: 'small' }, t.leads.length + ' Lead(s):'), ...t.leads.map(l => h('label', { style: 'display:flex;gap:8px;align-items:center' }, h('input', { type: 'checkbox', checked: true, style: 'width:auto', onchange: (e) => e.target.checked ? wahl.add(l.id) : wahl.delete(l.id) }), `${l.firma} (${l.email || l.telefon || '–'}, ${l.status}, seit ${datum(l.erstellt_am)})`))) : h('p', { class: 'small muted' }, 'Keine Leads gefunden.'),
        t.kunden.length ? h('p', { class: 'small' }, 'Kundenkonten: ' + t.kunden.map(k => k.kundennummer + ' ' + k.firma).join(', ') + '. Auskunft/Löschung dafür in der Kundenakte (Export, Offboarding).') : '',
        t.benutzer.length ? h('p', { class: 'small' }, 'Portal-Zugänge: ' + t.benutzer.map(b => b.name + ' (' + b.rolle + ')').join(', ')) : '',
        t.partner.length ? h('p', { class: 'small' }, 'Vertriebler: ' + t.partner.map(b => b.name).join(', ')) : '',
        t.sperrliste.length ? h('p', { class: 'small' }, 'Auf der Sperrliste: ' + t.sperrliste.length + ' Eintrag/Einträge.') : '',
        h('div', { class: 'row' }, knopf('Auskunft als Datei', () => window.open('/api/admin/datenschutz-anfragen/' + a.id + '/auskunft', '_blank', 'noopener')),
          t.leads.length ? knopf('Gewählte Leads löschen', async () => {
            if (!idc.checked) { melde(m, 'Bitte zuerst bestätigen, dass die Identität geprüft ist.'); return; }
            if (!confirm(wahl.size + ' Lead(s) endgültig löschen' + (sperr.checked ? ' und die E-Mail-Adresse sperren' : '') + '?')) return;
            try { const r = await api('/api/admin/datenschutz-anfragen/' + a.id + '/loeschen', { method: 'POST', body: { lead_ids: [...wahl], sperren: sperr.checked } });
              melde(m, r.geloescht + ' gelöscht.' + (r.fehler.length ? ' Nicht möglich: ' + r.fehler.join('; ') : ''), r.fehler.length ? 'info' : 'ok'); suchen(); } catch (x) { fehler(m, x); }
          }, 'bad') : ''),
        t.leads.length ? h('label', { class: 'small', style: 'display:flex;gap:8px;align-items:center' }, sperr, ' E-Mail/Telefon nach dem Löschen sperren, damit die Person nicht erneut angesprochen wird (Hinweis zur Zulässigkeit: Anwalts-Checkliste)') : '');
    } catch (x) { fehler(m, x); }
  };
  dialog(ART[a.art] + ': ' + a.name, h('div', { class: 'stack' },
    h('p', { class: 'small' }, (a.email || 'ohne E-Mail') + ' · Eingang ' + datum(a.eingang_am) + ' · Frist ' + datum(a.frist_am)), a.nachricht ? h('p', { class: 'small', style: 'white-space:pre-wrap' }, a.nachricht) : '',
    h('label', { style: 'display:flex;gap:8px;align-items:center' }, idc, ' Identität der Person geprüft (z. B. Rückfrage über die bekannte E-Mail-Adresse)'), st, nt,
    h('div', { class: 'row' }, knopf('Speichern', async () => { try { await api('/api/admin/datenschutz-anfragen/' + a.id, { method: 'PUT', body: { status: st.value, identitaet_geprueft: idc.checked, notiz: nt.value || null } }); danach(); } catch (x) { fehler(m, x); } }, 'btn'), knopf('Daten suchen', suchen)),
    m, treffer));
}

V.dsgvo = async () => {
  const d = await api('/api/admin/datenschutz-anfragen'), m = h('div');
  const neu = h('form', { class: 'row', style: 'flex-wrap:wrap;gap:8px', onsubmit: async (e) => {
    e.preventDefault(); const o = Object.fromEntries(new FormData(e.target)); Object.keys(o).forEach(k => { if (!o[k]) delete o[k]; });
    try { await api('/api/admin/datenschutz-anfragen', { method: 'POST', body: o }); location.reload(); } catch (x) { fehler(m, x); }
  } }, h('select', { name: 'art', 'aria-label': 'Art' }, ...Object.entries(ART).map(([v, l]) => h('option', { value: v }, l))), h('input', { name: 'name', placeholder: 'Name', required: true, 'aria-label': 'Name' }),
    h('input', { name: 'email', placeholder: 'E-Mail', 'aria-label': 'E-Mail' }), h('select', { name: 'quelle', 'aria-label': 'Eingang über' }, ...[['mail', 'per E-Mail'], ['brief', 'per Brief'], ['telefon', 'telefonisch'], ['manuell', 'sonst']].map(([v, l]) => h('option', { value: v }, l))),
    h('button', { class: 'btn' }, 'Anfrage erfassen'));
  return h('div', { class: 'stack' }, kopf('Datenschutz-Anfragen', d.ueberfaellig ? h('span', { class: 'pill bad' }, d.ueberfaellig + ' überfällig') : h('span', { class: 'pill ' + (d.offen ? 'warn' : 'ok') }, d.offen + ' offen')),
    h('div', { class: 'card' }, h('p', { class: 'small muted' }, 'Betroffene haben Anspruch auf Auskunft, Löschung, Berichtigung und mehr (Art. 15 bis 21 DSGVO). Die Frist beträgt einen Monat ab Eingang. Hier erfasst du jede Anfrage (auch per Mail oder Brief), findest die Daten der Person und erzeugst die Auskunft oder löschst Leads. Das Formular für Betroffene: ' + location.origin + '/datenschutz-anfrage. Ob eine Löschung zulässig ist (Aufbewahrungspflichten), klärt der Anwalt.'), neu, m),
    h('div', { class: 'card' }, tabelle([['Eingang', z => datum(z.eingang_am)], ['Art', z => z.art_text], ['Person', z => z.name + (z.email ? ' (' + z.email + ')' : '')], ['Frist', z => h('span', { class: z.ueberfaellig ? 'pill bad' : z.bald ? 'pill warn' : '' }, datum(z.frist_am))],
      ['Stand', z => z.status.replace('_', ' ')], ['', z => knopf('Öffnen', () => dsgvoDialog(z, () => location.reload()))]], d.anfragen, 'Noch keine Anfragen.')));
};
