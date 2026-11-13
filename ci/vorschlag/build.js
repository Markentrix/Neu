// node build.js [screenshot-ordner]  →  ../Markentrix_CI_Vorschlaege.pdf
const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1123, height: 794 } });
  p.on('console', m => console.log('WERTE:', m.text())); await p.goto('file://' + path.join(__dirname, process.argv[3]||'vorschlag.html'), { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
  const over = await p.evaluate(() => [...document.querySelectorAll('.page')].map((pg, i) => { const f = pg.querySelector('.foot').getBoundingClientRect().top; let m = 0; pg.querySelectorAll('.box,.m,.rec,p,h1').forEach(e => m = Math.max(m, e.getBoundingClientRect().bottom)); return [i + 1, Math.round(f - m)]; }));
  console.log('frei bis Fußzeile:', JSON.stringify(over));
  await p.pdf({ path: path.join(__dirname, '..', process.argv[4]||'Markentrix_CI_Vorschlaege.pdf'), width: '1123px', height: '794px', printBackground: true });
  if (process.argv[2]) { const n = await p.locator('.page').count(); for (let i = 0; i < n; i++) await p.locator('.page').nth(i).screenshot({ path: path.join(process.argv[2], (process.argv[5]||'v')+(i+1)+'.png') }); }
  await b.close(); })();
