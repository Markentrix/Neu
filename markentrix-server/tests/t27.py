"""Browser-Test (Playwright, Chromium): Kernabläufe aller drei Portale, Mobilansicht (375 px), Barrierefreiheit (axe-core), keine JS-Fehler."""
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
k=a.post("/api/admin/kunden",json={"firma":"Browser Kunde GmbH","ansprechpartner":"Tina Test","email":"kunde@browser.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token("kunde@browser.de"),"password":"InhaberPasswort1"})
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":"vera@browser.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token("vera@browser.de"),"password":"VeraPasswort123"})
for i in range(5): a.post("/api/admin/leads",json={"firma":f"Lead {i} GmbH","telefon":"0511 555","ort":"Celle","vertriebspartner_id":p})
PORT={"admin":("chef@test.de",ADMPW,"/admin"),"kunde":("kunde@browser.de","InhaberPasswort1","/app"),"vertrieb":("vera@browser.de","VeraPasswort123","/vertrieb")}

async def login(br,m,pw,pfad,w):
    ctx=await br.new_context(viewport={"width":w,"height":900},bypass_csp=True); pg=await ctx.new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
    await pg.wait_for_selector(".side a.nav",state="attached")
    return ctx,pg,errs

async def seiten_pruefen(pg,name,pfad,w):
    hrefs=await pg.eval_on_selector_all(".side a.nav[href^='#']","e=>e.map(x=>x.getAttribute('href'))")
    schlecht=[];ueber=[]
    for hr in hrefs:
        await pg.goto(B+pfad+hr); await pg.wait_for_timeout(700)
        await pg.add_script_tag(content=AXE)
        ax=await pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
        ov=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
        if ax: schlecht.append((hr,ax[:3]))
        if ov>0: ueber.append((hr,ov))
    chk(f"{name} @{w}px: {len(hrefs)} Seiten ohne Barrierefreiheits-Verstoß",not schlecht,schlecht)
    chk(f"{name} @{w}px: kein seitliches Überlaufen",not ueber,ueber)
    chk(f"{name} @{w}px: Seiten vorhanden",len(hrefs)>=4,hrefs)

async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        # --- Login-Fehler
        ctx=await br.new_context(); pg=await ctx.new_page(); await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p","falsch-falsch"); await pg.click("#b")
        await pg.wait_for_timeout(800); chk("Falsches Passwort: bleibt auf Login",pg.url.rstrip("/")==B and await pg.locator(".msg, .err, #m:not(:empty)").count()>=0); await ctx.close()
        zust={}
        for name,(m,pwd,pfad) in PORT.items():
            ctx,pg,errs=await login(br,m,pwd,pfad,1280)
            zust[name]=await ctx.storage_state()
            await seiten_pruefen(pg,name,pfad,1280)
            if name=="admin":
                # Suche per Tastatur
                await pg.goto(B+"/admin#uebersicht"); await pg.wait_for_selector("text=Geschäftszahlen")
                await pg.keyboard.press("Control+k"); await pg.fill(".suchbox input","Browser Kunde"); await pg.wait_for_selector(".suchgruppe:text-is(\"Kunden\")",timeout=5000)
                await pg.keyboard.press("Enter"); await pg.wait_for_url("**#kunde/*",timeout=5000)
                await pg.wait_for_selector("text=Zustand & Verlauf",timeout=8000); chk("Admin: Suche → Kundenseite mit Zeitachse",True)
                # Ansicht anpassen
                await pg.goto(B+"/admin#uebersicht"); await pg.wait_for_selector("text=Geschäftszahlen")
                chk("Admin: Karte 'Jetzt wichtig' sichtbar",await pg.locator("h2:has-text('Jetzt wichtig')").count()==1)
                chk("Admin: Cockpit mit MRR-Ziel-Knopf, Trichter und Prognose",await pg.locator("text=/MRR-Ziel/").count()>=1 and await pg.locator("text=/Zahlungseingänge|Erwartete/").count()>=1)
                await pg.click(".neuknopf"); await pg.wait_for_selector(".suchtreffer a:has-text('Neuer Kunde')"); await pg.click(".suchtreffer a:has-text('Neuer Kunde')"); await pg.wait_for_selector("form input[name=firma]"); chk("Admin: '+ Neu' → Neuer Kunde",pg.url.endswith("#neu"))
                await pg.goto(B+"/admin#uebersicht"); await pg.wait_for_selector("text=Geschäftszahlen")
                chk("Admin: Betriebs-Ampel sichtbar",await pg.locator("h2:has-text('Betrieb')").count()==1 and await pg.locator(".ampel .ap").count()>=3)
                await pg.goto(B+"/admin#meintag"); await pg.wait_for_selector("h1:has-text('Mein Tag')"); chk("Admin: Mein Tag lädt",await pg.locator("text=Meine Filter").count()==1)
                await pg.goto(B+"/admin#belege?erinnerung=1"); await pg.wait_for_selector(".dlg"); chk("Admin: Erinnerungs-Dialog öffnet",await pg.locator(".dlg h2:has-text('Zahlungserinnerungen')").count()==1)
                await pg.keyboard.press("Escape"); await pg.wait_for_timeout(200); chk("Admin: Dialog schließt mit Esc",await pg.locator(".dlg").count()==0)
                await pg.goto(B+"/admin#kunden"); await pg.wait_for_selector("tbody tr input[type=checkbox]"); await pg.locator("tbody tr input[type=checkbox]").first.check()
                chk("Admin: Kundenliste Sammelleiste erscheint",await pg.locator(".sammelleiste:visible").count()==1)
                await pg.click(".sammelleiste >> text=Aufgabe anlegen"); await pg.wait_for_selector(".dlg"); await pg.fill(".dlg input[maxlength='200']","Browser-Sammelaufgabe"); await pg.click(".dlg >> text=Aufgaben anlegen")
                await pg.wait_for_selector("text=1 Aufgaben angelegt",timeout=5000); chk("Admin: Sammelaufgabe angelegt",True); await pg.keyboard.press("Escape")
                await pg.select_option("select[name=status]","onboarding"); await pg.wait_for_timeout(600)
                pg.once("dialog",lambda d: asyncio.ensure_future(d.accept("Onboarding-Kunden")))
                await pg.click("text=Aktuelle Auswahl speichern"); await pg.wait_for_timeout(1200)
                chk("Admin: Filter gespeichert und auswählbar",await pg.locator("select[aria-label='Gespeicherte Filter'] option:has-text('Onboarding-Kunden')").count()==1)
                await pg.goto(B+"/admin#einstellungen"); await pg.wait_for_selector("h2:has-text('Textvorlagen')"); chk("Admin: Textvorlagen-Karte mit Standardvorlagen",await pg.locator("text=Willkommen / Onboarding").count()>=1)
                await pg.goto(B+"/admin#uebersicht"); await pg.wait_for_selector("text=Geschäftszahlen")
                await pg.click("text=Ansicht anpassen"); await pg.click("label:has-text('Geschäftszahlen') input"); await pg.click("button:has-text('Speichern')"); await pg.wait_for_load_state(); await pg.wait_for_selector("h1:has-text('Übersicht')")
                await pg.wait_for_timeout(600); chk("Admin: Karte ausblenden bleibt nach Neuladen",await pg.locator("h2:has-text('Geschäftszahlen')").count()==0)
                # Glocke
                await pg.click(".glocke"); chk("Admin: Glocke öffnet",await pg.locator(".glockepanel").is_visible())
                # Neuer Kunde über das Formular
                await pg.goto(B+"/admin#neu"); await pg.wait_for_selector("form input[name=firma]")
                await pg.fill("form input[name=firma]","Formular Test GmbH"); await pg.fill("form input[name=email]","formular@browser.de")
                for n,v in(("ansprechpartner","Max Muster"),("telefon","0511 1"),("strasse","Weg 2"),("plz","29221"),("ort","Celle")):
                    if await pg.locator(f"form input[name={n}]").count(): await pg.fill(f"form input[name={n}]",v)
                await pg.click("form button[type=submit], form .btn:not(.sec)"); await pg.wait_for_timeout(1500)
                r=a.get("/api/admin/kunden",params={"q":"Formular Test"}).json(); chk("Admin: Kunde über das Formular angelegt",len(r)==1,r)
            if name=="kunde":
                await pg.goto(B+"/app#uebersicht"); await pg.wait_for_selector("text=Ansicht anpassen"); chk("Kunde: Übersicht mit Anpassen-Knopf",True); chk("Kunde: Karte 'Dein Monat mit Markentrix'",await pg.locator("h2:has-text('Dein Monat mit Markentrix')").count()==1 and await pg.locator("text=Dein nächster Schritt").count()==1)
                await pg.goto(B+"/app#einstellungen"); await pg.wait_for_selector("text=App & Benachrichtigungen"); chk("Kunde: Push-Karte mit Anlässen",await pg.locator("text=Neue Anfrage").count()>=1)
            if name=="vertrieb":
                await pg.goto(B+"/vertrieb#leads"); await pg.wait_for_selector("text=Lead 0 GmbH",timeout=8000); chk("Vertrieb: zugewiesene Leads sichtbar",True)
            chk(f"{name}: keine JavaScript-Fehler",not errs,errs)
            await ctx.close()
        # --- Mobil (Sitzung wiederverwenden)
        for name,(m,pwd,pfad) in PORT.items():
            ctx=await br.new_context(viewport={"width":375,"height":800},bypass_csp=True,storage_state=zust[name]); pg=await ctx.new_page()
            errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+pfad); await pg.wait_for_selector(".side a.nav",state="attached")
            await seiten_pruefen(pg,name,pfad,375); chk(f"{name} @375px: keine JavaScript-Fehler",not errs,errs); await ctx.close()
        await br.close()
asyncio.run(main())
