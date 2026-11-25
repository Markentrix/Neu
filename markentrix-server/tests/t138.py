"""Admin-Menü am Desktop: Favoriten per Stern, Betriebs-Ampel neben der Glocke, Zähler an Gruppen, Barrierefreiheit."""
import asyncio, httpx, time, re, email, subprocess, os, sys
from playwright.async_api import async_playwright
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
sfx=str(int(time.time())+3700)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt"); sys.exit(0)
AXE=open(AXEJS).read()
hh=a.get("/api/admin/heute").json(); chk("Heute-Daten liefern Zähler-Felder",all(x in hh for x in ("leads_gesamt","wiedervorlagen","rechnungen","onboarding")),list(hh))
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for dunkel in (False,True):
            n="dunkel" if dunkel else "hell"
            ctx=await br.new_context(viewport={"width":1280,"height":900},bypass_csp=True,color_scheme="dark" if dunkel else "light")
            pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",open("/var/tmp/pt/adminpw").read().strip()); await pg.click("#b"); await pg.wait_for_url("**/admin*")
            await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})}); localStorage.removeItem('mk-admin-favoriten')")
            await pg.goto(B+"/admin#uebersicht"); await pg.wait_for_selector(".navkopf"); await pg.wait_for_timeout(600)
            chk(f"{n}: Betriebs-Ampel neben der Glocke",await pg.locator(".brandzeile .ampelpunkt").count()==1)
            kl=await pg.locator(".brandzeile .ampelpunkt").get_attribute("class"); chk(f"{n}: Ampel hat einen Stand",any(x in kl for x in ("ok","warn","bad","unbekannt")),kl)
            chk(f"{n}: Gruppen ohne Favoriten",await pg.locator(".navkopf:has-text('Favoriten')").count()==0)
            chk(f"{n}: sechs Gruppen",await pg.locator(".navgruppe").count()==6,await pg.locator(".navgruppe").count())
            await pg.locator(".navzeile:has(a[href='#kalender'])").hover(); await pg.locator(".navzeile:has(a[href='#kalender']) .sternknopf").click(); await pg.wait_for_selector(".navkopf:has-text('Favoriten')",timeout=6000); await pg.wait_for_timeout(300)
            chk(f"{n}: Stern legt Favoriten-Gruppe an",await pg.locator(".navgruppe:has(.navkopf:has-text('Favoriten')) a[href='#kalender']").count()==1)
            chk(f"{n}: Favoriten stehen zuerst","favoriten" in (await pg.locator(".navgruppe .navkopf").first.inner_text()).lower())
            await pg.reload(); await pg.wait_for_selector(".navkopf"); await pg.wait_for_timeout(500)
            chk(f"{n}: Favorit bleibt nach Neuladen",await pg.locator(".navgruppe:has(.navkopf:has-text('Favoriten')) a[href='#kalender']").count()==1)
            await pg.add_script_tag(content=AXE)
            v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))"); chk(f"{n}: Menü Barrierefreiheit",not v,v[:3])
            await pg.screenshot(path=f"/var/tmp/pt/admin_desktop_{n}.png")
            await pg.locator(".navgruppe:has(.navkopf:has-text('Favoriten')) .sternknopf").first.click(); await pg.wait_for_timeout(800)
            chk(f"{n}: Stern entfernt den Favoriten wieder",await pg.locator(".navkopf:has-text('Favoriten')").count()==0)
            o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk(f"{n}: ohne seitliches Überlaufen",o<=0,o)
            chk(f"{n}: keine JavaScript-Fehler",not errs,errs)
            await ctx.close()
        # Handy: Favoriten verdoppeln die Kacheln nicht
        ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True,is_mobile=True,has_touch=True)
        pg=await ctx.new_page()
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",open("/var/tmp/pt/adminpw").read().strip()); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.evaluate("localStorage.setItem('mk-admin-favoriten','[\"kalender\"]')")
        await pg.goto(B+"/admin#meintag"); await pg.wait_for_selector(".tabbar"); await pg.click(".tabbar button"); await pg.wait_for_selector(".mehrblatt.kachel")
        chk("Handy: Kalender-Kachel nur einmal",await pg.locator(".mehrblatt a.nav[href='#kalender']").count()==1,await pg.locator(".mehrblatt a.nav[href='#kalender']").count())
        await ctx.close(); await br.close()
asyncio.run(main())
