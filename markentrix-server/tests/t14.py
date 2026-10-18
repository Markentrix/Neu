import httpx, base64, subprocess, time, zipfile, io, json, os, re, email
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","iban":"DE89370400440532013000","steuernummer":"12/345/67890","zahlungsziel_tage":14,"mwst_satz":19})
sfx=str(int(time.time()))
k=a.post("/api/admin/kunden",json={"firma":"Ende GmbH "+sfx,"ansprechpartner":"Egon","email":f"egon{sfx}@e.de","telefon":"0511","strasse":"Weg 2","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]; knr=k["kundennummer"]
# Daten anlegen
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht) values ('{kid}','Max','max@x.de','Hallo')")
sql(f"insert into kontakte (kunden_id,name,email) values ('{kid}','Frieda','f@x.de')")
sql(f"insert into wissensbasis (kunden_id,bereich,schluessel,wert) values ('{kid}','faq','a','b')")
sql(f"insert into chat_verlauf (kunden_id,absender,text) values ('{kid}','kunde','hi')")
d=f"/var/tmp/pt/up/{kid}"; os.makedirs(d,exist_ok=True); open(d+"/x.pdf","wb").write(b"%PDF-1.4 test")
sql(f"insert into wochenangebote_uploads (kunden_id,dateiname,mime,groesse,dateipfad) values ('{kid}','angebot.pdf','application/pdf',13,'{d}/x.pdf')")
b=a.post(f"/api/admin/kunden/{kid}/buchungen",json={"produkt_code":"KI_ONE"}).json()
r=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","betreff":"Test","positionen":[{"text":"Leistung","menge":1,"einheit":"Stk","preis_cent":10000}]}); rid=r.json()["id"]
r=a.post(f"/api/admin/belege/{rid}/ausstellen",json={}); chk("rechnung ausgestellt",r.status_code==200,r.text); nr=r.json()["nummer"]
av=a.post(f"/api/admin/kunden/{kid}/avv").json()["id"]
pdf=base64.b64encode(a.get(f"/api/admin/avv/{av}/vorlage.pdf").content).decode()
a.post(f"/api/admin/avv/{av}/upload",json={"datei_base64":pdf,"datei_name":"avv.pdf","unterschrieben_am":"2026-10-10"})
# Export
r=a.get(f"/api/admin/kunden/{kid}/export.zip"); chk("export 200",r.status_code==200 and r.headers["content-type"]=="application/zip",r.text[:200])
z=zipfile.ZipFile(io.BytesIO(r.content)); n=z.namelist()
chk("export enthält Daten",all(x in n for x in ["LIESMICH.txt","daten/kunde.json","daten/anfragen.json","daten/kontakte.json","daten/belege.json","daten/zugaenge.json"]),n)
chk("export Anfrage drin","Hallo" in z.read("daten/anfragen.json").decode())
chk("export Rechnungs-PDF",any(x.startswith("belege/") and x.endswith(".pdf") for x in n),n)
chk("export AVV-Datei",any(x.startswith("avv/") for x in n),n)
chk("export Upload-Datei",any(x.startswith("uploads/") for x in n),n)
chk("export kein Passwort-Hash","passwort_hash" not in z.read("daten/zugaenge.json").decode())
chk("export 404",a.get("/api/admin/kunden/nix/export.zip").status_code==404)
# Löschen-Schutz
chk("aktiv: Löschen verboten",a.post(f"/api/admin/kunden/{kid}/loeschen",json={"bestaetigung":knr,"export_uebergeben":True}).status_code==400)
chk("status gekuendigt",a.post(f"/api/admin/kunden/{kid}/status",json={"status":"gekuendigt"}).status_code==200)
chk("falsche Bestätigung",a.post(f"/api/admin/kunden/{kid}/loeschen",json={"bestaetigung":"MK-0","export_uebergeben":True}).status_code==400)
chk("ohne Export-Haken",a.post(f"/api/admin/kunden/{kid}/loeschen",json={"bestaetigung":knr,"export_uebergeben":False}).status_code==400)
chk("Daten noch da",sql(f"select count(*) from anfragen where kunden_id='{kid}'")=="1")
# Kunde (Login) vorher
tok=None
for x in reversed([x for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]):
    mm=email.message_from_string(x)
    if f"egon{sfx}@e.de" in str(mm["To"]):
        for p in mm.walk():
            if p.get_content_type()=="text/plain":
                g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",p.get_payload(decode=True).decode())
                if g: tok=g.group(1); break
    if tok: break
chk("einladung gefunden",tok is not None)
r=a.post(f"/api/admin/kunden/{kid}/loeschen",json={"bestaetigung":knr,"export_uebergeben":True}); chk("löschen",r.status_code==200,r.text)
chk("Zähler",r.json()["geloescht"].get("anfragen")==1 and r.json()["geloescht"].get("kontakte")==1,r.json())
for t in ["anfragen","kontakte","wissensbasis","chat_verlauf","wochenangebote_uploads","benutzer"]:
    chk(f"{t} leer",sql(f"select count(*) from {t} where kunden_id='{kid}'")=="0")
chk("Upload-Ordner entfernt",not os.path.exists(d))
chk("Rechnung bleibt",sql(f"select count(*) from belege where kunden_id='{kid}' and nummer='{nr}'")=="1")
chk("AVV bleibt",sql(f"select count(*) from avv where kunden_id='{kid}'")=="1")
chk("Buchung bleibt",sql(f"select count(*) from buchungen where kunden_id='{kid}'")=="1")
chk("Kontaktdaten entfernt",sql(f"select coalesce(ansprechpartner,'')||coalesce(email,'')||coalesce(telefon,'') from kunden where id='{kid}'")=="")
chk("Stammdaten bleiben",sql(f"select firma||strasse from kunden where id='{kid}'").startswith("Ende GmbH"))
chk("geloescht_am gesetzt",sql(f"select geloescht_am is not null from kunden where id='{kid}'")=="t")
chk("Löschprotokoll",int(sql("select count(*) from loeschprotokoll where tabelle like '%"+kid+"%'"))>=4)
chk("Audit",int(sql(f"select count(*) from audit_log where aktion='kunde_inhalte_geloescht' and kunden_id='{kid}'"))==1)
chk("zweites Löschen verboten",a.post(f"/api/admin/kunden/{kid}/loeschen",json={"bestaetigung":knr,"export_uebergeben":True}).status_code==400)
chk("Einladung ungültig",httpx.get(B+f"/api/einladung/{tok}").status_code==404)
chk("Rechnung-PDF weiter abrufbar",a.get(f"/api/admin/belege/{rid}/pdf").status_code==200)
chk("Export danach noch möglich",a.get(f"/api/admin/kunden/{kid}/export.zip").status_code==200)
chk("nicht auf AVV-fehlt-Liste",not any(x["id"]==kid for x in a.get("/api/admin/avv-fehlt").json()))
k2=a.get(f"/api/admin/kunden/{kid}").json()["kunde"]; chk("detail hat geloescht_am",k2["geloescht_am"] is not None and "logo" not in k2)
nk=httpx.Client(base_url=B,headers=H); chk("kunde kann nicht mehr einloggen",nk.post("/api/login",json={"email":f"egon{sfx}@e.de","password":"x"}).status_code in (401,403,429))
chk("kunde als admin-only",httpx.Client(base_url=B,headers=H).get(f"/api/admin/kunden/{kid}/export.zip").status_code==401)
