import httpx, time, re, email, subprocess, asyncio, os
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True})
sfx=str(int(time.time())+360)
mv=f"hilfe{sfx}@v.de"; mk=f"hilfek{sfx}@k.de"
pid=a.post("/api/admin/vertrieb/partner",json={"name":"Hilfe Vertrieb","email":mv,"status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(mv),"password":"VeraPasswort123"})
k=a.post("/api/admin/kunden",json={"firma":f"Hilfe Kunde {sfx}","ansprechpartner":"Tina Test","email":mk,"telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token(mk),"password":"InhaberPasswort1"})
v=httpx.Client(base_url=B,headers=H); chk("Vertriebler-Login",v.post("/api/login",json={"email":mv,"password":"VeraPasswort123"}).status_code==200)
r=v.get("/api/vertrieb/provisionsregeln"); chk("Provisionsregeln für Vertriebler lesbar",r.status_code==200 and isinstance(r.json(),list),r.text)
chk("Provisionsregeln: nur Anzeige (kein Schreiben)",v.post("/api/vertrieb/provisionsregeln",json={}).status_code in (404,405))
from playwright.async_api import async_playwright
async def login(br,m,pw,pfad,w):
    ctx=await br.new_context(viewport={"width":w,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=500 else None)
    await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
    await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
    await pg.goto(B+pfad+"#heute" if pfad!="/admin" else B+pfad); await pg.wait_for_selector(".hilfesuche input",timeout=8000)
    try: await pg.click(".dlgoverlay >> text=Überspringen",timeout=1500)
    except Exception: pass
    return ctx,pg,errs
async def frage(pg,q):
    f=pg.locator(".hilfesuche input"); await f.fill(""); await f.fill(q); await pg.wait_for_timeout(250)
    return await pg.locator(".hilfetreffer button").all_inner_texts()
async def offen(pg,q,erwartet,inhalt,name):
    t=await frage(pg,q); chk(f"{name}: „{q}“ → erster Treffer „{erwartet}“",bool(t) and t[0]==erwartet,t)
    if t:
        await pg.locator(".hilfesuche input").press("Enter"); await pg.wait_for_selector(".dlg",timeout=4000)
        tx=await pg.locator(".dlg").inner_text(); chk(f"{name}: Anleitung enthält {inhalt}",inhalt in tx and "Wo:" in tx,tx[:200])
        chk(f"{name}: Anleitung ohne Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
async def ui():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        for w in (390,1280):
            ctx,pg,errs=await login(br,mv,"VeraPasswort123","/vertrieb",w)
            await offen(pg,"Leads anlegen","Lead anlegen (einzeln)","Lead speichern",f"Vertrieb@{w}")
            await offen(pg,"Wie komme ich an meine Provision","Meine Provision verstehen","Einzelposten",f"Vertrieb@{w}")
            await offen(pg,"Gespräch üben","Übungsmodus","nichts gespeichert",f"Vertrieb@{w}") if False else None
            await frage(pg,"Leads anlegen"); await pg.locator(".hilfesuche input").press("Enter"); await pg.wait_for_selector(".dlg")
            chk(f"Vertrieb@{w}: Frage „gelöst?“ sichtbar",await pg.locator(".dlg >> text=Ist dein Problem damit gelöst?").is_visible())
            await pg.click(".dlg >> text=Nein, noch nicht"); await pg.fill(".dlg textarea","Test: klappt nicht"); await pg.click(".dlg >> text=An das Team senden")
            await pg.wait_for_selector(".dlg >> text=Team wurde informiert",timeout=4000); chk(f"Vertrieb@{w}: Nein → Team informiert",True)
            await pg.keyboard.press("Escape")
            t=await frage(pg,"Qwertzuiop"); chk(f"Vertrieb@{w}: Unsinn → freundlicher Hinweis",t==["Frage an das Team senden"] and "keine Anleitung" in await pg.locator(".hilfetreffer").inner_text() and await pg.locator(".hilfetreffer >> text=Frage an das Team senden").count()==1)
            await pg.goto(B+"/vertrieb#uebung"); await pg.wait_for_selector("h2:text-is('Übungsmodus')",timeout=6000)
            chk(f"Vertrieb@{w}: Übungsmodus zeigt Beispiel",await pg.locator("text=Autohaus Beispiel").count()>0)
            await pg.click("text=Er sagt: „Ich habe keine Zeit.“"); chk(f"Vertrieb@{w}: Antwort erscheint",await pg.locator("text=Passt Ihnen Dienstag").is_visible())
            chk(f"Vertrieb@{w}: Übungsmodus kein Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            await pg.goto(B+"/vertrieb#provisionen"); await pg.wait_for_selector("h2:text-is('Pro Monat')",timeout=6000)
            chk(f"Vertrieb@{w}: Provisionen-Seite lädt",True)
            chk(f"Vertrieb@{w}: keine JS-Fehler",not errs,errs); await ctx.close()
            ctx,pg,errs=await login(br,mk,"InhaberPasswort1","/app",w)
            await offen(pg,"Wo trage ich meinen PayPal-Link ein","PayPal-Link eintragen","Dein PayPal.Me-Link",f"Kunde@{w}")
            await offen(pg,"Welche Daten muss ich wofür hinterlegen","Welche Daten muss ich wofür hinterlegen?","Kontaktformular",f"Kunde@{w}")
            await offen(pg,"Urlaub eintragen","Urlaub und Sperrtage eintragen","Zeitraum",f"Kunde@{w}")
            chk(f"Kunde@{w}: keine JS-Fehler",not errs,errs); await ctx.close()
            ctx,pg,errs=await login(br,"chef@test.de",ADMPW,"/admin",w)
            await offen(pg,"Mahnung","Zahlungserinnerung und Mahnungen","Standard ist aus",f"Admin@{w}")
            await offen(pg,"Neuen Kunden anlegen","Neuen Kunden anlegen","Onboarding",f"Admin@{w}")
            chk(f"Admin@{w}: keine JS-Fehler",not errs,errs); await ctx.close()
        await br.close()
asyncio.run(ui())
import json
for rolle in ("vertrieb","kunde","admin"):
    d=json.load(open(f"/home/claude/markentrix-server/portal/app/hilfe/{rolle}.json"))
    n=len(d["artikel"]); chk(f"Hilfe {rolle}: mindestens 8 Artikel ({n})",n>=8)
    chk(f"Hilfe {rolle}: jeder Artikel hat Schritte, Ort und Stichwörter",all(x["s"] and x["wo"] and x["k"] for x in d["artikel"]))
# PDF
for c,rolle,name in ((v,"vertrieb","Vertrieb"),(a,"kunde","Kunden"),(a,"admin","Admin"),(a,"vertrieb","Vertrieb(admin)")):
    r=c.get("/api/hilfe/anleitung.pdf",params={"rolle":rolle}); chk(f"PDF {name}: erzeugt",r.status_code==200 and r.content[:4]==b"%PDF" and len(r.content)>8000,(r.status_code,len(r.content)))
r=v.get("/api/hilfe/anleitung.pdf",params={"rolle":"admin"}); chk("Vertriebler bekommt trotz rolle=admin nur die eigene PDF",r.status_code==200 and len(v.get("/api/hilfe/anleitung.pdf").content)==len(r.content))
import io
from pypdf import PdfReader
tx=" ".join(pg.extract_text() for pg in PdfReader(io.BytesIO(a.get("/api/hilfe/anleitung.pdf",params={"rolle":"kunde"}).content)).pages)
chk("Kunden-PDF enthält PayPal-Anleitung und Einstellungen","PayPal-Link eintragen" in tx and "Einstellungsmöglichkeiten" in tx and "Hilfe, wenn etwas nicht klappt" in tx)
chk("Artikel-API liefert JSON",len(v.get("/api/hilfe/artikel").json()["artikel"])>=8)
# Einladungsmails mit PDF
def anhang(adr):
    for m in reversed(mails()):
        if adr in str(m["To"]): return [p.get_filename() for p in m.walk() if p.get_filename()]
chk("Einladung an Vertriebler enthält PDF",anhang(mv)==["Markentrix-Anleitung-vertrieb.pdf"],anhang(mv))
chk("Einladung an Kunden enthält PDF",anhang(mk)==["Markentrix-Anleitung-kunde.pdf"],anhang(mk))
print("fertig")
