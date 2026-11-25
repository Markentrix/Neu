"""Website-Einrichtungs-Assistent im Kundenportal: Logo-Upload durch den Kunden, Schritt für Schritt bis zur Testmail."""
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
sfx=str(int(time.time())+3300)
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
Image.new("RGB",(300,100),(30,120,200)).save("/var/tmp/pt/logo133.png")
Image.new("RGB",(30,30),(200,0,0)).save("/var/tmp/pt/logo133.gif")
kA,cA,mA=neuer_kunde("Einricht")
dom=f"einricht{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kA}','website',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
import base64
P="/api/kunde/website-dienste/logo"
b64=lambda f: base64.b64encode(open(f,"rb").read()).decode()
chk("Logo: GIF wird abgelehnt",cA.put(P,json={"logo_base64":b64("/var/tmp/pt/logo133.gif")}).status_code==400)
chk("Logo: kein Base64 wird abgelehnt",cA.put(P,json={"logo_base64":"das ist kein logo!!!!!!!!!!"}).status_code==400)
chk("Logo: zu groß wird abgelehnt",cA.put(P,json={"logo_base64":base64.b64encode(b"\x89PNG\r\n\x1a\n"+b"0"*(420*1024)).decode()}).status_code==400)
chk("Checkliste: Logo noch offen",not [p for p in cA.get("/api/kunde/website-dienste").json()["start"]["punkte"] if p["code"]=="logo"][0]["erledigt"])
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for w in (390,1280):
            ctx=await br.new_context(viewport={"width":w,"height":800},bypass_csp=True,is_mobile=w<700,has_touch=w<700,accept_downloads=True)
            pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            cA.put("/api/kunde/website-dienste/mail",json={"aktiv":False,"empfaenger":"","betreff":"","name":"","signatur":"","bewertung":False})
            sql(f"update kunden set logo=null, logo_typ=null where id='{kA}'"); sql(f"delete from mail_protokoll where kunden_id='{kA}' and art='test'")
            await pg.goto(B+"/app#heute"); await pg.wait_for_selector("h2:has-text('Ihre Website einrichten')",timeout=8000)
            chk(f"{w}px: Heute zeigt die Einrichtungs-Karte",await pg.locator("a[href='#einrichten']").count()>=1)
            await pg.locator("a.btn[href='#einrichten']").first.click(); await pg.wait_for_selector("h1:has-text('Website einrichten')",timeout=8000)
            await pg.wait_for_selector("text=Schritt 1 von 5",timeout=5000)
            chk(f"{w}px: Schritt 1 fragt nach der Mailadresse",await pg.locator("h2:has-text('Wohin sollen Anfragen')").count()==1)
            await pg.locator("input[aria-label='E-Mail-Adresse für Anfragen']").fill("kein-mail")
            await pg.locator("button:has-text('Speichern und weiter')").click(); await pg.wait_for_timeout(500)
            chk(f"{w}px: ungültige Adresse zeigt Fehler",await pg.locator("text=gültige E-Mail").count()==1)
            await pg.locator("input[aria-label='E-Mail-Adresse für Anfragen']").fill(f"chef@{dom}")
            await pg.locator("button:has-text('Speichern und weiter')").click(); await pg.wait_for_selector("h2:has-text('Ihr Logo')",timeout=6000)
            chk(f"{w}px: Schritt 2 (Logo) folgt automatisch",await pg.locator("text=Schritt 2 von 5").count()==1)
            o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk(f"{w}px: kein seitliches Überlaufen",o<=0,o)
            await pg.add_script_tag(content=AXE)
            v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))"); chk(f"{w}px: Barrierefreiheit",not v,v[:3])
            await pg.locator("button:has-text('Logo hochladen')").click(); await pg.wait_for_timeout(400)
            chk(f"{w}px: ohne Datei kommt eine Meldung",await pg.locator("text=Datei auswählen").count()==1)
            await pg.locator("input[type=file]").set_input_files("/var/tmp/pt/logo133.png")
            await pg.locator("button:has-text('Logo hochladen')").click(); await pg.wait_for_selector("h2:has-text('Abschluss unter jeder Mail')",timeout=6000)
            chk(f"{w}px: Logo gespeichert, Schritt 3 (Signatur)",sql(f"select logo_typ from kunden where id='{kA}'")=="image/png")
            chk(f"{w}px: Signatur ist vorbelegt",f"Einricht {sfx}" in await pg.locator("textarea").input_value())
            await pg.locator("button:has-text('Speichern und weiter')").click(); await pg.wait_for_selector("h2:has-text('Testmail')",timeout=6000)
            n0=len(mail_an(f"chef@{dom}"))
            await pg.locator("button:has-text('Testmail senden')").click(); await pg.wait_for_selector("h2:has-text('Testanfrage')",timeout=8000)
            chk(f"{w}px: Testmail angekommen, letzter Schritt",len(mail_an(f"chef@{dom}"))>n0 and await pg.locator("text=Schritt 5 von 5").count()==1)
            await pg.goto(B+"/app#dienste"); await pg.wait_for_selector("a.btn[href='#einrichten']",timeout=6000)
            chk(f"{w}px: Start-Checkliste verweist auf den Assistenten",True)
            chk(f"{w}px: keine JavaScript-Fehler",not errs,errs)
            await ctx.close()
        await br.close()
asyncio.run(main())
