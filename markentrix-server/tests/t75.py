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
sfx=str(int(time.time())+257)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import io, json, os, sys, base64, datetime
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)
kid,c,mail=neuer_kunde("Onb")
r=c.get("/api/kunde/startliste"); chk("Startliste: Kunde ist am Zug",r.status_code==200 and r.json().get("am_zug")=="kunde",r.text[:200])
# Stillstand: 15 Tage alt, nichts erledigt
sql(f"update kunden set erstellt_am=now()-interval '15 days', status='onboarding' where id='{kid}'")
sql(f"update onboarding_punkte set erledigt_am=NULL where kunden_id='{kid}'")
jobs.aufgaben_automatisch(cfg())
chk("Aufgabe: Kunde anrufen bei Stillstand",int(sql(f"select count(*) from aufgaben where kunden_id='{kid}' and titel like 'Kunde anrufen%'"))==1)
jobs.aufgaben_automatisch(cfg())
chk("Aufgabe nur einmal pro Woche",int(sql(f"select count(*) from aufgaben where kunden_id='{kid}' and titel like 'Kunde anrufen%'"))==1)
sql(f"update benutzer set passwort_hash=NULL where kunden_id='{kid}'")
jobs.aufgaben_automatisch(cfg())
chk("Aufgabe: Zugang prüfen, Einladung neu senden",int(sql(f"select count(*) from aufgaben where kunden_id='{kid}' and titel like 'Zugang prüfen%'"))==1)
# Freigabe mit Datum, Entscheidung
r=a.post(f"/api/admin/kunden/{kid}/freigaben-kunden",json={"titel":"Beitrag Test","art":"social","inhalt":"Text","veroeffentlichung_am":str(datetime.date.today()+datetime.timedelta(days=3))}); chk("Freigabe angelegt",r.status_code==200,r.text)
# Ticket und Team-Antwort
t=c.post("/api/kunde/tickets",json={"betreff":"Frage","art":"frage","text":"Hallo"}); chk("Nachricht angelegt",t.status_code==200,t.text)
r=a.post(f"/api/admin/tickets/{t.json()['id']}/nachricht",json={"text":"Antwort vom Team"}); chk("Team-Antwort funktioniert",r.status_code==200,r.text)
# Upload ins Onboarding: kein Fehler
r=c.post("/api/kunde/unterlagen",files={"datei":("logo.png",b"\x89PNG\r\n\x1a\n"+b"0"*50,"image/png")},data={"kategorie":"logo_material"}); chk("Unterlage hochgeladen (mit Team-Hinweis)",r.status_code==200,r.text[:200])
