"""Gesperrte Zugänge bleiben gesperrt; Telefon-Webhook mit Geheimnis je Kunde."""
import httpx, time, re, email, email.header, subprocess, io, zipfile, json
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def text(m):
    for p in m.walk():
        if p.get_content_type()=="text/plain": return p.get_payload(decode=True).decode("utf8","replace")
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+450)
mk=f"exp{sfx}@k.de"
mk=f"sp{sfx}@k.de"
k=a.post("/api/admin/kunden",json={"firma":f"Sperre {sfx}","ansprechpartner":"Tina Test","email":mk,"telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(mk),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); assert c.post("/api/login",json={"email":mk,"password":"InhaberPasswort1"}).status_code==200
def mitglied(name,mail):
    c.post("/api/kunde/team/einladen",json={"name":name,"email":mail,"kunden_rolle":"empfang"}); httpx.post(B+"/api/einladung",headers=H,json={"token":token(mail),"password":"EmpfangPasswort1"})
    return sql(f"select id from benutzer where email='{mail}'")
m1=f"gs{sfx}@k.de"; m2=f"ok{sfx}@k.de"; id1=mitglied("Gesperrt Gabi",m1); id2=mitglied("Offen Otto",m2)
def login(mail): return httpx.post(B+"/api/login",headers=H,json={"email":mail,"password":"EmpfangPasswort1"}).status_code
r=c.patch(f"/api/kunde/team/{id1}",json={"aktiv":False}); chk("Inhaber sperrt Gabi einzeln",r.status_code==200,r.text)
chk("Merkmal gesetzt",sql(f"select gesperrt_manuell from benutzer where id='{id1}'")=="t")
a.post(f"/api/admin/kunden/{kid}/status",json={"status":"pausiert"})
chk("Pausiert: niemand kann sich anmelden",login(m2)!=200 and login(m1)!=200)
a.post(f"/api/admin/kunden/{kid}/status",json={"status":"aktiv"})
chk("Wieder aktiv: Otto kommt wieder rein",login(m2)==200)
chk("Wieder aktiv: Gabi bleibt gesperrt",login(m1)!=200 and sql(f"select aktiv from benutzer where id='{id1}'")=="f")
c.post("/api/login",json={"email":mk,"password":"InhaberPasswort1"})
r=c.patch(f"/api/kunde/team/{id1}",json={"aktiv":True}); chk("Entsperren durch den Inhaber geht",r.status_code==200 and login(m1)==200 and sql(f"select gesperrt_manuell from benutzer where id='{id1}'")=="f",r.text)
r=a.post(f"/api/admin/benutzer/{id2}/aktiv",json={"aktiv":False}); chk("Admin sperrt Otto",r.status_code==200,r.text)
a.post(f"/api/admin/kunden/{kid}/status",json={"status":"pausiert"}); a.post(f"/api/admin/kunden/{kid}/status",json={"status":"aktiv"})
chk("Admin-Sperre bleibt nach Pause und Reaktivierung",login(m2)!=200)
# ---- Telefon-Webhook
g=a.post("/api/admin/einstellungen/telefon/neues-geheimnis").json()["geheimnis"]
knr=sql(f"select kundennummer from kunden where id='{kid}'")
k2=a.post("/api/admin/kunden",json={"firma":f"Zweiter {sfx}","ansprechpartner":"Zoe Zwei","email":f"z{sfx}@k.de","telefon":"0512","strasse":"Weg 2","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}).json()["id"]
knr2=sql(f"select kundennummer from kunden where id='{k2}'")
call={"data":{"call_id":f"c-{sfx}","caller":{"phone_number":"+4951188"},"summary":"Rückruf","direction":"inbound"}}
ad=a.get(f"/api/admin/kunden/{knr}/telefon-adresse"); chk("Kunden-Adresse abrufbar",ad.status_code==200 and f"/telefon/{knr}?s=" in ad.json()["url"],ad.text)
s1=ad.json()["url"].split("?s=")[1]; s2=a.get(f"/api/admin/kunden/{knr2}/telefon-adresse").json()["url"].split("?s=")[1]
chk("Geheimnisse sind je Kunde verschieden und nicht das Hauptgeheimnis",s1!=s2 and s1!=g and g not in a.get(f"/api/admin/kunden/{knr}/telefon-adresse").text)
chk("Eigenes Geheimnis wirkt für den eigenen Kunden",httpx.post(B+f"/api/webhook/telefon/{knr}?s={s1}",json=call).status_code==200)
chk("Geheimnis eines anderen Kunden wird abgelehnt (401)",httpx.post(B+f"/api/webhook/telefon/{knr}?s={s2}",json={**call,"data":{**call["data"],"call_id":"x2"}}).status_code==401)
chk("Im Header geht es auch",httpx.post(B+f"/api/webhook/telefon/{knr}",headers={"X-Webhook-Secret":s1},json={**call,"data":{**call["data"],"call_id":"x3"}}).status_code==200)
chk("Gemeinsames Geheimnis geht zunächst weiter (nichts bricht)",httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",json={**call,"data":{**call["data"],"call_id":"x4"}}).status_code==200)
chk("Nicht-ASCII-Geheimnis: 401 statt Absturz",httpx.post(B+f"/api/webhook/telefon/{knr}?s=%C3%A4%C3%B6",json=call).status_code==401)
r=a.post("/api/admin/einstellungen/telefon/nur-pro-kunde",json={"aktiv":True}); chk("Gemeinsames Geheimnis abschalten",r.status_code==200 and a.get("/api/admin/einstellungen/telefon").json()["nur_pro_kunde"] is True,r.text)
chk("Danach: gemeinsames Geheimnis 401",httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",json={**call,"data":{**call["data"],"call_id":"x5"}}).status_code==401)
chk("Danach: Kunden-Geheimnis 200",httpx.post(B+f"/api/webhook/telefon/{knr}?s={s1}",json={**call,"data":{**call["data"],"call_id":"x6"}}).status_code==200)
g2=a.post("/api/admin/einstellungen/telefon/neues-geheimnis").json()["geheimnis"]
chk("Neues Hauptgeheimnis: alte Kunden-Geheimnisse ungültig, Schalter bleibt",httpx.post(B+f"/api/webhook/telefon/{knr}?s={s1}",json={**call,"data":{**call["data"],"call_id":"x7"}}).status_code==401 and a.get("/api/admin/einstellungen/telefon").json()["nur_pro_kunde"] is True)
chk("Unbekannte Kundennummer bei Adresse: 404",a.get("/api/admin/kunden/K-NIX/telefon-adresse").status_code==404)
a.post("/api/admin/einstellungen/telefon/nur-pro-kunde",json={"aktiv":False})
print("FERTIG")
