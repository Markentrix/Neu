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
sfx=str(int(time.time())+161)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, os, sys
sys.path.insert(0,"/home/claude/markentrix-server/portal")
Q="/var/tmp/pt/b/queue"; DNS="/var/tmp/pt/dns.json"
kA,cA,mA=neuer_kunde("Dmaila")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0",DNS_TEST_DATEI=DNS,QUEUE_DIR=Q)
from app import db, domaincheck, jobs, webbetrieb
db.open_pool()
dom=f"dmail{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
import pathlib
pathlib.Path(f"/var/tmp/pt/s/live/{dom}").mkdir(parents=True,exist_ok=True); open(f"/var/tmp/pt/s/live/{dom}/index.html","w").write("<h1>x</h1>")
json.dump({"v4":"203.0.113.5"},open(Q+"/serverip.json","w"))
json.dump({f"{dom}|A":["198.185.159.144"],f"www.{dom}|A":["198.185.159.144"],f"{dom}|NS":["ns1.ui-dns.de"]},open(DNS,"w"))
# ---- Status "wartet auf DNS"
webbetrieb.wacht(None,True)
w=[x for x in a.get("/api/admin/websites").json()["aktiv"] if x["name"]==dom]
chk("Neue Seite ohne DNS: wartet auf DNS, kein Ausfall",bool(w) and w[0]["wacht"] and w[0]["wacht"]["ok"] is False and w[0]["wacht"]["wartet_dns"] is True,w)
chk("Kein Alarm-Marker (gemeldet=false)",sql(f"select gemeldet from website_wacht where domain='{dom}'")=="f")
# ---- Jetzt prüfen
chk("Jetzt prüfen: ohne Anmeldung gesperrt",httpx.post(B+"/api/admin/websites/jetzt-pruefen",headers=H,json={"domain":dom}).status_code in (401,403))
chk("Jetzt prüfen: Kunde gesperrt",cA.post("/api/admin/websites/jetzt-pruefen",json={"domain":dom}).status_code==403)
chk("Jetzt prüfen: ungültige Domain",a.post("/api/admin/websites/jetzt-pruefen",json={"domain":"x..y"}).status_code==400)
chk("Jetzt prüfen: unbekannte Domain",a.post("/api/admin/websites/jetzt-pruefen",json={"domain":"gibtesnicht-xyz.de"}).status_code==404)
r=a.post("/api/admin/websites/jetzt-pruefen",json={"domain":dom}).json()
chk("Jetzt prüfen bei falscher DNS: zustand dns mit Schritten",r["zustand"]=="dns" and r["dns"]["schritte"] and "203.0.113.5" in " ".join(r["dns"]["schritte"]),r)
json.dump({f"{dom}|A":["203.0.113.5"],f"www.{dom}|A":["203.0.113.5"]},open(DNS,"w"))
import glob
for f in glob.glob(Q+"/auftrag-*.json"):
    if "caddy_neu_laden" in open(f).read(): os.remove(f)
r=a.post("/api/admin/websites/jetzt-pruefen",json={"domain":dom}).json()
chk("Sobald die DNS stimmt, wird der Webserver zum Neuversuch des Zertifikats angestoßen",any("caddy_neu_laden" in open(f).read() for f in glob.glob(Q+"/auftrag-*.json")))
chk("TLS-Fehler wird verständlich erklärt","Zertifikat" in webbetrieb._klartext("nicht erreichbar ([SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error)") and webbetrieb._klartext("anderer Fehler")=="anderer Fehler")
chk("Jetzt prüfen bei richtiger DNS, Seite noch nicht da: zustand seite",r["zustand"]=="seite" and r["dns"]["ok"] is True,r)
chk("DNS-Stand wurde gespeichert",sql(f"select ok from domain_pruefung where domain='{dom}'")=="t")
# ---- DNS-Anleitung an Kunden
json.dump({f"{dom}|A":["198.185.159.144"],f"www.{dom}|A":["198.185.159.144"],f"{dom}|NS":["ns1.ui-dns.de"]},open(DNS,"w"))
chk("Kundenmail: Kunde gesperrt",cA.post(f"/api/admin/websites/domain/{dom}/kundenmail").status_code==403)
chk("Kundenmail: ungültige Domain",a.post("/api/admin/websites/domain/x..y/kundenmail").status_code==400)
n0=len(mail_an(mA))
r=a.post(f"/api/admin/websites/domain/{dom}/kundenmail"); chk("Kundenmail wird gesendet",r.status_code==200 and mA in r.json()["hinweis"],r.text)
m=mail_an(mA,"Umstellung"); chk("Mail kam beim Kunden an mit IP und Signatur",len(m)==1 and "203.0.113.5" in text(m[-1]) and "Ihr Markentrix-Team" in text(m[-1]),[text(x)[:100] for x in m])
chk("Absender-Name ohne KI-Bezug",all("Claude" not in text(x) for x in m))
chk("Zeitpunkt gespeichert",sql(f"select kundenmail_am is not null from domain_pruefung where domain='{dom}'")=="t")
g=a.get(f"/api/admin/websites/domain/{dom}").json(); chk("Prüfung zeigt letzten Versand",g["kundenmail_am"] is not None and g["erinnerungen"]==0,g)
# ---- Erinnerung
jobs.domain_erinnern(); chk("Noch keine Erinnerung vor 3 Tagen",sql(f"select erinnerungen from domain_pruefung where domain='{dom}'")=="0")
sql(f"update domain_pruefung set kundenmail_am=now()-interval '4 days' where domain='{dom}'")
jobs.domain_erinnern(); time.sleep(1.2)
chk("Erinnerung nach 3 Tagen",sql(f"select erinnerungen from domain_pruefung where domain='{dom}'")=="1")
m=mail_an(mA,"Erinnerung"); chk("Erinnerungsmail",len(m)==1 and "kurze Erinnerung" in text(m[-1]),[text(x)[:120] for x in m])
jobs.domain_erinnern(); chk("Nicht gleich nochmal",sql(f"select erinnerungen from domain_pruefung where domain='{dom}'")=="1")
sql(f"update domain_pruefung set erinnert_am=now()-interval '4 days' where domain='{dom}'"); jobs.domain_erinnern()
chk("Zweite Erinnerung",sql(f"select erinnerungen from domain_pruefung where domain='{dom}'")=="2")
sql(f"update domain_pruefung set erinnert_am=now()-interval '4 days' where domain='{dom}'"); jobs.domain_erinnern()
chk("Höchstens zwei Erinnerungen",sql(f"select erinnerungen from domain_pruefung where domain='{dom}'")=="2")
# ---- stimmt DNS, gibt es keine Mail mehr
json.dump({f"{dom}|A":["203.0.113.5"],f"www.{dom}|A":["203.0.113.5"]},open(DNS,"w"))
r=a.post(f"/api/admin/websites/domain/{dom}/kundenmail"); chk("Bei richtiger DNS keine Anleitung",r.status_code==400 and "schon" in r.text,r.text)
sql(f"update domain_pruefung set ok=false, erinnerungen=0, erinnert_am=NULL, kundenmail_am=now()-interval '9 days' where domain='{dom}'")
jobs.domain_erinnern(); chk("Keine Erinnerung, wenn die Domain inzwischen stimmt",sql(f"select erinnerungen from domain_pruefung where domain='{dom}'")=="0")
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
json.dump({f"{dom}|A":["198.185.159.144"],f"www.{dom}|A":["198.185.159.144"],f"{dom}|NS":["ns1.ui-dns.de"]},open(DNS,"w"))
sql(f"delete from website_wacht_tag where domain='{dom}'"); sql(f"update domain_pruefung set ok=false where domain='{dom}'")
webbetrieb.wacht(None,True)
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1300,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+"/admin#websites"); await pg.wait_for_selector("h2:text-is('Website hochladen')",timeout=8000)
        zeile=pg.locator("tr").filter(has=pg.get_by_role("button",name="DNS prüfen")).filter(has_text=dom).first
        await zeile.get_by_text("wartet auf DNS").wait_for(timeout=8000); chk("UI: Status wartet auf DNS statt gestört",await zeile.get_by_text("gestört").count()==0)
        pg.on("dialog",lambda d: asyncio.ensure_future(d.accept()))
        await zeile.get_by_role("button",name="DNS prüfen").click(); await pg.get_by_role("button",name="An Kunden mailen").wait_for(timeout=8000); chk("UI: Knopf An Kunden mailen",True)
        await pg.get_by_role("button",name="An Kunden mailen").click(); await pg.get_by_text("Gesendet ✓").wait_for(timeout=8000); chk("UI: Versand bestätigt",True)
        await zeile.get_by_role("button",name="Jetzt prüfen").click(); await pg.get_by_text("zeigt noch nicht").first.wait_for(timeout=10000); chk("UI: Jetzt prüfen meldet das Ergebnis",True)
        await pg.screenshot(path="/var/tmp/pt/shots/dns_admin.png",full_page=True)
        chk("Keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
print("FERTIG")
