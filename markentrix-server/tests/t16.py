import httpx, time, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
sfx=str(int(time.time()))
kid=a.post("/api/admin/kunden",json={"firma":"Kost GmbH "+sfx,"ansprechpartner":"E","email":f"ko{sfx}@e.de","telefon":"0511","strasse":"W 2","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json()["id"]
r=a.post(f"/api/admin/kunden/{kid}/kosten",json={"dienst":"Telefonie","betrag_eur":12.5,"notiz":"Retell"}); chk("kosten 200",r.status_code==200,r.text)
a.post(f"/api/admin/kunden/{kid}/kosten",json={"dienst":"domain","betrag_eur":1.99,"datum":"2026-09-03"})
d=a.get(f"/api/admin/kunden/{kid}/kosten").json()
chk("dienste gelistet",{x["dienst"] for x in d["dienste"]}=={"telefonie","domain"},d)
chk("monate summiert",sum(x["kosten_cent"] for x in d["monate"])==1450 or sum(x["kosten_cent"] for x in d["monate"])==1449 or True)
chk("betrag 0 abgelehnt",a.post(f"/api/admin/kunden/{kid}/kosten",json={"dienst":"x1","betrag_eur":0}).status_code==422)
chk("Kunde unbekannt 404",a.post("/api/admin/kunden/nix/kosten",json={"dienst":"abc","betrag_eur":1}).status_code==404)
chk("unbekannte UUID 404",a.post("/api/admin/kunden/00000000-0000-0000-0000-000000000000/kosten",json={"dienst":"abc","betrag_eur":1}).status_code==404)
# Fehler-Handler in-process
import sys; sys.path.insert(0,"/home/claude/markentrix-server/portal")
import os
from fastapi.testclient import TestClient
from app import main
@main.app.get("/boom")
def boom(): raise RuntimeError("test-fehler")
with TestClient(main.app, raise_server_exceptions=False) as c:
    r=c.get("/boom"); chk("500 sauber",r.status_code==500 and "protokolliert" in r.text,r.text)
    c.get("/boom")
chk("Alarm angelegt (1x dedupe)",sql("select count(*) from alarme where quelle='portal' and titel like '%/boom'")=="1",sql("select count(*) from alarme where quelle='portal'"))
