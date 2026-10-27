"""Handy-Feinschliff 2: Bildschirmgrößen (320–768 px), dunkles Design, große Schrift, Wischen im Anruf-Modus, Anruf-Nachfrage im Admin, Ladegerüst, Vibration."""
import asyncio, httpx, time, subprocess, os, sys
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:400])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt"); sys.exit(0)
AXE=open(AXEJS).read()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+3122)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Wanda Wisch","email":f"wanda{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"wanda{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"WandaPasswort123456"})
ids=[]
for i in range(3):
    r=a.post("/api/admin/leads",json={"firma":f"Wisch{i} {sfx} GmbH","telefon":f"0511 88{i}{sfx}","ort":"Celle","plz":"29221","email":f"wisch{i}{sfx}@lead.de","vertriebspartner_id":pid}); assert r.status_code==200,r.text; ids.append(r.json()["id"])
sql(f"update leads set temperatur='heiss' where id in ({','.join(repr(x) for x in ids)})")
chk("Startseiten haben ein Ladegerüst",all('class="skelett"' in httpx.get(B+p).text for p in ("/vertrieb","/admin","/app")))
VERT="heute leads pipeline provisionen konto".split(); ADMIN="uebersicht meintag leads kunden einstellungen".split()
async def login(br,m,pw,pfad,w,dunkel=False):
    ctx=await br.new_context(viewport={"width":w,"height":800},bypass_csp=True,has_touch=True,is_mobile=w<700,color_scheme="dark" if dunkel else "light"); pg=await ctx.new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
    await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"); await pg.goto(B+pfad)
    await pg.wait_for_selector(".side a.nav, .tabbar",state="attached"); return ctx,pg,errs
async def pruefe(pg,name,pfad,seiten,w,extra=""):
    ueber=[];ax=[]
    for s in seiten:
        await pg.goto(B+pfad+"#"+s); await pg.wait_for_timeout(700)
        try: await pg.wait_for_load_state("networkidle",timeout=8000)
        except Exception: pass
        if extra: await pg.evaluate(extra)
        await pg.wait_for_timeout(300)
        o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        if o>0:
            wer=await pg.evaluate("[...document.querySelectorAll('body *')].filter(e=>!e.closest('thead')&&e.getBoundingClientRect().right>document.documentElement.clientWidth+1).slice(0,4).map(e=>e.tagName+'.'+e.className+' '+Math.round(e.getBoundingClientRect().right)+' '+(e.textContent||'').trim().slice(0,30))")
            ueber.append((s,o,wer))
        await pg.add_script_tag(content=AXE)
        v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
        if v: ax.append((s,v[:2]))
    chk(f"{name} {w}px{' '+extra[:22] if extra else ''}: kein seitliches Überlaufen",not ueber,ueber)
    chk(f"{name} {w}px{' '+extra[:22] if extra else ''}: Barrierefreiheit/Kontrast",not ax,ax)
async def swipe(pg,x0,x1,y=400):
    c=await pg.context.new_cdp_session(pg)
    await c.send("Input.dispatchTouchEvent",{"type":"touchStart","touchPoints":[{"x":x0,"y":y}]})
    for k in range(1,6): await c.send("Input.dispatchTouchEvent",{"type":"touchMove","touchPoints":[{"x":x0+(x1-x0)*k/5,"y":y}]})
    await c.send("Input.dispatchTouchEvent",{"type":"touchEnd","touchPoints":[]})
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for w in (320,360,412,768):
            ctx,pg,errs=await login(br,f"wanda{sfx}@v.de","WandaPasswort123456","/vertrieb",w,dunkel=True)
            await pruefe(pg,"Vertrieb dunkel","/vertrieb",VERT,w); chk(f"Vertrieb dunkel {w}px: keine JS-Fehler",not errs,errs); await ctx.close()
        ctx,pg,errs=await login(br,f"wanda{sfx}@v.de","WandaPasswort123456","/vertrieb",320)
        await pruefe(pg,"Vertrieb","/vertrieb",VERT,320,"document.documentElement.style.fontSize='125%'"); await ctx.close()
        ctx,pg,errs=await login(br,"chef@test.de",ADMPW,"/admin",360,dunkel=True)
        await pruefe(pg,"Admin dunkel","/admin",ADMIN,360); await ctx.close()
        # ---- Vertrieb: Wischen, Vibration, Ladebalken
        ctx,pg,errs=await login(br,f"wanda{sfx}@v.de","WandaPasswort123456","/vertrieb",390)
        await pg.evaluate("window.__v=[];navigator.vibrate=(m)=>{window.__v.push(m);return true}")
        await pg.evaluate("sessionStorage.setItem('mk-anrufmodus',JSON.stringify({modus:'heiss',filter:'',erledigt:[],start:Date.now()}))")
        await pg.goto(B+f"/vertrieb#lead/{ids[0]}"); await pg.wait_for_selector(".card:has-text('Anruf-Modus')",timeout=8000); await pg.wait_for_timeout(500)
        chk("Anruf-Modus nennt die Wischgesten",await pg.locator("text=wischen").count()>=1)
        await swipe(pg,330,60); await pg.wait_for_timeout(1500)
        h1=await pg.evaluate("location.hash"); chk("Nach links wischen: nächster Lead",h1.startswith("#lead/") and ids[0] not in h1,h1)
        await swipe(pg,60,330); await pg.wait_for_timeout(1500)
        chk("Nach rechts wischen: zurück zum vorigen Lead",await pg.evaluate("location.hash")==f"#lead/{ids[0]}",await pg.evaluate("location.hash"))
        chk("Wischen löst Vibration aus",len(await pg.evaluate("window.__v"))>=2,await pg.evaluate("window.__v"))
        await swipe(pg,200,230); await pg.wait_for_timeout(500); chk("Kurzes Wischen tut nichts",await pg.evaluate("location.hash")==f"#lead/{ids[0]}")
        async def lang(route):
            await asyncio.sleep(1.2); await route.continue_()
        await pg.route("**/api/vertrieb/heute*",lang)
        await pg.goto(B+"/vertrieb#heute"); await pg.wait_for_selector("#ladebalken",state="attached",timeout=4000); chk("Langsame Abfrage zeigt den Ladebalken",True)
        await pg.wait_for_selector("#ladebalken",state="detached",timeout=8000); chk("Ladebalken verschwindet wieder",True)
        chk("Keine JS-Fehler",not errs,errs); await ctx.close()
        # ---- Admin: Anruf-Nachfrage
        ctx,pg,errs=await login(br,"chef@test.de",ADMPW,"/admin",390)
        await pg.evaluate(f"localStorage.setItem('mk-anruf',JSON.stringify({{lid:'{ids[1]}',firma:'Wisch1 GmbH',t:Date.now()-60000,basis:'/api/admin/leads/'}}))")
        await pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(2000)
        chk("Admin: Nach dem Anruf kommt die Nachfrage",await pg.locator(".dlg:has-text('Wie lief der Anruf')").count()==1)
        chk("Admin: Dialog zeigt die Ergebnis-Knöpfe",await pg.locator(".dlg button:has-text('erreicht')").count()>=1)
        await pg.locator(".dlg button:has-text('Später')").click(); await pg.wait_for_timeout(300)
        chk("Admin: ‚Später‘ schließt den Dialog",await pg.locator(".dlg").count()==0)
        chk("Admin: Nachfrage nicht doppelt",await pg.evaluate("localStorage.getItem('mk-anruf')")is None)
        # Vertriebs-Merker wird im Admin ignoriert
        await pg.evaluate(f"localStorage.setItem('mk-anruf',JSON.stringify({{lid:'{ids[1]}',firma:'X',t:Date.now()-60000,basis:'/api/vertrieb/leads/'}}))")
        await pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(1500)
        chk("Admin ignoriert Merker des Vertriebs",await pg.locator(".dlg").count()==0)
        chk("Admin: keine JS-Fehler",not errs,errs); await ctx.close(); await br.close()
asyncio.run(main())
