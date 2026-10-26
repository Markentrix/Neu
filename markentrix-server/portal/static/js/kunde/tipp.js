// „Ein Tipp für dich“: unverbindlicher Hinweis auf ein passendes Paket. Erscheint nur, wenn der Admin die Hinweise eingeschaltet hat.
import { h, api } from '../common.js';

export async function tippKarte() {
  let d;
  try { d = await api('/api/kunde/tipp', { leise: true }); } catch (e) { return ''; }
  if (!d || !d.tipp) return '';
  const t = d.tipp, box = h('div', { class: 'card' });
  const reagiere = async (art, danach) => { try { await api('/api/kunde/tipp/' + t.code + '/reaktion', { method: 'POST', body: { art } }); } catch (e) { /* der Hinweis ist nur ein Angebot */ } danach(); };
  box.append(h('h2', {}, 'Ein Tipp für dich: ' + t.titel), h('p', {}, t.text),
    h('p', { class: 'small muted' }, 'Das ist ein unverbindlicher Hinweis. Im nächsten Schritt siehst du Inhalt und Preis des Pakets „' + t.paket + '“. Gebucht wird nichts ohne deine Bestätigung.'),
    h('div', { class: 'row' }, h('button', { class: 'btn', onclick: () => reagiere('interesse', () => { location.hash = '#pakete'; }) }, 'Paket ansehen'),
      h('button', { class: 'btn sec', onclick: () => reagiere('nein', () => box.remove()) }, 'Nein danke')));
  return box;
}
