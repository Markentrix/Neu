"""Terminvorschläge ohne Angebot: an Kunden und Leads, Auswahl per Link, Kalender, Einladung, Rückzug, Konflikte."""
import httpx, time, re, email, email.header, subprocess
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def mails_an(adr):
    time.sleep(1.5); return [m for m in mails() if adr in str(m["To"])]
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time()))
TZ=ZoneInfo("Europe/Berlin")
def zeit(tage,std):
    d=(datetime.now(TZ)+timedelta(days=tage)).replace(hour=std,minute=0,second=0,microsecond=0); return d.astimezone(timezone.utc).isoformat()
base=40+int(sfx[-2:])%40  # weit in der Zukunft, wenig Überschneidung mit anderen Tests
k=a.post("/api/admin/kunden",json={"firma":f"Terminkunde {sfx}","ansprechpartner":"Tina Test","email":f"tv{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json()
kid=k["id"]
t1,t2,t3=zeit(base,10),zeit(base,14),zeit(base+1,9)
chk("Ohne Empfänger abgelehnt",a.post("/api/admin/terminvorschlaege",json={"zeiten":[t1]}).status_code==400)
chk("Mehr als 3 abgelehnt",a.post("/api/admin/terminvorschlaege",json={"kunden_id":kid,"zeiten":[t1,t2,t3,zeit(base+2,9)]}).status_code==422)
chk("Vergangenheit abgelehnt",a.post("/api/admin/terminvorschlaege",json={"kunden_id":kid,"zeiten":[zeit(-2,10)]}).status_code==400)
r=a.post("/api/admin/terminvorschlaege",json={"kunden_id":kid,"zeiten":[t1,t2,t3],"nachricht":"Wir sprechen kurz über Ihre Website."}); chk("Kunde: Vorschläge gesendet",r.status_code==200 and r.json()["gesendet"],r.text)
tok=sql(f"select token from terminvorschlaege where kunden_id='{kid}' and status='offen'")
m=mails_an(f"tv{sfx}@k.de"); chk("Mail mit Auswahl-Link je Termin",m and text(m[-1]).count("/termin?t="+tok)>=4 and "Wir sprechen kurz" in text(m[-1]),text(m[-1]) if m else "keine Mail")
chk("Mail ohne KI-Namen","Claude" not in text(m[-1]))
v=httpx.get(B+"/api/public/terminvorschlag",params={"t":tok}).json(); chk("Öffentlich: 3 freie Termine",v["status"]=="offen" and len(v["termine"])==3,v)
chk("Ungültiger Token 404",httpx.get(B+"/api/public/terminvorschlag",params={"t":"nix"}).status_code==404)
chk("Seite /termin erreichbar",httpx.get(B+"/termin?t="+tok).status_code==200)
chk("GET bucht nichts",sql(f"select count(*) from gespraechstermine where kunden_id='{kid}'")=="0")
chk("Fremder Termin abgelehnt",httpx.post(B+"/api/public/terminvorschlag",headers=H,json={"t":tok,"start":zeit(base+5,11)}).status_code==400)
# Ein Vorschlag wird anderweitig belegt: Kalender-Eintrag überschneidet t2
a.post("/api/admin/kalender/eintraege",json={"art":"sperre","titel":"Blocker","start":t2,"ende":(datetime.fromisoformat(t2)+timedelta(hours=1)).isoformat()})
v=httpx.get(B+"/api/public/terminvorschlag",params={"t":tok}).json()
chk("Belegter Vorschlag verschwindet",len(v["termine"])<=2 and not any(datetime.fromisoformat(x)==datetime.fromisoformat(t2) for x in v["termine"]),v)
chk("Belegten wählen: 409",httpx.post(B+"/api/public/terminvorschlag",headers=H,json={"t":tok,"start":t2}).status_code==409)
r=httpx.post(B+"/api/public/terminvorschlag",headers=H,json={"t":tok,"start":t1}); chk("Bestätigt",r.status_code==200 and r.json()["ok"],r.text)
g=sql(f"select status||'|'||gebucht_von||'|'||coalesce(lead_id::text,'-') from gespraechstermine where kunden_id='{kid}'"); chk("Gespräch im Kalender (Kunde, ohne Lead)",g=="gebucht|terminvorschlag|-",g)
chk("Vorschlag gewählt",sql(f"select status from terminvorschlaege where token='{tok}'")=="gewaehlt")
chk("Zweite Wahl abgelehnt",httpx.post(B+"/api/public/terminvorschlag",headers=H,json={"t":tok,"start":t3}).status_code==409)
v=httpx.get(B+"/api/public/terminvorschlag",params={"t":tok}).json(); chk("Link zeigt danach den Termin",v["status"]=="gewaehlt" and v["termin"]["start"],v)
m=mails_an(f"tv{sfx}@k.de"); ics=[p for x in m for p in x.walk() if p.get_filename()=="termin.ics"]; chk("Bestätigungsmail mit Einladung (.ics)",bool(ics))
chk("Team-Mail",any("Beratungsgespräch bestätigt" in str(email.header.make_header(email.header.decode_header(x["Subject"] or ""))) for x in mails()))
kal=a.get("/api/admin/kalender",params={"von":(datetime.now(TZ)+timedelta(days=base-1)).date().isoformat(),"bis":(datetime.now(TZ)+timedelta(days=base+3)).date().isoformat()})
chk("Im Admin-Kalender sichtbar",kal.status_code==200 and f"Terminkunde {sfx}" in kal.text,kal.text[:200])
# Lead
lid=a.post("/api/admin/leads",json={"firma":f"Tvlead {sfx}","telefon":f"0511 74{sfx[-5:]}","ort":"Celle","plz":"29221","email":f"tvl{sfx}@lead.de","ansprechpartner":"Herr Lead"}).json()["id"]
l1,l2=zeit(base+10,10),zeit(base+10,15)
r=a.post("/api/admin/terminvorschlaege",json={"lead_id":lid,"zeiten":[l1,l2]}); chk("Lead: gesendet",r.status_code==200 and r.json()["gesendet"],r.text)
ltok=sql(f"select token from terminvorschlaege where lead_id='{lid}' and status='offen'")
# neuer Versand zieht alten zurück
r=a.post("/api/admin/terminvorschlaege",json={"lead_id":lid,"zeiten":[l1,l2],"an_email":f"andere{sfx}@lead.de"}); chk("Neuer Versand an andere Adresse",r.status_code==200 and r.json()["gesendet"],r.text)
chk("Alter Vorschlag zurückgezogen",sql(f"select status from terminvorschlaege where token='{ltok}'")=="zurueckgezogen")
chk("Zurückgezogener Link nicht mehr wählbar",httpx.post(B+"/api/public/terminvorschlag",headers=H,json={"t":ltok,"start":l1}).status_code==409)
ltok=sql(f"select token from terminvorschlaege where lead_id='{lid}' and status='offen'")
chk("Mail an abweichende Adresse",bool(mails_an(f"andere{sfx}@lead.de")))
lst=a.get("/api/admin/terminvorschlaege",params={"lead_id":lid}).json(); chk("Liste zeigt beide",len(lst)==2)
chk("Liste braucht genau einen Bezug",a.get("/api/admin/terminvorschlaege").status_code==400)
httpx.post(B+"/api/public/terminvorschlag",headers=H,json={"t":ltok,"start":l2})
s=sql(f"select status from leads where id='{lid}'"); chk("Lead-Status Termin",s=="termin",s)
chk("Verlauf-Eintrag am Lead",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and art='termin'"))>=2)
# Rückzug
r=a.post("/api/admin/terminvorschlaege",json={"kunden_id":kid,"zeiten":[zeit(base+20,10)]}); vid=a.get("/api/admin/terminvorschlaege",params={"kunden_id":kid}).json()[0]["id"]
sql(f"update terminvorschlaege set erstellt_am=now()-interval '3 days' where id='{vid}'")
hz=a.get("/api/admin/heute").json(); chk("Mein Tag: Vorschlag ohne Antwort nach 3 Tagen",any(x["id"]==vid and x["tage"]>=3 for x in hz["vorschlaege"]),hz.get("vorschlaege"))
n0=len(mails_an(f"tv{sfx}@k.de")); r=a.post(f"/api/admin/terminvorschlaege/{vid}/nachfassen"); chk("Nachfassen gesendet",r.status_code==200,r.text)
m=mails_an(f"tv{sfx}@k.de"); chk("Erinnerungsmail mit Link",len(m)>n0 and "Erinnerung" in text(m[-1]) and "/termin?t=" in text(m[-1]),text(m[-1]) if m else "")
chk("Nachfass-Zähler",sql(f"select nachfass_anzahl from terminvorschlaege where id='{vid}'")=="1")
chk("Nachfassen bei fremder ID 404",a.post("/api/admin/terminvorschlaege/00000000-0000-0000-0000-000000000000/nachfassen").status_code==404)
sql(f"insert into gespraechstermine (start,ende,name,email,status,token,gebucht_von,kunden_id) values (now()+interval '5 hours',now()+interval '5 hours 30 minutes','Heute Gast','heute{sfx}@k.de','gebucht','tk{sfx}','terminvorschlag','{kid}')")
hz=a.get("/api/admin/heute").json(); chk("Mein Tag: Gespräch in den nächsten 36 Stunden",any(x["name"]=="Heute Gast" for x in hz["gespraeche"]),hz.get("gespraeche"))
chk("Zurückziehen",a.delete(f"/api/admin/terminvorschlaege/{vid}").status_code==200)
chk("Zweites Zurückziehen 404",a.delete(f"/api/admin/terminvorschlaege/{vid}").status_code==404)
# Ohne Anmeldung kein Admin-Zugriff
chk("Admin-API geschützt",httpx.get(B+"/api/admin/terminvorschlaege",params={"lead_id":lid}).status_code in (401,403))
