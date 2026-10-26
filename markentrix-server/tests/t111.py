"""Zusatzverkauf-Hinweise (ab Werk aus), Kündigungsgrund mit Auswertung, Kalender-Abo der Vertriebler."""
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
sfx=str(int(time.time())+1730)
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
pub=httpx.Client(base_url=B,headers=H)
# ------------------------------------------------------------ Hinweise im Kundenportal
kid,c=neuer_kunde("Tipp")
chk("Hinweise sind ab Werk aus",a.get("/api/admin/zusatzverkauf").json()["aktiv"] is False)
sql(f"update kunden set erstellt_am=now()-interval '60 days', status='aktiv' where id='{kid}'")
for i in range(6): sql(f"insert into anfragen (kunden_id,name,quelle) values ('{kid}','Anrufer {i}','telefon')")
chk("Ausgeschaltet: kein Hinweis trotz Zahlen",c.get("/api/kunde/tipp").json()["tipp"] is None)
chk("Einschalten braucht Anmeldung",pub.put("/api/admin/zusatzverkauf",json={"aktiv":True}).status_code in (401,403))
chk("Einschalten",a.put("/api/admin/zusatzverkauf",json={"aktiv":True}).status_code==200)
t=c.get("/api/kunde/tipp").json()["tipp"]
chk("Viele Telefonanfragen: Hinweis auf BUSINESS ohne Preis",t and t["code"]=="KI_BUSINESS" and "€" not in json.dumps(t),t)
chk("Reaktion mit falscher Art abgelehnt",c.post("/api/kunde/tipp/KI_BUSINESS/reaktion",json={"art":"kaufen"}).status_code==422)
chk("Reaktion auf unbekannten Hinweis: 404",c.post("/api/kunde/tipp/GIBTSNICHT/reaktion",json={"art":"nein"}).status_code==404)
chk("Nein danke",c.post("/api/kunde/tipp/KI_BUSINESS/reaktion",json={"art":"nein"}).status_code==200)
chk("Nach Ablehnung 90 Tage Ruhe",c.get("/api/kunde/tipp").json()["tipp"] is None)
sql(f"update kunden_tipps set geaendert_am=now()-interval '100 days' where kunden_id='{kid}'")
chk("Nach der Ruhezeit wieder möglich",(c.get("/api/kunde/tipp").json()["tipp"] or {}).get("code")=="KI_BUSINESS")
z=[x for x in a.get("/api/admin/zusatzverkauf").json()["zahlen"] if x["code"]=="KI_BUSINESS"]
chk("Auswertung zählt gezeigt",z and z[0]["gezeigt"]>=1,z)
kid2,c2=neuer_kunde("Neutip")
for i in range(6): sql(f"insert into anfragen (kunden_id,name,quelle) values ('{kid2}','A {i}','telefon')")
chk("Neuer Kunde (unter 30 Tage): kein Hinweis",c2.get("/api/kunde/tipp").json()["tipp"] is None)
a.put("/api/admin/zusatzverkauf",json={"aktiv":False}); chk("Wieder aus: kein Hinweis",c.get("/api/kunde/tipp").json()["tipp"] is None)
# ------------------------------------------------------------ Kündigungsgrund
kid3,c3=neuer_kunde("Kuend")
chk("Ungültiger Grundcode abgelehnt",c3.post("/api/kunde/kuendigung",json={"bestaetigt":True,"grund_code":"quatsch"}).status_code==422)
r=c3.post("/api/kunde/kuendigung",json={"bestaetigt":True,"grund_code":"preis","grund":"zu teuer für uns"}); chk("Kündigung mit Grund",r.status_code==200,r.text)
chk("Grund gespeichert",sql(f"select grund_code from kuendigungswuensche where kunden_id='{kid3}'")=="preis")
g=a.get("/api/admin/kuendigungsgruende").json(); e=[x for x in g["gruende"] if x["code"]=="preis"]
chk("Auswertung nennt Grund",e and e[0]["n"]>=1 and e[0]["text"]=="zu teuer" and g["gesamt"]>=1,g)
chk("Auswertung nur für Admin",pub.get("/api/admin/kuendigungsgruende").status_code in (401,403))
kl=[x for x in a.get("/api/admin/kuendigungswuensche").json() if x.get("kunden_id")==kid3] if isinstance(a.get("/api/admin/kuendigungswuensche").json(),list) else []
chk("Admin-Liste enthält Grundcode",not kl or kl[0].get("grund_code")=="preis",kl)
# ------------------------------------------------------------ Kalender-Abo
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Kalle Kalender","email":f"kalle{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"kalle{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"KallePasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"kalle{sfx}@v.de","password":"KallePasswort123456"}).status_code==200
chk("Kunde hat keinen Kalender-Link",c.get("/api/vertrieb/kalender-link").status_code==403)
chk("Anfangs kein Link",v.get("/api/vertrieb/kalender-link").json()["link"] is None)
l1=v.post("/api/vertrieb/kalender-link/neu").json()["link"]
chk("Link https und webcal",l1["https"].startswith("http") and l1["webcal"].startswith("webcal://") and ".ics" in l1["https"],l1)
tok=l1["https"].split("/kalender/")[1][:-4]
lead=a.post("/api/admin/leads",json={"firma":f"Kal;Firma, Test {sfx}","telefon":f"0511 88{sfx[-6:]}","ort":"Celle","plz":"29221","vertriebspartner_id":pid}).json()["id"]
sql(f"update leads set wiedervorlage_am=current_date+2 where id='{lead}'")
r=pub.get(f"/api/public/kalender/{tok}.ics"); ics=r.text
chk("ICS ohne Anmeldung abrufbar",r.status_code==200 and "text/calendar" in r.headers["content-type"] and ics.startswith("BEGIN:VCALENDAR") and ics.rstrip().endswith("END:VCALENDAR"),ics[:200])
chk("Wiedervorlage im Kalender, Sonderzeichen maskiert","Kal\\;Firma\\, Test "+sfx in ics.replace("\r\n ",""),ics[:600])
chk("Zeilen höchstens 75 Zeichen",all(len(x.encode())<=75 for x in ics.split("\r\n")))
sql(f"update leads set status='verloren' where id='{lead}'")
chk("Verlorener Lead verschwindet",f"Test {sfx}" not in pub.get(f"/api/public/kalender/{tok}.ics").text.replace("\r\n ",""))
chk("Falscher Token: 404",pub.get("/api/public/kalender/"+"x"*43+".ics").status_code==404)
chk("Zu kurzer Token: 404",pub.get("/api/public/kalender/abc.ics").status_code==404)
l2=v.post("/api/vertrieb/kalender-link/neu").json()["link"]
chk("Neuer Link macht alten ungültig",pub.get(f"/api/public/kalender/{tok}.ics").status_code==404 and l2["https"]!=l1["https"])
chk("Neuer Link funktioniert",pub.get("/api/public/kalender/"+l2["https"].split("/kalender/")[1]).status_code==200)
sql(f"update vertriebspartner set status='beendet' where id='{pid}'")
chk("Gesperrter Vertriebler: 404",pub.get("/api/public/kalender/"+l2["https"].split("/kalender/")[1]).status_code==404)
