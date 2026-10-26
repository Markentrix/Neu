"""Lead-Funnel (Kampagnenseiten), Empfehlungsprogramm: Rechtssperre, Anmeldung, Dublette, Roboterfalle, Auswertung, Empfehlungslink, Prämie."""
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
sfx=str(int(time.time())+1700)
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

from app import jobs
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
pub=httpx.Client(base_url=B,headers={**H,"User-Agent":"Mozilla/5.0 (iPhone) Safari"})
slug=f"werk-{sfx}"
basis={"slug":slug,"name":"Werkstatt-Kampagne","titel":"Mehr Aufträge für Ihre Werkstatt","untertitel":"Wir automatisieren Ihre Anfragen","nutzen":["Weniger Büroarbeit","Mehr Termine"],"button":"Jetzt anfragen","einwilligung_text":"Ich willige ein, dass Markentrix mich kontaktiert.","kosten_cent":20000}
# ---------------------------------------------------------------- Rechtssperre
r=a.post("/api/admin/funnel",json={**basis,"aktiv":True,"rechtlich_geprueft":False}); chk("Live ohne Rechtsprüfung wird abgelehnt",r.status_code==400 and "geprüft" in r.text,r.text)
r=a.post("/api/admin/funnel",json={**basis,"slug":"X Y!"}); chk("Ungültiger Seitenname wird abgelehnt",r.status_code==400,r.text)
r=a.post("/api/admin/funnel",json={**basis,"aktiv":False}); chk("Seite lässt sich ausgeschaltet anlegen",r.status_code==200 and r.json()["link"].endswith("/f/"+slug),r.text); kid=r.json()["id"]
chk("Doppelter Seitenname wird abgelehnt",a.post("/api/admin/funnel",json=basis).status_code==409)
chk("Ausgeschaltete Seite ist öffentlich nicht erreichbar",pub.get(f"/api/public/funnel/{slug}").status_code==404)
chk("Anmeldung bei ausgeschalteter Seite wird abgelehnt",pub.post(f"/api/public/funnel/{slug}",json={"name":"Max Muster","email":f"m{sfx}@x.de","telefon":"0511 1","einwilligung":True}).status_code==404)
r=a.put(f"/api/admin/funnel/{kid}",json={**basis,"aktiv":True,"rechtlich_geprueft":True}); chk("Mit Rechtsprüfung geht die Seite live",r.status_code==200,r.text)
r=pub.get(f"/api/public/funnel/{slug}").json()
chk("Öffentliche Seite liefert Texte und Vorteile",r["titel"]=="Mehr Aufträge für Ihre Werkstatt" and r["nutzen"]==["Weniger Büroarbeit","Mehr Termine"] and "einwilligung_text" in r,r)
chk("Seite /f/name wird ausgeliefert",pub.get(f"/f/{slug}").status_code==200 and "funnel.js" in pub.get(f"/f/{slug}").text)
# ---------------------------------------------------------------- Anmeldung
mail=f"fun{sfx}@lead.de"; kam={"name":"Max Muster","firma":f"Funnel GmbH {sfx}","email":mail,"telefon":"0511 99","website":"www.funnel.de","einwilligung":True,"utm":{"utm_source":"meta","utm_campaign":"werk1","x":"y"}}
r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"einwilligung":False}); chk("Ohne Einwilligung kein Lead",r.status_code==400 and sql(f"select count(*) from leads where email='{mail}'")=="0",r.text)
r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"telefon":None}); chk("Telefon ist Pflicht (wenn so eingestellt)",r.status_code==400,r.text)
r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"email":"kaputt"}); chk("Ungültige E-Mail wird abgelehnt",r.status_code==400)
r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"zweitfeld":"Bot"}); chk("Roboterfalle: scheinbar ok, aber kein Lead",r.status_code==200 and sql(f"select count(*) from leads where email='{mail}'")=="0",r.text)
r=pub.post(f"/api/public/funnel/{slug}",json=kam); chk("Anmeldung klappt und bietet Termin an",r.status_code==200 and r.json()["neu"] and r.json()["termin"],r.text)
time.sleep(1.2)
z=sql(f"select quelle||'|'||temperatur||'|'||(kampagne_id='{kid}')||'|'||coalesce(utm->>'utm_source','')||'|'||coalesce(utm->>'x','kein-x') from leads where email='{mail}'")
chk("Lead: Quelle, heiß, Kampagne, nur erlaubte UTM-Angaben",z=="website|heiss|true|meta|kein-x",z)
lid=sql(f"select id from leads where email='{mail}'")
chk("Einwilligung steht im Verlauf",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and art='consent' and inhalt like '%{slug[:5]}%' or lead_id='{lid}' and art='consent'") or 0)>=1)
chk("Aufgabe „innerhalb einer Stunde anrufen“ angelegt",int(sql(f"select count(*) from aufgaben where auto_schluessel like 'lead-funnel-{lid}-%'"))==1)
chk("Team bekommt eine Mail",any("Neuer Lead" in betreff(m) and "Funnel GmbH" in betreff(m) for m in mails()))
r=pub.post(f"/api/public/funnel/{slug}",json=kam); chk("Zweite Anmeldung derselben E-Mail ergänzt den Lead",r.status_code==200 and not r.json()["neu"] and sql(f"select count(*) from leads where email='{mail}'")=="1",r.text)
# ---------------------------------------------------------------- Auswertung
d=a.get("/api/admin/funnel").json(); k=[x for x in d["kampagnen"] if x["slug"]==slug][0]
chk("Auswertung: Aufrufe, Leads, Kosten pro Lead",k["aufrufe"]>=1 and k["leads"]==1 and k["kosten_pro_lead_cent"]==20000 and k["kosten_pro_kunde_cent"] is None,k)
chk("Feste Empfehlungsseite ist vorhanden, aber aus",any(x["slug"]=="empfehlung" and not x["aktiv"] and x["feste"] for x in d["kampagnen"]))
chk("Feste Seite lässt sich nicht löschen",a.delete(f"/api/admin/funnel/{[x for x in d['kampagnen'] if x['slug']=='empfehlung'][0]['id']}").status_code==400)
chk("Ohne Anmeldung kein Zugriff auf Funnel-Verwaltung",pub.get("/api/admin/funnel").status_code in (401,403))
# ---------------------------------------------------------------- Empfehlungsprogramm
KID,kc=neuer_kunde("Empf")
chk("Empfehlung ist ab Werk aus (Kunde sieht nichts)",kc.get("/api/kunde/empfehlung").json()=={"aktiv":False})
emp=[x for x in d["kampagnen"] if x["slug"]=="empfehlung"][0]
r=a.put("/api/admin/empfehlung",json={"aktiv":True,"beschreibung":"x"}); chk("Einschalten ohne geprüfte Seite wird abgelehnt",r.status_code==400,r.text)
ek={k2:emp[k2] for k2 in ("name","titel","untertitel","nutzen","button","einwilligung_text","danke_titel","danke_text","telefon_pflicht","website_abfragen","termin_anbieten","kosten_cent")}
r=a.put(f"/api/admin/funnel/{emp['id']}",json={**ek,"aktiv":True,"rechtlich_geprueft":True}); chk("Empfehlungsseite lässt sich nach Prüfung einschalten",r.status_code==200,r.text)
chk("Seite allein reicht nicht, solange das Programm aus ist",pub.get("/api/public/funnel/empfehlung").status_code==404 and kc.get("/api/kunde/empfehlung").json()=={"aktiv":False})
r=a.put("/api/admin/empfehlung",json={"aktiv":True,"beschreibung":"Als Dankeschön melden wir uns persönlich bei Ihnen."}); chk("Programm einschalten klappt",r.status_code==200,r.text)
e=kc.get("/api/kunde/empfehlung").json()
chk("Kunde bekommt persönlichen Link und Text",e["aktiv"] and len(e["code"])==8 and e["link"].endswith("/f/empfehlung?ref="+e["code"]) and "Dankeschön" in e["beschreibung"] and e["gesamt"]==0,e)
chk("Code bleibt gleich",kc.get("/api/kunde/empfehlung").json()["code"]==e["code"])
r=pub.post("/api/public/funnel/empfehlung",json={"name":"Erika Neu","firma":f"Empfohlen GmbH {sfx}","email":f"emp{sfx}@lead.de","telefon":"0511 55","einwilligung":True,"ref":e["code"].lower()}); chk("Anmeldung über den Link klappt",r.status_code==200,r.text)
z=sql(f"select quelle||'|'||(empfohlen_von='{KID}') from leads where email='emp{sfx}@lead.de'"); chk("Lead ist als Empfehlung des Kunden markiert",z=="empfehlung|true",z)
elid=sql(f"select id from leads where email='emp{sfx}@lead.de'")
chk("Prämienzeile ohne Betrag angelegt",sql(f"select status||'|'||coalesce(betrag_cent::text,'leer') from empfehlungs_praemien where lead_id='{elid}'")=="offen|leer")
pub.post("/api/public/funnel/empfehlung",json={"name":"Falsch Code","email":f"falsch{sfx}@lead.de","telefon":"0511 56","einwilligung":True,"ref":"ZZZZZZZZ"})
chk("Unbekannter Code: Lead ohne Empfehlung",sql(f"select quelle||'|'||coalesce(empfohlen_von::text,'-') from leads where email='falsch{sfx}@lead.de'")=="website|-")
e2=kc.get("/api/kunde/empfehlung").json(); chk("Kunde sieht die Zahl seiner Empfehlungen, keine Beträge",e2["gesamt"]==1 and e2["kunden"]==0 and "betrag" not in json.dumps(e2),e2)
li=a.get("/api/admin/empfehlung/liste").json()["eintraege"]; chk("Admin sieht die Empfehlung mit dem Kunden",any(x["lead_id"]==elid and x["geber_id"]==KID for x in li),li)
chk("Ungültiger Prämienstatus wird abgelehnt",a.put(f"/api/admin/empfehlung/{elid}",json={"status":"x"}).status_code==422)
r=a.put(f"/api/admin/empfehlung/{elid}",json={"status":"ausgezahlt","betrag_cent":5000,"notiz":"Gutschrift Oktober"}); chk("Prämie festlegen klappt",r.status_code==200 and sql(f"select status||'|'||betrag_cent from empfehlungs_praemien where lead_id='{elid}'")=="ausgezahlt|5000",r.text)
chk("Änderung steht im Protokoll",int(sql("select count(*) from audit_log where aktion='empfehlung_praemie'"))>=1)
a.put("/api/admin/empfehlung",json={"aktiv":False,"beschreibung":""}); chk("Programm ausschalten: Kunde sieht nichts, Link tot",kc.get("/api/kunde/empfehlung").json()=={"aktiv":False} and pub.get("/api/public/funnel/empfehlung").status_code==404)
# ---------------------------------------------------------------- Löschen und Bremse
r=a.delete(f"/api/admin/funnel/{kid}"); chk("Eigene Seite löschen klappt, Lead bleibt",r.status_code==200 and sql(f"select count(*) from leads where id='{lid}'")=="1" and sql(f"select coalesce(kampagne_id::text,'-') from leads where id='{lid}'")=="-")

# ---------------------------------------------------------------- Zeitraum, Roboter
slug2=f"zeit-{sfx}"; r=a.post("/api/admin/funnel",json={**basis,"slug":slug2,"aktiv":True,"rechtlich_geprueft":True}); k2=r.json()["id"]
pub.get(f"/api/public/funnel/{slug2}")
httpx.get(B+f"/api/public/funnel/{slug2}",headers={**H,"User-Agent":"Googlebot/2.1"})
httpx.get(B+f"/api/public/funnel/{slug2}",headers={**H,"User-Agent":"facebookexternalhit/1.1"})
httpx.get(B+f"/api/public/funnel/{slug2}",headers={**H,"User-Agent":"Mozilla/5.0 Safari"},cookies={"mk_session":a.cookies.get("mk_session")})
z=[x for x in a.get("/api/admin/funnel?tage=7").json()["kampagnen"] if x["slug"]==slug2][0]
chk("Aufrufe zählen weder Roboter noch angemeldete Besucher",z["aufrufe"]==1,z["aufrufe"])
sql(f"update lead_kampagnen_tage set tag=current_date-10 where kampagne_id='{k2}'")
sql(f"insert into lead_kampagnen_tage (kampagne_id,tag,aufrufe) values ('{k2}',current_date,3)")
z7=[x for x in a.get("/api/admin/funnel?tage=7").json()["kampagnen"] if x["slug"]==slug2][0]; z30=[x for x in a.get("/api/admin/funnel?tage=30").json()["kampagnen"] if x["slug"]==slug2][0]; z0=[x for x in a.get("/api/admin/funnel").json()["kampagnen"] if x["slug"]==slug2][0]
chk("Zeitraum 7 Tage: jüngere Aufrufe, Vergleich mit Zeit davor",z7["aufrufe"]==3 and z7["aufrufe_vorher"]==1,(z7["aufrufe"],z7["aufrufe_vorher"]))
chk("Zeitraum 30 Tage und „seit Start“ zählen alles",z30["aufrufe"]==4 and z0["aufrufe"]==4)
chk("Kosten pro Lead nur bei „seit Start“",all(x["kosten_pro_lead_cent"] is None for x in a.get("/api/admin/funnel?tage=7").json()["kampagnen"]))
chk("Ungültiger Zeitraum wird abgelehnt",a.get("/api/admin/funnel?tage=5").status_code==400)
st=[pub.post(f"/api/public/funnel/{slug}",json={**kam,"zweitfeld":"Bot"}).status_code for _ in range(25)]
chk("Zu viele Anmeldungen vom selben Anschluss werden gebremst",429 in st,st)
