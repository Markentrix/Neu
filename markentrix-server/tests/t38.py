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
sfx=str(int(time.time())+7)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
kid,c,mail=neuer_kunde("Nutzung")
pw="InhaberPasswort1"
# --- Nutzungsmessung
r=c.post("/api/me/nutzung",json={"seite":"heute"}); chk("Seite melden",r.status_code==200 and r.json()["ok"],r.text)
r=c.post("/api/me/nutzung",json={"seite":"Böse Seite; drop"}); chk("Ungültiger Seitenname wird nicht gespeichert",r.status_code==200 and r.json()["ok"] is False,r.text)
chk("Kein Seitenname mit Sonderzeichen in der Tabelle",sql("select count(*) from nutzung_seiten where seite !~ '^[a-z0-9_-]{1,30}$'")=="0")
r=c.get("/api/admin/nutzung"); chk("Kunde darf Auswertung nicht lesen",r.status_code==403,r.status_code)
r=httpx.post(B+"/api/me/nutzung",headers=H,json={"seite":"heute"}); chk("Ohne Login keine Meldung",r.status_code==401,r.status_code)
r=a.get("/api/admin/nutzung"); j=r.json()
chk("Admin-Auswertung",r.status_code==200 and any(s["seite"]=="heute" and s["rolle"]=="kunde" for s in j["seiten"]) and j["aktiv"].get("kunde",0)>=1 and "tour" in j,r.text[:300])
chk("Nur Seite/Tag/Rolle gespeichert (keine Inhalte)",sql("select string_agg(column_name,',' order by column_name) from information_schema.columns where table_name='nutzung_seiten'")=="n,rolle,seite,tag")
r=a.get("/api/admin/nutzung?tage=999"); chk("Zeitraum wird begrenzt",r.json()["tage"]==180)
# --- Ansicht: Tour
r=c.get("/api/me/ansicht"); chk("Tour anfangs nicht gesehen",r.json().get("tour_gesehen") is False,r.text)
r=c.put("/api/me/ansicht",json={"tour_gesehen":True}); chk("Tour speichern",r.status_code==200,r.text)
chk("Tour gesehen",c.get("/api/me/ansicht").json()["tour_gesehen"] is True)
c.put("/api/me/ansicht",json={"tour_gesehen":False})

# --- Browser: Tour + Handy-Leiste
from playwright.async_api import async_playwright
import asyncio
async def main():
    async with async_playwright() as pw_:
        br=await pw_.chromium.launch()
        ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True); pg=await ctx.new_page()
        errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e",mail); await pg.fill("#p",pw); await pg.click("#b"); await pg.wait_for_url("**/app*")
        await pg.wait_for_selector(".dlgoverlay",timeout=5000); chk("Tour erscheint beim ersten Start",await pg.locator(".dlg h3").inner_text()=="Willkommen bei Markentrix")
        await pg.click(".dlg >> text=Weiter"); await pg.click(".dlg >> text=Weiter")
        chk("Dritter Schritt",await pg.locator(".dlg >> text=Schritt 3 von 3").count()==1)
        await pg.click(".dlg >> text=Fertig"); await pg.wait_for_selector(".dlgoverlay",state="detached")
        chk("Tour als gesehen gespeichert",c.get("/api/me/ansicht").json()["tour_gesehen"] is True)
        await pg.reload(); await pg.wait_for_selector(".tabbar"); await pg.wait_for_timeout(800)
        chk("Tour kommt nicht wieder",await pg.locator(".dlgoverlay").count()==0)
        chk("Handy-Leiste sichtbar",await pg.locator(".tabbar").is_visible())
        chk("Leiste: Heute, zwei Seiten, Mehr",await pg.locator(".tabbar > *").count()==4)
        b=await pg.locator(".tabbar a").first.bounding_box(); chk("Tippfläche mind. 44px",b["height"]>=44,b)
        chk("Seitenleiste am Handy ohne Menüpunkte",await pg.locator(".side a.nav").first.is_hidden())
        ueber=await pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth"); chk("Kein Seitwärts-Scrollen",not ueber)
        await pg.click(".tabbar button"); await pg.wait_for_selector(".mehrblatt")
        chk("Mehr zeigt Menü + Abmelden",await pg.locator(".mehrblatt a.nav[href='#hilfe']").count()==1 and await pg.locator(".mehrblatt >> text=Abmelden").count()==1)
        await pg.click(".mehrblatt a.nav[href='#hilfe']"); await pg.wait_for_selector("text=Tour nochmal ansehen")
        chk("Menü schließt nach Auswahl",await pg.locator(".mehrblatt").count()==0)
        chk("Mehr ist markiert auf Hilfe",await pg.locator(".tabbar button.on").count()==1)
        await pg.click("text=Tour nochmal ansehen"); await pg.wait_for_selector(".dlg h3"); chk("Tour wiederholbar",True)
        await pg.keyboard.press("Escape")
        await pg.set_viewport_size({"width":1280,"height":900}); chk("Am Desktop keine Leiste",not await pg.locator(".tabbar").is_visible())
        chk("Seite hat Nutzung gemeldet",int(sql("select coalesce(sum(n),0) from nutzung_seiten where rolle='kunde' and seite='hilfe'"))>=1)
        chk("Keine JS-Fehler",not errs,errs)
        await br.close()
asyncio.run(main())
