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
from app import jobs
kid,c,kmail=neuer_kunde("Fristfirma")
def L(name,**kw): return lead(name,**kw)
alt=L("Fristabgelaufen"); frisch=L("Fristfrisch"); tot=L("TotAlt"); toteneu=L("TotNeu"); termin=L("TerminAlt"); kundelead=L("KundeLead")
sql(f"update leads set loeschen_nach=current_date-1 where id in ('{alt}','{termin}','{kundelead}')")
sql(f"update leads set status='termin' where id='{termin}'")
sql(f"update leads set kunden_id='{kid}' where id='{kundelead}'")
sql(f"update leads set loeschen_nach=current_date+30 where id='{frisch}'")
sql(f"update leads set status='tot', loeschen_nach=current_date+30 where id in ('{tot}','{toteneu}')")
# Rule-Tabelle 'leads' = 365 Tage; 'tot' alt machen (Trigger setzt geaendert_am -> direkt per ALTER TRIGGER umgehen)
sql("alter table leads disable trigger leads_geaendert")
sql(f"update leads set geaendert_am=now()-interval '400 days' where id='{tot}'")
sql("alter table leads enable trigger leads_geaendert")
# Chat, Lead-Finder, Akquise
sql(f"insert into chat_verlauf (kunden_id,absender,text,erstellt_am) values ('{kid}','kunde','alt',now()-interval '800 days'),('{kid}','kunde','neu',now())")
sql(f"insert into lf_betriebe (name,erstellt_am) values ('Alt Betrieb',now()-interval '200 days'),('Neu Betrieb',now())")
n0=int(sql("select count(*) from loeschprotokoll"))
erg=jobs.fristen_ausfuehren()
ex=lambda i: sql(f"select count(*) from leads where id='{i}'")=="1"
chk("Abgelaufener Lead gelöscht",not ex(alt),erg)
chk("Lead mit künftiger Frist bleibt",ex(frisch))
chk("Lead im Termin/Angebot bleibt trotz Frist",ex(termin))
chk("Lead mit Kundenbezug bleibt",ex(kundelead))
chk("Toter Lead nach 400 Tagen gelöscht",not ex(tot))
chk("Frisch toter Lead bleibt",ex(toteneu))
chk("Alter Chat gelöscht, neuer bleibt",sql(f"select string_agg(text,',') from chat_verlauf where kunden_id='{kid}'")=="neu")
chk("Alter Lead-Finder-Eintrag gelöscht, neuer bleibt",sql("select string_agg(name,',') from lf_betriebe")=="Neu Betrieb",sql("select string_agg(name,',') from lf_betriebe"))
chk("Löschprotokoll führt die Löschungen",int(sql("select count(*) from loeschprotokoll"))>=n0+3 and sql("select count(*) from loeschprotokoll where tabelle like 'leads%' and regel_id is not null")!="0")
erg2=jobs.fristen_ausfuehren(); chk("Zweiter Lauf löscht nichts mehr",sum(erg2.values())==0,erg2)
sql("delete from job_marker where schluessel like 'fristen-%'"); jobs.fristen_loeschen({}); jobs.fristen_loeschen({})
if __import__('datetime').datetime.now(__import__('datetime').timezone.utc).hour>=2: chk("Tagesjob läuft nur einmal je Tag (Marker)",sql("select count(*) from job_marker where schluessel like 'fristen-%'")=="1")
# Auskunft/Export
r=a.get(f"/api/admin/kunden/{kid}/export.zip"); chk("Datenexport pro Kunde liefert ZIP",r.status_code==200 and r.content[:2]==b"PK",r.status_code)
# Demo-Daten (Anlegen, doppeltes Anlegen verhindert, Entfernen)
import os as _os
def cli(*arg): return subprocess.run(["python3","-m","app.cli",*arg],cwd=_os.environ["PYTHONPATH"],env=_os.environ.copy(),capture_output=True,text=True)
r=cli("demo-daten"); chk("Demo-Daten angelegt",r.returncode==0 and "angelegt" in r.stdout,r.stdout+r.stderr)
chk("Demo: 5 Leads, 3 Anfragen, Referenzkunde",sql("select count(*) from leads where firma like 'DEMO – %'")=="5" and sql("select count(*) from kunden where firma like 'DEMO – %' and referenzkunde")=="1" and sql("select count(*) from anfragen a join kunden k on k.id=a.kunden_id where k.firma like 'DEMO – %'")=="3")
r=cli("demo-daten"); chk("Demo-Daten nicht doppelt",r.returncode!=0 and "gibt es schon" in (r.stdout+r.stderr))
r=cli("demo-daten-entfernen"); chk("Demo-Daten entfernt",r.returncode==0 and sql("select count(*) from kunden where firma like 'DEMO – %'")=="0" and sql("select count(*) from leads where firma like 'DEMO – %'")=="0",r.stdout+r.stderr)
# Famulor-Probe: nur Struktur, keine Inhalte
sql("select 1")
kidt,ct,_=neuer_kunde("Telprobe")
knr=sql(f"select kundennummer from kunden where id='{kidt}'")
sql(f"update kunden set status='aktiv' where id='{kidt}'")
g=a.post("/api/admin/einstellungen/telefon/neues-geheimnis").json()["geheimnis"]
r=httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",json={"data":{"call_id":"x1","caller":{"phone_number":"+49 511 99999"},"summary":"Geheimer Inhalt 4711"},"extra":{"foo":1}})
chk("Webhook nimmt Nachricht an",r.status_code==200,r.text)
p=a.get("/api/admin/einstellungen/telefon").json()["letzte_nachricht"]
chk("Probe: Struktur erfasst, Zuordnung sichtbar",p and p["erkannt"].get("ref")=="call_id" and p["erkannt"].get("nummer")=="phone_number" and "dauer" in p["nicht_erkannt"],p)
chk("Probe enthält keine Inhalte (keine Rufnummer/Text)","99999" not in str(p) and "4711" not in str(p),p)
