// Ziel für „Teilen mit Markentrix“ (aus WhatsApp, Galerie, Browser …): zeigt das Geteilte und lässt das Ziel wählen.
import { h, api, melde, toast, zielFuerRolle, groesse } from './common.js';

const wurzel = document.getElementById('app');
const alsDatei = async (antwort) => {
  const blob = await antwort.blob();
  return new File([blob], decodeURIComponent(antwort.headers.get('X-Name') || 'Datei'), { type: blob.type });
};

async function geteiltLesen() {
  const c = await caches.open('mk-teilen');
  let text = '';
  const t = await c.match('/teilen-text'); if (t) { try { text = (await t.json()).text || ''; } catch { /* leer */ } }
  const dateien = [];
  for (const k of await c.keys()) if (new URL(k.url).pathname.startsWith('/teilen-datei/')) { const r = await c.match(k); if (r) dateien.push(await alsDatei(r)); }
  return { text, dateien };
}
const aufraeumen = async () => { try { await caches.delete('mk-teilen'); } catch { /* egal */ } };

function bild(f) {   // als data:-Adresse, weil die Sicherheitsrichtlinie keine blob:-Bilder erlaubt
  const i = h('img', { alt: '', style: 'max-width:96px;max-height:72px;border-radius:8px;margin-right:8px;vertical-align:middle' });
  const r = new FileReader(); r.onload = () => { i.src = String(r.result); }; r.readAsDataURL(f);
  return i;
}

function vorschau(geteilt) {
  return h('div', { class: 'card' }, h('h2', {}, 'Geteilt mit Markentrix'),
    geteilt.text ? h('p', { style: 'white-space:pre-wrap;word-break:break-word' }, geteilt.text) : '',
    geteilt.dateien.length ? h('ul', { class: 'prio' }, geteilt.dateien.map(f => h('li', {},
      f.type.startsWith('image/') ? bild(f) : '📎 ',
      f.name, h('span', { class: 'small muted' }, ' (' + groesse(f.size) + ')')))) : '');
}

async function kundeZiel(geteilt, box) {
  const betreff = h('input', { type: 'text', maxlength: 200, 'aria-label': 'Betreff', value: (geteilt.text.split('\n')[0] || 'Vom Handy geteilt').slice(0, 120) });
  const text = h('textarea', { rows: 4, 'aria-label': 'Nachricht', maxlength: 4000 }, geteilt.text);
  const senden = h('button', { class: 'btn', onclick: async () => {
    if (senden.disabled) return; senden.disabled = true; senden.textContent = 'Wird gesendet …';
    try {
      const r = await api('/api/kunde/tickets', { method: 'POST', body: { betreff: betreff.value.trim() || 'Vom Handy geteilt', art: 'frage', text: text.value.trim() || 'Siehe Anhang.' } });
      let fehl = 0;
      for (const f of geteilt.dateien) { try { const fd = new FormData(); fd.append('datei', f); await api('/api/kunde/tickets/' + r.id + '/dateien', { method: 'POST', body: fd }); } catch { fehl++; } }
      await aufraeumen();
      if (fehl) toast(fehl + ' Datei(en) konnten nicht angehängt werden. Die Nachricht ist angekommen.');
      location.href = '/app#nachrichten/' + r.id;
    } catch (e) { melde(box, e.message); senden.disabled = false; senden.textContent = 'An Markentrix senden'; }
  } }, 'An Markentrix senden');
  return h('div', { class: 'card' }, h('h3', {}, 'Nachricht an das Markentrix-Team'), h('label', {}, 'Betreff'), betreff, h('label', {}, 'Nachricht'), text, h('div', { style: 'margin-top:10px' }, senden));
}

async function auswahlListe(lade, zeile, aktion, box, platzhalter) {
  const suche = h('input', { type: 'search', placeholder: platzhalter, 'aria-label': platzhalter });
  const liste = h('div');
  let alle = [];
  try { alle = await lade(); } catch (e) { melde(box, e.message); }
  const zeigen = () => {
    const q = suche.value.trim().toLowerCase();
    const treffer = alle.filter(x => !q || zeile(x).toLowerCase().includes(q)).slice(0, 25);
    liste.replaceChildren(...(treffer.length ? treffer.map(x => h('button', { type: 'button', class: 'btn sec', style: 'width:100%;justify-content:flex-start;margin:4px 0', onclick: () => aktion(x) }, zeile(x))) : [h('p', { class: 'muted' }, 'Nichts gefunden.')]));
  };
  suche.addEventListener('input', zeigen); zeigen();
  return h('div', {}, suche, liste);
}

async function adminZiel(geteilt, box) {
  const intern = h('input', { type: 'checkbox', id: 'tl-intern', checked: true });
  const speichern = async (k) => {
    try {
      const dateien = geteilt.dateien.slice();
      if (geteilt.text.trim() && !dateien.length) dateien.push(new File([geteilt.text], 'Geteilter Text.txt', { type: 'text/plain' }));
      if (!dateien.length) { melde(box, 'Es ist nichts zum Speichern angekommen.'); return; }
      for (const f of dateien) { const fd = new FormData(); fd.append('datei', f); fd.append('kategorie', 'sonstiges'); fd.append('sichtbar_kunde', intern.checked ? 'false' : 'true'); await api('/api/admin/kunden/' + k.id + '/unterlagen', { method: 'POST', body: fd }); }
      await aufraeumen(); toast(dateien.length + ' Datei(en) bei ' + k.firma + ' gespeichert.', 'ok'); location.href = '/admin#kunde/' + k.id;
    } catch (e) { melde(box, e.message); }
  };
  return h('div', { class: 'card' }, h('h3', {}, 'Bei einem Kunden ablegen'),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit' }, intern, 'Nur intern (für den Kunden nicht sichtbar)'),
    await auswahlListe(() => api('/api/admin/kunden'), k => k.kundennummer + ' · ' + k.firma, speichern, box, 'Kunde suchen …'));
}

async function vertriebZiel(geteilt, box) {
  const speichern = async (l) => {
    if (!geteilt.text.trim()) { melde(box, 'Zu Leads lässt sich nur Text speichern, Dateien nicht.'); return; }
    try { await api('/api/vertrieb/leads/' + l.id + '/aktivitaet', { method: 'POST', body: { art: 'notiz', inhalt: geteilt.text.trim().slice(0, 2000) } }); await aufraeumen(); toast('Notiz bei ' + l.firma + ' gespeichert.', 'ok'); location.href = '/vertrieb#lead/' + l.id; }
    catch (e) { melde(box, e.message); }
  };
  return h('div', { class: 'card' }, h('h3', {}, 'Als Notiz bei einem Lead speichern'), geteilt.dateien.length ? h('p', { class: 'small muted' }, 'Hinweis: Dateien lassen sich bei Leads nicht speichern, nur der Text.') : '',
    await auswahlListe(() => api('/api/vertrieb/leads'), l => l.firma + (l.ort ? ' · ' + l.ort : ''), speichern, box, 'Lead suchen …'));
}

(async () => {
  const box = h('div');
  let me;
  try { me = await api('/api/me'); } catch { wurzel.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;margin:40px auto' }, h('h1', {}, 'Bitte zuerst anmelden'), h('p', {}, 'Melden Sie sich an und wählen Sie dann noch einmal „Teilen“.'), h('a', { class: 'btn', href: '/login' }, 'Zur Anmeldung'))); return; }
  const geteilt = await geteiltLesen();
  const kopf = h('div', { class: 'appleiste' }, h('a', { class: 'btn sec small', href: zielFuerRolle(me.rolle) }, '‹ Zurück zur App'));
  if (!geteilt.text && !geteilt.dateien.length) { wurzel.replaceChildren(h('div', { class: 'main', style: 'max-width:640px;margin:0 auto;padding:16px' }, kopf, h('div', { class: 'card' }, h('h2', {}, 'Nichts angekommen'), h('p', {}, 'Wählen Sie in einer anderen App „Teilen“ und dann „Markentrix“.')))); return; }
  const ziel = me.rolle === 'admin' ? await adminZiel(geteilt, box) : me.rolle === 'vertrieb' ? await vertriebZiel(geteilt, box) : await kundeZiel(geteilt, box);
  wurzel.replaceChildren(h('div', { class: 'main', style: 'max-width:640px;margin:0 auto;padding:16px' }, kopf, h('h1', {}, 'Teilen'), vorschau(geteilt), box, ziel));
})();
