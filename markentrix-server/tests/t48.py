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
sfx=str(int(time.time())+73)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import io, json, os, subprocess, zipfile, glob
kA,cA,mA=neuer_kunde("Upa"); kB,cB,mB=neuer_kunde("Upb")
S="/var/tmp/pt/s"; Q="/var/tmp/pt/b/queue"
os.makedirs("/var/tmp/pt/b/caddy/sites",exist_ok=True); open("/var/tmp/pt/b/mode","w").write("extern")
def worker():
    r=subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":"/var/tmp/pt/b","MK_SITES":S},capture_output=True,text=True); return r.stdout+r.stderr
def zipb(dateien,**kw):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        for n,c in dateien.items(): z.writestr(n,c)
    return b.getvalue()
def up(daten,name,art="live",kunde=None,skript="1",fname="site.zip"):
    return a.post("/api/admin/websites/upload",files={"datei":(fname,daten,"application/zip")},data={"art":art,"name":name,"kunden_id":kunde or "","dienste_skript":skript})
dom=f"upload{sfx}.de"
HTML="<!doctype html><html><body><h1>Version {v}</h1></body></html>"
# ---- Ablehnungen
chk("Kunde darf nicht hochladen",cA.post("/api/admin/websites/upload",files={"datei":("a.zip",b"x","application/zip")},data={"art":"live","name":dom}).status_code==403)
r=up(zipb({"index.html":HTML.format(v=1)}),dom); chk("Neue Live-Website braucht einen Kunden",r.status_code==400 and "Kunden" in r.text,r.text)
r=up(zipb({"index.html":HTML.format(v=1)}),"kein domain",kunde=kA); chk("Ungültiger Name",r.status_code==400,r.text)
r=up(zipb({"index.html":HTML.format(v=1)}),dom,kunde="00000000-0000-0000-0000-000000000000"); chk("Unbekannter Kunde",r.status_code==400,r.text)
r=up(b"das ist keine zip",dom,kunde=kA); chk("Keine ZIP",r.status_code==400 and "ZIP" in r.text,r.text)
r=up(b"x",dom,kunde=kA,fname="seite.rar"); chk("Nur .zip erlaubt",r.status_code==400)
r=up(zipb({"index.html":"x","../boese.html":"y"}),dom,kunde=kA); chk("Pfad nach oben (../) abgelehnt",r.status_code==400 and "unsicher" in r.text,r.text)
r=up(zipb({"/etc/boese.html":"y","index.html":"x"}),dom,kunde=kA); chk("Absoluter Pfad abgelehnt",r.status_code==400,r.text)
b=io.BytesIO()
with zipfile.ZipFile(b,"w") as z:
    z.writestr("index.html","x"); i=zipfile.ZipInfo("link.html"); i.create_system=3; i.external_attr=(0o120777<<16); z.writestr(i,"/etc/passwd")
r=up(b.getvalue(),dom,kunde=kA); chk("Symlink abgelehnt",r.status_code==400 and "Verknüpfung" in r.text,r.text)
r=up(zipb({"index.html":"x","shell.php":"<?php system($_GET[0]);"}),dom,kunde=kA); chk("Skripte (.php) abgelehnt",r.status_code==400 and "shell.php" in r.text,r.text)
r=up(zipb({"index.html":"x","setup.exe":"MZ"}),dom,kunde=kA); chk(".exe abgelehnt",r.status_code==400)
r=up(zipb({"startseite.html":"x"}),dom,kunde=kA); chk("Ohne index.html abgelehnt",r.status_code==400 and "index.html" in r.text,r.text)
chk("Nach Ablehnung bleibt nichts liegen",not glob.glob(S+"/live/.upload-*") and not glob.glob(Q+"/auftrag-*.json"))
# ---- Veröffentlichen (Ordner „meine-seite/“ in der ZIP wird abgestreift, Mac- und Git-Reste ignoriert)
z1=zipb({"meine-seite/index.html":HTML.format(v=1),"meine-seite/css/a.css":"body{}","meine-seite/.git/config":"x","__MACOSX/._index.html":"x","meine-seite/.DS_Store":"x","meine-seite/bild.png":"PNG"})
r=up(z1,dom,kunde=kA); chk("Upload angenommen",r.status_code==200 and r.json()["dateien"]==3 and r.json()["skript_in_seiten"]==1,r.text)
chk("Zwischenordner und Auftrag liegen bereit",len(glob.glob(S+"/live/.upload-*"))==1 and len(glob.glob(Q+"/auftrag-*.json"))==1)
v=a.get("/api/admin/websites/veroeffentlichungen").json(); chk("Verlauf zeigt laufenden Auftrag",len(v["offen"])==1 and v["offen"][0]["name"]==dom,v)
chk("Website noch nicht live vor dem Server-Dienst",not os.path.isdir(f"{S}/live/{dom}"))
out=worker(); chk("Server-Dienst veröffentlicht",os.path.isfile(f"{S}/live/{dom}/index.html") and "veröffentlicht" in out,out)
idx=open(f"{S}/live/{dom}/index.html").read(); sid=cA.get("/api/kunde/website-dienste").json()["site_id"]
chk("Website-Dienste-Skript mit Site-ID eingebaut (vor </body>)",f'data-site="{sid}"' in idx and idx.index("site.js")<idx.index("</body>") and idx.count("site.js")==1,idx)
chk("Dateien ohne Git/Mac-Reste, Unterordner da",os.path.isfile(f"{S}/live/{dom}/css/a.css") and not os.path.exists(f"{S}/live/{dom}/.git") and not os.path.exists(f"{S}/live/{dom}/.DS_Store") and not os.path.exists(f"{S}/live/{dom}/__MACOSX"))
chk("Ordner für Wochenangebote angelegt",os.path.isdir(f"{S}/live/{dom}/angebote/archiv"))
chk("Webserver-Eintrag für Domain und www",os.path.isfile(f"/var/tmp/pt/b/caddy/sites/{dom}.caddy") and f"{dom}, www.{dom}" in open(f"/var/tmp/pt/b/caddy/sites/{dom}.caddy").read())
cfg=open(f"/var/tmp/pt/b/caddy/sites/{dom}.caddy").read()
chk("Webserver: Adressen ohne .html (try_files) und eigene 404-Seite",'try_files {path} {path}.html {path}/index.html' in cfg and '/404.html' in cfg and 'handle /api/*' in cfg,cfg)
chk("Ohne Datenschutzseite kein data-datenschutz",'data-datenschutz' not in idx,idx)
domD=f"dsgvo{sfx}.de"
r=up(zipb({"index.html":HTML.format(v=1),"datenschutz.html":"<html><body>DS</body></html>","unter/index.html":"<html><body>u</body></html>"}),domD,kunde=kA); worker()
idxD=open(f"{S}/live/{domD}/index.html").read(); tagD=idxD[idxD.index("<script"):idxD.index("</script>")]
chk("Datenschutzseite erkannt: Skript trägt data-datenschutz",'data-datenschutz="/datenschutz.html"' in tagD and idxD.count("site.js")==1 and idxD.count("data-datenschutz")==1,idxD)
chk("Zwischenordner und Auftrag aufgeräumt",not glob.glob(S+"/live/.upload-*") and not glob.glob(Q+"/auftrag-*.json"))
meta=json.load(open(f"{S}/live/{dom}/site.json")); nrA=sql(f"select kundennummer from kunden where id='{kA}'")
chk("Kennung site.json mit Kundennummer und Firma",meta["name"]==dom and meta["kunde"].startswith(nrA) and "Upa" in meta["kunde"],(meta,nrA))
chk("Domain beim Kunden vermerkt",sql(f"select domain from kunden where id='{kA}'")==dom)
r=a.get("/api/admin/websites").json()["aktiv"]; chk("Websiteliste zeigt Kundennummer",any(x["name"]==dom and nrA in x["kunde"] for x in r),r)
chk("Website im Portal als live eingetragen",sql(f"select status from websites where domain='{dom}' and kunden_id='{kA}'")=="live")
v=a.get("/api/admin/websites/veroeffentlichungen").json(); e=[x for x in v["ergebnisse"] if x["name"]==dom]
chk("Ergebnis im Portal sichtbar mit Adresse und DNS-Hinweis",e and e[0]["ok"] and e[0]["url"]==f"https://{dom}/" and "A-Eintrag" in e[0]["text"],v)
chk("Website-Dienste erlauben die neue Domain",httpx.get(B+f"/site/{sid}/config",headers={"Origin":f"https://{dom}"}).status_code==200)
chk("Site-Liste zeigt sie",any(x["name"]==dom for x in a.get("/api/admin/websites").json()["aktiv"]))
# ---- Aktualisieren: Wochenangebote bleiben, vorige Version gesichert
open(f"{S}/live/{dom}/angebote/aktuell.pdf","w").write("PDF")
r=up(zipb({"index.html":HTML.format(v=2)}),dom,skript="0"); chk("Update ohne Kundenangabe (Domain bekannt)",r.status_code==200,r.text)
chk("Ohne Haken kein Skript",r.json()["skript_in_seiten"]==0)
out=worker(); idx=open(f"{S}/live/{dom}/index.html").read()
chk("Neue Version online",("Version 2" in idx) and "site.js" not in idx,idx)
chk("Wochenangebote bleiben erhalten",open(f"{S}/live/{dom}/angebote/aktuell.pdf").read()=="PDF")
chk("Alte Version gesichert",len(glob.glob(f"{S}/.vorversionen/*__live__{dom}"))==1)
chk("Alte Dateien der Vorversion nur dort (css weg in neuer Version)",not os.path.exists(f"{S}/live/{dom}/css/a.css"))
r=a.post("/api/admin/websites/zurueck",json={"art":"live","name":dom}); chk("Zurückholen angenommen",r.status_code==200,r.text)
out=worker(); idx=open(f"{S}/live/{dom}/index.html").read(); chk("Vorige Version wieder online",("Version 1" in idx) and os.path.isfile(f"{S}/live/{dom}/css/a.css"),out)
chk("Wochenangebote auch nach dem Zurückholen da",open(f"{S}/live/{dom}/angebote/aktuell.pdf").read()=="PDF")
r=a.post("/api/admin/websites/zurueck",json={"art":"live","name":dom}); worker(); chk("Erneutes Zurückholen wechselt wieder (Hin und Her)","Version 2" in open(f"{S}/live/{dom}/index.html").read())
r=a.post("/api/admin/websites/zurueck",json={"art":"live","name":"gibtesnicht.de"}); out=worker(); v=a.get("/api/admin/websites/veroeffentlichungen").json()
chk("Zurückholen ohne Vorversion: verständlicher Fehler",any((not x["ok"]) and x["name"]=="gibtesnicht.de" and "keine frühere" in x["text"] for x in v["ergebnisse"]),v)
# Auswahl per Kundennummer
nrB=sql(f"select kundennummer from kunden where id='{kB}'"); dom2=f"nummer{sfx}.de"
r=up(zipb({"index.html":"x"}),dom2,kunde=nrB.lower()); chk("Upload mit Kundennummer statt ID",r.status_code==200,r.text); worker()
chk("Zuordnung zur Kundennummer",sql(f"select kunden_id from websites where domain='{dom2}'")==kB)
chk("Unbekannte Kundennummer",up(zipb({"index.html":"x"}),f"y{sfx}.de",kunde="MK-999999").status_code==400)
# Datenschutzseite wird erkannt: Skript verlinkt die echte Adresse
domD=f"dsgvo{sfx}.de"
r=up(zipb({"index.html":HTML.format(v=1),"datenschutz.html":"<html><body>DS</body></html>"}),domD,kunde=kA); worker()
idx=open(f"{S}/live/{domD}/index.html").read()
chk("Datenschutzseite erkannt: data-datenschutz im Skript",'data-datenschutz="/datenschutz.html"' in idx and idx.count("site.js")==1,idx)
domN=f"keinds{sfx}.de"
r=up(zipb({"index.html":HTML.format(v=1)}),domN,kunde=kA); worker()
idx=open(f"{S}/live/{domN}/index.html").read()
chk("Ohne Datenschutzseite kein Attribut",'data-datenschutz' not in idx and idx.count("site.js")==1,idx)
r=up(zipb({"index.html":'<html><body><script src="https://alt.example/static/js/site.js" data-site="mk_alt" defer></script></body></html>',"datenschutz/index.html":"x"}),domD,kunde=kA); worker()
idx=open(f"{S}/live/{domD}/index.html").read()
chk("Vorhandenes Skript: Attribut ergänzt, nicht doppelt",idx.count("site.js")==1 and idx.count("data-datenschutz=")==1 and 'data-datenschutz="/datenschutz/"' in idx,idx)
# Fremde Domain
r=up(zipb({"index.html":"x"}),dom,kunde=kB); chk("Domain gehört schon einem anderen Kunden",r.status_code==400,r.text)
# ---- Ganzes Projekt (wie ElbDetail): nur der Ordner website-fertig/ wird übernommen, Server-Code & Co. bleiben draußen
domE=f"elbtest{sfx}.de"
proj={"elbdetail/README.md":"x","elbdetail/server/app.py":"print(1)","elbdetail/deploy/Dockerfile":"FROM x","elbdetail/deploy/docker-compose.yml":"a: b","elbdetail/build/build.py":"x",
      "elbdetail/content/a.json":"{}","elbdetail/docs/index.html":"docs","elbdetail/website-fertig/index.html":HTML.format(v=1),"elbdetail/website-fertig/leistungen/a.html":"<html><body>a</body></html>",
      "elbdetail/website-fertig/img/x.png":"PNG","elbdetail/website-fertig/config.js":"window.ELB={}","elbdetail/website-fertig/fonts/f.woff2":"F"}
r=up(zipb(proj),domE,kunde=kA,skript="0"); chk("Projekt-ZIP (website-fertig/) angenommen",r.status_code==200 and r.json().get("dateien")==5 and "website-fertig" in r.json().get("ordner",""),r.text)
out=worker(); chk("Nur die Website liegt online",os.path.isfile(f"{S}/live/{domE}/index.html") and os.path.isfile(f"{S}/live/{domE}/leistungen/a.html") and os.path.isfile(f"{S}/live/{domE}/img/x.png"),out)
chk("Server-Code, Build und Docker bleiben draußen",not any(os.path.exists(f"{S}/live/{domE}/{x}") for x in ("server","deploy","build","content","docs","README.md")))
r=up(zipb({"proj/a/b/index.html":"x","proj/server/app.py":"x","proj/y.txt":"z"}),f"tief{sfx}.de",kunde=kA,skript="0"); chk("Tief liegende index.html wird gefunden",r.status_code==200,r.text)
r=up(zipb({"proj/website-fertig/index.html":"x","proj/website-fertig/evil.exe":"MZ"}),f"tief2{sfx}.de",kunde=kA); chk("Verbotene Datei im Website-Ordner weiter abgelehnt",r.status_code==400 and "evil.exe" in r.text,r.text)


# ---- Demo
r=up(zipb({"index.html":HTML.format(v=9)}),"testdemo",art="demo",skript="0"); chk("Demo hochladen (ohne Kunde)",r.status_code==200,r.text)
worker(); chk("Demo online im Demo-Ordner",os.path.isfile(f"{S}/demos/testdemo/index.html"))
# ---- Sicherheit des Server-Dienstes: manipulierter Zwischenordner (Symlink) wird abgelehnt
ev=f"{'a1'*8}"; os.makedirs(f"{S}/live/.upload-{ev}"); open(f"{S}/live/.upload-{ev}/index.html","w").write("x"); os.symlink("/etc/passwd",f"{S}/live/.upload-{ev}/link.html")
open(f"{Q}/auftrag-{'b2'*8}.json","w").write(json.dumps({"aktion":"veroeffentlichen","art":"live","name":f"boese{sfx}.de","upload":ev,"kunde":"x"}))
out=worker(); chk("Symlink im Zwischenordner: nicht veröffentlicht",not os.path.exists(f"{S}/live/boese{sfx}.de") and not os.path.exists(f"{S}/live/.upload-{ev}"),out)
open(f"{Q}/auftrag-{'c3'*8}.json","w").write(json.dumps({"aktion":"veroeffentlichen","art":"live","name":"../../etc","upload":ev,"kunde":"x"})); out=worker(); chk("Ungültiger Name im Auftrag verworfen",not os.path.exists("/etc/index.html"))
open(f"{Q}/auftrag-{'d4'*8}.json","w").write(json.dumps({"aktion":"veroeffentlichen","art":"live","name":f"x{sfx}.de","upload":"../../etc","kunde":"x"})); out=worker(); chk("Ungültige Upload-ID verworfen",not os.path.exists(f"{S}/live/x{sfx}.de"))
chk("Auditprotokoll",int(sql("select count(*) from audit_log where aktion in ('website_hochgeladen','website_zurueck')") or 0)>=4)
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip(); dom3=f"ui{sfx}.de"
open("/var/tmp/pt/ui.zip","wb").write(zipb({"index.html":HTML.format(v=5)}))
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1100,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+"/admin#websites"); await pg.wait_for_selector("h2:text-is('Website hochladen')",timeout=8000)
        chk("UI: Auswahl zeigt Kundennummer",nrA in await pg.locator(".card:has(h2:text-is('Website hochladen')) select").nth(1).inner_text())
        await pg.click("text=Hochladen und veröffentlichen"); await pg.wait_for_selector("text=Bitte eine ZIP-Datei wählen"); chk("UI: ohne Datei kommt ein Hinweis",True)
        c=pg.locator(".card:has(h2:text-is('Website hochladen'))")
        await c.locator("select").nth(1).select_option(label=[o for o in await c.locator("select").nth(1).locator("option").all_inner_texts() if nrA in o][0])
        await c.locator("input[placeholder^='Domain ohne www']").fill(dom3); await c.locator("input[type=file]").set_input_files("/var/tmp/pt/ui.zip")
        await c.get_by_role("button",name="Hochladen und veröffentlichen").click(); await pg.wait_for_selector("text=Hochgeladen und geprüft",timeout=10000)
        chk("UI: Upload bestätigt",True)
        worker(); await pg.wait_for_selector(f"a[href='https://{dom3}/']",timeout=20000); chk("UI: Ergebnis mit Adresse erscheint",True)
        chk("UI: Seite liegt auf dem Server",os.path.isfile(f"{S}/live/{dom3}/index.html"))
        await pg.screenshot(path="/var/tmp/pt/shots/upload_admin.png",full_page=True)
        chk("Keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
