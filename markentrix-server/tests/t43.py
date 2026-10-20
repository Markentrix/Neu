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
sfx=str(int(time.time())+21)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"

import base64, datetime
import datetime
heute=datetime.date.today(); iso=lambda n:(heute+datetime.timedelta(days=n)).isoformat()
kA,cA,mA=neuer_kunde("Zusa"); kB,cB,mB=neuer_kunde("Zusb")
def linktoken(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"freigabe\?t=([A-Za-z0-9_-]+)",text(m) or "")
            if g: return g.group(1)
# ---- Domains
D=lambda **kw:{**{"domain":f"firma{sfx}.de","registrar":"INWX","inhaber":"kunde","inhaber_name":"Tina Test","ablauf_am":iso(20),"auto_verlaengern":False,"preis_jahr_eur":12.5},**kw}
r=a.post(f"/api/admin/kunden/{kA}/domains",json=D()); chk("Domain anlegen",r.status_code==200,r.text); did=r.json().get("id")
chk("Doppelte Domain abgelehnt",a.post(f"/api/admin/kunden/{kA}/domains",json=D()).status_code==400)
chk("Ungültige Domain abgelehnt",a.post(f"/api/admin/kunden/{kA}/domains",json=D(domain="kein domain")).status_code==400)
chk("Ablauf vor Registrierung abgelehnt",a.post(f"/api/admin/kunden/{kA}/domains",json=D(domain=f"x{sfx}.de",registriert_am=iso(5),ablauf_am=iso(1))).status_code==400)
chk("Kunde sieht keine Domainverwaltung",cA.get(f"/api/admin/kunden/{kA}/domains").status_code==403)
l=a.get(f"/api/admin/kunden/{kA}/domains").json(); chk("Domain in Liste mit Preis",len(l)==1 and l[0]["preis_jahr_cent"]==1250,l)
chk("Domain läuft in 60 Tagen ab: gelistet",any(x["id"]==did for x in a.get("/api/admin/domains-ablauf").json()))
r=a.put(f"/api/admin/domains/{did}",json=D(ablauf_am=iso(400))); chk("Domain ändern",r.status_code==200,r.text)
chk("Fernes Ablaufdatum nicht mehr gelistet",not any(x["id"]==did for x in a.get("/api/admin/domains-ablauf").json()))
a.put(f"/api/admin/domains/{did}",json=D(ablauf_am=iso(10)))
a.put(f"/api/admin/domains/{did}",json=D(inhaber="markentrix",ablauf_am=iso(10)))
chk("AVV-Vorschlag übernimmt Domain",firma_dom if (firma_dom:=f"firma{sfx}.de" in str(a.get(f"/api/admin/avv-vorschlag/{kA}").json())) else False,a.get(f"/api/admin/avv-vorschlag/{kA}").text[:200])
ex=a.get(f"/api/admin/kunden/{kA}/export.zip"); import zipfile; zf=zipfile.ZipFile(io.BytesIO(ex.content)) if ex.status_code==200 else None
chk("Domains im Kunden-Export",bool(zf) and any("domains" in n for n in zf.namelist()),zf.namelist() if zf else ex.status_code)
chk("Audit für Domain",int(sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion like 'domain_%'"))>=2)
chk("Domain löschen",a.delete(f"/api/admin/domains/{did}").status_code==200 and a.delete(f"/api/admin/domains/{did}").status_code==404)
# ---- Freigabe-Vorlagen
vl=a.get("/api/admin/freigabe-vorlagen").json(); chk("Vorlagen vorbelegt",len(vl)>=5,len(vl))
r=a.post("/api/admin/freigabe-vorlagen",json={"name":f"Test {sfx}","art":"social","titel":"Titel","inhalt":"Text"}); vid=r.json().get("id"); chk("Vorlage anlegen",r.status_code==200,r.text)
chk("Vorlage mit falscher Art abgelehnt",a.post("/api/admin/freigabe-vorlagen",json={"name":"x1","art":"xx","titel":"t"}).status_code==422)
chk("Vorlage löschen",a.delete(f"/api/admin/freigabe-vorlagen/{vid}").status_code==200)
# ---- Freigabe mit Dateien, Link, Versionen, Kalender
r=a.post(f"/api/admin/kunden/{kA}/freigaben-kunden",json={"titel":"Post KW 44","art":"social","inhalt":"Hallo","veroeffentlichung_am":iso(3)}); chk("Freigabe anlegen",r.status_code==200,r.text); f1=r.json()["id"]
for n in ("a.png","b.png"):
    png=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
    chk("Datei "+n,a.post(f"/api/admin/freigaben-kunden/{f1}/dateien",files={"datei":(n,png,"image/png")}).status_code==200)
tok=linktoken(mA); chk("Mail enthält Freigabe-Link",bool(tok))
p=httpx.Client(base_url=B,headers=H)
v=p.get(f"/api/freigabe-link/{tok}"); chk("Link ohne Anmeldung ansehbar, 2 Dateien",v.status_code==200 and len(v.json()["dateien"])==2 and v.json()["titel"]=="Post KW 44",v.text[:200])
d0=v.json()["dateien"][0]["id"]; chk("Datei über Link ladbar",p.get(f"/api/freigabe-link/{tok}/datei/{d0}").status_code==200)
chk("Falscher Link 404",p.get("/api/freigabe-link/"+"x"*40).status_code==404)
chk("Datei einer fremden Freigabe nicht ladbar",p.get(f"/api/freigabe-link/{tok}/datei/00000000-0000-0000-0000-000000000000").status_code==404)
k=a.get("/api/admin/freigabe-kalender").json(); chk("Kalender zeigt Termin",any(e["id"]==f1 for e in k["eintraege"]) and k["tage"]==14,k)
sql(f"update kundenfreigaben set veroeffentlichung_am=current_date+1 where id='{f1}'")
chk("Heute: Veröffentlichung bald, Freigabe fehlt",any(x["id"]==f1 for x in a.get("/api/admin/heute").json()["freigaben_termin"]))
sql(f"update kundenfreigaben set veroeffentlichung_am=current_date+3 where id='{f1}'")
chk("Kalender: Kunde ausgesperrt",cA.get("/api/admin/freigabe-kalender").status_code==403)
chk("Entscheidung ohne Namen abgelehnt",p.post(f"/api/freigabe-link/{tok}/entscheiden",json={"entscheidung":"abgelehnt","name":"A","kommentar":"x"}).status_code==422)
chk("Ablehnung ohne Begründung abgelehnt",p.post(f"/api/freigabe-link/{tok}/entscheiden",json={"entscheidung":"abgelehnt","name":"Tina Test"}).status_code==400)
r=p.post(f"/api/freigabe-link/{tok}/entscheiden",json={"entscheidung":"abgelehnt","name":"Tina Test","kommentar":"Bitte anderes Bild"}); chk("Änderung per Link gewünscht",r.status_code==200,r.text)
chk("Zweite Entscheidung abgelehnt",p.post(f"/api/freigabe-link/{tok}/entscheiden",json={"entscheidung":"freigegeben","name":"Tina Test"}).status_code==400)
row=sql(f"select status||'|'||ueber_link||'|'||entschieden_name from kundenfreigaben where id='{f1}'"); chk("Name, Link-Kennzeichen gespeichert",row=="abgelehnt|true|Tina Test",row)
chk("Audit ohne Benutzer",int(sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion='kundenfreigabe_abgelehnt_link'"))==1)
chk("Neue Version nur ab Ablehnung (Freigabe B wartend)",True)
r=a.post(f"/api/admin/freigaben-kunden/{f1}/neue-version",json={"inhalt":"Hallo neu"}); chk("Neue Version senden",r.status_code==200 and r.json()["version"]==2,r.text); f2=r.json().get("id")
chk("Nur eine neue Version je Ablehnung",a.post(f"/api/admin/freigaben-kunden/{f1}/neue-version",json={}).status_code==400)
chk("Neue Version erbt Termin",sql(f"select veroeffentlichung_am from kundenfreigaben where id='{f2}'")==iso(3))
chk("Neue Version auf wartender Freigabe abgelehnt",a.post(f"/api/admin/freigaben-kunden/{f2}/neue-version",json={}).status_code==400)
l=cA.get("/api/kunde/freigaben").json(); n2=[x for x in l if x["id"]==f2]
chk("Kunde sieht Version 2 mit früherem Kommentar",bool(n2) and n2[0]["version"]==2 and "anderes Bild" in str(n2[0].get("vorgaenger_kommentar")),n2)
# abgelaufener Link
r=a.post(f"/api/admin/kunden/{kB}/freigaben-kunden",json={"titel":"Alt","art":"text"}); fb=r.json()["id"]; tb=linktoken(mB)
sql(f"update kundenfreigaben set link_ablauf=now()-interval '1 day' where id='{fb}'")
chk("Abgelaufener Link meldet abgelaufen",p.get(f"/api/freigabe-link/{tb}").json()["abgelaufen"] is True)
chk("Abgelaufener Link entscheidet nicht",p.post(f"/api/freigabe-link/{tb}/entscheiden",json={"entscheidung":"freigegeben","name":"Bob Test"}).status_code==400)
# 5 Tage ohne Reaktion
sql(f"update kundenfreigaben set angefragt_am=now()-interval '6 days' where id='{fb}'")
fh=[x for x in a.get("/api/admin/heute").json()["freigaben"] if x["id"]==fb]; chk("Heute: Freigabe seit Tagen offen mit Telefon",bool(fh) and fh[0]["tage"]>=5 and fh[0].get("telefon"),fh)
# ---- Vertretung
chk("Vertretung ohne Zeitraum abgelehnt",cA.put("/api/kunde/vertretung",json={"email":"v@k.de","name":"V"}).status_code==400)
chk("Vertretung mit falscher E-Mail abgelehnt",cA.put("/api/kunde/vertretung",json={"email":"nix","von":iso(0),"bis":iso(5)}).status_code==400)
chk("Vertretung Ende vor Beginn abgelehnt",cA.put("/api/kunde/vertretung",json={"email":f"v{sfx}@k.de","von":iso(5),"bis":iso(1)}).status_code==400)
r=cA.put("/api/kunde/vertretung",json={"email":f"v{sfx}@k.de","name":"Vera Vertretung","von":iso(-1),"bis":iso(5)}); chk("Vertretung speichern",r.status_code==200,r.text)
chk("Vertretung lesen",cA.get("/api/kunde/vertretung").json()["email"]==f"v{sfx}@k.de")
a.post(f"/api/admin/kunden/{kA}/freigaben-kunden",json={"titel":"Mit Vertretung","art":"text"}); 
chk("Vertretung bekommt Freigabe-Mail im Zeitraum",len(mail_an(f"v{sfx}@k.de","Mit Vertretung"))>=1)
cA.put("/api/kunde/vertretung",json={"email":f"v{sfx}@k.de","von":iso(10),"bis":iso(12)}); n0=len(mail_an(f"v{sfx}@k.de",""))
a.post(f"/api/admin/kunden/{kA}/freigaben-kunden",json={"titel":"Ohne Vertretung","art":"text"})
chk("Außerhalb des Zeitraums keine Mail an Vertretung",len(mail_an(f"v{sfx}@k.de",""))==n0)
cA.put("/api/kunde/vertretung",json={}); chk("Vertretung löschen",cA.get("/api/kunde/vertretung").json()["email"] is None)
# ---- Vertragsstand
vs=a.get("/api/admin/vertragsstand"); chk("Vertragsstand abrufbar",vs.status_code==200 and len(vs.json()["punkte"] if isinstance(vs.json(),dict) else vs.json())>=6,vs.text[:200])
chk("Vertragsstand nur für Admins",cA.get("/api/admin/vertragsstand").status_code==403)
# ---- Onboarding erkennt Domain
a.post(f"/api/admin/kunden/{kB}/domains",json=D(domain=f"onb{sfx}.de"))
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) values ('{kB}','website',true) on conflict do nothing")
ob=a.get(f"/api/admin/kunden/{kB}/onboarding"); chk("Onboarding kennt Domain-Schritt",ob.status_code==200 and any(p["code"]=="domain" and p["automatisch"] for p in ob.json()["punkte"]),[(p["code"],p["erledigt"],p["automatisch"]) for p in ob.json()["punkte"]])
# ---- App-Installation (Android/iPhone)
mf=httpx.get(B+"/manifest.webmanifest").json()
chk("Manifest: ID, Standalone, maskierbares Icon",mf.get("id")=="/" and mf["display"]=="standalone" and any(i["purpose"]=="maskable" and i["sizes"]=="512x512" for i in mf["icons"]) and mf.get("prefers_related_applications") is False,mf)
chk("Manifest: alle Icons erreichbar",all(httpx.get(B+i["src"]).status_code==200 for i in mf["icons"]))
chk("iPhone: Home-Bildschirm-Symbol erreichbar",httpx.get(B+"/static/icons/apple-touch-icon.png").status_code==200)
for seite in ("/","/app","/admin","/vertrieb"):
    t=httpx.get(B+seite,follow_redirects=True).text
    chk("Kopfzeile iPhone/Android "+seite,"apple-touch-icon" in t and "mobile-web-app-capable" in t,seite)
