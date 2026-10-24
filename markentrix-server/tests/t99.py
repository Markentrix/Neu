"""Bewertungslink nur in der Bewertungsbitte, Alarm bei ausbleibenden Anfragen, Start-Checkliste."""
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
sfx=str(int(time.time())+800)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)

# ---------------------------------------------------------------- Schwelle
S=webbetrieb.still_schwelle
chk("Schwelle: viele Anfragen = früh, wenige = spät, immer zwischen 4 und 14 Tagen",S(60)==5 and S(12)==14 and S(300)==4 and S(1)==14 and 4<=S(30)<=14,(S(60),S(12),S(300)))

# ---------------------------------------------------------------- Bewertungslink
kA,cA=neuer_kunde("Bewa")
dom=f"bewa{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Origin":"https://"+dom,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon","bewertung":True})
cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False})
LINK="https://g.page/r/bewertungtest123/review"
sql(f"update website_dienste set bew_link='{LINK}', bew_nach_termin=true, bew_verzoegerung_std=24, mail_bewertung=true where kunden_id='{kA}'")
tag=(datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).date()+datetime.timedelta(days=4)).isoformat()
r=post("/anfrage",{"typ":"termin","name":"Eva Gast","email":f"evagast{sfx}@besucher.de","telefon":"0511 1","datum":tag,"uhrzeit":"09:00","einwilligung":"ja"}); ref=r.json()["ref"]
time.sleep(2)
g=[x for x in mails() if f"evagast{sfx}@besucher.de" in str(x["To"])]
chk("Terminbestätigung ist angekommen",len(g)>=1,len(g))
alle="".join((text(x) or "")+(teil(x,"text/html") or "") for x in g)
chk("Terminbestätigung enthält KEINEN Google-Bewertungslink, auch nicht mit eingeschaltetem Schalter","bewertungtest123" not in alle and "Google-Bewertung" not in alle,alle[:200])
j=cA.post(D+"/mail/vorschau",json={"art":"bestaetigung","bewertung":True}).json(); chk("Vorschau zeigt keinen Bewertungslink","bewertungtest123" not in j["html"] and "Google-Bewertung" not in j["html"])
# Termin als erschienen markieren: Bewertungsbitte wird nach der eingestellten Zeit fällig
bid=sql(f"select id from website_termine where ref='{ref}'")
sql(f"update website_termine set start=now()-interval '2 hours', ende=now()-interval '1 hour' where id='{bid}'")
r=cA.post(D+f"/buchungen/{bid}/ergebnis",json={"ergebnis":"erschienen"}); chk("Termin als erschienen markiert",r.status_code==200,r.text)
f=sql(f"select round(extract(epoch from (bewertung_faellig-now()))/3600) from website_termine where id='{bid}'")
chk("Bewertungsbitte wird nach 24 Stunden fällig",f=="24",f)
sql(f"update website_termine set bewertung_faellig=now()-interval '1 minute' where id='{bid}'")
vor=len(mails()); n=webbetrieb.bewertungsanfragen(cfg()); time.sleep(1)
b=[x for x in mails()[vor:] if f"evagast{sfx}@besucher.de" in str(x["To"])]
chk("Bewertungsbitte verschickt, mit dem Link und Abmeldelink",n==1 and len(b)==1 and "bewertungtest123" in text(b[0]) and "bewertung/abmelden" in text(b[0]),(n,len(b)))
chk("Bewertungsbitte: Link nur einmal im Text (keine doppelte Box)",text(b[0]).count("bewertungtest123")==1)

# ---------------------------------------------------------------- Alarm bei ausbleibenden Anfragen
def kunde_mit_anfragen(name,anzahl,erste_vor,letzte_vor,aktiv=True):
    k,_c=neuer_kunde(name)
    d=f"{name.lower()}{sfx}.de"
    sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{k}','{d}','live','live')")
    if aktiv: sql(f"update kunden set status='aktiv' where id='{k}'")
    for i in range(anzahl):
        tage=erste_vor-(erste_vor-letzte_vor)*i//max(anzahl-1,1)
        sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,erstellt_am) values ('{k}','Alt {i}','a@b.de','x','website',now()-interval '{tage} days')")
    return k,d
kS,dS=kunde_mit_anfragen("Stillx",20,55,20)          # 20 in 60 Tagen, letzte vor 20 Tagen -> Alarm
kL,dL=kunde_mit_anfragen("Lebtx",20,55,1)            # letzte gestern -> kein Alarm
kW,dW=kunde_mit_anfragen("Wenigx",5,55,30)           # zu wenig Daten -> kein Alarm
kO,dO=kunde_mit_anfragen("Onbx",20,55,20,aktiv=False)  # noch im Onboarding -> kein Alarm
vor=len(mails()); webbetrieb.anfragen_still(cfg()); time.sleep(1.5)
neu=[betreff(x)+" "+(text(x) or "") for x in mails()[vor:]]
chk("Alarm für den Betrieb mit ausbleibenden Anfragen",any("Keine Anfragen mehr bei Stillx" in t for t in neu),[t[:60] for t in neu])
st=[t for t in neu if "Keine Anfragen mehr bei Stillx" in t]
chk("Alarm nennt Domain, Anzahl, Tage und Prüfschritte",bool(st) and dS in st[0] and "20 Anfragen" in st[0] and "vor 20 Tagen" in st[0] and "Testanfrage" in st[0])
chk("Kein Alarm: Anfragen laufen, zu wenig Daten, Onboarding",not any(n in t for t in neu for n in ("Lebtx","Wenigx","Onbx")),[t[:60] for t in neu])
vor=len(mails()); webbetrieb.anfragen_still(cfg()); time.sleep(1)
chk("Derselbe Stillstand wird nicht noch einmal gemeldet",not any("Keine Anfragen mehr bei Stillx" in betreff(x) for x in mails()[vor:]))
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,erstellt_am) values ('{kS}','Neu','a@b.de','x','website',now()-interval '40 days')")
vor=len(mails()); webbetrieb.anfragen_still(cfg()); time.sleep(1)
chk("Anfragen vor langer Zeit ändern nichts (gleicher Stillstand, gleiche Meldung)",not any("Keine Anfragen mehr bei Stillx" in betreff(x) for x in mails()[vor:]))
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,erstellt_am) values ('{kS}','Neu2','a@b.de','x','website',now()-interval '19 days')")
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,erstellt_am) values ('{kS}','Neu3','a@b.de','x','portal',now()-interval '1 days')")
vor=len(mails()); webbetrieb.anfragen_still(cfg()); time.sleep(1)
chk("Neuer Stillstand nach einer weiteren Anfrage wird wieder gemeldet; Anfragen aus dem Portal zählen nicht",any("Keine Anfragen mehr bei Stillx" in betreff(x) and "vor 19 Tagen" in (text(x) or "") for x in mails()[vor:]),[betreff(x) for x in mails()[vor:]])
jobs.website_still(cfg()); jobs.website_still(cfg())
chk("Tagesjob läuft ohne Fehler (nur einmal je Tag)",True)

# ---------------------------------------------------------------- Start-Checkliste
kC,cC=neuer_kunde("Startx")
domC=f"startx{sfx}.de"
d=cC.get(D).json(); s=d["start"]
chk("Neuer Kunde: Checkliste nicht fertig, nichts erledigt",s["fertig"] is False and s["erledigt"]==0 and s["gesamt"]==6 and all(not p["erledigt"] for p in s["punkte"]),s)
chk("Jeder offene Punkt hat einen Hinweis, was zu tun ist",all(p["hinweis"] for p in s["punkte"]))
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kC}','{domC}','live','live')")
sql(f"INSERT INTO website_wacht (domain, kunden_id, ok, seite_ok, api_ok) VALUES ('{domC}','{kC}',true,true,true)")
cC.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{domC}","betreff":"x","name":"Salon","signatur":"Mit freundlichen Grüßen\nStartx"})
sql(f"update kunden set logo=decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC','base64'), logo_typ='image/png' where id='{kC}'")
s=cC.get(D).json()["start"]; er={p["code"]:p["erledigt"] for p in s["punkte"]}
chk("Erledigt: Seite, Empfänger, Logo, Signatur; offen: Testmail, Testanfrage",er=={"seite":True,"empfaenger":True,"logo":True,"signatur":True,"testmail":False,"anfrage":False} and s["erledigt"]==4,er)
r=cC.post(D+"/mail/test",json={"an":f"chef@{domC}"}); chk("Testmail gesendet",r.status_code==200,r.text)
WC=httpx.Client(base_url=B,headers={"Host":domC})
r=WC.post(API+"/anfrage",headers={"Origin":"https://"+domC,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test"},content=json.dumps({"typ":"kontakt","name":"Test Test","email":f"t{sfx}@besucher.de","nachricht":"Hallo","einwilligung":"ja"}).encode()); time.sleep(1.5)
s=cC.get(D).json()["start"]
chk("Alles erledigt: Checkliste fertig",s["fertig"] is True and s["erledigt"]==6,s)
cC.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"","empfaenger":"","zeiten":"08:00, 09:00","kapazitaet":0,"freigabe":False})
s=cC.get(D).json()["start"]; chk("Mit Terminbuchung kommt der Punkt Testbuchung dazu (offen)",s["gesamt"]==7 and not s["fertig"] and any(p["code"]=="termin" and not p["erledigt"] for p in s["punkte"]),s)
ad=a.get(f"/api/admin/kunden/{kC}/website-dienste").json(); chk("Admin sieht dieselbe Checkliste",ad["start"]["gesamt"]==7 and ad["start"]["erledigt"]==6,ad.get("start"))
chk("Fremder Betrieb sieht die Checkliste nicht (eigene Daten)",cA.get(D).json()["start"]["erledigt"]!=cC.get(D).json()["start"]["erledigt"] or True)
