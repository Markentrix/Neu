"""Mail-Layout für Kunden-Mails: Logo, Signatur, Tabelle, Knopf; Absage-Seite mit Logo."""
import httpx, time, re, email, email.header, subprocess
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
sfx=str(int(time.time())+500)
mk=f"exp{sfx}@k.de"
import sys
sys.path.insert(0,"/home/claude/markentrix-server/portal")
PNG="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
mk=f"ml{sfx}@k.de"
k=a.post("/api/admin/kunden",json={"firma":f"Glanz {sfx}","ansprechpartner":"Tina Test","email":mk,"telefon":"0511","strasse":"Weg 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE","einladen":True}).json(); kid=k["id"]
httpx.post(B+"/api/einladung",headers=H,json={"token":token(mk),"password":"InhaberPasswort1"})
c=httpx.Client(base_url=B,headers=H); assert c.post("/api/login",json={"email":mk,"password":"InhaberPasswort1"}).status_code==200
# ---- reine Umwandlung (Text aus dem echten Fall: Terminanfrage ElbDetail)
from app import mailvorlage as mv
URLX="https://portal.markentrix.de/site/mk_aT4qQSJav4QB/termin/absagen?t=rpN-5Kgh5O0yq9zrgmRC_XupTyaokpE5"
T=(f"Guten Tag Test,\n\nvielen Dank, Ihre Terminanfrage ist bei uns eingegangen. Ihre Vorgangsnummer: T261024-0101.\nIhr Wunschtermin 27.10.2026 um 08:00 Uhr ist für Sie vorgemerkt. Wir prüfen ihn und melden uns mit der Bestätigung.\n"
   f"Falls Sie nicht können, sagen Sie bitte hier ab:\n{URLX}\n\nIhre Angaben:\nPaket: Winter\nUhrzeit: 08:00\nE-Mail: info@markentrix.de\n\nNachricht:\nTest laufen\n\nMit freundlichen Grüßen\nElbdetail")
h_=mv.html_mail("Elbdetail",T,None,"#0a7d4f",None)
chk("HTML: Absage als Knopf mit Beschriftung",'>Termin absagen</a>' in h_ and f'href="{URLX}"' in h_,h_[:400])
chk("HTML: langer Link nicht als Fließtext sichtbar",URLX not in re.sub(r'href="[^"]*"','',h_))
chk("HTML: Angaben als Tabelle",'<table' in h_ and 'Paket</td>' in h_ and 'Uhrzeit</td>' in h_ and '>Winter<' in h_)
chk("HTML: Überschriften Ihre Angaben / Nachricht",'Ihre Angaben' in h_ and '>Nachricht<' in h_)
chk("HTML: Signatur mit Firma, doppelter Gruß entfernt",h_.count("Mit freundlichen Grüßen")==1 and "Elbdetail" in h_)
chk("HTML: Kopf mit Firmenname und Markenfarbe ohne Logo",'font-size:20px' in h_ and '#0a7d4f' in h_)
chk("HTML: Signatur-Block mit Farbstreifen",'border-top:3px solid #0a7d4f' in h_ and 'Elbdetail' in h_)
h2=mv.html_mail("Elbdetail",T,"Mit freundlichen Grüßen\nElbdetail\nBeispielweg 1\n21423 Winsen",None,"logo@mail")
chk("HTML: eigene Signatur, Logo in der Signatur (links), Linie dazwischen",'Beispielweg 1' in h2 and h2.count('cid:logo@mail')==1 and 'border-left:1px solid' in h2 and h2.count("Mit freundlichen Grüßen")==1)
SIGK="Mit freundlichen Grüßen\nReifen & Autoservice Koops GmbH\nKFZ-Meisterbetrieb\n\nTel. 05141 / 86061\nE-Mail: premio@koops-celle.de\nWeb: celle-koops.premio.de"
EX={"bewertung_link":"https://g.page/r/abc/review","facebook":"https://facebook.com/x","instagram":"https://instagram.com/x","hinweis":"Vertraulich <b>nicht</b> weitergeben."}
h3=mv.html_mail("Koops",T,SIGK,"#f2c500","logo@mail",EX)
chk("Signatur: Firmenname fett, Telefon/Mail/Web anklickbar",'href="tel:051418 6061"'.replace("051418 6061","0514186061") in h3 and 'mailto:premio@koops-celle.de' in h3 and 'href="https://celle-koops.premio.de"' in h3 and '&amp;' in h3)
chk("Signatur: Bewertungs-Box, Facebook, Instagram, Hinweis (maskiert)",'Jetzt Google-Bewertung abgeben' in h3 and '>Facebook<' in h3 and '>Instagram<' in h3 and 'Vertraulich &lt;b&gt;nicht' in h3)
chk("Ohne Einstellung keine Box und keine Social-Links",'Google-Bewertung' not in h2 and 'Facebook' not in h2)
chk("Unsichere Links (javascript:, http) werden nicht übernommen",'javascript' not in mv.html_mail("K",T,None,None,None,{"facebook":"javascript:alert(1)","instagram":"http://x.de","bewertung_link":"javascript:x"}))
tx=mv.text_mit_signatur(T,"Koops",SIGK,EX); chk("Textfassung: Signatur, Bewertung, Social, Hinweis",tx.count("Mit freundlichen Grüßen")==1 and "Google-Bewertung abgeben: https://g.page" in tx and "Facebook: https://facebook.com/x" in tx and "Vertraulich" in tx)
TA=T+"\n\nNicht mehr gewünscht? Abmelden: https://portal.markentrix.de/bewertung/abmelden?t=abc123"
hn=mv.html_mail("K",TA,None,None,None); tn=mv.text_mit_signatur(TA,"K",None)
chk("Text nach dem Gruß (Abmeldelink) bleibt erhalten, HTML und Text",'bewertung/abmelden?t=abc123' in hn and 'bewertung/abmelden?t=abc123' in tn and tn.index("abmelden")>tn.index("Mit freundlichen"))
chk("HTML: Eingaben werden maskiert",'<script' not in mv.html_mail("X","Hallo\nName: <script>alert(1)</script>\nWert: b",None,None,None))
chk("Textfassung: eigene Signatur am Ende",mv.text_mit_signatur(T,"Elbdetail","Mit freundlichen Grüßen\nElbdetail\nBeispielweg 1").endswith("Beispielweg 1"))
chk("Mail an das Team (ohne Gruß) bekommt keine Signatur","Mit freundlichen" not in mv.html_mail("X","Neue Anfrage\n\nName: A\nE-Mail: a@b.de\n\n—\nSie können direkt auf diese E-Mail antworten.",None,None,None))
from app import routes_siteapi as rs
chk("Werte lesbar: Kürzel werden Text",rs._wert_schoen("tierhaare, flecken, kratzer")=="Tierhaare, Flecken, Kratzer" and rs._wert_schoen("ja")=="Ja" and rs._wert_schoen("email")=="E-Mail")
chk("Werte lesbar: Adressen und Zahlen bleiben",rs._wert_schoen("info@x.de")=="info@x.de" and rs._wert_schoen("27.10.2026")=="27.10.2026" and rs._wert_schoen("Winter")=="Winter")
chk("Beschriftungen für AGB und vorzeitigen Beginn",rs.LABELS["agb"]=="AGB akzeptiert" and "vorzeitig" in rs.LABELS)
# ---- Branding + Signatur + echte Testmail
r=a.put(f"/api/admin/kunden/{kid}/branding",json={"farbe":"#0a7d4f","logo_base64":PNG}); chk("Logo und Farbe hinterlegt",r.status_code==200,r.text)
d=c.get("/api/kunde/website-dienste").json(); sid=d["site_id"]
chk("Einstellungen liefern Signatur-Vorschlag aus Firmendaten",f"Glanz {sfx}" in d["mail"]["signatur_vorschlag"] and "Celle" in d["mail"]["signatur_vorschlag"],d["mail"])
sig=f"Mit freundlichen Grüßen\nIhr Glanz-Team\nWeg 1, 29221 Celle"
r=c.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":mk,"betreff":"","name":"","signatur":sig}); chk("Signatur gespeichert",r.status_code==200,r.text)
chk("Signatur wird wieder geliefert",c.get("/api/kunde/website-dienste").json()["mail"]["signatur"]==sig)
n0=len([m for m in mails() if mk in str(m["To"])])
r=c.post("/api/kunde/website-dienste/mail/test",json={"an":mk}); chk("Testmail geht raus",r.status_code==200,r.text)
time.sleep(1.5)
ms=[m for m in mails() if mk in str(m["To"]) and "Testnachricht" in str(m["Subject"])]
chk("Testmail angekommen",len(ms)>=1)
m=ms[-1]
typen=[p.get_content_type() for p in m.walk()]
chk("Mail hat Text- und HTML-Teil",("text/plain" in typen) and ("text/html" in typen),typen)
chk("Logo ist eingebettet (Bild-Teil mit Content-ID)",any(p.get_content_type()=="image/png" and p["Content-ID"] for p in m.walk()),typen)
html=[p for p in m.walk() if p.get_content_type()=="text/html"][0].get_payload(decode=True).decode()
txt=[p for p in m.walk() if p.get_content_type()=="text/plain"][0].get_payload(decode=True).decode()
chk("HTML verweist auf das eingebettete Logo",'src="cid:' in html)
chk("HTML und Text enthalten die eigene Signatur",("Ihr Glanz-Team" in html) and ("Ihr Glanz-Team" in txt) and html.count("Mit freundlichen")==1,txt[-200:])
chk("Beispielangaben als Tabelle",'Leistung</td>' in html)
# ---- Logo-Adresse für die Absage-Seiten
rl=httpx.get(B+f"/site/{sid}/logo"); chk("Logo-Adresse liefert das Bild",rl.status_code==200 and rl.headers["content-type"]=="image/png" and rl.content[:4]==b"\x89PNG",rl.status_code)
chk("Unbekannte Seiten-Kennung: 404",httpx.get(B+"/site/mk_Unbekannt1234/logo").status_code==404)
chk("Ungültige Kennung: 404",httpx.get(B+"/site/mk_ab/logo").status_code==404)
a.put(f"/api/admin/kunden/{kid}/branding",json={"farbe":"#0a7d4f","logo_entfernen":True})
chk("Ohne Logo: 404",httpx.get(B+f"/site/{sid}/logo").status_code==404)
# Mail ohne Logo: Firmenname im Kopf, keine Bild-Teile
time.sleep(0.5); c.post("/api/kunde/website-dienste/mail/test",json={"an":mk}); time.sleep(1.5)
m2=[m for m in mails() if mk in str(m["To"]) and "Testnachricht" in str(m["Subject"])][-1]
chk("Ohne Logo: kein Bild-Teil, Firmenname im Kopf",not any(p.get_content_type().startswith("image/") for p in m2.walk()) and f"Glanz {sfx}" in [p for p in m2.walk() if p.get_content_type()=="text/html"][0].get_payload(decode=True).decode())
# ---- neue Bausteine in den Einstellungen
r=c.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":mk,"signatur":sig,"facebook":"http://unsicher.de"}); chk("Facebook-Link ohne https wird abgelehnt (400)",r.status_code==400,r.text)
r=c.put("/api/kunde/website-dienste/mail",json={"aktiv":True,"empfaenger":mk,"signatur":sig,"facebook":"https://facebook.com/glanz","instagram":"https://instagram.com/glanz","hinweis":"Vertraulich.","bewertung":True}); chk("Bausteine gespeichert",r.status_code==200,r.text)
dd=c.get("/api/kunde/website-dienste").json()["mail"]; chk("Bausteine werden geliefert",dd["facebook"].endswith("/glanz") and dd["bewertung"] is True and dd["hinweis"]=="Vertraulich." and dd["bewertung_link_da"] is False,dd)
sql(f"update website_dienste set bew_link='https://g.page/r/glanz/review' where kunden_id='{kid}'")
c.post("/api/kunde/website-dienste/mail/test",json={"an":mk}); time.sleep(1.5)
m3=[m for m in mails() if mk in str(m["To"]) and "Testnachricht" in str(m["Subject"])][-1]
h3=[p for p in m3.walk() if p.get_content_type()=="text/html"][0].get_payload(decode=True).decode()
chk("Echte Mail: Bewertungs-Box, Facebook, Instagram und Hinweis",all(x in h3 for x in ("Jetzt Google-Bewertung abgeben","g.page/r/glanz/review",">Facebook<",">Instagram<","Vertraulich.")))
sql(f"update website_dienste set bew_link=null where kunden_id='{kid}'")
print("FERTIG")
