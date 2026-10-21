import httpx, time, re, email, subprocess
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
sfx=str(int(time.time())+129)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"mwst_satz":19,"steuernummer":"12/345/67890"})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import os, sys
sys.path.insert(0,"/home/claude/markentrix-server/portal")
ENV={**os.environ,"DATABASE_URL":"postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest","PORTAL_SECRET":"testgeheimnis123","PORTAL_JOBS":"0","SELBSTTEST_URL":B,"PYTHONPATH":"/home/claude/markentrix-server/portal"}
def lauf():
    r=subprocess.run([sys.executable,"-m","app.cli","selbsttest"],capture_output=True,text=True,env=ENV,cwd="/home/claude/markentrix-server/portal",timeout=300); return r.returncode,r.stdout+r.stderr
os.environ.update(ENV)
from app import db, betrieb
db.open_pool(); betrieb.notieren("jobs")
rc,out=lauf()
chk("Selbsttest: alles in Ordnung",rc==0 and "FEHLER" not in out,out)
for t in ("Portal antwortet","Anmeldung weist falsche Daten ab","Datenbank erreichbar","Mail-Server","Website-API antwortet","Hintergrundaufgaben laufen"):
    chk("Selbsttest prüft: "+t,t in out,out)
chk("Selbsttest sendet keine Mail",not mail_an("selbsttest@invalid.example"))
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":1,"sicherung":"keine","absender":"info@markentrix.de"})
rc,out=lauf(); chk("Mail-Server nicht erreichbar: Fehler gemeldet",rc==1 and "FEHLER  Mail-Server" in out,out)
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
