// Gemeinsame Helfer. Es wird nie innerHTML mit Daten benutzt – nur textContent.
export function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'value') e.value = v;
    else if (v === true) e.setAttribute(k, '');
    else e.setAttribute(k, v);
  }
  for (const c of kids.flat()) {
    if (c === null || c === undefined || c === false) continue;
    e.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return e;
}
/** Element per ID (für Eingabefelder; Typ bewusst offen). @param {string} id @returns {any} */
export const el = (id) => document.getElementById(id);
/** Formularfelder als einfaches Objekt. @param {any} f @returns {Record<string, any>} */
export const formular = (f) => Object.fromEntries(new FormData(f));

// ---------------------------------------------------------------- Schlechtes Netz: Warteschlange und Offline-Ansicht
// Einträge zu Leads (Kontakt festhalten, Notiz) gehen bei fehlendem Netz in eine Warteschlange auf dem Gerät und werden nachgesendet.
// Gelesene Seiten (Heute, Leads) werden nur zwischengespeichert, wenn der Admin die Offline-Ansicht erlaubt hat; beim Abmelden wird alles gelöscht.
const OFFLINE_LESEN = /^\/api\/(vertrieb\/(heute|leadsuche|leads\/[\w-]+)|kunde\/heute|admin\/(heute|leads\/[\w-]+))(\?.*)?$/;
const WARTEND = /^\/api\/(vertrieb|admin)\/leads\/[\w-]+\/(kontakt|aktivitaet)$/;
const OC = 'mk-oc:', QK = 'mk-queue';
/** Zahl am App-Symbol (Android/iPhone, nur bei installierter App): was Aufmerksamkeit braucht. */
async function badgeAktualisieren() {
  const nav = /** @type {any} */ (navigator);
  if (!nav.setAppBadge) return;
  try {
    const r = await fetch('/api/me/badge', { headers: { 'X-MK': '1' }, credentials: 'same-origin' });
    if (!r.ok) return;
    const { n } = await r.json();
    if (n > 0) await nav.setAppBadge(n); else await nav.clearAppBadge();
  } catch (e) { /* Zahl am Symbol ist nur ein Zusatz */ }
}
let offlineErlaubt = false, offline = false, sendet = false;
const lsLesen = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const lsSchreiben = (k, v) => { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } };
function cacheLesen(path) { try { return JSON.parse(lsLesen(OC + path) || 'null'); } catch (e) { return null; } }
function cacheSchreiben(path, d) { lsSchreiben(OC + path, JSON.stringify({ t: Date.now(), d })); }
export function offlineLoeschen() { try { Object.keys(localStorage).filter(k => k.startsWith(OC)).forEach(k => localStorage.removeItem(k)); } catch (e) { /* egal */ } }
const queueLesen = () => { try { return JSON.parse(lsLesen(QK) || '[]'); } catch (e) { return []; } };
const queueSchreiben = (q) => { if (q.length) lsSchreiben(QK, JSON.stringify(q)); else { try { localStorage.removeItem(QK); } catch (e) { /* egal */ } } };
export const wartendeEintraege = () => queueLesen().length;
function warteschlangeAnlegen(path, body) { const q = queueLesen(); q.push({ path, body, t: Date.now() }); queueSchreiben(q); offline = true; statusLeiste(); }
/** Schmale Leiste oben: kein Netz und/oder wartende Einträge. */
export function statusLeiste(stand) {
  if (typeof document === 'undefined') return;
  let b = document.getElementById('offlineleiste');
  const n = wartendeEintraege(), aus = offline || (typeof navigator !== 'undefined' && navigator.onLine === false);
  if (!aus && !n) { if (b) b.remove(); return; }
  if (!b) { b = document.createElement('div'); b.id = 'offlineleiste'; b.setAttribute('role', 'status'); document.body.prepend(b); }
  b.textContent = (aus ? 'Kein Netz.' + (stand ? ' Stand von ' + new Date(stand).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr.' : '') : 'Verbunden.') + (n ? ' ' + n + (n === 1 ? ' Eintrag wartet' : ' Einträge warten') + ' auf das Senden.' : '');
}
/** Wartende Einträge der Reihe nach senden. Bei Netzfehler wird später weiter versucht, bei einem Fehler des Servers wird der Eintrag gemeldet und entfernt. */
export async function warteschlangeSenden() {
  if (sendet || !queueLesen().length) return;
  sendet = true; let ok = 0;
  try {
    for (let q = queueLesen(); q.length; q = queueLesen()) {
      const e = q[0]; let r;
      try { r = await fetch(e.path, { method: 'POST', headers: { 'X-MK': '1', 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify(e.body) }); } catch (x) { offline = true; break; }
      if (r.status === 401) break;
      q.shift(); queueSchreiben(q);
      if (r.ok) ok++;
      else { let t = 'Fehler ' + r.status; try { const d = await r.json(); if (typeof d.detail === 'string') t = d.detail; } catch (x) { /* leer */ } toast('Ein gespeicherter Eintrag konnte nicht gesendet werden: ' + t); }
    }
  } finally { sendet = false; if (!queueLesen().length && ok) offline = false; statusLeiste(); }
  if (ok) toast(ok + (ok === 1 ? ' Eintrag wurde nachgesendet.' : ' Einträge wurden nachgesendet.'), 'ok');
}
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => { offline = false; statusLeiste(); warteschlangeSenden(); });
  window.addEventListener('offline', () => { offline = true; statusLeiste(); });
  setInterval(() => { if (queueLesen().length) warteschlangeSenden(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && /^\/(app|vertrieb|admin)/.test(location.pathname)) badgeAktualisieren(); });
  setInterval(() => { if (document.visibilityState === 'visible' && /^\/(app|vertrieb|admin)/.test(location.pathname)) badgeAktualisieren(); }, 300000);
  if (/^\/(app|vertrieb|admin)/.test(location.pathname)) {
    fetch('/api/me', { headers: { 'X-MK': '1' }, credentials: 'same-origin' }).then(r => r.ok ? r.json() : null).then(m => {
      offlineErlaubt = !!(m && m.offline_daten); if (m && !offlineErlaubt) offlineLoeschen();
      statusLeiste(); setTimeout(warteschlangeSenden, 2500); badgeAktualisieren();
    }).catch(() => { statusLeiste(); });
  }
}
let laufend = 0, balkenT = null;
/** Schmaler Balken oben, wenn eine Abfrage länger als 0,3 s dauert (statt leerer Fläche). */
function ladeBalken(an) {
  laufend += an ? 1 : -1; if (laufend < 0) laufend = 0;
  clearTimeout(balkenT);
  if (laufend > 0) balkenT = setTimeout(() => { if (!document.getElementById('ladebalken')) { const b = document.createElement('div'); b.id = 'ladebalken'; b.setAttribute('aria-hidden', 'true'); document.body.append(b); } }, 300);
  else { const b = document.getElementById('ladebalken'); if (b) b.remove(); }
}
export async function api(path, opt = {}) {
  /** @type {any} */
  const o = { method: opt.method || 'GET', headers: { 'X-MK': '1' }, credentials: 'same-origin' };
  if (opt.body instanceof FormData) o.body = opt.body;
  else if (opt.body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(opt.body); }
  let r;
  const lang = o.method === 'GET' && !opt.leise; if (lang) ladeBalken(true);
  try { r = await fetch(path, o); } catch (e) {
    if (o.method === 'GET' && offlineErlaubt && OFFLINE_LESEN.test(path)) { const c = cacheLesen(path); if (c) { offline = true; statusLeiste(c.t); return c.d; } }
    if (o.method === 'POST' && WARTEND.test(path) && opt.body !== undefined && !(opt.body instanceof FormData)) { warteschlangeAnlegen(path, opt.body); return { queued: true }; }
    offline = true; statusLeiste();
    throw new Error('Keine Verbindung zum Server.');
  } finally { if (lang) ladeBalken(false); }
  if (offline) { offline = false; statusLeiste(); warteschlangeSenden(); }
  let d = null;
  try { d = await r.json(); } catch (e) { /* leer */ }
  if (r.ok && o.method === 'GET' && offlineErlaubt && OFFLINE_LESEN.test(path) && d) cacheSchreiben(path, d);
  if (r.status === 401 && !opt.leise && !path.includes('/login')) { location.href = '/'; throw new Error('Bitte neu anmelden.'); }
  if (!r.ok) {
    let t = d && d.detail;
    if (Array.isArray(t)) t = 'Bitte die Eingaben prüfen.';
    throw new Error(t || 'Fehler ' + r.status);
  }
  return d;
}
export const datum = (s) => s ? new Date(s).toLocaleDateString('de-DE') : '';
export const zeit = (s) => s ? new Date(s).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }) : '';
export const euro = (c) => c === null || c === undefined ? '' : (c / 100).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
export const groesse = (b) => b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
export function melde(box, text, art = 'err') {
  box.replaceChildren(text ? h('div', { class: 'msg ' + art }, text) : '');
}
export async function abmelden() {
  try { await api('/api/logout', { method: 'POST' }); } catch (e) { /* egal */ }
  offlineLoeschen(); try { localStorage.removeItem(QK); } catch (e) { /* egal */ }
  try { const nav = /** @type {any} */ (navigator); if (nav.clearAppBadge) nav.clearAppBadge(); } catch (e) { /* egal */ }
  location.href = '/';
}
/** Zielseite je Rolle: dieselbe Zuordnung wie beim Anmelden auf dem Server (routes_auth.py). @param {string} rolle */
export const zielFuerRolle = (rolle) => rolle === 'admin' ? '/admin' : rolle === 'vertrieb' ? '/vertrieb' : '/app';
/** Start einer Portalseite ist fehlgeschlagen: sichtbare Meldung statt einer leeren (im Dunkelmodus schwarzen) Seite. @param {any} wurzel @param {any} e */
export function startFehler(wurzel, e) {
  wurzel.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;width:calc(100% - 24px);margin:24px auto' }, h('h1', {}, 'Das Portal konnte nicht gestartet werden'),
    h('p', {}, (e && e.message) || 'Unbekannter Fehler.'),
    h('div', { class: 'row' }, h('button', { class: 'btn', onclick: () => location.reload() }, 'Neu laden'), h('button', { class: 'btn sec', onclick: abmelden }, 'Abmelden'))));
}
export function sparkline(werte, farbe = '#8B5CF6') {
  const ns = 'http://www.w3.org/2000/svg', w = 280, hh = 46, max = Math.max(1, ...werte);
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${hh}`); svg.setAttribute('class', 'spark'); svg.setAttribute('preserveAspectRatio', 'none');
  const bw = w / werte.length;
  werte.forEach((v, i) => {
    const r = document.createElementNS(ns, 'rect'), bh = Math.max(2, (v / max) * (hh - 4));
    r.setAttribute('x', String(i * bw + 2)); r.setAttribute('y', String(hh - bh)); r.setAttribute('width', String(Math.max(2, bw - 4)));
    r.setAttribute('height', String(bh)); r.setAttribute('rx', '3'); r.setAttribute('fill', farbe); r.setAttribute('opacity', v ? '1' : '.25');
    svg.append(r);
  });
  return svg;
}

// Karte für die Zwei-Faktor-Anmeldung (Authenticator-App). Wird in allen drei Bereichen genutzt.
export function zweiFaktorKarte() {
  const m = h('div'), box = h('div'), card = h('div', { class: 'card' }, h('h2', {}, 'Zwei-Faktor-Anmeldung'),
    h('p', { class: 'small muted' }, 'Zusätzlicher Schutz: Beim Anmelden wird neben dem Passwort ein Code aus einer Authenticator-App (z. B. Google Authenticator, Microsoft Authenticator, 2FAS) abgefragt.'), m, box);
  const laden = async () => {
    let s; try { s = await api('/api/2fa'); } catch (e) { melde(m, e.message); return; }
    if (s.aktiv) {
      const pw = h('input', { type: 'password', autocomplete: 'current-password' }), code = h('input', { inputmode: 'numeric', autocomplete: 'one-time-code', placeholder: '6-stelliger Code' });
      box.replaceChildren(h('p', {}, h('span', { class: 'pill ok' }, 'aktiv'), ' Noch ' + s.notfallcodes_uebrig + ' Notfallcodes übrig.'),
        h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Passwort'), pw), h('div', {}, h('label', {}, 'Code aus der App oder Notfallcode'), code),
          h('div', {}, h('label', {}, ' '), h('button', { class: 'btn sec', onclick: async () => {
            try { await api('/api/2fa/deaktivieren', { method: 'POST', body: { passwort: pw.value, code: code.value } }); melde(m, 'Zwei-Faktor-Anmeldung ausgeschaltet.', 'ok'); laden(); } catch (x) { melde(m, x.message); } } }, 'Ausschalten'))));
    } else {
      box.replaceChildren(h('p', {}, h('span', { class: 'pill' }, 'aus'), ' '), h('button', { class: 'btn', onclick: async () => {
        try {
          const r = await api('/api/2fa/start', { method: 'POST' });
          const code = h('input', { inputmode: 'numeric', autocomplete: 'one-time-code', placeholder: '6-stelliger Code' });
          box.replaceChildren(h('p', {}, '1. Code mit der Authenticator-App scannen:'), h('img', { src: r.qr, alt: 'QR-Code', style: 'width:200px;height:200px;background:#fff;border-radius:12px;padding:6px' }),
            h('p', { class: 'small muted' }, 'Oder Schlüssel von Hand eingeben: ', h('code', {}, r.geheimnis)),
            h('p', {}, '2. Den angezeigten 6-stelligen Code hier eingeben:'), h('div', { class: 'row' }, code, h('button', { class: 'btn', onclick: async () => {
              try { const a = await api('/api/2fa/aktivieren', { method: 'POST', body: { code: code.value } });
                box.replaceChildren(h('div', { class: 'msg ok' }, 'Zwei-Faktor-Anmeldung ist aktiv. Bitte die Notfallcodes jetzt sicher aufbewahren – sie werden nur einmal angezeigt und ersetzen den App-Code, falls das Handy verloren geht.'),
                  h('pre', { style: 'background:rgba(127,127,127,.12);padding:12px;border-radius:10px;user-select:all' }, a.notfallcodes.join('\n')), h('button', { class: 'btn sec', onclick: laden }, 'Fertig'));
              } catch (x) { melde(m, x.message); } } }, 'Bestätigen')));
        } catch (x) { melde(m, x.message); } } }, 'Einrichten'));
    }
  };
  laden();
  return card;
}

// Fußzeile mit Impressum und Datenschutz
export const rechtFuss = () => h('div', { class: 'rechtfuss small muted' }, h('a', { href: '/impressum' }, 'Impressum'), ' · ', h('a', { href: '/datenschutz' }, 'Datenschutz'), ' · ', h('a', { href: '/status', target: '_blank', rel: 'noopener' }, 'Systemstatus'));


// Kontaktergebnis zu einem Lead festhalten (Admin und Vertriebler): Schnellauswahl, Notiz, Wiedervorlage
const WV_SCHNELL = [['Morgen', 1], ['In 3 Tagen', 3], ['Nächste Woche', 7], ['In 2 Wochen', 14], ['Keine', 0]];
const tagIn = (n) => n ? new Date(Date.now() + n * 864e5).toISOString().slice(0, 10) : '';

/** Wiedervorlage-Feld mit Schnellwahl (Morgen, in 3 Tagen, nächste Woche …). Gibt { el, tag } zurück. */
export function wiedervorlageWahl(start = '') {
  const tag = h('input', { type: 'date', style: 'max-width:170px', value: start, 'aria-label': 'Wiedervorlage' });
  const zeit = h('input', { type: 'time', style: 'max-width:120px', 'aria-label': 'Uhrzeit für die Erinnerung (freiwillig)' });
  const chips = h('div', { class: 'row', style: 'gap:6px;flex-wrap:wrap;margin-top:4px' }, WV_SCHNELL.map(([t, n]) => h('button', { type: 'button', class: 'btn sec small', onclick: () => { tag.value = tagIn(n); } }, t)));
  return { tag, zeit, el: h('div', {}, h('label', { style: 'margin:0' }, 'Wiedervorlage'), h('div', { class: 'row', style: 'gap:8px;align-items:center;flex-wrap:wrap' }, tag, zeit, h('span', { class: 'small muted' }, 'Uhrzeit = Push 1 Std. und 5 Min. vorher')), chips) };
}

/**
 * Kontaktergebnis festhalten. Optionen: { nach: (r) => void } wird statt Neuladen aufgerufen,
 * { naechster: () => void } blendet „Speichern & nächster Lead“ ein.
 */
/** Knöpfe unter einem Notizfeld: Diktieren (Spracherkennung des Browsers) und Zusammenfassen (KI). Gibt '' zurück, wenn beides nicht geht. */
export function notizWerkzeug(feld, m) {
  const SR = typeof window !== 'undefined' && (/** @type {any} */ (window).SpeechRecognition || /** @type {any} */ (window).webkitSpeechRecognition);
  let erkenner = null, laeuft = false;
  const mik = SR ? h('button', { type: 'button', class: 'btn sec small', 'aria-pressed': 'false', onclick: () => {
    if (laeuft && erkenner) { erkenner.stop(); return; }
    erkenner = new SR(); erkenner.lang = 'de-DE'; erkenner.continuous = true; erkenner.interimResults = false;
    const vorher = feld.value ? feld.value.replace(/\s+$/, '') + ' ' : '';
    let gesamt = '';
    erkenner.onresult = (e) => { gesamt = Array.from(e.results).map(r => r[0].transcript).join(' '); feld.value = (vorher + gesamt).slice(0, Number(feld.maxLength) > 0 ? Number(feld.maxLength) : 1500); feld.dispatchEvent(new Event('input')); };
    erkenner.onend = () => { laeuft = false; mik.textContent = '🎤 Diktieren'; mik.setAttribute('aria-pressed', 'false'); };
    erkenner.onerror = (e) => { melde(m, e.error === 'not-allowed' ? 'Bitte erlaube dem Browser den Zugriff aufs Mikrofon.' : 'Die Spracherkennung hat nicht geklappt. Du kannst auch die Mikrofon-Taste deiner Handy-Tastatur benutzen.'); };
    try { erkenner.start(); laeuft = true; mik.textContent = '⏹ Fertig'; mik.setAttribute('aria-pressed', 'true'); melde(m, 'Ich höre zu … Sprich jetzt. Nenne keine Gesundheits- oder Zahlungsdaten.', 'info'); } catch { melde(m, 'Das Diktieren konnte nicht starten.'); }
  } }, '🎤 Diktieren') : '';
  const ki = h('button', { type: 'button', class: 'btn sec small', onclick: async () => {
    if (feld.value.trim().length < 20) { melde(m, 'Die Notiz ist für eine Zusammenfassung noch zu kurz.'); return; }
    ki.disabled = true; melde(m, 'Wird zusammengefasst …', 'info');
    try { const r = await api('/api/vertrieb/notiz-zusammenfassen', { method: 'POST', body: { text: feld.value } }); feld.value = r.zusammenfassung.slice(0, Number(feld.maxLength) > 0 ? Number(feld.maxLength) : 1500); melde(m, 'Zusammengefasst. Bitte kurz prüfen. Dieser Text wurde mit KI-Unterstützung vorbereitet.', 'ok'); }
    catch (x) { melde(m, x.message); }
    ki.disabled = false;
  } }, '✨ Zusammenfassen');
  return h('div', { class: 'row', style: 'gap:6px;flex-wrap:wrap;margin:4px 0' }, mik, ki, h('span', { class: 'small muted' }, SR ? 'Diktieren geht über den Browser (Google bzw. Apple).' : 'Zum Diktieren die Mikrofon-Taste der Handy-Tastatur nutzen.'));
}

export function kontaktKarte(optionen, url, wiedervorlage, extra = {}) {
  const m = h('div'), notiz = h('textarea', { rows: 2, placeholder: 'Kurze Notiz (freiwillig) – du kannst sie auch diktieren', maxlength: 1500, 'aria-label': 'Notiz' }), wv = wiedervorlageWahl();
  let wahl = null; const knoepfe = [];
  const speichern = h('button', { class: 'btn', disabled: true }, 'Speichern'), weiter = extra.naechster ? h('button', { class: 'btn sec', disabled: true }, 'Speichern & nächster Lead') : '';
  const grund = h('select', { 'aria-label': 'Grund für die Absage', style: 'display:none;width:auto' }, h('option', { value: '' }, 'Grund wählen …'), Object.entries(extra.verlustgruende || {}).map(([c, t]) => h('option', { value: c }, t)));
  const waehle = (o, b) => { wahl = o; knoepfe.forEach(x => x.classList.remove('gewaehlt')); b.classList.add('gewaehlt'); speichern.disabled = false; if (weiter) weiter.disabled = false;
    wv.tag.value = tagIn(o.wiedervorlage_tage); grund.style.display = o.code === 'kein_interesse' && extra.verlustgruende ? '' : 'none'; };
  optionen.forEach((o, i) => { const b = h('button', { type: 'button', class: 'btn sec small', onclick: () => waehle(o, b) }, extra.kurzwahl && i < 9 ? h('span', { class: 'muted', style: 'margin-right:4px' }, (i + 1) + ' ·') : '', o.text); knoepfe.push(b); });
  const los = async (danach) => { if (!wahl) return;
    if (wv.zeit.value && !wv.tag.value) { melde(m, 'Für die Uhrzeit bitte auch ein Datum wählen.'); return; }
    if (wahl.code === 'kein_interesse' && extra.verlustgruende && !grund.value) { melde(m, 'Bitte den Grund der Absage wählen. Das hilft bei der Auswertung.'); return; }
    try { const r = await api(url, { method: 'POST', body: { ergebnis: wahl.code, notiz: notiz.value || null, wiedervorlage: wv.tag.value || null, wiedervorlage_zeit: wv.zeit.value || null, verlust_grund: grund.value || null } });
      if (r && r.queued) { toast('Kein Netz: Der Eintrag ist gespeichert und wird gesendet, sobald wieder Netz da ist.', 'ok'); notiz.value = ''; return; }
      vibriere(25);
      if (danach) danach(r); else if (extra.nach) extra.nach(r); else location.reload(); } catch (x) { melde(m, x.message); } };
  speichern.onclick = () => los(null);
  if (weiter) /** @type {any} */ (weiter).onclick = () => los(extra.naechster);
  const box = h('div', { class: 'card kontaktkarte' }, h('h2', {}, 'Kontakt festhalten'),
    h('p', { class: 'small muted' }, 'Was ist passiert? Der Verlauf und, wo es passt, der Status werden automatisch gesetzt.'), m,
    h('div', { class: 'row', style: 'flex-wrap:wrap;gap:6px' }, knoepfe),
    h('div', { style: 'margin-top:10px' }, notiz, notizWerkzeug(notiz, m)),
    h('div', { class: 'row', style: 'margin-top:6px;align-items:flex-end;flex-wrap:wrap' }, grund, wv.el, h('div', { class: 'aktionsleiste' }, speichern, weiter)),
    wiedervorlage ? h('p', { class: 'small muted' }, 'Aktuelle Wiedervorlage: ' + datum(wiedervorlage)) : '');
  // Tastenkürzel am Computer: 1 bis 9 wählt das Ergebnis, N speichert und springt zum nächsten Lead, S speichert
  const taste = (/** @type {KeyboardEvent} */ e) => {
    if (!document.body.contains(box)) { document.removeEventListener('keydown', taste); return; }
    const t = /** @type {HTMLElement|null} */ (e.target);
    if (e.ctrlKey || e.metaKey || e.altKey || (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable))) return;
    if (/^[1-9]$/.test(e.key) && knoepfe[Number(e.key) - 1]) { e.preventDefault(); knoepfe[Number(e.key) - 1].click(); }
    else if (e.key.toLowerCase() === 'n' && weiter && wahl) { e.preventDefault(); /** @type {HTMLElement} */ (weiter).click(); }
    else if (e.key.toLowerCase() === 's' && wahl) { e.preventDefault(); speichern.click(); }
  };
  document.addEventListener('keydown', taste);
  return box;
}

/** Knopf „Leitfaden“: öffnet den Gesprächsleitfaden zum Lead als Blatt, ohne die Seite zu verlassen (zum Nachlesen während des Anrufs).
 * @param {string} basis '/api/vertrieb' oder '/api/admin' */
export function leitfadenKnopf(basis, lid, l, allgemein = '') {
  return h('button', { type: 'button', class: 'btn sec small', onclick: () => dialog('Leitfaden: ' + l.firma, h('div', { class: 'stack' },
    skriptKarte(l.skript, l.skript_am, basis + '/leads/' + lid + '/skript'),
    h('p', { class: 'small muted' }, 'Merkhilfe: freundlich einsteigen, zuerst zuhören und fragen, dann einen konkreten Nutzen nennen, am Ende einen kleinen nächsten Schritt vorschlagen (Rückruf oder Termin). Bei „kein Interesse“ höflich verabschieden.'),
    allgemein ? h('p', {}, h('a', { href: allgemein, onclick: () => { document.querySelector('.dlgoverlay')?.remove(); } }, 'Allgemeiner Leitfaden mit Einwand-Antworten')) : '')) }, '📋 Leitfaden');
}

/** Lead-Daten in Kurzform: nur ausgefüllte Felder, Telefon und E-Mail zum Anklicken, lange Notizen eingeklappt. */
export function leadDatenAnsicht(l, zusatz = []) {
  const felder = [['Ansprechpartner', l.ansprechpartner], ['Telefon', l.telefon, 'tel'], ['E-Mail', l.email, 'mail'], ['Website', l.website, 'web'], ['Branche', l.branche], ['Ort', [l.plz, l.ort].filter(Boolean).join(' ')], ...zusatz].filter(f => f[1] !== undefined && f[1] !== null && f[1] !== '' && f[1] !== '–');
  const wert = ([, w, art]) => art === 'tel' ? h('a', { href: 'tel:' + String(w).replace(/[^+\d]/g, ''), 'data-lead': l.id, 'data-firma': l.firma }, w)
    : art === 'mail' ? h('a', { href: 'mailto:' + w }, w)
      : art === 'web' ? h('a', { href: /^https?:/.test(w) ? w : 'https://' + w, target: '_blank', rel: 'noopener' }, String(w).replace(/^https?:\/\//, '').replace(/\/$/, '')) : String(w);
  const lang = l.notiz && l.notiz.length > 140;
  return h('div', {}, felder.length ? h('div', { class: 'form2' }, felder.map(f => h('div', {}, h('div', { class: 'small muted' }, f[0]), h('div', {}, wert(f))))) : h('p', { class: 'muted' }, 'Noch keine Kontaktdaten. Mit „Daten bearbeiten“ ergänzen.'),
    l.notiz ? (lang ? h('details', { class: 'leadnotiz' }, h('summary', { class: 'small muted' }, 'Notiz: ' + l.notiz.slice(0, 90) + ' …'), h('p', { class: 'muted' }, l.notiz)) : h('p', { class: 'muted leadnotiz' }, l.notiz)) : '');
}

/** Reiter für die Lead-Seite: zeigt immer nur einen Bereich. Der gewählte Reiter bleibt je Lead erhalten (auch nach dem Neuladen). */
export function leadReiter(lid, reiter, standard) {
  const KEY = 'mk-leadreiter';
  const lesen = () => { try { const o = JSON.parse(sessionStorage.getItem(KEY) || 'null'); return o && o.lid === lid ? o.k : null; } catch { return null; } };
  let aktiv = lesen(); if (!reiter.some(r => r[0] === aktiv)) aktiv = standard || reiter[0][0];
  const leiste = h('div', { class: 'tabs', role: 'tablist' }), felder = h('div', { class: 'stack' });
  const zeige = (k) => {
    aktiv = k; try { sessionStorage.setItem(KEY, JSON.stringify({ lid, k })); } catch { /* egal */ }
    leiste.replaceChildren(...reiter.map(([key, text]) => h('button', { type: 'button', role: 'tab', 'aria-selected': String(key === k), class: key === k ? 'on' : '', onclick: () => zeige(key) }, text)));
    felder.replaceChildren(...reiter.filter(r => r[0] === k).map(r => r[2]));
  };
  zeige(aktiv);
  return h('div', { class: 'stack' }, leiste, felder);
}
/** Merkt den Reiter vor dem Öffnen eines Leads (z. B. „Angebot“ direkt nach dem Anruf-Dialog). */
export function leadReiterSetzen(lid, k) { try { sessionStorage.setItem('mk-leadreiter', JSON.stringify({ lid, k })); } catch { /* egal */ } }

/** „⋯ Mehr“: selten gebrauchte Knöpfe in einem kleinen Menü. */
export function mehrMenue(...knoepfe) {
  const items = knoepfe.flat().filter(Boolean);
  if (!items.length) return '';
  const d = /** @type {HTMLDetailsElement} */ (h('details', { class: 'mehr' }, h('summary', { class: 'btn sec small' }, '⋯ Mehr'), h('div', { class: 'mehr-liste' }, items)));
  const aus = (/** @type {Event} */ e) => { if (!document.body.contains(d)) { document.removeEventListener('click', aus); return; } if (!d.contains(/** @type {Node} */ (e.target))) d.open = false; };
  document.addEventListener('click', aus);
  return d;
}

// Gesprächsleitfaden (KI) für einen Lead: zeigt den gespeicherten Entwurf, Knopf erzeugt oder erneuert ihn
export function skriptKarte(skript, skriptAm, url) {
  const m = h('div'), box = h('div');
  const zeige = (s) => box.replaceChildren(
    h('h3', {}, 'Einstieg'), h('p', {}, s.einstieg),
    s.fragen.length ? [h('h3', {}, 'Fragen'), h('ul', {}, s.fragen.map(f => h('li', {}, f)))] : '',
    h('h3', {}, 'Was Markentrix für den Betrieb tun kann'), h('p', {}, s.nutzen),
    s.einwaende.length ? [h('h3', {}, 'Wenn der Kunde sagt …'), s.einwaende.map(e => h('p', {}, h('b', {}, '„' + e.einwand + '“'), h('br'), e.antwort))] : '',
    h('h3', {}, 'Abschluss'), h('p', {}, s.abschluss));
  if (skript) zeige(skript);
  const knopf = h('button', { class: 'btn sec small', onclick: async () => { knopf.disabled = true; melde(m, 'Wird erstellt …', 'info');
    try { zeige(await api(url, { method: 'POST' })); melde(m, 'Neuer Entwurf erstellt.', 'ok'); } catch (x) { melde(m, x.message); } knopf.disabled = false; } }, skript ? 'Neu erstellen' : 'Gesprächsleitfaden erstellen');
  return h('div', { class: 'card' }, h('h2', {}, 'Gesprächsleitfaden (KI-Entwurf)'),
    h('p', { class: 'small muted' }, 'Ein Vorschlag aus den Daten dieses Betriebs. Bitte nicht ablesen, nichts versprechen und keine Preise nennen. Wer kein Interesse hat, wird respektiert. Dieser Text wurde mit KI-Unterstützung vorbereitet.' + (skriptAm ? ' Erstellt am ' + datum(skriptAm) + '.' : '')), m, box, h('p', {}, knopf));
}

// ---------------------------------------------------------------- App-Installation und Push-Nachrichten
let installAngebot = null;
export const installBereit = () => !!installAngebot;
export async function installStarten() { if (!installAngebot) return; const e = installAngebot; installAngebot = null; try { await e.prompt(); } catch { /* abgebrochen */ } }
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); installAngebot = e; });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
}
const b64zuBytes = (s) => { const p = '='.repeat((4 - s.length % 4) % 4), r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from(r, c => c.charCodeAt(0)); };

// ---------------------------------------------------------------- Passkey (Fingerabdruck, Face-ID, Geräte-PIN)
const pkBytes = (s) => { const p = '='.repeat((4 - s.length % 4) % 4), r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from(r, c => c.charCodeAt(0)); };
const pkText = (buf) => { let t = ''; for (const b of new Uint8Array(buf)) t += String.fromCharCode(b); return btoa(t).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
export const passkeyGeht = () => typeof window !== 'undefined' && !!window.PublicKeyCredential && !!navigator.credentials;

/** Anmeldung ohne Passwort. Gibt das Ziel (z. B. „/app“) zurück. Wirft einen Error mit verständlichem Text. */
export async function passkeyAnmelden(bleiben = false) {
  const o = await api('/api/passkey/login/start', { method: 'POST', body: {} });
  let c;
  try {
    c = await navigator.credentials.get({ publicKey: { challenge: pkBytes(o.challenge), rpId: o.rpId, timeout: o.timeout, userVerification: 'required', allowCredentials: [] } });
  } catch (e) {
    throw new Error(e && e.name === 'NotAllowedError' ? 'Abgebrochen oder auf diesem Gerät ist kein Passkey vorhanden. Melde dich mit dem Passwort an und richte unter „Konto“ einen Passkey ein.' : 'Die Passkey-Anmeldung hat nicht geklappt.');
  }
  const pc = /** @type {PublicKeyCredential} */ (c), r = /** @type {AuthenticatorAssertionResponse} */ (pc.response);
  const res = await api('/api/passkey/login/fertig', { method: 'POST', body: { id: pkText(pc.rawId), clientDataJSON: pkText(r.clientDataJSON), authenticatorData: pkText(r.authenticatorData), signature: pkText(r.signature) } });
  return res.ziel;
}

/** Passkey auf diesem Gerät einrichten (Konto angemeldet). */
export async function passkeyEinrichten(name) {
  const o = await api('/api/passkey/registrieren/start', { method: 'POST', body: {} });
  let c;
  try {
    c = await navigator.credentials.create({ publicKey: { challenge: pkBytes(o.challenge), rp: o.rp, user: { id: pkBytes(o.user.id), name: o.user.name, displayName: o.user.displayName }, pubKeyCredParams: o.pubKeyCredParams,
      excludeCredentials: o.excludeCredentials.map(x => ({ type: 'public-key', id: pkBytes(x.id) })), timeout: o.timeout, attestation: 'none', authenticatorSelection: o.authenticatorSelection } });
  } catch (e) {
    throw new Error(e && e.name === 'InvalidStateError' ? 'Auf diesem Gerät ist schon ein Passkey eingerichtet.' : e && e.name === 'NotAllowedError' ? 'Abgebrochen. Zum Einrichten bitte das Gerät bestätigen (Fingerabdruck, Gesicht oder PIN).' : 'Das Einrichten hat nicht geklappt. Hat dein Gerät eine Bildschirmsperre?');
  }
  const r = /** @type {AuthenticatorAttestationResponse} */ (/** @type {PublicKeyCredential} */ (c).response);
  await api('/api/passkey/registrieren/fertig', { method: 'POST', body: { clientDataJSON: pkText(r.clientDataJSON), attestationObject: pkText(r.attestationObject), name: name || null } });
}

/** Karte „Anmeldung mit Fingerabdruck / Face-ID“ für die Konto-Seiten. */
export function passkeyKarte() {
  const m = h('div'), box = h('div');
  const laden = async () => {
    let liste = [];
    try { liste = await api('/api/passkey'); } catch (e) { melde(m, e.message); return; }
    box.replaceChildren(
      liste.length ? h('ul', { class: 'prio' }, liste.map(p => h('li', {}, h('div', { class: 'pt' }, h('b', {}, p.name), h('span', { class: 'small muted' }, 'eingerichtet am ' + datum(p.erstellt_am) + (p.zuletzt_am ? ' · zuletzt benutzt ' + datum(p.zuletzt_am) : ''))),
        h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('Diesen Passkey entfernen?')) return; try { await api('/api/passkey/' + p.id, { method: 'DELETE' }); laden(); } catch (x) { melde(m, x.message); } } }, 'Entfernen'))))
        : h('p', { class: 'muted' }, 'Noch kein Passkey eingerichtet.'),
      passkeyGeht() ? h('p', {}, h('button', { class: 'btn', onclick: async () => {
        const name = (prompt('Wie soll das Gerät heißen? (zum Beispiel „Mein Handy“)', /iphone|ipad/i.test(navigator.userAgent) ? 'Mein iPhone' : /android/i.test(navigator.userAgent) ? 'Mein Android-Handy' : 'Dieser Computer') || '').trim();
        if (!name) return;
        try { await passkeyEinrichten(name); melde(m, 'Eingerichtet. Ab jetzt kannst du dich auf der Anmeldeseite mit „Mit Fingerabdruck / Face-ID anmelden“ einloggen.', 'ok'); laden(); } catch (x) { melde(m, x.message); }
      } }, 'Passkey auf diesem Gerät einrichten')) : h('p', { class: 'small muted' }, 'Dieser Browser unterstützt keine Passkeys. Nutze Chrome oder Safari in einer aktuellen Version.'));
  };
  laden();
  return h('div', { class: 'card' }, h('h2', {}, 'Anmeldung mit Fingerabdruck oder Face-ID (Passkey)'),
    h('p', { class: 'small muted' }, 'Kein Passwort mehr eintippen: Du bestätigst die Anmeldung mit Fingerabdruck, Gesicht oder der Gerätesperre. Das ist schneller und sicherer als ein Passwort und zählt als Zwei-Faktor-Anmeldung. Richte es am besten auf jedem Gerät ein, das du benutzt.'), m, box);
}

/** Schaltet Push auf diesem Gerät ein (Erlaubnis, Abo, Speichern). Wirft bei Ablehnung/Fehler einen Error mit verständlichem Text. */
export async function pushEinschalten() {
  if (await Notification.requestPermission() !== 'granted') throw new Error('Die Erlaubnis wurde abgelehnt. Du kannst sie später unter „App & Benachrichtigungen“ im Konto einschalten.');
  const reg = await navigator.serviceWorker.ready, st = await api('/api/push/status');
  const neu = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64zuBytes(st.schluessel) });
  const j = neu.toJSON();
  await api('/api/push/abo', { method: 'POST', body: { endpoint: j.endpoint, p256dh: j.keys.p256dh, auth: j.keys.auth, geraet: navigator.userAgent.slice(0, 150) } });
}

/** In der installierten App (Handy): einmal freundlich fragen, ob Benachrichtigungen aufs Handy kommen sollen. „Später“ fragt nach 7 Tagen wieder, „Nein danke“ nie mehr. */
export async function pushNachfrage() {
  try {
    const standalone = typeof matchMedia !== 'undefined' && matchMedia('(display-mode: standalone)').matches || /** @type {any} */ (navigator).standalone === true;
    if (!standalone || !/android|iphone|ipad/i.test(navigator.userAgent) || !('serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window)) return;
    if (Notification.permission !== 'default' || location.hash === '#willkommen') return;
    let vermerk = '';
    try { vermerk = localStorage.getItem('mk-pushfrage') || ''; } catch { /* ohne Speicher fragen wir höchstens einmal je Sitzung */ }
    if (vermerk === 'nein' || (vermerk.startsWith('spaeter:') && Date.now() - Number(vermerk.slice(8)) < 7 * 864e5)) return;
    const reg = await navigator.serviceWorker.ready;
    if (await reg.pushManager.getSubscription()) return;
    const setze = (v) => { try { localStorage.setItem('mk-pushfrage', v); } catch { /* egal */ } };
    const m = h('div'), inhalt = h('div', {},
      h('p', {}, 'Möchtest du Benachrichtigungen aufs Handy bekommen? Du erfährst sofort, wenn etwas Wichtiges passiert (zum Beispiel eine neue Nachricht, eine Freigabe oder eine Anfrage).'),
      h('p', { class: 'small muted' }, 'In den Meldungen stehen keine Namen oder Inhalte, nur der Anlass. Du kannst das jederzeit im Konto unter „App & Benachrichtigungen“ ändern. Gleich fragt dich dein Handy noch einmal, bitte dort „Zulassen“ tippen.'), m,
      h('div', { class: 'row' },
        h('button', { class: 'btn', onclick: async () => { try { await pushEinschalten(); setze('ja'); d.zu(); } catch (x) { setze('nein'); melde(m, x.message || 'Das hat nicht geklappt.'); } } }, 'Ja, benachrichtigen'),
        h('button', { class: 'btn sec', onclick: () => { setze('spaeter:' + Date.now()); d.zu(); } }, 'Später'),
        h('button', { class: 'btn sec', onclick: () => { setze('nein'); d.zu(); } }, 'Nein danke')));
    const d = dialog('Benachrichtigungen aufs Handy?', inhalt);
  } catch { /* die Nachfrage ist nur ein Angebot, nie ein Fehler */ }
}

export function pushKarte(rolle) {
  const m = h('div'), box = h('div'), install = h('div'), anlass = h('div');
  const ios = /iphone|ipad/i.test(navigator.userAgent), standalone = window.matchMedia && matchMedia('(display-mode: standalone)').matches;
  const geht = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  async function zeigen() {
    if (!geht) { box.replaceChildren(h('p', { class: 'muted small' }, ios && !standalone ? 'Auf dem iPhone geht das erst, wenn du das Portal zum Home-Bildschirm hinzufügst (Teilen → „Zum Home-Bildschirm“) und von dort öffnest.' : 'Dieser Browser unterstützt keine Push-Nachrichten.')); return; }
    const reg = await navigator.serviceWorker.ready, abo = await reg.pushManager.getSubscription();
    if (abo) box.replaceChildren(h('p', {}, h('span', { class: 'pill ok' }, 'an'), ' Benachrichtigungen sind auf diesem Gerät eingeschaltet.'),
      h('div', { class: 'row' }, h('button', { class: 'btn sec small', onclick: async () => { try { await api('/api/push/test', { method: 'POST' }); melde(m, 'Testnachricht gesendet.', 'ok'); } catch (x) { melde(m, x.message); } } }, 'Testnachricht'),
        h('button', { class: 'btn sec small', onclick: async () => { try { await api('/api/push/abmelden', { method: 'POST', body: { endpoint: abo.endpoint } }); await abo.unsubscribe(); zeigen(); } catch (x) { melde(m, x.message); } } }, 'Ausschalten')));
    else box.replaceChildren(h('button', { class: 'btn small', onclick: async () => {
      try {
        if (await Notification.requestPermission() !== 'granted') { melde(m, 'Die Erlaubnis wurde im Browser abgelehnt. Du kannst sie in den Browser-Einstellungen ändern.'); return; }
        const st = await api('/api/push/status');
        const neu = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64zuBytes(st.schluessel) });
        const j = neu.toJSON();
        await api('/api/push/abo', { method: 'POST', body: { endpoint: j.endpoint, p256dh: j.keys.p256dh, auth: j.keys.auth, geraet: navigator.userAgent.slice(0, 150) } });
        melde(m, 'Eingeschaltet.', 'ok'); zeigen();
      } catch (x) { melde(m, x.message || 'Das hat nicht geklappt.'); }
    } }, 'Benachrichtigungen auf diesem Gerät einschalten'));
  }
  zeigen().catch(() => {});
  if (rolle && ANLAESSE[rolle]) ladeAnsicht().then(a => {
    const aus = new Set(a.push_aus || []);
    anlass.replaceChildren(h('h3', {}, 'Wobei soll ich dich benachrichtigen?'), ...ANLAESSE[rolle].map(([tag, name]) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:5px 0' },
      h('input', { type: 'checkbox', checked: !aus.has(tag), style: 'width:auto', onchange: async (e) => {
        e.target.checked ? aus.delete(tag) : aus.add(tag);
        try { await api('/api/me/ansicht', { method: 'PUT', body: { push_aus: [...aus] } }); a.push_aus = [...aus]; melde(m, ''); } catch (x) { e.target.checked = !e.target.checked; melde(m, x.message); }
      } }), name)));
  }).catch(() => {});
  const tagZeile = h('div');
  if (rolle === 'vertrieb' || rolle === 'kunde') ladeAnsicht().then(a => {
    const stand = a.tag_zeit || (rolle === 'vertrieb' ? '08:00' : 'aus');
    const zeiten = ['aus', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '10:00'];
    const sel = h('select', { 'aria-label': 'Uhrzeit für „Dein Tag“', style: 'width:auto' }, zeiten.map(z => h('option', { value: z, selected: z === stand }, z === 'aus' ? 'aus' : z + ' Uhr')));
    sel.onchange = async () => { try { await api('/api/me/ansicht', { method: 'PUT', body: { tag_zeit: sel.value } }); a.tag_zeit = sel.value; melde(m, 'Gespeichert.', 'ok'); } catch (x) { melde(m, x.message); } };
    tagZeile.replaceChildren(h('h3', {}, 'Morgens „Dein Tag“'), h('p', { class: 'small muted' }, rolle === 'vertrieb' ? 'Eine Nachricht pro Werktag mit fälligen Anrufen und Terminen. Ist nichts los, kommt keine.' : 'Eine Nachricht pro Werktag mit neuen Anfragen, Terminen und Freigaben. Ist nichts los, kommt keine.'), h('label', { class: 'row', style: 'gap:8px;align-items:center' }, 'Uhrzeit ', sel));
  }).catch(() => {});
  const ua = navigator.userAgent, android = /android/i.test(ua), fremd = android && /SamsungBrowser|OPR\/|Opera|Vivaldi|Firefox|DuckDuckGo|EdgA|Brave|MiuiBrowser|UCBrowser/i.test(ua);
  if (!standalone) install.replaceChildren(
    installAngebot ? h('p', {}, h('button', { class: 'btn small', onclick: async () => { installAngebot.prompt(); installAngebot = null; install.replaceChildren(); } }, 'Als App installieren')) : '',
    fremd ? h('div', { class: 'msg info' }, 'Bitte öffne das Portal zum Installieren in Google Chrome. Andere Android-Browser legen teils eine App an, die Google Play Protect als „unsicher“ blockiert.') : '',
    h('p', { class: 'small muted' }, ios ? 'iPhone: in Safari auf das Teilen-Symbol tippen, dann „Zum Home-Bildschirm“ und „Hinzufügen“.'
      : android ? 'Android: in Google Chrome das Menü ⋮ öffnen, dann „App installieren“ (oder „Zum Startbildschirm hinzufügen“) wählen. Die App ist immer auf dem neuesten Stand, Updates brauchen nichts zu tun.'
        : 'Am Rechner: in Chrome oder Edge in der Adressleiste auf das Installieren-Symbol klicken.'));
  return h('div', { class: 'card' }, h('h2', {}, 'App & Benachrichtigungen'),
    h('p', { class: 'small muted' }, 'Das Portal lässt sich wie eine App aufs Handy legen. Mit Benachrichtigungen erfährst du sofort, wenn etwas Wichtiges passiert. Sie enthalten keine Namen oder Inhalte, nur den Anlass.'), m, box, anlass, tagZeile, install);
}

const LEER_SVG = '<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><rect x="10" y="14" width="44" height="36" rx="8" fill="none" stroke="currentColor" stroke-width="2" opacity=".35"/><path d="M10 28h14l3 6h10l3-6h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" opacity=".35"/><circle cx="48" cy="16" r="7" fill="#8B5CF6" opacity=".9"/><path d="M45 16l2 2 4-4" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
/** Freundlicher leerer Zustand: kleine Illustration, ein Satz, optional ein nächster Schritt. */
export function leerZustand(text, aktion) {
  const bild = h('span', { 'aria-hidden': 'true' });
  bild.innerHTML = LEER_SVG;   // feste, eigene Grafik ohne Fremdinhalt
  return h('div', { class: 'leer' }, bild, h('p', { class: 'muted', style: 'margin:0' }, text), aktion ? h('p', { style: 'margin:10px 0 0' }, aktion) : '');
}

/** Knopf für das Erscheinungsbild: automatisch → hell → dunkel. */
export function themeKnopf() {
  const T = /** @type {any} */ (window).mkTheme, namen = { auto: 'automatisch', hell: 'hell', dunkel: 'dunkel' }, icon = { auto: '◐', hell: '☀', dunkel: '☾' };
  const k = h('button', { type: 'button', class: 'themeknopf' });
  const zeigen = () => { const w = T ? T.get() : 'auto'; k.textContent = icon[w] || '◐'; k.title = 'Darstellung: ' + namen[w] + ' (klicken zum Wechseln)'; k.setAttribute('aria-label', 'Darstellung wechseln, aktuell ' + namen[w]); };
  k.addEventListener('click', () => { if (!T) return; T.set({ auto: 'hell', hell: 'dunkel', dunkel: 'auto' }[T.get()] || 'auto'); zeigen(); });
  zeigen();
  return k;
}

/** Meldet eine geöffnete Seite für die Nutzungsstatistik (nur Seitenname, keine Inhalte). Fehler bleiben unbemerkt. */
let _letzteSeite = '', _letzteZeit = 0;
export function nutzung(seite) {
  const jetzt = Date.now();
  if (!/^[a-z0-9_-]{1,30}$/.test(seite) || (seite === _letzteSeite && jetzt - _letzteZeit < 5000)) return;
  _letzteSeite = seite; _letzteZeit = jetzt;
  api('/api/me/nutzung', { method: 'POST', body: { seite }, leise: true }).catch(() => {});
}

/** Menü in einklappbaren Gruppen. gruppen: [[Titel, [[id, Text, Zähler], ...], standardOffen]]. Die Gruppe der aktuellen Seite ist immer offen; der Zustand wird je Gerät gemerkt. */
export function navGruppen(gruppen, aktiv, schluessel) {
  const lies = (k) => { try { return localStorage.getItem('mk-nav-' + schluessel + '-' + k); } catch { return null; } };
  return gruppen.filter(g => g[1].length).map(([titel, punkte, standard]) => {
    const enthaelt = punkte.some(p => p[0] === aktiv);
    const gemerkt = lies(titel);
    let offen = enthaelt || (gemerkt === null ? standard !== false : gemerkt === '1');
    const summe = punkte.reduce((n, p) => n + (p[2] || 0), 0);
    const liste = h('div', { class: 'navliste', hidden: !offen }, punkte.map(p => h('a', { class: 'nav' + (p[0] === aktiv ? ' on' : ''), href: '#' + p[0] }, p[1], p[2] ? h('span', { class: 'badge' }, p[2]) : '')));
    const kopf = h('button', { type: 'button', class: 'navkopf', 'aria-expanded': String(offen) }, h('span', {}, titel), h('span', { class: 'navrechts' }, summe && !offen ? h('span', { class: 'badge' }, summe) : '', h('span', { class: 'pfeil', 'aria-hidden': 'true' }, '▾')));
    kopf.addEventListener('click', () => {
      offen = !offen; liste.hidden = !offen; kopf.setAttribute('aria-expanded', String(offen));
      kopf.querySelector('.navrechts .badge')?.remove();
      if (!offen && summe) kopf.querySelector('.navrechts').prepend(h('span', { class: 'badge' }, summe));
      try { localStorage.setItem('mk-nav-' + schluessel + '-' + titel, offen ? '1' : '0'); } catch { /* ohne Speicher geht es trotzdem */ }
    });
    return h('div', { class: 'navgruppe' }, kopf, liste);
  });
}

// ---------------------------------------------------------------- Glocke, Suche, Ansicht
const ANLAESSE = {
  admin: [['buchung', 'Gespräch gebucht'], ['check', 'Website-Check'], ['ticket', 'Kundennachricht'], ['zahlung', 'Zahlung / Lastschrift'], ['fruehwarnung', 'Kunden-Frühwarnung'], ['fehler', 'Fehler im Portal'], ['angebotsanfrage', 'Vertriebler bittet um Angebot'], ['betriebsalarm', 'Betriebsalarm: Server, Sicherung, Mail'], ['wochenrueckblick', 'Montags: Wochenrückblick'], ['angebotsreaktion', 'Angebot angesehen, angenommen oder abgelehnt']],
  vertrieb: [['zugewiesen', 'Neue Leads zugewiesen'], ['buchung', 'Gespräch gebucht'], ['angebotsstatus', 'Status einer Angebotsanfrage'], ['angebotsreaktion', 'Angebot angesehen, angenommen oder abgelehnt'], ['wochenrueckblick', 'Montags: Wochenrückblick']],
  kunde: [['anfrage', 'Neue Anfrage'], ['anruf', 'Neuer Anruf'], ['wochenrueckblick', 'Montags: Wochenrückblick']],
};
let _ansicht = null;
export const ladeAnsicht = () => (_ansicht = _ansicht || api('/api/me/ansicht', { leise: true }).catch(() => ({ ausgeblendet: [], push_aus: [] })));

/** Welche Karten ausgeblendet sind: gespeicherte Auswahl, sonst die Standardauswahl. */
export const ausgeblendetSet = (a, standard = []) => new Set(a && a.gesetzt ? a.ausgeblendet : standard);

export function anpassenKnopf(liste, standard = []) {
  const panel = h('div', { class: 'card', style: 'display:none;margin-bottom:12px' });
  const knopf = h('button', { class: 'btn sec small', onclick: async () => {
    if (panel.style.display === 'block') { panel.style.display = 'none'; return; }
    const a = await ladeAnsicht(), aus = ausgeblendetSet(a, standard);
    panel.replaceChildren(h('h3', {}, 'Welche Karten möchtest du sehen?'),
      ...liste.map(([id, name]) => h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px;margin:6px 0' },
        h('input', { type: 'checkbox', checked: !aus.has(id), style: 'width:auto', onchange: (e) => { e.target.checked ? aus.delete(id) : aus.add(id); } }), name)),
      h('p', {}, h('button', { class: 'btn small', onclick: async () => { await api('/api/me/ansicht', { method: 'PUT', body: { ausgeblendet: [...aus] } }); location.reload(); } }, 'Speichern')));
    panel.style.display = 'block';
  } }, 'Ansicht anpassen');
  return { knopf, panel };
}

export function glocke() {
  const zahl = h('span', { class: 'badge', style: 'display:none' }), liste = h('div', { class: 'glockeliste' });
  const panel = h('div', { class: 'glockepanel', style: 'display:none' });
  const knopf = h('button', { class: 'glocke', title: 'Benachrichtigungen', 'aria-label': 'Benachrichtigungen', onclick: async (e) => { e.stopPropagation(); panel.style.display = panel.style.display === 'none' ? 'block' : 'none'; if (panel.style.display === 'block') await laden(); } }, '🔔', zahl);
  const aktualisieren = (n) => { zahl.textContent = n; zahl.style.display = n ? '' : 'none'; };
  async function laden() {
    try {
      const d = await api('/api/benachrichtigungen', { leise: true }); aktualisieren(d.ungelesen);
      liste.replaceChildren(...(d.liste.length ? d.liste.map(n => h('a', { class: 'glockeeintrag' + (n.gelesen_am ? '' : ' neu'), href: n.url || '#', onclick: async (e) => { e.preventDefault(); try { await api('/api/benachrichtigungen/gelesen', { method: 'POST', body: { ids: [n.id] } }); } catch (x) { /* egal */ } location.href = n.url || '/'; } },
        h('b', {}, n.titel), h('span', { class: 'small muted' }, n.text || ''), h('span', { class: 'small muted' }, zeit(n.erstellt_am)))) : [h('p', { class: 'muted small', style: 'padding:10px' }, 'Noch keine Benachrichtigungen.')]));
    } catch (x) { /* leise */ }
  }
  panel.append(h('div', { class: 'row', style: 'padding:8px 10px;border-bottom:1px solid var(--line)' }, h('b', { class: 'grow' }, 'Benachrichtigungen'),
    h('button', { class: 'btn sec small', onclick: async () => { try { await api('/api/benachrichtigungen/gelesen', { method: 'POST', body: { alle: true } }); await laden(); } catch (x) { /* egal */ } } }, 'Alle gelesen')), liste);
  const wrap = h('div', { class: 'glockewrap' }, knopf, panel);
  const zu = (e) => { if (!wrap.isConnected) document.removeEventListener('click', zu); else if (!panel.contains(e.target)) panel.style.display = 'none'; };
  document.addEventListener('click', zu);
  laden();
  const takt = setInterval(() => { if (!wrap.isConnected) { clearInterval(takt); return; } if (!document.hidden) api('/api/benachrichtigungen', { leise: true }).then(d => aktualisieren(d.ungelesen)).catch(() => {}); }, 60000);
  return wrap;
}

/**
 * Befehlspalette (Strg+K): sucht Datensätze und bietet Aktionen an.
 * @param {{titel: string, text?: string, link?: string, aktion?: () => void, neu?: boolean}[]} befehle
 */
export function sucheKnopf(befehle = []) {
  let overlay = null;
  const oeffnen = (nurNeu = false) => {
    if (overlay || document.querySelector('.suchoverlay')) return;
    const eingabe = h('input', { placeholder: nurNeu ? 'Was möchtest du anlegen?' : 'Suchen oder Aktion eingeben …', autofocus: true, 'aria-label': 'Suche und Aktionen' }), ergebnis = h('div', { class: 'suchtreffer' });
    let timer = null, treffer = [], pos = -1;
    const schliessen = () => { overlay.remove(); overlay = null; };
    const markieren = () => treffer.forEach((a, i) => a.classList.toggle('auswahl', i === pos));
    const eintrag = (t) => {
      const a = h('a', { href: t.link || '#', onclick: (e) => { if (t.aktion) { e.preventDefault(); schliessen(); t.aktion(); } else schliessen(); } }, h('b', {}, t.titel), h('span', { class: 'small muted' }, t.text || ''));
      treffer.push(a); return a;
    };
    const gruppe = (name, liste) => liste.length ? h('div', {}, h('div', { class: 'suchgruppe' }, name), liste.map(eintrag)) : '';
    const passend = (q) => befehle.filter(b => nurNeu ? b.neu : (q.length < 2 ? !b.neu || false : b.titel.toLowerCase().includes(q.toLowerCase())));
    const suchen = async () => {
      const q = eingabe.value.trim();
      treffer = []; pos = -1;
      if (nurNeu || q.length < 2) { ergebnis.replaceChildren(gruppe(nurNeu ? 'Neu anlegen' : 'Aktionen', passend(q)), nurNeu ? '' : gruppe('Zuletzt geöffnet', zuletztGeoeffnet().map(z => ({ titel: z.titel, text: z.link.slice(1).split('/')[0], link: z.link }))), nurNeu ? '' : h('p', { class: 'muted small', style: 'padding:10px' }, 'Tippe mindestens 2 Zeichen, um Kunden, Leads, Rechnungen und mehr zu suchen.')); return; }
      try {
        const d = await api('/api/admin/suche?q=' + encodeURIComponent(q));
        if (eingabe.value.trim() !== q) return;
        treffer = []; pos = -1;
        const kunden = (d.gruppen.find(g => g.art === 'Kunden') || { treffer: [] }).treffer.slice(0, 3);
        const direkt = kunden.flatMap(k => [{ titel: 'Rechnung für ' + k.titel, text: 'neu anlegen', link: '#neubeleg/' + k.link.split('/')[1] + '/rechnung' }, { titel: 'Angebot für ' + k.titel, text: 'neu anlegen', link: '#neubeleg/' + k.link.split('/')[1] + '/angebot' }]);
        ergebnis.replaceChildren(gruppe('Aktionen', passend(q)), ...d.gruppen.map(g => gruppe(g.art, g.treffer.map(t => ({ titel: t.titel, text: t.text, link: t.link })))), gruppe('Schnell anlegen', direkt),
          !d.gruppen.length && !passend(q).length && !direkt.length ? h('p', { class: 'muted small', style: 'padding:10px' }, 'Nichts gefunden.') : '');
      } catch (x) { ergebnis.replaceChildren(h('p', { class: 'muted small', style: 'padding:10px' }, x.message)); }
    };
    eingabe.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(suchen, 200); });
    eingabe.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') schliessen();
      else if (e.key === 'ArrowDown' && treffer.length) { e.preventDefault(); pos = (pos + 1) % treffer.length; markieren(); treffer[pos].scrollIntoView({ block: 'nearest' }); }
      else if (e.key === 'ArrowUp' && treffer.length) { e.preventDefault(); pos = (pos - 1 + treffer.length) % treffer.length; markieren(); treffer[pos].scrollIntoView({ block: 'nearest' }); }
      else if (e.key === 'Enter') { const a = treffer[pos >= 0 ? pos : 0]; if (a) { e.preventDefault(); a.click(); if (a.getAttribute('href') && a.getAttribute('href') !== '#') location.hash = a.getAttribute('href'); } }
    });
    overlay = h('div', { class: 'suchoverlay', onclick: (e) => { if (e.target === overlay) schliessen(); } }, h('div', { class: 'suchbox', role: 'dialog', 'aria-label': 'Suche und Aktionen' }, eingabe, ergebnis));
    document.body.append(overlay); eingabe.focus(); suchen();
  };
  const taste = (e) => { if (!knopf.isConnected) { document.removeEventListener('keydown', taste); document.removeEventListener('mk-palette', ruf); return; } if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); oeffnen(); } };
  const ruf = (e) => { if (knopf.isConnected) oeffnen(Boolean(e.detail && e.detail.nurNeu)); };
  document.addEventListener('keydown', taste);
  document.addEventListener('mk-palette', ruf);
  const knopf = h('button', { class: 'suchknopf', onclick: () => oeffnen(), 'aria-label': 'Suche öffnen' }, '🔍 Suchen', h('kbd', {}, 'Strg K'));
  return knopf;
}

/** „+ Neu“-Knopf: öffnet die Befehlspalette mit den Anlegen-Aktionen. */
export function neuKnopf() {
  return h('button', { class: 'neuknopf', onclick: () => document.dispatchEvent(new CustomEvent('mk-palette', { detail: { nurNeu: true } })) }, '+ Neu');
}

// ---------------------------------------------------------------- Barrierefreiheit: fehlende Beschriftungen automatisch ergänzen
const _lesbar = (s) => String(s || '').replace(/[_-]+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').trim();
function beschriften(wurzel) {
  wurzel.querySelectorAll('input:not([type=hidden]):not([aria-label]):not([aria-labelledby]), select:not([aria-label]):not([aria-labelledby]), textarea:not([aria-label]):not([aria-labelledby])').forEach((f) => {
    if (f.labels && f.labels.length && f.labels[0].textContent.trim()) return;
    let t = f.getAttribute('title') || f.getAttribute('placeholder') || '';
    if (!t) { let v = f.previousElementSibling; while (v && !t) { if (/^(LABEL|H[1-6]|SPAN|B)$/.test(v.tagName) && v.textContent.trim()) t = v.textContent.trim(); v = v.previousElementSibling; } }
    if (!t) { const l = f.closest('label'); if (l) t = l.textContent.trim(); }
    if (!t && f.parentElement) { const l = f.parentElement.querySelector(':scope > label'); if (l) t = l.textContent.trim(); }
    if (!t && f.tagName === 'SELECT' && f.options.length) t = f.options[0].textContent.trim();
    if (!t) t = _lesbar(f.getAttribute('name') || f.getAttribute('id') || f.getAttribute('type') || 'Eingabe');
    f.setAttribute('aria-label', t.slice(0, 80));
  });
  wurzel.querySelectorAll('th:empty').forEach((th) => th.append(Object.assign(document.createElement('span'), { className: 'nur-sr', textContent: 'Aktion' })));
  wurzel.querySelectorAll('.tablewrap:not([tabindex])').forEach((t) => { t.tabIndex = 0; });
}
let _timerBeschriften = null;
new MutationObserver(() => { clearTimeout(_timerBeschriften); _timerBeschriften = setTimeout(() => beschriften(document.body), 50); }).observe(document.documentElement, { childList: true, subtree: true });

/** Veränderung zum Vormonat als kleiner Pfeil. gut = true, wenn „mehr“ besser ist. */
export function delta(jetzt, vorher, gut = true, format = (x) => String(x), zeitraum = 'Vormonat') {
  const d = jetzt - vorher;
  if (d === 0) return h('span', { class: 'delta gleich' }, '→ wie im ' + zeitraum);
  return h('span', { class: 'delta ' + ((d > 0) === gut ? 'auf' : 'ab') }, (d > 0 ? '▲ +' : '▼ −') + format(Math.abs(d)) + ' zum ' + zeitraum);
}


/** Dialogfenster (Esc oder Klick daneben schließt). Gibt { zu } zurück. */
export function dialog(titel, inhalt, breit = false) {
  const zu = () => { ov.remove(); document.removeEventListener('keydown', esc); window.removeEventListener('hashchange', zu); };
  const esc = (/** @type {KeyboardEvent} */ e) => { if (e.key === 'Escape') zu(); };
  const ov = h('div', { class: 'dlgoverlay', onclick: (e) => { if (e.target === ov) zu(); } },
    h('div', { class: 'dlg' + (breit ? ' breit' : ''), role: 'dialog', 'aria-modal': 'true', 'aria-label': titel },
      h('div', { class: 'dlgkopf' }, h('h2', {}, titel), h('button', { class: 'btn sec small', 'aria-label': 'Schließen', onclick: zu }, '✕')), inhalt));
  document.addEventListener('keydown', esc); window.addEventListener('hashchange', zu); document.body.append(ov);
  // Am Handy: Dialog als Blatt von unten, am Kopf nach unten wischen schließt ihn
  const kopf = ov.querySelector('.dlgkopf'), blatt = /** @type {HTMLElement} */ (ov.querySelector('.dlg'));
  let y0 = null;
  if (kopf) {
    kopf.addEventListener('touchstart', (e) => { y0 = e.touches[0].clientY; }, { passive: true });
    kopf.addEventListener('touchmove', (e) => { if (y0 === null) return; const d = e.touches[0].clientY - y0; if (d > 0) blatt.style.transform = 'translateY(' + d + 'px)'; }, { passive: true });
    kopf.addEventListener('touchend', (e) => { if (y0 === null) return; const d = e.changedTouches[0].clientY - y0; y0 = null; if (d > 90) zu(); else blatt.style.transform = ''; });
  }
  return { zu };
}

/** CSV-Datei im Browser erzeugen und herunterladen (Excel-tauglich: Semikolon, UTF-8 mit BOM). */
export function csvLaden(dateiname, kopfzeile, zeilen) {
  const q = (v) => '"' + String(v === null || v === undefined ? '' : v).replace(/"/g, '""') + '"';
  const text = '\ufeff' + [kopfzeile, ...zeilen].map(z => z.map(q).join(';')).join('\r\n');
  const a = h('a', { href: URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })), download: dateiname });
  document.body.append(a); a.click(); a.remove();
}

/** Hinweis mit „Rückgängig“ für ein paar Sekunden. fn macht die Aktion rückgängig und darf einen Fehler werfen. */
export function rueckgaengig(text, fn, sekunden = 10) {
  document.querySelectorAll('.undo').forEach(e => e.remove());
  let t = null;
  const weg = () => { clearTimeout(t); box.remove(); };
  const box = h('div', { class: 'undo', role: 'status' }, h('span', {}, text), h('button', { class: 'btn small', onclick: async (e) => { e.target.disabled = true; try { await fn(); box.firstChild.textContent = 'Rückgängig gemacht.'; e.target.remove(); setTimeout(weg, 2000); } catch (x) { box.firstChild.textContent = 'Rückgängig nicht möglich: ' + x.message; e.target.remove(); setTimeout(weg, 4000); } } }, 'Rückgängig'));
  document.body.append(box); t = setTimeout(weg, sekunden * 1000);
  window.addEventListener('hashchange', weg, { once: true });
}

// Zuletzt geöffnete Seiten (nur in diesem Browser) für die Suche
const ZUL = 'mk_zuletzt';
export const zuletztGeoeffnet = () => { try { return JSON.parse(localStorage.getItem(ZUL) || '[]'); } catch { return []; } };
if (!/** @type {any} */ (window).__mkZuletzt) {
  /** @type {any} */ (window).__mkZuletzt = true;
  window.addEventListener('hashchange', () => {
    const hash = location.hash;
    if (!/^#(kunde|lead|beleg|postfach|partner)\//.test(hash)) return;
    setTimeout(() => {
      if (location.hash !== hash) return;
      const titel = (document.querySelector('.main h1, main h1, h1') || {}).textContent;
      if (!titel) return;
      try { const l = zuletztGeoeffnet().filter(x => x.link !== hash); l.unshift({ link: hash, titel: titel.trim().slice(0, 80) }); localStorage.setItem(ZUL, JSON.stringify(l.slice(0, 8))); } catch { /* ohne Speicher keine Liste */ }
    }, 900);
  });
}

/** Tabellen auf dem Handy als beschriftete Karten: jede Zelle bekommt die Spaltenüberschrift als Label (CSS .stapel, ab 640 px). */
export function stapelTabellen() {
  let geplant = false;
  const lauf = () => {
    geplant = false;
    document.querySelectorAll('table').forEach(t => {
      const k = [...t.querySelectorAll('thead th')].map(x => x.textContent.trim());
      if (!k.length) return;
      if (!t.classList.contains('stapel')) {
        t.classList.add('stapel'); t.setAttribute('role', 'table');
        t.querySelectorAll('thead tr').forEach(r => r.setAttribute('role', 'row'));
        t.querySelectorAll('thead th').forEach(x => x.setAttribute('role', 'columnheader'));
      }
      t.querySelectorAll('tbody tr').forEach(r => {
        if (r.hasAttribute('data-stapel')) return;
        r.setAttribute('data-stapel', '1'); r.setAttribute('role', 'row');
        [...r.children].forEach((c, i) => { c.setAttribute('role', 'cell'); c.setAttribute('data-label', k[i] || ''); });
      });
    });
  };
  const plane = () => { if (!geplant) { geplant = true; requestAnimationFrame(lauf); } };
  new MutationObserver(plane).observe(document.body, { childList: true, subtree: true });
  plane();
}

/**
 * Feste Menüleiste unten am Handy (Admin und Partnerportal): bis zu vier wichtigste Seiten plus „Mehr“ mit dem ganzen Menü.
 * gruppen: [[Titel, [[id, Name, Zähler]], offen]] wie bei navGruppen; feste: Seiten-IDs in Wunschreihenfolge.
 */
export function mobilLeiste({ aktiv, gruppen, feste, icons, kurz = {}, schluessel, extra = [] }) {
  const alle = gruppen.flatMap(g => g[1]), ids = alle.map(p => p[0]);
  const fest = feste.filter(i => ids.includes(i)).slice(0, 4), zahl = (i) => (alle.find(p => p[0] === i) || [])[2] || 0;
  const rest = ids.filter(i => !fest.includes(i)), mehrZahl = rest.reduce((n, i) => n + zahl(i), 0);
  const mehr = () => dialog('Menü', h('div', { class: 'mehrblatt' }, navGruppen(gruppen.map(([titel, p]) => [titel, p, true]), aktiv, schluessel + '-mehr'), extra,
    h('div', { class: 'brandzeile', style: 'margin-top:10px' }, themeKnopf()), h('button', { class: 'btn sec', style: 'width:100%;margin-top:10px', onclick: () => abmelden() }, 'Abmelden')));
  return h('nav', { class: 'tabbar', 'aria-label': 'Hauptmenü' },
    fest.map(id => h('a', { href: '#' + id, class: id === aktiv ? 'on' : '', 'aria-current': id === aktiv ? 'page' : null },
      h('span', { class: 'ic', 'aria-hidden': 'true' }, icons[id] || '•', zahl(id) ? h('span', { class: 'badge' }, zahl(id)) : ''), h('span', {}, kurz[id] || alle.find(p => p[0] === id)[1]))),
    h('button', { type: 'button', class: !fest.includes(aktiv) ? 'on' : '', onclick: mehr }, h('span', { class: 'ic', 'aria-hidden': 'true' }, '☰', mehrZahl ? h('span', { class: 'badge' }, mehrZahl) : ''), h('span', {}, 'Menü')));
}

/** Kurze Meldung unten im Bild (statt alert): verschwindet von selbst, wird vorgelesen. */
/** @param {number|number[]} [muster] */
export function vibriere(muster = 15) {
  try { if (navigator.vibrate && !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)) navigator.vibrate(muster); } catch { /* ohne Vibration */ }
}

export function toast(text, art = 'bad') {
  vibriere(art === 'ok' ? 15 : [30, 50, 30]);
  const t = h('div', { class: 'toast ' + art, role: 'status', 'aria-live': 'polite' }, text);
  document.body.append(t); setTimeout(() => t.remove(), 6000);
}

// ---------------------------------------------------------------- Zurück zur Liste (Filter, Suche, Seite und Scrollstand bleiben erhalten)
const VORHER = 'mk-vorher', SCROLL = 'mk-scroll';
const lesen = (k) => { try { return sessionStorage.getItem(k); } catch (e) { return null; } };
const schreiben = (k, v) => { try { sessionStorage.setItem(k, v); } catch (e) { /* ohne Speicher funktioniert es einfach wie bisher */ } };
let scrollTimer = 0;
window.addEventListener('scroll', () => {
  clearTimeout(scrollTimer);
  scrollTimer = window.setTimeout(() => { try { const s = JSON.parse(lesen(SCROLL) || '{}'); s[location.hash] = Math.round(window.scrollY); schreiben(SCROLL, JSON.stringify(s)); } catch (e) { /* egal */ } }, 150);
}, { passive: true });
window.addEventListener('hashchange', (e) => {
  const alt = (e.oldURL.split('#')[1] || '');
  if (alt) schreiben(VORHER, '#' + alt);
  // Zurück aus einem Datensatz: Scrollstand der Liste wiederherstellen (die Seite baut sich erst nach dem Laden auf)
  if (alt.startsWith('lead/') || alt.startsWith('kunde/')) {
    let y = 0; try { y = JSON.parse(lesen(SCROLL) || '{}')[location.hash] || 0; } catch (x) { /* egal */ }
    if (y > 50) [150, 500, 1100, 2000].forEach(t => setTimeout(() => { if (Math.abs(window.scrollY - y) > 8 && document.documentElement.scrollHeight >= y + window.innerHeight) window.scrollTo(0, y); }, t));
  }
});

/** Ziel für „Zurück zur Liste“: die Liste mit ihren Filtern, wenn man von dort kam, sonst die Standardliste.
 * @param {string} std z. B. 'leads' */
export function listenZiel(std) {
  const v = lesen(VORHER) || '', liste = [].concat(std);
  return liste.some(s => v === '#' + s || v.startsWith('#' + s + '?')) ? v : '#' + liste[0];
}

/** Knopf „← Liste“, der zur zuletzt gesehenen Liste mit denselben Filtern führt. */
export function listenKnopf(std, text = '← Liste') {
  return h('a', { class: 'btn sec small', href: listenZiel(std), onclick: (e) => { e.preventDefault(); location.hash = listenZiel(std); } }, text);
}

// ---------------------------------------------------------------- Handy-Feinschliff
/** Passende Tastatur und Eingabehilfen je Feld (ohne bestehende Angaben zu überschreiben). */
export function eingabeHilfen(wurzel = document) {
  wurzel.querySelectorAll('input').forEach((el) => {
    const i = /** @type {HTMLInputElement} */ (el), n = ((i.name || '') + ' ' + (i.id || '') + ' ' + (i.placeholder || '')).toLowerCase();
    if (i.type === 'tel' || /telefon|handy|phone/.test(n)) { if (!i.inputMode) i.inputMode = 'tel'; if (!i.autocomplete) i.autocomplete = 'tel'; }
    else if (i.type === 'email') { if (!i.inputMode) i.inputMode = 'email'; if (!i.autocapitalize) i.autocapitalize = 'none'; if (!i.autocomplete) i.setAttribute('autocomplete', 'email'); }
    else if (/plz|postleitzahl/.test(n) && !i.inputMode) { i.inputMode = 'numeric'; i.setAttribute('autocomplete', 'postal-code'); }
    else if (i.type === 'number' && !i.inputMode) i.inputMode = 'decimal';
    else if (i.type === 'url' && !i.inputMode) { i.inputMode = 'url'; i.autocapitalize = 'none'; }
  });
}
if (typeof document !== 'undefined') {
  let t = null;
  new MutationObserver(() => { clearTimeout(t); t = setTimeout(() => eingabeHilfen(), 150); }).observe(document.documentElement, { childList: true, subtree: true });
  // Zum Aktualisieren ganz oben nach unten ziehen (nur Touch, nur wenn die Seite ganz oben steht)
  let sy = null, zug = 0;
  const ind = () => { let e = document.getElementById('ziehen'); if (!e) { e = document.createElement('div'); e.id = 'ziehen'; e.textContent = '↓ Loslassen zum Aktualisieren'; document.body.append(e); } return e; };
  document.addEventListener('touchstart', (e) => { sy = (window.scrollY <= 0 && !document.querySelector('.dlgoverlay') && e.touches.length === 1) ? e.touches[0].clientY : null; zug = 0; }, { passive: true });
  document.addEventListener('touchmove', (e) => { if (sy === null) return; zug = e.touches[0].clientY - sy; const i = document.getElementById('ziehen'); if (zug > 20) { const x = ind(); x.style.transform = 'translateY(' + Math.min(zug, 90) / 2 + 'px)'; x.classList.toggle('bereit', zug > 90); } else if (i) i.remove(); }, { passive: true });
  document.addEventListener('touchend', () => { const i = document.getElementById('ziehen'); if (i) i.remove(); if (sy !== null && zug > 90 && !document.querySelector('textarea:focus, input:focus')) location.reload(); sy = null; zug = 0; });
}

// ---------------------------------------------------------------- Nach dem Anruf: App fragt „Wie lief es?“ (Vertrieb und Admin)
/**
 * Merkt sich, welchen Lead man anruft, und fragt nach der Rückkehr in die App nach dem Ergebnis.
 * @param {{ leadApi: string, leadHash: string, angebot?: boolean }} cfg
 */
export function anrufNachfrage(cfg) {
  const ANRUF = 'mk-anruf';
  document.addEventListener('click', (e) => {
    const a = e.target instanceof Element ? e.target.closest('a[href^="tel:"]') : null;
    if (!a) return;
    const lid = a.getAttribute('data-lead') || ((location.hash.match(/^#lead\/([\w-]+)/) || [])[1]);
    if (!lid) return;
    try { localStorage.setItem(ANRUF, JSON.stringify({ lid, firma: a.getAttribute('data-firma') || '', t: Date.now(), basis: cfg.leadApi })); } catch { /* ohne Speicher keine Nachfrage */ }
  });
  async function nachfragen() {
    let o = null;
    try { o = JSON.parse(localStorage.getItem(ANRUF) || 'null'); } catch { /* leer */ }
    if (!o || o.basis !== cfg.leadApi) return;
    const alter = Date.now() - o.t;
    if (alter < 8000) return;                       // Anruf läuft wahrscheinlich noch
    try { localStorage.removeItem(ANRUF); } catch { /* egal */ }
    if (alter > 3 * 36e5) return;                   // zu alt, nicht mehr nachfragen
    try {
      const d = await api(cfg.leadApi + o.lid, { leise: true });
      vibriere([20, 40, 20]);
      const dlg = dialog('Wie lief der Anruf' + (o.firma ? ' bei ' + o.firma : '') + '?', h('div', {},
        kontaktKarte(d.kontakt_optionen, cfg.leadApi + o.lid + '/kontakt', null, { verlustgruende: d.verlustgruende, nach: () => { dlg.zu(); location.reload(); } }),
        h('p', { class: 'row' }, cfg.angebot ? h('button', { class: 'btn sec', onclick: () => { try { sessionStorage.setItem('mk-zum-angebot', o.lid); } catch { /* egal */ } dlg.zu(); location.hash = cfg.leadHash + o.lid; } }, 'Angebot für diesen Lead') : '',
          h('button', { class: 'btn sec', onclick: () => dlg.zu() }, 'Später / nicht angerufen'))), true);
    } catch { /* Nachfrage ist nur ein Angebot */ }
  }
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') nachfragen(); });
  window.addEventListener('pageshow', () => { setTimeout(nachfragen, 1200); });
}
