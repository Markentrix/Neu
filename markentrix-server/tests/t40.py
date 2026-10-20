import asyncio, httpx, time, os, sys
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:400])
AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
a=httpx.Client(base_url=B,headers=H); PW=open("/var/tmp/pt/adminpw").read().strip(); a.post("/api/login",json={"email":"chef@test.de","password":PW})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
sfx=str(int(time.time())+11)
kid=a.post("/api/admin/kunden",json={"firma":"AVV Dialog "+sfx,"ansprechpartner":"Dora Dialog","email":f"dora{sfx}@av.de","strasse":"Weg 2","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json()["id"]
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1280,"height":1000},bypass_csp=True); pg=await ctx.new_page()
        errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+"/admin#kunde/"+kid); await pg.wait_for_selector("text=Neuen AVV erstellen",timeout=8000)
        await pg.click("text=Neuen AVV erstellen"); await pg.wait_for_selector(".dlg")
        chk("Dialog: 14 Module, Portal fest angekreuzt",await pg.locator(".dlg input[type=checkbox]").count()==14 and await pg.locator(".dlg input[type=checkbox]").first.is_disabled())
        chk("Dialog: Weisungsberechtigter vorbelegt",await pg.locator(".dlg input[type=email]").input_value()==f"dora{sfx}@av.de")
        await pg.locator(".dlg label:has-text('Domainverwaltung (INWX)') input").check()
        await pg.click(".dlg >> text=Entwurf erstellen"); await pg.wait_for_selector(".dlg .msg, .dlg .err, .dlg [role=alert]",timeout=4000)
        chk("Dialog: Domain-Pflichtangabe wird verlangt",await pg.locator(".dlg").count()==1 and "Domain" in await pg.locator(".dlg").inner_text())
        await pg.locator(".dlg label:has-text('Domain(s)') input").fill(f"dora{sfx}.de")
        await pg.add_script_tag(content=open(AXEJS).read())
        ax=await pg.evaluate("axe.run(document.querySelector('.dlg'),{runOnly:['wcag2a','wcag2aa','best-practice']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))")
        chk("Dialog: barrierefrei",not ax,ax)
        await pg.click(".dlg >> text=Entwurf erstellen"); await pg.wait_for_selector("text=Module & Angaben prüfen",timeout=8000)
        await pg.click("text=Module & Angaben prüfen"); await pg.wait_for_selector(".dlg .msg ul li")
        chk("Prüfdialog nennt fehlendes Hauptvertrags-Datum",'Hauptvertrag' in await pg.locator(".dlg .msg").inner_text())
        await pg.locator(".dlg input[type=date]").fill("2026-10-01"); await pg.click(".dlg >> text=Speichern"); await pg.wait_for_selector("text=Module & Angaben prüfen",timeout=8000)
        av=a.get(f"/api/admin/kunden/{kid}/avv").json()["liste"]; p=a.get(f"/api/admin/avv/{av[0]['id']}/pruefen").json()
        chk("Entwurf gespeichert, nichts mehr offen",p["offen"]==[] and "domain" in p["anlage"]["module"] and p["anlage"]["domain"]==f"dora{sfx}.de",p)
        chk("keine JavaScript-Fehler",not errs,errs)
        await br.close()
asyncio.run(main())
