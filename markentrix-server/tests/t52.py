import httpx, time, re, email, subprocess
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
sfx=str(int(time.time())+81)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, zoneinfo, os, sys
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.datetime.now(TZ).date()
kA,cA,mA=neuer_kunde("Erin"); kB,cB,mB=neuer_kunde("Erib")
dom=f"erinnerung{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test","Origin":"https://"+dom},content=json.dumps(body).encode())
KAL={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon, Hauptstr. 1","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00, 12:00","kapazitaet":0,"freigabe":False,"halte_std":72}
r=cA.put("/api/kunde/website-dienste/kalender",json=KAL); chk("Kalender speichern (Erinnerung Standard)",r.status_code==200,r.text)
st=cA.get("/api/kunde/website-dienste").json()["kalender"]; chk("Erinnerung standardmäßig an: 24 und 2 Stunden",st["erinnerung"] is True and st["erinnerung_std1"]==24 and st["erinnerung_std2"]==2,st)
chk("Erinnerungszeit außerhalb des Bereichs abgelehnt",cA.put("/api/kunde/website-dienste/kalender",json={**KAL,"erinnerung_std1":999}).status_code==422)
tag=(heute+datetime.timedelta(days=5)).isoformat()
def buchen(name,mail,zeit):
    r=post("/anfrage",{"typ":"termin","name":name,"email":mail,"telefon":"0511 1","nachricht":"x","einwilligung":"ja","datum":tag,"uhrzeit":zeit}); assert r.status_code==200,r.text; return r.json()["ref"]
ref1=buchen("Mia Merk","mia@besucher.de","08:00"); ref2=buchen("Nils Neu","nils@besucher.de","09:00"); ref3=buchen("Olga Oft","olga@besucher.de","10:00")
chk("Buchung sofort gültig",sql(f"select status from website_termine where ref='{ref1}'")=="gebucht")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import webbetrieb, berichte, db
db.open_pool()
webbetrieb.erinnerungen(); chk("Termine in 5 Tagen: noch keine Erinnerung",not mail_an("mia@besucher.de","Erinnerung"))
# Termin morgen früh, vor Tagen gebucht -> erste Erinnerung
sql(f"update website_termine set start=now()+interval '20 hours', ende=now()+interval '20.5 hours', erstellt_am=now()-interval '3 days' where ref='{ref1}'")
# Termin morgen früh, aber gerade erst gebucht -> keine Zusatzmail
sql(f"update website_termine set start=now()+interval '20 hours 30 minutes', ende=now()+interval '21 hours', erstellt_am=now()-interval '10 minutes' where ref='{ref2}'")
n=webbetrieb.erinnerungen(); ms=mail_an("mia@besucher.de","Erinnerung")
chk("Erste Erinnerung an den Besucher",n==1 and len(ms)==1,n)
t=text(ms[0]) if ms else ""
chk("Mail enthält Absage-Link und Ort","/site/" in t and "/termin/absagen?t=" in t and "Salon, Hauptstr. 1" in t,t[:400])
chk("Stufe 1 vermerkt",sql(f"select erinnerung from website_termine where ref='{ref1}'")=="1")
chk("Frisch gebuchter Termin bekommt keine zweite Mail, wird aber vermerkt",not mail_an("nils@besucher.de","Erinnerung") and sql(f"select erinnerung from website_termine where ref='{ref2}'")=="1")
webbetrieb.erinnerungen(); chk("Nicht doppelt",len(mail_an("mia@besucher.de","Erinnerung"))==1)
absag=re.search(r"(/site/[^\s]+/termin/absagen\?t=[A-Za-z0-9_-]+)",t).group(1)
# zweite Erinnerung 2 Stunden vorher
sql(f"update website_termine set start=now()+interval '90 minutes', ende=now()+interval '2 hours' where ref='{ref1}'")
webbetrieb.erinnerungen(); chk("Zweite Erinnerung",len(mail_an("mia@besucher.de","Erinnerung"))==2 and sql(f"select erinnerung from website_termine where ref='{ref1}'")=="2")
# ausgeschaltet
cA.put("/api/kunde/website-dienste/kalender",json={**KAL,"erinnerung":False})
sql(f"update website_termine set start=now()+interval '10 hours', ende=now()+interval '11 hours', erstellt_am=now()-interval '3 days', erinnerung=0 where ref='{ref3}'")
webbetrieb.erinnerungen(); chk("Abgeschaltet: keine Erinnerung",not mail_an("olga@besucher.de","Erinnerung"))
cA.put("/api/kunde/website-dienste/kalender",json={**KAL,"erinnerung":True,"erinnerung_std1":12,"erinnerung_std2":0})
webbetrieb.erinnerungen(); chk("Eigene Zeiten (12 h) gelten",len(mail_an("olga@besucher.de","Erinnerung"))==1)
r=W.post(absag.split("?")[0],data={"t":absag.split("t=")[1]}); chk("Absage-Link funktioniert",r.status_code==200 and sql(f"select status from website_termine where ref='{ref1}'")=="abgesagt",r.status_code)
sql(f"update website_termine set start=now()+interval '2 hours', erinnerung=1 where ref='{ref3}'")
webbetrieb.erinnerungen(); chk("Stufe 2 aus (0): keine weitere Mail",len(mail_an("olga@besucher.de","Erinnerung"))==1)
# ---- Nichterschienen
sql(f"update website_termine set start=now()-interval '3 hours', ende=now()-interval '2.5 hours', status='gebucht', ergebnis=null where ref='{ref2}'")
b=cA.get("/api/kunde/website-dienste/buchungen").json()
chk("Vergangener Termin wird zur Rückmeldung angeboten",any(x["email"]=="nils@besucher.de" for x in b["vergangen"]),b)
bid=[x["id"] for x in b["vergangen"] if x["email"]=="nils@besucher.de"][0]
chk("Ungültiges Ergebnis abgelehnt",cA.post(f"/api/kunde/website-dienste/buchungen/{bid}/ergebnis",json={"ergebnis":"vielleicht"}).status_code==422)
chk("Fremder Kunde darf nicht bewerten",cB.post(f"/api/kunde/website-dienste/buchungen/{bid}/ergebnis",json={"ergebnis":"erschienen"}).status_code==409 and sql(f"select coalesce(ergebnis,'-') from website_termine where id='{bid}'")=="-")
r=cA.post(f"/api/kunde/website-dienste/buchungen/{bid}/ergebnis",json={"ergebnis":"nicht_erschienen"}); chk("Nicht erschienen vermerkt",r.status_code==200 and sql(f"select ergebnis from website_termine where id='{bid}'")=="nicht_erschienen",r.text)
chk("Portal-Termin auf nicht erschienen",sql(f"select t.status from termine t join website_termine w on w.termin_id=t.id where w.id='{bid}'")=="nicht_erschienen")
chk("Nicht mehr in der Rückmeldeliste",not any(x["id"]==bid for x in cA.get("/api/kunde/website-dienste/buchungen").json()["vergangen"]))
# derselbe Besucher bucht erneut
ref4=buchen("Nils Neu","nils@besucher.de","11:00")
sql(f"update website_termine set start=now()-interval '2 hours', ende=now()-interval '1.5 hours' where ref='{ref4}'")
v=cA.get("/api/kunde/website-dienste/buchungen").json()["vergangen"]; chk("Zähler: Besucher ist schon einmal nicht erschienen",any(x["email"]=="nils@besucher.de" and x["fehlt_bisher"]==1 for x in v),v)
bid4=[x["id"] for x in v if x["email"]=="nils@besucher.de"][0]
chk("Erschienen vermerkt",cA.post(f"/api/kunde/website-dienste/buchungen/{bid4}/ergebnis",json={"ergebnis":"erschienen"}).status_code==200)
ref5=buchen("Zukunft Zeit","zukunft@besucher.de","12:00"); fid=sql(f"select id from website_termine where ref='{ref5}'")
chk("Zukünftiger Termin kann nicht bewertet werden",cA.post(f"/api/kunde/website-dienste/buchungen/{fid}/ergebnis",json={"ergebnis":"erschienen"}).status_code==409)
s=cA.get("/api/kunde/website-dienste/statistik?tage=30").json(); chk("Statistik: 1 erschienen, 1 nicht erschienen",s["erschienen"]==1 and s["nicht_erschienen"]==1,s)
# ---- Monatsbericht
von=heute.replace(day=1); bis=(von.replace(day=28)+datetime.timedelta(days=4)).replace(day=1)
sql(f"insert into website_wacht_tag (domain, tag, geprueft, ok) values ('{dom}', current_date, 10, 9) on conflict do nothing")
with db.tx("system") as cur: d=berichte.sammeln(cur,kA,von,bis)
w=d["website"]; chk("Bericht: Website-Zahlen",w["buchungen"]>=3 and w["nicht_erschienen"]==1 and w["erschienen"]==1 and float(w["erreichbarkeit"])==90.0,w)
with db.tx("system") as cur:
    bid_b=berichte.erstellen(cur,kA,von)
with db.tx("system") as cur: pdfb,_=berichte.pdf_erzeugen(cur,bid_b)
chk("Bericht-PDF entsteht",pdfb[:4]==b"%PDF" and len(pdfb)>1500)
with db.tx("system") as cur: alt=berichte.sammeln(cur,kB,von,bis)
chk("Kunde ohne Website: Bericht trotzdem sauber",alt["website"]["aufrufe"]==0 and alt["website"]["erreichbarkeit"] is None)
