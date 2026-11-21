// Browser-Test (Playwright). Umgebung: PW_DIR (Ordner mit playwright), AXE_PATH (axe.min.js), BASE (Adresse der gebauten Seite, Standard http://localhost:8766).
// Zuvor dist/ bauen und lokal ausliefern: cd dist && python3 -m http.server 8766
const BASE = process.env.BASE || 'http://localhost:8766';
import { createRequire } from 'module';
const require = createRequire((process.env.PW_DIR||'/opt/node-tools')+'/'); const { chromium } = require('playwright');
const b = await chromium.launch(); const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage();
const reqs=[], posts=[]; p.on('request',r=>reqs.push(r.url()));
await p.route('**/api/anfrage.php',async r=>{posts.push(JSON.parse(r.request().postData()||'{}')); await r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'});});
const bad=u=>/googletagmanager\.com|google-analytics\.com|metricool\.com/.test(u);
async function state(label){
  const ck=(await ctx.cookies()).map(c=>c.name); const ss=await p.evaluate(()=>({utm:sessionStorage.getItem('mx-utm'),consent:localStorage.getItem('mx-consent')}));
  console.log(label,'| Tracker-Anfragen:',reqs.filter(bad).length,'| Cookies:',JSON.stringify(ck),'| mx-utm:',ss.utm,'| Einwilligung gespeichert:',ss.consent);
}
async function sendRueckruf(){ const f=p.locator('form[name=rueckruf]').first(); await f.locator('[name=name]').fill('Max Test'); await f.locator('[name=tel]').fill('0511123456'); await f.locator('input[name=einwilligung]').check(); await f.locator('input[name=unternehmer]').check(); posts.length=0; await f.locator('[type=submit]').click(); await p.waitForLoadState('networkidle'); await p.waitForTimeout(500); const k=Object.keys(posts[0]||{}).filter(k=>/^utm_/.test(k)); return k.length?k.map(x=>x+'='+posts[0][x]).join(','):'keine Herkunftsdaten'; }
await p.goto(BASE+'/?utm_source=newsletter&utm_medium=mail&utm_campaign=test',{waitUntil:'networkidle',referer:'https://www.google.com/search?q=x'}); await p.waitForTimeout(800);
console.log('Banner sichtbar:',await p.locator('#mx-consent').isVisible());
await state('1) vor Banner-Klick       ');
console.log('   Formular ohne Einwilligung -> ', await sendRueckruf());
await p.goto(BASE+'/?utm_source=newsletter&utm_medium=mail&utm_campaign=test',{waitUntil:'networkidle'}); await p.click('#mxc-no'); await p.waitForTimeout(500); await state('2) nach „Nur notwendige“');
await p.goto(BASE+'/?utm_source=newsletter&utm_medium=mail&utm_campaign=test',{waitUntil:'networkidle'}); await p.waitForTimeout(500);
console.log('   Formular nach „Nur notwendige“ -> ', await sendRueckruf());
await p.evaluate(()=>{localStorage.removeItem('mx-consent')}); await p.goto(BASE+'/?utm_source=newsletter&utm_medium=mail&utm_campaign=test',{waitUntil:'networkidle'}); await p.waitForTimeout(400); await p.click('#mxc-yes'); await p.waitForTimeout(1500);
await state('3) nach „Alle akzeptieren“ ');
await p.goto(BASE+'/?utm_source=newsletter&utm_medium=mail&utm_campaign=test',{waitUntil:'networkidle'}); await p.waitForTimeout(500);
console.log('   Formular mit Einwilligung -> ', await sendRueckruf());
await b.close();
