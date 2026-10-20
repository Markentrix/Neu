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
sfx=str(int(time.time()))
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
kid,c,kmail=neuer_kunde("Alpha"); kid2,c2,kmail2=neuer_kunde("Beta")

# ---- AVV per Klick
r=a.post(f"/api/admin/kunden/{kid}/avv",json={"hauptvertrag_datum":"2026-10-01"}); chk("AVV erstellt",r.status_code==200,r.text); aid=r.json()["id"]
chk("Kunde sieht noch nichts zur Bestätigung",c.get("/api/kunde/avv-offen").json()==[])
chk("Kunde kann Entwurf nicht lesen",c.get(f"/api/kunde/avv-offen/{aid}/vorlage.pdf").status_code==404)
r=a.post(f"/api/admin/avv/{aid}/portal-freigeben"); chk("Admin gibt frei",r.status_code==200 and r.json()["gemailt"],r.text)
chk("Mail an Kunde",len(mail_an(kmail,"bestätigen"))>=1)
chk("Badge avv",c.get("/api/kunde/start").json()["badges"]["avv"]==1)
o=c.get("/api/kunde/avv-offen").json(); chk("Kunde sieht offenen AVV",len(o)==1 and o[0]["id"]==aid,o)
chk("Anderer Kunde sieht ihn nicht",c2.get("/api/kunde/avv-offen").json()==[] and c2.get(f"/api/kunde/avv-offen/{aid}/vorlage.pdf").status_code==404)
r=c.get(f"/api/kunde/avv-offen/{aid}/vorlage.pdf"); chk("Kunde lädt Vertrag",r.status_code==200 and r.content[:4]==b"%PDF")
chk("Fremder Kunde kann nicht bestätigen",c2.post(f"/api/kunde/avv-offen/{aid}/bestaetigen",json={"name":"Max Muster","akzeptiert":True}).status_code==404)
chk("Ohne Häkchen abgelehnt",c.post(f"/api/kunde/avv-offen/{aid}/bestaetigen",json={"name":"Tina Test","akzeptiert":False}).status_code==400)
chk("Zu kurzer Name abgelehnt",c.post(f"/api/kunde/avv-offen/{aid}/bestaetigen",json={"name":"T","akzeptiert":True}).status_code==422)
r=c.post(f"/api/kunde/avv-offen/{aid}/bestaetigen",json={"name":"Tina Test","akzeptiert":True}); chk("Bestätigt",r.status_code==200,r.text)
chk("Team-Mail",len(mail_an("info@markentrix.de","AVV bestätigt"))>=1 or len(mail_an("chef@test.de","AVV bestätigt"))>=1)
l=c.get("/api/kunde/avv").json(); chk("Kunde sieht bestätigten AVV",len(l)==1 and l[0]["datei_name"]=="AVV-online-bestaetigt.pdf",l)
pdf=c.get(f"/api/kunde/avv/{aid}/datei"); chk("PDF enthält Bestätigungsvermerk",pdf.status_code==200 and pdf.content[:4]==b"%PDF")
open("/var/tmp/avv-online.pdf","wb").write(pdf.content)
t=" ".join(subprocess.run(["pdftotext","/var/tmp/avv-online.pdf","-"],capture_output=True,text=True).stdout.split())
chk("Vermerk mit Name und Prüfsumme","Tina Test" in t and "SHA-256" in t and "elektronisch bestätigt" in t,t[-400:])
chk("Nachweis in DB",sql(f"select online_bestaetigt_name||'|'||length(online_bestaetigt_hash) from avv where id='{aid}'")=="Tina Test|64")
chk("AVV zählt als vorhanden",a.get(f"/api/admin/kunden/{kid}/avv").json()["vorhanden"] is True)
chk("Doppelt bestätigen nicht möglich",c.post(f"/api/kunde/avv-offen/{aid}/bestaetigen",json={"name":"Tina Test","akzeptiert":True}).status_code==404)
chk("Audit",sql("select count(*) from audit_log where aktion='avv_online_bestaetigt'")>="1")
# Mitarbeiter ohne Inhaberrolle: kein Zugriff (Rolle wird über require_inhaber geprüft)
chk("Ohne Login 401",httpx.get(B+"/api/kunde/avv-offen").status_code==401)

# ---- Onboarding aus Kundensicht
sl=c.get("/api/kunde/startliste").json(); chk("Startliste aktiv",sl["aktiv"] and sl["gesamt"]>=5,sl)
av=[p for p in sl["punkte"] if "Auftragsverarbeitung" in p["titel"]][0]; chk("AVV-Schritt erledigt, keine Aktion mehr",av["fertig"] and av["seite"] is None,av)
br=[p for p in sl["punkte"] if p["titel"]=="Briefing ausgefüllt"]; chk("Briefing-Schritt offen mit Aktion",len(br)==1 and not br[0]["fertig"] and br[0]["seite"]=="briefing",br)
chk("Interne Punkte nicht sichtbar",not any("Rechnung" in p["titel"] for p in sl["punkte"]))
st=c.get("/api/kunde/briefing").json()["struktur"]; fl={f["key"]:"x" for ab in st for f in ab["felder"] if f["pflicht"]}
rb=c.put("/api/kunde/briefing",json={"daten":fl,"abschicken":True}); chk("Briefing abgeschickt",rb.status_code==200,rb.text)
sl=c.get("/api/kunde/startliste").json(); br=[p for p in sl["punkte"] if p["titel"]=="Briefing ausgefüllt"][0]; chk("Briefing abgeschickt: Schritt erledigt",br["fertig"],br)
a.patch(f"/api/admin/kunden/{kid}/status" if False else f"/api/admin/kunden/{kid}/status",json={"status":"aktiv"}) if False else a.post(f"/api/admin/kunden/{kid}/status",json={"status":"aktiv"})
chk("Nach Onboarding keine Startliste",c.get("/api/kunde/startliste").json()["aktiv"] is False)
lst=a.get("/api/admin/kunden").json(); b2=[k for k in lst if k["id"]==kid2][0]
chk("Kundenliste: Fortschritt im Onboarding",b2.get("onboarding") and b2["onboarding"]["gesamt"]>=5,b2)
chk("Kundenliste: Module einzeln",isinstance(b2["module"],list) and len(b2["module"])>=3)
# Erinnerungen (Job-Logik)
sql(f"update kunden set erstellt_am=now()-interval '9 days' where id='{kid2}'")
from app import db, jobs
db.open_pool(); n0=len(mails())
jobs.aufgaben_automatisch({"alarm_email":""}); jobs.aufgaben_automatisch({"alarm_email":""})
chk("Erinnerungsmail an Kunde (einmal)",len([m for m in mails()[n0:] if "Start" in str(m["Subject"]) and kmail2 in str(m["To"])])==1,[str(m["Subject"]) for m in mails()[n0:]])
chk("Mail nennt Briefing","Briefing" in text([m for m in mails()[n0:] if kmail2 in str(m["To"]) and "Start" in str(m["Subject"])][0]))
t=[x for x in a.get("/api/admin/aufgaben?status=alle").json() if x["kunden_id"]==kid2 and x["titel"].startswith("Onboarding nachfassen")]
chk("Aufgabe Onboarding nachfassen (einmal)",len(t)==1,t)
chk("Kein Doppelversand binnen 7 Tagen",sql(f"select onboarding_erinnert_am is not null from kunden where id='{kid2}'")=="t")

# ---- Kontaktformular -> Lead
sec=a.post("/api/admin/website-check/schluessel",json={}).json()["schluessel"]; S={"X-MK":"1","X-Lead-Secret":sec}; U=B+"/api/public/kontakt-lead"
pl={"email":f"anfrage{sfx}@muster.de","name":"Erika Muster","firma":"Muster GmbH","telefon":"0511 99","thema":"Websites & Funnels","budget":"bis 2.500 €","nachricht":"Wir brauchen eine neue Seite.","einwilligung":True}
chk("Ohne Schlüssel 401",httpx.post(U,headers={"X-MK":"1"},json=pl).status_code==401)
chk("Falscher Schlüssel 401",httpx.post(U,headers={"X-MK":"1","X-Lead-Secret":"x"},json=pl).status_code==401)
chk("Ohne Einwilligung 400",httpx.post(U,headers=S,json={**pl,"einwilligung":False}).status_code==400)
chk("Ungültige E-Mail 400",httpx.post(U,headers=S,json={**pl,"email":"kaputt"}).status_code==400)
r=httpx.post(U,headers=S,json=pl); chk("Lead angelegt",r.status_code==200 and r.json()["neu"],r.text)
row=sql(f"select firma||'|'||temperatur||'|'||quelle from leads where lower(email)='anfrage{sfx}@muster.de'"); chk("Lead heiß, Quelle website",row=="Muster GmbH|heiss|website",row)
lid=sql(f"select id from leads where lower(email)='anfrage{sfx}@muster.de'")
d=a.get(f"/api/admin/leads/{lid}").json(); chk("Nachricht im Verlauf",any("neue Seite" in x["inhalt"] and "Budget" in x["inhalt"] for x in d["aktivitaeten"]))
chk("Aufgabe Anfrage beantworten",any(x["titel"]=="Anfrage beantworten: Muster GmbH" for x in a.get("/api/admin/aufgaben").json()))
r=httpx.post(U,headers=S,json={**pl,"nachricht":"Noch eine Frage."}); chk("Zweite Anfrage: gleicher Lead",r.status_code==200 and not r.json()["neu"] and sql(f"select count(*) from leads where lower(email)='anfrage{sfx}@muster.de'")=="1",r.text)
chk("Zweite Nachricht ergänzt",sum(1 for x in a.get(f"/api/admin/leads/{lid}").json()["aktivitaeten"] if x["inhalt"].startswith("Anfrage über das Kontaktformular"))==2)

# ---- Heute zu tun
h=a.get("/api/admin/heute").json()
chk("Heute: Struktur",all(k in h for k in ("nachrichten","aufgaben","leads","freigaben","onboarding","rechnungen","avv_fehlt","gesamt")),h.keys())
chk("Heute: heißer Lead dabei",any(l["firma"]=="Muster GmbH" and l["temperatur"]=="heiss" for l in h["leads"]),h["leads"])
chk("Heute: Onboarding hängt",any(o["id"]==kid2 for o in h["onboarding"]),h["onboarding"])
chk("Heute: Kunde ohne Zugriff",c.get("/api/admin/heute").status_code==403)

# ---- Angebot aus Lead
k=a.post(f"/api/admin/leads/{lid}/zu-kunde"); chk("Lead zu Kunde",k.status_code==200 and "id" in k.json(),k.text)
chk("Lead hat Kunde",sql(f"select kunden_id is not null from leads where id='{lid}'")=="t")
v=a.get(f"/api/admin/kunden/{k.json()['id']}/belege-vorlage"); chk("Angebots-Vorlage für den Kunden erreichbar",v.status_code==200,v.text[:200])
