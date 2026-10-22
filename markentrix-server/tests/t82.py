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
sfx=str(int(time.time())+312)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Plan"); kB,cB,mB=neuer_kunde("Planb")
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
dom=f"plan{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False}); chk("Kalender: Sofortbuchung",r.status_code==200,r.text)
r=cA.put(D+"/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/salona"}); chk("PayPal.Me eintragen",r.status_code==200,r.text)


def naechster(wt):  # ISO-Wochentag, mindestens 3 Tage in der Zukunft
    d=heute+datetime.timedelta(days=3)
    while d.isoweekday()!=wt: d+=datetime.timedelta(days=1)
    return d.isoformat()
def slots(tag,**q): return {x["zeit"]:x["frei"] for x in W.get(API+"/slots",params={"tag":tag,**q},headers={"Origin":"https://"+dom}).json()["slots"]}
# ---- Wochenplan mit Pause
K=lambda plan:cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":60,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"","kapazitaet":0,"freigabe":False,"plan":plan})
r=K({"1":"09:00-12:00, 13:00-18:00","6":"09:00-10:00"}); chk("Wochenplan speichern",r.status_code==200,r.text)
r=K({"1":"quatsch"}); chk("Ungültige Zeiten abgelehnt",r.status_code==400,r.text)
r=K({"1":"12:00-09:00"}); chk("Ende vor Beginn abgelehnt",r.status_code==400,r.text)
r=K({"1":"09:00-12:00, 11:00-13:00"}); chk("Überschneidende Fenster abgelehnt",r.status_code==400,r.text)
r=K({"1":"09:00-12:00, 13:00-18:00","6":"09:00-10:00"})
k=cA.get(D).json()["kalender"]; chk("Plan kommt zurück, ältere Felder nachgezogen",k["plan"]=={"1":"09:00-12:00, 13:00-18:00","6":"09:00-10:00"} and k["wochentage"]==[1,6] and k["von"]=="09:00" and k["bis"]=="18:00",k)
mo=naechster(1); sa=naechster(6); so=naechster(7); di=naechster(2)
s=slots(mo); chk("Montag: Vormittag und Nachmittag frei, Mittagspause nicht angeboten",s.get("09:00") is True and s.get("11:30") is True and "12:00" not in s and "12:30" not in s and s.get("13:00") is True and s.get("17:30") is True and "18:00" not in s,s)
s=slots(sa); chk("Samstag kurz",list(s)==["09:00","09:30"] and all(s.values()),s)
s=slots(so); chk("Sonntag geschlossen: nichts frei",not any(s.values()),s)
s=slots(di); chk("Dienstag (nicht im Plan) geschlossen",not any(s.values()),s)
v=W.get(API+"/verfuegbarkeit",headers={"Origin":"https://"+dom}).json(); chk("Ruhetage aus dem Plan",sorted(v["closedWeekdays"])==[0,2,3,4,5],v["closedWeekdays"])
chk("Zeitenliste ohne Mittagspause","12:00" not in v["slotTimes"] and "09:00" in v["slotTimes"],v["slotTimes"])
# ---- Mitarbeiter mit eigenem Plan
cA.post(D+"/leistungen",json={"name":"Schnitt","dauer_min":30,"puffer_min":0,"preis":"20 €"})
r=cA.post(D+"/mitarbeiter",json={"name":"Anna","plan":{"2":"14:00-16:00"}}); chk("Mitarbeiterin mit eigenem Plan",r.status_code==200,r.text)
r=cA.post(D+"/mitarbeiter",json={"name":"Ben"}); chk("Mitarbeiter ohne Plan: wie der Betrieb",r.status_code==200,r.text)
t=cA.get(D+"/team").json(); chk("Team liefert den Plan",[m["plan"] for m in t["mitarbeiter"] if m["name"]=="Anna"]==[{"2":"14:00-16:00"}],t["mitarbeiter"])
s=slots(di,mitarbeiter="anna"); chk("Anna dienstags nachmittags",s.get("14:00") is True and s.get("15:30") is True and "16:00" not in s,s)
s=slots(mo,mitarbeiter="anna"); chk("Anna montags nicht",not any(s.values()),s)
s=slots(mo,mitarbeiter="ben"); chk("Ben folgt dem Betrieb (Montag mit Pause)",s.get("09:00") is True and "12:00" not in s,s)
s=slots(di); chk("Ohne Wunschperson: Dienstag über Anna buchbar",s.get("14:00") is True and s.get("09:00") is not True,s)
# ---- Plan wieder leeren -> ältere Einstellung
r=K({}); k=cA.get(D).json()["kalender"]; chk("Plan leeren: ältere Felder gelten",r.status_code==200 and k["plan"]=={},k)
print("fertig")
