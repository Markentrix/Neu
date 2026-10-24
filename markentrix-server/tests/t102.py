"""Angebots-Erinnerung: Rückfrage nach dem Grund, Automatik (Standard aus), abgemeldete Leads."""
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
sfx=str(int(time.time())+1100)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb, angebotserinnerung
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)



a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
pos=[{"text":"BUSINESS – monatlich","menge":1,"einheit":"Monat","preis_cent":19900}]
def lead_ang(tag):
    lid=a.post("/api/admin/leads",json={"firma":f"Auto{tag} {sfx}","telefon":f"0511 72{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","email":f"auto{tag}{sfx}@lead.de","ansprechpartner":"Herr Auto"}).json()["id"]
    bid=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"A","einleitung":"H","schluss":"D","positionen":pos,"leistungen":[]}).json()["id"]
    a.post(f"/api/admin/leads/{lid}/angebote/{bid}/senden",json={"gueltig_tage":30}); return lid,bid
def alt(bid,tage): sql(f"update belege set versendet_am=now()-interval '{tage} days', erinnert_am=NULL where id='{bid}'")
# Texte
T=angebotserinnerung.text_bauen
b1,t1=T(1,"Herr X","Firma","AN-1",None,"https://l","Markentrix",True); b2,t2=T(2,"Herr X","Firma","AN-1",None,"https://l","Markentrix",True); b3,t3=T(3,None,"Firma","AN-1",None,"https://l","Markentrix",False)
chk("Stufe 2 fragt, woran es liegt, mit Beispielen",all(w in t2 for w in ("woran es liegt","Preis","Umfang","Zeitpunkt","anderen Angebot")) and "Woran" in b2,t2)
chk("Stufe 3 bittet um offene Rückmeldung",("ganz offen" in t3) and ("nicht erneut" in t3))
chk("Alle Stufen enden mit Grußzeile",all(t.rstrip().endswith("Markentrix") and "Viele Grüße" in t for t in (t1,t2,t3)))
# Einstellung
chk("Automatik ist standardmäßig aus",a.get("/api/admin/einstellungen/angebote").json()["auto_erinnerung"] is False)
lid,bid=lead_ang("a"); alt(bid,5)
chk("Aus: Lauf sendet nichts",angebotserinnerung.auto_lauf()==0 and sql(f"select erinnerungen from belege where id='{bid}'")=="0")
r=a.put("/api/admin/einstellungen/angebote",json={"auto_erinnerung":True}); chk("Einschalten",r.status_code==200 and a.get("/api/admin/einstellungen/angebote").json()["auto_erinnerung"])
chk("Einschalten wird protokolliert",int(sql("select count(*) from audit_log where aktion='einstellung_angebote'"))>=1)
lid2,bid2=lead_ang("b"); alt(bid2,1)         # zu frisch
lid3,bid3=lead_ang("c"); alt(bid3,5); sql(f"update leads set abgemeldet=true where id='{lid3}'")
lid4,bid4=lead_ang("d"); alt(bid4,5); sql(f"update belege set erinnerungen=2, erinnert_am=now()-interval '9 days' where id='{bid4}'")
lid5,bid5=lead_ang("e"); alt(bid5,5); sql(f"update belege set faellig_am=current_date-1 where id='{bid5}'")
n0=len(mails()); n=angebotserinnerung.auto_lauf(); time.sleep(1.5)
z=lambda b: sql(f"select erinnerungen from belege where id='{b}'")
chk("Ein: nur das fällige Angebot wird erinnert",z(bid)=="1" and z(bid2)=="0" and z(bid3)=="0" and z(bid4)=="2" and z(bid5)=="0",[z(x) for x in (bid,bid2,bid3,bid4,bid5)])
chk("Genau eine Mail, als automatisch protokolliert",n==1 and len([x for x in mails()[n0:] if "auto" in str(x["To"])])==1 and int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and inhalt like '%(automatisch)%'"))==1,n)
chk("Audit mit automatisch=true",int(sql("select count(*) from audit_log where aktion='angebot_erinnert' and details->>'automatisch'='true'"))==1)
chk("Zweiter Lauf am selben Tag sendet nichts mehr",angebotserinnerung.auto_lauf()==0)
sql(f"update belege set erinnert_am=now()-interval '4 days' where id='{bid}'"); n=angebotserinnerung.auto_lauf(); time.sleep(1)
chk("Stufe 2 geht automatisch, Stufe 3 nie",n==1 and z(bid)=="2")
sql(f"update belege set erinnert_am=now()-interval '9 days' where id='{bid}'"); chk("Stufe 3 nicht automatisch",angebotserinnerung.auto_lauf()==0 and z(bid)=="2")
chk("Abgemeldeter Lead: auch manuell gesperrt",a.get(f"/api/admin/angebote-erinnerung/{bid3}").json()["moeglich"] is False and "abgemeldet" in a.get(f"/api/admin/angebote-erinnerung/{bid3}").json()["grund"])
a.put("/api/admin/einstellungen/angebote",json={"auto_erinnerung":False}); lid6,bid6=lead_ang("f"); alt(bid6,6)
chk("Wieder aus: nichts mehr",angebotserinnerung.auto_lauf()==0 and z(bid6)=="0")
c=httpx.Client(base_url=B,headers=H)
chk("Einstellung nur für Admins",c.put("/api/admin/einstellungen/angebote",json={"auto_erinnerung":True}).status_code in (401,403))
