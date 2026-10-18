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
import os, json
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Ali Markt","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    time.sleep(1.2); httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
kid,c=neuer_kunde("Anadolu")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kid}','wochenangebote',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
dom=f"anadolu{sfx}.de"; os.makedirs(f"/var/tmp/pt/s/live/{dom}",exist_ok=True)
r=a.post(f"/api/admin/kunden/{kid}/websites",json={"domain":dom,"art":"live"}); chk("Website angelegt",r.status_code==200,r.text)
wid=sql(f"select id from websites where kunden_id='{kid}'")
chk("Standard nur Deutsch",sql(f"select sprachen from websites where id='{wid}'")=="{de}")
chk("Sprachen ungültig",a.put(f"/api/admin/websites/{wid}/sprachen",json={"sprachen":["de","fr"]}).status_code==400)
r=a.put(f"/api/admin/websites/{wid}/sprachen",json={"sprachen":["tr","en","ar"]}); chk("Sprachen setzen (de immer dabei)",r.status_code==200 and r.json()["sprachen"]==["de","tr","en","ar"],r.text)
chk("Admin sieht Sprachen",any(w["sprachen"]==["de","tr","en","ar"] for w in a.get(f"/api/admin/kunden/{kid}").json()["websites"]))
seite=f"/var/tmp/pt/s/live/{dom}/angebote/"
r=c.get("/api/kunde/angebots-inhalte"); chk("Liste leer + Sprachen",r.status_code==200 and r.json()["sprachen"]==["de","tr","en","ar"] and r.json()["inhalte"]==[] and r.json()["website"]==dom,r.text)
# Datei zuerst hochladen, Texte danach: Datei muss bleiben
r=c.post("/api/kunde/wochenangebote",files={"datei":("a.pdf",b"%PDF-1.4 test","application/pdf")}); chk("Datei veröffentlicht",r.status_code==200 and r.json()["status"]=="veroeffentlicht",r.text)
r=c.post("/api/kunde/angebots-inhalte",json={"art":"angebot","titel":{"de":"Tomaten <script>alert(1)</script>","tr":"Domates","ar":"طماطم"},"text":{"de":"Frisch vom Feld","tr":"Taze"},"preis":"1,99 € / kg"}); chk("Angebot anlegen",r.status_code==200 and r.json()["status"]=="veroeffentlicht",r.text); iid=r.json()["id"]
h=open(seite+"index.html",encoding="utf8").read()
chk("Seite: alle Sprachen",all(x in h for x in ["Domates","طماطم",'lang="ar"','dir="rtl"',"Frisch vom Feld","1,99 € / kg"]))
chk("Seite: English fällt auf Deutsch zurück",'lang="en"><h3>Tomaten' in h)
chk("Seite: HTML maskiert","<script>alert(1)</script>" not in h and "&lt;script&gt;" in h)
chk("Seite: Datei bleibt",'src="aktuell.pdf"' in h and os.path.exists(seite+"aktuell.pdf"))
chk("Seite: Sprachwahl",'data-sp="tr"' in h and 'data-sp="ar"' in h)
r=c.post("/api/kunde/angebots-inhalte",json={"art":"event","titel":{"de":"Grillfest"},"gueltig_von":"2026-10-24","gueltig_bis":"2026-10-25"}); chk("Event",r.status_code==200,r.text)
r=c.post("/api/kunde/angebots-inhalte",json={"art":"geschlossen","text":{"de":"Inventur","tr":"Sayım"}}); chk("Heute geschlossen (ohne Titel)",r.status_code==200,r.text)
h=open(seite+"index.html",encoding="utf8").read()
chk("Seite: geschlossen in 4 Sprachen",all(x in h for x in ["Heute geschlossen","Bugün kapalıyız","Closed today","مغلق اليوم","Sayım"]))
chk("Seite: geschlossen mit heutigem Datum",'class="zu" data-von="'+time.strftime("%Y-%m-%d") in h)
chk("Seite: Event mit Gültigkeit",'data-von="2026-10-24"' in h and "Grillfest" in h)
m=json.load(open(seite+"aktuell.json",encoding="utf8")); chk("json: Inhalte + Sprachen",len(m["inhalte"])==3 and m["sprachen"]==["de","tr","en","ar"] and m["datei"]=="aktuell.pdf",m)
# Validierung
chk("ohne deutschen Titel",c.post("/api/kunde/angebots-inhalte",json={"art":"angebot","titel":{"tr":"Domates"}}).status_code==400)
chk("unbekannte Sprache",c.post("/api/kunde/angebots-inhalte",json={"art":"angebot","titel":{"de":"x","fr":"y"}}).status_code==400)
chk("Enddatum vor Start",c.post("/api/kunde/angebots-inhalte",json={"art":"event","titel":{"de":"x"},"gueltig_von":"2026-10-25","gueltig_bis":"2026-10-24"}).status_code==400)
chk("Art ungültig",c.post("/api/kunde/angebots-inhalte",json={"art":"spam","titel":{"de":"x"}}).status_code==422)
chk("Titel zu lang",c.post("/api/kunde/angebots-inhalte",json={"art":"angebot","titel":{"de":"x"*201}}).status_code==400)
# Ändern, ausblenden, löschen
r=c.patch(f"/api/kunde/angebots-inhalte/{iid}",json={"preis":"2,49 € / kg","titel":{"de":"Tomaten","en":"Tomatoes"}}); chk("Ändern",r.status_code==200,r.text)
h=open(seite+"index.html",encoding="utf8").read(); chk("Seite aktualisiert",("2,49 € / kg" in h and "Tomatoes" in h and "1,99" not in h and "Domates" not in h))
r=c.patch(f"/api/kunde/angebots-inhalte/{iid}",json={"aktiv":False}); chk("Ausblenden",r.status_code==200)
chk("Ausgeblendet nicht auf Seite","Tomatoes" not in open(seite+"index.html",encoding="utf8").read())
r=c.delete(f"/api/kunde/angebots-inhalte/{iid}"); chk("Löschen",r.status_code==200)
chk("Löschen 404",c.delete(f"/api/kunde/angebots-inhalte/{iid}").status_code==404)
chk("PATCH 404",c.patch("/api/kunde/angebots-inhalte/nix",json={"aktiv":True}).status_code==404)
# Mandantentrennung
kid2,c2=neuer_kunde("Fremd")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kid2}','wochenangebote',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
chk("Fremder sieht nichts",c2.get("/api/kunde/angebots-inhalte").json()["inhalte"]==[])
alle=c.get("/api/kunde/angebots-inhalte").json()["inhalte"]; fid=alle[0]["id"]
chk("Fremder kann nicht ändern",c2.patch(f"/api/kunde/angebots-inhalte/{fid}",json={"aktiv":False}).status_code==404)
chk("Fremder kann nicht löschen",c2.delete(f"/api/kunde/angebots-inhalte/{fid}").status_code==404)
r=c2.post("/api/kunde/angebots-inhalte",json={"art":"hinweis","titel":{"de":"Ohne Website"}}); chk("Ohne Website: gespeichert mit Hinweis",r.status_code==200 and r.json()["status"]=="ohne_website",r.text)
# Modul aus -> gesperrt
sql(f"update kunden_module set aktiv=false where kunden_id='{kid2}' and modul_code='wochenangebote'")
chk("Modul aus: gesperrt",c2.get("/api/kunde/angebots-inhalte").status_code in (402,403))
# Datei erneut hochladen behält Texte
r=c.post("/api/kunde/wochenangebote",files={"datei":("b.pdf",b"%PDF-1.4 neu","application/pdf")}); chk("2. Datei",r.status_code==200 and r.json()["status"]=="veroeffentlicht",r.text)
chk("Texte bleiben nach neuer Datei","Grillfest" in open(seite+"index.html",encoding="utf8").read())
# Export enthält Inhalte
import zipfile
sql(f"update kunden set status='gekuendigt' where id='{kid}'")
z=zipfile.ZipFile(io.BytesIO(a.get(f"/api/admin/kunden/{kid}/export.zip").content)); chk("Export enthält Inhalte","daten/angebots_inhalte.json" in z.namelist() and "Grillfest" in z.read("daten/angebots_inhalte.json").decode())
import app.db as db
try: db.close_pool()
except Exception: pass
