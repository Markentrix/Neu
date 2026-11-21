// Browser-Test (Playwright). Umgebung: PW_DIR (Ordner mit playwright), AXE_PATH (axe.min.js), BASE (Adresse der gebauten Seite, Standard http://localhost:8766).
// Zuvor dist/ bauen und lokal ausliefern: cd dist && python3 -m http.server 8766
const BASE = process.env.BASE || 'http://localhost:8766';
import { createRequire } from 'module';
const require = createRequire((process.env.PW_DIR||'/opt/node-tools')+'/'); const { chromium } = require('playwright');
const b = await chromium.launch(); const B=BASE;
async function ctxPage(){ const ctx=await b.newContext({viewport:{width:1280,height:900}}); const p=await ctx.newPage(); const reqs=[]; p.on('request',r=>reqs.push(r.url()));
  const posts=[]; await p.route('**/api/anfrage.php',async r=>{posts.push(JSON.parse(r.request().postData()||'{}')); await r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'});});
  return {ctx,p,reqs,posts}; }
const forms=[
 {name:'Kontakt',url:'/kontakt.html',sel:'form[name=kontakt]',fill:{'[name=name]':'Max Test','[name=email]':'max@example.org'},extra:async(p)=>{ await p.selectOption('form[name=kontakt] select[name=thema]',{index:1}).catch(()=>{}); }},
 {name:'Rückruf (Start)',url:'/',sel:'form[name=rueckruf]',fill:{'[name=name]':'Max Test','[name=tel]':'0511123456'}},
 {name:'Rückruf (Kontakt)',url:'/kontakt.html',sel:'form[name=rueckruf]',fill:{'[name=name]':'Max Test','[name=tel]':'0511123456'}},
 {name:'Bewerbung',url:'/partner-werden.html',sel:'form[name=bewerbung]',fill:{'[name=name]':'Max Test','[name=email]':'max@example.org'}},
 {name:'Website-Check',url:'/website-check.html',sel:'form[name=website-check-bericht]',fill:{'[name=name]':'Max Test','[name=email]':'max@example.org'},reveal:true},
];
for (const f of forms) {
  const {ctx,p,posts}=await ctxPage(); await p.addInitScript(()=>{try{localStorage.setItem('mx-consent',JSON.stringify({v:2,analytics:false,ts:Date.now()}))}catch(e){}});
  await p.goto(B+f.url,{waitUntil:'networkidle'}); await p.addStyleTag({content:'.reveal{opacity:1!important;transform:none!important}'});
  const form=p.locator(f.sel).first();
  if(f.reveal) await p.evaluate(s=>{const e=document.querySelector(s);let n=e;while(n&&n!==document.body){n.hidden=false;n=n.parentElement}},f.sel);
  for (const [s,v] of Object.entries(f.fill)) await form.locator(s).fill(v);
  if(f.extra) await f.extra(p);
  const hasBox=await form.locator('input[name=unternehmer]').count(); const pre=await form.locator('input[name=unternehmer]').isChecked();
  await form.locator('input[name=einwilligung]').check();
  await form.locator('[type=submit]').click(); await p.waitForTimeout(500);
  const failed=posts.length===0; const err=await form.locator('input[name=unternehmer]').evaluate(e=>(e.closest('.check')?.querySelector('.error')?.textContent)||'');
  await form.locator('input[name=unternehmer]').check(); await form.locator('[type=submit]').click(); await p.waitForTimeout(700);
  console.log(f.name.padEnd(20),'Box vorhanden:',!!hasBox,'| vorangekreuzt:',pre,'| ohne Haken abgelehnt:',failed,'| Meldung:',JSON.stringify(err.slice(0,50)),'| mit Haken gesendet:',posts.length===1,'| Wert im Payload:',posts[0]&&posts[0].unternehmer);
  await ctx.close();
}
await b.close();
