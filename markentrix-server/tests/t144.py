"""Kundenseiten: Sicherheits-Kopfzeilen im Caddy-Eintrag, Nachrüsten alter Einträge, Testmodus und scharfer Modus."""
import os, sys, tempfile, shutil, subprocess
from pathlib import Path
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
REPO=os.path.dirname(os.environ["PYTHONPATH"]); sys.path.insert(0,REPO+"/bin")
T=Path(tempfile.mkdtemp()); (T/"cs").mkdir(); (T/"base").mkdir()
os.environ["MK_BASE"]=str(T/"base"); (T/"base"/"caddy-sites-dir").write_text(str(T/"cs")); (T/"base"/"mode").write_text("host")
sys.dont_write_bytecode = True
import worker
worker.BASE=T/"base"; worker.caddy_gueltig=lambda: True; worker.reload_caddy=lambda: True; worker.log=lambda *a,**k: None
ref=[l.strip() for l in open(REPO+"/docs/CADDY-KUNDEN-KOPFZEILEN.md").read().splitlines()]
c=worker.caddy_inhalt("neu.de")
for n in ("Strict-Transport-Security","X-Content-Type-Options","X-Frame-Options","Referrer-Policy","Permissions-Policy","Content-Security-Policy-Report-Only"):
    chk(f"Neuer Eintrag sendet {n}",f"\t\t{n} " in c)
chk("Server-Kopfzeile wird entfernt","\t\t-Server\n" in c)
chk("Standard ist der Testmodus (nur melden)","Content-Security-Policy-Report-Only" in c and '\t\tContent-Security-Policy "' not in c)
chk("Website-API und Dateien bleiben im Eintrag","handle /api/*" in c and "file_server" in c and "try_files" in c)
chk("PayPal-Quote richtig maskiert",'payment=(self \\"https://www.paypal.com\\")' in c)
chk("CSP erlaubt das Portal und Google/PayPal wie in der Vorgabe","script-src 'self' https://portal.markentrix.de https://www.googletagmanager.com https://www.paypal.com" in c and "frame-ancestors 'self'" in c)
# Alte Einträge werden nachgerüstet, von Hand geänderte nicht
(T/"cs"/"alt.de.caddy").write_text(worker.caddy_inhalt("alt.de",2))
(T/"cs"/"v1.de.caddy").write_text(worker.caddy_inhalt("v1.de",1))
(T/"cs"/"hand.de.caddy").write_text(worker.caddy_inhalt("hand.de",2)+"# eigene Änderung\n")
(T/"cs"/"neu.de.caddy").write_text(c)
worker.caddy_nachruesten()
chk("Alter Standard-Eintrag (Version 2) bekommt die Kopfzeilen",(T/"cs"/"alt.de.caddy").read_text()==worker.caddy_inhalt("alt.de"))
chk("Ältester Eintrag (Version 1) bekommt Kopfzeilen und Website-API",(T/"cs"/"v1.de.caddy").read_text()==worker.caddy_inhalt("v1.de"))
chk("Von Hand geänderter Eintrag bleibt unangetastet","Content-Security" not in (T/"cs"/"hand.de.caddy").read_text() and "eigene Änderung" in (T/"cs"/"hand.de.caddy").read_text())
# Scharf schalten
(T/"base"/"kunden-csp").write_text("scharf\n"); worker.caddy_nachruesten()
s=(T/"cs"/"alt.de.caddy").read_text()
chk("Scharf: Content-Security-Policy ohne Report-Only",'\t\tContent-Security-Policy "' in s and "Report-Only" not in s,s[:300])
chk("Scharf: auch bereits nachgerüstete Dateien werden umgestellt",'\t\tContent-Security-Policy "' in (T/"cs"/"neu.de").with_suffix(".de.caddy").read_text())
(T/"base"/"kunden-csp").write_text("testen\n"); worker.caddy_nachruesten()
chk("Zurück auf Testmodus",'Report-Only' in (T/"cs"/"alt.de.caddy").read_text())
# Ablehnung durch Caddy: alte Fassung bleibt
worker.caddy_gueltig=lambda: False; (T/"cs"/"abg.de.caddy").write_text(worker.caddy_inhalt("abg.de",2)); worker.caddy_nachruesten()
chk("Lehnt Caddy die neue Fassung ab, bleibt die alte",(T/"cs"/"abg.de.caddy").read_text()==worker.caddy_inhalt("abg.de",2))
# mkctl kunden-csp
env=dict(os.environ,MK_BASE=str(T/"base"))
shutil.rmtree(T)
