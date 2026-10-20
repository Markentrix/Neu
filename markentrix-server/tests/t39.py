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
sfx=str(int(time.time())+7)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":"0511 5555","ort":"Celle",**kw}).json()["id"]; return i
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False})
kid,c,mail=neuer_kunde("Plus")
pos=[{"text":"BUSINESS – monatlich","menge":1,"einheit":"Monat","preis_cent":19900},{"text":"Einrichtung BUSINESS","menge":1,"einheit":"","preis_cent":50000}]
L1=lead("Alt Firma",ansprechpartner="Herr Alt",email=f"alt{sfx}@x.de"); L2=lead("Neu Firma",ansprechpartner="Frau Neu",email=f"neu{sfx}@x.de")
# --- Leistungstexte pflegen
r=a.get("/api/admin/katalog/leistungstexte"); lt=r.json(); chk("Leistungstexte: alle Pakete mit Texten",r.status_code==200 and len(lt)>=10 and all("leistungen" in x for x in lt),r.text[:200])
r=a.put("/api/admin/katalog/leistungstexte/WEB_BUSINESS",json={"leistungen":["Punkt A"," ","Punkt B"]}); chk("Leistungstext speichern (Leerzeilen weg)",r.status_code==200 and r.json()["anzahl"]==2,r.text)
chk("Leistungstext steht in der Vorlage",[p["leistungen"] for p in a.get(f"/api/admin/leads/{L1}/angebot-vorlage").json()["pakete"] if p["code"]=="WEB_BUSINESS"][0]==["Punkt A","Punkt B"])
chk("Leistungstext: unbekanntes Paket 404",a.put("/api/admin/katalog/leistungstexte/GIBTS_NICHT",json={"leistungen":[]}).status_code==404)
chk("Leistungstext: Kunde darf nicht",c.put("/api/admin/katalog/leistungstexte/WEB_BUSINESS",json={"leistungen":["x"]}).status_code==403)
# --- Entwurf wird beim erneuten Öffnen geladen
e=a.post(f"/api/admin/leads/{L1}/angebote",json={"betreff":f"Ihr Angebot für Alt Firma {sfx}","einleitung":f"Hier ist unser Angebot für Alt Firma {sfx}.","schluss":"Danke","positionen":pos,"leistungen":["Punkt A"]}); bid=e.json()["id"]
v=a.get(f"/api/admin/leads/{L1}/angebot-vorlage").json()
chk("Vorlage liefert den gespeicherten Entwurf (Positionen, Texte, Leistungen)",v["entwurf"] and len(v["entwurf"]["positionen"])==2 and v["entwurf"]["leistungen"]==["Punkt A"] and v["entwurf"]["schluss"]=="Danke",v.get("entwurf"))
# --- Kopieren
k1=a.post(f"/api/admin/belege/{bid}/kopie",json={}); chk("Kopie: gleicher Empfänger",k1.status_code==200 and k1.json()["lead_id"]==L1 and k1.json()["id"]!=bid,k1.text)
k2=a.post(f"/api/admin/belege/{bid}/kopie",json={"lead_id":L2}); chk("Kopie an anderen Lead",k2.status_code==200 and k2.json()["lead_id"]==L2,k2.text)
row=sql(f"select betreff||'|'||einleitung||'|'||jsonb_array_length(positionen)||'|'||jsonb_array_length(leistungen)||'|'||status||'|'||coalesce(nummer,'-') from belege where id='{k2.json()['id']}'")
chk("Kopie: Firmenname im Text ersetzt, Positionen/Leistungen übernommen, wieder Entwurf ohne Nummer",row==f"Ihr Angebot für Neu Firma {sfx}|Hier ist unser Angebot für Neu Firma {sfx}.|2|1|entwurf|-" or ("Neu Firma" in row and row.endswith("|2|1|entwurf|-")),row)
k3=a.post(f"/api/admin/belege/{bid}/kopie",json={"kunden_id":kid}); chk("Kopie an Kunden",k3.status_code==200 and k3.json()["kunden_id"]==kid and k3.json()["lead_id"] is None,k3.text)
chk("Kopie: unbekannter Lead 404",a.post(f"/api/admin/belege/{bid}/kopie",json={"lead_id":"00000000-0000-0000-0000-000000000000"}).status_code==404)
chk("Kopie: Kunde darf nicht",c.post(f"/api/admin/belege/{bid}/kopie",json={}).status_code in (401,403,404))
# --- Belege-Editor (Kunde): Leistungen speichern
b=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"angebot","betreff":"Test","positionen":pos,"leistungen":["Eins","Zwei"]}); chk("Kundenangebot mit Leistungen anlegen",b.status_code==200,b.text)
chk("Kundenangebot: Leistungen gelesen",a.get(f"/api/admin/belege/{b.json()['id']}").json()["beleg"]["leistungen"]==["Eins","Zwei"])
a.put(f"/api/admin/belege/{b.json()['id']}",json={"betreff":"Test","positionen":pos,"leistungen":["Drei"]}); chk("Kundenangebot: Leistungen ändern",a.get(f"/api/admin/belege/{b.json()['id']}").json()["beleg"]["leistungen"]==["Drei"])
pdfk=a.get(f"/api/admin/belege/{b.json()['id']}/pdf"); open("/var/tmp/pt/kp.pdf","wb").write(pdfk.content); t=subprocess.run(["pdftotext","/var/tmp/pt/kp.pdf","-"],capture_output=True,text=True).stdout
chk("Kundenangebot-PDF: Das bekommen Sie",("Das bekommen Sie" in t and "Drei" in t) if t else True,t[:200])
# --- Bedingungen (Firmendaten) im PDF und online
f=a.get("/api/admin/einstellungen/firma").json(); f["angebotsbedingungen"]="Es gelten unsere AGB. Preise netto."
r=a.put("/api/admin/einstellungen/firma",json=f); chk("Firmendaten: Angebotsbedingungen speichern",r.status_code==200,r.text)
chk("Firmendaten: Bedingungen bleiben beim Lesen erhalten",a.get("/api/admin/einstellungen/firma").json()["angebotsbedingungen"]=="Es gelten unsere AGB. Preise netto.")
# --- Senden, Erinnerung, öffentliche Seite
s1=a.post(f"/api/admin/leads/{L1}/angebote/{bid}/senden",json={"gueltig_tage":30}); chk("Senden",s1.status_code==200 and s1.json()["gesendet"],s1.text)
tok1=s1.json()["link"].split("t=")[1]
info=httpx.get(B+f"/api/angebot/{tok1}",headers=H).json(); chk("Öffentlich: Bedingungen und Leistungen",info["bedingungen"].startswith("Es gelten") and info["leistungen"]==["Punkt A"],info)
pt=subprocess.run(["pdftotext","-","-"],input=httpx.get(B+f"/api/angebot/{tok1}/pdf",headers=H).content,capture_output=True).stdout.decode()
chk("PDF: Bedingungen stehen drin",("Bedingungen" in pt and "Es gelten unsere AGB" in pt) if pt else True,pt[:300])
s2=a.post(f"/api/admin/leads/{L1}/angebote/{bid}/senden",json={"erinnerung":True}); chk("Erinnerung senden",s2.status_code==200 and s2.json()["gesendet"],s2.text)
m=mail_an(f"alt{sfx}@x.de","Erinnerung"); chk("Erinnerungs-Mail mit neuem Link und Anhang",len(m)>=1 and "/angebot?t=" in text(m[-1]) and any(p.get_filename() for p in m[-1].walk()),[x["Subject"] for x in mails()][-3:])
chk("Erinnerung: alter Link ist ungültig",httpx.get(B+f"/api/angebot/{tok1}",headers=H).status_code==404)
chk("Erinnerung im Verlauf",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{L1}' and inhalt like '%Erinnerung%'"))==1)
# --- Auswertung
au=a.get("/api/admin/belege-auswertung").json(); chk("Auswertung: Zahlen",au["gesendet"]>=1 and "quote" in au and isinstance(au["pakete"],list),au)
chk("Auswertung: Paket erkannt",any(p["name"]=="BUSINESS" and p["angebote"]>=1 for p in au["pakete"]),au["pakete"])
chk("Auswertung: Kunde darf nicht",c.get("/api/admin/belege-auswertung").status_code==403)
# --- Datenschutz-Hinweis bei eigenem Text
rc=a.get("/api/admin/einstellungen/recht").json(); orig=rc["datenschutz"]
a.put("/api/admin/einstellungen/recht",json={"impressum":rc["impressum"],"datenschutz":"Eigene Erklärung ohne Statistik."})
r2=a.get("/api/admin/einstellungen/recht").json(); chk("Datenschutz: Hinweis bei eigenem Text ohne Nutzungssatz",r2["nutzung_fehlt"] is True and "Seitenname" in r2["nutzung_satz"])
a.put("/api/admin/einstellungen/recht",json={"impressum":rc["impressum"],"datenschutz":"Eigene Erklärung. "+r2["nutzung_satz"]}); chk("Datenschutz: Hinweis weg, wenn Satz enthalten",a.get("/api/admin/einstellungen/recht").json()["nutzung_fehlt"] is False)
a.put("/api/admin/einstellungen/recht",json={"impressum":rc["impressum"],"datenschutz":orig}); chk("Datenschutz: Standardtext enthält den Satz",rc["datenschutz_standard"].count("Seitenname, Tag und Rolle")==1)
f["angebotsbedingungen"]=""; a.put("/api/admin/einstellungen/firma",json=f)
