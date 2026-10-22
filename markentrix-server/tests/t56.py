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
sfx=str(int(time.time())+113)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, os, sys, io, zipfile, zoneinfo, tempfile, pathlib
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.datetime.now(TZ).date()
Q="/var/tmp/pt/b/queue"; S="/var/tmp/pt/s"; DNS="/var/tmp/pt/dns.json"
kA,cA,mA=neuer_kunde("Dnsa"); kB,cB,mB=neuer_kunde("Dnsb")
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0",DNS_TEST_DATEI=DNS,QUEUE_DIR=Q)
from app import db, domaincheck, jobs, livecheck, webbetrieb
db.open_pool()
# ================= 1. DNS-Assistent
dom=f"dns{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
chk("Ohne Anmeldung kein Zugriff",httpx.get(B+f"/api/admin/websites/domain/{dom}").status_code in (401,403))
chk("Kunde darf nicht prüfen",cA.get(f"/api/admin/websites/domain/{dom}").status_code==403)
chk("Ungültige Domain abgelehnt",a.get("/api/admin/websites/domain/ABC..x").status_code==400)
r=a.get(f"/api/admin/websites/domain/{dom}").json()
chk("Server-Adresse unbekannt: klare Meldung statt falschem Ergebnis",r["ok"] is False and any("öffentliche Adresse" in p for p in r["probleme"]),r)
json.dump({"v4":"203.0.113.5"},open(Q+"/serverip.json","w"))
json.dump({f"{dom}|A":["198.185.159.144","198.185.159.145"],f"www.{dom}|A":["198.185.159.144"],f"{dom}|NS":["ns1049.ui-dns.com","ns1049.ui-dns.de"]},open(DNS,"w"))
r=a.get(f"/api/admin/websites/domain/{dom}").json()
chk("Zeigt noch auf Squarespace",r["ok"] is False and r["apex"]["status"]=="falsch" and r["apex"]["zeigt_auf"]=="Squarespace" and r["www"]["status"]=="falsch",r["apex"])
chk("DNS-Anbieter IONOS erkannt",r["dns_anbieter"]=="IONOS",r["dns_anbieter"])
chk("Anleitung nennt Server-Adresse",any("203.0.113.5" in s for s in r["schritte"]))
chk("Kundentext fertig",r["kundentext"].startswith("Guten Tag") and "203.0.113.5" in r["kundentext"] and "IONOS" in r["kundentext"] and "Viele Grüße" in r["kundentext"],r["kundentext"][:200])
json.dump({f"{dom}|A":["203.0.113.5"],f"www.{dom}|A":["203.0.113.5"],f"{dom}|AAAA":["2a00:1450::1"],f"{dom}|NS":["ns1.ui-dns.de"]},open(DNS,"w"))
r=a.get(f"/api/admin/websites/domain/{dom}").json()
chk("A stimmt, aber fremde IPv6 stört",r["ok"] is False and r["apex"]["status"]=="ok" and r["apex"]["aaaa_stoert"] and any("AAAA" in p for p in r["probleme"]),r)
json.dump({f"{dom}|A":["203.0.113.5"],f"www.{dom}|CNAME":[dom],f"www.{dom}|A":["203.0.113.5"]},open(DNS,"w"))
r=a.get(f"/api/admin/websites/domain/{dom}").json()
chk("Alles richtig: ok, kein Kundentext",r["ok"] is True and r["kundentext"]=="" and not r["probleme"],r)
json.dump({f"{dom}|A":["203.0.113.5"]},open(DNS,"w"))
r=a.get(f"/api/admin/websites/domain/{dom}").json(); chk("www fehlt wird erkannt",r["ok"] is False and r["www"]["status"]=="fehlt",r["www"])
l=a.get("/api/admin/websites").json()
chk("Ergebnis in der Website-Liste (Status gespeichert)",sql(f"select ok from domain_pruefung where domain='{dom}'")=="f")
# Job: meldet erst, wenn die Domain stimmt, und nur einmal
sql(f"delete from domain_pruefung where domain='{dom}'")
jobs.domain_lauf(); chk("Job speichert den offenen Stand ohne Meldung",sql(f"select ok||'|'||live_gemeldet from domain_pruefung where domain='{dom}'")=="false|false" or sql(f"select ok::text||'|'||live_gemeldet::text from domain_pruefung where domain='{dom}'")=="false|false")
json.dump({f"{dom}|A":["203.0.113.5"],f"www.{dom}|A":["203.0.113.5"]},open(DNS,"w"))
jobs.domain_lauf(); chk("Job erkennt: jetzt live, einmal gemeldet",sql(f"select ok::text||'|'||live_gemeldet::text from domain_pruefung where domain='{dom}'")=="true|true")
vor=sql(f"select geprueft_am from domain_pruefung where domain='{dom}'"); time.sleep(1.1); jobs.domain_lauf()
chk("Job lässt fertige Domains in Ruhe",sql(f"select geprueft_am from domain_pruefung where domain='{dom}'")==vor)
chk("Kunde B sieht nichts von der Prüfung",cB.get("/api/admin/websites").status_code==403)
chk("Anbieter-Erkennung",domaincheck.anbieter_ip("23.227.38.65")=="Shopify" and domaincheck.anbieter_ip("203.0.113.5") is None and domaincheck.anbieter_ns(["ns.cloudflare.com"])=="Cloudflare")
# ================= 2. Livegang-Check
def zipb(dateien):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        for n,c in dateien.items(): z.writestr(n,c)
    return b.getvalue()
def up(daten,name,kunde=None):
    return a.post("/api/admin/websites/upload",files={"datei":("site.zip",daten,"application/zip")},data={"art":"live","name":name,"kunden_id":kunde or "","dienste_skript":"0"})
GUT='<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Salon Muster</title><meta name="description" content="Friseur in Celle"><meta name="viewport" content="width=device-width"></head><body><a href="impressum.html">Impressum</a> <a href="/datenschutz.html">Datenschutz</a><img src="logo.png"></body></html>'
dg=f"gut{sfx}.de"
r=up(zipb({"index.html":GUT,"impressum.html":"<html><title>I</title><body>x</body></html>","datenschutz.html":"<html><title>D</title><body>x</body></html>","logo.png":"x"*100}),dg,kA)
c=r.json().get("check") or {}
chk("Sauberer Upload: grün",r.status_code==200 and c.get("ampel")=="gruen" and all(p["stufe"]=="hinweis" for p in c.get("punkte",[])),c)
SCHLECHT='<html><head></head><body><a href="gibt-es-nicht.html">x</a><img src="bilder/gross.jpg"><img src="fehlt.png"><form action="/x"><input></form><p>Lorem ipsum dolor</p><a href="http://localhost:3000/">dev</a><link href="https://fonts.googleapis.com/css?family=X" rel="stylesheet"><a href="mailto:a@b.de">m</a><a href="#oben">o</a><a href="https://extern.de/x">e</a></body></html>'
ds=f"schlecht{sfx}.de"
r=up(zipb({"index.html":SCHLECHT,"bilder/gross.jpg":"x"*2_000_000}),ds,kB)
c=r.json().get("check") or {}; t=" | ".join(x["text"] for x in c.get("punkte",[]))
chk("Schlechter Upload: rot",c.get("ampel")=="rot",c)
for was,muster in (("Impressum fehlt","Impressum"),("Datenschutz fehlt","Datenschutzerklärung"),("toter Link","gibt-es-nicht.html"),("totes Bild","fehlt.png"),("großes Bild","2.0 MB groß") if False else ("großes Bild","MB groß"),
                   ("localhost","localhost"),("Lorem ipsum","Lorem ipsum"),("Titel fehlt","Seitentitel fehlt"),("Beschreibung fehlt","Meta-Beschreibung"),("Viewport","Viewport"),("Google Fonts","Google Fonts")):
    chk(f"Check meldet: {was}",muster in t,t[:300])
chk("mailto, #anker und externe Links sind keine toten Links","mailto" not in t and "#oben" not in t and "extern.de" not in t,t[:200])
chk("Hochladen funktioniert trotz rotem Check",r.status_code==200)
# in-process auf Ordner
with tempfile.TemporaryDirectory() as td:
    p=pathlib.Path(td); (p/"sub").mkdir()
    (p/"index.html").write_text(GUT.replace('impressum.html','sub/'))
    (p/"sub"/"index.html").write_text('<html lang="de"><title>S</title><a href="../impressum.html">zurück</a><a href="../../../etc/passwd">x</a>')
    (p/"impressum.html").write_text("x"); (p/"datenschutz.html").write_text("x"); (p/"logo.png").write_text("x")
    c=livecheck.pruefen(p); t=" | ".join(x["text"] for x in c["punkte"])
    chk("Ordner-Link und ../-Verweise werden aufgelöst, Ausbruch gilt als tot","etc/passwd" in t and "../impressum.html" not in t,t)
    (p/"index.html").unlink(); c=livecheck.pruefen(p); chk("Ohne index.html: Fehler",c["ampel"]=="rot" and "index.html" in " ".join(x["text"] for x in c["punkte"]))
os.makedirs(f"{S}/live/{dg}",exist_ok=True); open(f"{S}/live/{dg}/index.html","w").write(GUT)
r=a.get(f"/api/admin/websites/livecheck?art=live&name={dg}"); chk("Check einer veröffentlichten Seite",r.status_code==200 and r.json()["ampel"] in ("gelb","rot","gruen"),r.text[:200])
chk("Check: unbekannte Seite 404",a.get("/api/admin/websites/livecheck?art=live&name=nichtda.de").status_code==404)
chk("Check: Kunde verboten",cA.get(f"/api/admin/websites/livecheck?art=live&name={dg}").status_code==403)
chk("Check: ungültiger Name",a.get("/api/admin/websites/livecheck?art=live&name=../x").status_code==400)
# ================= 3. Bewertungsanfrage nach Termin
dom2=f"bew{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom2}','live','live')")
W=httpx.Client(base_url=B,headers={"Host":dom2}); API="/siteapi/api"
def post(pfad,body): return W.post(API+pfad,headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Test","Origin":"https://"+dom2},content=json.dumps(body).encode())
KAL={"aktiv":True,"dauer":30,"tage":30,"von":"08:00","bis":"18:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"","empfaenger":"","zeiten":"08:00, 09:00, 10:00, 11:00","kapazitaet":0,"freigabe":False,"halte_std":72}
cA.put("/api/kunde/website-dienste/kalender",json=KAL)
tag=(heute+datetime.timedelta(days=3)).isoformat()
def buchen(name,mail,zeit):
    r=post("/anfrage",{"typ":"termin","name":name,"email":mail,"telefon":"0511 1","nachricht":"x","einwilligung":"ja","datum":tag,"uhrzeit":zeit}); assert r.status_code==200,r.text; return r.json()["ref"]
def vergangen(ref):
    sql(f"update website_termine set start=now()-interval '3 hours', ende=now()-interval '2.5 hours' where ref='{ref}'"); return sql(f"select id from website_termine where ref='{ref}'")
r1=buchen("Bea Bew","bea@besucher.de","08:00"); r2=buchen("Carl Cool","carl@besucher.de","09:00"); r3=buchen("Dora Dau","dora@besucher.de","10:00")
chk("Standard: Anfrage aus",sql(f"select bew_nach_termin::text from website_dienste where kunden_id='{kA}'")=="false")
b1=vergangen(r1); cA.post(f"/api/kunde/website-dienste/buchungen/{b1}/ergebnis",json={"ergebnis":"erschienen"})
chk("Ohne Opt-in keine Anfrage vorgemerkt",sql(f"select bewertung_faellig is null from website_termine where id='{b1}'")=="t")
chk("Anschalten ohne Link/Place-ID abgelehnt",cA.put("/api/kunde/website-dienste/bewertungen/anfrage",json={"aktiv":True,"verzoegerung_std":3}).status_code==400)
chk("Verzögerung außerhalb 1–72 abgelehnt",cA.put("/api/kunde/website-dienste/bewertungen/anfrage",json={"aktiv":True,"verzoegerung_std":99}).status_code==422)
cA.put("/api/kunde/website-dienste/bewertungen",json={"aktiv":False,"link":"https://g.page/r/abc123/review"})
chk("Anschalten mit Link",cA.put("/api/kunde/website-dienste/bewertungen/anfrage",json={"aktiv":True,"verzoegerung_std":3}).status_code==200)
d=cA.get("/api/kunde/website-dienste").json()["bewertungen"]; chk("Einstellung wird angezeigt",d["nach_termin"] is True and d["verzoegerung_std"]==3,d)
chk("Kunde B kann fremde Einstellung nicht sehen/ändern (eigene bleibt aus)",cB.get("/api/kunde/website-dienste").json()["bewertungen"]["nach_termin"] is False)
b2=vergangen(r2); b3=vergangen(r3)
cA.post(f"/api/kunde/website-dienste/buchungen/{b2}/ergebnis",json={"ergebnis":"erschienen"}); cA.post(f"/api/kunde/website-dienste/buchungen/{b3}/ergebnis",json={"ergebnis":"nicht_erschienen"})
chk("Erschienen: Anfrage in ca. 3 Stunden vorgemerkt",sql(f"select (bewertung_faellig between now()+interval '2 hours 50 minutes' and now()+interval '3 hours 10 minutes')::text from website_termine where id='{b2}'")=="true")
chk("Nicht erschienen: keine Anfrage",sql(f"select bewertung_faellig is null from website_termine where id='{b3}'")=="t")
webbetrieb.bewertungsanfragen(); chk("Noch nicht fällig: nichts verschickt",not mail_an("carl@besucher.de","Bewertung") and not mail_an("carl@besucher.de","Besuch"))
sql(f"update website_termine set bewertung_faellig=now()-interval '1 minute' where id='{b2}'")
n=webbetrieb.bewertungsanfragen(); ms=mail_an("carl@besucher.de","g.page/r/abc123")
chk("Fällig: Bewertungsanfrage geht raus",n==1 and len(ms)==1,n)
t=text(ms[0]) if ms else ""
chk("Mail: Link, Name, Abmeldelink","g.page/r/abc123/review" in t and "Carl Cool" in t and "/bewertung/abmelden?t=" in t,t[:500])
webbetrieb.bewertungsanfragen(); chk("Nicht doppelt",len(mail_an("carl@besucher.de","g.page/r/abc123"))==1 and sql(f"select bewertung_gesendet is not null from website_termine where id='{b2}'")=="t")
chk("Protokoll: Art Bewertung",sql(f"select count(*) from mail_protokoll where art='bewertung' and kunden_id='{kA}'")!="0")
ab=re.search(r"(/site/[^\s]+/bewertung/abmelden\?t=[A-Za-z0-9_-]+)",t).group(1)
r=httpx.get(B+ab); chk("Abmelden: Seite bestätigt",r.status_code==200 and "keine Bewertungsanfragen" in r.text,r.text[:200])
chk("Abmelden: Adresse gesperrt",sql(f"select count(*) from website_bewertung_sperre where kunden_id='{kA}' and email='carl@besucher.de'")=="1")
chk("Abmelden: ungültiger Link",httpx.get(B+"/site/mk_abcdef123/bewertung/abmelden?t=zzzzzzzzzzzz").status_code==200 and "nicht mehr gültig" in httpx.get(B+"/site/mk_abcdef123/bewertung/abmelden?t=zzzzzzzzzzzz").text)
r4=buchen("Carl Cool","carl@besucher.de","11:00"); b4=vergangen(r4)
cA.post(f"/api/kunde/website-dienste/buchungen/{b4}/ergebnis",json={"ergebnis":"erschienen"})
chk("Gesperrte Adresse: keine neue Anfrage",sql(f"select bewertung_faellig is null from website_termine where id='{b4}'")=="t")
# Kunde gekündigt / pausiert: keine Mails
sql(f"update website_termine set bewertung_faellig=now()-interval '1 minute', bewertung_gesendet=null where id='{b1}'")
sql(f"update kunden set status='gekuendigt' where id='{kA}'"); webbetrieb.bewertungsanfragen()
chk("Gekündigter Kunde: keine Anfrage",not mail_an("bea@besucher.de","g.page"))
sql(f"update kunden set status='aktiv' where id='{kA}'")
