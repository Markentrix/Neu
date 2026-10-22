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
sfx=str(int(time.time())+249)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import io, json, os, sys, base64, datetime
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)
ADM=sql("select email from benutzer where rolle='admin' and aktiv order by erstellt_am limit 1")
p=a.post("/api/admin/vertrieb/partner",json={"name":"Paul Plan","email":f"paul{sfx}@v.de"}).json(); pid=p["id"]
l=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"paul{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":l.split("token=")[1],"password":"PaulPasswort123456"})
v=httpx.Client(base_url=B,headers=H); v.post("/api/login",json={"email":f"paul{sfx}@v.de","password":"PaulPasswort123456"})
v.put("/api/me/ansicht",json={"tour_gesehen":True})
def lead(firma,**kw):
    r=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":kw.pop("telefon","0511 7000001"),"ort":"Celle","plz":kw.pop("plz","29221"),**kw}); assert r.status_code==200,r.text; return r.json()["id"]
heute=datetime.date.today()
# ---- 1: Wiedervorlagen und Löschfrist
L1=lead("Wv",email=f"wv{sfx}@x.de",telefon="0511 7000011")
sql(f"update leads set loeschen_nach=current_date+30 where id='{L1}'")
r=a.post(f"/api/admin/leads/{L1}/kontakt",json={"ergebnis":"anruf_erreicht"}); chk("erreicht: Wiedervorlage in 3 Tagen",r.status_code==200 and r.json()["wiedervorlage_am"]==str(heute+datetime.timedelta(days=3)),r.text)
chk("Aktivität verlängert die Löschfrist",sql(f"select loeschen_nach >= current_date+360 from leads where id='{L1}'")=="t")
r=a.post(f"/api/admin/leads/{L1}/kontakt",json={"ergebnis":"antwort"}); chk("geantwortet: Wiedervorlage in 2 Tagen",r.json()["wiedervorlage_am"]==str(heute+datetime.timedelta(days=2)),r.text)
r=a.post(f"/api/admin/leads/{L1}/kontakt",json={"ergebnis":"termin"}); chk("Termin: Wiedervorlage in 3 Tagen",r.json()["wiedervorlage_am"]==str(heute+datetime.timedelta(days=3)),r.text)
chk("Ergebnis-Code gespeichert",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{L1}' and ergebnis='anruf_erreicht'"))==1)
L2=lead("Alt",email=f"alt{sfx}@x.de",telefon="0511 7000012")
sql(f"update leads set status='angebot', letzter_kontakt_am=now()-interval '13 months', wiedervorlage_am=NULL where id='{L2}'")
jobs.fristen_ausfuehren(); chk("Angebot ohne Aktivität seit 12 Monaten wird abgelegt",sql(f"select status from leads where id='{L2}'")=="verloren")
# ---- 9: Verlustgrund
L3=lead("Absage",email=f"absage{sfx}@firma-absage{sfx}.de",telefon="0511 7000013",website=f"www.firma-absage{sfx}.de")
chk("Ungültiger Grund abgelehnt",a.post(f"/api/admin/leads/{L3}/kontakt",json={"ergebnis":"kein_interesse","verlust_grund":"quatsch"}).status_code==400)
r=a.post(f"/api/admin/leads/{L3}/kontakt",json={"ergebnis":"kein_interesse","verlust_grund":"zu_teuer"}); chk("Kein Interesse mit Grund",r.status_code==200 and sql(f"select status||'|'||verlust_grund||'|'||coalesce(wiedervorlage_am::text,'-') from leads where id='{L3}'")=="verloren|zu_teuer|-",r.text)
au=a.get("/api/admin/vertrieb/auswertung").json(); chk("Auswertung zeigt Verlustgründe",any(x["grund"]=="zu_teuer" for x in au["verlustgruende"]),au.get("verlustgruende"))
# ---- 3: Sperrliste
chk("Kein Interesse landet auf der Sperrliste (E-Mail, Telefon, Domain)",int(sql(f"select count(*) from sperrliste where grund='kein_interesse' and wert in ('absage{sfx}@firma-absage{sfx}.de','firma-absage{sfx}.de','495117000013')"))==3,sql("select art||wert from sperrliste order by id desc limit 6"))
r=a.post("/api/admin/leads",json={"firma":"Neu Absage","email":f"absage{sfx}@firma-absage{sfx}.de"}); chk("Admin kann gesperrten Kontakt nicht anlegen",r.status_code==409 and "kein Interesse" in r.json()["detail"],r.text)
r=v.post("/api/vertrieb/leads",json={"firma":"Andere Firma","website":f"https://firma-absage{sfx}.de/kontakt"}); chk("Vertriebler: gleiche Domain gesperrt",r.status_code==409,r.text)
csv=f"Firma,E-Mail,Telefon\nGesperrt GmbH,absage{sfx}@firma-absage{sfx}.de,\nImport Neu {sfx},imp{sfx}@imp{sfx}.de,0511 7000099\n"
imp=lambda **k: a.post("/api/admin/leads/import",json={"datei_base64":base64.b64encode(csv.encode()).decode(),"datei_name":"t.csv","liste":"T74","nur_pruefen":True,**k})
r=imp(); bl=r.json()["blaetter"][0]; chk("Import überspringt gesperrte Kontakte",r.status_code==200 and bl["gesperrt"]==1 and bl["neu"]==1,r.text)
r=imp(nur_pruefen=False,verteilen=True,grundlage="b2b_mutmasslich"); chk("Import mit Verteilung und Grundlage",r.status_code==200 and sql(f"select vertriebspartner_id is not null and ansprache_grundlage='b2b_mutmasslich' from leads where email='imp{sfx}@imp{sfx}.de'")=="t",r.text)
chk("Import: ungültige Grundlage",imp(grundlage="egal").status_code==400)
L4=lead("Widerspruch",email=f"wid{sfx}@w{sfx}.de",telefon="0511 7000014")
r=a.post(f"/api/admin/leads/{L4}/kontakt",json={"ergebnis":"widerspruch"}); chk("Widerspruch: gesperrt und Sperrliste",sql(f"select status from leads where id='{L4}'")=="gesperrt" and int(sql(f"select count(*) from sperrliste where grund='widerspruch' and wert='wid{sfx}@w{sfx}.de'"))==1,r.text)
r=a.post("/api/admin/vertrieb/sperrliste",json={"email":f"hand{sfx}@h{sfx}.de","grund":"manuell"}); chk("Sperrliste von Hand ergänzen",r.status_code==200 and r.json()["neu"]==1,r.text)
sl=a.get(f"/api/admin/vertrieb/sperrliste?q=hand{sfx}").json(); chk("Sperrliste lesen",len(sl)>=1)
chk("Sperrliste: Kunde/Vertriebler darf nicht",v.get("/api/admin/vertrieb/sperrliste").status_code in (401,403))
chk("Sperrliste löschen",a.delete(f"/api/admin/vertrieb/sperrliste/{sl[0]['id']}").status_code==200)
chk("Sperrliste ohne Angabe abgelehnt",a.post("/api/admin/vertrieb/sperrliste",json={"grund":"manuell"}).status_code==400)
# ---- 8: Vertriebler ergänzt Daten, Dubletten
V1=v.post("/api/vertrieb/leads",json={"firma":f"Eigen {sfx}","plz":"29221","ansprache_grundlage":"empfehlung"}).json()["id"]
r=v.post("/api/vertrieb/leads",json={"firma":f"Eigen {sfx}","plz":"29221"}); chk("Dublette in eigener Liste",r.status_code==409 and "deiner Liste" in r.json()["detail"],r.text)
r=v.post("/api/vertrieb/leads",json={"firma":"X","ansprache_grundlage":"quatsch"}); chk("Ungültige Grundlage",r.status_code==400)
r=v.patch(f"/api/vertrieb/leads/{V1}",json={"email":f"eigen{sfx}@e.de","ansprechpartner":"Frau Eigen"}); chk("Vertriebler ergänzt Kontaktdaten",r.status_code==200 and sql(f"select email from leads where id='{V1}'")==f"eigen{sfx}@e.de",r.text)
chk("… im Verlauf vermerkt",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{V1}' and inhalt like 'Angaben ergänzt%'"))==1)
chk("Ungültige E-Mail abgelehnt",v.patch(f"/api/vertrieb/leads/{V1}",json={"email":"keine"}).status_code==400)
chk("Gesperrte E-Mail abgelehnt",v.patch(f"/api/vertrieb/leads/{V1}",json={"email":f"absage{sfx}@firma-absage{sfx}.de"}).status_code==409)
L5=lead("Fremd",email=f"fremd{sfx}@f.de",telefon="0511 7000015",plz="29225",vertriebspartner_id=None)
r=v.post("/api/vertrieb/leads",json={"firma":f"Fremd {sfx}","plz":"29225"}); chk("Dublette bei fremdem Lead ohne Namen des Kollegen",r.status_code==409 and "bereits erfasst" in r.json()["detail"],r.text)
d=v.get(f"/api/vertrieb/leads/{V1}").json(); chk("Lead-Detail: Verlustgründe und Check-Feld","verlustgruende" in d and "check" in d)
r=v.post(f"/api/vertrieb/leads/{V1}/status",json={"status":"verloren","verlust_grund":"hat_anbieter"}); chk("Vertriebler: verloren mit Grund",r.status_code==200 and sql(f"select verlust_grund from leads where id='{V1}'")=="hat_anbieter",r.text)
# ---- 10: Zuweisung mit Push, Filter
L6=lead("Zuw",email=f"zuw{sfx}@z.de",telefon="0511 7000016")
chk("Zuweisung ändern",a.patch(f"/api/admin/leads/{L6}",json={"vertriebspartner_id":pid}).status_code==200 and sql(f"select vertriebspartner_id from leads where id='{L6}'")==pid)
sql(f"update leads set wiedervorlage_am=current_date-2, status='antwort' where id='{L6}'")
r=a.get("/api/admin/leads?fokus=ueberfaellig").json(); chk("Filter: überfällig",any(x["id"]==L6 for x in r["leads"]) and all(x["wiedervorlage_am"] and x["wiedervorlage_am"]<str(heute) for x in r["leads"]),r["gesamt"])
# ---- 2: Eingehende Anfragen
sec=a.post("/api/admin/website-check/schluessel",json={}).json()["schluessel"]; S={"X-MK":"1","X-Lead-Secret":sec}; U=B+"/api/public/kontakt-lead"
em=f"anfrage{sfx}@kunde{sfx}.de"
r=httpx.post(U,headers=S,json={"email":em,"name":"Anna Anfrage","firma":f"Anfrage {sfx}","einwilligung":True,"nachricht":"Bitte melden"}); chk("Kontaktformular",r.status_code==200 and r.json()["neu"],r.text)
chk("… ohne Auto-Zuweisung bleibt der Lead frei, Grundlage = Anfrage",sql(f"select coalesce(vertriebspartner_id::text,'-')||'|'||ansprache_grundlage from leads where email='{em}'")=="-|anfrage")
chk("… Team bekommt eine Mail",bool(mail_an(ADM,f"Neue Anfrage: Anfrage {sfx}")))
r=a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":True,"reaktionsstunden":2,"preise_sichtbar":False}); chk("Auto-Zuweisung einschalten",r.status_code==200)
em2=f"auto{sfx}@kunde{sfx}.de"
httpx.post(U,headers=S,json={"email":em2,"name":"Auto Matik","firma":f"Auto {sfx}","einwilligung":True})
chk("Auto-Zuweisung weist zu",sql(f"select vertriebspartner_id is not null from leads where email='{em2}'")=="t" and int(sql(f"select count(*) from lead_aktivitaeten a join leads l on l.id=a.lead_id where l.email='{em2}' and a.inhalt like 'Automatisch%'"))==1)
a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":False,"reaktionsstunden":2,"preise_sichtbar":False})
sql(f"update leads set status='verloren', wiedervorlage_am=NULL where email='{em}'")
httpx.post(U,headers=S,json={"email":em,"name":"Anna Anfrage","firma":f"Anfrage {sfx}","einwilligung":True})
chk("Erneute Anfrage belebt verlorenen Lead",sql(f"select status||'|'||wiedervorlage_am::text from leads where email='{em}'")==f"antwort|{heute}")
sql(f"update leads set erstellt_am=now()-interval '5 hours', letzter_kontakt_am=NULL, status='neu', temperatur='heiss' where email='{em}'")
jobs.anfragen_eskalation(cfg()); jobs.anfragen_eskalation(cfg())
chk("Eskalation einmal je Anfrage",int(sql(f"select count(*) from job_marker where schluessel like 'eskalation-%' and schluessel in (select 'eskalation-'||id from leads where email='{em}')"))==1)
# Absage eines Gesprächs
LT=lead("Abs",email=f"abs{sfx}@x.de",telefon="0511 7000017",vertriebspartner_id=pid)
sql(f"update leads set status='termin' where id='{LT}'")
sql(f"insert into gespraechstermine (start,ende,name,email,lead_id,token) values (now()+interval '3 days',now()+interval '3 days 30 minutes','Abs','abs{sfx}@x.de','{LT}','tokabsage{sfx}1234')")
r=httpx.post(B+"/api/public/buchung/absagen",headers=H,data={"t":f"tokabsage{sfx}1234"}); chk("Absage setzt Lead zurück",sql(f"select status||'|'||wiedervorlage_am::text from leads where id='{LT}'")==f"antwort|{heute}",r.text[-200:])
# ---- 6/4: Angebot, telefonische Annahme, Ablehnungsgrund
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","kleinunternehmer":True,"mwst_satz":19})
pos=[{"text":"BUSINESS – monatlich","menge":1,"einheit":"Monat","preis_cent":19900},{"text":"Einrichtung BUSINESS","menge":1,"einheit":"","preis_cent":50000}]
LA=lead("Ang",email=f"ang{sfx}@a.de",telefon="0511 7000018",ansprechpartner="Herr Ang",vertriebspartner_id=pid)
def angebot(lid):
    bid=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"Angebot","einleitung":"Hallo","schluss":"Danke","positionen":pos,"leistungen":[]}).json()["id"]
    s=a.post(f"/api/admin/leads/{lid}/angebote/{bid}/senden",json={"gueltig_tage":30}); assert s.status_code==200,s.text; return bid,s.json()["link"].split("t=")[1]
bid,tok=angebot(LA)
chk("Nach Angebot: Wiedervorlage in 4 Tagen",sql(f"select wiedervorlage_am::text from leads where id='{LA}'")==str(heute+datetime.timedelta(days=4)))
r=a.post(f"/api/admin/belege/{bid}/angebot-status",json={"status":"angenommen"}); chk("Telefonische Annahme",r.status_code==200,r.text)
chk("… Verlauf, Aufgabe und Wiedervorlage heute",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{LA}' and inhalt like '%angenommen%'"))==1 and int(sql(f"select count(*) from aufgaben where titel like 'Angebot angenommen: Kunde anlegen (Ang {sfx}%'"))==1 and sql(f"select wiedervorlage_am::text from leads where id='{LA}'")==str(heute))
chk("… Bestätigungsmail an den Kunden",bool(mail_an(f"ang{sfx}@a.de","so geht es weiter")))
LB=lead("Abl",email=f"abl{sfx}@a.de",telefon="0511 7000019",vertriebspartner_id=pid)
bidb,tokb=angebot(LB)
r=httpx.post(B+f"/api/angebot/{tokb}/ablehnen",headers=H,json={"grund":"","grund_code":"zu_teuer"}); chk("Ablehnung mit Grund",r.status_code==200 and int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{LB}' and inhalt like '%Grund: Zu teuer%'"))==1 and sql(f"select status from leads where id='{LB}'")=="antwort",r.text)
LC=lead("Nachf",email=f"nachf{sfx}@a.de",telefon="0511 7000020",vertriebspartner_id=pid)
bidc,_t=angebot(LC)
sql(f"update belege set versendet_am=now()-interval '6 days' where id='{bidc}'")
jobs.aufgaben_automatisch(cfg()); chk("Aufgabe: Angebot nachfassen",int(sql(f"select count(*) from aufgaben where auto_schluessel='angebotnachfassen-{bidc}'"))==1)
# ---- 4: Assistent Kunde aus Angebot
vs=a.get(f"/api/admin/leads/{LA}/zu-kunde-vorschlag").json(); chk("Assistent schlägt Paket vor",vs["vorschlag"] and vs["angebot"] and len(vs["pakete"])>3,vs)
r=a.post(f"/api/admin/leads/{LA}/zu-kunde",json={"paket_code":vs["vorschlag"],"einladen":True,"beginn":str(heute)}); chk("Kunde + Buchung + Einladung",r.status_code==200 and r.json()["buchung_id"] and r.json()["einladungslink"],r.text)
kn=r.json()["id"]
chk("… Buchung beauftragt, Module aktiv, Onboarding angelegt, Vertriebler übernommen",sql(f"select count(*) from buchungen where kunden_id='{kn}' and status='beauftragt'")=="1" and int(sql(f"select count(*) from kunden_module where kunden_id='{kn}' and aktiv"))>0 and int(sql(f"select count(*) from onboarding_punkte where kunden_id='{kn}'"))>0 and sql(f"select vertriebspartner_id from kunden where id='{kn}'")==pid)
r=a.post(f"/api/admin/leads/{L1}/zu-kunde",json={"einladen":True}); chk("Einladen ohne E-Mail",r.status_code in (200,400))
sql(f"update kunden set erstellt_am=now()-interval '5 days' where id='{kn}'"); sql(f"update buchungen set status='gekuendigt' where kunden_id='{kn}'")
jobs.aufgaben_automatisch(cfg()); chk("Warnung: Kunde mit Vertriebler ohne Buchung",int(sql(f"select count(*) from aufgaben where titel like 'Keine Buchung, keine Provision:%' and kunden_id='{kn}'"))==1)
# ---- 5: Termine durch den Vertriebler, Erinnerungen
a.put("/api/admin/einstellungen/buchung",json={"aktiv":True,"dauer":30,"tage":14,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":1,"ort":"Telefon"})
LV=lead("Term",email=f"term{sfx}@t.de",telefon="0511 7000021",ansprechpartner="Herr Term",vertriebspartner_id=pid)
sl=v.get(f"/api/vertrieb/leads/{LV}/slots").json(); chk("Vertriebler sieht freie Termine",sl["aktiv"] and len(sl["tage"])>0)
st=sl["tage"][-1]["slots"][0]["start"]
chk("Ohne Zustimmung kein Termin",v.post(f"/api/vertrieb/leads/{LV}/termin",json={"start":st}).status_code==400)
r=v.post(f"/api/vertrieb/leads/{LV}/termin",json={"start":st,"zugestimmt":True}); chk("Termin gebucht",r.status_code==200,r.text)
chk("… Lead steht auf Termin, Mail geht raus",sql(f"select status from leads where id='{LV}'")=="termin" and bool(mail_an(f"term{sfx}@t.de","Ihr Gespräch")))
LV2=lead("Term2",email=f"term2{sfx}@t.de",telefon="0511 7000022",vertriebspartner_id=pid)
chk("Derselbe Slot ist weg",v.post(f"/api/vertrieb/leads/{LV2}/termin",json={"start":st,"zugestimmt":True}).status_code==409)
LV3=lead("Term3",telefon="0511 7000023",vertriebspartner_id=pid)
chk("Ohne E-Mail kein Termin",v.post(f"/api/vertrieb/leads/{LV3}/termin",json={"start":st,"zugestimmt":True}).status_code in (400,409))
chk("Fremder Lead: nicht erreichbar",v.get(f"/api/vertrieb/leads/{L5}/slots").status_code==404)
chk("Buchungslink",v.get("/api/vertrieb/buchungslink").json()["link"].endswith("/buchen"))
sql(f"update gespraechstermine set start=now()+interval '23 hours 30 minutes', ende=now()+interval '24 hours' where lead_id='{LV}' and status='gebucht'")
jobs.gespraech_erinnerungen(cfg()); n1=len(mail_an(f"term{sfx}@t.de","Erinnerung")); jobs.gespraech_erinnerungen(cfg())
chk("Erinnerung 24 Stunden vorher (nur einmal)",n1==1 and len(mail_an(f"term{sfx}@t.de","Erinnerung"))==1,n1)
sql(f"update gespraechstermine set start=now()+interval '90 minutes', ende=now()+interval '2 hours' where lead_id='{LV}' and status='gebucht'")
jobs.gespraech_erinnerungen(cfg()); chk("Erinnerung 2 Stunden vorher",len(mail_an(f"term{sfx}@t.de","Erinnerung"))==2)
sql(f"update gespraechstermine set start=now()-interval '2 hours', ende=now()-interval '90 minutes' where lead_id='{LV}' and status='gebucht'")
jobs.aufgaben_automatisch(cfg()); chk("Aufgabe nach dem Gespräch",int(sql("select count(*) from aufgaben where titel like 'Gespräch-Ergebnis festhalten: Herr Term%' or titel like 'Gespräch-Ergebnis festhalten: %Term%'"))>=1)
# ---- 7/9: Zahlen, Preise
v.post(f"/api/vertrieb/leads/{LV}/kontakt",json={"ergebnis":"anruf_erreicht"})
z=v.get("/api/vertrieb/zahlen").json(); chk("Zahlen zählen über den Ergebnis-Code",z["erreicht_woche"]>=1 and "provision" in z,z)
pk=v.get("/api/vertrieb/pakete").json(); chk("Pakete ohne Preise (Standard)",pk and "monatlich_cent" not in pk[0])
a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":False,"reaktionsstunden":4,"preise_sichtbar":True})
pk=v.get("/api/vertrieb/pakete").json(); chk("Pakete mit Preisen, wenn freigegeben",pk and "monatlich_cent" in pk[0])
a.put("/api/admin/vertrieb/steuerung",json={"auto_zuweisung":False,"reaktionsstunden":4,"preise_sichtbar":False})
jobs.provisionsvorschau(cfg()); chk("Provisionsvorschau läuft ohne Fehler",True)
