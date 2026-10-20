import { h, api, dialog, ladeAnsicht } from '../common.js';
import { hat } from './kern.js';

/** Drei kurze Schritte beim ersten Login. `erzwingen` zeigt sie auch nach „gesehen“ (Hilfe-Seite). */
export async function tour(erzwingen = false) {
  const ans = await ladeAnsicht();
  if (ans.tour_gesehen && !erzwingen) return;
  const schritte = [
    ['Willkommen bei Markentrix', 'Hier siehst du auf einen Blick, was für dein Geschäft läuft. Auf „Heute“ steht immer als Erstes, was jetzt dran ist.', '#heute', 'Zu „Heute“'],
    [hat('anfragen_termine') ? 'Anfragen und Termine' : 'Nachrichten an uns', hat('anfragen_termine') ? 'Neue Anfragen von deiner Website und per Telefon landen unter „Anfragen“. Ruf zurück, solange sie frisch sind – das entscheidet oft über den Auftrag.' : 'Schreib uns jederzeit unter „Nachrichten“. Wir antworten persönlich.', hat('anfragen_termine') ? '#anfragen' : '#nachrichten', 'Ansehen'],
    ['Hilfe ist immer da', 'Unter „Mehr“ (am Handy) oder im Menü links findest du „Hilfe“ mit Antworten auf die häufigsten Fragen. Diese Tour kannst du dort jederzeit wiederholen.', '#hilfe', 'Zur Hilfe'],
  ];
  let i = 0;
  const kasten = h('div', { class: 'stack' });
  const dlg = dialog('Kurze Tour', kasten);
  const fertig = async () => {
    dlg.zu();
    if (!ans.tour_gesehen) { try { await api('/api/me/ansicht', { method: 'PUT', body: { tour_gesehen: true }, leise: true }); ans.tour_gesehen = true; } catch { /* nächstes Mal wieder */ } }
  };
  const zeichne = () => {
    const [titel, text, ziel, knopf] = schritte[i], letzte = i === schritte.length - 1;
    kasten.replaceChildren(
      h('p', { class: 'small muted' }, `Schritt ${i + 1} von ${schritte.length}`),
      h('h3', {}, titel), h('p', {}, text),
      h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap' },
        h('button', { class: 'btn', onclick: () => { if (letzte) fertig(); else { i++; zeichne(); } } }, letzte ? 'Fertig' : 'Weiter'),
        h('a', { class: 'btn sec', href: ziel, onclick: () => fertig() }, knopf),
        letzte ? '' : h('button', { class: 'btn sec', onclick: fertig }, 'Überspringen')));
  };
  zeichne();
}
