import httpx, time, re, email, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def mail_an(adr, enthaelt=""):
    time.sleep(1.2)
    return [m for m in mails() if adr in str(m["To"]) and enthaelt in str(email.header.make_header(email.header.decode_header(m["Subject"] or ""))) + text(m)]
def token(adr):
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+89)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, os, sys, shutil
S="/var/tmp/pt/s"; Q="/var/tmp/pt/b/queue"; BK="/var/tmp/pt/b/backups"
os.makedirs("/var/tmp/pt/b/caddy/sites",exist_ok=True); open("/var/tmp/pt/b/mode","w").write("extern")
def worker():
    r=subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":"/var/tmp/pt/b","MK_SITES":S},capture_output=True,text=True); return r.stdout+r.stderr
kA,cA,mA=neuer_kunde("Wca"); kB,cB,mB=neuer_kunde("Wcb")
dom=f"wacht{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
os.makedirs(f"{S}/live/{dom}",exist_ok=True); open(f"{S}/live/{dom}/index.html","w").write("<html>Neu</html>"); open(f"{S}/live/{dom}/site.json","w").write(json.dumps({"typ":"live","name":dom,"kunde":"x"}))
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0",WACHT_BASIS="http://localhost:8000",WACHT_API_PRAEFIX="/siteapi")
from app import webbetrieb, db, config
db.open_pool()
cfg={"alarm_email":f"alarm{sfx}@team.de"}
# ---- Wachdienst
e=webbetrieb.pruefen(dom); chk("Prüfung gesunde Website (Startseite und Website-API)",e["api_ok"] and e["seite_ok"] and e["ok"],e)
webbetrieb.wacht(cfg,True)
w=sql(f"select ok||'|'||fehlversuche||'|'||gemeldet from website_wacht where domain='{dom}'"); chk("Stand gespeichert, ok",w=="true|0|false",w)
chk("Tageszähler",sql(f"select geprueft||'|'||ok from website_wacht_tag where domain='{dom}' and tag=current_date")=="1|1")
config.WACHT_BASIS="http://127.0.0.1:9"
webbetrieb.wacht(cfg,True); chk("Erster Fehlschlag: noch kein Alarm",not mail_an(cfg["alarm_email"],dom) and sql(f"select fehlversuche from website_wacht where domain='{dom}'")=="1")
webbetrieb.wacht(cfg,True); m=mail_an(cfg["alarm_email"],"nicht erreichbar"); chk("Zweiter Fehlschlag: Alarm an Admin",len(m)==1 and dom in text(m[0]),len(m))
webbetrieb.wacht(cfg,True); chk("Kein zweiter Alarm",len(mail_an(cfg["alarm_email"],"nicht erreichbar"))==1)
s=cA.get("/api/kunde/website-dienste/wacht").json()["seiten"]; chk("Kunde sieht Status (gestört)",len(s)==1 and s[0]["ok"] is False and s[0]["fehler"],s)
chk("Anderer Kunde sieht nichts",cB.get("/api/kunde/website-dienste/wacht").json()["seiten"]==[])
config.WACHT_BASIS="http://localhost:8000"
webbetrieb.wacht(cfg,True); chk("Entwarnung nach Erholung",len(mail_an(cfg["alarm_email"],"wieder erreichbar"))==1 and sql(f"select gemeldet from website_wacht where domain='{dom}'")=="f")
p=sql(f"select round(100.0*sum(ok)/sum(geprueft)) from website_wacht_tag where domain='{dom}'"); chk("Erreichbarkeit rechnet Ausfälle ein",p=="40",p)
# Zertifikat
sd={"domain":dom,"kunden_id":kA,"firma":"Wca","kundennummer":"K1","letzte_veroeffentlichung":None,"lief_schon":True}
ok_e={"ok":True,"seite_ok":True,"api_ok":True,"http":200,"ms":50,"cert_tage":5,"fehler":""}
webbetrieb._verbuchen(cfg,sd,ok_e); chk("Zertifikat unter 14 Tagen: Hinweis",len(mail_an(cfg["alarm_email"],"Zertifikat läuft ab"))==1,len(mail_an(cfg["alarm_email"],"Zertifikat läuft ab")))
webbetrieb._verbuchen(cfg,sd,ok_e); chk("Hinweis nicht jede Runde",len(mail_an(cfg["alarm_email"],"Zertifikat läuft ab"))==1)
# Neue Seite ohne erfolgreiche Prüfung löst keinen Alarm aus
neu={**sd,"domain":f"neu{sfx}.de","lief_schon":False,"letzte_veroeffentlichung":datetime.datetime.now(datetime.timezone.utc)}
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{neu['domain']}','live','live')")
bad={"ok":False,"seite_ok":False,"api_ok":False,"http":None,"ms":None,"cert_tage":None,"fehler":"Startseite nicht erreichbar"}
for _ in range(3): webbetrieb._verbuchen(cfg,neu,bad)
chk("Frische Website, DNS noch nicht umgestellt: kein Alarm",not mail_an(cfg["alarm_email"],neu["domain"]))
# ---- Admin-Liste zeigt Status
l=a.get("/api/admin/websites").json(); z=[x for x in l["aktiv"] if x["name"]==dom]
chk("Admin-Liste: Wachdienst und Eigentümer",len(z)==1 and z[0]["wacht"]["domain"]==dom and z[0]["eigner"]["kunden_id"]==kA,z)
# ---- Vorschau-Freigabe
demo=f"vorschau{sfx}"; os.makedirs(f"{S}/demos/{demo}",exist_ok=True); open(f"{S}/demos/{demo}/index.html","w").write("<html>Demo</html>")
chk("Kunde darf keine Vorschau verschicken",cA.post("/api/admin/websites/vorschau-freigabe",json={"kunden_id":kA,"demo_name":demo}).status_code==403)
chk("Unbekannte Demo: 404",a.post("/api/admin/websites/vorschau-freigabe",json={"kunden_id":kA,"demo_name":"gibtesnicht"}).status_code==404)
chk("Unbekannter Kunde: 404",a.post("/api/admin/websites/vorschau-freigabe",json={"kunden_id":"00000000-0000-0000-0000-000000000000","demo_name":demo}).status_code==404)
chk("Ungültige Kunden-ID: 404",a.post("/api/admin/websites/vorschau-freigabe",json={"kunden_id":"x","demo_name":demo}).status_code==404)
r=a.post("/api/admin/websites/vorschau-freigabe",json={"kunden_id":kA,"demo_name":demo,"hinweis":"Schauen Sie mal."}); chk("Vorschau verschickt",r.status_code==200,r.text)
ms=mail_an(mA,"Vorschau"); chk("Mail mit Freigabe-Link an den Kunden",len(ms)==1 and "/freigabe?t=" in text(ms[0]),len(ms))
tok=re.search(r"/freigabe\?t=([A-Za-z0-9_-]+)",text(ms[0])).group(1)
d=httpx.get(B+"/api/freigabe-link/"+tok,headers=H).json(); chk("Freigabe zeigt Demo-Adresse",d["status"]=="wartet" and f"/{demo}/" in d["inhalt"] and "Schauen Sie mal." in d["inhalt"] and d["art"]=="website",d)
l=a.get("/api/admin/websites").json(); z=[x for x in l["aktiv"] if x["name"]==demo][0]; chk("Admin sieht: Freigabe wartet",z["freigabe"] and z["freigabe"]["status"]=="wartet",z)
r=httpx.post(B+f"/api/freigabe-link/{tok}/entscheiden",headers=H,json={"entscheidung":"freigegeben","name":"Tina Test"}); chk("Kunde gibt per Klick frei",r.status_code==200,r.text)
l=a.get("/api/admin/websites").json(); z=[x for x in l["aktiv"] if x["name"]==demo][0]; chk("Freigabe mit Name und Zeit festgehalten",z["freigabe"]["status"]=="freigegeben" and z["freigabe"]["entschieden_name"]=="Tina Test" and z["freigabe"]["entschieden_am"],z["freigabe"])
chk("Team bekommt Info über die Freigabe",len(mail_an("chef@test.de","Vorschau"))>=1)
# ---- Wiederherstellung aus Tagessicherung
tag="2026-10-20_0300"
quelle="/var/tmp/pt/bkquelle"; shutil.rmtree(quelle,ignore_errors=True); os.makedirs(f"{quelle}/sites/live/{dom}/css"); os.makedirs(f"{quelle}/sites/live/{dom}/angebote")
open(f"{quelle}/sites/live/{dom}/index.html","w").write("<html>Sicherungsstand</html>"); open(f"{quelle}/sites/live/{dom}/css/a.css","w").write("a{}"); open(f"{quelle}/sites/live/{dom}/angebote/alt.txt","w").write("alt")
os.makedirs(f"{BK}/{tag}",exist_ok=True)
subprocess.run(["tar","-czf",f"{BK}/{tag}/sites.tar.gz","-C",quelle,"sites"],check=True)
os.makedirs(f"{S}/live/{dom}/angebote",exist_ok=True); open(f"{S}/live/{dom}/angebote/aktuell.txt","w").write("neu")
worker()
si=a.get("/api/admin/websites/sicherungen").json(); chk("Sicherungsliste für das Portal",tag in si["tage"],si)
chk("Kunde sieht die Sicherungsliste nicht",cA.get("/api/admin/websites/sicherungen").status_code==403)
chk("Ungültiges Datum abgelehnt",a.post("/api/admin/websites/aus-sicherung",json={"art":"live","name":dom,"tag":"../../etc"}).status_code==400)
chk("Ungültiger Name abgelehnt",a.post("/api/admin/websites/aus-sicherung",json={"art":"live","name":"../x","tag":tag}).status_code==400)
r=a.post("/api/admin/websites/aus-sicherung",json={"art":"live","name":dom,"tag":tag}); chk("Auftrag angenommen",r.status_code==200,r.text)
out=worker()
idx=open(f"{S}/live/{dom}/index.html").read(); chk("Seite aus Sicherung online",idx=="<html>Sicherungsstand</html>" and os.path.isfile(f"{S}/live/{dom}/css/a.css"),out)
chk("Aktuelle Wochenangebote bleiben erhalten",os.path.isfile(f"{S}/live/{dom}/angebote/aktuell.txt") and not os.path.isfile(f"{S}/live/{dom}/angebote/alt.txt"))
vor=glob.glob(f"{S}/.vorversionen/*__live__{dom}") if (glob:=__import__("glob")) else []
chk("Jetzige Version als Vorversion gesichert",vor and "Neu" in open(vor[0]+"/index.html").read(),vor)
chk("site.json bleibt",os.path.isfile(f"{S}/live/{dom}/site.json"))
v=a.get("/api/admin/websites/veroeffentlichungen").json(); chk("Ergebnis im Verlauf",any(x.get("ok") and x.get("name")==dom for x in v["ergebnisse"]),v)
# nicht enthaltene Seite
a.post("/api/admin/websites/aus-sicherung",json={"art":"live","name":f"fehlt{sfx}.de","tag":tag}); out=worker()
chk("Seite nicht in der Sicherung: klare Meldung, nichts angelegt",not os.path.exists(f"{S}/live/fehlt{sfx}.de"))
v=a.get("/api/admin/websites/veroeffentlichungen").json(); chk("Fehler wird gemeldet",any((not x.get("ok")) and "nicht enthalten" in x.get("text","") for x in v["ergebnisse"]),v)
# Symlink in der Sicherung wird abgelehnt
shutil.rmtree(quelle); os.makedirs(f"{quelle}/sites/live/{dom}"); open(f"{quelle}/sites/live/{dom}/index.html","w").write("x"); os.symlink("/etc/passwd",f"{quelle}/sites/live/{dom}/boese")
tag2="2026-10-21_0300"; os.makedirs(f"{BK}/{tag2}",exist_ok=True); subprocess.run(["tar","-czf",f"{BK}/{tag2}/sites.tar.gz","-C",quelle,"sites"],check=True)
a.post("/api/admin/websites/aus-sicherung",json={"art":"live","name":dom,"tag":tag2}); worker()
chk("Symlink in der Sicherung: abgelehnt, Seite unverändert",open(f"{S}/live/{dom}/index.html").read()=="<html>Sicherungsstand</html>")
