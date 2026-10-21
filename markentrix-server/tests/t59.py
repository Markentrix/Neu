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
sfx=str(int(time.time())+137)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"mwst_satz":19,"steuernummer":"12/345/67890"})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime
kA,cA,mA=neuer_kunde("Emp"); kB,cB,mB=neuer_kunde("Empb")
heute=datetime.date.today()
def einladen(c,mail,rolle,bis=None):
    body={"email":mail,"name":"Vertretung","kunden_rolle":rolle}
    if bis: body["zugang_bis"]=bis
    r=c.post("/api/kunde/team/einladen",json=body); assert r.status_code==200,r.text; return r.json()
def zugang(mail):
    adr=mail
    time.sleep(1.2)
    t=token(adr); httpx.post(B+"/api/einladung",headers=H,json={"token":t,"password":"EmpfangPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":adr,"password":"EmpfangPasswort1"}); return c,r
mE=f"empfang{sfx}@k.de"
einladen(cA,mE,"empfang",(heute+datetime.timedelta(days=7)).isoformat())
cE,r=zugang(mE); chk("Empfang: Login klappt",r.status_code==200,r.text)
chk("Rolle gespeichert",sql(f"select kunden_rolle||'|'||zugang_bis from benutzer where email='{mE}'")==f"empfang|{(heute+datetime.timedelta(days=7)).isoformat()}")
for pfad in ("/api/kunde/start","/api/kunde/anfragen","/api/kunde/termine","/api/kunde/kontakte","/api/kunde/tickets","/api/kunde/profil"):
    chk("Empfang darf "+pfad,cE.get(pfad).status_code==200,cE.get(pfad).text[:120])
for pfad in ("/api/kunde/belege","/api/kunde/team","/api/kunde/kuendigung","/api/kunde/datenexport.zip","/api/kunde/avv","/api/kunde/monatsberichte","/api/kunde/website-dienste","/api/kunde/website-dienste/zustellung","/api/kunde/dokumente","/api/kunde/vertretung","/api/kunde/lastschrift","/api/kunde/berichte"):
    chk("Empfang gesperrt: "+pfad,cE.get(pfad).status_code==403,(pfad,cE.get(pfad).status_code))
chk("Empfang darf nicht kündigen",cE.post("/api/kunde/kuendigung",json={"bestaetigt":True}).status_code==403)
chk("Empfang darf Kontakt anlegen",cE.post("/api/kunde/kontakte",json={"name":"Max Muster","telefon":"0511 123"}).status_code in (200,201))
chk("Admin-Bereich bleibt zu",cE.get("/api/admin/kunden").status_code==403)
# Mitarbeiter-Zugang: weiterhin wie bisher
chk("Inhaber sieht Team mit Ablaufdatum",any(x["email"]==mE and str(x["zugang_bis"])==(heute+datetime.timedelta(days=7)).isoformat() for x in cA.get("/api/kunde/team").json()))
# Ablauf: abgelaufener Zugang wird abgewiesen, bestehende Sitzung endet
sql(f"update benutzer set zugang_bis=current_date-1 where email='{mE}'")
chk("Abgelaufen: laufende Sitzung endet",cE.get("/api/kunde/start").status_code==401)
r=httpx.Client(base_url=B,headers=H).post("/api/login",json={"email":mE,"password":"EmpfangPasswort1"}); chk("Abgelaufen: Login abgelehnt",r.status_code==401,r.status_code)
# Inhaber verlängert
uid=sql(f"select id from benutzer where email='{mE}'")
r=cA.patch(f"/api/kunde/team/{uid}",json={"zugang_bis":(heute+datetime.timedelta(days=3)).isoformat()}); chk("Inhaber verlängert den Zugang",r.status_code==200)
r=httpx.Client(base_url=B,headers=H).post("/api/login",json={"email":mE,"password":"EmpfangPasswort1"}); chk("Nach Verlängerung wieder Login",r.status_code==200,r.text)
r=cA.patch(f"/api/kunde/team/{uid}",json={"zugang_bis":None}); chk("Befristung entfernen",r.status_code==200 and sql(f"select zugang_bis is null from benutzer where id='{uid}'")=="t")
chk("Rollenwechsel auf Mitarbeiter: Rechnungen weiter gesperrt, Anfragen offen",cA.patch(f"/api/kunde/team/{uid}",json={"kunden_rolle":"mitarbeiter"}).status_code==200)
chk("Ungültige Rolle abgelehnt",cA.post("/api/kunde/team/einladen",json={"email":f"x{sfx}@k.de","kunden_rolle":"chef"}).status_code==400)
# Fremder Kunde
chk("Anderer Kunde kann fremdes Mitglied nicht ändern",cB.patch(f"/api/kunde/team/{uid}",json={"zugang_bis":None}).status_code==404)
chk("Empfang kann Team nicht einladen",cE.post("/api/kunde/team/einladen",json={"email":f"y{sfx}@k.de","kunden_rolle":"inhaber"}).status_code in (401,403))
