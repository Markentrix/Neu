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
sfx=str(int(time.time())+97)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, os, sys, io, zipfile
S="/var/tmp/pt/s"
kA,cA,mA=neuer_kunde("Zua"); kB,cB,mB=neuer_kunde("Zub")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import zustellung, db
db.open_pool()
# ---- DNS-Auswertung (Abfrage ersetzt)
def fake(tab):
    return lambda name: tab.get(name, [])
zustellung.txt=fake({"gut.de":["v=spf1 include:_spf.x.de ~all"],"_dmarc.gut.de":["v=DMARC1; p=none"],"selector1._domainkey.gut.de":["v=DKIM1; k=rsa; p=ABC"]})
r=zustellung.pruefen_domain("gut.de"); chk("DNS: alles vorhanden",r["spf"]=="ok" and r["dkim"]=="ok" and r["dmarc"]=="ok" and not zustellung.schlecht(r),r)
zustellung.txt=fake({"schlecht.de":["v=spf1 +all"]})
r=zustellung.pruefen_domain("schlecht.de"); chk("DNS: SPF +all, DKIM und DMARC fehlen",r["spf"]=="warn" and r["dkim"]=="fehlt" and r["dmarc"]=="fehlt" and zustellung.schlecht(r),r)
zustellung.txt=fake({"zwei.de":["v=spf1 a ~all","v=spf1 mx ~all"]})
chk("DNS: doppelter SPF-Eintrag",zustellung.pruefen_domain("zwei.de")["spf"]=="warn")
zustellung.txt=lambda n: None
r=zustellung.pruefen_domain("offline.de"); chk("DNS nicht erreichbar: unbekannt statt falschem Alarm",r["spf"]=="unbekannt" and r["dkim"]=="unbekannt" and not zustellung.schlecht(r),r)
chk("Fehlerklassen",zustellung.fehlerart("SMTPRecipientsRefused: 550 no such user")=="adresse" and zustellung.fehlerart("SMTPAuthenticationError 535")=="anmeldung" and zustellung.fehlerart("ConnectionRefusedError")=="verbindung")
# ---- Protokoll über echten Versand
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
vor=int(sql("select count(*) from mail_protokoll"))
r=a.post("/api/admin/einstellungen/testmail",json={"an":f"ok{sfx}@ziel.de"}); chk("Testmail geht raus",r.status_code==200,r.text)
chk("Erfolg im Protokoll, nur Domain gespeichert",sql(f"select count(*) from mail_protokoll where an_domain='ziel.de' and ok")=="1" and sql("select count(*) from mail_protokoll where an_domain like '%@%'")=="0")
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":1,"sicherung":"keine","absender":"info@markentrix.de"})
r=a.post("/api/admin/einstellungen/testmail",json={"an":f"fehl{sfx}@ziel2.de"}); 
f=sql("select fehlerart from mail_protokoll where an_domain='ziel2.de' and not ok"); chk("Fehlversand im Protokoll (Verbindung)",f=="verbindung",f)
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
z=a.get("/api/admin/zustellung").json(); chk("Admin-Übersicht mit Kennzahlen",z["kennzahlen"]["fehler"]>=1 and z["kennzahlen"]["gesamt"]>=2 and z["absender"]=="info@markentrix.de",z["kennzahlen"])
chk("Kunde darf Admin-Übersicht nicht lesen",cA.get("/api/admin/zustellung").status_code==403)
chk("Prüfung auslösen",a.post("/api/admin/zustellung/pruefen").status_code==200)
kz=cA.get("/api/kunde/website-dienste/zustellung").json(); chk("Kunde: ohne eigenes Postfach keine DNS-Prüfung",kz["eigenes_postfach"] is False and kz["dns"] is None)
chk("Kunde: Prüfung ohne Postfach abgelehnt",cA.post("/api/kunde/website-dienste/zustellung/pruefen").status_code==400)
# ---- Frühwarnung: neue Signale
sql(f"update kunden set status='aktiv', erstellt_am=now()-interval '60 days' where id='{kA}'")
for _ in range(3): zustellung.protokoll(kA,"termin",f"x@besucher.de",False,"SMTPRecipientsRefused: 550 no such user")
dom=f"fw{sfx}.de"
sql(f"insert into websites (kunden_id, domain, art, status) values ('{kA}','{dom}','live','live')")
sql(f"insert into website_wacht (domain, kunden_id, ok, seite_ok, api_ok, seit, fehlversuche) values ('{dom}','{kA}',false,false,false,now()-interval '3 hours',5)")
sql(f"insert into kundenfreigaben (kunden_id, titel, art, status, angefragt_am) values ('{kA}','Alt','sonstiges','wartet',now()-interval '10 days')")
fw=a.get("/api/admin/fruehwarnung").json(); e=[x for x in fw["kunden"] if x["id"]==kA]
g=" ".join(e[0]["gruende"]) if e else ""
chk("Frühwarnung: Website gestört, Mailfehler, alte Freigabe",bool(e) and "nicht erreichbar" in g and "nicht zugestellt" in g and "Freigabe wartet" in g,g)
# ---- Datenexport
sql(f"update kunden set notizen='GEHEIM-INTERN-NOTIZ' where id='{kA}'")
os.makedirs(f"{S}/live/{dom}",exist_ok=True); open(f"{S}/live/{dom}/index.html","w").write("<html>Export</html>"); open(f"{S}/live/{dom}/site.json","w").write("{}")
c1=cA.post("/api/kunde/anfragen",json={"name":"X","kontakt":"x@y.de","nachricht":"Hallo"}) if False else None
chk("Export: Anmeldung nötig",httpx.get(B+"/api/kunde/datenexport.zip").status_code in (401,403))
r=cA.get("/api/kunde/datenexport.zip"); chk("Export: ZIP kommt",r.status_code==200 and r.headers["content-type"]=="application/zip" and r.content[:2]==b"PK",r.status_code)
zf=zipfile.ZipFile(io.BytesIO(r.content)); n=zf.namelist()
chk("Export: Inhalt (Daten, Liesmich, Website-Dateien)","daten/kunde.json" in n and "LIESMICH.txt" in n and f"websites/{dom}/index.html" in n and f"websites/{dom}/site.json" not in n,n[:12])
chk("Export: keine internen Notizen","GEHEIM-INTERN" not in zf.read("daten/kunde.json").decode())
chk("Export: nur eigene Daten",f"{kB}" not in zf.read("daten/kunde.json").decode())
chk("Audit-Eintrag für den Export",int(sql(f"select count(*) from audit_log where aktion='kunde_datenexport_selbst' and kunden_id='{kA}'"))==1)
r=cA.get("/api/kunde/datenexport.zip"); r=cA.get("/api/kunde/datenexport.zip"); r=cA.get("/api/kunde/datenexport.zip"); chk("Export: Begrenzung pro Stunde",r.status_code==429,r.status_code)
# ---- Kündigungswunsch
morgen=(datetime.date.today()+datetime.timedelta(days=40)).isoformat()
chk("Kündigung ohne Bestätigung abgelehnt",cA.post("/api/kunde/kuendigung",json={"grund":"x"}).status_code==400)
chk("Kündigung mit Datum in der Vergangenheit abgelehnt",cA.post("/api/kunde/kuendigung",json={"bestaetigt":True,"wunschdatum":"2020-01-01"}).status_code==400)
r=cA.post("/api/kunde/kuendigung",json={"bestaetigt":True,"wunschdatum":morgen,"grund":"Zu teuer"}); chk("Kündigungswunsch angenommen",r.status_code==200,r.text)
chk("Bestätigung an den Kunden",len(mail_an(mA,"Kündigungswunsch"))==1)
chk("Meldung an das Team",len(mail_an("chef@test.de",f"Zua {sfx}"))>=1)
chk("Zweiter Wunsch abgelehnt",cA.post("/api/kunde/kuendigung",json={"bestaetigt":True}).status_code==400)
chk("Kunde sieht den offenen Wunsch",cA.get("/api/kunde/kuendigung").json()["offen"]["grund"]=="Zu teuer")
chk("Anderer Kunde sieht ihn nicht",cB.get("/api/kunde/kuendigung").json()["offen"] is None)
l=a.get("/api/admin/kuendigungswuensche").json(); chk("Admin-Liste",any(x["kunden_id"]==kA for x in l),l)
fw=a.get("/api/admin/fruehwarnung").json(); e=[x for x in fw["kunden"] if x["id"]==kA]; chk("Frühwarnung: Stufe hoch wegen Kündigungswunsch",bool(e) and e[0]["stufe"]=="hoch" and any("Kündigungswunsch" in x for x in e[0]["gruende"]),e)
chk("Zurücknehmen",cA.delete("/api/kunde/kuendigung").status_code==200 and cA.get("/api/kunde/kuendigung").json()["offen"] is None)
cA.post("/api/kunde/kuendigung",json={"bestaetigt":True}); wid=a.get("/api/admin/kuendigungswuensche").json()
wid=[x["id"] for x in wid if x["kunden_id"]==kA][0]
chk("Admin: als bearbeitet markieren",a.post(f"/api/admin/kuendigungswuensche/{wid}/bearbeitet").status_code==200 and not [x for x in a.get("/api/admin/kuendigungswuensche").json() if x["kunden_id"]==kA])
chk("Admin: unbekannte ID",a.post("/api/admin/kuendigungswuensche/00000000-0000-0000-0000-000000000000/bearbeitet").status_code==404)
