// Fotografiert die bisherige Website (Voll-Seiten-Bilder) für die Vergleichsansicht.
// Aufruf: NODE_PATH=$(npm root -g) node build/compare/capture-old.js [Seiten-ids, z. B. start kontakt]
// Braucht Playwright und Internetzugang. Die Bilder liegen danach in build/compare/alt/ und werden eingecheckt.
const { chromium } = require('playwright');
const path = require('path');

const BASE = 'https://psschneider.de';
const ONLY = process.argv.slice(2);
const PAGES = require('./pages.json').filter(p => !ONLY.length || ONLY.includes(p.id));
const OUT = path.join(__dirname, 'alt');

(async () => {
  const b = await chromium.launch();
  for (const [kind, vp, dsf] of [['d', { width: 1280, height: 900 }, 1], ['m', { width: 390, height: 800 }, 2]]) {
    const ctx = await b.newContext({ viewport: vp, deviceScaleFactor: dsf, isMobile: kind === 'm', hasTouch: kind === 'm' });
    for (const p of PAGES) {
      if (!p.old) continue;
      const pg = await ctx.newPage();
      try {
        const r = await pg.goto(BASE + p.old, { waitUntil: 'networkidle', timeout: 60000 });
        // Seite langsam durchscrollen, damit nachgeladene Bilder erscheinen
        await pg.evaluate(async () => {
          const h = document.documentElement.scrollHeight;
          for (let y = 0; y < h; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
          window.scrollTo(0, 0);
        });
        // Cookie-Hinweis und andere fest angeheftete Elemente ausblenden, sonst liegen sie mitten im Bild
        await pg.evaluate(() => {
          for (const el of document.querySelectorAll('body *')) {
            const cs = getComputedStyle(el);
            if (cs.position === 'fixed' || /cookie/i.test(el.id + ' ' + el.className)) el.style.setProperty('display', 'none', 'important');
          }
        });
        await pg.waitForTimeout(600);
        const height = await pg.evaluate(() => document.documentElement.scrollHeight);
        await pg.screenshot({ path: path.join(OUT, `${p.id}-${kind}.jpg`), type: 'jpeg', quality: kind === 'd' ? 78 : 70, fullPage: true });
        console.log(kind, p.id, r.status(), height + ' px');
      } catch (e) { console.log(kind, p.id, 'FEHLER', e.message.slice(0, 100)); }
      await pg.close();
    }
    await ctx.close();
  }
  await b.close();
})();
