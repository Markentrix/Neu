const { chromium } = require('playwright'); const path=require('path');
(async()=>{const b=await chromium.launch(); for (const n of process.argv.slice(3)) { const p=await b.newPage({viewport:{width:1536,height:900}});
 await p.goto('file://'+path.join(__dirname,`bogen_${n}.html`),{waitUntil:'networkidle'}); await p.evaluate(()=>document.fonts.ready);
 await p.screenshot({path:path.join(process.argv[2],`bogen_${n}.png`),fullPage:true}); await p.close(); } await b.close();})();
