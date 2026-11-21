// Browser-Test (Playwright). Umgebung: PW_DIR (Ordner mit playwright), AXE_PATH (axe.min.js), BASE (Adresse der gebauten Seite, Standard http://localhost:8766).
// Zuvor dist/ bauen und lokal ausliefern: cd dist && python3 -m http.server 8766
const BASE = process.env.BASE || 'http://localhost:8766';
import { createRequire } from 'module'; import { readFileSync } from 'fs'; import {execSync} from 'child_process';
const require = createRequire((process.env.PW_DIR||'/opt/node-tools')+'/'); const { chromium } = require('playwright');
const axeSrc = readFileSync((process.env.AXE_PATH||'axe.min.js'), 'utf8');
const pages=execSync("cd "+(process.env.DIST||'dist')+" && find . -name '*.html' | sed 's|^\\./||' | sort").toString().trim().split('\n').filter(x=>!x.includes('beispiel/')&&!x.startsWith('lp/')&&x!=='danke.html');
const b = await chromium.launch(); let bad=0;
for (const w of [390,1440]) {
 const ctx=await b.newContext({viewport:{width:w,height:900},reducedMotion:'reduce'}); const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.addInitScript(()=>{try{localStorage.setItem('mx_consent','{"analytics":false}')}catch(e){}});
 for (const u of pages) {
  await p.goto(BASE+'/'+u,{waitUntil:'load'});
  await p.addStyleTag({content:'.reveal{opacity:1!important;transform:none!important}'});
  await p.addScriptTag({content:axeSrc});
  const r=await p.evaluate(async()=>(await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>v.id+' ×'+v.nodes.length+' '+v.nodes[0].target.join(' ').slice(-70)));
  const ow=await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(r.length||ow){bad++;console.log(w,u,r,ow?'ÜBERLAUF':'')}
 }
 console.log(w,'fertig, JS-Fehler:',errs.length); await ctx.close();
}
console.log(pages.length,'Seiten, auffällig:',bad); await b.close();
