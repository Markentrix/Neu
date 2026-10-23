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
sfx=str(int(time.time())+370)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
kA,cA,mA=neuer_kunde("Wert"); kB,cB,mB=neuer_kunde("Wertb")
# ---- Wert-Karte
for i in range(4): sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,status) values ('{kA}','A{i}','a{i}@x.de','Hallo','website','neu')")
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,status) values ('{kA}','Spam','s@x.de','Billig kaufen','website','spam')")
for i,(erg,preis,anz) in enumerate((("erschienen",50,10),("erschienen",70,0),("nicht_erschienen",40,0),(None,30,0))):
    sql(f"insert into website_termine (kunden_id,start,ende,name,email,token,status,ergebnis,preis_betrag,anzahlung_betrag,anzahlung_erhalten_am,erinnerung) values ('{kA}',now()+interval '{i+1} days',now()+interval '{i+1} days 30 minutes','K{i}','k{i}@x.de','tok{sfx}{i}','gebucht',{('NULL' if erg is None else repr(erg))},{preis},{anz},{'now()' if anz else 'NULL'},2)")
sql(f"insert into website_warteliste (kunden_id,ref,name,email,tag,status,benachrichtigt_am) values ('{kA}','L{sfx}','W','w@x.de',current_date,'benachrichtigt',now())")
w=cA.get("/api/kunde/wertbilanz"); chk("Wert-Endpunkt antwortet",w.status_code==200,w.text); w=w.json(); d=w["dieser"]
chk("Anfragen ohne Spam gezählt",d["anfragen"]==4 and d["spam_abgefangen"]==1,d)
chk("Termine, Erschienene, Nicht erschienene",d["termine_gebucht"]==4 and d["erschienen"]==2 and d["nicht_erschienen"]==1,d)
chk("Umsatz nur aus erschienenen Terminen",d["umsatz_erschienen"]==120.0,d)
chk("Anzahlung erhalten",d["anzahlungen_summe"]==10.0 and d["anzahlungen_anzahl"]==1,d)
chk("Erinnerungen und Warteliste",d["erinnerungen"]==8 and d["warteliste_benachrichtigt"]==1,d)
chk("Zeitersparnis aus Vorgängen berechnet",d["vorgaenge"]==4+8+1 and d["stunden_gespart"]==round(13*3/60,1),d)
z=cB.get("/api/kunde/wertbilanz").json()["dieser"]; chk("Anderer Kunde sieht nichts von A",z["anfragen"]==0 and z["termine_gebucht"]==0 and z["umsatz_erschienen"]==0,z)
chk("Ohne Anmeldung nicht möglich",httpx.get(B+"/api/kunde/wertbilanz").status_code==401)
# ---- Vertriebler im Blick
p1=a.post("/api/admin/vertrieb/partner",json={"name":f"Spaet {sfx}","email":f"sp{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
p2=a.post("/api/admin/vertrieb/partner",json={"name":f"Fleissig {sfx}","email":f"fl{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"fl{sfx}@v.de"),"password":"VeraPasswort123"})
for i in range(3): sql(f"insert into leads (firma,telefon,status,vertriebspartner_id,erstellt_am) values ('Alt {sfx} {i}','05141 7{sfx}{i}','neu','{p1}',now()-interval '10 days')")
sql(f"insert into leads (firma,telefon,status,vertriebspartner_id,wiedervorlage_am,letzter_kontakt_am) values ('Fällig {sfx}','05141 8{sfx}','kontaktiert','{p1}',current_date-1,now()-interval '3 days')")
ids=[]
for i in range(2): sql(f"insert into leads (firma,telefon,status,vertriebspartner_id,letzter_kontakt_am) values ('Neu {sfx} {i}','05141 9{sfx}{i}','kontaktiert','{p2}',now())")
lid=sql(f"select id from leads where firma='Neu {sfx} 0'")
for i in range(5): sql(f"insert into lead_aktivitaeten (lead_id,art,inhalt,zeit) values ('{lid}','anruf','x',now()-interval '{i} hours')")
sql(f"insert into lead_aktivitaeten (lead_id,art,inhalt) values ('{lid}','termin','x')")
q=a.get("/api/admin/vertrieb/qualitaet"); chk("Qualitäts-Endpunkt antwortet",q.status_code==200,q.text); q=q.json()
sp=[x for x in q["vertriebler"] if x["name"]==f"Spaet {sfx}"][0]; fl=[x for x in q["vertriebler"] if x["name"]==f"Fleissig {sfx}"][0]
chk("Säumiger Vertriebler: rot mit Gründen",sp["ampel"]=="rot" and sp["unberuehrt_7t"]==3 and sp["ueberfaellig"]==1 and any("keine Anrufe" in h for h in sp["hinweise"]),sp)
chk("Fleißiger Vertriebler: in Ordnung, Quote berechnet",fl["ampel"]=="gruen" and fl["anrufe_7t"]==5 and fl["termine_30t"]==1 and fl["termin_quote"]==20.0,fl)
chk("Sortierung: Handlungsbedarf zuerst",q["vertriebler"].index(sp)<q["vertriebler"].index(fl))
v=httpx.Client(base_url=B,headers=H); v.post("/api/login",json={"email":f"fl{sfx}@v.de","password":"VeraPasswort123"})
chk("Vertriebler darf die Übersicht nicht lesen",v.get("/api/admin/vertrieb/qualitaet").status_code in (401,403))
chk("Kunde darf die Übersicht nicht lesen",cA.get("/api/admin/vertrieb/qualitaet").status_code in (401,403))
# ---- Aktivität je Vertriebler
ak=a.get(f"/api/admin/vertrieb/partner/{p2}/aktivitaet?tage=7"); chk("Aktivitäts-Endpunkt antwortet",ak.status_code==200,ak.text); ak=ak.json()
chk("Aktivität: Summen stimmen",ak["summe"]["anrufe"]==5 and ak["summe"]["termine"]==1 and ak["summe"]["leads_bearbeitet"]==1,ak["summe"])
chk("Aktivität: Verlauf hat 7 Tage, offene Leads gezählt",len(ak["verlauf"])==7 and ak["summe"]["offene_leads"]==2 and ak["summe"]["neue_leads"]==2,ak["summe"])
chk("Aktivität: letzte Einträge mit Firma",len(ak["letzte"])==6 and ak["letzte"][0]["firma"]==f"Neu {sfx} 0",ak["letzte"][:1])
a0=a.get(f"/api/admin/vertrieb/partner/{p1}/aktivitaet?tage=90").json(); chk("Säumiger Vertriebler: keine Aktivität, 90 Tage",a0["summe"]["anrufe"]==0 and len(a0["verlauf"])==90 and a0["letzte"]==[],a0["summe"])
chk("Ungültiger Zeitraum wird 30 Tage",len(a.get(f"/api/admin/vertrieb/partner/{p2}/aktivitaet?tage=5").json()["verlauf"])==30)
chk("Unbekannter Vertriebler: 404",a.get("/api/admin/vertrieb/partner/00000000-0000-0000-0000-000000000000/aktivitaet").status_code==404)
chk("Vertriebler darf Aktivität nicht lesen",v.get(f"/api/admin/vertrieb/partner/{p2}/aktivitaet").status_code in (401,403))
chk("Kunde darf Aktivität nicht lesen",cA.get(f"/api/admin/vertrieb/partner/{p2}/aktivitaet").status_code in (401,403))
from playwright.async_api import async_playwright
async def ui():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        for breite in (390,1280):
            for m,pw_,pfad,erwartet,name in ((mA,"InhaberPasswort1","/app","Das hat Markentrix im","Kunde"),("chef@test.de",ADMPW,"/admin","Vertriebler im Blick","Admin")):
                ctx=await br.new_context(viewport={"width":breite,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]
                pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("response",lambda r: errs.append(f"HTTP {r.status} {r.url}") if r.status>=500 else None)
                await pg.goto(B+"/"); await pg.fill("#e",m); await pg.fill("#p",pw_); await pg.click("#b"); await pg.wait_for_url("**"+pfad+"*")
                await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
                await pg.goto(B+pfad+("#heute" if name=="Kunde" else "#uebersicht")); await pg.wait_for_selector(f"h2:has-text('{erwartet}')",timeout=10000)
                chk(f"{name}@{breite}: Karte „{erwartet}“ sichtbar",True)
                chk(f"{name}@{breite}: kein seitliches Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
                if name=="Admin":
                    await pg.goto(B+f"/admin#partner/{p2}"); await pg.wait_for_selector("h2:has-text('Aktivität')",timeout=10000); await pg.click("button:has-text('90 Tage')"); await pg.wait_for_selector("button[aria-pressed=true]:has-text('90 Tage')",timeout=5000)
                    chk(f"Admin@{breite}: Aktivität im Vertriebler-Detail, Zeitraum wechselbar",True)
                    chk(f"Admin@{breite}: Detail ohne seitliches Überlaufen",await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"))
                chk(f"{name}@{breite}: keine JS-Fehler",not errs,errs); await ctx.close()
        await br.close()
asyncio.run(ui())
print("fertig")
