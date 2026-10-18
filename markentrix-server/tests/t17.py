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
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
kid,c,kmail=neuer_kunde("Alpha"); kid2,c2,kmail2=neuer_kunde("Beta")

# ---- Tickets
r=c.post("/api/kunde/tickets",json={"betreff":"Öffnungszeiten ändern","art":"aenderung","text":"Bitte ab Montag 8 Uhr."}); chk("ticket neu",r.status_code==200 and r.json()["nr"].startswith("T-"),r.text); tid=r.json()["id"]
chk("Mail ans Team",len(mail_an("info@markentrix.de","Öffnungszeiten"))>=1 or len(mail_an("chef@test.de","Öffnungszeiten"))>=1 or len([m for m in mails() if "Öffnungszeiten" in text(m)])>=1)
chk("ungültige Art",c.post("/api/kunde/tickets",json={"betreff":"x","art":"quatsch","text":"y"}).status_code==422)
chk("Kunde sieht eigene Liste",[t["id"] for t in c.get("/api/kunde/tickets").json()]==[tid])
chk("Fremder Kunde sieht nichts",c2.get("/api/kunde/tickets").json()==[])
chk("Fremder Kunde: Detail 404",c2.get(f"/api/kunde/tickets/{tid}").status_code==404)
chk("Fremder Kunde: Antwort 404",c2.post(f"/api/kunde/tickets/{tid}/nachricht",json={"text":"hi"}).status_code==404)
chk("ungültige ID 404",c.get("/api/kunde/tickets/nix").status_code==404)
al=a.get("/api/admin/tickets").json(); chk("Admin sieht Ticket",any(t["id"]==tid and t["team_ungelesen"] for t in al),al)
d=a.get(f"/api/admin/tickets/{tid}").json(); chk("Admin-Detail",d["nr"].startswith("T-") and len(d["nachrichten"])==1 and d["firma"].startswith("Alpha"),d)
chk("danach gelesen",sql(f"select team_ungelesen from tickets where id='{tid}'")=="f")
# interne Notiz
chk("interne Notiz",a.post(f"/api/admin/tickets/{tid}/nachricht",json={"text":"GEHEIM intern","intern":True}).status_code==200)
chk("Kunde sieht Notiz nicht","GEHEIM" not in str(c.get(f"/api/kunde/tickets/{tid}").json()))
n0=len(mails()); time.sleep(1)
# Antwort
r=a.post(f"/api/admin/tickets/{tid}/nachricht",json={"text":"Erledigt, ab Montag gilt 8 Uhr."}); chk("Antwort",r.status_code==200,r.text)
ma=mail_an(kmail,"Öffnungszeiten"); chk("Mail an Kunde",len(ma)==1,len(ma)); chk("Mail ohne KI-Namen","Claude" not in text(ma[0]) and "Markentrix-Team" in text(ma[0]))
chk("keine Mail bei interner Notiz",len([m for m in mails() if "GEHEIM" in (text(m) or "")])==0)
d=c.get(f"/api/kunde/tickets/{tid}").json(); chk("Kunde sieht Antwort",len(d["nachrichten"])==2 and d["nachrichten"][1]["von"]=="team",d)
chk("Status in_arbeit",d["status"]=="in_arbeit")
chk("erste Antwort gesetzt",sql(f"select erste_antwort_am is not null from tickets where id='{tid}'")=="t")
# Kunde antwortet, Anhang
r=c.post(f"/api/kunde/tickets/{tid}/nachricht",json={"text":"Danke!"}); chk("Kunde antwortet",r.status_code==200)
pdf=b"%PDF-1.4 test"
r=c.post(f"/api/kunde/tickets/{tid}/dateien",files={"datei":("plan.pdf",pdf,"application/pdf")}); chk("Anhang Kunde",r.status_code==200,r.text); fid=r.json()["id"]
chk("Anhang falscher Inhalt",c.post(f"/api/kunde/tickets/{tid}/dateien",files={"datei":("x.pdf",b"kein pdf","application/pdf")}).status_code==400)
chk("Anhang .exe verboten",c.post(f"/api/kunde/tickets/{tid}/dateien",files={"datei":("x.exe",b"MZ","application/octet-stream")}).status_code==400)
chk("Anhang zu groß",c.post(f"/api/kunde/tickets/{tid}/dateien",files={"datei":("g.pdf",b"%PDF"+b"0"*(9*1024*1024),"application/pdf")}).status_code==413)
r=c.get(f"/api/kunde/dateien/{fid}"); chk("Download Kunde",r.status_code==200 and r.content==pdf and "attachment" in r.headers["content-disposition"],r.headers)
chk("Fremder Download 404",c2.get(f"/api/kunde/dateien/{fid}").status_code==404)
chk("Admin Download",a.get(f"/api/admin/dateien/{fid}").content==pdf)
chk("Team-Anhang",a.post(f"/api/admin/tickets/{tid}/dateien",files={"datei":("antwort.png",b"\x89PNG\r\n\x1a\n0000","image/png")}).status_code==200)
# Erledigen + Bewerten
chk("Bewerten vor erledigt verboten",c.post(f"/api/kunde/tickets/{tid}/zufriedenheit",json={"punkte":9}).status_code==400)
chk("erledigen",a.patch(f"/api/admin/tickets/{tid}",json={"status":"erledigt","zustaendig":"chef@test.de","prioritaet":"hoch"}).status_code==200)
chk("erledigt_am",sql(f"select erledigt_am is not null from tickets where id='{tid}'")=="t")
chk("Bewertung 11 ungültig",c.post(f"/api/kunde/tickets/{tid}/zufriedenheit",json={"punkte":11}).status_code==422)
chk("Bewertung",c.post(f"/api/kunde/tickets/{tid}/zufriedenheit",json={"punkte":10,"kommentar":"Super schnell"}).status_code==200)
chk("Doppelt bewerten verboten",c.post(f"/api/kunde/tickets/{tid}/zufriedenheit",json={"punkte":3}).status_code==400)
chk("Fremder bewertet nicht",c2.post(f"/api/kunde/tickets/{tid}/zufriedenheit",json={"punkte":1}).status_code==404)
chk("Antwort öffnet wieder",c.post(f"/api/kunde/tickets/{tid}/nachricht",json={"text":"Noch eine Frage"}).status_code==200 and c.get(f"/api/kunde/tickets/{tid}").json()["status"]=="offen")
chk("Filter offene",any(t["id"]==tid for t in a.get("/api/admin/tickets?status=offene").json()))
chk("Filter Status ungültig",a.get("/api/admin/tickets?status=x").status_code==400)
r=a.post(f"/api/admin/kunden/{kid}/tickets",json={"betreff":"Bitte Logo schicken","art":"auftrag","text":"Wir brauchen euer Logo."}); chk("Team eröffnet Ticket",r.status_code==200,r.text)
chk("Team-Ticket wartet auf Kunde",sql(f"select status from tickets where id='{r.json()['id']}'")=="wartet_auf_kunde")
chk("Mail dazu",len(mail_an(kmail,"Logo"))>=1)
# nur_lesen
tm=c.post("/api/kunde/team/einladen",json={"email":f"lese{sfx}@k.de","name":"Lese","kunden_rolle":"nur_lesen"}); chk("Team einladen",tm.status_code==200,tm.text)
time.sleep(1); httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"lese{sfx}@k.de"),"password":"LesePasswort123"})
cl=httpx.Client(base_url=B,headers=H); cl.post("/api/login",json={"email":f"lese{sfx}@k.de","password":"LesePasswort123"})
chk("nur_lesen sieht Tickets",len(cl.get("/api/kunde/tickets").json())>=1)
chk("nur_lesen schreibt nicht",cl.post("/api/kunde/tickets",json={"betreff":"x","art":"frage","text":"y"}).status_code==403)

# ---- Unterlagen
r=c.post("/api/kunde/unterlagen",files={"datei":("briefing.pdf",pdf,"application/pdf")},data={"kategorie":"briefing"}); chk("Unterlage Kunde",r.status_code==200,r.text); uid=r.json()["id"]
chk("Kategorie ungültig",c.post("/api/kunde/unterlagen",files={"datei":("b.pdf",pdf,"application/pdf")},data={"kategorie":"hack"}).status_code==400)
r=a.post(f"/api/admin/kunden/{kid}/unterlagen",files={"datei":("vertrag.pdf",pdf,"application/pdf")},data={"kategorie":"vertrag","sichtbar_kunde":"true"}); chk("Unterlage Team sichtbar",r.status_code==200,r.text)
r=a.post(f"/api/admin/kunden/{kid}/unterlagen",files={"datei":("intern.pdf",pdf,"application/pdf")},data={"kategorie":"sonstiges","sichtbar_kunde":"false"}); chk("Unterlage Team intern",r.status_code==200); intern=r.json()["id"]
ku=c.get("/api/kunde/unterlagen").json()["dateien"]; chk("Kunde sieht 2, nicht die interne",len(ku)==2 and all(x["id"]!=intern for x in ku),ku)
chk("interne Datei nicht ladbar",c.get(f"/api/kunde/dateien/{intern}").status_code==404)
chk("Admin sieht 3",len(a.get(f"/api/admin/kunden/{kid}/unterlagen").json()["dateien"])==3)
chk("Beta sieht keine",c2.get("/api/kunde/unterlagen").json()["dateien"]==[])
chk("Kunde löscht eigene",c.delete(f"/api/kunde/unterlagen/{uid}").status_code==200)
vid=[x["id"] for x in c.get("/api/kunde/unterlagen").json()["dateien"]][0]
chk("Kunde löscht Team-Datei nicht",c.delete(f"/api/kunde/unterlagen/{vid}").status_code==404)
chk("nur_lesen lädt nicht hoch",cl.post("/api/kunde/unterlagen",files={"datei":("b.pdf",pdf,"application/pdf")},data={"kategorie":"briefing"}).status_code==403)
chk("Admin löscht",a.delete(f"/api/admin/unterlagen/{intern}").status_code==200)

# ---- Freigaben
r=a.post(f"/api/admin/kunden/{kid}/freigaben-kunden",json={"titel":"Instagram-Beitrag Oktober","art":"social","inhalt":"Herbstangebot ab Montag!"}); chk("Freigabe anfragen",r.status_code==200,r.text); frid=r.json()["id"]
chk("Datei zur Freigabe",a.post(f"/api/admin/freigaben-kunden/{frid}/dateien",files={"datei":("post.png",b"\x89PNG\r\n\x1a\n0000","image/png")}).status_code==200)
chk("Mail Freigabe",len(mail_an(kmail,"Freigabe"))>=1)
fl=c.get("/api/kunde/freigaben").json(); chk("Kunde sieht Freigabe",len(fl)==1 and fl[0]["status"]=="wartet" and len(fl[0]["dateien"])==1,fl)
chk("Fremder sieht keine",c2.get("/api/kunde/freigaben").json()==[])
chk("Fremder entscheidet nicht",c2.post(f"/api/kunde/freigaben/{frid}/entscheiden",json={"entscheidung":"freigegeben"}).status_code==404)
chk("nur_lesen entscheidet nicht",cl.post(f"/api/kunde/freigaben/{frid}/entscheiden",json={"entscheidung":"freigegeben"}).status_code==403)
chk("Ablehnen braucht Kommentar",c.post(f"/api/kunde/freigaben/{frid}/entscheiden",json={"entscheidung":"abgelehnt"}).status_code==400)
chk("ungültige Entscheidung",c.post(f"/api/kunde/freigaben/{frid}/entscheiden",json={"entscheidung":"vielleicht"}).status_code==422)
chk("Freigeben",c.post(f"/api/kunde/freigaben/{frid}/entscheiden",json={"entscheidung":"freigegeben","kommentar":"Top"}).status_code==200)
chk("Zweite Entscheidung verboten",c.post(f"/api/kunde/freigaben/{frid}/entscheiden",json={"entscheidung":"abgelehnt","kommentar":"doch nicht"}).status_code==400)
fa=[f for f in a.get("/api/admin/freigaben-kunden").json() if f["id"]==frid][0]
chk("Admin sieht Entscheidung mit Zeitstempel",fa["status"]=="freigegeben" and fa["entschieden_am"] and fa["entschieden_name"] and fa["entschieden_ip"],fa)
time.sleep(2); chk("Mail ans Team",len([m for m in mails() if "freigegeben" in (str(email.header.make_header(email.header.decode_header(m["Subject"] or "")))+(text(m) or "")).lower()])>=1)
r=a.post(f"/api/admin/kunden/{kid}/freigaben-kunden",json={"titel":"Flyer","art":"design"}); f2=r.json()["id"]
chk("zurückziehen",a.post(f"/api/admin/freigaben-kunden/{f2}/zurueckziehen").status_code==200)
chk("zurückgezogen nicht mehr entscheidbar",c.post(f"/api/kunde/freigaben/{f2}/entscheiden",json={"entscheidung":"freigegeben"}).status_code==400)
chk("Filter wartet",all(f["status"]=="wartet" for f in a.get("/api/admin/freigaben-kunden?status=wartet").json()))

# ---- Aufgaben
r=a.post("/api/admin/aufgaben",json={"titel":"Logo besorgen","kunden_id":kid,"faellig_am":"2020-01-01"}); chk("Aufgabe neu",r.status_code==200,r.text); aid=r.json()["id"]
l=a.get("/api/admin/aufgaben").json(); chk("Aufgabe überfällig",any(x["id"]==aid and x["ueberfaellig"] and x["firma"].startswith("Alpha") for x in l),l)
chk("Aufgabe erledigt",a.patch(f"/api/admin/aufgaben/{aid}",json={"status":"erledigt"}).status_code==200 and sql(f"select erledigt_von from aufgaben where id='{aid}'")=="chef@test.de")
chk("nicht mehr offen",all(x["id"]!=aid for x in a.get("/api/admin/aufgaben").json()))
chk("Aufgabe löschen",a.delete(f"/api/admin/aufgaben/{aid}").status_code==200)
chk("Aufgabe ungültige Kunden-ID",a.post("/api/admin/aufgaben",json={"titel":"x","kunden_id":"nix"}).status_code==400)
chk("Kunde hat keinen Zugriff auf Aufgaben",c.get("/api/admin/aufgaben").status_code==403)
# automatische Aufgaben
sql(f"update tickets set geaendert_am=now()-interval '2 days' where id='{tid}' and status='offen'")
import sys; sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs
db.open_pool(); n0=len(mails())
for x in a.get("/api/admin/aufgaben?status=alle").json():
    if x["quelle"]=="auto": a.patch(f"/api/admin/aufgaben/{x['id']}",json={"status":"erledigt"})
jobs.aufgaben_automatisch({"alarm_email":""}); jobs.aufgaben_automatisch({"alarm_email":""})
auto=[x for x in a.get("/api/admin/aufgaben?status=alle").json() if x["kunden_id"]==kid]
chk("Auto-Aufgabe Antworten",len([x for x in auto if x["quelle"]=="auto" and x["titel"].startswith("Antworten")])==1,[x["titel"] for x in auto])
chk("nur einmal (Dedupe)",len([x for x in auto if x["titel"].startswith("Antworten")])==1)
chk("Sammelmail an Admin",len([m for m in mails()[n0:] if "Aufgabe" in str(m["Subject"])])>=1)
sql(f"update kundenfreigaben set angefragt_am=now()-interval '5 days' where id='{f2}'"); sql(f"update kundenfreigaben set status='wartet' where id='{f2}'")
n1=len(mails()); jobs.aufgaben_automatisch({"alarm_email":""}); jobs.aufgaben_automatisch({"alarm_email":""})
chk("Freigabe-Erinnerung einmal",len([m for m in mails()[n1:] if "Erinnerung" in str(m["Subject"]) and kmail in str(m["To"])])==1)

# ---- Kennzahlen, Stammdaten, Module
z=a.get("/api/admin/kennzahlen").json(); chk("Kennzahlen",z["tickets_offen"]>=1 and z["bewertungen"]>=1 and z["nps"] is not None and z["antwortzeit_h"] is not None and len(z["kunden"])>=2,z)
u=a.get("/api/admin/uebersicht").json(); chk("Übersicht enthält Zusammenarbeit","zusammenarbeit" in u and u["zusammenarbeit"]["tickets_offen"]>=1)
kk=c.get("/api/kunde/kennzahlen").json(); chk("Kunden-Kennzahlen",kk["freigaben_wartend"]==1 and "bewertung_faellig" in kk and kk["antwortzeit_h"] is not None,kk)
chk("Quartalsbewertung",c.post("/api/kunde/zufriedenheit",json={"punkte":8,"kommentar":"gut"}).status_code==200)
r=c.patch("/api/kunde/stammdaten",json={"strasse":"Neue Str. 5","ort":"Hannover"}); chk("Stammdaten ändern",r.status_code==200,r.text)
chk("Stammdaten gespeichert",sql(f"select strasse||'|'||ort||'|'||plz from kunden where id='{kid}'")=="Neue Str. 5|Hannover|29221")
chk("Mail Stammdaten",len([m for m in mails() if "Stammdaten" in str(m["Subject"])])>=1 or len(mail_an("info@markentrix.de","Stammdaten"))>=1)
chk("Stammdaten leer 400",c.patch("/api/kunde/stammdaten",json={}).status_code==400)
chk("nur_lesen: Stammdaten verboten",cl.patch("/api/kunde/stammdaten",json={"ort":"X"}).status_code==403)
mod=sql("select code from module where art='agent' order by sortierung limit 1")
r=c.post("/api/kunde/modul-anfrage",json={"modul_code":mod}); chk("Modul anfragen",r.status_code==200,r.text)
chk("Modul doppelt verboten",c.post("/api/kunde/modul-anfrage",json={"modul_code":mod}).status_code==400)
chk("Modul unbekannt 404",c.post("/api/kunde/modul-anfrage",json={"modul_code":"gibtsnicht"}).status_code==404)
chk("Modul-Ticket sichtbar",any(t["art"]=="modul" for t in c.get("/api/kunde/tickets").json()))
chk("Profil enthält Anschrift+Schalter",{"strasse","benachr_nachrichten"}<=set(c.get("/api/kunde/profil").json()["kunde"]))
chk("Benachrichtigung abschalten",c.patch("/api/kunde/profil",json={"benachr_nachrichten":False}).status_code==200)
n2=len(mails()); a.post(f"/api/admin/tickets/{tid}/nachricht",json={"text":"Hallo nochmal"}); time.sleep(1.5)
chk("keine Mail wenn abgeschaltet",len([m for m in mails()[n2:] if kmail in str(m["To"])])==0)
# Offboarding berücksichtigt neue Daten
chk("Beta: Ticket",c2.post("/api/kunde/tickets",json={"betreff":"Abschied","art":"frage","text":"tschüss"}).status_code==200)
chk("Beta: Unterlage",c2.post("/api/kunde/unterlagen",files={"datei":("a.pdf",pdf,"application/pdf")},data={"kategorie":"sonstiges"}).status_code==200)
a.post(f"/api/admin/kunden/{kid2}/status",json={"status":"gekuendigt"})
import zipfile
zz=zipfile.ZipFile(io.BytesIO(a.get(f"/api/admin/kunden/{kid2}/export.zip").content)); nm=zz.namelist()
chk("Export: Tickets",any(n.endswith("tickets.json") for n in nm) and "Abschied" in zz.read("daten/tickets.json").decode())
chk("Export: Dateien",any(n.startswith("dateien/dokument/") for n in nm),nm)
r=a.post(f"/api/admin/kunden/{kid2}/loeschen",json={"bestaetigung":sql(f"select kundennummer from kunden where id='{kid2}'"),"export_uebergeben":True}); chk("Löschen",r.status_code==200,r.text)
for t in ["tickets","ticket_nachrichten","dateien","kundenfreigaben","zufriedenheit"]: chk(f"{t} leer",sql(f"select count(*) from {t} where kunden_id='{kid2}'")=="0")

db.close_pool()
