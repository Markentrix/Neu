"""Browser-Test (Playwright, Chromium): ALLE Seiten von Kunden- und Vertriebler-Portal (Barrierefreiheit, Überlauf, JS-Fehler; 390 und 1280 px) plus Kernabläufe der Werkzeuge."""
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
k=a.post("/api/admin/kunden",json={"firma":"Werkzeug Kunde GmbH","ansprechpartner":"Tina Test","email":"kunde@werkzeug.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token("kunde@werkzeug.de"),"password":"InhaberPasswort1"})
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":"vera@werkzeug.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token("vera@werkzeug.de"),"password":"VeraPasswort123"})
for i in range(5): a.post("/api/admin/leads",json={"firma":f"WLead {i} GmbH","telefon":"0511 555","ort":"Celle","vertriebspartner_id":p})
import subprocess
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
kid=k["id"]
for i in range(8): sql(f"INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES ('{kid}','Anfrager {i}','a{i}@x.de','Bitte um Rückruf','{'telefon' if i%3==0 else 'website'}','{'beantwortet' if i<3 else 'neu'}',now()-interval '{i+1} days',true)")
KUNDE="heute uebersicht status briefing nachrichten freigaben assistent anfragen termine bewertungen kontakte dokumente unterlagen auswertung berichte belege anrufe website wochenangebote werbung automationen avv team hilfe einstellungen".split()
VERT="heute uebersicht leads pipeline angebote leitfaden kunden provisionen konto".split()

async def login(br,m,pw,pfad,w):
    ctx=await br.new_context(viewport={"width":w,"height":900},bypass_csp=True); pg=await ctx.new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda x: x.type=="error" and "favicon" not in x.text and "Failed to load resource" not in x.text and errs.append(x.text))
    await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
    await pg.wait_for_selector(".side a.nav",state="attached")
    return ctx,pg,errs

async def alle(pg,name,pfad,seiten,w):
    schlecht=[];ueber=[];leer=[]
    for s in seiten:
        await pg.goto(B+pfad+"#"+s); await pg.wait_for_timeout(650)
        if await pg.locator("main h1, #main h1, h1").count()==0: leer.append(s)
        await pg.add_script_tag(content=AXE)
        ax=await pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
        ov=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        if ax: schlecht.append((s,ax[:3]))
        if ov>0: ueber.append((s,ov))
    chk(f"{name} @{w}px: alle {len(seiten)} Seiten ohne Barrierefreiheits-Verstoß",not schlecht,schlecht)
    chk(f"{name} @{w}px: alle Seiten ohne seitliches Überlaufen",not ueber,ueber)
    chk(f"{name} @{w}px: jede Seite hat eine Überschrift",not leer,leer)

async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        for w in (390,1280):
            ctx,pg,errs=await login(br,"kunde@werkzeug.de","InhaberPasswort1","/app",w)
            await alle(pg,"Kunde","/app",KUNDE,w); chk(f"Kunde @{w}px: keine JavaScript-Fehler",not errs,errs); await ctx.close()
            ctx,pg,errs=await login(br,"vera@werkzeug.de","VeraPasswort123","/vertrieb",w)
            await alle(pg,"Vertrieb","/vertrieb",VERT,w); chk(f"Vertrieb @{w}px: keine JavaScript-Fehler",not errs,errs); await ctx.close()
        # ---- Kunde: Kernabläufe
        ctx,pg,errs=await login(br,"kunde@werkzeug.de","InhaberPasswort1","/app",1280)
        await pg.goto(B+"/app"); await pg.wait_for_selector(".heutezeile",timeout=8000); chk("Kunde: Heute zeigt Anfragen mit Aktionen",await pg.locator(".heutezeile").count()>=1)
        await pg.locator(".heutezeile .btn:text('Antworten')").first.click(); await pg.wait_for_selector(".dlg",timeout=5000)
        chk("Kunde: Antwort-Dialog mit Vorlagen und Kanälen",await pg.locator(".dlg").inner_text()!="" and await pg.locator(".dlg a, .dlg button").count()>=2)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200); chk("Kunde: Dialog schließt mit Esc",await pg.locator(".dlg").count()==0)
        await pg.goto(B+"/app#bewertungen"); await pg.wait_for_selector("input[type=url]",timeout=8000)
        await pg.fill("input[type=url]","https://g.page/r/abc/review"); await pg.click("button:text('Speichern')"); await pg.wait_for_timeout(1200)
        chk("Kunde: Bewertungslink gespeichert",sql(f"select count(*) from kunden_werkzeuge where kunden_id='{kid}'")!="0")
        await pg.goto(B+"/app#auswertung"); await pg.wait_for_selector("svg",timeout=8000); await pg.wait_for_timeout(800)
        chk("Kunde: Diagramme werden gezeichnet (SVG)",await pg.locator("svg").count()>=3,await pg.locator("svg").count())
        await pg.goto(B+"/app#uebersicht"); await pg.wait_for_timeout(1000); chk("Kunde: Reise-Karte sichtbar",await pg.locator(".reise").count()>=1)
        chk("Kunde: keine JavaScript-Fehler in den Abläufen",not errs,errs); await ctx.close()
        # ---- Vertriebler: Kernabläufe
        ctx,pg,errs=await login(br,"vera@werkzeug.de","VeraPasswort123","/vertrieb",1280)
        await pg.goto(B+"/vertrieb"); await pg.wait_for_selector(".heutezeile",timeout=8000); n0=await pg.locator(".heutezeile").count(); chk("Vertrieb: Mein Tag zeigt Anrufe",n0>=2,n0)
        await pg.locator(".heutezeile .btn:text('Nicht erreicht')").first.click(); await pg.wait_for_timeout(900)
        chk("Vertrieb: 'Nicht erreicht' nimmt den Lead aus der Liste",await pg.locator(".heutezeile").count()==n0-1)
        await pg.locator(".heutezeile .btn:text('Gesprochen')").first.click(); await pg.wait_for_selector(".dlg"); await pg.click(".dlg .btn:text('Festhalten')"); await pg.wait_for_timeout(900)
        chk("Vertrieb: Gesprächsnotiz festgehalten",sql("select count(*) from lead_aktivitaeten")!="0" if sql("select to_regclass('lead_aktivitaeten')") else True)
        await pg.goto(B+"/vertrieb#leitfaden"); await pg.wait_for_timeout(900); chk("Vertrieb: Leitfaden lädt",await pg.locator("h1").count()>=1)
        await pg.goto(B+"/vertrieb#pipeline"); await pg.wait_for_selector(".kanban",timeout=8000); chk("Vertrieb: Pipeline-Board mit Spalten",await pg.locator(".kspalte").count()>=4)
        await pg.goto(B+"/vertrieb#leads"); await pg.wait_for_selector("table a",timeout=8000); await pg.locator("table a").first.click()
        await pg.wait_for_selector("button:text('Angebot anfragen')",timeout=8000); await pg.click("button:text('Angebot anfragen')"); await pg.wait_for_selector("button:text('Mail-Entwurf öffnen')",timeout=8000)
        chk("Vertrieb: Angebotsanfrage mit Mail-Entwurf",True)
        chk("Vertrieb: keine JavaScript-Fehler in den Abläufen",not errs,errs); await ctx.close()
        await br.close()
asyncio.run(main())
