"""Erzeugt die Bilder für Hilfe und PDF-Anleitungen (kein Test): Screenshots der echten Oberfläche mit Beispieldaten. Aufruf: TESTS=hilfebilder bash tests/run.sh"""
import asyncio, httpx, time, re, email, os, sys
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:400])
AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt (npm i --prefix /var/tmp/axe axe-core@4.10.2)"); sys.exit(0)
AXE=open(AXEJS).read()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.5)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False})
k=a.post("/api/admin/kunden",json={"firma":"Autohaus Beispiel GmbH","ansprechpartner":"Max Mustermann","email":"kunde@werkzeug.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token("kunde@werkzeug.de"),"password":"InhaberPasswort1"})
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Beispiel","email":"vera@werkzeug.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token("vera@werkzeug.de"),"password":"VeraPasswort123"})
for i in range(5): a.post("/api/admin/leads",json={"firma":["Kfz Müller","Tischlerei Hahn","Friseur Schulz","Malerbetrieb Berger","Elektro Lange"][i],"telefon":f"0511 {time.time_ns()}","ort":"Celle","vertriebspartner_id":p})
import subprocess
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
kid=k["id"]
for i in range(8): sql(f"INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES ('{kid}','{["Familie Berger","Tischlerei Hahn","M. Schulz","Frau Lehmann","Herr Wagner","Kfz Peters","A. Neumann","Fam. Voigt"][i]}','a{i}@x.de','Bitte um Rückruf wegen eines Termins','{'telefon' if i%3==0 else 'website'}','{'beantwortet' if i<3 else 'neu'}',now()-interval '{i+1} days',true)")

KUNDE="heute uebersicht status briefing nachrichten freigaben assistent anfragen termine bewertungen kontakte dokumente unterlagen auswertung berichte belege anrufe website wochenangebote werbung automationen avv team hilfe einstellungen".split()
VERT="heute uebersicht leads pipeline angebote leitfaden uebung kunden provisionen konto".split()
import io
try:
    from PIL import Image
except Exception: Image=None
OUT="/home/claude/markentrix-server/portal/static/hilfe"
ADMIN="uebersicht kunden onboarding neu vertrieb leads belege websites einstellungen protokoll preise katalog".split()
# etwas mehr Beispieldaten
a.post("/api/admin/kunden",json={"firma":"Tischlerei Hahn","ansprechpartner":"Frau Hahn","email":"hahn@example.org","telefon":"05141 123","strasse":"Hauptstr. 2","plz":"29221","ort":"Celle","paket_code":"KI_ONE"})
async def knips(pg,rolle,seite,pfad,w,h_):
    await pg.goto(B+pfad+"#"+seite); await pg.wait_for_timeout(900)
    try: await pg.wait_for_load_state("networkidle",timeout=8000)
    except Exception: pass
    await pg.wait_for_timeout(500)
    # Scrollleisten/Hinweise ausblenden, Banner "App installieren" weg
    await pg.add_style_tag(content=".appbanner{display:none!important}")
    png=await pg.screenshot(full_page=False,type="png")
    os.makedirs(f"{OUT}/{rolle}",exist_ok=True)
    pfad_png=f"{OUT}/{rolle}/{seite}.png"
    if Image:
        im=Image.open(io.BytesIO(png)).convert("RGB"); im=im.quantize(colors=128,method=Image.Quantize.MEDIANCUT); im.save(pfad_png,optimize=True)
    else: open(pfad_png,"wb").write(png)
    return os.path.getsize(pfad_png)
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); n=0
        for rolle,m,pw_,pfad,seiten,w,hh in (("kunde","kunde@werkzeug.de","InhaberPasswort1","/app",KUNDE+["willkommen","dienste","kalender"],390,844),
                                           ("vertrieb","vera@werkzeug.de","VeraPasswort123","/vertrieb",VERT+["willkommen"],390,844),
                                           ("admin","chef@test.de",ADMPW,"/admin",ADMIN,1100,760)):
            ctx=await br.new_context(viewport={"width":w,"height":hh},bypass_csp=True,device_scale_factor=1); pg=await ctx.new_page()
            await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw_); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            await pg.goto(B+pfad); await pg.wait_for_selector(".side a.nav, .nav",state="attached",timeout=15000)
            try: await pg.click(".dlgoverlay >> text=Überspringen",timeout=2000)
            except Exception: pass
            for s in seiten:
                try: await knips(pg,rolle,s,pfad,w,hh); n+=1
                except Exception as e: print("FEHLER",rolle,s,str(e)[:120])
            await ctx.close()
        print("Bilder erzeugt:",n)
asyncio.run(main())
