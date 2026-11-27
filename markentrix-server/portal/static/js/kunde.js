import { api, stapelTabellen, appStil, h, zweiFaktorKarte, pushNachfrage, zielFuerRolle, startFehler } from './common.js';
stapelTabellen(); appGefuehl();
appStil({ fab: (seite) => {
  if (!darfSchreiben()) return null;
  if (seite === 'termine' && hat('anfragen_termine')) return { text: '＋ Termin', zielText: 'Neuer Termin' };
  if (seite === 'nachrichten') return { text: '＋ Nachricht', zielText: 'Neue Nachricht' };
  if (['heute', 'anfragen', 'kalender'].includes(seite)) return { text: '＋ Nachricht', href: '#nachrichten' };
  return null;
} });
import { appGefuehl } from './appgefuehl.js';
import { setzeStart, zeige, hat } from './kunde/kern.js';
import { darfSchreiben } from './kunde/postfach.js';
import './kunde/uebersicht.js';
import './kunde/anfragen.js';
import './kunde/heute.js';
import './kunde/bewertungen.js';
import './kunde/postfach.js';
import './kunde/auswertung.js';
import './kunde/dokumente.js';
import './kunde/website.js';
import './kunde/dienste.js';
import './kunde/einrichten.js';
import './kunde/shop.js';
import './kunde/kalender.js';
import './kunde/stamm.js';
import './kunde/pakete.js';
import './kunde/wissen.js';
import './kunde/belege.js';
import './kunde/konto.js';
import { erstStart } from './anleitung.js';

(async () => {
  try {
    const startP = api('/api/kunde/start'); startP.catch(() => {});
    const me = await api('/api/me');
    if (me.rolle === 'admin' || me.rolle === 'vertrieb') { location.href = zielFuerRolle(me.rolle); return; }
    if (me.agb_offen) {
      const r = document.getElementById('app'), haken = h('input', { type: 'checkbox', id: 'agbhaken', style: 'width:auto' }), m = h('div');
      r.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;margin:40px auto' }, h('h1', {}, 'Allgemeine Geschäftsbedingungen'),
        h('p', {}, 'Bitte lesen und bestätigen Sie unsere AGB (Version ' + me.agb_offen.version + '), damit Sie das Portal nutzen können. Wir halten Ihre Bestätigung mit Datum und Uhrzeit fest.'),
        h('p', {}, h('a', { class: 'btn sec', href: '/api/agb.pdf', target: '_blank', rel: 'noopener' }, 'AGB als PDF öffnen')),
        h('label', { style: 'display:flex;gap:8px;align-items:flex-start;color:inherit;font-size:15px' }, haken, 'Ich habe die AGB gelesen und erkenne sie für unser Unternehmen an.'), m,
        h('p', {}, h('button', { class: 'btn', onclick: async () => { if (!haken.checked) { m.replaceChildren(h('div', { class: 'msg err' }, 'Bitte setzen Sie zuerst den Haken.')); return; }
          try { await api('/api/kunde/agb/zustimmen', { method: 'POST', body: { bestaetigt: true, agb_id: me.agb_offen.id } }); location.reload(); } catch (x) { m.replaceChildren(h('div', { class: 'msg err' }, x.message)); } } }, 'Bestätigen und weiter'))));
      return;
    }
    if (me.zwei_faktor_pflicht) { const r = document.getElementById('app'); r.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;margin:40px auto' }, h('h1', {}, 'Zwei-Faktor-Anmeldung einrichten'), h('p', {}, 'Für Ihren Zugang ist die Zwei-Faktor-Anmeldung Pflicht. Bitte jetzt mit einer Authenticator-App einrichten, danach geht es direkt weiter.'), zweiFaktorKarte(), h('p', {}, h('button', { class: 'btn', onclick: () => location.reload() }, 'Weiter zum Portal')))); return; }
    const start = await startP;
    setzeStart(start);
    if (start.kunde.branding_farbe) { const f = start.kunde.branding_farbe; document.documentElement.style.setProperty('--grad', f); document.documentElement.style.setProperty('--violet', f); }
  } catch (e) { startFehler(document.getElementById('app'), e); return; }
  window.addEventListener('hashchange', zeige);
  zeige();
  erstStart().then(() => setTimeout(pushNachfrage, 2500)).catch(() => {});
})();
