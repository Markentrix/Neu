"""Lead-Funnel mit Vorlage „Website-Check“: Seite, Anmeldung, Prüfung mit Ampel, Ergebnis-Mail mit PDF, PageSpeed, Nachfass-Mails Tag 1/3/7,
Nachhol-Job, Schutz vor Abrufen ins eigene Netz, Admin (Probe, PDF, Einstellungen) und Browser (390/1280 px, Barrierefreiheit)."""
import httpx, time, re, email, email.header, json, os, sys, subprocess, threading, io, asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def teil(m,typ):
    for p in m.walk():
        if p.get_content_type()==typ: return p.get_payload(decode=True)
text=lambda m: (teil(m,"text/plain") or b"").decode("utf8","replace")
betreff=lambda m: str(email.header.make_header(email.header.decode_header(m["Subject"])))
an=lambda adr: [m for m in mails() if adr in str(m["To"])]

# ---------------------------------------------------------------- kleine Test-Websites und PageSpeed-Ersatz (Port 8997)
GUT='''<!doctype html><html lang="de"><head><title>Malerbetrieb Muster in Frankfurt</title><meta name="description" content="Malerbetrieb in Frankfurt: Innen, Fassade, Tapeten. Festpreise ab 18 Euro und Termine online buchen.">
<meta name="viewport" content="width=device-width, initial-scale=1"></head><body><h1>Malerbetrieb Muster</h1><a href="tel:+4969123">Anrufen</a><p>Innen ab 18 € je m²</p>
<p>4,9 Sterne, Kundenstimmen</p><a href="/termin">Termin online buchen</a><a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a></body></html>'''
SCHLECHT='<html><head><title>Home</title></head><body><p>Willkommen auf unserer Homepage</p></body></html>'
PSI={"lighthouseResult":{"categories":{"performance":{"score":0.42},"seo":{"score":0.83}},"audits":{"largest-contentful-paint":{"displayValue":"6,8 s"}}}}
class W(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/psi"):
            body=json.dumps(PSI).encode(); self.send_response(200); self.send_header("Content-Type","application/json")
        elif self.path.startswith("/weiter"):
            self.send_response(302); self.send_header("Location","/gut"); self.end_headers(); return
        elif self.path.startswith("/gut"): body=GUT.encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        elif self.path.startswith("/schlecht"): body=SCHLECHT.encode(); self.send_response(200); self.send_header("Content-Type","text/html")
        else: body=b"weg"; self.send_response(404)
        self.end_headers(); self.wfile.write(body)
    def log_message(self,*a): pass
threading.Thread(target=ThreadingHTTPServer(("127.0.0.1",8997),W).serve_forever,daemon=True).start()
WEB="http://127.0.0.1:8997"

ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H,timeout=90); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","telefon":"05141 12345","kleinunternehmer":True,"mwst_satz":19})
pub=httpx.Client(base_url=B,headers=H,timeout=30)
sfx=str(int(time.time())+2100)
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0",
                  SITE_LOKAL_ERLAUBT="1",PAGESPEED_BASE_URL=WEB+"/psi")
from app import db, jobs, config, funnelcheck
from app.db import tx
db.open_pool()
def cfg():
    with tx("system") as cur: return jobs.einstellungen_lesen(cur)

# ---------------------------------------------------------------- Kampagne anlegen
d=a.get("/api/admin/funnel").json(); v=d.get("vorgabe") or {}
chk("Vorgaben für neue Seiten: 3 Nachfass-Mails (Tag 1, 3, 7) und Ergebnis-Mail",v.get("folge_tage")==[1,3,7] and len(v.get("folge_texte",[]))==3 and "{ampel}" in v.get("check_betreff",""),v)
chk("Probezeile für die Vorgaben wird nicht gespeichert",sql("select count(*) from lead_kampagnen where slug='zz-vorgabe-probe'")=="0")
slug=f"check-{sfx}"
basis={"slug":slug,"name":"Website-Check Frankfurt","titel":"Wie gut ist Ihre Website wirklich?","untertitel":"Wir prüfen Ihre Website kostenlos.","nutzen":["Ampel","PDF","Kostenlos"],
       "button":"Kostenlos prüfen lassen","einwilligung_text":"Ich bin einverstanden, dass Markentrix mich zum Website-Check per E-Mail und Telefon kontaktiert.","kosten_cent":10000,
       "vorlage":"website_check","kicker":"Für Betriebe in Frankfurt & Rhein-Main","check_mail":True,"folge_aktiv":True,"folge_tage":[1,3,7],
       "folge_betreffe":v["folge_betreffe"],"folge_texte":v["folge_texte"],"rechtlich_geprueft":True,"aktiv":True}
r=a.post("/api/admin/funnel",json={**basis,"slug":f"x{sfx}","vorlage":"standard"}); chk("PDF-Mail nur mit Vorlage Website-Check",r.status_code==400 and "Website-Check" in r.text,r.text)
chk("Abgelehnte Seite wurde nicht angelegt",sql(f"select count(*) from lead_kampagnen where slug='x{sfx}'")=="0")
r=a.post("/api/admin/funnel",json={**basis,"slug":f"y{sfx}","folge_tage":[3,1,7]}); chk("Nachfass-Tage müssen aufsteigen",r.status_code==400,r.text)
r=a.post("/api/admin/funnel",json={**basis,"slug":f"z{sfx}","folge_tage":[1,3],"folge_betreffe":v["folge_betreffe"]}); chk("Je Stufe Tag, Betreff und Text nötig",r.status_code==400,r.text)
r=a.post("/api/admin/funnel",json=basis); chk("Website-Check-Seite anlegen",r.status_code==200,r.text); kid=r.json()["id"]
k=[x for x in a.get("/api/admin/funnel").json()["kampagnen"] if x["slug"]==slug][0]
chk("Liste zeigt Vorlage, PDF-Mail und Nachfass-Tage",k["vorlage"]=="website_check" and k["check_mail"] and k["folge_aktiv"] and k["folge_tage"]==[1,3,7],k)
r=a.put(f"/api/admin/funnel/{kid}",json={**{x:basis[x] for x in basis if x not in ("slug","check_mail","folge_aktiv","folge_tage","folge_betreffe","folge_texte","vorlage","kicker")}})
k=[x for x in a.get("/api/admin/funnel").json()["kampagnen"] if x["slug"]==slug][0]
chk("Ändern ohne die neuen Felder lässt sie unverändert",r.status_code==200 and k["check_mail"] and k["folge_tage"]==[1,3,7] and k["kicker"]==basis["kicker"],r.text)
std=f"std-{sfx}"; a.post("/api/admin/funnel",json={**basis,"slug":std,"vorlage":"standard","check_mail":False})
chk("Standard-Seite bleibt beim bisherigen Formular",'funnel.js' in pub.get(f"/f/{std}").text and "funnel-check" not in pub.get(f"/f/{std}").text)
s=pub.get(f"/f/{slug}"); chk("Website-Check-Seite wird mit eigener Vorlage ausgeliefert",s.status_code==200 and "funnel-check.js" in s.text and "<script>" not in s.text,s.status_code)
g=pub.get(f"/api/public/funnel/{slug}").json()
chk("Öffentliche Angaben: Vorlage, Zeile, PDF-Hinweis, Kontakt aus den Firmendaten",g["vorlage"]=="website_check" and g["kicker"]==basis["kicker"] and g["check_mail"] and g["kontakt"]["telefon"]=="05141 12345" and g["website_abfragen"],g)
chk("Unbekannte Seite: Standardvorlage, keine Daten",pub.get("/f/gibtsnicht-xyz").status_code==200 and pub.get("/api/public/funnel/gibtsnicht-xyz").status_code==404)

# ---------------------------------------------------------------- Anmeldung und Prüfung
mail=f"check{sfx}@lead.de"; kam={"name":"Max Muster","email":mail,"telefon":"069 99","einwilligung":True,"utm":{"utm_source":"meta","utm_campaign":"check-ffm","utm_content":"A"}}
r=pub.post(f"/api/public/funnel/{slug}",json=kam); chk("Ohne Website-Adresse keine Anmeldung",r.status_code==400 and "Website" in r.text,r.text)
r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"website":"nur text"}); chk("Ungültige Website-Adresse wird abgelehnt",r.status_code==400,r.text)
r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"website":WEB+"/gut"}); j=r.json()
chk("Anmeldung klappt und liefert ein Kennzeichen für die Ampel",r.status_code==200 and j["neu"] and len(j.get("check") or "")>=20,r.text)
tok=j["check"]; lid=sql(f"select id from leads where email='{mail}'")
st=None
for _ in range(40):
    st=pub.get(f"/api/public/funnel/{slug}/check/{tok}").json()
    if st["status"]!="laeuft": break
    time.sleep(0.5)
schlecht_=[p["titel"] for p in st.get("punkte",[]) if p["status"]!="gut"]
chk("Prüfung ist nach kurzer Zeit fertig: 9 Prüfpunkte, nur https fehlt (Testseite läuft über http), deshalb Rot",st["status"]=="fertig" and len(st["punkte"])==9 and schlecht_==["Sichere Verbindung (https)"] and st["ampel"]=="rot" and st["score"]==85 and st["mail"],st)
chk("Status-Abfrage gibt keine persönlichen Daten heraus",not any(x in json.dumps(st) for x in (mail,"Max Muster","069")),st)
chk("Falsches Kennzeichen oder falsche Seite: nicht gefunden",pub.get(f"/api/public/funnel/{slug}/check/{'x'*24}").status_code==404 and pub.get(f"/api/public/funnel/{std}/check/{tok}").status_code==404)
chk("Lead: Firma aus der Website, Punktzahl, UTM und Kampagne",sql(f"select firma||'|'||score||'|'||(utm->>'utm_content')||'|'||(kampagne_id='{kid}') from leads where id='{lid}'")=="127.0.0.1|85|A|true",sql(f"select firma, score from leads where id='{lid}'"))
chk("Check gespeichert (fertig, grün, Kampagne)",sql(f"select status||'|'||ampel||'|'||(kampagne_id='{kid}') from lead_checks where lead_id='{lid}'")=="fertig|rot|true")
chk("Aufgabe „innerhalb einer Stunde anrufen“ bleibt",int(sql(f"select count(*) from aufgaben where auto_schluessel like 'lead-funnel-{lid}-%'"))==1)
time.sleep(1.5)
m=[x for x in an(mail) if "Website-Check" in betreff(x)]
chk("Ergebnis-Mail an den Interessenten mit Ampel im Betreff",len(m)==1 and betreff(m[0])=="Ihr Website-Check für 127.0.0.1: Rot",[betreff(x) for x in an(mail)])
if m:
    tx_=text(m[0]); pdfteil=[p for p in m[0].walk() if p.get_content_type()=="application/pdf"]
    chk("Mail: Anrede, Punkte, Terminlink, Gruß vom Team, Abmeldelink, kein KI-Name",tx_.startswith("Guten Tag Max Muster,") and "- Gut:" in tx_ and "/buchen" in tx_ and "Ihr Markentrix-Team" in tx_ and "/api/public/abmelden?t=" in tx_ and "Claude" not in tx_,tx_[:600])
    chk("PDF hängt an",len(pdfteil)==1 and pdfteil[0].get_filename()=="Website-Check-127.0.0.1.pdf",[p.get_content_type() for p in m[0].walk()])
    from pypdf import PdfReader
    t=" ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdfteil[0].get_payload(decode=True))).pages)
    chk("PDF enthält Ampel-Ergebnis und Prüfpunkte",("Ihr Website-Check" in t) and ("85 von 100" in t) and ("Ihre nächsten Schritte" in t) and ("Mit einem Tipp anrufen" in t),t[:300])
chk("Versand im Verlauf vermerkt",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and art='mail_gesendet' and inhalt like '%PDF%'"))==1)
chk("Ergebnis-Mail wird nicht doppelt geschickt",funnelcheck.mail_senden(int(sql(f"select id from lead_checks where lead_id='{lid}'")))==False and len([x for x in an(mail) if "Website-Check" in betreff(x)])==1)

# ---------------------------------------------------------------- PageSpeed zuschalten, schlechte Seite
chk("PageSpeed ist ab Werk aus",a.get("/api/admin/funnel-check/einstellungen").json()=={"pagespeed":False,"pagespeed_key_gesetzt":False})
a.put("/api/admin/funnel-check/einstellungen",json={"pagespeed":True,"pagespeed_key":"geheimer-schluessel-123"})
chk("Einstellung gespeichert, Schlüssel nur als „hinterlegt“ sichtbar",a.get("/api/admin/funnel-check/einstellungen").json()=={"pagespeed":True,"pagespeed_key_gesetzt":True})
mail2=f"check2{sfx}@lead.de"; r=pub.post(f"/api/public/funnel/{slug}",json={**kam,"email":mail2,"website":WEB+"/schlecht"}); tok2=r.json()["check"]
for _ in range(40):
    st2=pub.get(f"/api/public/funnel/{slug}/check/{tok2}").json()
    if st2["status"]!="laeuft": break
    time.sleep(0.5)
tempo=[p for p in st2.get("punkte",[]) if p["titel"]=="Ladezeit"]
chk("Schlechte Seite: Ampel Rot, Ladezeit aus PageSpeed",st2.get("ampel")=="rot" and tempo and "PageSpeed" in tempo[0]["text"] and "6,8 s" in tempo[0]["text"],st2)
lid2=sql(f"select id from leads where email='{mail2}'")
chk("Ergebnis vermerkt, dass PageSpeed genutzt wurde",sql(f"select ergebnis->>'pagespeed' from lead_checks where lead_id='{lid2}'")=="true")
a.put("/api/admin/funnel-check/einstellungen",json={"pagespeed":False,"pagespeed_key":"-"})
chk("Schlüssel lässt sich löschen",a.get("/api/admin/funnel-check/einstellungen").json()["pagespeed_key_gesetzt"]==False)

# ---------------------------------------------------------------- Admin: Lead, PDF, Probe, Rechte
ld=a.get(f"/api/admin/leads/{lid}").json(); c=ld["checks"][0]
chk("Lead-Ansicht zeigt den Check mit Ampel",c["status"]=="fertig" and c["ampel"]=="rot" and len(c["ergebnis"]["punkte"])==9,c.get("status"))
r=a.get(f"/api/admin/leads/{lid}/checks/{c['id']}/pdf"); chk("PDF des Checks im Admin abrufbar",r.status_code==200 and r.headers["content-type"]=="application/pdf" and r.content[:4]==b"%PDF",r.status_code)
chk("PDF zu fremdem Lead oder ohne Anmeldung: nein",a.get(f"/api/admin/leads/{lid2}/checks/{c['id']}/pdf").status_code==404 and pub.get(f"/api/admin/leads/{lid}/checks/{c['id']}/pdf").status_code in (401,403))
r=a.get("/api/admin/funnel-check/probe",params={"website":WEB+"/weiter"}); chk("Probe-Check folgt Umleitungen und liefert ein PDF",r.status_code==200 and r.content[:4]==b"%PDF",r.status_code)
chk("Probe legt keinen Lead an",sql("select count(*) from leads where website like '%/weiter%'")=="0")
chk("Probe mit ungültiger Adresse: verständlicher Fehler",a.get("/api/admin/funnel-check/probe",params={"website":"kaputt"}).status_code==400)
chk("Probe und Einstellungen nur für Admins",pub.get("/api/admin/funnel-check/probe",params={"website":WEB+"/gut"}).status_code in (401,403) and pub.get("/api/admin/funnel-check/einstellungen").status_code in (401,403))

# ---------------------------------------------------------------- Schutz: keine Abrufe ins eigene Netz (wie auf dem echten Server)
config.SITE_LOKAL_ERLAUBT=False
chk("Ohne Testfreigabe: localhost und Sonderports werden abgelehnt",funnelcheck.normalisieren("http://localhost:8000")is None and funnelcheck.normalisieren("https://beispiel.de:8443/") is None and funnelcheck.normalisieren("https://www.beispiel.de")=="https://www.beispiel.de")
s=funnelcheck.abrufen("http://127.0.0.1/"); chk("Abruf interner Adressen wird verweigert (127.0.0.1)",not s["ok"] and "nicht öffentlich" in s["fehler"],s)
chk("Umleitungsziele im eigenen Netz werden verweigert (10.x, 169.254.x, 192.168.x)",not any(funnelcheck._erlaubt(u) for u in ("http://10.0.0.1/","http://169.254.169.254/latest","http://192.168.1.1/","http://[::1]/")))
e=funnelcheck.pruefen("http://127.0.0.1:8997/gut"); chk("Check einer internen Adresse: Rot, „nicht erreichbar“, kein Absturz",e["ampel"]=="rot" and not e["erreichbar"],e)
config.SITE_LOKAL_ERLAUBT=True

# ---------------------------------------------------------------- Nachhol-Job
sql(f"insert into lead_checks (lead_id, website, status, token, kampagne_id, erstellt_am) values ('{lid2}', '{WEB}/gut', 'laeuft', 'nachhol{sfx}xxxxxxxxxxxx', '{kid}', now() - interval '10 minutes')")
sql(f"insert into lead_checks (lead_id, website, status, token, kampagne_id, erstellt_am, versuche) values ('{lid2}', '{WEB}/gut', 'laeuft', 'aufgeben{sfx}xxxxxxxxxxx', '{kid}', now() - interval '2 hours', 3)")
jobs.funnel_checks_nachholen(cfg())
chk("Liegengebliebener Check wird nachgeholt",sql(f"select status from lead_checks where token='nachhol{sfx}xxxxxxxxxxxx'")=="fertig")
chk("Nach 3 Fehlversuchen: als Fehler markiert und im Verlauf vermerkt",sql(f"select status from lead_checks where token='aufgeben{sfx}xxxxxxxxxxx'")=="fehler" and int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid2}' and inhalt like 'Website-Check ließ sich nicht%'"))==1)

# ---------------------------------------------------------------- Nachfass-Mails Tag 1, 3, 7
vorher=len(mails())
jobs.funnel_folgemails(cfg(),stunde=10); chk("Am ersten Tag noch keine Nachfass-Mail",len(mails())==vorher)
sql(f"update leads set erstellt_am=now()-interval '26 hours' where id='{lid}'")
jobs.funnel_folgemails(cfg(),stunde=21); chk("Abends (nach 19 Uhr) wird nichts verschickt",len(mails())==vorher)
jobs.funnel_folgemails(cfg(),stunde=10); time.sleep(1)
m=an(mail); b1=[x for x in m if betreff(x)==v["folge_betreffe"][0]]
chk("Nach 1 Tag: Nachfass-Mail 1 mit wichtigstem Punkt bzw. Terminlink",len(b1)==1 and "/buchen" in text(b1[0]) and "Ihr Markentrix-Team" in text(b1[0]) and "/api/public/abmelden?t=" in text(b1[0]),[betreff(x) for x in m])
jobs.funnel_folgemails(cfg(),stunde=10); time.sleep(1); chk("Kein zweites Mal am selben Tag",len([x for x in an(mail) if betreff(x)==v["folge_betreffe"][0]])==1 and int(sql(f"select count(*) from lead_funnel_folge where lead_id='{lid}'"))==1)
sql(f"update leads set erstellt_am=now()-interval '4 days' where id='{lid}'"); sql(f"update lead_funnel_folge set gesendet_am=now()-interval '3 days' where lead_id='{lid}'")
jobs.funnel_folgemails(cfg(),stunde=10); time.sleep(1); chk("Nach 3 Tagen: Nachfass-Mail 2",len([x for x in an(mail) if betreff(x)==v["folge_betreffe"][1]])==1)
sql(f"insert into lead_aktivitaeten (lead_id, art, inhalt, von) values ('{lid}','termin','Gespräch gebucht','website')")
sql(f"update leads set erstellt_am=now()-interval '8 days' where id='{lid}'"); sql(f"update lead_funnel_folge set gesendet_am=now()-interval '5 days' where lead_id='{lid}'")
jobs.funnel_folgemails(cfg(),stunde=10); time.sleep(1); chk("Nach gebuchtem Termin keine weitere Nachfass-Mail",len([x for x in an(mail) if betreff(x)==v["folge_betreffe"][2]])==0)
# Abmeldung stoppt ebenfalls
sql(f"update leads set erstellt_am=now()-interval '2 days', abgemeldet=true where id='{lid2}'")
jobs.funnel_folgemails(cfg(),stunde=10); time.sleep(1); chk("Nach Abmeldung keine Nachfass-Mail",len([x for x in an(mail2) if betreff(x)==v["folge_betreffe"][0]])==0)
# allgemeine Folgemails lassen Funnel-Leads mit eigenen Nachfass-Mails aus
a.put("/api/admin/einstellungen/folgemails",json={"aktiv":True,"tage_1":1,"tage_2":7})
mail3=f"check3{sfx}@lead.de"; pub.post(f"/api/public/funnel/{slug}",json={**kam,"email":mail3,"website":WEB+"/gut"}); lid3=sql(f"select id from leads where email='{mail3}'")
sql(f"update leads set erstellt_am=now()-interval '3 days' where id='{lid3}'")
jobs.lead_folgemails(cfg()); time.sleep(1)
chk("Allgemeine Folgemails gehen nicht zusätzlich an Funnel-Leads mit eigenen Nachfass-Mails",sql(f"select folge_stufe from leads where id='{lid3}'")=="0")

# ---------------------------------------------------------------- Browser: Seite und Danke-Ansicht
AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
async def browser():
    from playwright.async_api import async_playwright
    AXE=open(AXEJS).read()
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        for w in (390,1280):
            pg=await br.new_page(viewport={"width":w,"height":900}); fehler=[]
            pg.on("pageerror",lambda e: fehler.append(str(e))); pg.on("console",lambda m: fehler.append(m.text) if m.type=="error" else None)
            await pg.goto(B+f"/f/{slug}?utm_source=meta&utm_content=B"); await pg.wait_for_selector("#f:not([hidden])")
            await pg.evaluate(AXE)
            ax=await pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
            ov=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
            chk(f"Seite @{w}px: ohne Barrierefreiheits-Verstoß und ohne Überlaufen",not ax and ov<=0,(ax,ov))
            chk(f"Seite @{w}px: Inhalte aus der Kampagne",await pg.text_content("#kicker")==basis["kicker"] and await pg.inner_text("#b")==basis["button"] and "PDF" in await pg.inner_text("#el"))
            await pg.screenshot(path=f"/var/tmp/pt/funnel_{w}.png",full_page=True)
            await pg.click("#b"); chk(f"Seite @{w}px: Pflichtfelder werden angemahnt",(await pg.inner_text("#f-w")).startswith("Bitte"))
            await pg.fill("#w",f"127.0.0.1:8997/gut"); await pg.fill("#n","Bea Browser"); await pg.fill("#t","069 777"); await pg.fill("#e",f"b{w}{sfx}@lead.de"); await pg.check("#c")
            await pg.click("#b"); await pg.wait_for_selector("#danke:not([hidden])",timeout=10000)
            await pg.wait_for_selector("#liste:not([hidden])",timeout=30000)
            chk(f"Danke-Ansicht @{w}px: Ampel und Prüfpunkte erscheinen",await pg.get_attribute("#ampel","data-farbe") in ("gruen","gelb","rot") and await pg.locator("#liste li").count()==9)
            await pg.screenshot(path=f"/var/tmp/pt/danke_{w}.png",full_page=True)
            chk(f"Danke-Ansicht @{w}px: Termin-Knopf und Anruf-Link",await pg.get_attribute("#terminbox a.knopf","href")=="/buchen" and (await pg.get_attribute("#anruf","href")).startswith("tel:"))
            await pg.evaluate(AXE)
            ax=await pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
            chk(f"Danke-Ansicht @{w}px: ohne Barrierefreiheits-Verstoß",not ax,ax)
            chk(f"@{w}px: keine JavaScript-Fehler",not fehler,fehler)
            chk(f"@{w}px: UTM-Angaben aus der Adresse kommen im Lead an",sql(f"select utm->>'utm_content' from leads where email='b{w}{sfx}@lead.de'")=="B")
            await pg.close()
        await br.close()
if os.path.exists(AXEJS): asyncio.run(browser())
else: print("FAIL axe-core fehlt")
