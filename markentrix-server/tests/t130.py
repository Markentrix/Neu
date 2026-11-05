"""Admin-Kalender: Sperren und eigene Termine blockieren die Online-Buchung, Gespräche verschieben und absagen (mit Mail und Kalendereinladung),
Wiedervorlagen, Baustein für die Website (freigegebene Herkunft, nur https) und Oberfläche (390/1280 px, Barrierefreiheit)."""
import httpx, time, re, email, email.header, os, sys, subprocess, asyncio, datetime, json
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def betreff(m): return str(email.header.make_header(email.header.decode_header(m["Subject"] or "")))
def mail_an(adr, enthaelt=""):
    time.sleep(1.5)
    return [m for m in mails() if adr in str(m["To"]) and enthaelt in betreff(m)]
def ics_von(m):
    for p in m.walk():
        if p.get_content_type()=="text/calendar" or (p.get_filename() or "").endswith(".ics"): return p.get_payload(decode=True).decode()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+130)
E={"aktiv":True,"dauer":30,"tage":14,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"ort":"Telefon","erlaubte_seiten":"markentrix.de, www.markentrix.de"}
chk("Buchung einschalten",a.put("/api/admin/einstellungen/buchung",json=E).status_code==200)
anon=httpx.Client(base_url=B,headers=H)
def slots():
    d=anon.get("/api/public/buchung/slots").json(); return {s["start"]:(t["datum"],s["uhr"]) for t in d["tage"] for s in t["slots"]}
s0=slots(); chk("Freie Termine vorhanden",len(s0)>10,len(s0))
tage=sorted({v[0] for v in s0.values()}); T=tage[3]
chk("Tag hat Termine",any(v[0]==T for v in s0.values()))
# Sperre (ganztägig) blockiert den Tag
r=a.post("/api/admin/kalender/eintraege",json={"art":"sperre","titel":"Urlaub","start":T+"T00:00","ende":T+"T00:00","ganztag":True}); chk("Sperre anlegen",r.status_code==200,r.text); sid=r.json()["id"]
s1=slots(); chk("Ganztägige Sperre: Tag nicht mehr buchbar, andere Tage schon",not any(v[0]==T for v in s1.values()) and len(s1)>0,len(s1))
chk("Sperre nur ein Tag (24 Stunden)",len(s0)-len(s1)==sum(1 for v in s0.values() if v[0]==T))
chk("Sperre löschen",a.delete("/api/admin/kalender/eintraege/"+sid).status_code==200)
chk("Nach dem Löschen wieder buchbar",any(v[0]==T for v in slots().values()))
# eigener Termin 10:00-11:00 blockiert 10:00 und 10:30, nicht 9:30 und 11:00
r=a.post("/api/admin/kalender/eintraege",json={"art":"termin","titel":"Kundenanruf","start":T+"T10:00","ende":T+"T11:00"}); eid=r.json()["id"]
uhren={v[1] for v in slots().values() if v[0]==T}
chk("Eigener Termin 10–11 Uhr blockiert 10:00 und 10:30",("10:00" not in uhren) and ("10:30" not in uhren) and ("09:30" in uhren) and ("11:00" in uhren),sorted(uhren))
r=a.put("/api/admin/kalender/eintraege/"+eid,json={"art":"termin","titel":"Kundenanruf","start":T+"T10:15","ende":T+"T10:45"})
uhren={v[1] for v in slots().values() if v[0]==T}
chk("Verlegter Eintrag 10:15–10:45 blockiert 10:00 und 10:30 (Überschneidung)",r.status_code==200 and "10:00" not in uhren and "10:30" not in uhren and "11:00" in uhren,sorted(uhren))
a.delete("/api/admin/kalender/eintraege/"+eid)
chk("Eintrag ohne Ende nach Beginn abgelehnt",a.post("/api/admin/kalender/eintraege",json={"art":"termin","titel":"x","start":T+"T11:00","ende":T+"T10:00"}).status_code==400)
chk("Ungültige Art abgelehnt",a.post("/api/admin/kalender/eintraege",json={"art":"foo","titel":"x","start":T+"T10:00","ende":T+"T11:00"}).status_code==422)
chk("Unbekannter Eintrag: 404",a.delete("/api/admin/kalender/eintraege/00000000-0000-0000-0000-000000000000").status_code==404)
# Buchung eines Interessenten
mk=f"kal{sfx}@interessent.de"; start=[k for k,v in s0.items() if v[0]==T and v[1]=="14:00"][0]
r=anon.post("/api/public/buchung",json={"start":start,"name":"Karla Kalender","email":mk,"telefon":"0511 99","nachricht":"Hallo","einwilligung":True}); chk("Interessent bucht",r.status_code==200,r.text)
mail_an(mk,"gebucht") or mail_an(mk,"Gespräch")
kal=a.get(f"/api/admin/kalender?von={T}&bis={T}").json()
g=[x for x in kal["gespraeche"] if x["email"]==mk]; chk("Gespräch steht im Kalender",len(g)==1,kal)
gid=g[0]["id"] if g else None
lid=g[0]["lead_id"] if g else None
chk("Wiedervorlage des Leads am Gesprächstag",any(x["id"]==lid for x in kal["wiedervorlagen"]),kal["wiedervorlagen"])
chk("Buchungseinstellung im Kalender sichtbar",kal["buchung"]=={"aktiv":True,"dauer":30})
chk("Zeitraum über 70 Tage abgelehnt",a.get("/api/admin/kalender?von=2026-01-01&bis=2026-06-01").status_code==400)
chk("Ungültiges Datum abgelehnt",a.get("/api/admin/kalender?von=heute&bis=morgen").status_code==400)
# Verschieben
neu=[k for k,v in s0.items() if v[0]==T and v[1]=="15:00"][0]; neu_lokal=T+"T15:00"
chk("Auf belegte Zeit verschieben: 409",anon.post("/api/public/buchung",json={"start":start,"name":"Zweiter","email":"z"+mk,"einwilligung":True}).status_code==409)
r=a.post(f"/api/admin/gespraeche/{gid}/verschieben",json={"start":neu_lokal,"mail":True}); chk("Verschieben",r.status_code==200,r.text)
m=mail_an(mk,"verschoben"); chk("Mail „verschoben“ an den Interessenten",len(m)==1,[betreff(x) for x in mails()][-3:])
c=ics_von(m[0]) if m else ""; chk("Kalendereinladung mit gleicher UID und höherer Sequenz",bool(c) and "SEQUENCE:1" in c and "METHOD:PUBLISH" in c,c)
uh=lambda: {v[1] for v in slots().values() if v[0]==T}
chk("Alter Termin 14:00 wieder frei, neuer 15:00 belegt",("14:00" in uh()) and ("15:00" not in uh()),sorted(uh()))
chk("Lead: Aktivität „verschoben“",sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and inhalt like 'Gespräch verschoben%'")=="1")
chk("Verschieben in die Vergangenheit: 400",a.post(f"/api/admin/gespraeche/{gid}/verschieben",json={"start":"2020-01-01T10:00"}).status_code==400)
chk("Verschieben ohne Mail: keine zweite Mail",(a.post(f"/api/admin/gespraeche/{gid}/verschieben",json={"start":T+"T15:30","mail":False}).status_code==200) and len(mail_an(mk,"verschoben"))==1)
chk("Unbekanntes Gespräch: 404",a.post("/api/admin/gespraeche/00000000-0000-0000-0000-000000000000/verschieben",json={"start":T+"T16:00"}).status_code==404)
# Absagen
r=a.post(f"/api/admin/gespraeche/{gid}/absagen",json={"mail":True,"grund":"Ich bin leider krank."}); chk("Absagen",r.status_code==200,r.text)
m=mail_an(mk,"abgesagt"); chk("Mail „abgesagt“ mit Grund",len(m)==1,[betreff(x) for x in mails()][-3:])
c=ics_von(m[0]) if m else ""; chk("Absage-Einladung (CANCEL)",bool(c) and "METHOD:CANCEL" in c and "STATUS:CANCELLED" in c,c)
chk("Termin 15:30 wieder frei",("15:30" in uh()))
chk("Nicht mehr im Kalender",not [x for x in a.get(f"/api/admin/kalender?von={T}&bis={T}").json()["gespraeche"] if x["email"]==mk])
chk("Zweites Absagen: 404",a.post(f"/api/admin/gespraeche/{gid}/absagen",json={}).status_code==404)
chk("Lead zurück auf „antwort“",sql(f"select status from leads where id='{lid}'")=="antwort")
# Rechte
chk("Ohne Anmeldung: kein Kalender",anon.get(f"/api/admin/kalender?von={T}&bis={T}").status_code in (401,403))
chk("Ohne Anmeldung: kein Eintrag",anon.post("/api/admin/kalender/eintraege",json={"art":"sperre","titel":"x","start":T+"T10:00","ende":T+"T11:00"}).status_code in (401,403))
# Baustein für die Website
o=httpx.Client(base_url=B)
r=o.options("/api/public/buchung/slots",headers={"Origin":"https://markentrix.de","Access-Control-Request-Method":"GET","Access-Control-Request-Headers":"x-mk,content-type"})
chk("Vorabfrage von markentrix.de erlaubt",r.status_code==204 and r.headers.get("access-control-allow-origin")=="https://markentrix.de" and "x-mk" in r.headers.get("access-control-allow-headers","").lower(),(r.status_code,dict(r.headers)))
r=o.get("/api/public/buchung/slots",headers={"Origin":"https://www.markentrix.de"}); chk("Termine abrufbar von www.markentrix.de",r.status_code==200 and r.headers.get("access-control-allow-origin")=="https://www.markentrix.de",dict(r.headers))
r=o.get("/api/public/buchung/slots",headers={"Origin":"https://fremd.example"}); chk("Fremde Herkunft bekommt keine Freigabe",r.status_code==200 and "access-control-allow-origin" not in r.headers)
r=o.get("/api/public/buchung/slots",headers={"Origin":"http://markentrix.de"}); chk("Unverschlüsselte Herkunft bekommt keine Freigabe","access-control-allow-origin" not in r.headers)
r=o.options("/api/public/buchung",headers={"Origin":"https://fremd.example","Access-Control-Request-Method":"POST"}); chk("Vorabfrage fremder Herkunft ohne Freigabe","access-control-allow-origin" not in r.headers)
r=o.post("/api/public/buchung",headers={"Origin":"https://fremd.example","X-MK":"1"},json={"start":start,"name":"Mallory","email":"m@x.de","einwilligung":True}); chk("Buchen von fremder Herkunft: 403",r.status_code==403,r.text)
r=o.post("/api/public/buchung",headers={"Origin":"https://markentrix.de","X-MK":"1"},json={"start":neu,"name":"Web Besucher","email":f"web{sfx}@interessent.de","einwilligung":True}); chk("Buchen über den Baustein (markentrix.de)",r.status_code==200 and r.headers.get("access-control-allow-origin")=="https://markentrix.de",r.text)
r=o.post("/api/public/buchung",headers={"Origin":"https://markentrix.de"},json={"start":neu,"name":"Ohne Kopf","email":"o@x.de","einwilligung":True}); chk("Ohne X-MK-Kopfzeile: 403",r.status_code==403)
r=o.post("/api/public/buchung/absagen",headers={"Origin":"https://markentrix.de","X-MK":"1"},data={"t":"x"*24}); chk("Absage-Link nicht für Fremdseiten (kein CORS)","access-control-allow-origin" not in r.headers)
a.put("/api/admin/einstellungen/buchung",json={**E,"erlaubte_seiten":"andere.de"})
r=o.get("/api/public/buchung/slots",headers={"Origin":"https://markentrix.de"}); chk("Einstellung gilt sofort: markentrix.de nicht mehr freigegeben","access-control-allow-origin" not in r.headers)
a.put("/api/admin/einstellungen/buchung",json=E)
r=o.get("/static/js/erstgespraech.js"); chk("Baustein-Skript wird ausgeliefert",r.status_code==200 and "data-mk-erstgespraech" in r.text and "attachShadow" in r.text and "mk-erstgespraech-gebucht" in r.text)
sql("delete from kalender_eintraege")
# Oberfläche
AXE=open("/var/tmp/axe/node_modules/axe-core/axe.min.js").read()
heute=datetime.date.today()
a.post("/api/admin/kalender/eintraege",json={"art":"sperre","titel":"Urlaub Test","start":(heute+datetime.timedelta(days=2)).isoformat()+"T00:00","ende":(heute+datetime.timedelta(days=4)).isoformat()+"T00:00","ganztag":True})
a.post("/api/admin/kalender/eintraege",json={"art":"termin","titel":"Anruf Steuerberater mit langem Titel","start":heute.isoformat()+"T23:00","ende":heute.isoformat()+"T23:30"})
sl=slots(); st2=sorted(k for k,v in sl.items() if v[1]=="16:00")[0]
anon.post("/api/public/buchung",json={"start":st2,"name":"Oskar Oberfläche","email":f"ui{sfx}@interessent.de","einwilligung":True})
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for w,dunkel in ((390,False),(390,True),(1280,False)):
            ctx=await br.new_context(viewport={"width":w,"height":800},bypass_csp=True,is_mobile=w<700,has_touch=w<700,color_scheme="dark" if dunkel else "light"); pg=await ctx.new_page()
            errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",open("/var/tmp/pt/adminpw").read().strip()); await pg.click("#b"); await pg.wait_for_url("**/admin*")
            await pg.goto(B+"/admin#kalender"); await pg.wait_for_selector("h1:has-text('Kalender')",timeout=8000); await pg.wait_for_timeout(600)
            t=f"{w}px{' dunkel' if dunkel else ''}"
            chk(t+": Monatsansicht mit Einträgen",await pg.locator(".kalchip").count()>=2)
            chk(t+": Gespräch sichtbar",await pg.locator(".kalchip:has-text('Oskar Oberfläche')").count()>=1)
            for ansicht in ("Monat","Woche"):
                await pg.locator(f"button:text-is('{ansicht}')").click(); await pg.wait_for_timeout(500)
                o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                chk(f"{t} {ansicht}: kein seitliches Überlaufen",o<=0,o)
                await pg.add_script_tag(content=AXE)
                v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
                chk(f"{t} {ansicht}: Barrierefreiheit/Kontrast",not v,v[:3])
            if w==1280:
                await pg.locator(".kalchip:has-text('Oskar')").first.click(); await pg.wait_for_selector("[role=dialog]:has-text('Verschieben')")
                await pg.add_script_tag(content=AXE)
                v=await pg.evaluate("axe.run(document.querySelector('[role=dialog]'),{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))"); chk("Gesprächs-Dialog: Barrierefreiheit",not v,v[:3])
                await pg.keyboard.press("Escape")
                await pg.locator("button:has-text('+ Eintrag')").click(); await pg.wait_for_selector("[role=dialog]:has-text('Neuer Eintrag')")
                await pg.fill("[aria-label=Titel]","Neu per Oberfläche"); await pg.locator("[role=dialog] button:has-text('Speichern')").click(); await pg.wait_for_timeout(1200)
                chk("Eintrag per Oberfläche angelegt",sql("select count(*) from kalender_eintraege where titel='Neu per Oberfläche'")=="1")
                await pg.goto(B+"/admin#einstellungen"); await pg.wait_for_selector("input[name=seiten]",state="attached",timeout=25000); chk("Einstellungen: Seiten für den Baustein",await pg.input_value("input[name=seiten]")=="markentrix.de, www.markentrix.de")
            chk(t+": keine JavaScript-Fehler",not errs,errs[:2])
            await ctx.close()
        await br.close()
asyncio.run(main())
