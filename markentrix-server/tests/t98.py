"""Bestätigen/Ablehnen per Knopf in der Mail an den Betrieb und Mail-Vorschau im Kundenportal."""
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
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+700)
k=a.post("/api/admin/kunden",json={"firma":f"Knopf {sfx}","ansprechpartner":"Tina Test","email":f"knopf{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"knopf{sfx}@k.de"),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); assert c.post("/api/login",json={"email":f"knopf{sfx}@k.de","password":"InhaberPasswort1"}).status_code==200
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import routes_sitedienste as rsd
dom=f"knopf{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kid}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
c.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=c.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":True}); chk("Kalender mit eigener Bestätigung",r.status_code==200,r.text)
sid=sql(f"select site_id from website_dienste where kunden_id='{kid}'")
tag=(datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).date()+datetime.timedelta(days=4)).isoformat()
T=lambda uhr,name:{"typ":"termin","name":name,"email":f"{name.lower().replace(' ','')}{sfx}@besucher.de","telefon":"0511 1","datum":tag,"uhrzeit":uhr,"einwilligung":"ja"}

# ---- Token
bid0="11111111-2222-3333-4444-555555555555"
t1,t2=rsd.aktionstoken(bid0,"bestaetigen"),rsd.aktionstoken(bid0,"ablehnen")
chk("Schlüssel: gleich bei gleicher Eingabe, verschieden je Aktion und Buchung",t1==rsd.aktionstoken(bid0,"bestaetigen") and t1!=t2 and t1!=rsd.aktionstoken(bid0.replace("1","2"),"bestaetigen") and len(t1)==32)

# ---- Anfrage, Mail an den Betrieb
def buchen(uhr,name):
    r=post("/anfrage",T(uhr,name)); assert r.status_code==200,r.text
    ref=r.json()["ref"]; time.sleep(1.8)
    bid=sql(f"select id from website_termine where ref='{ref}'")
    m=[x for x in mails() if f"chef@{dom}" in str(x["To"]) and ref in str(x["Subject"])]
    return bid,ref,m
bid,ref,m=buchen("09:00","Mia Gast")
chk("Buchung ist vorgemerkt (wartet auf Bestätigung)",sql(f"select status from website_termine where id='{bid}'")=="reserviert")
chk("Mail an den Betrieb ist da",len(m)==1,len(m))
t_=text(m[0]); h_=teil(m[0],"text/html")
li=re.findall(r"https?://\S+/site/"+sid+r"/buchung/"+bid+r"/(bestaetigen|ablehnen)\?k=([A-Za-z0-9_-]+)",t_)
chk("Mail enthält Link zum Bestätigen und zum Ablehnen",sorted(x[0] for x in li)==["ablehnen","bestaetigen"],t_[:600])
chk("HTML-Mail: zwei Knöpfe mit Beschriftung",">Termin bestätigen<" in h_ and ">Termin ablehnen<" in h_ and h_.count("/buchung/")>=2)
chk("Hinweis: Links nicht weiterleiten","nicht weiterleiten" in t_)
lk={a_:k_ for a_,k_ in li}
url=lambda akt,k=None:f"/site/{sid}/buchung/{bid}/{akt}?k={k or lk[akt]}"

# ---- GET ändert nichts und prüft den Schlüssel
r=W.get(url("bestaetigen")); chk("GET zeigt Rückfrage mit Datum und Gast, ändert nichts",r.status_code==200 and "Mia Gast" in r.text and "Ja, bestätigen" in r.text and sql(f"select status from website_termine where id='{bid}'")=="reserviert",r.text[:300])
chk("Falscher Schlüssel: ungültig",("ungültig" in W.get(url("bestaetigen","x"*32)).text) and "ungültig" in W.get(url("ablehnen",lk["bestaetigen"])).text)
chk("Schlüssel passt nicht zu anderer Buchung",("ungültig" in W.get(f"/site/{sid}/buchung/{bid.replace(bid[:2],'ff' if bid[:2]!='ff' else 'ee')}/bestaetigen?k={lk['bestaetigen']}").text))
chk("Falsche Website: nicht gefunden/ungültig","ungültig" in W.get(f"/site/mk_FALSCH123456/buchung/{bid}/bestaetigen?k={lk['bestaetigen']}").text or "nicht mehr" in W.get(f"/site/mk_FALSCH123456/buchung/{bid}/bestaetigen?k={lk['bestaetigen']}").text)
chk("Unbekannte Aktion: ungültig","ungültig" in W.get(f"/site/{sid}/buchung/{bid}/loeschen?k={lk['bestaetigen']}").text)
chk("Fremder Kunde kann nicht bestätigen (POST mit falschem Schlüssel)","ungültig" in W.post(f"/site/{sid}/buchung/{bid}/bestaetigen",data={"k":"y"*32}).text and sql(f"select status from website_termine where id='{bid}'")=="reserviert")

# ---- Bestätigen
vor=len(mails())
r=W.post(url("bestaetigen").split("?")[0],data={"k":lk["bestaetigen"]}); chk("POST bestätigt",r.status_code==200 and "bestätigt" in r.text,r.text[:300])
time.sleep(1.8)
chk("Status gebucht, Termin bestätigt",sql(f"select status from website_termine where id='{bid}'")=="gebucht" and sql(f"select t.status from termine t join website_termine w on w.termin_id=t.id where w.id='{bid}'")=="bestaetigt")
g=[x for x in mails()[vor:] if f"miagast{sfx}@besucher.de" in str(x["To"])]
chk("Gast bekommt die Bestätigung mit Kalender-Einladung",len(g)==1 and "bestätigt" in str(email.header.make_header(email.header.decode_header(g[0]["Subject"]))) and any(p.get_content_type()=="text/calendar" for p in g[0].walk()),[str(x["Subject"]) for x in mails()[vor:]])
r=W.get(url("bestaetigen")); chk("Zweiter Klick: schon bestätigt","schon bestätigt" in r.text)
r=W.post(url("bestaetigen").split("?")[0],data={"k":lk["bestaetigen"]}); chk("Zweiter POST: keine Doppelmail",("schon bestätigt" in r.text) and len([x for x in mails()[vor:] if f"miagast{sfx}@besucher.de" in str(x["To"])])==1)
chk("Protokoll: Bestätigung per Mail steht im Audit-Log",int(sql(f"select count(*) from audit_log where kunden_id='{kid}' and aktion='website_buchung_bestaetigt'"))==1)

# ---- Ablehnen
bid2,ref2,m2=buchen("10:00","Ben Gast")
t2_=text(m2[0]); l2={a_:k_ for a_,k_ in re.findall(r"/buchung/"+bid2+r"/(bestaetigen|ablehnen)\?k=([A-Za-z0-9_-]+)",t2_)}
u2=f"/site/{sid}/buchung/{bid2}/ablehnen"
r=W.get(u2+"?k="+l2["ablehnen"]); chk("Ablehnen-Seite hat Feld für die Begründung","name=\"grund\"" in r.text and "Ja, ablehnen" in r.text)
vor=len(mails())
r=W.post(u2,data={"k":l2["ablehnen"],"grund":"Leider sind wir an dem Tag ausgebucht."}); chk("POST lehnt ab",r.status_code==200 and "abgelehnt" in r.text,r.text[:200])
time.sleep(1.8)
chk("Status abgesagt, Termin abgesagt",sql(f"select status from website_termine where id='{bid2}'")=="abgesagt" and sql(f"select t.status from termine t join website_termine w on w.termin_id=t.id where w.id='{bid2}'")=="abgesagt")
g=[x for x in mails()[vor:] if f"bengast{sfx}@besucher.de" in str(x["To"])]
chk("Gast bekommt eine Absage mit der Begründung",len(g)==1 and "ausgebucht" in text(g[0]),[str(x["Subject"]) for x in mails()[vor:]])
chk("Zeit ist wieder buchbar",post("/anfrage",T("10:00","Cem Gast")).status_code==200)
r=W.get(f"/site/{sid}/buchung/{bid2}/ablehnen?k={l2['ablehnen']}"); chk("Nach der Absage: Link meldet 'schon abgesagt'","schon abgesagt" in r.text)
# Bestätigten Termin über den Ablehnen-Link absagen
r=W.post(f"/site/{sid}/buchung/{bid}/ablehnen",data={"k":lk["ablehnen"],"grund":""}); time.sleep(1.5)
chk("Auch ein bestätigter Termin lässt sich über den Ablehnen-Link absagen",sql(f"select status from website_termine where id='{bid}'")=="abgesagt",r.text[:200])

# ---- Sofortbuchung (ohne Bestätigung) hat keine Knöpfe
c.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False})
b3,r3,m3=buchen("11:00","Dora Gast")
chk("Sofortbuchung: Mail ohne Bestätigen-Knöpfe",len(m3)==1 and "/buchung/" not in text(m3[0]),text(m3[0])[:300] if m3 else "")

# ---- Mail-Vorschau
vor=len(mails())
chk("Vorschau ohne Anmeldung nicht möglich",httpx.Client(base_url=B,headers=H).post(D+"/mail/vorschau",json={"art":"bestaetigung"}).status_code in (401,403))
r=c.post(D+"/mail/vorschau",json={"art":"bestaetigung","signatur":"Mit freundlichen Grüßen\nVORSCHAUFIRMA GmbH\nTel. 0511 99999","bewertung":False,"facebook":"","instagram":"","hinweis":"VORSCHAUHINWEIS"}); j=r.json()
chk("Vorschau Terminbestätigung: Betreff",r.status_code==200 and "bestätigt" in j["betreff"],r.text[:200])
chk("Vorschau: ungespeicherte Signatur",all(x in j["html"] for x in ("VORSCHAUFIRMA","0511 99999")),[x for x in ("VORSCHAUFIRMA","0511 99999") if x not in j["html"]])
chk("Vorschau: Hinweistext","VORSCHAUHINWEIS" in j["html"],j["html"][-600:])
chk("Vorschau: Absage-Knopf im Beispiel, kein Skript","Termin absagen" in j["html"] and "<script" not in j["html"])
chk("Vorschau ohne Logo: Hinweis 'logo' false",j["logo"] is False)
chk("Vorschau speichert nichts",sql(f"select coalesce(mail_signatur,'') from website_dienste where kunden_id='{kid}'")=="")
chk("Vorschau verschickt nichts",len(mails())==vor)
sql(f"update kunden set logo=decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC','base64'), logo_typ='image/png' where id='{kid}'")
j=c.post(D+"/mail/vorschau",json={"art":"eingang"}).json()
chk("Vorschau Eingangsbestätigung mit Logo als Bild (kein cid)",j["logo"] is True and "data:image/png;base64," in j["html"] and "cid:" not in j["html"] and "Eingangsbestätigung" in j["betreff"] and "Vorgangsnummer" in j["html"])
r=c.post(D+"/mail/vorschau",json={"art":"bestaetigung","facebook":"http://unsicher.example"}); chk("Vorschau: unsicherer Link wird abgelehnt (400)",r.status_code==400)
r=c.post(D+"/mail/vorschau",json={"art":"anders"}); chk("Vorschau: unbekannte Art abgelehnt",r.status_code in (400,422))
j=c.post(D+"/mail/vorschau",json={"art":"bestaetigung","signatur":"<script>alert(1)</script>"}).json(); chk("Vorschau: Eingaben werden maskiert","<script>alert" not in j["html"])
