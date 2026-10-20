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
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
kid,c,mail=neuer_kunde("Werkstatt"); kid2,c2,_m2=neuer_kunde("Fremd")
def anf(k,name,kontakt,quelle="website",status="neu"): return sql(f"INSERT INTO anfragen (kunden_id,name,kontakt,nachricht,quelle,status,benachrichtigt) VALUES ('{k}','{name}','{kontakt}','Bitte Termin','{quelle}','{status}',true) RETURNING id").split("\n")[0]
a1=anf(kid,"Max Muster","max@x.de"); a2=anf(kid,"Rita","0511 123456","telefon"); a3=anf(kid2,"Fremder","f@x.de")
sql(f"INSERT INTO termine (kunden_id,titel,beginn,status,kontakt_name) VALUES ('{kid}','Reifenwechsel',now()+interval '1 hour','geplant','Max Muster')")
sql(f"INSERT INTO termine (kunden_id,titel,beginn,status,kontakt_name,kontakt_info) VALUES ('{kid}','Inspektion',now()-interval '2 days','erledigt','Karl Kunde','karl@x.de')")

# ---- Heute
h=c.get("/api/kunde/heute"); chk("Heute: 200",h.status_code==200,h.text[:300]); h=h.json()
chk("Heute: 2 Anfragen, 1 Rückruf",len(h["anfragen"])==2 and len(h["rueckrufe"])==1 and h["rueckrufe"][0]["name"]=="Rita",h)
chk("Heute: Fremdanfrage nicht sichtbar",all(x["id"]!=a3 for x in h["anfragen"]))
chk("Heute: Bewertungs-Vorschlag erkannt",h["bewertung_vorschlaege"]==1,h)
chk("Heute: Termin heute/morgen Listen vorhanden","termine_heute" in h and "termine_morgen" in h)

# ---- Entwürfe
e=c.get(f"/api/kunde/anfragen/{a1}/entwuerfe"); chk("Entwürfe: 200",e.status_code==200,e.text[:300]); e=e.json()
chk("Entwürfe: Kanal Mail, Platzhalter ersetzt",e["anfrage"]["kanal"]=="mail" and all("{" not in v["text"] for v in e["vorlagen"]) and "Max Muster" in e["vorlagen"][0]["text"] and "Werkstatt" in e["vorlagen"][0]["text"],e["vorlagen"][0])
chk("Entwürfe: Telefon-Kanal",c.get(f"/api/kunde/anfragen/{a2}/entwuerfe").json()["anfrage"]["kanal"]=="telefon")
chk("Entwürfe: fremde Anfrage 404",c.get(f"/api/kunde/anfragen/{a3}/entwuerfe").status_code==404)
chk("Entwürfe: ungültige ID 404",c.get("/api/kunde/anfragen/xyz/entwuerfe").status_code==404)
v=c.post("/api/kunde/antwortvorlagen",json={"name":"Eigene","text":"Hallo {name}, bei {firma} geht das."}); chk("Eigene Vorlage anlegen",v.status_code==200,v.text)
e=c.get(f"/api/kunde/anfragen/{a1}/entwuerfe").json(); eig=[x for x in e["vorlagen"] if x["eigene"]]
chk("Eigene Vorlage erscheint ausgefüllt",len(eig)==1 and eig[0]["text"].startswith("Hallo Max Muster"),eig)
chk("Fremder Kunde sieht sie nicht",not [x for x in c2.get(f"/api/kunde/anfragen/{a3}/entwuerfe").json()["vorlagen"] if x["eigene"]])
chk("Fremde Vorlage löschen: 404",c2.delete(f"/api/kunde/antwortvorlagen/{v.json()['id']}").status_code==404)
chk("Eigene Vorlage löschen",c.delete(f"/api/kunde/antwortvorlagen/{v.json()['id']}").status_code==200)

# ---- Beantwortet
chk("Beantwortet: ungültiger Kanal 422",c.post(f"/api/kunde/anfragen/{a1}/beantwortet",json={"kanal":"brief"}).status_code==422)
chk("Beantwortet: fremde Anfrage 404",c.post(f"/api/kunde/anfragen/{a3}/beantwortet",json={"kanal":"mail"}).status_code==404)
chk("Beantwortet: ok",c.post(f"/api/kunde/anfragen/{a1}/beantwortet",json={"kanal":"mail"}).status_code==200)
chk("Beantwortet: Status gesetzt",sql(f"SELECT status||antwort_kanal FROM anfragen WHERE id='{a1}'")=="beantwortetmail")
chk("Heute: beantwortete Anfrage verschwindet",all(x["id"]!=a1 for x in c.get("/api/kunde/heute").json()["anfragen"]))

# ---- Bewertungen
b=c.get("/api/kunde/bewertungen").json(); chk("Bewertungen: Standardtext mit {link}","{link}" in b["text"] and b["link"] is None and len(b["vorschlaege"])==1,b)
chk("Bitte ohne Link: 400",c.post("/api/kunde/bewertungen/bitte",json={"name":"Karl Kunde","kontakt":"karl@x.de"}).status_code==400)
chk("Link ohne https: 400",c.put("/api/kunde/bewertungen/einstellung",json={"link":"http://x.de/r"}).status_code==400)
chk("Link mit javascript: 400",c.put("/api/kunde/bewertungen/einstellung",json={"link":"javascript:alert(1)"}).status_code==400)
chk("Text ohne {link}: 400",c.put("/api/kunde/bewertungen/einstellung",json={"link":"https://g.page/r/abc","text":"Bitte bewerten"}).status_code==400)
chk("Link speichern",c.put("/api/kunde/bewertungen/einstellung",json={"link":"https://g.page/r/abc/review"}).status_code==200)
r=c.post("/api/kunde/bewertungen/bitte",json={"name":"Karl Kunde","kontakt":"karl@x.de","ausloeser":"Inspektion"}); chk("Bitte anlegen",r.status_code==200 and "https://g.page/r/abc/review" in r.json()["text"] and "Karl Kunde" in r.json()["text"] and r.json()["kanal"]=="mail",r.text)
bid=r.json()["id"]
chk("Doppelte Bitte (90 Tage): 409",c.post("/api/kunde/bewertungen/bitte",json={"name":"Karl Kunde","kontakt":"karl@x.de"}).status_code==409)
chk("Vorschlag verschwindet nach Bitte",c.get("/api/kunde/bewertungen").json()["vorschlaege"]==[])
chk("Fremder kann nicht freigeben",c2.post(f"/api/kunde/bewertungen/{bid}/freigeben",json={"kanal":"mail"}).status_code==404)
chk("Freigabe: ungültiger Kanal 422",c.post(f"/api/kunde/bewertungen/{bid}/freigeben",json={"kanal":"fax"}).status_code==422)
chk("Freigabe ok",c.post(f"/api/kunde/bewertungen/{bid}/freigeben",json={"kanal":"mail"}).status_code==200)
chk("Status gesendet + Zeit",sql(f"SELECT status||kanal||(gesendet_am IS NOT NULL) FROM bewertungsanfragen WHERE id='{bid}'")=="gesendetmailtrue")
chk("Zweite Freigabe: 404",c.post(f"/api/kunde/bewertungen/{bid}/freigeben",json={"kanal":"mail"}).status_code==404)
r2=c.post("/api/kunde/bewertungen/bitte",json={"name":"Eva","kontakt":"0170 1234567"}).json()
chk("Verwerfen",c.delete(f"/api/kunde/bewertungen/{r2['id']}").status_code==200 and sql(f"SELECT status FROM bewertungsanfragen WHERE id='{r2['id']}'")=="abgelehnt")
b=c.get("/api/kunde/bewertungen").json(); chk("Liste und Zähler",b["gesendet_30d"]==1 and len(b["liste"])==2,b)
chk("Fremder Kunde sieht keine Bitten",c2.get("/api/kunde/bewertungen").json()["liste"]==[])
nl=httpx.Client(base_url=B,headers=H); nl.post("/api/login",json={"email":f"werkstatt{sfx}@k.de","password":"InhaberPasswort1"})
sql(f"UPDATE benutzer SET kunden_rolle='nur_lesen' WHERE email='werkstatt{sfx}@k.de'")
lesen=httpx.Client(base_url=B,headers=H); lesen.post("/api/login",json={"email":f"werkstatt{sfx}@k.de","password":"InhaberPasswort1"})
chk("nur_lesen: Heute ok, Schreiben 403",lesen.get("/api/kunde/heute").status_code==200 and lesen.post("/api/kunde/bewertungen/bitte",json={"name":"X","kontakt":"x@x.de"}).status_code==403)
print("t33 fertig")
