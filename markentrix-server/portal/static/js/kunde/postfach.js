import { h, api, zeit, groesse, melde, toast } from '../common.js';
import { start, tabelle, zeige, V } from './kern.js';
import { ARTEN, STATUS_TXT } from './anfragen.js';

const tstatus = (s) => h('span', { class: 'pill ' + (s === 'erledigt' ? 'ok' : s === 'wartet_auf_kunde' ? 'warn' : '') }, STATUS_TXT[s] || s);
export const darfSchreiben = () => start.kunden_rolle !== 'nur_lesen';

function dateiLinks(liste) {
  return liste.length ? h('div', { class: 'small', style: 'margin-top:6px' }, liste.map(d => h('a', { class: 'dateilink', href: '/api/kunde/dateien/' + d.id, target: '_blank', rel: 'noopener' }, '📎 ' + d.name + ' (' + groesse(d.groesse) + ')'))) : '';
}

V.nachrichten = async (id) => {
  if (id) return nachrichtDetail(id);
  const liste = await api('/api/kunde/tickets'), m = h('div');
  const betreff = h('input', { name: 'betreff', required: true, maxlength: 200, placeholder: 'Worum geht es?' });
  const art = h('select', { name: 'art' }, ...Object.entries(ARTEN).filter(([v]) => v !== 'modul').map(([v, t]) => h('option', { value: v }, t)));
  const text = h('textarea', { name: 'text', rows: 5, required: true, maxlength: 10000, placeholder: 'Beschreibe dein Anliegen. Je genauer, desto schneller können wir helfen.' });
  try { text.value = localStorage.getItem('mk_entwurf_nachricht') || ''; } catch { /* ohne Speicher weiter */ }
  text.addEventListener('input', () => { try { localStorage.setItem('mk_entwurf_nachricht', text.value); } catch { /* ignorieren */ } });
  const foto = h('input', { type: 'file', accept: 'image/*,.pdf', 'aria-label': 'Foto oder Datei anhängen (freiwillig)' }), senden = h('button', { class: 'btn' }, 'Absenden');
  const form = h('form', { onsubmit: async (e) => { e.preventDefault(); if (senden.disabled) return; senden.disabled = true; senden.textContent = 'Wird gesendet …';
    try {
      const r = await api('/api/kunde/tickets', { method: 'POST', body: { betreff: betreff.value, art: art.value, text: text.value } });
      if (foto.files[0]) { try { const f = new FormData(); f.append('datei', foto.files[0]); await api('/api/kunde/tickets/' + r.id + '/dateien', { method: 'POST', body: f }); } catch (x) { toast('Die Nachricht ist angekommen, der Anhang leider nicht: ' + x.message); } }
      try { localStorage.removeItem('mk_entwurf_nachricht'); } catch { /* ignorieren */ }
      location.hash = '#nachrichten/' + r.id;
    } catch (x) { senden.disabled = false; senden.textContent = 'Absenden'; melde(m, x.message + ' Dein Text bleibt erhalten, du kannst es noch einmal versuchen.'); } } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Betreff'), betreff), h('div', {}, h('label', {}, 'Art'), art)),
    h('label', {}, 'Nachricht'), text, h('label', {}, 'Foto oder Datei (freiwillig)'), foto, h('p', { class: 'small muted' }, 'Wir antworten in der Regel innerhalb von einem Werktag, hier im Portal und per E-Mail.'), h('p', {}, senden));
  return h('div', { class: 'stack' },
    darfSchreiben() ? h('div', { class: 'card' }, h('h2', {}, 'Neue Nachricht an Markentrix'), h('p', { class: 'small muted' }, 'Fragen, Aufträge oder Änderungswünsche, z. B. neue Öffnungszeiten, ein Foto für die Website, ein Problem. Wir antworten hier und per E-Mail.'), m, form) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Deine Nachrichten'),
      tabelle([['Nr.', z => h('a', { href: '#nachrichten/' + z.id }, z.nr)], ['Betreff', z => h('a', { href: '#nachrichten/' + z.id }, (z.kunde_ungelesen ? '● ' : '') + z.betreff)], ['Art', z => ARTEN[z.art] || z.art], ['Status', z => tstatus(z.status)], ['Frist', z => z.status === 'erledigt' ? (z.erledigt_am ? 'erledigt am ' + new Date(z.erledigt_am).toLocaleDateString('de-DE') : '') : (z.frist ? 'bis ' + new Date(z.frist).toLocaleDateString('de-DE') : '')], ['Zuletzt', z => zeit(z.geaendert_am)]], liste, 'Noch keine Nachrichten.')));
};

async function nachrichtDetail(id) {
  const t = await api('/api/kunde/tickets/' + id), m = h('div');
  const bubbles = t.nachrichten.map(n => h('div', { class: 'bub ' + (n.von === 'kunde' ? 'kunde' : 'team') }, h('div', { class: 'small wer' }, (n.von === 'kunde' ? (n.autor_name || 'Du') : (n.autor_name || 'Markentrix-Team')) + ' · ' + zeit(n.erstellt_am)), n.text));
  const text = h('textarea', { rows: 4, maxlength: 10000, placeholder: t.status === 'erledigt' ? 'Noch etwas offen? Schreibe hier, dann öffnen wir die Anfrage wieder.' : 'Deine Antwort …' });
  const datei = h('input', { type: 'file', accept: '.pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx,.pptx,.txt,.csv,.zip' });
  { const hash = location.hash, anzahl = t.nachrichten.length;   // Chat-Gefühl: neue Nachrichten alle 12 s holen, nur wenn nichts getippt wird
    const iv = setInterval(async () => { if (location.hash !== hash) return clearInterval(iv); if (document.hidden) return;
      try { const n = await api('/api/kunde/tickets/' + id); if (n.nachrichten.length !== anzahl && !text.value.trim()) { clearInterval(iv); location.reload(); } } catch (e) { /* nächster Versuch */ } }, 12000); }
  const senden = async () => {
    try {
      if (text.value.trim()) await api('/api/kunde/tickets/' + id + '/nachricht', { method: 'POST', body: { text: text.value } });
      if (datei.files[0]) { const f = new FormData(); f.append('datei', datei.files[0]); await api('/api/kunde/tickets/' + id + '/dateien', { method: 'POST', body: f }); }
      if (!text.value.trim() && !datei.files[0]) { melde(m, 'Bitte schreibe etwas oder wähle eine Datei.'); return; }
      zeige();
    } catch (x) { melde(m, x.message); }
  };
  let bewertung = '';
  if (t.status === 'erledigt') {
    if (t.bewertung) bewertung = h('p', { class: 'small muted' }, 'Deine Bewertung: ' + t.bewertung.punkte + ' von 10. Danke!');
    else if (darfSchreiben()) {
      const mb = h('div'), kom = h('input', { placeholder: 'Kommentar (freiwillig)', maxlength: 1000 }); let wahl = null;
      const kn = Array.from({ length: 11 }, (_, i) => h('button', { class: 'btn sec small', type: 'button', onclick: (e) => { wahl = i; kn.forEach(b => b.classList.remove('gewaehlt')); e.target.classList.add('gewaehlt'); } }, String(i)));
      bewertung = h('div', { class: 'card' }, h('h3', {}, 'Wie zufrieden warst du mit der Bearbeitung?'), mb, h('div', { class: 'row punkte' }, kn),
        h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, kom), h('button', { class: 'btn', onclick: async () => { if (wahl === null) { melde(mb, 'Bitte wähle eine Zahl von 0 bis 10.'); return; }
          try { await api('/api/kunde/tickets/' + id + '/zufriedenheit', { method: 'POST', body: { punkte: wahl, kommentar: kom.value } }); zeige(); } catch (x) { melde(mb, x.message); } } }, 'Bewerten')));
    }
  }
  return h('div', { class: 'stack' },
    h('div', { class: 'card' }, h('div', { class: 'row' }, h('a', { href: '#nachrichten' }, '← Alle Nachrichten'), h('span', { class: 'grow' }), tstatus(t.status)),
      h('h2', { style: 'margin-top:10px' }, t.nr + ' · ' + t.betreff), h('p', { class: 'small muted' }, (ARTEN[t.art] || t.art) + ' · eröffnet am ' + zeit(t.erstellt_am) + (t.status === 'erledigt' && t.erledigt_am ? ' · erledigt am ' + new Date(t.erledigt_am).toLocaleDateString('de-DE') : t.frist ? ' · wir melden uns bis ' + new Date(t.frist).toLocaleDateString('de-DE') : '')),
      h('div', { class: 'chatlog thread' }, bubbles), dateiLinks(t.dateien)),
    bewertung,
    darfSchreiben() ? h('div', { class: 'card' }, h('h3', {}, 'Antworten'), m, text, h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, h('label', { style: 'margin:0 0 4px' }, 'Datei anhängen (max. 8 MB, optional)'), datei), h('button', { class: 'btn', onclick: senden }, 'Senden'))) : '');
}

// ------------------------------------------------------------- Briefing
V.briefing = async () => {
  const d = await api('/api/kunde/briefing'), m = h('div'), eingaben = {};
  const feld = (f) => {
    const wert = d.daten[f.key] || '';
    const el = f.art === 'lang' ? h('textarea', { rows: 3, maxlength: 3000 }, wert)
      : f.art.startsWith('wahl:') ? h('select', {}, h('option', { value: '' }, '– bitte wählen –'), f.art.slice(5).split('|').map(o => h('option', { value: o, selected: o === wert }, o)))
      : h('input', { maxlength: 3000, value: wert });
    if (f.art === 'lang') el.value = wert;
    eingaben[f.key] = el;
    return h('div', {}, h('label', {}, f.frage + (f.pflicht ? ' *' : '')), el);
  };
  const sammeln = () => Object.fromEntries(Object.entries(eingaben).map(([k, el]) => [k, el.value]));
  const los = async (abschicken) => {
    try { await api('/api/kunde/briefing', { method: 'PUT', body: { daten: sammeln(), abschicken } }); if (abschicken) { toast('Danke! Dein Briefing ist beim Markentrix-Team angekommen.', 'ok'); location.hash = '#uebersicht'; setTimeout(() => location.reload(), 1500); } else melde(m, 'Gespeichert. Du kannst jederzeit weitermachen.', 'ok'); } catch (x) { melde(m, x.message); }
  };
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Briefing'),
    h('p', { class: 'small muted' }, 'Mit diesen Angaben bauen wir deine Website, Texte und Auswertungen. Du kannst zwischenspeichern und später weitermachen. Pflichtfelder sind mit * markiert. Logo und Bilder lädst du unter „Dokumente“ hoch.'),
    d.status === 'abgeschickt' ? h('div', { class: 'msg ok' }, 'Abgeschickt am ' + zeit(d.abgeschickt_am) + '. Du kannst unten jederzeit Änderungen vornehmen und erneut abschicken.') : '', m),
    d.struktur.map(a => h('div', { class: 'card' }, h('h3', {}, a.abschnitt), h('div', { class: 'stack' }, a.felder.map(feld)))),
    darfSchreiben() ? h('div', { class: 'row' }, h('button', { class: 'btn sec', onclick: () => los(false) }, 'Zwischenspeichern'), h('button', { class: 'btn', onclick: () => los(true) }, d.status === 'abgeschickt' ? 'Änderungen abschicken' : 'Abschicken')) : h('p', { class: 'muted small' }, 'Mit deinem Zugang kannst du nur ansehen.'));
};

// ------------------------------------------------------------- Auswertung
