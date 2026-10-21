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
sfx=str(int(time.time())+145)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"mwst_satz":19,"steuernummer":"12/345/67890"})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import json
Q="/var/tmp/pt/b/queue"
kA,cA,mA=neuer_kunde("Sta"); kB,cB,mB=neuer_kunde("Stb")
sql(f"update kunden set status='aktiv' where id in ('{kA}','{kB}')")
dom=f"status{sfx}.de"
sql(f"insert into websites (kunden_id, domain, art, status, letzte_veroeffentlichung) values ('{kA}','{dom}','live','live',now()-interval '2 days')")
sql(f"insert into website_wacht (domain, kunden_id, ok, seite_ok, api_ok, ms, cert_tage, seit) values ('{dom}','{kA}',true,true,true,120,55,now())")
sql(f"insert into website_wacht_tag (domain, tag, geprueft, ok) values ('{dom}', current_date, 100, 99)")
sql(f"insert into website_qualitaet (domain, kunden_id, seiten, median_ms, startseite_kb, tote, langsam) values ('{dom}','{kA}',5,240,80,'[]','[]')")
sql(f"insert into audit_log (kunden_id, aktion, details) values ('{kA}','website_hochgeladen','{{}}')")
json.dump({"tage":["2026-10-20_0315","2026-10-19_0315"],"db_tage":[]},open(Q+"/sicherungen.json","w"))
d=cA.get("/api/kunde/statusseite").json(); chk("Standard: aus, kein Link",d=={"aktiv":False,"url":None},d)
chk("Ohne Anmeldung kein Zugriff auf die Einstellung",httpx.get(B+"/api/kunde/statusseite").status_code in (401,403))
r=cA.put("/api/kunde/statusseite",json={"aktiv":True}); u=r.json()["url"]; chk("Einschalten liefert Link",r.status_code==200 and "/status/" in u and len(u.split("/status/")[1])>=24,r.text)
tok=u.split("/status/")[1]
p=httpx.get(B+"/status/"+tok)
chk("Öffentliche Seite ohne Anmeldung",p.status_code==200 and "text/html" in p.headers["content-type"],p.status_code)
t=p.text
for n,k in (("Domain",dom),("Erreichbar","Erreichbar"),("Prozent","99,0 %"),("Zertifikat","noch 55 Tage"),("Ladezeit","240 ms"),("Veröffentlicht","Zuletzt veröffentlicht")): chk("Seite zeigt "+n,k in t,t[t.find("<main>"):][:900])
chk("Seite zeigt Sicherung und Änderungen","20.10.2026" in t and "Website aktualisiert" in t)
chk("Nicht indexierbar, nicht zwischenspeichern","noindex" in p.headers.get("x-robots-tag","") and "no-store" in p.headers.get("cache-control",""))
chk("Keine internen Daten (Kundennummer, E-Mail, Rechnungen)",mA not in t and "Rechnung" not in t)
sql(f"update website_wacht set ok=false where domain='{dom}'"); t=httpx.get(B+"/status/"+tok).text
chk("Störung wird angezeigt","Aktuell gestört" in t)
chk("Falscher Token: 404",httpx.get(B+"/status/"+"x"*30).status_code==404 and httpx.get(B+"/status/kurz").status_code==404)
chk("Anderer Kunde sieht fremde Daten nicht",dom not in httpx.get(B+"/status/"+cB.put("/api/kunde/statusseite",json={"aktiv":True}).json()["url"].split("/status/")[1]).text)
r=cA.post("/api/kunde/statusseite/neu",json={}); u2=r.json()["url"]; chk("Neuer Link",r.status_code==200 and u2!=u)
chk("Alter Link ungültig",httpx.get(B+"/status/"+tok).status_code==404 and httpx.get(B+"/status/"+u2.split("/status/")[1]).status_code==200)
cA.put("/api/kunde/statusseite",json={"aktiv":False}); chk("Ausschalten: Link tot",httpx.get(B+"/status/"+u2.split("/status/")[1]).status_code==404)
chk("Neuer Link ohne Statusseite: 404",cB.post("/api/kunde/statusseite/neu",json={}).status_code==200 and True)
sql(f"update kunden set status='gekuendigt' where id='{kB}'"); chk("Gekündigter Kunde: Seite aus",httpx.get(B+"/status/"+cB.get("/api/kunde/statusseite").json()["url"].split("/status/")[1]).status_code==404)
