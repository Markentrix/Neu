import httpx, time, re, email, subprocess, io
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain":
            if str(p.get("Content-Transfer-Encoding","")).lower()=="8bit": return p.get_payload()     # kurze Zeilen gehen unkodiert (8bit) raus
            return p.get_payload(decode=True).decode("utf8","replace")
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


import datetime, json
from PIL import Image
buf=io.BytesIO(); Image.new("RGB",(1200,900),(224,122,42)).save(buf,"WEBP"); WEBP=buf.getvalue()
buf=io.BytesIO(); Image.new("RGB",(1200,900),(1,2,3)).save(buf,"PNG"); PNG=buf.getvalue()
kA,cA,mA=neuer_kunde("Shopa"); kB,cB,mB=neuer_kunde("Shopb")
dom=f"shop{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom})
S="/api/kunde/shop"
HK={"Origin":"https://"+dom,"User-Agent":"Mozilla/5.0 Test","Content-Type":"application/json"}
def pub(body,h=None): return W.post("/siteapi/api/anfrage",headers={**HK,**(h or {})},content=json.dumps(body).encode())
def get(p,h=None): return W.get("/siteapi/api"+p,headers=h or {"User-Agent":"Mozilla/5.0 Test"})
cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"Neue Anfrage","name":"Shop A"})
cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"waehrung":"EUR","me_link":"https://paypal.me/shopa"})
# ---- Modul und Zugang
chk("Ohne Modul: Kundenportal gesperrt",cA.get(S).status_code==403)
chk("Ohne Modul: Website bekommt 404",get("/produkte").status_code==404)
for k in (kA,):
    sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{k}','shop',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
d=cA.get(S); chk("Mit Modul: Übersicht leer",d.status_code==200 and d.json()["produkte"]==[] and d.json()["einstellungen"]["aktiv"] is False and d.json()["domains"]==[dom] and d.json()["paypal_bereit"] is True,d.text[:300])
chk("Anderer Kunde ohne Modul gesperrt",cB.get(S).status_code==403)
c2=httpx.Client(base_url=B); chk("Ohne Anmeldung abgelehnt",c2.get(S).status_code in (401,403))
chk("Shop aus: Website bekommt 404",get("/produkte").status_code==404)
# ---- Einstellungen, Farben, Kategorien
r=cA.put(S+"/einstellungen",json={"aktiv":False,"ref_praefix":"SA","versand_pauschale":4.9,"versandfrei_ab":49,"abholung":True,"produktionszeit":"2 bis 4 Werktage","lieferzeit":"2 Tage","gutschein_aktiv":True,"gutschein_min":10,"gutschein_max":100,"gutschein_betraege":[50,10,20]})
chk("Einstellungen speichern",r.status_code==200,r.text)
chk("Präfix klein abgelehnt",cA.put(S+"/einstellungen",json={"ref_praefix":"sa"}).status_code==422)
chk("Min über Max abgelehnt",cA.put(S+"/einstellungen",json={"ref_praefix":"SA","gutschein_min":50,"gutschein_max":10}).status_code==422)
r=cA.post(S+"/farben",json={"name":"Orange Silk (glänzend)","hex":"#e07a2a"}); chk("Farbe anlegen",r.status_code==200,r.text)
chk("Farbe mit Unsinn-Hex abgelehnt",cA.post(S+"/farben",json={"name":"Kaputt","hex":"rot"}).status_code==422)
chk("Doppelte Farbe abgelehnt",cA.post(S+"/farben",json={"name":"Orange Silk (glänzend)","hex":"#e07a2a"}).status_code==409)
cA.post(S+"/farben",json={"name":"Schwarz","hex":"#111111"})
r=cA.post(S+"/kategorien",json={"name":"Wohnen & Deko","sort":1}); chk("Kategorie anlegen",r.status_code==200,r.text)
cA.post(S+"/kategorien",json={"name":"Leer"})
fk=lambda: {f["schluessel"] for f in cA.get(S).json()["farben"]}
chk("Farbschlüssel aus Namen",fk()=={"orange-silk-glaenzend","schwarz"},fk())
# ---- Artikel
P=lambda **kw:{**{"name":"Kleiner Kürbis","preis":0.99,"kategorie":"wohnen-deko","kurz":"Lächelnder Mini-Kürbis","lang":"Lang","material":"PLA+ Silk","masse":"ca. 3,5 cm","gewicht":"ca. 6 g","farben":["orange-silk-glaenzend"],"tags":["neu"],"aktiv":True},**kw}
r=cA.post(S+"/produkte",json=P()); chk("Artikel anlegen",r.status_code==200 and r.json()["schluessel"]=="kleiner-kuerbis",r.text); pid=r.json()["id"]
chk("Doppelter Kurzname abgelehnt",cA.post(S+"/produkte",json=P()).status_code==409)
chk("Unbekannte Farbe abgelehnt",cA.post(S+"/produkte",json=P(name="X",farben=["gibtsnicht"])).status_code==422)
chk("Unbekannte Kategorie abgelehnt",cA.post(S+"/produkte",json=P(name="Y",kategorie="nix")).status_code==422)
chk("Wunschtext ohne Zeichenzahl abgelehnt",cA.post(S+"/produkte",json=P(name="Z",personalisierbar=True,textmax=0)).status_code==422)
chk("Negativer Preis abgelehnt",cA.post(S+"/produkte",json=P(name="N",preis=-1)).status_code==422)
r=cA.post(S+"/produkte",json=P(name="Namensschild",preis=7.5,personalisierbar=True,textlabel="Name",textmax=12,farben=["orange-silk-glaenzend","schwarz"],kategorie=None,tags=[])); pid2=r.json()["id"]
r=cA.post(S+"/produkte",json=P(name="Entwurf",aktiv=False,preis=1)); chk("Entwurf anlegen",r.status_code==200); pid3=r.json()["id"]
r=cA.post(S+"/produkte",json=P(name="Kürbis-Trio",preis=2.79,verwandt=["kleiner-kuerbis","gibtsnicht"])); pid4=r.json()["id"]
# ---- Bilder
U=lambda p:S+"/produkte/"+p+"/bilder"
hdr={"Content-Type":"image/webp"}
r=cA.post(U(pid),content=WEBP,headers=hdr); chk("WebP-Bild hochladen",r.status_code==200 and r.json().get("id"),r.text); bid=r.json().get("id")
r=cA.post(U(pid),content=PNG,headers={"Content-Type":"image/png"}); chk("PNG abgelehnt (Browser wandelt um)",r.status_code==400,r.text)
r=cA.post(U(pid),content=b"kein bild",headers=hdr); chk("Kein Bild abgelehnt",r.status_code==400,r.text)
r=cA.post(U(pid),content=WEBP+b"0"*700000,headers=hdr); chk("Zu großes Bild abgelehnt",r.status_code in (400,413),r.status_code)
tiny=io.BytesIO(); Image.new("RGB",(100,80)).save(tiny,"WEBP"); r=cA.post(U(pid),content=tiny.getvalue(),headers=hdr); chk("Winziges Bild abgelehnt",r.status_code==400,r.text)
r=cB.post(U(pid),content=WEBP,headers=hdr); chk("Fremder Kunde: Bild-Upload gesperrt",r.status_code==403,r.status_code)
r=cA.get(S+"/bilder/"+bid); chk("Vorschau im Portal",r.status_code==200 and r.headers["content-type"]=="image/webp" and r.content[:4]==b"RIFF")
r=cA.put(S+"/bilder/"+bid,json={"alt":"Kleiner Kürbis in Orange Silk","sort":10}); chk("Bildtext speichern",r.status_code==200,r.text)
# ---- Öffentlicher Katalog (Shop noch aus)
chk("Modul an, Shop aus: 404",get("/produkte").status_code==404)
cA.put(S+"/einstellungen",json={"aktiv":True,"ref_praefix":"SA","versand_pauschale":4.9,"versandfrei_ab":49,"abholung":True,"produktionszeit":"2 bis 4 Werktage","lieferzeit":"2 Tage","gutschein_aktiv":True,"gutschein_min":10,"gutschein_max":100,"gutschein_betraege":[50,10,20]})
r=get("/produkte"); k=r.json(); chk("Katalog 200 mit Cache-Kopf",r.status_code==200 and r.headers["cache-control"]=="public, max-age=300" and r.headers.get("etag"),r.headers)
ids=[p["id"] for p in k["produkte"]]; chk("Nur aktive Artikel, in Reihenfolge",ids==["kleiner-kuerbis","kuerbis-trio","namensschild"] or sorted(ids)==["kleiner-kuerbis","kuerbis-trio","namensschild"],ids)
chk("Entwurf nicht ausgeliefert","entwurf" not in ids)
p=[x for x in k["produkte"] if x["id"]=="kleiner-kuerbis"][0]
chk("Preis als Zahl in Euro",p["preis"]==0.99 and isinstance(p["preis"],float))
chk("Felder des Vertrags",all(x in p for x in ("id","name","kategorie","preis","kurz","lang","material","masse","gewicht","farben","tags","personalisierbar","textlabel","textmax","bilder","sort","aktiv","geaendert")),p.keys())
chk("Farben je Artikel verweisen auf Farbliste",p["farben"]==["orange-silk-glaenzend"] and k["farben"][0]["hex"]=="#e07a2a",k["farben"])
chk("Bild-URL relativ, WebP, mit Maßen",p["bilder"][0]["url"]==f"/api/medien/{bid}.webp" and p["bilder"][0]["w"]==1200 and p["bilder"][0]["h"]==900 and p["bilder"][0]["alt"]=="Kleiner Kürbis in Orange Silk",p["bilder"])
chk("Versand und Zeiten",k["versand"]=={"pauschale":4.9,"versandfreiAb":49.0,"abholung":True,"produktionszeit":"2 bis 4 Werktage","lieferzeit":"2 Tage"},k["versand"])
chk("Leere Kategorie fehlt",[c["key"] for c in k["kategorien"]]==["wohnen-deko"],k["kategorien"])
ns=[x for x in k["produkte"] if x["id"]=="namensschild"][0]; chk("Wunschtext-Artikel",ns["personalisierbar"] is True and ns["textlabel"]=="Name" and ns["textmax"]==12 and "personalisiert" in ns["tags"] and ns["farben"][0]=="orange-silk-glaenzend",ns)
chk("Stand ist ein Zeitstempel",k["stand"].endswith("Z") and len(k["stand"])==20)
r2=get("/produkte",{"User-Agent":"Mozilla/5.0 Test","If-None-Match":r.headers["etag"]}); chk("ETag: 304 ohne Inhalt",r2.status_code==304 and not r2.content,r2.status_code)
r=get("/produkte/kuerbis-trio"); chk("Einzelner Artikel mit verwandt (nur aktive)",r.status_code==200 and r.json()["verwandt"]==["kleiner-kuerbis"],r.text[:300])
chk("Entwurf einzeln: 404 {ok:false}",get("/produkte/entwurf").status_code==404 and get("/produkte/entwurf").json()=={"ok":False})
chk("Unbekannter Artikel: 404",get("/produkte/gibts-nicht").status_code==404)
chk("Farben-Endpunkt",[f["key"] for f in get("/farben").json()["farben"]]==["orange-silk-glaenzend","schwarz"])
chk("Kategorien-Endpunkt",[c["key"] for c in get("/kategorien").json()["kategorien"]]==["wohnen-deko"])
g=get("/gutschein").json(); chk("Gutschein-Einstellung",g=={"aktiv":True,"einloesen":True,"betraege":[10,20,50],"min":10,"max":100,"gueltigkeitMonate":36,"zustellung":["E-Mail (PDF)","Post (Karte)"]},g)
r=get(f"/medien/{bid}.webp"); chk("Bild wird ausgeliefert",r.status_code==200 and r.headers["content-type"]=="image/webp" and "max-age" in r.headers["cache-control"] and r.content[:4]==b"RIFF")
r=get(f"/medien/{bid}.png"); chk("Falsche Endung: 404",r.status_code==404)
W2=httpx.Client(base_url=B,headers={"Host":"fremd-"+dom}); chk("Fremde Domain: 404",W2.get("/siteapi/api/produkte").status_code==404)
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kB}','b{dom}','live','live')")
WB=httpx.Client(base_url=B,headers={"Host":"b"+dom}); chk("Anderer Kunde ohne Modul sieht nichts",WB.get("/siteapi/api/produkte").status_code==404 and WB.get(f"/siteapi/api/medien/{bid}.webp").status_code==404)
# ---- Bestellung
POS=lambda **kw:{**{"id":"kuerbis-trio","name":"Kürbis-Trio","farbe":"orange-silk-glaenzend","text":"","menge":2,"einzelpreis":2.79},**kw}
BE=lambda **kw:{**{"typ":"bestellung","name":"Max Muster","email":f"max{sfx}@besucher.de","telefon":"","einwilligung":"ja","agb":"ja","website":"","lieferart":"versand","adresse":{"strasse":"Musterweg 1","plz":"29227","ort":"Celle","land":"DE"},"zahlungsart":"paypal","positionen":[POS()],"zwischensumme":5.58,"versand":4.90,"summe":10.48,"anmerkung":""},**kw}
r=pub(BE()); j=r.json(); chk("Bestellung angenommen mit Nummer",r.status_code==200 and j.get("ok") and j["ref"].startswith(f"SA-{datetime.date.today().year}-0001"),r.text); ref1=j.get("ref")
chk("PayPal-Link mit Betrag",j.get("paypalUrl")=="https://paypal.me/shopa/10.48EUR",j)
chk("Bestellung gespeichert",sql(f"select status||'|'||summe_cent||'|'||versand_cent from shop_bestellungen where ref='{ref1}'")=="eingegangen|1048|490")
chk("Position gespeichert",sql(f"select menge||'|'||einzelpreis_cent||'|'||farbe_name from shop_positionen where bestellung_id=(select id from shop_bestellungen where ref='{ref1}')")=="2|279|Orange Silk (glänzend)")
m=mail_an(f"max{sfx}@besucher.de",ref1); chk("Bestätigung an Kundin: genau eine Mail",len(m)==1,len(m))
T=text(m[0]) if m else ""
chk("Mail: Positionen",("2 × Kürbis-Trio" in T),ascii(T[:200])); chk("Mail: Summe",("10,48 €" in T),ascii(T)); chk("Mail: PayPal-Link","https://paypal.me/shopa/10.48EUR" in T,ascii(T)); chk("Mail: Adresse","Musterweg 1" in T,ascii(T))
chk("Mail im Namen der Firma, ohne KI-Name",m and "Shopa" in text(m[0]) and "Claude" not in text(m[0]) and "Markentrix-Team" not in text(m[0]))
m=mail_an(f"chef@{dom}",ref1); chk("Mail an den Betrieb",len(m)==1 and "Max Muster" in text(m[0]) and "Shop" in text(m[0]),[text(x)[:200] for x in m])
r=pub(BE(summe=9.99)); chk("Falsche Summe: 422 auf summe",r.status_code==422 and "summe" in r.json()["errors"],r.text)
r=pub(BE(positionen=[POS(einzelpreis=1.00)],zwischensumme=2,summe=6.9)); chk("Falscher Einzelpreis: 422 auf summe",r.status_code==422 and "summe" in r.json()["errors"],r.text)
r=pub(BE(positionen=[POS(menge=18)],zwischensumme=50.22,versand=0,summe=50.22)); chk("Versandfrei ab 49 €: Versand 0",r.status_code==200 and "paypalUrl" in r.json(),r.text)
chk("Versand 0 gerechnet",sql(f"select versand_cent||'|'||summe_cent from shop_bestellungen where ref='{r.json().get('ref')}'")=="0|5022")
r=pub(BE(positionen=[POS(menge=18)],zwischensumme=50.22,versand=4.9,summe=55.12)); chk("Versand trotz Versandfrei verlangt: 422",r.status_code==422,r.text)
r=pub(BE(lieferart="abholung",zahlungsart="abholung",adresse=None,versand=0,summe=5.58)); chk("Abholung ohne Adresse und Versand",r.status_code==200 and "paypalUrl" not in r.json(),r.text); refa=r.json().get("ref")
chk("Fortlaufende Nummern",refa.endswith("0003"),refa)
r=pub(BE(lieferart="abholung",zahlungsart="paypal",adresse=None,versand=0,summe=5.58)); chk("Abholung mit PayPal: PayPal-Link",r.status_code==200 and r.json().get("paypalUrl","").endswith("/5.58EUR"),r.text)
r=pub(BE(lieferart="versand",zahlungsart="abholung")); chk("Versand mit Zahlung bei Abholung abgelehnt",r.status_code==422 and "zahlungsart" in r.json()["errors"],r.text)
r=pub(BE(adresse={"strasse":"","plz":"","ort":""})); chk("Versand ohne Adresse: Fehler je Feld",r.status_code==422 and {"strasse","plz","ort"}<=set(r.json()["errors"]),r.text)
r=pub(BE(agb="")); chk("Ohne AGB abgelehnt",r.status_code==422 and "agb" in r.json()["errors"],r.text)
r=pub(BE(einwilligung="")); chk("Ohne Einwilligung abgelehnt",r.status_code==422 and "einwilligung" in r.json()["errors"],r.text)
r=pub(BE(email="kaputt")); chk("Ungültige Mail abgelehnt",r.status_code==422 and "email" in r.json()["errors"],r.text)
r=pub(BE(positionen=[])); chk("Leerer Warenkorb abgelehnt",r.status_code==422 and "positionen" in r.json()["errors"],r.text)
r=pub(BE(positionen=[POS(id="entwurf",name="Entwurf",einzelpreis=1)])); chk("Entwurf nicht bestellbar",r.status_code==422,r.text)
r=pub(BE(positionen=[POS(farbe="gruen")])); chk("Farbe außerhalb der Auswahl abgelehnt",r.status_code==422,r.text)
r=pub(BE(positionen=[POS(menge=0)])); chk("Menge 0 abgelehnt",r.status_code==422,r.text)
r=pub(BE(positionen=[POS(menge=100)])); chk("Menge 100 abgelehnt",r.status_code==422,r.text)
NS=lambda **kw:POS(id="namensschild",name="Namensschild",einzelpreis=7.5,menge=1,**kw)
r=pub(BE(positionen=[NS(text="")],zwischensumme=7.5,summe=12.4)); chk("Wunschtext Pflicht",r.status_code==422,r.text)
r=pub(BE(positionen=[NS(text="x"*13)],zwischensumme=7.5,summe=12.4)); chk("Wunschtext zu lang",r.status_code==422,r.text)
r=pub(BE(positionen=[NS(text="Lotta")],zwischensumme=7.5,summe=12.4)); chk("Wunschtext angenommen",r.status_code==200,r.text)
chk("Wunschtext gespeichert",sql(f"select wunschtext from shop_positionen where bestellung_id=(select id from shop_bestellungen where ref='{r.json().get('ref')}')")=="Lotta")
r=pub(BE(positionen=[POS(text="Hallo")])); chk("Text bei Artikel ohne Wunschtext: Preis stimmt trotzdem, Text ignoriert",r.status_code==200 and sql(f"select coalesce(wunschtext,'-') from shop_positionen where bestellung_id=(select id from shop_bestellungen where ref='{r.json().get('ref')}')")=="-",r.text)
r=pub({k:v for k,v in BE().items() if k not in ("zwischensumme","versand","summe")}); chk("Ohne Summenangaben: Portal rechnet selbst",r.status_code==200,r.text)
r=W.post("/siteapi/api/anfrage",headers={"Origin":"https://"+dom,"User-Agent":"Mozilla/5.0 Test","Content-Type":"application/x-www-form-urlencoded"},content=b"typ=bestellung&name=Max"); chk("Formular-Bestellung abgelehnt",r.status_code==422,r.status_code)
n0=int(sql(f"select count(*) from shop_bestellungen where kunden_id='{kA}'"))
r=pub(BE(website="http://spam.example")); chk("Lockfeld: so tun als ob, nichts speichern",r.status_code==200 and int(sql(f"select count(*) from shop_bestellungen where kunden_id='{kA}'"))==n0)
r=pub(BE(),{"Origin":"https://fremd.example"}); chk("Fremde Herkunft: 403",r.status_code==403,r.status_code)
r=pub(BE(name="<b>Mallory</b>",positionen=[POS(name="Gehackt",einzelpreis=2.79)])); chk("Namen der Website werden ignoriert, Portal nutzt eigene",r.status_code==200 and sql(f"select name from shop_positionen where bestellung_id=(select id from shop_bestellungen where ref='{r.json().get('ref')}')")=="Kürbis-Trio",r.text)
# ---- Gutschein-Betrag (Shop-Grenzen)
G=lambda **kw:{**{"typ":"gutschein","name":"Greta Gast","email":f"greta{sfx}@besucher.de","betrag":"50","einwilligung":True},**kw}
chk("Gutschein im Rahmen",pub(G()).status_code==200)
r=pub(G(betrag="5")); chk("Gutschein unter Minimum abgelehnt",r.status_code==422 and "wunschbetrag" in r.json()["errors"],r.text)
r=pub(G(betrag="500")); chk("Gutschein über Maximum abgelehnt",r.status_code==422,r.text)
# ---- Gutschein im Shop einlösen
WD="/api/kunde/website-dienste/gutscheine"
pub(G(email=f"gut{sfx}@besucher.de",betrag="30"))
gl=[x for x in cA.get(WD).json()["gutscheine"] if x["email"].startswith("gut")][0]
v=cA.get(WD+"/code-vorschlag").json()["code"]; chk("Code-Vorschlag: XXXX-XXXX-XXXX ohne verwechselbare Zeichen",bool(re.match(r"^[A-HJ-NP-Z2-9]{4}(-[A-HJ-NP-Z2-9]{4}){2}$",v)),v)
chk("Code-Vorschlag ist jedes Mal anders",cA.get(WD+"/code-vorschlag").json()["code"]!=v)
chk("Code-Vorschlag nur für Inhaber mit Anmeldung",httpx.Client(base_url=B).get(WD+"/code-vorschlag").status_code in (401,403))
CODE=v
chk("Code kann man nicht vor dem Versand einlösen",W.post("/siteapi/api/gutschein/pruefen",headers=HK,content=json.dumps({"code":CODE}).encode()).json()["gueltig"] is False)
r=cA.post(WD+"/"+gl["id"]+"/zahlungslink",json={"betrag":"30"}); r=cA.post(WD+"/"+gl["id"]+"/code",json={"code":CODE}); chk("Code senden",r.status_code==200,r.text)
m=mail_an(f"gut{sfx}@besucher.de",CODE); chk("Mail nennt den Ablauf",len(m)==1 and "Gültig bis:" in text(m[0]),[text(x)[:200] for x in m])
gl=[x for x in cA.get(WD).json()["gutscheine"] if x["id"]==gl["id"]][0]; chk("Gültig 36 Monate, Rest 30,00",gl["rest"]=="30.00" and gl["eingeloest"]=="0.00" and gl["gueltig_bis"][:4]==str(datetime.date.today().year+3),gl)
PR=lambda c,h=None:W.post("/siteapi/api/gutschein/pruefen",headers=h or HK,content=json.dumps({"code":c}).encode())
r=PR(CODE.lower()); j=r.json(); chk("Prüfen (Groß/Klein egal): gültig mit Rest und Ablauf",r.status_code==200 and j["gueltig"] is True and j["rest"]==30.0 and j["ablauf"][:4]==str(datetime.date.today().year+3),r.text)
j=PR("FALSCH-CODE-XYZ").json(); chk("Falscher Code: ungültig, ohne Hinweis ob es ihn gibt",j["gueltig"] is False and "ungültig" in j["message"],j)
r=PR(CODE,{**HK,"Origin":"https://fremd.example"}); chk("Prüfen von fremder Herkunft: 403",r.status_code==403,r.status_code)
sql(f"update shop_einstellungen set gutschein_aktiv=false where kunden_id='{kA}'")
chk("Gutscheine im Shop aus: nicht einlösbar",PR(CODE).json()["gueltig"] is False)
r=pub(BE(gutscheincode=CODE)); chk("Bestellung mit Code bei ausgeschalteten Gutscheinen: 422",r.status_code==422 and "gutscheincode" in r.json()["errors"],r.text)
sql(f"update shop_einstellungen set gutschein_aktiv=true where kunden_id='{kA}'")
r=pub(BE(gutscheincode="NICHT-DA-123")); chk("Bestellung mit falschem Code: 422 auf gutscheincode",r.status_code==422 and "gutscheincode" in r.json()["errors"],r.text)
chk("Falscher Code verbraucht nichts",sql(f"select eingeloest from website_gutscheine where id='{gl['id']}'")=="0.00")
r=pub(BE(gutscheincode=CODE.lower())); j=r.json(); chk("Bestellung 10,48 € mit Gutschein 30 €: nichts zu zahlen",r.status_code==200 and j["gutschein"]=={"abgezogen":10.48,"rest":19.52,"zuZahlen":0.0} and "paypalUrl" not in j,r.text); refg=j.get("ref")
chk("Bestellung gleich auf „bezahlt“",sql(f"select status||'|'||gutschein_cent||'|'||gutschein_code||'|'||(bezahlt_am is not null) from shop_bestellungen where ref='{refg}'")==f"bezahlt|1048|{CODE}|true")
chk("Guthaben abgebucht",sql(f"select eingeloest from website_gutscheine where id='{gl['id']}'")=="10.48")
m=mail_an(f"max{sfx}@besucher.de",refg); T=text(m[0]) if m else ""
chk("Mail zeigt Gutschein und „vollständig bezahlt“","Gutschein" in T and "Zu zahlen: 0,00 €" in T and "vollständig mit dem Gutschein bezahlt" in T and "paypal.me" not in T,ascii(T))
r=pub(BE(positionen=[POS(menge=18)],zwischensumme=50.22,versand=0,summe=50.22,gutscheincode=CODE)); j=r.json(); chk("Bestellung 50,22 €: Rest 19,52 € abgezogen, 30,70 € per PayPal",r.status_code==200 and j["gutschein"]=={"abgezogen":19.52,"rest":0.0,"zuZahlen":30.7} and j["paypalUrl"]=="https://paypal.me/shopa/30.70EUR",r.text); refh=j.get("ref")
chk("Gutschein aufgebraucht",sql(f"select eingeloest from website_gutscheine where id='{gl['id']}'")=="30.00" and sql(f"select status from shop_bestellungen where ref='{refh}'")=="eingegangen")
chk("Aufgebrauchter Code: nicht mehr gültig",PR(CODE).json()["gueltig"] is False)
r=pub(BE(gutscheincode=CODE)); chk("Aufgebrauchter Code bei Bestellung: 422",r.status_code==422 and "gutscheincode" in r.json()["errors"],r.text)
chk("Zahlbetrag im Portal",[b for b in cA.get(S).json()["bestellungen"] if b["ref"]==refh][0]["zu_zahlen"]==30.7 and [b for b in cA.get(S).json()["bestellungen"] if b["ref"]==refh][0]["gutschein_code"]==CODE)
chk("Dienste-Karte zeigt Restguthaben 0",[x for x in cA.get(WD).json()["gutscheine"] if x["id"]==gl["id"]][0]["rest"]=="0.00")
bid_g=[b for b in cA.get(S).json()["bestellungen"] if b["ref"]==refg][0]["id"]
r=cA.put(S+"/bestellungen/"+bid_g,json={"status":"storniert"}); chk("Bestellung stornieren",r.status_code==200,r.text)
chk("Storno bucht 10,48 € zurück",sql(f"select eingeloest from website_gutscheine where id='{gl['id']}'")=="19.52")
chk("Zurückgebuchter Code wieder gültig mit Rest 10,48",PR(CODE).json()["rest"]==10.48)
r=cA.put(S+"/bestellungen/"+bid_g,json={"status":"storniert"}); chk("Zweites Storno bucht nicht doppelt",r.status_code==200 and sql(f"select eingeloest from website_gutscheine where id='{gl['id']}'")=="19.52")
r=cA.put(S+"/bestellungen/"+bid_g,json={"status":"eingegangen"}); chk("Stornierte Bestellung nicht wieder öffnen",r.status_code==409,r.text)
# anderer Kunde kann den Code nicht nutzen
HB={"Origin":"https://b"+dom,"User-Agent":"Mozilla/5.0 Test","Content-Type":"application/json"}
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kB}','shop',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
rb=cB.put(S+"/einstellungen",json={"aktiv":True,"gutschein_aktiv":True}); chk("Fremder Kunde schaltet seinen Shop ein",rb.status_code==200,rb.text)
rb=WB.post("/siteapi/api/gutschein/pruefen",headers=HB,content=json.dumps({"code":CODE}).encode()); chk("Fremder Shop kennt den Code nicht",rb.json().get("gueltig") is False,(rb.status_code,rb.text))
# Prüfen ist begrenzt (10 je 10 Minuten und IP)
n429=0
for i in range(8):
    if PR("RATE-"+str(i)).status_code==429: n429+=1
chk("Code-Raten wird gebremst (429)",n429>=1,n429)
# ---- Portal: Bestellungen bearbeiten
d=cA.get(S).json(); chk("Bestellungen im Portal, neueste zuerst",len(d["bestellungen"])>=8 and d["bestellungen"][0]["ref"]>d["bestellungen"][-1]["ref"],[b["ref"] for b in d["bestellungen"]])
b1=[b for b in d["bestellungen"] if b["ref"]==ref1][0]; chk("Positionen und Adresse sichtbar",b1["positionen"][0]["menge"]==2 and b1["adresse"]["ort"]=="Celle" and b1["summe"]==10.48 and b1["status"]=="eingegangen",b1)
r=cA.put(S+"/bestellungen/"+b1["id"],json={"status":"bezahlt","mail":True}); chk("Status Bezahlt mit Mail",r.status_code==200 and r.json()["mail"] is True,r.text)
m=mail_an(f"max{sfx}@besucher.de","Zahlung erhalten"); chk("Mail „Zahlung erhalten“",len(m)==1 and ref1 in text(m[0]) and "Claude" not in text(m[0]),[text(x)[:200] for x in m])
chk("bezahlt_am gesetzt",sql(f"select bezahlt_am is not null from shop_bestellungen where ref='{ref1}'")=="t")
r=cA.put(S+"/bestellungen/"+b1["id"],json={"status":"versendet","sendungsnummer":"JJD123","mail":True}); chk("Versendet mit Sendungsnummer",r.status_code==200,r.text)
m=mail_an(f"max{sfx}@besucher.de","unterwegs"); chk("Versandmail mit Sendungsnummer",len(m)==1 and "JJD123" in text(m[0]),[text(x)[:200] for x in m])
r=cA.put(S+"/bestellungen/"+b1["id"],json={"status":"versendet","sendungsnummer":"JJD123","mail":True}); chk("Gleicher Status: keine zweite Mail",r.status_code==200 and r.json()["mail"] is False and len(mail_an(f"max{sfx}@besucher.de","unterwegs"))==1,r.text)
r=cA.put(S+"/bestellungen/"+b1["id"],json={"status":"abholbereit"}); chk("Abholbereit bei Versand abgelehnt",r.status_code==409,r.text)
ba=[b for b in d["bestellungen"] if b["ref"]==refa][0]
r=cA.put(S+"/bestellungen/"+ba["id"],json={"status":"abholbereit","abholtermin":"Sa, 14.11., 10 bis 12 Uhr","mail":True}); chk("Abholbereit mit Termin",r.status_code==200,r.text)
m=mail_an(f"max{sfx}@besucher.de","abholbereit"); chk("Abholmail mit Termin",len(m)==1 and "14.11." in text(m[0]),[text(x)[:200] for x in m])
r=cA.put(S+"/bestellungen/"+ba["id"],json={"status":"versendet"}); chk("Versendet bei Abholung abgelehnt",r.status_code==409,r.text)
r=cA.put(S+"/bestellungen/"+b1["id"],json={"status":"kaputt"}); chk("Unbekannter Status abgelehnt",r.status_code==422)
r=cA.put(S+"/bestellungen/"+b1["id"],json={"status":"im_druck","notiz":"Heute drucken","mail":False}); chk("Ohne Mail-Haken keine Mail",r.status_code==200 and r.json()["mail"] is False and len(mail_an(f"max{sfx}@besucher.de","in Arbeit"))==0)
chk("Notiz gespeichert",sql(f"select notiz from shop_bestellungen where ref='{ref1}'")=="Heute drucken")
chk("Fremder Kunde kommt nicht an Bestellungen",cB.put(S+"/bestellungen/"+b1["id"],json={"status":"storniert"}).status_code in (403,404))
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kB}','shop',true) on conflict (kunden_id,modul_code) do update set aktiv=true")
chk("Fremder Kunde mit Modul: Bestellung 404",cB.put(S+"/bestellungen/"+b1["id"],json={"status":"storniert"}).status_code==404)
chk("Fremder Kunde sieht keine Artikel und Bestellungen",cB.get(S).json()["produkte"]==[] and cB.get(S).json()["bestellungen"]==[])
chk("Fremder Kunde kommt nicht an Artikel",cB.put(S+f"/produkte/{pid}",json=P(farben=[],kategorie=None)).status_code==404 and cB.delete(S+f"/produkte/{pid}").status_code==404)
chk("Fremder Kunde kommt nicht an Bilder",cB.get(S+"/bilder/"+bid).status_code==404 and cB.delete(S+"/bilder/"+bid).status_code==404)
chk("Fremder Kunde: gleicher Kurzname erlaubt",cB.post(S+"/produkte",json=P(name="Kleiner Kürbis",kategorie=None,farben=[])).status_code==200)
# ---- Pflege
r=cA.put(S+f"/produkte/{pid4}",json=P(name="Kürbis-Trio",preis=3.19,aktiv=False)); chk("Artikel ändern und auf Entwurf stellen",r.status_code==200)
chk("Geändert: aus dem Katalog verschwunden",get("/produkte/kuerbis-trio").status_code==404 and "kuerbis-trio" not in [x["id"] for x in get("/produkte").json()["produkte"]])
r=pub(BE()); chk("Entwurf-Artikel nicht mehr bestellbar",r.status_code==422,r.text)
cA.put(S+f"/produkte/{pid4}",json=P(name="Kürbis-Trio",preis=3.19,aktiv=True))
r=pub(BE()); chk("Preisänderung: alter Preis der Website wird abgelehnt",r.status_code==422 and "summe" in r.json()["errors"],r.text)
fid=[f for f in cA.get(S).json()["farben"] if f["schluessel"]=="schwarz"][0]["id"]
cA.put(S+f"/produkte/{pid2}",json=P(name="Namensschild",preis=7.5,personalisierbar=True,textlabel="Name",textmax=12,farben=["orange-silk-glaenzend","schwarz"],kategorie=None))
chk("Farbe löschen",cA.delete(S+"/farben/"+fid).status_code==200)
chk("Farbe wird bei Artikeln entfernt",[p for p in cA.get(S).json()["produkte"] if p["schluessel"]=="namensschild"][0]["farben"]==["orange-silk-glaenzend"])
kid2=[k for k in cA.get(S).json()["kategorien"] if k["schluessel"]=="wohnen-deko"][0]["id"]
chk("Kategorie löschen",cA.delete(S+"/kategorien/"+kid2).status_code==200 and [p for p in cA.get(S).json()["produkte"] if p["schluessel"]=="kleiner-kuerbis"][0]["kategorie"] is None)
chk("Bild löschen",cA.delete(S+"/bilder/"+bid).status_code==200 and get("/produkte/kleiner-kuerbis").json()["bilder"]==[])
chk("Artikel löschen",cA.delete(S+f"/produkte/{pid3}").status_code==200 and cA.delete(S+f"/produkte/{pid3}").status_code==404)
chk("Ohne CSRF-Kopf abgelehnt",httpx.Client(base_url=B).put(S+"/einstellungen",json={}).status_code in (401,403))
chk("Audit geschrieben",int(sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion like 'shop_%'"))>=4)
chk("Bestellungen bleiben nach Artikel-Löschen",int(sql(f"select count(*) from shop_positionen where kunden_id='{kA}'"))>=8)
