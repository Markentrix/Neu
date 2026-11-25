// Prüft den Foto-Weg gegen den Mock: Fotos werden als verkleinerte JPEG-Daten mitgesendet, bei Ablehnung (413) geht die Anfrage ohne Fotos durch.
// Aufruf: node tools/mock.mjs &  node tools/fototest.mjs   und mit MOCK_FOTOS=ablehnen node tools/mock.mjs  node tools/fototest.mjs ablehnen
import { createRequire } from 'node:module'; import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const { chromium } = createRequire(import.meta.url)('playwright');
const BASE = process.env.BASE || 'http://localhost:8787', ablehnen = process.argv[2] === 'ablehnen', erg = [];
const E = (ok, t) => erg.push(`${ok ? 'PASS' : 'FAIL'}  ${t}`);
const foto = fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'website-fertig', 'assets', 'portrait.jpg'));
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 390, height: 800 } });
await p.goto(BASE + '/kontakt/', { waitUntil: 'networkidle' });
await p.setInputFiles('#f-photos', [{ name: 'a.jpg', mimeType: 'image/jpeg', buffer: foto }, { name: 'b.jpg', mimeType: 'image/jpeg', buffer: foto }]);
await p.waitForFunction(() => document.querySelectorAll('#photo-list li').length === 2, null, { timeout: 15000 });
await p.fill('#f-name', 'Erika Mustermann'); await p.fill('#f-email', 'erika@example.de'); await p.selectOption('#f-subject', { index: 1 });
await p.fill('#f-message', 'Heckschaden, Fotos anbei.'); await p.fill('#f-plate', 'CE AB 123'); await p.fill('#f-insurer', 'HUK'); await p.check('#f-consent');
await p.click('button[type=submit]'); await p.waitForURL('**/danke.html*', { timeout: 20000 });
const last = await (await fetch(BASE + '/__last')).json();
E(/MOCK-/.test(await p.evaluate(() => document.body.innerText)), 'Weiterleitung auf die Danke-Seite mit Vorgangsnummer');
E(last.typ === 'kontakt' && last.einwilligung === 'ja' && last.kennzeichen === 'CE AB 123' && last.versicherung === 'HUK' && last.antwort === 'E-Mail', 'Felder nach Vertrag: typ, einwilligung, kennzeichen, versicherung, antwort');
if (!ablehnen) {
  E(Array.isArray(last.fotos) && last.fotos.length === 2, 'zwei Fotos als Daten mitgesendet');
  E(last.fotos && last.fotos.every(n => n < 400000), `Fotos klein genug (${(last.fotos || []).map(n => Math.round(n / 1024) + ' KB').join(', ')})`);
  E(!(await p.isVisible('[data-photo-note]')), 'kein Foto-Hinweis auf der Danke-Seite');
} else {
  E(last.fotos === undefined, 'nach Ablehnung wurde ohne Fotos gesendet');
  E(await p.isVisible('[data-photo-note]'), 'Danke-Seite weist auf WhatsApp für die Fotos hin');
}
await b.close(); console.log(erg.join('\n')); process.exit(erg.some(e => e.startsWith('FAIL')) ? 1 : 0);
