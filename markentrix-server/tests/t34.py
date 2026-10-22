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
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":f"0511 {time.time_ns()}","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200
kid,c,mail=neuer_kunde("Reise"); kid2,c2,_m=neuer_kunde("Zweit")
def anf(k,name,kontakt,quelle="website",status="neu",tage=1): return sql(f"INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,erstellt_am,benachrichtigt) VALUES ('{k}','{name}','{kontakt}','Test','{quelle}','{status}',now()-interval '{tage} days',true) RETURNING id").split("\n")[0]
for i in range(12): anf(kid,f"A{i}",f"a{i}@x.de","telefon" if i%3==0 else "website","beantwortet" if i<6 else "neu",tage=i+1)
anf(kid2,"Fremd","f@x.de")
sql(f"INSERT INTO termine (kunden_id,titel,beginn,status) VALUES ('{kid}','T1',now()-interval '3 days','erledigt'),('{kid}','T2',now()-interval '5 days','geplant')")

# ---- Diagramme
d=c.get("/api/kunde/diagramme"); chk("Diagramme: 200",d.status_code==200,d.text[:300]); d=d.json()
chk("Diagramme: 26 Wochen",len(d["wochen"])==26,len(d["wochen"]))
chk("Diagramme: Summe Anfragen = 12 (abgeschlossene Wochen + laufende, nur eigene)",sum(w["anfragen"] for w in d["wochen"])+d["laufende_woche"]["anfragen"]==12,d["wochen"][-4:])
chk("Diagramme: Quellen telefon 4 / website 8",d["quellen"].get("telefon")==4 and d["quellen"].get("website")==8,d["quellen"])
chk("Diagramme: Wochentage Summe 12",sum(d["wochentage"])==12 and len(d["wochentage"])==7)
chk("Diagramme: Trichter",d["trichter"]["anfragen"]==12 and d["trichter"]["beantwortet"]==6 and d["trichter"]["termine"]==2 and d["trichter"]["erledigt"]==1,d["trichter"])
chk("Diagramme: Klartext nennt Quelle und Grundlage",any("website" in x.lower() and "8 von 12" in x for x in d["klartext"]),d["klartext"])
d2=c2.get("/api/kunde/diagramme").json(); chk("Diagramme: wenig Daten -> ehrlicher Satz",len(d2["klartext"])==1 and "reichen" in d2["klartext"][0],d2["klartext"])
chk("Diagramme: Fremdkunde sieht nur eigene",sum(d2["quellen"].values())==1)

# ---- Startliste mit Phasen
sl=c.get("/api/kunde/startliste").json(); chk("Startliste: Phasen vorhanden",sl["aktiv"] and len(sl["phasen"])==4 and sl["aktuelle_phase"] in ("start","material","aufbau","live"),sl)
chk("Startliste: jeder Punkt hat Phase",all(p["phase"] for p in sl["punkte"]))

# ---- Onboarding-Board
b=a.get("/api/admin/onboarding/board"); chk("Board: 200",b.status_code==200,b.text[:300]); b=b.json()
alle=[k for s in b["spalten"] for k in s["kunden"]]
chk("Board: beide Kunden genau einmal",sum(1 for k in alle if k["id"] in (kid,kid2))==2,[k["firma"] for k in alle])
chk("Board: Spalten Start..Live",[s["schluessel"] for s in b["spalten"]][:4]==["start","material","aufbau","live"])
chk("Board: Karte mit Fortschritt",all("fertig" in k and "gesamt" in k and "naechster" in k for k in alle))
chk("Board: Kunde darf nicht",c.get("/api/admin/onboarding/board").status_code==403)

# ---- Pipeline
def lead_st(f,st): i=lead(f+str(time.time_ns())); sql(f"UPDATE leads SET status='{st}' WHERE id='{i}'"); return i
for st in ["neu","neu","kontaktiert","termin","angebot","angebot","gewonnen"]: lead_st("PL",st)
for st in ["gewonnen"]*5+["verloren"]*5: lead_st("PE",st)
pl=a.get("/api/admin/pipeline"); chk("Pipeline: 200",pl.status_code==200,pl.text[:300]); pl=pl.json()
sp={s["status"]:s for s in pl["spalten"]}
chk("Pipeline: Spaltenzähler >= erwartet",sp["angebot"]["anzahl"]>=2 and sp["termin"]["anzahl"]>=1,{k:v["anzahl"] for k,v in sp.items()})
chk("Pipeline: Spalte hat höchstens 25 Leads",all(len(s["leads"])<=25 for s in pl["spalten"]))
chk("Pipeline: Trichter kumulativ fallend",all(pl["trichter"][i]["anzahl"]>=pl["trichter"][i+1]["anzahl"] for i in range(5)),pl["trichter"])
chk("Pipeline: Quote berechnet (>=8 entschieden)",pl["quote"] is not None and pl["entschieden"]>=10,pl)
chk("Pipeline: Prognose Felder",set(pl["prognose"])>={"angebote","quote","schnitt_cent","erwartet_cent","hinweis"},pl["prognose"])
chk("Pipeline: Prognose ohne Kundenwert -> Hinweis statt Zahl",pl["prognose"]["erwartet_cent"] is None and pl["prognose"]["hinweis"],pl["prognose"])
chk("Pipeline: Vertriebler-Filter ungültig 400/404",a.get("/api/admin/pipeline?vertriebler=xyz").status_code in (400,404))
chk("Pipeline: Vertriebler-Filter leer ok",a.get(f"/api/admin/pipeline?vertriebler={p}").json()["spalten"][0]["anzahl"]==0)
chk("Pipeline: Kunde darf nicht",c.get("/api/admin/pipeline").status_code==403)
l1=lead("Eigener"); a.patch(f"/api/admin/leads/{l1}",json={"status":"termin"}); sql(f"UPDATE leads SET vertriebspartner_id='{p}' WHERE id='{l1}'")
vp=v.get("/api/vertrieb/pipeline"); chk("Vertriebler-Pipeline: nur eigene",vp.status_code==200 and sum(s["anzahl"] for s in vp.json()["spalten"])==1 and "prognose" not in vp.json(),vp.text[:300])
chk("Vertriebler-Pipeline: Kunde 403",c.get("/api/vertrieb/pipeline").status_code==403)

# ---- Suche
sql(f"INSERT INTO termine (kunden_id,titel,beginn,status,kontakt_name) VALUES ('{kid}','Zahnriemen',now()+interval '2 days','geplant','Zora Zufall')")
r=a.get("/api/admin/suche?q=Zora").json()["gruppen"]; chk("Suche: Termin gefunden",any(g["art"]=="Termine" and g["treffer"] for g in r),r)
r=a.get("/api/admin/suche?q=Vera").json()["gruppen"]; chk("Suche: Vertriebler gefunden mit Partner-Link",any(g["art"]=="Vertriebler" and g["treffer"][0]["link"].startswith("#partner/") for g in r),r)
r=a.get("/api/admin/suche?q=a5@x.de").json()["gruppen"]; chk("Suche: Kundenanfrage per Kontakt",any(g["art"]=="Kundenanfragen" for g in r),r)

# ---- Sammelaktion rückgängig
r=a.post("/api/admin/kunden/bulk",json={"aktion":"aufgabe","ids":[kid,kid2],"titel":"Sammel-Test"}).json()
chk("Bulk: sammel_id geliefert",r.get("angelegt")==2 and r.get("sammel_id"),r)
chk("Bulk: Aufgaben vorhanden",sql(f"SELECT count(*) FROM aufgaben WHERE sammel_id='{r['sammel_id']}'")=="2")
sql(f"UPDATE aufgaben SET status='erledigt' WHERE sammel_id='{r['sammel_id']}' AND kunden_id='{kid2}'")
u=a.post("/api/admin/kunden/bulk/rueckgaengig",json={"sammel_id":r["sammel_id"]}); chk("Rückgängig: nur offene entfernt",u.status_code==200 and u.json()["entfernt"]==1,u.text)
chk("Rückgängig: erledigte bleibt",sql(f"SELECT count(*) FROM aufgaben WHERE sammel_id='{r['sammel_id']}'")=="1")
chk("Rückgängig: ungültige Kennung 400",a.post("/api/admin/kunden/bulk/rueckgaengig",json={"sammel_id":"xyz"}).status_code==400)
chk("Rückgängig: Kunde 403",c.post("/api/admin/kunden/bulk/rueckgaengig",json={"sammel_id":r["sammel_id"]}).status_code==403)
print("t34 fertig")
