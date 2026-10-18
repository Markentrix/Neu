import httpx, re, base64, struct, zlib, subprocess, json
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
import time; sfx=str(int(time.time()))
k=a.post("/api/admin/kunden",json={"firma":"Team Test "+sfx,"ansprechpartner":"Tina","email":f"tina{sfx}@tt.de","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
def tok(mailto):
    raw=open("/var/tmp/pt/mails.txt").read()
    import email, quopri
    for x in reversed([x for x in raw.split("\n=====\n") if x.strip()]):
        m=email.message_from_string(x)
        if mailto in str(m["To"]):
            for part in m.walk():
                if part.get_content_type()=="text/plain":
                    t=part.get_payload(decode=True).decode("utf8"); g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",t)
                    if g: return g.group(1)
inh=httpx.Client(base_url=B,headers=H)
t=tok(f"tina{sfx}@tt.de"); chk("einladung inhaber",t is not None)
chk("pw setzen",httpx.post(B+"/api/einladung",headers=H,json={"token":t,"password":"InhaberPasswort1"}).status_code==200)
chk("login inhaber",inh.post("/api/login",json={"email":f"tina{sfx}@tt.de","password":"InhaberPasswort1"}).status_code==200)
chk("me rolle",inh.get("/api/me").json()["kunden_rolle"]=="inhaber")
chk("start rolle",inh.get("/api/kunde/start").json()["kunden_rolle"]=="inhaber")
team=inh.get("/api/kunde/team").json(); chk("team liste",len(team)==1 and team[0]["kunden_rolle"]=="inhaber",team)
# Einladen
chk("ungültige rolle",inh.post("/api/kunde/team/einladen",json={"email":"x@y.de","kunden_rolle":"chef"}).status_code==400)
chk("ungültige mail",inh.post("/api/kunde/team/einladen",json={"email":"quatsch","kunden_rolle":"mitarbeiter"}).status_code==400)
r=inh.post("/api/kunde/team/einladen",json={"email":f"max{sfx}@tt.de","name":"Max","kunden_rolle":"mitarbeiter"}); chk("einladen mitarbeiter",r.status_code==200 and r.json()["gemailt"],r.text)
r=inh.post("/api/kunde/team/einladen",json={"email":f"lena{sfx}@tt.de","name":"Lena","kunden_rolle":"nur_lesen"}); chk("einladen nur_lesen",r.status_code==200)
mit=httpx.Client(base_url=B,headers=H); lesen=httpx.Client(base_url=B,headers=H)
for c,n,pw in ((mit,"max","MitarbeiterPw1"),(lesen,"lena","LesenPasswort1")):
    httpx.post(B+"/api/einladung",headers=H,json={"token":tok(f"{n}{sfx}@tt.de"),"password":pw}); c.post("/api/login",json={"email":f"{n}{sfx}@tt.de","password":pw})
chk("mitarbeiter start",mit.get("/api/kunde/start").status_code==200 and mit.get("/api/kunde/start").json()["kunden_rolle"]=="mitarbeiter")
chk("mitarbeiter kein team",mit.get("/api/kunde/team").status_code==403)
chk("mitarbeiter keine belege",mit.get("/api/kunde/belege").status_code==403)
chk("mitarbeiter einladen verboten",mit.post("/api/kunde/team/einladen",json={"email":"a@b.de","kunden_rolle":"inhaber"}).status_code==403)
chk("mitarbeiter darf profil ändern",mit.patch("/api/kunde/profil",json={"telefon":"123"}).status_code==200)
chk("nur_lesen darf lesen",lesen.get("/api/kunde/start").status_code==200 and lesen.get("/api/kunde/anfragen").status_code==200)
r=lesen.patch("/api/kunde/profil",json={"telefon":"999"}); chk("nur_lesen darf nicht schreiben",r.status_code==403,r.text)
chk("nur_lesen kein chat senden",lesen.post("/api/kunde/chat",json={"text":"hi"}).status_code==403)
# Eigenschutz
me=[x for x in inh.get("/api/kunde/team").json() if x["email"].startswith("tina")][0]
chk("selbst sperren verboten",inh.patch(f"/api/kunde/team/{me['id']}",json={"aktiv":False}).status_code==400)
chk("selbst degradieren verboten",inh.patch(f"/api/kunde/team/{me['id']}",json={"kunden_rolle":"mitarbeiter"}).status_code==400)
mx=[x for x in inh.get("/api/kunde/team").json() if x["email"].startswith("max")][0]
chk("rolle ändern",inh.patch(f"/api/kunde/team/{mx['id']}",json={"kunden_rolle":"nur_lesen"}).status_code==200)
chk("jetzt nur lesen",mit.patch("/api/kunde/profil",json={"telefon":"1"}).status_code==403)
chk("sperren",inh.patch(f"/api/kunde/team/{mx['id']}",json={"aktiv":False}).status_code==200)
chk("gesperrt: Sitzung weg",mit.get("/api/kunde/start").status_code==401)
chk("gesperrt: login geht nicht",httpx.post(B+"/api/login",headers=H,json={"email":f"max{sfx}@tt.de","password":"MitarbeiterPw1"}).status_code in (401,403))
chk("fremder Zugang 404",inh.patch("/api/kunde/team/00000000-0000-0000-0000-000000000000",json={"aktiv":False}).status_code==404)
chk("ungültige id 404",inh.patch("/api/kunde/team/nix",json={"aktiv":False}).status_code==404)
# fremder Kunde: anderer Kunde darf nicht
k2=a.post("/api/admin/kunden",json={"firma":"Fremd "+sfx,"paket_code":"KI_ONE"}).json()
fremd=a.post(f"/api/admin/kunden/{k2['id']}/einladung",json={"email":f"fremd{sfx}@tt.de","per_mail":True}).json()
httpx.post(B+"/api/einladung",headers=H,json={"token":tok(f"fremd{sfx}@tt.de"),"password":"FremdPasswort11"}); f=httpx.Client(base_url=B,headers=H); f.post("/api/login",json={"email":f"fremd{sfx}@tt.de","password":"FremdPasswort11"})
chk("fremder inhaber kann nicht ändern",f.patch(f"/api/kunde/team/{mx['id']}",json={"aktiv":True}).status_code==404)
chk("fremder sieht anderes Team nicht",all(x["email"].startswith("fremd") for x in f.get("/api/kunde/team").json()))
chk("einladung mail eines anderen Kunden → 409",inh.post("/api/kunde/team/einladen",json={"email":f"fremd{sfx}@tt.de","kunden_rolle":"mitarbeiter"}).status_code==409)
# admin sieht Rolle
d=a.get(f"/api/admin/kunden/{kid}").json(); chk("admin zugänge mit rolle",all("kunden_rolle" in z for z in d["benutzer"]) and "logo" not in d["kunde"],list(d["kunde"].keys()))
# Branding
png=base64.b64encode(b"\x89PNG\r\n\x1a\n"+b"0"*100).decode()
chk("farbe ungültig",a.put(f"/api/admin/kunden/{kid}/branding",json={"farbe":"rot"}).status_code==400)
chk("logo ungültig",a.put(f"/api/admin/kunden/{kid}/branding",json={"logo_base64":base64.b64encode(b"<svg onload=alert(1)>").decode()}).status_code==400)
chk("logo nicht base64",a.put(f"/api/admin/kunden/{kid}/branding",json={"logo_base64":"!!!"}).status_code==400)
r=a.put(f"/api/admin/kunden/{kid}/branding",json={"farbe":"#ff6600","logo_base64":"data:image/png;base64,"+png}); chk("branding speichern",r.status_code==200,r.text)
chk("kunde sieht farbe",inh.get("/api/kunde/start").json()["kunde"]["branding_farbe"]=="#ff6600" and inh.get("/api/kunde/start").json()["kunde"]["logo_vorhanden"])
r=inh.get("/api/kunde/logo"); chk("logo abrufbar",r.status_code==200 and r.headers["content-type"]=="image/png" and r.content.startswith(b"\x89PNG"))
chk("fremder logo 404",f.get("/api/kunde/logo").status_code==404)
chk("admin logo",a.get(f"/api/admin/kunden/{kid}/logo").status_code==200)
r=a.put(f"/api/admin/kunden/{kid}/branding",json={"farbe":None,"logo_entfernen":True}); chk("entfernen",r.status_code==200 and inh.get("/api/kunde/logo").status_code==404)
chk("kunde darf kein branding",inh.put(f"/api/admin/kunden/{kid}/branding",json={"farbe":"#000000"}).status_code==403)
# PWA
chk("manifest",json.loads(httpx.get(B+"/manifest.webmanifest").text)["short_name"]=="Markentrix")
chk("sw",httpx.get(B+"/sw.js").status_code==200 and "javascript" in httpx.get(B+"/sw.js").headers["content-type"])
chk("icon",httpx.get(B+"/static/icons/icon-192.png").status_code==200)
