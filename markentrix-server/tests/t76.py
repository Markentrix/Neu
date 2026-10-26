"""Browser-Test: Admin-Portal komplett (390 und 1280 px) plus neue Masken (Steuerung, Lead, Freigabe, Nachricht, Domain)."""
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
import subprocess
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+265)
KM=f"k{sfx}@bt.de"; VM=f"v{sfx}@bt.de"
k=a.post("/api/admin/kunden",json={"firma":f"Browser Kunde {sfx}","ansprechpartner":"Tina Test","email":KM,"telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(KM),"password":"InhaberPasswort1"})
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Browser","email":VM,"status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(VM),"password":"VeraPasswort123"})
lid=a.post("/api/admin/leads",json={"firma":f"Browser Lead {sfx}","telefon":f"0511 {time.time_ns()}","email":f"bl{sfx}@bl{sfx}.de","ort":"Celle","vertriebspartner_id":p}).json()["id"]
a.post("/api/admin/vertrieb/steuerung" if False else "/api/admin/leads/"+lid+"/notiz",json={}) if False else None
fid=a.post(f"/api/admin/kunden/{kid}/freigaben-kunden",json={"titel":"Browser Beitrag","art":"social","inhalt":"Text","veroeffentlichung_am":"2030-01-02"}).json()["id"]
ADMIN="uebersicht meintag postfach freigaben aufgaben kennzahlen kunden onboarding vertraege zufriedenheit neu vertrieb leads pipeline auswertung funnel dsgvo websites belege preise compliance katalog einstellungen protokoll".split()
os.makedirs("/var/tmp/pt/shots",exist_ok=True)
async def login(br,m,pw,pfad,w):
    ctx=await br.new_context(viewport={"width":w,"height":900 if w>500 else 800},bypass_csp=True); pg=await ctx.new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda x: x.type=="error" and "favicon" not in x.text and "Failed to load resource" not in x.text and errs.append(x.text))
    await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*"); await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"); await pg.goto(B+pfad)
    await pg.wait_for_selector(".side a.nav",state="attached")
    return ctx,pg,errs
async def pruefe(pg,name,pfad,seiten,w):
    schlecht=[];ueber=[];leer=[]
    for s in seiten:
        await pg.goto(B+pfad+"#"+s); await pg.wait_for_timeout(700)
        try: await pg.wait_for_load_state("networkidle",timeout=8000)      # langsame Rechner: erst prüfen, wenn die Seite fertig geladen und beschriftet ist
        except Exception: pass
        await pg.wait_for_timeout(600)
        if await pg.locator("h1").count()==0: leer.append(s)
        await pg.add_script_tag(content=AXE)
        ax=await pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
        if ax: schlecht.append((s,ax[:3]))
        ov=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        if ov>0: ueber.append((s,ov))
        await pg.screenshot(path=f"/var/tmp/pt/shots/{name}_{w}_{s}.png")
    chk(f"{name} @{w}px: Barrierefreiheit",not schlecht,schlecht); chk(f"{name} @{w}px: kein Überlaufen",not ueber,ueber); chk(f"{name} @{w}px: Überschrift vorhanden",not leer,leer)
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        for w in (390,1280):
            ctx,pg,errs=await login(br,"chef@test.de",ADMPW,"/admin",w)
            await pruefe(pg,"Admin","/admin",ADMIN,w); chk(f"Admin @{w}px: keine JavaScript-Fehler",not errs,errs)
            # Steuerung und Sperrliste
            await pg.goto(B+"/admin#leads"); await pg.wait_for_selector("h2:text('Steuerung und Sperrliste')",timeout=8000)
            chk(f"Admin @{w}px: Steuerungskarte sichtbar",True)
            await pg.check("#st_auto"); await pg.click(".card:has(h2:text('Steuerung und Sperrliste')) button:text-is('Speichern')"); await pg.wait_for_timeout(800)
            chk(f"Admin @{w}px: Steuerung speichern",a.get("/api/admin/vertrieb/steuerung").json()["auto_zuweisung"] is True)
            a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":False,"reaktionsstunden":24,"preise_sichtbar":False})
            # Zum Kunden machen
            await pg.goto(B+"/admin#lead/"+lid); await pg.wait_for_selector("summary:text('Mehr')",timeout=8000); await pg.click("summary:text('Mehr')"); await pg.click("button:text('Zum Kunden machen'), a:text('Zum Kunden machen')")
            await pg.wait_for_selector(".dlg select[aria-label='Paket']"); chk(f"Admin @{w}px: Assistent „Zum Kunden machen“ öffnet",True)
            await pg.screenshot(path=f"/var/tmp/pt/shots/zukunde_{w}.png"); await pg.click(".dlgkopf button"); await ctx.close()
            # Vertrieb
            ctx,pg,errs=await login(br,VM,"VeraPasswort123","/vertrieb",w)
            await pg.goto(B+"/vertrieb#lead/"+lid); await pg.wait_for_selector("button:text('Daten ergänzen')",timeout=8000)
            chk(f"Vertrieb @{w}px: Anruflink vorhanden",await pg.locator("a[href^='tel:']").count()>=1)
            await pg.click("button:text('Daten ergänzen')"); await pg.fill("input[name=ansprechpartner]","Frau Browser"); await pg.select_option("select[name=ansprache_grundlage]","einwilligung"); await pg.click("button:text('Speichern')"); await pg.wait_for_timeout(900)
            chk(f"Vertrieb @{w}px: Daten ergänzen speichert",sql(f"select ansprechpartner||'|'||ansprache_grundlage from leads where id='{lid}'")=="Frau Browser|einwilligung")
            await pg.click("button[role=tab]:text('Angebot')"); await pg.click("button:text('Freie Zeiten zeigen')"); await pg.wait_for_timeout(900); chk(f"Vertrieb @{w}px: Terminkarte lädt",await pg.locator("text=Kunde hat dem Termin zugestimmt").count()==1)
            chk(f"Vertrieb @{w}px: kein „undefined“/„null“ im Lead",not re.search(r"\b(undefined|null)\b",await pg.locator("main, #main, body").first.inner_text()));
            await pg.screenshot(path=f"/var/tmp/pt/shots/lead_vertrieb_{w}.png"); chk(f"Vertrieb @{w}px: keine JavaScript-Fehler",not errs,errs); await ctx.close()
            # Kunde
            ctx,pg,errs=await login(br,KM,"InhaberPasswort1","/app",w)
            try: await pg.click(".dlgoverlay >> text=Überspringen",timeout=2000)
            except Exception: pass
            fid=a.post(f"/api/admin/kunden/{kid}/freigaben-kunden",json={"titel":f"Browser Beitrag {w}","art":"social","inhalt":"Text","veroeffentlichung_am":"2030-01-02"}).json()["id"]
            await pg.goto(B+"/app#freigaben"); await pg.wait_for_selector("text=geplante Veröffentlichung",timeout=8000)
            await pg.click(f".card:has-text('Browser Beitrag {w}') button:text-is('Freigeben')"); chk(f"Kunde @{w}px: Freigabe braucht Bestätigung",sql(f"select status from kundenfreigaben where id='{fid}'")=="wartet")
            await pg.screenshot(path=f"/var/tmp/pt/shots/freigabe_{w}.png")
            await pg.click(f".card:has-text('Browser Beitrag {w}') button:has-text('Ja, jetzt freigeben')"); await pg.wait_for_timeout(1200); chk(f"Kunde @{w}px: Freigabe nach Bestätigung",sql(f"select status from kundenfreigaben where id='{fid}'")=="freigegeben")
            await pg.goto(B+"/app#nachrichten"); await pg.wait_for_selector("input[name=betreff]"); await pg.fill("input[name=betreff]",f"Frage {w}"); await pg.fill("textarea[name=text]","Hallo, bitte melden.")
            open("/var/tmp/pt/foto.png","wb").write(b"\x89PNG\r\n\x1a\n"+b"0"*40); await pg.set_input_files("input[type=file]","/var/tmp/pt/foto.png"); await pg.click("button:text('Absenden')"); await pg.wait_for_timeout(1500)
            chk(f"Kunde @{w}px: Nachricht mit Anhang",sql(f"select count(*) from tickets t join dateien d on d.ticket_id=t.id where t.betreff='Frage {w}' and t.kunden_id='{kid}'")=="1")
            chk(f"Kunde @{w}px: keine JavaScript-Fehler",not errs,errs); await ctx.close()
        await br.close()
asyncio.run(main())
