"""Erinnerung an unbeantwortete Angebote (Lead und Kunde): Vorschau, Versand, Begrenzung, Rechte."""
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
sfx=str(int(time.time())+1000)
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
def vorschau(bid): return a.get(f"/api/admin/angebote-erinnerung/{bid}")
def alt(bid,tage): sql(f"update belege set versendet_am=now()-interval '{tage} days', erinnert_am=NULL where id='{bid}'")
# ---------------- Lead-Angebot
lid=a.post("/api/admin/leads",json={"firma":f"Erinn {sfx}","telefon":"0511 7100001","ort":"Celle","plz":"29221","email":f"erinn{sfx}@lead.de","ansprechpartner":"Herr Erinn"}).json()["id"]
bid=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"Angebot","einleitung":"Hallo","schluss":"Danke","positionen":pos,"leistungen":[]}).json()["id"]
chk("Entwurf: keine Erinnerung möglich",vorschau(bid).json()["moeglich"] is False)
s=a.post(f"/api/admin/leads/{lid}/angebote/{bid}/senden",json={"gueltig_tage":30}); link=s.json()["link"]; chk("Angebot gesendet",s.json()["gesendet"],s.text)
v=vorschau(bid).json(); chk("Gerade erst gesendet: Erinnerung gesperrt mit Grund",v["moeglich"] is False and "frühestens" in v["grund"],v)
r=a.post(f"/api/admin/angebote-erinnerung/{bid}",json={}); chk("Senden zu früh wird abgelehnt",r.status_code==400,r.text)
alt(bid,4)
v=vorschau(bid).json(); chk("Nach 4 Tagen möglich, Stufe 1, Link, Gültigkeit und Grußzeile im Text",v["moeglich"] and v["stufe"]==1 and link in v["text"] and "gültig bis" in v["text"] and v["text"].rstrip().endswith("Markentrix") and "Viele Grüße" in v["text"] and v["an"]==f"erinn{sfx}@lead.de",v)
n0=len(mails())
r=a.post(f"/api/admin/angebote-erinnerung/{bid}",json={"text":v["text"].replace("kurz nachfragen","kurz EIGENTEXT nachfragen")}); time.sleep(1.2)
chk("Erinnerung 1 gesendet",r.status_code==200 and r.json()["gesendet"] and r.json()["stufe"]==1,r.text)
m=[x for x in mails()[n0:] if f"erinn{sfx}@lead.de" in str(x["To"])]
chk("Mail: Betreff, geänderter Text, PDF-Anhang",len(m)==1 and "Erinnerung" in betreff(m[0]) and "EIGENTEXT" in text(m[0]) and any(p.get_content_type()=="application/pdf" for p in m[0].walk()),[betreff(x) for x in m])
chk("Zähler und Datum gesetzt",sql(f"select erinnerungen||'|'||(erinnert_am is not null) from belege where id='{bid}'")=="1|true")
chk("Wiedervorlage in 3 Tagen und Aktivität",sql(f"select wiedervorlage_am::text from leads where id='{lid}'")==str(__import__("datetime").date.today()+__import__("datetime").timedelta(days=3)) and int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and inhalt like '%Erinnerung 1%'"))==1)
chk("Direkt danach gesperrt",vorschau(bid).json()["moeglich"] is False)
r=a.post(f"/api/admin/angebote-erinnerung/{bid}",json={"text":"Hallo ohne Link"}); chk("Nach Sperre kein Doppelversand",r.status_code==400)
sql(f"update belege set erinnert_am=now()-interval '4 days' where id='{bid}'")
r=a.post(f"/api/admin/angebote-erinnerung/{bid}",json={"text":"Hallo ohne Link"}); chk("Text ohne Angebotslink wird abgelehnt",r.status_code==400 and "Link" in r.text,r.text)
v=vorschau(bid).json(); chk("Stufe 2: fragt nach offenen Fragen",v["stufe"]==2 and "Fragen" in v["text"] and "Fragen" in v["betreff"],v["betreff"])
a.post(f"/api/admin/angebote-erinnerung/{bid}",json={})
sql(f"update belege set erinnert_am=now()-interval '4 days' where id='{bid}'")
v=vorschau(bid).json(); chk("Stufe 3: letzte Nachfrage",v["stufe"]==3 and "nicht erneut" in v["text"],v)
a.post(f"/api/admin/angebote-erinnerung/{bid}",json={})
sql(f"update belege set erinnert_am=now()-interval '9 days' where id='{bid}'")
v=vorschau(bid).json(); chk("Nach 3 Erinnerungen keine weitere",v["moeglich"] is False and "3 Erinnerungen" in v["grund"],v)
# Abgelaufen, angenommen, gesperrter Lead
b2=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"Zwei","einleitung":"H","schluss":"D","positionen":pos,"leistungen":[]}).json()["id"]
a.post(f"/api/admin/leads/{lid}/angebote/{b2}/senden",json={"gueltig_tage":30}); alt(b2,5)
sql(f"update belege set faellig_am=current_date-1 where id='{b2}'"); v=vorschau(b2).json(); chk("Abgelaufenes Angebot: keine Erinnerung",v["moeglich"] is False and "abgelaufen" in v["grund"],v)
sql(f"update belege set faellig_am=current_date+10 where id='{b2}'"); sql(f"update leads set status='gesperrt' where id='{lid}'")
v=vorschau(b2).json(); chk("Gesperrter Lead: keine Erinnerung",v["moeglich"] is False and "gesperrt" in v["grund"],v)
sql(f"update leads set status='angebot' where id='{lid}'"); sql(f"update belege set status='angenommen' where id='{b2}'")
chk("Angenommenes Angebot: keine Erinnerung",vorschau(b2).json()["moeglich"] is False)
chk("Unbekannte ID: 404",a.get("/api/admin/angebote-erinnerung/00000000-0000-0000-0000-000000000000").status_code==404 and a.get("/api/admin/angebote-erinnerung/xyz").status_code==404)
# Übersicht und Lead-Liste liefern Zähler
ang=a.get("/api/admin/heute").json()["angebote"]; chk("Übersicht kennt Zähler",any(x["id"]==bid and x["erinnerungen"]==3 for x in ang),ang[:2])
chk("Lead-Liste kennt Zähler",any(x["id"]==bid and x["erinnerungen"]==3 for x in a.get(f"/api/admin/leads/{lid}/angebote").json()))
# ---------------- Angebot an bestehenden Kunden
kid,c=neuer_kunde("Erinn")
b3=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"angebot","betreff":"Zusatz","einleitung":"H","schluss":"D","positionen":pos}); chk("Kundenangebot angelegt",b3.status_code==200,b3.text); b3=b3.json()["id"]
a.post(f"/api/admin/belege/{b3}/ausstellen",json={}); s=a.post(f"/api/admin/belege/{b3}/senden"); chk("Kundenangebot gesendet",s.json().get("gesendet"),s.text)
alt(b3,4); v=vorschau(b3).json()
chk("Kunde: Vorschau mit Portal-Link, ohne Lead-Hinweis",v["moeglich"] and "/app#belege" in v["text"] and not v["hinweis"],v)
n0=len(mails()); r=a.post(f"/api/admin/angebote-erinnerung/{b3}",json={}); time.sleep(1.2)
chk("Kundenangebot: Erinnerung gesendet, Zähler 1",r.json()["gesendet"] and sql(f"select erinnerungen from belege where id='{b3}'")=="1",r.text)
chk("Mail an Kunden mit PDF",any(f"erinn{sfx}@k.de" in str(x["To"]) and any(p.get_content_type()=="application/pdf" for p in x.walk()) for x in mails()[n0:]))
chk("Kunde selbst darf nicht",c.get(f"/api/admin/angebote-erinnerung/{b3}").status_code in (401,403))
# Teil-Admin ohne Finanzrecht
user={"id":"x","email":"t@t.de","admin_rechte":["leads"]}
with tx("admin") as cur:
    cur.execute("SELECT * FROM belege WHERE id=%s",(b3,)); bb=cur.fetchone()
    try: angebotserinnerung._pruefen(cur,bb,user); ok=False
    except Exception as e: ok=getattr(e,"status_code",0)==403
chk("Teil-Admin ohne Finanzrecht: Kundenangebot gesperrt",ok)
