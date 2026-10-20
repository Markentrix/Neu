from datetime import date, timedelta
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


# ---------------------------------------------------------------- Zahlen
z0=v.get("/api/vertrieb/zahlen"); chk("Zahlen: 200 mit Wochenziel 40",z0.status_code==200 and z0.json()["wochenziel"]==40,z0.text[:300])
l1=lead("Zahl-Lead",vertriebspartner_id=p); l2=lead("Zahl-Lead2",vertriebspartner_id=p); l3=lead("Zahl-Lead3",vertriebspartner_id=p)
for lid in (l1,l2,l3): chk("Kontakt festhalten "+lid[:4],v.post(f"/api/vertrieb/leads/{lid}/kontakt",json={"ergebnis":"anruf_erreicht" if lid!=l3 else "anruf_nicht_erreicht"}).status_code==200)
chk("Termin festhalten",v.post(f"/api/vertrieb/leads/{l1}/kontakt",json={"ergebnis":"termin","notiz":"Dienstag 10 Uhr"}).status_code==200)
z=v.get("/api/vertrieb/zahlen").json()
chk("Zahlen: Anrufe/Erreicht/Termine zählen",z["anrufe_woche"]==3 and z["erreicht_woche"]==2 and z["termine_woche"]==1 and z["anrufe_heute"]==3,z)
chk("Zahlen: Quoten",z["quote_erreicht"]==67 and z["quote_termin"]==50,z)
chk("Zahlen: Provision-Block vorhanden",set(z["provision"])>={"offen_cent","monat_cent","offene_angebote","rechenbeispiel_cent"},z["provision"])
chk("Wochenziel setzen",v.put("/api/vertrieb/ziel",json={"anrufe":55}).status_code==200 and v.get("/api/vertrieb/zahlen").json()["wochenziel"]==55)
chk("Wochenziel: 0 und 501 abgewiesen",v.put("/api/vertrieb/ziel",json={"anrufe":0}).status_code==422 and v.put("/api/vertrieb/ziel",json={"anrufe":501}).status_code==422)
chk("Zahlen: Kunde darf nicht",neuer_kunde("Zahl")[1].get("/api/vertrieb/zahlen").status_code==403)
# Zahlen sind nur die eigenen: anderer Vertriebler sieht nichts davon
p2=a.post("/api/admin/vertrieb/partner",json={"name":"Willi Vertrieb","email":f"willi{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"willi{sfx}@v.de"),"password":"WilliPasswort123"})
w=httpx.Client(base_url=B,headers=H); assert w.post("/api/login",json={"email":f"willi{sfx}@v.de","password":"WilliPasswort123"}).status_code==200
chk("Zahlen: fremder Vertriebler sieht 0 Anrufe",w.get("/api/vertrieb/zahlen").json()["anrufe_woche"]==0)

# ---------------------------------------------------------------- Leitfaden
r=v.get("/api/vertrieb/leitfaden"); j=r.json(); chk("Leitfaden: Standard mit Abschnitten, Einwänden, Branchen",r.status_code==200 and len(j["abschnitte"])>=5 and len(j["einwaende"])>=5 and "werkstatt" in j["branchen"],r.text[:200])
t=a.get("/api/admin/einstellungen/leitfaden").json(); chk("Leitfaden: Admin sieht Text, nicht angepasst",t["angepasst"] is False and "[Abschnitt] Vor dem Anruf" in t["text"])
neu=t["text"].replace("Vor dem Anruf","Vorbereitung ZZZ")
chk("Leitfaden: Admin speichert",a.put("/api/admin/einstellungen/leitfaden",json={"text":neu}).status_code==200)
chk("Leitfaden: Änderung beim Vertriebler",v.get("/api/vertrieb/leitfaden").json()["abschnitte"][0]["titel"]=="Vorbereitung ZZZ")
chk("Leitfaden: kaputter Text 400",a.put("/api/admin/einstellungen/leitfaden",json={"text":"Hallo"}).status_code==400)
chk("Leitfaden: auf Standard zurück",a.put("/api/admin/einstellungen/leitfaden",json={"standard":True}).status_code==200 and v.get("/api/vertrieb/leitfaden").json()["abschnitte"][0]["titel"]=="Vor dem Anruf")
chk("Leitfaden: Vertriebler darf nicht bearbeiten",v.put("/api/admin/einstellungen/leitfaden",json={"text":neu}).status_code==403)
lw=lead("Werkstatt-Lead",vertriebspartner_id=p,branche="Kfz-Werkstatt"); h1=v.get(f"/api/vertrieb/leads/{lw}/branchenhinweis").json()
chk("Branchenhinweis passt zur Branche",h1 and h1["code"]=="werkstatt" and len(h1["tipps"])>=2,h1)
chk("Branchenhinweis: unbekannte Branche = null",v.get(f"/api/vertrieb/leads/{l1}/branchenhinweis").json() is None)
chk("Branchenhinweis: fremder Lead 404",w.get(f"/api/vertrieb/leads/{lw}/branchenhinweis").status_code==404)

# ---------------------------------------------------------------- Nach dem Gespräch (Mail-Entwurf)
le=lead("Mail-Lead",vertriebspartner_id=p,ansprechpartner="Herr Meier",email="meier@mail-lead.de")
r=v.get(f"/api/vertrieb/leads/{le}/nachgespraech").json()
chk("Mail-Entwurf: Platzhalter gefüllt, Empfänger gesetzt",r["an"]=="meier@mail-lead.de" and "Herr Meier" in r["text"] and "Vera Vertrieb" in r["text"] and "{" not in r["text"] and "Mail-Lead" in r["betreff"],r)
chk("Mail-Entwurf: wird nicht vom Portal gesendet",not mail_an("meier@mail-lead.de"))

# ---------------------------------------------------------------- Angebotsanfrage
pk=v.get("/api/vertrieb/pakete").json(); chk("Pakete: nur Name und Code, keine Preise",len(pk)>=1 and set(pk[0])=={"code","name"},pk[:1])
r=v.post(f"/api/vertrieb/leads/{l1}/angebotsanfrage",json={"paket_code":pk[0]["code"],"notiz":"Will 2 Standorte"}); chk("Angebot anfragen",r.status_code==200,r.text); aid=r.json()["id"]
chk("Doppelte Anfrage: 409",v.post(f"/api/vertrieb/leads/{l1}/angebotsanfrage",json={}).status_code==409)
chk("Unbekanntes Paket: 400",v.post(f"/api/vertrieb/leads/{l2}/angebotsanfrage",json={"paket_code":"gibtsnicht"}).status_code==400)
chk("Fremder Lead: 404",w.post(f"/api/vertrieb/leads/{l1}/angebotsanfrage",json={}).status_code==404)
chk("Admin-Aufgabe wurde angelegt",sql("select count(*) from aufgaben where titel like 'Angebot erstellen: Zahl-Lead %'")=="1")
chk("Verlauf: Eintrag Angebot angefragt",sql(f"select count(*) from lead_aktivitaeten where lead_id='{l1}' and inhalt like 'Angebot angefragt%'")=="1")
chk("Glocke für Admin",sql("select count(*) from benachrichtigungen where tag='angebotsanfrage'")!="0")
r=v.get(f"/api/vertrieb/leads/{l1}/angebotsanfragen").json(); chk("Vertriebler sieht Status Angefragt",len(r)==1 and r[0]["status"]=="angefragt",r)
chk("Admin sieht Anfrage mit Vertriebler",a.get(f"/api/admin/leads/{l1}/angebotsanfragen").json()[0]["vertriebler"]=="Vera Vertrieb")
chk("Admin setzt Status",a.patch(f"/api/admin/angebotsanfragen/{aid}",json={"status":"angebot_raus","admin_notiz":"Kommt morgen"}).status_code==200)
time.sleep(0.5)
r=v.get("/api/vertrieb/angebotsanfragen").json(); chk("Vertriebler sieht neuen Status und Notiz",r[0]["status"]=="angebot_raus" and r[0]["admin_notiz"]=="Kommt morgen",r)
chk("Glocke für Vertriebler bei Statuswechsel",sql("select count(*) from benachrichtigungen where tag='angebotsstatus'")!="0")
chk("Status ungültig: 422",a.patch(f"/api/admin/angebotsanfragen/{aid}",json={"status":"quatsch"}).status_code==422)
chk("Vertriebler darf Status nicht ändern",v.patch(f"/api/admin/angebotsanfragen/{aid}",json={"status":"angenommen"}).status_code==403)
chk("Nach Angebot raus ist neue Anfrage möglich",v.post(f"/api/vertrieb/leads/{l1}/angebotsanfrage",json={"notiz":"Zusatz"}).status_code==200)
v.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"kein_interesse"})
chk("Verlorener Lead: keine Anfrage",v.post(f"/api/vertrieb/leads/{l2}/angebotsanfrage",json={}).status_code==400)
