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
sfx=str(int(time.time())+340)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Amp"); kB,cB,mB=neuer_kunde("Ampb")
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
dom=f"amp{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False}); chk("Kalender: Sofortbuchung",r.status_code==200,r.text)
r=cA.put(D+"/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/salona"}); chk("PayPal.Me eintragen",r.status_code==200,r.text)




def zeile(kid,r=None):
    r=r or a.get("/api/admin/kunden-ampel").json()
    return next((x for x in r["kunden"] if x["id"]==kid),None)
r=a.get("/api/admin/kunden-ampel"); chk("Ampel erreichbar",r.status_code==200 and "summe" in r.json(),r.text[:200])
chk("Kunde ohne Website: Hinweis",zeile(kA) and zeile(kA)["farbe"] in ("gelb","gruen"),zeile(kA))
cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":14,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5],"vorlauf_std":0,"ort":"x","empfaenger":"","zeiten":"","kapazitaet":0,"freigabe":False})
a.post(f"/api/admin/kunden/{kA}/buchungsvorlage",json={"code":"friseur"})
z=zeile(kA); chk("Buchung an, Leistungen inaktiv: gelb mit Erklärung",z["farbe"]=="gelb" and any("inaktiv" in t for t in z["gelb"]),z)
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sql(f"INSERT INTO website_wacht (domain, kunden_id, ok, seit) VALUES ('{dom}','{kA}',false, now() - interval '3 hours')")
z=zeile(kA); chk("Website gestört: rot",z["farbe"]=="rot" and any("Website" in t for t in z["rot"]),z)
r=a.get("/api/admin/kunden-ampel").json(); chk("Rot steht oben in der Liste",r["kunden"][0]["farbe"]=="rot" and r["summe"]["rot"]>=1,r["summe"])
sql(f"UPDATE website_wacht SET ok=true WHERE domain='{dom}'")
chk("Wieder in Ordnung: nicht mehr rot",zeile(kA)["farbe"]!="rot")
r=cA.get("/api/admin/kunden-ampel"); chk("Kunde hat keinen Zugriff",r.status_code in (401,403),r.status_code)
print("fertig")
