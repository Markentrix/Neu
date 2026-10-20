import { api, stapelTabellen } from './common.js';
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
import './kunde/belege.js';
import './kunde/konto.js';
import { erstStart } from './anleitung.js';

(async () => {
  try {
    const me = await api('/api/me');
    if (me.rolle === 'admin') { location.href = '/admin'; return; }
    const start = await api('/api/kunde/start');
    setzeStart(start);
    if (start.kunde.branding_farbe) { const f = start.kunde.branding_farbe; document.documentElement.style.setProperty('--grad', f); document.documentElement.style.setProperty('--violet', f); }
  } catch (e) { return; }
  window.addEventListener('hashchange', zeige);
  zeige();
  erstStart().catch(() => {});
})();
