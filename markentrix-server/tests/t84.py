import httpx, time, re, email, subprocess, io
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
sfx=str(int(time.time())+330)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Kal"); kB,cB,mB=neuer_kunde("Kalb")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)
import openpyxl
heute=datetime.datetime.now(TZ).date()
tage=[(heute+datetime.timedelta(days=i)).isoformat() for i in (3,4,5,6,7,8)]
dom=f"kal{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False}); chk("Kalender: Sofortbuchung",r.status_code==200,r.text)
r=cA.put(D+"/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/salona"}); chk("PayPal.Me eintragen",r.status_code==200,r.text)



import asyncio
r=cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":60,"von":"09:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"","kapazitaet":0,"freigabe":False}); chk("Kalender aktiv",r.status_code==200,r.text)
tag=(heute+datetime.timedelta(days=5)).isoformat()
def slots(t): return {x["zeit"]:x["frei"] for x in W.get(API+"/slots",params={"tag":t},headers={"Origin":"https://"+dom}).json()["slots"]}
chk("Vorher frei",slots(tag).get("10:00") is True)
M=lambda **kw:cA.post(D+"/buchungen/manuell",json={"name":"Frau Test","telefon":"0511 99","start":tag+"T10:00","dauer_min":60,**kw})
r=M(); chk("Termin von Hand eingetragen",r.status_code==200 and len(r.json()["angelegt"])==1,r.text)
s=slots(tag); chk("Zeit ist gesperrt (10:00 und 10:30)",s.get("10:00") is False and s.get("10:30") is False and s.get("11:00") is True,s)
k=cA.get(D+f"/kalender-ansicht?von={tag}&tage=1").json(); t0=k["termine"][0] if k["termine"] else {}
chk("Kalenderansicht liefert den Termin",len(k["termine"])==1 and t0["manuell"] is True and t0["name"]=="Frau Test" and "" in k["arbeitszeit"],k)
r=M(); chk("Gleiche Zeit nochmal: abgelehnt",r.status_code==409,r.text)
r=M(start=tag+"T10:30"); chk("Überschneidung abgelehnt",r.status_code==409,r.text)
r=M(email="kaputt"); chk("Ungültige E-Mail",r.status_code==400,r.text)
r=cA.post(D+"/buchungen/manuell",json={"name":"Alt","start":"2020-01-01T10:00","dauer_min":30}); chk("Vergangenheit abgelehnt",r.status_code==400,r.text)
r=cA.post(D+"/buchungen/manuell",json={"name":"Zwei Personen","start":tag+"T13:00","dauer_min":30,"personen":2}); chk("Zwei Personen: doppelte Dauer",r.status_code==200 and sql(f"select (extract(epoch from ende-start)/60)::int from website_termine where id='{r.json()['angelegt'][0]['id']}'")=="60",r.text)
# Serie mit einem Konflikt
t14=(heute+datetime.timedelta(days=19)).isoformat()
cA.post(D+"/buchungen/manuell",json={"name":"Block","start":t14+"T15:00","dauer_min":30})
r=cA.post(D+"/buchungen/manuell",json={"name":"Serie","start":tag+"T15:00","dauer_min":30,"wiederholen":3,"abstand_tage":7}); j=r.json()
chk("Serie: drei von vier, einer übersprungen",r.status_code==200 and len(j["angelegt"])==3 and len(j["uebersprungen"])==1,r.text)
chk("Serienzeiten in der Datenbank",sql(f"select count(*) from website_termine where kunden_id='{kA}' and name='Serie' and status='gebucht'")=="3")
# Absagen
bid=t0["id"]
r=cB.post(D+f"/buchungen/{bid}/ablehnen",json={"grund":""}); chk("Fremder Betrieb kann nicht absagen",r.status_code==409,r.text)
r=cA.post(D+f"/buchungen/{bid}/ablehnen",json={"grund":"Krank"}); chk("Absagen ohne E-Mail-Adresse geht",r.status_code==200,r.text)
chk("Zeit wieder frei",slots(tag).get("10:00") is True)
chk("Heute-Liste enthält Termine von Hand (Tabelle termine)",sql(f"select count(*) from termine where kunden_id='{kA}' and kontakt_name='Serie'")=="3")
# Browser
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); errs=[]
        for breite in (390,1280):
            ctx=await br.new_context(viewport={"width":breite,"height":900},bypass_csp=True); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=400 and not r.url.endswith("/api/me") else None)
            await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            await pg.goto(B+"/app#kalender"); await pg.wait_for_selector("h1:text-is('Kalender')",timeout=8000); await pg.wait_for_selector(".kal-spalte",timeout=8000)
            chk(f"UI {breite}px: kein seitliches Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"),await pg.evaluate("document.documentElement.scrollWidth"))
            if breite==1280:
                await pg.get_by_role("button",name="+ Termin eintragen").click(); await pg.wait_for_selector(".dlg")
                await pg.fill(".dlg input[aria-label='Name']","Browser Gast"); await pg.fill(".dlg input[aria-label='Datum']",heute.isoformat()); await pg.fill(".dlg input[aria-label='Uhrzeit']","16:00")
                await pg.locator(".dlg").get_by_role("button",name="Eintragen",exact=True).click(); await pg.wait_for_selector(".dlg",state="detached",timeout=8000)
                chk("UI: Termin per Formular eingetragen",sql(f"select count(*) from website_termine where kunden_id='{kA}' and name='Browser Gast'")=="1")
                await pg.wait_for_selector(".kal-termin",timeout=8000); await pg.locator(".kal-termin").first.click(); await pg.wait_for_selector(".dlg")
                chk("UI: Termin-Details öffnen sich","Termin absagen" in await pg.locator(".dlg").inner_text())
                await pg.screenshot(path="/var/tmp/pt/shots/kalender.png",full_page=True)
            await ctx.close()
        chk("UI: keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
print("fertig")
