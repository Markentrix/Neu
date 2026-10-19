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
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":"0511 5555","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200

import xml.etree.ElementTree as ET
from datetime import date, timedelta
sys.path.insert(0,"/home/claude/markentrix-server/portal")
r=a.get("/api/me/ansicht").json(); chk("Ansicht: gesetzt=False am Anfang",r.get("gesetzt") is False,r)
a.put("/api/me/ansicht",json={"ausgeblendet":[]}); chk("Ansicht: gesetzt=True nach Speichern",a.get("/api/me/ansicht").json()["gesetzt"] is True)
# ===== Cockpit: Trichter, Prognose, Ziel
kid,c,kmail=neuer_kunde("Wertkunde")
sql(f"update kunden set status='aktiv' where id='{kid}'")
l1=lead("Tr1"); l2=lead("Tr2"); l3=lead("Tr3"); l4=lead("Tr4")
sql(f"update leads set status='antwort' where id='{l2}'"); sql(f"update leads set status='termin' where id='{l3}'"); sql(f"update leads set status='gewonnen' where id='{l4}'")
co=a.get("/api/admin/cockpit").json(); t=co["trichter"]
chk("Trichter zählt Stufen",t["gesamt"]>=4 and t["erreicht"]>=3 and t["gespraech"]>=2 and t["kunden"]>=1 and t["gesamt"]>=t["bearbeitet"]>=t["erreicht"]>=t["gespraech"]>=t["kunden"],t)
chk("Prognose hat 5 Zeiträume",[p["name"] for p in co["prognose"]]==["überfällig","0–7 Tage","8–14 Tage","15–21 Tage","22–30 Tage"],co["prognose"])
chk("Ziel anfangs 0",co["ziel_mrr_cent"]==0)
chk("Ziel setzen",a.put("/api/admin/cockpit/ziel",json={"mrr_cent":500000}).status_code==200 and a.get("/api/admin/cockpit").json()["ziel_mrr_cent"]==500000)
chk("Ziel: negativ abgewiesen",a.put("/api/admin/cockpit/ziel",json={"mrr_cent":-5}).status_code==422)
chk("Ziel: Kunde darf nicht",c.put("/api/admin/cockpit/ziel",json={"mrr_cent":1}).status_code==403)
# Prognose mit offenen Rechnungen (je 119,00 € brutto)
f=a.get("/api/admin/einstellungen/firma").json(); f["name"]=f["name"] or "Markentrix Test"; f["iban"]="DE02120300000000202051"; f["bic"]="BYLADEM1001"; f.update({"strasse":"Weg 5","plz":"29221","ort":"Celle","steuernummer":"12/345/67890","email":"info@markentrix.de","inhaber":"Chris Test"})
chk("Firma mit IBAN",a.put("/api/admin/einstellungen/firma",json=f).status_code==200)
def rechnung(tage):
    b=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","betreff":"Test","positionen":[{"text":"Leistung","menge":1,"einheit":"","preis_cent":10000}]}).json()["id"]
    assert a.post(f"/api/admin/belege/{b}/ausstellen").status_code==200
    sql(f"update belege set faellig_am=current_date+({tage}) where id='{b}'"); return b
rechnung(-2); rechnung(3); rechnung(10); rechnung(40)
pg={p["name"]:p["cent"] for p in a.get("/api/admin/cockpit").json()["prognose"]}
chk("Prognose: überfällig, 0–7, 8–14, nach 30 Tagen nicht enthalten",pg["überfällig"]==11900 and pg["0–7 Tage"]==11900 and pg["8–14 Tage"]==11900 and pg["15–21 Tage"]==0 and pg["22–30 Tage"]==0,pg)
# ===== Kunden-Wert
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,status,erstellt_am) values ('{kid}','A','x','y','neu',now()),('{kid}','B','x','y','beantwortet',now()),('{kid}','C','x','y','neu',date_trunc('month',now())-interval '5 days'),('{kid}','S','x','y','spam',now())")
sql(f"insert into anrufe (kunden_id,richtung,beginn,dauer_sek) values ('{kid}','ein',now(),120),('{kid}','ein',now(),60),('{kid}','aus',now(),600),('{kid}','ein',date_trunc('month',now())-interval '3 days',30)")
w=c.get("/api/kunde/wert").json()
chk("Wert: Anfragen (ohne Spam), Vormonat, bearbeitet",w["anfragen"]=={"jetzt":2,"vorher":1,"bearbeitet":1},w)
chk("Wert: Anrufe nur eingehende, Minuten",w["anrufe"]["jetzt"]==2 and w["anrufe"]["vorher"]==1 and w["anrufe"]["minuten"]==3,w)
chk("Wert: Monat im Format JJJJ-MM",len(w["monat"])==7)
chk("Wert: nur für Kunden",a.get("/api/kunde/wert").status_code==403 and httpx.get(B+"/api/kunde/wert").status_code==401)
k2,c2,_=neuer_kunde("Fremd")
chk("Wert: Mandantentrennung",c2.get("/api/kunde/wert").json()["anfragen"]["jetzt"]==0)
