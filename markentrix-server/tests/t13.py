import httpx, base64, subprocess, time, re, email
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time()))
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
k=a.post("/api/admin/kunden",json={"firma":"AVV Test "+sfx,"ansprechpartner":"Anna","email":f"anna{sfx}@av.de","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
d=a.get(f"/api/admin/kunden/{kid}/avv").json(); chk("leer",d["liste"]==[] and d["vorhanden"] is False,d)
chk("auf Fehlt-Liste",any(x["id"]==kid for x in a.get("/api/admin/avv-fehlt").json()))
chk("übersicht avv_fehlt",any(x["id"]==kid for x in a.get("/api/admin/uebersicht").json()["avv_fehlt"]))
chk("liste avv_ok false",[x for x in a.get("/api/admin/kunden?q="+sfx).json()][0]["avv_ok"] is False)
v=a.get(f"/api/admin/avv-vorschlag/{kid}").json(); chk("Vorschlag: Portal + Weisung aus Kunde",v["anlage"]["module"]==["portal"] and v["anlage"]["weisung_name"]=="Anna" and v["anlage"]["weisung_email"]==f"anna{sfx}@av.de",v)
chk("Modul ohne Domain abgelehnt",a.post(f"/api/admin/kunden/{kid}/avv",json={"module":["portal","domain"]}).status_code==400)
chk("E-Mail ohne Konto-Wahl abgelehnt",a.post(f"/api/admin/kunden/{kid}/avv",json={"module":["portal","email"]}).status_code==400)
r=a.post(f"/api/admin/kunden/{kid}/avv",json={"module":["portal","email_auftragnehmer","domain","ki_chat"],"domain":f"avv{sfx}.de","weisung_name":"Anna","weisung_email":f"anna{sfx}@av.de"}); chk("erstellen",r.status_code==200,r.text); aid=r.json()["id"]
p=a.get(f"/api/admin/avv/{aid}/pruefen").json(); chk("Prüfliste: Hauptvertrags-Datum fehlt",len(p["offen"])==1 and "Hauptvertrag" in p["offen"][0],p)
r=a.post(f"/api/admin/avv/{aid}/senden"); chk("Senden gesperrt bei offenen Punkten",r.status_code==400 and "Hauptvertrag" in r.text,r.text)
chk("Freigabe gesperrt bei offenen Punkten",a.post(f"/api/admin/avv/{aid}/portal-freigeben").status_code==400)
chk("Datum ungültig abgelehnt",a.put(f"/api/admin/avv/{aid}/anlage",json={"module":["portal"],"hauptvertrag_datum":"morgen"}).status_code==422)
r=a.put(f"/api/admin/avv/{aid}/anlage",json={"module":["portal","email_auftragnehmer","domain","ki_chat"],"domain":f"avv{sfx}.de","hauptvertrag_datum":"2026-10-01","weisung_name":"Anna","weisung_email":f"anna{sfx}@av.de"}); chk("Anlage speichern",r.status_code==200,r.text)
chk("Prüfliste leer",a.get(f"/api/admin/avv/{aid}/pruefen").json()["offen"]==[])
r=a.get(f"/api/admin/avv/{aid}/vorlage.pdf"); chk("pdf",r.status_code==200 and r.content[:4]==b"%PDF",r.text[:200]); open("avv.pdf","wb").write(r.content)
x=subprocess.run(["pdftotext","-layout","avv.pdf","-"],capture_output=True,text=True).stdout
chk("AVV V2: Inhalt",all(s in x for s in ["Anlage 1: Gebuchte Module","Anlage 2: Technische","Anlage 3: Unterauftragsverarbeiter","Version 2","01.10.2026",f"avv{sfx}.de","Anthropic","INWX","Hetzner","Google Ireland"]),x[:400])
chk("AVV V2: nicht gebuchte Anbieter fehlen",not any(s in x for s in ["BEK Service","Meta Platforms Ireland"]) and "[Datum]" not in x,x[-600:])
r=a.post(f"/api/admin/avv/{aid}/senden"); chk("senden",r.status_code==200,r.text)
time.sleep(1)
raw=[x for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()][-1]; m=email.message_from_string(raw)
chk("mail an kunde mit anhang",f"anna{sfx}@av.de" in str(m["To"]) and any(p.get_filename() for p in m.walk()),m["To"])
chk("mail ohne KI-Namen","claude" not in raw.lower())
chk("gesendet_am",a.get(f"/api/admin/kunden/{kid}/avv").json()["liste"][0]["gesendet_am"] is not None)
# Upload-Validierung
pdf=base64.b64encode(open("avv.pdf","rb").read()).decode()
chk("upload kein pdf",a.post(f"/api/admin/avv/{aid}/upload",json={"datei_base64":base64.b64encode(b"MZ exe").decode(),"unterschrieben_am":"2026-10-01"}).status_code==400)
chk("upload kein base64",a.post(f"/api/admin/avv/{aid}/upload",json={"datei_base64":"!!","unterschrieben_am":"2026-10-01"}).status_code==400)
chk("upload zukunft",a.post(f"/api/admin/avv/{aid}/upload",json={"datei_base64":pdf,"unterschrieben_am":"2030-01-01"}).status_code==400)
chk("upload unbekannte id",a.post("/api/admin/avv/00000000-0000-0000-0000-000000000000/upload",json={"datei_base64":pdf,"unterschrieben_am":"2026-10-01"}).status_code==404)
chk("noch nicht vorhanden",a.get(f"/api/admin/kunden/{kid}/avv").json()["vorhanden"] is False)
# Kunde vor Upload: sieht nichts
tok=None
for x in reversed([x for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]):
    mm=email.message_from_string(x)
    if f"anna{sfx}@av.de" in str(mm["To"]):
        for p in mm.walk():
            if p.get_content_type()=="text/plain":
                g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",p.get_payload(decode=True).decode())
                if g: tok=g.group(1); break
    if tok: break
httpx.post(B+"/api/einladung",headers=H,json={"token":tok,"password":"AvvKundePw123"}); c=httpx.Client(base_url=B,headers=H); c.post("/api/login",json={"email":f"anna{sfx}@av.de","password":"AvvKundePw123"})
chk("kunde sieht vor upload nichts",c.get("/api/kunde/avv").json()==[])
r=a.post(f"/api/admin/avv/{aid}/upload",json={"datei_base64":"data:application/pdf;base64,"+pdf,"datei_name":"AVV unterschrieben.pdf","unterschrieben_am":"2026-10-15"}); chk("upload",r.status_code==200,r.text)
chk("vorhanden",a.get(f"/api/admin/kunden/{kid}/avv").json()["vorhanden"] is True)
chk("nicht mehr auf fehlt-liste",not any(x["id"]==kid for x in a.get("/api/admin/avv-fehlt").json()))
chk("liste avv_ok true",a.get("/api/admin/kunden?q="+sfx).json()[0]["avv_ok"] is True)
o=a.get(f"/api/admin/kunden/{kid}/onboarding").json(); av=[p for p in o["punkte"] if p["code"]=="avv"][0]; chk("onboarding automatisch",av["fertig"] and av["automatisch"],av)
r=a.get(f"/api/admin/avv/{aid}/datei"); chk("admin download",r.status_code==200 and r.content[:4]==b"%PDF")
l=c.get("/api/kunde/avv").json(); chk("kunde sieht avv",len(l)==1 and l[0]["unterschrieben_am"]=="2026-10-15" and "datei" not in l[0],l)
r=c.get(f"/api/kunde/avv/{aid}/datei"); chk("kunde download",r.status_code==200 and r.content[:4]==b"%PDF" and r.headers["content-type"]=="application/pdf")
chk("kunde darf Admin-Endpunkt nicht",c.get(f"/api/admin/avv/{aid}/datei").status_code==403 and c.post(f"/api/admin/kunden/{kid}/avv").status_code==403)
chk("löschen mit Datei verboten",a.delete(f"/api/admin/avv/{aid}").status_code==400)
# fremder Kunde
k2=a.post("/api/admin/kunden",json={"firma":"AVV Fremd "+sfx,"email":f"f{sfx}@av.de","paket_code":"KI_ONE","einladen":True}).json()
tok2=None
for x in reversed([x for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]):
    mm=email.message_from_string(x)
    if f"f{sfx}@av.de" in str(mm["To"]):
        for p in mm.walk():
            if p.get_content_type()=="text/plain":
                g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",p.get_payload(decode=True).decode())
                if g: tok2=g.group(1); break
    if tok2: break
httpx.post(B+"/api/einladung",headers=H,json={"token":tok2,"password":"FremdAvvPw1234"}); f=httpx.Client(base_url=B,headers=H); f.post("/api/login",json={"email":f"f{sfx}@av.de","password":"FremdAvvPw1234"})
chk("fremder sieht kein AVV",f.get("/api/kunde/avv").json()==[] and f.get(f"/api/kunde/avv/{aid}/datei").status_code==404)
# Entwurf löschen
r2=a.post(f"/api/admin/kunden/{k2['id']}/avv").json(); chk("entwurf löschen",a.delete(f"/api/admin/avv/{r2['id']}").status_code==200)
chk("ungültige id",a.get("/api/admin/avv/nix/vorlage.pdf").status_code==404 and a.get("/api/admin/kunden/nix/avv").status_code==404)
# Einstellungen Unterauftragsverarbeiter
chk("einst lesen",a.get("/api/admin/einstellungen/avv").json()["standard"].startswith("Hetzner"))
a.put("/api/admin/einstellungen/avv",json={"unterauftragnehmer":"Hetzner Online GmbH | Hosting | Deutschland\nMailbox.org | E-Mail | Deutschland"})
r=a.get(f"/api/admin/avv/{aid}/vorlage.pdf"); open("avv2.pdf","wb").write(r.content)
txt=subprocess.run(["pdftotext","avv2.pdf","-"],capture_output=True,text=True).stdout
chk("eigene Unterauftragnehmer im PDF","Mailbox.org" in txt and "AVV Test" in txt and "29221 Celle" in txt,txt[:300])
a.put("/api/admin/einstellungen/avv",json={"unterauftragnehmer":""})
# Erinnerungs-Job
sql(f"update kunden set erstellt_am=now()-interval '5 days', avv_erinnert_am=null where id='{k2['id']}'")
import sys,os
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import jobs, db
db.open_pool()
n0=open("/var/tmp/pt/mails.txt").read().count("=====")
jobs.avv_erinnerung({"alarm_email":""}); time.sleep(1)
raw=open("/var/tmp/pt/mails.txt").read(); n1=raw.count("=====")
chk("erinnerung gesendet",n1==n0+1 and "AVV fehlt" in raw and f"AVV Fremd {sfx}" in raw.split("\n=====\n")[-1] or "Fremd" in raw[-1500:])
chk("kunde mit avv nicht in erinnerung",f"AVV Test {sfx}" not in raw[-1500:])
jobs.avv_erinnerung({"alarm_email":""}); time.sleep(1)
chk("nicht doppelt innerhalb 7 Tage",open("/var/tmp/pt/mails.txt").read().count("=====")==n1)
