import { chromium } from 'playwright'; import fs from 'node:fs';
const BASE = 'http://localhost:8787', PFAD = process.argv[2] || '/', BREITEN = [1440, 768, 390, 320], funde = [];
const F = (b, typ, text) => funde.push(`${b}px  ${typ}: ${text}`);
fs.mkdirSync('shots', { recursive: true });
const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
for (const b of BREITEN) {
  const page = await browser.newPage({ viewport: { width: b, height: b > 600 ? 900 : 800 } });
  page.on('console', m => m.type() === 'error' && F(b, 'KONSOLE', m.text().slice(0, 90)));
  page.on('request', r => { const u = r.url(); if (!u.startsWith(BASE) && !u.startsWith('data:')) F(b, 'FREMDABRUF', u.slice(0, 90)); });
  page.on('response', r => r.status() >= 400 && !r.url().includes('/api/') && F(b, 'FEHLT', `${r.status()} ${r.url().replace(BASE, '')}`));
  await page.goto(BASE + PFAD, { waitUntil: 'networkidle' });
  (await page.evaluate(() => {
    const out = [], kurz = e => (e.tagName.toLowerCase() + (e.className ? '.' + String(e.className).split(' ')[0] : '') + ' "' + (e.textContent || e.name || '').trim().slice(0, 28) + '"');
    const sichtbar = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
    const lum = c => { const [r, g, bl] = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * bl; };
    const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
    const grund = e => { for (; e; e = e.parentElement) { const s = getComputedStyle(e); if (s.backgroundImage !== 'none') return null; const c = rgb(s.backgroundColor); if (c.length === 3 || c[3] > .5) return c; } return [255, 255, 255]; };
    if (document.documentElement.scrollWidth > innerWidth + 1) out.push(['UEBERLAUF', `Seite ist ${document.documentElement.scrollWidth}px breit`]);
    [...document.querySelectorAll('body *')].filter(e => sichtbar(e) && e.getBoundingClientRect().right > innerWidth + 1).slice(0, 3).forEach(e => out.push(['UEBERLAUF', kurz(e)]));
    const h1 = document.querySelectorAll('h1').length; if (h1 !== 1) out.push(['H1', `${h1} statt 1`]);
    document.querySelectorAll('h1,h2,h3').forEach(h => { const z = Math.round(h.getBoundingClientRect().height / parseFloat(getComputedStyle(h).lineHeight)); if (z > 2) out.push(['HEADLINE', `${z} Zeilen: ${kurz(h)}`]); });
    if (innerWidth < 600) document.querySelectorAll('a,button,input,select,textarea,[role=button]').forEach(e => { if (!sichtbar(e) || e.type === 'hidden') return; const r = e.getBoundingClientRect(); if (r.height < 44 && !(e.tagName === 'A' && e.closest('p,li'))) out.push(['TIPPZIEL', `${Math.round(r.height)}px hoch: ${kurz(e)}`]); });
    document.querySelectorAll('input,select,textarea').forEach(e => { if (sichtbar(e) && parseFloat(getComputedStyle(e).fontSize) < 16) out.push(['EINGABE', `Schrift unter 16px (iOS zoomt): ${kurz(e)}`]); if (sichtbar(e) && !e.labels?.length && !e.getAttribute('aria-label')) out.push(['LABEL', `fehlt: ${kurz(e)}`]); });
    document.querySelectorAll('img').forEach(i => { if (!i.hasAttribute('alt')) out.push(['ALT', i.getAttribute('src')]); if (!i.getAttribute('width') || !i.getAttribute('height')) out.push(['BILDMASS', `width/height fehlt: ${i.getAttribute('src')}`]); });
    const fam = new Set(); document.querySelectorAll('body *').forEach(e => { if (sichtbar(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) { fam.add(getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g, '').trim());
      const s = getComputedStyle(e), bg = grund(e), fg = rgb(s.color); if (bg && fg.length >= 3) { const a = lum(fg), c = lum(bg), k = (Math.max(a, c) + .05) / (Math.min(a, c) + .05), gross = parseFloat(s.fontSize) >= 24; if (k < (gross ? 3 : 4.5)) out.push(['KONTRAST', `${k.toFixed(1)}:1 ${kurz(e)}`]); } } });
    if (fam.size > 2) out.push(['SCHRIFTEN', `${fam.size} Familien: ${[...fam].join(', ')}`]);
    const css = [...document.styleSheets].flatMap(s => { try { return [...s.cssRules].map(r => r.cssText); } catch { return []; } }).join('\n');
    const tAll = [...document.querySelectorAll('body *')].find(e => { const s = getComputedStyle(e); return s.transitionProperty === 'all' && parseFloat(s.transitionDuration) > 0; }); if (tAll) out.push(['CSS', `transition: all an ${kurz(tAll)}`]);
    if (/100vh/.test(css)) out.push(['CSS', '100vh (besser 100svh/100dvh)']);
    if (/user-scalable\s*=\s*no|maximum-scale\s*=\s*1/.test(document.querySelector('meta[name=viewport]')?.content || '')) out.push(['ZOOM', 'Zoom gesperrt']);
    return out;
  })).forEach(([t, x]) => F(b, t, x));
  await page.screenshot({ path: `shots/${PFAD.replace(/\W+/g, '_').replace(/^_+|_+$/g, '') || 'start'}_${b}.png`, fullPage: true });
  await page.close();
}
await browser.close();
console.log(funde.length ? [...new Set(funde)].join('\n') : 'Keine Funde.'); console.log(`\n${new Set(funde).size} Funde. Screenshots in shots/ ansehen.`);
process.exit(funde.length ? 1 : 0);
