import httpx, time, re, email, subprocess, io, sys, json
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
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs
db.open_pool()
import os
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":f"0511 {time.time_ns()}","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200

import xml.etree.ElementTree as ET
from datetime import date, timedelta
from app import push
import datetime
aid=sql("select id from benutzer where email='chef@test.de'")

# ===== 1. Suche
kid,c,kmail=neuer_kunde("Suchfirma")
lid=lead("Sucheleads")
r=a.get("/api/admin/suche",params={"q":"Suchfirma"}).json()
chk("Suche findet Kunde",any(g["art"]=="Kunden" and any(kid in t["link"] for t in g["treffer"]) for g in r["gruppen"]),r)
r=a.get("/api/admin/suche",params={"q":"Sucheleads"}).json()
chk("Suche findet Lead",any(g["art"]=="Leads" and any(lid in t["link"] for t in g["treffer"]) for g in r["gruppen"]),r)
chk("Suche: 1 Zeichen leer",a.get("/api/admin/suche",params={"q":"S"}).json()["gruppen"]==[])
r=a.get("/api/admin/suche",params={"q":"%%"}); chk("Suche: Platzhalter wird escaped",r.status_code==200 and r.json()["gruppen"]==[],r.text)
r=a.get("/api/admin/suche",params={"q":"_"*5}); chk("Suche: Unterstriche escaped",r.status_code==200 and r.json()["gruppen"]==[],r.text)
chk("Kunde darf nicht suchen",c.get("/api/admin/suche",params={"q":"Suchfirma"}).status_code==403)
sql("update benutzer set admin_rechte=array['nachrichten'] where email='chef@test.de'")
r=a.get("/api/admin/suche",params={"q":"Suchfirma"})
chk("Suche respektiert Rechte (keine Kunden/Leads)",r.status_code==200 and not any(g["art"] in("Kunden","Leads") for g in r.json()["gruppen"]),r.text)
sql("update benutzer set admin_rechte=NULL where email='chef@test.de'")

# ===== 2. Zeitachse
sql(f"update kunden set status='aktiv' where id='{kid}'")
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht) values ('{kid}','A','x','y')")
z=a.get(f"/api/admin/kunden/{kid}/zeitachse"); chk("Zeitachse 200",z.status_code==200,z.text)
z=z.json(); chk("Zeitachse hat Ereignisse und Zustand",len(z["ereignisse"])>=1 and z["zustand"]["anfragen_30d"]==1 and "risiko" in z["zustand"],z)
zs=[e["zeit"] for e in z["ereignisse"]]; chk("Zeitachse absteigend sortiert",zs==sorted(zs,reverse=True))
chk("Zeitachse unbekannter Kunde 404",a.get("/api/admin/kunden/00000000-0000-0000-0000-000000000000/zeitachse").status_code==404)
chk("Zeitachse ungültige ID 404",a.get("/api/admin/kunden/xyz/zeitachse").status_code in(404,422))
chk("Kunde darf keine Zeitachse",c.get(f"/api/admin/kunden/{kid}/zeitachse").status_code==403)

# ===== 3. Cockpit
k2,c2,_=neuer_kunde("Kuendiger")
sql(f"update kunden set status='aktiv' where id='{k2}'")
co0=a.get("/api/admin/cockpit").json()
chk("Cockpit: 12 Monate",len(co0["reihe"])==12 and all(k in co0 for k in("mrr_cent","aktiv","churn_prozent","offen_cent")),co0)
sql(f"update kunden set status='gekuendigt' where id='{k2}'")
chk("Trigger setzt gekuendigt_am",sql(f"select gekuendigt_am is not null from kunden where id='{k2}'")=="t")
co=a.get("/api/admin/cockpit").json()
chk("Cockpit zählt Kündigung",co["kuendigungen_90d"]==co0["kuendigungen_90d"]+1 and co["reihe"][-1]["kuendigungen"]>=1,co)
sql(f"update kunden set status='aktiv' where id='{k2}'")
chk("Reaktivierung löscht gekuendigt_am",sql(f"select gekuendigt_am is null from kunden where id='{k2}'")=="t")
chk("Cockpit nur für Admin",c.get("/api/admin/cockpit").status_code==403)
sql("update benutzer set admin_rechte=array['nachrichten'] where email='chef@test.de'")
chk("Cockpit braucht Finanzrecht",a.get("/api/admin/cockpit").status_code==403)
sql("update benutzer set admin_rechte=NULL where email='chef@test.de'")
# Monatsmail
sql("delete from job_marker where key like 'cockpit-%'")
class Jetzt(datetime.datetime):
    @classmethod
    def now(cls,tz=None): return datetime.datetime(2026,3,2,9,0,tzinfo=datetime.timezone.utc)
orig=jobs.datetime; jobs.datetime=Jetzt
n0=len(mails()); jobs.geschaeftszahlen_mail({}); jobs.geschaeftszahlen_mail({})
jobs.datetime=orig; time.sleep(1.5)
neu=[m for m in mails()[n0:] if "Geschäftszahlen" in str(email.header.make_header(email.header.decode_header(m["Subject"] or "")))]
chk("Geschäftszahlen-Mail genau einmal",len(neu)==1,len(neu))

# ===== 4. Ansicht
r=a.get("/api/me/ansicht").json(); chk("Ansicht leer",r=={"ausgeblendet":[],"push_aus":[],"gesetzt":False,"tour_gesehen":False,"tag_zeit":None},r)
chk("Ansicht speichern",a.put("/api/me/ansicht",json={"ausgeblendet":["system","cockpit"]}).status_code==200)
r=a.get("/api/me/ansicht").json(); chk("Ansicht gelesen",r["ausgeblendet"]==["cockpit","system"] and r["push_aus"]==[],r)
a.put("/api/me/ansicht",json={"push_aus":["ticket"]}); r=a.get("/api/me/ansicht").json()
chk("Teilupdate lässt andere Liste",r["ausgeblendet"]==["cockpit","system"] and r["push_aus"]==["ticket"],r)
chk("Ansicht: ungültiger Schlüssel 400",a.put("/api/me/ansicht",json={"ausgeblendet":["<x>"]}).status_code==400)
chk("Ansicht: pro Benutzer getrennt",c.get("/api/me/ansicht").json()["ausgeblendet"]==[])
chk("Kunde kann Ansicht setzen",c.put("/api/me/ansicht",json={"ausgeblendet":["karten"]}).status_code==200 and c.get("/api/me/ansicht").json()["ausgeblendet"]==["karten"])
a.put("/api/me/ansicht",json={"ausgeblendet":[]})

# ===== 5. Glocke
sql("delete from benachrichtigungen")
push.senden([aid],"Neue Nachricht","Text","/admin#postfach","buchung")
push.senden([aid],"Test","x","/admin","test")
push.senden([aid],"Ticket","x","/admin#postfach","ticket")  # push_aus: ticket -> Push aus, Eintrag?
time.sleep(1)
g=a.get("/api/benachrichtigungen").json()
chk("Glocke: Eintrag gespeichert, Test nicht",any(x["tag"]=="buchung" for x in g["liste"]) and not any(x["tag"]=="test" for x in g["liste"]),g)
chk("Glocke: ungelesen zählt",g["ungelesen"]==len(g["liste"]) and g["ungelesen"]>=1,g)
i=[x["id"] for x in g["liste"] if x["tag"]=="buchung"][0]
a.post("/api/benachrichtigungen/gelesen",json={"ids":[i]}); g2=a.get("/api/benachrichtigungen").json()
chk("Einzeln gelesen",g2["ungelesen"]==g["ungelesen"]-1,g2)
a.post("/api/benachrichtigungen/gelesen",json={"alle":True}); chk("Alle gelesen",a.get("/api/benachrichtigungen").json()["ungelesen"]==0)
chk("Fremde Glocke getrennt",c.get("/api/benachrichtigungen").json()["liste"]==[])
c.post("/api/benachrichtigungen/gelesen",json={"alle":True}); chk("Fremdes Lesen ändert nichts",any(x["gelesen_am"] for x in a.get("/api/benachrichtigungen").json()["liste"]))
chk("Glocke braucht Login",httpx.get(B+"/api/benachrichtigungen").status_code==401)
sql(f"insert into benachrichtigungen (benutzer_id,tag,titel,erstellt_am) values ('{aid}','x','alt',now()-interval '90 days')")
jobs.anrufe_bereinigen()
chk("Alte Benachrichtigungen werden bereinigt",sql("select count(*) from benachrichtigungen where titel='alt'")=="0")

# ===== 6. Seiten
for p in("/admin","/app","/vertrieb"): chk("Seite "+p,httpx.get(B+p).status_code==200)
for f in("common","admin","kunde","vertrieb"): chk(f"{f}.js ausgeliefert",httpx.get(B+f"/static/js/{f}.js").status_code==200)
print("Fertig")
