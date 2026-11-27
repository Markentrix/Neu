"""AGB: Upload, Bestätigung bei der Anmeldung (Nachweis), Mitsenden an Angebots- und Rechnungsmails, Link auf der Angebotsseite."""
import httpx, time, re, email, subprocess, base64
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
def anhaenge(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]): return [p.get_filename() for p in m.walk() if p.get_filename()], text(m)
    return [],""
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False,"steuernummer":"12/345/67890"})
sfx=str(int(time.time()))
PDF=b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
b64=lambda b: "data:application/pdf;base64,"+base64.b64encode(b).decode()
sql("update agb_versionen set aktiv=false")
chk("Ohne AGB: /api/agb.pdf 404",httpx.get(B+"/api/agb.pdf").status_code==404)
chk("Kein PDF abgelehnt",a.post("/api/admin/agb",json={"version":"X","datei_base64":"data:text/plain;base64,"+base64.b64encode(b"hallo").decode()}).status_code==400)
# Kunde anlegen (vor AGB): Anmeldung ohne Pflicht
k=a.post("/api/admin/kunden",json={"firma":f"Agbkunde {sfx}","ansprechpartner":"Tina Test","email":f"agb{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"agb{sfx}@k.de"),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); c.post("/api/login",json={"email":f"agb{sfx}@k.de","password":"InhaberPasswort1"})
chk("Ohne AGB: nichts zu bestätigen",c.get("/api/me").json()["agb_offen"] is None)
r=a.post("/api/admin/agb",json={"version":"Stand 11/2026","datei_base64":b64(PDF),"datei_name":"AGB Markentrix.pdf","mitsenden":True,"login_pflicht":True}); chk("AGB hochgeladen",r.status_code==200,r.text); v1=r.json()["id"]
d=a.get("/api/admin/agb").json(); chk("Liste: eine aktive Version",[x["aktiv"] for x in d["versionen"]].count(True)==1 and d["versionen"][0]["version"]=="Stand 11/2026",d)
p=httpx.get(B+"/api/agb.pdf"); chk("Öffentlich als PDF abrufbar",p.status_code==200 and p.content==PDF and p.headers["content-type"]=="application/pdf")
chk("Admin: Datei abrufbar",a.get(f"/api/admin/agb/{v1}/datei").content==PDF)
# Bestätigung
me=c.get("/api/me").json(); chk("Inhaber muss bestätigen",me["agb_offen"] and me["agb_offen"]["id"]==v1 and me["agb_offen"]["version"]=="Stand 11/2026",me)
chk("Ohne Haken abgelehnt",c.post("/api/kunde/agb/zustimmen",json={"bestaetigt":False,"agb_id":v1}).status_code==400)
chk("Falsche Version abgelehnt",c.post("/api/kunde/agb/zustimmen",json={"bestaetigt":True,"agb_id":"00000000-0000-0000-0000-000000000000"}).status_code==409)
chk("Admin kann nicht als Kunde bestätigen",a.post("/api/kunde/agb/zustimmen",json={"bestaetigt":True,"agb_id":v1}).status_code in (401,403))
r=c.post("/api/kunde/agb/zustimmen",json={"bestaetigt":True,"agb_id":v1}); chk("Bestätigt",r.status_code==200,r.text)
chk("Danach nichts mehr offen",c.get("/api/me").json()["agb_offen"] is None)
z=sql(f"select version||'|'||(sha256<>'')||'|'||(ip<>'')||'|'||benutzer from agb_zustimmungen where kunden_id='{k['id']}'"); chk("Nachweis gespeichert (Version, Prüfsumme, IP, Benutzer)",z==f"Stand 11/2026|true|true|agb{sfx}@k.de",z)
chk("Admin sieht den Nachweis",any(x["benutzer"]==f"agb{sfx}@k.de" for x in a.get("/api/admin/agb").json()["zustimmungen"]))
# Mitarbeiter-Zugang wird nicht gesperrt: nur Inhaber (hier geprüft über Kunde ohne Haken im Datenmodell)
# Neue Version: erneut bestätigen
r=a.post("/api/admin/agb",json={"version":"Stand 12/2026","datei_base64":b64(PDF+b"%neu\n"),"datei_name":"AGB2.pdf"}); v2=r.json()["id"]
chk("Neue Version: wieder offen",c.get("/api/me").json()["agb_offen"]["version"]=="Stand 12/2026")
chk("Alte Version nicht mehr aktiv",sql(f"select aktiv from agb_versionen where id='{v1}'")=="f")
a.put(f"/api/admin/agb/{v2}",json={"login_pflicht":False}); chk("Ohne Pflicht: nichts offen",c.get("/api/me").json()["agb_offen"] is None)
a.put(f"/api/admin/agb/{v2}",json={"login_pflicht":True})
# Mails: Rechnung mit AGB-Anhang
r=a.post(f"/api/admin/kunden/{k['id']}/belege",json={"art":"rechnung","betreff":"Test","positionen":[{"text":"Leistung","menge":1,"einheit":"","preis_cent":10000}]}); rid=r.json()["id"]
a.post(f"/api/admin/belege/{rid}/ausstellen"); r=a.post(f"/api/admin/belege/{rid}/senden"); chk("Rechnung gesendet",r.json().get("gesendet") is True,r.text)
an,t=anhaenge(f"agb{sfx}@k.de"); chk("Rechnung: PDF und AGB im Anhang",len(an)>=2 and "AGB2.pdf" in an,an); chk("Mailtext nennt die AGB vor der Grußformel","AGB" in t and t.index("AGB")<t.index("Viele Grüße"),t[-300:])
a.put(f"/api/admin/agb/{v2}",json={"mitsenden":False}); sql(f"update belege set status='gestellt' where id='{rid}'")
n0=len(mails()); a.post(f"/api/admin/belege/{rid}/senden"); an,t=anhaenge(f"agb{sfx}@k.de")
chk("Ohne „mitsenden“: kein AGB-Anhang und kein AGB-Hinweis",len(mails())>n0 and "AGB2.pdf" not in an and "Allgemeinen Geschäftsbedingungen" not in t,(an,t[-200:]))
# Angebotsseite zeigt den Link
a.put(f"/api/admin/agb/{v2}",json={"mitsenden":True})
l=a.post("/api/admin/leads",json={"firma":f"Agblead {sfx}","email":f"agblead{sfx}@test-x.de","ort":"Celle"}).json()["id"]
