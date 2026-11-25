// Erzeugt website-fertig/assets/og-image.jpg (1200x630) im Stil der Website: weißer Grund, große Schrift, Fahrzeug von der Seite.
// Aufruf: node build/make-og.js   (benötigt Playwright mit Chromium und Python 3)
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const pub = path.resolve(__dirname, '..', 'website-fertig', 'assets');
const car = execFileSync('python3', ['-c', "import sys; sys.path.insert(0, r'" + __dirname + "'); import artwork; print(artwork.car_side('Fahrzeug'))"]).toString();
const html = `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:E;font-weight:800;src:url('file://${pub}/fonts/Epilogue-800.woff2')}
@font-face{font-family:E;font-weight:600;src:url('file://${pub}/fonts/Epilogue-600.woff2')}
*{box-sizing:border-box;margin:0}
:root{--fg:#101114;--surface:#fff;--paper-2:#ECEDEF;--accent:#D71A21;--muted:#494C53}
body{width:1200px;height:630px;background:#fff;position:relative;overflow:hidden;color:#101114;font-family:E,sans-serif}
.stage{position:absolute;left:0;right:0;bottom:0;height:250px;background:#ECEDEF}
svg{position:absolute;left:50px;bottom:-14px;width:1120px;height:auto}
.v-lead,.v-dot{display:none}
.v-ground{stroke:var(--fg);stroke-width:2}.v-skid{fill:var(--fg)}
.v-body{fill:#fff;stroke:var(--fg);stroke-width:2.5;stroke-linejoin:round}
.v-ghost path{fill:none;stroke:var(--muted);stroke-width:1.5;stroke-dasharray:6 5}
.v-detail *{fill:none;stroke:var(--fg);stroke-width:1.5}.v-detail .v-glass{fill:var(--paper-2)}.v-detail .v-handle{fill:var(--fg)}.v-detail .v-lamp{fill:#fff}
.v-tyre{fill:var(--fg)}.v-rim{fill:#fff;stroke:var(--fg);stroke-width:2}.v-spoke line{stroke:var(--fg);stroke-width:2.2;stroke-linecap:round}.v-disc{fill:none;stroke:var(--fg);stroke-width:2}.v-hub{fill:var(--fg)}
.v-hatch{stroke:var(--accent);stroke-width:2.4}.v-ring{fill:none;stroke:var(--accent);stroke-width:4;stroke-linecap:round}
.logo{position:absolute;left:72px;top:44px;height:78px}
h1{position:absolute;left:72px;top:132px;font:800 100px/.98 E,sans-serif;letter-spacing:-.045em}
.tel{position:absolute;right:72px;top:62px;text-align:right;font:800 46px/1 E;letter-spacing:-.04em}
.tel small{display:block;font:600 19px E;letter-spacing:0;color:var(--accent);margin-bottom:6px}
</style><div class="stage"></div>${car}
<img class="logo" src="file://${pub}/logo.png"><h1>Kfz-Gutachter<br>in Celle</h1>
<div class="tel"><small>Jetzt anrufen</small>0172 517 81 50</div>`;
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
