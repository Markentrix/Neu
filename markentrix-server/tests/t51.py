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
sfx=str(int(time.time())+151)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import datetime, json, zoneinfo, concurrent.futures
TZ=zoneinfo.ZoneInfo("Europe/Berlin")
heute=datetime.datetime.now(TZ).date()
kA,cA,mA=neuer_kunde("Fri"); kB,cB,mB=neuer_kunde("Frb")
dom=f"friseur{sfx}.de"
sql(f"INSERT INTO websites (kunden_id, domain, art, status) VALUES ('{kA}','{dom}','live','live')")
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) values ('{kA}','website',true) on conflict do nothing"); sql(f"update kunden_module set aktiv=true where kunden_id='{kA}' and modul_code='website'")
W=httpx.Client(base_url=B,headers={"Host":dom}); API="/siteapi/api"
def post(body,ua="Mozilla/5.0 Test"): return W.post(API+"/anfrage",headers={"Content-Type":"application/json","Origin":"https://"+dom,"User-Agent":ua},content=json.dumps(body).encode())
K="/api/kunde/website-dienste"
cA.put(K+"/mail",json={"aktiv":True,"empfaenger":f"chef@{dom}","betreff":"x","name":"Salon"})
r=cA.put(K+"/kalender",json={"aktiv":True,"dauer":30,"tage":30,"von":"09:00","bis":"17:00","wochentage":[1,2,3,4,5,6,7],"vorlauf_std":0,"zeiten":"","kapazitaet":0,"freigabe":False,"halte_std":72}); chk("Kalender einrichten",r.status_code==200,r.text)
# ---- Leistungen
def leist(**kw): return cA.post(K+"/leistungen",json=kw)
r=leist(name="Herrenschnitt",dauer_min=30,preis="25 €"); chk("Leistung anlegen, Kurzname automatisch",r.status_code==200 and r.json()["schluessel"]=="herrenschnitt",r.text); lh=r.json()["id"]
r=leist(name="Damenschnitt",dauer_min=60); ld=r.json()["id"]
r=leist(name="Färben & Tönen",dauer_min=120,puffer_min=15); chk("Umlaute im Kurznamen",r.json()["schluessel"]=="faerben-toenen",r.text); lf=r.json()["id"]
chk("Doppelter Kurzname abgelehnt",leist(name="Herrenschnitt",dauer_min=30).status_code==400)
chk("Dauer außerhalb abgelehnt",leist(name="Zu lang",dauer_min=2000).status_code==422)
r=cA.put(f"{K}/leistungen/{lf}",json={"name":"Färben & Tönen","schluessel":"faerben","dauer_min":120,"puffer_min":15,"aktiv":True}); chk("Kurzname ändern",r.status_code==200,r.text)
chk("Fremde Firma kann Leistung nicht ändern",cB.put(f"{K}/leistungen/{lh}",json={"name":"Hack","dauer_min":5}).status_code==404)
chk("Fremde Firma sieht nichts",{k:v for k,v in cB.get(K+"/team").json().items() if k!="einstellung"}=={"leistungen":[],"mitarbeiter":[]})
# ---- Mitarbeiter
def ma(**kw): return cA.post(K+"/mitarbeiter",json=kw)
r=ma(name="Anna",leistungen=[]); chk("Mitarbeiterin anlegen",r.status_code==200 and r.json()["schluessel"]=="anna",r.text); anna=r.json()["id"]
r=ma(name="Ben",wochentage=[1,2,3,4,5],von="10:00",bis="14:00",leistungen=[lh]); chk("Mitarbeiter mit eigenen Zeiten und nur Herrenschnitt",r.status_code==200,r.text); ben=r.json()["id"]
chk("Ungültige Uhrzeiten abgelehnt",ma(name="Cora",zeiten="8 Uhr").status_code==400)
chk("Ende vor Beginn abgelehnt",ma(name="Cora",von="14:00",bis="10:00").status_code==400)
chk("Unbekannte Leistung abgelehnt",ma(name="Cora",leistungen=["00000000-0000-0000-0000-000000000000"]).status_code==400)
t=cA.get(K+"/team").json(); chk("Team lesbar",len(t["leistungen"])==3 and len(t["mitarbeiter"])==2 and t["mitarbeiter"][1]["leistungen"]==[lh],t)
r=W.get(API+"/leistungen").json(); chk("Öffentliche Leistungsliste",[x["key"] for x in r["leistungen"]]==["herrenschnitt","damenschnitt","faerben"] and r["leistungen"][2]["dauer"]==120,r)
r=W.get(API+"/mitarbeiter").json(); chk("Öffentliche Mitarbeiterliste mit Angebot",[(x["key"],x["leistungen"]) for x in r["mitarbeiter"]]==[("anna",[]),("ben",["herrenschnitt"])],r)
# Werktag mindestens 3 Tage voraus
d=heute+datetime.timedelta(days=3)
while d.isoweekday()>5: d+=datetime.timedelta(days=1)
tag=d.isoformat()
def slots(tag,**q): return {x["zeit"]:x["frei"] for x in W.get(API+"/slots",params={"tag":tag,**q}).json()["slots"]}
s=slots(tag,leistung="faerben",mitarbeiter="anna"); chk("Färben (2 Std.) passt nur bis 15:00 in den Tag",s["09:00"] and s["15:00"] and not s["15:30"] and not s["16:30"],s)
s=slots(tag,leistung="faerben",mitarbeiter="ben"); chk("Ben bietet kein Färben an: nichts frei",not any(s.values()),s)
s=slots(tag,leistung="herrenschnitt",mitarbeiter="ben"); chk("Ben arbeitet nur 10 bis 14 Uhr",not s["09:30"] and s["10:00"] and s["13:30"] and not s["14:00"],s)
r=W.get(API+"/slots",params={"tag":tag,"mitarbeiter":"gibtesnicht"}); chk("Unbekannte Person: 422",r.status_code==422 and "mitarbeiter" in r.json()["errors"],r.text)
r=W.get(API+"/slots",params={"tag":tag,"leistung":"gibtesnicht"}); chk("Unbekannte Leistung: 422",r.status_code==422 and "leistung" in r.json()["errors"],r.text)
v=W.get(API+"/verfuegbarkeit",params={"leistung":"herrenschnitt","mitarbeiter":"ben"}).json(); chk("Ben: Wochenende geschlossen",v["closedWeekdays"]==[0,6],v["closedWeekdays"])
v=W.get(API+"/verfuegbarkeit").json(); chk("Betrieb insgesamt: täglich offen (Anna)",v["closedWeekdays"]==[] and v["selfBooking"],v["closedWeekdays"])
# ---- Buchen
B1=lambda **kw:{"typ":"termin","name":"Gast Eins","email":"eins@besucher.de","telefon":"0511 111","einwilligung":"ja","datum":tag,"uhrzeit":"10:00","leistung":"damenschnitt","mitarbeiter":"anna",**kw}
r=post(B1()); chk("Damenschnitt bei Anna gebucht",r.status_code==200 and r.json()["ok"],r.text)
z=sql(f"select (extract(epoch from (ende-start))/60)::int || '|' || (select name from website_mitarbeiter where id=mitarbeiter_id) || '|' || (select name from website_leistungen where id=leistung_id) || '|' || status from website_termine where kunden_id='{kA}' and name='Gast Eins'")
chk("Dauer 60 Min., Zuordnung und Status gespeichert",z=="60|Anna|Damenschnitt|gebucht",z)
chk("Termin im Portal mit Leistung und Person",sql(f"select titel from termine where kunden_id='{kA}' and kontakt_name='Gast Eins'")=="Damenschnitt – Anna")
m=mail_an("eins@besucher.de","Ihr Termin"); chk("Bestätigung nennt Leistung und Person, mit Einladung",len(m)==1 and "Damenschnitt" in text(m[0]) and "bei Anna" in text(m[0]) and any(p.get_content_type()=="text/calendar" for p in m[0].walk()),[text(x) for x in m])
s=slots(tag,leistung="damenschnitt",mitarbeiter="anna"); chk("Anna: 10:00 und 10:30 belegt, 11:00 frei, 09:00 frei (passt vor 10:00)",not s["10:00"] and not s["10:30"] and s["11:00"] and s["09:00"],s)
s=slots(tag,leistung="damenschnitt",mitarbeiter="anna"); chk("09:30 passt nicht (60 Min. würden in die Buchung ragen)",not s["09:30"],s)
s=slots(tag,leistung="herrenschnitt",mitarbeiter="anna"); chk("Herrenschnitt (30 Min.) passt um 09:30 noch",s["09:30"] and not s["10:30"],s)
s=slots(tag,leistung="herrenschnitt"); chk("Egal wer: 10:30 frei über Ben",s["10:30"],s)
r=post(B1(name="Gast Zwei",email="zwei@besucher.de",uhrzeit="10:30",leistung="herrenschnitt",mitarbeiter="")); chk("Herrenschnitt ohne Wunschperson gebucht",r.status_code==200,r.text)
chk("Automatisch Ben zugeordnet",sql(f"select m.name from website_termine w join website_mitarbeiter m on m.id=w.mitarbeiter_id where w.kunden_id='{kA}' and w.name='Gast Zwei'")=="Ben")
s=slots(tag,leistung="herrenschnitt"); chk("10:30 jetzt für niemanden mehr frei",not s["10:30"],s)
r=post(B1(name="Gast Drei",email="drei@besucher.de",uhrzeit="10:30",leistung="herrenschnitt",mitarbeiter="ben")); chk("Doppelbuchung bei Ben abgelehnt",r.status_code==422 and "uhrzeit" in r.json()["errors"],r.text)
r=post(B1(name="Gast Drei",email="drei@besucher.de",leistung="gibtesnicht")); chk("Unbekannte Leistung bei der Buchung: 422",r.status_code==422 and "leistung" in r.json()["errors"],r.text)
r=post(B1(name="Gast Drei",email="drei@besucher.de",leistung="faerben",mitarbeiter="ben",uhrzeit="11:00")); chk("Ben kann nicht färben: Buchung abgelehnt",r.status_code==422,r.text)
# Pufferzeit
r=post(B1(name="Gast Vier",email="vier@besucher.de",uhrzeit="12:00",leistung="faerben",mitarbeiter="anna")); chk("Färben bei Anna gebucht",r.status_code==200,r.text)
s=slots(tag,leistung="herrenschnitt",mitarbeiter="anna"); chk("Pause nach dem Färben: 14:00 gesperrt, 14:30 frei",not s["13:30"] and not s["14:00"] and s["14:30"],s)
s=slots(tag,leistung="herrenschnitt"); chk("Egal wer 14:00: Ben arbeitet nur bis 14:00, also niemand",not s["14:00"],s)
# Urlaub einer Person
r=cA.post(K+"/sperrtage",json={"von":tag,"grund":"Urlaub","mitarbeiter_id":anna}); chk("Urlaub für Anna",r.status_code==200,r.text)
s=slots(tag,leistung="damenschnitt",mitarbeiter="anna"); chk("Anna hat an dem Tag keine freien Zeiten",not any(s.values()),s)
s=slots(tag,leistung="herrenschnitt",mitarbeiter="ben"); chk("Ben ist weiter buchbar",s["11:00"],s)
st=cA.get(K+"/sperrtage").json()["tage"]; chk("Sperrtage nennen die Person",st and st[0]["mitarbeiter"]=="Anna",st)
chk("Urlaub entfernen",cA.delete(f"{K}/sperrtage/{tag}?mitarbeiter={anna}").status_code==200 and slots(tag,leistung="damenschnitt",mitarbeiter="anna")["11:00"])
r=cA.post(K+"/sperrtage",json={"von":tag,"mitarbeiter_id":"00000000-0000-0000-0000-000000000000"}); chk("Urlaub für fremde Person abgelehnt",r.status_code==400,r.text)
# Buchungsliste
b=cA.get(K+"/buchungen").json()["buchungen"]; chk("Buchungsliste zeigt Leistung und Person",any(x["leistung"]=="Damenschnitt" and x["mitarbeiter"]=="Anna" for x in b) and any(x["leistung"]=="Herrenschnitt" and x["mitarbeiter"]=="Ben" for x in b),b)
# ---- Gleichzeitige Buchungen: genau eine gewinnt
tag2=(d+datetime.timedelta(days=1)).isoformat()
def versuch(i): return post(B1(name=f"Rennen {i}",email=f"rennen{i}@besucher.de",datum=tag2,uhrzeit="09:00",leistung="damenschnitt",mitarbeiter="anna")).status_code
with concurrent.futures.ThreadPoolExecutor(6) as ex: codes=list(ex.map(versuch,range(6)))
chk("6 gleichzeitige Buchungen: genau eine klappt",codes.count(200)==1 and codes.count(422)==5,codes)
chk("In der Datenbank nur eine Buchung",sql(f"select count(*) from website_termine where kunden_id='{kA}' and name like 'Rennen%' and status='gebucht'")=="1")
# ---- Mitarbeiter löschen: Termine bleiben
chk("Mitarbeiter löschen",cA.delete(f"{K}/mitarbeiter/{ben}").status_code==200)
chk("Termin von Ben bleibt erhalten",sql(f"select count(*) from website_termine where kunden_id='{kA}' and name='Gast Zwei' and status='gebucht'")=="1")
s=slots(tag,leistung="herrenschnitt"); chk("Ohne Ben bedient nur noch Anna",s["11:00"] and not s["10:00"],s)
# Anna pausieren: niemand mehr
r=cA.put(f"{K}/mitarbeiter/{anna}",json={"name":"Anna","aktiv":False}); chk("Mitarbeiterin pausieren",r.status_code==200,r.text)
chk("Ohne aktive Person ist nichts buchbar",not any(slots(tag,leistung="herrenschnitt").values()))
cA.put(f"{K}/mitarbeiter/{anna}",json={"name":"Anna","aktiv":True})
cA.put(f"{K}/mitarbeiter/{anna}",json={"name":"Anna","aktiv":True})
r=ma(name="Dora"); chk("Zweite Mitarbeiterin",r.status_code==200)
# ---- Oberfläche im Kundenportal
import asyncio, os
from playwright.async_api import async_playwright
os.makedirs("/var/tmp/pt/shots",exist_ok=True)
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1100,"height":1400},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=400 and not r.url.endswith("/api/me") else None)
        await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        await pg.goto(B+"/app#dienste")
        await pg.wait_for_selector("h2:text-is('Leistungen und Mitarbeiter')",timeout=8000)
        for t in ["Buchungen über die Website","Urlaub und Sperrtage","Besucher der letzten 30 Tage"]: chk("UI: Karte "+t,await pg.locator(f".card h2:text-is('{t}')").count()==1)
        c=pg.locator(".card:has(h2:text-is('Leistungen und Mitarbeiter'))")
        chk("UI: vorhandene Leistung mit Website-Kurzname","herrenschnitt" in await c.inner_text())
        await c.locator("input[placeholder='z. B. Damenhaarschnitt']").fill("Bartpflege"); await c.locator("input[placeholder='Min.']").fill("30"); await c.get_by_role("button",name="Hinzufügen").click()
        await pg.wait_for_selector("text=Name auf der Website: bartpflege",timeout=8000); chk("UI: Leistung hinzugefügt",True)
        chk("UI: Leistung liegt in der Datenbank",sql(f"select count(*) from website_leistungen where kunden_id='{kA}' and schluessel='bartpflege'")=="1")
        await pg.screenshot(path="/var/tmp/pt/shots/team_kunde.png",full_page=True)
        chk("UI: keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())

# ---- Betrieb ohne Team verhält sich wie vorher
tm=cA.get(K+"/team").json()
for x in tm["mitarbeiter"]: cA.delete(f"{K}/mitarbeiter/{x['id']}")
for x in tm["leistungen"]: cA.delete(f"{K}/leistungen/{x['id']}")
s=slots((d+datetime.timedelta(days=2)).isoformat()); chk("Ohne Team und Leistungen: Raster wie eingestellt",s["09:00"] and s["16:30"] and "17:00" not in s,s)
