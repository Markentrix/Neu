"""Frei anlegbare Katalog-Pakete: anlegen, im Kundenportal/Angebot sichtbar, Module, Preis, ausblenden, löschen."""
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
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time()))
name=f"Website plus Google-Anzeige {sfx}"
chk("Ohne Preis abgelehnt",a.post("/api/admin/pakete",json={"name":name}).status_code==400)
chk("Unbekanntes Modul abgelehnt",a.post("/api/admin/pakete",json={"name":name,"monatlich_cent":14900,"module":["gibtsnicht"]}).status_code==400)
mods=a.get("/api/admin/pakete").json()["module"]; mc=mods[0]["code"]
r=a.post("/api/admin/pakete",json={"name":name,"beschreibung":"Website mit einer Google-Anzeige pro Monat","monatlich_cent":14900,"einrichtung_cent":9900,"abrechnung":"monatlich","laufzeit_monate":12,"leistungen":["1 Google-Anzeige pro Monat","Monatsbericht"],"module":[mc]})
chk("Paket angelegt",r.status_code==200 and r.json()["code"].startswith("EIGEN_"),r.text); code=r.json()["code"]
chk("Gleicher Name bekommt anderen Code",a.post("/api/admin/pakete",json={"name":name,"monatlich_cent":100}).json()["code"]!=code)
l=[p for p in a.get("/api/admin/pakete").json()["pakete"] if p["code"]==code][0]
chk("Preis, Module, Leistungen gespeichert",l["monatlich_cent"]==14900 and l["einrichtung_cent"]==9900 and l["module"]==[mc] and l["leistungen"]==["1 Google-Anzeige pro Monat","Monatsbericht"] and l["eigen"],l)
chk("Im Angebot wählbar (Leistungstexte)",code in [p["code"] for p in a.get("/api/admin/katalog/leistungstexte").json()])
chk("In der Preisliste (aktuelle Preise)",code in [p["code"] for p in a.get("/api/admin/preise").json()["aktuell"]])
# Kunde sieht es
k=a.post("/api/admin/kunden",json={"firma":f"Paketkunde {sfx}","ansprechpartner":"Tina Test","email":f"pk{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"pk{sfx}@k.de"),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); c.post("/api/login",json={"email":f"pk{sfx}@k.de","password":"InhaberPasswort1"})
kat=c.get("/api/kunde/paketkatalog").json(); alle={p["code"]:p for g in kat["gruppen"] for p in g["produkte"]}
chk("Kunde sieht das Paket mit Preis",code in alle and alle[code]["monatlich_cent"]==14900 and alle[code]["einrichtung_cent"]==9900,alle.get(code))
chk("Eigene Gruppe „Kombi-Pakete“",any(g["kategorie"]=="kombi" and g["titel"]=="Kombi-Pakete" for g in kat["gruppen"]))
r=c.post(f"/api/kunde/pakete/{code}/dazubuchen",json={"bestaetigt":True}); chk("Kunde kann es dazubuchen (angefragt)",r.status_code==200,r.text)
chk("Buchung mit eingefrorenem Preis",sql(f"select monatlich_cent from buchungen where kunden_id='{k['id']}' and produkt_code='{code}'")=="14900")
chk("Gebuchtes Paket nicht löschbar",a.delete(f"/api/admin/pakete/{code}").status_code==409)
# Preisänderung wirkt neu, Buchung bleibt
a.post("/api/admin/preise",json={"produkt_code":code,"gueltig_ab":"2099-01-01","monatlich_cent":19900})
chk("Bestehende Buchung behält den Preis",sql(f"select monatlich_cent from buchungen where kunden_id='{k['id']}' and produkt_code='{code}'")=="14900")
# Ändern, ausblenden
r=a.put(f"/api/admin/pakete/{code}",json={"leistungen":["Neu 1"],"module":[]}); chk("Ändern",r.status_code==200,r.text)
l=[p for p in a.get("/api/admin/pakete").json()["pakete"] if p["code"]==code][0]; chk("Änderung gespeichert",l["leistungen"]==["Neu 1"] and l["module"]==[],l)
a.put(f"/api/admin/pakete/{code}",json={"aktiv":False})
alle={p["code"] for g in c.get("/api/kunde/paketkatalog").json()["gruppen"] for p in g["produkte"]}
chk("Ausgeblendet: nicht mehr im Kundenportal",code not in alle)
# Feste Pakete geschützt
chk("Festes Paket nicht löschbar",a.delete("/api/admin/pakete/KI_ONE").status_code==400)
chk("Festes Paket: Name nicht änderbar",a.put("/api/admin/pakete/KI_ONE",json={"name":"Xyz"}).status_code==400)
chk("Festes Paket: Leistungen änderbar",a.put("/api/admin/pakete/KI_ONE",json={"leistungen":["A"]}).status_code==200)
# Ungebuchtes Paket löschen
r=a.post("/api/admin/pakete",json={"name":f"Probe {sfx}","nur_auf_anfrage":True}); c2=r.json()["code"]
chk("Nur auf Anfrage ohne Preis möglich",r.status_code==200 and sql(f"select count(*) from produkt_preise where produkt_code='{c2}'")=="0",r.text)
chk("Ungebuchtes Paket löschen",a.delete(f"/api/admin/pakete/{c2}").status_code==200 and sql(f"select count(*) from produkte where code='{c2}'")=="0")

# ================= Staffelpreise (Monat 1: 149, Monat 2: 199, ab Monat 3: 249)
import datetime, os, sys
sys.dont_write_bytecode=True
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import abo, db, staffel
db.open_pool()
ST=[{"ab_monat":1,"cent":14900},{"ab_monat":2,"cent":19900},{"ab_monat":3,"cent":24900}]
chk("Staffel: Preis je Vertragsmonat",[staffel.preis_im_monat(ST,24900,m) for m in (1,2,3,4,12)]==[14900,19900,24900,24900,24900])
chk("Staffel: Text",staffel.text(ST)=="Monat 1: 149,00 €, Monat 2: 199,00 €, ab Monat 3: 249,00 €",staffel.text(ST))
chk("Staffel: Vertragsmonat zählt ab Beginn",staffel.monat_nr(datetime.date(2026,11,20),datetime.date(2026,11,1))==1 and staffel.monat_nr(datetime.date(2026,11,20),datetime.date(2027,1,1))==3)
SQLST="jsonb_build_array(jsonb_build_object('ab_monat',1,'cent',14900),jsonb_build_object('ab_monat',2,'cent',19900),jsonb_build_object('ab_monat',3,'cent',24900))"
chk("SQL-Funktion gleich Python",[sql(f"select mk_monatspreis({SQLST}, 24900, {m})") for m in (1,2,3,7)]==["14900","19900","24900","24900"])
st=f"Staffelpaket {sfx}"
chk("Staffel ohne Monat 1 abgelehnt",a.post("/api/admin/pakete",json={"name":st,"staffel":[{"ab_monat":2,"cent":100},{"ab_monat":3,"cent":200}]}).status_code==400)
chk("Doppelter Monat abgelehnt",a.post("/api/admin/pakete",json={"name":st,"staffel":[{"ab_monat":1,"cent":100},{"ab_monat":1,"cent":200}]}).status_code==400)
r=a.post("/api/admin/pakete",json={"name":st,"abrechnung":"monatlich","staffel":ST}); chk("Paket mit Staffel angelegt",r.status_code==200,r.text); sc=r.json()["code"]
l=[p for p in a.get("/api/admin/pakete").json()["pakete"] if p["code"]==sc][0]
chk("Regelpreis = letzte Stufe, Staffel gespeichert",l["monatlich_cent"]==24900 and l["staffel"]==ST,l)
kat={p["code"]:p for g in c.get("/api/kunde/paketkatalog").json()["gruppen"] for p in g["produkte"]}
chk("Kunde sieht den Staffelpreis",kat[sc]["staffel_text"]==staffel.text(ST) and kat[sc]["staffel"]==ST,kat.get(sc))
r=c.post(f"/api/kunde/pakete/{sc}/dazubuchen",json={"bestaetigt":True}); chk("Staffelpaket dazubuchen",r.status_code==200,r.text)
chk("Buchung friert die Staffel ein",sql(f"select staffel->2->>'cent' from buchungen where kunden_id='{k['id']}' and produkt_code='{sc}'")=="24900")
# Neue Preisversion mit anderer Staffel ändert die Buchung nicht
a.post("/api/admin/preise",json={"produkt_code":sc,"gueltig_ab":"2099-01-01","staffel":[{"ab_monat":1,"cent":1},{"ab_monat":2,"cent":2}]})
chk("Neue Preisversion mit Staffel (Regelpreis aus letzter Stufe)",sql(f"select monatlich_cent from produkt_preise where produkt_code='{sc}' and gueltig_ab='2099-01-01'")=="2")
chk("Bestehende Buchung behält die Staffel",sql(f"select staffel->0->>'cent' from buchungen where kunden_id='{k['id']}' and produkt_code='{sc}'")=="14900")
# Rechnung: Buchung aktiv, Beginn vor 1 Monat → Zeitraum ab heute = Vertragsmonat 2; Quartal über Monat 2 bis 4
bid=sql(f"select id from buchungen where kunden_id='{k['id']}' and produkt_code='{sc}'")
beg=(datetime.date.today().replace(day=1)-datetime.timedelta(days=1)).replace(day=1)
sql(f"update buchungen set status='aktiv', beginn='{beg}' where id='{bid}'")
sql(f"delete from buchungen where kunden_id='{k['id']}' and id<>'{bid}'")
start=datetime.date.today().replace(day=1)
with db.tx("admin") as cur:
    pos1=abo._positionen(cur,{"aus_buchungen":True,"kunden_id":k["id"],"intervall_monate":1,"naechste_am":start})
    pos3=abo._positionen(cur,{"aus_buchungen":True,"kunden_id":k["id"],"intervall_monate":3,"naechste_am":start})
chk("Rechnung Monat 2: 199 €",len(pos1)==1 and pos1[0]["preis_cent"]==19900 and pos1[0]["menge"]==1,pos1)
chk("Quartal Monat 2 bis 4: 199 € einmal, 249 € zweimal",[(x["preis_cent"],x["menge"]) for x in pos3]==[(19900,1),(24900,2)],pos3)
# Provision folgt dem Preis des Monats
sql(f"update buchungen set rabatt_cent=0 where id='{bid}'")
bas=lambda m: sql(f"select (mk_monatspreis(b.staffel,b.monatlich_cent,{m})-b.rabatt_cent) from buchungen b where b.id='{bid}'")
chk("Provisionsbasis je Vertragsmonat",[bas(1),bas(2),bas(3)]==["14900","19900","24900"])

# ================= Laufzeit 1/3/6/12/24 Monate
chk("Ungültige Laufzeit abgelehnt",a.post("/api/admin/pakete",json={"name":f"Lauf {sfx}","monatlich_cent":100,"laufzeit_monate":5}).status_code==400)
for lz in (1,3,6,12,24):
    r=a.post("/api/admin/pakete",json={"name":f"Lauf{lz} {sfx}","monatlich_cent":100,"laufzeit_monate":lz}); chk(f"Laufzeit {lz} Monate",r.status_code==200 and sql(f"select laufzeit_monate from produkte where code='{r.json()['code']}'")==str(lz),r.text)
lc=r.json()["code"]
chk("Laufzeit ändern",a.put(f"/api/admin/pakete/{lc}",json={"laufzeit_monate":3}).status_code==200 and sql(f"select laufzeit_monate from produkte where code='{lc}'")=="3")
chk("Laufzeit entfernen (0 = keine feste Laufzeit)",a.put(f"/api/admin/pakete/{lc}",json={"laufzeit_monate":0}).status_code==200 and sql(f"select laufzeit_monate is null from produkte where code='{lc}'")=="t")
