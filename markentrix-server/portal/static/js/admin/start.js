import { h, api, datum, zeit, euro, melde, ladeAnsicht, anpassenKnopf } from '../common.js';
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
  const ans = await ladeAnsicht(), aus = new Set(ans.ausgeblendet || []);
  const cp = await sicherApi('/api/admin/cockpit');
  const KARTEN = [['system', 'Systemstatus'], ['fruehwarnung', 'Kunden-Frühwarnung'], ['cockpit', 'Geschäftszahlen'], ['heute', 'Heute zu tun'], ['zahlen', 'Kennzahlen-Kacheln'], ['avv', 'AVV fehlt'], ['onboarding', 'Neue Kunden im Onboarding'], ['aktionen', 'Letzte Aktionen']];
  const an = anpassenKnopf(KARTEN), zeige = (id, el) => aus.has(id) ? '' : el;
  return h('div', {}, kopf('Übersicht', an.knopf), an.panel, zeige('system', sys ? systemKarte(sys) : ''), zeige('fruehwarnung', fw ? fruehwarnKarte(fw) : ''), zeige('cockpit', cp ? cockpitKarte(cp) : ''), zeige('heute', heuteKarte(heute)),
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

export function cockpitKarte(c) {
  const max = Math.max(1, ...c.reihe.map(r => r.umsatz_cent)), mon = (m) => ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'][Number(String(m).slice(5, 7)) - 1];
  const kachel = (t, w, extra) => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, t), h('b', {}, w), extra ? h('span', { class: 'small muted' }, extra) : '');
  return h('div', { class: 'card' }, h('h2', {}, 'Geschäftszahlen'),
    h('div', { class: 'grid3' }, kachel('Monatlich wiederkehrend (MRR)', euro(c.mrr_cent), c.aktiv + ' aktive Kunden · ' + euro(c.arpu_cent) + ' je Kunde'),
      kachel('Kündigungen (90 Tage)', c.kuendigungen_90d, c.churn_prozent !== null ? String(c.churn_prozent).replace('.', ',') + ' % vom Bestand' : ''),
      kachel('Offen / überfällig', euro(c.offen_cent), euro(c.ueberfaellig_cent) + ' überfällig'),
      kachel('Neue Leads (30 Tage)', c.leads_30d, c.termine_30d + ' Gespräche gebucht')),
    h('h3', { style: 'margin-top:14px' }, 'Zahlungseingang der letzten 12 Monate'),
    h('div', { class: 'balken', style: 'margin-bottom:22px' }, c.reihe.map(r => h('div', { style: 'height:' + Math.max(2, Math.round(r.umsatz_cent / max * 100)) + '%', title: mon(r.monat) + ': ' + euro(r.umsatz_cent) + ' · ' + r.neukunden + ' neu · ' + r.kuendigungen + ' gekündigt · ' + r.leads + ' Leads' }, h('span', {}, mon(r.monat))))));
}


export function systemKarte(s) {
  const st = s.status, ok = s.probleme.length === 0;
  const zeile = (t, w, schlecht) => h('div', { class: 'small', style: 'margin:2px 0' }, h('span', { class: 'muted' }, t + ': '), h('span', { style: schlecht ? 'color:#991b1b;font-weight:600' : '' }, w));
  const std = (n) => n === null || n === undefined || n >= 9999 ? 'nie' : n < 1 ? 'vor weniger als 1 Stunde' : 'vor ' + n + ' Std.';
  return h('div', { class: 'card' }, h('h2', {}, 'Systemstatus ', h('span', { class: 'pill ' + (ok ? 'ok' : 'bad') }, ok ? 'alles in Ordnung' : s.probleme.length + (s.probleme.length === 1 ? ' Problem' : ' Probleme'))),
    ok ? '' : h('ul', { style: 'color:#991b1b;margin:6px 0' }, s.probleme.map(p => h('li', {}, p))),
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

