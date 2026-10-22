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
sfx=str(int(time.time())+233)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import io, json, os, sys, datetime
from pypdf import PdfReader
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs, berichte
db.open_pool()
kA,cA,mA=neuer_kunde("Qa"); kB,cB,mB=neuer_kunde("Qb")
ADM=sql("select email from benutzer where rolle='admin' and aktiv order by erstellt_am limit 1")
p=a.post("/api/admin/vertrieb/partner",json={"name":"Paul Plan","email":f"paul{sfx}@v.de"}).json(); pid=p["id"]
l=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"paul{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":l.split("token=")[1],"password":"PaulPasswort123456"})
v=httpx.Client(base_url=B,headers=H); v.post("/api/login",json={"email":f"paul{sfx}@v.de","password":"PaulPasswort123456"})
def pdf_in_mail(adr,t):
    for m in reversed(mail_an(adr,t)):
        for part in m.walk():
            if part.get_content_type()=="application/pdf": return part.get_payload(decode=True)
# ---- 5: Gegenzeichnung im Protokoll
zid=a.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={"projekt":"Seite A"}).json()["id"]
ang={"elemente":{"name":{"an":True,"text":"Qa GmbH"},"kurz":{"an":True,"text":"Neue Website für <b>Qa</b>"},"zitat":{"an":True,"text":"Top <script>alert(1)</script>"},"link":{"an":True,"text":"https://qa.example.de"}},"kanaele":["web"]}
r=cA.post(f"/api/kunde/vertraege/{zid}/bestaetigen",json={"name":"Tina Test","ort":"Celle","akzeptiert":True,"angaben":ang}); chk("Referenz bestätigt",r.status_code==200,r.text)
b=pdf_in_mail(mA,"Kopie"); tx_=PdfReader(io.BytesIO(b)).pages[-1].extract_text().replace("\n"," ")
chk("Protokoll: Gegenzeichnung von Markentrix mit Versanddatum",("Gegenzeichnung Markentrix" in tx_) and ("Markentrix hat den Vertrag am" in tx_) and (f"an {mA}" in tx_.replace(" ","") or mA in tx_.replace(" ","")),tx_[-400:])
# ---- 10: Referenzseite
chk("Seite ist standardmäßig nicht öffentlich",httpx.get(B+"/referenzen").status_code==404 and httpx.get(B+"/api/referenzen").json()["eintraege"]==[])
rs=a.get("/api/admin/referenzseite").json(); chk("Admin sieht Vorschau",not rs["aktiv"] and any(e["name"]=="Qa GmbH" for e in rs["eintraege"]),rs)
chk("Seite nur für Admins",cA.get("/api/admin/referenzseite").status_code==403 and v.put("/api/admin/referenzseite",json={"aktiv":True}).status_code==403)
chk("Einschalten",a.put("/api/admin/referenzseite",json={"aktiv":True,"titel":"Referenzen","intro":"Unsere Projekte"}).status_code==200)
h_=httpx.get(B+"/referenzen"); chk("Öffentliche Seite zeigt nur Freigegebenes",h_.status_code==200 and "Qa GmbH" in h_.text and "Neue Website für" in h_.text and "https://qa.example.de" in h_.text,h_.status_code)
chk("Inhalte sind maskiert (kein Skript, kein HTML)","<script>alert" not in h_.text and "<b>Qa</b>" not in h_.text and "&lt;script&gt;" in h_.text)
# Kunde B: nur Name, kein Kanal -> nicht sichtbar
zb=a.post(f"/api/admin/kunden/{kB}/referenzvertrag",json={"projekt":"Seite B"}).json()["id"]
cB.post(f"/api/kunde/vertraege/{zb}/bestaetigen",json={"name":"Tina Test","ort":"Celle","akzeptiert":True,"angaben":{"elemente":{"name":{"an":True}},"kanaele":["social"]}})
chk("Kunde ohne Kanal „Website“ oder ohne Wortlaut erscheint nicht",f"Qb {sfx}" not in httpx.get(B+"/referenzen").text)
cA.post(f"/api/kunde/vertraege/{zid}/widerrufen",json={})
chk("Widerruf nimmt den Eintrag sofort von der Seite",all(e["name"]!="Qa GmbH" for e in httpx.get(B+"/api/referenzen").json()["eintraege"]))
a.put("/api/admin/referenzseite",json={"aktiv":False,"titel":"Referenzen","intro":""}); chk("Ausschalten: wieder 404",httpx.get(B+"/referenzen").status_code==404)
# ---- 12: Monatsbericht-Tipp
e=berichte.empfehlung({"anfragen":{"gesamt":10,"vormonat":10,"bearbeitet":2,"nach_quelle":{},"spam":0},"termine":{"gesamt":0,"nach_status":{}},"website":{"erreichbarkeit":97.0},"module":[]})
chk("Tipp: Erreichbarkeit hat Vorrang",e["titel"]=="Website zuverlässiger machen" and "97" in e["text"],e)
e=berichte.empfehlung({"anfragen":{"gesamt":10,"vormonat":10,"bearbeitet":2,"nach_quelle":{},"spam":0},"termine":{"gesamt":0,"nach_status":{}},"website":{},"module":[]}); chk("Tipp: unbeantwortete Anfragen",e["titel"]=="Anfragen schneller beantworten",e)
e=berichte.empfehlung({"anfragen":{"gesamt":0,"vormonat":0,"bearbeitet":0,"nach_quelle":{},"spam":0},"termine":{"gesamt":0,"nach_status":{}},"website":{"besucher":2},"module":[]}); chk("Tipp: Sichtbarkeit bei Flaute",e["titel"]=="Mehr Sichtbarkeit aufbauen",e)
e=berichte.empfehlung({"anfragen":{"gesamt":4,"vormonat":4,"bearbeitet":4,"nach_quelle":{},"spam":0},"termine":{"gesamt":0,"nach_status":{}},"website":{},"module":["wochenangebote"],"wochenangebote":0}); chk("Tipp: Modul ungenutzt",e["titel"]=="Wochenangebot veröffentlichen",e)
e=berichte.empfehlung({"anfragen":{"gesamt":4,"vormonat":4,"bearbeitet":4,"nach_quelle":{},"spam":0},"termine":{"gesamt":0,"nach_status":{}},"website":{"besucher":50,"anfragen":1},"module":[]}); chk("Tipp: ohne Auffälligkeit freundlicher Standard",e["titel"]=="Weiter so",e)
r=jobs.bericht_senden(kA,datetime.date.today().replace(day=1)-datetime.timedelta(days=1),mail=True); chk("Bericht gesendet",r["gesendet"],r)
mm=mail_an(mA,"Monatsbericht"); chk("Mail nennt den Tipp",len(mm)>=1 and "Unser Tipp für den nächsten Monat" in text(mm[-1]))
pb=pdf_in_mail(mA,"Monatsbericht"); chk("PDF enthält den Tipp",pb and "Unser Tipp für den nächsten Monat" in "".join(pg.extract_text() for pg in PdfReader(io.BytesIO(pb)).pages))
# ---- 11 + 6: Zufriedenheitsumfrage und Einwilligung
sql(f"update kunden set status='aktiv', erstellt_am=now()-interval '40 days' where id in ('{kA}','{kB}')")
jobs.umfragen_erzeugen()
o=cA.get("/api/kunde/umfrage").json()["offen"]; chk("Umfrage liegt im Portal bereit",o and o["art"]=="start",o)
chk("Ohne Einwilligung keine Mail",len(mail_an(mA,"zufrieden"))==0)
jobs.umfragen_erzeugen(); chk("Nicht doppelt",int(sql(f"select count(*) from kunden_umfragen where kunden_id='{kA}'"))==1)
uid=o["id"]
chk("Wert über 10 abgelehnt",cA.post(f"/api/kunde/umfrage/{uid}",json={"punkte":11}).status_code==422)
chk("Fremde Umfrage: 404",cB.post(f"/api/kunde/umfrage/{uid}",json={"punkte":9}).status_code==404)
chk("Vertriebler gesperrt",v.get("/api/kunde/umfrage").status_code in (401,403))
a.put("/api/admin/umfragen/einstellungen",json={"bewertungslink":"https://g.page/r/test"})
r=cA.post(f"/api/kunde/umfrage/{uid}",json={"punkte":10,"kommentar":"Alles top"}); chk("Begeisterter Kunde bekommt den Bewertungslink",r.status_code==200 and r.json()["bewertungslink"]=="https://g.page/r/test",r.text)
chk("Zweite Antwort nicht möglich",cA.post(f"/api/kunde/umfrage/{uid}",json={"punkte":1}).status_code==404)
chk("Danach keine offene Umfrage",cA.get("/api/kunde/umfrage").json()["offen"] is None)
ub=cB.get("/api/kunde/umfrage").json()["offen"]; r=cB.post(f"/api/kunde/umfrage/{ub['id']}",json={"punkte":4,"kommentar":"Zu langsam"}); chk("Unzufriedener Kunde: kein Link",r.status_code==200 and r.json()["bewertungslink"]=="")
mu=mail_an(ADM,"Unzufriedener Kunde"); chk("Team wird sofort informiert",len(mu)>=1 and "Zu langsam" in text(mu[-1]) and "4 von 10" in text(mu[-1]))
au=a.get("/api/admin/umfragen").json(); chk("Auswertung: Antworten, NPS, Verlauf",au["anzahl"]>=2 and au["nps"] is not None and au["quartale"] and any(x["kommentar"]=="Zu langsam" for x in au["antworten"]),au)
chk("Auswertung nur für Admins",cA.get("/api/admin/umfragen").status_code==403 and v.get("/api/admin/umfragen").status_code==403)
chk("Einwilligung: erst nein",cA.get("/api/kunde/einwilligungen").json()["umfrage_mail"] is False)
chk("Einwilligung erteilen",cA.put("/api/kunde/einwilligungen",json={"umfrage_mail":True}).status_code==200 and cA.get("/api/kunde/einwilligungen").json()["umfrage_mail"] is True)
chk("Nachweis mit Zeit und IP protokolliert",sql(f"select count(*) from kunden_einwilligungen where kunden_id='{kA}' and erteilt and ip is not null and benutzer='{mA}'")=="1")
cA.put("/api/kunde/einwilligungen",json={"umfrage_mail":True}); chk("Gleiche Einstellung erzeugt keinen zweiten Eintrag",sql(f"select count(*) from kunden_einwilligungen where kunden_id='{kA}'")=="1")
chk("Fremder Kunde sieht nur seine Einwilligung",cB.get("/api/kunde/einwilligungen").json()["umfrage_mail"] is False and v.get("/api/kunde/einwilligungen").status_code in (401,403))
sql(f"update kunden_umfragen set angelegt_am=now()-interval '100 days' where kunden_id='{kA}'"); jobs.umfragen_erzeugen()
chk("Nach 90 Tagen neue Umfrage (Quartal)",sql(f"select count(*) from kunden_umfragen where kunden_id='{kA}' and art='quartal' and beantwortet_am is null")=="1")
mq=mail_an(mA,"zufrieden"); chk("Mit Einwilligung kommt die Mail, mit Hinweis auf Widerruf, ohne KI-Namen",len(mq)==1 and "widerrufen" in text(mq[0]) and "Claude" not in text(mq[0]))
sql(f"update kunden_umfragen set angelegt_am=now()-interval '35 days' where kunden_id='{kA}' and beantwortet_am is null"); jobs.umfragen_erzeugen()
chk("Unbeantwortete Umfrage verfällt nach 30 Tagen",sql(f"select count(*) from kunden_umfragen where kunden_id='{kA}' and verfallen")=="1")
cA.put("/api/kunde/einwilligungen",json={"umfrage_mail":False}); chk("Widerruf der Einwilligung protokolliert",cA.get("/api/kunde/einwilligungen").json()["umfrage_mail"] is False and sql(f"select count(*) from kunden_einwilligungen where kunden_id='{kA}'")=="2")
# ---- 8: Rangliste
lid=a.post("/api/admin/leads",json={"firma":f"Rang Lead {sfx}","telefon":"0511 2","ort":"Celle"}).json()["id"]
sql(f"update leads set vertriebspartner_id='{pid}' where id='{lid}'")
sql(f"insert into lead_aktivitaeten (lead_id, art, inhalt, von) values ('{lid}','anruf','Angerufen: erreicht','test'),('{lid}','anruf','Angerufen: nicht erreicht','test')")
chk("Rangliste standardmäßig aus",v.get("/api/vertrieb/rangliste").json()=={"aktiv":False})
chk("Einstellung nur für Admins",v.put("/api/admin/vertrieb/rangliste-einstellung",json={"aktiv":True}).status_code==403 and cA.get("/api/admin/vertrieb/rangliste-einstellung").status_code==403)
a.put("/api/admin/vertrieb/rangliste-einstellung",json={"aktiv":True,"namen":False})
rg=v.get("/api/vertrieb/rangliste").json(); me=[x for x in rg["listen"]["anrufe"] if x["ich"]]
chk("Rangliste: eigene Position als „Du“ mit Wert",rg["aktiv"] and len(me)==1 and me[0]["name"]=="Du" and me[0]["wert"]==2 and me[0]["rang"]>=1,rg)
chk("Ohne Namen heißen andere „Vertriebler n“",all(x["ich"] or x["name"].startswith("Vertriebler") for l_ in rg["listen"].values() for x in l_))
chk("Rangliste nicht für Kunden",cA.get("/api/vertrieb/rangliste").status_code in (401,403))
a.put("/api/admin/vertrieb/rangliste-einstellung",json={"aktiv":True,"namen":True}); rg=v.get("/api/vertrieb/rangliste").json()
chk("Mit Namen: nur Vornamen",all(x["ich"] or " " not in x["name"] for l_ in rg["listen"].values() for x in l_))
# ---- 9: Nachfass-Erinnerung
sql(f"update leads set status='kontaktiert', wiedervorlage_am=current_date-1 where id='{lid}'")
jobs.vertrieb_erinnern(); mn=mail_an(f"paul{sfx}@v.de","nachfassen"); chk("Vertriebler bekommt die Erinnerung mit dem Lead",len(mn)==1 and f"Rang Lead {sfx}" in text(mn[0]) and "Wiedervorlage" in text(mn[0]) and "Claude" not in text(mn[0]),[text(x)[:200] for x in mn])
chk("Glocke/Push-Eintrag",int(sql(f"select count(*) from benachrichtigungen b join benutzer u on u.id=b.benutzer_id where u.vertriebspartner_id='{pid}' and b.tag='nachfassen'"))==1)
jobs.vertrieb_erinnern(); chk("Höchstens einmal am Tag",len(mail_an(f"paul{sfx}@v.de","nachfassen"))==1)
chk("Erinnerung ausschalten",v.put("/api/vertrieb/erinnerung",json={"an":False}).status_code==200 and v.get("/api/vertrieb/erinnerung").json()["an"] is False)
sql(f"update vertriebspartner set erinnerung_am=null where id='{pid}'"); jobs.vertrieb_erinnern(); chk("Ausgeschaltet: keine Mail mehr",len(mail_an(f"paul{sfx}@v.de","nachfassen"))==1)
v.put("/api/vertrieb/erinnerung",json={"an":True}); sql(f"update leads set wiedervorlage_am=null, letzter_kontakt_am=now()-interval '9 days' where id='{lid}'"); sql(f"update vertriebspartner set erinnerung_am=null where id='{pid}'")
jobs.vertrieb_erinnern(); mn=mail_an(f"paul{sfx}@v.de","nachfassen"); chk("Auch Leads ohne Kontakt seit einer Woche werden genannt",len(mn)==2 and "über einer Woche" in text(mn[-1]))
sql(f"update leads set status='gewonnen' where id='{lid}'"); sql(f"update vertriebspartner set erinnerung_am=null where id='{pid}'"); jobs.vertrieb_erinnern()
chk("Erledigte Leads lösen nichts aus",len(mail_an(f"paul{sfx}@v.de","nachfassen"))==2)
chk("Erinnerungs-Einstellung nur für Vertriebler",cA.put("/api/vertrieb/erinnerung",json={"an":False}).status_code in (401,403))
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
TOUR="fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); errs=[]
        async def seite(mail,pw_,ziel,breite=1200):
            ctx=await br.new_context(viewport={"width":breite,"height":1000},bypass_csp=True); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e",mail); await pg.fill("#p",pw_); await pg.click("#b"); await pg.wait_for_url("**/"+ziel+"*")
            await pg.evaluate(TOUR); await pg.wait_for_timeout(400); return pg
        sql(f"insert into kunden_umfragen (kunden_id, art) select '{kB}','quartal' where not exists (select 1 from kunden_umfragen where kunden_id='{kB}' and beantwortet_am is null and not verfallen)")
        pk=await seite(mB,"InhaberPasswort1","app"); await pk.goto(B+"/app#heute"); await pk.reload(); await pk.wait_for_selector("h2:has-text('Wie zufrieden bist du mit Markentrix?')",timeout=8000)
        chk("UI Kunde: Umfrage mit 11 Knöpfen auf der Startseite",await pk.locator("button[aria-label$=' von 10']").count()==11)
        await pk.locator("button[aria-label='9 von 10']").click(); await pk.wait_for_selector("h2:has-text('Danke für deine Rückmeldung!')",timeout=5000)
        chk("UI Kunde: Dank mit Bewertungslink bei 9",await pk.get_by_role("link",name="Bewertung schreiben").count()==1)
        await pk.goto(B+"/app#einstellungen"); await pk.reload(); await pk.wait_for_selector("h2:has-text('Meine Einwilligungen')",timeout=8000)
        chk("UI Kunde: Einwilligungen mit Referenz-Hinweis",await pk.get_by_text("Zufriedenheitsumfrage").count()>=1 and await pk.get_by_text("Referenz").count()>=1)
        pv=await seite(f"paul{sfx}@v.de","PaulPasswort123456","vertrieb",420); await pv.goto(B+"/vertrieb#konto"); await pv.reload(); await pv.wait_for_selector("h2:has-text('Nachfass-Erinnerung')",timeout=8000)
        chk("UI Vertrieb: Erinnerung schaltbar",await pv.get_by_text("Tägliche Erinnerung per Mail").count()==1)
        await pv.goto(B+"/vertrieb#uebersicht"); await pv.reload(); await pv.wait_for_selector("h2:has-text('Rangliste dieses Monats')",timeout=8000)
        chk("UI Vertrieb: Rangliste sichtbar",await pv.get_by_text("Du: ").count()>=1)
        pa_=await seite("chef@test.de",PW,"admin"); await pa_.goto(B+"/admin#zufriedenheit"); await pa_.reload(); await pa_.wait_for_selector("h1:has-text('Zufriedenheit')",timeout=8000)
        chk("UI Admin: Zufriedenheit mit NPS und Antworten",await pa_.get_by_text("NPS").count()>=1 and await pa_.get_by_text("Zu langsam").count()>=1)
        await pa_.goto(B+"/admin#vertraege"); await pa_.reload(); await pa_.wait_for_selector("h2:has-text('Referenzseite für die Website')",timeout=8000)
        chk("UI Admin: Referenzseite einstellbar",await pa_.get_by_text("Seite veröffentlichen").count()==1)
        await pa_.goto(B+"/admin#auswertung"); await pa_.reload(); await pa_.wait_for_selector("h2:has-text('Rangliste im Partnerportal')",timeout=8000)
        chk("UI Admin: Rangliste einstellbar",await pa_.get_by_text("Vornamen der anderen zeigen").count()==1)
        chk("Keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
print("FERTIG")
