import re, email, email.header, httpx, subprocess, time
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def cl(): return httpx.Client(base_url=B,headers=H)
def mails():
    try: raw=[x for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
    out=[]
    for x in raw:
        m=email.message_from_string(x)
        body=""; anh=[]
        for part in m.walk():
            if part.get_content_type()=="text/plain": body=part.get_payload(decode=True).decode("utf8")
            if part.get_filename(): anh.append((part.get_filename(),part.get_payload(decode=True)))
        out.append({"to":str(m["To"]),"subject":str(email.header.make_header(email.header.decode_header(m["Subject"] or ""))),"body":body,"anh":anh})
    return out
a=cl(); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
# --- Firma unvollständig: Rechnung ausstellen blockiert
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False})
k=a.post("/api/admin/kunden",json={"firma":"Rechnung Test GmbH","ansprechpartner":"Rita","email":"rita@rt.de","strasse":"Hauptstr. 5","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
# Onboarding
o=a.get(f"/api/admin/kunden/{kid}/onboarding").json(); chk("onboarding angelegt",o["gesamt"]>=8 and o["fertig"]==0,o)
codes=[p["code"] for p in o["punkte"]]; chk("rechnung-punkt vorhanden",("rechnung" in codes))
r=a.patch(f"/api/admin/kunden/{kid}/onboarding/vertrag",json={"erledigt":True}); chk("punkt erledigt",r.status_code==200)
o=a.get(f"/api/admin/kunden/{kid}/onboarding").json(); chk("fortschritt",o["fertig"]==1 and [p for p in o["punkte"] if p["code"]=="vertrag"][0]["erledigt_am"])
a.post(f"/api/admin/kunden/{kid}/onboarding",json={"titel":"Flyer drucken"}); o=a.get(f"/api/admin/kunden/{kid}/onboarding").json(); chk("eigener punkt",any(p["titel"]=="Flyer drucken" for p in o["punkte"]))
chk("offen-Liste",any(x["id"]==kid for x in a.get("/api/admin/onboarding/offen").json()))
chk("404 onboarding",a.get("/api/admin/kunden/nix/onboarding").status_code==404)
# Vorlage aus Buchungen
b=a.post(f"/api/admin/kunden/{kid}/buchungen",json={"produkt_code":"KI_ONE"}); chk("buchung",b.status_code==200,b.text)
v=a.get(f"/api/admin/kunden/{kid}/belege-vorlage").json(); chk("vorlage aus buchung",len(v["positionen"])>=1,v)
# Angebot
r=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"angebot","betreff":"Website-Paket","positionen":v["positionen"]+[{"text":"Zusatz","menge":2.5,"einheit":"Std","preis_cent":9000}]}); chk("angebot entwurf",r.status_code==200,r.text); ang=r.json()["id"]
chk("ungültige position",a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"angebot","positionen":[{"text":"","menge":1,"preis_cent":1}]}).status_code==400)
d=a.get(f"/api/admin/belege/{ang}").json()["beleg"]; chk("entwurf ohne nummer",d["nummer"] is None and d["status"]=="entwurf")
r=a.put(f"/api/admin/belege/{ang}",json={"betreff":"Website-Paket","positionen":d["positionen"],"einleitung":"Danke für Ihr Interesse."}); chk("entwurf ändern",r.status_code==200)
r=a.post(f"/api/admin/belege/{ang}/ausstellen",json={"gueltig_tage":14}); chk("angebot ausstellen",r.status_code==200 and r.json()["nummer"].startswith("AN-"),r.text); angnr=r.json()["nummer"]
chk("ausgestellt nicht änderbar",a.put(f"/api/admin/belege/{ang}",json={"betreff":"x","positionen":d["positionen"]}).status_code==400)
chk("ausgestellt nicht löschbar",a.delete(f"/api/admin/belege/{ang}").status_code==400)
open("/var/tmp/pt/mails.txt","w").close()
r=a.post(f"/api/admin/belege/{ang}/senden"); chk("angebot senden",r.json()["gesendet"] is True,r.text)
m=mails()[-1]; chk("mail angebot mit pdf",m["to"]=="rita@rt.de" and m["anh"] and m["anh"][0][1][:4]==b"%PDF" and "Claude" not in m["body"],m["subject"])
# Kunde: Zugang
tok=re.search(r"token=([A-Za-z0-9_-]+)",[x for x in mails()] and "")  # placeholder
# --- Rechnung aus Angebot
r=a.post(f"/api/admin/belege/{ang}/rechnung"); chk("rechnung aus angebot",r.status_code==200,r.text); re_id=r.json()["id"]
# Firmendaten fehlen Steuernummer → blockiert
r=a.post(f"/api/admin/belege/{re_id}/ausstellen"); chk("ohne Steuernummer blockiert",r.status_code==400 and "Steuernummer" in r.text,r.text)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False})
r=a.post(f"/api/admin/belege/{re_id}/ausstellen"); jahr=time.strftime("%Y"); chk("rechnung nummer",r.status_code==200 and re.match(rf"RE-{jahr}-\d{{4}}$",r.json()["nummer"]),r.text); renr=r.json()["nummer"]
d=a.get(f"/api/admin/belege/{re_id}").json()["beleg"]
# Summe: Einrichtung+monatlich+2.5*90
netto=sum(round(p["menge"]*p["preis_cent"]) for p in d["positionen"]); chk("summen",d["netto_cent"]==netto and d["ust_cent"]==round(netto*0.19) and d["brutto_cent"]==netto+d["ust_cent"],d)
nr2=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","positionen":[{"text":"Test","menge":1,"preis_cent":10000}]}).json()["id"]; r=a.post(f"/api/admin/belege/{nr2}/ausstellen").json()["nummer"]
chk("fortlaufend",int(r[-4:])==int(renr[-4:])+1,(r,renr))
p=a.get(f"/api/admin/belege/{re_id}/pdf"); chk("rechnung pdf",p.status_code==200 and p.content[:4]==b"%PDF",p.status_code); open("/var/tmp/pt/rechnung.pdf","wb").write(p.content)
# Überfällig + Mahnung
chk("mahnung zu früh",a.post(f"/api/admin/belege/{re_id}/mahnung",json={"stufe":1}).status_code==400)
subprocess.run(["su","postgres","-c",f"psql -q -h /var/tmp/pgtest -p 54329 markentrix -c \"update belege set faellig_am=current_date-10, datum=current_date-24 where id='{re_id}'\""])
l=a.get("/api/admin/belege?art=rechnung").json(); chk("überfällig erkannt",[x for x in l["belege"] if x["id"]==re_id][0]["ueberfaellig"] is True and l["summen"]["ueberfaellig_n"]>=1,l["summen"])
open("/var/tmp/pt/mails.txt","w").close()
r=a.post(f"/api/admin/belege/{re_id}/mahnung",json={"stufe":1}); chk("zahlungserinnerung",r.status_code==200 and r.json()["gesendet"],r.text)
m=mails()[-1]; chk("mahn mail",m["anh"] and "Zahlungserinnerung" in m["subject"]); open("/var/tmp/pt/mahn.pdf","wb").write(m["anh"][0][1])
chk("stufe nicht doppelt",a.post(f"/api/admin/belege/{re_id}/mahnung",json={"stufe":1}).status_code==400)
chk("stufe 2",a.post(f"/api/admin/belege/{re_id}/mahnung",json={"stufe":2}).status_code==200)
# Bezahlt
r=a.post(f"/api/admin/belege/{re_id}/bezahlt",json={}); chk("bezahlt",r.status_code==200,r.text)
chk("nicht doppelt bezahlt",a.post(f"/api/admin/belege/{re_id}/bezahlt",json={}).status_code==400)
# Storno
r=a.post(f"/api/admin/belege/{re_id}/stornieren"); chk("storno",r.status_code==200 and r.json()["nummer"].startswith("RE-"),r.text); sid=r.json()["id"]
s=a.get(f"/api/admin/belege/{sid}").json()["beleg"]; o=a.get(f"/api/admin/belege/{re_id}").json()["beleg"]
chk("storno negativ",s["brutto_cent"]==-o["brutto_cent"] and s["storno_von"]==re_id and o["status"]=="storniert",(s["brutto_cent"],o["brutto_cent"]))
chk("storno nicht erneut",a.post(f"/api/admin/belege/{re_id}/stornieren").status_code==400 and a.post(f"/api/admin/belege/{sid}/stornieren").status_code==400)
open("/var/tmp/pt/storno.pdf","wb").write(a.get(f"/api/admin/belege/{sid}/pdf").content)
# Referenzkunde
rk=a.post("/api/admin/kunden",json={"firma":"Ref Kunde","referenzkunde":True}).json()["id"]
chk("referenz: keine rechnung",a.post(f"/api/admin/kunden/{rk}/belege",json={"art":"rechnung","positionen":[{"text":"x","menge":1,"preis_cent":100}]}).status_code==400)
chk("referenz: vorlage leer",a.get(f"/api/admin/kunden/{rk}/belege-vorlage").json()["positionen"]==[])
chk("referenz: angebot ok",a.post(f"/api/admin/kunden/{rk}/belege",json={"art":"angebot","positionen":[{"text":"Website kostenlos","menge":1,"preis_cent":0}]}).status_code==200)
# Kleinunternehmer
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","strasse":"Teststr. 1","plz":"29221","ort":"Celle","steuernummer":"12/345/67890","kleinunternehmer":True,"mwst_satz":19})
kb=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","positionen":[{"text":"Leistung","menge":1,"preis_cent":10000}]}).json()["id"]; a.post(f"/api/admin/belege/{kb}/ausstellen")
d=a.get(f"/api/admin/belege/{kb}").json()["beleg"]; chk("kleinunternehmer ohne USt",d["ust_cent"]==0 and d["brutto_cent"]==10000 and d["kleinunternehmer"])
open("/var/tmp/pt/klein.pdf","wb").write(a.get(f"/api/admin/belege/{kb}/pdf").content)
# Übersicht
u=a.get("/api/admin/uebersicht").json(); chk("übersicht rechnungen","rechnungen_offen_cent" in u,u.keys())
# --- Kundenportal
open("/var/tmp/pt/mails.txt","w").close()
a.post(f"/api/admin/kunden/{kid}/einladung",json={"email":"rita@rt.de","per_mail":True})
mm=mails()[-1]; t=re.search(r"token=([A-Za-z0-9_-]+)",mm["body"]).group(1)
httpx.post(B+"/api/einladung",headers=H,json={"token":t,"password":"RitaPasswort123"})
c=cl(); c.post("/api/login",json={"email":"rita@rt.de","password":"RitaPasswort123"})
kl=c.get("/api/kunde/belege").json(); chk("kunde sieht eigene belege (keine entwürfe)",len(kl)>=3 and all(x["status"]!="entwurf" for x in kl),[x["status"] for x in kl])
chk("kunde pdf",c.get(f"/api/kunde/belege/{re_id}/pdf").content[:4]==b"%PDF")
chk("kunde fremder beleg 404",c.get(f"/api/kunde/belege/{[x for x in a.get('/api/admin/belege').json()['belege'] if x['firma']=='Ref Kunde'][0]['id']}/pdf").status_code==404)
chk("kunde annehmen",c.post(f"/api/kunde/belege/{ang}/annehmen").status_code==200)
chk("nicht doppelt annehmen",c.post(f"/api/kunde/belege/{ang}/annehmen").status_code==400)
chk("kunde kann rechnung nicht annehmen",c.post(f"/api/kunde/belege/{renr and re_id}/annehmen").status_code in (400,404))
chk("kunde kann admin-api nicht",c.get("/api/admin/belege").status_code==403)
# Monatsbericht kunde-pdf
bid=a.post(f"/api/admin/kunden/{kid}/bericht",json={"monat":time.strftime("%Y-%m",time.gmtime(time.time()-40*86400)),"senden":False}).json()["id"]
mb=c.get("/api/kunde/monatsberichte").json(); chk("kunde monatsberichte",len(mb)==1)
pp=c.get(f"/api/kunde/monatsberichte/{bid}/pdf"); chk("kunde bericht pdf",pp.content[:4]==b"%PDF",pp.status_code)
