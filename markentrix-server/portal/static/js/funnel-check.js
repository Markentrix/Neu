// Funnel-Vorlage „Website-Check“ (/f/<name>): Formular, dann Danke-Ansicht mit Ampel. Ohne Cookies; gibt UTM-Angaben an das Portal weiter.
import { api, h } from './common.js';

const slug = decodeURIComponent(location.pathname.split('/')[2] || '');
const q = new URLSearchParams(location.search);
const el = (id) => /** @type {HTMLElement} */ (document.getElementById(id));
const inp = (id) => /** @type {HTMLInputElement} */ (document.getElementById(id));
const f = /** @type {HTMLFormElement} */ (el('f'));
const FELDER = ['w', 'n', 't', 'e', 'c'];
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
  el('firma').textContent = el('fussname').textContent = kamp.firma;
  if (kamp.kicker) { el('kicker').textContent = kamp.kicker; el('kicker').hidden = false; }
  if (kamp.titel) el('titel').textContent = kamp.titel;
  el('untertitel').textContent = kamp.untertitel || '';
  el('nutzen').replaceChildren(...(kamp.nutzen || []).map(n => h('li', {}, n)));
  el('ew').textContent = kamp.einwilligung_text;
  el('b').textContent = kamp.button;
  el('tl').textContent = kamp.telefon_pflicht ? 'Telefon' : 'Telefon (freiwillig)';
  inp('t').required = !!kamp.telefon_pflicht;
  el('el').textContent = kamp.check_mail ? 'E-Mail (hierhin kommt das Ergebnis als PDF)' : 'E-Mail';
  kontaktLinks();
  f.hidden = false;
}

function pruefen() {
  FELDER.forEach(x => fehler(x, ''));
  let erstes = '';
  const fail = (id, t) => { fehler(id, t); if (!erstes) erstes = id; };
  let w = inp('w').value.trim();
  if (w && !/^https?:\/\//i.test(w)) w = 'https://' + w;
  try { const u = new URL(w); if (!u.hostname.includes('.')) w = ''; } catch (e) { w = ''; }
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
  el('seite').hidden = true; el('danke').hidden = false;
  el('dt').textContent = kamp.danke_titel || 'Danke! Ihr Check läuft.';
  el('dx').textContent = kamp.danke_text || '';
  el('terminbox').hidden = !r.termin;
  el('adresse').textContent = 'Geprüft wird: ' + website;
  window.scrollTo(0, 0);
  el('dt').setAttribute('tabindex', '-1'); el('dt').focus();
  if (r.check) abfragen(r.check, 0);
  else ampel('', 'Wir sehen uns Ihre Website an und melden uns.');
}

function ampel(farbe, text) {
  const a = el('ampel');
  a.setAttribute('data-farbe', farbe);
  a.setAttribute('aria-label', 'Ampel: ' + text);
  el('urteil').textContent = text;
}

async function abfragen(token, n) {
  let s = null;
  try { s = await api('/api/public/funnel/' + encodeURIComponent(slug) + '/check/' + encodeURIComponent(token), { leise: true }); } catch (e) { s = null; }
  if (s && s.status === 'fertig') {
    ampel(s.ampel, s.zusammenfassung);
    el('liste').replaceChildren(...s.punkte.map(p => h('li', {}, h('span', { class: 'dot ' + p.status, 'aria-hidden': 'true' }),
      h('span', {}, h('b', {}, p.titel), h('span', { class: 't' }, p.text)))));
    el('liste').hidden = false;
    if (s.mail) el('dx').textContent = (kamp.danke_text ? kamp.danke_text + ' ' : '') + 'Das ausführliche Ergebnis kommt als PDF per E-Mail.';
    return;
  }
  if ((s && s.status === 'fehler') || n >= 40) { ampel('', 'Die Schnell-Ampel ist gerade nicht verfügbar. Wir sehen uns Ihre Website trotzdem an und melden uns.'); return; }
  setTimeout(() => abfragen(token, n + 1), 3000);
}

laden();
