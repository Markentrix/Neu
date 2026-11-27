"""Neuer Kunde aus Screenshot: Felder werden gelesen, nichts wird gespeichert, Fehlerfälle."""
import httpx, base64, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
png=base64.b64encode(b"\x89PNG\r\n\x1a\n"+b"0"*400).decode()
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
n0=sql("select count(*) from kunden")
r=a.post("/api/admin/kunden/aus-bild",json={"typ":"image/png","daten":png}); j=r.json() if r.status_code==200 else {}
chk("Felder gelesen",r.status_code==200 and j["felder"]["firma"]=="Parkett Kauer" and j["felder"]["strasse"]=="Wormser Strasse 69" and j["felder"]["plz"]=="01309",r.text)
chk("Website ohne Protokoll und Pfad",j["felder"]["website"]=="parkett-kauer.de",j)
chk("Widerspruch wird gemeldet",("Radebeul" in j["hinweis"]),j)
chk("Es entsteht kein Kunde",sql("select count(*) from kunden")==n0)
chk("Kosten festgehalten",int(sql("select count(*) from kosten_log where kunden_id is null and dienst='anthropic' and menge=1290"))>=1)
chk("Falsche Kopfbytes abgelehnt",a.post("/api/admin/kunden/aus-bild",json={"typ":"image/jpeg","daten":png}).status_code==400)
chk("Kein Base64 abgelehnt",a.post("/api/admin/kunden/aus-bild",json={"typ":"image/png","daten":"!"*200}).status_code==400)
chk("Falscher Typ abgelehnt",a.post("/api/admin/kunden/aus-bild",json={"typ":"application/pdf","daten":png}).status_code==422)
chk("Ohne Anmeldung nicht möglich",httpx.post(B+"/api/admin/kunden/aus-bild",headers=H,json={"typ":"image/png","daten":png}).status_code in (401,403))
