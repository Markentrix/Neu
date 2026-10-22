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
import os, json
sfx=str(int(time.time()))
mail=f"lead{sfx}@firma.de"; U=B+"/api/public/website-check"
payload={"email":mail,"name":"Max Muster","firma":"Muster Bau","website":"https://muster-bau.de","score":42,"ergebnis":{"ladezeit":"langsam","ssl":True,"probleme":["kein Impressum","keine Mobilansicht"]},"einwilligung":True,"einwilligung_text":"Ich stimme zu"}
chk("Ohne Schlüssel gesperrt",httpx.post(U,headers=H,json=payload).status_code==401)
r=a.get("/api/admin/website-check"); chk("Stand: nicht aktiv",r.status_code==200 and r.json()["aktiv"] is False and r.json()["adresse"].endswith("/api/public/website-check"),r.text)
r=a.post("/api/admin/website-check/schluessel",json={}); sec=r.json()["schluessel"]; chk("Schlüssel erzeugt",r.status_code==200 and len(sec)>=40,r.text)
chk("Stand: aktiv",a.get("/api/admin/website-check").json()["aktiv"] is True)
S={**H,"X-Lead-Secret":sec}
chk("Falscher Schlüssel",httpx.post(U,headers={**H,"X-Lead-Secret":"falsch"},json=payload).status_code==401)
chk("Ohne X-MK-Header geblockt",httpx.post(U,headers={"X-Lead-Secret":sec},json=payload).status_code==403)
chk("Ohne Einwilligung kein Lead",httpx.post(U,headers=S,json={**payload,"einwilligung":False}).status_code==400 and sql(f"select count(*) from leads where lower(email)='{mail}'")=="0")
chk("Ungültige E-Mail",httpx.post(U,headers=S,json={**payload,"email":"kein-mail"}).status_code==400)
chk("Score ungültig",httpx.post(U,headers=S,json={**payload,"score":150}).status_code==422)
chk("Ergebnis zu groß",httpx.post(U,headers=S,json={**payload,"ergebnis":{"x":"y"*21000}}).status_code==400)
n0=len(mails())
r=httpx.post(U,headers=S,json=payload); chk("Check 1: neuer Lead",r.status_code==200 and r.json()["neu"] is True,r.text)
chk("Lead gespeichert",sql(f"select quelle||'|'||firma||'|'||score||'|'||status from leads where lower(email)='{mail}'")=="website|Muster Bau|42|neu")
lid=sql(f"select id from leads where lower(email)='{mail}'")
chk("Aufbewahrungsfrist gesetzt",sql(f"select loeschen_nach > current_date + 300 from leads where id='{lid}'")=="t")
chk("Einwilligung protokolliert",sql(f"select count(*) from lead_aktivitaeten where lead_id='{lid}' and art='consent' and inhalt like '%Ich stimme zu%'")=="1")
chk("Ergebnis gespeichert",sql(f"select count(*) from lead_checks where lead_id='{lid}' and ergebnis->>'ladezeit'='langsam'")=="1")
time.sleep(2); chk("Mail ans Team",any("Neuer Lead" in str(m["Subject"]) and "Muster Bau" in str(m["Subject"]) for m in mails()[n0:]))
chk("Aufgabe Nachfassen",sql(f"select count(*) from aufgaben where titel='Lead nachfassen: Muster Bau'")=="1")
r=httpx.post(U,headers=S,json={**payload,"email":mail.upper(),"score":55,"website":"https://muster-bau.de/neu"}); chk("Check 2: gleicher Lead (ohne Duplikat)",r.status_code==200 and r.json()["neu"] is False and sql(f"select count(*) from leads where lower(email)='{mail}'")=="1",r.text)
chk("Beide Checks gespeichert",sql(f"select count(*) from lead_checks where lead_id='{lid}'")=="2" and sql(f"select score from leads where id='{lid}'")=="55")
d=a.get(f"/api/admin/leads/{lid}").json(); chk("Admin sieht Checks im Lead",len(d["checks"])==2 and d["checks"][0]["ergebnis"]["probleme"][0]=="kein Impressum" and any("Website-Check" in x["inhalt"] for x in d["aktivitaeten"]),d.get("checks"))
chk("Lead in Leadliste",any(l["id"]==lid for l in a.get("/api/admin/leads?q=Muster").json()["leads"]))
chk("Status bleibt bei Wiederholung",sql(f"select status from leads where id='{lid}'")=="neu")
a.patch(f"/api/admin/leads/{lid}",json={"status":"kontaktiert"}); httpx.post(U,headers=S,json=payload)
chk("Erneuter Check holt den Lead zurück auf Antwort",sql(f"select status from leads where id='{lid}'")=="antwort")
r=httpx.post(U,headers=S,json={"email":f"b{sfx}@x.de","einwilligung":True,"website":"www.beispiel.de/seite"}); chk("Ohne Firma: Domain als Name",r.status_code==200 and sql(f"select firma from leads where lower(email)='b{sfx}@x.de'")=="www.beispiel.de")
chk("Neuer Schlüssel ersetzt alten",a.post("/api/admin/website-check/schluessel",json={}).status_code==200 and httpx.post(U,headers=S,json=payload).status_code==401)
chk("Website-Lead startet als warm",sql(f"select temperatur from leads where id='{lid}'")=="warm")
chk("Einstufung heiss",a.patch(f"/api/admin/leads/{lid}",json={"temperatur":"heiss"}).status_code==200 and sql(f"select temperatur from leads where id='{lid}'")=="heiss")
chk("Einstufung in Liste",[l for l in a.get("/api/admin/leads?q=Muster").json()["leads"] if l["id"]==lid][0]["temperatur"]=="heiss")
chk("Ungültige Einstufung 400",a.patch(f"/api/admin/leads/{lid}",json={"temperatur":"lauwarm"}).status_code==400)
chk("Einstufung entfernen",a.patch(f"/api/admin/leads/{lid}",json={"temperatur":""}).status_code==200 and sql(f"select coalesce(temperatur,'-') from leads where id='{lid}'")=="-")
chk("Lead löschen",a.delete(f"/api/admin/leads/{lid}").status_code==200 and sql(f"select count(*) from leads where id='{lid}'")=="0" and sql(f"select count(*) from lead_checks where lead_id='{lid}'")=="0")
chk("Löschen: 404 beim zweiten Mal",a.delete(f"/api/admin/leads/{lid}").status_code==404)
chk("Löschen im Audit",sql("select count(*) from audit_log where aktion='lead_geloescht'")>="1")
k=httpx.Client(base_url=B,headers=H)
chk("Kunde darf Admin-Endpunkt nicht",k.get("/api/admin/website-check").status_code in (401,403))
import app.db as db
try: db.close_pool()
except Exception: pass
