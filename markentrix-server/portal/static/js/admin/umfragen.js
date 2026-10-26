// Zufriedenheit: Auswertung der Umfragen, die Kunden im Portal beantworten (0 bis 10), mit NPS und Kommentaren.
import { h, api, datum, melde } from '../common.js';
import { V, fehler, knopf, kopf, tabelle } from './kern.js';

V.zufriedenheit = async () => {
  const d = await api('/api/admin/umfragen'), m = h('div'), link = h('input', { type: 'url', value: d.bewertungslink || '', placeholder: 'https://g.page/r/… (Link zur Google-Bewertung, freiwillig)', maxlength: 400, 'aria-label': 'Bewertungslink' });
  const kg = await api('/api/admin/kuendigungsgruende').catch(() => ({ gruende: [], gesamt: 0 }));
  const pillP = (p) => h('span', { class: 'pill ' + (p >= 9 ? 'ok' : p >= 7 ? 'warn' : 'bad') }, p + ' / 10');
  return h('div', { class: 'stack' }, kopf('Zufriedenheit', h('span', { class: 'pill ' + (d.nps === null ? '' : d.nps >= 30 ? 'ok' : d.nps >= 0 ? 'warn' : 'bad') }, d.nps === null ? 'noch keine Antworten' : 'NPS ' + d.nps)), m,
    h('div', { class: 'card' }, h('p', {}, h('b', {}, d.anzahl), ' Antworten, ', h('b', {}, d.offen), ' Umfragen warten noch auf eine Antwort. ', h('b', {}, d.mit_einwilligung), ' Kunden haben der Umfrage per Mail zugestimmt.'),
      h('p', { class: 'small muted' }, 'Gefragt wird 30 Tage nach dem Start und danach alle 90 Tage, im Portal auf der Startseite des Kunden. Eine Mail gibt es nur bei Zustimmung. Der NPS ist der Anteil der Begeisterten (9–10) minus der Anteil der Unzufriedenen (0–6). Bei 0–6 bekommst du sofort eine Mail.')),
    h('div', { class: 'card' }, h('h2', {}, 'Bewertungslink'), h('p', { class: 'small muted' }, 'Wer 9 oder 10 gibt, sieht danach diesen Link mit der Bitte um eine öffentliche Bewertung.'), link,
      h('p', {}, knopf('Speichern', async () => { try { await api('/api/admin/umfragen/einstellungen', { method: 'PUT', body: { bewertungslink: link.value.trim() } }); melde(m, 'Gespeichert.', 'ok'); } catch (x) { fehler(m, x); } }))),
    h('div', { class: 'card' }, h('h2', {}, 'Kündigungsgründe (letzte 12 Monate)'), kg.gesamt ? tabelle([['Hauptgrund', z => z.text], ['Anzahl', z => z.n]], kg.gruende) : h('p', { class: 'small muted' }, 'Noch keine Kündigung in den letzten 12 Monaten.'),
      h('p', { class: 'small muted' }, 'Kunden wählen den Hauptgrund beim Kündigen (freiwillig). Zurückgenommene Kündigungen zählen nicht.')),
    d.quartale.length ? h('div', { class: 'card' }, h('h2', {}, 'Verlauf'), tabelle([['Quartal', q => q.quartal], ['Antworten', q => q.n], ['Begeistert', q => q.foerderer], ['Unzufrieden', q => q.kritiker], ['NPS', q => q.nps]], d.quartale)) : '',
    h('div', { class: 'card' }, h('h2', {}, 'Antworten'), tabelle([['Kunde', a => h('a', { href: '#kunde/' + a.kunden_id }, a.firma)], ['Wert', a => pillP(a.punkte)], ['Kommentar', a => a.kommentar || '–'], ['Am', a => datum(a.beantwortet_am)]], d.antworten, 'Noch keine Antworten.')));
};
