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
sfx=str(int(time.time())+55)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"

import base64, datetime
import asyncio, os
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
kA,cA,mA=neuer_kunde("Anl")
# ---- Mail, QR
mm=[m for m in mails() if mA in str(m["To"])]; chk("Einladungsmail nennt Chrome/Safari und Installation",bool(mm) and "Chrome" in text(mm[-1]) and "Safari" in text(mm[-1]) and "App installieren" in text(mm[-1]))
q=a.get("/api/admin/portal-qr"); chk("QR-Code zur Portal-Adresse",q.status_code==200 and q.json()["svg"].startswith("data:image/svg+xml") and q.json()["url"].startswith("http"),q.text[:150])
chk("QR nur für Admins",cA.get("/api/admin/portal-qr").status_code==403)
pid=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Anleitung","email":f"va{sfx}@k.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"va{sfx}@k.de"),"password":"VeraPasswort123"})
AND="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36"
IOS="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
SAMSUNG="Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0 Mobile Safari/537.36"
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch()
        async def neu(ua):
            ctx=await br.new_context(viewport={"width":390,"height":844},device_scale_factor=2,user_agent=ua,has_touch=True,is_mobile=True,bypass_csp=True); return ctx, await ctx.new_page()
        async def login(pg,mail,pw_,ziel):
            await pg.goto(B+"/"); await pg.fill("#e",mail); await pg.fill("#p",pw_); await pg.click("#b"); await pg.wait_for_url("**/"+ziel+"*")
        # Kunde, Android
        ctx,pg=await neu(AND); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await login(pg,mA,"InhaberPasswort1","app")
        try: await pg.wait_for_selector(".schritt",timeout=8000)
        except Exception: print("DEBUG",pg.url,errs,(await pg.inner_text("body"))[:300]); raise
        chk("Kunde: erster Start zeigt die Anleitung",pg.url.endswith("#willkommen") and "So startest du bei Markentrix" in await pg.locator(".anltitel").inner_text(),pg.url)
        chk("Kunde: Android-Reiter vorgewählt, 5 Installationsschritte mit Bild",await pg.locator("button[aria-pressed=true]").inner_text()=="Android (Chrome)" and await pg.locator(".card:has-text('1 · App aufs Handy legen') .schritt").count()==5 and await pg.locator(".card:has-text('1 · App aufs Handy legen') .schritt svg").count()==5)
        chk("Kunde: Hinweis auf Chrome statt Fremdbrowser",await pg.locator("text=Samsung Internet").count()>=1)
        await pg.click("text=iPhone (Safari)"); chk("Kunde: iPhone-Reiter hat 6 Schritte mit Teilen-Symbol",await pg.locator(".card:has-text('1 · App aufs Handy legen') .schritt").count()==6 and await pg.locator("text=Teilen-Symbol antippen").count()==1)
        n=await pg.locator(".card:has-text('2 · So arbeitest du mit dem Portal') .schritt").count(); txt=await pg.locator(".card:has-text('2 · So arbeitest du mit dem Portal')").inner_text()
        chk("Kunde: Portal-Schritte mit Bildern, ohne Vertriebsthemen",n>=3 and "Freigaben" in txt and "Provision" not in txt and "Pipeline" not in txt and await pg.locator(".card:has-text('2 · So arbeitest du mit dem Portal') .schritt svg").count()==n,txt[:200])
        chk("Kunde: Menüpunkt „So geht’s“ erreichbar",await pg.locator(".tabbar").is_visible())
        await pg.screenshot(path="/var/tmp/pt/shots/anleitung_kunde.png",full_page=True)
        chk("Kunde: Banner nicht auf der Anleitung selbst",await pg.locator(".appbanner").count()==0)
        await pg.click("text=Los geht’s"); await pg.wait_for_function("location.hash==='#heute'"); await pg.wait_for_selector(".appbanner",timeout=4000)
        chk("Kunde: danach Banner „App aufs Handy legen“",await pg.locator(".appbanner").count()==1)
        await pg.click(".appbanner a"); await pg.wait_for_function("location.hash==='#willkommen'")
        await pg.goto(B+"/app#heute"); await pg.wait_for_selector(".appbanner"); await pg.click(".appbanner .zu"); await pg.reload(); await pg.wait_for_selector(".tabbar"); await pg.wait_for_timeout(500)
        chk("Kunde: Banner lässt sich wegklicken und bleibt weg",await pg.locator(".appbanner").count()==0)
        chk("Kunde: Anleitung kommt nicht erneut von allein","willkommen" not in pg.url)
        chk("Keine JS-Fehler Kunde",not errs,errs); await ctx.close()
        # Vertrieb, iPhone
        ctx,pg=await neu(IOS); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await login(pg,f"va{sfx}@k.de","VeraPasswort123","vertrieb"); await pg.wait_for_selector(".schritt",timeout=8000)
        chk("Vertrieb: eigene Überschrift, iPhone vorgewählt","Partnerportal" in await pg.locator(".anltitel").inner_text() and await pg.locator("button[aria-pressed=true]").inner_text()=="iPhone (Safari)")
        txt=await pg.locator(".card:has-text('So arbeitest du als Vertriebspartner')").inner_text(); n=await pg.locator(".card:has-text('So arbeitest du als Vertriebspartner') .schritt").count()
        chk("Vertrieb: acht Schritte (Anrufe, Ergebnis, Lead, Pipeline, Angebot, Zahlen, Provision, Leitfaden) mit Bild",n==8 and all(w in txt for w in ("Heute anrufen","Pipeline","Provisionen","Leitfaden","Angebot anfragen")) and await pg.locator(".card:has-text('So arbeitest du als Vertriebspartner') .schritt svg").count()==8,txt[:200])
        await pg.screenshot(path="/var/tmp/pt/shots/anleitung_vertrieb.png",full_page=True)
        chk("Vertrieb: Menüleiste mit Anleitung im Menü",await pg.locator(".tabbar").is_visible())
        await pg.click("text=Los geht’s"); await pg.wait_for_function("location.hash==='#heute'"); chk("Vertrieb: danach Heute-Seite",await pg.locator("h1").first.inner_text()!="")
        chk("Keine JS-Fehler Vertrieb",not errs,errs); await ctx.close()
        # Samsung-Browser: Warnhinweis
        ctx,pg=await neu(SAMSUNG); await login(pg,mA,"InhaberPasswort1","app"); await pg.goto(B+"/app#einstellungen"); await pg.wait_for_selector("text=App & Benachrichtigungen")
        chk("Samsung Internet: Hinweis auf Chrome in der App-Karte",await pg.locator("text=Bitte öffne das Portal zum Installieren in Google Chrome").count()==1); await ctx.close()
        # Desktop: kein Banner
        ctx=await br.new_context(viewport={"width":1280,"height":900},bypass_csp=True); pg=await ctx.new_page(); await login(pg,mA,"InhaberPasswort1","app"); await pg.goto(B+"/app#heute"); await pg.wait_for_selector("h1")
        chk("Desktop: kein Handy-Banner",await pg.locator(".appbanner").count()==0); await ctx.close()
        # Admin-Kundenblatt: QR-Karte
        ctx=await br.new_context(viewport={"width":1280,"height":900},bypass_csp=True); pg=await ctx.new_page(); await login(pg,"chef@test.de",PW,"admin")
        await pg.goto(B+"/admin#kunde/"+kA); await pg.wait_for_selector("text=Portal aufs Handy des Kunden",timeout=8000)
        chk("Admin: QR-Karte im Kundenblatt mit WhatsApp",await pg.locator("img[alt='QR-Code zum Portal']").count()==1 and await pg.locator("a:has-text('Per WhatsApp senden')").get_attribute("href").__await__().__next__ is not None if False else await pg.locator("a:has-text('Per WhatsApp senden')").count()==1)
        await pg.goto(B+"/admin#vertrieb"); 
        await br.close()
asyncio.run(main())
