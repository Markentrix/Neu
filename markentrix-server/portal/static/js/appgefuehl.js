// App-Gefühl am Handy: Lang drücken auf Listeneinträge, gemerkte Position, Foto aufnehmen und Spracheingabe an Eingabefeldern.
import { h, dialog, vibriere } from './common.js';

const LANG = 'a.btn, button, a[href]';

/** Alle bedienbaren Knöpfe einer Zeile (ohne ausgeblendete und ohne Mini-Symbole ohne Text). */
function aktionenVon(zeile) {
  const seen = new Set();
  return [...zeile.querySelectorAll(LANG)].filter((k) => {
    const el = /** @type {HTMLElement} */ (k), t = (el.getAttribute('data-wisch-text') || el.textContent || el.getAttribute('aria-label') || '').trim();
    if (!t || t.length > 40 || el.hidden || el.hasAttribute('disabled') || el.closest('[hidden]') || seen.has(t)) return false;
    seen.add(t); return true;
  });
}

function langDruck() {
  const wahl = '.heutezeile, ul.prio > li, table.stapel tbody tr, .liste > li';
  /** @type {{t: number, x: number, y: number, el: Element} | null} */
  let z = null;
  let gerade = 0;   // Zeitpunkt des letzten Menüs: der anschließende Klick (Finger loslassen) wird verschluckt
  const stop = () => { if (z) { clearTimeout(z.t); z = null; } };
  document.addEventListener('touchstart', (e) => {
    stop();
    const t = e.target instanceof Element ? e.target : null, zeile = t && t.closest(wahl);
    if (!zeile || e.touches.length !== 1 || t.closest('input, textarea, select, .dlg, [contenteditable]')) return;
    const k = aktionenVon(zeile);
    if (k.length < 2) return;
    z = { x: e.touches[0].clientX, y: e.touches[0].clientY, el: zeile, t: window.setTimeout(() => {
      const el = z && z.el; z = null; if (!el) return;
      const liste = aktionenVon(el); if (liste.length < 2) return;
      gerade = Date.now(); vibriere(20);
      const titel = ((el.querySelector('.pt b, b, strong, h3') || {}).textContent || el.textContent || 'Aktionen').trim().replace(/\s+/g, ' ').slice(0, 50);
      const d = dialog(titel, h('div', { class: 'langmenue' }, liste.map((k) => {
        const text = (k.getAttribute('data-wisch-text') || k.textContent || k.getAttribute('aria-label') || '').trim();
        return h('button', { type: 'button', class: 'btn sec', onclick: () => { gerade = 0; d.zu(); setTimeout(() => /** @type {HTMLElement} */ (k).click(), 30); } }, text);
      })));
    }, 550) };
  }, { passive: true });
  document.addEventListener('touchmove', (e) => { if (z && (Math.abs(e.touches[0].clientX - z.x) > 10 || Math.abs(e.touches[0].clientY - z.y) > 10)) stop(); }, { passive: true });
  document.addEventListener('touchend', stop); document.addEventListener('touchcancel', stop);
  document.addEventListener('click', (e) => { if (gerade && Date.now() - gerade < 700 && !(e.target instanceof Element && e.target.closest('.dlg'))) { gerade = 0; e.preventDefault(); e.stopPropagation(); } }, true);
  document.addEventListener('contextmenu', (e) => { const t = e.target instanceof Element ? e.target : null; if (t && t.closest(wahl) && !t.closest('input, textarea') && matchMedia('(pointer:coarse)').matches) e.preventDefault(); });
}

const ORT = 'mk-ort:' + (typeof location !== 'undefined' ? location.pathname : '');
function ortMerken() {
  // Als installierte App dort weitermachen, wo man aufgehört hat (nur wenn die App ohne Ziel geöffnet wird)
  try {
    const standalone = matchMedia('(display-mode: standalone)').matches || /** @type {any} */ (navigator).standalone;
    if (standalone && !location.hash) {
      const o = JSON.parse(localStorage.getItem(ORT) || 'null');
      if (o && o.hash && Date.now() - o.zeit < 12 * 3600 * 1000) history.replaceState(history.state, '', location.pathname + location.search + '#' + o.hash);
    }
  } catch { /* ohne Speicher startet die App wie gewohnt */ }
  const sichern = () => { try { const hs = location.hash.slice(1); if (hs && !hs.startsWith('anrufen')) localStorage.setItem(ORT, JSON.stringify({ hash: hs, zeit: Date.now() })); } catch { /* egal */ } };
  window.addEventListener('hashchange', sichern); sichern();
  // Zurück (Taste oder Wisch): die Liste steht wieder an derselben Stelle
  let zurueck = false;
  window.addEventListener('popstate', () => { zurueck = true; setTimeout(() => { zurueck = false; }, 900); });
  window.addEventListener('hashchange', () => {
    if (!zurueck) return;
    let y = 0; try { y = JSON.parse(sessionStorage.getItem('mk-scroll') || '{}')[location.hash] || 0; } catch { /* egal */ }
    if (y > 50) [150, 500, 1100, 2000].forEach((t) => setTimeout(() => { if (Math.abs(window.scrollY - y) > 8 && document.documentElement.scrollHeight >= y + window.innerHeight) window.scrollTo(0, y); }, t));
  });
}

// ---------------------------------------------------------------- Foto aufnehmen und Spracheingabe
const grob = () => matchMedia('(pointer:coarse)').matches;
export const spracheErlaubt = () => { try { return localStorage.getItem('mk-sprache') === '1'; } catch { return false; } };
const SR = () => /** @type {any} */ (window).SpeechRecognition || /** @type {any} */ (window).webkitSpeechRecognition;
export const spracheGeht = () => !!SR();

function fotoKnopf(feld) {
  if (feld.dataset.kamera) return; feld.dataset.kamera = '1';
  const acc = (feld.accept || '').toLowerCase();
  if (acc && !/image|\.(jpe?g|png|webp)|\*\/\*/.test(acc)) return;
  const knopf = h('button', { type: 'button', class: 'btn sec small fotoknopf' }, '📷 Foto aufnehmen');
  knopf.addEventListener('click', () => {
    const k = h('input', { type: 'file', accept: 'image/*', capture: 'environment', hidden: true });
    k.addEventListener('change', () => {
      const f = k.files && k.files[0]; if (!f) return;
      const dt = new DataTransfer(); if (feld.multiple) [...feld.files].forEach((x) => dt.items.add(x)); dt.items.add(f);
      feld.files = dt.files; feld.dispatchEvent(new Event('change', { bubbles: true })); k.remove();
    });
    document.body.append(k); k.click();
  });
  feld.insertAdjacentElement('afterend', knopf);
}

function mikroKnopf(feld) {
  if (feld.dataset.mikro) return; feld.dataset.mikro = '1';
  if (feld.readOnly || feld.disabled) return;
  let erk = null;
  const knopf = h('button', { type: 'button', class: 'btn sec small mikroknopf', 'aria-pressed': 'false', 'aria-label': 'Spracheingabe starten' }, '🎙 Sprechen');
  const aus = () => { if (erk) { try { erk.stop(); } catch { /* schon beendet */ } erk = null; } knopf.setAttribute('aria-pressed', 'false'); knopf.textContent = '🎙 Sprechen'; knopf.classList.remove('an'); };
  knopf.addEventListener('click', () => {
    if (erk) { aus(); return; }
    const R = SR(); if (!R) return;
    erk = new R(); erk.lang = 'de-DE'; erk.continuous = true; erk.interimResults = false;
    erk.onresult = (e) => {
      let t = ''; for (let i = e.resultIndex; i < e.results.length; i++) if (e.results[i].isFinal) t += e.results[i][0].transcript;
      if (t.trim()) { feld.value = (feld.value && !/\s$/.test(feld.value) ? feld.value + ' ' : feld.value) + t.trim(); feld.dispatchEvent(new Event('input', { bubbles: true })); }
    };
    erk.onend = aus; erk.onerror = aus;
    try { erk.start(); knopf.setAttribute('aria-pressed', 'true'); knopf.textContent = '⏹ Fertig'; knopf.classList.add('an'); vibriere(10); } catch { aus(); }
  });
  feld.insertAdjacentElement('afterend', knopf);
}

function eingabeKnoepfe() {
  const lauf = () => {
    if (grob()) document.querySelectorAll('input[type=file]:not([data-kamera])').forEach((f) => fotoKnopf(f));
    if (spracheErlaubt() && spracheGeht() && grob()) document.querySelectorAll('textarea:not([data-mikro])').forEach((f) => mikroKnopf(f));
  };
  let t = 0;
  new MutationObserver(() => { clearTimeout(t); t = window.setTimeout(lauf, 200); }).observe(document.documentElement, { childList: true, subtree: true });
  lauf();
}

/** Tippen auf eine Push-Meldung, während die App läuft: direkt zur Seite springen, ohne Neuladen. */
function meldungsSprung() {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.addEventListener('message', (e) => {
    if (!e.data || e.data.typ !== 'mk-oeffnen') return;
    try { const u = new URL(e.data.url, location.origin); if (u.pathname === location.pathname) { if (u.hash && u.hash !== location.hash) location.hash = u.hash; } else location.href = u.pathname + u.hash; } catch { /* ungültiges Ziel */ }
  });
}

export function appGefuehl() {
  if (typeof document === 'undefined') return;
  meldungsSprung();
  langDruck(); ortMerken(); eingabeKnoepfe();
}
