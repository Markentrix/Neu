// Baut das CI-Handbuch: node build.js  →  ../Markentrix_CI_2026_v3.pdf
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const dir = __dirname, parts = path.join(dir, 'parts');
  const body = fs.readdirSync(parts).filter(f => f.endsWith('.html')).sort().map(f => fs.readFileSync(path.join(parts, f), 'utf8')).join('\n');
  const html = fs.readFileSync(path.join(dir, 'template.html'), 'utf8').replace('<!--PAGES-->', body);
  const outHtml = path.join(dir, 'handbuch.html'); fs.writeFileSync(outHtml, html);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 794, height: 1123 } });
  await p.goto('file://' + outHtml, { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
  const report = await p.evaluate(() => [...document.querySelectorAll('.page')].map((pg, i) => {
    const over = []; const pr = pg.getBoundingClientRect(); const foot = pg.querySelector('.pf').getBoundingClientRect().top;
    pg.querySelectorAll('.pc *').forEach(e => { const r = e.getBoundingClientRect(); if (!r.width) return;
      if (r.bottom > foot - 4 || r.right > pr.right - 40) over.push(e.tagName + '.' + e.className + ':' + (e.textContent || '').trim().slice(0, 30));
      if ((e.scrollWidth > e.clientWidth + 1) && getComputedStyle(e).display !== 'inline' && e.children.length === 0) over.push('CLIP ' + (e.textContent || '').trim().slice(0, 30)); });
    const last = [...pg.querySelectorAll('.pc > *')].pop().getBoundingClientRect().bottom; return over.length ? { page: i + 1, frei: Math.round(foot - last), over: over.slice(0, 3) } : { page: i + 1, frei: Math.round(foot - last) }; }).filter(Boolean));
  console.log(report.length ? JSON.stringify(report, null, 1) : 'Kein Überlauf.');
  console.log('Schriften:', await p.evaluate(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight).join(', ')));
  await p.pdf({ path: path.join(dir, '..', 'Markentrix_CI_2026_v3.pdf'), format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  if (process.argv[2]) { const n = await p.locator('.page').count(); for (let i = 0; i < n; i++) await p.locator('.page').nth(i).screenshot({ path: path.join(process.argv[2], `p${String(i + 1).padStart(2, '0')}.png`) }); }
  await b.close();
})();
