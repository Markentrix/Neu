import httpx, time, re, email, subprocess
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
sfx=str(int(time.time())+169)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import json, os, sys
from time import time as t0
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import zweifaktor
kA,cA,mA=neuer_kunde("Zwei")
sfx2=sfx
p=a.post("/api/admin/vertrieb/partner",json={"name":"Zora Zwei"}).json()
l=a.post(f"/api/admin/vertrieb/partner/{p['id']}/einladung",json={"email":f"zora{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":l.split("token=")[1],"password":"ZoraPasswort1234"})
v=httpx.Client(base_url=B,headers=H); r=v.post("/api/login",json={"email":f"zora{sfx}@v.de","password":"ZoraPasswort1234"}); chk("Vertrieb meldet sich an",r.status_code==200,r.text)
chk("Standard: keine Pflicht für Vertrieb",v.get("/api/me").json()["zwei_faktor_pflicht"] is False and v.get("/api/vertrieb/start").status_code==200)
s=a.get("/api/admin/sicherheit"); chk("Sicherheitsübersicht für Admin",s.status_code==200 and any(k["email"]==f"zora{sfx}@v.de" and k["totp_aktiv"] is False for k in s.json()["konten"]) and s.json()["vertrieb_pflicht"] is False,s.text[:300])
chk("Übersicht: Kunde gesperrt",cA.get("/api/admin/sicherheit").status_code==403 and cA.put("/api/admin/sicherheit",json={"vertrieb_2fa":True}).status_code==403)
chk("Übersicht: Vertrieb gesperrt",v.get("/api/admin/sicherheit").status_code==403)
chk("Übersicht: ohne Anmeldung gesperrt",httpx.get(B+"/api/admin/sicherheit",headers=H).status_code in (401,403))
chk("Übersicht zeigt keine Kundenkonten",all(k["rolle"] in ("admin","vertrieb") for k in s.json()["konten"]) and mA not in str(s.json()))
chk("Pflicht einschalten",a.put("/api/admin/sicherheit",json={"vertrieb_2fa":True}).status_code==200 and a.get("/api/admin/sicherheit").json()["vertrieb_pflicht"] is True)
me=v.get("/api/me").json(); chk("Vertrieb ohne 2FA: Pflicht gemeldet",me["zwei_faktor_pflicht"] is True and me["zwei_faktor"] is False,me)
r=v.get("/api/vertrieb/start"); chk("Vertrieb-Funktionen ohne 2FA gesperrt",r.status_code==403 and "Zwei-Faktor" in r.text,r.text)
s=v.post("/api/2fa/start").json(); chk("Einrichtung bleibt erlaubt",bool(s.get("geheimnis")),s)
r=v.post("/api/2fa/aktivieren",json={"code":zweifaktor._code(s["geheimnis"],int(t0()//30))}); chk("2FA eingerichtet",r.status_code==200,r.text)
chk("Danach frei",v.get("/api/me").json()["zwei_faktor_pflicht"] is False and v.get("/api/vertrieb/start").status_code==200)
chk("Übersicht zeigt aktiv",any(k["email"]==f"zora{sfx}@v.de" and k["totp_aktiv"] for k in a.get("/api/admin/sicherheit").json()["konten"]))
chk("Kunden-Portal bleibt unberührt",cA.get("/api/kunde/start").status_code==200)
chk("Admin bleibt unberührt",a.get("/api/admin/uebersicht").status_code==200)
chk("Pflicht ausschalten",a.put("/api/admin/sicherheit",json={"vertrieb_2fa":False}).status_code==200 and a.get("/api/admin/sicherheit").json()["vertrieb_pflicht"] is False)
chk("Audit",sql("select count(*) from audit_log where aktion='sicherheit_vertrieb_2fa'")!="0")
sql(f"update benutzer set totp_aktiv=false, totp_secret=NULL, totp_recovery='[]'::jsonb where email='zora{sfx}@v.de'")
print("FERTIG")
