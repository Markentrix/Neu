"""Fotos zu Anfragen und Terminen: Bildprüfung (ohne Standort/Kameradaten), Upload, Verknüpfung, Mail-Anhang, Portal-Anzeige, Löschfrist, Aufräumen, Export."""
import httpx, time, re, email, json, os, struct, sys, subprocess, zlib, base64, datetime, zoneinfo, io, zipfile
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
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+600)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, offboarding, fotos
from app.db import tx
db.open_pool()

# ---------------------------------------------------------------- Bilder von Hand gebaut (ohne Bildbibliothek)
def jpeg(exif=b"Exif\0\0GPSMARKER-52.6N-10.0E Kamera-XYZ", w=1, h=1):
    app1=b"\xff\xe1"+struct.pack(">H",len(exif)+2)+exif
    com=b"\xff\xfe"+struct.pack(">H",9)+b"SECRET!"
    app0=b"\xff\xe0"+struct.pack(">H",16)+b"JFIF\0\1\1\0\0\1\0\1\0\0"
    sof=b"\xff\xc0"+struct.pack(">H",11)+b"\x08"+struct.pack(">HH",h,w)+b"\x01\x01\x11\x00"
    sos=b"\xff\xda"+struct.pack(">H",8)+b"\x01\x01\x00\x00\x3f\x00"+b"\x12\x34\x56"
    return b"\xff\xd8"+app1+com+app0+sof+sos+b"\xff\xd9"
def chunk(t,d): return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d))
PNG1=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")
def png_mit_text():
    kopf=PNG1[:8]; rest=PNG1[8:]
    i=0; teile=[]
    while i<len(rest):
        ln=struct.unpack(">I",rest[i:i+4])[0]; teile.append(rest[i:i+12+ln]); i+=12+ln
    return kopf+teile[0]+chunk(b"tEXt",b"Comment\0GPSMARKER-PNG")+chunk(b"eXIf",b"GPSMARKER-EXIF")+b"".join(teile[1:])
def riff(chunks):
    inh=b"WEBP"+b"".join(chunks)
    return b"RIFF"+struct.pack("<I",len(inh))+inh
def wchunk(t,d): return t+struct.pack("<I",len(d))+d+(b"\0" if len(d)&1 else b"")
def webp(flags=0x18):
    vp8x=wchunk(b"VP8X",bytes([flags,0,0,0])+(0).to_bytes(3,"little")+(0).to_bytes(3,"little"))
    return riff([vp8x,wchunk(b"VP8L",b"\x2f\x00\x00\x00\x00BILD"),wchunk(b"EXIF",b"GPSMARKER-WEBP"),wchunk(b"XMP ",b"GPSMARKER-XMP")])

# ---------------------------------------------------------------- Einheiten: Prüfung und Bereinigung
t,d=fotos.pruefen(jpeg())
chk("JPEG: Typ erkannt, Standort/Kamera/Kommentar entfernt, Bilddaten bleiben",t=="image/jpeg" and b"GPSMARKER" not in d and b"SECRET" not in d and b"Kamera" not in d and d.startswith(b"\xff\xd8") and d.endswith(b"\xff\xd9") and b"\x12\x34\x56" in d and b"JFIF" in d,d[:80])
t,d=fotos.pruefen(png_mit_text())
chk("PNG: Textblöcke und EXIF entfernt, Bild bleibt",t=="image/png" and b"GPSMARKER" not in d and b"IHDR" in d and b"IDAT" in d and d.endswith(b"IEND\xaeB`\x82"))
t,d=fotos.pruefen(webp())
chk("WebP: EXIF/XMP entfernt, Kennzeichen bereinigt, Größe stimmt",t=="image/webp" and b"GPSMARKER" not in d and b"VP8L" in d and d[4:8]==struct.pack("<I",len(d)-8) and d[20]&0x0C==0 and d[20]&0x10==0x10,d[:40])
def fehler(daten):
    try: fotos.pruefen(daten); return False
    except fotos.FotoFehler: return True
chk("Abgelehnt: HTML/Skript, GIF, SVG, PDF, leer",all(fehler(x) for x in (b"<html><script>alert(1)</script>",b"GIF89a\1\0\1\0",b"<svg xmlns='http://www.w3.org/2000/svg'/>",b"%PDF-1.4",b"")))
chk("Abgelehnt: JPEG ohne Bilddaten/abgeschnitten, JPEG mit riesigen Maßen",fehler(jpeg()[:30]) and fehler(jpeg(w=20000,h=20000)))
chk("Abgelehnt: PNG mit falscher Reihenfolge/ohne Ende, animiertes WebP",fehler(PNG1[:40]) and fehler(riff([wchunk(b"VP8X",bytes([0x02,0,0,0,0,0,0,0,0,0])),wchunk(b"ANIM",b"\0"*6),wchunk(b"VP8L",b"x")])))
chk("Abgelehnt: mehr als 6 MB",fehler(jpeg()+b"\0"*(6*1024*1024)))
chk("Kennungen: Liste, Text, Fremdzeichen, Doppelte, Höchstzahl",fotos.kennungen("abcdefghijkl, abcdefghijkl;zzzzzzzzzzzz")==["abcdefghijkl","zzzzzzzzzzzz"] and fotos.kennungen(["abcdefghij","a b c d e f g h i"]) == ["abcdefghij"] and len(fotos.kennungen([f"tok{i}tok{i}tok{i}" for i in range(9)]))==5 and fotos.kennungen(None)==[])

# ---------------------------------------------------------------- Kunde A: Website, Mail, Fotos
kA,cA=neuer_kunde("Fotoa"); kB,cB=neuer_kunde("Fotob")
dom=f"foto{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
ORG={"Origin":"https://"+dom,"User-Agent":"Mozilla/5.0 Test"}
def post(pfad,body): return W.post(API+pfad,headers={**ORG,"Content-Type":"application/json"},content=json.dumps(body).encode())
def up(daten,origin=None): return W.post(API+"/foto",headers={**ORG,**({"Origin":origin} if origin else {}),"Content-Type":"text/plain"},content=daten)
D="/api/kunde/website-dienste"
cA.put(D+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
cA.put(D+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False})
r=W.get(API+"/foto",headers=ORG); chk("Ohne Einschalten: Info zeigt aus",r.status_code==200 and r.json()["aktiv"] is False,r.text)
r=up(jpeg()); chk("Ohne Einschalten: Upload abgelehnt (409)",r.status_code==409,r.text)
z=cA.get(D).json(); chk("Einstellungen: Fotos standardmäßig aus, 90 Tage",z["fotos"]=={"aktiv":False,"tage":90},z.get("fotos"))
chk("Frist unter 7 Tagen abgelehnt",cA.put(D+"/fotos",json={"aktiv":True,"tage":3}).status_code>=400)
chk("Frist über 365 Tagen abgelehnt",cA.put(D+"/fotos",json={"aktiv":True,"tage":500}).status_code>=400)
chk("Nur der Inhaber darf einstellen (Fremder ohne Anmeldung)",httpx.Client(base_url=B,headers=H).put(D+"/fotos",json={"aktiv":True,"tage":10}).status_code in (401,403))
r=cA.put(D+"/fotos",json={"aktiv":True,"tage":7}); chk("Fotos einschalten mit 7 Tagen",r.status_code==200,r.text)
z=cA.get(D).json(); chk("Einstellung gespeichert",z["fotos"]=={"aktiv":True,"tage":7},z.get("fotos"))
r=W.get(API+"/foto",headers=ORG).json(); chk("Info: aktiv, bis 5 Fotos, Hinweistext mit Löschfrist",r["aktiv"] and r["max"]==5 and "7 Tagen" in r["hinweis"],r)

# ---- Upload über die Website-API
toks=[]
for i in range(3):
    r=up(jpeg(exif=b"Exif\0\0GPSMARKER-"+str(i).encode())); ok=r.status_code==200 and r.json().get("token"); toks.append(r.json().get("token") if ok else None)
chk("3 Fotos hochgeladen, Kennungen erhalten",all(toks) and len(set(toks))==3,toks)
gp=sql(f"select count(*) from website_fotos where kunden_id='{kA}' and position('GPSMARKER'::bytea in daten)>0")
chk("In der Datenbank steht kein Standort/Kamera-Text",gp=="0",gp)
chk("Noch nicht verknüpft: ohne Löschdatum, Kennung vorhanden",sql(f"select count(*) from website_fotos where kunden_id='{kA}' and loeschen_am is null and token is not null")=="3")
r=up(b"<script>alert(1)</script>"); chk("Skript statt Foto abgelehnt (400)",r.status_code==400,r.text)
r=up(jpeg(),origin="https://boese.example"); chk("Fremde Herkunft abgelehnt (403)",r.status_code==403,r.text)
r=up(b"\xff\xd8\xff"+b"0"*(7*1024*1024)); chk("Zu große Datei abgelehnt (413)",r.status_code==413,r.status_code)
# ---- Anfrage mit Fotos
nm=f"Fotomann{sfx}"
r=post("/anfrage",{"typ":"kontakt","name":nm,"email":f"foto{sfx}@besucher.de","nachricht":"Kratzer an der Tür","einwilligung":"ja","fotos":toks+["gibtesnicht1234567890","gibtesnicht1234567890"]})
chk("Anfrage mit Fotos angenommen",r.status_code==200,r.text)
time.sleep(2)
chk("3 Fotos hängen an der Anfrage, Kennung gelöscht",sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null and token is null")=="3")
fr=sql(f"select round(extract(epoch from (min(loeschen_am)-now()))/86400) from website_fotos where kunden_id='{kA}' and anfrage_id is not null")
chk("Löschdatum = heute + 7 Tage",fr=="7",fr)
chk("Das Foto-Feld erscheint nicht im Anfragetext",sql(f"select count(*) from anfragen where kunden_id='{kA}' and nachricht ilike '%gibtesnicht%'")=="0")
m=[x for x in mails() if f"chef@{dom}" in str(x["To"]) and nm in str(x["Subject"])]
chk("Mail an den Betrieb ist angekommen",len(m)==1,len(m))
if m:
    an=[p for p in m[0].walk() if p.get_content_type()=="image/jpeg"]; t_=text(m[0])
    chk("Mail: 3 Fotos im Anhang",len(an)==3,len(an))
    chk("Mail: Hinweis mit Anzahl, Portal und Löschfrist","Fotos: 3" in t_ and "7 Tagen" in t_ and "Kundenportal" in t_,t_[:500])
    chk("Mail: Anhänge enthalten keine Standortdaten",all(b"GPSMARKER" not in p.get_payload(decode=True) for p in an))
r=post("/anfrage",{"typ":"kontakt","name":nm+" zwei","email":f"foto2{sfx}@besucher.de","nachricht":"nochmal","einwilligung":"ja","fotos":toks})
time.sleep(1)
chk("Dieselben Kennungen lassen sich nicht ein zweites Mal verwenden",sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null")=="3")
# ---- Formular (urlencoded) mit zwei Kennungen
t2=[up(jpeg()).json()["token"] for _ in range(2)]
r=W.post(API+"/anfrage",headers={**ORG,"Content-Type":"application/x-www-form-urlencoded"},content="typ=kontakt&name=Formular+Mann&email=form%s%%40besucher.de&nachricht=Hallo&einwilligung=ja&fotos=%s&fotos=%s"%(sfx,t2[0],t2[1]),)
chk("Formular-Anfrage mit zwei Foto-Kennungen",r.status_code in (200,303),r.status_code)
chk("Formular: beide Fotos verknüpft",sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null")=="5")
# ---- Terminanfrage mit Foto
tag=(datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).date()+datetime.timedelta(days=4)).isoformat()
t3=up(jpeg()).json()["token"]
r=post("/anfrage",{"typ":"termin","name":"Termin Foto","email":f"tf{sfx}@besucher.de","telefon":"0511 1","datum":tag,"uhrzeit":"09:00","einwilligung":"ja","fotos":[t3]})
chk("Terminanfrage mit Foto gebucht",r.status_code==200,r.text)
time.sleep(1.5)
chk("Foto hängt an Anfrage und Buchung",sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null and buchung_id is not null")=="1")
bu=cA.get(D+"/buchungen").json(); fb=[x for x in bu["buchungen"] if x["name"]=="Termin Foto"]
chk("Portal Buchungen: Foto mit Löschdatum",len(fb)==1 and len(fb[0]["fotos"])==1 and fb[0]["fotos"][0]["loeschen_am"],bu)
te=cA.get("/api/kunde/termine").json(); ft=[x for x in te if x["kontakt_name"]=="Termin Foto"]
chk("Portal Termine: Foto sichtbar, anfrage_id nicht nach außen",len(ft)==1 and len(ft[0]["fotos"])==1 and "anfrage_id" not in ft[0],te[:1])

# ---------------------------------------------------------------- Portal: Anzeige, Fremdzugriff, Löschen
an=cA.get("/api/kunde/anfragen").json(); mit=[x for x in an if x["name"]==nm]
chk("Portal Anfragen: 3 Fotos mit Löschdatum",len(mit)==1 and len(mit[0]["fotos"])==3 and all(f["loeschen_am"] for f in mit[0]["fotos"]),an[:1])
f0=mit[0]["fotos"][0]["id"]
r=cA.get(f"/api/kunde/fotos/{f0}"); chk("Foto abrufbar: Bildtyp, nosniff, nicht zwischenspeichern",r.status_code==200 and r.headers["content-type"]=="image/jpeg" and r.headers.get("x-content-type-options")=="nosniff" and "no-store" in r.headers.get("cache-control","") and "default-src" in r.headers.get("content-security-policy","") and r.content.startswith(b"\xff\xd8"),dict(r.headers))
chk("Fremder Betrieb sieht das Foto nicht (404)",cB.get(f"/api/kunde/fotos/{f0}").status_code==404)
chk("Ohne Anmeldung kein Zugriff",httpx.Client(base_url=B,headers=H).get(f"/api/kunde/fotos/{f0}").status_code in (401,403))
chk("Fremder Betrieb kann nicht löschen (404)",cB.delete(f"/api/kunde/fotos/{f0}").status_code==404 and sql(f"select count(*) from website_fotos where id='{f0}'")=="1")
chk("Ungültige Kennung: 404",cA.get("/api/kunde/fotos/xyz").status_code==404)
chk("Fremder Betrieb sieht keine Fotos in seiner Anfrageliste",all(not x.get("fotos") for x in cB.get("/api/kunde/anfragen").json()))
chk("Betrieb löscht ein Foto selbst",cA.delete(f"/api/kunde/fotos/{f0}").status_code==200 and cA.get(f"/api/kunde/fotos/{f0}").status_code==404 and cA.delete(f"/api/kunde/fotos/{f0}").status_code==404)
chk("Löschen steht im Protokoll",sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion='foto_geloescht'")=="1")

# ---------------------------------------------------------------- Widget (Kontaktformular der Bausteine)
sid=sql(f"select site_id from website_dienste where kunden_id='{kA}'")
WR=httpx.Client(base_url=B)
def wup(daten,origin=None): return WR.post(f"/site/{sid}/foto",headers={"Origin":origin or "https://"+dom,"Content-Type":"text/plain"},content=daten)
cf=WR.get(f"/site/{sid}/config",headers={"Origin":"https://"+dom}).json(); chk("Widget-Config nennt Fotos",cf["fotos"]=={"aktiv":True,"max":5,"tage":7},cf.get("fotos"))
chk("Widget: fremde Herkunft abgelehnt",wup(jpeg(),"https://boese.example").status_code==403)
chk("Widget: Skript statt Foto abgelehnt",wup(b"<script>").status_code==400)
w1=wup(jpeg()); chk("Widget: Foto hochgeladen",w1.status_code==200 and w1.json().get("token"),w1.text)
r=WR.post(f"/site/{sid}/kontakt",headers={"Origin":"https://"+dom,"Content-Type":"text/plain"},content=json.dumps({"name":"Widget Foto","email":f"wf{sfx}@besucher.de","telefon":"","nachricht":"Mit Bild bitte","einwilligung":True,"fotos":[w1.json()["token"]]}))
chk("Widget-Kontakt mit Foto angenommen",r.status_code==200,r.text)
time.sleep(1.5)
chk("Widget-Kontakt: Foto an der Anfrage",sql(f"select count(*) from website_fotos f join anfragen a on a.id=f.anfrage_id where f.kunden_id='{kA}' and a.name='Widget Foto'")=="1")
mw=[x for x in mails() if f"chef@{dom}" in str(x["To"]) and "Widget Foto" in (text(x) or "")]
chk("Widget-Kontakt: Mail mit Bild im Anhang",len(mw)==1 and len([p for p in mw[0].walk() if p.get_content_type()=="image/jpeg"])==1,len(mw))

# ---------------------------------------------------------------- Ausschalten wirkt sofort
r=cA.put(D+"/fotos",json={"aktiv":False,"tage":7}); chk("Fotos ausschalten",r.status_code==200)
chk("Aus: Upload abgelehnt (API und Widget)",up(jpeg()).status_code==409 and wup(jpeg()).status_code==409)
vorher=sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null")
rest=sql(f"select token from website_fotos where kunden_id='{kA}' and token is not null limit 1")
post("/anfrage",{"typ":"kontakt","name":"Aus Foto","email":f"aus{sfx}@besucher.de","nachricht":"x","einwilligung":"ja","fotos":[rest or "gibtesnicht1234567890"]})
time.sleep(1); chk("Aus: mitgeschickte Kennungen werden ignoriert",sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null")==vorher)

# ---------------------------------------------------------------- Löschfrist und Aufräumen
with tx("system") as cur:
    cur.execute("SELECT id FROM website_fotos WHERE kunden_id=%s AND anfrage_id IS NOT NULL ORDER BY erstellt_am LIMIT 1",(kA,)); alt=str(cur.fetchone()["id"])
    cur.execute("UPDATE website_fotos SET loeschen_am=now()-interval '1 minute' WHERE id=%s",(alt,))
    cur.execute("INSERT INTO website_fotos (kunden_id, token, typ, groesse, daten, erstellt_am) VALUES (%s,'verwaist-test-0001','image/jpeg',3,%s,now()-interval '25 hours')",(kA,b"abc"))
    cur.execute("INSERT INTO website_fotos (kunden_id, token, typ, groesse, daten, erstellt_am) VALUES (%s,'frisch-test-000001','image/jpeg',3,%s,now()-interval '2 hours')",(kA,b"abc"))
    cur.execute("SELECT count(*) AS n FROM loeschprotokoll WHERE tabelle LIKE 'website_fotos%%'"); n0=cur.fetchone()["n"]
with tx("system") as cur: cfg=jobs.einstellungen_lesen(cur)
jobs.fotos_aufraeumen(cfg)
chk("Abgelaufenes Foto gelöscht",sql(f"select count(*) from website_fotos where id='{alt}'")=="0")
chk("Nie abgeschicktes Foto (über 24 Std.) gelöscht",sql("select count(*) from website_fotos where token='verwaist-test-0001'")=="0")
chk("Frischer, noch nicht abgeschickter Upload bleibt",sql("select count(*) from website_fotos where token='frisch-test-000001'")=="1")
chk("Noch nicht abgelaufene Fotos bleiben",int(sql(f"select count(*) from website_fotos where kunden_id='{kA}' and anfrage_id is not null"))>=4)
chk("Löschprotokoll hat beide Einträge",int(sql("select count(*) from loeschprotokoll where tabelle like 'website_fotos%'"))==n0+2)

# ---------------------------------------------------------------- Wird eine Anfrage gelöscht, verschwinden ihre Fotos
with tx("system") as cur:
    cur.execute("SELECT anfrage_id FROM website_fotos WHERE kunden_id=%s AND anfrage_id IS NOT NULL LIMIT 1",(kA,)); aid=cur.fetchone()["anfrage_id"]
    cur.execute("SELECT count(*) AS n FROM website_fotos WHERE anfrage_id=%s",(aid,)); vor=cur.fetchone()["n"]
    cur.execute("DELETE FROM anfragen WHERE id=%s",(aid,))
    cur.execute("SELECT count(*) AS n FROM website_fotos WHERE anfrage_id=%s",(aid,)); nach=cur.fetchone()["n"]
chk("Anfrage löschen entfernt ihre Fotos mit",vor>=1 and nach==0,(vor,nach))

# ---------------------------------------------------------------- Mail-Größe, Export, Kundentrennung
with tx("system") as cur:
    cur.execute("SELECT id FROM website_fotos WHERE kunden_id=%s AND loeschen_am IS NOT NULL",(kA,)); ids=[str(r["id"]) for r in cur.fetchall()]
    kl=fotos.fuer_mail(cur,kA,ids); alt_max=fotos.MAIL_MAX; fotos.MAIL_MAX=10; gross=fotos.fuer_mail(cur,kA,ids); fotos.MAIL_MAX=alt_max
    fremd=fotos.fuer_mail(cur,kB,ids)
chk("Mail-Anhänge: normal vorhanden, bei Überschreitung keine, fremder Betrieb nichts",len(kl)==len(ids)>0 and gross==[] and fremd==[],(len(kl),len(ids)))
with tx("system") as cur: z=offboarding.export_zip(cur,kA)
namen=zipfile.ZipFile(io.BytesIO(z)).namelist()
chk("Datenexport enthält die Fotos als Bilddateien",any(n.startswith("fotos/") and n.endswith(".jpg") for n in namen),[n for n in namen if "foto" in n][:5])
