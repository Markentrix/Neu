"""Digitale Visitenkarte für Admin und Vertriebler: vCard-Datei, Versand per Mail mit Anhang, Sperren, Verlauf."""
import httpx, time, re, email, email.header, json, os, sys, subprocess, datetime, zoneinfo
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
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+1750)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db
from app.db import tx
db.open_pool()
pub=httpx.Client(base_url=B,headers=H)
kid,c=neuer_kunde("Vkk")
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Visitenkarte","email":f"vera{sfx}@v.de","telefon":"0511 123456"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"vera{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"VeraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123456"}).status_code==200
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","telefon":"05141 99","website":"markentrix.de","kleinunternehmer":True,"mwst_satz":19})
chk("Kunde hat keine Visitenkarte (403)",c.get("/api/vertrieb/visitenkarte").status_code==403 and c.get("/api/admin/visitenkarte").status_code==403)
chk("Ohne Anmeldung kein Zugriff",pub.get("/api/admin/visitenkarte.vcf").status_code in (401,403) and pub.get("/api/vertrieb/visitenkarte.vcf").status_code in (401,403))
d=v.get("/api/vertrieb/visitenkarte").json()["karte"]
chk("Vertriebler: Vorgaben aus Konto und Partner",d["funktion"]=="Vertrieb" and d["telefon"]=="0511 123456" and d["email"]==f"vera{sfx}@v.de",d)
da=a.get("/api/admin/visitenkarte").json()["karte"]
chk("Admin: Vorgaben aus Firmendaten",da["web"]=="markentrix.de" and da["telefon"]=="05141 99" and da["funktion"]=="Inhaber",da)
chk("Speichern ohne Namen abgelehnt",v.put("/api/vertrieb/visitenkarte",json={**d,"anzeigename":" "}).status_code==400)
chk("Ungültige E-Mail abgelehnt",v.put("/api/vertrieb/visitenkarte",json={**d,"anzeigename":"V","email":"kein-mail"}).status_code==400)
chk("Speichern",v.put("/api/vertrieb/visitenkarte",json={**d,"anzeigename":"Vera Müller-Lüdenscheidt","mobil":"0171 5551234","funktion":"Vertrieb, Celle; Region Nord"}).status_code==200)
r=v.get("/api/vertrieb/visitenkarte.vcf"); t=r.content.decode("utf8")
chk("vCard-Datei mit passendem Typ und Dateiname",r.status_code==200 and "text/vcard" in r.headers["content-type"] and ".vcf" in r.headers["content-disposition"],r.headers)
u=t.replace("\r\n ","")
chk("vCard enthält Name, Firma, Telefone, Mail, Web, Anschrift",all(x in u for x in ("BEGIN:VCARD","VERSION:3.0","FN:Vera Müller-Lüdenscheidt","N:Müller-Lüdenscheidt;Vera","ORG:Markentrix","TEL;TYPE=CELL,VOICE:0171 5551234",f"EMAIL;TYPE=INTERNET,WORK:vera{sfx}@v.de","URL:https://markentrix.de","ADR;TYPE=WORK:;;Teststr. 1;Celle;;29221","END:VCARD")),u)
chk("Sonderzeichen im Titel maskiert, Zeilenende CRLF",r"TITLE:Vertrieb\, Celle\; Region Nord" in u and "\r\n" in t and all(len(x.encode())<=75 for x in t.split("\r\n")),u)
# Versand
def lead(tag,**kw):
    dd={"firma":f"VK{tag} {sfx}","telefon":f"0511 75{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","vertriebspartner_id":pid,"email":f"vk{tag}{sfx}@lead.de","ansprechpartner":"Herr Lead"}; dd.update(kw)
    r=a.post("/api/admin/leads",json=dd); assert r.status_code==200,r.text; return r.json()["id"]
l1=lead("a"); vor=len(mails())
r=v.post(f"/api/vertrieb/leads/{l1}/visitenkarte",json={"kanal":"mail"}); chk("Mail an Lead",r.status_code==200 and r.json()["gesendet"] is True,r.text)
time.sleep(1.5); neu=[m for m in mails()[vor:] if f"vka{sfx}@lead.de" in str(m["To"])]
chk("Mail kommt an, mit .vcf-Anhang und Reply-To",len(neu)==1 and any(p.get_content_type()=="text/vcard" and (p.get_filename() or "").endswith(".vcf") for p in neu[0].walk()) and f"vera{sfx}@v.de" in str(neu[0]["Reply-To"]),[p.get_content_type() for p in neu[0].walk()] if neu else "keine")
if neu:
    tx_=text(neu[0]); chk("Mailtext persönlich, ohne KI-Namen",("Vera Müller-Lüdenscheidt" in tx_) and ("Claude" not in tx_) and ("Anthropic" not in tx_),tx_[:300])
chk("Verlauf des Leads vermerkt den Versand",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{l1}' and inhalt like 'Visitenkarte per E-Mail gesendet%'"))==1)
chk("Anderer Empfänger möglich",v.post(f"/api/vertrieb/leads/{l1}/visitenkarte",json={"kanal":"mail","an":f"anders{sfx}@lead.de"}).json().get("an")==f"anders{sfx}@lead.de")
r=v.post(f"/api/vertrieb/leads/{l1}/visitenkarte",json={"kanal":"mail","an":"kaputt"}); chk("Ungültige Adresse abgelehnt",r.status_code==400,r.text)
chk("WhatsApp/Teilen/Datei werden nur vermerkt",all(v.post(f"/api/vertrieb/leads/{l1}/visitenkarte",json={"kanal":k}).status_code==200 for k in ("whatsapp","teilen","datei")) and int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{l1}' and inhalt like 'Visitenkarte%'"))>=5)
chk("Unbekannter Kanal abgelehnt",v.post(f"/api/vertrieb/leads/{l1}/visitenkarte",json={"kanal":"fax"}).status_code==422)
l2=lead("b",email=None); chk("Ohne E-Mail-Adresse: Hinweis statt Versand",v.post(f"/api/vertrieb/leads/{l2}/visitenkarte",json={"kanal":"mail"}).status_code==400)
l3=lead("c"); sql(f"update leads set status='gesperrt' where id='{l3}'"); chk("Gesperrter Lead: nichts gesendet",v.post(f"/api/vertrieb/leads/{l3}/visitenkarte",json={"kanal":"mail"}).status_code==400)
l4=lead("d"); sql(f"update leads set status='consent_ausstehend' where id='{l4}'"); chk("Lead ohne Einwilligung: nichts gesendet",v.post(f"/api/vertrieb/leads/{l4}/visitenkarte",json={"kanal":"mail"}).status_code==400)
l5=lead("e",vertriebspartner_id=None); chk("Fremder Lead: 404",v.post(f"/api/vertrieb/leads/{l5}/visitenkarte",json={"kanal":"mail"}).status_code==404)
chk("Admin kann an jeden Lead senden",a.post(f"/api/admin/leads/{l5}/visitenkarte",json={"kanal":"mail"}).json().get("gesendet") is True)
chk("Admin-Datei",a.get("/api/admin/visitenkarte.vcf").status_code==200 and b"BEGIN:VCARD" in a.get("/api/admin/visitenkarte.vcf").content)
chk("Vertriebler erreicht Admin-Routen nicht",v.get("/api/admin/visitenkarte").status_code==403 and v.post(f"/api/admin/leads/{l1}/visitenkarte",json={"kanal":"datei"}).status_code==403)
