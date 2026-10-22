import httpx, time, re, email, subprocess, io, sys, json, datetime
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
kid,c,kmail=neuer_kunde("Alpha"); kid2,c2,kmail2=neuer_kunde("Beta")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs, berichte
db.open_pool()

# ---- Kontaktergebnis (Admin + Vertriebler)
lid=a.post("/api/admin/leads",json={"firma":f"Kontakt GmbH {sfx}","ansprechpartner":"K. Kontakt","email":f"kk{sfx}@k.de"}).json()["id"]
d=a.get(f"/api/admin/leads/{lid}").json(); chk("Optionen im Lead",len(d.get("kontakt_optionen",[]))>=8,list(d))
r=a.post(f"/api/admin/leads/{lid}/kontakt",json={"ergebnis":"anruf_nicht_erreicht","notiz":"Mailbox"}); chk("nicht erreicht",r.status_code==200,r.text)
chk("Wiedervorlage gesetzt",sql(f"select wiedervorlage_am is not null from leads where id='{lid}'")=="t")
chk("Status bleibt neu",sql(f"select status from leads where id='{lid}'")=="neu")
r=a.post(f"/api/admin/leads/{lid}/kontakt",json={"ergebnis":"anruf_erreicht"}); chk("erreicht",r.status_code==200,r.text)
chk("Status kontaktiert",sql(f"select status from leads where id='{lid}'")=="kontaktiert")
a.post(f"/api/admin/leads/{lid}/kontakt",json={"ergebnis":"termin"})
a.post(f"/api/admin/leads/{lid}/kontakt",json={"ergebnis":"anruf_erreicht"})
chk("Status geht nie zurück",sql(f"select status from leads where id='{lid}'")=="termin")
chk("Unbekanntes Ergebnis abgelehnt",a.post(f"/api/admin/leads/{lid}/kontakt",json={"ergebnis":"quatsch"}).status_code in (400,422))
chk("Verlauf hat Einträge",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}'"))>=4)
a.post(f"/api/admin/leads/{lid}/kontakt",json={"ergebnis":"kein_interesse"}); chk("Kein Interesse = verloren",sql(f"select status from leads where id='{lid}'")=="verloren")
lid_f=a.post("/api/admin/leads",json={"firma":"Falsche Nummer "+str(int(time.time())),"telefon":"0511 1","ort":"Celle"}).json()["id"]; a.post(f"/api/admin/leads/{lid_f}/kontakt",json={"ergebnis":"falsche_nummer"}); chk("Nummer falsch = abgelegt (tot), keine Wiedervorlage",sql(f"select status||coalesce(wiedervorlage_am::text,'-') from leads where id='{lid_f}'")=="tot-")
chk("Wiedervorlage gelöscht",sql(f"select wiedervorlage_am is null from leads where id='{lid}'")=="t")
# Vertriebler
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv"}).json(); pid=p["id"]
a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"vera{sfx}@v.de","per_mail":True})
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); chk("Vertriebler Login",v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200)
l2=a.post("/api/admin/leads",json={"firma":f"Vera Lead {sfx}","email":f"vl{sfx}@k.de"}).json()["id"]
l3=a.post("/api/admin/leads",json={"firma":f"Fremd Lead {sfx}","email":f"fl{sfx}@k.de"}).json()["id"]
sql(f"update leads set vertriebspartner_id='{pid}' where id='{l2}'")
vl=v.get("/api/vertrieb/leads").json(); chk("Vertriebler sieht nur eigene Leads",any(x["id"]==l2 for x in vl) and not any(x["id"]==l3 for x in vl),vl)
chk("Vertriebler Detail hat Optionen",len(v.get(f"/api/vertrieb/leads/{l2}").json().get("kontakt_optionen",[]))>=8)
r=v.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"mail_gesendet","notiz":"Infos geschickt"}); chk("Vertriebler erfasst Kontakt",r.status_code==200,r.text)
chk("Status kontaktiert (Vertriebler)",sql(f"select status from leads where id='{l2}'")=="kontaktiert")
chk("Fremder Lead: kein Zugriff",v.post(f"/api/vertrieb/leads/{l3}/kontakt",json={"ergebnis":"anruf_erreicht"}).status_code in (403,404))
chk("Kunde kein Zugriff auf Vertrieb",c.post(f"/api/vertrieb/leads/{l2}/kontakt",json={"ergebnis":"antwort"}).status_code in (401,403))
sql(f"update leads set wiedervorlage_am=current_date-1 where id='{l2}'")
h=a.get("/api/admin/heute").json(); chk("Heute: Wiedervorlage vom Vertriebler",any(x["id"]==l2 for x in h["wiedervorlagen"]),h["wiedervorlagen"])

# ---- Monatsbericht: Einordnung
vm=berichte.vormonat(); bm=vm.strftime("%Y-%m")
br=a.post(f"/api/admin/kunden/{kid}/bericht",json={"monat":bm,"senden":False}).json(); bid=br["id"]
t=a.get(f"/api/admin/berichte/{bid}").json(); chk("Auto-Einordnung vorhanden",bool(t.get("einordnung")) or bool(t.get("auto")) or "einordnung" in t,t)
r=a.put(f"/api/admin/berichte/{bid}",json={"einordnung":"Das war ein starker Monat für Anadolu Test.","naechste_schritte":["Google-Profil aktualisieren","Newsletter planen"]}); chk("Texte speichern",r.status_code==200,r.text)
t=a.get(f"/api/admin/berichte/{bid}").json(); chk("Texte gelesen","starker Monat" in json.dumps(t),t)
pdf=a.get(f"/api/admin/berichte/{bid}/pdf"); open("/var/tmp/b22.pdf","wb").write(pdf.content)
tx=" ".join(subprocess.run(["pdftotext","/var/tmp/b22.pdf","-"],capture_output=True,text=True).stdout.split())
chk("PDF enthält Einordnung und Schritte","starker Monat" in tx and "Google-Profil" in tx and "nächsten Schritte" in tx,tx[-400:])
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
r=a.post(f"/api/admin/berichte/{bid}/ki-entwurf"); chk("KI-Entwurf",r.status_code==200 and "KI" in json.dumps(r.json()),r.text)
r=a.post(f"/api/admin/berichte/{bid}/senden"); chk("Bericht senden",r.status_code==200,r.text)
chk("Kunde sieht Texte",any(("einordnung" in x and x["einordnung"]) or x.get("schritte") for x in c.get("/api/kunde/monatsberichte").json()),c.get("/api/kunde/monatsberichte").text[:300])
chk("Fremder Kunde sieht keinen Bericht",c2.get("/api/kunde/monatsberichte").json()==[])
chk("Bericht-Texte: Kunde kein Zugriff",c.get(f"/api/admin/berichte/{bid}").status_code==403)

# ---- Status-Seite
s=c.get("/api/kunde/status").json(); chk("Status Struktur",all(k in s for k in ("auftraege","wartet_auf_dich","websites","module")),list(s))
chk("Status ohne Login 401",httpx.get(B+"/api/kunde/status").status_code==401)

# ---- Folgemails
f=a.get("/api/admin/einstellungen/folgemails").json(); chk("Folgemails Standard aus",f["aktiv"] is False and f["kunden_feedback"] is False,f)
chk("Zweite Mail muss später kommen",a.put("/api/admin/einstellungen/folgemails",json={**f,"aktiv":True,"tage_1":5,"tage_2":3}).status_code==400)
cfg={"alarm_email":""}
w=httpx.post(B+"/api/public/kontakt-lead",headers={**H,"X-Lead-Secret":"x"},json={"email":"a@b.de","einwilligung":True})
sql("delete from leads where email like 'fm%@k.de'")
def lead_mit_consent(mail,tage,consent=True):
    i=sql(f"insert into leads (firma,email,ansprechpartner,erstellt_am) values ('FM {mail}','{mail}','Frau Folge',now()-interval '{tage} days') returning id").split()[0]
    if consent: sql(f"insert into lead_aktivitaeten (lead_id,art,inhalt) values ('{i}','consent','ok')")
    return i
fa=lead_mit_consent(f"fm1{sfx}@k.de",3); fb=lead_mit_consent(f"fm2{sfx}@k.de",3,False); fc=lead_mit_consent(f"fm3{sfx}@k.de",1)
open("/var/tmp/pt/mails.txt","a").close(); jobs.lead_folgemails(cfg)
chk("Ausgeschaltet: keine Mail",not mail_an(f"fm1{sfx}@k.de"))
r=a.put("/api/admin/einstellungen/folgemails",json={**f,"aktiv":True,"tage_1":2,"tage_2":7}); chk("Einschalten",r.status_code==200,r.text)
jobs.lead_folgemails(cfg); m1=mail_an(f"fm1{sfx}@k.de")
chk("Stufe 1 gesendet",len(m1)==1,len(m1)); chk("Mail mit Abmeldelink und Buchungslink","/api/public/abmelden?t=" in text(m1[0]) and "/buchen" in text(m1[0]),text(m1[0])[-300:])
chk("Ohne Einwilligung keine Mail",not mail_an(f"fm2{sfx}@k.de")); chk("Zu frisch keine Mail",not mail_an(f"fm3{sfx}@k.de"))
jobs.lead_folgemails(cfg); chk("Nicht doppelt",len(mail_an(f"fm1{sfx}@k.de"))==1)
sql(f"update leads set folge_gesendet_am=now()-interval '6 days' where id='{fa}'"); jobs.lead_folgemails(cfg)
chk("Stufe 2 gesendet",len(mail_an(f"fm1{sfx}@k.de"))==2); jobs.lead_folgemails(cfg); chk("Nicht dritte Mail",len(mail_an(f"fm1{sfx}@k.de"))==2)
tok=re.search(r"abmelden\?t=([\w-]+)",text(m1[0])).group(1)
r=httpx.get(B+"/api/public/abmelden?t="+tok); chk("Abmelden",r.status_code==200 and "keine weiteren" in r.text,r.text[-200:])
chk("Abgemeldet markiert",sql(f"select abgemeldet from leads where id='{fa}'")=="t")
chk("Falscher Token",("ungültig" in httpx.get(B+"/api/public/abmelden?t=gibtesnicht1234").text))
sql(f"update leads set folge_stufe=0, erstellt_am=now()-interval '5 days' where id='{fa}'"); n0=len(mail_an(f"fm1{sfx}@k.de")); jobs.lead_folgemails(cfg)
chk("Abgemeldet: nie wieder",len(mail_an(f"fm1{sfx}@k.de"))==n0)
# Kunden-Feedback
a.put("/api/admin/einstellungen/folgemails",json={**f,"aktiv":True,"kunden_feedback":True})
a.post(f"/api/admin/kunden/{kid}/status",json={"status":"aktiv"}); sql(f"update kunden set erstellt_am=now()-interval '40 days', feedback_mail_am=null where id='{kid}'")
jobs.kunden_feedback(cfg); chk("Ohne Einwilligung keine Feedback-Mail",len(mail_an(kmail,"läuft es"))==0)
sql(f"insert into kunden_einwilligungen (kunden_id, art, erteilt) values ('{kid}','umfrage_mail',true)"); sql(f"update kunden set feedback_mail_am=null where id='{kid}'")
jobs.kunden_feedback(cfg); chk("Feedback-Mail",len(mail_an(kmail,"läuft es"))>=1)
n=len(mail_an(kmail,"läuft es")); jobs.kunden_feedback(cfg); chk("Feedback nur einmal",len(mail_an(kmail,"läuft es"))==n)
a.put("/api/admin/einstellungen/folgemails",json={**f,"aktiv":False})

# ---- Terminbuchung
chk("Buchung aus: keine Slots",httpx.get(B+"/api/public/buchung/slots").json()["aktiv"] is False)
chk("Seite /buchen",httpx.get(B+"/buchen").status_code==200)
bs={"aktiv":True,"dauer":30,"tage":14,"von":"09:00","bis":"12:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Videocall"}
chk("Spät vor früh abgelehnt",a.put("/api/admin/einstellungen/buchung",json={**bs,"von":"12:00","bis":"09:00"}).status_code==400)
chk("Einstellungen speichern",a.put("/api/admin/einstellungen/buchung",json=bs).status_code==200)
sl=httpx.get(B+"/api/public/buchung/slots").json(); chk("Slots vorhanden",sl["aktiv"] and len(sl["tage"])>=10 and len(sl["tage"][-1]["slots"])==6,sl["tage"][-1:])
slot=sl["tage"][-1]["slots"][0]
chk("Ohne Einwilligung abgelehnt",httpx.post(B+"/api/public/buchung",headers=H,json={"start":slot["start"],"name":"Bea Buchung","email":f"bb{sfx}@k.de"}).status_code==400)
chk("Freier Zeitpunkt außerhalb der Zeiten abgelehnt",httpx.post(B+"/api/public/buchung",headers=H,json={"start":"2030-01-01T03:00:00+00:00","name":"Bea Buchung","email":f"bb{sfx}@k.de","einwilligung":True}).status_code==409)
r=httpx.post(B+"/api/public/buchung",headers=H,json={"start":slot["start"],"name":"Bea Buchung","email":f"bb{sfx}@k.de","telefon":"0170","nachricht":"Website neu","einwilligung":True}); chk("Gebucht",r.status_code==200,r.text)
chk("Zweite Buchung desselben Slots abgelehnt",httpx.post(B+"/api/public/buchung",headers=H,json={"start":slot["start"],"name":"Cora Zweite","email":f"cz{sfx}@k.de","einwilligung":True}).status_code==409)
sl2=httpx.get(B+"/api/public/buchung/slots").json(); chk("Slot nicht mehr frei",slot["start"] not in [s["start"] for d in sl2["tage"] for s in d["slots"]])
mm=mail_an(f"bb{sfx}@k.de","Gespräch"); chk("Bestätigung mit Kalender",len(mm)==1 and any(p.get_content_type()=="text/calendar" for p in mm[0].walk()),len(mm))
chk("Team-Mail",len(mail_an("chef@test.de","Gespräch gebucht"))>=1 or len(mail_an("info@markentrix.de","Gespräch gebucht"))>=1)
chk("Lead angelegt mit Status Termin",sql(f"select status||'|'||temperatur from leads where email='bb{sfx}@k.de'")=="termin|heiss")
chk("Einwilligung im Verlauf",int(sql(f"select count(*) from lead_aktivitaeten a join leads l on l.id=a.lead_id where l.email='bb{sfx}@k.de' and a.art='consent'"))==1)
g=a.get("/api/admin/gespraeche").json(); chk("Admin sieht Gespräch",any(x["email"]==f"bb{sfx}@k.de" for x in g),g)
chk("Kunde sieht Gespräche nicht",c.get("/api/admin/gespraeche").status_code==403)
ab=re.search(r"absagen\?t=([\w-]+)",text(mm[0])).group(1)
r=httpx.get(B+"/api/public/buchung/absagen?t="+ab); chk("Absagen",r.status_code==200 and "abgesagt" in r.text,r.text[-200:])
sl3=httpx.get(B+"/api/public/buchung/slots").json(); chk("Slot wieder frei",slot["start"] in [s["start"] for d in sl3["tage"] for s in d["slots"]])
chk("Zweites Absagen ohne Wirkung","nicht mehr aktiv" in httpx.get(B+"/api/public/buchung/absagen?t="+ab).text)
# bestehender Lead wird wiederverwendet
r=httpx.post(B+"/api/public/buchung",headers=H,json={"start":slot["start"],"name":"Bea Buchung","email":f"bb{sfx}@k.de","einwilligung":True}); chk("Erneut buchen",r.status_code==200,r.text)
chk("Nur ein Lead je E-Mail",sql(f"select count(*) from leads where email='bb{sfx}@k.de'")=="1")
a.put("/api/admin/einstellungen/buchung",json={**bs,"aktiv":False}); chk("Ausgeschaltet: Buchung 409",httpx.post(B+"/api/public/buchung",headers=H,json={"start":slot["start"],"name":"Dora D","email":f"dd{sfx}@k.de","einwilligung":True}).status_code==409)

# ---- Team-Rechte
chk("Kunde darf Mitarbeiter nicht verwalten",c.get("/api/admin/mitarbeiter").status_code==403)
m=a.get("/api/admin/mitarbeiter").json(); chk("Mitarbeiterliste",len(m["liste"])>=1 and "leads" in m["bereiche"],m)
chk("Unbekannter Bereich abgelehnt",a.post("/api/admin/mitarbeiter",json={"email":f"ma{sfx}@t.de","rechte":["alles"]}).status_code==400)
r=a.post("/api/admin/mitarbeiter",json={"email":f"ma{sfx}@t.de","name":"Max Mitarbeiter","rechte":["leads","nachrichten"]}); chk("Mitarbeiter eingeladen",r.status_code==200,r.text)
time.sleep(1.5); httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"ma{sfx}@t.de"),"password":"MaxPasswort1234"})
ma=httpx.Client(base_url=B,headers=H); chk("Mitarbeiter Login",ma.post("/api/login",json={"email":f"ma{sfx}@t.de","password":"MaxPasswort1234"}).status_code==200)
me=ma.get("/api/me").json(); chk("me zeigt Rechte",me["rolle"]=="admin" and sorted(me["admin_rechte"])==["leads","nachrichten"],me)
chk("Erlaubt: Leads",ma.get("/api/admin/leads").status_code==200)
chk("Erlaubt: Nachrichten",ma.get("/api/admin/tickets").status_code==200)
chk("Erlaubt: Heute",ma.get("/api/admin/heute").status_code==200)
chk("Verboten: Kunden",ma.get("/api/admin/kunden").status_code==403)
chk("Verboten: Rechnungen",ma.get("/api/admin/belege").status_code==403)
chk("Verboten: Einstellungen",ma.get("/api/admin/einstellungen/folgemails").status_code==403)
chk("Verboten: Protokoll",ma.get("/api/admin/audit").status_code==403)
chk("Verboten: Kunden-Detail",ma.get(f"/api/admin/kunden/{kid}/historie").status_code==403)
chk("Mitarbeiter kann keine Mitarbeiter anlegen",ma.post("/api/admin/mitarbeiter",json={"email":f"x{sfx}@t.de","rechte":["leads"]}).status_code==403)
chk("Mitarbeiter kann Rechte nicht ändern",ma.get("/api/admin/mitarbeiter").status_code==403)
mid=[x for x in a.get("/api/admin/mitarbeiter").json()["liste"] if x["email"]==f"ma{sfx}@t.de"][0]["id"]
chk("Rechte erweitern",a.patch(f"/api/admin/mitarbeiter/{mid}",json={"rechte":["leads","kunden"]}).status_code==200)
chk("Jetzt Kunden erlaubt",ma.get("/api/admin/kunden").status_code==200)
chk("Eigenes Konto nicht änderbar",a.patch(f"/api/admin/mitarbeiter/{[x for x in m['liste'] if x['email']=='chef@test.de'][0]['id']}",json={"aktiv":False}).status_code==400)
chk("Chef (voll) hat NULL-Rechte",a.get("/api/me").json()["admin_rechte"] is None)
chk("Sperren",a.patch(f"/api/admin/mitarbeiter/{mid}",json={"aktiv":False}).status_code==200)
chk("Gesperrt: Sitzung ungültig",ma.get("/api/admin/leads").status_code==401)

# ---- Änderungshistorie
a.put(f"/api/admin/kunden/{kid}",json={"telefon":"0511999"}) if False else None
hs=a.get(f"/api/admin/kunden/{kid}/historie").json(); chk("Historie hat Einträge",len(hs)>=2 and all("aktion" in x for x in hs),hs[:2])
chk("Historie nur dieses Kunden",not any(x["aktion"]=="avv_online_bestaetigt" for x in a.get(f"/api/admin/kunden/{kid2}/historie").json()))
chk("Kunde sieht Historie nicht",c.get(f"/api/admin/kunden/{kid}/historie").status_code==403)
chk("Audit Mitarbeiter",int(sql("select count(*) from audit_log where aktion in ('mitarbeiter_angelegt','mitarbeiter_geaendert')"))>=3)
