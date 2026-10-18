import sys, time, httpx
sys.path.insert(0,"/home/claude/markentrix-server/portal")
from app import zweifaktor as z
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else i)
def cl(): return httpx.Client(base_url=B,headers=H)
# RFC 6238 Testvektor
g="GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
chk("RFC6238",z._code(g,59//30)=="287082" and z.pruefen_code(g,"287082",0,59)==1)
chk("replay blockiert",z.pruefen_code(g,"287082",1,59) is None)
pw=open("/var/tmp/pt/adminpw").read().strip()
a=cl(); r=a.post("/api/login",json={"email":"chef@test.de","password":pw}); chk("login ohne 2fa",r.json().get("ziel")=="/admin",r.text)
r=a.post("/api/2fa/start"); d=r.json(); chk("start",r.status_code==200 and d["qr"].startswith("data:image/svg") and d["geheimnis"],r.text[:100])
chk("falscher code",a.post("/api/2fa/aktivieren",json={"code":"000000"}).status_code==400)
k=z.pruefen_code(d["geheimnis"],z._code(d["geheimnis"],int(time.time()//30)),0)
r=a.post("/api/2fa/aktivieren",json={"code":z._code(d["geheimnis"],int(time.time()//30))}); chk("aktivieren",r.status_code==200 and len(r.json()["notfallcodes"])==10,r.text)
codes=r.json()["notfallcodes"]
chk("me zeigt 2fa",a.get("/api/me").json()["zwei_faktor"] is True)
b=cl(); r=b.post("/api/login",json={"email":"chef@test.de","password":pw}); chk("login verlangt code",r.status_code==200 and r.json()=={"zwei_faktor":True},r.text); chk("noch keine session",b.get("/api/me").status_code==401)
b2=cl(); r=b2.post("/api/login",json={"email":"chef@test.de","password":pw,"code":"123456"}); chk("falscher code 401",r.status_code==401 and "Code" in r.text,r.text)
# aktueller Schritt wurde bei der Aktivierung verbraucht -> nächster Schritt (±1 erlaubt)
nxt=z._code(d["geheimnis"],int(time.time()//30)+1)
b3=cl(); r=b3.post("/api/login",json={"email":"chef@test.de","password":pw,"code":nxt}); chk("login mit code",r.status_code==200 and r.json().get("ziel")=="/admin",r.text)
b4=cl(); r=b4.post("/api/login",json={"email":"chef@test.de","password":pw,"code":nxt}); chk("replay abgelehnt",r.status_code==401,r.text)
b5=cl(); r=b5.post("/api/login",json={"email":"chef@test.de","password":pw,"code":codes[0]}); chk("notfallcode ok",r.status_code==200,r.text)
b6=cl(); r=b6.post("/api/login",json={"email":"chef@test.de","password":pw,"code":codes[0]}); chk("notfallcode nur einmal",r.status_code==401,r.text)
b7=cl(); r=b7.post("/api/login",json={"email":"chef@test.de","password":"falsch12345","code":"123456"}); chk("falsches pw verrät kein 2fa","Code" not in r.text,r.text)
chk("status",a.get("/api/2fa").json()=={"aktiv":True,"notfallcodes_uebrig":9},a.get("/api/2fa").text)
# Admin kann zurücksetzen / ausschalten
r=a.post("/api/2fa/deaktivieren",json={"passwort":"falsch","code":codes[1]}); chk("ausschalten braucht pw",r.status_code==400)
r=a.post("/api/2fa/deaktivieren",json={"passwort":pw,"code":codes[1]}); chk("ausschalten",r.status_code==200,r.text)
chk("danach login ohne code",cl().post("/api/login",json={"email":"chef@test.de","password":pw}).json().get("ziel")=="/admin")
uid=a.get("/api/me").json()["id"]
chk("admin reset 404 bei Unsinn",a.post("/api/admin/benutzer/nix/2fa-zuruecksetzen").status_code==404)
chk("admin reset ok",a.post(f"/api/admin/benutzer/{uid}/2fa-zuruecksetzen").status_code==200)
# Recht / Firma
p=httpx.get(B+"/api/recht"); chk("recht öffentlich",p.status_code==200 and "Datenschutz" in p.json()["datenschutz"] and "§ 5 DDG" in p.json()["impressum"],p.text[:200])
chk("seiten",httpx.get(B+"/impressum").status_code==200 and httpx.get(B+"/datenschutz").status_code==200)
r=a.put("/api/admin/einstellungen/firma",json={"name":"Markentrix","inhaber":"Christian Wien","strasse":"Teststr. 1","plz":"29221","ort":"Celle","email":"info@markentrix.de","kleinunternehmer":False,"iban":"DE00 0000 0000 0000 0000 00"}); chk("firma speichern",r.status_code==200,r.text)
p=httpx.get(B+"/api/recht").json(); chk("firma im impressum","Christian Wien" in p["impressum"] and "29221 Celle" in p["impressum"] and "info@markentrix.de" in p["datenschutz"],p["impressum"])
r=a.put("/api/admin/einstellungen/recht",json={"impressum":"Mein eigener Text","datenschutz":""}); p=httpx.get(B+"/api/recht").json(); chk("override",p["impressum"]=="Mein eigener Text" and "Verantwortlicher" in p["datenschutz"])
a.put("/api/admin/einstellungen/recht",json={"impressum":"","datenschutz":""})
chk("recht nur admin",cl().put("/api/admin/einstellungen/recht",json={"impressum":"x"}).status_code==401)
