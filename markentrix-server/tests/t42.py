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
sfx=str(int(time.time())+21)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"

import base64, datetime
def avv_ablegen(kid, module, version="2"):
    r=a.post(f"/api/admin/kunden/{kid}/avv",json={"module":module,"hauptvertrag_datum":"2026-10-01"}); assert r.status_code==200,r.text; aid=r.json()["id"]
    pdf=base64.b64encode(a.get(f"/api/admin/avv/{aid}/vorlage.pdf").content).decode()
    r=a.post(f"/api/admin/avv/{aid}/upload",json={"datei_base64":pdf,"datei_name":"avv.pdf","unterschrieben_am":"2026-10-10"}); assert r.status_code==200,r.text
    if version!="2": sql(f"update avv set version='{version}' where id='{aid}'")
    return aid
kA,cA,mA=neuer_kunde("Uava"); kB,cB,mB=neuer_kunde("Uavb"); kC,cC,mC=neuer_kunde("Uavc")
avv_ablegen(kA,["portal","ki_chat"]); avv_ablegen(kB,["portal"]); avv_ablegen(kC,["portal"],version="1")
# ---- alte Fassung erkennen
v=[x["id"] for x in a.get("/api/admin/avv-veraltet").json()]
chk("Kunde mit AVV Version 1 gilt als veraltet, Version 2 nicht",kC in v and kA not in v and kB not in v,v)
d=a.get(f"/api/admin/kunden/{kC}/avv").json(); chk("Kundenkarte kennt veraltet",d["veraltet"] and d["veraltet"]["entwurf_id"] is None and a.get(f"/api/admin/kunden/{kA}/avv").json()["veraltet"] is None,d.get("veraltet"))
chk("Heute-Liste enthält veraltete AVV",any(x["id"]==kC for x in a.get("/api/admin/heute").json()["avv_veraltet"]))
r=a.post(f"/api/admin/kunden/{kC}/avv",json={"module":["portal"],"hauptvertrag_datum":"2026-10-01"}); chk("Version-2-Entwurf anlegen",r.status_code==200,r.text)
chk("Entwurf wird gemeldet",a.get(f"/api/admin/kunden/{kC}/avv").json()["veraltet"]["entwurf_id"]==r.json()["id"])
# ---- Vorschau
r=a.post(f"/api/admin/avv-vorschau/{kA}",json={"module":["portal","domain"],"domain":"vorschau.de"}); txt=""
if r.status_code==200: open("/var/tmp/pt/vs.pdf","wb").write(r.content); txt=subprocess.run(["pdftotext","/var/tmp/pt/vs.pdf","-"],capture_output=True,text=True).stdout
chk("Vorschau-PDF ohne Speichern",r.status_code==200 and r.content[:4]==b"%PDF" and "vorschau.de" in txt,r.text[:200])
chk("Vorschau legt nichts an",len(a.get(f"/api/admin/kunden/{kA}/avv").json()["liste"])==1)
chk("Kunde darf keine Vorschau",cA.post(f"/api/admin/avv-vorschau/{kA}",json={"module":["portal"]}).status_code==403)
# ---- Änderung ankündigen
heute=datetime.date.today()
def aend(**kw):
    o={"art":"neu","name":f"Beispiel Cloud {sfx}","leistung":"Speicherung von Chat-Nachrichten","modul":"ki_chat","ort":"Frankfurt","wirksam_ab":(heute+datetime.timedelta(days=30)).isoformat(),"hinweis":"Nur zur Info."}; o.update(kw); return a.post("/api/admin/uav-aenderungen",json=o)
r=aend(wirksam_ab=(heute+datetime.timedelta(days=10)).isoformat()); chk("Weniger als vier Wochen Vorlauf abgelehnt",r.status_code==400 and "vier Wochen" in r.text,r.text)
chk("Unbekanntes Modul abgelehnt",aend(modul="gibtsnicht").status_code==400)
chk("Kunde darf nicht ankündigen",cA.post("/api/admin/uav-aenderungen",json={}).status_code in (403,422))
r=aend(); chk("Ankündigung nur an Kunden mit KI-Chat",r.status_code==200 and r.json()["kunden"]>=2 and r.json()["gesendet"]>=1,r.text)
la=cA.get("/api/kunde/uav-aenderungen").json(); lb=cB.get("/api/kunde/uav-aenderungen").json(); lc=cC.get("/api/kunde/uav-aenderungen").json()
chk("A (KI-Chat) betroffen, B (nur Portal) nicht, C (Version 1) vorsichtshalber ja",len(la)==1 and len(lb)==0 and len(lc)==1,(la,lb,lc))
chk("Mail an A mit Frist und Portal-Link",len(mail_an(mA,"Unterauftragsverarbeiter"))>=1 and "Beispiel Cloud" in text(mail_an(mA,"Unterauftragsverarbeiter")[-1]) and "#avv" in text(mail_an(mA,"Unterauftragsverarbeiter")[-1]))
chk("B bekommt keine Mail",len(mail_an(mB,"Unterauftragsverarbeiter"))==0)
mid=la[0]["id"]
chk("Widerspruch: Begründung zu kurz",cA.post(f"/api/kunde/uav-aenderungen/{mid}/widerspruch",json={"grund":"nein","name":"Tina Test"}).status_code==422)
chk("Fremder Kunde kann nicht widersprechen",cB.post(f"/api/kunde/uav-aenderungen/{mid}/widerspruch",json={"grund":"Das möchten wir nicht.","name":"Bea Test"}).status_code==404)
r=cA.post(f"/api/kunde/uav-aenderungen/{mid}/widerspruch",json={"grund":"Wir möchten keine Speicherung außerhalb Deutschlands.","name":"Tina Test"}); chk("Widerspruch einlegen",r.status_code==200,r.text)
chk("Zweiter Widerspruch abgelehnt",cA.post(f"/api/kunde/uav-aenderungen/{mid}/widerspruch",json={"grund":"Noch einmal zur Sicherheit.","name":"Tina Test"}).status_code==400)
chk("Team bekommt Meldung über Widerspruch",len(mail_an("chef@test.de","Widerspruch gegen Unterauftragsverarbeiter"))>=1 or len(mail_an("info@markentrix.de","Widerspruch gegen Unterauftragsverarbeiter"))>=1)
l=a.get("/api/admin/uav-aenderungen").json(); e=[x for x in l if x["name"]==f"Beispiel Cloud {sfx}"][0]
chk("Admin sieht Widerspruch",e["widersprueche"]==1 and e["widerspruch_liste"][0]["firma"].startswith("Uava") and "Deutschlands" in e["widerspruch_liste"][0]["widerspruch_grund"],e)
chk("Kundenliste zeigt Widerspruch",cA.get("/api/kunde/uav-aenderungen").json()[0]["widerspruch_am"] is not None)
sql(f"update uav_aenderungen set wirksam_ab=current_date where name='Beispiel Cloud {sfx}'")
chk("Nach Fristablauf kein Widerspruch mehr",cC.post(f"/api/kunde/uav-aenderungen/{lc[0]['id']}/widerspruch",json={"grund":"Zu spät, aber gewollt.","name":"Cora Test"}).status_code==400 and cC.get("/api/kunde/uav-aenderungen").json()[0]["widerspruch_moeglich"] is False)
chk("Audit: Ankündigung und Widerspruch protokolliert",int(sql("select count(*) from audit_log where aktion in ('uav_aenderung_angekuendigt','uav_widerspruch')"))>=2)
