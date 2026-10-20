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

export async function api(path, opt = {}) {
  /** @type {any} */
  const o = { method: opt.method || 'GET', headers: { 'X-MK': '1' }, credentials: 'same-origin' };
  if (opt.body instanceof FormData) o.body = opt.body;
  else if (opt.body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(opt.body); }
  let r;
  try { r = await fetch(path, o); } catch (e) { throw new Error('Keine Verbindung zum Server.'); }
  let d = null;
  try { d = await r.json(); } catch (e) { /* leer */ }
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
  location.href = '/';
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
export const rechtFuss = () => h('div', { class: 'rechtfuss small muted' }, h('a', { href: '/impressum' }, 'Impressum'), ' · ', h('a', { href: '/datenschutz' }, 'Datenschutz'));


// Kontaktergebnis zu einem Lead festhalten (Admin und Vertriebler): Schnellauswahl, Notiz, Wiedervorlage
const WV_SCHNELL = [['Morgen', 1], ['In 3 Tagen', 3], ['Nächste Woche', 7], ['In 2 Wochen', 14], ['Keine', 0]];
const tagIn = (n) => n ? new Date(Date.now() + n * 864e5).toISOString().slice(0, 10) : '';

/** Wiedervorlage-Feld mit Schnellwahl (Morgen, in 3 Tagen, nächste Woche …). Gibt { el, tag } zurück. */
export function wiedervorlageWahl(start = '') {
  const tag = h('input', { type: 'date', style: 'max-width:170px', value: start, 'aria-label': 'Wiedervorlage' });
  const chips = h('div', { class: 'row', style: 'gap:6px;flex-wrap:wrap;margin-top:4px' }, WV_SCHNELL.map(([t, n]) => h('button', { type: 'button', class: 'btn sec small', onclick: () => { tag.value = tagIn(n); } }, t)));
  return { tag, el: h('div', {}, h('label', { style: 'margin:0' }, 'Wiedervorlage'), tag, chips) };
}

/**
 * Kontaktergebnis festhalten. Optionen: { nach: (r) => void } wird statt Neuladen aufgerufen,
 * { naechster: () => void } blendet „Speichern & nächster Lead“ ein.
 */
export function kontaktKarte(optionen, url, wiedervorlage, extra = {}) {
  const m = h('div'), notiz = h('input', { placeholder: 'Kurze Notiz (freiwillig)', maxlength: 1500, 'aria-label': 'Notiz' }), wv = wiedervorlageWahl();
  let wahl = null; const knoepfe = [];
  const speichern = h('button', { class: 'btn', disabled: true }, 'Speichern'), weiter = extra.naechster ? h('button', { class: 'btn sec', disabled: true }, 'Speichern & nächster Lead') : '';
  const waehle = (o, b) => { wahl = o; knoepfe.forEach(x => x.classList.remove('gewaehlt')); b.classList.add('gewaehlt'); speichern.disabled = false; if (weiter) weiter.disabled = false;
    wv.tag.value = tagIn(o.wiedervorlage_tage); };
  optionen.forEach(o => { const b = h('button', { type: 'button', class: 'btn sec small', onclick: () => waehle(o, b) }, o.text); knoepfe.push(b); });
  const los = async (danach) => { if (!wahl) return;
    try { const r = await api(url, { method: 'POST', body: { ergebnis: wahl.code, notiz: notiz.value || null, wiedervorlage: wv.tag.value || null } });
      if (danach) danach(r); else if (extra.nach) extra.nach(r); else location.reload(); } catch (x) { melde(m, x.message); } };
  speichern.onclick = () => los(null);
  if (weiter) /** @type {any} */ (weiter).onclick = () => los(extra.naechster);
  return h('div', { class: 'card' }, h('h2', {}, 'Kontakt festhalten'),
    h('p', { class: 'small muted' }, 'Was ist passiert? Der Verlauf und, wo es passt, der Status werden automatisch gesetzt.'), m,
    h('div', { class: 'row', style: 'flex-wrap:wrap;gap:6px' }, knoepfe),
    h('div', { class: 'row', style: 'margin-top:10px;align-items:flex-end;flex-wrap:wrap' }, h('div', { class: 'grow' }, notiz), wv.el, speichern, weiter),
    wiedervorlage ? h('p', { class: 'small muted' }, 'Aktuelle Wiedervorlage: ' + datum(wiedervorlage)) : '');
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
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); installAngebot = e; });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
}
const b64zuBytes = (s) => { const p = '='.repeat((4 - s.length % 4) % 4), r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from(r, c => c.charCodeAt(0)); };

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
  if (!standalone) install.replaceChildren(installAngebot ? h('p', {}, h('button', { class: 'btn sec small', onclick: async () => { installAngebot.prompt(); installAngebot = null; install.replaceChildren(); } }, 'Als App installieren')) :
    h('p', { class: 'small muted' }, ios ? 'Als App: Teilen-Symbol → „Zum Home-Bildschirm“.' : 'Als App: im Browser-Menü „App installieren“ bzw. „Zum Startbildschirm hinzufügen“ wählen.'));
  return h('div', { class: 'card' }, h('h2', {}, 'App & Benachrichtigungen'),
    h('p', { class: 'small muted' }, 'Das Portal lässt sich wie eine App aufs Handy legen. Mit Benachrichtigungen erfährst du sofort, wenn etwas Wichtiges passiert. Sie enthalten keine Namen oder Inhalte, nur den Anlass.'), m, box, anlass, install);
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
  vertrieb: [['zugewiesen', 'Neue Leads zugewiesen'], ['heute', 'Morgens: Anrufe des Tages'], ['buchung', 'Gespräch gebucht'], ['angebotsstatus', 'Status einer Angebotsanfrage'], ['angebotsreaktion', 'Angebot angesehen, angenommen oder abgelehnt'], ['wochenrueckblick', 'Montags: Wochenrückblick']],
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
