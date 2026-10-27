// Rendert SVG-Dateien per Chromium zu PNG. Aufruf: node build/render.js jobs.json
const fs = require('fs');
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const j of jobs) {
    const svg = fs.readFileSync(j.svg, 'utf8');
    await page.setViewportSize({ width: j.w, height: j.h });
    await page.setContent('<!doctype html><html><head><style>html,body{margin:0;padding:0}svg{display:block}</style></head><body>' + svg + '</body></html>');
    await page.screenshot({ path: j.png, clip: { x: 0, y: 0, width: j.w, height: j.h }, omitBackground: true });
  }
  await browser.close();
})();
