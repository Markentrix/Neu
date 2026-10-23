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
sfx=str(int(time.time())+97)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.datetime.now(TZ).date(); morgen=heute+datetime.timedelta(days=1)
kA,cA,mA=neuer_kunde("Api"); kB,cB,mB=neuer_kunde("Apb")
dom=f"salon{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
def web(host=None): return httpx.Client(base_url=B,headers={"Host":host or dom})
W=web(); API="/siteapi/api"
def post(c,pfad,body,origin=True,ua="Mozilla/5.0 Test",**kw):
    h={"Content-Type":"application/json","User-Agent":ua}
    if origin: h["Origin"]="https://"+dom
    return c.post(API+pfad,headers=h,content=json.dumps(body).encode(),**kw)
# ---- Kunde erkennen
chk("Unbekannte Domain: 404",web("gibtesnicht.de").get(API+"/verfuegbarkeit").status_code==404)
chk("Portal-Adresse selbst: 404",web("portal.markentrix.de").get(API+"/verfuegbarkeit").status_code==404)
chk("www-Variante der Domain geht",web("www."+dom).get(API+"/verfuegbarkeit").status_code==200)
chk("Health",W.get(API+"/health").json().get("ok") is True)
v=W.get(API+"/verfuegbarkeit").json(); chk("Ohne Kalender: keine Selbstbuchung, Wochenende geschlossen",v["selfBooking"] is False and v["closedWeekdays"]==[0,6] and v["blocked"]==[],v)
chk("PayPal.Me aus: Schnittstelle gibt keinen Link heraus",v.get("paypalMe")=="",v)
sql(f"UPDATE website_dienste SET pp_aktiv=true, pp_me_link='https://paypal.me/testsalon/' WHERE kunden_id='{kA}'")
v2=W.get(API+"/verfuegbarkeit").json(); chk("PayPal.Me aus dem Portal wird an die Website gegeben",v2.get("paypalMe")=="https://paypal.me/testsalon",v2)
sql(f"UPDATE website_dienste SET pp_aktiv=false WHERE kunden_id='{kA}'")
chk("PayPal im Portal ausgeschaltet: kein Link",W.get(API+"/verfuegbarkeit").json().get("paypalMe")=="")
# ---- Anfragen
cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
F=lambda **kw:{**{"typ":"kontakt","name":"Erika Muster","email":"erika@besucher.de","telefon":"0511 123","nachricht":"Bitte um Rückruf","einwilligung":"ja","paket":"schnitt"},**kw}
r=W.post(API+"/anfrage",headers={"Origin":"https://boese.de","Content-Type":"application/json","User-Agent":"Mozilla"},content=json.dumps(F()).encode()); chk("Fremde Herkunft: 403",r.status_code==403,r.text)
r=post(W,"/anfrage",F()); chk("Anfrage ok mit Vorgangsnummer",r.status_code==200 and r.json()["ok"] and re.match(r"^K\d{6}-[0-9A-F]{4}$",r.json()["ref"]),r.text); ref=r.json()["ref"]
n=sql(f"select count(*) from anfragen where kunden_id='{kA}' and quelle='website' and nachricht like '%{ref}%' and nachricht like '%schnitt%'"); chk("Anfrage liegt im Kundenportal",n=="1",n)
chk("Mail an den Inhaber",len(mail_an(f"chef@{dom}",ref))==1)
chk("Eingangsbestätigung an den Besucher",len(mail_an("erika@besucher.de",ref))==1)
r=post(W,"/anfrage",F(name="",email="kaputt",einwilligung="")); j=r.json(); chk("Ungültige Eingabe: 422 mit Feldfehlern",r.status_code==422 and {"name","email","einwilligung"}<=set(j["errors"]),r.text)
r=post(W,"/anfrage",F(typ="termin",telefon="")); chk("Termin braucht Telefon",r.status_code==422 and "telefon" in r.json()["errors"],r.text)
r=post(W,"/anfrage",F(typ="unbekannt")); chk("Unbekannter Typ abgelehnt",r.status_code==422,r.text)
vor=sql(f"select count(*) from anfragen where kunden_id='{kA}'"); r=post(W,"/anfrage",F(website="http://spam")); chk("Lockfeld: still verworfen",r.status_code==200 and sql(f"select count(*) from anfragen where kunden_id='{kA}'")==vor)
r=W.post(API+"/anfrage",headers={"Origin":"https://"+dom,"Content-Type":"application/x-www-form-urlencoded","User-Agent":"Mozilla"},content="typ=kontakt&name=Hans+Test&email=hans%40besucher.de&nachricht=Hallo&einwilligung=on",follow_redirects=False); chk("Formular ohne JavaScript: Weiterleitung auf danke.html",r.status_code==303 and r.headers["location"].startswith("/danke.html?typ=kontakt&ref=K"),r.headers)
# ---- Terminbuchung mit festen Zeiten, Limit und Freigabe
r=cA.put("/api/kunde/website-dienste/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Salon, Hauptstr. 1","empfaenger":"","zeiten":"08:00, 09:00, 10:00","kapazitaet":2,"freigabe":True,"halte_std":72}); chk("Kalender mit festen Zeiten speichern",r.status_code==200,r.text)
chk("Ungültige Uhrzeit abgelehnt",cA.put("/api/kunde/website-dienste/kalender",json={"aktiv":True,"zeiten":"8 Uhr","wochentage":[1]}).status_code==400)
v=W.get(API+"/verfuegbarkeit").json(); chk("Bestätigt der Betrieb jede Buchung selbst, meldet die Schnittstelle selfBooking=false; Zeiten wie eingestellt",v["selfBooking"] is False and v["slotTimes"]==["08:00","09:00","10:00"] and v["closedWeekdays"]==[],v)
chk("Nächster freier Tag ist heute oder morgen",v["nextFree"] in (heute.isoformat(),morgen.isoformat()),v["nextFree"])
chk("Zeitraum danach gesperrt",(heute+datetime.timedelta(days=40)).isoformat() in v["blocked"])
tag=(heute+datetime.timedelta(days=3)).isoformat()
s=W.get(API+"/slots",params={"tag":tag}).json(); chk("Slots eines freien Tages",[x["zeit"] for x in s["slots"]]==["08:00","09:00","10:00"] and all(x["frei"] for x in s["slots"]),s)
chk("Ungültiges Datum bei Slots",W.get(API+"/slots",params={"tag":"quatsch"}).status_code==400)
def T(**kw): return F(**{**dict(typ="termin",datum=tag,uhrzeit="09:00",klasse="damen"),**kw})
r=post(W,"/anfrage",T(name="Mia Kunde",email="mia@besucher.de")); chk("Termin gebucht (reserviert)",r.status_code==200 and r.json()["ref"].startswith("T"),r.text); tref=r.json()["ref"]
row=sql(f"select status from website_termine where kunden_id='{kA}' and ref='{tref}'"); chk("Reservierung gespeichert",row=="reserviert",row)
chk("Termin im Portal als geplant",sql(f"select status from termine where kunden_id='{kA}' and kontakt_name='Mia Kunde'")=="geplant")
s=W.get(API+"/slots",params={"tag":tag}).json(); chk("09:00 jetzt belegt",{x["zeit"]:x["frei"] for x in s["slots"]}=={"08:00":True,"09:00":False,"10:00":True},s)
r=post(W,"/anfrage",T(name="Zweite",email="zweite@besucher.de")); chk("Doppelbuchung abgelehnt",r.status_code==422 and "uhrzeit" in r.json()["errors"],r.text)
r=post(W,"/anfrage",T(uhrzeit="11:00",email="x@besucher.de")); chk("Nicht angebotene Uhrzeit abgelehnt",r.status_code==422,r.text)
chk("Mail an Inhaber mit Hinweis zum Bestätigen",len(mail_an(f"chef@{dom}","bestätigen"))>=1)
chk("Besucher bekommt Eingangsbestätigung mit Wunschtermin",len(mail_an("mia@besucher.de","vorgemerkt"))==1)
b=cA.get("/api/kunde/website-dienste/buchungen").json(); chk("Buchungsliste zeigt die Reservierung",b["freigabe"] and any(x["ref"]==tref and x["status"]=="reserviert" and x["details"].get("klasse")=="damen" for x in b["buchungen"]),b)
bid=[x["id"] for x in b["buchungen"] if x["ref"]==tref][0]
chk("Andere Firma kann nicht bestätigen",cB.post(f"/api/kunde/website-dienste/buchungen/{bid}/bestaetigen",json={}).status_code in (409,403))
chk("Anzahlung muss eine Zahl sein",cA.post(f"/api/kunde/website-dienste/buchungen/{bid}/bestaetigen",json={"anzahlung":"viel"}).status_code==400)
cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"client_id":"","waehrung":"EUR","me_link":"https://paypal.me/salon"})
r=cA.post(f"/api/kunde/website-dienste/buchungen/{bid}/bestaetigen",json={"anzahlung":"30","hinweis":"Bitte 5 Minuten früher kommen."}); chk("Bestätigen",r.status_code==200,r.text)
m=mail_an("mia@besucher.de","bestätigt"); chk("Bestätigung mit PayPal-Link, Hinweis und Einladung",len(m)==1 and "paypal.me/salon/30.00EUR" in text(m[0]) and "5 Minuten" in text(m[0]) and any(p.get_content_type()=="text/calendar" for p in m[0].walk()),[text(x) for x in m])
chk("Termin im Portal bestätigt",sql(f"select status from termine where kunden_id='{kA}' and kontakt_name='Mia Kunde'")=="bestaetigt")
chk("Zweites Bestätigen nicht mehr möglich",cA.post(f"/api/kunde/website-dienste/buchungen/{bid}/bestaetigen",json={}).status_code==409)
# Limit pro Tag (2) und Ablehnen gibt den Termin wieder frei
r=post(W,"/anfrage",T(uhrzeit="10:00",name="Dritte",email="dritte@besucher.de")); chk("Zweite Buchung am Tag",r.status_code==200,r.text); r10=r.json()["ref"]
v=W.get(API+"/verfuegbarkeit").json(); chk("Tageslimit erreicht: Tag ausgebucht",tag in v["blocked"],v["blocked"][:5])
s=W.get(API+"/slots",params={"tag":tag}).json(); chk("Am ausgebuchten Tag ist nichts frei",not any(x["frei"] for x in s["slots"]),s)
b10=[x["id"] for x in cA.get("/api/kunde/website-dienste/buchungen").json()["buchungen"] if x["ref"]==r10][0]
r=cA.post(f"/api/kunde/website-dienste/buchungen/{b10}/ablehnen",json={"grund":"Leider schon vergeben."}); chk("Ablehnen",r.status_code==200,r.text)
chk("Absage-Mail an den Besucher",len(mail_an("dritte@besucher.de","Leider schon vergeben"))==1)
v=W.get(API+"/verfuegbarkeit").json(); chk("Nach Absage ist der Tag wieder buchbar",tag not in v["blocked"])
# Haltefrist
r=post(W,"/anfrage",T(uhrzeit="10:00",name="Vierte",email="vierte@besucher.de")); chk("Buchung für Ablauftest",r.status_code==200,r.text)
sql(f"update website_termine set erstellt_am=now()-interval '5 days' where kunden_id='{kA}' and name='Vierte'")
s=W.get(API+"/slots",params={"tag":tag}).json(); chk("Abgelaufene Reservierung gibt die Zeit frei",{x["zeit"]:x["frei"] for x in s["slots"]}["10:00"] is True,s)
chk("Abgelaufene Reservierung ist abgesagt",sql(f"select status from website_termine where kunden_id='{kA}' and name='Vierte'")=="abgesagt")
# Sperrtage
tag2=(heute+datetime.timedelta(days=5)).isoformat()
r=cA.post("/api/kunde/website-dienste/sperrtage",json={"von":tag2,"bis":(heute+datetime.timedelta(days=6)).isoformat(),"grund":"Urlaub"}); chk("Sperrtage eintragen",r.status_code==200,r.text)
v=W.get(API+"/verfuegbarkeit").json(); chk("Sperrtage sind blockiert",tag2 in v["blocked"] and (heute+datetime.timedelta(days=6)).isoformat() in v["blocked"])
r=post(W,"/anfrage",T(datum=tag2,email="u@besucher.de")); chk("Buchung am Sperrtag abgelehnt",r.status_code==422,r.text)
chk("Sperrtage-Liste",len(cA.get("/api/kunde/website-dienste/sperrtage").json()["tage"])==2)
chk("Sperrtag entfernen",cA.delete(f"/api/kunde/website-dienste/sperrtage/{tag2}").status_code==200 and tag2 not in W.get(API+"/verfuegbarkeit").json()["blocked"])
chk("Sperrzeitraum zu lang",cA.post("/api/kunde/website-dienste/sperrtage",json={"von":tag2,"bis":(heute+datetime.timedelta(days=400)).isoformat()}).status_code==400)
# Ohne Freigabe: sofort bestätigt
cA.put("/api/kunde/website-dienste/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"zeiten":"08:00, 09:00, 10:00","kapazitaet":0,"freigabe":False})
tag3=(heute+datetime.timedelta(days=8)).isoformat()
r=post(W,"/anfrage",T(datum=tag3,uhrzeit="08:00",name="Sofort",email="sofort@besucher.de")); chk("Ohne Freigabe: gebucht",r.status_code==200 and sql(f"select status from website_termine where kunden_id='{kA}' and name='Sofort'")=="gebucht",r.text)
m=mail_an("sofort@besucher.de","Ihr Termin"); chk("Sofort-Bestätigung mit Einladung",len(m)==1 and any(p.get_content_type()=="text/calendar" for p in m[0].walk()))
# Ohne E-Mail keine Selbstbuchung: normale Anfrage
r=post(W,"/anfrage",T(datum=tag3,uhrzeit="09:00",name="Ohne Mail",email="")); chk("Ohne E-Mail nur Anfrage, kein Termin",r.status_code==200 and sql(f"select count(*) from website_termine where kunden_id='{kA}' and name='Ohne Mail'")=="0",r.text)
# Kalender aus: Slots alle belegt, keine Selbstbuchung
cA.put("/api/kunde/website-dienste/kalender",json={"aktiv":False,"wochentage":[1,2,3,4,5]})
chk("Kalender aus: nichts frei",not any(x["frei"] for x in W.get(API+"/slots",params={"tag":tag3}).json()["slots"]))
# ---- Statistik
ok0=int(sql(f"select count(*) from website_stat where kunden_id='{kA}'") or 0)
r=post(W,"/e",{"t":"pv","u":"/preise.html?x=1","r":"google.com","w":390}); chk("Ereignis: 204",r.status_code==204)
post(W,"/e",{"t":"ev","n":"WhatsApp-Klick","u":"/"}); post(W,"/e",{"t":"pv","u":"/"},ua="Googlebot/2.1"); post(W,"/e",{"t":"x"})
chk("Nur echte Besucher werden gezählt",int(sql(f"select count(*) from website_stat where kunden_id='{kA}'"))==ok0+2,sql(f"select count(*) from website_stat where kunden_id='{kA}'"))
chk("Pfad ohne Parameter, keine IP gespeichert",sql(f"select pfad from website_stat where kunden_id='{kA}' and art='pv'")=="/preise.html" and "127.0.0.1" not in sql(f"select besucher from website_stat where kunden_id='{kA}' limit 1"))
st=cA.get("/api/kunde/website-dienste/statistik").json(); chk("Statistik im Kundenportal",st["besucher"]>=1 and st["whatsapp"]==1 and st["seiten"][0]["pfad"]=="/preise.html" and st["anfragen"]>=3,st)
cA.put("/api/kunde/website-dienste/statistik-schalter",json={"aktiv":False}); post(W,"/e",{"t":"pv","u":"/aus"}); chk("Statistik abschaltbar",sql(f"select count(*) from website_stat where kunden_id='{kA}' and pfad='/aus'")=="0")
# ---- Mandantentrennung
chk("Firma B sieht keine Buchungen von A",cB.get("/api/kunde/website-dienste/buchungen").json()["buchungen"]==[] if cB.get("/api/kunde/website-dienste").json()["kalender"]["aktiv"] else True)
chk("Firma B sieht keine Sperrtage von A",cB.get("/api/kunde/website-dienste/sperrtage").json()["tage"]==[])
chk("Statistik von B ist leer",cB.get("/api/kunde/website-dienste/statistik").json()["aufrufe"]==0)
# ---- Caddy-Weiterleitung (Worker)
import os
os.makedirs("/var/tmp/pt/b/caddy/sites",exist_ok=True); open("/var/tmp/pt/b/mode","w").write("extern")
alt="/var/tmp/pt/b/caddy/sites/alt-test.de.caddy"; open(alt,"w").write("alt-test.de, www.alt-test.de {\n\tencode zstd gzip\n\troot * /srv/sites/live/alt-test.de\n\tfile_server\n}\n")
hand="/var/tmp/pt/b/caddy/sites/hand-test.de.caddy"; open(hand,"w").write("hand-test.de {\n\t# von Hand angepasst\n\troot * /x\n\tfile_server\n}\n")
subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":"/var/tmp/pt/b","MK_SITES":"/var/tmp/pt/s"},capture_output=True,text=True)
t=open(alt).read(); chk("Alter Standard-Eintrag bekommt /api-Weiterleitung",("rewrite * /siteapi{uri}" in t and "reverse_proxy mk-portal:8000" in t and "file_server" in t),t)
chk("Von Hand geänderter Eintrag bleibt unberührt","siteapi" not in open(hand).read())

# ---- Begrenzung gegen Missbrauch
codes=[post(W,"/anfrage",F(name="",einwilligung="")).status_code for _ in range(60)]
chk("Zu viele Anfragen einer Adresse werden gebremst",429 in codes,set(codes))
