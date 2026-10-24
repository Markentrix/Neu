"""Sicherheit (Rate-Limit in der Datenbank, Kunden-2FA, 2FA-Reset nur Haupt-Admin, Dubletten-Meldung, Push-Absicherung), abgelaufene Angebote, Zustellfehler, Löschkonzept-Prüfung."""
import httpx, time, re, email, email.header, json, os, sys, subprocess, datetime, zoneinfo
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def teil(m,typ):
    for p in m.walk():
        if p.get_content_type()==typ: return p.get_payload(decode=True).decode("utf8","replace")
text=lambda m: teil(m,"text/plain")
betreff=lambda m: str(email.header.make_header(email.header.decode_header(m["Subject"])))
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+1400)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, angebotserinnerung, offboarding, push, security, config
from app.db import tx
db.open_pool()

from fastapi import HTTPException
# ---------------------------------------------------------------- Löschkonzept: jede Tabelle mit kunden_id ist geregelt
tabs=set(sql("select table_name from information_schema.columns where table_schema='public' and column_name='kunden_id'").split())
geregelt=set(offboarding.LOESCH_TABELLEN)|set(offboarding.AUFBEWAHREN)
chk("Löschkonzept: keine Tabelle mit kunden_id ohne Regel",not (tabs-geregelt),sorted(tabs-geregelt))
chk("Löschkonzept: Listen verweisen nur auf echte Tabellen",not (geregelt-tabs),sorted(geregelt-tabs))
chk("Löschkonzept: nichts doppelt",not (set(offboarding.LOESCH_TABELLEN)&set(offboarding.AUFBEWAHREN)) and len(offboarding.LOESCH_TABELLEN)==len(set(offboarding.LOESCH_TABELLEN)))
# Offboarding löscht Besucherdaten wirklich
kid,c=neuer_kunde("Loesch")
sql(f"insert into website_termine (kunden_id,start,ende,name,email,token) values ('{kid}',now()+interval '1 day',now()+interval '1 day 1 hour','Besucher Geheim','besucher{sfx}@x.de','tok{sfx}')")
sql(f"update kunden set status='gekuendigt' where id='{kid}'")
kn=sql(f"select kundennummer from kunden where id='{kid}'")
r=a.post(f"/api/admin/kunden/{kid}/loeschen",json={"bestaetigung":kn,"export_uebergeben":True})
chk("Offboarding läuft",r.status_code==200,r.text)
chk("Besucher-Termine sind gelöscht",sql(f"select count(*) from website_termine where kunden_id='{kid}'")=="0")
chk("Export enthält die Besucher-Termine",set(["website_termine","website_warteliste"])<=set(offboarding.EXPORT_TABELLEN))

# ---------------------------------------------------------------- Rate-Limit in der Datenbank
k=f"t105:{sfx}"
security.rate_limit(k,2,60); security.rate_limit(k,2,60)
try: security.rate_limit(k,2,60); ok=False
except HTTPException as e: ok=e.status_code==429
chk("Rate-Limit: dritter Versuch gesperrt (429)",ok)
chk("Rate-Limit: Zähler steht in der Datenbank",sql(f"select anzahl from rate_zaehler where schluessel='{k}'")=="3")
sql(f"update rate_zaehler set fenster_start=now()-interval '3 days' where schluessel='{k}'")
with tx("system") as cur: n=security.rate_aufraeumen(cur)
chk("Rate-Limit: alte Zähler werden aufgeräumt",n>=1 and sql(f"select count(*) from rate_zaehler where schluessel='{k}'")=="0")
security.rate_limit(k,2,60)
sql(f"update rate_zaehler set fenster_start=now()-interval '2 minutes' where schluessel='{k}'")
security.rate_limit(k,2,60)
chk("Rate-Limit: neues Fenster beginnt wieder bei 1",sql(f"select anzahl from rate_zaehler where schluessel='{k}'")=="1")

# ---------------------------------------------------------------- Push: nur bekannte Dienste, https, öffentliche Adressen
alt=config.PUSH_HTTP_ERLAUBT; config.PUSH_HTTP_ERLAUBT=False
z=lambda u: push.ziel_erlaubt(u,aufloesen=False)
chk("Push: bekannter Dienst erlaubt",z("https://fcm.googleapis.com/fcm/send/abc") and z("https://updates.push.services.mozilla.com/wpush/v2/x"))
chk("Push: fremde Adresse, http, Port, Zugangsdaten, Täuschung abgelehnt",not any(z(u) for u in ("https://evil.example/x","http://fcm.googleapis.com/x","https://fcm.googleapis.com:8443/x","https://u@fcm.googleapis.com/x","https://googleapis.com.evil.example/x","https://127.0.0.1/x","https://localhost/x")))
chk("Push: Adresse im internen Netz abgelehnt",push.ziel_erlaubt("https://localhost/x")==False)
config.PUSH_HTTP_ERLAUBT=alt

# ---------------------------------------------------------------- Kunden-2FA (Schalter, Standard aus)
kid2,c2=neuer_kunde("Zwei")
chk("Kunden-2FA: Standard aus",a.get("/api/admin/sicherheit").json().get("kunden_pflicht") is False and c2.get("/api/me").json()["zwei_faktor_pflicht"] is False)
chk("Kunden-2FA: Kunde kann arbeiten",c2.get("/api/kunde/start").status_code==200)
r=a.put("/api/admin/sicherheit",json={"kunden_2fa":True}); chk("Einschalten ok",r.status_code==200,r.text)
chk("Kunden-2FA an: Inhaber muss einrichten",c2.get("/api/me").json()["zwei_faktor_pflicht"] is True and c2.get("/api/kunde/start").status_code==403)
chk("Kunden-2FA an: Vertriebs-Pflicht bleibt unberührt",a.get("/api/admin/sicherheit").json()["kunden_pflicht"] is True)
chk("Kunden-2FA an: Einrichten bleibt erreichbar",c2.post("/api/2fa/start").status_code==200)
chk("Kunden-2FA wird protokolliert",int(sql("select count(*) from audit_log where aktion='sicherheit_kunden_2fa'"))>=1)
a.put("/api/admin/sicherheit",json={"kunden_2fa":False})
chk("Kunden-2FA aus: wieder frei",c2.get("/api/kunde/start").status_code==200)

# ---------------------------------------------------------------- 2FA-Reset nur Haupt-Admin
m=a.post("/api/admin/mitarbeiter",json={"email":f"teil{sfx}@t.de","name":"Teil Admin","rechte":["leads"]}).json()
tk=m["link"].split("token=")[1]; httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"TeilPasswort123456"})
t=httpx.Client(base_url=B,headers=H); r=t.post("/api/login",json={"email":f"teil{sfx}@t.de","password":"TeilPasswort123456"}); chk("Teil-Admin angemeldet",r.status_code==200,r.text)
uid=sql(f"select id from benutzer where email='teil{sfx}@t.de'")
chk("Teil-Admin darf keine 2FA zurücksetzen (403)",t.post(f"/api/admin/benutzer/{uid}/2fa-zuruecksetzen").status_code==403)
chk("Haupt-Admin darf (200)",a.post(f"/api/admin/benutzer/{uid}/2fa-zuruecksetzen").status_code==200)

# ---------------------------------------------------------------- Dubletten-Meldung verrät dem Vertriebler nichts
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de"}).json(); pid=p["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"vera{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"VeraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123456"}).status_code==200
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
fremd=a.post("/api/admin/leads",json={"firma":f"Fremdfirma {sfx}","telefon":f"0511 7{sfx[-6:]}","ort":"Celle","plz":"29221"}).json()
r=v.post("/api/vertrieb/leads",json={"firma":f"Andere {sfx}","telefon":f"0511 7{sfx[-6:]}","ort":"Celle","plz":"29221"})
chk("Dublette: Vertriebler bekommt Ablehnung ohne Namen",r.status_code in (400,409) and "Fremdfirma" not in r.text and "Kunde" not in r.text and "Team" in r.text,r.text)

# ---------------------------------------------------------------- Abgelaufene Angebote und Zustellfehler
k3,c3=neuer_kunde("Abl")
b=a.post(f"/api/admin/kunden/{k3}/belege",json={"art":"angebot","betreff":"Test","positionen":[{"text":"Leistung","menge":1,"einheit":"Stk","preis_cent":10000}]}); assert b.status_code==200,b.text
bid=b.json()["id"]
r=a.post(f"/api/admin/belege/{bid}/ausstellen"); assert r.status_code==200,r.text
sql(f"update belege set status='versendet', versendet_am=now()-interval '10 days', faellig_am=current_date-2 where id='{bid}'")
chk("Abgelaufen: Erinnerung gesperrt",a.get(f"/api/admin/angebote-erinnerung/{bid}").json()["moeglich"] is False)
n=angebotserinnerung.abgelaufen_melden()
chk("Job meldet das abgelaufene Angebot einmal",n>=1 and sql(f"select ablauf_gemeldet_am is not null from belege where id='{bid}'")=="t",n)
chk("Job meldet nicht zweimal",angebotserinnerung.abgelaufen_melden()==0)
chk("Glocke: Admin bekommt Meldung",int(sql("select count(*) from benachrichtigungen where titel='Angebot abgelaufen'"))>=1)
chk("Verlängern: zu kurz abgelehnt",a.post(f"/api/admin/angebote-erinnerung/{bid}/verlaengern",json={"tage":3}).status_code==422)
r=a.post(f"/api/admin/angebote-erinnerung/{bid}/verlaengern",json={"tage":14}); chk("Verlängern ok",r.status_code==200,r.text)
chk("Gültigkeit +14 Tage, Meldung zurückgesetzt",sql(f"select faellig_am=current_date+14 and ablauf_gemeldet_am is null and erinnerungen=0 from belege where id='{bid}'")=="t")
chk("Verlängert: Erinnerung wieder möglich",a.get(f"/api/admin/angebote-erinnerung/{bid}").json()["moeglich"] is True)
chk("Verlängern protokolliert",int(sql("select count(*) from audit_log where aktion='angebot_verlaengert'"))==1)
sql(f"update belege set status='angenommen', angenommen_am=now() where id='{bid}'")
chk("Angenommenes Angebot: Verlängern abgelehnt",a.post(f"/api/admin/angebote-erinnerung/{bid}/verlaengern",json={"tage":14}).status_code==400)
# Zustellfehler festhalten
angebotserinnerung.mail_ergebnis(bid,False,"Adresse existiert nicht")
chk("Zustellfehler steht am Angebot",sql(f"select mail_fehler from belege where id='{bid}'")=="Adresse existiert nicht")
chk("Zustellfehler erscheint in Angebote im Blick",any(x.get("mail_fehler")=="Adresse existiert nicht" for x in a.get("/api/admin/heute").json()["angebote"]))
angebotserinnerung.mail_ergebnis(bid,True)
chk("Erfolg löscht den Fehler",sql(f"select mail_fehler is null from belege where id='{bid}'")=="t")
