"""Erste-Woche-Karte (Kunde), heiße Leads mit Begründung, Notiz-Zusammenfassung per KI, Nachfrage-Grundlagen für Vertriebler."""
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
sfx=str(int(time.time())+1600)
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
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)




a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de"}).json(); pid=p["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"vera{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"VeraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); r=v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123456"}); assert r.status_code==200,r.text
def lead(tag,**kw):
    d={"firma":f"Vert{tag} {sfx}","telefon":f"0511 74{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","vertriebspartner_id":pid,"email":f"vert{tag}{sfx}@lead.de","ansprechpartner":"Herr Lead"}; d.update(kw)
    r=a.post("/api/admin/leads",json=d); assert r.status_code==200,r.text; return r.json()["id"]
def steuerung(an): a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":False,"reaktionsstunden":2,"preise_sichtbar":False,"vertrieb_angebote":an})

a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":False,"reaktionsstunden":2,"preise_sichtbar":False,"vertrieb_angebote":True})
# ---------------------------------------------------------------- Heiße Leads mit Begründung
L1=lead("a"); L2=lead("b"); L3=lead("c")
sql(f"update leads set temperatur='heiss' where id='{L1}'")
r=v.get("/api/vertrieb/heute").json()
h1=[x for x in r["heiss"] if x["id"]==L1]
chk("Heißer Lead steht oben mit Begründung",len(h1)==1 and "Als heiß eingestuft" in h1[0]["gruende"],h1)
chk("Lead ohne Signal hat leere Begründung",all(x["gruende"]==[] for x in r["neu"] if x["id"]==L2),r["neu"])
v.post(f"/api/vertrieb/leads/{L2}/angebot-senden",json={"paket_codes":["KI_ONE"],"gueltig_tage":30}); time.sleep(1.2)
bid=sql(f"select id from belege where lead_id='{L2}' and art='angebot' limit 1"); nr=sql(f"select nummer from belege where id='{bid}'")
sql(f"update leads set letzter_kontakt_am=now(), status='angebot' where id='{L2}'")
r=v.get("/api/vertrieb/heute").json(); chk("Angebot noch nicht angesehen: kein Signal",not any(x["id"]==L2 for x in r["heiss"]))
sql(f"update belege set angesehen_am=now() where id='{bid}'")
r=v.get("/api/vertrieb/heute").json(); x=[z for z in r["heiss"] if z["id"]==L2]
chk("Angebot angesehen: Lead rückt nach oben mit Grund",len(x)==1 and any(f"Angebot {nr} angesehen" in g for g in x[0]["gruende"]),x)
chk("Begründung enthält keine Preise",not any("€" in g or "cent" in g.lower() for g in x[0]["gruende"]))
sql(f"insert into lead_aktivitaeten (lead_id,art,inhalt,von) values ('{L3}','antwort','Antwort per Mail','lead')")
r=v.get("/api/vertrieb/heute").json(); x=[z for z in r["heiss"] if z["id"]==L3]
chk("Antwort des Leads: Grund „kürzlich geantwortet“",len(x)==1 and "Hat kürzlich geantwortet" in x[0]["gruende"],x)
sql(f"update leads set status='verloren' where id='{L3}'")
chk("Verlorener Lead taucht nicht auf",not any(z["id"]==L3 for z in v.get("/api/vertrieb/heute").json()["heiss"]))

# ---------------------------------------------------------------- Notiz zusammenfassen
r=v.post("/api/vertrieb/notiz-zusammenfassen",json={"text":"Habe mit dem Inhaber gesprochen, er hat Interesse an der Terminbuchung, will aber erst seine Frau fragen, ruft Montag zurück."})
chk("Zusammenfassung kommt zurück",r.status_code==200 and "Nächster Schritt" in r.json()["zusammenfassung"] and r.json()["zusammenfassung"].startswith("•"),r.text)
import json as _j; mk=_j.load(open("/var/tmp/pt/mock_last.json"))
chk("Nur der Notiztext geht an die KI, keine Lead-Daten","Inhaber gesprochen" in str(mk["body"]["messages"]) and "Vera" not in str(mk) and f"@" not in str(mk["body"]["messages"]),str(mk)[:300])
chk("Zu kurze Notiz: 422",v.post("/api/vertrieb/notiz-zusammenfassen",json={"text":"ok"}).status_code==422)
chk("Nicht angemeldet: 401",httpx.post(B+"/api/vertrieb/notiz-zusammenfassen",headers=H,json={"text":"Das ist eine lange Notiz zum Testen"}).status_code==401)
kid,c=neuer_kunde("Ew"); chk("Kunde darf nicht (403)",c.post("/api/vertrieb/notiz-zusammenfassen",json={"text":"Das ist eine lange Notiz zum Testen"}).status_code==403)

# ---------------------------------------------------------------- Erste Woche (Kunde)
e=c.get("/api/kunde/erste-woche").json(); codes=[s["code"] for s in e["schritte"]]
chk("Erste Woche aktiv für neuen Kunden",e["aktiv"] and codes[:4]==["app","push","sicher","nachricht"],e)
chk("Nichts ist am Anfang erledigt (außer clientseitig)",all(not s["fertig"] for s in e["schritte"] if s["code"]!="app"))
chk("App-Schritt wird im Browser entschieden (null)",e["schritte"][0]["fertig"] is None)
r=c.post("/api/kunde/tickets",json={"betreff":"Hallo","text":"Erste Frage","art":"frage"}); chk("Nachricht schreiben",r.status_code in (200,201),r.text)
e=c.get("/api/kunde/erste-woche").json(); chk("Nachricht erledigt",[s for s in e["schritte"] if s["code"]=="nachricht"][0]["fertig"] is True,e)
sql(f"insert into push_abos (benutzer_id,endpoint,p256dh,auth) select id,'https://fcm.googleapis.com/x{sfx}','a','b' from benutzer where email='ew{sfx}@k.de'")
e=c.get("/api/kunde/erste-woche").json(); chk("Push eingeschaltet erkannt",[s for s in e["schritte"] if s["code"]=="push"][0]["fertig"] is True)
sql(f"update benutzer set totp_aktiv=true where email='ew{sfx}@k.de'")
e=c.get("/api/kunde/erste-woche").json(); chk("Zwei-Faktor erkannt",[s for s in e["schritte"] if s["code"]=="sicher"][0]["fertig"] is True)
chk("Ausblenden speichern",c.put("/api/me/ansicht",json={"erste_woche_zu":True}).status_code==200)
chk("Ausgeblendet: Karte weg",c.get("/api/kunde/erste-woche").json()["aktiv"] is False)
k2,c2=neuer_kunde("Alt"); sql(f"update kunden set erstellt_am=now()-interval '40 days' where id='{k2}'")
chk("Älter als 30 Tage: keine Karte",c2.get("/api/kunde/erste-woche").json()["aktiv"] is False)
chk("Vertriebler hat keinen Zugriff (403)",v.get("/api/kunde/erste-woche").status_code==403)
