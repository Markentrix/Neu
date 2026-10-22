from datetime import date, timedelta
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
sfx=str(int(time.time())+7)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":f"0511 {time.time_ns()}","ort":"Celle",**kw}).json()["id"]; return i
import os, datetime
os.environ["BACKUP_DIR"]="/var/tmp/pt/bk"
ROOT=os.path.dirname(os.environ["PYTHONPATH"].split(":")[0])
sys.path.insert(0,ROOT+"/portal")
from app import db, jobs
db.open_pool()
def schreibe(alter_min=2,backup=5,platte=40):
    json.dump({"zeit":time.time()-alter_min*60,"backup_stunden":backup,"offsite_stunden":9999,"offsite_aktiv":False,"platte_prozent":platte,"zertifikat_tage":60,"probleme":[]},open("/var/tmp/pt/bk/system.json","w"))
def lauf():
    with db.tx("system") as cur: cfg=jobs.einstellungen_lesen(cur)
    jobs.betriebs_alarm(cfg); time.sleep(1.5)
def glocke(): return int(sql("select count(*) from benachrichtigungen where tag='betriebsalarm'") or 0)
def alarmmails(t=""): return [m for m in mails() if "Markentrix: " in str(m["Subject"]) and t in str(email.header.make_header(email.header.decode_header(m["Subject"] or "")))]
sql("delete from betrieb_status where schluessel='alarm'"); sql("delete from benachrichtigungen where tag='betriebsalarm'")
schreibe(); lauf(); chk("Alarm: alles grün -> nichts gemeldet",glocke()==0)
schreibe(backup=70); lauf(); n1=glocke()
chk("Alarm: Sicherung rot -> Glocke für Admin(s)",n1>=1,n1)
chk("Alarm: Text nennt den Punkt","Sicherung" in sql("select titel from benachrichtigungen where tag='betriebsalarm' order by id desc limit 1"))
chk("Alarm: Mail verschickt",len(alarmmails("Betriebsalarm"))>=1)
lauf(); chk("Alarm: bleibt rot -> keine Wiederholung innerhalb 24 h",glocke()==n1,glocke())
sql("update betrieb_status set wert=jsonb_set(wert,'{punkte,backup,gemeldet}','1') where schluessel='alarm'")
lauf(); chk("Alarm: nach 24 h erneut erinnert",glocke()>n1,glocke())
n2=glocke(); schreibe(); lauf()
chk("Alarm: wieder grün -> Entwarnung",glocke()>n2 and "Wieder in Ordnung" in sql("select titel from benachrichtigungen where tag='betriebsalarm' order by id desc limit 1"))
n3=glocke(); lauf(); chk("Alarm: nach Entwarnung Ruhe",glocke()==n3)
schreibe(alter_min=45); lauf(); chk("Alarm: verstummter Wächter wird gemeldet",glocke()>n3)
schreibe()
cl=httpx.Client(base_url=B,headers=H)
chk("Alarm: Anlass im Admin-Menü der Push-Einstellungen (common.js)","betriebsalarm" in open(ROOT+"/portal/static/js/common.js").read())

# ---- Wochenrückblick (Montags, nur Zahlen)
import datetime as _dt
from zoneinfo import ZoneInfo
class _Montag(_dt.datetime):
    @classmethod
    def now(cls, tz=None): return _dt.datetime(2030,1,7,9,0,tzinfo=tz or ZoneInfo("Europe/Berlin"))   # Montag
class _Dienstag(_dt.datetime):
    @classmethod
    def now(cls, tz=None): return _dt.datetime(2030,1,8,9,0,tzinfo=tz or ZoneInfo("Europe/Berlin"))
sql("delete from job_marker where schluessel like 'wochenrueckblick-%'"); sql("delete from benachrichtigungen where tag='wochenrueckblick'")
neuer_kunde("Rueck")  # Kunde mit Anfragen
kid_r=sql(f"select id from kunden where firma='Rueck {sfx}'")
for i in range(3): sql(f"INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES ('{kid_r}','R{i}','r{i}@x.de','T','website','neu',now()-interval '1 day',true)")
sql(f"update kunden set status='aktiv' where id='{kid_r}'")
with db.tx("system") as cur: cfg=jobs.einstellungen_lesen(cur)
jobs.datetime=_Dienstag; jobs.wochenrueckblick(cfg); time.sleep(1.2)
chk("Rückblick: Dienstag -> nichts",int(sql("select count(*) from benachrichtigungen where tag='wochenrueckblick'") or 0)==0)
jobs.datetime=_Montag; jobs.wochenrueckblick(cfg); time.sleep(1.5)
kt=sql(f"select text from benachrichtigungen b join benutzer u on u.id=b.benutzer_id where b.tag='wochenrueckblick' and u.kunden_id='{kid_r}'")
chk("Rückblick: Kunde bekommt Zahlen (3 Anfragen)","3 Anfragen" in kt,kt)
chk("Rückblick: Admin bekommt Wochenrückblick",int(sql("select count(*) from benachrichtigungen b join benutzer u on u.id=b.benutzer_id where b.tag='wochenrueckblick' and u.rolle='admin'") or 0)>=1)
chk("Rückblick: keine Namen im Text","R0" not in kt and "Rueck" not in kt,kt)
n=int(sql("select count(*) from benachrichtigungen where tag='wochenrueckblick'")); jobs.wochenrueckblick(cfg); time.sleep(1)
chk("Rückblick: nur einmal pro Woche",int(sql("select count(*) from benachrichtigungen where tag='wochenrueckblick'"))==n)
