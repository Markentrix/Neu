import sys, os, time, re, email, httpx
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_BASE_URL="http://localhost:8000")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs, berichte, mailer
from email import policy
db.open_pool()
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else i)
def cl(): return httpx.Client(base_url=B,headers=H)
def mails():
    raw=open("/var/tmp/pt/mails.txt").read(); return [m for m in raw.split("\n=====\n") if m.strip()] if "=====" in raw else [raw]
a=cl(); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
open("/var/tmp/pt/mails.txt","w").close()
k=a.post("/api/admin/kunden",json={"firma":"Bericht GmbH","email":"bg@x.de","ansprechpartner":"Bea","paket_code":"KI_ONE","einladen":True}).json()
kid=k["id"]
with db.tx("admin") as cur:
    cur.execute("UPDATE kunden SET status='aktiv', erstellt_am=now()-interval '90 days' WHERE id=%s",(kid,))
    # Daten im Vormonat
    vm=berichte.vormonat(); 
    for i in range(5): cur.execute("INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES (%s,%s,%s,%s,%s,%s,%s,true)",(kid,f"Max{i}","max@x.de","Bitte Angebot","website","erledigt" if i<3 else "neu",vm.replace(day=10)))
    cur.execute("INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES (%s,'Spammer','s@s.de','buy','email','spam',%s,true)",(kid,vm.replace(day=11)))
    cur.execute("INSERT INTO termine (kunden_id,titel,beginn,status) VALUES (%s,'Beratung',%s,'erledigt')",(kid,vm.replace(day=12)))
    cur.execute("INSERT INTO anrufe (kunden_id,richtung,beginn,dauer_sek) VALUES (%s,'ein',%s,125)",(kid,vm.replace(day=13)))
mails_vor=len(open("/var/tmp/pt/mails.txt").read())
# --- Neue Anfrage → Mail
with db.tx("admin") as cur:
    cur.execute("INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle) VALUES (%s,'Neuer Lead','lead@x.de','Ich brauche eine Website','website')",(kid,))
    cur.execute("INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status) VALUES (%s,'Spam','s@x.de','kauf','email','spam')",(kid,))
cfg=jobs.STANDARD.copy()
open("/var/tmp/pt/mails.txt","w").close()
jobs.anfragen_mails(cfg); time.sleep(0.5)
txt=open("/var/tmp/pt/mails.txt").read()
def dec(t):
    out=""
    for m in re.split(r"\n={5,}\n|(?m)^From nobody.*$",t):
        pass
    return t
chk("anfrage-mail an kunde","bg@x.de" in txt)
jobs.anfragen_mails(cfg); chk("kein zweiter Versand",txt==open("/var/tmp/pt/mails.txt").read())
with db.tx("admin") as cur:
    cur.execute("SELECT count(*) n FROM anfragen WHERE NOT benachrichtigt"); chk("alles markiert",cur.fetchone()["n"]==0)
# --- Kunde schaltet ab
a.patch  # noqa
# --- Termin-Erinnerung
with db.tx("admin") as cur:
    cur.execute("INSERT INTO termine (kunden_id,titel,beginn,status,kontakt_name) VALUES (%s,'Morgen-Termin',now()+interval '5 hours','geplant','Herr Test')",(kid,))
    cur.execute("INSERT INTO termine (kunden_id,titel,beginn,status) VALUES (%s,'Weit weg',now()+interval '10 days','geplant')",(kid,))
open("/var/tmp/pt/mails.txt","w").close()
jobs.termin_erinnerungen(cfg); t2=open("/var/tmp/pt/mails.txt").read()
chk("erinnerung gesendet","bg@x.de" in t2 and "Erinnerung" in t2)
with db.tx("admin") as cur:
    cur.execute("SELECT titel, erinnerung_gesendet FROM termine WHERE kunden_id=%s AND titel IN ('Morgen-Termin','Weit weg')",(kid,)); r={x["titel"]:x["erinnerung_gesendet"] for x in cur.fetchall()}
chk("nur nahe Termine",r=={"Morgen-Termin":True,"Weit weg":False},r)
# --- Monatsbericht manuell
bm=vm.strftime("%Y-%m")
r=a.post(f"/api/admin/kunden/{kid}/bericht",json={"monat":bm,"senden":True}).json(); chk("bericht erstellt+gesendet",r["gesendet"] is True,r)
r2=a.post(f"/api/admin/kunden/{kid}/bericht",json={"monat":bm,"senden":False}).json(); chk("idempotent",r2["id"]==r["id"])
chk("aktueller Monat abgelehnt",a.post(f"/api/admin/kunden/{kid}/bericht",json={"monat":date_s if (date_s:=time.strftime('%Y-%m')) else ''}).status_code==400)
l=a.get(f"/api/admin/kunden/{kid}/berichte").json(); chk("liste",len(l)==1 and l[0]["versendet_am"])
p=a.get(f"/api/admin/berichte/{r['id']}/pdf"); chk("admin pdf",p.status_code==200 and p.content[:4]==b"%PDF" and len(p.content)>2000,p.status_code)
open("/var/tmp/pt/bericht.pdf","wb").write(p.content)
raw=open("/var/tmp/pt/mails.txt").read(); chk("pdf angehängt","application/pdf" in raw and "Monatsbericht" in raw)
# --- Kunde sieht Bericht, nicht fremde
with db.tx("system") as cur:
    cur.execute("SELECT einladung_token_hash FROM benutzer WHERE kunden_id=%s",(kid,))
m=re.search(r"token=([\w-]+)",raw) ; 
tok=re.search(r"token=([A-Za-z0-9_=-]+)",open("/var/tmp/pt/mails.txt").read())
