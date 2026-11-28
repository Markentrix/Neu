"""Mail-Verlauf je Kunde und Lead, Stammdaten-Check, Terminvorschläge durch Vertriebler, Beratung nur Inhaber."""
import httpx, time, re, email, subprocess
from datetime import datetime, timedelta, timezone
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time()))
def zeit(tage,std=10): return (datetime.now(timezone.utc)+timedelta(days=tage)).replace(hour=std,minute=0,second=0,microsecond=0).isoformat()
base=90+int(sfx[-2:])%50
k=a.post("/api/admin/kunden",json={"firma":f"Verlaufkunde {sfx}","ansprechpartner":"Vera Verlauf","email":f"vv{sfx}@k.de","telefon":"0511 123456","strasse":"Weg 1","plz":"29221","ort":"Celle","branche":"Kfz","paket_code":"KI_ONE","einladen":True}).json()
kid=k["id"]
d=a.get(f"/api/admin/kunden/{kid}/mails").json(); chk("Einladung steht im Verlauf (Adresse erkannt)",d["gesamt"]>=1 and any(x["art"]=="zugang" for x in d["mails"]),d)
r=a.post("/api/admin/terminvorschlaege",json={"kunden_id":kid,"zeiten":[zeit(base)]}); chk("Terminvorschlag gesendet",r.status_code==200 and r.json()["gesendet"],r.text)
vid=a.get("/api/admin/terminvorschlaege",params={"kunden_id":kid}).json()[0]["id"]
sql(f"update terminvorschlaege set erstellt_am=now()-interval '3 days' where id='{vid}'")
chk("Nachfassen",a.post(f"/api/admin/terminvorschlaege/{vid}/nachfassen").status_code==200)
d=a.get(f"/api/admin/kunden/{kid}/mails").json()
art={x["art"]:x for x in d["arten"]}; chk("Zähler: 1 Terminvorschlag, 1 Erinnerung",art.get("termin",{}).get("n")==1 and art.get("erinnerung",{}).get("n")==1,d["arten"])
chk("Betreff und Zeit im Verlauf",all(x["betreff"] and x["zeit"] and x["an"]==f"vv{sfx}@k.de" for x in d["mails"]),d["mails"][:2])
chk("Neueste Mail zuerst",d["mails"][0]["art"]=="erinnerung")
c0=a.get(f"/api/admin/kunden/{kid}/stammdaten-check").json(); chk("Check: vollständiger Kunde ist komplett gepflegt",c0["ok"]==c0["gesamt"],c0)
# Fehlversand
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":1,"sicherung":"keine","absender":"info@markentrix.de"})
a.post("/api/admin/terminvorschlaege",json={"kunden_id":kid,"zeiten":[zeit(base+1)]})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
d=a.get(f"/api/admin/kunden/{kid}/mails").json(); chk("Fehlversand sichtbar",d["fehler"]>=1 and any(not x["ok"] and x["fehler"] for x in d["mails"]),d["arten"])
c=a.get(f"/api/admin/kunden/{kid}/stammdaten-check").json(); chk("Check meldet nicht zustellbare Mails",any(p["feld"]=="email_funktioniert" and not p["ok"] for p in c["punkte"]),c)
k2=a.post("/api/admin/kunden",json={"firma":f"Lueckenkunde {sfx}"}).json()
c=a.get(f"/api/admin/kunden/{k2['id']}/stammdaten-check")
chk("Lückenhafter Kunde: Hinweise",c.status_code==200 and c.json()["ok"]<c.json()["gesamt"]-4 and any(p["feld"]=="email" and not p["ok"] for p in c.json()["punkte"]),c.text)
chk("Unbekannter Kunde 404",a.get("/api/admin/kunden/00000000-0000-0000-0000-000000000000/mails").status_code==404)
# Lead + Vertrieb
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"vera{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
tok=re.search(r"token=([A-Za-z0-9_-]+)",lk).group(1)
httpx.post(B+"/api/einladung",headers=H,json={"token":tok,"password":"VeraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); chk("Vertriebler angemeldet",v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123456"}).status_code==200)
l1=a.post("/api/admin/leads",json={"firma":f"Veralead {sfx}","telefon":f"0511 76{sfx[-5:]}","ort":"Celle","plz":"29221","email":f"vl{sfx}@lead.de","vertriebspartner_id":pid,"trotzdem":True}).json()["id"]
l2=a.post("/api/admin/leads",json={"firma":f"Fremdlead {sfx}","telefon":f"0511 77{sfx[-5:]}","ort":"Celle","plz":"29221","email":f"fl{sfx}@lead.de","trotzdem":True}).json()["id"]
r=v.post(f"/api/vertrieb/leads/{l1}/terminvorschlaege",json={"zeiten":[zeit(base+3),zeit(base+3,14)]}); chk("Vertriebler sendet Terminvorschläge an eigenen Lead",r.status_code==200 and r.json()["gesendet"],r.text)
chk("Fremder Lead: 404",v.post(f"/api/vertrieb/leads/{l2}/terminvorschlaege",json={"zeiten":[zeit(base+3)]}).status_code==404)
chk("Liste der eigenen Vorschläge",len(v.get(f"/api/vertrieb/leads/{l1}/terminvorschlaege").json())==1)
chk("Fremde Liste: 404",v.get(f"/api/vertrieb/leads/{l2}/terminvorschlaege").status_code==404)
d=v.get(f"/api/vertrieb/leads/{l1}/mails").json(); chk("Vertriebler sieht Mail-Verlauf des eigenen Leads",d["gesamt"]>=1 and d["mails"][0]["art"]=="termin",d)
chk("Fremder Mail-Verlauf: 404",v.get(f"/api/vertrieb/leads/{l2}/mails").status_code==404)
chk("Admin sieht Lead-Verlauf",a.get(f"/api/admin/leads/{l1}/mails").json()["gesamt"]>=1)
chk("Vertriebler nicht im Admin-Verlauf",v.get(f"/api/admin/leads/{l1}/mails").status_code in (401,403))
chk("Admin-Terminvorschlag-API für Vertriebler gesperrt",v.post("/api/admin/terminvorschlaege",json={"lead_id":l1,"zeiten":[zeit(base+4)]}).status_code in (401,403))
# Beratung nur Inhaber: Mitarbeiter-Zugang
a.put("/api/admin/einstellungen/buchung",json={"aktiv":True,"dauer":30,"tage":30,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":12,"ort":"Telefon","erlaubte_seiten":"markentrix.de"})
def mails():
    return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
tok2=[re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m)).group(1) for m in mails() if f"vv{sfx}@k.de" in str(m["To"]) and "einladung?token" in (text(m) or "")][-1]
httpx.post(B+"/api/einladung",headers=H,json={"token":tok2,"password":"InhaberPasswort1"})
ci=httpx.Client(base_url=B,headers=H); ci.post("/api/login",json={"email":f"vv{sfx}@k.de","password":"InhaberPasswort1"})
chk("Inhaber sieht Beratungsseite",ci.get("/api/kunde/beratung").status_code==200)
