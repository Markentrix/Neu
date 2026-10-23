"""Interne Daten bleiben beim Team: Selbstbedienungs-Export des Kunden und Profiländerung durch Nicht-Inhaber."""
import httpx, time, re, email, email.header, subprocess, io, zipfile, json
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+400)
mk=f"exp{sfx}@k.de"
k=a.post("/api/admin/kunden",json={"firma":f"Export {sfx}","ansprechpartner":"Tina Test","email":mk,"telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(mk),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); assert c.post("/api/login",json={"email":mk,"password":"InhaberPasswort1"}).status_code==200
# Team-interne Daten anlegen
sql(f"insert into dateien (kunden_id,bereich,name,mime,groesse,daten,von,sichtbar_kunde) values ('{kid}','dokument','NUR-TEAM-intern.txt','text/plain',5,'\\x696e7465726e','team',false)")
sql(f"insert into dateien (kunden_id,bereich,name,mime,groesse,daten,von,sichtbar_kunde) values ('{kid}','dokument','fuer-kunde.txt','text/plain',5,'\\x6f6666656e','team',true)")
sql(f"insert into belege (kunden_id,art,status,notiz) values ('{kid}','rechnung','entwurf','GEHEIM-ENTWURF-NOTIZ')")
sql(f"insert into belege (kunden_id,art,status,notiz) values ('{kid}','rechnung','gestellt','GEHEIM-INTERNE-BELEGNOTIZ')")
sql(f"update kunden set notizen='GEHEIM-KUNDENNOTIZ-TEAM' where id='{kid}'")
r=c.get("/api/kunde/datenexport.zip"); chk("Export kommt",r.status_code==200 and r.headers["content-type"]=="application/zip",r.status_code)
z=zipfile.ZipFile(io.BytesIO(r.content)); namen=z.namelist(); alles=b"".join(z.read(n) for n in namen).decode("utf8","replace")
chk("Export: Datei mit sichtbar_kunde=false fehlt",not any("NUR-TEAM" in n for n in namen),namen)
chk("Export: sichtbare Datei ist dabei",any("fuer-kunde.txt" in n for n in namen),namen)
chk("Export: Beleg-Entwurf fehlt",json.loads(z.read("daten/belege.json")).__len__()==1 and "GEHEIM-ENTWURF-NOTIZ" not in alles)
chk("Export: interne Beleg-Notiz fehlt",("GEHEIM-INTERNE-BELEGNOTIZ" not in alles))
chk("Export: interne Kunden-Notiz des Teams fehlt","GEHEIM-KUNDENNOTIZ-TEAM" not in alles)
# Admin-Export enthält dagegen alles
ra=a.get(f"/api/admin/kunden/{kid}/export.zip")
if ra.status_code==200:
    za=zipfile.ZipFile(io.BytesIO(ra.content)); chk("Admin-Export enthält auch die interne Datei",any("NUR-TEAM" in n for n in za.namelist()),za.namelist())
else: print("INFO Admin-Export-Route:",ra.status_code)
# Profil: Empfang darf die E-Mail-Adresse nicht umleiten, aber unveränderte Werte speichern
t=c.post("/api/kunde/team/einladen",json={"name":"Emma Empfang","email":f"emp{sfx}@k.de","kunden_rolle":"empfang"}); chk("Empfangs-Zugang angelegt",t.status_code==200,t.text)
tk=token(f"emp{sfx}@k.de"); httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"EmpfangPasswort1"})
e=httpx.Client(base_url=B,headers=H); chk("Empfang meldet sich an",e.post("/api/login",json={"email":f"emp{sfx}@k.de","password":"EmpfangPasswort1"}).status_code==200)
r=e.patch("/api/kunde/profil",json={"email":"umleitung@boese.de"}); chk("Empfang kann Kontakt-E-Mail nicht ändern",r.status_code in (403,),r.text)
r=e.patch("/api/kunde/profil",json={"benachr_email":"umleitung@boese.de"}); chk("Empfang kann Benachrichtigungs-Adresse nicht ändern",r.status_code==403,r.text)
chk("Adressen unverändert",sql(f"select email||'|'||coalesce(benachr_email,'') from kunden where id='{kid}'")==f"{mk}|")
r=e.patch("/api/kunde/profil",json={"email":mk,"benachr_email":"","benachr_termine":False}); chk("Empfang kann unveränderte Adressen mitsenden und Schalter ändern",r.status_code==200,r.text)
r=c.patch("/api/kunde/profil",json={"benachr_email":"neu@firma.de"}); chk("Inhaber kann die Adresse ändern",r.status_code==200 and sql(f"select benachr_email from kunden where id='{kid}'")=="neu@firma.de",r.text)

# ---- Website-Dienste: Pausierung, Freigabe, Vertragsende
sid=sql(f"select site_id from website_dienste where kunden_id='{kid}'")
if not sid:
    c.get("/api/kunde/website-dienste"); sid=sql(f"select site_id from website_dienste where kunden_id='{kid}'")
chk("Website-Dienste-Kennung vorhanden",sid.startswith("mk_"),sid)
sql(f"update website_dienste set mail_aktiv=true, kal_aktiv=true, kal_freigabe=false, mail_empfaenger='chef@firma.de' where kunden_id='{kid}'")
sql(f"insert into websites (kunden_id,domain,art,status) values ('{kid}','exp{sfx}.de','live','live') on conflict do nothing")
O={"Origin":f"https://exp{sfx}.de"}
def kontakt(): return httpx.post(B+f"/site/{sid}/kontakt",headers={**O},content=json.dumps({"name":"Max","email":"max@x.de","nachricht":"Hallo","einwilligung":True}))
chk("Widget-Kontaktformular normal erreichbar",kontakt().status_code in (200,),kontakt().text)
import sys; sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, mailer
db.open_pool(); ok,grund=mailer.senden("zeile@x.de","Betreff mit\nZeilenumbruch","Text"); time.sleep(1)
chk("Betreff mit Zeilenumbruch verhindert den Mailversand nicht",ok,grund)
chk("Betreff wurde zu einer Zeile",any("Betreff mit Zeilenumbruch" in str(email.header.make_header(email.header.decode_header(m["Subject"] or ""))) for m in mails() if "zeile@x.de" in str(m["To"])))
sql(f"update website_dienste set verzug_pause=true where kunden_id='{kid}'")
chk("Widget-Kontakt bei Zahlungsverzug-Pause gesperrt (503)",kontakt().status_code==503)
r=httpx.post(B+f"/site/{sid}/termin",headers=O,content=json.dumps({"start":"2030-01-01T09:00:00+01:00","name":"Max","email":"max@x.de","einwilligung":True})); chk("Widget-Termin bei Pause gesperrt (503)",r.status_code==503,r.text)
sql(f"update website_dienste set verzug_pause=false, kal_freigabe=true where kunden_id='{kid}'")
r=httpx.post(B+f"/site/{sid}/termin",headers=O,content=json.dumps({"start":"2030-01-01T09:00:00+01:00","name":"Max","email":"max@x.de","einwilligung":True})); chk("Widget-Termin bucht nie am Betrieb vorbei, wenn Bestätigung nötig ist (409)",r.status_code==409,r.text)
sql(f"update kunden set status='beendet' where id='{kid}'")
chk("Nach Vertragsende: Widget-Kontakt nicht mehr möglich (404)",kontakt().status_code==404)
chk("Nach Vertragsende: Website-API antwortet nicht mehr (404)",httpx.get(B+"/siteapi/api/verfuegbarkeit",headers={"Host":f"exp{sfx}.de"}).status_code==404)
sql(f"update kunden set status='aktiv' where id='{kid}'")
# ---- Vertriebler nach Partner-Ende
pe=f"vp{sfx}@v.de"; p=a.post("/api/admin/vertrieb/partner",json={"name":f"Ende {sfx}","email":pe,"status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(pe),"password":"VertriebPasswort1"})
v=httpx.Client(base_url=B,headers=H); rl=v.post("/api/login",json={"email":pe,"password":"VertriebPasswort1"}); chk("Vertriebler meldet sich an",rl.status_code==200,rl.text)
r=v.get("/api/vertrieb/leads"); chk("Vertriebler sieht seine Leads",r.status_code==200,r.text)
sql(f"update vertriebspartner set status='beendet' where id='{p}'")
r=v.get("/api/vertrieb/leads"); chk("Nach Partner-Ende kein Zugang mehr (bestehende Sitzung)",r.status_code==401,(r.status_code,r.text))
chk("Nach Partner-Ende kein neuer Login",v.post("/api/login",json={"email":pe,"password":"VertriebPasswort1"}).status_code in (401,403) or v.get("/api/vertrieb/leads").status_code==401)
