"""Admin: Dienst-Fehler in der Kunden-Ampel und Fehlerhilfe für Google-Abfragen (Places API)."""
import httpx, time, re, email, subprocess, json
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
sfx=str(int(time.time())+3600)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


k=a.post("/api/admin/kunden",json={"firma":f"Ampelfehler {sfx}","ansprechpartner":"Hans","email":f"ampel{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle"}).json()["id"]
def ampel():
    return [x for x in a.get("/api/admin/kunden-ampel").json()["kunden"] if x["id"]==k][0]
sql(f"insert into website_dienste (kunden_id) select '{k}' where not exists (select 1 from website_dienste where kunden_id='{k}')")
sql(f"insert into website_ereignisse (kunden_id,art,ok,hinweis) values ('{k}','bewertungen',false,'Google lehnt die Abfrage ab. Google sagt: PERMISSION_DENIED: Permission denied on the service.')")
x=ampel(); chk("Ampel: Dienst-Fehler macht den Kunden rot",x["farbe"]=="rot" and any("bewertungen" in t for t in x["rot"]),x)
sql(f"insert into website_ereignisse (kunden_id,art,ok,hinweis) values ('{k}','bewertungen',true,null)")
x=ampel(); chk("Ampel: nach erfolgreichem Abruf nicht mehr rot wegen des Dienstes",not any("bewertungen" in t for t in x["rot"]),x)
sql(f"insert into website_ereignisse (kunden_id,art,ok,hinweis,zeit) values ('{k}','kontakt',false,'alt',now()-interval '20 days')")
x=ampel(); chk("Ampel: Fehler älter als 7 Tage zählt nicht",not any("kontakt" in t for t in x["rot"]),x)
e=a.post("/api/admin/fehlerhilfe/erklaeren",json={"text":"Google lehnt die Abfrage ab (Schlüssel, Abrechnung oder Places-API (New) bei Markentrix nicht aktiv). Google sagt: PERMISSION_DENIED: Permission denied on the service."}).json()
chk("Fehlerhilfe: Google-Fehler erkannt",e.get("bekannt") and "Google" in e["titel"],e)
chk("Fehlerhilfe: kein install.sh-Tipp bei Google-Fehler","install.sh" not in json.dumps(e),e)
chk("Fehlerhilfe: nennt Places API (New)","Places API (New)" in json.dumps(e,ensure_ascii=False))
e2=a.post("/api/admin/fehlerhilfe/erklaeren",json={"text":"PermissionError: [Errno 13] Permission denied: '/srv/sites/x'"}).json()
chk("Fehlerhilfe: Dateirechte weiter erkannt",e2.get("bekannt") and "install.sh" in json.dumps(e2),e2)
