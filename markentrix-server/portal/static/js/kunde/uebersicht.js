import { h, api, melde, ladeAnsicht, anpassenKnopf, ausgeblendetSet, delta as vormonat } from '../common.js';
import { start, hat, V, karten } from './kern.js';

/** Reise-Karte: Phasen von „Start“ bis „Live“ mit Haken, aktueller Phase und den Schritten darunter. */
function startKarte(sl) {
  if (!sl.aktiv) return '';
  const pct = sl.gesamt ? Math.round(100 * sl.fertig / sl.gesamt) : 0, phasen = (sl.phasen || []).filter(p => !p.leer);
  const zeile = (p) => h('div', { class: 'row', style: 'padding:6px 0;border-bottom:1px solid var(--line)' },
    h('span', { style: 'width:22px', 'aria-hidden': 'true' }, p.fertig ? '✅' : '⬜'), h('span', { class: 'grow' + (p.fertig ? ' muted' : '') }, p.titel, h('span', { class: 'sr-only' }, p.fertig ? ' (erledigt)' : ' (offen)')),
    p.seite ? h('a', { class: 'btn small', href: '#' + p.seite }, p.aktion) : '');
  const schritte = phasen.map((ph, i) => h('li', { class: 'reise-schritt ' + (ph.erledigt ? 'fertig' : ph.schluessel === sl.aktuelle_phase ? 'aktuell' : ''), ...(ph.schluessel === sl.aktuelle_phase ? { 'aria-current': 'step' } : {}) },
    h('span', { class: 'reise-punkt', 'aria-hidden': 'true' }, ph.erledigt ? '✓' : String(i + 1)), h('b', {}, ph.titel), h('span', { class: 'small muted' }, ph.fertig + ' von ' + ph.gesamt)));
  const aktuell = phasen.find(p => p.schluessel === sl.aktuelle_phase);
  const inPhase = (k) => sl.punkte.filter(p => p.phase === k);
  return h('div', { class: 'card' }, h('h2', {}, 'Dein Start bei Markentrix'),
    h('p', { class: 'small muted' }, sl.fertig + ' von ' + sl.gesamt + ' Schritten erledigt. Wir kümmern uns um die meisten, ein paar brauchen deine Hilfe.'),
    sl.am_zug ? h('p', { class: 'small' }, sl.am_zug === 'kunde' ? '👉 Gerade bist du am Zug: bitte erledige die markierten Schritte, dann geht es sofort weiter.' : '⏳ Gerade ist Markentrix am Zug. Du musst nichts tun, wir melden uns bei Rückfragen.') : '',
    h('div', { class: 'fortschritt', role: 'progressbar', 'aria-valuenow': String(pct), 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-label': 'Fortschritt beim Start' }, h('div', { style: 'width:' + pct + '%' })),
    h('ol', { class: 'reise' }, schritte),
    aktuell ? h('div', {}, h('h3', {}, 'Jetzt dran: ' + aktuell.titel), inPhase(aktuell.schluessel).map(zeile)) : h('p', {}, 'Alle Schritte sind erledigt. 🎉'),
    phasen.filter(p => p.erledigt).length ? h('details', { style: 'margin-top:10px' }, h('summary', { class: 'small muted' }, 'Schon erledigt anzeigen'), phasen.filter(p => p.erledigt).map(ph => h('div', {}, h('h3', {}, ph.titel), inPhase(ph.schluessel).map(zeile)))) : '');
}

/** „Dein Monat mit Markentrix“: was das Team und die Assistenten diesen Monat geleistet haben, plus der nächste Schritt. */
function wertKarte(w, z, sl) {
  const MON = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
  const name = MON[Number(w.monat.slice(5, 7)) - 1];
  const schritte = [];
  (sl.punkte || []).filter(p => !p.fertig && p.seite).slice(0, 2).forEach(p => schritte.push([p.titel, 'Aus deiner Startliste.', '#' + p.seite]));
  if (z.freigaben_wartend) schritte.push([z.freigaben_wartend + (z.freigaben_wartend === 1 ? ' Freigabe wartet' : ' Freigaben warten') + ' auf deine Entscheidung', 'Sobald du freigibst, geht es weiter.', '#freigaben']);
  if (z.wartet_auf_dich) schritte.push([z.wartet_auf_dich + (z.wartet_auf_dich === 1 ? ' Nachricht wartet' : ' Nachrichten warten') + ' auf deine Antwort', 'Das Team braucht eine Rückmeldung von dir.', '#nachrichten']);
  const offen = w.anfragen.jetzt - w.anfragen.bearbeitet;
  if (hat('anfragen_termine') && offen > 0) schritte.push([offen + (offen === 1 ? ' Anfrage ist' : ' Anfragen sind') + ' noch nicht bearbeitet', 'Schnelle Antworten erhöhen die Abschlusschance.', '#anfragen']);
  const kachel = (titel, wert, vergleich, extra) => h('div', {}, h('span', { class: 'small muted' }, titel), h('b', {}, wert), vergleich, extra ? h('span', { class: 'small muted', style: 'display:block' }, extra) : '');
  const leer = !w.anfragen.jetzt && !w.anrufe.jetzt && !w.anfragen.vorher && !w.anrufe.vorher;
  const text = 'Mein Monat mit Markentrix (' + name + '): ' + w.anfragen.jetzt + ' Anfragen, ' + w.anrufe.jetzt + ' vom Telefon-Assistenten angenommene Anrufe' + (w.termine.jetzt ? ', ' + w.termine.jetzt + ' Termine' : '') + '.';
  const kopieren = h('button', { class: 'btn sec small', onclick: async (e) => { try { await navigator.clipboard.writeText(text); e.target.textContent = 'Kopiert ✓'; } catch (x) { window.prompt('Zum Kopieren:', text); } } }, 'Zusammenfassung kopieren');
  return h('div', { class: 'card wert' }, h('h2', {}, 'Dein Monat mit Markentrix · ' + name),
    leer ? h('p', { class: 'muted' }, 'In diesem Monat gibt es noch keine Anfragen oder Anrufe. Sobald etwas eingeht, siehst du es hier.') :
      h('div', { class: 'kennz' },
        hat('anfragen_termine') ? kachel('Anfragen', w.anfragen.jetzt, vormonat(w.anfragen.jetzt, w.anfragen.vorher), w.anfragen.bearbeitet + ' bearbeitet') : '',
        hat('anfragen_termine') || w.anrufe.jetzt || w.anrufe.vorher ? kachel('Anrufe vom Telefon-Assistenten', w.anrufe.jetzt, vormonat(w.anrufe.jetzt, w.anrufe.vorher), w.anrufe.minuten ? w.anrufe.minuten + ' Minuten Gesprächszeit' : '') : '',
        w.termine.jetzt ? kachel('Termine', w.termine.jetzt, '', 'in diesem Monat') : '',
        z.antwortzeit_h !== null && z.antwortzeit_h !== undefined ? kachel('Antwortzeit des Teams', String(z.antwortzeit_h).replace('.', ',') + ' h', '', 'im Schnitt, 90 Tage') : ''),
    h('h3', {}, 'Dein nächster Schritt'),
    schritte.length ? h('ul', { class: 'prio' }, schritte.map(([t, s, l]) => h('li', {}, h('span', { class: 'punkt warn', 'aria-hidden': 'true' }), h('div', { class: 'pt' }, h('b', {}, t), h('span', { class: 'small muted' }, s)), h('a', { class: 'btn small', href: l }, 'Los')))) : h('p', {}, 'Alles erledigt, es gibt gerade nichts, was du tun musst. ✅'),
    h('p', {}, kopieren));
}

V.uebersicht = async () => {
  const [z, sl, w] = await Promise.all([api('/api/kunde/kennzahlen'), api('/api/kunde/startliste'), api('/api/kunde/wert', { leise: true }).catch(() => null)]);
  const karte = (titel, zahl, text, link) => h('a', { class: 'card', href: link, style: 'text-decoration:none;color:inherit' }, h('h3', {}, titel), h('div', { class: 'stat' }, h('b', {}, zahl), h('span', { class: 'muted small' }, text)));
  const zusatz = [
    karte('Nachrichten', z.nachrichten_offen, z.wartet_auf_dich ? z.wartet_auf_dich + ' warten auf dich' : 'offen', '#nachrichten'),
    karte('Freigaben', z.freigaben_wartend, z.freigaben_wartend ? 'warten auf deine Entscheidung' : 'nichts offen', '#freigaben'),
    karte('Anfragen', z.anfragen_30d, 'letzte 30 Tage', '#anfragen'),
    z.antwortzeit_h !== null ? h('div', { class: 'card' }, h('h3', {}, 'Antwortzeit des Teams'), h('div', { class: 'stat' }, h('b', {}, String(z.antwortzeit_h).replace('.', ',') + ' h'), h('span', { class: 'muted small' }, 'im Schnitt, letzte 90 Tage'))) : '',
  ];
  const ans = await ladeAnsicht(), aus = ausgeblendetSet(ans), an = anpassenKnopf([['wert', 'Dein Monat mit Markentrix'], ['zufriedenheit', 'Zufriedenheits-Abfrage'], ['karten', 'Kennzahlen-Kacheln']]);
  return h('div', { class: 'stack' }, h('div', { class: 'row' }, h('div', { class: 'grow' }), an.knopf), an.panel, w && !aus.has('wert') ? wertKarte(w, z, sl) : '', startKarte(sl), start.badges && start.badges.briefing && !sl.aktiv ? h('div', { class: 'card' }, h('h2', {}, 'Dein Briefing fehlt noch'), h('p', { class: 'small muted' }, 'Mit ein paar Angaben zu deinem Unternehmen können wir deine Website und Texte viel schneller fertigstellen. Es dauert etwa 10 Minuten.'), h('a', { class: 'btn', href: '#briefing' }, 'Jetzt ausfüllen')) : '', z.bewertung_faellig && !aus.has('zufriedenheit') ? zufriedenheitKarte() : '', aus.has('karten') ? '' : h('div', { class: 'grid3' }, karten(), zusatz));
};

function zufriedenheitKarte() {
  const m = h('div'), kom = h('input', { placeholder: 'Möchtest du uns etwas mitgeben? (freiwillig)', maxlength: 1000 }); let wahl = null;
  const knoepfe = Array.from({ length: 11 }, (_, i) => h('button', { class: 'btn sec small', type: 'button', onclick: (e) => { wahl = i; knoepfe.forEach(b => b.classList.remove('gewaehlt')); e.target.classList.add('gewaehlt'); } }, String(i)));
  return h('div', { class: 'card' }, h('h2', {}, 'Wie zufrieden bist du mit uns?'), h('p', { class: 'small muted' }, 'Von 0 (gar nicht) bis 10 (sehr). Dauert 10 Sekunden und hilft uns, besser zu werden.'), m,
    h('div', { class: 'row punkte' }, knoepfe), h('div', { class: 'row', style: 'margin-top:10px' }, h('div', { class: 'grow' }, kom),
      h('button', { class: 'btn', onclick: async () => { if (wahl === null) { melde(m, 'Bitte wähle eine Zahl.'); return; }
        try { await api('/api/kunde/zufriedenheit', { method: 'POST', body: { punkte: wahl, kommentar: kom.value } }); location.reload(); } catch (x) { melde(m, x.message); } } }, 'Senden')));
}
