"""Vertrieb: Schnell anlegen (Vorwahl-Ort, Dublette), Leitfaden-Blatt am Lead (Vertrieb und Admin), Tagesziel im Anruf-Modus und auf „Heute“."""
import asyncio, httpx, time, subprocess
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+5124)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Quinn Quick","email":f"quinn{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"quinn{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"QuinnPasswort123456"})
lid=a.post("/api/admin/leads",json={"firma":f"Ziel{sfx} GmbH","telefon":f"0511 66{sfx}","ort":"Celle","plz":"29221","email":f"ziel{sfx}@lead.de","vertriebspartner_id":pid}).json()["id"]
sql(f"update leads set temperatur='heiss' where id='{lid}'")
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"quinn{sfx}@v.de","password":"QuinnPasswort123456"}).status_code==200
v.put("/api/vertrieb/wochenziel",json={"anrufe":5}) if False else None
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(); ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True); pg=await ctx.new_page()
        errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e",f"quinn{sfx}@v.de"); await pg.fill("#p","QuinnPasswort123456"); await pg.click("#b"); await pg.wait_for_url("**/vertrieb*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        await pg.wait_for_selector(".tabbar, .side a.nav",state="attached")
        # ---- Vorwahl-Hilfen
        r=await pg.evaluate("import('/static/js/vorwahl.js').then(m=>[m.ortZurVorwahl('05141 123456'),m.ortZurVorwahl('+49 511 99'),m.ortZurVorwahl('0049 40 123'),m.ortZurVorwahl('01701234567'),m.nummerBereinigen('+49 (0)511 / 12-3'),JSON.stringify(m.ausText('Autohaus Müller\\nTel. 05141 12345'))])")
        chk("Vorwahl: Celle, Hannover, Hamburg, Handy ohne Ort",r[:4]==["Celle","Hannover","Hamburg",""],r)
        chk("Nummer bereinigen: +49 (0)511 → 0511…",r[4]=="0511123",r[4])
        chk("Aus Text: Telefon und Firma",'"telefon":"05141 12345"' in r[5] and "Autohaus Müller" in r[5],r[5])
        # ---- Schnell anlegen
        await pg.goto(B+"/vertrieb#leads"); await pg.wait_for_selector("button:has-text('Schnell anlegen')",timeout=8000)
        await pg.click("button:has-text('Schnell anlegen')"); await pg.wait_for_selector(".dlg input[type=tel]",timeout=4000)
        chk("Schnell anlegen: Telefonfeld mit Zifferntastatur",await pg.locator(".dlg input[type=tel]").get_attribute("inputmode")=="tel")
        nr=f"05141 77{sfx[-5:]}"
        await pg.fill(".dlg input[type=tel]",nr); await pg.wait_for_timeout(200)
        chk("Ort wird aus der Vorwahl vorgeschlagen",await pg.locator(".dlg input[aria-label=Ort]").input_value()=="Celle")
        await pg.click(".dlg button:has-text('Lead anlegen')"); await pg.wait_for_timeout(500)
        chk("Ohne Firma kommt ein Hinweis",await pg.locator(".dlg:has-text('Namen der Firma')").count()==1)
        await pg.fill(".dlg input[aria-label=Firma]",f"Schnell{sfx} Autohaus"); await pg.click(".dlg button:has-text('Lead anlegen')"); await pg.wait_for_url("**#lead/*",timeout=8000)
        chk("Lead ist angelegt und geöffnet",sql(f"select count(*) from leads where firma='Schnell{sfx} Autohaus' and ort='Celle' and vertriebspartner_id='{pid}'")=="1")
        await pg.goto(B+"/vertrieb#leads"); await pg.click("button:has-text('Schnell anlegen')"); await pg.fill(".dlg input[type=tel]",nr); await pg.fill(".dlg input[aria-label=Firma]",f"Schnell{sfx} Autohaus"); await pg.click(".dlg button:has-text('Lead anlegen')"); await pg.wait_for_timeout(800)
        chk("Dublette wird gemeldet, nichts doppelt angelegt",await pg.locator(".dlg .msg").count()>=1 and sql(f"select count(*) from leads where firma='Schnell{sfx} Autohaus'")=="1",await pg.locator(".dlg").inner_text())
        await pg.keyboard.press("Escape")
        # ---- Leitfaden-Blatt
        await pg.goto(B+f"/vertrieb#lead/{lid}"); await pg.wait_for_selector("button:has-text('Leitfaden')",timeout=8000)
        await pg.click("button:has-text('Leitfaden')"); await pg.wait_for_selector(".dlg:has-text('Merkhilfe')",timeout=4000)
        chk("Leitfaden öffnet als Blatt mit Gesprächsleitfaden und Merkhilfe",await pg.locator(".dlg:has-text('Gesprächsleitfaden')").count()==1)
        chk("Link zum allgemeinen Leitfaden vorhanden",await pg.locator(".dlg a[href='#leitfaden']").count()==1)
        await pg.keyboard.press("Escape")
        # ---- Tagesziel
        await pg.goto(B+"/vertrieb#heute"); await pg.wait_for_selector("text=Tagesziel",timeout=8000)
        chk("Heute zeigt das Tagesziel",await pg.locator("[aria-label=Tagesziel]").count()==1 and await pg.locator("text=Wochenziel geteilt durch 5").count()==1)
        z=v.get("/api/vertrieb/zahlen").json(); ziel=max(1,-(-z["wochenziel"]//5))
        await pg.evaluate("sessionStorage.setItem('mk-anrufmodus',JSON.stringify({modus:'heiss',filter:'',erledigt:[],start:Date.now()}))")
        await pg.evaluate("localStorage.removeItem('mk-ziel-mk-anrufmodus')")
        await pg.goto(B+f"/vertrieb#lead/{lid}"); await pg.wait_for_selector(f"text=Heute 0 von {ziel} Anrufen",timeout=8000); chk("Anruf-Modus zeigt „Heute 0 von Ziel“",True)
        chk("Noch keine Feier vor dem Ziel",await pg.locator(".toast:has-text('Tagesziel erreicht')").count()==0)
        for i in range(ziel): v.post(f"/api/vertrieb/leads/{lid}/kontakt",json={"ergebnis":"anruf_nicht_erreicht"})
        await pg.reload(); await pg.wait_for_selector(".toast:has-text('Tagesziel erreicht')",timeout=8000); chk("Ziel erreicht: Meldung erscheint",True)
        await pg.reload(); await pg.wait_for_timeout(2500); chk("Meldung kommt nur einmal pro Tag",await pg.locator(".toast:has-text('Tagesziel erreicht')").count()==0)
        chk("Keine JS-Fehler",not errs,errs); await ctx.close()
        # ---- Admin: Leitfaden-Blatt
        ctx,pg=None,None
        ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True); pg=await ctx.new_page()
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",ADMPW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+f"/admin#lead/{lid}"); await pg.wait_for_selector("button:has-text('Leitfaden')",timeout=8000)
        await pg.click("button:has-text('Leitfaden')"); await pg.wait_for_selector(".dlg:has-text('Merkhilfe')",timeout=4000); chk("Admin: Leitfaden-Blatt öffnet",True)
        await br.close()
asyncio.run(main())
