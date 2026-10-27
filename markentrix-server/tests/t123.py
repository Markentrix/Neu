"""Kurzbefehle am App-Symbol, Zahl am App-Symbol (/api/me/badge) und Morgen-Push „Dein Tag“ mit eigener Uhrzeit."""
import httpx, time, subprocess, sys, os, json
from datetime import datetime
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
# ---------------------------------------------------------------- Kurzbefehle
for r,erwartet in (("vertrieb","#anrufen"),("kunde","#anfragen"),("admin","#meintag")):
    m=httpx.get(B+"/manifest.webmanifest?r="+r).json(); sc=m.get("shortcuts",[])
    chk(f"Manifest {r}: Kurzbefehle vorhanden",len(sc)>=3 and any(erwartet in s["url"] for s in sc),sc)
    chk(f"Manifest {r}: jeder Kurzbefehl hat Name und Ziel im eigenen Portal",all(s["name"] and s["url"].startswith({"vertrieb":"/vertrieb","kunde":"/app","admin":"/admin"}[r]) for s in sc))
m0=httpx.get(B+"/manifest.webmanifest").json(); chk("Manifest ohne Rolle: wie bisher, ohne Kurzbefehle","shortcuts" not in m0 and m0["short_name"]=="Markentrix" and m0["orientation"]=="portrait")
chk("Unbekannte Rolle: keine Kurzbefehle","shortcuts" not in httpx.get(B+"/manifest.webmanifest?r=zzz").json())
chk("Seiten verweisen auf das Manifest der Rolle",all(f"manifest.webmanifest?r={r}" in httpx.get(B+p).text for p,r in (("/vertrieb","vertrieb"),("/app","kunde"),("/admin","admin"))))
# ---------------------------------------------------------------- Vertrieb: Zahl und Push
sfx=str(int(time.time())+4123)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Tilda Tag","email":f"tilda{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"tilda{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"TildaPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"tilda{sfx}@v.de","password":"TildaPasswort123456"}).status_code==200
chk("Ohne Leads: Zahl 0",v.get("/api/me/badge").json()=={"n":0},v.get("/api/me/badge").text)
ids=[a.post("/api/admin/leads",json={"firma":f"Tag{i} {sfx} GmbH","telefon":f"0511 99{i}{sfx}","ort":"Celle","plz":"29221","email":f"tag{i}{sfx}@lead.de","vertriebspartner_id":pid}).json()["id"] for i in range(3)]
sql(f"update leads set temperatur='heiss' where id in ({','.join(repr(x) for x in ids[:2])})")
chk("Zwei heiße neue Leads: Zahl 2",v.get("/api/me/badge").json()["n"]==2,v.get("/api/me/badge").text)
chk("Admin-Zahl ist eine Zahl",isinstance(a.get("/api/me/badge").json()["n"],int))
# Einstellung
r=v.put("/api/me/ansicht",json={"tag_zeit":"25:00"}); chk("Ungültige Uhrzeit wird abgelehnt",r.status_code==422,r.status_code)
r=v.put("/api/me/ansicht",json={"tag_zeit":"09:00"}); chk("Uhrzeit speichern",r.status_code==200 and v.get("/api/me/ansicht").json()["tag_zeit"]=="09:00")
v.put("/api/me/ansicht",json={"push_aus":["heute","buchung"]}); v.put("/api/me/ansicht",json={"tag_zeit":"09:00"})
chk("Neue Uhrzeit hebt alte Stummschaltung auf, anderes bleibt",v.get("/api/me/ansicht").json()["push_aus"]==["buchung"],v.get("/api/me/ansicht").json())
# Job
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","portal"))
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import jobs, db, tagesblick
from app.leadkontakt import TZ
db.open_pool()
def zeit(tag,std,mi=0):
    class FD(datetime):
        @classmethod
        def now(cls,tz=None): return datetime(2026,10,tag,std,mi,tzinfo=TZ)
    jobs.datetime=FD
def eintraege(): return int(sql(f"select count(*) from benachrichtigungen where tag='heute' and benutzer_id=(select id from benutzer where email='tilda{sfx}@v.de')"))
zeit(28,8,30); jobs.tag_pushes({}); chk("Vor der gewählten Uhrzeit (09:00) kommt nichts",eintraege()==0)
zeit(28,9,5); jobs.tag_pushes({}); chk("Zur gewählten Uhrzeit kommt „Dein Tag“",eintraege()==1,eintraege())
txt=sql(f"select titel||'|'||text from benachrichtigungen where tag='heute' and benutzer_id=(select id from benutzer where email='tilda{sfx}@v.de')")
chk("Text nennt die Zahl, aber keinen Namen",txt.startswith("Dein Tag|2 Leads warten") and "Tag0" not in txt and "GmbH" not in txt,txt)
zeit(28,9,6); jobs.tag_pushes({}); chk("Höchstens einmal am Tag",eintraege()==1,eintraege())
zeit(29,13,0); jobs.tag_pushes({}); chk("Zu spät (mehr als 3 Stunden nach der Zeit): nichts",eintraege()==1)
zeit(31,9,5); jobs.tag_pushes({}); chk("Am Wochenende (31.10.) kommt nichts",eintraege()==1)   # 31.10.2026 ist ein Samstag
v.put("/api/me/ansicht",json={"tag_zeit":"aus"}); zeit(29,9,5); jobs.tag_pushes({}); chk("„aus“: nichts",eintraege()==1)
v.put("/api/me/ansicht",json={"tag_zeit":"09:00"}); sql(f"update leads set wiedervorlage_am=null, temperatur='kalt' where vertriebspartner_id='{pid}'")
zeit(30,9,5); jobs.tag_pushes({}); chk("Nichts zu tun: keine Nachricht",eintraege()==1,eintraege())
# ---------------------------------------------------------------- Texte (Kunde, Admin)
chk("Kunde: Text mit Anfragen und Freigaben",tagesblick.push_text("kunde",{"anfragen":2,"freigaben":1,"nachrichten":0,"termine":1})==("Dein Tag","2 neue Anfragen · 1 Termin heute · 1 Freigabe wartet"))
chk("Kunde: ohne Inhalt keine Nachricht",tagesblick.push_text("kunde",{"anfragen":0,"freigaben":0,"nachrichten":0,"termine":0}) is None)
chk("Zahl am Symbol: Kunde summiert Anfragen, Freigaben, Nachrichten",tagesblick.zahl("kunde",{"anfragen":2,"freigaben":1,"nachrichten":3,"termine":9})==6)
kid=a.post("/api/admin/kunden",json={"firma":f"Tagkunde {sfx} GmbH","ansprechpartner":"T T","email":f"tk{sfx}@kk.de","telefon":"0511","strasse":"W 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":False}).json()["id"]
with db.tx("kunde",kid) as cur: d=tagesblick.kunde(cur)
chk("Kundenzahlen lassen sich lesen (Row-Level-Security)",set(d)=={"anfragen","freigaben","nachrichten","termine"} and all(isinstance(x,int) for x in d.values()),d)
