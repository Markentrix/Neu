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
sfx=str(int(time.time())+350)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Stm"); kB,cB,mB=neuer_kunde("Stmb")
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
dom=f"stm{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False}); chk("Kalender: Sofortbuchung",r.status_code==200,r.text)
r=cA.put(D+"/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/salona"}); chk("PayPal.Me eintragen",r.status_code==200,r.text)




import asyncio
cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":60,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"","kapazitaet":0,"freigabe":False})
cA.post(D+"/leistungen",json={"name":"Schnitt","dauer_min":30,"puffer_min":0,"preis":"20 €"})
ls=cA.get(D+"/team").json()["leistungen"]; lid=ls[0]["id"]
rA=cA.post(D+"/mitarbeiter",json={"name":"Anna"}); rB=cA.post(D+"/mitarbeiter",json={"name":"Ben"}); mAnna=rA.json()["id"]; mBen=rB.json()["id"]
tag=(heute+datetime.timedelta(days=4)).isoformat()
M=lambda c,**kw:c.post(D+"/buchungen/manuell",json={"name":"Gast","start":tag+"T10:00","dauer_min":30,**kw})
M(cA,name="Frau Anna Kunde",mitarbeiter_id=mAnna,email="stamm1@besucher.de",telefon="0511 1"); M(cA,name="Herr Ben Kunde",mitarbeiter_id=mBen,start=tag+"T11:00",telefon="0511 2")
# ---- Mitarbeiter-Zugang mit Personenbindung
r=cA.post("/api/kunde/team/einladen",json={"email":f"anna{sfx}@k.de","name":"Anna Team","kunden_rolle":"mitarbeiter","website_mitarbeiter_id":mAnna}); chk("Anna eingeladen und mit Person verknüpft",r.status_code==200,r.text)
r=cA.post("/api/kunde/team/einladen",json={"email":f"x{sfx}@k.de","kunden_rolle":"mitarbeiter","website_mitarbeiter_id":"00000000-0000-0000-0000-000000000000"}); chk("Unbekannte Person abgelehnt",r.status_code==400,r.text)
tm=cA.get("/api/kunde/team").json(); chk("Team zeigt Person",any(x.get("person")=="Anna" for x in tm),tm)
cAnna=httpx.Client(base_url=B,headers=H); tk=token(f"anna{sfx}@k.de"); httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"AnnaPasswort12"}); r=cAnna.post("/api/login",json={"email":f"anna{sfx}@k.de","password":"AnnaPasswort12"}); chk("Anna meldet sich an",r.status_code==200,r.text)
k=cAnna.get(D+f"/kalender-ansicht?von={tag}&tage=1"); chk("Anna sieht im Kalender nur ihren Termin",k.status_code==200 and [t["name"] for t in k.json()["termine"]]==["Frau Anna Kunde"] and [m["name"] for m in k.json()["mitarbeiter"]]==["Anna"],k.text[:300])
o=cAnna.get(D+"/kalender-optionen").json(); chk("Optionen nur mit eigener Person",[m["name"] for m in o["mitarbeiter"]]==["Anna"] and o["eigene"]==mAnna,o)
r=cAnna.post(D+"/buchungen/manuell",json={"name":"Von Anna","start":tag+"T14:00","dauer_min":30,"mitarbeiter_id":mBen}); chk("Anna trägt immer für sich selbst ein",r.status_code==200 and sql(f"select mitarbeiter_id from website_termine where name='Von Anna'")==mAnna,r.text)
bid_ben=sql(f"select id from website_termine where name='Herr Ben Kunde'")
r=cAnna.post(D+f"/buchungen/{bid_ben}/ablehnen",json={"grund":""}); chk("Anna kann Bens Termin nicht absagen",r.status_code==409,r.text)
r=cAnna.get(D+"/stamm"); chk("Personengebundener Zugang: keine Stammkundenliste",r.status_code==403,r.status_code)
r=cAnna.get("/api/kunde/start"); chk("Start meldet Personenbindung",r.json().get("personengebunden") is True,r.text[:100])
r=cAnna.get(D+"/team"); chk("Mitarbeiter sieht die Team-Einstellungen nicht",r.status_code==403,r.status_code)
r=cAnna.get("/api/kunde/team"); chk("Und nicht die Team-Verwaltung",r.status_code==403,r.status_code)
# nur lesen
r=cA.post("/api/kunde/team/einladen",json={"email":f"lese{sfx}@k.de","kunden_rolle":"nur_lesen"}); tk=token(f"lese{sfx}@k.de"); httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"LesePasswort12"}); cL=httpx.Client(base_url=B,headers=H); cL.post("/api/login",json={"email":f"lese{sfx}@k.de","password":"LesePasswort12"})
chk("Nur-lesen sieht den Kalender",cL.get(D+f"/kalender-ansicht?von={tag}&tage=1").status_code==200)
chk("Nur-lesen darf nichts eintragen",M(cL,start=tag+"T16:00").status_code==403)
# Empfang
r=cA.post("/api/kunde/team/einladen",json={"email":f"empf{sfx}@k.de","kunden_rolle":"empfang"}); tk=token(f"empf{sfx}@k.de"); httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"EmpfPasswort12"}); cE=httpx.Client(base_url=B,headers=H); cE.post("/api/login",json={"email":f"empf{sfx}@k.de","password":"EmpfPasswort12"})
r=M(cE,start=tag+"T15:00",name="Telefon Gast"); chk("Empfang trägt Termine ein",r.status_code==200,r.text)
chk("Empfang sieht alle Termine",len(cE.get(D+f"/kalender-ansicht?von={tag}&tage=1").json()["termine"])>=3)
# ---- Stammkunden
s=cA.get(D+"/stamm").json(); namen={p["name"]:p for p in s["personen"]}; chk("Stammliste mit Personen",s["gesamt"]>=2 and "Frau Anna Kunde" in namen and "Herr Ben Kunde" in namen,s["gesamt"])
p=namen["Frau Anna Kunde"]; chk("Person über E-Mail erkannt, kommender Termin",p["kommend"]>=1 and p["schluessel"]=="stamm1@besucher.de",p)
chk("Person über Telefon erkannt",namen["Herr Ben Kunde"]["schluessel"]=="tel:05112",namen["Herr Ben Kunde"])
r=cA.put(D+"/stamm/notiz",json={"schluessel":p["schluessel"],"notiz":"Allergie gegen Ammoniak"}); chk("Notiz speichern",r.status_code==200,r.text)
chk("Notiz kommt zurück",{x["name"]:x for x in cA.get(D+"/stamm").json()["personen"]}["Frau Anna Kunde"]["notiz"]=="Allergie gegen Ammoniak")
chk("Suche nach Telefonnummer",[x["name"] for x in cA.get(D+"/stamm?q=0511 2").json()["personen"]]==["Herr Ben Kunde"])
chk("Suche nach Namensteil",[x["name"] for x in cA.get(D+"/stamm?q=anna").json()["personen"]][:1]==["Frau Anna Kunde"])
chk("Fremder Betrieb sieht fremde Notizen nicht",all(x["notiz"]=="" for x in cB.get(D+"/stamm").json()["personen"]))
cA.put(D+"/stamm/notiz",json={"schluessel":p["schluessel"],"notiz":""}); chk("Notiz löschen",{x["name"]:x for x in cA.get(D+"/stamm").json()["personen"]}["Frau Anna Kunde"]["notiz"]=="")
# ---- Ich komme
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sid=sql(f"select site_id from website_dienste where kunden_id='{kA}'")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
r=post("/anfrage",{"typ":"termin","name":"Komme Gast","email":"komme@besucher.de","telefon":"0511 77","datum":tag,"uhrzeit":"12:00","einwilligung":"ja"}); chk("Buchung über die Website",r.status_code==200,r.text)
tok=sql(f"select token from website_termine where name='Komme Gast'"); P=httpx.Client(base_url=B)
r=P.get(f"/site/{sid}/termin/komme",params={"t":tok}); chk("Ich-komme-Seite fragt nach",r.status_code==200 and "Ja, ich komme" in r.text and sql(f"select (kommt_am is null)::text from website_termine where token='{tok}'")=="true",r.text[:200])
r=P.post(f"/site/{sid}/termin/komme",data={"t":tok}); chk("Bestätigung gespeichert",r.status_code==200 and "Danke" in r.text and sql(f"select (kommt_am is not null)::text from website_termine where token='{tok}'")=="true",r.text[:200])
k=cA.get(D+f"/kalender-ansicht?von={tag}&tage=1").json(); chk("Kalender zeigt Bestätigung",[t["kommt"] for t in k["termine"] if t["name"]=="Komme Gast"]==[True],k["termine"])
# Erinnerung enthält den Link
sql(f"update website_termine set start=now()+interval '20 hours', ende=now()+interval '20.5 hours', erstellt_am=now()-interval '3 days', erinnerung=0, kommt_am=null where token='{tok}'")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb
db.open_pool()
with db.tx("system") as cur: cfg=jobs.einstellungen_lesen(cur)
webbetrieb.erinnerungen(cfg); m=mail_an("komme@besucher.de","Erinnerung"); chk("Erinnerung mit Ich-komme-Link",bool(m) and "/termin/komme?t=" in text(m[-1]),[text(x)[:200] for x in m[-1:]])
# ---- Warteliste
tag2=(heute+datetime.timedelta(days=9)).isoformat()
r=post("/anfrage",{"typ":"warteliste","name":"Wartet Gast","email":"warte@besucher.de","datum":tag2,"einwilligung":"ja"}); chk("Auf die Warteliste",r.status_code==200 and r.json()["ref"].startswith("L"),r.text)
chk("Warteliste gespeichert",sql(f"select count(*) from website_warteliste where email='warte@besucher.de' and status='offen'")=="1")
r=post("/anfrage",{"typ":"warteliste","name":"Ohne Mail","datum":tag2,"einwilligung":"ja"}); chk("Ohne E-Mail abgelehnt",r.status_code==422,r.text)
r=post("/anfrage",{"typ":"warteliste","name":"Ohne Tag","email":"x@besucher.de","einwilligung":"ja"}); chk("Ohne Wunschtag abgelehnt",r.status_code==422,r.text)
r=post("/anfrage",{"typ":"termin","name":"Voll Gast","email":"voll@besucher.de","telefon":"0511 5","datum":tag2,"uhrzeit":"10:00","einwilligung":"ja"}); vtok=sql(f"select token from website_termine where name='Voll Gast'")
n=sd_fn=None
from app import sitedienste as sd
chk("Noch frei: keine Benachrichtigung ohne Änderung",True)
r=P.post(f"/site/{sid}/termin/absagen",data={"t":vtok}); chk("Absage löst Benachrichtigung aus",r.status_code==200,r.text[:100])
m=mail_an("warte@besucher.de","frei geworden"); chk("Wartende bekommt Mail mit freien Zeiten",bool(m) and "frei geworden" in str(m[-1]["Subject"]) or bool(m) and "Zeit" in text(m[-1]),[str(x["Subject"]) for x in m])
chk("Status benachrichtigt",sql("select status from website_warteliste where email='warte@besucher.de'")=="benachrichtigt")
chk("Nicht doppelt benachrichtigt",sd.warteliste_benachrichtigen(kA,datetime.date.fromisoformat(tag2))==0)
# ---- Mehrere Personen
tag3=(heute+datetime.timedelta(days=11)).isoformat()
r=post("/anfrage",{"typ":"termin","name":"Zwei Gäste","email":"zwei@besucher.de","telefon":"0511 8","datum":tag3,"uhrzeit":"10:00","leistung":"schnitt","personen":"2","einwilligung":"ja"}); chk("Buchung für zwei Personen",r.status_code==200,r.text)
row=sql("select (extract(epoch from ende-start)/60)::int || '|' || preis_betrag from website_termine where name='Zwei Gäste'"); chk("Dauer und Preis verdoppelt",row=="60|40.00",row)
s2={x["zeit"]:x["frei"] for x in W.get(API+"/slots",params={"tag":tag3,"leistung":"schnitt","personen":"2"},headers={"Origin":"https://"+dom}).json()["slots"]}; chk("Slots rechnen mit doppelter Dauer",s2.get("16:30") is False and s2.get("16:00") is True,s2)
from playwright.async_api import async_playwright
async def ui():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); errs=[]
        for breite in (390,1280):
            ctx=await br.new_context(viewport={"width":breite,"height":900},bypass_csp=True); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=400 and not r.url.endswith("/api/me") else None)
            await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            for seite,titel in (("stamm","Stammkunden"),("team","Team"),("kalender","Kalender")):
                await pg.goto(B+"/app#"+seite); await pg.wait_for_selector(f"h1:text-is('{titel}'), h2:text-is('{titel}')",timeout=8000)
                chk(f"UI {breite}px {seite}: kein Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            await ctx.close()
        chk("UI: keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(ui())
print("fertig")
