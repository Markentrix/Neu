import httpx, subprocess, time, os, sys
B="http://localhost:8000"; B2="http://localhost:8001"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
PW=open("/var/tmp/pt/adminpw").read().strip()
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import jobs, db, zweifaktor
db.open_pool()
# ---- Aufbewahrung wie im AVV
chk("Chatverlauf: 180 Tage (6 Monate)",sql("select aufbewahrung_tage from loeschregeln where tabelle='chat_verlauf'")=="180")
chk("Audit-Log: Regel 365 Tage",sql("select aufbewahrung_tage from loeschregeln where tabelle='audit_log'")=="365")
sql("insert into audit_log (zeit,aktion) values (now()-interval '13 months','t41_alt'),(now()-interval '11 months','t41_neu')")
try:
    with db.tx("system") as cur: cur.execute("DELETE FROM audit_log WHERE aktion='t41_alt'")
    chk("Anwendung darf Audit-Log nicht direkt löschen",False)
except Exception: chk("Anwendung darf Audit-Log nicht direkt löschen",True)
e=jobs.fristen_ausfuehren()
chk("Frist-Job löscht Audit-Einträge über 12 Monate, behält jüngere",sql("select count(*) from audit_log where aktion='t41_alt'")=="0" and sql("select count(*) from audit_log where aktion='t41_neu'")=="1" and e.get("audit_log",0)>=1,e)
chk("Löschprotokoll hält das Audit-Aufräumen fest",int(sql("select count(*) from loeschprotokoll where tabelle='audit_log'") or 0)>=1)
# ---- Zwei-Faktor-Pflicht für Admins (zweite Instanz mit eingeschalteter Pflicht)
env=dict(os.environ,PORTAL_ADMIN_2FA="1")
p=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--port","8001"],cwd="/home/claude/markentrix-server/portal",env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(40):
        try:
            if httpx.get(B2+"/api/me",headers=H).status_code in (200,401): break
        except Exception: time.sleep(0.5)
    a=httpx.Client(base_url=B2,headers=H); r=a.post("/api/login",json={"email":"chef@test.de","password":PW}); chk("Admin ohne 2FA kann sich anmelden (um 2FA einzurichten)",r.status_code==200,r.text)
    me=a.get("/api/me").json(); chk("/api/me meldet 2FA-Pflicht",me["zwei_faktor_pflicht"] is True and me["zwei_faktor"] is False,me)
    r=a.get("/api/admin/uebersicht"); chk("Admin-Funktionen ohne 2FA gesperrt",r.status_code==403 and "Zwei-Faktor" in r.text,r.text)
    chk("Admin-Funktion Mitarbeiter ohne 2FA gesperrt",a.get("/api/admin/team").status_code in (403,404))
    s=a.post("/api/2fa/start").json(); chk("2FA-Einrichtung ist erlaubt",bool(s.get("geheimnis")),s)
    from time import time as t0
    code=zweifaktor._code(s["geheimnis"],int(t0()//30))
    r=a.post("/api/2fa/aktivieren",json={"code":code}); chk("2FA aktivieren",r.status_code==200 and len(r.json()["notfallcodes"])>=5,r.text)
    chk("danach keine Pflicht mehr, Admin-Funktionen frei",a.get("/api/me").json()["zwei_faktor_pflicht"] is False and a.get("/api/admin/uebersicht").status_code==200)
finally:
    p.terminate()
    sql("update benutzer set totp_aktiv=false, totp_secret=NULL, totp_recovery='[]'::jsonb, totp_letzter_schritt=0 where email='chef@test.de'")
chk("Testadmin wieder ohne 2FA zurückgesetzt",sql("select totp_aktiv from benutzer where email='chef@test.de'")=="f")
