// Browser-Test (Playwright). Umgebung: PW_DIR (Ordner mit playwright), AXE_PATH (axe.min.js), BASE (Adresse der gebauten Seite, Standard http://localhost:8766).
// Zuvor dist/ bauen und lokal ausliefern: cd dist && python3 -m http.server 8766
const BASE = process.env.BASE || 'http://localhost:8766';
import { createRequire } from 'module';
const require = createRequire((process.env.PW_DIR||'/opt/node-tools')+'/'); const { chromium } = require('playwright');
const b = await chromium.launch(); const DAY=86400000, now=Date.now();
const cases=[
 ['kein Eintrag',null],
 ['Zustimmung aktuell',JSON.stringify({v:2,ts:now-DAY,analytics:true})],
 ['Ablehnung aktuell',JSON.stringify({v:2,ts:now-DAY,analytics:false})],
 ['Zustimmung abgelaufen (200 Tage)',JSON.stringify({v:2,ts:now-200*DAY,analytics:true})],
 ['Zustimmung alte Version (v1)',JSON.stringify({v:1,ts:now-DAY,analytics:true})],
 ['Zustimmung ohne Zeitstempel',JSON.stringify({v:2,analytics:true})],
 ['Zeitstempel in der Zukunft',JSON.stringify({v:2,ts:now+30*DAY,analytics:true})],
 ['analytics als Text "true"',JSON.stringify({v:2,ts:now-DAY,analytics:'true'})],
 ['beschädigtes JSON','{"v":2,"ts":'+now+',"analytics":tr'],
];
const bad=u=>/googletagmanager\.com|google-analytics\.com|metricool\.com/.test(u);
for (const [name,val] of cases) {
  const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage(); const reqs=[], posts=[];
  p.on('request',r=>reqs.push(r.url())); await p.route('**/api/anfrage.php',async r=>{posts.push(JSON.parse(r.request().postData()||'{}')); await r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'});});
  await p.addInitScript(([v])=>{ if(v!==null && !sessionStorage.getItem('__seeded')){ localStorage.setItem('mx-consent',v); sessionStorage.setItem('__seeded','1'); sessionStorage.setItem('mx-utm',JSON.stringify({utm_source:'alt'})); } },[val]);
  await p.goto(BASE+'/?utm_source=neu&utm_medium=test',{waitUntil:'networkidle'}); await p.waitForTimeout(1500);
  const banner=await p.locator('#mx-consent').isVisible().catch(()=>false);
  const trk=reqs.filter(bad).length; const utm=await p.evaluate(()=>sessionStorage.getItem('mx-utm'));
  const f=p.locator('form[name=rueckruf]').first(); await f.locator('[name=name]').fill('T'); await f.locator('[name=tel]').fill('0511123456'); await f.locator('input[name=einwilligung]').check(); await f.locator('input[name=unternehmer]').check(); await f.locator('[type=submit]').click(); await p.waitForTimeout(900);
  const ok=posts.length===1; const u=Object.keys(posts[0]||{}).filter(k=>/^utm_/.test(k)).map(k=>k+'='+posts[0][k]).join(',');
  const stored=await p.evaluate(()=>localStorage.getItem('mx-consent'));
  console.log(name.padEnd(34),'| Banner:',banner?'ja':'nein','| Tracker:',trk,'| mx-utm:',utm||'-','| Formular geht durch:',ok,'| Herkunft im Formular:',u||'keine','| Eintrag erhalten:',stored!==null);
  await ctx.close();
}
await b.close();
