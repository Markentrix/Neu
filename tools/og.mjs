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
  else { const first = desc.split(/(?<=[.!?])\s/)[0]; sub = first.length <= 118 ? first : desc.slice(0, desc.lastIndexOf(' ', 112)).replace(/[,;:]$/, '') + ' …'; }
  if (canon === '') { main = 'Websites, die Anfragen bringen.'; sub = 'Landingpages, SEO und GEO für Betriebe in Celle und Umgebung.'; }
  const kind = canon.startsWith('/blog/') ? 'Blog' : canon.startsWith('/leistungen/') ? 'Leistung' : canon.startsWith('/ki-marketing-') ? 'Region' : 'Webdesign-Agentur in Celle';
  pages.push({ name, main, sub, kind });
}

const LOGO = '<svg viewBox="0 0 48 48" width="74" height="74" fill="none"><defs><linearGradient id="g" x1="9" y1="40" x2="39" y2="9" gradientUnits="userSpaceOnUse"><stop stop-color="#28C7F7"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs><path d="M11 38V13.5L23.5 26.5L31 18.5" stroke="url(#g)" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M31 38V18.5" stroke="url(#g)" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M31 18.5L37 12.5M37 12.5L30.5 12.5M37 12.5L37 19" stroke="url(#g)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const html = p => {
  const big = p.main.length > 44 ? 60 : p.main.length > 28 ? 72 : 84;
  return `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:SG;font-weight:700;src:url("file://${FONTS}/space-grotesk-700.woff2")}
@font-face{font-family:In;font-weight:400;src:url("file://${FONTS}/inter-400.woff2")}
@font-face{font-family:In;font-weight:600;src:url("file://${FONTS}/inter-600.woff2")}
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;position:relative;overflow:hidden;font-family:In,sans-serif;color:#0B1020;background:
 radial-gradient(900px 520px at 100% 0%,rgba(139,92,246,.16),transparent 60%),radial-gradient(900px 560px at 0% 100%,rgba(40,199,247,.20),transparent 60%),#F8FAFD}
.dots{position:absolute;inset:0;background-image:radial-gradient(rgba(11,16,32,.08) 1.2px,transparent 1.4px);background-size:28px 28px;-webkit-mask-image:linear-gradient(115deg,transparent 35%,#000 100%);mask-image:linear-gradient(115deg,transparent 35%,#000 100%)}
.top{position:absolute;left:80px;top:72px;display:flex;align-items:center;gap:22px}
.word{font:600 27px In;letter-spacing:.42em;text-transform:uppercase}
.kind{position:absolute;right:80px;top:92px;font:600 21px In;letter-spacing:.16em;text-transform:uppercase;color:#6D3FD1}
.main{position:absolute;left:80px;right:80px;top:200px}
h1{font:700 ${big}px/1.04 SG;letter-spacing:-.02em;max-width:1010px}
h2{font:700 ${Math.round(big*0.62)}px/1.1 SG;letter-spacing:-.015em;margin-top:22px;max-width:1010px;background:linear-gradient(90deg,#1F8FD9,#7C4DE0);-webkit-background-clip:text;background-clip:text;color:transparent}
.pill{position:absolute;left:80px;bottom:62px;padding:14px 28px;border-radius:999px;background:#fff;border:1px solid rgba(11,16,32,.14);font:600 24px In;color:#6D3FD1}
</style><div class="dots"></div>
<div class="top">${LOGO}<span class="word">Markentrix</span></div><div class="kind">${esc(p.kind)}</div>
<div class="main"><h1>${esc(p.main)}</h1>${p.sub ? `<h2>${esc(p.sub)}</h2>` : ''}</div>
<div class="pill">markentrix.de · Celle</div>`;
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
