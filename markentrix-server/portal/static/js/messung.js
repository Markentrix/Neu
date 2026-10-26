// Messung der Werbung (Meta-Pixel, Google-Tag) auf Funnel-Seiten: lädt erst nach ausdrücklicher Einwilligung, ohne Einwilligung geht keine Anfrage an Meta oder Google.
import { h } from './common.js';

const SCHLUESSEL = 'mk-funnel-messung';
const gespeichert = () => { try { return localStorage.getItem(SCHLUESSEL); } catch (e) { return null; } };
const merke = (v) => { try { localStorage.setItem(SCHLUESSEL, v); } catch (e) { /* ohne Speicher wird eben jedes Mal gefragt */ } };
let aktiv = false;   // wird erst nach der Einwilligung wahr

const skriptLaden = (src) => { const s = document.createElement('script'); s.async = true; s.src = src; document.head.append(s); };

/** @param {any} t */
function starten(t) {
  const w = /** @type {any} */ (window);
  aktiv = true;
  if (t.meta) {
    if (!w.fbq) {
      /** @type {any} */ const n = w.fbq = function (...a) { if (n.callMethod) n.callMethod(...a); else n.queue.push(a); };
      if (!w._fbq) w._fbq = n;
      n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
      skriptLaden('https://connect.facebook.net/en_US/fbevents.js');
    }
    w.fbq('init', t.meta); w.fbq('track', 'PageView');
  }
  if (t.google) {
    w.dataLayer = w.dataLayer || [];
    w.gtag = function () { w.dataLayer.push(arguments); };   // Google erwartet das Arguments-Objekt, kein Array
    skriptLaden('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(t.google));
    w.gtag('js', new Date()); w.gtag('config', t.google);
  }
}

/** Zeigt den Hinweis, sofern noch nicht entschieden wurde.
 * @param {any} t */
export function messungFragen(t) {
  if (!t) return;
  const g = gespeichert();
  if (g === 'ja') { starten(t); return; }
  if (g === 'nein') return;
  const box = document.getElementById('messung');
  if (!box) return;
  const anbieter = [t.meta ? 'Meta (Facebook, Instagram)' : '', t.google ? 'Google' : ''].filter(Boolean).join(' und ');
  box.hidden = false;
  box.replaceChildren(h('p', { class: 'small', style: 'margin:0 0 8px' }, 'Mit Ihrer Einwilligung messen wir mit Diensten von ' + anbieter + ', wie gut unsere Werbung funktioniert. Dabei werden Daten an diese Anbieter übertragen. Sie können ablehnen, die Seite funktioniert genauso.'),
    h('div', { class: 'row' }, h('button', { class: 'btn small', type: 'button', onclick: () => { merke('ja'); box.hidden = true; starten(t); } }, 'Einverstanden'),
      h('button', { class: 'btn small', type: 'button', onclick: () => { merke('nein'); box.hidden = true; } }, 'Ablehnen')));
}

/** Meldet einen neuen Lead, aber nur nach Einwilligung.
 * @param {any} t */
export function leadMelden(t) {
  if (!aktiv || !t) return;
  const w = /** @type {any} */ (window);
  if (t.meta && w.fbq) w.fbq('track', 'Lead');
  if (t.google && t.google_label && w.gtag) w.gtag('event', 'conversion', { send_to: t.google_label });
}
