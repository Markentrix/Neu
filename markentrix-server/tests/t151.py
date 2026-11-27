"""Kundenportal: Beratungsgespräch selbst buchen, Dokumente-Ablage."""
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
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Testbank","zahlungsziel_tage":14,"mwst_satz":19,"kleinunternehmer":False,"steuernummer":"12/345/67890"})
sfx=str(int(time.time()))
k=a.post("/api/admin/kunden",json={"firma":f"Beratkunde {sfx}","ansprechpartner":"Bea Berat","email":f"ber{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"ber{sfx}@k.de"),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); c.post("/api/login",json={"email":f"ber{sfx}@k.de","password":"InhaberPasswort1"})
d=c.get("/api/kunde/beratung").json(); chk("Buchung aus: keine Zeiten",d["aktiv"] is False and d["tage"]==[],d)
chk("Buchen bei ausgeschalteter Buchung: 409",c.post("/api/kunde/beratung",json={"start":"2030-01-01T10:00:00+01:00"}).status_code==409)
a.put("/api/admin/einstellungen/buchung",json={"aktiv":True,"dauer":30,"tage":30,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":12,"ort":"Telefon","erlaubte_seiten":"markentrix.de"})
d=c.get("/api/kunde/beratung").json(); chk("Freie Zeiten da",d["aktiv"] and len(d["tage"])>=5 and d["meine"]==[],d.get("tage",[])[:1])
s=d["tage"][1]["slots"][2]["start"]
chk("Ohne Anmeldung nicht möglich",httpx.post(B+"/api/kunde/beratung",headers=H,json={"start":s}).status_code in (401,403))
chk("Zeit außerhalb der Slots abgelehnt",c.post("/api/kunde/beratung",json={"start":"2031-01-01T03:07:00+01:00"}).status_code==409)
r=c.post("/api/kunde/beratung",json={"start":s,"nachricht":"Website und Telefon"}); chk("Gebucht",r.status_code==200,r.text)
g=sql(f"select status||'|'||gebucht_von||'|'||coalesce(lead_id::text,'-')||'|'||nachricht from gespraechstermine where kunden_id='{k['id']}'"); chk("Im Kalender als Kunden-Gespräch",g=="gebucht|kundenportal|-|Website und Telefon",g)
time.sleep(1.5); m=[x for x in mails() if f"ber{sfx}@k.de" in str(x["To"]) and any(p.get_filename()=="termin.ics" for p in x.walk())]; chk("Bestätigung mit Einladung",bool(m))
d=c.get("/api/kunde/beratung").json(); chk("Danach: eigener Termin statt Zeiten",len(d["meine"])==1 and d["tage"]==[] and "absagen" in d["meine"][0],d)
chk("Zweite Buchung abgelehnt",c.post("/api/kunde/beratung",json={"start":s}).status_code==409)
kal=a.get("/api/admin/kalender",params={"von":s[:10],"bis":s[:10]}); chk("Admin-Kalender zeigt es",kal.status_code==200 and f"Beratkunde {sfx}" in kal.text,kal.text[:200])
# Ablage
a.post(f"/api/admin/kunden/{k['id']}/belege",json={"art":"rechnung","betreff":"Ablagetest","positionen":[{"text":"Leistung","menge":1,"einheit":"","preis_cent":10000}]})
rid=a.get(f"/api/admin/kunden/{k['id']}/belege").json()[0]["id"]; a.post(f"/api/admin/belege/{rid}/ausstellen"); a.post(f"/api/admin/belege/{rid}/senden")
l=c.get("/api/kunde/ablage"); chk("Ablage lädt",l.status_code==200,l.text); l=l.json()
chk("Ablage enthält die Rechnung mit PDF-Link",any(x["art"]=="Rechnung" and "Ablagetest" in x["titel"] and x["link"].endswith("/pdf") for x in l),l)
pdf=c.get([x for x in l if x["art"]=="Rechnung"][0]["link"]); chk("PDF-Link funktioniert",pdf.status_code==200 and pdf.content[:4]==b"%PDF")
import base64
a.post("/api/admin/agb",json={"version":"Stand T151","datei_base64":"data:application/pdf;base64,"+base64.b64encode(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n").decode(),"datei_name":"agb.pdf","mitsenden":False,"login_pflicht":False})
l=c.get("/api/kunde/ablage").json(); chk("Ablage enthält die AGB",any(x["art"]=="AGB" and "Stand T151" in x["titel"] for x in l),l)
chk("Ohne Anmeldung keine Ablage",httpx.get(B+"/api/kunde/ablage",headers=H).status_code in (401,403))
