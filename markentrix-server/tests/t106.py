"""Passkey-Anmeldung (WebAuthn): Registrierung, Anmeldung ohne Passwort, Fälschungs- und Wiederholungsschutz, Zählerprüfung, Zwei-Faktor-Pflicht."""
import httpx, time, re, email, email.header, json, os, sys, subprocess, datetime, zoneinfo
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def mails():
    try: return [email.message_from_string(x) for x in open("/var/tmp/pt/mails.txt").read().split("\n=====\n") if x.strip()]
    except FileNotFoundError: return []
def teil(m,typ):
    for p in m.walk():
        if p.get_content_type()==typ: return p.get_payload(decode=True).decode("utf8","replace")
text=lambda m: teil(m,"text/plain")
betreff=lambda m: str(email.header.make_header(email.header.decode_header(m["Subject"])))
def token(adr):
    time.sleep(1.2)
    for m in reversed(mails()):
        if adr in str(m["To"]):
            g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",text(m))
            if g: return g.group(1)
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
sfx=str(int(time.time())+1500)
def neuer_kunde(name):
    k=a.post("/api/admin/kunden",json={"firma":f"{name} {sfx}","ansprechpartner":"Tina Test","email":f"{name.lower()}{sfx}@k.de","telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json()
    httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"{name.lower()}{sfx}@k.de"),"password":"InhaberPasswort1"})
    c=httpx.Client(base_url=B,headers=H); r=c.post("/api/login",json={"email":f"{name.lower()}{sfx}@k.de","password":"InhaberPasswort1"}); assert r.status_code==200,r.text
    return k["id"],c
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app import db, passkey
from app.db import tx
db.open_pool()


import hashlib, struct, base64, secrets
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def cb(x):
    def kopf(t,n):
        if n<24: return bytes([t<<5|n])
        if n<256: return bytes([t<<5|24,n])
        return bytes([t<<5|25])+n.to_bytes(2,"big")
    if isinstance(x,bool): raise TypeError
    if isinstance(x,int): return kopf(0,x) if x>=0 else kopf(1,-1-x)
    if isinstance(x,bytes): return kopf(2,len(x))+x
    if isinstance(x,str): return kopf(3,len(x.encode()))+x.encode()
    if isinstance(x,dict): return kopf(5,len(x))+b"".join(cb(k)+cb(v) for k,v in x.items())
    raise TypeError(x)
ORIGIN="http://localhost:8000"; RP=hashlib.sha256(b"localhost").digest()
class Geraet:
    def __init__(s): s.key=ec.generate_private_key(ec.SECP256R1()); s.cid=secrets.token_bytes(32); s.zaehler=1
    def registrieren(s,ch,flags=0x45,origin=ORIGIN,typ="webauthn.create"):
        n=s.key.public_key().public_numbers()
        cose=cb({1:2,3:-7,-1:1,-2:n.x.to_bytes(32,"big"),-3:n.y.to_bytes(32,"big")})
        ad=RP+bytes([flags])+struct.pack(">I",s.zaehler)+bytes(16)+struct.pack(">H",len(s.cid))+s.cid+cose
        cd=json.dumps({"type":typ,"challenge":ch,"origin":origin}).encode()
        return {"clientDataJSON":b64u(cd),"attestationObject":b64u(cb({"fmt":"none","attStmt":{},"authData":ad}))}
    def anmelden(s,ch,zaehler=None,flags=0x05,origin=ORIGIN,defekt=False):
        s.zaehler=zaehler if zaehler is not None else s.zaehler+1
        ad=RP+bytes([flags])+struct.pack(">I",s.zaehler)
        cd=json.dumps({"type":"webauthn.get","challenge":ch,"origin":origin}).encode()
        sig=s.key.sign(ad+hashlib.sha256(cd).digest(),ec.ECDSA(hashes.SHA256()))
        if defekt: sig=sig[:-1]+bytes([sig[-1]^1])
        return {"id":b64u(s.cid),"clientDataJSON":b64u(cd),"authenticatorData":b64u(ad),"signature":b64u(sig)}

kid,c=neuer_kunde("Pass"); g=Geraet()
chk("Passkey-Liste anfangs leer",c.get("/api/passkey").json()==[])
st=c.post("/api/passkey/registrieren/start").json()
chk("Start liefert Aufforderung, Seite und Gerätesperre-Pflicht",st["rp"]["id"]=="localhost" and len(st["challenge"])>=40 and st["authenticatorSelection"]["userVerification"]=="required",st)
chk("Falsche Webseite (origin) wird abgelehnt",c.post("/api/passkey/registrieren/fertig",json=g.registrieren(st["challenge"],origin="https://boese.example")).status_code==400)
st=c.post("/api/passkey/registrieren/start").json()
chk("Ohne Gerätesperre (UV fehlt) abgelehnt",c.post("/api/passkey/registrieren/fertig",json=g.registrieren(st["challenge"],flags=0x41)).status_code==400)
st=c.post("/api/passkey/registrieren/start").json()
chk("Falscher Typ abgelehnt",c.post("/api/passkey/registrieren/fertig",json=g.registrieren(st["challenge"],typ="webauthn.get")).status_code==400)
st=c.post("/api/passkey/registrieren/start").json()
r=c.post("/api/passkey/registrieren/fertig",json={**g.registrieren(st["challenge"]),"name":"Mein Testhandy"}); chk("Registrierung ok",r.status_code==200,r.text)
chk("Aufforderung nur einmal gültig (Wiederholung abgelehnt)",c.post("/api/passkey/registrieren/fertig",json=g.registrieren(st["challenge"])).status_code==400)
l=c.get("/api/passkey").json(); chk("Passkey steht in der Liste",len(l)==1 and l[0]["name"]=="Mein Testhandy")
st=c.post("/api/passkey/registrieren/start").json(); chk("Schon eingerichtetes Gerät wird ausgeschlossen",len(st["excludeCredentials"])==1)
chk("Einrichtung ist protokolliert",int(sql("select count(*) from audit_log where aktion='passkey_eingerichtet'"))==1)

# Anmeldung ohne Passwort
p=httpx.Client(base_url=B,headers=H)
s1=p.post("/api/passkey/login/start").json()
r=p.post("/api/passkey/login/fertig",json=g.anmelden(s1["challenge"])); chk("Anmeldung per Passkey ok",r.status_code==200 and r.json()["ziel"]=="/app",r.text)
chk("Danach angemeldet",p.get("/api/me").status_code==200 and p.get("/api/me").json()["kunden_id"]==kid)
chk("Sitzung ist als Passkey-Sitzung vermerkt",sql("select count(*) from sitzungen where passkey")=="1")
s2=p.post("/api/passkey/login/start").json()
r=httpx.Client(base_url=B,headers=H).post("/api/passkey/login/fertig",json=g.anmelden(s2["challenge"],zaehler=1)); chk("Zähler nicht größer (Kopie): abgelehnt",r.status_code==401,r.text)
s3=p.post("/api/passkey/login/start").json()
chk("Gefälschte Signatur abgelehnt",httpx.post(B+"/api/passkey/login/fertig",headers=H,json=g.anmelden(s3["challenge"],defekt=True)).status_code==401)
s4=p.post("/api/passkey/login/start").json(); ok=g.anmelden(s4["challenge"])
chk("Ohne Gerätesperre abgelehnt",httpx.post(B+"/api/passkey/login/fertig",headers=H,json=g.anmelden(s4["challenge"],flags=0x01)).status_code==401)
chk("Falsche Webseite abgelehnt",httpx.post(B+"/api/passkey/login/fertig",headers=H,json=g.anmelden(s4["challenge"],origin="https://boese.example")).status_code==401)
s5=p.post("/api/passkey/login/start").json(); wert=g.anmelden(s5["challenge"])
chk("Erfundene Aufforderung abgelehnt",httpx.post(B+"/api/passkey/login/fertig",headers=H,json=g.anmelden(b64u(secrets.token_bytes(32)))).status_code==401)
r1=httpx.post(B+"/api/passkey/login/fertig",headers=H,json=wert); r2=httpx.post(B+"/api/passkey/login/fertig",headers=H,json=wert)
chk("Gleiche Antwort zweimal: nur einmal gültig",r1.status_code==200 and r2.status_code==401,(r1.status_code,r2.status_code))
chk("Unbekanntes Gerät abgelehnt",httpx.post(B+"/api/passkey/login/fertig",headers=H,json=Geraet().anmelden(p.post("/api/passkey/login/start").json()["challenge"])).status_code==401)
chk("Anmeldung protokolliert",int(sql("select count(*) from audit_log where aktion='login_passkey'"))>=2)

# Zwei-Faktor-Pflicht: Passkey zählt, Passwort allein nicht
a.put("/api/admin/sicherheit",json={"kunden_2fa":True})
pw=httpx.Client(base_url=B,headers=H); pw.post("/api/login",json={"email":f"pass{sfx}@k.de","password":"InhaberPasswort1"})
chk("Pflicht an: Passwort allein reicht nicht",pw.get("/api/kunde/start").status_code==403)
sx=httpx.Client(base_url=B,headers=H); g.zaehler+=5; sx.post("/api/passkey/login/fertig",json=g.anmelden(sx.post("/api/passkey/login/start").json()["challenge"]))
chk("Pflicht an: Passkey-Anmeldung zählt als Zwei-Faktor",sx.get("/api/kunde/start").status_code==200 and sx.get("/api/me").json()["zwei_faktor_pflicht"] is False)
a.put("/api/admin/sicherheit",json={"kunden_2fa":False})

# Entfernen
pid=l[0]["id"]; chk("Fremder kann Passkey nicht löschen",httpx.Client(base_url=B,headers=H).delete(f"/api/passkey/{pid}").status_code==401)
kid2,c2=neuer_kunde("Pass2"); chk("Anderer Kunde: 404",c2.delete(f"/api/passkey/{pid}").status_code==404)
chk("Entfernen ok",c.delete(f"/api/passkey/{pid}").status_code==200 and c.get("/api/passkey").json()==[])
chk("Nach Entfernen keine Anmeldung mehr",httpx.post(B+"/api/passkey/login/fertig",headers=H,json=g.anmelden(httpx.post(B+"/api/passkey/login/start",headers=H).json()["challenge"])).status_code==401)
# CBOR-Leser gegen Müll
try: passkey.cbor(b"\xff\xff"); ok=False
except passkey.PasskeyFehler: ok=True
chk("Müll-Antwort wirft sauberen Fehler",ok)
