"""App-Gefühl: Zurück-Taste schließt Fenster, Aktualisieren, Lang drücken, Aktionen ohne Warten, Bequem, Foto/Sprache, Teilen, später erinnern, gemerkte Seite."""
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



kA,cA,mA=neuer_kunde("Appgef")
kB=a.post("/api/admin/kunden",json={"firma":f"Zielkunde {sfx}","ansprechpartner":"Z Z","email":f"ziel{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json()["id"]
INIT_SR="""window.__sr=[];window.webkitSpeechRecognition=function(){window.__sr.push(this);this.start=function(){this.l=1};this.stop=function(){this.l=0;if(this.onend)this.onend()}};window.SpeechRecognition=window.webkitSpeechRecognition;"""
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        ctx=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True,is_mobile=True,has_touch=True,service_workers="allow")
        await ctx.add_init_script(INIT_SR)
        pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e",mA); await pg.fill("#p","InhaberPasswort1"); await pg.click("#b"); await pg.wait_for_url("**/app*")
        await pg.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})")
        await pg.goto(B+"/app#heute"); await pg.wait_for_selector(".main",timeout=8000); await pg.wait_for_timeout(600)
        # 1) Zurück-Taste schließt das Fenster, nicht die Seite
        n0=await pg.evaluate("history.length")
        await pg.locator(".tabbar button").last.click(); await pg.wait_for_selector(".dlg",timeout=4000)
        chk("Fenster legt einen Verlaufseintrag an",await pg.evaluate("history.length")==n0+1)
        await pg.go_back(); await pg.wait_for_timeout(500)
        chk("Zurück schließt das Fenster",await pg.locator(".dlg").count()==0)
        chk("… und bleibt auf der Seite",pg.url.endswith("/app#heute"),pg.url)
        await pg.locator(".tabbar button").last.click(); await pg.wait_for_selector(".dlg",timeout=4000)
        await pg.locator(".dlg [aria-label=Schließen]").click(); await pg.wait_for_timeout(500)
        chk("Schließen per Knopf: Fenster weg und Verlauf wieder wie vorher",await pg.locator(".dlg").count()==0 and await pg.evaluate("history.length")>=n0 and pg.url.endswith("/app#heute"),pg.url)
        await pg.go_back(); await pg.wait_for_timeout(600)
        await pg.goto(B+"/app#heute"); await pg.wait_for_selector(".main",timeout=8000); await pg.wait_for_timeout(500)
        # Fenster, aus dem man per Link weitergeht: ein Zurück führt wieder zur Ausgangsseite
        await pg.locator(".tabbar button").last.click(); await pg.wait_for_selector(".dlg",timeout=4000)
        await pg.locator(".dlg a[href='#kalender'], .dlg a[href='#termine'], .dlg a[href='#dokumente']").first.click(); await pg.wait_for_timeout(700)
        chk("Link im Fenster schließt es",await pg.locator(".dlg").count()==0)
        await pg.go_back(); await pg.wait_for_timeout(800)
        chk("Zurück nach Link im Fenster landet wieder auf der Ausgangsseite (kein toter Zwischenstand)",pg.url.endswith("#heute"),pg.url)
        # 2) Runterziehen aktualisiert ohne Neuladen
        await pg.evaluate("window.__marke=1")
        await pg.evaluate("""()=>{const el=document.body;const mk=(t,y)=>new TouchEvent(t,{bubbles:true,cancelable:true,touches:t==='touchend'?[]:[new Touch({identifier:1,target:el,clientX:150,clientY:y})],changedTouches:[new Touch({identifier:1,target:el,clientX:150,clientY:y})]});
          el.dispatchEvent(mk('touchstart',60)); el.dispatchEvent(mk('touchmove',120)); el.dispatchEvent(mk('touchmove',220)); el.dispatchEvent(mk('touchend',220));}""")
        await pg.wait_for_selector(".aktualisiert",timeout=3000)
        chk("Runterziehen zeigt „Aktualisiert“ und lädt die Seite nicht komplett neu",await pg.evaluate("window.__marke")==1)
        await pg.wait_for_timeout(1500); await pg.wait_for_selector(".main:not(.laedt)",timeout=6000)
        # 3) Lang drücken: Aktionsmenü
        await pg.evaluate("""()=>{window.__k=[];const z=document.createElement('div');z.className='heutezeile';z.id='lz';z.innerHTML='<div class="pt"><b>Langtest</b></div>';
          for(const t of ['Eins','Zwei']){const b=document.createElement('button');b.className='btn small';b.textContent=t;b.onclick=()=>window.__k.push(t);z.append(b);} document.querySelector('.main').prepend(z);}""")
        await pg.evaluate("""()=>{const el=document.querySelector('#lz b');const r=el.getBoundingClientRect();window.__t=new Touch({identifier:7,target:el,clientX:r.left+5,clientY:r.top+5});
          el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,cancelable:true,touches:[window.__t],changedTouches:[window.__t]}));}""")
        await pg.wait_for_selector(".langmenue",timeout=3000)
        chk("Lang drücken öffnet das Aktionsmenü mit beiden Knöpfen",await pg.locator(".langmenue button").count()==2 and "Langtest" in await pg.locator(".dlgkopf h2").inner_text())
        await pg.evaluate("document.querySelector('#lz b').dispatchEvent(new TouchEvent('touchend',{bubbles:true,changedTouches:[window.__t]}))")
        await pg.locator(".langmenue button", has_text="Zwei").click(); await pg.wait_for_timeout(500)
        chk("Menüpunkt löst den echten Knopf aus",await pg.evaluate("window.__k")==["Zwei"],await pg.evaluate("window.__k"))
        # 7) Aktion ohne Warten: sofort weg, bei Fehler wieder da
        await pg.evaluate("""()=>{const z=document.createElement('div');z.className='heutezeile';z.id='fz';z.innerHTML='<b>Fehlertest</b>';const b=document.createElement('button');b.className='btn small';b.setAttribute('data-sofort','1');b.textContent='Erledigt';
          b.onclick=()=>setTimeout(()=>{const m=document.createElement('div');m.className='msg err';m.textContent='Server sagt nein';document.querySelector('.main').append(m);},500);z.append(b);document.querySelector('.main').prepend(z);}""")
        await pg.locator("#fz button").click(); await pg.wait_for_timeout(120)
        chk("Eintrag verschwindet sofort",await pg.evaluate("document.querySelector('#fz').classList.contains('weg')"))
        await pg.wait_for_timeout(1000)
        chk("Bei Fehler kommt der Eintrag zurück",await pg.evaluate("!document.querySelector('#fz').classList.contains('weg')") and await pg.locator(".toast", has_text="Erneut versuchen").count()==1)
        await pg.evaluate("""()=>{const z=document.createElement('div');z.className='heutezeile';z.id='oz';z.innerHTML='<b>Okaytest</b>';const b=document.createElement('button');b.className='btn small';b.setAttribute('data-sofort','1');b.textContent='Erledigt';
          b.onclick=()=>setTimeout(()=>z.remove(),300);z.append(b);document.querySelector('.main').prepend(z);}""")
        await pg.locator("#oz button").click(); await pg.wait_for_timeout(1200)
        chk("Bei Erfolg bleibt der Eintrag weg und es kommt keine Fehlermeldung",await pg.locator("#oz").count()==0 and await pg.locator(".toast", has_text="nicht geklappt").count()==1)
        # 10) Foto aufnehmen an Dateifeldern, 11) Sprache nur auf Wunsch
        await pg.evaluate("""()=>{const i=document.createElement('input');i.type='file';i.id='ff';i.accept='image/*,.pdf';document.querySelector('.main').append(i);const t=document.createElement('textarea');t.id='tt';document.querySelector('.main').append(t);}""")
        await pg.wait_for_timeout(600)
        chk("Dateifeld bekommt „Foto aufnehmen“",await pg.locator("#ff + .fotoknopf").count()==1)
        chk("Sprache standardmäßig aus: kein Mikrofon-Knopf",await pg.locator("#tt + .mikroknopf").count()==0)
        await pg.locator(".tabbar button").last.click(); await pg.wait_for_selector(".dlg",timeout=4000)
        chk("Menü hat Schalter „Bequem“ und „Sprache“",await pg.locator(".dichteknopf").count()==1 and await pg.locator(".spracheknopf").count()==1)
        await pg.locator(".spracheknopf").click(); await pg.wait_for_selector("text=Browser die Aufnahme",timeout=3000)
        chk("Sprache einschalten erklärt die Datenweitergabe",await pg.locator("text=Markentrix speichert keine Aufnahmen").count()==1)
        await pg.locator("button:has-text('Einschalten')").click(); await pg.wait_for_timeout(300)
        chk("Danach ist Sprache an",await pg.evaluate("localStorage.getItem('mk-sprache')")=="1")
        await pg.locator(".dichteknopf").click(); await pg.wait_for_timeout(200)
        chk("Bequem schaltet größere Darstellung ein",await pg.evaluate("document.documentElement.classList.contains('bequem') && localStorage.getItem('mk-dichte')")=="bequem")
        await pg.go_back(); await pg.wait_for_timeout(500)
        await pg.wait_for_selector("#tt + .mikroknopf",timeout=4000)
        await pg.locator("#tt + .mikroknopf").click(); await pg.wait_for_timeout(200)
        await pg.evaluate("""()=>{const r=window.__sr[0];r.onresult({resultIndex:0,results:[Object.assign([{transcript:'Hallo Welt'}],{isFinal:true})]});}""")
        chk("Spracheingabe schreibt den Text ins Feld",await pg.evaluate("document.querySelector('#tt').value")=="Hallo Welt",await pg.evaluate("document.querySelector('#tt').value"))
        await pg.reload(); await pg.wait_for_selector(".main",timeout=8000)
        chk("Bequem bleibt nach dem Neuladen",await pg.evaluate("document.documentElement.classList.contains('bequem')"))
        # Bequem aus, damit die übrigen Prüfungen die normale Größe sehen
        await pg.evaluate("localStorage.setItem('mk-dichte','');localStorage.setItem('mk-sprache','0')")
        # 9) Teilen: Service Worker nimmt geteilte Dateien an, Seite /teilen legt sie als Nachricht ab
        await pg.evaluate("navigator.serviceWorker.ready.then(()=>1)"); await pg.reload(); await pg.wait_for_timeout(800)
        kontrolliert=await pg.evaluate("!!navigator.serviceWorker.controller"); chk("Service Worker ist aktiv",kontrolliert)
        r=await pg.evaluate("""async()=>{const f=new FormData();f.append('title','Foto vom Kunden');f.append('text','Bitte ansehen');f.append('dateien',new File([new Uint8Array([137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82,0,0,0,1,0,0,0,1,8,6,0,0,0,31,21,196,137,0,0,0,10,73,68,65,84,120,156,99,0,1,0,0,5,0,1,13,10,45,180,0,0,0,0,73,69,78,68,174,66,96,130])],'foto.png',{type:'image/png'}));
          const x=await fetch('/teilen',{method:'POST',body:f});return x.status+' '+x.url;}""")
        chk("Teilen: POST wird angenommen und zur Teilen-Seite geleitet",r.startswith("200") and "/teilen?neu=1" in r,r)
        await pg.goto(B+"/teilen?neu=1"); await pg.wait_for_selector("h1:has-text('Teilen')",timeout=8000)
        chk("Teilen-Seite zeigt Text und Datei",await pg.locator("text=Bitte ansehen").count()>=1 and await pg.locator("text=foto.png").count()==1)
        await pg.locator("button:has-text('An Markentrix senden')").click(); await pg.wait_for_url("**/app#nachrichten/*",timeout=8000)
        tid=pg.url.split("/")[-1]
        t=cA.get(f"/api/kunde/tickets/{tid}").json(); chk("Teilen: Nachricht mit Anhang beim Team angekommen",t.get("betreff","").startswith("Foto vom Kunden") and len(t.get("dateien",[]))==1,t)
        chk("Zwischenspeicher nach dem Senden leer",await pg.evaluate("caches.has('mk-teilen').then(x=>!x)"))
        chk("Manifest kennt das Teilen-Ziel",'"share_target"' in httpx.get(B+"/manifest.webmanifest?r=kunde").text)
        await pg.goto(B+"/teilen"); await pg.wait_for_selector("h2:has-text('Nichts angekommen')",timeout=6000); chk("Leere Teilen-Seite zeigt Hinweis",True)
        # Teilen als Admin: Datei bei einem Kunden ablegen (intern)
        ctx3=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True,is_mobile=True,has_touch=True)
        p3=await ctx3.new_page(); await p3.goto(B+"/"); await p3.fill("#e","chef@test.de"); await p3.fill("#p",open("/var/tmp/pt/adminpw").read().strip()); await p3.click("#b"); await p3.wait_for_url("**/admin*")
        await p3.evaluate("""async()=>{const c=await caches.open('mk-teilen');await c.put('/teilen-text',new Response(JSON.stringify({text:'Kurznotiz',zeit:1})));await c.put('/teilen-datei/0',new Response(new Blob(['Hallo'],{type:'text/plain'}),{headers:{'Content-Type':'text/plain','X-Name':'notiz.txt'}}));}""")
        await p3.goto(B+"/teilen"); await p3.wait_for_selector("input[type=search]",timeout=8000)
        await p3.fill("input[type=search]","Zielkunde"); await p3.locator("button:has-text('Zielkunde')").first.click(); await p3.wait_for_url("**/admin#kunde/*",timeout=8000)
        u=a.get(f"/api/admin/kunden/{kB}/unterlagen").json()["dateien"]; chk("Admin: geteilte Datei liegt intern beim Kunden",any(x["name"]=="notiz.txt" and not x.get("sichtbar_kunde",True) for x in u),u)
        # 12) Gemerkte Seite in der installierten App
        ctx2=await br.new_context(viewport={"width":390,"height":800},bypass_csp=True,is_mobile=True,has_touch=True)
        await ctx2.add_init_script("const q=window.matchMedia.bind(window);window.matchMedia=(s)=>{const m=q(s);return /standalone/.test(s)?{matches:true,media:s,addEventListener(){},removeEventListener(){},addListener(){},removeListener(){}}:m;};if(location.pathname==='/app'&&!sessionStorage.getItem('gesetzt')){sessionStorage.setItem('gesetzt','1');localStorage.setItem('mk-ort:/app',JSON.stringify({hash:'termine',zeit:Date.now()}));}")
        p2=await ctx2.new_page(); await p2.goto(B+"/"); await p2.fill("#e",mA); await p2.fill("#p","InhaberPasswort1"); await p2.click("#b"); await p2.wait_for_url("**/app*")
        await p2.wait_for_timeout(1500)
        chk("Installierte App öffnet dort, wo man aufgehört hat",p2.url.endswith("#termine"),p2.url)
        chk("ohne JavaScript-Fehler",not errs,errs[:2])
        await br.close()
asyncio.run(main())

# 11) „In 1 Stunde erinnern“ aus der Push-Meldung
r=cA.post("/api/push/spaeter",json={"titel":"Neue Anfrage","text":"Maxi","url":"/app#anfragen","minuten":60}); chk("Später erinnern: angenommen",r.status_code==200,r.text)
n=sql("select count(*) from push_spaeter"); chk("Erinnerung ist vorgemerkt",n=="1",n)
chk("Ungültiges Ziel wird abgelehnt",cA.post("/api/push/spaeter",json={"titel":"x","url":"http://boese.de"}).status_code==422)
sql("update push_spaeter set faellig_am=now()-interval '1 minute'")
sys.path.insert(0,os.environ["PYTHONPATH"]); from app import jobs, db; db.open_pool(); jobs.push_spaeter_senden({})
chk("Fällige Erinnerung wird abgeholt und gelöscht",sql("select count(*) from push_spaeter")=="0")
chk("Erinnerung steht in der Glocke",int(sql("select count(*) from benachrichtigungen where titel like 'Erinnerung: Neue Anfrage%'"))>=1)
