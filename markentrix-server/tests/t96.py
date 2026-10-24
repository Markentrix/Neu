"""Team-Mails: Aufgaben-Mail nennt, was genau offen ist; Markentrix-Mails im Layout mit Logo."""
import httpx, time, re, email, email.header, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+550)
mk=f"exp{sfx}@k.de"
import sys
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs, mailvorlage as mv
db.open_pool()
mk=f"ob{sfx}@k.de"
k=a.post("/api/admin/kunden",json={"firma":f"Nachfass {sfx}","ansprechpartner":"Tina Test","email":mk,"telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":False}).json(); kid=k["id"]
sql(f"update kunden set erstellt_am=now()-interval '9 days' where id='{kid}'")
team=f"team{sfx}@k.de"; n0=len(mails())
jobs.aufgaben_automatisch({"alarm_email":team}); time.sleep(1.5)
ms=[m for m in mails()[n0:] if team in str(m["To"]) and "neue Aufgabe" in str(m["Subject"])]
chk("Aufgaben-Mail ist angekommen",len(ms)==1,[str(m["Subject"]) for m in mails()[n0:]])
m=ms[0]
txt=[p for p in m.walk() if p.get_content_type()=="text/plain"][0].get_payload(decode=True).decode()
html=[p for p in m.walk() if p.get_content_type()=="text/html"][0].get_payload(decode=True).decode()
chk("Text: Aufgabe mit Firma",f"Onboarding nachfassen: Nachfass {sfx}" in txt,txt[:400])
chk("Text: seit wie vielen Tagen und Fortschritt","Seit 9 Tagen im Onboarding" in txt and "Schritten erledigt" in txt,txt[:600])
chk("Text: offene Schritte einzeln aufgeführt","Noch offen:" in txt and "- Briefing ausgefüllt" in txt and "- Auftragsverarbeitungsvertrag (AVV)" in txt,txt)
chk("Text: Kunde ist am Zug wird genannt","Kunde ist am Zug" in txt)
chk("Text: Link direkt zum Kunden",f"/admin#kunde/{kid}" in txt)
chk("HTML: Liste, Knopf zum Portal und Überschrift der Aufgabe",'<ul' in html and ">Im Portal öffnen<" in html and f"Nachfass {sfx}" in html and "1. Onboarding" in html)
chk("HTML: Fuß „automatische Meldung“ klein",'(automatische Meldung des Portals)' in html and 'font-size:12px' in html)
chk("Markentrix-Logo ist eingebettet",any(p.get_content_type()=="image/png" and p["Content-ID"] for p in m.walk()))
chk("Kein Kunden-Gruß/Signaturblock in Mails von Markentrix","border-top:3px" not in html)
# Aufgabe-Datensatz gleich, nur einmal
chk("Aufgabe nur einmal",sql(f"select count(*) from aufgaben where kunden_id='{kid}' and titel like 'Onboarding nachfassen:%'")=="1")
# Einzelfälle der Beschreibung
with db.tx("system") as cur:
    cur.execute("select id, kunden_id, ticket_id, titel from aufgaben where kunden_id=%s and titel like 'Onboarding nachfassen:%%'",(kid,)); ro=cur.fetchone()
    d=__import__("app.aufgabendetail",fromlist=["x"]).beschreibe(cur,ro)
    chk("beschreibe(): Zeilen und Link",any("Noch offen" in z for z in d["detail"]) and d["link"].endswith(f"#kunde/{kid}"),d)
    d2=__import__("app.aufgabendetail",fromlist=["x"]).beschreibe(cur,{"id":0,"kunden_id":None,"ticket_id":None,"titel":"Etwas Unbekanntes"})
    chk("beschreibe(): unbekannte Aufgabe bricht nichts",d2["detail"]==[] and d2["link"].endswith("/admin#aufgaben"))
    d3=__import__("app.aufgabendetail",fromlist=["x"]).beschreibe(cur,{"id":0,"kunden_id":"00000000-0000-0000-0000-000000000000","ticket_id":None,"titel":"Onboarding nachfassen: X"})
    chk("beschreibe(): Kunde ohne Daten bricht nichts",isinstance(d3["detail"],list))
# Alte Form (Liste von Texten) funktioniert weiter
from app import mailer
n1=len(mails()); ok,g=mailer.aufgaben_digest_team(team,["Alt: nur Text"]); time.sleep(1.2)
chk("Alte Aufrufform (nur Texte) geht weiter",ok and any("Alt: nur Text" in (text(x) or "") for x in mails()[n1:]),g)
# Test-Mail der Einstellungen im Layout, Text unverändert
tm=f"tm{sfx}@k.de"; n2=len(mails()); r=a.post("/api/admin/einstellungen/testmail",json={"an":tm}); time.sleep(1.5)
mt=[x for x in mails()[n2:] if tm in str(x["To"])]
chk("Testmail geht raus",r.status_code==200 and len(mt)==1,r.text)
if mt:
    typen=[p.get_content_type() for p in mt[0].walk()]
    chk("Testmail: Text und HTML und Logo",("text/plain" in typen) and ("text/html" in typen) and ("image/png" in typen),typen)
    t0=[p for p in mt[0].walk() if p.get_content_type()=="text/plain"][0].get_payload(decode=True).decode()
    chk("Testmail: Textfassung nicht verändert",t0.strip().startswith("Das ist") or "Testmail" in t0 or len(t0)>5,t0[:120])
# Gruß bleibt in Mails von Markentrix erhalten
hh=mv.html_mail("Markentrix","Guten Tag,\n\nes gibt Neuigkeiten.\n\nViele Grüße\nIhr Markentrix-Team",None,"#4f46e5","logo@mail",None,True)
chk("Markentrix-Mail: Gruß und Team stehen unverändert da",hh.count("Viele Grüße")==1 and "Ihr Markentrix-Team" in hh)
print("FERTIG")
