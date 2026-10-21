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
sfx=str(int(time.time())+105)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import json, os, subprocess, glob
Q="/var/tmp/pt/b/queue"; BK="/var/tmp/pt/b/backups"; os.makedirs(Q,exist_ok=True); os.makedirs(BK,exist_ok=True)
W="/var/tmp/pt/psqlw"
open(W,"w").write('#!/bin/bash\nexec su postgres -c "psql -h /var/tmp/pgtest -p 54329 $(printf \'%q \' "$@")"\n'); os.chmod(W,0o755)
def worker():
    r=subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":"/var/tmp/pt/b","MK_SITES":"/var/tmp/pt/s","MK_PSQL":W},capture_output=True,text=True); return r.stdout+r.stderr
kA,cA,mA=neuer_kunde("Rsa"); kB,cB,mB=neuer_kunde("Rsb")
def an(k,n,t): sql(f"insert into anfragen (kunden_id, name, kontakt, nachricht, quelle) values ('{k}','{n}','x@y.de','{t}','website')")
for i in range(3): an(kA,f"Alt{i}",f"vor der Sicherung {i}")
an(kB,"Fremd","Gehört dem anderen Kunden")
tag="2026-10-19_0300"; os.makedirs(f"{BK}/{tag}",exist_ok=True)
subprocess.run(f"su postgres -c 'pg_dump -h /var/tmp/pgtest -p 54329 markentrix' | gzip > {BK}/{tag}/markentrix-db.sql.gz",shell=True,check=True)
# danach: zwei gelöscht, eine neue dazu
sql(f"delete from anfragen where kunden_id='{kA}' and name in ('Alt0','Alt1')"); an(kA,"Neu","nach der Sicherung")
sql(f"delete from anfragen where kunden_id='{kB}'")
chk("Vorher: 2 Anfragen vorhanden",sql(f"select count(*) from anfragen where kunden_id='{kA}'")=="2")
chk("Kunde darf keinen Auszug anfordern",cA.post(f"/api/admin/kunden/{kA}/auszug",json={"tag":tag}).status_code==403)
chk("Ungültiges Datum abgelehnt",a.post(f"/api/admin/kunden/{kA}/auszug",json={"tag":"../x"}).status_code==400)
chk("Unbekannter Kunde: 404",a.post("/api/admin/kunden/00000000-0000-0000-0000-000000000000/auszug",json={"tag":tag}).status_code==404)
r=a.post(f"/api/admin/kunden/{kA}/auszug",json={"tag":tag}); chk("Auszug angefordert",r.status_code==200,r.text); uid=r.json()["id"]
chk("Status: läuft",a.get(f"/api/admin/kunden/auszug/{uid}").json()["status"]=="laeuft")
out=worker()
s=a.get("/api/admin/datensicherungen").json(); chk("Datenbanksicherungen werden aufgelistet",tag in s["tage"],s)
d=a.get(f"/api/admin/kunden/auszug/{uid}").json(); chk("Auszug bereit",d["status"]=="bereit",(d,out[-400:]))
t={x["tabelle"]:x for x in d.get("tabellen",[])}
chk("Anfragen: 3 in Sicherung, 2 fehlen",t.get("anfragen",{}).get("in_sicherung")==3 and t["anfragen"]["fehlt_jetzt"]==2,t.get("anfragen"))
chk("Zugangsdaten und Protokolle nie im Auszug","benutzer" not in t and "audit_log" not in t and "mail_protokoll" not in t,list(t))
raw=open(f"{Q}/kundenauszug-{uid}.json").read(); chk("Nur Daten dieses Kunden",kB not in raw and "Fremd" not in raw)
chk("Datei hat keine Weltlesbarkeit",(os.stat(f"{Q}/kundenauszug-{uid}.json").st_mode & 0o007)==0)
chk("Wegwerf-Datenbank wieder gelöscht",sql(f"select count(*) from pg_database where datname='mkrestore_{uid}'")=="0")
chk("Kunde darf nicht zurückspielen",cA.post(f"/api/admin/kunden/auszug/{uid}/zurueckspielen",json={"tabellen":["anfragen"]}).status_code==403)
chk("Unbekannte Tabelle: nichts passiert",a.post(f"/api/admin/kunden/auszug/{uid}/zurueckspielen",json={"tabellen":["benutzer"]}).status_code==400)
r=a.post(f"/api/admin/kunden/auszug/{uid}/zurueckspielen",json={"tabellen":["anfragen"]}); chk("Zurückgespielt",r.status_code==200 and r.json()["ergebnis"]["anfragen"]["zurueck"]==2,r.text)
chk("Jetzt 4 Anfragen, die neue blieb",sql(f"select count(*) from anfragen where kunden_id='{kA}'")=="4" and sql(f"select count(*) from anfragen where kunden_id='{kA}' and name='Neu'")=="1")
chk("Anderer Kunde unverändert (nichts zurückgespielt)",sql(f"select count(*) from anfragen where kunden_id='{kB}'")=="0")
r=a.post(f"/api/admin/kunden/auszug/{uid}/zurueckspielen",json={"tabellen":["anfragen"]}); chk("Zweites Mal: nichts doppelt",r.status_code==200 and r.json()["ergebnis"]["anfragen"]["zurueck"]==0 and sql(f"select count(*) from anfragen where kunden_id='{kA}'")=="4",r.text)
chk("Audit-Eintrag",int(sql(f"select count(*) from audit_log where aktion='kundendaten_aus_sicherung' and kunden_id='{kA}'"))>=1)
chk("Auszug löschen",a.delete(f"/api/admin/kunden/auszug/{uid}").status_code==200 and not os.path.exists(f"{Q}/kundenauszug-{uid}.json"))
chk("Gelöschter Auszug: 404 beim Zurückspielen",a.post(f"/api/admin/kunden/auszug/{uid}/zurueckspielen",json={"tabellen":["anfragen"]}).status_code==404)
chk("Ungültige Auszug-ID",a.get("/api/admin/kunden/auszug/../../etc").status_code in (404,405,422))
# Sicherung nicht vorhanden
r=a.post(f"/api/admin/kunden/{kA}/auszug",json={"tag":"2020-01-01_0000"}); uid2=r.json()["id"]; worker()
d=a.get(f"/api/admin/kunden/auszug/{uid2}").json(); chk("Fehlende Sicherung: klare Meldung",d["status"]=="fehler" and "nicht" in d["text"],d)
# Kunde, den es in der Sicherung noch nicht gab
sql(f"insert into kunden (firma, email, status) values ('Spaet {sfx}','spaet{sfx}@k.de','aktiv')"); ks=sql(f"select id from kunden where firma='Spaet {sfx}'")
r=a.post(f"/api/admin/kunden/{ks}/auszug",json={"tag":tag}); uid3=r.json()["id"]; worker()
d=a.get(f"/api/admin/kunden/auszug/{uid3}").json(); chk("Kunde war damals noch nicht da: Fehlermeldung",d["status"]=="fehler" and "noch nicht vorhanden" in d["text"],d)
chk("Keine Wegwerf-Datenbanken übrig",sql("select count(*) from pg_database where datname like 'mkrestore_%'")=="0")
