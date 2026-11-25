// Prüfskript nach Abschnitt 18 des Skills: läuft über alle Seiten und fasst zusammen. Erst node tools/mock.mjs starten.
import { createRequire } from 'node:module'; import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const { chromium } = createRequire(import.meta.url)('playwright');
const BASE = process.env.BASE || 'http://localhost:8787';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'website-fertig'); const pages = [];
(function walk(d) { for (const f of fs.readdirSync(d)) { const p = path.join(d, f); if (fs.statSync(p).isDirectory()) walk(p); else if (f === 'index.html') pages.push('/' + path.relative(root, d) + (path.relative(root, d) ? '/' : '')); else if (f.endsWith('.html')) pages.push('/' + path.relative(root, p).replace(/\\/g, '/')); } })(root);
if (process.env.ONLY) { const k = pages.filter(p => process.env.ONLY.split(',').some(o => p.includes(o))); pages.length = 0; pages.push(...k); }
const main = async () => {
  const browser = await chromium.launch(); const sum = {}; const ex = {};
  const add = (t, w, p, x) => { const k = t; sum[k] = (sum[k] || 0) + 1; (ex[k] = ex[k] || []).length < 4 && ex[k].push(`${w}px ${p} ${x}`); };
  for (const b of (process.env.W || '1440,768,390,320').split(',').map(Number)) {
    const ctx = await browser.newContext({ viewport: { width: b, height: b > 600 ? 900 : 800 }, isMobile: b < 800, hasTouch: b < 800 });
    for (const P of pages) {
      const page = await ctx.newPage();
      page.on('console', m => m.type() === 'error' && add('KONSOLE', b, P, m.text().slice(0, 80)));
      page.on('request', r => { const u = r.url(); if (!u.startsWith(BASE) && !u.startsWith('data:')) add('FREMDABRUF', b, P, u.slice(0, 80)); });
      page.on('response', r => r.status() >= 400 && add('FEHLT', b, P, `${r.status()} ${r.url().replace(BASE, '')}`));
      await page.goto(BASE + P, { waitUntil: 'networkidle' });
      const res = await page.evaluate(() => {
        const out = [], kurz = e => (e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '') + ' "' + (e.textContent || e.name || '').trim().slice(0, 28) + '"');
        const sichtbar = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
        const lum = c => { const [r, g, bl] = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * bl; };
        const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
        const grund = e => { for (; e; e = e.parentElement) { const s = getComputedStyle(e); if (s.backgroundImage !== 'none') return null; const c = rgb(s.backgroundColor); if (c.length === 3 || c[3] > .5) return c; } return [255, 255, 255]; };
        if (document.documentElement.scrollWidth > innerWidth + 1) out.push(['UEBERLAUF', `Seite ${document.documentElement.scrollWidth}px breit`]);
        const h1 = document.querySelectorAll('h1').length; if (h1 !== 1) out.push(['H1', `${h1} statt 1`]);
        document.querySelectorAll('h1,h2,h3').forEach(h => { if (!sichtbar(h)) return; const z = Math.round(h.getBoundingClientRect().height / (parseFloat(getComputedStyle(h).lineHeight) || parseFloat(getComputedStyle(h).fontSize))); if (z > 2) out.push(['HEADLINE>2', `${z} Zeilen: ${kurz(h)}`]); });
        if (innerWidth < 600) document.querySelectorAll('a,button,input,select,textarea,[role=button]').forEach(e => { if (!sichtbar(e) || e.type === 'hidden' || e.closest('.hp,.skip-link') || e.classList.contains('file-input')) return; const r = e.getBoundingClientRect(); if (r.height < 40 && !(e.tagName === 'A' && e.closest('p,li,.legal-page,.prose')) && !e.classList.contains('skip-link')) out.push(['TIPPZIEL', `${Math.round(r.height)}px: ${kurz(e)}`]); });
        document.querySelectorAll('input,select,textarea').forEach(e => { if (!sichtbar(e) || e.closest('.hp')) return; if (parseFloat(getComputedStyle(e).fontSize) < 16 && e.type !== 'checkbox' && e.type !== 'radio' && e.type !== 'file') out.push(['EINGABE<16', kurz(e)]); if (!e.labels?.length && !e.getAttribute('aria-label')) out.push(['LABEL', kurz(e)]); });
        document.querySelectorAll('img').forEach(i => { if (!i.hasAttribute('alt')) out.push(['ALT', i.getAttribute('src')]); if (!i.getAttribute('width') || !i.getAttribute('height')) out.push(['BILDMASS', i.getAttribute('src')]); });
        const fam = new Set(); document.querySelectorAll('body *').forEach(e => { if (sichtbar(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) { fam.add(getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g, '').trim());
          if (e.closest('[class*="draft"], .btn, .chips, .action-bar, .primary-nav, .id-tag')) return;
          const s = getComputedStyle(e), bg = grund(e), fg = rgb(s.color); if (bg && fg.length >= 3 && (fg.length === 3 || fg[3] > .9)) { const a = lum(fg), c = lum(bg), k = (Math.max(a, c) + .05) / (Math.min(a, c) + .05), gross = parseFloat(s.fontSize) >= 24 || (parseFloat(s.fontSize) >= 18.66 && parseInt(s.fontWeight) >= 700); if (k < (gross ? 3 : 4.5)) out.push(['KONTRAST', `${k.toFixed(1)}:1 ${kurz(e)}`]); } } });
        if (fam.size > 2) out.push(['SCHRIFTEN', `${fam.size} Familien: ${[...fam].join(', ')}`]);
        const css = [...document.styleSheets].flatMap(s => { try { return [...s.cssRules].map(r => r.cssText); } catch { return []; } }).join('\n');
        if (/transition(-property)?:\s*all/.test(css)) out.push(['CSS', 'transition: all']);
        if (/100vh/.test(css)) out.push(['CSS', '100vh']);
        return out;
      });
      res.forEach(([t, x]) => add(t, b, P, x));
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  const keys = Object.keys(sum);
  console.log(keys.length ? keys.map(k => `${k}: ${sum[k]}   z. B. ${ex[k].join(' | ')}`).join('\n') : 'Keine Funde.');
};
main();
