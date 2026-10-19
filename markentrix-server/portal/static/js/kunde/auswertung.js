import { h, api, sparkline } from '../common.js';
import { hat, tabelle, V } from './kern.js';

const delta = (neu, alt) => alt ? ((neu - alt) / alt * 100) : null;
const pfeil = (p) => p === null ? '' : (p >= 0 ? '▲ +' : '▼ ') + Math.round(p) + ' % zum Vormonat';
V.auswertung = async () => {
  const d = await api('/api/kunde/auswertung'), z = d.dieser, v = d.letzter;
  const karte = (titel, wert, alt, einheit = '') => h('div', { class: 'card stat' }, h('span', { class: 'muted small' }, titel), h('b', {}, String(wert) + einheit), alt !== undefined ? h('span', { class: 'small ' + (delta(wert, alt) >= 0 ? 'ok' : 'muted') }, pfeil(delta(wert, alt))) : '');
  const quellen = Object.entries(z.anfragen.nach_quelle);
  const maxq = Math.max(1, ...quellen.map(q => q[1]));
  const QN = { website: 'Website', email: 'E-Mail', telefon: 'Telefon', chat: 'Chat', whatsapp: 'WhatsApp', sonstiges: 'Sonstiges' };
  const ext = d.extern.length ? d.extern[d.extern.length - 1] : null;
  const anrufe = Object.values(z.anrufe).reduce((a, b) => a + b.anzahl, 0);
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Auswertung ' + d.monat_name), h('p', { class: 'small muted' }, 'Die Zahlen aktualisieren sich laufend. Den Vergleich zeigen wir gegen ' + d.vormonat_name + ' (ganzer Monat).')),
    h('div', { class: 'grid3' },
      karte('Anfragen', z.anfragen.gesamt, v.anfragen.gesamt), karte('Termine', z.termine.gesamt, v.termine.gesamt), karte('Anrufe', anrufe),
      karte('Fragen an den Agenten', z.chat_fragen), karte('Automatische Abläufe', z.automatische_ablaeufe), karte('Bewertungsbitten verschickt', z.bewertungsanfragen)),
    h('div', { class: 'card' }, h('h3', {}, 'Anfragen pro Woche (12 Wochen)'), sparkline(d.wochen.map(w => w.anfragen)), h('p', { class: 'small muted' }, 'Zuletzt: ' + d.wochen.map(w => w.anfragen).join(' · '))),
    h('div', { class: 'card' }, h('h3', {}, 'Anfragen und Termine pro Monat'), tabelle([['Monat', r => r.monat], ['Anfragen', r => r.anfragen], ['Termine', r => r.termine]], d.monate)),
    quellen.length ? h('div', { class: 'card' }, h('h3', {}, 'Woher kommen die Anfragen (' + d.monat_name + ')'), quellen.map(([q, n]) => h('div', { class: 'row', style: 'margin:6px 0' }, h('span', { style: 'width:110px' }, QN[q] || q), h('div', { style: 'height:14px;border-radius:7px;background:#8B5CF6;width:' + Math.max(4, n / maxq * 100) + '%;max-width:70%' }), h('b', {}, n)))) : '',
    h('div', { class: 'card' }, h('h3', {}, 'Website und Google'), ext ? h('div', { class: 'grid3' },
      ext.besucher !== null ? karte('Website-Besucher (' + ext.monat + ')', ext.besucher) : '', ext.google_aufrufe !== null ? karte('Google-Aufrufe', ext.google_aufrufe) : '',
      ext.google_sterne !== null ? karte('Google-Sterne', String(ext.google_sterne).replace('.', ','), undefined, ' ★ (' + (ext.google_bewertungen ?? '–') + ' Bewertungen)') : '') : h('p', { class: 'muted' }, 'Besucher- und Google-Zahlen trägt das Markentrix-Team monatlich ein. Sobald sie vorliegen, erscheinen sie hier.'),
      d.extern.length > 1 ? tabelle([['Monat', r => r.monat], ['Besucher', r => r.besucher ?? '–'], ['Google-Aufrufe', r => r.google_aufrufe ?? '–'], ['Sterne', r => r.google_sterne ?? '–'], ['Bewertungen', r => r.google_bewertungen ?? '–']], d.extern) : ''));
};

// ------------------------------------------------------------- Hilfe
const HILFE = [
  ['Start', 'Wie melde ich mich an und ändere mein Passwort?', 'Du meldest dich mit deiner E-Mail-Adresse und deinem Passwort an. Unter Einstellungen kannst du dein Passwort ändern und die Zwei-Faktor-Anmeldung einschalten. Das macht dein Konto deutlich sicherer.'],
  ['Start', 'Ich habe mein Passwort vergessen.', 'Klicke auf der Anmeldeseite auf „Passwort vergessen“ und folge dem Link in der E-Mail. Kommt keine E-Mail an, melde dich direkt bei uns, wir setzen dein Passwort zurück.'],
  ['Start', 'Was muss ich am Anfang tun?', 'Fülle das Briefing aus (Menü „Briefing“). Lade dein Logo und wichtige Unterlagen unter „Dokumente“ hoch. So können wir sofort loslegen.'],
  ['Zusammenarbeit', 'Wie erreiche ich das Markentrix-Team?', 'Schreib uns unter „Nachrichten“. Wähle eine Art (Frage, Auftrag, Änderungswunsch, Problem), beschreibe dein Anliegen und hänge bei Bedarf eine Datei an. Wir antworten dort und per E-Mail.'],
  ['Zusammenarbeit', 'Was sind Freigaben?', 'Bevor wir etwas veröffentlichen, zum Beispiel einen Beitrag oder Text, zeigen wir es dir unter „Freigaben“. Du kannst freigeben oder eine Änderung wünschen (mit kurzem Kommentar). Deine Entscheidung wird mit Datum und Uhrzeit festgehalten.'],
  ['Zusammenarbeit', 'Wo lade ich Logos, Verträge und Bilder hoch?', 'Unter „Dokumente“. Wähle die Art (zum Beispiel Logo oder Briefing) und die Datei. Erlaubt sind PDF, Bilder, Word, Excel, PowerPoint, Text, CSV und ZIP bis 8 MB. Bitte lade dort keine Passwörter hoch.'],
  ['Auswertung', 'Was zeigt die Auswertung?', 'Anfragen, Termine, Anrufe und die Arbeit des Agenten im laufenden Monat, im Vergleich zum Vormonat, dazu der Verlauf über 12 Wochen. Website-Besucher und Google-Zahlen trägt das Team monatlich ein.'],
  ['Auswertung', 'Wo finde ich den Monatsbericht?', 'Unter „Monatsberichte“. Dort steht für jeden Monat ein Bericht, den du als PDF herunterladen kannst.'],
  ['Funktionen', 'Wie bearbeite ich Anfragen und Termine?', 'Unter „Anfragen“ siehst du alle Anfragen und setzt den Status (zum Beispiel beantwortet oder erledigt). Unter „Termine“ findest du die kommenden Termine.', 'anfragen_termine'],
  ['Funktionen', 'Was kann der Assistent?', 'Du kannst dem Assistenten Fragen zu deinen Anfragen, Terminen und zum Portal stellen. Er gibt keine Rechts-, Steuer- oder Preisauskunft. Dafür schreib dem Team.', 'ki_chat'],
  ['Funktionen', 'Wie ändere ich Angebote, Öffnungszeiten oder „heute geschlossen“ auf meiner Website?', 'Unter „Wochenangebote“ lädst du eine Datei hoch und legst Angebote mit Preis, Events, Hinweise und „Heute geschlossen“ an. Mit „Aus Deutsch übersetzen“ füllt der Agent die anderen Sprachen aus. Bitte lies die Übersetzung kurz durch und speichere dann. Die Seite aktualisiert sich sofort.', 'wochenangebote'],
  ['Funktionen', 'Welche Zusatzfunktionen gibt es?', 'Unter „Automationen“ siehst du, was für dich aktiv ist. Mit „Anfragen“ bei einer Funktion erreicht uns deine Nachricht, wir melden uns mit Details und Preis.', 'automationen'],
  ['Konto', 'Wie lade ich Mitarbeiter ein?', 'Unter „Team“ (nur für Inhaber). Wähle die Rolle: Inhaber, Mitarbeiter oder Nur ansehen. Die Person bekommt einen Einladungslink.'],
  ['Konto', 'Wie ändere ich meine Anschrift oder E-Mail-Einstellungen?', 'Unter „Einstellungen“. Die Rechnungsanschrift änderst du als Inhaber selbst. Firmenname und Rechtsform ändern wir für dich: Schreib uns dazu unter Nachrichten.'],
  ['Konto', 'Wo finde ich Rechnungen und Angebote?', 'Unter „Angebote & Rechnungen“ (nur für Inhaber). Dort kannst du Angebote annehmen und Rechnungen als PDF laden.'],
  ['Datenschutz', 'Wo liegen meine Daten und kann ich sie mitnehmen?', 'Deine Daten liegen auf einem eigenen Server von Markentrix bei Hetzner. Den Auftragsverarbeitungsvertrag findest du unter „Datenschutz-Vertrag“. Bei Vertragsende bekommst du einen vollständigen Export deiner Daten.'],
];
V.hilfe = async () => {
  const such = h('input', { type: 'search', placeholder: 'Wonach suchst du? Zum Beispiel „Passwort“ oder „Angebot“', style: 'width:100%' }), box = h('div', { class: 'stack' });
  const zeichne = () => {
    const q = such.value.trim().toLowerCase();
    const liste = HILFE.filter(e => (!e[3] || hat(e[3])) && (!q || (e[1] + ' ' + e[2] + ' ' + e[0]).toLowerCase().includes(q)));
    box.replaceChildren(...(liste.length ? liste.map(e => h('details', { class: 'card hilfe' }, h('summary', {}, h('b', {}, e[1]), ' ', h('span', { class: 'pill' }, e[0])), h('p', {}, e[2]))) : [h('div', { class: 'card' }, h('p', { class: 'muted' }, 'Dazu haben wir nichts gefunden. Schreib uns einfach, wir helfen gern.'))]));
  };
  such.oninput = zeichne; zeichne();
  return h('div', { class: 'stack' }, h('div', { class: 'card' }, h('h2', {}, 'Hilfe'), h('p', { class: 'small muted' }, 'Antworten auf die häufigsten Fragen.'), such), box,
    h('div', { class: 'card' }, h('h3', {}, 'Nichts gefunden?'), h('p', { class: 'small muted' }, 'Wir helfen dir persönlich weiter.'), h('a', { class: 'btn', href: '#nachrichten' }, 'Nachricht an das Team')));
};

// ------------------------------------------------------------- Freigaben
export const FART = { social: 'Social Media', text: 'Text', angebot: 'Angebot', design: 'Design', website: 'Website', sonstiges: 'Sonstiges' };
