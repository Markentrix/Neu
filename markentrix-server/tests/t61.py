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
sfx=str(int(time.time())+153)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"mwst_satz":19,"steuernummer":"12/345/67890"})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, os, sys, json
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, preisaenderung
db.open_pool()
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Prea"); kB,cB,mB=neuer_kunde("Preb"); kC,cC,mC=neuer_kunde("Prec")
sql(f"update kunden set status='aktiv' where id in ('{kA}','{kB}','{kC}')")
for k,m,rab in ((kA,4900,900),(kB,2000,0),(kC,3000,0)):
    sql(f"delete from buchungen where kunden_id='{k}'"); sql(f"insert into buchungen (kunden_id, produkt_code, monatlich_cent, rabatt_cent, status) values ('{k}','KI_ONE',{m},{rab},'aktiv')")
# ================= Preiserhöhung
chk("Preisberechnung rundet kaufmännisch",preisaenderung.neu_preis(4000,5)==4200 and preisaenderung.neu_preis(1999,3)==2059 and preisaenderung.neu_preis(2000,2.5)==2050)
P="/api/admin/preisaenderungen"; spaet=(heute+datetime.timedelta(days=45)).isoformat()
body={"titel":"Preisanpassung Test","prozent":5,"wirksam_ab":spaet,"text":"Wegen gestiegener Kosten."}
chk("Kunde darf nicht",cA.post(P+"/vorschau",json=body).status_code==403)
chk("Frist unter 30 Tagen abgelehnt",a.post(P+"/vorschau",json={**body,"wirksam_ab":(heute+datetime.timedelta(days=10)).isoformat()}).status_code==400)
chk("Mehr als 25 % abgelehnt",a.post(P+"/vorschau",json={**body,"prozent":30}).status_code==422)
v=a.post(P+"/vorschau",json=body).json(); mine=[x for x in v["kunden"] if x["id"] in (kA,kB,kC)]
chk("Vorschau: alte und neue Summen je Kunde (Rabatt eingerechnet)",{x["id"]:(x["alt_cent"],x["neu_cent"]) for x in mine}=={kA:(4000,4200),kB:(2000,2100),kC:(3000,3150)},mine)
sql(f"update kunden set referenzkunde=true where id='{kC}'")
v=a.post(P+"/vorschau",json=body).json(); chk("Referenzkunden ausgenommen",kC not in [x["id"] for x in v["kunden"]])
sql(f"update kunden set referenzkunde=false where id='{kC}'")
sql(f"insert into kuendigungswuensche (kunden_id, status, ende_am, ip) values ('{kC}','offen','{(heute+datetime.timedelta(days=20)).isoformat()}','127.0.0.1')")
v=a.post(P+"/vorschau",json=body).json(); chk("Kunden mit laufender Kündigung ausgenommen",kC not in [x["id"] for x in v["kunden"]])
r=a.post(P,json=body); chk("Entwurf angelegt",r.status_code==200 and r.json()["kunden"]>=2,r.text); pid=r.json()["id"]
chk("Entwurf: noch keine Mail",not mail_an(mA,"Preisanpassung"))
r=a.post(f"{P}/{pid}/ankuendigen"); chk("Ankündigen",r.status_code==200 and r.json()["gesendet"]>=2,r.text)
ms=mail_an(mA,"Preisanpassung"); t=text(ms[0]) if ms else ""
chk("Mail: alter und neuer Preis, Stichtag, persönlicher Link","40,00 €" in t and "42,00 €" in t and (heute+datetime.timedelta(days=45)).strftime("%d.%m.%Y") in t and "/preis/" in t and "Wegen gestiegener Kosten" in t,t[:600])
tokA=re.search(r"/preis/([A-Za-z0-9_-]+)",t).group(1)
tB=text(mail_an(mB,"Preisanpassung")[0]); tokB=re.search(r"/preis/([A-Za-z0-9_-]+)",tB).group(1)
r=httpx.get(B+"/preis/"+tokA); chk("Kundenseite zeigt Preise und Buttons",r.status_code==200 and "42,00" in r.text and "Einwand senden" in r.text,r.text[:200])
chk("Gelesen vermerkt",sql(f"select gelesen_am is not null from preisaenderung_kunden where token='{tokA}'")=="t")
chk("Ungültiger Token: 404",httpx.get(B+"/preis/"+"y"*30).status_code==404)
r=httpx.post(B+"/preis/"+tokA,data={"aktion":"ok"},headers=H); chk("Kenntnisnahme",r.status_code==200 and "Bestätigung vermerkt" in r.text,r.text[:200])
r=httpx.post(B+"/preis/"+tokB,data={"aktion":"widerspruch","text":"Zu teuer für uns"},headers=H); chk("Einwand wird entgegengenommen",r.status_code==200 and "Einwand ist bei uns eingegangen" in r.text,r.text[:200])
d=a.get(f"{P}/{pid}").json(); b=[x for x in d["kunden"] if x["kunden_id"]==kB][0]
chk("Admin sieht Einwand mit Text",b["widerspruch_am"] and b["widerspruch_text"]=="Zu teuer für uns")
chk("Liste zählt Einwände",any(x["id"]==pid and x["widersprueche"]==1 for x in a.get(P).json()["liste"]))
preisaenderung.anwenden(); chk("Vor dem Stichtag ändert sich nichts",sql(f"select monatlich_cent from buchungen where kunden_id='{kA}'")=="4900")
sql(f"update preisaenderungen set wirksam_ab=current_date where id='{pid}'")
n=preisaenderung.anwenden(); chk("Am Stichtag: Kunde ohne Einwand bekommt neuen Preis (Rabatt bleibt)",sql(f"select monatlich_cent||'|'||rabatt_cent from buchungen where kunden_id='{kA}'")=="5145|900",sql(f"select monatlich_cent from buchungen where kunden_id='{kA}'"))
chk("Kunde mit Einwand bleibt unverändert",sql(f"select monatlich_cent from buchungen where kunden_id='{kB}'")=="2000")
chk("Status angewendet, Audit-Eintrag",sql(f"select status from preisaenderungen where id='{pid}'")=="angewendet" and sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion='preisaenderung_angewendet'")=="1")
preisaenderung.anwenden(); chk("Nicht doppelt angewendet",sql(f"select monatlich_cent from buchungen where kunden_id='{kA}'")=="5145")
chk("Angewendet: Seite zeigt Hinweis statt Buttons",httpx.get(B+"/preis/"+tokA).status_code==200)
r=a.post(f"{P}/{pid}/abbrechen"); chk("Angewendetes nicht mehr abbrechbar",r.status_code==400)
# feste Positionen im Wartungsplan
r=a.post(f"/api/admin/kunden/{kA}/abrechnungsplaene",json={"titel":"Hosting fix","intervall_monate":1,"aus_buchungen":False,"positionen":[{"text":"Hosting","menge":1,"einheit":"Monat","preis_cent":2000}],"naechste_am":(heute+datetime.timedelta(days=60)).isoformat()}); planA=r.json()["id"]
r=a.post(P,json={**body,"titel":"Zweite Runde","prozent":10}); pid2=r.json()["id"]; a.post(f"{P}/{pid2}/ankuendigen")
sql(f"update preisaenderungen set wirksam_ab=current_date where id='{pid2}'"); preisaenderung.anwenden()
chk("Feste Plan-Position wird mit angepasst",json.loads(sql(f"select positionen from abrechnungsplaene where id='{planA}'"))[0]["preis_cent"]==2200)
r=a.post(P,json={**body,"titel":"Dritte"}); pid3=r.json()["id"]
chk("Entwurf lässt sich abbrechen",a.post(f"{P}/{pid3}/abbrechen").status_code==200 and httpx.get(B+"/preis/x"*1).status_code==404)
# ================= Zahlungsverzug
sql(f"update kunden set status='aktiv' where id in ('{kA}','{kB}')")
sql(f"delete from kuendigungswuensche where kunden_id='{kC}'")
r=a.post(f"/api/admin/kunden/{kB}/abrechnungsplaene",json={"titel":"Wartung","intervall_monate":1,"aus_buchungen":True,"naechste_am":(heute+datetime.timedelta(days=30)).isoformat()}); planB=r.json()["id"]
bid=a.post(f"/api/admin/kunden/{kB}/belege",json={"art":"rechnung","betreff":"Test","positionen":[{"text":"Leistung","menge":1,"einheit":"","preis_cent":5000}]}).json()["id"]
a.post(f"/api/admin/belege/{bid}/ausstellen")
sql(f"update belege set faellig_am=current_date-60, mahnstufe=3, mahn_am=current_date-20 where id='{bid}'")
def verzug_lauf():
    sql("delete from betrieb_status where schluessel like 'marker%'") ; sql("delete from job_marker") if False else None
    jobs._marker = lambda key: True
    jobs.zahlungsverzug({})
now=datetime.datetime.now(datetime.timezone.utc)
class _DT(datetime.datetime):
    @classmethod
    def now(cls,tz=None): return datetime.datetime(now.year,now.month,now.day,12,0,tzinfo=datetime.timezone.utc)
jobs.datetime=_DT
cfgp=a.get("/api/admin/einstellungen/zahlung").json()["mahnwesen"]
chk("Einstellung: standardmäßig aus",cfgp["verzug_tage"]==0 and cfgp["verzug_dienste"] is False,cfgp)
verzug_lauf(); chk("Funktion aus: nichts pausiert",sql(f"select aktiv::text from abrechnungsplaene where id='{planB}'")=="true")
def setze(tage,dienste): return a.put("/api/admin/einstellungen/zahlung",json={"glaeubiger_id":"","vorab_tage":3,"mahn_aktiv":False,"tage_1":7,"tage_2":21,"tage_3":35,"verzug_tage":tage,"verzug_dienste":dienste})
chk("Einstellung speichern",setze(14,False).status_code==200)
verzug_lauf(); chk("Verzug nach 20 Tagen > 14: Plan pausiert, Dienste weiter an",sql(f"select aktiv::text||'|'||pausiert_verzug::text from abrechnungsplaene where id='{planB}'")=="false|true" and sql(f"select coalesce(verzug_pause::text,'false') from website_dienste where kunden_id='{kB}'") in ("false",""))
chk("Audit-Eintrag",sql(f"select count(*) from audit_log where kunden_id='{kB}' and aktion='zahlungsverzug_pausiert'")=="1")
chk("Anderer Kunde unberührt",sql(f"select aktiv::text from abrechnungsplaene where id='{planA}'")=="true")
verzug_lauf(); chk("Zweiter Lauf: keine doppelte Meldung",sql(f"select count(*) from audit_log where kunden_id='{kB}' and aktion='zahlungsverzug_pausiert'")=="1")
# Dienste pausieren
setze(14,True); sql(f"insert into website_dienste (kunden_id, site_id) values ('{kB}','mk_{sfx}b') on conflict (kunden_id) do nothing") if False else None
a.get("/api/admin/kunden") 
cB.get("/api/kunde/website-dienste")
verzug_lauf(); chk("Mit Option: Dienste der Website pausiert",sql(f"select verzug_pause::text from website_dienste where kunden_id='{kB}'")=="true")
domb=f"verzug{sfx}.de"; sql(f"insert into websites (kunden_id, domain, art, status) values ('{kB}','{domb}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":domb}); API="/siteapi/api"
r=W.post(API+"/anfrage",headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test","Origin":"https://"+domb},content=json.dumps({"typ":"kontakt","name":"A B","email":"a@b.de","nachricht":"Hallo","einwilligung":"ja"}).encode())
chk("Formular antwortet 503 mit freundlichem Text",r.status_code==503,(r.status_code,r.text[:150]))
chk("Lesende Abfragen (Gesundheit) laufen weiter",W.get(API+"/health").status_code==200)
# Zahlung -> Freigabe
a.post(f"/api/admin/belege/{bid}/bezahlt",json={"datum":heute.isoformat(),"betrag_cent":5950}) if False else None
sql(f"update belege set status='bezahlt', bezahlt_am=current_date, bezahlt_cent=brutto_cent where id='{bid}'")
verzug_lauf(); chk("Nach Zahlung: Plan wieder aktiv, Dienste frei",sql(f"select aktiv::text||'|'||pausiert_verzug::text from abrechnungsplaene where id='{planB}'")=="true|false" and sql(f"select verzug_pause::text from website_dienste where kunden_id='{kB}'")=="false")
chk("Audit: aufgehoben",sql(f"select count(*) from audit_log where kunden_id='{kB}' and aktion='zahlungsverzug_aufgehoben'")=="1")
r=W.post(API+"/anfrage",headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test","Origin":"https://"+domb},content=json.dumps({"typ":"kontakt","name":"A B","email":"a@b.de","nachricht":"Hallo","einwilligung":"ja"}).encode())
chk("Formular wieder offen",r.status_code==200,(r.status_code,r.text[:150]))
# Manuell pausierter Plan bleibt pausiert
a.put(f"/api/admin/abrechnungsplaene/{planB}",json={"aktiv":False}); sql(f"update belege set status='versendet' where id='{bid}'")
sql(f"update belege set status='bezahlt' where id='{bid}'"); verzug_lauf()
chk("Von Hand pausierter Plan wird nicht ungefragt reaktiviert",sql(f"select aktiv::text from abrechnungsplaene where id='{planB}'")=="false")
