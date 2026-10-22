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
sfx=str(int(time.time())+320)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Vorl"); kB,cB,mB=neuer_kunde("Vorlb")
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
dom=f"vorl{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False}); chk("Kalender: Sofortbuchung",r.status_code==200,r.text)
r=cA.put(D+"/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/salona"}); chk("PayPal.Me eintragen",r.status_code==200,r.text)



r=a.get("/api/admin/buchungsvorlagen"); chk("Vorlagen-Liste",r.status_code==200 and {"friseur","kfz","fahrzeugpflege"} <= {v["code"] for v in r.json()},r.text[:200])
r=a.post(f"/api/admin/kunden/{kA}/buchungsvorlage",json={"code":"gibtsnicht"}); chk("Unbekannte Vorlage",r.status_code==404,r.text)
r=a.post(f"/api/admin/kunden/{kA}/buchungsvorlage",json={"code":"friseur"}); chk("Friseur-Vorlage angewendet",r.status_code==200 and r.json()["leistungen"]==5,r.text)
t=cA.get(D+"/team").json(); ls={x["name"]:x for x in t["leistungen"]}
chk("Leistungen inaktiv und ohne Preis",len(ls)==5 and not any(x["aktiv"] for x in ls.values()) and not any(x["preis"] for x in ls.values()),t["leistungen"])
chk("Zusatzfragen und Freigabe übernommen",[f["key"] for f in ls["Färben"]["felder"]]==["haarlaenge","letzte_behandlung"] and ls["Strähnen und Balayage"]["freigabe"] is True,ls.get("Färben"))
k=cA.get(D).json()["kalender"]; chk("Arbeitszeiten mit Pause übernommen",k["plan"].get("2")=="09:00-13:00, 14:00-18:00" and k["plan"].get("6")=="09:00-14:00" and k["wochentage"]==[2,3,4,5,6],k["plan"])
r=a.post(f"/api/admin/kunden/{kA}/buchungsvorlage",json={"code":"kfz"}); chk("Zweites Mal nicht möglich",r.status_code==409,r.text)
r=a.post(f"/api/admin/kunden/{kB}/buchungsvorlage",json={"code":"kfz"}); chk("Kfz-Vorlage bei anderem Kunden",r.status_code==200,r.text)
chk("Wissensbasis bekommt inaktive Leistungen nicht",sql(f"select count(*) from wissensbasis where kunden_id='{kB}' and quelle='system' and aktiv and wert like '%Inspektion%'") in ("0",""))
r=cB.get(D+"/team"); chk("Kfz: Kennzeichen als Pflichtfeld",any(f["key"]=="kennzeichen" and f["pflicht"] for l in r.json()["leistungen"] for f in l["felder"]),r.text[:200])
print("fertig")
