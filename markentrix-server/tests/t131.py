"""Terminvorschläge im Angebot: bis zu 3 Zeiten, der Empfänger wählt im Angebots-Link, das Gespräch landet im Admin-Kalender (Lead- und Kunden-Angebote)."""
import httpx, time, re, email, email.header, json, subprocess, datetime
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
def mail_an(adr, enthaelt=""):
    time.sleep(1.5)
    return [m for m in mails() if adr in str(m["To"]) and enthaelt in betreff(m)]
def einladung(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m) or "")
            if g: return g.group(1)
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
sfx=str(int(time.time())+3100)
UTC=datetime.timezone.utc
def zeit(tage,std): d=(datetime.datetime.now(UTC)+datetime.timedelta(days=tage)).replace(hour=std,minute=0,second=0,microsecond=0); return d.isoformat()
pos=[{"text":"BUSINESS – monatlich","menge":1,"einheit":"Monat","preis_cent":19900}]
t1,t2,t3=zeit(5,9),zeit(6,10),zeit(7,11)

# ---- Lead-Angebot
lid=a.post("/api/admin/leads",json={"firma":f"Termin {sfx}","telefon":f"0511 93{sfx[-5:]}","ort":"Celle","plz":"29221","email":f"termin{sfx}@lead.de","ansprechpartner":"Frau Termin"}).json()["id"]
bid=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"A","einleitung":"H","schluss":"D","positionen":pos,"leistungen":[]}).json()["id"]
P=f"/api/admin/belege/{bid}/termine"
chk("Mehr als 3 Vorschläge werden abgelehnt",a.put(P,json={"termine":[t1,t2,t3,zeit(8,9)]}).status_code==400)
chk("Vergangene Zeit wird abgelehnt",a.put(P,json={"termine":[zeit(-1,9)]}).status_code==400)
chk("Doppelter Vorschlag wird abgelehnt",a.put(P,json={"termine":[t1,t1]}).status_code==400)
sql(f"insert into kalender_eintraege (art,titel,start,ende) values ('sperre','Urlaub','{t3}'::timestamptz,'{t3}'::timestamptz+interval '2 hours')")
r=a.put(P,json={"termine":[t1,t3]}); chk("Vorschlag in belegter Zeit wird abgelehnt",r.status_code==400 and "überschneidet" in r.text,r.text)
sql("delete from kalender_eintraege where titel='Urlaub'")
r=a.put(P,json={"termine":[t3,t1,t2]}); chk("3 Vorschläge werden gespeichert, sortiert",r.status_code==200 and r.json()["termine"]==sorted(r.json()["termine"]) and len(r.json()["termine"])==3,r.text)
chk("Nur Admins dürfen Vorschläge ändern",httpx.Client(base_url=B,headers=H).put(P,json={"termine":[]}).status_code in (401,403))
r=a.post(f"/api/admin/leads/{lid}/angebote/{bid}/senden",json={"gueltig_tage":30}); chk("Senden",r.status_code==200 and r.json()["gesendet"],r.text)
link=r.json()["link"]; tok=link.split("t=")[1]
m=mail_an(f"termin{sfx}@lead.de","Angebot")
chk("Mail nennt die Terminvorschläge und den Link",bool(m) and "Beratungsgespräch" in text(m[-1]) and "Uhr" in text(m[-1]) and "/angebot?t=" in text(m[-1]),text(m[-1]) if m else "keine Mail")
c=httpx.Client(base_url=B,headers=H)
d=c.get(f"/api/angebot/{tok}").json()
chk("Angebotsseite liefert 3 freie Vorschläge",len(d.get("termine",[]))==3 and d["termin"] is None and d["termin_dauer"]>=15,d)
W=f"/api/angebot/{tok}/termin"
chk("Zeit außerhalb der Vorschläge wird abgelehnt",c.post(W,json={"start":zeit(9,9)}).status_code==400)
sql(f"insert into kalender_eintraege (art,titel,start,ende) values ('termin','Belegt','{t2}'::timestamptz,'{t2}'::timestamptz+interval '1 hour')")
d=c.get(f"/api/angebot/{tok}").json(); chk("Belegter Vorschlag verschwindet",len(d["termine"])==2,d["termine"])
chk("Belegten Vorschlag buchen: 409",c.post(W,json={"start":t2}).status_code==409)
sql("delete from kalender_eintraege where titel='Belegt'")
n0=len(mails())
r=c.post(W,json={"start":t1}); chk("Termin wählen",r.status_code==200 and "Uhr" in r.json()["wann"],r.text)
g=sql(f"select count(*)||'|'||coalesce(max(lead_id::text),'')||'|'||coalesce(max(gebucht_von),'') from gespraechstermine where beleg_id='{bid}' and status='gebucht'")
chk("Gespräch steht in der Datenbank, am Lead und am Angebot",g==f"1|{lid}|angebot",g)
mm=mail_an(f"termin{sfx}@lead.de","Beratungsgespräch")
chk("Bestätigung an den Empfänger mit Kalendereinladung",bool(mm) and any(p.get_content_type()=="text/calendar" for p in mm[-1].walk()) and "absagen" in text(mm[-1]))
chk("Team bekommt Bescheid",any("Beratungsgespräch gewählt" in betreff(x) for x in mails()[n0:]))
chk("Zweite Wahl: 409",c.post(W,json={"start":t3}).status_code==409)
d=c.get(f"/api/angebot/{tok}").json(); chk("Seite zeigt den gebuchten Termin, keine Vorschläge mehr",d["termin"] and d["termine"]==[],d)
v=(datetime.datetime.now(UTC)).date().isoformat(); b=(datetime.datetime.now(UTC)+datetime.timedelta(days=10)).date().isoformat()
k=a.get(f"/api/admin/kalender?von={v}&bis={b}").json()
chk("Termin erscheint im Admin-Kalender",any("Beratungsgespräch" in (x.get("nachricht") or "") for x in k["gespraeche"]),k["gespraeche"])
chk("Lead-Verlauf hat den Eintrag",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and art='termin' and inhalt like 'Beratungsgespräch%'"))==1)
chk("Vorschläge ändern nach Buchung: 400",a.put(P,json={"termine":[]}).status_code==400)
tk=sql(f"select token from gespraechstermine where beleg_id='{bid}' and status='gebucht'")
r=httpx.post(B+"/api/public/buchung/absagen",data={"t":tk}); chk("Absage über den Link",r.status_code==200 and sql(f"select status from gespraechstermine where beleg_id='{bid}'")=="abgesagt",r.text[:200])
d=c.get(f"/api/angebot/{tok}").json(); chk("Nach Absage sind die Vorschläge wieder wählbar",len(d["termine"])==3 and d["termin"] is None,d)
chk("Ohne Termin gebucht: Vorschläge sind änderbar",a.put(P,json={"termine":[t1]}).status_code==200)

# ---- Angebot an bestehenden Kunden (ohne Lead): Online-Link entsteht beim Senden
r=a.post("/api/admin/kunden",json={"firma":f"Kundtermin {sfx}","ansprechpartner":"Tina Test","email":f"kundtermin{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":False}); kid=r.json()["id"]
bk=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"angebot","betreff":"Kundenangebot","einleitung":"H","schluss":"D","positionen":pos,"leistungen":[]}).json()["id"]
PK=f"/api/admin/belege/{bk}/termine"
chk("Kunden-Angebot: Vorschläge am Entwurf",a.put(PK,json={"termine":[t1,t2]}).status_code==200)
chk("Detail liefert die Vorschläge",len(a.get(f"/api/admin/belege/{bk}").json()["beleg"]["terminvorschlaege"])==2)
chk("Ausstellen",a.post(f"/api/admin/belege/{bk}/ausstellen",json={}).status_code==200)
chk("Nach dem Ausstellen noch änderbar",a.put(PK,json={"termine":[t1,t2,t3]}).status_code==200)
r=a.post(f"/api/admin/belege/{bk}/senden"); chk("Senden an den Kunden",r.status_code==200 and r.json()["gesendet"],r.text)
m=mail_an(f"kundtermin{sfx}@k.de","Angebot")
chk("Kunden-Mail hat Online-Link und Terminvorschläge",bool(m) and "/angebot?t=" in text(m[-1]) and "Beratungsgespräch" in text(m[-1]),text(m[-1]) if m else "keine Mail")
tk2=re.search(r"/angebot\?t=([A-Za-z0-9_-]+)",text(m[-1])).group(1)
r2=a.post(f"/api/admin/belege/{bk}/senden"); m2=mail_an(f"kundtermin{sfx}@k.de","Angebot")
chk("Erneut senden: derselbe Link bleibt gültig","/angebot?t="+tk2 in text(m2[-1]))
d=c.get(f"/api/angebot/{tk2}").json(); chk("Seite für Kunden-Angebot zeigt 3 Vorschläge",len(d["termine"])==3 and d["empfaenger"].startswith("Kundtermin"),d)
r=c.post(f"/api/angebot/{tk2}/termin",json={"start":t2}); chk("Kunde wählt Termin",r.status_code==200,r.text)
g=sql(f"select count(*)||'|'||coalesce(max(lead_id::text),'-')||'|'||max(name) from gespraechstermine where beleg_id='{bk}' and status='gebucht'")
chk("Gespräch ohne Lead, Name aus dem Kunden",g=="1|-|Tina Test",g)
chk("Mail an den Kunden mit Einladung",bool(mail_an(f"kundtermin{sfx}@k.de","Beratungsgespräch")))
chk("Termin im Admin-Kalender (Kunden-Angebot)",any("Beratungsgespräch" in (x.get("nachricht") or "") and not x.get("lead_id") for x in a.get(f"/api/admin/kalender?von={v}&bis={b}").json()["gespraeche"]))
r=c.post(f"/api/angebot/{tk2}/annehmen",json={"name":"Tina Test","bestaetigt":True}); chk("Online-Annahme eines Kunden-Angebots geht",r.status_code==200 and sql(f"select status from belege where id='{bk}'")=="angenommen",r.text)
chk("Danach zeigt die Seite weiter den Termin",c.get(f"/api/angebot/{tk2}").json()["termin"] is not None)
