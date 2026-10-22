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
sfx=str(int(time.time())+217)
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":True,"mwst_satz":19})
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
import io, json, os, sys, base64, datetime
from email import message_from_string
from pypdf import PdfReader
kA,cA,mA=neuer_kunde("Rv")
p=a.post("/api/admin/vertrieb/partner",json={"name":"Max Muster","email":f"max{sfx}@v.de"}).json(); pid=p["id"]
l=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"max{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":l.split("token=")[1],"password":"MaxPasswort123456"})
v=httpx.Client(base_url=B,headers=H); v.post("/api/login",json={"email":f"max{sfx}@v.de","password":"MaxPasswort123456"})
a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Heinrich-Hüdig-Straße 1","plz":"29227","ort":"Celle","email":"info@markentrix.de","steuernummer":"12/345/67890"})
def pdf_in_mail(adr,t):
    for m in reversed(mail_an(adr,t)):
        for part in m.walk():
            if part.get_content_type()=="application/pdf": return part.get_payload(decode=True), text(m)
    return None,None
def werte(b): return {k:x.get("/V") for k,x in PdfReader(io.BytesIO(b)).get_fields().items()}
# ---- Referenzvertrag
chk("Kunde darf keinen Referenzvertrag erstellen",cA.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={"projekt":"x"}).status_code==403)
chk("Ohne Anmeldung gesperrt",httpx.post(B+f"/api/admin/kunden/{kA}/referenzvertrag",headers=H,json={}).status_code in (401,403))
chk("Vertriebler gesperrt",v.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={}).status_code==403)
chk("Unbekannter Kunde",a.post("/api/admin/kunden/00000000-0000-0000-0000-000000000000/referenzvertrag",json={}).status_code==404)
chk("Ungültige ID",a.post("/api/admin/kunden/xyz/referenzvertrag",json={}).status_code==404)
r=a.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={"projekt":"Website www.rv.de","hauptvertrag_vom":"01.10.2026","zeitraum":"01.09.–30.09.2026"}); chk("Referenzvertrag erstellt und gesendet",r.status_code==200 and r.json()["gesendet"],r.text); zid=r.json()["id"]
b,txt=pdf_in_mail(f"rv{sfx}@k.de","Referenzvertrag"); chk("Mail mit PDF-Anhang an den Kunden",b is not None and b.startswith(b"%PDF"))
w=werte(b); chk("Formular vorausgefüllt (Firma, Straße, Ort, Vertreter, Projekt)",f"Rv {sfx}" in w["kunde_firma"] and w["kunde_strasse"]=="Weg 1" and w["kunde_ort"]=="29221 Celle" and w["kunde_vertreter"]=="Tina Test" and w["a_projekt"]=="Website www.rv.de" and w["a_datum"]=="01.10.2026",w)
chk("Unterschriftsfeld Markentrix mit Ort und Datum",w["sig_mx_ortdatum"]=="Celle, "+datetime.date.today().strftime("%d.%m.%Y"))
chk("Nichts vorangekreuzt (Kunde entscheidet selbst)",all(x in (None,"/Off","") for k,x in w.items() if k.endswith("_ck")),[k for k,x in w.items() if k.endswith("_ck") and x not in (None,"/Off","")])
chk("Mailtext: freiwillig, widerrufbar, kein KI-Name",txt and "freiwillig" in txt and "widerrufen" in txt and "Claude" not in txt)
chk("Text des Vertrags unverändert (7 Seiten)",len(PdfReader(io.BytesIO(b)).pages)==7)
vp=a.get(f"/api/admin/vertragsdokumente/{zid}/vorlage.pdf"); chk("PDF herunterladbar",vp.status_code==200 and vp.content.startswith(b"%PDF") and werte(vp.content)["a_projekt"]=="Website www.rv.de")
z=a.get(f"/api/admin/kunden/{kA}/vertragsdokumente").json(); chk("Liste zeigt Versand",len(z)==1 and z[0]["gesendet_an"]==f"rv{sfx}@k.de" and not z[0]["unterschrieben_am"] and not z[0]["hat_datei"],z)
chk("Liste enthält keine Dateiinhalte","\"datei\":" not in json.dumps(z) and "hat_datei" in z[0])
r=a.post(f"/api/admin/kunden/{kA}/referenzvertrag",json={"projekt":"Nur Entwurf","senden":False}); chk("Nur erstellen: nichts gesendet",r.status_code==200 and not r.json()["gesendet"])
zid2=r.json()["id"]; n0=len(mail_an("anderer@x.de",""))
r=a.post(f"/api/admin/vertragsdokumente/{zid2}/senden",json={"an":"anderer@x.de"}); chk("Später senden an andere Adresse",r.status_code==200,r.text); chk("Mail ging an die angegebene Adresse",pdf_in_mail("anderer@x.de","Referenzvertrag")[0] is not None)
# Unterschrieben ablegen
pdfb=base64.b64encode(vp.content).decode()
chk("Ablegen: Datum in der Zukunft abgelehnt",a.post(f"/api/admin/vertragsdokumente/{zid}/upload",json={"datei_base64":pdfb,"unterschrieben_am":"2099-01-01"}).status_code==400)
chk("Ablegen: kein PDF/Bild abgelehnt",a.post(f"/api/admin/vertragsdokumente/{zid}/upload",json={"datei_base64":base64.b64encode(b"MZ boese").decode(),"unterschrieben_am":"2026-10-22"}).status_code==400)
chk("Ablegen: Unsinn abgelehnt",a.post(f"/api/admin/vertragsdokumente/{zid}/upload",json={"datei_base64":"%%%","unterschrieben_am":"2026-10-22"}).status_code==400)
r=a.post(f"/api/admin/vertragsdokumente/{zid}/upload",json={"datei_base64":pdfb,"datei_name":"Referenz unterschrieben.pdf","unterschrieben_am":"2026-10-20"}); chk("Unterschriebene Fassung abgelegt",r.status_code==200,r.text)
z=a.get(f"/api/admin/kunden/{kA}/vertragsdokumente").json(); zz=[x for x in z if x["id"]==zid][0]; chk("Stand: unterschrieben",str(zz["unterschrieben_am"])=="2026-10-20" and zz["hat_datei"])
d=a.get(f"/api/admin/vertragsdokumente/{zid}/datei"); chk("Datei abrufbar",d.status_code==200 and d.content.startswith(b"%PDF") and d.headers["content-type"]=="application/pdf" and d.headers.get("x-content-type-options")=="nosniff")
chk("Kunde kommt nicht an die Datei",cA.get(f"/api/admin/vertragsdokumente/{zid}/datei").status_code==403)
chk("Löschen",a.delete(f"/api/admin/vertragsdokumente/{zid2}").status_code==200 and a.delete(f"/api/admin/vertragsdokumente/{zid2}").status_code==404)
chk("Unbekannte Datei: 404",a.get("/api/admin/vertragsdokumente/00000000-0000-0000-0000-000000000000/datei").status_code==404 and a.get("/api/admin/vertragsdokumente/xyz/vorlage.pdf").status_code==404)
# ---- Handelsvertretervertrag
chk("Kunde darf nicht",cA.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={}).status_code==403)
chk("Vertriebler darf sich nicht selbst einen erstellen",v.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={}).status_code==403)
chk("Ungültige Beauftragung",a.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={"beauftragung":"x"}).status_code==422)
chk("Unbekannter Vertriebler",a.post("/api/admin/vertrieb/partner/00000000-0000-0000-0000-000000000000/handelsvertretervertrag",json={}).status_code==404)
r=a.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={"rechtsform":"Einzelunternehmen","strasse":"Str 2","ort":"30159 Hannover","steuer":"99/999","beauftragung":"neben","einmal":"25"}); chk("Handelsvertretervertrag erstellt und gesendet",r.status_code==200 and r.json()["gesendet"],r.text); hid=r.json()["id"]
b,txt=pdf_in_mail(f"max{sfx}@v.de","Handelsvertretervertrag"); chk("Mail mit PDF an den Vertriebler",b is not None)
w=werte(b); chk("Partnerdaten vorausgefüllt",w["pt_name"]=="Max Muster" and w["pt_mail"]==f"max{sfx}@v.de" and w["pt_strasse"]=="Str 2" and w["pt_ort"]=="30159 Hannover" and w["pt_rechtsform"]=="Einzelunternehmen" and w["pt_steuer"]=="99/999" and w["vertrag_pt_name"]=="Max Muster",w)
chk("Nebenberuf angekreuzt, Hauptberuf nicht",w["beauftragung_Nebenberuf"]=="/Yes" and w["beauftragung_Hauptberuf"]=="/Off")
chk("Provision: eigene Eingabe übernommen, Rest aus der Vorlage",w["rate_einmal"]=="25" and w["rate_monat"]=="15" and w["rate_praemie"]=="10" and w["rate_vorschuss"]=="50",w)
chk("Steuernummer von Markentrix aus den Firmendaten",w["mx_steuer"]=="12/345/67890",w["mx_steuer"])
chk("Anlage 3 bleibt dem Partner überlassen (nichts angekreuzt)",all(x in (None,"/Off","") for k,x in w.items() if k.startswith("a3_") and not k.endswith(("_ort_datum","_gew_seit","_gew_amt","_steuer"))))
chk("Vertragstext vollständig (12 Seiten)",len(PdfReader(io.BytesIO(b)).pages)==12)
chk("Mailtext ohne KI-Namen",txt and "Anlage 3" in txt and "Claude" not in txt)
chk("Ablegen setzt Vereinbarungsdatum beim Vertriebler",a.post(f"/api/admin/vertragsdokumente/{hid}/upload",json={"datei_base64":base64.b64encode(b).decode(),"unterschrieben_am":"2026-10-21"}).status_code==200 and sql(f"select vereinbarung_am from vertriebspartner where id='{pid}'")=="2026-10-21")
chk("Liste beim Vertriebler",len(a.get(f"/api/admin/vertrieb/partner/{pid}/vertragsdokumente").json())==1)
r=a.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={"senden":False}); w2=werte(a.get(f"/api/admin/vertragsdokumente/{r.json()['id']}/vorlage.pdf").content)
chk("Ohne Eingaben: Name und Mail aus den Stammdaten, Beauftragung offen",w2["pt_name"]=="Max Muster" and w2["beauftragung_Nebenberuf"]=="/Off" and w2["beauftragung_Hauptberuf"]=="/Off")
sql(f"update vertriebspartner set email=NULL where id='{pid}'"); r=a.post(f"/api/admin/vertrieb/partner/{pid}/handelsvertretervertrag",json={}); chk("Ohne E-Mail-Adresse: verständlicher Fehler",r.status_code==400 and "E-Mail" in r.text,r.text)
sql(f"update vertriebspartner set email='max{sfx}@v.de' where id='{pid}'")
chk("Audit",int(sql("select count(*) from audit_log where aktion in ('vertrag_erstellt','vertrag_gesendet','vertrag_unterschrieben_abgelegt')"))>=6)
# ---- Telefonleitfaden für Vertriebler
r=v.get("/api/vertrieb/telefonleitfaden.pdf"); chk("Vertriebler sieht den Telefonleitfaden",r.status_code==200 and r.content.startswith(b"%PDF") and len(PdfReader(io.BytesIO(r.content)).pages)==18 and r.headers["content-type"]=="application/pdf",r.status_code)
chk("Nicht zwischenspeichern",("no-store" in r.headers.get("cache-control","")))
chk("Kunde sieht ihn nicht",cA.get("/api/vertrieb/telefonleitfaden.pdf").status_code==403)
chk("Ohne Anmeldung nicht",httpx.get(B+"/api/vertrieb/telefonleitfaden.pdf",headers=H).status_code in (401,403))
chk("Admin über den Vertriebs-Pfad nicht",a.get("/api/vertrieb/telefonleitfaden.pdf").status_code==403)
# ---- Oberfläche
import asyncio
from playwright.async_api import async_playwright
PW=open("/var/tmp/pt/adminpw").read().strip()
async def main():
    async with async_playwright() as pw:
        br=await pw.chromium.launch(); ctx=await br.new_context(viewport={"width":1300,"height":1000},bypass_csp=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+"/"); await pg.fill("#e","chef@test.de"); await pg.fill("#p",PW); await pg.click("#b"); await pg.wait_for_url("**/admin*")
        await pg.goto(B+f"/admin#kunde/{kA}"); await pg.wait_for_selector("h2:has-text('Referenzvertrag')",timeout=8000)
        c=pg.locator(".card:has(h2:has-text('Referenzvertrag'))"); chk("UI Kunde: Referenzvertrag-Karte mit Liste und Formular",await c.get_by_role("button",name="Erstellen und per Mail senden").count()==1 and await c.get_by_text("unterschrieben").count()>=1)
        vals=await c.locator("input").evaluate_all("e=>e.map(x=>x.value)"); chk("UI Kunde: Vorbelegung (Vertreter und E-Mail)","Tina Test" in vals and f"rv{sfx}@k.de" in vals,vals)
        await pg.goto(B+f"/admin#partner/{pid}"); await pg.wait_for_selector("h2:has-text('Handelsvertretervertrag')",timeout=8000)
        h=pg.locator(".card:has(h2:has-text('Handelsvertretervertrag'))"); chk("UI Vertriebler: Karte, Stand „liegt vor“",await h.get_by_text("liegt vor").count()>=1 and await h.get_by_role("button",name="Erstellen und per Mail senden").count()==1)
        await pg.screenshot(path="/var/tmp/pt/shots/handelsvertreter.png",full_page=True)
        ctx2=await br.new_context(viewport={"width":420,"height":900},bypass_csp=True); vp=await ctx2.new_page(); e2=[]; vp.on("pageerror",lambda e:e2.append(str(e)))
        await vp.goto(B+"/"); await vp.fill("#e",f"max{sfx}@v.de"); await vp.fill("#p","MaxPasswort123456"); await vp.click("#b"); await vp.wait_for_url("**/vertrieb*"); await vp.evaluate("fetch('/api/me/ansicht',{method:'PUT',headers:{'Content-Type':'application/json','X-MK':'1'},body:JSON.stringify({tour_gesehen:true})})"); await vp.wait_for_timeout(500)
        await vp.goto(B+"/vertrieb#leitfaden"); await vp.reload(); await vp.wait_for_selector("h2:has-text('Telefonleitfaden Kaltakquise')",timeout=8000)
        chk("UI Vertrieb: Leitfaden-PDF mit Öffnen und Herunterladen",await vp.locator("a[href='/api/vertrieb/telefonleitfaden.pdf']").count()==2)
        chk("Keine JS-Fehler",not errs and not e2,errs+e2); await br.close()
asyncio.run(main())
print("FERTIG")
