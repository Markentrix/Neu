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
export async function api(path, opt = {}) {
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
    r.setAttribute('x', i * bw + 2); r.setAttribute('y', hh - bh); r.setAttribute('width', Math.max(2, bw - 4));
    r.setAttribute('height', bh); r.setAttribute('rx', 3); r.setAttribute('fill', farbe); r.setAttribute('opacity', v ? '1' : '.25');
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
export function kontaktKarte(optionen, url, wiedervorlage) {
  const m = h('div'), notiz = h('input', { placeholder: 'Kurze Notiz (freiwillig)', maxlength: 1500 }), tag = h('input', { type: 'date', style: 'max-width:170px' });
  let wahl = null; const knoepfe = [];
  const speichern = h('button', { class: 'btn', disabled: true }, 'Speichern');
  const waehle = (o, b) => { wahl = o; knoepfe.forEach(x => x.classList.remove('gewaehlt')); b.classList.add('gewaehlt'); speichern.disabled = false;
    tag.value = o.wiedervorlage_tage ? new Date(Date.now() + o.wiedervorlage_tage * 864e5).toISOString().slice(0, 10) : ''; };
  optionen.forEach(o => { const b = h('button', { type: 'button', class: 'btn sec small', onclick: () => waehle(o, b) }, o.text); knoepfe.push(b); });
  speichern.onclick = async () => { if (!wahl) return;
    try { await api(url, { method: 'POST', body: { ergebnis: wahl.code, notiz: notiz.value || null, wiedervorlage: tag.value || null } }); location.reload(); } catch (x) { melde(m, x.message); } };
  return h('div', { class: 'card' }, h('h2', {}, 'Kontakt festhalten'),
    h('p', { class: 'small muted' }, 'Was ist passiert? Der Verlauf und, wo es passt, der Status werden automatisch gesetzt.'), m,
    h('div', { class: 'row', style: 'flex-wrap:wrap;gap:6px' }, knoepfe),
    h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, notiz), h('div', {}, h('label', { style: 'margin:0' }, 'Wiedervorlage'), tag), speichern),
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
const bytesZuB64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

export function pushKarte() {
  const m = h('div'), box = h('div'), install = h('div');
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
  if (!standalone) install.replaceChildren(installAngebot ? h('p', {}, h('button', { class: 'btn sec small', onclick: async () => { installAngebot.prompt(); installAngebot = null; install.replaceChildren(); } }, 'Als App installieren')) :
    h('p', { class: 'small muted' }, ios ? 'Als App: Teilen-Symbol → „Zum Home-Bildschirm“.' : 'Als App: im Browser-Menü „App installieren“ bzw. „Zum Startbildschirm hinzufügen“ wählen.'));
  return h('div', { class: 'card' }, h('h2', {}, 'App & Benachrichtigungen'),
    h('p', { class: 'small muted' }, 'Das Portal lässt sich wie eine App aufs Handy legen. Mit Benachrichtigungen erfährst du sofort, wenn etwas Wichtiges passiert. Sie enthalten keine Namen oder Inhalte, nur den Anlass.'), m, box, install);
}
