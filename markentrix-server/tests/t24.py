import httpx, time, re, email, subprocess, io, sys, json
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
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
kid,c,kmail=neuer_kunde("Alpha")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs
db.open_pool()
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":"0511 5555","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); chk("Vertriebler Login",v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200)
l_wv=lead("WV Lead"); l_hot=lead("Hot Lead"); l_neu=lead("Neu Lead"); l_ok=lead("Schon Kontakt"); l_fremd=lead("Fremd Lead")
for i in (l_wv,l_hot,l_neu,l_ok): sql(f"update leads set vertriebspartner_id='{p}' where id='{i}'")
sql(f"update leads set wiedervorlage_am=current_date-1, status='kontaktiert', letzter_kontakt_am=now() where id='{l_wv}'")
sql(f"update leads set temperatur='heiss' where id='{l_hot}'"); sql(f"update leads set temperatur='warm' where id='{l_neu}'")
sql(f"update leads set status='kontaktiert', letzter_kontakt_am=now() where id='{l_ok}'")

# ---- Arbeitsliste
h=v.get("/api/vertrieb/heute").json()
chk("Wiedervorlage fällig",[x["id"] for x in h["wiedervorlagen"]]==[l_wv],h["wiedervorlagen"])
chk("Heiß ohne Kontakt",[x["id"] for x in h["heiss"]]==[l_hot],h["heiss"])
chk("Neu zugewiesen",[x["id"] for x in h["neu"]]==[l_neu],h["neu"])
chk("Fremde und bearbeitete Leads fehlen",not any(x["id"] in (l_fremd,l_ok) for k in ("wiedervorlagen","heiss","neu") for x in h[k]))
chk("Gesamt",h["gesamt"]==3 and h["anrufe_heute"]==0,h)
v.post(f"/api/vertrieb/leads/{l_hot}/kontakt",json={"ergebnis":"anruf_nicht_erreicht"})
h=v.get("/api/vertrieb/heute").json(); chk("Nach Anruf: nicht mehr in Heiß-Liste",not h["heiss"] and h["anrufe_heute"]==1,h)
chk("Kunde kein Zugriff auf Arbeitsliste",c.get("/api/vertrieb/heute").status_code==403)
chk("Ohne Login 401",httpx.get(B+"/api/vertrieb/heute").status_code==401)

# ---- KI-Leitfaden
r=v.post(f"/api/vertrieb/leads/{l_hot}/skript"); chk("Ohne KI-Schlüssel: verständlicher Fehler",r.status_code==400 and "Schlüssel" in r.text,r.text)
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
r=v.post(f"/api/vertrieb/leads/{l_hot}/skript"); j=r.json()
chk("Leitfaden erzeugt",r.status_code==200 and j["einstieg"] and len(j["fragen"])==3 and len(j["einwaende"])==3 and j["abschluss"],r.text)
d=v.get(f"/api/vertrieb/leads/{l_hot}").json()["lead"]; chk("Leitfaden gespeichert und im Lead",d["skript"]["einstieg"]==j["einstieg"] and d["skript_am"],d.get("skript"))
chk("Fremder Lead: 404",v.post(f"/api/vertrieb/leads/{l_fremd}/skript").status_code==404)
chk("Admin kann Leitfaden erzeugen",a.post(f"/api/admin/leads/{l_fremd}/skript").status_code==200)
chk("Admin sieht Leitfaden im Lead",a.get(f"/api/admin/leads/{l_fremd}").json()["lead"]["skript"]["abschluss"])
chk("Kunde kein Zugriff",c.post(f"/api/admin/leads/{l_fremd}/skript").status_code==403 and c.post(f"/api/vertrieb/leads/{l_hot}/skript").status_code==403)

# ---- Auswertung
sql(f"update leads set status='termin', letzter_kontakt_am=now(), liste='Testliste', gruppe='Gastronomie' where id in ('{l_wv}')")
sql(f"update leads set status='gewonnen', letzter_kontakt_am=now(), liste='Testliste', gruppe='Gastronomie' where id='{l_ok}'")
sql(f"update leads set status='verloren', letzter_kontakt_am=now(), liste='Testliste', gruppe='Handwerk' where id='{l_neu}'")
au=a.get("/api/admin/vertrieb/auswertung").json()
g=au["gesamt"]; chk("Gesamt-Trichter",g["leads"]>=5 and g["termine"]>=2 and g["kunden"]>=1,g)
tl=[x for x in au["je_liste"] if x["name"]=="Testliste"][0]; chk("Liste Testliste",tl["leads"]==3 and tl["bearbeitet"]==3 and tl["termine"]==2 and tl["kunden"]==1 and tl["verloren"]==1,tl)
vv=[x for x in au["je_vertriebler"] if x["name"]=="Vera Vertrieb"][0]; chk("Je Vertriebler",vv["leads"]==4 and vv["anrufe_heute"]>=1,vv)
chk("Je Branche",[x for x in au["je_gruppe"] if x["name"]=="Gastronomie"][0]["leads"]==2)
chk("Nicht zugeordnet erscheint",any(x["name"]=="Nicht zugeordnet" for x in au["je_vertriebler"]))
chk("Kunde kein Zugriff auf Auswertung",c.get("/api/admin/vertrieb/auswertung").status_code==403 and v.get("/api/admin/vertrieb/auswertung").status_code==403)

# ---- Systemstatus
s=a.get("/api/admin/systemstatus").json(); chk("Ohne Überwachungsdaten",s["vorhanden"] is False and s["ki_eingerichtet"] is True and s["mail_eingerichtet"] is True,s)
def schreibe(alter_min,probleme=()):
    json.dump({"zeit":time.time()-alter_min*60,"backup_stunden":5,"offsite_stunden":9999,"offsite_aktiv":False,"platte_prozent":40,"zertifikat_tage":60,"probleme":list(probleme)},open("/var/tmp/pt/bk/system.json","w"))
schreibe(2); s=a.get("/api/admin/systemstatus").json(); chk("Status gelesen",s["vorhanden"] and s["probleme"]==[] and s["status"]["platte_prozent"]==40,s)
schreibe(2,["Festplatte zu 90% voll"]); s=a.get("/api/admin/systemstatus").json(); chk("Probleme durchgereicht","Festplatte zu 90% voll" in s["probleme"],s["probleme"])
schreibe(45); s=a.get("/api/admin/systemstatus").json(); chk("Verstummte Überwachung als Problem",any("nicht gemeldet" in x for x in s["probleme"]),s["probleme"])
chk("Kunde kein Zugriff auf Systemstatus",c.get("/api/admin/systemstatus").status_code==403)
schreibe(120); n0=len(mails()); jobs.ueberwachung_stumm({"alarm_email":""}); chk("Mail bei verstummter Überwachung",len(mail_an("chef@test.de","Überwachung"))==1)
jobs.ueberwachung_stumm({"alarm_email":""}); chk("Nur einmal pro Tag",len(mail_an("chef@test.de","Überwachung"))==1)

# ---- Anmelde-Link
def link_mails(adr): return [m for m in mails() if adr in str(m["To"]) and "Anmelde-Link" in str(email.header.make_header(email.header.decode_header(m["Subject"] or "")))]
r=httpx.post(B+"/api/login-link",headers=H,json={"email":kmail}); chk("Link anfordern",r.status_code==200 and "unterwegs" in r.json()["hinweis"],r.text)
time.sleep(1.5); lm=link_mails(kmail); chk("Mail mit Link",len(lm)==1 and "/anmelden?t=" in text(lm[0]),len(lm))
tok=re.search(r"anmelden\?t=([\w-]+)",text(lm[0])).group(1)
chk("Seite /anmelden",httpx.get(B+"/anmelden").status_code==200)
chk("Falscher Token",httpx.post(B+"/api/login-link/einloesen",headers=H,json={"token":"gibtesnicht12345"}).status_code==400)
cl=httpx.Client(base_url=B,headers=H); r=cl.post("/api/login-link/einloesen",json={"token":tok}); chk("Einlösen",r.status_code==200 and r.json()["ziel"]=="/app",r.text)
chk("Eingeloggt",cl.get("/api/me").json()["email"]==kmail)
chk("Zweites Einlösen abgelehnt",httpx.post(B+"/api/login-link/einloesen",headers=H,json={"token":tok}).status_code==400)
n=len(link_mails("chef@test.de")); httpx.post(B+"/api/login-link",headers=H,json={"email":"chef@test.de"}); time.sleep(1.5); chk("Admin bekommt keinen Link",len(link_mails("chef@test.de"))==n)
sql(f"update benutzer set totp_aktiv=true where lower(email)='{kmail}'"); n=len(link_mails(kmail)); httpx.post(B+"/api/login-link",headers=H,json={"email":kmail}); time.sleep(1.5); chk("Mit 2FA kein Link",len(link_mails(kmail))==n)
sql(f"update benutzer set totp_aktiv=false where lower(email)='{kmail}'")
httpx.post(B+"/api/login-link",headers=H,json={"email":f"vera{sfx}@v.de"}); time.sleep(1.5); lv=link_mails(f"vera{sfx}@v.de"); chk("Vertriebler bekommt Link",len(lv)==1)
tv=re.search(r"anmelden\?t=([\w-]+)",text(lv[0])).group(1); cv=httpx.Client(base_url=B,headers=H); r=cv.post("/api/login-link/einloesen",json={"token":tv}); chk("Vertriebler Einlösen -> /vertrieb",r.status_code==200 and r.json()["ziel"]=="/vertrieb",r.text)
httpx.post(B+"/api/login-link",headers=H,json={"email":kmail}); time.sleep(1.5); tk=re.search(r"anmelden\?t=([\w-]+)",text(link_mails(kmail)[-1])).group(1)
sql("update login_links set ablauf=now()-interval '1 minute'"); chk("Abgelaufener Link",httpx.post(B+"/api/login-link/einloesen",headers=H,json={"token":tk}).status_code==400)
chk("Audit Login per Link",int(sql("select count(*) from audit_log where aktion='login_per_link'"))>=2)
chk("Login-Seite hat Link-Option","Anmelde-Link" in httpx.get(B+"/").text)
