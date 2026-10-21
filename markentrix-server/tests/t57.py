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
sfx=str(int(time.time())+121)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"mwst_satz":19,"steuernummer":"12/345/67890"})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, os, sys, threading, time as _t
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
kA,cA,mA=neuer_kunde("Aboa"); kB,cB,mB=neuer_kunde("Abob")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import abo, config, db, jobs, webbetrieb, berichte
db.open_pool()
heute=datetime.date.today()
# ================= Wartungsvertrag
chk("Monate addieren (Monatsende)",abo.monate_addieren(datetime.date(2026,1,31),1)==datetime.date(2026,2,28) and abo.monate_addieren(datetime.date(2026,11,15),3)==datetime.date(2027,2,15) and abo.monate_addieren(datetime.date(2026,12,1),12)==datetime.date(2027,12,1))
chk("Zeitraumtext",abo.zeitraum(datetime.date(2026,11,1),1)=="01.11.2026 – 30.11.2026" and abo.zeitraum(datetime.date(2026,1,1),3)=="01.01.2026 – 31.03.2026")
sql(f"update kunden set status='aktiv' where id in ('{kA}','{kB}')")
sql(f"delete from buchungen where kunden_id='{kA}'")
sql(f"insert into buchungen (kunden_id, produkt_code, monatlich_cent, rabatt_cent, status) values ('{kA}','KI_ONE',4900,900,'aktiv')")
chk("Testkunde hat eine aktive Buchung",sql(f"select count(*) from buchungen where kunden_id='{kA}' and status='aktiv'")=="1")
P=f"/api/admin/kunden/{kA}/abrechnungsplaene"
chk("Kunde darf keine Pläne sehen",cA.get(P).status_code==403)
chk("Leere Liste",a.get(P).json()=={"plaene":[]})
chk("Ungültiger Turnus",a.post(P,json={"titel":"Wartung","intervall_monate":2,"aus_buchungen":True,"naechste_am":heute.isoformat()}).status_code==400)
chk("Ohne Positionen abgelehnt",a.post(P,json={"titel":"Wartung","intervall_monate":1,"aus_buchungen":False,"positionen":[],"naechste_am":heute.isoformat()}).status_code==400)
chk("Enddatum vor Beginn abgelehnt",a.post(P,json={"titel":"Wartung","intervall_monate":1,"aus_buchungen":True,"naechste_am":heute.isoformat(),"enddatum":(heute-datetime.timedelta(days=5)).isoformat()}).status_code==400)
r=a.post("/api/admin/kunden/00000000-0000-0000-0000-000000000000/abrechnungsplaene",json={"titel":"Wa","intervall_monate":1,"aus_buchungen":True,"naechste_am":heute.isoformat()}); chk("Unbekannter Kunde",r.status_code==404,(r.status_code,r.text[:100]))
r=a.post(P,json={"titel":"Wartung & Betrieb","intervall_monate":3,"aus_buchungen":True,"naechste_am":(heute+datetime.timedelta(days=10)).isoformat(),"auto_senden":False}); chk("Plan angelegt",r.status_code==200,r.text)
pid=r.json()["id"]
jobs.abrechnungslauf if False else None
n=abo.lauf(); chk("Noch nicht fällig: nichts erzeugt",n==0 and sql(f"select count(*) from belege where plan_id='{pid}'")=="0")
sql(f"update abrechnungsplaene set naechste_am=current_date where id='{pid}'")
n=abo.lauf(); chk("Fällig: eine Rechnung erzeugt",n==1 and sql(f"select count(*) from belege where plan_id='{pid}'")=="1",n)
b=sql(f"select status||'|'||art||'|'||netto_cent||'|'||brutto_cent||'|'||leistungszeitraum||'|'||nummer from belege where plan_id='{pid}'").split("|")
chk("Ausgestellt, Rechnung, 3 Monate à 40,00 netto (49 − 9 Rabatt), 19 % USt",b[0]=="gestellt" and b[1]=="rechnung" and b[2]=="12000" and b[3]=="14280" and b[5].startswith("RE-"),b)
chk("Leistungszeitraum 3 Monate",b[4].startswith(heute.strftime("%d.%m.%Y")) and b[4].count("–")==1,b[4])
chk("Plan rückt um 3 Monate weiter",sql(f"select naechste_am from abrechnungsplaene where id='{pid}'")==abo.monate_addieren(heute,3).isoformat())
chk("Ohne Auto-Versand keine Mail an den Kunden",not mail_an(mA,"Rechnung"))
n=abo.lauf(); chk("Zweiter Lauf am selben Tag: nichts doppelt",n==0 and sql(f"select count(*) from belege where plan_id='{pid}'")=="1")
sql(f"update abrechnungsplaene set naechste_am=current_date where id='{pid}'")
n=abo.lauf(); chk("Zeitraum schon abgerechnet: keine zweite Rechnung, Plan rückt weiter",n==0 and sql(f"select count(*) from belege where plan_id='{pid}'")=="1" and sql(f"select naechste_am from abrechnungsplaene where id='{pid}'")==abo.monate_addieren(heute,3).isoformat())
# Auto-Versand + nachholen
r=a.post(P,json={"titel":"Hosting","intervall_monate":1,"aus_buchungen":False,"positionen":[{"text":"Hosting","menge":1,"einheit":"Monat","preis_cent":1500}],"naechste_am":(heute-datetime.timedelta(days=62)).isoformat(),"auto_senden":True}); pid2=r.json()["id"]
n=abo.lauf()
chk("Rückstand: bis zu 3 Zeiträume werden nachgeholt",sql(f"select count(*) from belege where plan_id='{pid2}'")=="3",sql(f"select count(*) from belege where plan_id='{pid2}'"))
ms=mail_an(mA,"Rechnung"); chk("Auto-Versand: Rechnung per Mail mit PDF",len(ms)>=1 and any("pdf" in str(p.get_content_type()) for m in ms for p in m.walk()),len(ms))
chk("Versendet-Status gesetzt",sql(f"select count(*) from belege where plan_id='{pid2}' and status='versendet'")=="3")
# Sofort erzeugen
sql(f"update abrechnungsplaene set naechste_am=current_date+5, auto_senden=false where id='{pid2}'")
r=a.post(f"/api/admin/abrechnungsplaene/{pid2}/jetzt"); chk("Jetzt erzeugen",r.status_code==200 and r.json()["nummer"].startswith("RE-"),r.text)
chk("Kunde darf nicht auslösen",cA.post(f"/api/admin/abrechnungsplaene/{pid2}/jetzt").status_code==403)
# Pausieren, Ändern, Enddatum
r=a.put(f"/api/admin/abrechnungsplaene/{pid2}",json={"aktiv":False}); chk("Pausiert",r.status_code==200 and sql(f"select aktiv::text from abrechnungsplaene where id='{pid2}'")=="false")
sql(f"update abrechnungsplaene set naechste_am=current_date where id='{pid2}'"); vor=sql(f"select count(*) from belege where plan_id='{pid2}'"); abo.lauf()
chk("Pausiert: keine Rechnung",sql(f"select count(*) from belege where plan_id='{pid2}'")==vor)
a.put(f"/api/admin/abrechnungsplaene/{pid2}",json={"aktiv":True,"enddatum":(heute-datetime.timedelta(days=1)).isoformat()}); abo.lauf()
chk("Enddatum erreicht: Plan beendet sich selbst",sql(f"select aktiv::text from abrechnungsplaene where id='{pid2}'")=="false" and sql(f"select count(*) from belege where plan_id='{pid2}'")==vor)
chk("Fremde ID / Müll: 404",a.put("/api/admin/abrechnungsplaene/abc",json={"aktiv":False}).status_code==404 and a.delete("/api/admin/abrechnungsplaene/abc").status_code==404)
# Kunde nicht aktiv / Kündigung / Referenzkunde
r=a.post(f"/api/admin/kunden/{kB}/abrechnungsplaene",json={"titel":"Bb","intervall_monate":1,"aus_buchungen":False,"positionen":[{"text":"x","menge":1,"einheit":"","preis_cent":1000}],"naechste_am":heute.isoformat()}); pidB=r.json()["id"]
sql(f"update kunden set status='pausiert' where id='{kB}'") if False else sql(f"update kunden set status='onboarding' where id='{kB}'")
abo.lauf(); chk("Kunde nicht aktiv: keine Rechnung",sql(f"select count(*) from belege where plan_id='{pidB}'")=="0")
sql(f"update kunden set status='aktiv' where id='{kB}'")
sql(f"insert into kuendigungswuensche (kunden_id, status, ende_am, ip) values ('{kB}','offen','{(heute-datetime.timedelta(days=0)).isoformat()}','127.0.0.1')")
abo.lauf(); chk("Vertragsende erreicht: Plan beendet, keine Rechnung",sql(f"select count(*) from belege where plan_id='{pidB}'")=="0" and sql(f"select aktiv::text from abrechnungsplaene where id='{pidB}'")=="false")
sql(f"update kunden set referenzkunde=true where id='{kB}'")
r=a.post(f"/api/admin/kunden/{kB}/abrechnungsplaene",json={"titel":"Bb","intervall_monate":1,"aus_buchungen":True,"naechste_am":heute.isoformat()}); chk("Referenzkunde: kein Plan",r.status_code==400)
# fehlende Firmendaten -> klare Meldung, Lauf bleibt stabil
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"mwst_satz":19,"steuernummer":"","ustid":""})
sql(f"update abrechnungsplaene set naechste_am=current_date-400 where id='{pid}'")
r=a.post(f"/api/admin/abrechnungsplaene/{pid}/jetzt"); chk("Ohne Steuernummer: verständliche Meldung",r.status_code==400 and "Steuernummer" in r.text,r.text)
n=abo.lauf(); chk("Lauf ohne Firmendaten bricht nicht ab",n==0)
r=a.delete(f"/api/admin/abrechnungsplaene/{pid}"); chk("Plan löschen, Rechnungen bleiben",r.status_code==200 and sql(f"select count(*) from belege where plan_id='{pid}'")=="1")
# ================= Qualität (Ladezeit, tote Links)
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        p=self.path
        if p=="/langsam": _t.sleep(0.6)
        code=404 if p.startswith("/tot") else 200
        body=b'<html><body><a href="/a">a</a><a href="/tot1">t</a><a href="/langsam">l</a><a href="/a#x">dup</a><a href="mailto:a@b.de">m</a><a href="https://fremd.de/x">f</a><a href="/tot2">t2</a></body></html>' if p=="/" else b"ok"
        self.send_response(code); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
srv=ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
config.WACHT_BASIS=f"http://127.0.0.1:{srv.server_port}"; webbetrieb.LANGSAM_MS=300
dom=f"qual{sfx}.de"
sql(f"insert into websites (kunden_id, domain, art, status) values ('{kA}','{dom}','live','live')")
e=webbetrieb.qualitaet_pruefen(dom)
chk("Crawl: Seiten, tote Links, langsame Seite",e["seiten"]==5 and sorted(t["pfad"] for t in e["tote"])==["/tot1","/tot2"] and [l["pfad"] for l in e["langsam"]]==["/langsam"] and e["median_ms"] is not None,e)
chk("Externe Links, mailto und Anker werden nicht geprüft",all("fremd" not in t["pfad"] for t in e["tote"]))
n=webbetrieb.qualitaetslauf(); chk("Tageslauf speichert",n>=1 and sql(f"select jsonb_array_length(tote)||'|'||seiten from website_qualitaet where domain='{dom}'")=="2|5")
config.WACHT_BASIS="http://127.0.0.1:1"
e=webbetrieb.qualitaet_pruefen(dom); chk("Seite nicht erreichbar: kein Messwert statt falscher Zahlen",e["fehler"] and e["seiten"]==0)
chk("Lauf überschreibt bei Ausfall nichts",webbetrieb.qualitaetslauf() is not None and sql(f"select seiten from website_qualitaet where domain='{dom}'")=="5")
sql(f"insert into website_wacht (domain, kunden_id, ok, seite_ok, api_ok, seit) values ('{dom}','{kA}',true,true,true,now())")
w=cA.get("/api/kunde/website-dienste/wacht").json(); x=[s for s in w["seiten"] if s.get("domain")==dom]
chk("Kunde sieht Qualität in der Wacht-Anzeige",bool(x) and x[0]["qualitaet"] and len(x[0]["qualitaet"]["tote"])==2,w)
with db.tx("system") as cur: d=berichte.sammeln(cur,kA,heute.replace(day=1),heute+datetime.timedelta(days=1))
q=d["website"]["qualitaet"]; chk("Monatsbericht enthält Qualität",q and q["tote"]==2 and q["langsam"]==1,q)
with db.tx("system") as cur: bid_b=berichte.erstellen(cur,kA,heute.replace(day=1))
with db.tx("system") as cur: pdfb,_=berichte.pdf_erzeugen(cur,bid_b)
chk("Bericht-PDF entsteht",pdfb[:4]==b"%PDF")
