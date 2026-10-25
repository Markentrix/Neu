// Funnel-Vorlage „Website-Check“ (/f/<name>): Formular, dann Danke-Ansicht mit Gesamtwert und Prüfpunkten. Ohne Cookies; gibt UTM-Angaben an das Portal weiter.
import { api, h } from './common.js';

const slug = decodeURIComponent(location.pathname.split('/')[2] || '');
const q = new URLSearchParams(location.search);
const el = (id) => /** @type {HTMLElement} */ (document.getElementById(id));
const inp = (id) => /** @type {HTMLInputElement} */ (document.getElementById(id));
const f = /** @type {HTMLFormElement} */ (el('f'));
const FELDER = ['w', 'n', 't', 'e', 'c'];
const WORT = { gut: 'gut', mittel: 'teilweise', schlecht: 'fehlt' };
/** @type {any} */ let kamp = null;
let website = '';

function fehler(id, text) {
  el('f-' + id).textContent = text || '';
  inp(id).setAttribute('aria-invalid', text ? 'true' : 'false');
}

function ausweichen(text) {
  const m = el('m');
  m.replaceChildren(text + ' ');
  const k = kamp && kamp.kontakt;
  if (k && (k.telefon || k.email)) {
    m.append('Sie erreichen uns auch direkt: ');
    if (k.telefon) m.append(h('a', { href: 'tel:' + k.telefon.replace(/[^\d+]/g, '') }, k.telefon));
    if (k.telefon && k.email) m.append(' oder ');
    if (k.email) m.append(h('a', { href: 'mailto:' + k.email }, k.email));
    m.append('.');
  }
  m.hidden = false;
}

function kontaktLinks() {
  const k = kamp.kontakt || {};
  const tel = /** @type {HTMLAnchorElement} */ (el('fusstel')), mail = /** @type {HTMLAnchorElement} */ (el('fussmail')), anruf = /** @type {HTMLAnchorElement} */ (el('anruf'));
  if (k.telefon) { tel.href = anruf.href = 'tel:' + k.telefon.replace(/[^\d+]/g, ''); tel.hidden = anruf.hidden = false; }
  if (k.email) { mail.href = 'mailto:' + k.email; mail.hidden = false; }
}

async function laden() {
  try {
    kamp = await api('/api/public/funnel/' + encodeURIComponent(slug), { leise: true });
  } catch (e) {
    el('weg').hidden = false; return;
  }
  document.title = kamp.titel || kamp.name;
  el('firma').textContent = kamp.firma;
  if (kamp.kicker) { el('kicker').textContent = kamp.kicker; el('kicker').hidden = false; }
  if (kamp.titel) el('titel').textContent = kamp.titel;
  if (kamp.untertitel) el('untertitel').textContent = kamp.untertitel;
  el('nutzen').replaceChildren(...(kamp.nutzen || []).map(n => h('li', {}, n)));
  el('ew').textContent = kamp.einwilligung_text;
  el('b').textContent = kamp.button;
  el('tl').textContent = kamp.telefon_pflicht ? 'Telefon' : 'Telefon (freiwillig)';
  inp('t').required = !!kamp.telefon_pflicht;
  el('el').textContent = kamp.check_mail ? 'E-Mail (für den Bericht)' : 'E-Mail';
  kontaktLinks();
  if (kamp.referenz) {
    el('reftext').textContent = kamp.referenz.text;
    el('refname').textContent = kamp.referenz.name || '';
    if (kamp.referenz.link) { /** @type {HTMLAnchorElement} */ (el('reflink')).href = kamp.referenz.link; el('reflink').hidden = false; }
    el('referenz').hidden = false;
  }
  if (kamp.foto) {
    const bild = /** @type {HTMLImageElement} */ (el('foto'));
    bild.addEventListener('load', () => { bild.hidden = false; });
    bild.src = kamp.foto;
  }
  f.hidden = false;
  mitlaufen();
}

/** Knopf, der auf dem Handy unten mitläuft, solange das Formular nicht zu sehen ist. */
function mitlaufen() {
  const k = el('mitlaufend');
  if (!('IntersectionObserver' in window)) return;
  new IntersectionObserver((e) => { k.hidden = e[0].isIntersecting || !el('danke').hidden; }).observe(f);
  k.addEventListener('click', (ev) => { ev.preventDefault(); f.scrollIntoView({ behavior: 'smooth', block: 'center' }); setTimeout(() => inp('w').focus({ preventScroll: true }), 400); });
}

/** Schritt 1: nur die Website-Adresse. Erst danach Name, Telefon, E-Mail und Einwilligung. */
function adresse() {
  let w = inp('w').value.trim();
  if (w && !/^https?:\/\//i.test(w)) w = 'https://' + w;
  try { const u = new URL(w); if (!u.hostname.includes('.')) w = ''; } catch (e) { w = ''; }
  return w;
}

el('weiter').addEventListener('click', () => {
  fehler('w', '');
  if (!adresse()) { fehler('w', 'Bitte eine gültige Adresse eingeben, z. B. www.ihr-betrieb.de'); inp('w').focus(); return; }
  el('weiter').hidden = true;
  el('schritt2').hidden = false;
  el('schritt').textContent = 'Schritt 2 von 2';
  el('formtitel').textContent = 'Fast fertig: Wohin dürfen wir das Ergebnis schicken?';
  el('formsub').textContent = 'Danach sehen Sie Ihr Ergebnis sofort.';
  inp('n').focus();
});
inp('w').addEventListener('keydown', (ev) => { if (ev.key === 'Enter' && el('schritt2').hidden) { ev.preventDefault(); el('weiter').click(); } });

function pruefen() {
  FELDER.forEach(x => fehler(x, ''));
  let erstes = '';
  const fail = (id, t) => { fehler(id, t); if (!erstes) erstes = id; };
  const w = adresse();
  if (!w) fail('w', 'Bitte eine gültige Adresse eingeben, z. B. www.ihr-betrieb.de');
  if (inp('n').value.trim().length < 2) fail('n', 'Bitte Ihren Namen eingeben.');
  const tel = inp('t').value.replace(/\D/g, '');
  if (kamp.telefon_pflicht && tel.length < 6) fail('t', 'Bitte eine Telefonnummer eingeben.');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inp('e').value.trim())) fail('e', 'Bitte eine gültige E-Mail-Adresse eingeben.');
  if (!inp('c').checked) fail('c', 'Bitte bestätigen Sie die Einwilligung.');
  if (erstes) inp(erstes).focus();
  return erstes ? '' : w;
}

f.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  el('m').hidden = true;
  const w = pruefen();
  if (!w) return;
  const b = /** @type {HTMLButtonElement} */ (el('b'));
  b.disabled = true; b.textContent = 'Wird gesendet …';
  /** @type {Record<string,string>} */ const utm = {};
  for (const [k, v] of q.entries()) if (/^(utm_[a-z]+|gclid|fbclid)$/.test(k)) utm[k] = v;
  try {
    const r = await api('/api/public/funnel/' + encodeURIComponent(slug), { method: 'POST', leise: true, body: {
      name: inp('n').value.trim(), email: inp('e').value.trim(), telefon: inp('t').value.trim() || null, website: w,
      einwilligung: inp('c').checked, ref: q.get('ref'), utm, zweitfeld: inp('z').value || null } });
    website = w.replace(/^https?:\/\//, '').replace(/\/$/, '');
    danke(r);
  } catch (x) {
    ausweichen(/** @type {Error} */ (x).message);
    b.disabled = false; b.textContent = kamp.button;
  }
});

function danke(r) {
  el('seite').hidden = true; el('danke').hidden = false; el('mitlaufend').hidden = true;
  el('dt').textContent = kamp.danke_titel || 'Danke! Ihr Check läuft.';
  el('dx').textContent = kamp.danke_text || '';
  el('terminbox').hidden = !r.termin;
  el('adresse').textContent = 'Geprüft wird: ' + website;
  window.scrollTo(0, 0);
  el('dt').setAttribute('tabindex', '-1'); el('dt').focus();
  if (r.check) abfragen(r.check, 0);
  else wert(null, 'Wir sehen uns Ihre Website an und melden uns.');
}

/** Gesamtwert im Ring anzeigen (null = kein Wert, nur Text). */
function wert(score, text) {
  const ring = el('ring');
  ring.classList.remove('laeuft');
  ring.style.setProperty('--p', String(score ?? 0));
  el('score').textContent = score === null ? '–' : String(score);
  ring.setAttribute('aria-label', score === null ? text : 'Gesamtwert ' + score + ' von 100');
  el('urteil').textContent = text;
}

async function abfragen(token, n) {
  let s = null;
  try { s = await api('/api/public/funnel/' + encodeURIComponent(slug) + '/check/' + encodeURIComponent(token), { leise: true }); } catch (e) { s = null; }
  if (s && s.status === 'fertig') {
    wert(s.score, s.zusammenfassung);
    el('liste').replaceChildren(...s.punkte.map(p => h('li', {}, h('span', { class: 'chip ' + p.status }, WORT[p.status] || p.status),
      h('span', {}, h('b', {}, p.titel), h('span', { class: 't' }, p.text)))));
    el('liste').hidden = false;
    if (s.mail) el('dx').textContent = (kamp.danke_text ? kamp.danke_text + ' ' : '') + 'Der ausführliche Bericht kommt als PDF per E-Mail.';
    return;
  }
  if ((s && s.status === 'fehler') || n >= 40) { wert(null, 'Das Ergebnis ist gerade nicht verfügbar. Wir sehen uns Ihre Website trotzdem an und melden uns.'); return; }
  setTimeout(() => abfragen(token, n + 1), 3000);
}

laden();
