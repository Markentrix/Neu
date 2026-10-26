"""KI-Fehler: Admins sehen den genauen Grund, Vertriebler nur die freundliche Meldung; Systemstatus zeigt den letzten Fehler."""
import httpx, time, sys, os
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:400])
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+1780)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Kira KI","email":f"kira{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"kira{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"KiraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"kira{sfx}@v.de","password":"KiraPasswort123456"}).status_code==200
lid=a.post("/api/admin/leads",json={"firma":f"KIFehler {sfx}","telefon":f"0511 79{sfx[-5:]}","ort":"Celle","vertriebspartner_id":pid}).json()["id"]
# Falsche Adresse des KI-Dienstes: Verbindung scheitert
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, ki
db.open_pool()
import urllib.error, io, json
e=urllib.error.HTTPError("http://x",401,"Unauthorized",{},io.BytesIO(json.dumps({"error":{"type":"authentication_error","message":"invalid x-api-key"}}).encode()))
g=ki._http_grund(e); chk("401 wird lesbar erklärt",("HTTP 401" in g) and ("authentication_error" in g) and ("invalid x-api-key" in g) and ("Einstellungen → KI" in g),g)
e=urllib.error.HTTPError("http://x",404,"Not Found",{},io.BytesIO(b"kein json")); g=ki._http_grund(e); chk("404 ohne JSON: Modell-Hinweis",("Modell" in g) and ("HTTP 404" in g),g)
g=ki.grund(ValueError("kaputt")); chk("Anderer Fehler mit Typ",g.startswith("ValueError"),g)
# Echter Fehlerweg: Mock-Dienst abschalten
import subprocess
from app import config
alt=config.ANTHROPIC_BASE_URL; config.ANTHROPIC_BASE_URL="http://127.0.0.1:9"
try: ki.fragen("sk-test","m","s",[{"role":"user","content":"x"}])
except ki.KIFehler as ex: chk("Keine Verbindung: Grund nennt Adresse",("127.0.0.1:9" in str(ex)) and ("Keine Verbindung" in str(ex)),str(ex))
except Exception as ex: chk("Keine Verbindung: KIFehler erwartet",False,repr(ex))
config.ANTHROPIC_BASE_URL=alt
chk("fehler() liefert 502-Fehler",ki.fehler(ki.KIFehler("Grund A"),{"rolle":"admin"},"Meldung.").status_code==502)
chk("Admin sieht Grund",("Grund A" in ki.fehler(ki.KIFehler("Grund A"),{"rolle":"admin"},"Meldung.").detail))
chk("Vertriebler sieht ihn nicht",ki.fehler(ki.KIFehler("Grund A"),{"rolle":"vertrieb"},"Meldung.").detail=="Meldung.")
st=a.get("/api/admin/systemstatus").json()
ki_p=[p for p in st["ampel"] if p["id"]=="ki"]
chk("Systemstatus nennt den letzten KI-Fehler",ki_p and "Grund A" in ki_p[0]["detail"] and ki_p[0]["status"]=="warn",st["ampel"])
ok=v.post("/api/vertrieb/notiz-zusammenfassen",json={"text":"Gespraech mit dem Inhaber, wollte sich melden"}).status_code
chk("Notiz-KI über Mock klappt wieder (Erfolg löscht die Warnung)",ok==200,ok)
st=a.get("/api/admin/systemstatus").json(); chk("Warnung danach weg",not [p for p in st["ampel"] if p["id"]=="ki"],[p for p in st["ampel"] if p["id"]=="ki"])
# Testknopf in den Einstellungen
r=a.post("/api/admin/einstellungen/ki-test"); chk("KI-Test gegen Mock klappt",r.status_code==200 and r.json()["ok"] is True and r.json()["modell"]=="claude-sonnet-5-5",r.text)
chk("KI-Test nur für Admins",v.post("/api/admin/einstellungen/ki-test").status_code==403)
