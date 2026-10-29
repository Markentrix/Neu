import asyncio, httpx, time, re, email, subprocess, os, sys, json
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
sfx=str(int(time.time())+273)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt"); sys.exit(0)
AXE=open(AXEJS).read()
from PIL import Image
Image.new("RGB",(1600,1000),(30,120,200)).save("/var/tmp/pt/shopbild.png")
kA,cA,mA=neuer_kunde("Shopui")
dom=f"shopui{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kA}','shop',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"Neue Anfrage","name":"Shop UI"})
S="/api/kunde/shop"
cA.put(S+"/einstellungen",json={"aktiv":True,"ref_praefix":"UI","versand_pauschale":4.9,"versandfrei_ab":49,"abholung":True,"gutschein_aktiv":True})
cA.post(S+"/farben",json={"name":"Orange Silk","hex":"#e07a2a"}); cA.post(S+"/kategorien",json={"name":"Wohnen"})
for i in range(6):
    cA.post(S+"/produkte",json={"name":f"Artikel {i} mit einem ziemlich langen Namen für den Test","preis":1.5+i,"kategorie":"wohnen","farben":["orange-silk"],"aktiv":i<4,"kurz":"Kurz","lang":"Lang "*40})
W=httpx.Client(base_url=B,headers={"Host":dom})
for i in range(3):
    r=W.post("/siteapi/api/anfrage",headers={"Origin":"https://"+dom,"User-Agent":"Mozilla/5.0 Test","Content-Type":"application/json"},content=json.dumps({"typ":"bestellung","name":f"Kunde {i}","email":f"k{i}{sfx}@b.de","einwilligung":"ja","agb":"ja","lieferart":"abholung","zahlungsart":"abholung","positionen":[{"id":"artikel-0-mit-einem-ziemlich-langen-namen-fuer-den-test","name":"x","farbe":"orange-silk","menge":i+1}]}).encode())
    chk(f"Bestellung {i} per Website",r.status_code==200,r.text)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for w,dunkel in ((390,False),(390,True),(1280,False)):
            ctx=await br.new_context(viewport={"width":w,"height":800},bypass_csp=True,is_mobile=w<700,has_touch=w<700,color_scheme="dark" if dunkel else "light",accept_downloads=True); pg=await ctx.new_page()
            errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            await pg.goto(B+"/app#shop"); await pg.wait_for_selector("h1:has-text('Online-Shop')",timeout=8000); await pg.wait_for_timeout(600)
            chk(f"{w}px{' dunkel' if dunkel else ''}: Shop-Seite zeigt Bestellungen und Artikel",await pg.locator("text=Bestellungen (3 offen)").count()==1 and await pg.locator("summary:has-text('Artikel 3')").count()==1)
            chk(f"{w}px{' dunkel' if dunkel else ''}: Entwurf gekennzeichnet",await pg.locator("summary:has-text('(Entwurf)')").count()==2)
            for s in (None,"artikel","bestellung"):
                if s=="artikel":
                    await pg.locator("summary:has-text('Artikel 0')").click(); await pg.wait_for_timeout(200)
                if s=="bestellung":
                    await pg.locator("details:has(> summary:has-text('UI-'))").nth(1).locator("summary").click(); await pg.wait_for_timeout(200)
                o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                wer=await pg.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>document.documentElement.clientWidth+1).slice(0,4).map(e=>e.tagName+'.'+e.className)") if o>0 else []
                chk(f"{w}px{' dunkel' if dunkel else ''} {s or 'Start'}: kein seitliches Überlaufen",o<=0,wer)
                await pg.add_script_tag(content=AXE)
                v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
                chk(f"{w}px{' dunkel' if dunkel else ''} {s or 'Start'}: Barrierefreiheit/Kontrast",not v,v[:3])
            if w==1280:
                # Bild hochladen über die Oberfläche (Zuschnitt und WebP im Browser)
                await pg.locator("details:has(summary:has-text('Artikel 0')) input[type=file]").set_input_files("/var/tmp/pt/shopbild.png")
                await pg.locator("details:has(summary:has-text('Artikel 0')) button:has-text('Bild hochladen')").click(); await pg.wait_for_timeout(1500)
                n=sql(f"select count(*)||'|'||min(w)||'x'||min(h) from shop_bilder where kunden_id='{kA}'"); chk("Bild über die Oberfläche: 1200x900 WebP gespeichert",n=="1|1200x900",n)
                await pg.locator("summary:has-text('Artikel 0')").click(); await pg.wait_for_timeout(300)
                chk("Vorschau lädt im Portal",await pg.locator("img[src*='/api/kunde/shop/bilder/']").evaluate("e=>e.complete && e.naturalWidth>0"))
                # Bestellung über die Oberfläche bearbeiten
                d0=pg.locator("details:has(> summary:has-text('UI-'))").first      # neue Bestellungen sind schon aufgeklappt
                await d0.locator("select").first.select_option("abholbereit"); await d0.locator("input[placeholder^='z. B. Sa']").fill("Samstag 10 Uhr")
                await d0.locator("button:has-text('Speichern')").first.click(); await pg.wait_for_timeout(1500)
                st=sql(f"select status||'|'||abholtermin from shop_bestellungen where kunden_id='{kA}' order by erstellt_am desc limit 1"); chk("Bestellung per Oberfläche auf abholbereit",st=="abholbereit|Samstag 10 Uhr" or "abholbereit" in st,st)
                # Artikel anlegen über die Oberfläche
                f=pg.locator("details[open]:has(summary:has-text('Neuen Artikel')) ")
                await f.locator("input").first.fill("Neuer Artikel"); await f.locator("input[type=number]").first.fill("12.5")
                await f.locator("button:has-text('Anlegen')").click(); await pg.wait_for_timeout(1200)
                chk("Artikel über die Oberfläche angelegt",sql(f"select preis_cent from shop_produkte where kunden_id='{kA}' and schluessel='neuer-artikel'")=="1250")
            chk(f"{w}px{' dunkel' if dunkel else ''}: keine JavaScript-Fehler",not errs,errs)
            await ctx.close()
        await br.close()
asyncio.run(main())
