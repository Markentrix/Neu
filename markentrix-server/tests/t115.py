"""Zurück zur Liste: Filter, Suche und Seite bleiben erhalten (Admin-Leads und Kunden)."""
import httpx, time, asyncio
from playwright.async_api import async_playwright
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); r=a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}); assert r.status_code==200
sfx=str(int(time.time())+1760)
for i in range(3): a.post("/api/admin/leads",json={"firma":f"Zurueck{sfx} {i}","telefon":f"0511 76{i}{sfx[-5:]}","ort":"Celle","plz":"29221","quelle":"messe"})
async def lauf():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1280,"height":900})
        await ctx.add_cookies([{"name":"mk_session","value":a.cookies.get("mk_session"),"url":B}])
        pg=await ctx.new_page(); fehler=[]; pg.on("pageerror",lambda e: fehler.append(str(e)))
        liste=f"#leads?quelle=messe&q=Zurueck{sfx}"
        await pg.goto(B+"/admin"+liste); await pg.wait_for_selector(f"text=Zurueck{sfx} 0",timeout=10000)
        await pg.click(f"a:has-text('Zurueck{sfx} 0')"); await pg.wait_for_selector("text=← Liste",timeout=10000)
        await pg.click("a:has-text('← Liste')"); await pg.wait_for_selector(f"text=Zurueck{sfx} 1",timeout=10000)
        chk("Zurück führt zur Liste mit Suche und Filter",pg.url.endswith(liste),pg.url)
        chk("Filter sind noch gesetzt",await pg.input_value("select[name=f_quelle]")=="messe")
        await pg.goto(B+"/admin#leads"); await pg.wait_for_selector("text=Leads",timeout=10000)
        await pg.goto(B+"/admin#leads?quelle=messe"); await pg.wait_for_selector("text=Zurueck"+sfx,timeout=10000)
        await pg.click(f"a:has-text('Zurueck{sfx} 2')"); await pg.wait_for_selector("text=← Liste",timeout=10000)
        await pg.click("a:has-text('← Liste')"); await pg.wait_for_selector("text=Zurueck"+sfx,timeout=10000)
        chk("Zweite Liste mit anderem Filter ebenfalls erhalten",pg.url.endswith("#leads?quelle=messe"),pg.url)
        chk("Keine JavaScript-Fehler",fehler==[],fehler)
        await br.close()
asyncio.run(lauf())
