"""Angebotsgrund: festhalten, Online-Ablehnung, Auswertung, Rechte."""
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
sfx=str(int(time.time())+1200)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, webbetrieb, angebotsgrund
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)




a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
pos=[{"text":"BUSINESS – monatlich","menge":1,"einheit":"Monat","preis_cent":19900}]
def lead_ang(tag):
    lid=a.post("/api/admin/leads",json={"firma":f"Grund{tag} {sfx}","telefon":f"0511 73{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","email":f"grund{tag}{sfx}@lead.de","ansprechpartner":"Herr Grund"}).json()["id"]
    bid=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"A","einleitung":"H","schluss":"D","positionen":pos,"leistungen":[]}).json()["id"]
    s=a.post(f"/api/admin/leads/{lid}/angebote/{bid}/senden",json={"gueltig_tage":30}).json(); return lid,bid,s["link"].split("t=")[1]
G=lambda b: sql(f"select coalesce(grund_code,'')||'|'||coalesce(grund_text,'') from belege where id='{b}'")
chk("Liste der Gründe",len(a.get("/api/admin/angebote-grund").json()["gruende"])==len(angebotsgrund.GRUENDE))
lid,b1,t1=lead_ang("a")
r=a.post(f"/api/admin/angebote-grund/{b1}",json={"code":"zu_teuer","text":"Wollte Rabatt"}); chk("Grund festhalten",r.status_code==200 and G(b1)=="zu_teuer|Wollte Rabatt",r.text)
chk("Eintrag im Lead und Audit",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and inhalt like '%Grund festgehalten%Zu teuer%'"))==1 and int(sql("select count(*) from audit_log where aktion='angebot_grund'"))>=1)
chk("Ungültiger Grund abgelehnt",a.post(f"/api/admin/angebote-grund/{b1}",json={"code":"quatsch"}).status_code==400)
chk("Grund erscheint in der Lead-Liste und Übersicht",any(x["id"]==b1 and x["grund_code"]=="zu_teuer" for x in a.get(f"/api/admin/leads/{lid}/angebote").json()) and any(x["id"]==b1 and x["grund_code"]=="zu_teuer" for x in a.get("/api/admin/heute").json()["angebote"]))
a.post(f"/api/admin/angebote-grund/{b1}",json={"code":"konkurrenz"}); chk("Grund ändern",G(b1)=="konkurrenz|")
r=a.post(f"/api/admin/angebote-grund/{b1}",json={"code":""}); chk("Grund entfernen",r.status_code==200 and G(b1)=="|" and sql(f"select grund_am is null from belege where id='{b1}'")=="t")
a.post(f"/api/admin/angebote-grund/{b1}",json={"code":"zeitpunkt"})
# Online-Ablehnung speichert Grund
lid2,b2,t2=lead_ang("b")
r=httpx.post(B+f"/api/angebot/{t2}/ablehnen",headers=H,json={"grund":"zu spät dran","grund_code":"spaeter"}); chk("Online ablehnen",r.status_code==200,r.text)
chk("Online-Grund auf gemeinsame Liste abgebildet",G(b2)=="zeitpunkt|zu spät dran",G(b2))
lid3,b3,t3=lead_ang("c")
r=httpx.post(B+f"/api/angebot/{t3}/ablehnen",headers=H,json={}); chk("Online ablehnen ohne Grund",r.status_code==200 and G(b3)=="|")
a.post(f"/api/admin/angebote-grund/{b3}",json={"code":"keine_antwort"}); chk("Grund nachträglich bei abgelehntem Angebot",G(b3)=="keine_antwort|")
# Team lehnt ab, mit Grund
lid4,b4,t4=lead_ang("d")
r=a.post(f"/api/admin/belege/{b4}/angebot-status",json={"status":"abgelehnt","grund_code":"umfang","grund_text":"Fehlt Telefonanbindung"}); chk("Abgelehnt mit Grund",r.status_code==200 and G(b4)=="umfang|Fehlt Telefonanbindung",r.text)
lid5,b5,t5=lead_ang("e")
a.post(f"/api/admin/belege/{b5}/angebot-status",json={"status":"abgelehnt"}); chk("Abgelehnt ohne Grund bleibt ohne",G(b5)=="|")
# Angenommen: kein Grund
lid6,b6,t6=lead_ang("f"); httpx.post(B+f"/api/angebot/{t6}/annehmen",headers=H,json={"name":"Herr Grund","zustimmung":True,"zustimmung_agb":True,"vorzeitiger_beginn":True})
st=sql(f"select status from belege where id='{b6}'")
if st=="angenommen": chk("Angenommenes Angebot: Grund nicht möglich",a.post(f"/api/admin/angebote-grund/{b6}",json={"code":"zu_teuer"}).status_code==400)
else: sql(f"update belege set status='angenommen' where id='{b6}'"); chk("Angenommenes Angebot: Grund nicht möglich",a.post(f"/api/admin/angebote-grund/{b6}",json={"code":"zu_teuer"}).status_code==400)
# Entwurf
bd=a.post(f"/api/admin/leads/{lid}/angebote",json={"betreff":"E","einleitung":"H","schluss":"D","positionen":pos,"leistungen":[]}).json()["id"]
chk("Entwurf: kein Grund",a.post(f"/api/admin/angebote-grund/{bd}",json={"code":"zu_teuer"}).status_code==400)
chk("Unbekannte ID: 404",a.post("/api/admin/angebote-grund/00000000-0000-0000-0000-000000000000",json={"code":"zu_teuer"}).status_code==404 and a.post("/api/admin/angebote-grund/xyz",json={"code":"zu_teuer"}).status_code==404)
# Auswertung
au=a.get("/api/admin/belege-auswertung").json(); gz={g["code"]:g["anzahl"] for g in au["gruende"]}
chk("Auswertung zählt Gründe (angenommene nicht)",gz.get("zeitpunkt",0)>=2 and gz.get("umfang",0)>=1 and gz.get("keine_antwort",0)>=1 and gz.get("zu_teuer",0)==0,gz)
chk("Auswertung sortiert nach Anzahl",[g["anzahl"] for g in au["gruende"]]==sorted([g["anzahl"] for g in au["gruende"]],reverse=True))
# Kundenangebot und Rechte
kid,c=neuer_kunde("Grund")
bk=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"angebot","betreff":"Z","einleitung":"H","schluss":"D","positionen":pos}).json()["id"]
a.post(f"/api/admin/belege/{bk}/ausstellen",json={}); a.post(f"/api/admin/belege/{bk}/senden")
chk("Kundenangebot: Grund festhalten",a.post(f"/api/admin/angebote-grund/{bk}",json={"code":"intern","text":"Chef im Urlaub"}).status_code==200 and G(bk)=="intern|Chef im Urlaub")
chk("Kunde selbst darf nicht",c.post(f"/api/admin/angebote-grund/{bk}",json={"code":"zu_teuer"}).status_code in (401,403))
chk("Beleg-Seite liefert Grund und Anmerkung",a.get(f"/api/admin/belege/{bk}").json()["beleg"].get("grund_code")=="intern" and a.get(f"/api/admin/belege/{bk}").json()["beleg"].get("grund_text")=="Chef im Urlaub")
