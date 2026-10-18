import httpx, time
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"C W","strasse":"T 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","iban":"DE89370400440532013000","steuernummer":"12/345/67890","zahlungsziel_tage":14,"mwst_satz":19})
sfx=str(int(time.time()))
k=a.post("/api/admin/kunden",json={"firma":"Abgl GmbH "+sfx,"ansprechpartner":"E","email":f"ab{sfx}@e.de","telefon":"0511","strasse":"W 2","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json(); kid=k["id"]
def rech(cent):
    r=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","betreff":"T","positionen":[{"text":"L","menge":1,"einheit":"Stk","preis_cent":cent}]}).json()["id"]
    j=a.post(f"/api/admin/belege/{r}/ausstellen",json={}).json(); return r,j["nummer"]
r1,n1=rech(10000); r2,n2=rech(20000); r3,n3=rech(30000)
brutto=lambda c: f"{c*1.19/100:.2f}".replace(".",",")
csv=("Kontoauszug;;;\nBuchungstag;Valuta;Verwendungszweck;Betrag\n"
 f"15.10.2026;15.10.2026;Rechnung {n1} Danke;{brutto(10000)}\n"
 f"16.10.2026;16.10.2026;Zahlung {n2};10,00\n"
 f"17.10.2026;17.10.2026;Miete Oktober;-500,00\n"
 f"18.10.2026;18.10.2026;Spende;25,00\n")
r=a.post("/api/admin/belege/zahlungsabgleich",json={"csv":csv}); j=r.json()
chk("vorschau 200",r.status_code==200,r.text)
chk("1 sicher",len(j["sicher"])==1 and j["sicher"][0]["nummer"]==n1,j)
chk("1 abweichend",len(j["abweichend"])==1 and j["abweichend"][0]["nummer"]==n2,j)
chk("1 unbekannt (Ausgang ignoriert)",len(j["unbekannt"])==1,j)
st=lambda i: next(x for x in a.get(f"/api/admin/kunden/{kid}/belege").json() if x["id"]==i)["status"]
chk("Vorschau bucht nicht",st(r1)!="bezahlt")
j=a.post("/api/admin/belege/zahlungsabgleich",json={"csv":csv,"anwenden":True}).json()
chk("gebucht 1",j["gebucht"]==1,j)
chk("r1 bezahlt",st(r1)=="bezahlt"); chk("r2 offen",st(r2)!="bezahlt")
j=a.post("/api/admin/belege/zahlungsabgleich",json={"csv":csv,"anwenden":True}).json()
chk("zweiter Lauf bucht nichts",j["gebucht"]==0,j)
chk("kaputte CSV 400",a.post("/api/admin/belege/zahlungsabgleich",json={"csv":"a;b\n1;2"}).status_code==400)
c2=f"Datum,Betrag,Buchungstext\n2026-10-18,\"{brutto(30000)}\",\"Re {n3.lower()}\"\n"
j=a.post("/api/admin/belege/zahlungsabgleich",json={"csv":c2}).json()
chk("Komma-CSV + Kleinschreibung",len(j.get("sicher",[]))==1,j)
c = httpx.Client(base_url=B,headers=H)
chk("ohne Login 401",c.post("/api/admin/belege/zahlungsabgleich",json={"csv":csv}).status_code in (401,403))
