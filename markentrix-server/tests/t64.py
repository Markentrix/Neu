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
sfx=str(int(time.time())+177)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, os, sys
sys.path.insert(0,"/home/claude/markentrix-server/portal")
Q="/var/tmp/pt/b/queue"; DNS="/var/tmp/pt/dns.json"
kA,cA,mA=neuer_kunde("Onbo")
sql(f"update kunden set status='onboarding' where id='{kA}'")
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) values ('{kA}','website',true) on conflict (kunden_id, modul_code) do update set aktiv=true")
L=lambda: {p["code"]:p for p in a.get(f"/api/admin/kunden/{kA}/onboarding").json()["punkte"]}
p=L()
chk("Neue Schritte da: DNS und Google-Profil",{"dns","google_profil","domain","website","rechnung"}<=set(p),list(p))
chk("DNS noch offen",not p["dns"]["fertig"])
chk("Rechnung noch offen",not p["rechnung"]["fertig"])
dom=f"onbo{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sql(f"INSERT INTO domain_pruefung (domain, kunden_id, ok) VALUES ('{dom}','{kA}',false)")
chk("DNS offen bei falscher Domain",not L()["dns"]["fertig"])
sql(f"update domain_pruefung set ok=true where domain='{dom}'")
chk("DNS wird automatisch erkannt",L()["dns"]["fertig"] and L()["dns"]["automatisch"])
sql(f"INSERT INTO belege (art, kunden_id, status, nummer) VALUES ('rechnung','{kA}','entwurf','R-T{sfx}')")
chk("Entwurf zählt nicht als Rechnung",not L()["rechnung"]["fertig"])
sql(f"update belege set status='versendet' where nummer='R-T{sfx}'")
chk("Gestellte Rechnung wird erkannt",L()["rechnung"]["fertig"] and L()["rechnung"]["automatisch"])
chk("Google-Profil bleibt Handarbeit",not L()["google_profil"]["fertig"])
r=a.patch(f"/api/admin/kunden/{kA}/onboarding/google_profil",json={"erledigt":True}); chk("Google-Profil abhaken",r.status_code==200,r.text)
chk("Abgehakt",L()["google_profil"]["fertig"])
# Übersicht: nächster Schritt, hängt
o=[x for x in a.get("/api/admin/onboarding/offen").json() if x["id"]==kA]
chk("Übersicht nennt nächsten Schritt",bool(o) and o[0]["naechster"] and o[0]["gesamt"]>=10 and o[0]["fertig"]>=3,o)
chk("Frischer Kunde hängt nicht",bool(o) and o[0]["haengt"] is False and o[0]["tage_still"]<=1,o)
sql(f"update kunden set erstellt_am=now()-interval '20 days' where id='{kA}'")
sql(f"update onboarding_punkte set erledigt_am=now()-interval '12 days' where kunden_id='{kA}' and erledigt")
o=[x for x in a.get("/api/admin/onboarding/offen").json() if x["id"]==kA]
chk("Nach 12 Tagen Stillstand: hängt",bool(o) and o[0]["haengt"] is True and o[0]["tage_still"]>=11,o)
alle=a.get("/api/admin/onboarding/offen").json(); chk("Hängende Kunden stehen oben",alle[0]["haengt"] is True)
chk("Kunde sieht Übersicht nicht",cA.get("/api/admin/onboarding/offen").status_code==403)
print("FERTIG")
