"""App-Optik am Handy (Kundenportal): Kachel-Menü, Zurück-Pfeil, feste Kopfzeile, Abschnitte in Formulare & Buchung."""
import asyncio, httpx, time, re, email, subprocess, os, sys
from playwright.async_api import async_playwright
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
sfx=str(int(time.time())+3400)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt"); sys.exit(0)
AXE=open(AXEJS).read()
kA,cA,mA=neuer_kunde("Appopt")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kA}','website',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for dunkel in (False,True):
            ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True,is_mobile=True,has_touch=True,color_scheme="dark" if dunkel else "light")
            pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            n="dunkel" if dunkel else "hell"
            await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            await pg.goto(B+"/app#heute"); await pg.wait_for_selector(".tabbar"); await pg.wait_for_timeout(500)
            chk(f"{n}: auf Heute kein Zurück-Pfeil",await pg.locator(".zurueck").count()==0)
            await pg.click(".tabbar button"); await pg.wait_for_selector(".mehrblatt.kachel"); await pg.wait_for_timeout(300)
            cols=await pg.evaluate("getComputedStyle(document.querySelector('.mehrblatt .navliste')).gridTemplateColumns.split(' ').length")
            chk(f"{n}: Menü zeigt Kacheln (3 Spalten)",cols==3,cols)
            b=await pg.locator(".mehrblatt a.nav[href='#dienste']").bounding_box(); chk(f"{n}: Kachel groß genug zum Tippen",b["height"]>=80 and b["width"]>=90,b)
            sym=await pg.evaluate("getComputedStyle(document.querySelector('.mehrblatt a.nav[href=\"#dienste\"]'),'::before').content"); chk(f"{n}: Kachel hat ein Symbol",len(sym)>2 and "•" not in sym,sym)
            o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk(f"{n}: Menü ohne seitliches Überlaufen",o<=0,o)
            await pg.add_script_tag(content=AXE)
            v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))"); chk(f"{n}: Menü Barrierefreiheit",not v,v[:3])
            await pg.screenshot(path=f"/var/tmp/pt/app_menu_{n}.png")
            await pg.click(".mehrblatt a.nav[href='#dienste']"); await pg.wait_for_selector("h1:has-text('Website-Dienste')"); await pg.wait_for_timeout(400)
            chk(f"{n}: Unterseite hat Zurück-Pfeil",await pg.locator(".zurueck").count()==1)
            top=await pg.evaluate("(()=>{const e=document.querySelector('.main>.top');return getComputedStyle(e).position})()"); chk(f"{n}: Kopfzeile bleibt oben stehen",top=="sticky",top)
            chk(f"{n}: Abschnitte sind zugeklappt",await pg.locator("details.abschnitt").count()>=5 and await pg.locator("details.abschnitt[open]").count()<=1)
            chk(f"{n}: Schnellzugriff vorhanden",await pg.locator(".schnell button").count()>=3)
            await pg.locator(".schnell button:has-text('Kontaktformular')").click(); await pg.wait_for_timeout(500)
            chk(f"{n}: Schnellzugriff öffnet den Abschnitt",await pg.locator("details.abschnitt[open]:has(h2:has-text('Kontaktformular'))").count()==1 and await pg.locator("input[placeholder^='info@deinefirma']").first.is_visible())
            o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk(f"{n}: Dienste ohne seitliches Überlaufen",o<=0,o)
            await pg.add_script_tag(content=AXE)
            v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))"); chk(f"{n}: Dienste Barrierefreiheit",not v,v[:3])
            await pg.screenshot(path=f"/var/tmp/pt/app_dienste_{n}.png")
            await pg.locator(".zurueck").click(); await pg.wait_for_timeout(500)
            chk(f"{n}: Zurück-Pfeil führt zurück","#dienste" not in pg.url)
            chk(f"{n}: keine JavaScript-Fehler",not errs,errs)
            await ctx.close()
        await br.close()
asyncio.run(main())
