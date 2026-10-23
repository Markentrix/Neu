import httpx, time, re, email, subprocess, asyncio
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+380)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
sql("update buchungen set rabatt_grund=null where rabatt_grund like 'Pilot-Nachlass%'")
sql("update konditionen set wert_zahl=2 where schluessel='pilot_plaetze_ki'")
kA,cA,mA=neuer_kunde("Pak"); kR,cR,mR=neuer_kunde("Pakref")
sql(f"update kunden set referenzkunde=true where id='{kR}'")
k=cA.get("/api/kunde/paketkatalog"); chk("Katalog antwortet",k.status_code==200,k.text); k=k.json()
alle=[p for g in k["gruppen"] for p in g["produkte"]]
chk("Katalog hat Gruppen und Pakete",len(k["gruppen"])>=3 and len(alle)>=8,len(alle))
codes={p["code"]:p for p in alle}
chk("Normalkunde: kein Referenzkunde",k["referenzkunde"] is False)
chk("Preise aus der Preisliste (netto, Cent)",any((p["monatlich_cent"] or 0)>0 for p in alle),alle[:2])
bsp=[p for p in alle if not p["auf_anfrage"] and p["code"]!="KI_ONE"]; auf=[p for p in alle if p["auf_anfrage"]]
b=bsp[0]["code"]
r=cA.post(f"/api/kunde/pakete/{b}/dazubuchen",json={"bestaetigt":False}); chk("Ohne Bestätigung abgelehnt",r.status_code in (400,422),r.text)
r=cA.post("/api/kunde/pakete/GIBTSNICHT/dazubuchen",json={"bestaetigt":True}); chk("Unbekanntes Paket: 404",r.status_code==404,r.text)
n0=len(mails())
r=cA.post(f"/api/kunde/pakete/{b}/dazubuchen",json={"bestaetigt":True,"notiz":"Bitte bald"}); chk("Dazubuchen klappt",r.status_code==200,r.text); bid=r.json()["id"]
st=sql(f"select status||'|'||coalesce(monatlich_cent,0)||'|'||coalesce(projekt_cent,0)||'|'||coalesce(einrichtung_cent,0) from buchungen where id='{bid}'")
chk("Buchung als angefragt mit eingefrorenem Preis",st.startswith("angefragt|"),st)
chk("Aufgabe für den Admin angelegt",sql(f"select count(*) from aufgaben where auto_schluessel='paketbuchung-{bid}'")=="1")
time.sleep(1.5); neu=mails()[n0:]
chk("Mail an Admin und Kunde",any("Neue Paketbuchung" in str(m["Subject"]) for m in neu) and any(mA in str(m["To"]) for m in neu),[m["Subject"] for m in neu])
chk("Kunden-Mail ohne KI-Unterschrift",all("Claude" not in (text(m) or "") for m in neu))
r=cA.post(f"/api/kunde/pakete/{b}/dazubuchen",json={"bestaetigt":True}); chk("Doppelt buchen: 409",r.status_code==409,r.text)
k=cA.get("/api/kunde/paketkatalog").json(); chk("Status im Katalog sichtbar",[p for g in k["gruppen"] for p in g["produkte"] if p["code"]==b][0]["status"]=="angefragt")
chk("Admin sieht offene Buchung",any(x["id"]==bid for x in a.get("/api/admin/paket-buchungen").json()))
chk("Kunde darf Admin-Liste nicht lesen",cA.get("/api/admin/paket-buchungen").status_code in (401,403))
chk("Kunde darf nicht selbst bestätigen",cA.post(f"/api/admin/buchungen/{bid}/bestaetigen",json={}).status_code in (401,403))
r=a.post(f"/api/admin/buchungen/{bid}/bestaetigen",json={}); chk("Admin bestätigt",r.status_code==200,r.text)
chk("Status beauftragt",sql(f"select status from buchungen where id='{bid}'")=="beauftragt")
chk("Nicht mehr in offener Liste",not any(x["id"]==bid for x in a.get("/api/admin/paket-buchungen").json()))
chk("Zweite Bestätigung: 404",a.post(f"/api/admin/buchungen/{bid}/bestaetigen",json={}).status_code==404)
# Ablehnen
b2=bsp[1]["code"]; bid2=cA.post(f"/api/kunde/pakete/{b2}/dazubuchen",json={"bestaetigt":True}).json()["id"]
chk("Admin lehnt ab",a.post(f"/api/admin/buchungen/{bid2}/ablehnen").status_code==200 and sql(f"select status from buchungen where id='{bid2}'")=="beendet")
chk("Abgelehntes Paket wieder buchbar",cA.post(f"/api/kunde/pakete/{b2}/dazubuchen",json={"bestaetigt":True}).status_code==200)
# Auf Anfrage
if auf:
    ba=auf[0]["code"]; r=cA.post(f"/api/kunde/pakete/{ba}/dazubuchen",json={"bestaetigt":True}); chk("Auf Anfrage: Angebotswunsch",r.status_code==200,r.text)
    ida=r.json()["id"]; chk("Auf Anfrage lässt sich nicht direkt bestätigen",a.post(f"/api/admin/buchungen/{ida}/bestaetigen",json={}).status_code==400)
# Referenzkunde
k=cR.get("/api/kunde/paketkatalog").json(); chk("Referenzkunde erkannt",k["referenzkunde"] is True)
pr=[p for g in k["gruppen"] for p in g["produkte"] if p["code"]==b][0]
chk("Referenzkunde: 0 € und regulärer Preis sichtbar",(pr["monatlich_cent"] or 0)==0 and (pr["projekt_cent"] or 0)==0 and (pr["einrichtung_cent"] or 0)==0 and pr.get("regulaer"),pr)
r=cR.post(f"/api/kunde/pakete/{b}/dazubuchen",json={"bestaetigt":True}); chk("Referenzkunde kann dazubuchen",r.status_code==200,r.text)
chk("Referenz-Buchung kostet 0 €",sql(f"select coalesce(monatlich_cent,0)+coalesce(projekt_cent,0)+coalesce(einrichtung_cent,0) from buchungen where id='{r.json()['id']}'")=="0")
# ---- Nachlässe, Hinweise, neue Leistungen
def buch(c,code):
    r=c.post(f"/api/kunde/pakete/{code}/dazubuchen",json={"bestaetigt":True}); assert r.status_code==200,r.text
    return sql(f"select coalesce(einrichtung_cent,0)||'|'||coalesce(projekt_cent,0)||'|'||coalesce(rabatt_grund,'') from buchungen where id='{r.json()['id']}'")
sql("update buchungen set rabatt_grund=null where rabatt_grund like 'Pilot-Nachlass%'")
kP1,cP1,_=neuer_kunde("Pilota"); kP2,cP2,_=neuer_kunde("Pilotb"); kK,cK,_=neuer_kunde("Kombi")
kat=lambda c,code:[p for g in c.get("/api/kunde/paketkatalog").json()["gruppen"] for p in g["produkte"] if p["code"]==code][0]
chk("Pilot-Nachlass schon im Katalog sichtbar",kat(cP1,"KI_BUSINESS")["einrichtung_cent"]==124500 and kat(cP1,"KI_BUSINESS")["listenpreis"]["einrichtung_cent"]==249000,kat(cP1,"KI_BUSINESS"))
r1=buch(cP1,"KI_BUSINESS"); chk("Pilot 1: 50 % auf die Einrichtung",r1.startswith("124500|0|Pilot-Nachlass 50 %"),r1)
r2=buch(cP2,"KI_KOMPLETT"); chk("Pilot 2: 50 % auf die Einrichtung",r2.startswith("174500|0|Pilot-Nachlass"),r2)
chk("Monatspreis bleibt unverändert",sql(f"select monatlich_cent from buchungen where kunden_id='{kP1}' and produkt_code='KI_BUSINESS'")=="69900")
chk("Kombi: ohne KI kein Nachlass auf Website",kat(cK,"WEB_BUSINESS")["projekt_cent"]==449000 and kat(cK,"WEB_BUSINESS")["nachlaesse"]==[])
r3=buch(cK,"KI_BUSINESS"); chk("Dritter Kunde: kein Pilot-Nachlass mehr",r3=="249000|0|",r3)
chk("Kombi: nach KI-BUSINESS 500 € weniger auf Website",kat(cK,"WEB_BUSINESS")["projekt_cent"]==399000)
w=buch(cK,"WEB_BUSINESS"); chk("Kombi Website+KI gebucht",w.startswith("0|399000|Kombi-Nachlass Website und KI"),w)
w2=buch(cK,"WEB_LANDING"); chk("Kombi nur einmal (zweite Website zum Listenpreis)",w2.startswith("0|229000|") and "Kombi" not in w2,w2)
c1=buch(cK,"CI_BASIC"); chk("Kombi CI+Website: 500 € weniger",c1.startswith("0|79000|Kombi-Nachlass Corporate Identity und Website"),c1)
kk=cK.get("/api/kunde/paketkatalog").json(); chk("Zusatzkosten-Hinweis und Werbebudget-Hinweis",("Werbebudget" in kk["zusatzkosten"]) and "Plattform" in kat(cK,"GOOGLE_ADS_AGENT")["hinweis"])
chk("Referenzkunde bekommt keine zusätzlichen Nachlässe",kat(cR,"KI_BUSINESS")["nachlaesse"]==[] and kat(cR,"KI_BUSINESS")["einrichtung_cent"]==0)
for code in ("WEB_RELAUNCH","WEB_PFLEGE","SEO_GEO","GOOGLE_PROFIL"):
    pk=kat(cK,code); chk(f"{code}: auf Anfrage buchbar",pk["auf_anfrage"] is True)
rr=cK.post("/api/kunde/pakete/SEO_GEO/dazubuchen",json={"bestaetigt":True}); chk("SEO/GEO als Angebotswunsch",rr.status_code==200,rr.text)
chk("Preisstand 1. Oktober 2026",sql("select wert_text from konditionen where schluessel='preisstand'")=="Stand 1. Oktober 2026")
# Suchmaschinen: Portal nicht indexieren
for pf in ("/","/admin","/app","/vertrieb","/api/health"):
    rr=httpx.get(B+pf); chk(f"noindex-Header auf {pf}","noindex" in rr.headers.get("x-robots-tag","") ,rr.headers)
chk("Anmeldeseite mit robots-Meta",'name="robots"' in httpx.get(B+"/").text)
# Rechte
chk("Ohne Anmeldung nicht möglich",httpx.get(B+"/api/kunde/paketkatalog").status_code==401)
t=cA.post("/api/kunde/team",json={"name":"Emma Empfang","email":f"emp{sfx}@k.de","rolle":"empfang"})
if t.status_code==200:
    tk=token(f"emp{sfx}@k.de")
    if tk:
        httpx.post(B+"/api/einladung",headers=H,json={"token":tk,"password":"EmpfangPasswort1"}); e=httpx.Client(base_url=B,headers=H); e.post("/api/login",json={"email":f"emp{sfx}@k.de","password":"EmpfangPasswort1"})
        chk("Empfang darf keine Pakete buchen",e.post(f"/api/kunde/pakete/{bsp[2]['code']}/dazubuchen",json={"bestaetigt":True}).status_code in (401,403))
from playwright.async_api import async_playwright
async def ui():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        for m,pw_,pfad,hash_,erwartet,name in ((mA,"InhaberPasswort1","/app","#pakete","Pakete & Zusatzleistungen","Kunde"),("chef@test.de",ADMPW,"/admin","#uebersicht","Neue Paketbuchungen","Admin")):
            ctx=await br.new_context(viewport={"width":390,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]
            pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=500 else None)
            await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw_); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
            for breite in (390,1280):
                await pg.set_viewport_size({"width":breite,"height":900})
                await pg.goto(B+pfad+hash_); await pg.reload(); await pg.wait_for_selector(f"h2:has-text('{erwartet}')",timeout=10000)
                chk(f"{name}@{breite}: „{erwartet}“ sichtbar",True)
                if name=="Kunde":
                    await pg.click("button:has-text('Dazubuchen') >> nth=0"); await pg.wait_for_selector(".dlg",timeout=5000)
                    chk(f"Kunde@{breite}: Dialog mit Preis und Bestätigung","netto" in (await pg.inner_text(".dlg")) or "Preis" in (await pg.inner_text(".dlg")))
                chk(f"{name}@{breite}: kein seitliches Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
            chk(f"{name}: keine JS-Fehler",not errs,errs); await ctx.close()
        await br.close()
asyncio.run(ui())
print("fertig")
