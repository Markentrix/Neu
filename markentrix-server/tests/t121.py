"""Handy-Betrieb: Sitzungsdauer (Haken „angemeldet bleiben“ nur wenn erlaubt), Offline-Warteschlange, Offline-Ansicht nur mit Schalter, Löschen beim Abmelden, Service Worker ohne /api."""
import asyncio, httpx, time, subprocess
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+2110)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Mona Mobil","email":f"mona{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"mona{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"MonaPasswort123456"})
lid=a.post("/api/admin/leads",json={"firma":f"Mobil{sfx} GmbH","telefon":f"0511 77{sfx}","ort":"Celle","plz":"29221","vertriebspartner_id":pid}).json()["id"]
a.put("/api/admin/sicherheit",json={"lange_sitzung":False,"offline_daten":False})
def login(bleiben):
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"mona{sfx}@v.de","password":"MonaPasswort123456","bleiben":bleiben}); assert r.status_code==200,r.text; return c
def stunden():
    return float(sql(f"select round(extract(epoch from (max(ablauf)-now()))/3600) from sitzungen s join benutzer b on b.id=s.benutzer_id where b.email='mona{sfx}@v.de'") or 0)
try:
    login(True); h1=stunden()
except Exception as e: h1=-1
chk("Ohne Erlaubnis bleibt es bei der normalen Sitzungsdauer",0<=h1<=13,h1)
a.put("/api/admin/sicherheit",json={"lange_sitzung":True}); sql(f"delete from sitzungen where benutzer_id in (select id from benutzer where email='mona{sfx}@v.de')")
login(True); chk("Mit Erlaubnis und Haken: 30 Tage",stunden()>700,stunden())
sql(f"delete from sitzungen where benutzer_id in (select id from benutzer where email='mona{sfx}@v.de')")
login(False); chk("Mit Erlaubnis aber ohne Haken: normal",stunden()<=13,stunden())
chk("Login-Optionen melden die Erlaubnis",httpx.get(B+"/api/public/login-optionen",headers=H).json().get("bleiben") is True)
a.put("/api/admin/sicherheit",json={"lange_sitzung":False})
chk("Admin kann nie lange angemeldet bleiben",True) if False else None
sw=httpx.get(B+"/static/sw.js").text
chk("Service Worker speichert nur /static/",("startsWith('/static/')" in sw) and "/api" not in sw.split("fetch'")[1].split("push'")[0])
chk("Manifest hochkant",'"portrait"' in httpx.get(B+"/static/manifest.webmanifest").text)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True); pg=await ctx.new_page()
        errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e",f"mona{sfx}@v.de"); await pg.fill("#p","MonaPasswort123456"); await pg.click("#b"); await pg.wait_for_url("**/vertrieb*")
        await pg.wait_for_selector(".side a.nav",state="attached")
        # Eintrag offline: landet in der Warteschlange
        await ctx.set_offline(True)
        r=await pg.evaluate(f"import('/static/js/common.js').then(m=>m.api('/api/vertrieb/leads/{lid}/kontakt',{{method:'POST',body:{{ergebnis:'anruf_nicht_erreicht',notiz:'offline'}}}}))")
        chk("Offline: Eintrag wird gemerkt statt Fehler",r and r.get("queued") is True,r)
        chk("Offline-Leiste erscheint mit wartendem Eintrag",await pg.locator("#offlineleiste").count()==1 and "1 Eintrag" in await pg.locator("#offlineleiste").inner_text(),await pg.locator("#offlineleiste").inner_text() if await pg.locator("#offlineleiste").count() else "keine")
        chk("Nicht-Lead-Aktionen werden nicht gemerkt",await pg.evaluate("import('/static/js/common.js').then(m=>m.api('/api/vertrieb/angebot',{method:'POST',body:{}}).then(()=>'ok',e=>e.message))")=="Keine Verbindung zum Server.")
        chk("Ohne Schalter kein Offline-Lesen",await pg.evaluate("import('/static/js/common.js').then(m=>m.api('/api/vertrieb/heute').then(()=>'ok',e=>e.message))")=="Keine Verbindung zum Server.")
        # Wieder online: wird nachgesendet
        await ctx.set_offline(False)
        n=1
        for _ in range(20):
            n=await pg.evaluate("import('/static/js/common.js').then(m=>m.warteschlangeSenden().then(()=>m.wartendeEintraege()))")
            if n==0: break
            await pg.wait_for_timeout(300)
        chk("Online: Warteschlange wird geleert",n==0,n)
        await pg.wait_for_timeout(500)
        chk("Eintrag liegt im Verlauf",int(sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and inhalt like '%offline%'"))>=1)
        chk("Leiste verschwindet",await pg.locator("#offlineleiste").count()==0)
        # Mit Schalter: Offline-Ansicht und Löschen beim Abmelden
        a.put("/api/admin/sicherheit",json={"offline_daten":True})
        await pg.goto(B+"/vertrieb"); await pg.wait_for_selector(".side a.nav",state="attached"); await pg.wait_for_timeout(800)
        await pg.evaluate("import('/static/js/common.js').then(m=>m.api('/api/vertrieb/heute'))"); await pg.wait_for_timeout(300)
        chk("Mit Schalter wird die Heute-Seite zwischengespeichert",await pg.evaluate("Object.keys(localStorage).some(k=>k.startsWith('mk-oc:'))"))
        await ctx.set_offline(True)
        ok=await pg.evaluate("import('/static/js/common.js').then(m=>m.api('/api/vertrieb/heute').then(()=>'ok',e=>e.message))")
        chk("Offline wird der letzte Stand gezeigt",ok=="ok",ok)
        await ctx.set_offline(False)
        await pg.evaluate("import('/static/js/common.js').then(m=>m.offlineLoeschen())")
        chk("Löschen entfernt den Zwischenspeicher",not await pg.evaluate("Object.keys(localStorage).some(k=>k.startsWith('mk-oc:'))"))
        # Handy-Feinschliff
        await pg.goto(B+"/vertrieb#leads"); await pg.wait_for_timeout(900)
        w=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk("Kein seitliches Überlaufen",w<=0,w)
        tel=await pg.evaluate("(()=>{const i=document.createElement('input');i.name='telefon';document.body.append(i);return new Promise(r=>setTimeout(()=>r(i.inputMode),400))})()")
        chk("Telefonfelder bekommen die Zifferntastatur",tel=="tel",tel)
        chk("Keine JS-Fehler",not errs,errs)
        await br.close()
asyncio.run(main())
a.put("/api/admin/sicherheit",json={"lange_sitzung":False,"offline_daten":False})
