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
sfx=str(int(time.time())+185)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import io, json, os, subprocess, zipfile, glob
kA,cA,mA=neuer_kunde("Dla"); kB,cB,mB=neuer_kunde("Dlb")
S="/var/tmp/pt/s"; Q="/var/tmp/pt/b/queue"
os.makedirs("/var/tmp/pt/b/caddy/sites",exist_ok=True); open("/var/tmp/pt/b/mode","w").write("extern")
def worker():
    r=subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":"/var/tmp/pt/b","MK_SITES":S},capture_output=True,text=True); return r.stdout+r.stderr
def zipb(dateien,**kw):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        for n,c in dateien.items(): z.writestr(n,c)
    return b.getvalue()
sys_path=__import__("sys").path; sys_path.insert(0,"/home/claude/markentrix-server/portal")
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) values ('{kA}','website',true) on conflict do nothing"); sql(f"update kunden_module set aktiv=true where kunden_id='{kA}' and modul_code='website'")
demo=f"demo{sfx}"; import shutil
for x in glob.glob(S+"/live/.upload-*"): shutil.rmtree(x,ignore_errors=True)
for x in glob.glob(Q+"/auftrag-*.json"): os.unlink(x)
dom=f"dlive{sfx}.de"; dom2=f"dlive2{sfx}.de"
import pathlib
D=pathlib.Path(S)/"demos"/demo; (D/"css").mkdir(parents=True,exist_ok=True)
(D/"index.html").write_text('<!doctype html><html><body><h1>Demo</h1><script src="https://portal.markentrix.de/static/js/site.js" data-site="mk_FREMDEKENNUNG" defer></script></body></html>')
(D/"css"/"a.css").write_text("body{}"); (D/"site.json").write_text(json.dumps({"typ":"demo","name":demo,"kunde":"x"})); (D/"angebote").mkdir(exist_ok=True); (D/"angebote"/"w.json").write_text("{}")
(D/".git").mkdir(exist_ok=True); (D/".git"/"config").write_text("x")
J=lambda **k: a.post("/api/admin/websites/demo-zu-live",json=k)
# ---- Schutz
chk("Kunde darf nicht",cA.post("/api/admin/websites/demo-zu-live",json={"demo":demo,"domain":dom,"kunden_id":kA}).status_code==403)
chk("Ohne Anmeldung gesperrt",httpx.post(B+"/api/admin/websites/demo-zu-live",headers=H,json={"demo":demo,"domain":dom}).status_code in (401,403))
chk("Unbekannte Demo",J(demo="gibtesnicht",domain=dom,kunden_id=kA).status_code==404)
chk("Ungültige Domain",J(demo=demo,domain="kein domain",kunden_id=kA).status_code==400)
chk("Ungültiger Demo-Name",J(demo="../etc",domain=dom,kunden_id=kA).status_code==400)
chk("Neue Live-Website braucht einen Kunden",J(demo=demo,domain=dom).status_code==400)
chk("Nichts liegen geblieben",not glob.glob(S+"/live/.upload-*") and not glob.glob(Q+"/auftrag-*.json"))
# ---- Freigabe-Schutz
sql(f"insert into kundenfreigaben (kunden_id, titel, art, inhalt, demo_name, status) values ('{kA}','Vorschau','website','x','{demo}','wartet')")
r=J(demo=demo,domain=dom,kunden_id=kA); chk("Nicht freigegeben: Rückfrage (409)",r.status_code==409 and "trotzdem" in r.text and "noch nicht freigegeben" in r.text,r.text)
chk("Nach der Rückfrage nichts angelegt",not glob.glob(S+"/live/.upload-*") and not glob.glob(Q+"/auftrag-*.json") and sql(f"select count(*) from websites where domain='{dom}'")=="0")
r=J(demo=demo,domain=dom,kunden_id=kA,trotzdem=True); chk("Mit Bestätigung trotzdem möglich",r.status_code==200 and r.json()["freigabe"]=="wartet",r.text)
out=worker(); chk("Server-Dienst veröffentlicht",os.path.isfile(f"{S}/live/{dom}/index.html") and "veröffentlicht" in out,out)
sid=cA.get("/api/kunde/website-dienste").json()["site_id"]; idx=open(f"{S}/live/{dom}/index.html").read()
chk("Kennung des Demo-Skripts auf die des Kunden gesetzt",f'data-site="{sid}"' in idx and "FREMDEKENNUNG" not in idx and idx.count("site.js")==1,idx)
chk("CSS übernommen, Reste draußen (.git, Wochenangebote der Demo)",os.path.isfile(f"{S}/live/{dom}/css/a.css") and not os.path.exists(f"{S}/live/{dom}/.git") and not os.path.exists(f"{S}/live/{dom}/angebote/w.json"))
chk("Eigene site.json der Live-Seite (Typ live, nicht von der Demo)",json.load(open(f"{S}/live/{dom}/site.json"))["typ"]=="live")
chk("Webserver-Eintrag angelegt",os.path.isfile(f"/var/tmp/pt/b/caddy/sites/{dom}.caddy"))
chk("Demo selbst bleibt unverändert",(D/"index.html").is_file() and "FREMDEKENNUNG" in (D/"index.html").read_text())
chk("Website beim Kunden eingetragen",sql(f"select kunden_id from websites where domain='{dom}'")==kA)
chk("Audit nennt die Demo",sql(f"select count(*) from audit_log where aktion='website_hochgeladen' and details->>'aus_demo'='{demo}'")=="1")
# ---- freigegeben: ohne Rückfrage, zweites Ziel
sql(f"update kundenfreigaben set status='freigegeben' where demo_name='{demo}'")
r=J(demo=demo,domain=dom2,kunden_id=kA); chk("Freigegeben: ohne Rückfrage",r.status_code==200 and r.json()["freigabe"]=="freigegeben",r.text)
worker()
# ---- Update einer bestehenden Live-Seite: Kunde bleibt, vorige Version gesichert
(D/"index.html").write_text('<!doctype html><html><body><h1>Demo NEU</h1></body></html>')
r=J(demo=demo,domain=dom2); chk("Bestehende Domain: Kunde wird erkannt",r.status_code==200,r.text)
worker(); chk("Neue Version online",("Demo NEU" in open(f"{S}/live/{dom2}/index.html").read()))
chk("Vorige Version gesichert",bool(glob.glob(S+f"/.vorversionen/*__live__{dom2}")))
r=J(demo=demo,domain=dom2,kunden_id=kB); chk("Domain eines anderen Kunden: abgelehnt",r.status_code==400 and "anderen Kunden" in r.text,r.text)
# ---- Symlink in der Demo
os.symlink("/etc/passwd",str(D/"link.txt")); r=J(demo=demo,domain=f"dlive3{sfx}.de",kunden_id=kA,trotzdem=True); chk("Symlink in der Demo: abgelehnt",r.status_code==400 and "Symlink" in r.text,r.text)
chk("Nach Ablehnung nichts liegen geblieben",not glob.glob(S+"/live/.upload-*")); os.unlink(str(D/"link.txt"))
def sqlf(q):
    open("/var/tmp/q66.sql","w").write(q); os.chmod("/var/tmp/q66.sql",0o644)
    return subprocess.run(["su","postgres","-c","psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -f /var/tmp/q66.sql"],capture_output=True,text=True).stdout.strip()
# ---- Kunden-Sicht: Domain-Stand
DNS="/var/tmp/pt/dns.json"
chk("Domain-Stand: Kunde B sieht nichts von A",cB.get("/api/kunde/website-dienste/domains").json()["domains"]==[])
z={x["domain"]:x for x in cA.get("/api/kunde/website-dienste/domains").json()["domains"]}
chk("Neue Seite ohne Prüfung: wird eingerichtet",z[dom]["stand"]=="neu",z[dom])
erg=json.dumps({"schritte":["A-Eintrag für "+dom+" auf 203.0.113.5 setzen.","Danach prüfen, dass keine Weiterleitung aktiv ist."],"dns_anbieter":"IONOS","server_ipv4":["203.0.113.5"]}).replace("'","''")
sqlf(f"insert into domain_pruefung (domain, kunden_id, ok, ergebnis) values ('{dom}','{kA}',false,'{erg}')")
z={x["domain"]:x for x in cA.get("/api/kunde/website-dienste/domains").json()["domains"]}
chk("DNS offen: wartet auf Umstellung mit Schritten ohne interne Hinweise",z[dom]["stand"]=="wartet_dns" and len(z[dom]["schritte"])==1 and z[dom]["dns_anbieter"]=="IONOS" and "203.0.113.5" in z[dom]["schritte"][0],z[dom])
chk("Text in du-Form",all("Ihre" not in z[dom][k] for k in ("titel","text")),z[dom])
sql(f"update domain_pruefung set ok=true where domain='{dom}'")
sql(f"insert into website_wacht (domain, kunden_id, ok, fehler) values ('{dom}','{kA}',false,'Startseite nicht erreichbar (kein Zertifikat)')")
z={x["domain"]:x for x in cA.get("/api/kunde/website-dienste/domains").json()["domains"]}
chk("DNS ok, Zertifikat fehlt noch: HTTPS wird eingerichtet",z[dom]["stand"]=="zertifikat" and z[dom]["schritte"]==[],z[dom])
sql(f"update website_wacht set fehler='Startseite antwortet mit Fehler 500' where domain='{dom}'")
z={x["domain"]:x for x in cA.get("/api/kunde/website-dienste/domains").json()["domains"]}
chk("Sonst: gestört, ohne technische Einzelheiten",z[dom]["stand"]=="gestoert" and "Fehler 500" not in json.dumps(z[dom]),z[dom])
sql(f"update website_wacht set ok=true, fehler=NULL where domain='{dom}'")
z={x["domain"]:x for x in cA.get("/api/kunde/website-dienste/domains").json()["domains"]}
chk("Erreichbar: live",z[dom]["stand"]=="live" and z[dom]["seit"] is not None,z[dom])
# ---- Mehrere ZIPs
def upm(teile,name,kunde=None):
    return a.post("/api/admin/websites/upload",files=[("datei",(f"z{i}.zip",d,"application/zip")) for i,d in enumerate(teile,1)],data={"art":"live","name":name,"kunden_id":kunde or "","dienste_skript":"1"})
dm=f"mehr{sfx}.de"
z1=zipb({"index.html":"<html><body><h1>Teil1</h1><img src='bild.png'></body></html>","css/a.css":"body{}"})
z2=zipb({"bild.png":"PNG","css/b.css":"p{}","css/a.css":"body{color:red}"})
r=upm([z1,z2],dm,kA); chk("Zwei ZIPs werden zusammengeführt",r.status_code==200 and r.json()["dateien"]==5,r.text)
worker()
chk("Teile beider ZIPs online",os.path.isfile(f"{S}/live/{dm}/index.html") and os.path.isfile(f"{S}/live/{dm}/bild.png") and os.path.isfile(f"{S}/live/{dm}/css/b.css"))
chk("Später gewählte ZIP ersetzt gleichnamige Datei",open(f"{S}/live/{dm}/css/a.css").read()=="body{color:red}")
z3=zipb({"seite.html":"x"}); chk("Reihenfolge egal: index.html in der zweiten ZIP",upm([z2,z1],dm+"x" if False else f"mehr2{sfx}.de",kA).status_code==200); worker()
r=upm([z2,z3],f"mehr3{sfx}.de",kA); chk("Keine index.html in keiner ZIP: abgelehnt",r.status_code==400 and "index.html" in r.text,r.text)
r=upm([z1,zipb({"x.php":"<?php"})],f"mehr3{sfx}.de",kA); chk("Fehler nennt die betroffene ZIP",r.status_code==400 and "ZIP 2" in r.text,r.text)
r=upm([z1,b"keine zip"],f"mehr3{sfx}.de",kA); chk("Defekte zweite ZIP abgelehnt",r.status_code==400 and "ZIP 2" in r.text,r.text)
chk("Nach Ablehnung nichts liegen geblieben",not glob.glob(S+"/live/.upload-*") and not os.path.exists(f"{S}/live/mehr3{sfx}.de"))
r=upm([z1]*11,f"mehr3{sfx}.de",kA); chk("Mehr als 10 ZIPs abgelehnt",r.status_code==400)
# ---- Papierkorb endgültig löschen
KORB=pathlib.Path(S)/".papierkorb"
ids=[f"20260101-0000{i:02d}__live__korb{i}{sfx}.de" for i in (1,2)]+[f"20260101-000003__demo__korbd{sfx}"]
for t in ids: (KORB/t).mkdir(parents=True,exist_ok=True); (KORB/t/"index.html").write_text("x")
chk("Kunde darf Papierkorb nicht leeren",cA.post("/api/admin/websites/papierkorb-loeschen",json={"alle":True}).status_code==403)
chk("Ungültige ID abgelehnt",a.post("/api/admin/websites/papierkorb-loeschen",json={"id":"../../etc"}).status_code==404)
chk("Unbekannter Eintrag: 404",a.post("/api/admin/websites/papierkorb-loeschen",json={"id":"20260101-999999__live__gibtsnicht.de"}).status_code==404)
chk("Papierkorb listet Einträge",{x["id"] for x in a.get("/api/admin/websites").json()["papierkorb"]}>=set(ids))
r=a.post("/api/admin/websites/papierkorb-loeschen",json={"id":ids[0]}); chk("Einzelnen Eintrag löschen",r.status_code==200,r.text)
worker(); chk("Nur dieser Eintrag ist weg",not (KORB/ids[0]).exists() and (KORB/ids[1]).exists() and (KORB/ids[2]).exists())
chk("Audit geschrieben",sql("select count(*) from audit_log where aktion='papierkorb_geloescht'")>="1")
a.post("/api/admin/websites/papierkorb-loeschen",json={"alle":True}); worker(); chk("Papierkorb leeren",not any(KORB.iterdir()))
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip(); KPW="InhaberPasswort1"
dui=f"mehr2{sfx}.de"; sqlf(f"insert into domain_pruefung (domain, kunden_id, ok, ergebnis) values ('{dui}','{kA}',false,'{erg}')")
demo2=f"demoui{sfx}"; D2=pathlib.Path(S)/"demos"/demo2; D2.mkdir(parents=True,exist_ok=True); (D2/"index.html").write_text("<html><body><h1>UI</h1></body></html>"); (D2/"site.json").write_text(json.dumps({"typ":"demo","name":demo2,"kunde":""}))
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1300,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+"/admin#websites"); await pg.wait_for_selector("h2:text-is('Website hochladen')",timeout=8000)
        zeile=pg.locator("tr").filter(has_text=demo2).first
        await zeile.get_by_role("button",name="Live schalten").click(); await pg.wait_for_selector(".dlg",timeout=6000)
        chk("UI: Dialog zeigt Freigabe-Hinweis",await pg.get_by_text("keine Freigabe-Anfrage").count()>=1)
        await pg.locator(".dlg input").first.fill(f"ui{sfx}.de"); await pg.locator(".dlg select").select_option(index=1)
        pg.on("dialog",lambda d: asyncio.ensure_future(d.accept()))
        await pg.locator(".dlg").get_by_role("button",name="Jetzt live schalten").click(); await pg.get_by_text("wird innerhalb einer Minute als").wait_for(timeout=8000); chk("UI: Live-Schalten bestätigt",True)
        await pg.screenshot(path="/var/tmp/pt/shots/demo_live.png",full_page=True)
        ctx2=await br.new_context(viewport={"width":420,"height":900},bypass_csp=True); k=await ctx2.new_page(); e2=[]; k.on("pageerror",lambda e:e2.append(str(e)))
        await k.goto(B+"/"); await k.fill("#e",mA); await k.fill("#p",KPW); await k.click("#b"); await k.wait_for_url("**/app*")
        await k.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"); await k.goto(B+"/app#dienste")
        try: await k.wait_for_selector("#domain-stand",timeout=8000)
        except Exception: chk("UI Kunde: Domain-Stand mit Anleitung sichtbar",await k.locator("#domain-stand").get_by_text("Wartet auf die Umstellung deiner Domain").count()>=1 and "A-Eintrag für" in await k.inner_text("#domain-stand"))
        await k.screenshot(path="/var/tmp/pt/shots/domain_kunde.png",full_page=True)
        chk("Keine JS-Fehler",not errs and not e2,errs+e2); await br.close()
asyncio.run(main())
worker(); print("FERTIG")
