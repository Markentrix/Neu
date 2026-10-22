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
sfx=str(int(time.time())+273)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Gutea"); kB,cB,mB=neuer_kunde("Guteb")
dom=f"gutschein{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom})
def pub(body):
    return W.post("/siteapi/api/anfrage",headers={"Content-Type":"application/json","Origin":"https://"+dom,"User-Agent":"Mozilla/5.0 Test"},content=json.dumps(body).encode())
# ---- Gutschein-Ablauf
G=lambda **kw:{**{"typ":"gutschein","name":"Greta Gast","email":f"greta{sfx}@besucher.de","betrag":"50 €","empfaenger":"Oma Lotte","widmung":"Alles Gute","einwilligung":True},**kw}
cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"Neue Anfrage","name":"Firma A"})
chk("Karte leer, solange nichts angefragt",cA.get("/api/kunde/website-dienste/gutscheine").json()["gutscheine"]==[])
r=pub(G()); chk("Gutschein mit „50 €“ wird angenommen",r.status_code==200 and r.json().get("ok"),r.text); ref=r.json().get("ref","")
chk("Referenz beginnt mit G",ref.startswith("G"),ref)
r=pub(G(betrag="49,90 EUR",email=f"zwei{sfx}@besucher.de")); chk("Betrag „49,90 EUR“ akzeptiert",r.status_code==200,r.text)
r=pub(G(betrag="abc")); chk("Unsinniger Betrag abgelehnt",r.status_code==422,r.text)
r=pub(G(betrag="0")); chk("Betrag 0 abgelehnt",r.status_code==422,r.text)
r=pub(G(betrag="",email=f"drei{sfx}@besucher.de")); chk("Ohne Betrag erlaubt (Inhaber trägt ihn ein)",r.status_code==200,r.text)
l=cA.get("/api/kunde/website-dienste/gutscheine").json(); chk("Drei Anfragen sichtbar",len(l["gutscheine"])==3,l)
chk("PayPal noch nicht bereit",l["paypal_bereit"] is False)
g1=[x for x in l["gutscheine"] if x["ref"]==ref][0]; chk("Betrag 50,00 gelesen",g1["betrag"]=="50.00" and g1["empfaenger"]=="Oma Lotte" and g1["status"]=="angefragt",g1)
gz=[x for x in l["gutscheine"] if x["email"].startswith("zwei")][0]; chk("49,90 gelesen",gz["betrag"]=="49.90",gz)
g3=[x for x in l["gutscheine"] if x["email"].startswith("drei")][0]
U="/api/kunde/website-dienste/gutscheine/"
r=cA.post(U+g1["id"]+"/zahlungslink",json={}); chk("Zahlungslink ohne PayPal.Me: Hinweis",r.status_code==409,r.text)
r=cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/firmaa"}); chk("PayPal.Me eintragen",r.status_code==200,r.text)
r=cA.post(U+g1["id"]+"/zahlungslink",json={}); chk("Zahlungslink senden",r.status_code==200,r.text)
m=mail_an(f"greta{sfx}@besucher.de","Zahlungslink"); chk("Mail mit PayPal.Me-Link und Betrag",len(m)==1 and "https://paypal.me/firmaa/50.00EUR" in text(m[0]) and "Oma Lotte" in text(m[0]),[text(x) for x in m])
chk("Mail im Namen der Firma, ohne KI-Name",m and "Gutea" in text(m[0]) and "Claude" not in text(m[0]) and "Markentrix-Team" not in text(m[0]))
chk("Status: wartet auf Zahlung",sql(f"select status from website_gutscheine where ref='{ref}'")=="zahlungslink_gesendet")
r=cA.post(U+g3["id"]+"/zahlungslink",json={}); chk("Ohne Betrag: Hinweis",r.status_code==400,r.text)
r=cA.post(U+g3["id"]+"/zahlungslink",json={"betrag":"25"}); chk("Betrag beim Senden eintragen",r.status_code==200,r.text)
chk("Betrag gespeichert",sql(f"select betrag from website_gutscheine where id='{g3['id']}'")=="25.00")
r=cA.post(U+g1["id"]+"/code",json={"code":"x"}); chk("Zu kurzer Code abgelehnt",r.status_code in (400,422),r.text)
r=cA.post(U+g1["id"]+"/code",json={"code":"<b>böse</b>"}); chk("Code mit Sonderzeichen abgelehnt",r.status_code==400,r.text)
r=cA.post(U+g1["id"]+"/code",json={"code":"LOTTE-2026","hinweis":"Gültig bis Ende 2027."}); chk("Gutschein senden",r.status_code==200,r.text)
m=mail_an(f"greta{sfx}@besucher.de","LOTTE-2026"); chk("Mail mit Code",len(m)==1 and "Gutschein-Code: LOTTE-2026" in text(m[0]) and "Gültig bis Ende 2027." in text(m[0]) and "50,00 €" in text(m[0]),[text(x) for x in m])
chk("Status: gesendet",sql(f"select status||code from website_gutscheine where ref='{ref}'")=="gesendetLOTTE-2026")
r=cA.post(U+gz["id"]+"/storno"); chk("Stornieren",r.status_code==200,r.text)
r=cA.post(U+gz["id"]+"/code",json={"code":"NIX-1234"}); chk("Stornierte Anfrage: kein Code",r.status_code==409,r.text)
r=cA.post(U+g1["id"]+"/storno"); chk("Gesendeten Gutschein nicht stornierbar",r.status_code==409,r.text)
r=cB.post(U+g1["id"]+"/code",json={"code":"FREMD-1234"}); chk("Anderer Kunde kommt nicht heran",r.status_code==404,r.text)
chk("Anderer Kunde sieht nichts",cB.get("/api/kunde/website-dienste/gutscheine").json()["gutscheine"]==[])
c2=httpx.Client(base_url=B); chk("Ohne CSRF-Kopf abgelehnt",c2.post(U+g1["id"]+"/code",json={"code":"ABC-123"}).status_code in (401,403))
chk("Anfragen liegen auch unter „Anfragen“",int(sql(f"select count(*) from anfragen where kunden_id='{kA}' and nachricht like 'Gutschein%'"))==3)
chk("Audit geschrieben",int(sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion like 'website_gutschein%'"))>=3)
