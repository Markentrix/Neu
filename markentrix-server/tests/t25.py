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
from app import routes_zahlung, routes_fruehwarnung
import os
def lead(firma,**kw):
    i=a.post("/api/admin/leads",json={"firma":f"{firma} {sfx}","telefon":"0511 5555","ort":"Celle",**kw}).json()["id"]; return i
p=a.post("/api/admin/vertrieb/partner",json={"name":"Vera Vertrieb","email":f"vera{sfx}@v.de","status":"aktiv","einladen":True}).json()["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(f"vera{sfx}@v.de"),"password":"VeraPasswort123"})
v=httpx.Client(base_url=B,headers=H); assert v.post("/api/login",json={"email":f"vera{sfx}@v.de","password":"VeraPasswort123"}).status_code==200

import xml.etree.ElementTree as ET
from datetime import date, timedelta

# ================= 1. Frühwarnung
chk("bewerten: gesunder Kunde",routes_fruehwarnung.bewerten({"login":None.__class__ and __import__("datetime").datetime.now(__import__("datetime").timezone.utc),"a30":5,"a60":5,"ueberfaellig":0,"mahnstufe":0,"letzte_punkte":9,"ticket_wartet":0})[0]==0)
kid,c,kmail=neuer_kunde("Alpha")
sql(f"update kunden set status='aktiv', erstellt_am=now()-interval '90 days' where id='{kid}'")
gid_,c2,kmail2=neuer_kunde("Gesund")
sql(f"update kunden set status='aktiv', erstellt_am=now()-interval '90 days' where id='{gid_}'")
sql(f"update benutzer set letzter_login=now()-interval '60 days' where kunden_id='{kid}'")
sql(f"update benutzer set letzter_login=now() where kunden_id='{gid_}'")
sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht) select '{kid}','Alt','x','y' from generate_series(1,3)")
sql(f"update anfragen set erstellt_am=now()-interval '40 days' where kunden_id='{kid}'")
sql(f"insert into zufriedenheit (kunden_id,art,punkte) values ('{kid}','quartal',3)")
fw=a.get("/api/admin/fruehwarnung").json()
mein=[k for k in fw["kunden"] if str(k["id"])==kid]
chk("Frühwarnung: Risikokunde gelistet, hoch",len(mein)==1 and mein[0]["stufe"]=="hoch",fw)
txt=" ".join(mein[0]["gruende"]) if mein else ""
chk("Gründe: Login, Anfragen, Zufriedenheit","nicht mehr im Portal" in txt and "Keine Anfragen" in txt and "3 von 10" in txt,txt)
chk("Gesunder Kunde nicht gelistet",not any(str(k["id"])==gid_ for k in fw["kunden"]))
chk("Kunde kein Zugriff auf Frühwarnung",c.get("/api/admin/fruehwarnung").status_code==403)

# ================= 2. Lastschrift
chk("Mandat vor Einrichtung nicht verfügbar",c.get("/api/kunde/lastschrift").json()["verfuegbar"]==False)
f=a.get("/api/admin/einstellungen/firma").json(); f["name"]=f["name"] or "Markentrix Test"; f["iban"]="DE02120300000000202051"; f["bic"]="BYLADEM1001"; f.update({"strasse":"Weg 5","plz":"29221","ort":"Celle","steuernummer":"12/345/67890","email":"info@markentrix.de","inhaber":"Chris Test"})
chk("Firma mit IBAN",a.put("/api/admin/einstellungen/firma",json=f).status_code==200)
chk("Gläubiger-ID ungültig abgelehnt",a.put("/api/admin/einstellungen/zahlung",json={"glaeubiger_id":"XYZ","vorab_tage":3}).status_code==400)
chk("Fristen müssen aufsteigend sein",a.put("/api/admin/einstellungen/zahlung",json={"glaeubiger_id":"","vorab_tage":3,"tage_1":10,"tage_2":5,"tage_3":20}).status_code==400)
chk("Zahlung speichern",a.put("/api/admin/einstellungen/zahlung",json={"glaeubiger_id":"de98 zzz09999999999","vorab_tage":3,"mahn_aktiv":False}).status_code==200)
r=a.get("/api/admin/einstellungen/zahlung").json(); chk("Gläubiger-ID normalisiert",r["lastschrift"]["glaeubiger_id"]=="DE98ZZZ09999999999" and r["lastschrift"]["iban_da"],r)
m=c.get("/api/kunde/lastschrift").json(); chk("Mandat jetzt verfügbar, mit Text",m["verfuegbar"] and "SEPA-Basislastschrift" in m["text"] and m["mandat"] is None,m)
P={"kontoinhaber":"Tina Test","iban":"DE89 3704 0044 0532 0130 00","bic":"","zustimmung":True}
chk("Ungültige IBAN",c.post("/api/kunde/lastschrift",json={**P,"iban":"DE89370400440532013001"}).status_code==400)
chk("Ohne Zustimmung",c.post("/api/kunde/lastschrift",json={**P,"zustimmung":False}).status_code==400)
r=c.post("/api/kunde/lastschrift",json=P); chk("Mandat erteilt",r.status_code==200 and r.json()["referenz"].startswith("MK-"),r.text); ref=r.json()["referenz"]
chk("Mandatsbestätigung per Mail",len(mail_an(kmail,"SEPA-Lastschriftmandat"))>=1 and ref in text(mail_an(kmail,"SEPA-Lastschriftmandat")[-1]))
chk("IBAN verschlüsselt gespeichert",sql(f"select position('DE89' in iban_verschluesselt) from sepa_mandate where kunden_id='{kid}' and widerrufen_am is null")=="0")
chk("Nur Endziffern sichtbar",c.get("/api/kunde/lastschrift").json()["mandat"]["iban_ende"]=="3000")
# Rechnung
b=a.post(f"/api/admin/kunden/{kid}/belege",json={"art":"rechnung","betreff":"Website","positionen":[{"text":"Einrichtung Müller & Söhne","menge":1,"einheit":"","preis_cent":10000}]}).json()["id"]
chk("Rechnung ausstellen",a.post(f"/api/admin/belege/{b}/ausstellen").status_code==200)
nr=sql(f"select nummer from belege where id='{b}'")
l=a.get("/api/admin/lastschrift").json(); chk("Rechnung bereit zum Einzug",[x["id"] for x in l["bereit"]]==[b] and l["konfiguriert"],l)
morgen=date.today()+timedelta(days=4)
while morgen.weekday()>=5: morgen+=timedelta(days=1)
chk("Zu kurzfristig abgelehnt",a.post("/api/admin/lastschrift/export",json={"beleg_ids":[b],"einzug_am":str(date.today())}).status_code==400)
wochenende=date.today()+timedelta(days=4)
while wochenende.weekday()!=5: wochenende+=timedelta(days=1)
chk("Wochenende abgelehnt",a.post("/api/admin/lastschrift/export",json={"beleg_ids":[b],"einzug_am":str(wochenende)}).status_code==400)
chk("Kunde darf nicht exportieren",c.post("/api/admin/lastschrift/export",json={"beleg_ids":[b],"einzug_am":str(morgen)}).status_code==403)
r=a.post("/api/admin/lastschrift/export",json={"beleg_ids":[b],"einzug_am":str(morgen)}); chk("Export ok, XML",r.status_code==200 and "xml" in r.headers["content-type"] and "attachment" in r.headers["content-disposition"],r.text[:200])
ns={"p":"urn:iso:std:iso:20022:tech:xsd:pain.008.001.02"}
try:
    x=ET.fromstring(r.content); ok=True
except Exception as e: ok=False; x=None
chk("XML wohlgeformt",ok)
if ok:
    g=lambda p:x.find(p,ns)
    chk("Anzahl und Summe",g(".//p:GrpHdr/p:NbOfTxs").text=="1" and g(".//p:GrpHdr/p:CtrlSum").text=="119.00",r.text[:400])
    chk("Folgeart FRST beim ersten Einzug",g(".//p:PmtInf/p:PmtTpInf/p:SeqTp").text=="FRST")
    chk("Einzugsdatum",g(".//p:ReqdColltnDt").text==str(morgen))
    chk("Gläubiger-ID, Gläubiger-IBAN",g(".//p:CdtrSchmeId//p:Othr/p:Id").text=="DE98ZZZ09999999999" and g(".//p:CdtrAcct//p:IBAN").text=="DE02120300000000202051")
    chk("Schuldner-IBAN entschlüsselt",g(".//p:DbtrAcct//p:IBAN").text=="DE89370400440532013000")
    chk("Mandatsreferenz und Verwendungszweck",g(".//p:MndtId").text==ref and nr in g(".//p:Ustrd").text and g(".//p:EndToEndId").text==nr)
    chk("Umlaute SEPA-konform",g(".//p:Dbtr/p:Nm").text=="Tina Test")
chk("Beleg als angekündigt markiert",sql(f"select zahlart||'|'||einzug_am from belege where id='{b}'")==f"lastschrift|{morgen}")
vm=mail_an(kmail,"Ankündigung Lastschrift"); chk("Vorabankündigung per Mail",len(vm)==1 and "119,00" in text(vm[0]) and ref in text(vm[0]) and "DE98ZZZ09999999999" in text(vm[0]),[text(m) for m in vm])
chk("Zweiter Export derselben Rechnung abgelehnt",a.post("/api/admin/lastschrift/export",json={"beleg_ids":[b],"einzug_am":str(morgen)}).status_code==400)
l=a.get("/api/admin/lastschrift").json(); chk("Liste: angekündigt statt bereit",not l["bereit"] and [z["id"] for z in l["angekuendigt"]]==[b])
chk("Zurücksetzen",a.post("/api/admin/lastschrift/zuruecksetzen",json={"beleg_id":b}).status_code==200 and sql(f"select einzug_am is null from belege where id='{b}'")=="t")
chk("Zurücksetzen ohne Einzug: 404",a.post("/api/admin/lastschrift/zuruecksetzen",json={"beleg_id":b}).status_code==404)
r=a.post("/api/admin/lastschrift/export",json={"beleg_ids":[b],"einzug_am":str(morgen)}); x=ET.fromstring(r.content)
chk("Zweiter Einzug als Folgelastschrift (RCUR)",x.find(".//p:SeqTp",ns).text=="RCUR")
# Widerruf
chk("Widerruf löscht angekündigten Einzug",c.delete("/api/kunde/lastschrift").status_code==200 and sql(f"select einzug_am is null from belege where id='{b}'")=="t")
chk("Widerruf ohne Mandat: 404",c.delete("/api/kunde/lastschrift").status_code==404)
chk("Neues Mandat nach Widerruf",c.post("/api/kunde/lastschrift",json=P).status_code==200)
chk("Nur ein aktives Mandat",sql(f"select count(*) from sepa_mandate where kunden_id='{kid}' and widerrufen_am is null")=="1")

# ---- Zahlungserinnerungen
sql(f"update belege set faellig_am=current_date-10, mahnstufe=0, mahn_am=null where id='{b}'")
chk("Mahnlauf aus: nichts",routes_zahlung.mahnlauf()==[])
a.put("/api/admin/einstellungen/zahlung",json={"glaeubiger_id":"DE98ZZZ09999999999","vorab_tage":3,"mahn_aktiv":True,"tage_1":7,"tage_2":21,"tage_3":35})
sql(f"update belege set einzug_am=current_date+2, zahlart='lastschrift' where id='{b}'")
chk("Angekündigter Einzug wird nicht gemahnt",routes_zahlung.mahnlauf()==[])
sql(f"update belege set einzug_am=NULL, zahlart=NULL where id='{b}'")
res=routes_zahlung.mahnlauf(); chk("Stufe 1 verschickt",len(res)==1 and res[0][2]=="Zahlungserinnerung",res)
chk("Mail mit Zahlungserinnerung",len(mail_an(kmail,"Zahlungserinnerung"))>=1)
chk("Stufe 1 gespeichert",sql(f"select mahnstufe||'|'||(auto_gemahnt_am=current_date) from belege where id='{b}'")=="1|true")
chk("Kein Doppelversand am selben Tag",routes_zahlung.mahnlauf()==[])
sql(f"update belege set mahn_am=current_date-8, faellig_am=current_date-10 where id='{b}'")
chk("Stufe 2 erst nach 21 Tagen",routes_zahlung.mahnlauf()==[])
sql(f"update belege set mahn_am=current_date-8, faellig_am=current_date-25 where id='{b}'")
res=routes_zahlung.mahnlauf(); chk("Stufe 2 verschickt",len(res)==1 and res[0][2]=="1. Mahnung",res)
sql(f"update kunden set referenzkunde=true where id='{kid}'"); sql(f"update belege set mahn_am=current_date-8, faellig_am=current_date-60 where id='{b}'")
chk("Referenzkunden werden nicht gemahnt",routes_zahlung.mahnlauf()==[])
sql(f"update kunden set referenzkunde=false where id='{kid}'")
chk("Audit: automatische Mahnung",int(sql("select count(*) from audit_log where aktion='mahnung' and details->>'automatisch'='true'"))==2)

# ================= 3. Telefon
H2={}
chk("Webhook ohne Geheimnis: 401",httpx.post(B+f"/api/webhook/telefon/K",json={}).status_code==401)
g=a.post("/api/admin/einstellungen/telefon/neues-geheimnis").json()["geheimnis"]; chk("Geheimnis erzeugt",len(g)>=20)
knr=sql(f"select kundennummer from kunden where id='{kid}'")
chk("Falsches Geheimnis: 401",httpx.post(B+f"/api/webhook/telefon/{knr}?s=falsch",json={}).status_code==401)
chk("Einstellung zeigt Geheimnis nie",g not in a.get("/api/admin/einstellungen/telefon").text)
call={"data":{"call_id":"c-100","from_number":"+49511123456","caller_name":"Herr Meier","summary":"Möchte einen Termin für Dienstag.","duration":75,"direction":"inbound","outcome":"termin","ai_disclosure":True}}
r=httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",json=call); chk("Webhook ohne X-MK-Header akzeptiert",r.status_code==200 and r.json()["anfrage"]==True,r.text)
r=httpx.post(B+f"/api/webhook/telefon/{knr}",headers={"X-Webhook-Secret":g},json={**call,"data":{**call["data"],"call_id":"c-101","direction":"outbound"}}); chk("Ausgehend: Anruf ja, Anfrage nein",r.status_code==200 and r.json()["anfrage"]==False,r.text)
chk("Doppelter Anruf erkannt",httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",json=call).json().get("doppelt")==True)
chk("Unbekannte Kundennummer: 404",httpx.post(B+f"/api/webhook/telefon/K-NIX?s={g}",json=call).status_code==404)
chk("Kaputtes JSON: 400",httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",content=b"{nein",headers={"content-type":"application/json"}).status_code==400)
an=c.get("/api/kunde/anrufe").json(); chk("Anrufprotokoll: 2 Anrufe, Kennzahlen",len(an["anrufe"])==2 and an["woche"]==1,an)
e=[x for x in an["anrufe"] if x["richtung"]=="ein"][0]; chk("Felder übernommen",e["nummer"]=="+49511123456" and e["name"]=="Herr Meier" and e["dauer_sek"]==75 and "Dienstag" in e["zusammenfassung"] and e["ergebnis"]=="termin",e)
anf=c.get("/api/kunde/anfragen").json(); anf=anf if isinstance(anf,list) else anf.get("anfragen",anf)
chk("Anfrage aus Anruf mit Quelle telefon",any(x["quelle"]=="telefon" and "Dienstag" in x["nachricht"] and x["kontakt"]=="+49511123456" for x in anf),anf)
chk("KI-Hinweis übernommen",sql(f"select ki_hinweis_gegeben from anrufe where kunden_id='{kid}' and extern_ref='c-100'")=="t")
chk("Anrufe anderer Kunden nicht sichtbar",len(c2.get("/api/kunde/anrufe").json()["anrufe"])==0)
sql(f"update anrufe set beginn=now()-interval '200 days' where kunden_id='{kid}' and extern_ref='c-100'")
chk("Bereinigung entfernt Nummer/Name/Text nach 180 Tagen",jobs.anrufe_bereinigen()>=1 and sql(f"select coalesce(nummer,'-')||coalesce(name,'-')||coalesce(zusammenfassung,'-') from anrufe where extern_ref='c-100'")=="---")
sql(f"update kunden set status='gekuendigt' where id='{gid_}'")
chk("Gekündigter Kunde: 404",httpx.post(B+f"/api/webhook/telefon/{sql(f'select kundennummer from kunden where id=\'{gid_}\'')}?s={g}",json=call).status_code==404)

# ================= 4. Branchenvorlagen
vl=a.get("/api/admin/vorlagen").json(); chk("Vorlagen vorhanden",len(vl)>=6 and {"kfz","friseur","restaurant"}<=({v["code"] for v in vl}),vl)
k3,c3,_=neuer_kunde("Werkstatt")
sql(f"update kunden set ort='Celle' where id='{k3}'")
chk("Unbekannte Vorlage: 404",a.post(f"/api/admin/kunden/{k3}/vorlage",json={"code":"gibtsnicht"}).status_code==404)
chk("Unbekannter Kunde: 404",a.post("/api/admin/kunden/00000000-0000-0000-0000-000000000000/vorlage",json={"code":"kfz"}).status_code==404)
r=a.post(f"/api/admin/kunden/{k3}/vorlage",json={"code":"kfz"}); j=r.json(); chk("Vorlage angewendet",r.status_code==200 and j["wissen"]>=5 and j["beitraege"]==6 and j["aufgaben"]==4,r.text)
chk("Wissenseinträge inaktiv und als Vorlage markiert",sql(f"select count(*) from wissensbasis where kunden_id='{k3}' and quelle='vorlage' and not aktiv")==str(j["wissen"]))
chk("Beiträge als Entwurf, Platzhalter ersetzt",sql(f"select count(*) from content_beitraege where kunden_id='{k3}' and status='entwurf' and text not like '%{{firma}}%' and text not like '%{{ort}}%'")=="6" and "Celle" in sql(f"select string_agg(text,' ') from content_beitraege where kunden_id='{k3}'"))
chk("Aufgaben angelegt",sql(f"select count(*) from aufgaben where kunden_id='{k3}' and auto_schluessel like 'vorlage-kfz-%'")=="4")
chk("Kunde merkt sich Vorlage",a.get(f"/api/admin/kunden/{k3}").json()["kunde"]["vorlage"]=="kfz")
chk("Zweite Vorlage: 409",a.post(f"/api/admin/kunden/{k3}/vorlage",json={"code":"friseur"}).status_code==409)
with db.tx("admin") as cur:
    from app import onboarding
    chk("Onboarding 'Wissen' bleibt offen (inaktive Einträge zählen nicht)","wissen" not in onboarding.auto_erkannt(cur,k3))
chk("Kunde darf keine Vorlage anwenden",c3.post(f"/api/admin/kunden/{k3}/vorlage",json={"code":"kfz"}).status_code==403)
for code in ("friseur","restaurant","handwerk","einzelhandel","fitness"):
    kx,_,_=neuer_kunde("V"+code[:3]); chk(f"Vorlage {code}",a.post(f"/api/admin/kunden/{kx}/vorlage",json={"code":code}).status_code==200)

# ================= 5. Push
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
import base64, threading, http.server
b64=lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
unb64=lambda s: base64.urlsafe_b64decode(s+"="*(-len(s)%4))
EMPFANGEN=[]; CODE={"c":201}
class PS(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get("content-length",0)); EMPFANGEN.append({"pfad":self.path,"h":dict(self.headers),"body":self.rfile.read(n)})
        self.send_response(CODE["c"]); self.end_headers()
    def log_message(self,*a): pass
srv=http.server.HTTPServer(("127.0.0.1",8998),PS); threading.Thread(target=srv.serve_forever,daemon=True).start()
def neues_geraet(pfad):
    k=ec.generate_private_key(ec.SECP256R1()); auth=os.urandom(16)
    return k,auth,{"endpoint":f"http://127.0.0.1:8998/{pfad}","p256dh":b64(k.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)),"auth":b64(auth),"geraet":"Test"}
def entschluesseln(body,k,auth):
    salt,idl=body[:16],body[20]; as_pub=body[21:21+idl]; chiffre=body[21+idl:]
    ua_pub=k.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)
    gem=k.exchange(ec.ECDH(),ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(),as_pub))
    ikm=HKDF(hashes.SHA256(),32,auth,b"WebPush: info\x00"+ua_pub+as_pub).derive(gem)
    cek=HKDF(hashes.SHA256(),16,salt,b"Content-Encoding: aes128gcm\x00").derive(ikm); nonce=HKDF(hashes.SHA256(),12,salt,b"Content-Encoding: nonce\x00").derive(ikm)
    p=AESGCM(cek).decrypt(nonce,chiffre,None); assert p[-1]==2; return json.loads(p[:-1])
chk("Push ohne Login: 401",httpx.get(B+"/api/push/status").status_code==401)
st=v.get("/api/push/status").json(); chk("VAPID-Schlüssel (65 Byte öffentlich)",len(unb64(st["schluessel"]))==65 and st["geraete"]==0,st)
chk("Schlüssel bleibt stabil",v.get("/api/push/status").json()["schluessel"]==st["schluessel"])
chk("Push-Schlüssel verschlüsselt gespeichert","BEGIN PRIVATE" not in sql("select wert from portal_einstellungen where schluessel='push'"))
k1,au1,abo1=neues_geraet("geraet1")
chk("Anmeldung mit ungültigem Schlüssel: 400",v.post("/api/push/abo",json={**abo1,"p256dh":"@@@@@@@@@@@@@@@@@@@@@@@@"}).status_code==400)
chk("Anmeldung ok",v.post("/api/push/abo",json=abo1).status_code==200 and v.get("/api/push/status").json()["geraete"]==1)
chk("Doppelte Anmeldung ersetzt",v.post("/api/push/abo",json=abo1).status_code==200 and v.get("/api/push/status").json()["geraete"]==1)
# Auslöser: Leads dem Vertriebler zuweisen
l1=lead("Push Lead 1"); l2=lead("Push Lead 2")
r=a.post("/api/admin/leads/bulk",json={"aktion":"vertriebler","wert":p,"ids":[l1,l2]}); chk("Zuweisen",r.status_code==200,r.text)
time.sleep(2)
chk("Push beim Vertriebler angekommen",len(EMPFANGEN)==1,len(EMPFANGEN))
if EMPFANGEN:
    e=EMPFANGEN[0]; hd={k.lower():v_ for k,v_ in e["h"].items()}
    chk("Header: aes128gcm, TTL, VAPID",hd["content-encoding"]=="aes128gcm" and hd["ttl"]=="86400" and hd["authorization"].startswith("vapid t="),hd)
    nach=entschluesseln(e["body"],k1,au1); chk("Nutzlast entschlüsselbar",nach["titel"]=="Neue Leads" and "2 Lead" in nach["text"] and nach["url"].startswith("/vertrieb"),nach)
    chk("Keine Personennamen in der Nachricht","Push Lead" not in json.dumps(nach))
    t,k_=hd["authorization"][len("vapid "):].split(", ")
    jwt=t[2:]; kopf,claims,sig=jwt.split("."); pub=unb64(k_[2:]); chk("VAPID-Schlüssel stimmt mit Status überein",k_[2:]==st["schluessel"])
    cl=json.loads(unb64(claims)); chk("JWT: aud, exp, sub",cl["aud"]=="http://127.0.0.1:8998" and cl["exp"]>time.time() and cl["sub"].startswith("mailto:"),cl)
    pk=ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(),pub); s_=unb64(sig)
    try: pk.verify(encode_dss_signature(int.from_bytes(s_[:32],"big"),int.from_bytes(s_[32:],"big")),f"{kopf}.{claims}".encode(),ec.ECDSA(hashes.SHA256())); okv=True
    except Exception as ex: okv=False
    chk("JWT-Signatur (ES256) gültig",okv)
chk("Admin-Zuweisung an Fremde löst keinen Push aus",len(EMPFANGEN)==1)
# Testnachricht und Fehlerbehandlung
n0=len(EMPFANGEN); chk("Testnachricht",v.post("/api/push/test").status_code==200); time.sleep(1.5); chk("Testnachricht angekommen",len(EMPFANGEN)==n0+1)
CODE["c"]=410; v.post("/api/push/test"); time.sleep(1.5)
chk("Abgelaufenes Gerät (410) wird entfernt",v.get("/api/push/status").json()["geraete"]==0)
CODE["c"]=201
k2,au2,abo2=neues_geraet("geraet2"); v.post("/api/push/abo",json=abo2)
chk("Abmelden",v.post("/api/push/abmelden",json={"endpoint":abo2["endpoint"]}).status_code==200 and v.get("/api/push/status").json()["geraete"]==0)
# Gerät eines anderen Benutzers lässt sich nicht abmelden
k3_,au3,abo3=neues_geraet("geraet3"); v.post("/api/push/abo",json=abo3)
chk("Fremdes Gerät nicht abmeldbar",a.post("/api/push/abmelden",json={"endpoint":abo3["endpoint"]}).status_code==200 and v.get("/api/push/status").json()["geraete"]==1)
# Kunde: neue Anfrage-Push über Telefon-Webhook
kk,au4,abo4=neues_geraet("kunde1"); c.post("/api/push/abo",json=abo4); n0=len(EMPFANGEN)
httpx.post(B+f"/api/webhook/telefon/{knr}?s={g}",json={"call_id":"c-200","from_number":"+4951199","summary":"Rückruf bitte","direction":"inbound"}); time.sleep(2)
neu=[e for e in EMPFANGEN[n0:] if e["pfad"]=="/kunde1"]; chk("Kunde bekommt Push bei Anruf",len(neu)==1 and entschluesseln(neu[0]["body"],kk,au4)["titel"]=="Neuer Anruf")
# Kunde: Ticket -> Admin-Push
ka,au5,abo5=neues_geraet("admin1"); a.post("/api/push/abo",json=abo5); n0=len(EMPFANGEN)
c.post("/api/kunde/tickets",json={"betreff":"Frage","art":"frage","text":"Hallo, eine Frage zur Website.","prioritaet":"normal"}); time.sleep(2)
neu=[e for e in EMPFANGEN[n0:] if e["pfad"]=="/admin1"]; chk("Admin bekommt Push bei Kundennachricht",len(neu)==1 and entschluesseln(neu[0]["body"],ka,au5)["titel"]=="Neue Kundennachricht",len(neu))
# Job-Marker
chk("Job-Marker: nur einmal",jobs._marker("test-"+sfx) and not jobs._marker("test-"+sfx))
# PWA-Dateien
sw=httpx.get(B+"/sw.js"); chk("Service Worker mit Push-Handler",sw.status_code==200 and "addEventListener('push'" in sw.text and "notificationclick" in sw.text)
chk("Manifest erreichbar",httpx.get(B+"/manifest.webmanifest").status_code==200)

