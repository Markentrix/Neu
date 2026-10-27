"""Beste Anrufzeit je Branche (Hinweis auf der Lead-Seite, Anruf-Modus „beste Uhrzeit zuerst“) und Termin für die Terminbestätigung."""
import httpx, time, subprocess, sys, os, datetime
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+1810)
GR=f"Testfriseur{sfx}"
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Zora Zeit","email":f"zora{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"zora{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"ZoraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"zora{sfx}@v.de","password":"ZoraPasswort123456"}).status_code==200
def lead(tag,**kw):
    d={"firma":f"Zeit{tag} {sfx}","telefon":f"0511 55{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","email":f"zeit{tag}{sfx}@lead.de","vertriebspartner_id":pid}; d.update(kw)
    r=a.post("/api/admin/leads",json=d); assert r.status_code==200,r.text; return r.json()["id"]
andere=lead("a"); fris=lead("b"); stat=lead("c")
for i in (andere,fris): sql(f"update leads set temperatur='heiss' where id='{i}'")
sql(f"update leads set gruppe='{GR}' where id in ('{fris}','{stat}')")
chk("Ohne Daten kein Hinweis",v.get(f"/api/vertrieb/leads/{fris}").json()["anrufzeit"] is None)
# 24 Anrufe: 8 Uhr 7 von 8 erreicht, 11 Uhr 4 von 8, 14 Uhr 1 von 8
def anrufe(std,n,ok):
    for k in range(n):
        erg="anruf_erreicht" if k<ok else "anruf_nicht_erreicht"
        sql(f"insert into lead_aktivitaeten (lead_id,art,inhalt,von,ergebnis,zeit) values ('{stat}','anruf','x','t','{erg}',((current_date-{3+k%3})::timestamp + interval '{std} hours') at time zone 'Europe/Berlin')")
anrufe(8,8,7); anrufe(11,8,4); anrufe(14,8,1)
h=v.get(f"/api/vertrieb/leads/{fris}").json()["anrufzeit"]
chk("Hinweis nennt die beste Stunde und die Branche",h and GR in h["text"] and "8–9 Uhr" in h["text"] and "11" not in h["text"] and "14" not in h["text"],h)
chk("Hinweis auch im Admin",GR in (a.get(f"/api/admin/leads/{fris}").json()["anrufzeit"] or {}).get("text",""))
chk("Fremde Branche ohne Hinweis",v.get(f"/api/vertrieb/leads/{andere}").json()["anrufzeit"] is None)
# zu wenige Anrufe: keine Empfehlung
sql(f"delete from lead_aktivitaeten where lead_id='{stat}' and zeit > now() - interval '20 days' and extract(hour from zeit at time zone 'Europe/Berlin') <> 8")
chk("Zu wenige Anrufe: keine Empfehlung",v.get(f"/api/vertrieb/leads/{fris}").json()["anrufzeit"] is None)
anrufe(11,8,4); anrufe(14,8,1)
# ---------------------------------------------------------------- Anruf-Modus nach Uhrzeit
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import anrufzeiten, routes_vertriebfluss as rv, db
db.open_pool()
anrufzeiten.gruppen_jetzt=lambda cur,jetzt=None:[GR]
n1=rv._naechster_lead("heiss","","l.vertriebspartner_id=%s",[pid]); n2=rv._naechster_lead("zeit","","l.vertriebspartner_id=%s",[pid])
chk("Modus „heiß“: ältester heißer Lead zuerst",n1["id"]==andere,n1)
chk("Modus „beste Uhrzeit“: Branche mit guter Stunde zuerst",n2["id"]==fris,n2)
chk("Modus „beste Uhrzeit“ über die Schnittstelle erlaubt",v.get("/api/vertrieb/naechster",params={"modus":"zeit"}).status_code==200 and a.get("/api/admin/anrufmodus/naechster",params={"modus":"zeit"}).status_code==200)
# ---------------------------------------------------------------- Termin für die Bestätigung
chk("Ohne Termin keiner im Lead",v.get(f"/api/vertrieb/leads/{fris}").json()["termin"] is None)
morgen=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
v.post(f"/api/vertrieb/leads/{fris}/kontakt",json={"ergebnis":"rueckruf","wiedervorlage":morgen,"wiedervorlage_zeit":"10:15"})
t=v.get(f"/api/vertrieb/leads/{fris}").json()["termin"]
chk("Rückrufzeit erscheint als Termin",t and t["art"]=="rueckruf" and "T" in t["start"],t)
chk("Auch im Admin",(a.get(f"/api/admin/leads/{fris}").json()["termin"] or {}).get("art")=="rueckruf")
chk("Verlauf-Eintrag für die Bestätigung möglich",v.post(f"/api/vertrieb/leads/{fris}/aktivitaet",json={"art":"notiz","inhalt":"Terminbestätigung per WhatsApp vorbereitet"}).status_code==200)
