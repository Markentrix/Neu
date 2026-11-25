"""Rechnungen nach Jahr: Übersicht mit Summen und Export für die Steuerberatung (ZIP mit PDFs und Liste)."""
import httpx, time, io, zipfile, subprocess
from pypdf import PdfReader
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
a=httpx.Client(base_url=B,headers=H,timeout=60); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29227","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890","iban":"DE89370400440532013000","bic":"COBADEFFXXX","bank":"Finom","mwst_satz":19,"kleinunternehmer":False})
sfx=str(int(time.time())+3200)
k=a.post("/api/admin/kunden",json={"firma":f"Müller & Söhne {sfx}","ansprechpartner":"Eva Müller","email":f"eva{sfx}@example.org","strasse":"Weg 1","plz":"30159","ort":"Hannover"}).json()["id"]
def rechnung(preis):
    r=a.post(f"/api/admin/kunden/{k}/belege",json={"art":"rechnung","positionen":[{"text":"Leistung","menge":1,"preis_cent":preis}]}).json()["id"]
    n=a.post(f"/api/admin/belege/{r}/ausstellen").json()["nummer"]; return r,n
r1,n1=rechnung(100000); r2,n2=rechnung(50000)
a.post(f"/api/admin/belege/{r2}/bezahlt",json={})
sid=a.post(f"/api/admin/belege/{r1}/stornieren").json()["id"]
j=time.gmtime().tm_year
u=a.get(f"/api/admin/rechnungen-jahr?jahr={j}").json()
nrs=[x["nummer"] for x in u["rechnungen"]]
chk("Übersicht nennt Rechnungen, Storno und Jahre",n1 in nrs and n2 in nrs and any(x["storno"] for x in u["rechnungen"]) and j in u["jahre"],u["jahre"])
mon=u["monate"][time.gmtime().tm_mon-1]
chk("Monatssummen: Storno mindert den Umsatz",mon["anzahl"]>=3 and mon["brutto_cent"]>=59500 and u["summe"]["brutto_cent"]==sum(m["brutto_cent"] for m in u["monate"]) and u["summe"]["bezahlt_cent"]>=59500,(mon,u["summe"]))
chk("Dateiname korrekt",f"{n1}_Rechnung_Mueller-Soehne-{sfx}.pdf" in [x["datei"] for x in u["rechnungen"]],[x["datei"] for x in u["rechnungen"]][-3:])
chk("Jahr ungültig: 400",a.get("/api/admin/rechnungen-jahr?jahr=1900").status_code==400 and a.get(f"/api/admin/belege-export.zip?jahr={j}&monat=13").status_code==400)
chk("Ohne Anmeldung gesperrt",httpx.get(B+f"/api/admin/belege-export.zip?jahr={j}",headers=H).status_code in (401,403) and httpx.get(B+f"/api/admin/rechnungen-jahr?jahr={j}",headers=H).status_code in (401,403))
r=a.get(f"/api/admin/belege-export.zip?jahr={j}"); chk("ZIP kommt",r.status_code==200 and r.headers["content-type"]=="application/zip" and f"Rechnungen-{j}.zip" in r.headers["content-disposition"],r.status_code)
z=zipfile.ZipFile(io.BytesIO(r.content)); ns=z.namelist()
chk("Ordner heißt „Rechnungen <Jahr>“ mit PDFs, Liste und Lies-mich",all(x.startswith(f"Rechnungen {j}/") for x in ns) and any(x.endswith(f"{n1}_Rechnung_Mueller-Soehne-{sfx}.pdf") for x in ns) and f"Rechnungen {j}/Rechnungsliste {j}.csv" in ns and f"Rechnungen {j}/LIES-MICH.txt" in ns,ns[:6])
pdf=[x for x in ns if n2 in x and x.endswith(".pdf")][0]; p=z.read(pdf)
chk("PDF ist E-Rechnung (ZUGFeRD)",p[:4]==b"%PDF" and "factur-x.xml" in PdfReader(io.BytesIO(p)).attachments)
liste=z.read(f"Rechnungen {j}/Rechnungsliste {j}.csv").decode("utf-8")
chk("Liste: Kopfzeile, deutsche Zahlen, Storno negativ",liste.startswith("﻿Rechnungsnummer;") and "500,00" in liste and "-1190,00" in liste.replace("-1.190,00","-1190,00") or "-1000,00" in liste,liste[:600])
chk("Liste: Storno mit Bezug und Bezahlt-Datum",f";{n1};" in liste and n2 in liste and "bezahlt" in liste,liste[-500:])
r=a.get(f"/api/admin/belege-export.zip?jahr={j}&monat={time.gmtime().tm_mon}"); z=zipfile.ZipFile(io.BytesIO(r.content))
chk("Monatsexport hat Monatsordner",r.status_code==200 and any("/%02d "%time.gmtime().tm_mon in x for x in z.namelist()),z.namelist()[:3])
r=a.get(f"/api/admin/belege-export.zip?jahr={j+1}"); z=zipfile.ZipFile(io.BytesIO(r.content))
chk("Leeres Jahr: ZIP nur mit Liste",r.status_code==200 and len([x for x in z.namelist() if x.endswith('.pdf')])==0 and any(x.endswith('.csv') for x in z.namelist()))
chk("Export steht im Protokoll",int(subprocess.run(["su","postgres","-c","psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"select count(*) from audit_log where aktion='rechnungen_export'\""],capture_output=True,text=True).stdout.strip() or 0)>=3)
