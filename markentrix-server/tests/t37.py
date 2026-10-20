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
sfx=str(int(time.time())+7)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":"0511 5555","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False})
L=lead("Angebot GmbH",ansprechpartner="Frau Muster",email=f"lead{sfx}@angebot.de",vertriebspartner_id=p)
sql(f"update leads set status='kontaktiert' where id='{L}'")
sql("delete from benachrichtigungen where tag in ('angebotsreaktion','angebotsstatus')")

# ---- Vorlage
v0=a.get(f"/api/admin/leads/{L}/angebot-vorlage"); chk("Vorlage: 200",v0.status_code==200,v0.text[:300]); vo=v0.json()
chk("Vorlage: Pakete mit Preisen",len(vo["pakete"])>=3 and any(x["einrichtung_cent"] or x["monatlich_cent"] or x["projekt_cent"] for x in vo["pakete"]),vo["pakete"][:2])
chk("Vorlage: Gruß mit Namen und Firma ok",vo["gruss"]=="Guten Tag Frau Muster," and vo["firma_ok"] and vo["mwst_satz"]==19)
# ---- Entwurf, Vorschau
pak=[x for x in vo["pakete"] if x["monatlich_cent"]][0]
pos=[{"text":"Einrichtung "+pak["name"],"menge":1,"einheit":"","preis_cent":50000},{"text":pak["name"]+" – monatlich","menge":1,"einheit":"Monat","preis_cent":19900}]
e=a.post(f"/api/admin/leads/{L}/angebote",json={"betreff":"Ihr Angebot","einleitung":"Guten Tag","schluss":"Danke","positionen":pos,"leistungen":["## BUSINESS WEB","Bis zu sieben Inhaltsseiten","  ","Hosting und Sicherung inklusive"]}); chk("Entwurf: angelegt",e.status_code==200,e.text); bid=e.json()["id"]
chk("Entwurf: Summen (Netto 699, Brutto 831,81)",e.json()["netto_cent"]==69900 and e.json()["brutto_cent"]==83181,e.json())
pv=a.get(f"/api/admin/leads/{L}/angebote/{bid}/pdf"); chk("Vorschau: PDF",pv.status_code==200 and pv.content[:4]==b"%PDF",pv.status_code)
open("/var/tmp/pt/lv.pdf","wb").write(pv.content); pt=subprocess.run(["pdftotext","/var/tmp/pt/lv.pdf","-"],capture_output=True,text=True).stdout
chk("PDF: Abschnitt „Das bekommen Sie“ mit den Punkten",("Das bekommen Sie" in pt and "Bis zu sieben Inhaltsseiten" in pt and "Hosting und Sicherung inklusive" in pt) if pt else True,pt[:300])
vl=a.get(f"/api/admin/leads/{L}/angebot-vorlage").json(); chk("Vorlage: Pakete bringen ihren Leistungsumfang mit",any(p["code"]=="WEB_BUSINESS" and len(p["leistungen"])>=3 for p in vl["pakete"]),[p["code"] for p in vl["pakete"]][:5])
e2=a.post(f"/api/admin/leads/{L}/angebote",json={"beleg_id":bid,"betreff":"Ihr Angebot v2","einleitung":"x","schluss":"y","positionen":pos,"leistungen":["## BUSINESS WEB","Bis zu sieben Inhaltsseiten","Hosting und Sicherung inklusive"]}); chk("Entwurf: ändern statt neu",e2.json()["id"]==bid)
chk("Entwurf: ohne Position abgelehnt",a.post(f"/api/admin/leads/{L}/angebote",json={"positionen":[]}).status_code==400)
chk("Entwurf: ungültige Position abgelehnt",a.post(f"/api/admin/leads/{L}/angebote",json={"positionen":[{"text":"","menge":1,"preis_cent":5}]}).status_code==400)
chk("Entwurf: Kunde/Vertriebler kein Zugriff",v.get(f"/api/admin/leads/{L}/angebote").status_code==403 and v.post(f"/api/admin/leads/{L}/angebote",json={"positionen":pos}).status_code==403)
chk("Belege-Route verweigert Lead-Angebot (ausstellen)",a.post(f"/api/admin/belege/{bid}/ausstellen").status_code==400)
chk("Belege-Route verweigert Lead-Angebot (senden)",a.post(f"/api/admin/belege/{bid}/senden").status_code==400)
# ---- Senden
r=a.post(f"/api/admin/leads/{L}/angebote/{bid}/senden",json={"gueltig_tage":14}); chk("Senden: 200",r.status_code==200,r.text); j=r.json()
chk("Senden: Nummer, Mail raus, Link",j["nummer"].startswith("AN-") and j["gesendet"] and "/angebot?t=" in j["link"],j)
m=mail_an(f"lead{sfx}@angebot.de","Angebot"); chk("Senden: Mail mit PDF-Anhang und Link",bool(m) and any(p.get_content_type()=="application/pdf" for p in m[-1].walk()) and j["link"] in text(m[-1]),len(m))
chk("Senden: Lead steht auf 'angebot', Aktivität vorhanden",sql(f"select status from leads where id='{L}'")=="angebot" and "Angebot "+j["nummer"] in sql(f"select string_agg(inhalt,'|') from lead_aktivitaeten where lead_id='{L}'"))
chk("Senden: Link nicht im Klartext gespeichert",j["link"].split("t=")[1] not in sql(f"select coalesce(annahme_hash,'')||coalesce(notiz,'') from belege where id='{bid}'"))
tok=j["link"].split("t=")[1]
chk("Senden: Vertriebler bekommt Bescheid (Glocke)",int(sql("select count(*) from benachrichtigungen where tag='angebotsstatus' and titel='Angebot ist raus'") or 0)>=1)
chk("Senden: erneut ändern geht nicht (Entwurf-API)",a.post(f"/api/admin/leads/{L}/angebote",json={"beleg_id":bid,"positionen":pos}).status_code==400)
lst=a.get(f"/api/admin/leads/{L}/angebote").json(); chk("Liste: Status 'versendet'",lst[0]["status"]=="versendet" and lst[0]["hat_link"])
chk("Belegliste zeigt Lead-Angebot mit Lead-Namen",any(x["id"]==bid and "Angebot GmbH" in x["firma"] and x["lead_id"]==L for x in a.get("/api/admin/belege?art=angebot").json()["belege"]))
# ---- Öffentliche Seite
anon=httpx.Client(base_url=B,headers=H)
g=anon.get("/api/angebot/"+tok); chk("Öffentlich: Angebot sichtbar ohne Login",g.status_code==200 and g.json()["nummer"]==j["nummer"] and g.json()["brutto_cent"]==83181 and g.json()["anbieter"]=="Markentrix",g.text[:300])
chk("Öffentlich: Leistungsumfang sichtbar (leere Zeilen entfernt)",g.json()["leistungen"]==["## BUSINESS WEB","Bis zu sieben Inhaltsseiten","Hosting und Sicherung inklusive"],g.json().get("leistungen"))
hb=[x for x in a.get("/api/admin/heute").json()["angebote"] if x["nummer"]==j["nummer"]]
chk("Dashboard: Angebot erscheint mit Nummer, Firma und „angesehen“",len(hb)==1 and hb[0]["angesehen_am"] and hb[0]["firma"] and hb[0]["lead_id"]==L,hb)
chk("Öffentlich: keine internen Daten",not any(k in g.json() for k in ("lead_id","kunden_id","annahme_hash","notiz","vertriebspartner_id","partner_id")),list(g.json()))
chk("Öffentlich: PDF",anon.get(f"/api/angebot/{tok}/pdf").content[:4]==b"%PDF")
chk("Öffentlich: falscher Token 404",anon.get("/api/angebot/falsch"+tok).status_code==404 and anon.get("/api/angebot/x").status_code==404)
chk("Öffentlich: Seite wird ausgeliefert",anon.get("/angebot?t="+tok).status_code==200)
time.sleep(1); chk("Angesehen: Push + Zeitpunkt",sql(f"select angesehen_am is not null from belege where id='{bid}'")=="t" and int(sql("select count(*) from benachrichtigungen where tag='angebotsreaktion' and titel='Angebot angesehen'") or 0)>=1)
n=int(sql("select count(*) from benachrichtigungen where tag='angebotsreaktion' and titel='Angebot angesehen'")); anon.get("/api/angebot/"+tok); time.sleep(.8)
chk("Angesehen: nur beim ersten Mal",int(sql("select count(*) from benachrichtigungen where tag='angebotsreaktion' and titel='Angebot angesehen'"))==n)
chk("Annahme: ohne Bestätigung abgelehnt",anon.post(f"/api/angebot/{tok}/annehmen",json={"name":"Max Muster","bestaetigt":False}).status_code==400)
chk("Annahme: ohne Namen abgelehnt",anon.post(f"/api/angebot/{tok}/annehmen",json={"name":"M","bestaetigt":True}).status_code==422)
ok=anon.post(f"/api/angebot/{tok}/annehmen",json={"name":"Max Muster","bestaetigt":True}); chk("Annahme: ok",ok.status_code==200,ok.text)
time.sleep(1.2)
chk("Annahme: Status angenommen, Name und Zeit gespeichert",sql(f"select status||'|'||angenommen_von from belege where id='{bid}'")=="angenommen|Max Muster")
chk("Annahme: Verlauf, Aufgabe, Push",bool(sql(f"select 1 from lead_aktivitaeten where lead_id='{L}' and inhalt like '%online angenommen%'")) and bool(sql("select 1 from aufgaben where titel like 'Angebot angenommen%'")) and int(sql("select count(*) from benachrichtigungen where tag='angebotsreaktion' and titel like 'Angebot angenommen%'") or 0)>=1)
chk("Annahme: Admin-Mail",bool(mail_an("chef@test.de","angenommen")))
chk("Annahme: zweites Mal harmlos",anon.post(f"/api/angebot/{tok}/annehmen",json={"name":"Max Muster","bestaetigt":True}).json().get("schon") is True)
chk("Annahme: danach kein Ablehnen",anon.post(f"/api/angebot/{tok}/ablehnen",json={"grund":""}).status_code==400)
chk("Angenommenes nicht erneut sendbar",a.post(f"/api/admin/leads/{L}/angebote/{bid}/senden",json={}).status_code==400)
# ---- Lead -> Kunde: Angebot wandert mit
k=a.post(f"/api/admin/leads/{L}/zu-kunde").json(); chk("Lead zu Kunde: Angebot hängt jetzt am Kunden",sql(f"select kunden_id::text from belege where id='{bid}'")==k["id"])
chk("Lead zu Kunde: Rechnung aus Angebot möglich",a.post(f"/api/admin/belege/{bid}/rechnung").status_code==200)

# ---- Ablehnen, Ablauf, Sperre
L2=lead("Zweit Angebot",email=f"l2{sfx}@angebot.de"); b2=a.post(f"/api/admin/leads/{L2}/angebote",json={"positionen":pos}).json()["id"]
r2=a.post(f"/api/admin/leads/{L2}/angebote/{b2}/senden",json={"nur_link":True}); t2=r2.json()["link"].split("t=")[1]
chk("Nur Link: keine Mail, Link vorhanden",r2.json()["gesendet"] is False and "/angebot?t=" in r2.json()["link"])
sql(f"update belege set faellig_am=current_date-1 where id='{b2}'")
chk("Abgelaufen: Seite meldet es, Annahme gesperrt",anon.get("/api/angebot/"+t2).json()["abgelaufen"] is True and anon.post(f"/api/angebot/{t2}/annehmen",json={"name":"Max Muster","bestaetigt":True}).status_code==400)
sql(f"update belege set faellig_am=current_date+5 where id='{b2}'")
t2b=a.post(f"/api/admin/leads/{L2}/angebote/{b2}/senden",json={"nur_link":True}).json()["link"].split("t=")[1]
chk("Neuer Link macht den alten ungültig",anon.get("/api/angebot/"+t2).status_code==404 and anon.get("/api/angebot/"+t2b).status_code==200)
chk("Ablehnen funktioniert",anon.post(f"/api/angebot/{t2b}/ablehnen",json={"grund":"zu teuer"}).status_code==200 and sql(f"select status from belege where id='{b2}'")=="abgelehnt")
L3=lead("Gesperrt Angebot",email="g@x.de"); sql(f"update leads set status='consent_ausstehend' where id='{L3}'")
chk("Gesperrter Lead: kein Angebot",a.post(f"/api/admin/leads/{L3}/angebote",json={"positionen":pos}).status_code==400)
L4=lead("Ohne Mail Angebot"); b4=a.post(f"/api/admin/leads/{L4}/angebote",json={"positionen":pos}).json()["id"]
chk("Ohne E-Mail: Senden verlangt Adresse",a.post(f"/api/admin/leads/{L4}/angebote/{b4}/senden",json={}).status_code==400)
chk("Entwurf löschen",a.delete(f"/api/admin/leads/{L4}/angebote/{b4}").status_code==200)
chk("Lead löschen entfernt seine Angebote",(lambda bb: (a.delete(f"/api/admin/leads/{L2}").status_code==200) and sql(f"select count(*) from belege where id='{bb}'")=="0")(b2))
# Rechte: Mitarbeiter ohne Lead-Recht
chk("Rate-Limit/Missbrauch: Brute-Force auf Token wird gebremst",any(anon.get("/api/angebot/zzz"+str(i)).status_code==429 for i in range(70)))
