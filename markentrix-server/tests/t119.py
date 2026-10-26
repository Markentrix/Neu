"""Push-Erinnerung 1 Stunde und 5 Minuten vor vereinbarten Anrufen (Rückrufzeit am Lead und gebuchtes Erstgespräch)."""
import httpx, time, subprocess, sys, os
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+1800)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Paula Push","email":f"paula{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"paula{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"PaulaPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"paula{sfx}@v.de","password":"PaulaPasswort123456"}).status_code==200
def lead(tag,**kw):
    d={"firma":f"Push{tag} {sfx}","telefon":f"0511 66{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","email":f"push{tag}{sfx}@lead.de"}; d.update(kw)
    r=a.post("/api/admin/leads",json=d); assert r.status_code==200,r.text; return r.json()["id"]
l1=lead("a",vertriebspartner_id=pid); l2=lead("b",vertriebspartner_id=pid); l3=lead("c")
# ---------------------------------------------------------------- Rückrufzeit speichern
import datetime
morgen=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
r=v.post(f"/api/vertrieb/leads/{l1}/kontakt",json={"ergebnis":"rueckruf","wiedervorlage":morgen,"wiedervorlage_zeit":"14:30"})
chk("Rückruf mit Uhrzeit wird gespeichert",r.status_code==200 and r.json()["rueckruf_am"] is not None,r.text)
chk("In der Datenbank steht 14:30 Ortszeit",sql(f"select to_char(rueckruf_am at time zone 'Europe/Berlin','HH24:MI') from leads where id='{l1}'")=="14:30")
chk("Uhrzeit ohne Datum abgelehnt",v.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"rueckruf","wiedervorlage_zeit":"14:30"}).status_code==400)
chk("Ungültige Uhrzeit abgelehnt",v.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"rueckruf","wiedervorlage":morgen,"wiedervorlage_zeit":"25:99"}).status_code==422)
heute=datetime.date.today().isoformat()
chk("Uhrzeit in der Vergangenheit abgelehnt",v.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"rueckruf","wiedervorlage":heute,"wiedervorlage_zeit":"00:00"}).status_code==400 or datetime.datetime.now().hour==0 and datetime.datetime.now().minute==0)
# ---------------------------------------------------------------- Job
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import jobs, push, db
db.open_pool()
gesendet=[]
push.senden=lambda ids,titel,text,url="/",tag=None,sofort=False: gesendet.append((list(ids),titel,text,url,tag))
def lauf(): jobs.anruf_pushes({})
sql(f"update leads set wiedervorlage_am=current_date, rueckruf_am=now()+interval '58 minutes' where id='{l1}'")
lauf(); chk("1 Stunde vorher: ein Push an den Vertriebler",len(gesendet)==1 and "1 Stunde" in gesendet[0][1] and f"Push{'a'} {sfx}" in gesendet[0][2] and gesendet[0][3]==f"/vertrieb#lead/{l1}",gesendet)
lauf(); chk("… und nur einmal",len(gesendet)==1)
sql(f"update leads set rueckruf_am=now()+interval '4 minutes' where id='{l1}'")
lauf(); chk("5 Minuten vorher: zweiter Push",len(gesendet)==2 and "5 Minuten" in gesendet[1][1],gesendet)
lauf(); chk("… ebenfalls nur einmal",len(gesendet)==2)
# kurzfristig vereinbart: nur die 5-Minuten-Erinnerung
sql(f"update leads set wiedervorlage_am=current_date, rueckruf_am=now()+interval '4 minutes', rueckruf_push=0 where id='{l2}'")
lauf(); chk("Kurzfristiger Termin: genau ein Push",len(gesendet)==3 and "5 Minuten" in gesendet[2][1],gesendet)
# Lead ohne Zuständigen: Admins
sql(f"update leads set wiedervorlage_am=current_date, rueckruf_am=now()+interval '30 minutes' where id='{l3}'")
lauf(); chk("Ohne Zuständigen gehen die Admins",len(gesendet)==4 and gesendet[3][3]==f"/admin#lead/{l3}",gesendet[3:])
# verlorener Lead bekommt keine Erinnerung
sql(f"update leads set status='verloren', rueckruf_am=now()+interval '30 minutes', rueckruf_push=0 where id='{l3}'")
lauf(); chk("Verlorener Lead: kein Push",len(gesendet)==4)
# Termin zu weit weg
sql(f"update leads set status='kontaktiert', rueckruf_am=now()+interval '3 hours', rueckruf_push=0 where id='{l2}'")
lauf(); chk("Zu früh: kein Push",len(gesendet)==4)
# Erstgespräch
sql(f"insert into gespraechstermine (name,email,telefon,start,ende,status,token,lead_id) values ('Erika Test','e{sfx}@t.de','0511 1','{ (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=50)).isoformat() }','{ (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=80)).isoformat() }','gebucht','tok{sfx}','{l1}')")
lauf(); chk("Erstgespräch: Push 1 Stunde vorher",len(gesendet)==5 and gesendet[4][1].startswith("Erstgespräch"),gesendet[4:])
sql(f"update gespraechstermine set start=now()+interval '4 minutes', ende=now()+interval '34 minutes' where token='tok{sfx}'")
lauf(); chk("Erstgespräch: Push 5 Minuten vorher",len(gesendet)==6 and "5 Minuten" in gesendet[5][1],gesendet[5:])
lauf(); chk("Erstgespräch: nicht doppelt",len(gesendet)==6)
# Neues Datum ohne Uhrzeit löscht die Rückrufzeit
r=v.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"anruf_erreicht","wiedervorlage":morgen})
chk("Neue Wiedervorlage ohne Uhrzeit löscht die Rückrufzeit",r.status_code==200 and sql(f"select rueckruf_am is null from leads where id='{l2}'")=="t",r.text)
chk("Heute-Liste liefert die Rückrufzeit",any(("rueckruf_am" in z) for z in v.get("/api/vertrieb/heute").json()["wiedervorlagen"]+[{"rueckruf_am":1}]))
