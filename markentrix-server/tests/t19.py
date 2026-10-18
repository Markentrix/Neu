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
import os, json, zipfile
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Ali Markt","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    time.sleep(1.2); httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
kid,c=neuer_kunde("Briefa"); kid2,c2=neuer_kunde("Fremdb")
# ---- Briefing
r=c.get("/api/kunde/briefing"); chk("Briefing leer",r.status_code==200 and r.json()["status"]=="offen" and r.json()["daten"]=={} and len(r.json()["struktur"])==5,r.text)
chk("Start-Badge: Briefing offen",c.get("/api/kunde/start").json()["badges"]["briefing"]==1)
r=c.put("/api/kunde/briefing",json={"daten":{"beschreibung":"Türkischer Supermarkt","zielgruppe":"Familien"},"abschicken":False}); chk("Zwischenspeichern",r.status_code==200 and r.json()["status"]=="gespeichert",r.text)
chk("Zwischenstand bleibt",c.get("/api/kunde/briefing").json()["daten"]["beschreibung"]=="Türkischer Supermarkt" and c.get("/api/kunde/briefing").json()["status"]=="offen")
r=c.put("/api/kunde/briefing",json={"daten":{"beschreibung":"x"},"abschicken":True}); chk("Abschicken ohne Pflichtfelder",r.status_code==400 and "Öffnungszeiten" in r.text,r.text)
chk("Unbekanntes Feld",c.put("/api/kunde/briefing",json={"daten":{"hack":"x"}}).status_code==400)
chk("Zu langer Text",c.put("/api/kunde/briefing",json={"daten":{"beschreibung":"x"*3001}}).status_code==400)
n0=len(mails())
r=c.put("/api/kunde/briefing",json={"daten":{"beschreibung":"Türkischer Supermarkt","oeffnungszeiten":"Mo-Sa 8-20","leistungen":"Obst, Gemüse, Fleisch","ton":"freundlich"},"abschicken":True}); chk("Abschicken",r.status_code==200 and r.json()["status"]=="abgeschickt",r.text)
b=c.get("/api/kunde/briefing").json(); chk("Status abgeschickt",b["status"]=="abgeschickt" and b["abgeschickt_am"])
chk("Start-Badge weg",c.get("/api/kunde/start").json()["badges"]["briefing"]==0)
time.sleep(2); chk("Mail ans Team",any("Briefing abgeschickt" in str(m["Subject"]) for m in mails()[n0:]))
chk("Aufgabe fürs Team",sql(f"select count(*) from aufgaben where kunden_id='{kid}' and titel like 'Briefing prüfen%'")=="1")
ad=a.get(f"/api/admin/kunden/{kid}/briefing").json(); chk("Admin sieht Briefing",ad["status"]=="abgeschickt" and ad["daten"]["leistungen"]=="Obst, Gemüse, Fleisch")
chk("Admin 404",a.get("/api/admin/kunden/nix/briefing").status_code==404)
chk("Fremder sieht nichts",c2.get("/api/kunde/briefing").json()["daten"]=={})
# nur_lesen darf nicht schreiben
r=c.post("/api/kunde/team/einladen",json={"email":f"lese{sfx}@k.de","name":"Lese","kunden_rolle":"nur_lesen"}); chk("Team einladen",r.status_code==200,r.text)
time.sleep(1.2); httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"lese{sfx}@k.de"),"password":"LesePasswort123"})
cl=httpx.Client(base_url=B,headers=H); cl.post("/api/login",json={"email":f"lese{sfx}@k.de","password":"LesePasswort123"})
chk("nur_lesen kann ansehen",cl.get("/api/kunde/briefing").status_code==200)
chk("nur_lesen kann nicht schreiben",cl.put("/api/kunde/briefing",json={"daten":{"beschreibung":"y"}}).status_code==403)
# ---- Auswertung
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle) values ('{kid}','A','a@x.de','h','website'),('{kid}','B','b@x.de','h','telefon'),('{kid}','S','s@x.de','h','website')")
sql(f"update anfragen set status='spam' where kunden_id='{kid}' and name='S'")
sql(f"insert into termine (kunden_id,titel,beginn) values ('{kid}','T1',now())")
r=c.get("/api/kunde/auswertung"); j=r.json(); chk("Auswertung 200",r.status_code==200,r.text)
chk("Anfragen ohne Spam gezählt",j["dieser"]["anfragen"]["gesamt"]==2 and j["dieser"]["anfragen"]["nach_quelle"]=={"website":1,"telefon":1},j["dieser"]["anfragen"])
chk("Termine gezählt",j["dieser"]["termine"]["gesamt"]==1)
chk("12 Wochen + 6 Monate",len(j["wochen"])==12 and len(j["monate"])==6 and j["wochen"][-1]["anfragen"]==2 and j["monate"][-1]["anfragen"]==2,j["wochen"])
chk("Monatsname",j["monat_name"].endswith(str(time.localtime().tm_year)) and j["extern"]==[])
j2=c2.get("/api/kunde/auswertung").json(); chk("Fremder sieht eigene Zahlen",j2["dieser"]["anfragen"]["gesamt"]==0)
# ---- Externe Zahlen
mon=time.strftime("%Y-%m")
chk("Extern: ungültiger Monat",a.put(f"/api/admin/kunden/{kid}/kennzahlen-extern",json={"monat":"2026-13"}).status_code==422)
chk("Extern: Sterne zu hoch",a.put(f"/api/admin/kunden/{kid}/kennzahlen-extern",json={"monat":mon,"google_sterne":6}).status_code==422)
chk("Extern: negativ",a.put(f"/api/admin/kunden/{kid}/kennzahlen-extern",json={"monat":mon,"besucher":-1}).status_code==422)
r=a.put(f"/api/admin/kunden/{kid}/kennzahlen-extern",json={"monat":mon,"besucher":1200,"google_aufrufe":3400,"google_bewertungen":87,"google_sterne":4.6}); chk("Extern speichern",r.status_code==200,r.text)
a.put(f"/api/admin/kunden/{kid}/kennzahlen-extern",json={"monat":mon,"besucher":1300,"google_aufrufe":3400,"google_bewertungen":88,"google_sterne":4.7})
chk("Extern überschreibt",sql(f"select count(*) from kennzahlen_extern where kunden_id='{kid}'")=="1" and a.get(f"/api/admin/kunden/{kid}/kennzahlen-extern").json()[0]["besucher"]==1300)
e=c.get("/api/kunde/auswertung").json()["extern"]; chk("Kunde sieht Zahlen",len(e)==1 and e[0]["google_sterne"]=="4.7" or e[0]["google_sterne"]==4.7,e)
chk("Fremder sieht keine",c2.get("/api/kunde/auswertung").json()["extern"]==[])
chk("Kunde kann Extern nicht schreiben",c.put(f"/api/admin/kunden/{kid}/kennzahlen-extern",json={"monat":mon,"besucher":1}).status_code in (401,403))
# ---- Export
sql(f"update kunden set status='gekuendigt' where id='{kid}'")
z=zipfile.ZipFile(io.BytesIO(a.get(f"/api/admin/kunden/{kid}/export.zip").content)); chk("Export: Briefing + Zahlen","daten/briefings.json" in z.namelist() and "Türkischer Supermarkt" in z.read("daten/briefings.json").decode() and "daten/kennzahlen_extern.json" in z.namelist())
import app.db as db
try: db.close_pool()
except Exception: pass
