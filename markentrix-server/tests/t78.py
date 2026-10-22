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
sfx=str(int(time.time())+281)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import datetime, json, os, sys, zoneinfo
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.date.today()
kA,cA,mA=neuer_kunde("Wisa"); kB,cB,mB=neuer_kunde("Wisb")
U=f"/api/admin/kunden/{kA}/wissen"
def up(name,inhalt,ct="text/plain",c=None,pfad=None,**f):
    return (c or a).post(pfad or U+"/upload",files={"datei":(name,inhalt,ct)},data=f)
chk("Leer am Anfang",a.get(U).json()["eintraege"]==[])
r=up("Öffnungszeiten.txt","Montag bis Freitag 8 bis 17 Uhr.\nSamstag nach Absprache.\n".encode()); chk("TXT hochladen",r.status_code==200 and r.json()["schluessel"]=="Öffnungszeiten",r.text)
r=up("alt.txt","Umlaute äöü ß in Windows-Kodierung".encode("cp1252")); chk("Windows-Kodierung wird gelesen",r.status_code==200,r.text)
l=a.get(U).json()["eintraege"]; e=[x for x in l if x["schluessel"]=="alt"][0]; chk("Umlaute korrekt","äöü ß" in a.get(U+"/"+e["id"]).json()["wert"])
from pypdf import PdfWriter
import reportlab.pdfgen.canvas as cv
b=io.BytesIO(); c=cv.Canvas(b); c.drawString(72,720,"Preisliste: Reifenwechsel 49 Euro"); c.save()
r=up("Preise.pdf",b.getvalue(),"application/pdf",bereich="Preise & Leistungen"); chk("PDF hochladen, Text gelesen",r.status_code==200 and r.json()["zeichen"]>10,r.text)
l=a.get(U).json()["eintraege"]; p=[x for x in l if x["schluessel"]=="Preise"][0]; chk("Bereich bereinigt, Quelle upload, aktiv",p["bereich"]=="preise_leistungen" and p["quelle"]=="upload" and p["aktiv"],p)
chk("PDF-Text enthält den Inhalt","Reifenwechsel 49" in a.get(U+"/"+p["id"]).json()["wert"])
r=up("Preise.pdf",b.getvalue(),"application/pdf",bereich="Preise & Leistungen"); chk("Gleicher Titel ersetzt",r.json().get("ersetzt") is True and len([x for x in a.get(U).json()["eintraege"] if x["schluessel"]=="Preise"])==1,r.text)
w=PdfWriter(); w.add_blank_page(200,200); b2=io.BytesIO(); w.write(b2)
r=up("leer.pdf",b2.getvalue(),"application/pdf"); chk("PDF ohne Text: verständliche Meldung",r.status_code==422 and "kein lesbarer Text" in r.text,r.text)
r=up("kaputt.pdf",b"hallo","application/pdf"); chk("Keine echte PDF abgelehnt",r.status_code==422,r.text)
r=up("x.exe",b"MZ"); chk("Falsche Endung abgelehnt",r.status_code==422,r.text)
r=up("bin.txt",b"ab\x00cd"); chk("Binärdatei als TXT abgelehnt",r.status_code==422,r.text)
r=up("riesig.txt",b"a"*250000); chk("Zu langer Text abgelehnt",r.status_code==422,r.text)
r=up("leer.txt",b"  \n "); chk("Leere Textdatei abgelehnt",r.status_code==422,r.text)
r=a.post(U,json={"bereich":"faq","schluessel":"Parken","wert":"Kostenlose Parkplätze am Haus."}); chk("Eintrag von Hand",r.status_code==200,r.text)
r=a.patch(U+"/"+p["id"],json={"aktiv":False}); chk("Ausschalten",r.status_code==200 and a.get(U+"/"+p["id"]).json()["aktiv"] is False,r.text)
r=a.patch(U+"/"+p["id"],json={"wert":"Neuer Text"}); chk("Text ändern",r.status_code==200 and a.get(U+"/"+p["id"]).json()["wert"]=="Neuer Text",r.text)
chk("Kunde (Inhaber) hat keinen Zugriff",cA.get(U).status_code==403 and up("a.txt",b"x",c=cA).status_code==403)
chk("Anderer Kunde hat nichts davon",a.get(f"/api/admin/kunden/{kB}/wissen").json()["eintraege"]==[])
chk("Fremde Kunden-ID: Eintrag nicht ansprechbar",a.get(f"/api/admin/kunden/{kB}/wissen/{p['id']}").status_code==404 and a.delete(f"/api/admin/kunden/{kB}/wissen/{p['id']}").status_code==404)
chk("Unbekannter Kunde: 404",a.get("/api/admin/kunden/00000000-0000-0000-0000-000000000000/wissen").status_code==404)
chk("Eintrag steht in der Datenbank",int(sql(f"select count(*) from wissensbasis where kunden_id='{kA}' and aktiv"))==3)
r=a.delete(U+"/"+p["id"]); chk("Löschen",r.status_code==200 and a.get(U+"/"+p["id"]).status_code==404,r.text)
chk("Protokoll geschrieben",int(sql(f"select count(*) from audit_log where kunden_id='{kA}' and aktion like 'wissen%'"))>=5)
