"""Website-Wachdienst: www nicht doppelt, Ampel ohne Altlasten, Fehler mit Ursache und Lösung."""
import httpx, time, re, email, email.header, json, os, sys, subprocess, datetime, zoneinfo
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def teil(m,typ):
    for p in m.walk():
        if p.get_content_type()==typ: return p.get_payload(decode=True).decode("utf8","replace")
text=lambda m: teil(m,"text/plain")
betreff=lambda m: str(email.header.make_header(email.header.decode_header(m["Subject"])))
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+900)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)


kid,c=neuer_kunde("Wacht")
dom=f"wacht{sfx}.de"; www="www."+dom
# Anlegen: www wird abgelehnt
r=a.post(f"/api/admin/kunden/{kid}/websites",json={"domain":www,"art":"live"}); chk("www beim Anlegen abgelehnt, mit Hinweis",r.status_code==400 and dom in r.text,r.text)
r=a.post(f"/api/admin/kunden/{kid}/websites",json={"domain":dom,"art":"live"}); chk("Hauptadresse anlegen geht",r.status_code==200,r.text)
# www-Zeile direkt in der Datenbank (wie bei Altbestand)
sql(f"INSERT INTO websites (kunden_id, domain, art, status, verzeichnis) VALUES ('{kid}','{www}','live','live','/srv/sites/{www}')")
with tx("system") as cur:
    cur.execute("SELECT w.domain, w.kunden_id FROM websites w WHERE w.kunden_id=%s", (kid,)); z=cur.fetchall()
rest=[x["domain"] for x in webbetrieb.ohne_www_doppel(z)]
chk("Wachdienst prüft www nicht doppelt",rest==[dom],rest)
chk("www ohne Hauptadresse bleibt in der Prüfung",[x["domain"] for x in webbetrieb.ohne_www_doppel([{"domain":"www.a.de","kunden_id":1}])]==["www.a.de"])
chk("Hauptadresse eines anderen Kunden zählt nicht",len(webbetrieb.ohne_www_doppel([{"domain":"www.a.de","kunden_id":1},{"domain":"a.de","kunden_id":2}]))==2)
# Diagnose
D=webbetrieb.diagnose
t=D(www,"Startseite nicht erreichbar ([SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1010)); Website-API nicht erreichbar ([SSL: TLSV1_ALERT_INTERNAL_ERROR])")
chk("TLS-Fehler bei www: Ursache und Schritte nennen A-Eintrag und offline stellen",len(t)==1 and "A-Eintrag" in " ".join(t[0]["schritte"]) and "offline" in " ".join(t[0]["schritte"]) and t[0]["ursache"],t)
t=D("firma.de","Startseite nicht erreichbar (der Webserver hat für diese Domain noch kein Zertifikat: ALERT_INTERNAL_ERROR)")
chk("TLS-Fehler bei Hauptadresse: mkctl site-add genannt",any("mkctl site-add firma.de" in x for x in t[0]["schritte"]),t)
chk("DNS-Fehler erkannt",D("f.de","Startseite nicht erreichbar ([Errno -2] Name or service not known)")[0]["titel"].endswith("(DNS)"))
chk("Zeitüberschreitung erkannt",D("f.de","Startseite nicht erreichbar (timed out)")[0]["titel"].find("Keine Verbindung")>0)
chk("Zertifikat ungültig erkannt",any("Zertifikat" in x["titel"] for x in D("f.de","Zertifikat ungültig (expired)")))
chk("HTTP 502 erklärt",D("f.de","Startseite antwortet mit Fehler 502")[0]["ursache"].find("Portal")>0)
chk("API-Fehler erklärt",any("/api/health" in x["titel"] for x in D("f.de","Website-API (/api/health) antwortet nicht richtig")))
chk("Unbekannter Fehler: allgemeiner Hinweis mit Meldung",D("f.de","komisch")[0]["ursache"].endswith("komisch"))
chk("Kein Fehler: keine Erklärung",D("f.de","")==[])
# Ampel
sql(f"INSERT INTO website_wacht (domain, kunden_id, geprueft_am, ok, seite_ok, api_ok, fehler, seit, fehlversuche, gemeldet) VALUES ('{www}','{kid}',now(),false,false,false,'Startseite nicht erreichbar ([SSL: TLSV1_ALERT_INTERNAL_ERROR] x); Website-API nicht erreichbar ([SSL: TLSV1_ALERT_INTERNAL_ERROR] x)',now()-interval '2 days',9,true)")
def ampel():
    return [x for x in a.get("/api/admin/kunden-ampel").json()["kunden"] if x["id"]==kid][0]
k=ampel(); chk("Ampel rot bei gestörter aktiver Website, Hinweis auf Öffnen",k["farbe"]=="rot" and any("Öffnen" in x for x in k["rot"]),k)
p=a.get(f"/api/admin/kunden/{kid}/website-probleme").json()
chk("Probleme-Route: Domain, Fehler, Erklärung",len(p)==1 and p[0]["domain"]==www and p[0]["fehler"] and p[0]["erklaerung"] and p[0]["erklaerung"][0]["schritte"],p)
chk("Probleme-Route nur für Admins",c.get(f"/api/admin/kunden/{kid}/website-probleme").status_code in (401,403))
sql(f"UPDATE websites SET status='offline' WHERE kunden_id='{kid}' AND domain='{www}'")
k=ampel(); chk("Offline gestellte Website löst keine Ampel mehr aus",not any("antwortet nicht richtig" in x for x in k["rot"]),k)
chk("Probleme-Route danach leer",a.get(f"/api/admin/kunden/{kid}/website-probleme").json()==[])
with tx("system") as cur:
    chk("Status-Liste enthält die offline gestellte Website nicht",www not in [x["domain"] for x in webbetrieb.status(cur,kid)])
