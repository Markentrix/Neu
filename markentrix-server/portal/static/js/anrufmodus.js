// Anruf-Modus: nach jedem festgehaltenen Gespräch springt das Portal zum nächsten heißen Lead.
// Gemeinsam für Vertrieb und Admin; die Unterschiede (Adresse, Zielseite, Filter) kommen über `cfg`.
import { h, api, melde } from './common.js';

const TEXT = { heiss: 'Heiße Leads der Reihe nach', zufall: 'Zufällig aus den heißen Leads', zeit: 'Heiße Leads, beste Uhrzeit zuerst' };

/**
 * @param {{ schluessel: string, url: string, leadHash: string, heimHash: string, ohneModus?: (aktuell: string|null) => Promise<string|null> }} cfg
 */
export function anrufModus(cfg) {
  const lesen = () => { try { return JSON.parse(sessionStorage.getItem(cfg.schluessel) || 'null'); } catch { return null; } };
  const schreiben = (x) => { try { if (x) sessionStorage.setItem(cfg.schluessel, JSON.stringify(x)); else sessionStorage.removeItem(cfg.schluessel); } catch { /* ohne Speicher gibt es keinen Anruf-Modus */ } };

  /** Springt zum nächsten Lead. Im Anruf-Modus zum nächsten heißen, sonst (falls vorhanden) nach `ohneModus`. */
  async function naechster(aktuell) {
    const mo = lesen();
    try {
      if (mo) {
        if (aktuell && !mo.erledigt.includes(aktuell)) mo.erledigt.push(aktuell);
        const r = await api(cfg.url + '?modus=' + mo.modus + '&ausser=' + mo.erledigt.join(',') + (mo.filter ? '&vertriebler=' + encodeURIComponent(mo.filter) : ''));
        if (r.id) { schreiben(mo); location.hash = cfg.leadHash + r.id; return; }
        try { sessionStorage.setItem(cfg.schluessel + '-ende', String(mo.erledigt.length)); } catch { /* egal */ }
        schreiben(null); location.hash = cfg.heimHash; return;
      }
      const id = cfg.ohneModus ? await cfg.ohneModus(aktuell) : null;
      location.hash = id ? cfg.leadHash + id : cfg.heimHash;
    } catch { location.hash = cfg.heimHash; }
  }

  /** Karte zum Starten. */
  function karte(m, filterWerte) {
    const sel = h('select', { 'aria-label': 'Reihenfolge' }, Object.entries(TEXT).map(([k, t]) => h('option', { value: k }, t)));
    const fil = filterWerte ? h('select', { 'aria-label': 'Welche Leads' }, filterWerte.map(([k, t]) => h('option', { value: k }, t))) : null;
    let ende = null; try { ende = sessionStorage.getItem(cfg.schluessel + '-ende'); sessionStorage.removeItem(cfg.schluessel + '-ende'); } catch { /* egal */ }
    return h('div', { class: 'card' }, h('h2', {}, '📞 Anruf-Modus'),
      ende ? h('div', { class: 'msg ok' }, 'Anruf-Modus beendet: keine weiteren Leads in der Liste. ' + ende + ' abgearbeitet.') : '',
      h('p', { class: 'small muted' }, 'Nach jedem festgehaltenen Gespräch springt das Portal automatisch zum nächsten heißen Lead. Sind keine heißen mehr übrig, folgen fällige Wiedervorlagen und neue Leads. Am Computer wählst du das Ergebnis mit den Tasten 1 bis 9, „N“ speichert und springt weiter.'),
      h('div', { class: 'row', style: 'gap:8px;align-items:center;flex-wrap:wrap' }, sel, fil || '', h('button', { class: 'btn', onclick: async () => {
        schreiben({ modus: sel.value, filter: fil ? fil.value : '', erledigt: [], start: Date.now() }); await naechster(null);
        if (!lesen()) melde(m, 'Es gibt gerade keinen Lead zum Anrufen.', 'info'); } }, 'Anruf-Modus starten')));
  }

  /** Leiste oben im Lead, solange der Modus läuft. */
  function leiste(lid) {
    const mo = lesen(); if (!mo) return '';
    return h('div', { class: 'card', style: 'border-left:4px solid var(--akzent, #1E9BFF)' }, h('div', { class: 'row', style: 'align-items:center;gap:8px;flex-wrap:wrap' },
      h('b', {}, '📞 Anruf-Modus'), h('span', { class: 'small muted grow' }, TEXT[mo.modus] + ' · ' + mo.erledigt.length + ' abgearbeitet'),
      h('button', { class: 'btn sec small', onclick: () => naechster(lid) }, 'Überspringen'),
      h('button', { class: 'btn sec small', onclick: () => { schreiben(null); location.hash = cfg.heimHash; } }, 'Beenden')));
  }

  return { aktiv: () => !!lesen(), naechster, karte, leiste };
}
