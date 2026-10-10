// Erzeugt public/assets/og-image.jpg (1200x630) aus Logo, Porträt und Schriften.
// Aufruf: node build/make-og.js   (benötigt Playwright mit Chromium)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const os = require('os');
const pub = path.resolve(__dirname, '..', 'public', 'assets');
const html = `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:BC;font-weight:700;src:url('file://${pub}/fonts/BarlowCondensed-700.woff2')}
@font-face{font-family:B;font-weight:500;src:url('file://${pub}/fonts/Barlow-500.woff2')}
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;background:#fff;position:relative;overflow:hidden;font-family:B,sans-serif;color:#141518}
.bar{position:absolute;left:0;top:0;bottom:0;width:18px;background:#D71A21}
.logo{position:absolute;left:84px;top:64px;height:112px}
h1{position:absolute;left:84px;top:236px;width:690px;font:700 84px/1 BC,sans-serif;white-space:nowrap}
h1 span{color:#D71A21}
p{position:absolute;left:84px;bottom:64px;font-size:30px;color:#5B6168;line-height:1.3;width:640px}
.ph{position:absolute;right:0;top:0;bottom:0;width:420px;background:url('file://${pub}/portrait.jpg') 50% 20%/cover}
.ph::after{content:"";position:absolute;left:0;top:0;bottom:0;width:10px;background:#D71A21}
</style><div class="bar"></div><img class="logo" src="file://${pub}/logo.png"><h1>Kfz-Gutachter in <span>Celle</span></h1>
<p>Unabhängig · Schnell · Gerichtsfest<br>Patric Schneider, Kfz-Meister</p><div class="ph"></div>`;
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
