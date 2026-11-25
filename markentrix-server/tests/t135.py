"""Admin: Änderungshistorie eines Kunden zeigt 5 Einträge, per Knopf je 20 weitere."""
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
sfx=str(int(time.time())+3500)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt"); sys.exit(0)
AXE=open(AXEJS).read()
k=a.post("/api/admin/kunden",json={"firma":f"Historie {sfx}","ansprechpartner":"Hans Hist","email":f"hist{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle"}).json()["id"]
for i in range(40): a.put(f"/api/admin/kunden/{k}/branding",json={"farbe":"#%06x"%(i*1000+5)})
n=len(a.get(f"/api/admin/kunden/{k}/historie").json()); chk("Vorbereitung: mehr als 30 Einträge",n>30,n)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for w in (390,1280):
            ctx=await br.new_context(viewport={"width":w,"height":900},bypass_csp=True,is_mobile=w<700,has_touch=w<700)
            pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",open("/var/tmp/pt/adminpw").read().strip()); await pg.click("#b"); await pg.wait_for_url("**/admin*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            await pg.goto(B+f"/admin#kunde/{k}"); await pg.wait_for_selector("h2:has-text('Änderungshistorie')",timeout=8000); await pg.wait_for_timeout(500)
            karte=pg.locator(".card:has(> h2:has-text('Änderungshistorie'))")
            rows=lambda: karte.locator("tbody tr").count()
            chk(f"{w}px: zuerst nur 5 Einträge",await rows()==5,await rows())
            await karte.locator("button:has-text('Nächste 20')").click(); await pg.wait_for_timeout(200)
            chk(f"{w}px: nach Klick 25 Einträge",await rows()==25,await rows())
            await karte.locator("button:has-text('Nächste')").click(); await pg.wait_for_timeout(200)
            chk(f"{w}px: noch einmal: alle vorhandenen (max. n)",await rows()==min(45,n),await rows())
            await karte.locator("button:has-text('Wieder einklappen')").click(); await pg.wait_for_timeout(200)
            chk(f"{w}px: einklappen zeigt wieder 5",await rows()==5)
            await karte.locator("select[aria-label='Nach Aktion filtern']").select_option("kunde_angelegt"); await pg.wait_for_timeout(200)
            chk(f"{w}px: Filter nach Aktion",await rows()==1,await rows())
            await karte.locator("select[aria-label='Nach Aktion filtern']").select_option("branding_geaendert"); await pg.wait_for_timeout(200)
            chk(f"{w}px: Filter mit vielen Treffern zeigt wieder nur 5",await rows()==5 and await karte.locator("button:has-text('Nächste')").count()==1)
            await karte.locator("select[aria-label='Nach Person filtern']").select_option(index=1); await pg.wait_for_timeout(200)
            chk(f"{w}px: Filter nach Person",await rows()>=1)
            await karte.locator("select[aria-label='Nach Aktion filtern']").select_option(""); await karte.locator("select[aria-label='Nach Person filtern']").select_option(""); await pg.wait_for_timeout(200)
            o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk(f"{w}px: kein seitliches Überlaufen",o<=0,o)
            chk(f"{w}px: keine JavaScript-Fehler",not errs,errs)
            await ctx.close()
        await br.close()
asyncio.run(main())
