import { h, api } from './common.js';
import { belegEditor } from './admin/belege.js';
import {V, gerüst, zaehlerAdmin, setzeIch, setzePakete, setzeZeige } from './admin/kern.js';
import { kundeDetail } from './admin/kunden.js';
import { leadDetail, partnerDetail } from './admin/vertrieb.js';
import './admin/start.js';
import './admin/kunden.js';
import './admin/verwaltung.js';
import './admin/einstellungen.js';
import './admin/belege.js';
import './admin/vertrieb.js';
import './admin/postfach.js';
const root = document.getElementById('app');

async function seiteZeigen() {
  const hash = (location.hash || '#uebersicht').slice(1);
  let seite = hash.split('/')[0].split('?')[0], inhalt;
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
(async () => {
  try {
    const me = await api('/api/me');
    if (me.rolle !== 'admin') { location.href = '/app'; return; }
    setzeIch(me);
    setzePakete((await api('/api/admin/katalog')).produkte);
    try { const z = (await api('/api/admin/uebersicht')).zusammenarbeit; zaehlerAdmin.postfach = z.tickets_ungelesen; zaehlerAdmin.freigaben = z.freigaben_wartend; zaehlerAdmin.aufgaben = z.aufgaben_ueberfaellig; } catch (e) { /* Zähler sind optional */ }
  } catch (e) { return; }
  window.addEventListener('hashchange', seiteZeigen);
  seiteZeigen();
})();

