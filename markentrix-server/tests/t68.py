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
sfx=str(int(time.time())+201)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import json, os, time
kA,cA,mA=neuer_kunde("Ps")
P=httpx.Client(base_url=B)   # ohne Anmeldung
SJ="/var/tmp/pt/b/queue/sicherungen.json"; alt=open(SJ).read() if os.path.exists(SJ) else None
import datetime
open(SJ,"w").write(json.dumps({"tage":[datetime.date.today().isoformat()]})); os.chmod(SJ,0o644)
# ---- Öffentlich
r=P.get("/status"); chk("Seite ohne Anmeldung erreichbar",r.status_code==200 and "Markentrix Status" in r.text,r.status_code)
chk("Seite: Bausteine genannt",all(x in r.text for x in ("Kunden-Portal","Datenbank","Kunden-Websites","E-Mail-Versand","Datensicherung")))
chk("Nicht indexierbar-Kopf ok / kein Caching",r.headers.get("cache-control")=="no-store")
j=P.get("/api/status").json(); chk("JSON: Stufe und Bausteine",j["stufe"] in ("ok","warn","bad") and len(j["komponenten"])==5,j)
sql("delete from website_wacht"); sql("delete from website_wacht_tag")
j=P.get("/api/status").json(); w=[k for k in j["komponenten"] if k["name"]=="Kunden-Websites"][0]; chk("Ohne Messung: kein Alarm",w["stufe"]=="ok")
# Websites messen: 2 ok, 1 gestört -> nur Zahlen, keine Namen
doms=[f"ps{i}{sfx}.de" for i in range(3)]
for i,d in enumerate(doms):
    sql(f"insert into websites (kunden_id, domain, art, status) values ('{kA}','{d}','live','live')")
    sql(f"insert into website_wacht (domain, kunden_id, ok, seite_ok, api_ok) values ('{d}','{kA}',{'true' if i<2 else 'false'},true,true)")
    sql(f"insert into website_wacht_tag (domain, tag, geprueft, ok) values ('{d}',current_date,10,{10 if i<2 else 5})")
j=P.get("/api/status").json(); w=[k for k in j["komponenten"] if k["name"]=="Kunden-Websites"][0]
chk("1 von 3 gestört: Warnung mit Zahlen",w["stufe"]=="warn" and "2 von 3" in w["text"],w); chk("Gesamt: eingeschränkt",j["stufe"]=="warn",j["stufe"])
t=P.get("/status").text; chk("Keine Kundendomains auf der öffentlichen Seite",not any(d in t for d in doms) and "Firma" not in t)
chk("Verfügbarkeit 30 Tage berechnet",j["verfuegbarkeit_30_tage"]==83.33,j["verfuegbarkeit_30_tage"])
sql("update website_wacht set ok=false"); j=P.get("/api/status").json(); chk("Mehrheit gestört: rot",j["stufe"]=="bad",j["stufe"])
sql("update website_wacht set ok=true"); sql(f"update website_wacht set geprueft_am=now()-interval '2 hours'")
j=P.get("/api/status").json(); chk("Veraltete Messung zählt nicht",[k for k in j["komponenten"] if k["name"]=="Kunden-Websites"][0]["text"]=="Keine Messung aktiv")
# ---- Meldungen
chk("Kunde darf keine Meldung anlegen",cA.post("/api/admin/statusmeldungen",json={"art":"info","titel":"x"}).status_code==403)
chk("Ohne Anmeldung gesperrt",P.post("/api/admin/statusmeldungen",headers=H,json={"art":"info","titel":"x"}).status_code in (401,403))
chk("Ungültige Art",a.post("/api/admin/statusmeldungen",json={"art":"boese","titel":"x"}).status_code==422)
chk("Leerer Titel",a.post("/api/admin/statusmeldungen",json={"art":"info","titel":""}).status_code==422)
r=a.post("/api/admin/statusmeldungen",json={"art":"stoerung","titel":"Portal langsam <b>x</b>","text":"Wir arbeiten dran & prüfen"}); chk("Störung angelegt",r.status_code==200,r.text); mid=r.json()["id"]
t=P.get("/status").text; j=P.get("/api/status").json()
chk("Störung erscheint, Seite rot",j["stufe"]=="bad" and "Aktuelle Meldungen" in t and "Portal langsam" in t)
chk("HTML in Meldung maskiert",("<b>x</b>" not in t) and "&lt;b&gt;x&lt;/b&gt;" in t)
r=a.post(f"/api/admin/statusmeldungen/{mid}/beenden"); chk("Beenden",r.status_code==200)
chk("Zweites Beenden: 404",a.post(f"/api/admin/statusmeldungen/{mid}/beenden").status_code==404)
t=P.get("/status").text; j=P.get("/api/status").json()
chk("Nach Ende: wieder grün, Eintrag im Verlauf",j["stufe"]=="ok" and "Letzte 30 Tage" in t and "Portal langsam" in t and "Aktuelle Meldungen" not in t,j["stufe"])
a.post("/api/admin/statusmeldungen",json={"art":"wartung","titel":"Wartung Sonntag","beginn":"2099-01-01T00:00:00+00:00"})
j=P.get("/api/status").json(); chk("Geplante Wartung in der Zukunft: noch grün",j["stufe"]=="ok")
a.post("/api/admin/statusmeldungen",json={"art":"wartung","titel":"Wartung jetzt"}); j=P.get("/api/status").json(); chk("Laufende Wartung: eingeschränkt",j["stufe"]=="warn")
l=a.get("/api/admin/statusmeldungen").json(); chk("Admin sieht die Liste",len(l)>=3)
chk("Löschen",a.delete(f"/api/admin/statusmeldungen/{mid}").status_code==200 and a.delete(f"/api/admin/statusmeldungen/{mid}").status_code==404)
chk("Ungültige ID: 404",a.post("/api/admin/statusmeldungen/xyz/beenden").status_code==404)
chk("Audit geschrieben",sql("select count(*) from audit_log where aktion='statusmeldung_neu'")>="3")
sql("delete from statusmeldungen"); sql("delete from website_wacht"); sql("delete from website_wacht_tag")
open(SJ,"w").write(json.dumps({"tage":[(datetime.date.today()-datetime.timedelta(days=5)).isoformat()]}))
j=P.get("/api/status").json(); b=[k for k in j["komponenten"] if k["name"]=="Datensicherung"][0]; chk("Alte Sicherung (5 Tage): Warnung",b["stufe"]=="warn",b)
(os.remove(SJ) if alt is None else open(SJ,'w').write(alt))
# ---- Rate-Limit
c=0
for i in range(130):
    if P.get("/api/status").status_code==429: c+=1
chk("Rate-Limit schützt die öffentliche Seite",c>0,c)
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1200,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+"/admin#websites"); await pg.wait_for_selector("h2:text-is('Statusseite')",timeout=8000)
        c=pg.locator(".card:has(h2:text-is('Statusseite'))"); await c.locator("input").first.fill("UI-Test Wartung"); await c.get_by_role("button",name="Meldung veröffentlichen").click()
        await c.get_by_text("Veröffentlicht.").wait_for(timeout=6000); await c.get_by_text("UI-Test Wartung").first.wait_for(timeout=6000); chk("UI: Meldung veröffentlicht und gelistet",True)
        await c.get_by_role("button",name="Beenden").first.click(); await c.get_by_text("beendet",exact=False).first.wait_for(timeout=6000); chk("UI: Meldung beendet",True)
        pub=await ctx.new_page(); await pub.set_viewport_size({"width":390,"height":800}); await pub.goto(B+"/status"); await pub.screenshot(path="/var/tmp/pt/shots/status.png",full_page=True)
        chk("UI: Statusseite am Handy ohne seitliches Scrollen",await pub.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
        chk("Keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
sql("delete from statusmeldungen")
print("FERTIG")
