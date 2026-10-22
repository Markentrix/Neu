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
sfx=str(int(time.time())+193)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, os, subprocess, sys, glob
sys.path.insert(0,"/home/claude/markentrix-server/portal")
S="/var/tmp/pt/s"
kA,cA,mA=neuer_kunde("Ag"); kB,cB,mB=neuer_kunde("Agb")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs
db.open_pool()
def werktage(n):
    d=datetime.date.today()
    while n>0:
        d+=datetime.timedelta(days=1)
        if d.weekday()<5: n-=1
    return d.isoformat()
# ---- (3) Frist für Änderungswünsche
r=cA.post("/api/kunde/tickets",json={"betreff":"Öffnungszeiten ändern","art":"aenderung","text":"Samstag bis 14 Uhr"}); chk("Änderungswunsch angelegt",r.status_code==200,r.text); tid=r.json()["id"]
l={x["id"]:x for x in cA.get("/api/kunde/tickets").json()}
chk("Frist = 3 Werktage",str(l[tid]["frist"])==werktage(3),l[tid])
chk("Detail zeigt Frist",str(cA.get(f"/api/kunde/tickets/{tid}").json()["frist"])==werktage(3))
r=cA.post("/api/kunde/tickets",json={"betreff":"Seite lädt nicht","art":"problem","text":"Fehler"}); tp=r.json()["id"]
chk("Problem: 2 Werktage",str({x["id"]:x for x in cA.get("/api/kunde/tickets").json()}[tp]["frist"])==werktage(2))
r=cA.post("/api/kunde/tickets",json={"betreff":"Frage zur Rechnung","art":"frage","text":"?"}); tf=r.json()["id"]
chk("Frage: keine Frist",{x["id"]:x for x in cA.get("/api/kunde/tickets").json()}[tf]["frist"] is None)
chk("Kunde B sieht die Tickets von A nicht",cB.get("/api/kunde/tickets").json()==[])
sql(f"update kunden set status='aktiv', erstellt_am=now()-interval '40 days' where id='{kA}'")
from app.routes_fruehwarnung import risiko_fuer
from app.db import tx
def fw():
    with tx("admin") as cur: return {kA: risiko_fuer(cur,kA)}
chk("Pünktlich: keine Warnung wegen Frist",not any("Frist" in g for g in fw().get(kA,{}).get("gruende",[])))
sql(f"update tickets set faellig_am=current_date-1 where id='{tid}'")
chk("Überfällig: Frühwarnung nennt es",any("über der Frist" in g for g in fw().get(kA,{}).get("gruende",[])),fw().get(kA))
r=a.patch(f"/api/admin/tickets/{tid}",json={"status":"erledigt"}); chk("Admin erledigt den Wunsch",r.status_code==200,r.text)
l={x["id"]:x for x in cA.get("/api/kunde/tickets").json()}
chk("Erledigt: keine Frist mehr, Datum sichtbar",l[tid]["frist"] is None and l[tid]["erledigt_am"] is not None,l[tid])
chk("Erledigt zählt nicht mehr als überfällig",not any("über der Frist" in g for g in fw().get(kA,{}).get("gruende",[])))
# ---- (1) Bericht: Was wir erledigt haben
vm=(datetime.date.today().replace(day=1)-datetime.timedelta(days=1)).replace(day=1); tag=vm+datetime.timedelta(days=2)
sql(f"update tickets set erledigt_am='{tag} 10:00+00' where id='{tid}'")
sql(f"insert into audit_log (kunden_id, aktion, details, zeit) values ('{kA}','website_hochgeladen','{{}}','{tag} 11:00+00')")
r=a.post(f"/api/admin/kunden/{kA}/bericht",json={"monat":vm.strftime("%Y-%m"),"senden":False}); chk("Bericht erstellt",r.status_code==200,r.text)
bl=a.get(f"/api/admin/kunden/{kA}/berichte").json(); bid=bl[0]["id"]
pdf=a.get(f"/api/admin/berichte/{bid}/pdf"); open("/var/tmp/pt/b67.pdf","wb").write(pdf.content)
txt=subprocess.run(["pdftotext","/var/tmp/pt/b67.pdf","-"],capture_output=True,text=True).stdout
chk("PDF: Abschnitt „Was wir für Sie erledigt haben“",("erledigt haben" in txt) and "Öffnungszeiten ändern" in txt and "aktualisiert" in txt,txt[:400])
chk("PDF: Änderung als solche gekennzeichnet","Änderung:" in txt)
b2=a.post(f"/api/admin/kunden/{kB}/bericht",json={"monat":vm.strftime("%Y-%m"),"senden":False}); bidB=a.get(f"/api/admin/kunden/{kB}/berichte").json()[0]["id"]
txtB=subprocess.run(["pdftotext","-","-"],input=a.get(f"/api/admin/berichte/{bidB}/pdf").content,capture_output=True).stdout.decode()
chk("Anderer Kunde: Abschnitt fehlt, wenn nichts erledigt",("erledigt haben" not in txtB) and "Öffnungszeiten" not in txtB)
# ---- (2) Livecheck
dn=f"lc{sfx}"; D=f"{S}/demos/{dn}"; os.makedirs(D,exist_ok=True)
open(D+"/index.html","w").write('<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Test</title><meta name="description" content="x"><meta name="viewport" content="width=device-width"></head><body><p>Hallo</p><img src="a.png"><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></body></html>')
open(D+"/a.png","wb").write(b"x"); open(D+"/impressum.html","w").write("<title>I</title>"); open(D+"/datenschutz.html","w").write("<title>D</title>")
c=a.get(f"/api/admin/websites/livecheck?art=demo&name={dn}").json(); t=" | ".join(x["text"] for x in c["punkte"])
chk("Livecheck: Bild ohne alt",("alt-Text" in t),t); chk("Livecheck: keine Hauptüberschrift","Hauptüberschrift" in t); chk("Livecheck: kein Favicon","Favicon" in t); chk("Livecheck: kein Telefon-/Mail-Link","Telefon- oder E-Mail-Link" in t)
chk("Neue Hinweise machen die Ampel nicht rot",c["ampel"]!="rot",c["ampel"])
open(D+"/index.html","w").write('<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Test</title><meta name="description" content="x"><meta name="viewport" content="width=device-width"><link rel="icon" href="a.png"></head><body><h1>Hallo</h1><img src="a.png" alt="Bild"><a href="tel:+49511123">Anrufen</a><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></body></html>')
c=a.get(f"/api/admin/websites/livecheck?art=demo&name={dn}").json(); t=" | ".join(x["text"] for x in c["punkte"])
chk("Livecheck: saubere Seite ohne die neuen Hinweise",not any(w in t for w in ("alt-Text","Hauptüberschrift","Favicon","Telefon- oder")) and c["ampel"]=="gruen",t)
# ---- (7) Vertrag automatisch erkannt
def ob(): return {p["code"]:p for p in a.get(f"/api/admin/kunden/{kA}/onboarding").json()["punkte"]}
chk("Vertrag zunächst offen",not ob()["vertrag"]["fertig"])
sql(f"INSERT INTO belege (art, kunden_id, status, nummer) VALUES ('angebot','{kA}','versendet','A-T{sfx}')")
chk("Versendetes Angebot reicht nicht",not ob()["vertrag"]["fertig"])
sql(f"update belege set status='angenommen' where nummer='A-T{sfx}'")
chk("Angenommenes Angebot: Vertrag automatisch erkannt",ob()["vertrag"]["fertig"] and ob()["vertrag"]["automatisch"])
# AVV-Erinnerung an den Kunden
sql(f"INSERT INTO avv (kunden_id, version, portal_freigabe_am) VALUES ('{kA}','2',now()-interval '1 day')")
open("/var/tmp/pt/mails.txt","a").close(); n0=len(mail_an(f"ag{sfx}@k.de","AVV"))
jobs.avv_kunde_erinnern(); chk("Nach 1 Tag noch keine Erinnerung",sql(f"select erinnerungen from avv where kunden_id='{kA}'")=="0")
sql(f"update avv set portal_freigabe_am=now()-interval '4 days' where kunden_id='{kA}'")
jobs.avv_kunde_erinnern(); time.sleep(1.2)
chk("Nach 4 Tagen: Erinnerung per Mail an den Kunden",len(mail_an(f"ag{sfx}@k.de","AVV"))==n0+1 and sql(f"select erinnerungen from avv where kunden_id='{kA}'")=="1")
jobs.avv_kunde_erinnern(); chk("Nicht gleich nochmal",sql(f"select erinnerungen from avv where kunden_id='{kA}'")=="1")
sql(f"update avv set erinnert_am=now()-interval '4 days' where kunden_id='{kA}'"); jobs.avv_kunde_erinnern(); time.sleep(1.2)
chk("Zweite Erinnerung",sql(f"select erinnerungen from avv where kunden_id='{kA}'")=="2")
sql(f"update avv set erinnert_am=now()-interval '4 days' where kunden_id='{kA}'"); jobs.avv_kunde_erinnern()
chk("Nie mehr als zwei",sql(f"select erinnerungen from avv where kunden_id='{kA}'")=="2")
sql(f"update avv set datei_name='x' where kunden_id='{kA}'")
# ---- (9) Startpaket
chk("Kunde darf kein Startpaket auslösen",cA.post(f"/api/admin/kunden/{kA}/startpaket").status_code==403)
chk("Unbekannter Kunde: 404",a.post("/api/admin/kunden/00000000-0000-0000-0000-000000000000/startpaket").status_code==404)
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) values ('{kB}','website',true) on conflict do nothing"); sql(f"update kunden_module set aktiv=true where kunden_id='{kB}' and modul_code='website'")
m0=len(mail_an(f"agb{sfx}@k.de","Willkommen"))
r=a.post(f"/api/admin/kunden/{kB}/startpaket"); chk("Startpaket läuft",r.status_code==200 and r.json()["aufgaben"]==5 and r.json()["mail"],r.text)
time.sleep(1.2); mm=mail_an(f"agb{sfx}@k.de","Willkommen"); chk("Willkommensmail mit Wünschen",len(mm)==m0+1 and "Logo" in text(mm[-1]) and "Domain" in text(mm[-1]) and "Claude" not in text(mm[-1]),mm and text(mm[-1]))
tt=a.get("/api/admin/aufgaben?status=offen").json(); mine=[x for x in tt if x["kunden_id"]==kB]
chk("5 Aufgaben mit Fristen angelegt",len(mine)==5 and all(x["faellig_am"] for x in mine),mine)
chk("AVV-Aufgabe dabei",any("AVV" in x["titel"] for x in mine))
r=a.post(f"/api/admin/kunden/{kB}/startpaket"); chk("Zweiter Klick: nichts doppelt, keine zweite Mail",r.json()["aufgaben"]==0 and not r.json()["mail"],r.text)
time.sleep(1.2); chk("Nur eine Willkommensmail",len(mail_an(f"agb{sfx}@k.de","Willkommen"))==m0+1)
chk("Checkliste vorhanden",len(a.get(f"/api/admin/kunden/{kB}/onboarding").json()["punkte"])>=8)
sql(f"update kunden_module set aktiv=false where kunden_id='{kA}' and modul_code='website'")
r=a.post(f"/api/admin/kunden/{kA}/startpaket"); chk("Ohne Website-Modul: keine Domain-Aufgabe",r.json()["aufgaben"]==4,r.text)
print("FERTIG")
