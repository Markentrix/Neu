"""Anruf-Modus für den Admin: nächster heißer Lead über alle Leads oder nur eines Vertrieblers."""
import httpx, time, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); assert a.post("/api/login",json={"email":"chef@test.de","password":ADMPW}).status_code==200
pub=httpx.Client(base_url=B,headers=H)
sfx=str(int(time.time())+1790)
pid=a.post("/api/admin/vertrieb/partner",json={"name":"Anton Admin","email":f"anton{sfx}@v.de"}).json()["id"]
def lead(tag,**kw):
    d={"firma":f"Adm{tag} {sfx}","telefon":f"0511 88{ord(tag)}{sfx[-4:]}","ort":"Celle","plz":"29221","email":f"adm{tag}{sfx}@lead.de"}; d.update(kw)
    r=a.post("/api/admin/leads",json=d); assert r.status_code==200,r.text; return r.json()["id"]
mit=lead("a",vertriebspartner_id=pid); ohne=lead("b")
for i in (mit,ohne): sql(f"update leads set temperatur='heiss' where id='{i}'")
U="/api/admin/anrufmodus/naechster"
r=a.get(U,params={"modus":"heiss","vertriebler":pid}).json(); chk("Nur Leads eines Vertrieblers",r["id"]==mit and r["uebrig"]==1,r)
r=a.get(U,params={"modus":"heiss","vertriebler":"keiner"}).json(); chk("Nicht zugeordnete Leads",r["id"]==ohne,r)
r=a.get(U,params={"modus":"zufall"}).json(); chk("Alle Leads, zufällige Reihenfolge",r["id"] is not None and r["quelle"]=="heiss",r)
r=a.get(U,params={"modus":"heiss","vertriebler":pid,"ausser":mit}).json(); chk("Abgearbeitete kommen nicht wieder",r["id"] is None and r["uebrig"]==0,r)
chk("Ungültiger Modus abgelehnt",a.get(U,params={"modus":"x"}).status_code==400)
chk("Ungültiger Vertriebler abgelehnt",a.get(U,params={"vertriebler":"abc"}).status_code==400)
chk("Ohne Anmeldung kein Zugriff",pub.get(U).status_code in (401,403))
