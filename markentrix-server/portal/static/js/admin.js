import { anrufNachfrage, toast, h, api, nutzung, zweiFaktorKarte, stapelTabellen, pushNachfrage, zielFuerRolle, startFehler } from './common.js';
stapelTabellen();
import { belegEditor } from './admin/belege.js';
import {V, gerüst, zaehlerAdmin, systemAmpel, setzeIch, setzePakete, setzeZeige } from './admin/kern.js';
import { kundeDetail } from './admin/kunden.js';
import { leadDetail, partnerDetail, modus as anrufmodus } from './admin/vertrieb.js';
import './admin/start.js';
import './admin/kunden.js';
import './admin/verwaltung.js';
import './admin/einstellungen.js';
import './admin/belege.js';
import './admin/vertrieb.js';
import './admin/vertraege.js';
import './admin/umfragen.js';
import './admin/postfach.js';
import './admin/pipeline.js';
import './admin/onboardingboard.js';
import './admin/meintag.js';
import './admin/kalender.js';
import { liveHinweis } from './admin/funnel.js';
const root = document.getElementById('app');

async function seiteZeigen() {
  const hash = (location.hash || '#uebersicht').slice(1);
  let seite = hash.split('/')[0].split('?')[0], inhalt;
  if (seite === 'anrufen') {   // Kurzbefehl „Anruf-Modus“ vom App-Symbol
    if (!(await anrufmodus.starten())) { location.hash = '#leads'; toast('Gerade kein Lead zum Anrufen.', 'ok'); }
    return;
  }
  nutzung(seite);
  try {
    if (seite === 'kunde') inhalt = await kundeDetail(hash.split('/')[1]);
    else if (seite === 'partner') inhalt = await partnerDetail(hash.split('/')[1]);
    else if (seite === 'lead') inhalt = await leadDetail(hash.split('/')[1]);
    else if (seite === 'beleg') inhalt = await belegEditor(hash.split('/')[1]);
    else if (seite === 'neubeleg') inhalt = await belegEditor(null, hash.split('/')[1], hash.split('/')[2]);
    else if (V[seite]) inhalt = await V[seite](hash.split('?')[0].split('/').slice(1).join('/') || undefined);
    else { seite = 'uebersicht'; inhalt = await V.uebersicht(); }
  } catch (e) { inhalt = h('div', { class: 'msg err' }, e.message); }
  root.replaceChildren(gerüst(seite === 'kunde' ? 'kunden' : seite === 'partner' ? 'vertrieb' : seite === 'lead' ? 'leads' : (seite === 'beleg' || seite === 'neubeleg') ? 'belege' : seite, inhalt));
}

setzeZeige(seiteZeigen);
anrufNachfrage({ leadApi: '/api/admin/leads/', leadHash: '#lead/' });
(async () => {
  try {
    const katP = api('/api/admin/katalog'); katP.catch(() => {});
    const me = await api('/api/me');
    if (me.rolle !== 'admin') { location.href = zielFuerRolle(me.rolle); return; }
    if (me.zwei_faktor_pflicht) {   // Pflicht laut AVV: ohne Zwei-Faktor-Anmeldung kein Zugriff auf das Admin-Portal
      root.replaceChildren(h('div', { class: 'card', style: 'max-width:560px;margin:40px auto' }, h('h1', {}, 'Zwei-Faktor-Anmeldung einrichten'),
        h('p', {}, 'Für Administrator-Zugänge ist die Zwei-Faktor-Anmeldung Pflicht. Bitte jetzt einrichten, danach geht es direkt weiter.'), zweiFaktorKarte(),
        h('p', {}, h('button', { class: 'btn', onclick: () => location.reload() }, 'Weiter zum Portal'))));
      return;
    }
    setzeIch(me);
    setzePakete((await katP).produkte);
    try { const z = (await api('/api/admin/uebersicht')).zusammenarbeit; zaehlerAdmin.postfach = z.tickets_ungelesen; zaehlerAdmin.freigaben = z.freigaben_wartend; zaehlerAdmin.aufgaben = z.aufgaben_ueberfaellig; } catch (e) { /* Zähler sind optional */ }
    try {
      const hh = await api('/api/admin/heute', { leise: true });
      zaehlerAdmin.leads = (hh.leads_gesamt || 0) + (hh.wiedervorlagen || []).length; zaehlerAdmin.belege = (hh.rechnungen || []).length; zaehlerAdmin.onboarding = (hh.onboarding || []).length;
    } catch (e) { /* Zähler sind optional */ }
    try { const sy = await api('/api/admin/systemstatus', { leise: true }); systemAmpel.gesamt = sy.gesamt; const bad = (sy.ampel || []).filter(p => p.status === 'bad' || p.status === 'warn'); systemAmpel.text = bad.length ? bad.map(p => p.titel).join(', ') : ''; } catch (e) { /* Ampel ist optional */ }
  } catch (e) { startFehler(root, e); return; }
  window.addEventListener('hashchange', seiteZeigen);
  seiteZeigen();
  setTimeout(pushNachfrage, 2500);
  liveHinweis();
})();

