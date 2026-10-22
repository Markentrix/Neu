import httpx, time, re, email, subprocess, io
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
sfx=str(int(time.time())+209)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import io, json, os, subprocess, zipfile, glob
kA,cA,mA=neuer_kunde("Wma"); kB,cB,mB=neuer_kunde("Wmb")
S="/var/tmp/pt/s"; Q="/var/tmp/pt/b/queue"
os.makedirs("/var/tmp/pt/b/caddy/sites",exist_ok=True); open("/var/tmp/pt/b/mode","w").write("extern")
def worker():
    r=subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":"/var/tmp/pt/b","MK_SITES":S},capture_output=True,text=True); return r.stdout+r.stderr
def zipb(dateien,**kw):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        for n,c in dateien.items(): z.writestr(n,c)
    return b.getvalue()
import json, os, sys, time, glob
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pt/db_dummy".replace("?host=/var/tmp/pt/db_dummy","?host=/var/tmp/pgtest"),PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0",QUEUE_DIR=Q)
from app import db, jobs
db.open_pool()
for x in glob.glob(S+"/live/.upload-*"): __import__("shutil").rmtree(x,ignore_errors=True)
for x in glob.glob(Q+"/auftrag-*.json"): os.unlink(x)
dom=f"melde{sfx}.de"; HTML="<!doctype html><html><body><h1>V{v}</h1></body></html>"
def hoch(v,name,kunde,info="1",txt="",art="live"):
    return a.post("/api/admin/websites/upload",files=[("datei",("s.zip",zipb({"index.html":HTML.format(v=v)}),"application/zip"))],data={"art":art,"name":name,"kunden_id":kunde,"dienste_skript":"0","kunde_informieren":info,"aenderung":txt})
mails_an=lambda adr,t="": mail_an(adr,t)
mA_adr=f"wma{sfx}@k.de"
# ---- Neue Website: erst online melden, wenn erreichbar
r=hoch(1,dom,kA,txt="Neue Startseite"); chk("Upload angenommen",r.status_code==200,r.text)
chk("Meldung vorgemerkt",sql(f"select count(*) from website_meldungen where domain='{dom}' and status='offen'")=="1")
jobs.website_online_meldungen({}); chk("Server-Dienst noch nicht fertig: keine Mail",sql(f"select status from website_meldungen where domain='{dom}'")=="offen")
worker(); n0=len(mails_an(mA_adr,"online"))
jobs.website_online_meldungen({}); time.sleep(1.2)
chk("Veröffentlicht, aber Domain noch nicht erreichbar: keine Mail",len(mails_an(mA_adr,"online"))==n0 and sql(f"select status from website_meldungen where domain='{dom}'")=="offen")
sql(f"insert into website_wacht (domain, kunden_id, ok, seite_ok, api_ok, geprueft_am) values ('{dom}','{kA}',false,false,false,now()) on conflict (domain) do update set ok=false, geprueft_am=now()")
jobs.website_online_meldungen({}); chk("Gestört: weiter warten",sql(f"select status from website_meldungen where domain='{dom}'")=="offen")
sql(f"update website_wacht set ok=true, seite_ok=true, api_ok=true, geprueft_am=now() where domain='{dom}'")
jobs.website_online_meldungen({}); time.sleep(1.2); mm=mails_an(mA_adr,"online")
chk("Erreichbar: „Website ist online“-Mail an den Kunden",len(mm)==n0+1 and dom in text(mm[-1]) and "Neue Startseite" in text(mm[-1]),mm and text(mm[-1]))
chk("Mail ohne KI-Namen und mit Portal-Link",mm and "Claude" not in text(mm[-1]) and "/app#nachrichten" in text(mm[-1]))
chk("Status gesendet",sql(f"select status from website_meldungen where domain='{dom}'")=="gesendet")
chk("Glocke beim Kunden",int(sql(f"select count(*) from benachrichtigungen b join benutzer u on u.id=b.benutzer_id where u.kunden_id='{kA}' and b.tag='websiteonline'") or 0)>=1)
jobs.website_online_meldungen({}); time.sleep(1.2); chk("Nicht doppelt",len(mails_an(mA_adr,"online"))==n0+1)
# ---- Update einer bestehenden Seite
u0=len(mails_an(mA_adr,"aktualisiert"))
r=hoch(2,dom,kA,txt="Öffnungszeiten und neues Foto"); worker(); jobs.website_online_meldungen({}); time.sleep(1.2); mm=mails_an(mA_adr,"aktualisiert")
chk("Update: „aktualisiert“-Mail mit Hinweis",len(mm)==u0+1 and "Öffnungszeiten und neues Foto" in text(mm[-1]) and "online" in text(mm[-1]),mm and text(mm[-1]))
chk("Update-Mail nennt nicht „neue Website“","neue Website" not in text(mm[-1]))
# ---- Ohne Haken: keine Mail
c0=sql("select count(*) from website_meldungen")
r=hoch(3,dom,kA,info="0"); chk("Ohne Haken: nichts vorgemerkt",sql("select count(*) from website_meldungen")==c0); worker()
# ---- Demo: nie
r=hoch(1,f"demo{sfx}",None,info="1",art="demo"); chk("Demo-Upload ok",r.status_code==200,r.text); worker()
chk("Demo: keine Kundenmeldung",sql(f"select count(*) from website_meldungen where domain='demo{sfx}'")=="0")
# ---- Fehlgeschlagen / verschollen
sql(f"insert into website_meldungen (kunden_id, domain, upload_id, hinweis) values ('{kA}','{dom}','{'a'*16}','')")
sql(f"insert into website_meldungen (kunden_id, domain, upload_id, hinweis, erstellt_am) values ('{kA}','{dom}','{'b'*16}','',now()-interval '3 hours')")
sql(f"insert into website_meldungen (kunden_id, domain, upload_id, hinweis) values ('{kA}','{dom}','{'c'*16}','')")
open(f"{Q}/ergebnis-{'c'*16}.json","w").write(json.dumps({"ok":False,"text":"Fehlgeschlagen","aktion":"veroeffentlichen","art":"live","name":dom})); os.chmod(f"{Q}/ergebnis-{'c'*16}.json",0o644)
u1=len(mails_an(mA_adr,"aktualisiert")); jobs.website_online_meldungen({}); time.sleep(1.2)
st=lambda c: sql(f"select status from website_meldungen where upload_id='{c*16}'")
chk("Noch ohne Ergebnis: wartet",st("a")=="offen"); chk("Ergebnis nach 2 Stunden nicht da: verworfen",st("b")=="verworfen"); chk("Fehlgeschlagene Veröffentlichung: keine Mail, verworfen",st("c")=="verworfen" and len(mails_an(mA_adr,"aktualisiert"))==u1)
# ---- Kunde hat Benachrichtigungen abgeschaltet / Fremder Kunde bekommt nichts
sql(f"update kunden set benachr_nachrichten=false where id='{kA}'")
domB=f"meldeb{sfx}.de"; kBadr=f"wmb{sfx}@k.de"; b0=len(mails_an(kBadr,"")); a0=len(mails_an(mA_adr,"aktualisiert"))
r=hoch(1,dom,kA,txt="x"); worker(); jobs.website_online_meldungen({}); time.sleep(1.2)
chk("Benachrichtigungen aus: keine Mail, aber erledigt",len(mails_an(mA_adr,"aktualisiert"))==a0 and sql(f"select count(*) from website_meldungen where domain='{dom}' and hinweis='x' and status='offen'")=="0")
chk("Anderer Kunde bekommt nichts",len(mails_an(kBadr,""))==b0)
# ---- Demo -> Live mit Meldung
D=f"{S}/demos/dl{sfx}"; os.makedirs(D,exist_ok=True); open(D+"/index.html","w").write("<html><body>x</body></html>")
sql(f"update kunden set benachr_nachrichten=true where id='{kA}'")
dl=f"dlm{sfx}.de"; r=a.post("/api/admin/websites/demo-zu-live",json={"demo":f"dl{sfx}","domain":dl,"kunden_id":kA,"trotzdem":True,"aenderung":"Aus der Vorschau"}); chk("Demo live geschaltet",r.status_code==200,r.text)
chk("Meldung für Demo→Live vorgemerkt",sql(f"select hinweis from website_meldungen where domain='{dl}'")=="Aus der Vorschau")
worker(); sql(f"insert into website_wacht (domain, kunden_id, ok, seite_ok, api_ok) values ('{dl}','{kA}',true,true,true)"); jobs.website_online_meldungen({}); time.sleep(1.2)
chk("Demo→Live: Online-Mail",any(dl in text(m) for m in mails_an(mA_adr,"online")))
chk("Audit vermerkt Benachrichtigung",sql(f"select count(*) from audit_log where aktion='website_hochgeladen' and details->>'kunde_informiert'='true'")>="3")
for x in glob.glob(Q+"/auftrag-*.json"): os.unlink(x)
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1300,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+"/admin#websites"); await pg.wait_for_selector("h2:text-is('Website hochladen')",timeout=8000)
        c=pg.locator(".card:has(h2:text-is('Website hochladen'))")
        chk("UI: Haken „Kunden informieren“ standardmäßig an",await c.get_by_label("Kunden per Mail und Glocke informieren",exact=False).is_checked())
        chk("UI: Feld „Was wurde geändert?“",await c.locator("input[placeholder^='Was wurde geändert']").count()==1)
        chk("Keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
print("FERTIG")
