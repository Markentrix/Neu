import httpx, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
for rid in (1,4): a.post(f"/api/admin/provisionsregeln/{rid}/freigeben")
p=a.post("/api/admin/vertrieb/partner",json={"name":"Paul Prov2","firma":"PP","email":"pp@x.de","status":"aktiv"}).json(); pid=p["id"]
k=a.post("/api/admin/kunden",json={"firma":"Prov Kunde GmbH","paket_code":"KI_ONE"}).json(); kid=k["id"]
a.put(f"/api/admin/kunden/{kid}/partner",json={"partner_id":pid})
bb=a.post(f"/api/admin/kunden/{kid}/buchungen",json={"produkt_code":"KI_ONE","beginn":"2026-08-01"}).json(); a.patch(f"/api/admin/buchungen/{bb['id']}",json={"status":"aktiv"})
r=a.post("/api/admin/vertrieb/provisionen/berechnen",json={"monat":"2026-09","vorschau":False}).json(); chk("berechnet",r["angelegt"]>=1,r)
r2=a.post("/api/admin/vertrieb/provisionen/berechnen",json={"monat":"2026-09","vorschau":False}).json(); chk("idempotent",r2["angelegt"]==0,r2)
d=a.get(f"/api/admin/vertrieb/partner/{pid}").json(); pr=[x for x in d["provisionen"] if x["kundennummer"]==k.get("kundennummer",x["kundennummer"])]; chk("art in liste",d["provisionen"] and d["provisionen"][0]["art"]=="laufend",d["provisionen"][:1])
prid=d["provisionen"][0]["id"]
chk("rückbuchung vor Auszahlung abgelehnt",a.post(f"/api/admin/vertrieb/provisionen/{prid}/rueckbuchung",json={"monat":"2026-10"}).status_code==400)
for st in ("freigegeben","ausgezahlt"): a.post(f"/api/admin/vertrieb/provisionen/{prid}/status",json={"status":st})
r=a.post(f"/api/admin/vertrieb/provisionen/{prid}/rueckbuchung",json={"monat":"2026-10","notiz":"Zahlungsausfall"}); chk("rückbuchung",r.status_code==200,r.text)
chk("rückbuchung doppelt",a.post(f"/api/admin/vertrieb/provisionen/{prid}/rueckbuchung",json={"monat":"2026-10"}).status_code==409)
print(sql("select art,betrag_cent,status from provisionen order by art"))
chk("rückbuchung negativ",int(sql(f"select betrag_cent from provisionen where art='rueckbuchung' and vertriebspartner_id='{pid}'"))<0)
r=a.post("/api/admin/vertrieb/provisionen/verlaengerung",json={"buchung_id":bb["id"],"monat":"2026-10"}); chk("verlängerung",r.status_code==200 and r.json()["betrag_cent"]>0,r.text)
chk("verlängerung doppelt",a.post("/api/admin/vertrieb/provisionen/verlaengerung",json={"buchung_id":bb["id"],"monat":"2026-10"}).status_code==409)
chk("verlängerung buchung unbekannt",a.post("/api/admin/vertrieb/provisionen/verlaengerung",json={"buchung_id":"nix","monat":"2026-10"}).status_code==404)
r=a.get(f"/api/admin/vertrieb/{pid}/abrechnung/2026-10"); chk("abrechnung pdf admin",r.status_code==200 and r.content[:4]==b"%PDF",r.text[:200]); open("abrechnung.pdf","wb").write(r.content)
chk("abrechnung falscher monat",a.get(f"/api/admin/vertrieb/{pid}/abrechnung/2026-13").status_code in (400,404))
chk("abrechnung falsche id",a.get("/api/admin/vertrieb/nix/abrechnung/2026-10").status_code==404)
# Nachlauf: Partner beenden
a.patch(f"/api/admin/vertrieb/partner/{pid}",json={"status":"beendet"})
chk("beendet_am gesetzt",sql(f"select beendet_am is not null from vertriebspartner where id='{pid}'")=="t")
r=a.post("/api/admin/vertrieb/provisionen/berechnen",json={"monat":"2026-11","vorschau":True}).json(); chk("nachlauf rechnet weiter",any(z["pid"]==pid for z in r["zeilen"]),r)
r=a.post("/api/admin/vertrieb/provisionen/berechnen",json={"monat":"2027-06","vorschau":True}).json(); chk("nach Nachlauf keine Provision",all(z["pid"]!=pid for z in r["zeilen"]),r)
a.patch(f"/api/admin/vertrieb/partner/{pid}",json={"status":"aktiv"}); chk("reaktiviert löscht beendet_am",sql(f"select beendet_am is null from vertriebspartner where id='{pid}'")=="t")
# KI-Kosten
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
chk("preise gespeichert",a.get("/api/admin/einstellungen").json()["ki"]["preis_aus_eur"]==15)
sql(f"insert into kosten_log (kunden_id,dienst,einheit,menge,kosten_cent) values ('{kid}','anthropic','tokens',1000,12.5)")
c=a.get(f"/api/admin/kunden/{kid}/kosten").json(); chk("kosten api",c["monate"] and c["monate"][0]["kosten_cent"]>=12 and c["umsatz_monat_cent"]>0,c)
chk("kosten 404",a.get("/api/admin/kunden/nix/kosten").status_code==404)
# CSV
r=a.get("/api/admin/belege-export.csv"); chk("csv",r.status_code==200 and "Rechnungsnummer" in r.text,r.text[:200])
chk("csv datum falsch",a.get("/api/admin/belege-export.csv?von=quatsch").status_code==400)
# Vertriebler-Sicht
chk("vertrieb ohne login",httpx.get(B+"/api/vertrieb/abrechnung/2026-10").status_code in (401,403))
chk("kunde-Zugriff verboten",a.get("/api/vertrieb/abrechnung/2026-10").status_code==403)
