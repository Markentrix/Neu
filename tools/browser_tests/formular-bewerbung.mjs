// Browser-Test (Playwright). Umgebung: PW_DIR (Ordner mit playwright), AXE_PATH (axe.min.js), BASE (Adresse der gebauten Seite, Standard http://localhost:8766).
// Zuvor dist/ bauen und lokal ausliefern: cd dist && python3 -m http.server 8766
const BASE = process.env.BASE || 'http://localhost:8766';
import { createRequire } from 'module';
const require = createRequire((process.env.PW_DIR||'/opt/node-tools')+'/'); const { chromium } = require('playwright');
const b = await chromium.launch(); const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage(); const posts=[];
await p.route('**/api/anfrage.php',async r=>{posts.push(JSON.parse(r.request().postData()||'{}')); await r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'});});
await p.addInitScript(()=>{try{localStorage.setItem('mx-consent',JSON.stringify({v:2,analytics:false,ts:Date.now()}))}catch(e){}});
await p.goto(BASE+'/partner-werden.html',{waitUntil:'networkidle'});
const f=p.locator('form[name=bewerbung]'); await f.locator('[name=name]').fill('Max Test'); await f.locator('[name=email]').fill('max@example.org'); await f.locator('select[name=rolle]').selectOption({index:1});
await f.locator('input[name=einwilligung]').check(); await f.locator('[type=submit]').click(); await p.waitForTimeout(400); console.log('ohne Haken gesendet:',posts.length);
await f.locator('input[name=unternehmer]').check(); await f.locator('[type=submit]').click(); await p.waitForTimeout(600); console.log('mit Haken gesendet:',posts.length,'Wert:',posts[0]&&posts[0].unternehmer);
await b.close();
