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
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False})
k=a.post("/api/admin/kunden",json={"firma":"Werkzeug Kunde GmbH","ansprechpartner":"Tina Test","email":"kunde@werkzeug.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token("kunde@werkzeug.de"),"password":"InhaberPasswort1"})
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":"vera@werkzeug.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token("vera@werkzeug.de"),"password":"VeraPasswort123"})
for i in range(5): a.post("/api/admin/leads",json={"firma":f"WLead {i} GmbH","telefon":f"0511 {time.time_ns()}","ort":"Celle","vertriebspartner_id":p})
import subprocess
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
kid=k["id"]
for i in range(8): sql(f"INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES ('{kid}','Anfrager {i}','a{i}@x.de','Bitte um Rückruf','{'telefon' if i%3==0 else 'website'}','{'beantwortet' if i<3 else 'neu'}',now()-interval '{i+1} days',true)")
KUNDE="heute uebersicht status briefing nachrichten freigaben assistent anfragen termine bewertungen kontakte dokumente unterlagen auswertung berichte belege anrufe website wochenangebote werbung automationen avv team hilfe einstellungen".split()
VERT="heute uebersicht leads pipeline angebote leitfaden uebung kunden provisionen konto".split()

async def login(br,m,pw,pfad,w):
    ctx=await br.new_context(viewport={"width":w,"height":900},bypass_csp=True); pg=await ctx.new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda x: x.type=="error" and "favicon" not in x.text and "Failed to load resource" not in x.text and errs.append(x.text))
    await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*"); await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"); await pg.goto(B+pfad)
    await pg.wait_for_selector(".side a.nav",state="attached")
    if pfad=="/app":
        try: await pg.click(".dlgoverlay >> text=Überspringen",timeout=2500)
        except Exception: pass
    return ctx,pg,errs

async def alle(pg,name,pfad,seiten,w):
    schlecht=[];ueber=[];leer=[]
    for s in seiten:
        await pg.goto(B+pfad+"#"+s); await pg.wait_for_timeout(650)
        try: await pg.wait_for_load_state("networkidle",timeout=8000)
        except Exception: pass
        await pg.wait_for_timeout(500)
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
        await pg.goto(B+"/app#heute"); await pg.wait_for_selector(".navkopf"); await pg.wait_for_timeout(500)
        chk("Kunde: Heute zeigt „Dein nächster Schritt“",await pg.locator(".hero:has-text('Dein nächster Schritt')").count()==1)
        chk("Kunde: Menü in 4 Gruppen",await pg.locator(".navgruppe").count()==4,await pg.locator(".navgruppe").count())
        chk("Kunde: selten Genutztes ist zugeklappt, Gruppe der Seite offen",await pg.locator(".navkopf:has-text('Mein Betrieb')").get_attribute("aria-expanded")=="false" and await pg.locator(".navkopf:has-text('Täglich')").get_attribute("aria-expanded")=="true")
        await pg.locator(".navkopf:has-text('Mein Betrieb')").click(); await pg.wait_for_timeout(200)
        chk("Kunde: Gruppe lässt sich öffnen",await pg.locator("a.nav[href='#unterlagen']").is_visible())
        await pg.reload(); await pg.wait_for_selector(".navkopf"); await pg.wait_for_timeout(500)
        chk("Kunde: geöffnete Gruppe bleibt nach Neuladen offen",await pg.locator(".navkopf:has-text('Mein Betrieb')").get_attribute("aria-expanded")=="true")
        await pg.goto(B+"/app#hilfe"); await pg.wait_for_timeout(500)
        chk("Kunde: Gruppe der aktuellen Seite öffnet sich automatisch",await pg.locator(".navkopf:has-text('Verwaltung')").get_attribute("aria-expanded")=="true")
        await pg.locator(".themeknopf").click(); await pg.wait_for_timeout(200); t1=await pg.evaluate("document.documentElement.dataset.theme+'|'+localStorage.getItem('mk-theme')")
        await pg.locator(".themeknopf").click(); await pg.wait_for_timeout(200); t2=await pg.evaluate("document.documentElement.dataset.theme+'|'+localStorage.getItem('mk-theme')")
        chk("Darstellung: automatisch → hell → dunkel wechselt und wird gemerkt",t1=="light|hell" and t2=="dark|dunkel",(t1,t2))
        await pg.reload(); await pg.wait_for_selector(".navkopf"); chk("Darstellung: Dunkel bleibt nach Neuladen",await pg.evaluate("document.documentElement.dataset.theme")=="dark")
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
        await pg.wait_for_selector("button[role=tab]:text('Angebot')",timeout=8000); await pg.click("button[role=tab]:text('Angebot')"); await pg.wait_for_selector("button:text('Angebot anfragen')",timeout=8000); await pg.click("button:text('Angebot anfragen')"); await pg.wait_for_timeout(800); await pg.click("button[role=tab]:text('Gespräch')"); await pg.wait_for_selector("button:text('Mail-Entwurf öffnen')",timeout=8000)
        chk("Vertrieb: Angebotsanfrage mit Mail-Entwurf",True)
        chk("Vertrieb: Menü in 3 Gruppen, Mein Tag zuerst",await pg.locator(".navgruppe").count()==3 and (await pg.locator("a.nav").first.get_attribute("href"))=="#heute")
        chk("Vertrieb: keine JavaScript-Fehler in den Abläufen",not errs,errs); await ctx.close()
        # ---- Admin: Angebot an einen Lead senden (Dialog) und Annahme auf der öffentlichen Seite
        lid=[x for x in a.get("/api/admin/leads",params={"q":"WLead 1"}).json()][0]["id"] if isinstance(a.get("/api/admin/leads",params={"q":"WLead 1"}).json(),list) else a.get("/api/admin/leads",params={"q":"WLead 1"}).json()["leads"][0]["id"]
        a.patch(f"/api/admin/leads/{lid}",json={"email":"wlead1@angebot.de","status":"kontaktiert"})
        ctx,pg,errs=await login(br,"chef@test.de",ADMPW,"/admin",1280)
        await pg.goto(B+"/admin#lead/"+lid); await pg.wait_for_selector("button:text('Angebot senden')",timeout=8000)
        await pg.click("button:text('Angebot senden')"); await pg.wait_for_selector(".dlg select[aria-label='Paket hinzufügen']")
        opts=await pg.locator(".dlg select[aria-label='Paket hinzufügen'] option").count(); chk("Lead-Angebot: Dialog mit Paketen",opts>=4,opts)
        await pg.select_option(".dlg select[aria-label='Paket hinzufügen']",index=2); await pg.wait_for_timeout(300)
        n_pos=await pg.locator(".dlg input[aria-label='Leistung']").count(); chk("Lead-Angebot: Paket füllt Positionen mit Preis",n_pos>=1,n_pos)
        lv=await pg.locator(".dlg textarea[aria-label='Das bekommt der Kunde']").input_value(); chk("Lead-Angebot: Paket füllt „Das bekommt der Kunde“",len(lv.strip())>20,lv)
        chk("Lead-Angebot: Summe wird angezeigt",await pg.locator(".dlg:has-text('Netto')").count()==1)
        await pg.add_script_tag(content=AXE)
        v1=await pg.evaluate("axe.run(document.querySelector('.dlg'),{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
        chk("Lead-Angebot: Dialog barrierefrei",not v1,v1)
        await pg.click(".dlg button:text('Angebot jetzt senden')"); await pg.wait_for_selector(".dlg .msg.ok",timeout=8000)
        link=await pg.locator(".dlg input[readonly]").input_value(); chk("Lead-Angebot: Link nach dem Senden",'/angebot?t=' in link,link)
        chk("Lead-Angebot: Status im Lead 'angebot'",sql(f"select status from leads where id='{lid}'")=="angebot")
        await pg.goto(B+"/admin#lead/"+lid); await pg.reload(); await pg.wait_for_selector("button:text('Daten bearbeiten')",timeout=8000); await pg.click("button:text('Daten bearbeiten')")
        await pg.fill(".dlg input[name=ort]","Wunstorf"); await pg.fill(".dlg input[name=ansprechpartner]","Herr Browser"); await pg.click(".dlg >> text=Speichern"); await pg.wait_for_timeout(1200)
        chk("Lead-Daten im Browser ändern",sql(f"select ort||'|'||ansprechpartner from leads where id='{lid}'")=="Wunstorf|Herr Browser")
        await pg.goto(B+"/admin#belege"); await pg.wait_for_selector("button:text('+ Angebot an Neukunden')",timeout=8000); await pg.click("button:text('+ Angebot an Neukunden')")
        await pg.wait_for_selector(".dlg input[name=firma]"); chk("Neukunden-Dialog: Vorlage aus früherem Angebot wählbar",await pg.locator(".dlg select[aria-label='Vorlage aus früherem Angebot'] option").count()>=2); os.makedirs("/var/tmp/pt/shots",exist_ok=True); await pg.screenshot(path="/var/tmp/pt/shots/neukunde.png")
        await pg.fill(".dlg input[name=firma]","Neukunde Browser GmbH"); await pg.fill(".dlg input[name=email]","neu@browser-neu.de"); await pg.click(".dlg >> text=Weiter zum Angebot")
        await pg.wait_for_selector(".dlg select[aria-label='Paket hinzufügen']",timeout=8000)
        chk("Neukunden-Angebot: Lead angelegt, Angebotsdialog offen",sql("select count(*) from leads where firma='Neukunde Browser GmbH' and notiz like '%Neukunden%'")=="1")
        await pg.goto(B+"/admin#uebersicht"); await pg.wait_for_selector("h2:text('Angebote im Blick')",timeout=8000); chk("Dashboard: Karte Angebote im Blick zeigt Angebote",await pg.locator(".card:has(h2:text('Angebote im Blick')) li").count()>=1)
        await pg.screenshot(path="/var/tmp/pt/shots/dashboard.png",full_page=True)
        lid3=a.post("/api/admin/leads",json={"firma":"Entwurf Test GmbH","email":"entwurf@test-x.de","ort":"Celle"}).json()["id"]
        a.post(f"/api/admin/leads/{lid3}/angebote",json={"betreff":"Mein Entwurf","einleitung":"E","schluss":"S","positionen":[{"text":"Eigene Leistung A","menge":2,"einheit":"Std","preis_cent":5000},{"text":"Eigene Leistung B","menge":1,"einheit":"","preis_cent":12000}],"leistungen":["Alpha","Beta"]})
        await pg.goto(B+"/admin#lead/"+lid3); await pg.reload(); await pg.wait_for_selector("button[role=tab]:text('Angebot')",timeout=8000); await pg.click("button[role=tab]:text('Angebot')"); await pg.wait_for_selector("button:text('Bearbeiten und senden')",timeout=8000); await pg.click("button:text('Bearbeiten und senden')"); await pg.wait_for_selector(".dlg select[aria-label='Paket hinzufügen']")
        chk("Entwurf wieder öffnen: Positionen, Texte und Leistungen sind da",await pg.locator(".dlg input[aria-label='Leistung']").count()==2 and "Alpha\nBeta"==await pg.locator(".dlg textarea[aria-label='Das bekommt der Kunde']").input_value() and await pg.locator(".dlg input[aria-label='Betreff']").input_value()=="Mein Entwurf")
        await pg.screenshot(path="/var/tmp/pt/shots/angebotdialog.png")
        await pg.reload(); await pg.wait_for_selector("button:text('Kopieren')"); await pg.screenshot(path="/var/tmp/pt/shots/lead.png",full_page=True)
        await pg.goto(B+"/admin#preise"); await pg.reload(); await pg.wait_for_selector("h2:text('Leistungstexte der Pakete')",timeout=8000); await pg.click("summary:has-text('BUSINESS WEB')"); chk("Preise: Pflege der Leistungstexte",await pg.locator("textarea[aria-label='Leistungen BUSINESS WEB']").count()==1); await pg.screenshot(path="/var/tmp/pt/shots/preise.png")
        await pg.goto(B+"/admin#belege"); await pg.reload(); await pg.wait_for_selector("h2:text('Angebote: Auswertung')",timeout=8000); chk("Belege: Auswertungskarte",True); await pg.screenshot(path="/var/tmp/pt/shots/belege.png")
        await pg.goto(B+"/admin#einstellungen"); await pg.reload(); await pg.wait_for_selector("textarea[name=angebotsbedingungen]",state="attached",timeout=8000); chk("Einstellungen: Angebotsbedingungen-Feld",True)
        kb=a.get("/api/admin/kunden").json(); kb=kb if isinstance(kb,list) else kb.get("kunden",[])
        bq=a.post(f"/api/admin/kunden/{kb[0]['id']}/belege",json={"art":"angebot","betreff":"Editor","positionen":[{"text":"X","menge":1,"einheit":"","preis_cent":1000}],"leistungen":["Punkt eins"]}).json()["id"]
        await pg.goto(B+"/admin#beleg/"+bq); await pg.reload(); await pg.wait_for_selector("textarea[aria-label='Das bekommt der Kunde']",timeout=8000); chk("Belege-Editor: Feld Das bekommt der Kunde mit Paket-Auswahl",await pg.locator("textarea[aria-label='Das bekommt der Kunde']").input_value()=="Punkt eins" and await pg.locator("select[aria-label='Leistungen eines Pakets einfügen']").count()==1); await pg.screenshot(path="/var/tmp/pt/shots/editor.png")
        await ctx.close()
        for w,thema in ((1280,"hell"),(390,"dunkel")):
            ctx=await br.new_context(viewport={"width":w,"height":900},bypass_csp=True); await ctx.add_init_script(f"try{{localStorage.setItem('mk-theme','{thema}')}}catch(e){{}}"); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(link); await pg.wait_for_selector("text=Gesamtbetrag",timeout=8000); chk(f"Angebotsseite @{w}px: Abschnitt Das bekommen Sie",await pg.locator(".leistbox li").count()>=1); await pg.add_script_tag(content=AXE)
            v2=await pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
            ov=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
            chk(f"Angebotsseite @{w}px ({thema}): barrierefrei, kein Überlaufen, keine JS-Fehler",not v2 and ov<=0 and not errs,(v2,ov,errs))
            if w==390:
                await pg.fill("#name","Max Mustermann"); await pg.click("#ok"); await pg.click("button:text('Angebot verbindlich annehmen')"); await pg.wait_for_selector(".msg.ok:has-text('angenommen')",timeout=8000)
                chk("Angebotsseite: Annahme per Klick",sql(f"select status from belege where lead_id='{lid}'")=="angenommen")
            await ctx.close()
        # ---- Dunkelmodus: gleiche Barrierefreiheits-Prüfung auf allen Seiten
        for name,(m,pwd,pfad,seiten) in {"Kunde":("kunde@werkzeug.de","InhaberPasswort1","/app",KUNDE),"Vertrieb":("vera@werkzeug.de","VeraPasswort123","/vertrieb",VERT)}.items():
            c0,p0,_e=await login(br,m,pwd,pfad,1280); stz=await c0.storage_state(); await c0.close()
            ctx=await br.new_context(viewport={"width":1280,"height":900},bypass_csp=True,storage_state=stz); await ctx.add_init_script("try{localStorage.setItem('mk-theme','dunkel')}catch(e){}"); pg=await ctx.new_page()
            await pg.goto(B+pfad); await pg.wait_for_selector(".side a.nav",state="attached")
            chk(f"{name} (dunkel): Dunkelmodus aktiv",await pg.evaluate("document.documentElement.dataset.theme")=="dark")
            await alle(pg,name+" (dunkel)",pfad,seiten,1280); await ctx.close()
        await br.close()
asyncio.run(main())
