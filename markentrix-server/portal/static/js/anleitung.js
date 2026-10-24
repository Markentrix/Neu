// Anleitung „So startest du“: App aufs Handy legen (Android/iPhone) und Schritt für Schritt durchs Portal, mit Bildern.
// Kunde und Vertrieb bekommen unterschiedliche Schritte. Die Bilder sind feste, eigene SVG-Grafiken (kein Fremdinhalt).
import { h, api, ladeAnsicht, installBereit, installStarten } from './common.js';

// ---------------------------------------------------------------- Bausteine für die Handy-Grafiken
const FARBE = { akzent: '#4F46E5', hell: '#eef0ff', linie: '#cbd0e6', text: '#1f2540', grau: '#e5e8f5', gelb: '#f59e0b', gruen: '#16a34a' };
const r = (x, y, w, hh, f = FARBE.hell, rx = 6, st = '') => `<rect x="${x}" y="${y}" width="${w}" height="${hh}" rx="${rx}" fill="${f}" ${st}/>`;
const t = (x, y, s, gr = 8, f = FARBE.text, w = 500, an = 'start') => `<text x="${x}" y="${y}" font-size="${gr}" fill="${f}" font-weight="${w}" text-anchor="${an}" font-family="Inter,system-ui,sans-serif">${s}</text>`;
const ring = (x, y, w, hh) => `<rect class="pulse" x="${x}" y="${y}" width="${w}" height="${hh}" rx="9" fill="none" stroke="${FARBE.gelb}" stroke-width="2.5"/>`;
const knopf = (x, y, w, s, f = FARBE.akzent, tf = '#fff') => r(x, y, w, 16, f, 8) + t(x + w / 2, y + 11, s, 7.5, tf, 700, 'middle');
const logo = (x, y, gr = 22) => r(x, y, gr, gr, FARBE.akzent, gr / 4) + t(x + gr / 2, y + gr * 0.7, 'M', gr * 0.6, '#fff', 700, 'middle');
const zeile = (x, y, w, f = FARBE.grau) => r(x, y, w, 5, f, 2.5);
const handy = (inhalt, beschr) => `<svg viewBox="0 0 160 270" role="img" aria-label="${beschr}" focusable="false"><rect x="8" y="4" width="144" height="262" rx="20" fill="#fff" stroke="#9aa3c7" stroke-width="3"/><rect x="62" y="10" width="36" height="5" rx="2.5" fill="${FARBE.linie}"/>${inhalt}</svg>`;
const punkte3 = (x, y) => [0, 1, 2].map(i => `<circle cx="${x}" cy="${y + i * 5}" r="1.6" fill="${FARBE.text}"/>`).join('');
const leiste = (aktiv, namen) => r(14, 236, 132, 24, '#fff', 0, `stroke="${FARBE.linie}"`) + namen.map((n, i) => t(14 + 66 / namen.length * (2 * i + 1), 252, n, 6.5, i === aktiv ? FARBE.akzent : '#6b7396', i === aktiv ? 700 : 500, 'middle')).join('');

const BILDER = {
  login: () => handy(logo(65, 40, 30) + t(80, 90, 'Anmelden', 10, FARBE.text, 700, 'middle') + r(26, 102, 108, 20, '#fff', 6, `stroke="${FARBE.linie}"`) + t(32, 115, 'E-Mail', 7.5, '#8a91b4') + r(26, 130, 108, 20, '#fff', 6, `stroke="${FARBE.linie}"`) + t(32, 143, 'Passwort', 7.5, '#8a91b4') + knopf(26, 162, 108, 'Anmelden'), 'Anmeldeseite des Portals'),
  'ch-menue': () => handy(r(14, 22, 132, 18, FARBE.hell, 9) + t(24, 34, 'portal.markentrix.de', 7) + punkte3(136, 27) + ring(124, 20, 22, 22)
    + r(66, 46, 80, 86, '#fff', 8, `stroke="${FARBE.linie}"`) + t(74, 62, 'Neuer Tab', 7.5) + t(74, 78, 'Verlauf', 7.5) + r(68, 84, 76, 18, '#fde68a', 6) + t(74, 96, 'App installieren', 7.5, FARBE.text, 700) + t(74, 116, 'Einstellungen', 7.5) + ring(66, 82, 80, 22)
    + zeile(22, 150, 100) + zeile(22, 162, 80) + r(22, 178, 116, 44, FARBE.hell, 8), 'Chrome mit geöffnetem Menü, „App installieren“ ist markiert'),
  'ch-install': () => handy(r(14, 22, 132, 18, FARBE.hell, 9) + t(24, 34, 'portal.markentrix.de', 7) + r(14, 44, 132, 192, '#cfd3e6', 0)
    + r(26, 96, 108, 74, '#fff', 10) + logo(34, 104, 20) + t(60, 118, 'Markentrix', 8, FARBE.text, 700) + t(34, 140, 'App installieren?', 7.5) + t(80, 160, 'Abbrechen', 7, '#6b7396', 500, 'middle') + r(88, 148, 42, 16, FARBE.akzent, 8) + t(109, 159, 'Installieren', 6.5, '#fff', 700, 'middle') + ring(86, 146, 46, 20), 'Bestätigungsfenster zum Installieren'),
  home: () => handy([0, 1, 2].map(i => [0, 1, 2].map(j => (i === 1 && j === 1) ? '' : r(24 + j * 40, 34 + i * 46, 28, 28, FARBE.grau, 8)).join('')).join('')
    + logo(64, 80, 28) + t(78, 120, 'Markentrix', 7, FARBE.text, 700, 'middle') + ring(58, 74, 40, 52) + r(24, 214, 112, 28, FARBE.hell, 12), 'Startbildschirm mit dem Markentrix-Symbol'),
  'sa-teilen': () => handy(r(14, 22, 132, 18, FARBE.hell, 9) + t(80, 34, 'portal.markentrix.de', 7, FARBE.text, 500, 'middle') + logo(60, 60, 40) + zeile(30, 118, 100) + zeile(30, 130, 80) + r(22, 150, 116, 50, FARBE.hell, 8)
    + r(14, 232, 132, 28, '#f6f7fb', 0) + `<path d="M80 238v14M74 243l6-6 6 6M72 247h-3v10h22v-10h-3" fill="none" stroke="${FARBE.akzent}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>` + ring(66, 232, 28, 28), 'Safari mit dem Teilen-Symbol unten'),
  'sa-liste': () => handy(r(14, 22, 132, 224, '#9aa3c7', 0) + r(14, 70, 132, 176, '#fff', 14) + t(24, 90, 'Markentrix', 8, FARBE.text, 700) + zeile(24, 98, 60)
    + t(24, 128, 'Kopieren', 7.5) + t(24, 148, 'Lesezeichen', 7.5) + r(18, 156, 124, 20, '#fde68a', 6) + t(24, 170, 'Zum Home-Bildschirm  ＋', 7.5, FARBE.text, 700) + t(24, 194, 'Drucken', 7.5) + ring(16, 154, 128, 24), 'Teilen-Menü mit „Zum Home-Bildschirm“'),
  'sa-hinzu': () => handy(r(14, 22, 132, 224, '#fff', 0) + t(24, 42, 'Abbrechen', 7.5, FARBE.akzent) + t(80, 42, 'Zum Home-Bildschirm', 6.5, FARBE.text, 700, 'middle') + t(136, 42, 'Hinzufügen', 7.5, FARBE.akzent, 700, 'end') + ring(92, 30, 52, 18)
    + logo(24, 64, 28) + r(58, 70, 76, 16, FARBE.hell, 5) + t(64, 81, 'Markentrix', 7.5) + zeile(24, 108, 110) + zeile(24, 120, 90), 'Dialog „Zum Home-Bildschirm“ mit „Hinzufügen“'),
  push: () => handy(r(20, 40, 120, 52, '#fff', 12, `stroke="${FARBE.linie}"`) + logo(28, 48, 22) + t(58, 62, 'Markentrix', 8, FARBE.text, 700) + t(58, 76, 'Neue Nachricht für dich', 7.5) + t(58, 87, 'jetzt', 6.5, '#6b7396')
    + r(26, 128, 108, 78, '#fff', 12, `stroke="${FARBE.linie}"`) + t(80, 148, 'Benachrichtigungen', 8, FARBE.text, 700, 'middle') + t(80, 160, 'zulassen?', 8, FARBE.text, 700, 'middle') + t(52, 196, 'Nicht jetzt', 7, '#6b7396', 500, 'middle') + r(84, 182, 44, 18, FARBE.akzent, 9) + t(106, 194, 'Zulassen', 7.5, '#fff', 700, 'middle') + ring(82, 180, 48, 22), 'Handy fragt, ob Benachrichtigungen erlaubt sein sollen, „Zulassen“ ist markiert'),
  // ---- Kunde
  heute: () => handy(t(22, 38, 'Heute', 11, FARBE.text, 700) + r(20, 48, 120, 62, FARBE.hell, 10) + t(28, 64, 'Dein nächster Schritt', 7, '#6b7396') + t(28, 78, 'Eine Freigabe wartet', 8, FARBE.text, 700) + knopf(28, 88, 70, 'Freigaben prüfen') + r(20, 118, 120, 34, '#fff', 8, `stroke="${FARBE.linie}"`) + t(28, 132, 'Anfragen: keine offen', 7.5) + zeile(28, 140, 60) + r(20, 160, 120, 34, '#fff', 8, `stroke="${FARBE.linie}"`) + t(28, 174, 'Termine heute: 1', 7.5) + zeile(28, 182, 70) + leiste(0, ['Heute', 'Anfragen', 'Termine', 'Menü']), 'Seite Heute mit nächstem Schritt'),
  freigabe: () => handy(t(22, 38, 'Freigaben', 11, FARBE.text, 700) + r(20, 48, 120, 120, '#fff', 10, `stroke="${FARBE.linie}"`) + t(28, 64, 'Instagram-Beitrag', 8, FARBE.text, 700) + r(28, 70, 40, 12, '#fef3c7', 6) + t(48, 79, 'wartet', 6.5, '#92400e', 600, 'middle') + r(28, 90, 104, 40, FARBE.hell, 6) + zeile(34, 98, 80) + zeile(34, 108, 60) + zeile(34, 118, 70)
    + knopf(28, 140, 46, 'Freigeben') + r(80, 140, 52, 16, '#fff', 8, `stroke="${FARBE.linie}"`) + t(106, 151, 'Änderung', 7, FARBE.text, 700, 'middle') + ring(26, 138, 50, 20) + leiste(-1, ['Heute', 'Anfragen', 'Termine', 'Menü']), 'Freigabe mit Knöpfen Freigeben und Änderung wünschen'),
  anfragen: () => handy(t(22, 38, 'Anfragen', 11, FARBE.text, 700) + [0, 1, 2].map(i => r(20, 48 + i * 46, 120, 40, '#fff', 8, `stroke="${FARBE.linie}"`) + t(28, 62 + i * 46, ['Familie Berger', 'Tischlerei Hahn', 'M. Schulz'][i], 7.5, FARBE.text, 700) + zeile(28, 70 + i * 46, 70) + (i === 0 ? knopf(98, 74, 36, 'Rückruf') : '')).join('') + ring(94, 72, 44, 20) + leiste(1, ['Heute', 'Anfragen', 'Termine', 'Menü']), 'Liste der Anfragen mit Rückruf-Knopf'),
  nachrichten: () => handy(t(22, 38, 'Nachrichten', 11, FARBE.text, 700) + r(20, 50, 90, 30, FARBE.hell, 10) + zeile(28, 60, 70) + zeile(28, 70, 50) + r(50, 90, 90, 30, FARBE.akzent, 10) + zeile(58, 100, 70, '#c7c9f5') + zeile(58, 110, 40, '#c7c9f5') + r(20, 130, 80, 22, FARBE.hell, 10) + zeile(28, 138, 56)
    + r(20, 196, 90, 20, '#fff', 10, `stroke="${FARBE.linie}"`) + t(28, 209, 'Nachricht …', 7, '#8a91b4') + knopf(114, 197, 26, 'Senden', FARBE.akzent) + ring(18, 194, 124, 24), 'Chat mit dem Markentrix-Team'),
  menue: () => handy(t(22, 38, 'Heute', 11, FARBE.text, 700) + r(20, 48, 120, 40, FARBE.hell, 10) + leiste(3, ['Heute', 'Anfragen', 'Termine', 'Menü']) + ring(110, 232, 36, 30)
    + r(30, 96, 100, 128, '#fff', 12, `stroke="${FARBE.linie}"`) + ['Freigaben', 'Dokumente', 'Auswertung', 'Rechnungen', 'Hilfe', 'Einstellungen'].map((s, i) => t(40, 114 + i * 18, s, 7.5)).join(''), 'Menü mit allen Bereichen'),
  // ---- Vertrieb
  anrufe: () => handy(t(22, 38, 'Heute anrufen', 10, FARBE.text, 700) + r(20, 46, 120, 8, FARBE.grau, 4) + r(20, 46, 36, 8, FARBE.akzent, 4) + r(20, 62, 120, 60, '#fff', 8, `stroke="${FARBE.linie}"`) + t(28, 76, '🔥 Kfz Müller', 8, FARBE.text, 700) + t(28, 86, 'Celle', 6.5, '#6b7396') + knopf(28, 96, 82, '📞 0511 123456') + ring(26, 94, 86, 20) + r(20, 130, 120, 40, '#fff', 8, `stroke="${FARBE.linie}"`) + t(28, 144, 'Friseur Lange', 7.5, FARBE.text, 700) + zeile(28, 152, 60) + leiste(0, ['Anrufe', 'Leads', 'Pipeline', 'Menü']), 'Anrufliste mit Telefon-Knopf'),
  ergebnis: () => handy(t(22, 38, 'Kfz Müller', 10, FARBE.text, 700) + t(22, 52, 'Wie ist es gelaufen?', 7.5, '#6b7396') + [['Nicht erreicht', 62], ['Gesprochen …', 86], ['Termin …', 110], ['Kein Interesse', 134]].map(([s, y], i) => r(22, Number(y), 116, 18, i === 1 ? '#fde68a' : '#fff', 9, `stroke="${FARBE.linie}"`) + t(80, Number(y) + 12, s, 7.5, FARBE.text, 700, 'middle')).join('') + ring(20, 84, 120, 22) + t(22, 176, 'Notiz', 7, '#6b7396') + r(22, 182, 116, 26, FARBE.hell, 6) + zeile(28, 190, 80) + knopf(22, 214, 116, 'Speichern'), 'Ergebnis eines Anrufs festhalten'),
  lead: () => handy(t(22, 38, 'Neuer Lead', 10, FARBE.text, 700) + [['Firma *', 50], ['Ansprechpartner', 82], ['Telefon', 114]].map(([s, y]) => t(22, Number(y), s, 6.5, '#6b7396') + r(22, Number(y) + 4, 116, 18, '#fff', 6, `stroke="${FARBE.linie}"`)).join('') + knopf(22, 150, 116, 'Lead speichern') + ring(20, 148, 120, 20) + zeile(22, 184, 100) + zeile(22, 194, 80), 'Formular für einen neuen Lead'),
  pipeline: () => handy(t(22, 38, 'Pipeline', 10, FARBE.text, 700) + [['Neu', 3], ['Gespräch', 2], ['Angebot', 1]].map(([s, n], i) => r(18 + i * 43, 48, 40, 140, FARBE.hell, 8) + t(38 + i * 43, 60, s, 6.2, FARBE.akzent, 700, 'middle') + Array.from({ length: Number(n) }, (_, k) => r(21 + i * 43, 68 + k * 30, 34, 24, '#fff', 5, `stroke="${FARBE.linie}"`)).join('')).join('') + ring(104, 64, 42, 100) + leiste(2, ['Anrufe', 'Leads', 'Pipeline', 'Menü']), 'Pipeline mit drei Spalten'),
  angebot: () => handy(t(22, 38, 'Angebotsanfrage', 10, FARBE.text, 700) + r(22, 50, 116, 100, '#fff', 8, `stroke="${FARBE.linie}"`) + t(30, 66, 'Tischlerei Hahn', 8, FARBE.text, 700) + zeile(30, 76, 70) + zeile(30, 86, 90) + t(30, 112, 'Paket: Website + KI', 7.5) + t(130, 140, '€', 16, FARBE.akzent, 700, 'end') + knopf(22, 160, 116, 'Anfrage senden') + ring(20, 158, 120, 20) + r(22, 188, 116, 24, '#dcfce7', 8) + t(30, 203, 'Status: angesehen', 7.5, '#166534', 700), 'Angebot bei Markentrix anfragen'),
  zahlen: () => handy(t(22, 38, 'Meine Zahlen', 10, FARBE.text, 700) + [['Anrufe', '28/40', 0], ['Erreicht', '11', 1], ['Termine', '4', 0], ['Neue Kunden', '1', 1]].map(([s, v], i) => r(20 + (i % 2) * 60, 50 + Math.floor(i / 2) * 50, 56, 44, FARBE.hell, 8) + t(26 + (i % 2) * 60, 64 + Math.floor(i / 2) * 50, s, 6.5, '#6b7396') + t(26 + (i % 2) * 60, 84 + Math.floor(i / 2) * 50, v, 13, FARBE.akzent, 700)).join('') + r(20, 160, 120, 8, FARBE.grau, 4) + r(20, 160, 84, 8, FARBE.akzent, 4) + t(20, 182, 'Wochenziel: 40 Anrufe', 7, '#6b7396'), 'Kennzahlen der Woche'),
  provision: () => handy(t(22, 38, 'Provisionen', 10, FARBE.text, 700) + [['Mai', 52], ['Juni', 74], ['Juli', 38]].map(([s, v], i) => r(24 + i * 38, 150 - Number(v), 28, Number(v), i === 1 ? FARBE.akzent : '#a5b4fc', 5) + t(38 + i * 38, 164, s, 6.5, '#6b7396', 500, 'middle')).join('')
    + [['Kfz Müller', 'berechnet'], ['Hahn GmbH', 'ausgezahlt']].map(([s, st], i) => r(20, 176 + i * 28, 120, 24, '#fff', 8, `stroke="${FARBE.linie}"`) + t(28, 192 + i * 28, s, 7.5, FARBE.text, 700) + t(132, 192 + i * 28, st, 6.5, st === 'ausgezahlt' ? '#166534' : '#92400e', 700, 'end')).join(''), 'Provisionen pro Monat und Kunde'),
  leitfaden: () => handy(t(22, 38, 'Leitfaden', 10, FARBE.text, 700) + [['1', 'Begrüßung'], ['2', 'Bedarf erfragen'], ['3', 'Nutzen zeigen'], ['4', 'Termin vorschlagen']].map(([n, s], i) => `<circle cx="32" cy="${62 + i * 32}" r="9" fill="${FARBE.akzent}"/>` + t(32, 65 + i * 32, n, 8, '#fff', 700, 'middle') + t(48, 65 + i * 32, s, 8, FARBE.text, 600) + zeile(48, 71 + i * 32, 70)).join(''), 'Gesprächsleitfaden'),
};

/** Fertige Grafik als Element (innerHTML nur mit den festen Zeichenketten oben). */
export function bild(name) {
  const b = h('span', { class: 'handybild' });
  b.innerHTML = BILDER[name]();
  return b;
}

// ---------------------------------------------------------------- Inhalte
const INSTALL = {
  android: [
    ['login', 'Portal in Chrome öffnen', 'Öffne das Portal in Google Chrome und melde dich an. Bitte nicht in Samsung Internet, Opera oder einem anderen Browser: Dort angelegte Apps blockiert Google Play Protect teils als „unsicher“.'],
    ['ch-menue', 'Menü ⋮ öffnen, „App installieren“ wählen', 'Oben rechts auf die drei Punkte tippen. Steht dort „App installieren“, tippe darauf. Alternativ „Zum Startbildschirm hinzufügen“.'],
    ['ch-install', 'Mit „Installieren“ bestätigen', 'Chrome fragt noch einmal nach. Tippe auf „Installieren“. Das dauert ein paar Sekunden.'],
    ['home', 'Fertig', 'Das Markentrix-Symbol liegt jetzt auf deinem Startbildschirm. Ab jetzt öffnest du das Portal wie jede andere App. Updates passieren von selbst.'],
    ['push', 'Benachrichtigungen erlauben', 'Beim ersten Öffnen der App fragt dich Markentrix, ob du Benachrichtigungen aufs Handy bekommen möchtest. Tippe auf „Ja, benachrichtigen“ und danach beim Handy auf „Zulassen“. So erfährst du sofort, wenn etwas Wichtiges passiert. Du kannst das jederzeit unter „Konto“ bzw. „Einstellungen“ → „App & Benachrichtigungen“ ändern.'],
  ],
  iphone: [
    ['login', 'Portal in Safari öffnen', 'Öffne das Portal in Safari (nicht in Chrome oder in einer anderen App) und melde dich an.'],
    ['sa-teilen', 'Teilen-Symbol antippen', 'Unten in der Mitte auf das Symbol mit dem Pfeil nach oben tippen.'],
    ['sa-liste', '„Zum Home-Bildschirm“ wählen', 'In der Liste etwas nach unten wischen, bis „Zum Home-Bildschirm“ erscheint, und darauf tippen.'],
    ['sa-hinzu', '„Hinzufügen“ tippen', 'Oben rechts auf „Hinzufügen“ tippen. Der Name „Markentrix“ passt so.'],
    ['home', 'Fertig', 'Das Symbol liegt auf dem Home-Bildschirm. Erst jetzt, in der App, kannst du auch Benachrichtigungen einschalten (Konto → App & Benachrichtigungen).'],
    ['push', 'Benachrichtigungen erlauben', 'Öffne die App vom Home-Bildschirm (nicht aus Safari). Dort fragt dich Markentrix, ob du Benachrichtigungen aufs Handy bekommen möchtest. Tippe auf „Ja, benachrichtigen“ und danach beim Handy auf „Zulassen“. So erfährst du sofort, wenn etwas Wichtiges passiert. Du kannst das jederzeit unter „Konto“ bzw. „Einstellungen“ → „App & Benachrichtigungen“ ändern.'],
  ],
};

/** Kunde: was das Portal kann. `hat` prüft, ob der Kunde ein Modul gebucht hat. */
function schritteKunde(hat) {
  return [
    ['heute', 'Heute: das Wichtigste zuerst', 'Hier steht, was jetzt dran ist: offene Freigaben, neue Anfragen, Termine. Was hier nicht steht, ist erledigt.', '#heute', 'Zu „Heute“'],
    ['freigabe', 'Freigaben: du hast das letzte Wort', 'Bevor wir etwas veröffentlichen, zeigen wir es dir. Du tippst auf „Freigeben“ oder auf „Änderung wünschen“ und schreibst kurz, was anders sein soll. Das geht auch direkt über den Link in der E-Mail, ganz ohne Anmeldung. Datum, Uhrzeit und dein Name werden festgehalten.', '#freigaben', 'Zu den Freigaben'],
    hat('anfragen_termine')
      ? ['anfragen', 'Anfragen und Termine', 'Neue Anfragen von deiner Website oder per Telefon landen hier. Ruf zurück, solange sie frisch sind, das entscheidet oft über den Auftrag.', '#anfragen', 'Zu den Anfragen']
      : null,
    ['nachrichten', 'Nachrichten: direkter Draht zu uns', 'Fragen, Wünsche, Änderungen? Schreib uns hier. Du bekommst die Antwort im Portal und per E-Mail. Dateien und Bilder kannst du anhängen.', '#nachrichten', 'Nachricht schreiben'],
    ['menue', 'Menü: alles andere', 'Unten rechts auf „Mehr“ tippen: Dokumente, Auswertung, Rechnungen, Team, Hilfe und Einstellungen.', '#hilfe', 'Zur Hilfe'],
  ].filter(Boolean);
}

/** Vertrieb: der Vertriebler sieht mehr als der Kunde (Leads, Pipeline, Angebotsanfragen, Provisionen). */
function schritteVertrieb() {
  return [
    ['anrufe', 'Heute anrufen: deine Liste für den Tag', 'Jeden Morgen steht hier, wen du anrufen sollst: heiße Leads zuerst, danach die Wiedervorlagen. Mit dem 📞-Knopf rufst du direkt vom Handy an. Oben siehst du dein Wochenziel.', '#heute', 'Zu „Heute anrufen“'],
    ['ergebnis', 'Nach dem Anruf: Ergebnis festhalten', 'Tippe einen Knopf: „Nicht erreicht“, „Gesprochen …“, „Termin …“ oder „Kein Interesse“. Bei „Gesprochen“ und „Termin“ kannst du eine Notiz schreiben und eine Wiedervorlage setzen. So geht kein Kontakt verloren.', '#heute', 'Zu „Heute anrufen“'],
    ['lead', 'Neuen Lead eintragen', 'Unter „Meine Leads“ legst du neue Kontakte an. Bitte nur Kontakte eintragen, bei denen eine geschäftliche Ansprache zulässig ist.', '#leads', 'Zu „Meine Leads“'],
    ['pipeline', 'Pipeline: wo steht welcher Kontakt', 'Die Spalten zeigen, wer neu ist, mit wem du sprichst und wo ein Angebot läuft. So siehst du sofort, wo du nachfassen musst.', '#pipeline', 'Zur Pipeline'],
    ['angebot', 'Angebot anfragen', 'Will ein Kontakt ein Angebot, stellst du unter „Angebotsanfragen“ eine Anfrage an Markentrix. Dort siehst du auch den Stand: gesendet, angesehen, angenommen.', '#angebote', 'Zu den Angebotsanfragen'],
    ['zahlen', 'Meine Zahlen', 'Anrufe, erreichte Gespräche, Termine und neue Kunden dieser Woche auf einen Blick, dazu dein Wochenziel.', '#uebersicht', 'Zu „Meine Zahlen“'],
    ['provision', 'Meine Kunden und Provisionen', 'Hier siehst du, welche Kunden durch dich gewonnen wurden und wie weit deine Provision ist: berechnet, freigegeben oder ausgezahlt.', '#provisionen', 'Zu den Provisionen'],
    ['leitfaden', 'Leitfaden: dein Gesprächsfaden', 'Eine Vorlage für das Telefonat: Begrüßung, Bedarf, Nutzen, Terminvorschlag. Wirf kurz vor dem Anruf einen Blick darauf.', '#leitfaden', 'Zum Leitfaden'],
  ];
}

const schrittKarte = (nr, s, mitLink) => h('li', { class: 'schritt' },
  bild(s[0]),
  h('div', {}, h('div', { class: 'schrittkopf' }, h('span', { class: 'nr', 'aria-hidden': 'true' }, String(nr)), h('h3', {}, s[1])), h('p', {}, s[2]),
    mitLink && s[3] ? h('a', { class: 'btn sec small', href: s[3] }, s[4]) : ''));

// ---------------------------------------------------------------- Seite
const standalone = () => typeof matchMedia !== 'undefined' && matchMedia('(display-mode: standalone)').matches;
const plattform = () => /iphone|ipad/i.test(navigator.userAgent) ? 'iphone' : 'android';

/** Die Seite „So geht’s“: Teil 1 App installieren (Android/iPhone), Teil 2 Portal erklärt. rolle: 'kunde' | 'vertrieb'. */
export async function anleitungSeite(rolle, hat = () => true) {
  const ans = await ladeAnsicht();
  const liste = h('ol', { class: 'schritte' });
  let wahl = plattform();
  const reiter = h('div', { class: 'tabs' });
  const installBox = h('div');
  const zeichne = () => {
    liste.replaceChildren(...INSTALL[wahl].map((s, i) => schrittKarte(i + 1, s, false)));
    reiter.replaceChildren(...[['android', 'Android (Chrome)'], ['iphone', 'iPhone (Safari)']].map(([k, n]) => h('button', { type: 'button', class: k === wahl ? 'on' : '', 'aria-pressed': String(k === wahl), onclick: () => { wahl = k; zeichne(); } }, n)));
    installBox.replaceChildren(standalone() ? h('div', { class: 'msg ok' }, '✔ Du nutzt Markentrix schon als App.')
      : (wahl === 'android' && installBereit()) ? h('p', {}, h('button', { class: 'btn', onclick: async () => { await installStarten(); zeichne(); } }, 'Jetzt als App installieren')) : '');
  };
  zeichne();
  const schritte = rolle === 'vertrieb' ? schritteVertrieb() : schritteKunde(hat);
  const fertig = async () => {
    if (!ans.tour_gesehen) { try { await api('/api/me/ansicht', { method: 'PUT', body: { tour_gesehen: true }, leise: true }); ans.tour_gesehen = true; } catch { /* nächstes Mal wieder */ } }
    location.hash = rolle === 'vertrieb' ? '#heute' : '#heute';
  };
  return h('div', { class: 'stack' },
    h('h2', { class: 'anltitel', style: 'font-size:20px;margin:0' }, rolle === 'vertrieb' ? 'So startest du im Partnerportal' : 'So startest du bei Markentrix'),
    h('p', { class: 'muted' }, 'Zwei kurze Teile: erst die App aufs Handy legen (30 Sekunden), dann siehst du, wie du im Portal arbeitest. Du findest diese Seite jederzeit wieder unter „So geht’s“ im Menü.'),
    h('div', { class: 'card' }, h('h2', {}, '1 · App aufs Handy legen'), reiter, installBox, liste),
    h('div', { class: 'card' }, h('h2', {}, rolle === 'vertrieb' ? '2 · So arbeitest du als Vertriebspartner' : '2 · So arbeitest du mit dem Portal'),
      h('ol', { class: 'schritte' }, schritte.map((s, i) => schrittKarte(i + 1, s, true)))),
    h('div', { class: 'card' }, h('h2', {}, 'Fragen?'), h('p', {}, rolle === 'vertrieb' ? 'Melde dich einfach bei Markentrix, wir helfen dir persönlich weiter.' : 'Schreib uns unter „Nachrichten“, wir helfen dir persönlich weiter.'),
      h('button', { class: 'btn', onclick: fertig }, ans.tour_gesehen ? 'Zurück zu „Heute“' : 'Los geht’s')));
}

/** Beim allerersten Login zuerst die Anleitung zeigen (einmal pro Benutzer). */
export async function erstStart() {
  const ans = await ladeAnsicht();
  if (!ans.tour_gesehen && location.hash !== '#willkommen') location.hash = '#willkommen';
}

/** Kleines, wegklickbares Banner „App aufs Handy legen“ (nur am Handy, nur solange nicht installiert). */
export function installBanner() {
  let weg = false;
  try { weg = localStorage.getItem('mk-appbanner') === '1'; } catch { /* ohne Speicher erscheint es einfach wieder */ }
  if (weg || standalone() || !/android|iphone|ipad/i.test(navigator.userAgent) || location.hash === '#willkommen') return '';
  const b = h('div', { class: 'appbanner' }, h('span', {}, '📲 Markentrix als App aufs Handy legen'), h('a', { class: 'btn small', href: '#willkommen' }, 'Anleitung'),
    h('button', { type: 'button', class: 'zu', 'aria-label': 'Hinweis schließen', onclick: () => { b.remove(); try { localStorage.setItem('mk-appbanner', '1'); } catch { /* egal */ } } }, '✕'));
  return b;
}

/** Admin: QR-Code und Link, damit ein Kunde oder Vertriebler das Portal direkt am Handy öffnet. */
export async function qrKarte(rolle, name) {
  const d = await api('/api/admin/portal-qr').catch(() => null);
  if (!d) return '';
  const wer = rolle === 'vertrieb' ? 'Vertriebspartner' : 'Kunden';
  const text = `Hallo${name ? ' ' + name : ''}, hier ist dein Markentrix-${rolle === 'vertrieb' ? 'Partnerportal' : 'Portal'}: ${d.url}\nAm Handy in Chrome (Android) oder Safari (iPhone) öffnen und anmelden. Danach als App installieren: Android Menü ⋮ → „App installieren“, iPhone Teilen → „Zum Home-Bildschirm“.`;
  const m = h('span', { class: 'small muted' });
  return h('div', { class: 'card' }, h('h2', {}, 'Portal aufs Handy des ' + wer),
    h('p', { class: 'small muted' }, 'Zeig den Code am Bildschirm, der ' + (rolle === 'vertrieb' ? 'Vertriebler' : 'Kunde') + ' scannt ihn mit der Handy-Kamera und landet direkt auf der Anmeldung. Die Anleitung zum Installieren erscheint nach dem ersten Login von selbst.'),
    h('div', { class: 'row', style: 'align-items:center;gap:16px' }, h('img', { src: d.svg, alt: 'QR-Code zum Portal', width: 140, height: 140, style: 'background:#fff;padding:6px;border-radius:10px;border:1px solid var(--line)' }),
      h('div', { class: 'stack' }, h('div', { class: 'small' }, d.url),
        h('div', { class: 'row' }, h('button', { class: 'btn sec small', onclick: async () => { try { await navigator.clipboard.writeText(text); m.textContent = 'Text kopiert.'; } catch { m.textContent = 'Kopieren nicht möglich.'; } } }, 'Text mit Link kopieren'),
          h('a', { class: 'btn sec small', href: 'https://wa.me/?text=' + encodeURIComponent(text), target: '_blank', rel: 'noopener' }, 'Per WhatsApp senden'), m))));
}
