const { chromium } = require('playwright');
(async () => {
  const base = process.argv[2] || 'http://127.0.0.1:8765';
  const shots = process.argv[3] || '/tmp/shots';
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  const pages = ['index.html','preise.html','buchen.html','gutscheine.html','kinder.html','firmen.html','kartbahn.html','faq.html','kontakt.html','agb.html','widerruf.html','impressum.html','datenschutz.html','danke.html?typ=termin&ref=BK-1','404.html'];
  for (const p of pages) {
    await page.goto(base + '/' + p, { waitUntil: 'networkidle' });
    const sw = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
    const t = await page.title();
    console.log((sw[0] > sw[1] ? 'OVERFLOW ' : 'ok       ') + p + ' scrollWidth=' + sw[0] + ' title="' + t + '"');
    if (['index.html','buchen.html','preise.html','kinder.html','gutscheine.html'].includes(p)) await page.screenshot({ path: shots + '/m-' + p.replace('.html','') + '.png', fullPage: true });
  }
  // Desktop screenshot
  const d = await browser.newPage({ viewport: { width: 1366, height: 900 } });
  await d.goto(base + '/index.html', { waitUntil: 'networkidle' }); await d.screenshot({ path: shots + '/d-index.png', fullPage: true });
  await d.goto(base + '/buchen.html?angebot=kidsparty', { waitUntil: 'networkidle' }); await d.screenshot({ path: shots + '/d-buchen.png', fullPage: true });
  // Booking flow (mobile)
  await page.goto(base + '/buchen.html?angebot=tickets', { waitUntil: 'networkidle' });
  const tomorrow = new Date(Date.now() + 86400000 * 3); const iso = tomorrow.toISOString().slice(0, 10);
  await page.fill('#datum', iso); await page.dispatchEvent('#datum', 'change');
  await page.waitForSelector('.slot');
  const slots = await page.$$eval('.slot', b => b.map(x => x.textContent + (x.disabled ? '(x)' : '')));
  console.log('slots:', slots.join(' '));
  await page.click('.slot:has-text("16:00")');
  await page.fill('#teilnehmer', '6'); await page.fill('#kinder', '2');
  await page.fill('#vorname', 'Test'); await page.fill('#nachname', 'Fahrer'); await page.fill('#telefon', '0151 123456'); await page.fill('#email', 'test@example.org');
  await page.check('#agb'); await page.check('#einwilligung');
  const sum = await page.textContent('#sum-total'); console.log('Preis-Schätzung (6 Pers., 2 Kinder, 3 Fahrten, ' + iso + '):', sum);
  await page.click('#buchung button[type=submit]');
  await page.waitForSelector('.form-status[data-state]'); console.log('422 uhrzeit ->', (await page.textContent('.form-status')).trim().slice(0, 90));
  await page.waitForSelector('.slot'); await page.click('.slot:has-text("17:00")');
  await Promise.all([page.waitForNavigation(), page.click('#buchung button[type=submit]')]);
  console.log('nach Buchung:', page.url(), '| ref:', await page.textContent('#ref'), '|', await page.textContent('#danke-title'));
  await page.screenshot({ path: shots + '/m-danke.png', fullPage: true });
  // Kontaktformular
  await page.goto(base + '/kontakt.html', { waitUntil: 'networkidle' });
  await page.click('form[data-mk-form] button[type=submit]'); console.log('Kontakt leer ->', (await page.textContent('form[data-mk-form] .form-status')).trim());
  await page.fill('#k-name', 'Max'); await page.fill('#k-email', 'max@example.org'); await page.fill('#k-nachricht', 'Hallo'); await page.check('#k-einw');
  await Promise.all([page.waitForNavigation(), page.click('form[data-mk-form] button[type=submit]')]);
  console.log('Kontakt ->', page.url());
  // Map two-click
  await page.goto(base + '/kontakt.html', { waitUntil: 'networkidle' });
  console.log('iframes vor Klick:', await page.$$eval('iframe', f => f.length));
  console.log('errors:', errors.length ? errors : 'keine');
  await browser.close();
})().catch(e => { console.error('TESTFEHLER', e); process.exit(1); });
