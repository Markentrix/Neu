"""Vertriebler senden Angebote zu Katalogpreisen; Preisanfrage mit Freigabe durch den Admin."""
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
sfx=str(int(time.time())+1300)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb, angebotserinnerung
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
L1=lead("a")
# Standard: aus
chk("Standard: Vertriebler darf nicht",v.get(f"/api/vertrieb/leads/{L1}/angebot-start").json()=={"erlaubt":False} and v.post(f"/api/vertrieb/leads/{L1}/angebot-senden",json={"paket_codes":["KI_ONE"]}).status_code==403 and v.post(f"/api/vertrieb/leads/{L1}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":10,"begruendung":"Stammkunde, will Rabatt"}).status_code==403)
steuerung(True)
chk("Einschalten wird protokolliert",int(sql("select count(*) from audit_log where aktion='vertrieb_steuerung' and details->>'vertrieb_angebote'='true'"))==1)
st=v.get(f"/api/vertrieb/leads/{L1}/angebot-start").json(); kat={x["code"]:x for x in st["pakete"]}
chk("Start liefert Pakete mit Katalogpreisen",st["erlaubt"] and "KI_ONE" in kat and (kat["KI_ONE"]["monatlich_cent"] or kat["KI_ONE"]["einrichtung_cent"]) and kat["KI_ONE"]["grund"]=="" and st["email"]==f"verta{sfx}@lead.de",st)
# Senden zu Katalogpreisen, Preise aus dem Browser werden ignoriert
n0=len(mails())
r=v.post(f"/api/vertrieb/leads/{L1}/angebot-senden",json={"paket_codes":["KI_ONE"],"gueltig_tage":30,"preise":{"monatlich_cent":1},"positionen":[{"text":"x","preis_cent":1}]}); time.sleep(1.2)
chk("Vertriebler sendet Angebot",r.status_code==200 and r.json()["gesendet"],r.text)
bid=sql(f"select id from belege where lead_id='{L1}' and art='angebot' order by erstellt_am desc limit 1")
pos=json.loads(sql(f"select positionen from belege where id='{bid}'"))
erw=sorted(c for c in (kat["KI_ONE"]["einrichtung_cent"],kat["KI_ONE"]["monatlich_cent"],kat["KI_ONE"]["projekt_cent"]) if c)
chk("Positionen entsprechen exakt dem Katalog",sorted(p_["preis_cent"] for p_ in pos)==erw,(pos,erw))
chk("Status versendet, Mail an Lead mit PDF",sql(f"select status from belege where id='{bid}'")=="versendet" and any(f"verta{sfx}@lead.de" in str(x["To"]) and any(q.get_content_type()=="application/pdf" for q in x.walk()) for x in mails()[n0:]))
chk("Verlauf und Audit",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{L1}' and inhalt like '%zu Katalogpreisen gesendet%'"))==1 and int(sql("select count(*) from audit_log where aktion='vertriebler_angebot'"))==1)
# Prüfungen
chk("Fremder Lead: 404",v.get(f"/api/vertrieb/leads/{lead('b',vertriebspartner_id=None)}/angebot-start").status_code==404)
LN=lead("c",email=None); chk("Lead ohne E-Mail: 400",v.post(f"/api/vertrieb/leads/{LN}/angebot-senden",json={"paket_codes":["KI_ONE"]}).status_code==400)
LG=lead("d"); sql(f"update leads set status='gesperrt' where id='{LG}'"); chk("Gesperrter Lead: 400",v.post(f"/api/vertrieb/leads/{LG}/angebot-senden",json={"paket_codes":["KI_ONE"]}).status_code==400)
chk("Unbekanntes Paket: 400",v.post(f"/api/vertrieb/leads/{L1}/angebot-senden",json={"paket_codes":["GIBT_ES_NICHT"]}).status_code==400)
chk("Leere Auswahl und zu viele Pakete: 422",v.post(f"/api/vertrieb/leads/{L1}/angebot-senden",json={"paket_codes":[]}).status_code==422 and v.post(f"/api/vertrieb/leads/{L1}/angebot-senden",json={"paket_codes":list("abcde")}).status_code==422)
chk("Admin-Routen sind für Vertriebler zu",v.get("/api/admin/preisanfragen").status_code in (401,403) and v.post("/api/admin/preisanfragen/00000000-0000-0000-0000-000000000000/genehmigen",json={}).status_code in (401,403))
# Preisanfrage
L2=lead("e")
chk("Begründung zu kurz: 422",v.post(f"/api/vertrieb/leads/{L2}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":10,"begruendung":"zu kurz"}).status_code==422)
chk("Preis gleich Katalog: 400",v.post(f"/api/vertrieb/leads/{L2}/preisanfrage",json={"paket_code":"KI_ONE","begruendung":"Gleicher Preis wie Katalog"}).status_code==400)
r=v.post(f"/api/vertrieb/leads/{L2}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":10,"begruendung":"Stammkunde, kommt über Empfehlung"}); chk("Preisanfrage gestellt",r.status_code==200,r.text); aid=r.json()["id"]
row=json.loads(sql(f"select json_build_object('w',wunsch,'k',katalog,'s',status) from angebot_preisanfragen where id='{aid}'"))
chk("Wunschpreis = Katalog minus 10 % (server-seitig gerechnet)",row["s"]=="offen" and all(row["w"][f]==round(row["k"][f]*0.9) for f in row["k"]),row)
chk("Zweite offene Anfrage: 409",v.post(f"/api/vertrieb/leads/{L2}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":5,"begruendung":"Noch ein Versuch hier"}).status_code==409)
chk("Aufgabe für den Admin angelegt",int(sql(f"select count(*) from aufgaben where titel like 'Preisfreigabe prüfen: Verte {sfx}%'"))==1)
chk("Start zeigt offene Preisanfrage",v.get(f"/api/vertrieb/leads/{L2}/angebot-start").json()["preisanfrage_offen"] is True)
adm=a.get("/api/admin/preisanfragen").json(); chk("Admin sieht die Anfrage",any(x["id"]==aid and x["status"]=="offen" and x["vertriebler"]=="Vera Vertrieb" for x in adm))
chk("Vertriebler sieht Status",v.get(f"/api/vertrieb/leads/{L2}/preisanfragen").json()[0]["status"]=="offen")
chk("Vor Freigabe ist kein Angebot entstanden",int(sql(f"select count(*) from belege where lead_id='{L2}'"))==0)
# Freigabe mit geänderten Preisen
n0=len(mails()); mon=row["k"]["monatlich_cent"] or row["k"]["einrichtung_cent"]; feld="monatlich_cent" if row["k"]["monatlich_cent"] else "einrichtung_cent"
r=a.post(f"/api/admin/preisanfragen/{aid}/genehmigen",json={feld:mon-1000,"notiz":"Einmalig ok"}); time.sleep(1.2)
chk("Admin gibt frei, Angebot geht raus",r.status_code==200 and r.json()["gesendet"] and r.json()["preise"][feld]==mon-1000,r.text)
b2=sql(f"select id from belege where lead_id='{L2}' and art='angebot'"); pos=json.loads(sql(f"select positionen from belege where id='{b2}'"))
chk("Angebot enthält den freigegebenen Preis",any(q["preis_cent"]==mon-1000 for q in pos),pos)
chk("Anfrage genehmigt, mit Beleg und Entscheider",sql(f"select status||'|'||(beleg_id is not null)||'|'||entschieden_von from angebot_preisanfragen where id='{aid}'")==f"genehmigt|true|chef@test.de")
chk("Mail an den Lead gegangen",any(f"verte{sfx}@lead.de" in str(x["To"]) for x in mails()[n0:]))
chk("Zweite Entscheidung: 409",a.post(f"/api/admin/preisanfragen/{aid}/genehmigen",json={}).status_code==409 and a.post(f"/api/admin/preisanfragen/{aid}/ablehnen",json={}).status_code==409)
chk("Audit der Freigabe mit Preisen",int(sql("select count(*) from audit_log where aktion='preisanfrage_genehmigt' and details ? 'preise'"))==1)
# Ablehnen
L3=lead("f"); aid3=v.post(f"/api/vertrieb/leads/{L3}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":25,"begruendung":"Kunde droht mit Konkurrenz"}).json()["id"]
r=a.post(f"/api/admin/preisanfragen/{aid3}/ablehnen",json={"notiz":"Katalogpreis gilt"}); chk("Ablehnen",r.status_code==200 and sql(f"select status from angebot_preisanfragen where id='{aid3}'")=="abgelehnt")
chk("Nach Ablehnung kein Angebot",int(sql(f"select count(*) from belege where lead_id='{L3}'"))==0)
chk("Vertriebler sieht Ablehnung mit Anmerkung",v.get(f"/api/vertrieb/leads/{L3}/preisanfragen").json()[0]["admin_notiz"]=="Katalogpreis gilt")
chk("Danach neue Anfrage möglich",v.post(f"/api/vertrieb/leads/{L3}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":5,"begruendung":"Zweiter Versuch mit weniger"}).status_code==200)
# Freigabe-Sperren
L4=lead("g"); a4=v.post(f"/api/vertrieb/leads/{L4}/preisanfrage",json={"paket_code":"KI_ONE","nachlass_prozent":10,"begruendung":"Lead wird gleich gesperrt"}).json()["id"]
sql(f"update leads set status='gesperrt' where id='{L4}'"); chk("Freigabe bei gesperrtem Lead: 400, bleibt offen",a.post(f"/api/admin/preisanfragen/{a4}/genehmigen",json={}).status_code==400 and sql(f"select status from angebot_preisanfragen where id='{a4}'")=="offen")
# Ausschalten
steuerung(False); chk("Ausgeschaltet: Vertriebler darf wieder nicht",v.post(f"/api/vertrieb/leads/{L1}/angebot-senden",json={"paket_codes":["KI_ONE"]}).status_code==403)
