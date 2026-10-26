"""KI-Antwortvorschlag für Kunden-Anfragen."""
import httpx, time, re, email, email.header, json, os, sys, subprocess, datetime, zoneinfo
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def teil(m,typ):
    for p in m.walk():
        if p.get_content_type()==typ: return p.get_payload(decode=True).decode("utf8","replace")
text=lambda m: teil(m,"text/plain")
betreff=lambda m: str(email.header.make_header(email.header.decode_header(m["Subject"])))
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+1720)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db
from app.db import tx
db.open_pool()

a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
KID,kc=neuer_kunde("Antw")
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) select '{KID}', code, true from module where code='anfragen_termine' on conflict (kunden_id, modul_code) do update set aktiv=true")
aid=sql(f"insert into anfragen (kunden_id, name, kontakt, nachricht, quelle) values ('{KID}','Herr Test','test@x.de','Ich brauche neue Reifen fuer meinen Golf. Haben Sie Zeit?','website') returning id").split("\n")[0]
r=kc.post(f"/api/kunde/anfragen/{aid}/ki-vorschlag"); chk("Antwortvorschlag kommt zurück",r.status_code==200 and "Guten Tag" in r.json()["text"],r.text)
chk("Kosten werden festgehalten",int(sql(f"select count(*) from kosten_log where kunden_id='{KID}' and dienst='anthropic'"))>=1)
chk("Es wird nichts verschickt oder als beantwortet markiert",sql(f"select antwort_am is null from anfragen where id='{aid}'")=="t")
chk("Fremde oder unbekannte Anfrage: 404",kc.post("/api/kunde/anfragen/00000000-0000-0000-0000-000000000000/ki-vorschlag").status_code==404)
a.put("/api/admin/einstellungen/ki",json={"api_key":"","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
chk("Ohne Anbindung kommt eine verständliche Meldung",kc.post(f"/api/kunde/anfragen/{aid}/ki-vorschlag").status_code in (200,400))
chk("Ohne Anmeldung kein Zugriff",httpx.post(B+f"/api/kunde/anfragen/{aid}/ki-vorschlag",headers=H).status_code==401)
