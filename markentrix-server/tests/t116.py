"""Vertrieb: Lead-Suche mit Filtern, Anruf-Modus (nächster heißer Lead), Lead aus Foto."""
import httpx, time, base64, sys, os, re, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
sfx=str(int(time.time())+1770)
pub=httpx.Client(base_url=B,headers=H)
pr=a.post("/api/admin/vertrieb/partner",json={"name":"Nora Naechster","email":f"nora{sfx}@v.de"}).json(); pid=pr["id"]
lk=a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"nora{sfx}@v.de","per_mail":False}).json()["einladungslink"].replace(B,"")
httpx.post(B+"/api/einladung",headers=H,json={"token":lk.split("token=")[1],"password":"NoraPasswort123456"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"nora{sfx}@v.de","password":"NoraPasswort123456"}).status_code==200
def lead(tag,**kw):
    d={"firma":f"Nae{tag} {sfx}","telefon":f"0511 77{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","vertriebspartner_id":pid,"email":f"nae{tag}{sfx}@lead.de"}; d.update(kw)
    r=a.post("/api/admin/leads",json=d); assert r.status_code==200,r.text; return r.json()["id"]
ids={t:lead(t) for t in "abcde"}
for t in "abc": sql(f"update leads set temperatur='heiss' where id='{ids[t]}'")
sql(f"update leads set temperatur='warm' where id='{ids['d']}'")
sql(f"update leads set ort='Hannover', status='kontaktiert', wiedervorlage_am=current_date-1 where id='{ids['e']}'")
# ---------------------------------------------------------------- Suche
r=v.get("/api/vertrieb/leadsuche").json(); chk("Liste mit Zählern",r["gesamt"]==5 and r["zaehler"].get("neu")==4 and r["zaehler"].get("kontaktiert")==1 and r["faellig"]==1,r["zaehler"])
chk("Fällige Wiedervorlage steht oben",r["leads"][0]["id"]==ids["e"])
chk("Suche nach Firma",[x["id"] for x in v.get("/api/vertrieb/leadsuche",params={"q":f"Naeb {sfx}"}).json()["leads"]]==[ids["b"]])
chk("Suche nach Ort",[x["id"] for x in v.get("/api/vertrieb/leadsuche",params={"q":"Hannover"}).json()["leads"]]==[ids["e"]])
chk("Suche nach Telefonteil",v.get("/api/vertrieb/leadsuche",params={"q":sfx[-4:]}).json()["gesamt"]==5)
chk("Platzhalter % wirkt nicht als Joker",v.get("/api/vertrieb/leadsuche",params={"q":"%"}).json()["gesamt"]==0)
chk("Filter Status",v.get("/api/vertrieb/leadsuche",params={"status":"kontaktiert"}).json()["gesamt"]==1)
chk("Filter HOT",v.get("/api/vertrieb/leadsuche",params={"temperatur":"heiss"}).json()["gesamt"]==3)
chk("Filter fällig",v.get("/api/vertrieb/leadsuche",params={"faellig":1}).json()["gesamt"]==1)
chk("Ungültiger Status abgelehnt",v.get("/api/vertrieb/leadsuche",params={"status":"x"}).status_code==400)
chk("Seite jenseits des Endes ist leer, nicht kaputt",v.get("/api/vertrieb/leadsuche",params={"seite":9}).json()["leads"]==[])
chk("Fremde Leads tauchen nicht auf",lead("z",vertriebspartner_id=None) and v.get("/api/vertrieb/leadsuche").json()["gesamt"]==5)
chk("Ohne Anmeldung kein Zugriff",pub.get("/api/vertrieb/leadsuche").status_code in (401,403) and pub.get("/api/vertrieb/naechster").status_code in (401,403))
# ---------------------------------------------------------------- Anruf-Modus
n=v.get("/api/vertrieb/naechster",params={"modus":"heiss"}).json()
chk("Anruf-Modus: zuerst heißer Lead",n["quelle"]=="heiss" and n["id"] in (ids["a"],ids["b"],ids["c"]) and n["uebrig"]==3,n)
erledigt=[]; gesehen=[]
for _ in range(3):
    n=v.get("/api/vertrieb/naechster",params={"modus":"zufall","ausser":",".join(erledigt)}).json(); gesehen.append(n["id"]); erledigt.append(n["id"])
chk("Zufällig: jeder heiße Lead genau einmal",sorted(gesehen)==sorted([ids["a"],ids["b"],ids["c"]]),gesehen)
n=v.get("/api/vertrieb/naechster",params={"modus":"heiss","ausser":",".join(erledigt)}).json()
chk("Danach fällige Wiedervorlage",n["quelle"]=="wiedervorlage" and n["id"]==ids["e"],n)
erledigt.append(ids["e"])
n=v.get("/api/vertrieb/naechster",params={"modus":"heiss","ausser":",".join(erledigt)}).json()
chk("Danach neue Leads",n["quelle"]=="neu" and n["id"] in (ids["d"],),n)
erledigt.append(ids["d"]); n=v.get("/api/vertrieb/naechster",params={"modus":"heiss","ausser":",".join(erledigt)}).json()
chk("Zum Schluss: nichts mehr",n["id"] is None,n)
sql(f"update leads set status='gesperrt' where id='{ids['a']}'")
n=v.get("/api/vertrieb/naechster",params={"modus":"heiss"}).json(); chk("Gesperrter Lead wird nie angeboten",n["id"] != ids["a"],n)
ok=v.post(f"/api/vertrieb/leads/{ids['b']}/kontakt",json={"ergebnis":"anruf_nicht_erreicht"}).status_code==200
n=v.get("/api/vertrieb/naechster",params={"modus":"heiss"}).json()
chk("Festgehaltener Lead (Wiedervorlage in der Zukunft) kommt nicht sofort wieder",ok and n["id"]!=ids["b"] and n["uebrig"]==1,n)
chk("Ungültiger Modus abgelehnt",v.get("/api/vertrieb/naechster",params={"modus":"quatsch"}).status_code==400)
chk("Ungültige IDs in der Ausschlussliste stören nicht",v.get("/api/vertrieb/naechster",params={"ausser":"';drop table leads;--,123"}).status_code==200)
# ---------------------------------------------------------------- Foto
a.put("/api/admin/einstellungen/ki",json={"api_key":"sk-test","modell":"claude-sonnet-5-5","tageslimit":50,"preis_ein_eur":3,"preis_aus_eur":15})
jpg=base64.b64encode(b"\xff\xd8\xff\xe0"+b"0"*400).decode()
r=v.post("/api/vertrieb/leads/foto",json={"typ":"image/jpeg","daten":jpg}); chk("Foto: Felder werden gelesen",r.status_code==200 and r.json()["felder"]["firma"]=="Autohaus Foto GmbH" and r.json()["felder"]["ort"]=="Celle",r.text)
chk("Foto wird nicht gespeichert (kein Lead entsteht)",int(sql("select count(*) from leads where firma='Autohaus Foto GmbH'"))==0)
chk("Foto: Kosten werden festgehalten",int(sql("select count(*) from kosten_log where kunden_id is null and dienst='anthropic' and menge=960"))>=1)
chk("Foto: kein Bild (falsche Kopfbytes) abgelehnt",v.post("/api/vertrieb/leads/foto",json={"typ":"image/png","daten":jpg}).status_code==400)
chk("Foto: kein Base64 abgelehnt",v.post("/api/vertrieb/leads/foto",json={"typ":"image/jpeg","daten":"!"*200}).status_code==400)
chk("Foto: falscher Typ abgelehnt",v.post("/api/vertrieb/leads/foto",json={"typ":"application/pdf","daten":jpg}).status_code==422)
chk("Foto: ohne Anmeldung nicht möglich",pub.post("/api/vertrieb/leads/foto",json={"typ":"image/jpeg","daten":jpg}).status_code in (401,403))
