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
sfx=str(int(time.time())+225)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import io, json, os, sys, datetime
from pypdf import PdfReader
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, jobs
db.open_pool()
kA,cA,mA=neuer_kunde("Ov"); kB,cB,mB=neuer_kunde("Ow")
ADM=sql("select email from benutzer where rolle='admin' and aktiv order by erstellt_am limit 1")
p=a.post("/api/admin/vertrieb/partner",json={"name":"Nora Neu","email":f"nora{sfx}@v.de"}).json(); pid=p["id"]
l=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"nora{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":l.split("token=")[1],"password":"NoraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); v.post("/api/login",json={"email":f"nora{sfx}@v.de","password":"NoraPasswort123456"})
def pdf_in_mail(adr,t):
    for m in reversed(mail_an(adr,t)):
        for part in m.walk():
            if part.get_content_type()=="application/pdf": return part.get_payload(decode=True)
def werte(b): return {k:x.get("/V") for k,x in PdfReader(io.BytesIO(b)).get_fields().items()}
an=lambda x: x not in (None,"/Off","")
heute=datetime.date.today().isoformat()
# ---- Referenzvertrag online bestätigen (Kunde)
r=a.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={"projekt":"Website www.ov.de"}); zid=r.json()["id"]
li=cA.get("/api/kunde/vertraege").json(); chk("Kunde sieht den offenen Referenzvertrag",len(li)==1 and li[0]["offen"] and li[0]["id"]==zid,li)
chk("Anderer Kunde sieht nichts",cB.get("/api/kunde/vertraege").json()==[])
chk("Anderer Kunde: Vorlage 404",cB.get(f"/api/kunde/vertraege/{zid}/vorlage.pdf").status_code==404)
chk("Eigene Vorlage lesbar",cA.get(f"/api/kunde/vertraege/{zid}/vorlage.pdf").content.startswith(b"%PDF"))
chk("Vertriebler hat hier keinen Zutritt",v.get("/api/kunde/vertraege").status_code in (401,403))
ang={"elemente":{"name":{"an":True,"text":"Ov GmbH"},"logo":{"an":True,"text":""},"zitat":{"an":True,"text":"Super Arbeit!"},"xxx":{"an":True,"text":"böse"}},"kanaele":["web","social","quatsch"],"personen_zeigen":False,"einschraenkungen":"keine Fotos von Kindern"}
bst=lambda c,i,**kw: c.post(f"/api/kunde/vertraege/{i}/bestaetigen",json={"name":"Tina Test","ort":"Celle","akzeptiert":True,"angaben":ang,**kw})
chk("Ohne Haken bei „gelesen“ abgelehnt",bst(cA,zid,akzeptiert=False).status_code==400)
chk("Zu kurzer Name abgelehnt",bst(cA,zid,name="T").status_code==422)
chk("Ohne Auswahl abgelehnt",bst(cA,zid,angaben={}).status_code==400)
chk("Element ohne Kanal abgelehnt",bst(cA,zid,angaben={"elemente":{"name":{"an":True}},"kanaele":[]}).status_code==400)
chk("Fremder Kunde kann nicht bestätigen",bst(cB,zid).status_code==404)
r=bst(cA,zid); chk("Referenzvertrag online bestätigt",r.status_code==200,r.text)
chk("Zweites Bestätigen nicht mehr möglich",bst(cA,zid).status_code==404)
b=pdf_in_mail(mA,"Kopie"); chk("Kopie mit PDF per Mail",b is not None)
w=werte(b); chk("Haken: Name, Logo, Zitat; nicht Abbildungen",an(w["b_name_ck"]) and an(w["b_logo_ck"]) and an(w["b_zitat_ck"]) and not an(w["b_abb_ck"]),w)
chk("Texte übernommen, Unbekanntes ignoriert",w["b_name"]=="Ov GmbH" and w["b_zitat"]=="Super Arbeit!" and w["e_text"]=="keine Fotos von Kindern")
chk("Kanäle: Website und Social, nicht Print",an(w["c_web_ck"]) and an(w["c_social_ck"]) and not an(w["c_print_ck"]))
chk("Personen nicht freigegeben",not an(w["d_zeigen_ck"]))
chk("Unterschriftsfelder",w["sig_k_name"]=="Tina Test" and "Celle" in w["sig_k_ortdatum"] and "elektronisch" in w["sig_k_ortdatum"])
rd=PdfReader(io.BytesIO(b)); hs=sql(f"select online_hash from vertragsdokumente where id='{zid}'")
chk("Protokollseite angehängt (8 Seiten) mit Name und Prüfsumme",len(rd.pages)==8 and "Elektronische Bestätigung" in rd.pages[-1].extract_text() and hs in rd.pages[-1].extract_text().replace("\n","") and len(hs)==64,hs)
chk("Datenbank: Datum, Name, Konto",sql(f"select unterschrieben_am||'|'||online_name||'|'||online_email from vertragsdokumente where id='{zid}'")==f"{heute}|Tina Test|{mA}")
chk("Team-Mail über die Bestätigung",len(mail_an(ADM,"Referenzvertrag bestätigt"))>=1)
chk("Mail ohne KI-Namen",all("Claude" not in text(m) for m in mail_an(mA,"Kopie")))
chk("Audit",int(sql("select count(*) from audit_log where aktion='vertrag_online_bestaetigt'"))>=1)
d=cA.get(f"/api/kunde/vertraege/{zid}/datei"); chk("Kunde kann die bestätigte Datei ansehen",d.status_code==200 and d.content.startswith(b"%PDF") and d.headers.get("x-content-type-options")=="nosniff")
chk("Anderer Kunde nicht",cB.get(f"/api/kunde/vertraege/{zid}/datei").status_code==404)
li=cA.get("/api/kunde/vertraege").json(); chk("Liste: nicht mehr offen, mit Antworten",not li[0]["offen"] and "web" in li[0]["antworten"]["kanaele"] and "xxx" not in li[0]["antworten"]["elemente"],li)
chk("Menü-Zähler im Portal",cA.get("/api/kunde/start").json()["badges"]["vertraege_da"]==1 and cA.get("/api/kunde/start").json()["badges"]["vertraege"]==0)
# ---- Referenzliste und Widerruf
rl=a.get("/api/admin/vertragsdokumente/referenzen").json(); z=[x for x in rl["aktiv"] if x["id"]==zid]
chk("Referenzliste zeigt die Freigaben",len(z)==1 and {e["name"] for e in z[0]["elemente"]}>={"Name und Firma","Kundenstimme (Zitat)"} and "Website von Markentrix" in z[0]["kanaele"] and z[0]["einschraenkungen"]=="keine Fotos von Kindern" and z[0]["strukturiert"],rl)
chk("Referenzliste nur für Admins",cA.get("/api/admin/vertragsdokumente/referenzen").status_code==403 and v.get("/api/admin/vertragsdokumente/referenzen").status_code==403)
chk("Fremder Kunde kann nicht widerrufen",cB.post(f"/api/kunde/vertraege/{zid}/widerrufen",json={}).status_code==404)
r=cA.post(f"/api/kunde/vertraege/{zid}/widerrufen",json={"hinweis":"Wir haben das Logo gewechselt"}); chk("Kunde widerruft",r.status_code==200,r.text)
chk("Zweiter Widerruf: 404",cA.post(f"/api/kunde/vertraege/{zid}/widerrufen",json={}).status_code==404)
rl=a.get("/api/admin/vertragsdokumente/referenzen").json(); chk("Liste: bei „widerrufen“",[x["id"] for x in rl["widerrufen"]]==[zid] and not [x for x in rl["aktiv"] if x["id"]==zid])
mw=mail_an(ADM,"Referenz widerrufen"); chk("Team-Mail mit Frist und Hinweis",len(mw)>=1 and "7 Tagen" in text(mw[-1]) and "Logo gewechselt" in text(mw[-1]))
chk("Admin nimmt irrtümlichen Widerruf zurück",a.post(f"/api/admin/vertragsdokumente/{zid}/widerruf",json={"widerrufen":False}).status_code==200 and not a.get("/api/admin/vertragsdokumente/referenzen").json()["widerrufen"])
chk("Admin vermerkt Widerruf (z. B. aus Mail)",a.post(f"/api/admin/vertragsdokumente/{zid}/widerruf",json={}).status_code==200 and len(a.get("/api/admin/vertragsdokumente/referenzen").json()["widerrufen"])==1)
chk("Widerruf-Route nur Admin",cA.post(f"/api/admin/vertragsdokumente/{zid}/widerruf",json={}).status_code==403 and a.post("/api/admin/vertragsdokumente/xyz/widerruf",json={}).status_code==404)
# ---- Erinnerungen
r=a.post(f"/api/admin/kunden/{kB}/referenzvertrag",json={"projekt":"Website www.ow.de"}); zb=r.json()["id"]
jobs.vertrag_erinnern({}); chk("Frisch gesendet: noch keine Erinnerung",sql(f"select erinnerungen from vertragsdokumente where id='{zb}'")=="0")
sql(f"update vertragsdokumente set gesendet_am=now()-interval '8 days' where id='{zb}'"); jobs.vertrag_erinnern({})
chk("Nach 7 Tagen: 1. Erinnerung",sql(f"select erinnerungen from vertragsdokumente where id='{zb}'")=="1")
me=mail_an(mB,"Erinnerung"); chk("Erinnerung an den Kunden: freiwillig, Link, kein KI-Name",len(me)==1 and "freiwillig" in text(me[0]) and "/app#vertraege" in text(me[0]) and "Claude" not in text(me[0]))
chk("Sammelmail an das Team",len(mail_an(ADM,"Erinnerungen verschickt"))>=1)
jobs.vertrag_erinnern({}); chk("Am selben Tag keine zweite",sql(f"select erinnerungen from vertragsdokumente where id='{zb}'")=="1")
sql(f"update vertragsdokumente set erinnert_am=now()-interval '8 days' where id='{zb}'"); jobs.vertrag_erinnern({})
chk("Nach 14 Tagen: 2. Erinnerung",sql(f"select erinnerungen from vertragsdokumente where id='{zb}'")=="2")
sql(f"update vertragsdokumente set erinnert_am=now()-interval '8 days' where id='{zb}'"); jobs.vertrag_erinnern({})
chk("Danach nie wieder (höchstens zweimal)",sql(f"select erinnerungen from vertragsdokumente where id='{zb}'")=="2" and len(mail_an(mB,"Erinnerung"))==2)
chk("Bestätigte Verträge werden nie erinnert",sql(f"select erinnerungen from vertragsdokumente where id='{zid}'")=="0")
# ---- Handelsvertretervertrag online (Vertriebler)
chk("Vor dem Versand: kein Vertrag sichtbar",v.get("/api/vertrieb/vertrag").json()["dokumente"]==[])
r=a.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={}); hid=r.json()["id"]
d=v.get("/api/vertrieb/vertrag").json(); chk("Vertriebler sieht den offenen Vertrag",len(d["dokumente"])==1 and d["dokumente"][0]["offen"] and d["name"]=="Nora Neu",d)
chk("Kunde hat hier keinen Zutritt",cA.get("/api/vertrieb/vertrag").status_code in (401,403) and cA.get(f"/api/vertrieb/vertrag/{hid}/vorlage.pdf").status_code in (401,403))
chk("Vorlage lesbar",v.get(f"/api/vertrieb/vertrag/{hid}/vorlage.pdf").content.startswith(b"%PDF"))
hang={"rechtsform":"Einzelunternehmen","strasse":"Str 2","ort_anschrift":"30159 Hannover","steuer":"99/999","steuer_nr":"99/999","beauftragung":"neben","haken":{"gewerbe":True,"weisungsfrei":True,"nebenberuf":True},"janein":{"hilfspersonen":"nein","einziger_auftraggeber":"nein"}}
hb=lambda **kw: v.post(f"/api/vertrieb/vertrag/{hid}/bestaetigen",json={"name":"Nora Neu","ort":"Hannover","akzeptiert":True,"angaben":hang,**kw})
chk("Ohne Haken abgelehnt",hb(akzeptiert=False).status_code==400)
chk("Ohne Haupt-/Nebenberuf abgelehnt",hb(angaben={**hang,"beauftragung":""}).status_code==400)
chk("Ohne Anschrift abgelehnt",hb(angaben={**hang,"strasse":""}).status_code==400)
r=hb(); chk("Handelsvertretervertrag online bestätigt",r.status_code==200,r.text)
chk("Nicht noch einmal",hb().status_code==404)
b=pdf_in_mail(f"nora{sfx}@v.de","Kopie"); w=werte(b)
chk("Angaben im PDF",w["pt_strasse"]=="Str 2" and w["pt_ort"]=="30159 Hannover" and w["pt_rechtsform"]=="Einzelunternehmen" and w["pt_steuer"]=="99/999" and w["a3_steuer"]=="99/999" and w["vertrag_pt_name"]=="Nora Neu",w)
chk("Haken: Nebenberuf, Gewerbe, Weisungsfrei, Hilfspersonen nein",an(w["beauftragung_Nebenberuf"]) and not an(w["beauftragung_Hauptberuf"]) and an(w["a3_gewerbe"]) and an(w["a3_weisungsfrei"]) and an(w["a3_hilfspersonen_nein"]) and not an(w["a3_hilfspersonen_ja"]) and not an(w["a3_konkurrenz"]),w)
chk("Protokollseite (13 Seiten)",len(PdfReader(io.BytesIO(b)).pages)==13)
chk("Vereinbarungsdatum gesetzt",sql(f"select vereinbarung_am from vertriebspartner where id='{pid}'")==heute)
chk("Team-Mail",len(mail_an(ADM,"Handelsvertretervertrag bestätigt"))>=1)
chk("Datei abrufbar, fremde nicht",v.get(f"/api/vertrieb/vertrag/{hid}/datei").content.startswith(b"%PDF") and cA.get(f"/api/vertrieb/vertrag/{hid}/datei").status_code in (401,403))
# ---- Einarbeitung und Leitfaden
e=v.get("/api/vertrieb/einarbeitung").json(); chk("Checkliste: Vertrag erledigt, Rest offen",len(e["punkte"])==5 and [x["code"] for x in e["punkte"] if x["erledigt"]]==["vertrag"] and not e["fertig"],e)
chk("Leitfaden gelesen",v.post("/api/vertrieb/einarbeitung/leitfaden-gelesen").status_code==200 and "leitfaden" in [x["code"] for x in v.get("/api/vertrieb/einarbeitung").json()["punkte"] if x["erledigt"]])
chk("Admin sieht die Einarbeitung",len(a.get(f"/api/admin/vertrieb/partner/{pid}/einarbeitung").json()["punkte"])==5 and a.get("/api/admin/vertrieb/partner/xyz/einarbeitung").status_code==404 and v.get(f"/api/admin/vertrieb/partner/{pid}/einarbeitung").status_code==403)
t=v.get("/api/vertrieb/telefonleitfaden-text").json(); chk("Leitfaden als Text (18 Seiten, durchsuchbar)",len(t["seiten"])==18 and sum(len(s["text"]) for s in t["seiten"])>5000)
chk("Leitfaden-Text nur für Vertriebler",cA.get("/api/vertrieb/telefonleitfaden-text").status_code in (401,403) and httpx.get(B+"/api/vertrieb/telefonleitfaden-text",headers=H).status_code in (401,403))
# ---- Übersicht
u=a.get("/api/admin/vertragsdokumente/uebersicht").json(); ka={x["id"]:x for x in u["kunden"]}; pa={x["id"]:x for x in u["partner"]}
chk("Übersicht Kunden: AVV fehlt, Referenz widerrufen / wartet",not ka[kA]["avv_ok"] and ka[kA]["referenz"]["stand"]=="widerrufen" and ka[kB]["referenz"]["stand"]=="gesendet",ka.get(kA))
chk("Übersicht Vertriebler: Vertrag liegt vor, Einarbeitung 2 von 5",pa[pid]["vertrag"]["stand"]=="unterschrieben" and pa[pid]["einarbeitung_erledigt"]==2 and pa[pid]["einarbeitung_gesamt"]==5,pa.get(pid))
chk("Übersicht nur für Admins",cA.get("/api/admin/vertragsdokumente/uebersicht").status_code==403 and v.get("/api/admin/vertragsdokumente/uebersicht").status_code==403)
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
TOUR="fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); errs=[]
        async def seite(mail,pw_,ziel,breite=1200):
            ctx=await br.new_context(viewport={"width":breite,"height":1000},bypass_csp=True); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
            await pg.goto(B+"/"); await pg.fill("#e",mail); await pg.fill("#p",pw_); await pg.click("#b"); await pg.wait_for_url("**/"+ziel.split("#")[0].strip("/")+"*")
            await pg.evaluate(TOUR); await pg.wait_for_timeout(400); return pg
        # Kunde: offener Vertrag -> Formular
        a.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={"projekt":"Zweites Projekt"})
        pg=await seite(mA,"InhaberPasswort1","app"); await pg.goto(B+"/app#vertraege"); await pg.reload(); await pg.wait_for_selector("h2:has-text('Referenzvertrag: deine Freigabe')",timeout=8000)
        chk("UI Kunde: Formular mit allen Elementen und Kanälen",await pg.locator("input[type=checkbox]").count()>=16 and await pg.get_by_role("button",name="Freigabe bestätigen").count()==1)
        await pg.get_by_role("button",name="Freigabe bestätigen").click(); await pg.wait_for_selector(".msg",timeout=5000)
        chk("UI Kunde: Fehlermeldung ohne Angaben",await pg.locator(".msg").count()>=1)
        await pg.screenshot(path="/var/tmp/pt/shots/referenz_online.png",full_page=True)
        # Vertriebler: Vertrag, Checkliste, Suche
        pv=await seite(f"nora{sfx}@v.de","NoraPasswort123456","vertrieb",420); await pv.goto(B+"/vertrieb#vertrag"); await pv.reload(); await pv.wait_for_selector("h2:has-text('Mein Handelsvertretervertrag')",timeout=8000)
        chk("UI Vertrieb: Vertrag bestätigt, Download",await pv.get_by_text("online im Portal").count()>=1 and await pv.get_by_role("link",name="Vertrag ansehen").count()==1)
        await pv.goto(B+"/vertrieb#willkommen"); await pv.reload(); await pv.wait_for_selector("h2:has-text('Deine Startcheckliste')",timeout=8000)
        chk("UI Vertrieb: Checkliste mit erledigten Punkten",await pv.locator("li:has-text('✅')").count()==2 and await pv.locator("li:has-text('⬜')").count()==3)
        await pv.goto(B+"/vertrieb#leitfaden"); await pv.reload(); await pv.wait_for_selector("h2:has-text('Im Leitfaden suchen')",timeout=8000)
        await pv.fill("main .card input[type=search]","Einwand"); await pv.wait_for_timeout(400)
        chk("UI Vertrieb: Suche liefert Treffer mit Seitenangabe",await pv.get_by_text("Seite ").count()>=1)
        # Admin: Verträge-Seite
        pa_=await seite("chef@test.de",PW,"admin"); await pa_.goto(B+"/admin#vertraege"); await pa_.reload(); await pa_.wait_for_selector("h1:has-text('Verträge')",timeout=8000)
        chk("UI Admin: Übersicht mit Kunden, Vertrieblern, Referenzen",await pa_.get_by_text("Referenzen: was darf gezeigt werden?").count()==1 and await pa_.get_by_text("Nora Neu").count()>=1 and await pa_.get_by_text("Widerrufene Referenzen").count()==1)
        await pa_.screenshot(path="/var/tmp/pt/shots/vertraege_admin.png",full_page=True)
        await pa_.goto(B+f"/admin#partner/{pid}"); await pa_.reload(); await pa_.wait_for_selector("h2:has-text('Einarbeitung')",timeout=8000)
        chk("UI Admin: Einarbeitung beim Vertriebler",await pa_.locator("li:has-text('Handelsvertretervertrag unterschrieben')").count()==1)
        chk("Keine JS-Fehler",not errs,errs); await br.close()
asyncio.run(main())
print("FERTIG")
