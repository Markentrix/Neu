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
sfx=str(int(time.time())+241)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import io, json, os, sys, zipfile
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.makedirs("/var/tmp/pt/queue",exist_ok=True)
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0",QUEUE_DIR="/var/tmp/pt/queue")
from app import db, jobs, betrieb, config, einstellungen, dateien, onboarding
from app.db import tx
db.open_pool()
kA,cA,mA=neuer_kunde("Ra")
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)
# ---- 27: Sitzungen enden bei Passwortwechsel
c2=httpx.Client(base_url=B,headers=H); c2.post("/api/login",json={"email":mA,"password":"InhaberPasswort1"})
chk("zweite Sitzung läuft",c2.get("/api/me").status_code==200)
r=cA.post("/api/kunde/passwort",json={"alt":"InhaberPasswort1","neu":"NeuesPasswort123456"}); chk("Passwort geändert",r.status_code==200,r.text)
chk("andere Sitzung beendet",c2.get("/api/me").status_code==401)
chk("aktuelle Sitzung bleibt",cA.get("/api/me").status_code==200)
c3=httpx.Client(base_url=B,headers=H); c3.post("/api/login",json={"email":mA,"password":"NeuesPasswort123456"})
httpx.post(B+"/api/passwort-vergessen",headers=H,json={"email":mA}); tk=token(mA)
chk("Reset-Link vorhanden",bool(tk))
httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"WiederNeu123456789"})
chk("Reset beendet alle Sitzungen",c3.get("/api/me").status_code==401 and cA.get("/api/me").status_code==401)
# ---- 11: alle Onboarding-Ziele existieren
kern=open("/home/claude/markentrix-server/portal/static/js/kunde/kern.js").read()
ids=set(re.findall(r"^\s*\['([a-z_]+)',",kern.split("const SEITEN = [")[1].split("];")[0],re.M))
chk("Onboarding-Ziele sind echte Seiten",all(z[0] in ids for z in onboarding.KUNDE_AKTION.values()),[z for z in onboarding.KUNDE_AKTION.values() if z[0] not in ids])
# ---- 29: Mails gehen nicht verloren
with tx("system") as cur:
    cur.execute("UPDATE kunden SET benachr_anfragen=true, status='aktiv' WHERE id=%s",(kA,))
    cur.execute("INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle) VALUES (%s,'Max','max@x.de','Hallo','website') RETURNING id",(kA,)); aid=cur.fetchone()["id"]
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":9,"sicherung":"keine","absender":"info@markentrix.de"})
jobs.anfragen_mails(cfg())
chk("Mail fehlgeschlagen → Anfrage bleibt offen",sql(f"select benachrichtigt from anfragen where id='{aid}'")=="f",sql(f"select benachrichtigt from anfragen where id='{aid}'"))
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
jobs.anfragen_mails(cfg())
chk("zweiter Versuch klappt",sql(f"select benachrichtigt from anfragen where id='{aid}'")=="t" and bool(mail_an(mA,"nfrage")))
# Marker werden bei Absturz freigegeben, Fehler erst nach Erfolg gelöscht
def kaputt(c):
    jobs._marker("test-marker-"+sfx); raise RuntimeError("boom")
def gut(c): pass
kaputt.__name__="kaputt_job"
jobs._lauf(kaputt,cfg())
chk("Marker nach Absturz frei",sql(f"select count(*) from job_marker where schluessel='test-marker-{sfx}'")=="0")
with tx("system") as cur: st=betrieb.lesen(cur,"jobs")
chk("Fehler gemerkt",st["wert"].get("fehler_job")=="kaputt_job")
jobs._lauf(kaputt,cfg()); jobs._lauf(gut,cfg())
gut.__name__="kaputt_job"; jobs._lauf(gut,cfg())
with tx("system") as cur: st=betrieb.lesen(cur,"jobs")
chk("Fehler nach Erfolg gelöscht",not st["wert"].get("fehler_job"),st["wert"])
for _ in range(10): jobs._lauf(kaputt,cfg())
from app.routes_system import ampel
with tx("system") as cur: st=betrieb.lesen(cur,"jobs")
os.environ["PORTAL_JOBS"]="1"
p=[x for x in ampel(None,{"host":"x"},st,None) if x["id"]=="jobs"][0]
os.environ["PORTAL_JOBS"]="0"
chk("Dauerfehler → rot",p["status"]=="bad",p)
gut.__name__="kaputt_job"; jobs._lauf(gut,cfg())
# ---- 30: Veröffentlichung
q=config.QUEUE_DIR
(q/"ergebnis-aaaa1111bbbb2222.json").write_text(json.dumps({"id":"aaaa1111bbbb2222","aktion":"veroeffentlichen","name":"fehler-"+sfx+".de","ok":False,"text":"Fehlgeschlagen: index.html fehlt"}))
alt=q/"auftrag-0000alt.json"; alt.write_text("{}"); os.utime(alt,(time.time()-3600,time.time()-3600))
n0=int(sql("select count(*) from alarme where quelle='veroeffentlichung'"))
jobs.veroeffentlichung_wacht(cfg())
chk("Alarm bei Fehler und Stau",int(sql("select count(*) from alarme where quelle='veroeffentlichung'"))==n0+2)
jobs.veroeffentlichung_wacht(cfg())
chk("keine Doppelalarme",int(sql("select count(*) from alarme where quelle='veroeffentlichung'"))==n0+2)
chk("Mail ans Team",bool(mail_an(ADM if False else sql("select email from benutzer where rolle='admin' and aktiv order by erstellt_am limit 1"),"Veröffentlichung")))
alt.unlink(); (q/"ergebnis-aaaa1111bbbb2222.json").unlink()
# ---- 32: Quota und Dateiprüfung
cA.post("/api/login",json={"email":mA,"password":"WiederNeu123456789"})
def up(name,data,typ="application/zip"): return cA.post("/api/kunde/unterlagen",files={"datei":(name,data,typ)},data={"kategorie":"sonstiges"})
def zipb(files):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        for n,d in files.items(): z.writestr(n,d)
    return b.getvalue()
r_=up("a.zip",zipb({"x/setup.exe":"MZ"})); chk("Zip mit .exe abgelehnt",r_.status_code==400,(r_.status_code,r_.text))
chk("Office mit Makro abgelehnt",up("a.docx",zipb({"word/vbaProject.bin":"x","[Content_Types].xml":"<x/>"}),"application/octet-stream").status_code==400)
chk("PDF mit Startaktion abgelehnt",up("a.pdf",b"%PDF-1.4\n1 0 obj<</S/Launch>>endobj /Launch",).status_code==400)
chk("harmloses Zip ok",up("a.zip",zipb({"a.txt":"hallo"})).status_code==200)
chk("harmloses PDF ok",up("a.pdf",b"%PDF-1.4\n1 0 obj<<>>endobj").status_code==200)
dateien.QUOTA=10
try:
    with tx("kunde",kA) as cur:
        try: dateien.quota_pruefen(cur,kA,50); ok=False
        except Exception as e: ok=getattr(e,"status_code",0)==413; print(type(e),e)
    chk("Quota greift",ok)
finally: dateien.QUOTA=500*1024*1024
# ---- 33: Aufräumen
with tx("system") as cur:
    cur.execute("INSERT INTO alarme (zeit,stufe,quelle,titel) VALUES (now()-interval '400 days','info','test','alt-"+sfx+"')")
    cur.execute("INSERT INTO workflow_fehler (zeit,workflow_name) VALUES (now()-interval '300 days','alt-"+sfx+"')")
jobs.anrufe_bereinigen()
chk("alte Alarme und Workflow-Fehler weg",sql("select count(*) from alarme where titel='alt-"+sfx+"'")=="0" and sql("select count(*) from workflow_fehler where workflow_name='alt-"+sfx+"'")=="0")
# ---- 34: kaputtes Geheimnis fällt auf
with tx("system") as cur:
    cur.execute("INSERT INTO portal_einstellungen (schluessel,wert) VALUES ('zz"+sfx+"','kaputt') ON CONFLICT DO NOTHING")
    chk("unlesbar → leer",einstellungen.lesen(cur,"zz"+sfx)=={})
chk("… aber gemerkt",("zz"+sfx) in einstellungen.defekt)
p=[x for x in ampel(None,{"host":"x"},None,None) if x["id"]=="geheimnis"]
chk("Ampel warnt",bool(p) and p[0]["status"]=="bad")
sql("delete from portal_einstellungen where schluessel='zz"+sfx+"'"); einstellungen.defekt.clear()
import subprocess as sp
chk("mkctl-Syntax",sp.run(["bash","-n","/home/claude/markentrix-server/bin/mkctl"]).returncode==0)
