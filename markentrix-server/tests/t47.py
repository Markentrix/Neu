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
sfx=str(int(time.time())+61)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


import json, asyncio, datetime, os
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
kA,cA,mA=neuer_kunde("Dien")
sql(f"insert into kunden_module (kunden_id, modul_code, aktiv) values ('{kA}','website',true) on conflict do nothing")
sql(f"update kunden_module set aktiv=true where kunden_id='{kA}' and modul_code='website'")
dom=f"dienste{sfx}.de"
a.post(f"/api/admin/kunden/{kA}/domains",json={"domain":dom,"registrar":"INWX","inhaber":"markentrix","auto_verlaengern":True,"status":"aktiv"})
a.put("/api/admin/einstellungen/places",json={"api_key":"places-test"})
sid=cA.get("/api/kunde/website-dienste").json()["site_id"]
os.makedirs("/var/tmp/pt/shots",exist_ok=True)
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(args=["--disable-features=PrivateNetworkAccessSendPreflights,BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessRespectPreflightResults,LocalNetworkAccessChecks"])
        ctx=await br.new_context(viewport={"width":1100,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        await pg.goto(B+"/app#dienste"); await pg.wait_for_selector("text=Kontaktformular: Anfragen per E-Mail",timeout=8000)
        for t in ["Terminbuchung mit deinem Kalender","PayPal","Google-Bewertungen"]: chk("Kunde: Karte "+t,await pg.locator(f".card h2:text-is('{t}')").count()==1)
        chk("Kunde: Domain sichtbar",await pg.locator(f"text={dom}").count()>=1)
        chk("Kunde: Menüpunkt Website-Dienste",await pg.locator("a[href='#dienste']").count()>=1)
        # Formular einschalten
        mk=pg.locator(".card:has(h2:text-is('Kontaktformular: Anfragen per E-Mail'))")
        await mk.locator("input[type=checkbox]").first.check(); await mk.locator("input[placeholder^='info@deinefirma']").first.fill(f"chef@{dom}")
        await mk.get_by_role("button",name="Speichern",exact=True).click(); await pg.wait_for_selector("text=Gespeichert.",timeout=4000)
        chk("Kunde: Formular gespeichert",cA.get("/api/kunde/website-dienste").json()["mail"]["aktiv"])
        await mk.get_by_role("button",name="Testmail senden").click(); await pg.wait_for_selector("text=Testmail gesendet",timeout=8000)
        chk("Kunde: Testmail angekommen",bool(mail_an(f"chef@{dom}","Testnachricht")))
        # Anbieter-Vorschlag
        await mk.locator("summary:has-text('Optional: Mails über dein eigenes Postfach')").click()
        ab=mk.locator("input[type=email]"); await ab.fill("max@gmail.com"); await ab.blur(); await pg.wait_for_timeout(800)
        chk("Kunde: Gmail-Server automatisch vorbelegt",await mk.locator("input[placeholder='smtp.deinanbieter.de']").input_value()=="smtp.gmail.com" and await pg.locator("text=App-Passwort").count()>=1)
        await mk.locator("input[type=password]").fill("falsch"); await mk.get_by_role("button",name="Prüfen und speichern").click()
        await pg.wait_for_selector(".msg.err",timeout=20000); chk("Kunde: Fehler beim Prüfen ist verständlich und nennt kein Geheimnis","falsch" not in await mk.inner_text())
        # Kalender
        kk=pg.locator(".card:has(h2:text-is('Terminbuchung mit deinem Kalender'))")
        await kk.locator("input[type=checkbox]").first.check(); await kk.locator("input[placeholder^='https://calendar.google.com']").fill("http://127.0.0.1:8999/ical/test.ics")
        await kk.get_by_role("button",name="Speichern",exact=True).click(); await pg.wait_for_selector("text=Gespeichert.",timeout=8000)
        await pg.wait_for_selector("input[placeholder^='Adresse ist gespeichert']",timeout=6000)
        kk=pg.locator(".card:has(h2:text-is('Terminbuchung mit deinem Kalender'))"); await kk.get_by_role("button",name="Kalender testen").click(); await pg.wait_for_selector("text=Dein Kalender wurde gelesen",timeout=8000)
        chk("Kunde: Kalender-Test zeigt freie Termine","freie Termine werden angeboten" in await kk.inner_text())
        chk("Kunde: Kalender-Adresse nicht mehr im Formular","ical/test" not in await kk.locator("input").evaluate_all("els=>els.map(e=>e.value).join('|')"))
        # PayPal
        pp=pg.locator(".card:has(h2:text-is('PayPal'))"); await pp.locator("input[type=checkbox]").check(); await pp.locator("input[placeholder='https://paypal.me/deinname']").fill("https://paypal.me/dienste")
        await pp.get_by_role("button",name="Speichern").click(); await pg.wait_for_selector("text=Gespeichert.",timeout=4000)
        # Bewertungen
        bw=pg.locator(".card:has(h2:text-is('Google-Bewertungen'))"); await bw.locator("input[type=checkbox]").first.check(); await bw.locator("input[placeholder='ChIJ…']").fill("ChIJtestplace12345")
        await bw.get_by_role("button",name="Bei Google abfragen").click(); await pg.wait_for_selector("text=Google meldet 4,7 Sterne",timeout=8000)
        chk("Kunde: Bewertungen werden bei Google abgefragt",True)
        await pg.screenshot(path="/var/tmp/pt/shots/dienste_kunde.png",full_page=True)
        chk("Keine JS-Fehler Kunde",not errs,errs); await ctx.close()
        # Admin-Sicht
        ctx=await br.new_context(viewport={"width":1100,"height":900},bypass_csp=True); pg=await ctx.new_page()
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+f"/admin#kunde/{kA}"); await pg.wait_for_selector(".card h2:text-is('Website-Dienste')",timeout=10000)
        ad=pg.locator(".card:has(h2:text-is('Website-Dienste'))"); t=await ad.inner_text()
        chk("Admin: Dienste und Einbau-Code sichtbar",sid in t and 'data-mk="kontakt"' in t and 'data-mk="termin"' in t and 'data-mk="bewertungen"' in t and 'data-mk="paypal"' in t and "Kalender verbunden: an" in t,t[:400])
        chk("Admin: keine Geheimnisse","ical/test" not in t and "places-test" not in t)
        await pg.goto(B+"/admin#einstellungen"); await pg.wait_for_selector("text=Google-Bewertungen (Places API)",timeout=8000); chk("Admin: Places-Schlüssel gesetzt angezeigt",await pg.locator("text=Schlüssel ist hinterlegt").count()==1)
        await ctx.close()
        # Website-Skript auf einer Kunden-Domain (Seite wird abgefangen, Skript kommt vom Portal)
        ctx=await br.new_context(viewport={"width":900,"height":900},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        html=f"""<!doctype html><meta charset=utf-8><body><h1>Testfirma</h1><div id=k data-mk="kontakt"></div><div id=t data-mk="termin"></div><div id=b data-mk="bewertungen"></div><div id=p data-mk="paypal" data-betrag="49,90"></div>
<script src="{B}/static/js/site.js" data-site="{sid}" defer></script>"""
        await pg.route(f"http://{dom}/",lambda r:r.fulfill(status=200,content_type="text/html",body=html))
        con=[]; pg.on("console",lambda m:con.append(m.text)); pg.on("requestfailed",lambda r:con.append("FAILED "+r.url+" "+str(r.failure)))
        await pg.goto(f"http://{dom}/")
        try: await pg.wait_for_selector("#k form",timeout=8000)
        except Exception: print("DEBUG",con,errs,(await pg.inner_text("body"))[:200]); raise
        await pg.wait_for_selector("#k form",timeout=8000); await pg.wait_for_selector("#t .mk-chip",timeout=8000); await pg.wait_for_selector("#b .mk-sterne",timeout=8000)
        chk("Website: Bewertungen mit Sternen und Autor","4,7 von 5" in await pg.locator("#b").inner_text() and "Anna K." in await pg.locator("#b").inner_text())
        chk("Website: Fremdtext wird nicht als HTML gesetzt",await pg.locator("#b b").count()==0 and "<b>Top</b>" in await pg.locator("#b").inner_text())
        chk("Website: Bewerten-Knopf",await pg.locator("#b a[href*='writereview']").count()==1)
        chk("Website: PayPal.Me-Knopf mit Betrag",await pg.locator("#p a[href='https://paypal.me/dienste/49.90EUR']").count()==1,await pg.locator("#p").inner_html())
        chk("Website: Lockfeld unsichtbar",await pg.locator("#k .mk-falle").count()==1 and await pg.locator("#k .mk-falle").evaluate("e=>e.getBoundingClientRect().right<0"))
        await pg.fill("#k input[autocomplete=name]","Paula Besucherin"); await pg.fill("#k input[type=email]","paula@besucher.de"); await pg.fill("#k textarea","Hallo, bitte um Rückruf. <b>fett</b>")
        await pg.click("#k button[type=submit]"); await pg.wait_for_timeout(600); chk("Website: Formular verlangt Einwilligung (Browser blockt)",await pg.locator("#k .mk-ok").count()==0)
        await pg.check("#k input[type=checkbox]"); await pg.click("#k button[type=submit]"); await pg.wait_for_selector("#k .mk-ok",timeout=8000)
        chk("Website: Formular abgeschickt, Mail beim Inhaber",bool(mail_an(f"chef@{dom}","Rückruf")))
        await pg.locator("#t .mk-chip").first.click(); await pg.locator("#t .mk-chip").nth(len(await pg.locator("#t .mk-chip").all())-1).wait_for(); 
        chk("Website: Tage als Knöpfe",await pg.locator("#t .mk-chip").count()>=3)
        await pg.screenshot(path="/var/tmp/pt/shots/dienste_website.png",full_page=True)
        chk("Keine JS-Fehler Website",not errs,errs)
        # Analytics: erst nach Einwilligung
        cA.put("/api/kunde/website-dienste/analytics",json={"aktiv":True,"id":"G-AB12CD34EF"})
        ctx3=await br.new_context(bypass_csp=True); p3=await ctx3.new_page(); gtm=[]; p3.on("request",lambda r:gtm.append(r.url) if "googletagmanager" in r.url else None)
        await p3.route("**/googletagmanager.com/**",lambda r:r.fulfill(status=200,content_type="text/javascript",body="window.__gtmgeladen=1"))
        await p3.route(f"http://{dom}/",lambda r:r.fulfill(status=200,content_type="text/html",body=html+'<footer><span data-mk="cookies"></span></footer>')); await p3.goto(f"http://{dom}/"); await p3.wait_for_selector("[aria-label=Statistik]",timeout=6000)
        chk("Analytics: Abfrage erscheint, vorher nichts an Google",not gtm and "Ablehnen" in await p3.locator("[aria-label=Statistik]").inner_text())
        await p3.click("[aria-label=Statistik] >> text=Ablehnen"); await p3.wait_for_timeout(500); chk("Analytics: abgelehnt = nichts geladen",not gtm and await p3.locator("[aria-label=Statistik]").count()==0)
        await p3.reload(); await p3.wait_for_timeout(1200); chk("Analytics: Ablehnung wird gemerkt",await p3.locator("[aria-label=Statistik]").count()==0 and not gtm)
        await p3.click("footer a"); await p3.wait_for_selector("[aria-label=Statistik]"); await p3.click("[aria-label=Statistik] >> text=Erlauben"); await p3.wait_for_timeout(800)
        chk("Analytics: nach Zustimmung wird Google geladen",any("id=G-AB12CD34EF" in u for u in gtm),gtm)
        await p3.reload(); await p3.wait_for_timeout(1200); chk("Analytics: Zustimmung wird gemerkt (kein Banner, Google lädt)",await p3.locator("[aria-label=Statistik]").count()==0 and len(gtm)>=2)
        await ctx3.close()
        # Fremde Domain: Dienst verweigert, Seite bleibt leer, kein Absturz
        ctx2=await br.new_context(bypass_csp=True); p2=await ctx2.new_page(); e2=[]; p2.on("pageerror",lambda e:e2.append(str(e)))
        await p2.route("http://fremd.example/",lambda r:r.fulfill(status=200,content_type="text/html",body=html)); await p2.goto("http://fremd.example/"); await p2.wait_for_timeout(1500)
        chk("Fremde Domain: keine Formulare, kein Fehler",await p2.locator("#k form").count()==0 and not e2,e2)
        await br.close()
asyncio.run(main())
