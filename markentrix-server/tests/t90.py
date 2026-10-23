import httpx, time, subprocess, asyncio, sys, json
sys.path.insert(0,"/home/claude/markentrix-server/portal")
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H,timeout=40); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
from app import fehlerhilfe as f
# ---- Erkennung: Text -> richtige Regel
FAELLE=[("SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')","smtp_login"),
 ("SMTPServerDisconnected: Connection unexpectedly closed","smtp_verbindung"),
 ("SMTPRecipientsRefused: {'x@y.de': (550, b'Recipient address rejected')}","smtp_empfaenger"),
 ("OSError: [Errno 28] No space left on device","platte_voll"),
 ("psycopg.errors.UniqueViolation: duplicate key value violates unique constraint","eindeutig"),
 ('psycopg.errors.UndefinedTable: relation "neu_tabelle" does not exist',"migration"),
 ("InsufficientPrivilege: permission denied for table x","rechte"),
 ("httpx.ReadTimeout: timed out","zeitueberschreitung"),
 ("ssl.SSLCertVerificationError: CERTIFICATE_VERIFY_FAILED","tls"),
 ("cryptography.fernet.InvalidToken","einstellungen_defekt"),
 ("anthropic.AuthenticationError: 401 invalid x-api-key authentication_error","ki_schluessel"),
 ("Error 429 rate_limit_error","ki_limit"),
 ("socket.gaierror: [Errno -2] Name or service not known","dns"),
 ("FileNotFoundError: [Errno 2] No such file or directory: '/srv/sites/x'","datei_fehlt"),
 ("PermissionError: [Errno 13] Permission denied: '/srv/sites'","dateirechte"),
 ("psycopg.OperationalError: connection failed: Connection refused","datenbank_verbindung"),
 ("Hintergrundjobs melden sich nicht","jobs_still"),
 ("ConnectionRefusedError: [Errno 111] Connection refused","verbindung_verweigert"),
 ("SMTP ConnectionRefusedError: [Errno 111]","smtp_verbindung")]
for text_,erwartet in FAELLE:
    e=f.erklaeren(text_); chk(f"Erkannt: {erwartet}",e["id"]==erwartet and e["bekannt"] and e["schritte"] and e["ursache"],(e["id"],text_[:60]))
e=f.erklaeren("völlig unbekannter Murks xyz"); chk("Unbekannter Fehler: allgemeiner Hinweis mit Schritten",e["id"]=="allgemein" and not e["bekannt"] and len(e["schritte"])>=2,e)
chk("Wort „Zoom“/„Room“ löst keine Speicher-Regel aus",f.erklaeren("Zoom Room geplant")["id"]=="allgemein")
chk("Kurztipp nur bei erkannten Fehlern",f.kurztipp("Murks xyz")=="" and f.kurztipp("SMTPAuthenticationError 535").startswith("Tipp: "))
# ---- Geheimnisse werden entfernt
b=f.bereinigen("login failed password=Geheim123! und api_key: sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF Bearer abcdef123456")
chk("Passwort, Schlüssel und Token bereinigt","Geheim123" not in b and "abcdefghijklmnopqrstuvwxyz0123456789" not in b and "abcdef123456" not in b and "***" in b,b)
chk("Alle Regeln haben Titel, Ursache und Schritte",all(r[2] and r[3] and r[4] for r in f.REGELN))
# ---- Alarm mit Erklärung, Sperre, Fehler-Nr
from app import db
db.open_pool()
n0=int(sql("select count(*) from alarme where quelle='test:fh'"))
nr1=f.melden("test:fh",Exception("SMTPAuthenticationError 535 password=Streng123"),push_senden=False)
nr2=f.melden("test:fh",Exception("SMTPAuthenticationError 535 nochmal"),push_senden=False)
chk("Alarm angelegt, Wiederholung gesperrt",int(sql("select count(*) from alarme where quelle='test:fh'"))==n0+1 and nr1!=nr2)
d=json.loads(sql("select details from alarme where quelle='test:fh' order by id desc limit 1"))
chk("Alarm enthält Fehler-Nr, Erklärung und bereinigten Text",d["fehler_nr"]==nr1 and d["erklaerung"]["id"]=="smtp_login" and "Streng123" not in d["text"],d)
nr3=f.melden("test:fh",Exception("Murks xyz"),push_senden=False); chk("Andere Fehlerart derselben Quelle wird nicht unterdrückt",int(sql("select count(*) from alarme where quelle='test:fh'"))==n0+2)
# ---- Schnittstellen
r=a.get("/api/admin/fehlerhilfe"); chk("Liste der Fehler mit Erklärung",r.status_code==200 and any(x["fehler_nr"]==nr1 and x["erklaerung"]["titel"] for x in r.json()),r.text[:200])
r=a.post("/api/admin/fehlerhilfe/erklaeren",json={"text":"SMTPAuthenticationError: (535, 'bad')"}); chk("Fehler erklären (Eingabe)",r.status_code==200 and r.json()["id"]=="smtp_login" and r.json()["schritte"],r.text)
chk("Erklären: zu kurzer Text abgelehnt",a.post("/api/admin/fehlerhilfe/erklaeren",json={"text":"x"}).status_code==422)
r=a.post("/api/admin/fehlerhilfe/pruefen",json={}); j=r.json(); ids={p["id"] for p in j.get("punkte",[])}
chk("Prüfung liefert Datenbank, Platte, Einstellungen, Mail, Jobs",r.status_code==200 and {"db","platte","geheimnis","mail","jobs"}<=ids,r.text[:300])
chk("Jeder Problempunkt hat einen Vorschlag",all(p["ok"] or (p["vorschlag"] and p["vorschlag"]["schritte"]) for p in j["punkte"]),j)
chk("Datenbank-Punkt ist ok",[p for p in j["punkte"] if p["id"]=="db"][0]["ok"])
# Mail-Prüfung mit unerreichbarem Server -> Vorschlag
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":1,"sicherung":"keine","absender":"info@markentrix.de"})
j=a.post("/api/admin/fehlerhilfe/pruefen",json={}).json(); m=[p for p in j["punkte"] if p["id"]=="mail"][0]
chk("Mail nicht erreichbar: Problem mit Vorschlag",(not m["ok"]) and m["vorschlag"]["id"]=="smtp_verbindung" and not j["ok"],m)
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
j=a.post("/api/admin/fehlerhilfe/pruefen",json={}).json(); m=[p for p in j["punkte"] if p["id"]=="mail"][0]; chk("Mail erreichbar: Punkt ok",m["ok"],m)
# Rechte: ohne Anmeldung / als Kunde nicht erreichbar
chk("Ohne Anmeldung gesperrt",httpx.get(B+"/api/admin/fehlerhilfe",headers=H).status_code in (401,403) and httpx.post(B+"/api/admin/fehlerhilfe/erklaeren",headers=H,json={"text":"abc def"}).status_code in (401,403))
# ---- 500er-Antwort nennt die Fehler-Nr
from app import main as mn
class Fake:
    method="GET"
    class url: path="/api/test-fehlerhilfe"
r=asyncio.run(mn.unbehandelt(Fake(),RuntimeError("psycopg UndefinedTable relation x does not exist"))); body=json.loads(r.body)
nr=body["detail"].split("Nr. ")[-1].rstrip(").")
chk("500-Antwort nennt Fehler-Nr",r.status_code==500 and len(nr)==6,body)
time.sleep(0.5)
chk("Alarm dazu mit Migrations-Vorschlag",sql(f"select details->'erklaerung'->>'id' from alarme where details->>'fehler_nr'='{nr}'")=="migration")
# ---- Job-Absturz erzeugt Alarm mit Erklärung
from app import jobs
def kaputt(cfg): raise RuntimeError("No space left on device")
jobs._lauf(kaputt,{}); time.sleep(0.5)
chk("Job-Absturz → Alarm mit Platte-voll-Erklärung",sql("select details->'erklaerung'->>'id' from alarme where quelle='job:kaputt' order by id desc limit 1")=="platte_voll")
# ---- Website-Ereignis bekommt Tipp
from app import sitedienste as sd
k=a.post("/api/admin/kunden",json={"firma":f"Fehlerhilfe {int(time.time())}","ansprechpartner":"T","email":f"fh{int(time.time())}@k.de","telefon":"0511","strasse":"W 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json()
kid=k.get("id")
if kid:
    sd.ereignis(kid,"kontakt",False,"Versand fehlgeschlagen. SMTPAuthenticationError: (535, 'x')")
    h_=sql(f"select hinweis from website_ereignisse where kunden_id='{kid}' order by zeit desc limit 1")
    chk("Ereignis im Kundenportal enthält Tipp",h_ is not None and "Tipp:" in h_,h_)
# ---- Oberfläche
from playwright.async_api import async_playwright
async def ui():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":390,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]
        pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=500 else None)
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",ADMPW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        for breite in (390,1280):
            await pg.set_viewport_size({"width":breite,"height":900}); await pg.goto(B+"/admin#uebersicht"); await pg.reload()
            await pg.wait_for_selector("h2:has-text('Fehler-Hilfe')",timeout=10000); chk(f"Fehler-Hilfe-Karte @{breite} sichtbar",True)
            await pg.fill("textarea[aria-label='Fehlermeldung']","SMTPAuthenticationError: (535, 'Username and Password not accepted')")
            await pg.click("button:has-text('Fehler erklären')"); await pg.wait_for_selector("text=Mail-Anmeldung abgelehnt",timeout=8000); chk(f"Erklärung erscheint @{breite}",True)
            await pg.click("button:has-text('Jetzt alles prüfen')"); await pg.wait_for_selector("b:text-is('Datenbank')",timeout=20000); chk(f"Prüfung zeigt Ergebnis @{breite}",True)
            chk(f"Letzte Fehler mit Erklärung @{breite}",await pg.locator("summary:has-text('Nr. ')").count()>=1)
            ueber=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk(f"Kein seitliches Überlaufen @{breite}",ueber<=0,ueber)
        await pg.goto(B+"/admin#compliance"); await pg.reload(); await pg.wait_for_selector("th:has-text('Ursache und Vorschlag')",timeout=10000); chk("Alarmliste zeigt Ursache und Vorschlag",True)
        chk("Keine JavaScript-Fehler",not errs,errs); await br.close()
asyncio.run(ui())
