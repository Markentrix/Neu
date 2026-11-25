"""Rechnungs-PDF: Entwurf zeigt die gewählte Zahlungsfrist, Kopfblock steht weiter rechts."""
import httpx, time, subprocess, datetime
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19,"steuernummer":"12/345/67890","zahlungsziel_tage":14})
sfx=str(int(time.time())+4100)
k=a.post("/api/admin/kunden",json={"firma":f"Frist {sfx}","ansprechpartner":"Tina Test","email":f"frist{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle"}).json()["id"]
pos=[{"text":"Pflege","menge":1,"einheit":"","preis_cent":2990}]
def pdf_text(bid):
    r=a.get(f"/api/admin/belege/{bid}/pdf"); open("/var/tmp/b139.pdf","wb").write(r.content)
    return " ".join(subprocess.run(["pdftotext","-layout","/var/tmp/b139.pdf","-"],capture_output=True,text=True).stdout.split())
def neu(tage):
    r=a.post(f"/api/admin/kunden/{k}/belege",json={"art":"rechnung","betreff":"Test","positionen":pos,"zahlungsziel_tage":tage}); assert r.status_code==200,r.text
    return r.json()["id"]
heute=datetime.date.today()
for tage in (7,0,None):
    bid=neu(tage); t=pdf_text(bid)
    if tage==0: chk("Entwurf: sofort zahlbar",("Zahlbar sofort" in t) or ("sofort, ohne Abzug" in t),t[:400])
    else:
        soll=(heute+datetime.timedelta(days=tage if tage is not None else 14)).strftime("%d.%m.%Y")
        chk(f"Entwurf mit Frist {tage if tage is not None else 'Standard (14)'}: Zahlbar bis {soll}","Zahlbar bis" in t and soll in t,t[:500])
# geänderte Frist im Entwurf wird übernommen
bid=neu(7); a.put(f"/api/admin/belege/{bid}",json={"betreff":"Test","positionen":pos,"zahlungsziel_tage":30})
soll=(heute+datetime.timedelta(days=30)).strftime("%d.%m.%Y"); chk("Geänderte Frist (30 Tage) erscheint im PDF",soll in pdf_text(bid))
# Kopfblock weiter rechts: x-Position von „Kundennummer“ per bbox
x=subprocess.run(["pdftotext","-bbox","/var/tmp/b139.pdf","-"],capture_output=True,text=True).stdout
import re
m=re.search(r'xMin="([\d.]+)"[^>]*>Kundennummer<',x); chk("Kundennummer steht rechts (x > 280 pt)",bool(m) and float(m.group(1))>280,m and m.group(1))
