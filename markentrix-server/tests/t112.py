"""Messung auf Funnel-Seiten (Meta/Google): nichts vor der Einwilligung, Laden erst nach „Einverstanden“, Lead-Ereignis, Sicherheitsrichtlinie nur mit Messung, ID-Prüfung."""
import httpx, time, os, sys, json, asyncio
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
sfx=str(int(time.time())+1740)
basis={"name":"Messung","titel":"Mehr Aufträge","untertitel":"Test","nutzen":["A"],"button":"Jetzt anfragen","einwilligung_text":"Ich willige ein, dass Markentrix mich kontaktiert.","website_abfragen":False,"termin_anbieten":False,"telefon_pflicht":False,"aktiv":True,"rechtlich_geprueft":True}
ohne=f"ohne-{sfx}"; mit=f"mit-{sfx}"
chk("Ohne IDs wird angelegt",a.post("/api/admin/funnel",json={**basis,"slug":ohne}).status_code==200)
for feld,wert in (("meta_pixel_id","abc"),("google_tag_id","X-123"),("google_lead_label","AW-1")):
    r=a.post("/api/admin/funnel",json={**basis,"slug":f"bad-{feld[:4]}-{sfx}",feld:wert}); chk("Ungültige ID abgelehnt: "+feld,r.status_code in (400,422),r.text)
r=a.post("/api/admin/funnel",json={**basis,"slug":mit,"meta_pixel_id":"1234567890123","google_tag_id":"AW-123456789","google_lead_label":"AW-123456789/AbCdEfGhIj"}); chk("Mit IDs wird angelegt",r.status_code==200,r.text)
pub=httpx.Client(base_url=B,headers={**H,"User-Agent":"Mozilla/5.0 Safari"})
chk("Ohne IDs: keine Messung in der Antwort",pub.get(f"/api/public/funnel/{ohne}").json().get("tracking") is None)
tr=pub.get(f"/api/public/funnel/{mit}").json().get("tracking"); chk("Mit IDs: Messung in der Antwort",tr and tr["meta"]=="1234567890123" and tr["google"]=="AW-123456789",tr)
csp_ohne=httpx.get(B+f"/f/{ohne}").headers.get("content-security-policy",""); csp_mit=httpx.get(B+f"/f/{mit}").headers.get("content-security-policy","")
chk("Ohne Messung: strenge Richtlinie",csp_ohne and "facebook" not in csp_ohne and "googletagmanager" not in csp_ohne,csp_ohne)
chk("Mit Messung: Meta und Google erlaubt, sonst streng",("connect.facebook.net" in csp_mit and "googletagmanager.com" in csp_mit and "default-src 'self'" in csp_mit and "unsafe-eval" not in csp_mit),csp_mit)
# Browser
async def lauf():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        async def versuch(wahl):
            ctx=await br.new_context(viewport={"width":390,"height":800}); pg=await ctx.new_page(); angefragt=[]; fehler=[]
            async def blockiere(route):
                angefragt.append(route.request.url)
                u=route.request.url
                if u.endswith("fbevents.js"): await route.fulfill(status=200,content_type="application/javascript",body="window.__fb=window.__fb||[];var q=window.fbq&&window.fbq.queue||[];window.fbq.callMethod=function(){window.__fb.push([].slice.call(arguments))};q.forEach(function(x){window.fbq.callMethod.apply(null,x)});")
                elif "gtag/js" in u: await route.fulfill(status=200,content_type="application/javascript",body="window.__gt=true;")
                else: await route.fulfill(status=200,body="")
            await ctx.route("**/connect.facebook.net/**",blockiere); await ctx.route("**/www.googletagmanager.com/**",blockiere); await ctx.route("**/www.facebook.com/**",blockiere)
            pg.on("pageerror",lambda e: fehler.append(str(e)))
            await pg.goto(B+f"/f/{mit}"); await pg.wait_for_selector("#messung:not([hidden])",timeout=8000)
            vor=list(angefragt)
            if wahl=="ja": await pg.click("#messung button:has-text('Einverstanden')"); await pg.wait_for_timeout(800)
            else: await pg.click("#messung button:has-text('Ablehnen')"); await pg.wait_for_timeout(500)
            nach=list(angefragt)
            return pg,ctx,vor,nach,fehler,angefragt
        pg,ctx,vor,nach,fehler,alle=await versuch("nein")
        chk("Vor der Wahl keine Anfrage an Meta/Google",vor==[],vor); chk("Nach „Ablehnen“ ebenfalls nicht",nach==[],nach)
        chk("Banner weg nach Ablehnen",await pg.eval_on_selector("#messung","e=>e.hidden"),await pg.evaluate("[localStorage.getItem('mk-funnel-messung'), document.getElementById('messung').outerHTML.slice(0,200)]"))
        await pg.reload(); await pg.wait_for_timeout(800); chk("Ablehnung wird gemerkt, kein Banner",await pg.eval_on_selector("#messung","e=>e.hidden") and alle==[],alle); await ctx.close()
        pg,ctx,vor,nach,fehler,alle=await versuch("ja")
        chk("Vor der Wahl nichts geladen",vor==[],vor)
        chk("Nach „Einverstanden“ werden Meta und Google geladen",any("fbevents.js" in u for u in nach) and any("gtag/js" in u for u in nach),nach)
        chk("Keine JavaScript-Fehler",fehler==[],fehler)
        await ctx.close(); await br.close()
asyncio.run(lauf())
