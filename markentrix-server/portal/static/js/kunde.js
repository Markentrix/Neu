import { api, stapelTabellen, h, zweiFaktorKarte, pushNachfrage, zielFuerRolle, startFehler } from './common.js';
stapelTabellen();
import { setzeStart, zeige } from './kunde/kern.js';
import './kunde/uebersicht.js';
import './kunde/anfragen.js';
import './kunde/heute.js';
import './kunde/bewertungen.js';
import './kunde/postfach.js';
import './kunde/auswertung.js';
import './kunde/dokumente.js';
import './kunde/website.js';
import './kunde/dienste.js';
import './kunde/kalender.js';
import './kunde/stamm.js';
import './kunde/pakete.js';
import './kunde/wissen.js';
import './kunde/belege.js';
import './kunde/konto.js';
import { erstStart } from './anleitung.js';

(async () => {
  try {
    const me = await api('/api/me');
    if (me.rolle === 'admin' || me.rolle === 'vertrieb') { location.href = zielFuerRolle(me.rolle); return; }
    if (me.zwei_faktor_pflicht) { const r = document.getElementById('app'); r.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;margin:40px auto' }, h('h1', {}, 'Zwei-Faktor-Anmeldung einrichten'), h('p', {}, 'Für Ihren Zugang ist die Zwei-Faktor-Anmeldung Pflicht. Bitte jetzt mit einer Authenticator-App einrichten, danach geht es direkt weiter.'), zweiFaktorKarte(), h('p', {}, h('button', { class: 'btn', onclick: () => location.reload() }, 'Weiter zum Portal')))); return; }
    const start = await api('/api/kunde/start');
    setzeStart(start);
    if (start.kunde.branding_farbe) { const f = start.kunde.branding_farbe; document.documentElement.style.setProperty('--grad', f); document.documentElement.style.setProperty('--violet', f); }
  } catch (e) { startFehler(document.getElementById('app'), e); return; }
  window.addEventListener('hashchange', zeige);
  zeige();
  erstStart().then(() => setTimeout(pushNachfrage, 2500)).catch(() => {});
})();
