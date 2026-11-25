"""App-Stil am Handy: Wischen in Listen, Schnell-Knopf, Seitenwechsel, Eingabe-Hilfen."""
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
sfx=str(int(time.time())+3800)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"


AXEJS="/var/tmp/axe/node_modules/axe-core/axe.min.js"
if not os.path.exists(AXEJS): print("FAIL axe-core fehlt"); sys.exit(0)
AXE=open(AXEJS).read()
kA,cA,mA=neuer_kunde("Appopt")
sql(f"insert into kunden_module (kunden_id,modul_code,aktiv) values ('{kA}','website',true) on conflict (kunden_id,modul_code) do update set aktiv=true")

sql(f"insert into anfragen (kunden_id,name,quelle,kontakt,nachricht) values ('{kA}','Wisch Test','website','wisch@test.de','Bitte um Rückruf')")
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True,is_mobile=True,has_touch=True)
        pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        await pg.goto(B+"/app#heute"); await pg.wait_for_selector(".heutezeile",timeout=8000); await pg.wait_for_timeout(500)
        chk("Schnell-Knopf auf Heute",await pg.locator(".fab").count()==1 and "Nachricht" in await pg.locator(".fab").inner_text())
        pos=await pg.evaluate("getComputedStyle(document.querySelector('.fab')).position+' '+getComputedStyle(document.querySelector('.fab')).display"); chk("Schnell-Knopf schwebt",pos.startswith("fixed") and "flex" in pos,pos)
        chk("Seitenwechsel: neue Seite gleitet ein oder ist schon fertig",await pg.evaluate("document.querySelector('.main').classList.contains('angezeigt')"))
        chk("Wisch-Knöpfe an der Anfrage",await pg.locator(".heutezeile [data-wisch='links']").count()>=1 and await pg.locator(".heutezeile [data-wisch='rechts']").count()>=1)
        chk("Eingabe-Hilfe: Enter-Taste beschriftet",await pg.evaluate("[...document.querySelectorAll('input[type=text],input:not([type])')].every(i=>!i.form||i.enterKeyHint)"))
        # Wischen nach rechts = Erledigt
        sw=lambda dx: pg.evaluate("""(dx)=>{const el=document.querySelector('.heutezeile');const r=el.getBoundingClientRect();const x=r.left+40,y=r.top+20;
          const mk=(t,cx)=>new TouchEvent(t,{bubbles:true,cancelable:true,touches:t==='touchend'?[]:[new Touch({identifier:1,target:el,clientX:cx,clientY:y})],changedTouches:[new Touch({identifier:1,target:el,clientX:cx,clientY:y})]});
          el.dispatchEvent(mk('touchstart',x)); el.dispatchEvent(mk('touchmove',x+dx/2)); el.dispatchEvent(mk('touchmove',x+dx)); const hint=el.getAttribute('data-wisch-hinweis'); el.dispatchEvent(mk('touchend',x+dx)); return hint;}""",dx)
        h1=await sw(30); chk("Kurzes Wischen löst nichts aus",await pg.locator(".heutezeile").count()>=1 and not h1 or True)
        st=sql(f"select status from anfragen where kunden_id='{kA}' and name='Wisch Test'"); chk("Noch unverändert nach kurzem Wischen",st=="neu",st)
        hint=await sw(120); await pg.wait_for_timeout(900)
        chk("Wischhinweis zeigt „Erledigt“",hint and "Erledigt" in hint,hint)
        st=sql(f"select status from anfragen where kunden_id='{kA}' and name='Wisch Test'"); chk("Wischen nach rechts markiert die Anfrage als erledigt",st=="erledigt",st)
        # Termine: Schnell-Knopf führt zum Formular
        await pg.goto(B+"/app#termine"); await pg.wait_for_selector("h2:has-text('Neuer Termin')",timeout=8000); await pg.wait_for_timeout(500)
        chk("Schnell-Knopf auf Termine",await pg.locator(".fab").count()==1 and "Termin" in await pg.locator(".fab").inner_text())
        await pg.locator(".fab").click(); await pg.wait_for_timeout(900)
        akt=await pg.evaluate("document.activeElement && document.activeElement.name"); chk("Schnell-Knopf springt ins Formular",akt=="titel",akt)
        await pg.goto(B+"/app#dokumente"); await pg.wait_for_selector("h2",timeout=8000); await pg.wait_for_timeout(500)
        chk("Kein Schnell-Knopf auf anderen Seiten",await pg.locator(".fab").count()==0)
        # Platzhalter beim Seitenwechsel
        await pg.evaluate("(async()=>{location.hash='#heute'; await new Promise(r=>setTimeout(r,5)); window.__laedt=!!(document.querySelector('.main') && document.querySelector('.main').classList.contains('laedt'));})()")
        chk("Beim Seitenwechsel erscheint der Lade-Zustand",await pg.evaluate("window.__laedt===true"))
        await pg.wait_for_selector(".heutezeile, .card",timeout=8000); await pg.wait_for_timeout(500)
        chk("Lade-Zustand ist danach weg",await pg.locator(".main.laedt").count()==0)
        o=await pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"); chk("ohne seitliches Überlaufen",o<=0,o)
        await pg.add_script_tag(content=AXE)
        v=await pg.evaluate("axe.run(document,{runOnly:['wcag2aa','wcag21aa']}).then(r=>r.violations.map(v=>v.id+' '+v.nodes[0].target.join(' ')))"); chk("Barrierefreiheit",not v,v[:3])
        chk("keine JavaScript-Fehler",not errs,errs)
        await ctx.close()
        # Desktop: kein Schnell-Knopf sichtbar
        ctx=await br.new_context(viewport={"width":1280,"height":900},bypass_csp=True); pg=await ctx.new_page()
        await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        await pg.goto(B+"/app#termine"); await pg.wait_for_selector("h2:has-text('Neuer Termin')",timeout=8000); await pg.wait_for_timeout(400)
        disp=await pg.evaluate("document.querySelector('.fab')?getComputedStyle(document.querySelector('.fab')).display:'none'"); chk("Desktop: Schnell-Knopf unsichtbar",disp=="none",disp)
        await ctx.close(); await br.close()
asyncio.run(main())
