// Erzeugt public/assets/og-image.jpg (1200x630) im Stil der Website: schwarzer Grund, schräge Schrift, Porträt im Parallelogramm.
// Aufruf: node build/make-og.js   (benötigt Playwright mit Chromium und Python 3)
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const pub = path.resolve(__dirname, '..', 'public', 'assets');
const plan = execFileSync('python3', ['-c', "import sys; sys.path.insert(0, r'" + __dirname + "'); import artwork; print(artwork.car_plan())"]).toString();
const html = `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:BC;font-style:italic;font-weight:800;src:url('file://${pub}/fonts/BarlowCondensed-800i.woff2')}
@font-face{font-family:BC;font-style:italic;font-weight:700;src:url('file://${pub}/fonts/BarlowCondensed-700i.woff2')}
@font-face{font-family:BC;font-style:normal;font-weight:600;src:url('file://${pub}/fonts/BarlowCondensed-600.woff2')}
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;background:#0D0E10;position:relative;overflow:hidden;color:#fff;font-family:BC,sans-serif}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:56px 56px}
.plan{position:absolute;left:300px;bottom:-130px;width:640px;height:auto;color:rgba(255,255,255,.5);opacity:.28}
.plan .body,.plan .cabin,.plan .roof{stroke:rgba(255,255,255,.7)}
.plan .fine{stroke:rgba(255,255,255,.3)}
.plan .axis{stroke:rgba(255,255,255,.22);stroke-dasharray:9 7}
.plan .wheels rect{fill:none;stroke:rgba(255,255,255,.55)}
.plan .dz{stroke:#EF3B42;fill:rgba(239,59,66,.2)}.plan .hatch{stroke:#EF3B42;opacity:.7}
.plan .dim,.plan .leader{stroke:#EF3B42}.plan .dim-t{fill:#fff;stroke:none;font:600 15px BC;letter-spacing:.14em}
.plan .mk{fill:#EF3B42;stroke:none}.plan .mk-n{fill:#fff;stroke:none;font:italic 800 19px BC}.plan .dot{fill:#EF3B42;stroke:none}
.logo{position:absolute;left:72px;top:46px;height:86px}
.kick{position:absolute;left:72px;top:190px;font:600 24px BC;letter-spacing:.24em;text-transform:uppercase;color:#A9ABB0;display:flex;align-items:center;gap:16px}
.kick::before{content:"";width:46px;height:6px;background:#EF3B42;transform:skewX(-12deg)}
h1{position:absolute;left:72px;top:176px;font:italic 800 100px/.9 BC,sans-serif;text-transform:uppercase;letter-spacing:-.005em}
h1 span{display:block;color:#EF3B42}
.tel{position:absolute;left:72px;bottom:46px;font:italic 800 52px/1 BC;letter-spacing:.01em}
.tel small{display:block;font:600 20px BC;font-style:normal;letter-spacing:.24em;color:#EF3B42;margin-bottom:6px}
.slab,.ph{position:absolute;clip-path:polygon(15% 0,100% 0,85% 100%,0 100%)}
.slab{right:58px;top:96px;width:392px;height:446px;background:#D71A21;transform:translate(0,0)}
.ph{right:90px;top:72px;width:392px;height:446px;background:url('file://${pub}/portrait.jpg') 50% 14%/cover}
.tag{position:absolute;right:332px;top:430px;background:#fff;color:#0D0E10;padding:12px 40px 12px 22px;border-left:8px solid #D71A21;clip-path:polygon(0 0,100% 0,calc(100% - 18px) 100%,0 100%)}
.tag b{display:block;font:italic 800 34px/1 BC;text-transform:uppercase}
.tag i{font:600 17px BC;font-style:normal;letter-spacing:.06em;color:#4a4d53}
</style><div class="grid"></div><div class="plan-wrap">${plan.replace('class="plan"', 'class="plan"')}</div>
<img class="logo" src="file://${pub}/logo-dark.png"><h1>Kfz-Gutachter<br>in Celle<span>Unabhängig.</span></h1>
<div class="tel"><small>Jetzt anrufen</small>0172 517 81 50</div>
<div class="slab"></div><div class="ph"></div>
<div class="tag"><b>Patric Schneider</b><i>Kraftfahrzeugtechniker-Meister</i></div>`;
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
  const tmp = path.join(os.tmpdir(), 'og-psschneider.html');
  fs.writeFileSync(tmp, html);
  await pg.goto('file://' + tmp, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);
  await pg.screenshot({ path: path.join(pub, 'og-image.jpg'), type: 'jpeg', quality: 88 });
  await b.close();
})();
