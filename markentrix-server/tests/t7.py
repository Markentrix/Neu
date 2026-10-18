import httpx
B="http://localhost:8000"; H={"X-MK":"1"}
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else i)
u0=a.get("/api/admin/uebersicht").json()
k=a.post("/api/admin/kunden",json={"firma":"Referenz Schmiede","referenzkunde":True,"referenz_leistung":"Website + Agent","paket_code":"KI_ONE"}).json()
d=a.get(f"/api/admin/kunden/{k['id']}").json()["kunde"]; chk("flag gespeichert",d["referenzkunde"] and d["referenz_leistung"]=="Website + Agent",d)
r=a.post(f"/api/admin/kunden/{k['id']}/buchungen",json={"produkt_code":"KI_ONE","rabatt_cent":500}); chk("buchung",r.status_code==200,r.text)
b=a.get(f"/api/admin/kunden/{k['id']}").json()["buchungen"][0]; chk("preis 0",b["monatlich_cent"]==0 and b["einrichtung_cent"]==0 and b["rabatt_grund"]=="Referenzkunde",b)
a.patch(f"/api/admin/buchungen/{b['id']}",json={"status":"aktiv"})
u1=a.get("/api/admin/uebersicht").json(); chk("MRR unverändert",u1["monatlich_cent"]==u0["monatlich_cent"] and u1["referenzkunden"]==u0["referenzkunden"]+1,u1)
lst=a.get("/api/admin/kunden?q=Referenz").json(); chk("liste flag",lst[0]["referenzkunde"] is True)
r=a.patch(f"/api/admin/kunden/{k['id']}",json={"referenzkunde":False}); chk("zurück zu normal",r.status_code==200 and not a.get(f"/api/admin/kunden/{k['id']}").json()["kunde"]["referenzkunde"])
a.patch(f"/api/admin/kunden/{k['id']}",json={"referenzkunde":True,"referenz_nennen_erlaubt":True})
# Provision: Referenzkunde einem Partner zuordnen → keine Zeile
pid=a.post("/api/admin/vertrieb/partner",json={"name":"Test Partner t7","email":"t7@v.de","status":"aktiv"}).json()["id"]
print(a.put(f"/api/admin/kunden/{k['id']}/partner",json={"partner_id":pid}).status_code)
n=a.post("/api/admin/kunden",json={"firma":"Normal GmbH","paket_code":"KI_ONE"}).json(); a.put(f"/api/admin/kunden/{n['id']}/partner",json={"partner_id":pid}); bb=a.post(f"/api/admin/kunden/{n['id']}/buchungen",json={"produkt_code":"KI_ONE","beginn":"2026-08-01"}).json(); a.patch(f"/api/admin/buchungen/{bb['id']}",json={"status":"aktiv"})
b2=a.get(f"/api/admin/kunden/{k['id']}").json()["buchungen"][0]
print(a.post(f"/api/admin/kunden/{k['id']}/buchungen",json={"produkt_code":"KI_ONE","beginn":"2026-08-01"}).status_code)
a.post("/api/admin/provisionsregeln/1/freigeben")
r=a.post("/api/admin/vertrieb/provisionen/berechnen",json={"monat":"2026-10","vorschau":True}).json()
chk("keine Provision für Referenz",all(z["firma"]!="Referenz Schmiede" for z in r["zeilen"]),r)
chk("Normalkunde schon (Gegentest)",any(z["firma"]=="Normal GmbH" for z in r["zeilen"]),r)
