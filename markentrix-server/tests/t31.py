from datetime import date, timedelta
import httpx, time, re, email, subprocess, io, sys, json
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
sfx=str(int(time.time()))
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c,f"{name.lower()}{sfx}@k.de"
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import db, jobs
db.open_pool()
import os
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":"0511 5555","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200


f=a.get("/api/admin/einstellungen/firma").json(); f["name"]=f["name"] or "Markentrix Test"; f["iban"]="DE02120300000000202051"; f["bic"]="BYLADEM1001"; f.update({"strasse":"Weg 5","plz":"29221","ort":"Celle","steuernummer":"12/345/67890","email":"info@markentrix.de","inhaber":"Chris Test"})
chk("Firma vorbereitet",a.put("/api/admin/einstellungen/firma",json=f).status_code==200)
# ---------------------------------------------------------------- 1. Erinnerungen
def rechnung(kid,tage):
    b=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","betreff":"Test","positionen":[{"text":"Leistung","menge":1,"einheit":"","preis_cent":10000}]}).json()["id"]
    assert a.post(f"/api/admin/belege/{b}/ausstellen").status_code==200
    sql(f"update belege set faellig_am=current_date+({tage}), status='versendet' where id='{b}'"); return b
k1,c1,m1=neuer_kunde("Mahn"); k2,c2,m2=neuer_kunde("Mahnzwei")
b1=rechnung(k1,-10); b2=rechnung(k2,-20); b3=rechnung(k1,+5)
r=a.get("/api/admin/mahnvorschlaege"); chk("Mahnvorschläge: 200",r.status_code==200,r.text)
vs={x["id"]:x for x in r.json()}
chk("Vorschlag enthält nur überfällige",b1 in vs and b2 in vs and b3 not in vs, list(vs))
chk("Vorschlag: Stufe 1 mit Betreff und Text",vs[b1]["stufe"]==1 and "Zahlungserinnerung" in vs[b1]["betreff"] and "Tina Test" in vs[b1]["text"] and vs[b1]["moeglich"],vs[b1])
n0=len(mail_an(m1,"Zahlungserinnerung"))
r=a.post("/api/admin/mahnungen/senden",json={"eintraege":[{"id":b1,"stufe":1,"text":"Guten Tag Tina,\n\nbitte begleichen Sie die Rechnung bis Freitag. EIGENER-TEXT-4711"},{"id":b2,"stufe":2},{"id":b3,"stufe":1}]})
j=r.json(); chk("Sammelsenden: 2 von 3 gesendet",r.status_code==200 and j["gesendet"]==2,j)
chk("Sammelsenden: nicht überfällige abgelehnt",[x for x in j["ergebnis"] if x["id"]==b3][0]["gesendet"] is False,j)
ms=mail_an(m1,"EIGENER-TEXT-4711"); chk("Mail enthält den bearbeiteten Text",len(ms)==1,len(ms))
chk("Mahnstufe gespeichert",sql(f"select mahnstufe from belege where id='{b1}'")=="1" and sql(f"select mahnstufe from belege where id='{b2}'")=="2")
r=a.get("/api/admin/mahnvorschlaege").json(); v1=[x for x in r if x["id"]==b1][0]
chk("Nächster Vorschlag: Stufe 2 mit Warnung (gerade erst gemahnt)",v1["stufe"]==2 and "erst vor" in v1["warnung"],v1)
chk("Audit für Mahnung mit Hinweis auf angepassten Text",sql("select count(*) from audit_log where aktion='mahnung' and details->>'text_angepasst'='true'")!="0")
chk("Alte Mahn-Route funktioniert weiter",a.post(f"/api/admin/belege/{b2}/mahnung",json={"stufe":3,"senden":False}).status_code==200)
chk("Alle Stufen durch: kein Vorschlag mehr möglich",[x for x in a.get("/api/admin/mahnvorschlaege").json() if x["id"]==b2][0]["moeglich"] is False)
chk("Kunde darf Mahnvorschläge nicht sehen",c1.get("/api/admin/mahnvorschlaege").status_code==403)

# ---------------------------------------------------------------- 4. Vorlagen
r=a.get("/api/admin/textvorlagen"); vl=r.json(); chk("Standardvorlagen vorhanden",r.status_code==200 and len([x for x in vl if x["art"]=="mail"])>=4 and any(x["art"]=="aufgaben" for x in vl),r.text[:200])
mv=[x for x in vl if x["name"]=="Willkommen / Onboarding"][0]
r=a.get(f"/api/admin/textvorlagen/{mv['id']}/fuer/{k1}").json(); chk("Platzhalter werden gefüllt",f"Mahn {sfx}" in r["betreff"] and "Tina Test" in r["text"] and "{" not in r["text"],r)
r=a.post("/api/admin/textvorlagen",json={"art":"mail","name":"Test "+sfx,"betreff":"Hallo {firma}","text":"Text für {name}"}); chk("Vorlage anlegen",r.status_code==200,r.text); vid=r.json()["id"]
chk("Doppelter Name: 409",a.post("/api/admin/textvorlagen",json={"art":"mail","name":"Test "+sfx,"text":"x"}).status_code==409)
chk("Vorlage ändern",a.put(f"/api/admin/textvorlagen/{vid}",json={"art":"mail","name":"Test "+sfx,"betreff":"B","text":"Neu {firma}"}).status_code==200)
chk("Paket ohne Aufgaben: 400",a.post("/api/admin/textvorlagen",json={"art":"aufgaben","name":"leer "+sfx,"aufgaben":[]}).status_code==400)
chk("Vorlage löschen",a.delete(f"/api/admin/textvorlagen/{vid}").status_code==200 and a.delete(f"/api/admin/textvorlagen/{vid}").status_code==404)
chk("Kunde darf Vorlagen nicht sehen",c1.get("/api/admin/textvorlagen").status_code==403)
pk=[x for x in vl if x["art"]=="aufgaben"][0]
r=a.post(f"/api/admin/kunden/{k2}/aufgabenpaket",json={"vorlage_id":pk["id"]}); chk("Aufgabenpaket anwenden: 8 Aufgaben",r.status_code==200 and r.json()["angelegt"]==8,r.text)
chk("Aufgabenpaket doppelt: nichts doppelt",a.post(f"/api/admin/kunden/{k2}/aufgabenpaket",json={"vorlage_id":pk["id"]}).json()["angelegt"]==0)
chk("Aufgaben liegen beim Kunden",sql(f"select count(*) from aufgaben where kunden_id='{k2}' and quelle='auto'")=="8")

# ---------------------------------------------------------------- 2. Sammelaktionen Kunden
r=a.post("/api/admin/kunden/bulk",json={"ids":[k1,k2],"aktion":"aufgabe","titel":"Sammel-Aufgabe "+sfx,"faellig_am":str(date.today()+timedelta(days=2))}); chk("Bulk Aufgabe für 2 Kunden",r.status_code==200 and r.json()["angelegt"]==2,r.text)
chk("Bulk Aufgabe: ohne Titel 400",a.post("/api/admin/kunden/bulk",json={"ids":[k1],"aktion":"aufgabe"}).status_code==400)
r=a.post("/api/admin/kunden/bulk",json={"ids":[k1,k2],"aktion":"mail","betreff":"Info an {firma}","text":"Hallo {name}, SAMMELMAIL-{firma}"}); j=r.json(); chk("Bulk Mail an 2 Kunden",r.status_code==200 and j["gesendet"]==2,r.text)
chk("Bulk Mail: personalisiert",len(mail_an(m1,"SAMMELMAIL-Mahn "+sfx))==1 and len(mail_an(m2,"SAMMELMAIL-Mahnzwei "+sfx))==1)
chk("Bulk Mail: zu viele Kunden 400",a.post("/api/admin/kunden/bulk",json={"ids":[k1]*3+[f"00000000-0000-0000-0000-{i:012d}" for i in range(45)],"aktion":"mail","betreff":"x","text":"y"}).status_code==400)
chk("Bulk Paket",a.post("/api/admin/kunden/bulk",json={"ids":[k1],"aktion":"aufgabenpaket","vorlage_id":pk["id"]}).json()["angelegt"]==8)
chk("Bulk: ungültige ID 400",a.post("/api/admin/kunden/bulk",json={"ids":["kaputt"],"aktion":"aufgabe","titel":"x"}).status_code==400)
chk("Bulk: Kunde darf nicht",c1.post("/api/admin/kunden/bulk",json={"ids":[k1],"aktion":"aufgabe","titel":"x"}).status_code==403)
chk("Audit für Sammelmail",sql("select count(*) from audit_log where aktion='kunden_bulk_mail'")!="0")

# ---------------------------------------------------------------- 3. Gespeicherte Filter
r=a.post("/api/admin/meine-filter",json={"bereich":"leads","name":"Heiße ohne Zuordnung","abfrage":"temperatur=heiss&vertriebler=keiner"}); chk("Filter speichern",r.status_code==200,r.text); fid=r.json()["id"]
chk("Filter ersetzt bei gleichem Namen",a.post("/api/admin/meine-filter",json={"bereich":"leads","name":"Heiße ohne Zuordnung","abfrage":"temperatur=heiss"}).json()["id"]==fid)
fl=a.get("/api/admin/meine-filter?bereich=leads").json(); chk("Filter lesen",len(fl)==1 and fl[0]["abfrage"]=="temperatur=heiss",fl)
chk("Ungültige Zeichen abgelehnt",a.post("/api/admin/meine-filter",json={"bereich":"leads","name":"x","abfrage":"<script>"}).status_code==400)
chk("Ungültiger Bereich abgelehnt",a.post("/api/admin/meine-filter",json={"bereich":"geheim","name":"x"}).status_code==422)
chk("Filter sind nur für den Besitzer",c1.get("/api/admin/meine-filter").status_code==403)
chk("Filter löschen",a.delete(f"/api/admin/meine-filter/{fid}").status_code==200 and a.delete(f"/api/admin/meine-filter/{fid}").status_code==404)

# ---------------------------------------------------------------- 5. Ampel
r=a.get("/api/admin/systemstatus"); j=r.json(); chk("Systemstatus mit Ampel",r.status_code==200 and isinstance(j.get("ampel"),list) and j["gesamt"] in ("ok","warn","bad","unbekannt"),r.text[:300])
ids={x["id"]:x for x in j["ampel"]}
chk("Ampel: Mail-Punkt grün nach erfolgreichem Versand",ids["mail"]["status"]=="ok",ids.get("mail"))
chk("Ampel: Jobs-Punkt vorhanden",ids["jobs"]["status"] in ("warn","unbekannt","ok"),ids.get("jobs"))
from app import betrieb, routes_system
chk("Ampel: Jobs rot ohne Herzschlag",[p for p in routes_system.ampel(None,{"host":"x"},{"wert":{},"sekunden":900},None) if p["id"]=="jobs"][0]["status"] in ("bad","warn"))
sv=routes_system.ampel({"alter_minuten":2,"backup_stunden":50,"offsite_stunden":9999,"offsite_aktiv":True,"platte_prozent":95,"zertifikat_tage":5},{"host":"x"},None,{"wert":{"ok_am":"2026-01-01","fehler_am":"2026-01-02","fehler":"kaputt"}})
st={p["id"]:p["status"] for p in sv}
chk("Ampel: alte Sicherung, externe fehlt, Platte voll, Zertifikat knapp, Mailfehler = rot",st["backup"]==st["offsite"]==st["platte"]==st["zertifikat"]==st["mail"]=="bad",st)
chk("Ampel: Offsite nicht eingerichtet = gelb",[p for p in routes_system.ampel({"alter_minuten":1,"backup_stunden":1,"offsite_aktiv":False,"platte_prozent":10,"zertifikat_tage":60},{"host":"x"},None,None) if p["id"]=="offsite"][0]["status"]=="warn")
betrieb.notieren("jobs"); chk("Herzschlag wird gespeichert",sql("select count(*) from betrieb_status where schluessel='jobs'")=="1")
