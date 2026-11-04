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
sfx=str(int(time.time())+427)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime
D="/api/kunde/website-dienste"
kA,cA,mA=neuer_kunde("Zeitraum")
dom=f"zeitraum{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) select '{kA}', code, true from module on conflict (kunden_id,modul_code) do update set aktiv=true")
K=lambda t: {"aktiv":True,"dauer":30,"tage":t,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"x","empfaenger":"","zeiten":"","kapazitaet":0,"freigabe":False}
z=cA.get(D).json(); chk("Neuer Betrieb: Standard 90 Tage",z["kalender"]["tage"]==90,z["kalender"])
chk("180 Tage erlaubt",cA.put(D+"/kalender",json=K(180)).status_code==200)
chk("181 Tage abgelehnt",cA.put(D+"/kalender",json=K(181)).status_code==422)
chk("0 Tage abgelehnt",cA.put(D+"/kalender",json=K(0)).status_code==422)
chk("Gespeichert: 180",cA.get(D).json()["kalender"]["tage"]==180)
W=httpx.Client(base_url=B,headers={"Host":dom})
heute=datetime.date.today()
def gesperrt(): return set(W.get("/siteapi/api/verfuegbarkeit",headers={"User-Agent":"Mozilla/5.0 Test"}).json()["blocked"])
g=gesperrt(); chk("180 Tage: Tag 150 buchbar, Tag 190 gesperrt",(heute+datetime.timedelta(days=150)).isoformat() not in g and (heute+datetime.timedelta(days=190)).isoformat() in g)
cA.put(D+"/kalender",json=K(21)); g=gesperrt()
chk("21 Tage: Tag 20 buchbar, Tag 30 gesperrt",(heute+datetime.timedelta(days=20)).isoformat() not in g and (heute+datetime.timedelta(days=30)).isoformat() in g)
