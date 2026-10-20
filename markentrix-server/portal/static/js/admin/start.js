import { erinnerungsDialog } from './belege.js';
import { h, api, datum, zeit, euro, melde, ladeAnsicht, anpassenKnopf, ausgeblendetSet, delta, rueckgaengig } from '../common.js';
import { V, kopf, pill, sicherApi, tabelle, zeige } from './kern.js';

export function heuteKarte(t) {
  const abschnitt = (titel, liste, zeile) => liste.length ? h('div', { style: 'margin-bottom:12px' }, h('h3', {}, titel), liste.map(z => h('div', { class: 'row', style: 'padding:4px 0;border-bottom:1px solid var(--line)' }, zeile(z)))) : '';
  const TEMP = { kalt: '❄', warm: '☀', heiss: '🔥' };
  return h('div', { class: 'card' }, h('h2', {}, 'Heute zu tun', t.gesamt ? h('span', { class: 'badge', style: 'margin-left:8px' }, t.gesamt) : ''),
    t.gesamt ? '' : h('p', { class: 'muted' }, 'Alles erledigt. Nichts Dringendes offen. 🎉'),
    abschnitt('Nachrichten ohne Antwort', t.nachrichten, z => [h('a', { class: 'grow', href: '#postfach/' + z.id }, z.firma + ': ' + z.betreff)]),
    abschnitt('Aufgaben fällig oder überfällig', t.aufgaben, z => [h('a', { class: 'grow', href: '#aufgaben' }, z.titel), h('span', { class: 'small muted' }, datum(z.faellig_am))]),
    abschnitt('Leads: Wiedervorlage fällig', t.wiedervorlagen, z => [h('a', { class: 'grow', href: '#lead/' + z.id }, z.firma), h('span', { class: 'small muted' }, (z.vertriebler ? z.vertriebler + ' · ' : '') + datum(z.wiedervorlage_am))]),
    abschnitt('Neue Leads' + (t.leads_gesamt > t.leads.length ? ' (' + t.leads_gesamt + ')' : ''), t.leads, z => [h('a', { class: 'grow', href: '#lead/' + z.id }, (TEMP[z.temperatur] || '') + ' ' + z.firma), h('span', { class: 'small muted' }, z.quelle)]),
    abschnitt('Freigaben warten seit über 3 Tagen', t.freigaben, z => [h('a', { class: 'grow', href: '#kunde/' + z.kunden_id }, z.firma + ': ' + z.titel)]),
    abschnitt('Onboarding hängt', t.onboarding, z => [h('a', { class: 'grow', href: '#kunde/' + z.id }, z.firma)]),
    abschnitt('Rechnungen überfällig', t.rechnungen, z => [h('a', { class: 'grow', href: '#kunde/' + z.kunden_id }, z.firma + ': ' + z.nummer)]),
    abschnitt('AVV fehlt', t.avv_fehlt, z => [h('a', { class: 'grow', href: '#kunde/' + z.id }, z.firma)]));
}

V.uebersicht = async () => {
  const d = await api('/api/admin/uebersicht'), ob = (await sicherApi('/api/admin/onboarding/offen')) || [], heute = await api('/api/admin/heute'), sys = await sicherApi('/api/admin/systemstatus'), fw = await sicherApi('/api/admin/fruehwarnung');
  const s = d.kunden_status, summe = Object.values(s).reduce((a, b) => a + b, 0);
  const STANDARD_AUS = ['system', 'fruehwarnung', 'heute'], ans = await ladeAnsicht(), aus = ausgeblendetSet(ans, STANDARD_AUS);
  const cp = await sicherApi('/api/admin/cockpit');
  const KARTEN = [['top3', 'Heute zuerst (die 3 wichtigsten Dinge)'], ['prio', 'Jetzt wichtig (alles Dringende in einer Liste)'], ['betrieb', 'Betriebs-Ampel (Server, Sicherung, Mail, Jobs)'], ['system', 'Systemstatus'], ['fruehwarnung', 'Kunden-Frühwarnung'], ['cockpit', 'Geschäftszahlen'], ['heute', 'Heute zu tun'], ['zahlen', 'Kennzahlen-Kacheln'], ['avv', 'AVV fehlt'], ['onboarding', 'Neue Kunden im Onboarding'], ['aktionen', 'Letzte Aktionen']];
  const an = anpassenKnopf(KARTEN, STANDARD_AUS), zeige = (id, el) => aus.has(id) ? '' : el;
  return h('div', {}, kopf('Übersicht', an.knopf), an.panel, zeige('top3', heuteZuerstKarte(heute, sys, fw)), zeige('prio', prioritaetenKarte(heute, sys, fw)), zeige('betrieb', sys && sys.ampel ? betriebsKarte(sys) : ''), zeige('system', sys ? systemKarte(sys) : ''), zeige('fruehwarnung', fw ? fruehwarnKarte(fw) : ''), zeige('cockpit', cp ? cockpitKarte(cp) : ''), zeige('heute', heuteKarte(heute)),
    zeige('zahlen', h('div', { class: 'zahlenblock' },
    h('div', { class: 'grid3' },
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Kunden gesamt'), h('b', {}, summe)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Aktiv'), h('b', {}, s.aktiv || 0)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Im Onboarding'), h('b', {}, s.onboarding || 0)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Monatlich (gebucht)'), h('b', {}, euro(d.monatlich_cent))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Referenzkunden (unbezahlt)'), h('b', {}, d.referenzkunden)),
      h('a', { class: 'card stat', href: '#belege', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Offene Rechnungen' + (d.rechnungen_ueberfaellig ? ' (' + d.rechnungen_ueberfaellig + ' überfällig)' : '')), h('b', {}, euro(d.rechnungen_offen_cent))),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Neue Anfragen'), h('b', {}, d.neue_anfragen)),
      h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, 'Uploads (7 Tage)'), h('b', {}, d.uploads_7d))),
    h('div', { class: 'grid3' },
      h('a', { class: 'card stat', href: '#postfach', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Nachrichten offen (' + d.zusammenarbeit.tickets_ungelesen + ' ungelesen)'), h('b', {}, d.zusammenarbeit.tickets_offen)),
      h('a', { class: 'card stat', href: '#freigaben', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Freigaben warten auf Kunden'), h('b', {}, d.zusammenarbeit.freigaben_wartend)),
      h('a', { class: 'card stat', href: '#aufgaben', style: 'text-decoration:none;color:inherit' }, h('span', { class: 'muted small' }, 'Aufgaben offen (' + d.zusammenarbeit.aufgaben_ueberfaellig + ' überfällig)'), h('b', {}, d.zusammenarbeit.aufgaben_offen))))),
    aus.has('avv') ? '' : d.avv_fehlt.length ? h('div', { class: 'card' }, h('h2', {}, 'AVV fehlt bei ' + d.avv_fehlt.length + (d.avv_fehlt.length === 1 ? ' Kunde' : ' Kunden')), h('p', { class: 'small muted' }, 'Ohne unterschriebenen Auftragsverarbeitungsvertrag sollten keine Kundendaten verarbeitet werden.'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Status', z => pill(z.status)]], d.avv_fehlt)) : '',
    aus.has('onboarding') ? '' : ob.length ? h('div', { class: 'card' }, h('h2', {}, 'Neue Kunden im Onboarding'), tabelle([['Nr.', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer)], ['Firma', z => z.firma], ['Fortschritt', z => z.fertig + ' von ' + z.gesamt]], ob)) : '',
    zeige('aktionen', h('div', { class: 'card' }, h('h2', {}, 'Letzte Aktionen'), tabelle([['Zeit', z => zeit(z.zeit)], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d.letzte_aktionen))));
};

export async function zeitachseKarte(kid) {
  const z = await sicherApi('/api/admin/kunden/' + kid + '/zeitachse');
  if (!z) return '';
  const zu = z.zustand, risikoKlasse = { hoch: 'bad', mittel: 'warn' }[zu.risiko] || 'ok';
  return h('div', { class: 'card' }, h('h2', {}, 'Zustand & Verlauf'),
    h('div', { class: 'row', style: 'flex-wrap:wrap;gap:8px' },
      h('span', { class: 'pill ' + risikoKlasse }, 'Risiko: ' + (zu.risiko || 'niedrig')),
      h('span', { class: 'pill ' + (zu.ueberfaellig ? 'bad' : '') }, 'Offen: ' + euro(zu.offen_cent) + (zu.ueberfaellig ? ' (überfällig)' : '')),
      h('span', { class: 'pill' }, 'Anfragen 30 Tage: ' + zu.anfragen_30d),
      h('span', { class: 'pill' }, 'Letzter Login: ' + (zu.letzter_login ? zeit(zu.letzter_login) : 'noch nie')),
      zu.aufgabe ? h('span', { class: 'pill warn' }, 'Nächste Aufgabe: ' + zu.aufgabe) : ''),
    h('div', { class: 'zeitachse' }, z.ereignisse.length ? z.ereignisse.map(e => h('div', { class: 'ev' }, h('b', {}, e.titel), ' ', h('span', { class: 'small muted' }, zeit(e.zeit)), e.text ? h('div', { class: 'small muted' }, e.text) : '')) : h('p', { class: 'muted' }, 'Noch keine Ereignisse.')));
}

const MONATE = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
const monat = (m) => MONATE[Number(String(m).slice(5, 7)) - 1];

export function cockpitKarte(c) {
  const R = c.reihe, jetzt = R[R.length - 1], vor = R[R.length - 2] || jetzt;
  const max = Math.max(1, ...R.map(r => r.umsatz_cent));
  const kachel = (t, w, extra, link) => h(link ? 'a' : 'div', { class: 'card stat', href: link, style: link ? 'text-decoration:none;color:inherit' : '' }, h('span', { class: 'muted small' }, t), h('b', {}, w), extra || '');
  const ziel = c.ziel_mrr_cent, pro = ziel ? Math.min(100, Math.round(c.mrr_cent / ziel * 100)) : 0;
  const zielKnopf = h('button', { class: 'btn sec small', onclick: async () => {
    const v = prompt('MRR-Ziel pro Monat in Euro (0 = kein Ziel):', ziel ? String(ziel / 100) : '');
    if (v === null) return;
    const cent = Math.round(parseFloat(String(v).replace(/\./g, '').replace(',', '.')) * 100);
    if (!Number.isFinite(cent) || cent < 0) { alert('Bitte eine Zahl eingeben.'); return; }
    try { await api('/api/admin/cockpit/ziel', { method: 'PUT', body: { mrr_cent: cent } }); zeige(); } catch (x) { alert(x.message); }
  } }, ziel ? 'Ziel ändern' : 'MRR-Ziel setzen');
  const t = c.trichter, stufen = [['Neue Leads (90 Tage)', t.gesamt], ['Bearbeitet', t.bearbeitet], ['Erreicht', t.erreicht], ['Gespräch/Angebot', t.gespraech], ['Kunde geworden', t.kunden]];
  const prog = c.prognose, summe = prog.reduce((a, p) => a + p.cent, 0), pmax = Math.max(1, ...prog.map(p => p.cent));
  return h('div', { class: 'card' }, h('h2', {}, 'Geschäftszahlen'),
    h('div', { class: 'grid3 dicht' },
      kachel('Zahlungseingang ' + monat(jetzt.monat), euro(jetzt.umsatz_cent), delta(jetzt.umsatz_cent, vor.umsatz_cent, true, euro), '#belege'),
      kachel('Neukunden ' + monat(jetzt.monat), jetzt.neukunden, delta(jetzt.neukunden, vor.neukunden), '#kunden'),
      kachel('Neue Leads ' + monat(jetzt.monat), jetzt.leads, delta(jetzt.leads, vor.leads), '#leads'),
      kachel('Kündigungen ' + monat(jetzt.monat), jetzt.kuendigungen, delta(jetzt.kuendigungen, vor.kuendigungen, false), '#kunden'),
      kachel('Offen / überfällig', euro(c.offen_cent), h('span', { class: 'small ' + (c.ueberfaellig_cent ? 'delta ab' : 'muted') }, euro(c.ueberfaellig_cent) + ' überfällig'), '#belege'),
      kachel('Kündigungsquote (90 Tage)', (c.churn_prozent !== null ? String(c.churn_prozent).replace('.', ',') : '0') + ' %', h('span', { class: 'small muted' }, c.kuendigungen_90d + ' Kündigungen · ' + c.aktiv + ' aktiv'))),
    h('div', { class: 'row', style: 'margin:6px 0 2px' }, h('div', { class: 'grow' }, h('h3', {}, 'Wiederkehrender Umsatz (MRR): ' + euro(c.mrr_cent) + (ziel ? ' von ' + euro(ziel) + ' (' + pro + ' %)' : '')), ziel ? h('div', { class: 'fortschritt', role: 'progressbar', 'aria-valuenow': pro, 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-label': 'Fortschritt zum MRR-Ziel' }, h('div', { style: 'width:' + pro + '%' })) : h('p', { class: 'small muted' }, 'Setze ein Ziel, dann siehst du hier den Fortschritt. Durchschnitt je Kunde: ' + euro(c.arpu_cent) + '.')), zielKnopf),
    h('div', { class: 'cols', style: 'margin-top:12px' },
      h('div', {}, h('h3', {}, 'Verkaufstrichter (Leads der letzten 90 Tage)'),
        h('div', { class: 'trichter' }, stufen.map(([n, w], i) => h('div', { class: 'stufe' }, h('span', {}, n), h('div', { class: 'bar', style: 'width:' + Math.max(1, Math.round(w / Math.max(1, t.gesamt) * 100)) * 2 + 'px' }), h('b', {}, w), i ? h('span', { class: 'small muted' }, stufen[i - 1][1] ? Math.round(w / stufen[i - 1][1] * 100) + ' %' : '–') : '')))),
      h('div', {}, h('h3', {}, 'Erwartete Zahlungseingänge (offene Rechnungen): ' + euro(summe)),
        h('div', { class: 'trichter' }, prog.map(p => h('div', { class: 'stufe' }, h('span', {}, p.name), h('div', { class: 'bar', style: 'width:' + Math.max(1, Math.round(p.cent / pmax * 100)) * 1.4 + 'px;' + (p.name === 'überfällig' ? 'background:#dc2626' : '') }), h('b', {}, euro(p.cent))))))),
    h('h3', { style: 'margin-top:14px' }, 'Zahlungseingang der letzten 12 Monate'),
    h('div', { class: 'balken', style: 'margin-bottom:22px' }, R.map(r => h('div', { style: 'height:' + Math.max(2, Math.round(r.umsatz_cent / max * 100)) + '%', title: monat(r.monat) + ': ' + euro(r.umsatz_cent) + ' · ' + r.neukunden + ' neu · ' + r.kuendigungen + ' gekündigt · ' + r.leads + ' Leads' }, h('span', {}, monat(r.monat))))));
}

/** Alles Dringende, nach Wichtigkeit sortiert (gemeinsame Quelle für „Heute zuerst“ und „Jetzt wichtig“). */
export function prioListe(heute, sys, fw) {
  const L = [];
  const add = (score, ton, kat, titel, text, link, knopf) => L.push({ score, ton, kat, titel, text, link, knopf });
  (sys && sys.probleme ? sys.probleme : []).forEach(p => add(100, 'bad', 'System', p, 'Betrieb', '#einstellungen', 'Ansehen'));
  heute.rechnungen.forEach(z => add(90, 'bad', 'Zahlung', z.firma, 'Rechnung ' + z.nummer + ' ist überfällig', () => erinnerungsDialog(undefined, z.id), 'Erinnerung prüfen'));
  (fw && fw.kunden ? fw.kunden : []).forEach(z => add(z.stufe === 'hoch' ? 85 : 50, z.stufe === 'hoch' ? 'bad' : 'warn', 'Kündigungsrisiko', z.firma, (z.gruende || [])[0] || 'Auffälliger Verlauf', '#kunde/' + z.id, 'Öffnen'));
  heute.nachrichten.forEach(z => add(80, 'warn', 'Nachricht', z.firma, z.betreff, '#postfach/' + z.id, 'Antworten'));
  heute.avv_fehlt.forEach(z => add(75, 'warn', 'Vertrag', z.firma, 'AVV fehlt', '#kunde/' + z.id, 'Öffnen'));
  heute.aufgaben.forEach(z => add(70, 'warn', 'Aufgabe', z.titel, 'fällig ' + datum(z.faellig_am), '#aufgaben', 'Öffnen'));
  heute.onboarding.forEach(z => add(65, 'warn', 'Onboarding', z.firma, 'hängt seit über 5 Tagen', '#kunde/' + z.id, 'Öffnen'));
  heute.freigaben.forEach(z => add(60, '', 'Freigabe', z.firma, z.titel + ' wartet seit über 3 Tagen', '#kunde/' + z.kunden_id, 'Öffnen'));
  heute.wiedervorlagen.forEach(z => add(55, '', 'Lead', z.firma, 'Wiedervorlage fällig' + (z.vertriebler ? ' · ' + z.vertriebler : ''), '#lead/' + z.id, 'Öffnen'));
  if (heute.leads_gesamt) add(40, '', 'Leads', heute.leads_gesamt + ' neue Leads', 'warten auf den ersten Kontakt', '#leads', 'Öffnen');
  L.sort((a, b) => b.score - a.score);
  return L;
}

const SPERRE = 'mk_prio_ausgeblendet', TAGE7 = 7 * 864e5;
const sperreLaden = () => { try { const o = JSON.parse(localStorage.getItem(SPERRE) || '{}'), jetzt = Date.now(); Object.keys(o).forEach(k => { if (o[k] < jetzt) delete o[k]; }); return o; } catch { return {}; } };
const prioSchluessel = (z) => z.kat + '|' + z.titel + '|' + z.text;

/** Die drei wichtigsten Dinge des Tages, groß und mit einem Knopf. */
export function heuteZuerstKarte(heute, sys, fw) {
  const aus = sperreLaden(), L = prioListe(heute, sys, fw).filter(z => !aus[prioSchluessel(z)]).slice(0, 3);
  const std = new Date().getHours(), gruss = std < 11 ? 'Guten Morgen' : std < 18 ? 'Guten Tag' : 'Guten Abend';
  return h('div', { class: 'card hero' }, h('h2', {}, gruss + '. Das ist heute am wichtigsten'),
    L.length ? h('div', { class: 'top3' }, L.map((z, i) => h('div', { class: 'top3karte ' + z.ton }, h('span', { class: 'top3nr', 'aria-hidden': 'true' }, i + 1), h('div', { class: 'pt' }, h('b', {}, z.titel), h('span', { class: 'small muted' }, z.kat + ' · ' + z.text)),
      typeof z.link === 'function' ? h('button', { class: 'btn small', onclick: z.link }, z.knopf) : h('a', { class: 'btn small', href: z.link }, z.knopf))))
      : h('p', { class: 'muted' }, 'Nichts Dringendes offen. Gute Gelegenheit für die ', h('a', { href: '#pipeline' }, 'Lead-Pipeline'), ' oder einen Anruf bei einem Bestandskunden. 🎉'));
}

/** Alles Dringende in einer Liste, nach Wichtigkeit sortiert. */
export function prioritaetenKarte(heute, sys, fw) {
  const L = prioListe(heute, sys, fw);
  // Ausblenden: gilt 7 Tage, nur in diesem Browser. Die Ursache bleibt bestehen, der Hinweis ist nur ruhiggestellt.
  const laden = sperreLaden;
  const sichern = (o) => { try { localStorage.setItem(SPERRE, JSON.stringify(o)); } catch { /* ohne Speicher gilt das Ausblenden nur bis zum Neuladen */ } };
  let aus = laden();
  const schluessel = prioSchluessel;
  const ul = h('ul', { class: 'prio' }), mehr = h('p', {}), zaehler = h('span', { class: 'badge', style: 'margin-left:8px' }), zurueck = h('p', { class: 'small' });
  let alle = false;
  const zeichnen = () => {
    const sichtbar = L.filter(z => !aus[schluessel(z)]), versteckt = L.length - sichtbar.length;
    zaehler.textContent = String(sichtbar.length); zaehler.hidden = !sichtbar.length;
    ul.replaceChildren(...(alle ? sichtbar : sichtbar.slice(0, 8)).map(z => h('li', {}, h('span', { class: 'punkt ' + z.ton, 'aria-hidden': 'true' }),
      h('div', { class: 'pt' }, h('b', {}, z.titel), h('span', { class: 'small muted' }, z.text)), h('span', { class: 'pill kat' }, z.kat),
      typeof z.link === 'function' ? h('button', { class: 'btn sec small', onclick: z.link }, z.knopf) : h('a', { class: 'btn sec small', href: z.link }, z.knopf),
      h('button', { class: 'btn sec small', title: 'Für 7 Tage ausblenden', 'aria-label': 'Hinweis „' + z.titel + '“ für 7 Tage ausblenden', onclick: () => { const k = schluessel(z); aus[k] = Date.now() + TAGE7; sichern(aus); zeichnen(); rueckgaengig('„' + z.titel + '“ für 7 Tage ausgeblendet.', () => { delete aus[k]; sichern(aus); zeichnen(); }); } }, 'Ausblenden'))));
    ul.hidden = !sichtbar.length;
    leer.hidden = !!sichtbar.length; leer.textContent = versteckt ? 'Alles Offene ist ausgeblendet. Nichts Neues dringend.' : 'Alles erledigt. Nichts Dringendes offen. 🎉';
    mehr.replaceChildren(sichtbar.length > 8 ? h('button', { class: 'btn sec small', onclick: () => { alle = !alle; zeichnen(); } }, alle ? 'Weniger anzeigen' : 'Alle ' + sichtbar.length + ' anzeigen') : '');
    zurueck.replaceChildren(versteckt ? h('span', {}, versteckt + ' ausgeblendet · ', h('button', { class: 'btn sec small', onclick: () => { aus = {}; sichern(aus); zeichnen(); } }, 'Wieder anzeigen')) : '');
  };
  const leer = h('p', { class: 'muted' });
  zeichnen();
  const ok = !sys || !sys.probleme || !sys.probleme.length;
  return h('div', { class: 'card' }, h('h2', {}, 'Jetzt wichtig', zaehler),
    ul, leer, mehr, zurueck,
    h('div', { class: 'gesund small muted' }, h('span', { class: 'pill ' + (ok ? 'ok' : 'bad') }, ok ? 'System in Ordnung' : 'System: Handlungsbedarf'),
      h('span', { class: 'pill ' + (heute.rechnungen.length ? 'bad' : 'ok') }, heute.rechnungen.length ? heute.rechnungen.length + ' Rechnungen überfällig' : 'Keine Rechnung überfällig'),
      h('span', { class: 'pill ' + ((fw && fw.kunden && fw.kunden.some(k => k.stufe === 'hoch')) ? 'bad' : 'ok') }, (fw && fw.kunden && fw.kunden.some(k => k.stufe === 'hoch')) ? 'Kündigungsrisiko' : 'Kein Kündigungsrisiko')));
}

const AMPEL_TXT = { ok: 'Alles in Ordnung', warn: 'Hinweise', bad: 'Handlungsbedarf', unbekannt: 'Noch keine Messwerte' };

/** Betriebs-Ampel: ein Blick, ob Server, Sicherungen, Zertifikat, Hintergrundjobs und Mailversand gesund sind. */
export function betriebsKarte(sys) {
  return h('div', { class: 'card' }, h('h2', {}, 'Betrieb ', h('span', { class: 'pill ' + ({ ok: 'ok', warn: 'warn', bad: 'bad' }[sys.gesamt] || '') }, AMPEL_TXT[sys.gesamt] || '')),
    h('div', { class: 'ampel' }, sys.ampel.map(p => h('div', { class: 'ap ' + p.status, title: p.detail }, h('span', { class: 'lampe', 'aria-hidden': 'true' }),
      h('div', {}, h('b', {}, p.titel), h('div', { class: 'small muted' }, p.detail))))));
}

export function systemKarte(s) {
  const st = s.status, ok = s.probleme.length === 0;
  const zeile = (t, w, schlecht) => h('div', { class: 'small', style: 'margin:2px 0' }, h('span', { class: 'muted' }, t + ': '), h('span', { style: schlecht ? 'color:var(--badfg);font-weight:600' : '' }, w));
  const std = (n) => n === null || n === undefined || n >= 9999 ? 'nie' : n < 1 ? 'vor weniger als 1 Stunde' : 'vor ' + n + ' Std.';
  return h('div', { class: 'card' }, h('h2', {}, 'Systemstatus ', h('span', { class: 'pill ' + (ok ? 'ok' : 'bad') }, ok ? 'alles in Ordnung' : s.probleme.length + (s.probleme.length === 1 ? ' Problem' : ' Probleme'))),
    ok ? '' : h('ul', { style: 'color:var(--badfg);margin:6px 0' }, s.probleme.map(p => h('li', {}, p))),
    st ? h('div', { class: 'row', style: 'gap:24px;align-items:flex-start' },
      h('div', {}, zeile('Letzte Sicherung', std(st.backup_stunden), st.backup_stunden > 36), st.offsite_aktiv ? zeile('Externe Sicherung', std(st.offsite_stunden), st.offsite_stunden > 36) : zeile('Externe Sicherung', 'nicht eingerichtet', true)),
      h('div', {}, zeile('Festplatte', st.platte_prozent + ' % belegt', st.platte_prozent >= 85), st.zertifikat_tage >= 0 ? zeile('Zertifikat', 'noch ' + st.zertifikat_tage + ' Tage gültig', st.zertifikat_tage < 14) : ''),
      h('div', {}, zeile('E-Mail-Versand', s.mail_eingerichtet ? 'eingerichtet' : 'fehlt', !s.mail_eingerichtet), zeile('KI-Schlüssel', s.ki_eingerichtet ? 'hinterlegt' : 'fehlt', false), zeile('Überwachung zuletzt', 'vor ' + st.alter_minuten + ' Min.', st.alter_minuten > 30)))
      : h('p', { class: 'small muted' }, 'Die Server-Überwachung hat noch keine Daten geliefert. Nach dem nächsten Server-Update (git pull, bash install.sh) erscheint sie hier automatisch.'));
}

export function fruehwarnKarte(d) {
  if (!d.kunden.length) return h('div', { class: 'card' }, h('h2', {}, 'Kunden-Frühwarnung'), h('p', { class: 'muted' }, 'Kein Kunde mit auffälligem Verlauf (' + d.geprueft + ' geprüft).'));
  return h('div', { class: 'card' }, h('h2', {}, 'Kunden-Frühwarnung'), h('p', { class: 'small muted' }, 'Kunden mit Anzeichen für eine Kündigung, aus Anmeldungen, Anfragen, Zahlungen und Zufriedenheit. Ein Anruf in dieser Woche hilft am meisten.'),
    tabelle([['Kunde', z => h('a', { href: '#kunde/' + z.id }, z.kundennummer + ' ' + z.firma)], ['Risiko', z => h('span', { class: 'pill ' + (z.stufe === 'hoch' ? 'bad' : 'warn') }, z.stufe + ' (' + z.punkte + ')')], ['Gründe', z => z.gruende.join(' ')]], d.kunden));
}

// ------------------------------------------------------------- Aufgaben
V.aufgaben = async () => {
  const f = new URLSearchParams((location.hash.split('?')[1] || '')), status = f.get('status') || 'offen';
  const liste = await api('/api/admin/aufgaben?status=' + status), m = h('div');
  const tab = (st, t) => h('a', { href: '#aufgaben?status=' + st, class: 'tab' + (status === st ? ' on' : '') }, t);
  const titel = h('input', { maxlength: 200, placeholder: 'Neue Aufgabe …' }), zu = h('input', { placeholder: 'Zuständig (leer = ich)' }), fa = h('input', { type: 'date' });
  const neu = async () => { try { await api('/api/admin/aufgaben', { method: 'POST', body: { titel: titel.value, zustaendig: zu.value || null, faellig_am: fa.value || null } }); zeige(); } catch (x) { melde(m, x.message); } };
  const setz = async (z, st) => { try { await api('/api/admin/aufgaben/' + z.id, { method: 'PATCH', body: { status: st } }); zeige(); } catch (x) { melde(m, x.message); } };
  const weg = async (z) => { if (!confirm('Aufgabe löschen?')) return; try { await api('/api/admin/aufgaben/' + z.id, { method: 'DELETE' }); zeige(); } catch (x) { melde(m, x.message); } };
  return h('div', {}, kopf('Aufgaben'), m,
    h('div', { class: 'card' }, h('div', { class: 'row' }, h('div', { class: 'grow' }, titel), zu, fa, h('button', { class: 'btn', onclick: neu }, 'Anlegen'))),
    h('div', { class: 'tabs' }, tab('offen', 'Offen'), tab('erledigt', 'Erledigt'), tab('alle', 'Alle')),
    h('div', { class: 'card' }, h('p', { class: 'small muted' }, 'Aufgaben mit „auto“ legt das System selbst an, z. B. bei unbeantworteten Nachrichten, wartenden Freigaben oder überfälligen Rechnungen.'),
      tabelle([['Aufgabe', z => (z.ueberfaellig ? '⚠ ' : '') + z.titel + (z.quelle === 'auto' ? ' (auto)' : '')], ['Kunde', z => z.kunden_id ? h('a', { href: '#kunde/' + z.kunden_id }, z.firma) : ''], ['Zuständig', z => z.zustaendig || ''], ['Fällig', z => z.faellig_am ? datum(z.faellig_am) : ''],
        ['', z => h('div', { class: 'row' }, z.ticket_id ? h('a', { class: 'btn sec small', href: '#postfach/' + z.ticket_id }, 'Nachricht') : '', z.status === 'offen' ? h('button', { class: 'btn small', onclick: () => setz(z, 'erledigt') }, 'Erledigt') : h('button', { class: 'btn sec small', onclick: () => setz(z, 'offen') }, 'Wieder öffnen'), z.quelle === 'manuell' ? h('button', { class: 'btn bad small', onclick: () => weg(z) }, 'Löschen') : '')]], liste, 'Keine Aufgaben.')));
};

// ------------------------------------------------------------- Kennzahlen
V.kennzahlen = async () => {
  const z = await api('/api/admin/kennzahlen'), st = (t, w, link) => h(link ? 'a' : 'div', { class: 'card stat', href: link, style: link ? 'text-decoration:none;color:inherit' : '' }, h('span', { class: 'muted small' }, t), h('b', {}, w));
  const hh = (v) => v === null || v === undefined ? '–' : String(v).replace('.', ',') + ' h';
  return h('div', { class: 'stack' }, kopf('Kennzahlen'),
    h('div', { class: 'grid3' }, st('Nachrichten offen', z.tickets_offen, '#postfach'), st('davon ungelesen', z.tickets_ungelesen, '#postfach'), st('überfällig', z.tickets_ueberfaellig, '#postfach'),
      st('Freigaben warten', z.freigaben_wartend, '#freigaben'), st('Aufgaben offen', z.aufgaben_offen, '#aufgaben'), st('Aufgaben überfällig', z.aufgaben_ueberfaellig, '#aufgaben')),
    h('div', { class: 'card' }, h('h2', {}, 'Reaktionsgeschwindigkeit (90 Tage)'), h('div', { class: 'grid3' }, st('Erste Antwort im Schnitt', hh(z.antwortzeit_h)), st('Bis erledigt im Schnitt', hh(z.erledigungszeit_h)), st('Freigabe-Dauer im Schnitt', hh(z.freigabedauer_h)))),
    h('div', { class: 'card' }, h('h2', {}, 'Zufriedenheit (90 Tage)'), h('div', { class: 'grid3' }, st('Bewertungen', z.bewertungen), st('Durchschnitt (0–10)', z.bewertung_durchschnitt === null ? '–' : String(z.bewertung_durchschnitt).replace('.', ',')), st('NPS', z.nps === null ? '–' : z.nps)),
      h('p', { class: 'small muted' }, 'NPS = Anteil Promoter (9–10) minus Anteil Kritiker (0–6), in Prozentpunkten. Über 0 ist gut, über 50 sehr gut.')),
    h('div', { class: 'card' }, h('h2', {}, 'Pro Kunde'), tabelle([['Kunde', c => h('a', { href: '#kunde/' + c.id }, c.firma)], ['Status', c => pill(c.status)], ['Nachrichten offen', c => c.tickets_offen], ['Freigaben wartend', c => c.freigaben_wartend], ['Bewertung (180 T.)', c => c.bewertung === null ? '–' : String(c.bewertung).replace('.', ',')], ['Letzte Aktivität', c => c.letzte_aktivitaet ? zeit(c.letzte_aktivitaet) : '–']], z.kunden)),
    z.kommentare.length ? h('div', { class: 'card' }, h('h2', {}, 'Kommentare von Kunden'), tabelle([['Kunde', c => c.firma], ['Punkte', c => c.punkte], ['Kommentar', c => c.kommentar], ['Datum', c => zeit(c.erstellt_am)]], z.kommentare)) : '');
};

