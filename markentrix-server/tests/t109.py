"""Datenschutz-Anfragen (DSGVO): öffentliches Formular, Frist, Suche, Auskunftsdatei, Löschung mit Sperre, Fristen-Job."""
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
sfx=str(int(time.time())+1710)
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

from app import jobs
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
pub=httpx.Client(base_url=B,headers=H)
mail=f"dsg{sfx}@person.de"
L=a.post("/api/admin/leads",json={"firma":f"Person Betrieb {sfx}","telefon":f"0511 33{sfx[-5:]}","email":mail,"ansprechpartner":"Paula Person","ort":"Celle","plz":"29221"}).json()["id"]
a.post(f"/api/admin/leads/{L}/aktivitaet",json={"art":"notiz","inhalt":"Wollte Rückruf wegen Website"})
# ---------------------------------------------------------------- Eingang
chk("Formular-Seite wird ausgeliefert",pub.get("/datenschutz-anfrage").status_code==200 and "dsgvo.js" in pub.get("/datenschutz-anfrage").text)
chk("Ungültige Art wird abgelehnt",pub.post("/api/public/datenschutz-anfrage",json={"art":"x","name":"Paula Person","email":mail}).status_code==422)
chk("Ungültige E-Mail wird abgelehnt",pub.post("/api/public/datenschutz-anfrage",json={"art":"auskunft","name":"Paula Person","email":"kaputt"}).status_code==400)
chk("Roboterfalle legt nichts an",pub.post("/api/public/datenschutz-anfrage",json={"art":"auskunft","name":"Bot Bot","email":"bot@x.de","zweitfeld":"x"}).status_code==200 and sql("select count(*) from datenschutz_anfragen where name='Bot Bot'")=="0")
r=pub.post("/api/public/datenschutz-anfrage",json={"art":"auskunft","name":"Paula Person","email":mail,"nachricht":"Welche Daten habt ihr?"}); chk("Anfrage über das Formular klappt",r.status_code==200,r.text); time.sleep(1.2)
d=a.get("/api/admin/datenschutz-anfragen").json(); x=[q for q in d["anfragen"] if q["email"]==mail][0]; aid=x["id"]
fr=(datetime.date.fromisoformat(x["eingang_am"])); chk("Frist ist ein Monat nach Eingang",x["frist_am"]>x["eingang_am"] and 28<=(datetime.date.fromisoformat(x["frist_am"])-fr).days<=31 and x["status"]=="neu" and not x["identitaet_geprueft"],x)
chk("Aufgabe mit Frist angelegt",int(sql(f"select count(*) from aufgaben where auto_schluessel='dsgvo-{aid}'"))==1)
chk("Team bekommt eine Mail",any("Datenschutz-Anfrage" in betreff(m) for m in mails()))
chk("Zähler offen/überfällig stimmt",d["offen"]>=1 and d["ueberfaellig"]==0)
chk("Ohne Anmeldung kein Zugriff",pub.get("/api/admin/datenschutz-anfragen").status_code in (401,403))
# ---------------------------------------------------------------- Suche, Auskunft
t=a.get(f"/api/admin/datenschutz-anfragen/{aid}/suche").json(); chk("Suche findet den Lead",[l["id"] for l in t["leads"]]==[L],t)
r=a.get(f"/api/admin/datenschutz-anfragen/{aid}/auskunft"); j=r.json()
chk("Auskunftsdatei enthält Lead und Verlauf",r.status_code==200 and "attachment" in r.headers["content-disposition"] and j["leads"][0]["firma"]==f"Person Betrieb {sfx}" and any("Rückruf" in (e["inhalt"] or "") for e in j["leads"][0]["verlauf"]),r.text[:300])
# ---------------------------------------------------------------- Löschen
r=a.post(f"/api/admin/datenschutz-anfragen/{aid}/loeschen",json={"lead_ids":["00000000-0000-0000-0000-000000000000"]}); chk("Fremde Lead-ID wird nicht gelöscht",r.status_code==200 and r.json()["geloescht"]==0 and r.json()["fehler"],r.text)
r=a.post(f"/api/admin/datenschutz-anfragen/{aid}/loeschen",json={"lead_ids":[L],"sperren":True}); chk("Löschen mit Sperre klappt",r.status_code==200 and r.json()["geloescht"]==1 and not r.json()["fehler"],r.text)
chk("Lead ist weg",sql(f"select count(*) from leads where id='{L}'")=="0" and sql(f"select count(*) from lead_aktivitaeten where lead_id='{L}'")=="0")
chk("E-Mail steht auf der Sperrliste",sql(f"select count(*) from sperrliste where wert='{mail}'")=="1")
chk("Löschprotokoll hat einen Eintrag",int(sql("select count(*) from loeschprotokoll where tabelle like 'leads (Datenschutz-Anfrage)%'"))>=1)
chk("Status springt auf „in Arbeit“",sql(f"select status from datenschutz_anfragen where id='{aid}'")=="in_arbeit")
chk("Ungültiger Status wird abgelehnt",a.put(f"/api/admin/datenschutz-anfragen/{aid}",json={"status":"x"}).status_code==422)
r=a.put(f"/api/admin/datenschutz-anfragen/{aid}",json={"status":"erledigt","identitaet_geprueft":True,"notiz":"Auskunft per Mail"}); chk("Erledigt setzt das Datum",r.status_code==200 and sql(f"select identitaet_geprueft||'|'||(erledigt_am=current_date) from datenschutz_anfragen where id='{aid}'")=="true|true",r.text)
d=a.get("/api/admin/datenschutz-anfragen").json(); chk("Erledigte Anfrage zählt nicht mehr als offen",all(q["id"]!=aid or not q["bald"] for q in d["anfragen"]))
# ---------------------------------------------------------------- Selbst erfasst und Fristen-Job
alt=(datetime.date.today()-datetime.timedelta(days=25)).isoformat()
r=a.post("/api/admin/datenschutz-anfragen",json={"art":"loeschung","name":"Brief Absender","quelle":"brief","eingang_am":alt,"nachricht":"Per Post"}); chk("Anfrage per Brief erfassen",r.status_code==200,r.text); bid=r.json()["id"]
chk("Frist ist rechnerisch in wenigen Tagen",int(sql(f"select frist_am - current_date from datenschutz_anfragen where id='{bid}'"))<=7)
n=jobs.dsgvo_fristen_pruefen(); chk("Fristen-Job meldet die bald ablaufende Anfrage",n>=1 and int(sql(f"select count(*) from aufgaben where auto_schluessel='dsgvo-frist-{bid}'"))==1,n)
chk("Zweiter Lauf meldet nicht doppelt",jobs.dsgvo_fristen_pruefen()==0)
sql(f"update datenschutz_anfragen set frist_am=current_date-2 where id='{bid}'")
d=a.get("/api/admin/datenschutz-anfragen").json(); chk("Überfällige Anfrage wird gezählt",d["ueberfaellig"]>=1 and [q for q in d["anfragen"] if q["id"]==bid][0]["ueberfaellig"])
st=[pub.post("/api/public/datenschutz-anfrage",json={"art":"auskunft","name":"Spam Spam","email":"s@x.de","zweitfeld":"x"}).status_code for _ in range(8)]
chk("Zu viele Formular-Anfragen werden gebremst",429 in st,st)
