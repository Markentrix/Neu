"""Sicherheits-Sweep: jede API-Route ohne Anmeldung, mit Kundenrechten und Vertrieblerrechten; Header; Cookies; Abhängigkeiten."""
import httpx, sys, re, time, email, subprocess
sys.path.insert(0,"/home/claude/markentrix-server/portal")
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:500])
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.5)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
os_env=__import__("os").environ
from app.main import app
routen=[(m.upper(),p) for p,d in app.openapi()["paths"].items() for m in d if m.upper() in("GET","POST","PUT","PATCH","DELETE") and p.startswith("/api/")]
chk("Routen gefunden",len(routen)>200,len(routen))
def fuellen(p): return re.sub(r"\{[^}]+\}","00000000-0000-0000-0000-000000000000",p)
# Öffentliche Routen (bewusst ohne Anmeldung): jede muss hier ausdrücklich stehen
OEFFENTLICH=re.compile(r"^/api/(login|logout|einladung|passwort|public/|webhook/|buchen|angebot/|anmelde|recht$|loginlink|2fa/login|zweifaktor/login|health)")
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.post("/api/admin/kunden",json={"firma":"Sweep GmbH","ansprechpartner":"T","email":"sweep@k.de","telefon":"1","strasse":"W 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True})
httpx.post(B+"/api/einladung",headers=H,json={"token":token("sweep@k.de"),"password":"InhaberPasswort1"})
pid=a.post("/api/admin/vertrieb/partner",json={"name":"V","email":"v@sweep.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token("v@sweep.de"),"password":"VeraPasswort123"})
k=httpx.Client(base_url=B,headers=H); assert k.post("/api/login",json={"email":"sweep@k.de","password":"InhaberPasswort1"}).status_code==200
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":"v@sweep.de","password":"VeraPasswort123"}).status_code==200
anon=httpx.Client(base_url=B,headers=H)
offen=[];zuviel_k=[];zuviel_v=[];fehler500=[]
for m,p in routen:
    url=fuellen(p); geschuetzt=not OEFFENTLICH.match(p)
    for nm,cl in (("anon",anon),("kunde",k),("vertrieb",v)):
        if m=="DELETE" and "logout" in p: continue
        try: r=cl.request(m,url,json={} if m!="GET" else None)
        except Exception as e: fehler500.append((m,p,str(e)[:50])); continue
        if r.status_code>=500: fehler500.append((m,p,nm,r.status_code))
        if nm=="anon" and geschuetzt and r.status_code not in(401,403,404,405): offen.append((m,p,r.status_code))
        if nm=="kunde" and p.startswith("/api/admin/") and r.status_code not in(401,403,404,405): zuviel_k.append((m,p,r.status_code))
        if nm=="kunde" and p.startswith("/api/vertrieb/") and r.status_code not in(401,403,404,405): zuviel_k.append((m,p,r.status_code))
        if nm=="vertrieb" and p.startswith("/api/admin/") and r.status_code not in(401,403,404,405): zuviel_v.append((m,p,r.status_code))
        if nm=="vertrieb" and p.startswith("/api/kunde/") and r.status_code not in(401,403,404,405): zuviel_v.append((m,p,r.status_code))
    time.sleep(0.02)
chk("Keine geschützte Route ohne Anmeldung erreichbar",not offen,offen[:8])
chk("Kunde kommt an keine Admin-/Vertriebs-Route",not zuviel_k,zuviel_k[:8])
chk("Vertriebler kommt an keine Admin-/Kunden-Route",not zuviel_v,zuviel_v[:8])
chk("Keine Route antwortet mit Serverfehler (5xx) auf leere Eingabe",not fehler500,fehler500[:10])
# CSRF: Änderung ohne Header
r=httpx.post(B+"/api/admin/leads",json={"firma":"x"}); chk("Änderung ohne X-MK-Header abgewiesen",r.status_code==403)
r=a.post("/api/admin/leads",json={"firma":"x"},headers={"Origin":"https://evil.example"}); chk("Fremde Herkunft abgewiesen",r.status_code==403)
# Header
for pfad in ("/","/admin","/app","/vertrieb","/static/js/common.js","/api/me"):
    r=httpx.get(B+pfad); h=r.headers
    chk(f"Sicherheits-Header {pfad}","content-security-policy" in h and h.get("x-content-type-options")=="nosniff" and h.get("x-frame-options")=="DENY" and h.get("referrer-policy")=="no-referrer",dict(h))
csp=httpx.get(B+"/").headers["content-security-policy"]; chk("CSP ohne unsafe-inline/eval für Skripte","script-src 'self'" in csp and "unsafe-eval" not in csp and not re.search(r"script-src[^;]*unsafe-inline",csp),csp)
# Cookie
r=httpx.post(B+"/api/login",headers=H,json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()}); c=r.headers.get("set-cookie","").lower()
chk("Sitzungs-Cookie HttpOnly + SameSite","httponly" in c and "samesite" in c,c)
# Brute-Force-Bremse
st=[httpx.post(B+"/api/login",headers=H,json={"email":"nobody@x.de","password":"falsch"+str(i)}).status_code for i in range(15)]
chk("Login-Bremse greift bei Fehlversuchen",429 in st,st)
# Keine Geheimnisse in Antworten
r=a.get("/api/admin/einstellungen/zahlung"); chk("Einstellungen liefern keine Klartext-Geheimnisse",not re.search(r"-----BEGIN|api_key\"\s*:\s*\"sk-",r.text))
# SQL-Injection-Stichprobe
for q in ("' OR '1'='1","\"; DROP TABLE kunden;--","%' UNION SELECT 1--"):
    r=a.get("/api/admin/suche",params={"q":q}); r2=a.get("/api/admin/kunden",params={"q":q}); chk("Injection-Stichprobe: "+q[:12],r.status_code==200 and r2.status_code==200,(r.status_code,r2.status_code))
chk("Tabelle kunden noch da",subprocess.run(["su","postgres","-c","psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c 'select count(*) from kunden'"],capture_output=True,text=True).stdout.strip().isdigit())
# Fehler-Alarm: unbehandelter Fehler erzeugt Alarm + Push-Eintrag für Admins
import asyncio
from app import db, main as m
db.open_pool()
class Fake:
    method="GET"
    class url: path="/api/test-fehler"
asyncio.run(m.unbehandelt(Fake(),RuntimeError("Testfehler")))
time.sleep(1)
sq=lambda q: subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
chk("Unbehandelter Fehler → Alarm im System",sq("select count(*) from alarme where titel like '%test-fehler%'")=="1")
chk("Unbehandelter Fehler → Glocke der Admins",int(sq("select count(*) from benachrichtigungen where tag='fehler'") or 0)>=1)
