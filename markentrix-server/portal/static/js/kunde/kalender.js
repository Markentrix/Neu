import { h, api, melde, toast, dialog } from '../common.js';
import { V, zeige } from './kern.js';

const TZ = 'Europe/Berlin', WT = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
const PPM = 0.8;                                          // Pixel pro Minute
const feld = (label, el, tipp) => h('div', {}, h('label', {}, label), el, tipp ? h('div', { class: 'small muted' }, tipp) : '');
const heuteTag = () => new Date().toLocaleDateString('sv-SE', { timeZone: TZ });
const addTage = (tag, n) => { const d = new Date(tag + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const wochentag = (tag) => new Date(tag + 'T12:00:00Z').getUTCDay();
const montag = (tag) => addTage(tag, -((wochentag(tag) + 6) % 7));
const lokal = (iso) => { const s = new Date(iso).toLocaleString('sv-SE', { timeZone: TZ }); return { tag: s.slice(0, 10), min: Number(s.slice(11, 13)) * 60 + Number(s.slice(14, 16)) }; };
const uhr = (min) => String(Math.floor(min / 60)).padStart(2, '0') + ':' + String(min % 60).padStart(2, '0');
const hm = (t) => Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5));
const kurz = (tag) => WT[wochentag(tag)] + ' ' + tag.slice(8, 10) + '.' + tag.slice(5, 7) + '.';

/** Termin von Hand eintragen (Telefon, Laufkundschaft, Stammkunde), auch als Serie. */
export async function manuellDialog(vor, fertig) {
  const team = await api('/api/kunde/website-dienste/kalender-optionen');
  const m = h('div');
  const name = h('input', { maxlength: 120, 'aria-label': 'Name', value: vor.name || '' }), tel = h('input', { maxlength: 40, type: 'tel', 'aria-label': 'Telefon', value: vor.telefon || '' }), mail = h('input', { maxlength: 200, type: 'email', 'aria-label': 'E-Mail', value: vor.email || '' });
  const tag = h('input', { type: 'date', value: vor.tag || heuteTag(), 'aria-label': 'Datum' }), zeit = h('input', { type: 'time', value: vor.zeit || '09:00', 'aria-label': 'Uhrzeit' });
  const lz = h('select', { 'aria-label': 'Leistung' }, h('option', { value: '' }, '– keine Auswahl –'), team.leistungen.map(l => h('option', { value: l.id }, l.name + ' (' + l.dauer_min + ' Min.)')));
  const ma = h('select', { 'aria-label': 'Mitarbeiter' }, team.eigene ? '' : h('option', { value: '' }, team.mitarbeiter.length ? 'ohne Zuordnung' : 'Betrieb'), team.mitarbeiter.map(x => h('option', { value: x.id, selected: x.id === (team.eigene || vor.mitarbeiter) }, x.name)));
  const dauer = h('input', { type: 'number', min: 0, max: 720, placeholder: 'wie Leistung', 'aria-label': 'Dauer in Minuten' }), pers = h('input', { type: 'number', min: 1, max: 5, value: 1, 'aria-label': 'Personen' });
  const wdh = h('input', { type: 'number', min: 0, max: 51, value: 0, 'aria-label': 'Weitere Termine' }), abst = h('select', { 'aria-label': 'Abstand' }, [[7, 'jede Woche'], [14, 'alle 2 Wochen'], [21, 'alle 3 Wochen'], [28, 'alle 4 Wochen']].map(([v, n]) => h('option', { value: v }, n)));
  const notiz = h('textarea', { rows: 2, maxlength: 600, 'aria-label': 'Notiz' });
  const senden = async (e) => {
    const b = e.target; b.disabled = true; melde(m, '');
    try {
      const r = await api('/api/kunde/website-dienste/buchungen/manuell', { method: 'POST', body: { name: name.value, telefon: tel.value, email: mail.value, start: tag.value + 'T' + zeit.value, leistung_id: lz.value, dauer_min: Number(dauer.value) || 0, personen: Number(pers.value) || 1, mitarbeiter_id: ma.value, notiz: notiz.value, wiederholen: Number(wdh.value) || 0, abstand_tage: Number(abst.value) } });
      toast(r.angelegt.length + ' Termin' + (r.angelegt.length === 1 ? '' : 'e') + ' eingetragen' + (r.uebersprungen.length ? ', ' + r.uebersprungen.length + ' übersprungen (' + r.uebersprungen.map(u => u.wann).join(', ') + ')' : '') + '.', 'ok');
      d.zu(); fertig();
    } catch (x) { melde(m, x.message); b.disabled = false; }
  };
  const d = dialog('Termin eintragen', h('div', { class: 'stack' }, m,
    h('p', { class: 'small muted' }, 'Der Termin sperrt die Zeit wie eine Buchung über die Website. Es wird keine E-Mail verschickt.'),
    h('div', { class: 'form2' }, feld('Name *', name), feld('Telefon', tel), feld('E-Mail (optional)', mail, 'Nur wenn die Person Erinnerungen bekommen soll.'), feld('Datum', tag), feld('Uhrzeit', zeit), feld('Leistung', lz), feld('Mitarbeiter', ma),
      feld('Dauer in Minuten (optional)', dauer, 'Leer = Dauer der Leistung.'), feld('Personen', pers, 'Mehrere Personen nacheinander: Dauer mal Anzahl.'), feld('Weitere Termine (Serie)', wdh, '0 = nur dieser Termin.'), feld('Abstand', abst), feld('Notiz', notiz)),
    h('div', { class: 'row' }, h('button', { class: 'btn', onclick: senden }, 'Eintragen'), h('button', { class: 'btn sec', onclick: () => d.zu() }, 'Abbrechen'))));
}

function terminDialog(t, fertig) {
  const m = h('div');
  const absagen = async () => {
    const g = prompt('Kurze Begründung für die Absage (optional):', ''); if (g === null) return;
    try { const r = await api('/api/kunde/website-dienste/buchungen/' + t.id + '/ablehnen', { method: 'POST', body: { grund: g } }); toast('Abgesagt.' + (r.erstatten ? ' Bitte die Anzahlung zurückzahlen.' : ''), 'ok'); d.zu(); fertig(); } catch (x) { melde(m, x.message); }
  };
  const ergebnis = async (erg) => { try { await api('/api/kunde/website-dienste/buchungen/' + t.id + '/ergebnis', { method: 'POST', body: { ergebnis: erg } }); toast('Gespeichert.', 'ok'); d.zu(); fertig(); } catch (x) { melde(m, x.message); } };
  const s = lokal(t.start), e = lokal(t.ende);
  const d = dialog(t.name, h('div', { class: 'stack' }, m,
    h('p', {}, h('b', {}, kurz(s.tag) + ', ' + uhr(s.min) + ' bis ' + uhr(e.min) + ' Uhr'), t.status === 'reserviert' ? h('span', { class: 'pill warn', style: 'margin-left:6px' }, 'wartet auf Bestätigung') : ''),
    [t.leistung, t.mitarbeiter ? 'bei ' + t.mitarbeiter : '', t.manuell ? 'von Hand eingetragen' : ''].filter(Boolean).length ? h('p', { class: 'small' }, [t.leistung, t.mitarbeiter ? 'bei ' + t.mitarbeiter : '', t.manuell ? 'von Hand eingetragen' : ''].filter(Boolean).join(' · ')) : '',
    (t.telefon || t.email) ? h('p', { class: 'small' }, [t.telefon, t.email].filter(Boolean).join(' · ')) : '',
    t.anzahlung ? h('p', { class: 'small' }, 'Anzahlung ' + t.anzahlung.replace('.', ',') + ' € ', h('span', { class: 'pill ' + (t.anzahlung_erhalten ? 'ok' : 'warn') }, t.anzahlung_erhalten ? 'erhalten' : 'noch offen')) : '',
    t.kommt ? h('p', { class: 'small' }, h('span', { class: 'pill ok' }, 'hat „Ich komme“ bestätigt')) : '',
    t.notiz ? h('p', { class: 'small muted' }, t.notiz) : '',
    new Date(t.ende) < new Date() && t.status === 'gebucht' && !t.ergebnis ? h('div', { class: 'row' }, h('button', { class: 'btn', onclick: () => ergebnis('erschienen') }, 'Ist gekommen'), h('button', { class: 'btn sec', onclick: () => ergebnis('nicht_erschienen') }, 'Nicht erschienen')) : '',
    h('div', { class: 'row' }, h('button', { class: 'btn sec', onclick: absagen }, 'Termin absagen'), h('button', { class: 'btn', onclick: () => d.zu() }, 'Schließen'))));
}

/** Spalten nebeneinander liegender Termine: einfache Bahnen. */
function bahnen(liste) {
  const ende = []; let max = 1;
  const out = liste.slice().sort((a, b) => a.von - b.von).map(t => {
    let i = ende.findIndex(e => e <= t.von); if (i < 0) { i = ende.length; ende.push(0); }
    ende[i] = t.bis; max = Math.max(max, ende.length); return { ...t, bahn: i };
  });
  return { liste: out, n: max };
}

V.kalender = async () => {
  const stand = V.kalender.stand || (V.kalender.stand = { ansicht: window.innerWidth < 700 ? 'tag' : 'woche', tag: heuteTag() });
  const von = stand.ansicht === 'woche' ? montag(stand.tag) : stand.tag, tage = stand.ansicht === 'woche' ? 7 : 1;
  const r = await api('/api/kunde/website-dienste/kalender-ansicht?von=' + von + '&tage=' + tage);
  const neu = () => zeige();
  const spalten = [];
  const ohne = r.termine.filter(t => !t.mitarbeiter_id);
  if (stand.ansicht === 'tag' && r.mitarbeiter.length) {
    r.mitarbeiter.forEach(x => spalten.push({ titel: x.name, tag: von, mid: x.id, termine: r.termine.filter(t => t.mitarbeiter_id === x.id) }));
    if (ohne.length) spalten.push({ titel: 'ohne Zuordnung', tag: von, mid: '', termine: ohne });
  } else {
    for (let i = 0; i < tage; i++) { const tg = addTage(von, i); spalten.push({ titel: kurz(tg), tag: tg, mid: '', termine: r.termine.filter(t => lokal(t.start).tag === tg) }); }
  }
  // sichtbarer Zeitraum: Arbeitszeiten und Termine, mindestens 7 bis 19 Uhr
  let a = 7 * 60, b = 19 * 60;
  Object.values(r.arbeitszeit).forEach(p => Object.values(p).forEach(f => f.forEach(([x, y]) => { a = Math.min(a, hm(x) - hm(x) % 60); b = Math.max(b, Math.ceil(hm(y) / 60) * 60); })));
  r.termine.forEach(t => { a = Math.min(a, lokal(t.start).min - lokal(t.start).min % 60); b = Math.max(b, Math.ceil(lokal(t.ende).min / 60) * 60); });
  b = Math.min(b, 24 * 60);
  const hoehe = (b - a) * PPM;
  const planFuer = (mid) => r.arbeitszeit[mid] || r.arbeitszeit[''] || Object.values(r.arbeitszeit)[0] || {};
  const spalte = (sp) => {
    const wd = String(wochentag(sp.tag) || 7), fenster = (planFuer(sp.mid)[wd]) || [];
    const gesperrt = r.sperr.filter(s => s.tag === sp.tag && (!s.mitarbeiter_id || s.mitarbeiter_id === sp.mid));
    const col = h('div', { class: 'kal-spalte', style: 'position:relative;height:' + hoehe + 'px;border-left:1px solid var(--linie,#e5e7eb);min-width:' + (stand.ansicht === 'woche' ? 96 : 130) + 'px;flex:1;background:' + (fenster.length && !gesperrt.length ? 'transparent' : 'repeating-linear-gradient(45deg,rgba(128,128,128,.10),rgba(128,128,128,.10) 6px,transparent 6px,transparent 12px)'), role: 'group', 'aria-label': sp.titel });
    if (fenster.length && !gesperrt.length) { // außerhalb der Arbeitszeit grau
      let pos = a; [...fenster, [uhr(b), uhr(b)]].forEach(([x, y]) => { const s0 = Math.max(hm(x), a); if (s0 > pos) col.append(h('div', { style: 'position:absolute;left:0;right:0;top:' + (pos - a) * PPM + 'px;height:' + (s0 - pos) * PPM + 'px;background:rgba(128,128,128,.12)' })); pos = Math.max(pos, hm(y)); });
    }
    if (gesperrt.length) col.append(h('div', { class: 'small', style: 'position:absolute;top:4px;left:4px;right:4px;opacity:.8' }, gesperrt[0].grund || 'gesperrt'));
    col.addEventListener('click', (ev) => {
      if (ev.target !== col && !ev.target.style.background) return;
      const min = Math.round((ev.offsetY / PPM + a) / 15) * 15;
      manuellDialog({ tag: sp.tag, zeit: uhr(Math.min(min, 23 * 60)), mitarbeiter: sp.mid }, neu);
    });
    const { liste, n } = bahnen(sp.termine.map(t => ({ t, von: lokal(t.start).min, bis: lokal(t.ende).min })));
    liste.forEach(({ t, von: v, bis: e, bahn }) => {
      const top = (v - a) * PPM, hh = Math.max((e - v) * PPM, 22);
      col.append(h('button', { type: 'button', class: 'kal-termin', title: t.name + ' ' + uhr(v) + '–' + uhr(e), onclick: (ev) => { ev.stopPropagation(); terminDialog(t, neu); },
        style: 'position:absolute;top:' + top + 'px;height:' + hh + 'px;left:calc(' + (bahn * 100 / n) + '% + 2px);width:calc(' + (100 / n) + '% - 4px);overflow:hidden;text-align:left;padding:2px 4px;font-size:12px;line-height:1.2;border-radius:6px;border:1px solid var(--violet,#6D3FE0);background:' + (t.status === 'reserviert' ? 'rgba(245,158,11,.25)' : 'rgba(109,63,224,.18)') + ';color:inherit;cursor:pointer' },
      h('b', {}, uhr(v) + ' ' + t.name), h('div', {}, [t.leistung, stand.ansicht === 'woche' ? t.mitarbeiter : ''].filter(Boolean).join(' · '))));
    });
    return col;
  };
  const stunden = []; for (let m = a; m < b; m += 60) stunden.push(h('div', { style: 'height:' + 60 * PPM + 'px;font-size:11px;opacity:.7;border-top:1px solid var(--linie,#e5e7eb)' }, uhr(m)));
  const titel = stand.ansicht === 'woche' ? kurz(von) + ' bis ' + kurz(addTage(von, 6)) : WT[wochentag(von)] + ', ' + von.slice(8, 10) + '.' + von.slice(5, 7) + '.' + von.slice(0, 4);
  const spring = (n) => { stand.tag = addTage(stand.tag, n * (stand.ansicht === 'woche' ? 7 : 1)); neu(); };
  const bar = h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px' },
    h('button', { class: 'btn sec', onclick: () => spring(-1), 'aria-label': 'Zurück' }, '‹'), h('button', { class: 'btn sec', onclick: () => { stand.tag = heuteTag(); neu(); } }, 'Heute'), h('button', { class: 'btn sec', onclick: () => spring(1), 'aria-label': 'Weiter' }, '›'),
    h('b', {}, titel), h('span', { class: 'grow' }),
    h('button', { class: 'btn sec', 'aria-pressed': String(stand.ansicht === 'tag'), onclick: () => { stand.ansicht = 'tag'; neu(); } }, 'Tag'),
    h('button', { class: 'btn sec', 'aria-pressed': String(stand.ansicht === 'woche'), onclick: () => { stand.ansicht = 'woche'; neu(); } }, 'Woche'),
    h('button', { class: 'btn', onclick: () => manuellDialog({ tag: stand.tag }, neu) }, '+ Termin eintragen'));
  return h('div', { class: 'stack' }, h('div', { class: 'top' }, h('h1', {}, 'Kalender')),
    h('p', { class: 'small muted' }, 'Alle Termine von der Website und von Hand. Tippe auf einen freien Bereich, um dort einen Termin einzutragen, oder auf einen Termin für Details und Absage. Graue Flächen sind außerhalb der Arbeitszeit oder gesperrt.'),
    bar,
    h('div', { class: 'card', style: 'padding:8px' },
      h('div', { style: 'overflow-x:auto;max-width:100%' },
        h('div', { style: 'display:flex;min-width:' + (44 + spalten.length * (stand.ansicht === 'woche' ? 96 : 130)) + 'px' },
          h('div', { style: 'width:44px;flex:none;padding-top:26px' }, stunden),
          h('div', { style: 'display:flex;flex:1;flex-direction:column' },
            h('div', { style: 'display:flex' }, spalten.map(sp => h('div', { style: 'flex:1;min-width:' + (stand.ansicht === 'woche' ? 96 : 130) + 'px;text-align:center;font-weight:600;font-size:13px;height:26px' }, sp.titel))),
            h('div', { style: 'display:flex' }, spalten.map(spalte)))))));
};
