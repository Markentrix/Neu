import httpx, time, re, email, subprocess, io
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def mail_an(adr, enthaelt=""):
    time.sleep(1.2)
    return [m for m in mails() if adr in str(m["To"]) and enthaelt in str(email.header.make_header(email.header.decode_header(m["Subject"] or ""))) + text(m)]
def token(adr):
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+44)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"

import base64, datetime
import asyncio, os
from playwright.async_api import async_playwright
os.makedirs("/var/tmp/pt/shots",exist_ok=True)
kA,cA,mA=neuer_kunde("Mobil")
a.post(f"/api/admin/kunden/{kA}/domains",json={"domain":f"mobil{sfx}.de","inhaber":"markentrix","ablauf_am":(datetime.date.today()+datetime.timedelta(days=9)).isoformat()}) if False else None
a.post(f"/api/admin/kunden/{kA}/freigaben-kunden",json={"titel":"Instagram-Beitrag Wochenangebote KW 43 mit langem Titel","art":"social","inhalt":"Text","veroeffentlichung_am":(datetime.date.today()+datetime.timedelta(days=1)).isoformat()})
pid=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vv{sfx}@k.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vv{sfx}@k.de"),"password":"VeraPasswort123"})
VERT=["heute","uebersicht","pipeline","leitfaden","angebote","kunden","provisionen","leads","konto"]
ADMIN=["uebersicht","heute","nachrichten","freigaben","aufgaben","kunden","kunde/"+kA,"leads","belege","einstellungen","preise","kennzahlen","auswertung","protokoll","team","katalog","status","compliance","onboarding","verwaltung","pipeline","vertrieb","hilfe"]
KUNDE=["heute","uebersicht","status","briefing","nachrichten","freigaben","assistent","anfragen","termine","bewertungen","kontakte","dokumente","unterlagen","auswertung","berichte","belege","anrufe","website","wochenangebote","werbung","automationen","avv","team","hilfe","einstellungen"]
JS="""()=>{const W=innerWidth,out=[];if(document.documentElement.scrollWidth>W+1)out.push('Seite breiter als Bildschirm: '+document.documentElement.scrollWidth);
for(const e of document.querySelectorAll('main *, .main *, body *')){const r=e.getBoundingClientRect();if(!r.width||!r.height)continue;if(e.closest('thead')||e.closest('.nur-sr')||e.classList.contains('nur-sr'))continue;const cs=getComputedStyle(e);if(cs.position==='fixed'||cs.visibility==='hidden')continue;
let p=e.parentElement,scroll=false;while(p){const o=getComputedStyle(p).overflowX;if((o==='auto'||o==='scroll')&&(p.matches('.tablewrap,.tabs,.side,.tabbar,pre,.chart,.trichter,.pipeline,.board,.kanban,[data-scroll]'))){scroll=true;break}p=p.parentElement}
if(!scroll&&r.right>W+2&&e.children.length===0&&(e.innerText||'').trim())out.push('ragt raus: <'+e.tagName.toLowerCase()+' class="'+e.className+'"> '+(e.innerText||'').trim().slice(0,40));
const t=(e.innerText||'').trim();if(e.children.length===0&&t.length>=12&&r.width<90&&r.height>70&&cs.display!=='none')out.push('zu schmal ('+Math.round(r.width)+'px): '+t.slice(0,40));}
const tb=document.querySelector('.tabbar');if(document.querySelector('.shell.mobilleiste')){if(!tb)out.push('Menüleiste fehlt');else{const r=tb.getBoundingClientRect();if(r.bottom<innerHeight-2||r.height<40||tb.querySelectorAll('a,button').length<4)out.push('Menüleiste nicht sichtbar/vollständig');for(const x of tb.querySelectorAll('a,button')){const q=x.getBoundingClientRect();if(q.left<0||q.right>innerWidth+1)out.push('Menüpunkt ragt raus: '+x.innerText)}}}if(document.body.innerText.includes('[object Object]'))out.push('[object Object] sichtbar');if(/undefined|NaN/.test(document.body.innerText))out.push('undefined/NaN sichtbar');return out.slice(0,8)}"""
async def shoot(ctx,start,namen,tag,login):
    pg=await ctx.new_page(); await login(pg); res={}
    for n in namen:
        await pg.goto(start+"#"+n); await pg.reload(); await pg.wait_for_load_state("networkidle"); await pg.wait_for_timeout(350)
        try: await pg.locator("text=Überspringen").first.click(timeout=300); await pg.wait_for_timeout(150)
        except Exception: pass
        res[n]=await pg.evaluate(JS); await pg.screenshot(path=f"/var/tmp/pt/shots/{tag}_{n.replace('/','_') or 'start'}.png",full_page=True)
    await pg.goto(start+"#"+namen[0]); await pg.wait_for_timeout(900)
    try: await pg.locator("text=Überspringen").first.click(timeout=600)
    except Exception: pass
    await pg.screenshot(path=f"/var/tmp/pt/shots/{tag}_viewport.png")
    try:
        await pg.locator(".tabbar button").click(); await pg.wait_for_selector(".dlg",timeout=3000); await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"/var/tmp/pt/shots/{tag}_menue.png"); res["menue"]=[]
    except Exception as e: res["menue"]=["Menü öffnet nicht: "+str(e)[:80]]
    await pg.close(); return res
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        ctx=await br.new_context(viewport={"width":360,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True)
        async def la(pg):
            await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        r=await shoot(ctx,B+"/admin",ADMIN,"admin",la)
        for n,v in r.items(): chk("Handy admin #"+n+" sauber",not v,v)
        ctx2=await br.new_context(viewport={"width":360,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True)
        async def lk(pg):
            await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
        r=await shoot(ctx2,B+"/app",KUNDE,"app",lk)
        for n,v in r.items(): chk("Handy Kundenportal #"+n+" sauber",not v,v)
        ctx3=await br.new_context(viewport={"width":360,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True)
        async def lv(pg):
            await pg.goto(B+"/"); await pg.fill("#e",f"vv{sfx}@k.de"); await pg.fill("#p","VeraPasswort123"); await pg.click("#b"); await pg.wait_for_url("**/vertrieb*")
        r=await shoot(ctx3,B+"/vertrieb",VERT,"vert",lv)
        for n,v in r.items(): chk("Handy Vertrieb #"+n+" sauber",not v,v)
        await br.close()
PW=open("/var/tmp/pt/adminpw").read().strip()
asyncio.run(main())
