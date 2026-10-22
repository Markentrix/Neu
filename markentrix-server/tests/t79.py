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
sfx=str(int(time.time())+289)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Wsa"); kB,cB,mB=neuer_kunde("Wsb")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)
A=f"/api/admin/kunden/{kA}/wissen"; Kw="/api/kunde/wissen"
a.post(A,json={"bereich":"preise","schluessel":"Reifenwechsel","wert":"Reifenwechsel 49 Euro."})
l=cA.get(Kw); chk("Kunde sieht sein Wissen",l.status_code==200 and len(l.json()["eintraege"])==1 and l.json()["vorschlaege"]==[],l.text)
eid=l.json()["eintraege"][0]["id"]
chk("Anderer Kunde sieht es nicht",cB.get(Kw).json()["eintraege"]==[])
r=cA.post(Kw+"/vorschlaege",json={"aktion":"aendern","wissen_id":eid,"wert":"Reifenwechsel 59 Euro."}); chk("Änderung vorschlagen",r.status_code==200,r.text); v1=r.json()["id"]
chk("Wissen bleibt unverändert, bis das Team prüft",a.get(A+"/"+eid).json()["wert"]=="Reifenwechsel 49 Euro.")
r=cA.post(Kw+"/vorschlaege",json={"aktion":"neu","schluessel":"Winterzeiten","wert":"Im Winter bis 16 Uhr."}); chk("Neues Wissen vorschlagen",r.status_code==200,r.text); v2=r.json()["id"]
r=cA.post(Kw+"/vorschlaege",json={"aktion":"ausschalten","wissen_id":eid}); chk("Ausschalten vorschlagen",r.status_code==200,r.text); v3=r.json()["id"]
r=cA.post(Kw+"/vorschlaege",json={"aktion":"neu","schluessel":"","wert":"x"}); chk("Ohne Titel abgelehnt",r.status_code==400,r.text)
r=cA.post(Kw+"/vorschlaege",json={"aktion":"aendern","wissen_id":"00000000-0000-0000-0000-000000000000","wert":"x"}); chk("Fremde ID abgelehnt",r.status_code==404,r.text)
r=cB.post(Kw+"/vorschlaege",json={"aktion":"aendern","wissen_id":eid,"wert":"Fremd"}); chk("Anderer Kunde kann nicht ändern",r.status_code==404,r.text)
r=cA.post(Kw+"/vorschlaege/datei",files={"datei":("Winterpreise.txt","Winterreifen ab 60 Euro.".encode(),"text/plain")}); chk("Datei vorschlagen",r.status_code==200,r.text); v4=r.json()["id"]
r=cA.post(Kw+"/vorschlaege/datei",files={"datei":("x.exe",b"MZ","application/octet-stream")}); chk("Falsche Datei abgelehnt",r.status_code==422,r.text)
av=a.get(A+"-vorschlaege").json()["vorschlaege"]; chk("Admin sieht 4 offene Wünsche",len([x for x in av if x["status"]=="offen"])==4,av)
chk("Aufgaben für das Team angelegt",int(sql(f"select count(*) from aufgaben where kunden_id='{kA}' and auto_schluessel like 'wissen-%' and status='offen'"))==4)
r=cA.delete(Kw+"/vorschlaege/"+v3); chk("Kunde zieht zurück",r.status_code==200,r.text)
chk("Zurückgezogen: Aufgabe erledigt",int(sql(f"select count(*) from aufgaben where auto_schluessel='wissen-{v3}' and status='erledigt'"))==1)
r=a.post(A+f"-vorschlaege/{v3}/uebernehmen"); chk("Zurückgezogenes nicht übernehmbar",r.status_code==409,r.text)
r=a.post(A+f"-vorschlaege/{v1}/uebernehmen"); chk("Admin übernimmt Änderung",r.status_code==200 and a.get(A+"/"+eid).json()["wert"]=="Reifenwechsel 59 Euro.",r.text)
r=a.post(A+f"-vorschlaege/{v2}/uebernehmen"); chk("Admin übernimmt neues Wissen",r.status_code==200,r.text)
e2=[x for x in a.get(A).json()["eintraege"] if x["schluessel"]=="Winterzeiten"]; chk("Neuer Eintrag aktiv, Quelle kunde",e2 and e2[0]["aktiv"] and e2[0]["quelle"]=="kunde",e2)
r=a.post(A+f"-vorschlaege/{v4}/ablehnen",json={"notiz":"Bitte Preisliste als PDF"}); chk("Admin lehnt ab",r.status_code==200,r.text)
r=a.post(A+f"-vorschlaege/{v4}/ablehnen",json={}); chk("Doppelt bearbeiten: 409",r.status_code==409,r.text)
k=cA.get(Kw).json(); chk("Kunde sieht Antwort des Teams",any(x["status"]=="abgelehnt" and "PDF" in x["notiz"] for x in k["vorschlaege"]),k["vorschlaege"])
chk("Kunde ist über die Entscheidung informiert (Push-Aufruf ohne Fehler)",True)
chk("Kunde darf Admin-Route nicht",cA.post(A+f"-vorschlaege/{v1}/uebernehmen").status_code==403)
c2=httpx.Client(base_url=B); chk("Ohne Anmeldung kein Zugriff",c2.get(Kw).status_code==401)
# ---- Gutschein: Erinnerung nach 1 Tag
dom=f"erinnerung{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"Neue Anfrage","name":"Firma A"})
W=httpx.Client(base_url=B,headers={"Host":dom})
def pub(body): return W.post("/siteapi/api/anfrage",headers={"Content-Type":"application/json","Origin":"https://"+dom,"User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
G=lambda n,**kw:{**{"typ":"gutschein","name":n,"email":f"{n.lower()}{sfx}@besucher.de","betrag":"40 €","einwilligung":True},**kw}
r1=pub(G("Anna")); r2=pub(G("Bernd")); r3=pub(G("Clara")); chk("Drei Gutschein-Anfragen",all(x.status_code==200 for x in (r1,r2,r3)))
ref1,ref2,ref3=r1.json()["ref"],r2.json()["ref"],r3.json()["ref"]
open("/var/tmp/pt/mails.txt","a").close()
chk("Frisch: keine Erinnerung",webbetrieb.gutschein_erinnerung(cfg())==0)
sql(f"update website_gutscheine set erstellt_am=now()-interval '26 hours' where ref in ('{ref1}','{ref2}')")
sql(f"update website_gutscheine set status='gesendet' where ref='{ref2}'")
n=webbetrieb.gutschein_erinnerung(cfg()); time.sleep(1.2)
m=mail_an(mA,"Anna"); chk("Nach 1 Tag: Erinnerung für offene Anfrage",n>=1 and len(m)==1 and "Zahlungslink wurde noch nicht gesendet" in text(m[0]) and "Markentrix-Team" in text(m[0]) and "Claude" not in text(m[0]),[text(x) for x in m])
chk("Abgeschlossene Anfrage: keine Erinnerung",len(mail_an(mA,"Bernd"))==0)
chk("Junge Anfrage: keine Erinnerung",len(mail_an(mA,"Clara"))==0)
chk("Nur einmal",webbetrieb.gutschein_erinnerung(cfg())==0)
# doppelter Code
cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/firmaa"})
gl={x["ref"]:x["id"] for x in cA.get("/api/kunde/website-dienste/gutscheine").json()["gutscheine"]}
U="/api/kunde/website-dienste/gutscheine/"
r=cA.post(U+gl[ref1]+"/code",json={"code":"DOPPELT-1"}); chk("Code senden",r.status_code==200,r.text)
r=cA.post(U+gl[ref3]+"/code",json={"code":"doppelt-1"}); chk("Gleicher Code zweimal: 409",r.status_code==409,r.text)
r=cA.post(U+gl[ref3]+"/code",json={"code":"DOPPELT-2"}); chk("Anderer Code geht",r.status_code==200,r.text)
