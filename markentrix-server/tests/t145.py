"""Eigene Website (markentrix.de) im Portal: interner Eintrag ohne Login, unsichtbar in Listen, Live-Bewertungen über die Website-API."""
import httpx, time, json, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/places",json={"api_key":"places-test"})
r=a.get("/api/admin/eigene-seite"); chk("Vorher nicht eingerichtet",r.status_code==200 and r.json()["eingerichtet"] is False,r.text)
chk("Ungültige Domain abgelehnt",a.put("/api/admin/eigene-seite",json={"domain":"kein domain!"}).status_code==400)
chk("Ungültige Place-ID abgelehnt",a.put("/api/admin/eigene-seite",json={"place_id":"x y!"}).status_code==400)
chk("Live ohne Place-ID abgelehnt",a.put("/api/admin/eigene-seite",json={"aktiv":True}).status_code==400)
dom=f"eigene{int(time.time())}.de"
r=a.put("/api/admin/eigene-seite",json={"domain":dom,"place_id":"ChIJtestplace12345","aktiv":True}); chk("Einrichten",r.status_code==200 and r.json()["eingerichtet"] and r.json()["site_id"].startswith("mk_") and "data-site=" in r.json()["einbau"],r.text)
sid=r.json()["site_id"]; kid=r.json()["kunden_id"]
a.put("/api/admin/eigene-seite",json={"domain":dom,"place_id":"ChIJtestplace12345","aktiv":True})
chk("Nur ein interner Eintrag, auch nach erneutem Speichern",sql("SELECT count(*) FROM kunden WHERE status='intern'")=="1" and sql(f"SELECT count(*) FROM domains WHERE kunden_id='{kid}'")=="1")
chk("Nicht in der Kundenliste",kid not in [k["id"] for k in a.get("/api/admin/kunden").json()])
chk("Nicht in der Kunden-Ampel",kid not in [k["id"] for k in a.get("/api/admin/kunden-ampel").json()["kunden"]])
chk("Ohne Login (kein Benutzer)",sql(f"SELECT count(*) FROM benutzer WHERE kunden_id='{kid}'")=="0")
P=httpx.Client(base_url=B)
r=P.get(f"/site/{sid}/bewertungen",headers={"Origin":"https://"+dom}); d=r.json()
chk("Website-API liefert Live-Bewertungen für die eigene Seite",r.status_code==200 and d.get("aktiv") and d.get("quelle")=="google" and d["anzahl"]==128 and d["sterne"]==4.7,r.text)
chk("Fremde Herkunft abgelehnt",P.get(f"/site/{sid}/bewertungen",headers={"Origin":"https://boese.de"}).status_code==403)
chk("Zustand zeigt Google-Zahlen",a.get("/api/admin/eigene-seite").json()["google"]["anzahl"]==128)
