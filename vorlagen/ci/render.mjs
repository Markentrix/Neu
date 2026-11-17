// Druckt die HTML-Datei des Handbuchs als PDF und prüft, ob Inhalt in die Fußzeile ragt. Aufruf: node render.mjs <html> <pdf>
import { createRequire } from 'module';
const require = createRequire('/opt/node-tools/');
const { chromium } = require('playwright');
const [, , html, pdf] = process.argv;
const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
const pg = await b.newPage({ viewport: { width: 794, height: 1123 } });
await pg.goto('file://' + html); await pg.waitForTimeout(900);
const r = await pg.evaluate(() => [...document.querySelectorAll('.pg')].map((s, i) => {
  const top = s.getBoundingClientRect().top; let max = 0, who = '';
  s.querySelectorAll('*').forEach(e => { if (e.closest('.ft') || e.closest('.hd')) return; const q = e.getBoundingClientRect(); if (q.height > 0 && q.bottom - top > max) { max = q.bottom - top; who = e.tagName + '.' + (e.className || ''); } });
  return { seite: i + 1, unten: Math.round(max), ueber: Math.round(max - (1123 - 62)), who };
}));
for (const x of r) console.log(`Seite ${String(x.seite).padStart(2)}: Inhalt endet bei ${x.unten} px, Grenze 1061 ${x.ueber > 0 ? 'ZU LANG um ' + x.ueber + ' ' + x.who : 'ok'}`);
await pg.pdf({ path: pdf, preferCSSPageSize: true, printBackground: true });
await b.close();
