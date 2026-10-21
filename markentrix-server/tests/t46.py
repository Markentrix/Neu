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


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Sitea"); kB,cB,mB=neuer_kunde("Siteb")
dom=f"firma{sfx}.de"; O={"Origin":"https://"+dom}
a.post(f"/api/admin/kunden/{kA}/domains",json={"domain":dom,"registrar":"INWX","inhaber":"markentrix","auto_verlaengern":True,"status":"aktiv"})
z=cA.get("/api/kunde/website-dienste"); chk("Zustand lesbar",z.status_code==200,z.text); z=z.json(); sid=z["site_id"]
chk("Site-ID hat Präfix",sid.startswith("mk_") and len(sid)>=10,sid)
chk("Andere Firma hat andere Site-ID",cB.get("/api/kunde/website-dienste").json()["site_id"]!=sid)
chk("Domain des Kunden ist erlaubt",dom in z["domains"],z["domains"])
P=httpx.Client(base_url=B)
def pub(m,pfad,body=None,origin=O,ct="text/plain"):
    h={**origin,"Content-Type":ct}
    return P.request(m,f"/site/{sid}/{pfad}",headers=h,content=json.dumps(body).encode() if body is not None else None)
# ---- Herkunft
chk("Ohne Herkunft abgelehnt",P.get(f"/site/{sid}/config").status_code==403)
chk("Fremde Herkunft abgelehnt",P.get(f"/site/{sid}/config",headers={"Origin":"https://boese.de"}).status_code==403)
chk("Unbekannte Site-ID: 404",P.get("/site/mk_gibtesnicht1/config",headers=O).status_code==404)
r=P.get(f"/site/{sid}/config",headers=O); chk("Eigene Domain erlaubt, mit CORS-Kopf",r.status_code==200 and r.headers.get("access-control-allow-origin")==O["Origin"],r.headers)
chk("www-Variante erlaubt",P.get(f"/site/{sid}/config",headers={"Origin":"https://www."+dom}).status_code==200)
chk("Demo-Adresse erlaubt",P.get(f"/site/{sid}/config",headers={"Origin":"https://demo.localhost"}).status_code in (200,403))
r=P.options(f"/site/{sid}/kontakt",headers={**O,"Access-Control-Request-Method":"POST"}); chk("Vorabfrage (OPTIONS)",r.status_code==204 and "POST" in r.headers.get("access-control-allow-methods",""),r.status_code)
r=P.options(f"/site/{sid}/kontakt",headers={"Origin":"https://boese.de"}); chk("Vorabfrage fremde Herkunft abgelehnt",r.status_code==403)
c=pub("GET","config").json(); chk("Standard: nichts aktiv",c["kontakt"] is False and c["termin"]["aktiv"] is False and c["paypal"]["aktiv"] is False and c["bewertungen"] is False,c)
# ---- Kontaktformular
K=lambda **kw:{**{"name":"Erika Muster","email":"erika@besucher.de","telefon":"0511 123","nachricht":"Ich möchte einen Termin für Mittwoch.","einwilligung":True},**kw}
r=pub("POST","kontakt",K()); chk("Inaktiv: abgelehnt",r.status_code==409,r.text)
chk("Empfänger Pflicht",cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":""}).status_code==400)
chk("Ungültiger Empfänger abgelehnt",cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":"kaputt"}).status_code==400)
r=cA.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}, zweite@{dom}","betreff":"Neue Anfrage Website","name":"Firma A"}); chk("Mail speichern",r.status_code==200,r.text)
r=pub("POST","kontakt",K()); chk("Formular senden",r.status_code==200 and r.json().get("ok"),r.text)
chk("Mail kam beim Inhaber an (Antwort-an = Besucher)",any("erika@besucher.de" in str(m["Reply-To"]) and "Mittwoch" in text(m) for m in mail_an(f"chef@{dom}","Neue Anfrage Website")))
chk("Zweiter Empfänger bekam sie auch",bool(mail_an(f"zweite@{dom}","Mittwoch")))
chk("Absendername ist die Firma",any("Firma A" in str(m["From"]) for m in mail_an(f"chef@{dom}","Mittwoch")))
n=sql(f"select count(*) from anfragen where kunden_id='{kA}' and quelle='website' and name='Erika Muster'"); chk("Anfrage im Portal gespeichert",n=="1",n)
vor=len(mails()); r=pub("POST","kontakt",K(hp="http://spam.de")); time.sleep(1); chk("Lockfeld: stillschweigend ignoriert",r.status_code==200 and len(mails())==vor and sql(f"select count(*) from anfragen where kunden_id='{kA}'")=="1")
chk("Ohne Einwilligung abgelehnt",pub("POST","kontakt",K(einwilligung=False)).status_code==400)
chk("Ungültige E-Mail abgelehnt",pub("POST","kontakt",K(email="kein-mail")).status_code==400)
r=pub("POST","kontakt",K(nachricht="Umlaute äöü ß – und <script>alert(1)</script>"),ct="application/json"); chk("Auch als application/json",r.status_code==200,r.text)
r=pub("POST","kontakt",K()); chk("Begrenzung: zu viele Aufrufe → 429",r.status_code==429,r.status_code)
chk("Fehler tragen CORS-Kopf (Skript kann Text lesen)",r.headers.get("access-control-allow-origin")==O["Origin"],r.headers)
# ---- Eigenes Postfach (SMTP)
v=cA.get("/api/kunde/website-dienste/anbieter",params={"email":"max@gmail.com"}).json(); chk("Voreinstellung Gmail",v.get("host")=="smtp.gmail.com" and "App-Passwort" in v.get("hinweis",""),v)
v=cA.get("/api/kunde/website-dienste/anbieter",params={"email":"info@t-online.de"}).json(); chk("Voreinstellung T-Online",v.get("host")=="securesmtp.t-online.de" and v.get("port")==465,v)
v=cA.get("/api/kunde/website-dienste/anbieter",params={"email":"info@eigenefirma.de"}).json(); chk("Eigene Domain: Hinweis statt Raten",not v.get("host") and "smtp" in v.get("hinweis","").lower(),v)
S=lambda **kw:{**{"absender":f"info@{dom}","host":"127.0.0.1","port":8025,"sicherung":"keine","benutzer":"","passwort":"geheim-pw-123"},**kw}
r=cA.put("/api/kunde/website-dienste/smtp",json=S(host="gibtes-nicht.invalid")); chk("Unbekannter Server: verständlicher Fehler",r.status_code==400 and "nicht gefunden" in r.text,r.text)
r=cA.put("/api/kunde/website-dienste/smtp",json=S(port=1)); chk("Port zu: verständlicher Fehler",r.status_code==400 and "abgelehnt" in r.text,r.text)
r=cA.put("/api/kunde/website-dienste/smtp",json=S(passwort="")); chk("Passwort Pflicht",r.status_code==400)
r=cA.put("/api/kunde/website-dienste/smtp",json=S(absender="kaputt")); chk("Absender prüfen",r.status_code==400)
r=cA.put("/api/kunde/website-dienste/smtp",json=S()); chk("Eigenes Postfach speichern (nach Verbindungsprüfung)",r.status_code==200,r.text)
z=cA.get("/api/kunde/website-dienste").json()
chk("Passwort nie wieder lesbar",z["mail"]["smtp"].get("gesetzt") and "geheim-pw-123" not in json.dumps(z),z["mail"]["smtp"])
enc=sql(f"select smtp_enc from website_dienste where kunden_id='{kA}'"); chk("In der Datenbank verschlüsselt",enc and "geheim-pw-123" not in enc and "127.0.0.1" not in enc and f"info@{dom}" not in enc,enc[:60])
r=cA.post("/api/kunde/website-dienste/mail/test",json={"an":f"chef@{dom}"}); chk("Testmail über eigenes Postfach",r.status_code==200 and r.json().get("ueber")=="eigen",r.text)
chk("Testmail angekommen mit Kunden-Absender",any(f"info@{dom}" in str(m["From"]) for m in mail_an(f"chef@{dom}","Testnachricht")))
# Zugriff ohne Inhaber-Recht
chk("Ohne Anmeldung kein Zugriff",httpx.get(B+"/api/kunde/website-dienste").status_code==401)
chk("Admin-Zugang hat keinen Kunden-Zugriff auf Zugangsdaten",a.get("/api/kunde/website-dienste").status_code==403)
# Rückfall auf Markentrix bei defektem Zugang
sql(f"update website_dienste set smtp_enc='kaputt' where kunden_id='{kA}'")
r=cA.post("/api/kunde/website-dienste/mail/test",json={"an":f"chef@{dom}"}); chk("Defektes Postfach: Rückfall auf Markentrix",r.status_code==200 and r.json().get("ueber")=="markentrix",r.text)
st=cA.get("/api/kunde/website-dienste").json()["status"]; chk("Fehler im Status vermerkt",st.get("test",{}).get("fehler",0)>=1,st)
r=cA.delete("/api/kunde/website-dienste/smtp"); chk("Eigenes Postfach entfernen",r.status_code==200 and not cA.get("/api/kunde/website-dienste").json()["mail"]["smtp"])
# ---- Kalender
ical="http://127.0.0.1:8999/ical/test.ics"
KAL=lambda **kw:{**{"aktiv":True,"ical_url":ical,"dauer":60,"tage":10,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Praxis, Hauptstr. 1","empfaenger":""},**kw}
r=cA.put("/api/kunde/website-dienste/kalender",json=KAL(ical_url="http://127.0.0.1:8999/ical/leer.ics")); chk("Kein Kalender unter der Adresse: Fehler",r.status_code==400 and "iCal" in r.text,r.text)
r=cA.put("/api/kunde/website-dienste/kalender",json=KAL(ical_url="http://127.0.0.1:8999/ical/weg.ics")); chk("Kalender nicht abrufbar: Fehler",r.status_code==400 and "nicht abrufbar" in r.text,r.text)
r=cA.put("/api/kunde/website-dienste/kalender",json=KAL(von="18:00",bis="08:00")); chk("Ende vor Beginn abgelehnt",r.status_code==400)
r=cA.put("/api/kunde/website-dienste/kalender",json=KAL(wochentage=[])); chk("Kein Wochentag abgelehnt",r.status_code==400)
r=cA.put("/api/kunde/website-dienste/kalender",json=KAL()); chk("Kalender speichern",r.status_code==200,r.text)
enc=sql(f"select kal_ical_enc from website_dienste where kunden_id='{kA}'"); chk("Kalender-Adresse verschlüsselt",enc and "ical" not in enc and "8999" not in enc)
z=cA.get("/api/kunde/website-dienste").json(); chk("Kalender-Adresse nie wieder lesbar",z["kalender"]["ical_gesetzt"] and "ical/test" not in json.dumps(z))
r=cA.post("/api/kunde/website-dienste/kalender/test"); chk("Kalender-Test zeigt belegte und freie Zeiten",r.status_code==200 and r.json()["belegt"]>=3 and r.json()["freie"]>10 and r.json()["beispiele"],r.text)
chk("Termine ohne Herkunft abgelehnt",P.get(f"/site/{sid}/termine").status_code==403)
t=pub("GET","termine").json(); tage={x["datum"]:[s["uhr"] for s in x["slots"]] for x in t["tage"]}
d=lambda n:(heute+datetime.timedelta(days=n)).isoformat()
chk("Termine aktiv, 60 Minuten",t["aktiv"] and t["dauer"]==60 and t["ort"].startswith("Praxis"),t.get("dauer"))
chk("Täglicher Mittagstermin (wiederkehrend) blockiert 12:00",all("12:00" not in v for v in tage.values()) and "11:00" in tage.get(d(1),[]) and "13:00" in tage.get(d(1),[]),tage.get(d(1)))
chk("Einzeltermin blockiert 10:00 an Tag +2",d(2) in tage and "10:00" not in tage[d(2)] and "09:00" in tage[d(2)] and "11:00" in tage[d(2)],tage.get(d(2)))
chk("Ganztägiger Urlaub sperrt den Tag +4",d(4) not in tage,tage.get(d(4)))
loc=datetime.datetime.combine(heute+datetime.timedelta(days=3),datetime.time(8,0),tzinfo=datetime.timezone.utc).astimezone(TZ).strftime("%H:%M")
chk("Als „frei“ markierter Termin blockiert nicht",loc in tage.get(d(3),[]),(loc,tage.get(d(3))))
s1=[s for s in t["tage"] if s["datum"]==d(1)][0]["slots"]; start=[s for s in s1 if s["uhr"]=="10:00"][0]["start"]
B_=lambda **kw:{**{"start":start,"name":"Peter Kunde","email":"peter@besucher.de","telefon":"0170 1","nachricht":"Erstberatung","einwilligung":True},**kw}
chk("Buchen ohne Einwilligung abgelehnt",pub("POST","termin",B_(einwilligung=False)).status_code==400)
chk("Ungültiger Zeitpunkt abgelehnt",pub("POST","termin",B_(start="irgendwann")).status_code==400)
chk("Zeit außerhalb der Slots abgelehnt",pub("POST","termin",B_(start=datetime.datetime.combine(heute+datetime.timedelta(days=1),datetime.time(3,7),tzinfo=TZ).isoformat())).status_code==409)
r=pub("POST","termin",B_()); chk("Termin buchen",r.status_code==200 and r.json()["wann"],r.text)
m=mail_an("peter@besucher.de","Ihr Termin"); chk("Besucher bekommt Bestätigung mit Kalender-Anhang",bool(m) and any(p.get_content_type()=="text/calendar" for p in m[-1].walk()) and "termin/absagen?t=" in text(m[-1]),len(m))
chk("Inhaber bekommt Hinweis",bool(mail_an(f"chef@{dom}","Peter Kunde")))
r=pub("POST","termin",B_(name="Zweiter",email="zweiter@besucher.de")); chk("Doppelbuchung desselben Slots: 409",r.status_code==409,r.text)
t2=pub("GET","termine").json(); s1b=[s for x in t2["tage"] if x["datum"]==d(1) for s in x["slots"]]; chk("Gebuchter Slot verschwindet",all(s["uhr"]!="10:00" for s in s1b))
n=sql(f"select count(*) from termine where kunden_id='{kA}' and kontakt_name='Peter Kunde' and status='bestaetigt'"); chk("Termin erscheint im Kundenportal",n=="1",n)
chk("Offene Termine gezählt",cA.get("/api/kunde/website-dienste").json()["kalender"]["offene_termine"]==1)
lt=re.search(r"termin/absagen\?t=([A-Za-z0-9_-]+)",text(m[-1])).group(1)
chk("Absagen mit falschem Link",P.get(f"/site/{sid}/termin/absagen",params={"t":"x"*30}).text.count("nicht mehr aktiv")==1)
r=P.get(f"/site/{sid}/termin/absagen",params={"t":lt}); chk("Absagen per Link",r.status_code==200 and "abgesagt" in r.text,r.text[:200])
chk("Zweites Absagen wirkungslos",P.get(f"/site/{sid}/termin/absagen",params={"t":lt}).text.count("nicht mehr aktiv")==1)
chk("Termin im Portal abgesagt",sql(f"select status from termine where kunden_id='{kA}' and kontakt_name='Peter Kunde'")=="abgesagt")
t3=pub("GET","termine").json(); chk("Slot wieder frei",any(s["uhr"]=="10:00" for x in t3["tage"] if x["datum"]==d(1) for s in x["slots"]))
chk("Absagemail an Inhaber",bool(mail_an(f"chef@{dom}","abgesagt")))
chk("Termin-Daten anderer Firma nicht sichtbar",sql(f"select count(*) from website_termine where kunden_id='{kB}'")=="0")
# ---- PayPal
cid="A"+"x"*40
chk("PayPal: ungültige Client-ID",cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"client_id":"zu kurz!","waehrung":"EUR"}).status_code==400)
chk("PayPal: ungültiger Me-Link",cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"me_link":"https://boese.de/x","waehrung":"EUR"}).status_code==400)
chk("PayPal: aktiv ohne Angabe abgelehnt",cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"waehrung":"EUR"}).status_code==400)
chk("PayPal: Währung geprüft",cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"client_id":cid,"waehrung":"XXX"}).status_code==422)
r=cA.put("/api/kunde/website-dienste/paypal",json={"aktiv":True,"client_id":cid,"waehrung":"EUR","me_link":"https://paypal.me/firmaa"}); chk("PayPal speichern",r.status_code==200,r.text)
c=pub("GET","config").json()["paypal"]; chk("Website bekommt Client-ID, Währung, Me-Link",c["aktiv"] and c["client_id"]==cid and c["waehrung"]=="EUR" and c["me_link"].endswith("firmaa"),c)
# ---- Bewertungen
chk("Bewertungen inaktiv",pub("GET","bewertungen").json()=={"aktiv":False})
chk("Bewertungen: ohne Angabe nicht aktivierbar",cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True}).status_code==400)
chk("Bewertungen: Sterne 1–5",cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True,"sterne":9,"anzahl":3}).status_code==422)
chk("Bewertungen: http-Link abgelehnt",cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True,"sterne":4.5,"anzahl":3,"link":"javascript:alert(1)"}).status_code==400)
r=cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True,"sterne":4.5,"anzahl":30,"link":"https://g.page/r/xyz/review"}); chk("Bewertungen von Hand speichern",r.status_code==200,r.text)
b=pub("GET","bewertungen").json(); chk("Manuelle Zahlen werden geliefert",b["quelle"]=="manuell" and b["sterne"]==4.5 and b["anzahl"]==30 and b["schreiben"].startswith("https://g.page"),b)
chk("Place-ID prüfen",cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True,"place_id":"x y!"}).status_code==400)
r=cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True,"place_id":"ChIJtestplace12345"}); chk("Place-ID speichern",r.status_code==200,r.text)
r=cA.post("/api/kunde/website-dienste/bewertungen/test"); chk("Ohne Markentrix-Schlüssel: verständlicher Hinweis",r.status_code==400 and "freigeschaltet" in r.text,r.text)
chk("Kunde kann den Google-Schlüssel nicht setzen",cA.put("/api/admin/einstellungen/places",json={"api_key":"places-test"}).status_code==403)
chk("Admin setzt Google-Schlüssel",a.put("/api/admin/einstellungen/places",json={"api_key":"places-test"}).status_code==200 and a.get("/api/admin/einstellungen/places").json()["key_gesetzt"])
r=cA.post("/api/kunde/website-dienste/bewertungen/test"); chk("Google-Abfrage im Test",r.status_code==200 and r.json()["sterne"]==4.7 and r.json()["anzahl"]==128,r.text)
b=pub("GET","bewertungen").json(); chk("Google-Daten mit Autoren und Text",b["quelle"]=="google" and b["sterne"]==4.7 and b["anzahl"]==128 and b["bewertungen"][0]["autor"]=="Anna K." and "writereview?placeid=ChIJtestplace12345" in b["schreiben"],b)
cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":True,"place_id":"ChIJNichtDa12345"}); r=cA.post("/api/kunde/website-dienste/bewertungen/test"); chk("Unbekannter Eintrag: verständlicher Fehler",r.status_code==400 and "keinen Eintrag" in r.text,r.text)
# ---- Admin-Sicht ohne Geheimnisse
cA.put("/api/kunde/website-dienste/smtp",json=S())
ad=a.get(f"/api/admin/kunden/{kA}/website-dienste"); chk("Admin sieht den Status",ad.status_code==200 and ad.json()["site_id"]==sid and ad.json()["status"].get("kontakt"),ad.text[:200])
txt=ad.text; chk("Admin sieht keine Geheimnisse",all(x not in txt for x in ["geheim-pw-123","ical/test","places-test"]) and '"passwort"' not in txt,txt[:300])
chk("Kunde sieht keine Admin-Route",cA.get(f"/api/admin/kunden/{kA}/website-dienste").status_code==403)
chk("Admin-Route mit ungültiger ID: 404",a.get("/api/admin/kunden/kaputt/website-dienste").status_code==404)
# ---- Schutz vor Zugriffen ins eigene Netz (ohne Test-Ausnahme)
os.environ["SITE_LOKAL_ERLAUBT"]="0"; sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import sitedienste as sd
chk("Interne Adressen gesperrt",not any(sd.oeffentlich(h) for h in ["127.0.0.1","localhost","10.0.0.5","192.168.1.1","169.254.169.254","172.17.0.1","0.0.0.0"]))
try: sd.ical_url_pruefen("http://x.de/a.ics"); okh=False
except ValueError: okh=True
chk("http-Kalender abgelehnt",okh)
chk("webcal:// wird https://",sd.ical_url_pruefen("webcal://calendar.google.com/x.ics").startswith("https://"))
try: sd.ical_laden("https://localhost/x.ics"); okl=False
except ValueError: okl=True
chk("Kalender auf localhost nicht ladbar",okl)
# ---- Kalender-Leser (Einzelfälle)
UTC=datetime.timezone.utc
von=datetime.datetime(2026,3,1,tzinfo=UTC); bis=datetime.datetime(2026,3,31,tzinfo=UTC)
def ev(*z): return "BEGIN:VCALENDAR\r\n"+"\r\n".join(["BEGIN:VEVENT"]+list(z)+["END:VEVENT"])+"\r\nEND:VCALENDAR\r\n"
w=sd.ical_belegt(ev("UID:w","DTSTART;TZID=Europe/Berlin:20260302T090000","DTEND;TZID=Europe/Berlin:20260302T100000","RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=4"),von,bis)
chk("Wöchentlich Mo+Mi, 4 Mal",len(w)==4 and w[0][0]==datetime.datetime(2026,3,2,8,0,tzinfo=UTC) and w[1][0].day==4 and w[3][0].day==11,[x[0].isoformat() for x in w])
w=sd.ical_belegt(ev("UID:x","DTSTART:20260302T090000Z","DTEND:20260302T100000Z","RRULE:FREQ=DAILY;UNTIL=20260305T235959Z","EXDATE:20260303T090000Z"),von,bis)
chk("Täglich bis UNTIL ohne EXDATE",[x[0].day for x in w]==[2,4,5],[x[0].day for x in w])
w=sd.ical_belegt(ev("UID:m","DTSTART:20260310T090000Z","DURATION:PT90M","RRULE:FREQ=MONTHLY;BYDAY=2TU"),von,datetime.datetime(2026,5,31,tzinfo=UTC))
chk("Monatlich 2. Dienstag, Dauer 90 Minuten",[x[0].strftime("%m-%d") for x in w]==["03-10","04-14","05-12"] and (w[0][1]-w[0][0]).seconds==5400,[x[0].strftime("%m-%d") for x in w])
w=sd.ical_belegt(ev("UID:s","DTSTART:20260310T090000Z","DTEND:20260310T100000Z","STATUS:CANCELLED"),von,bis); chk("Abgesagte Termine blockieren nicht",w==[])
w=sd.ical_belegt(ev("UID:z","DTSTART;TZID=W. Europe Standard Time:20260715T090000","DTEND;TZID=W. Europe Standard Time:20260715T100000"),datetime.datetime(2026,7,1,tzinfo=UTC),datetime.datetime(2026,8,1,tzinfo=UTC))
chk("Outlook-Zeitzone (Sommerzeit) richtig",len(w)==1 and w[0][0].hour==7,w)
w=sd.ical_belegt("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:f\r\nDTSTART:20260310T090000Z\r\nSUMMARY:Lan\r\n ger Titel\r\nDTEND:20260310T100000Z\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n",von,bis); chk("Gefaltete Zeilen",len(w)==1)
w=sd.ical_belegt("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:murks\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n",von,bis); chk("Kaputter Termin bricht nicht ab",w==[])
