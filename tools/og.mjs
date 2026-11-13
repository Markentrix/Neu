// Erzeugt die Vorschaubilder (1200 x 630) für Social-Netzwerke, eines je indexierbarer Seite.
// Aufruf: node tools/og.mjs   (nach dem Build; benötigt Playwright mit Chromium)
// Ergebnis: static/img/og/<name>.png, der Build verweist automatisch darauf (siehe tools/build.py).
import { chromium } from 'playwright';
import { readdirSync, readFileSync, mkdirSync, writeFileSync, statSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const ROOT = process.env.MX_ROOT || resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = join(ROOT, 'dist'), OUT = join(ROOT, 'static/img/og'), FONTS = join(ROOT, 'static/fonts');
mkdirSync(OUT, { recursive: true });
const executablePath = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const unesc = s => s.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');
function walk(d) { let r = []; for (const f of readdirSync(d)) { const p = join(d, f); if (statSync(p).isDirectory()) { if (f !== 'api' && f !== 'beispiel') r = r.concat(walk(p)); } else if (f.endsWith('.html')) r.push(p); } return r; }

const pages = [];
for (const f of walk(DIST)) {
  const h = readFileSync(f, 'utf8');
  if (/name="robots" content="[^"]*noindex/.test(h)) continue;
  const canon = (h.match(/<link rel="canonical" href="https:\/\/markentrix\.de([^"]*)"/) || [])[1];
  if (canon === undefined) continue;
  const title = unesc((h.match(/<title>([^<]*)<\/title>/) || [])[1] || '').replace(/\s*\|\s*Markentrix( Blog)?$/, '');
  const desc = unesc((h.match(/<meta name="description" content="([^"]*)"/) || [])[1] || '');
  const name = canon === '' ? 'home' : canon.replace(/^\//, '').replace(/\//g, '-');
  let main = title, sub = '';
  const i = title.indexOf(':');
  if (i > 0 && i < 42) { main = title.slice(0, i); sub = title.slice(i + 1).trim(); }
  else { const first = desc.split(/(?<=[.!?])\s/)[0]; sub = first.length <= 76 ? first : desc.slice(0, desc.lastIndexOf(' ', 70)).replace(/[,;:]$/, '') + ' …'; }
  if (canon === '') { main = 'Websites, die Anfragen bringen.'; sub = 'Landingpages, SEO und GEO für Betriebe in Celle und Umgebung.'; }
  const kind = canon.startsWith('/blog/') ? 'Blog' : canon.startsWith('/leistungen/') ? 'Leistung' : canon.startsWith('/ki-marketing-') ? 'Region' : 'Webdesign-Agentur in Celle';
  pages.push({ name, main, sub, kind });
}

const LOGO_FILE = join(ROOT, 'static/img/logo/markentrix-logo-farbe-hell.svg'), LINIE_FILE = join(ROOT, 'static/img/logo/aufwaertslinie.svg');
// Markenhandbuch Version 3.0: Kreide, Tiefsee, Pfauenblau, Kupfer; Archivo und Source Sans 3; Kupferstrich und Aufwärtslinie
const html = p => {
  const big = p.main.length > 44 ? 62 : p.main.length > 28 ? 74 : 86;
  const words = esc(p.main).split(' '); const last = words.pop();
  const head = (words.length ? words.join(' ') + ' ' : '') + `<span class="hl">${last}</span>`;
  return `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:AR;font-weight:800;src:url("file://${FONTS}/archivo-800.woff2")}
@font-face{font-family:SS;font-weight:400;src:url("file://${FONTS}/source-sans-3-400.woff2")}
@font-face{font-family:SS;font-weight:700;src:url("file://${FONTS}/source-sans-3-700.woff2")}
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;position:relative;overflow:hidden;font-family:SS,sans-serif;color:#0C2128;background:#F7F4EE}
.logo{position:absolute;left:80px;top:64px;width:300px;height:auto}
.kind{position:absolute;right:80px;top:84px;font:700 22px SS;letter-spacing:.09em;text-transform:uppercase;color:#045268}
.main{position:absolute;left:80px;right:80px;top:196px}
h1{font:800 ${big}px/1.06 AR;letter-spacing:-.025em;max-width:1000px}
.hl{background-image:linear-gradient(#C67432,#C67432);background-repeat:no-repeat;background-size:100% .14em;background-position:0 98%;padding-bottom:.06em}
h2{font:400 ${Math.round(big*0.44)}px/1.3 SS;margin-top:26px;max-width:900px;color:#0C2128}
.foot{position:absolute;left:80px;bottom:58px;font:600 24px SS;color:#4E5C5F}
.linie{position:absolute;right:70px;bottom:44px;width:270px;height:auto}
</style>
<img class="logo" src="file://${LOGO_FILE}"><div class="kind">${esc(p.kind)}</div>
<div class="main"><h1>${head}</h1>${p.sub ? `<h2>${esc(p.sub)}</h2>` : ''}</div>
<div class="foot">markentrix.de · Celle</div><img class="linie" src="file://${LINIE_FILE}">`;
};

const b = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox', '--allow-file-access-from-files'] });
const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
let n = 0;
for (const p of pages) {
  const f = join('/tmp', `og-${p.name}.html`); writeFileSync(f, html(p));
  await pg.goto('file://' + f); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(120);
  await pg.screenshot({ path: join(OUT, p.name + '.png') }); n++;
}
await b.close();
console.log(n + ' Vorschaubilder → static/img/og/');
