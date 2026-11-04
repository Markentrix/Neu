# Abholdienst für Sicherungen (bin/backup-abholen.sh): nur feste Befehle, nur fertige Sicherungen, keine Einschleusung
import subprocess, os, tempfile, hashlib, io, tarfile
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
REPO=os.environ.get("MK_REPO","/home/claude/markentrix-server")
d=tempfile.mkdtemp(); b=d+"/b"
for n,fertig in (("2026-11-03_0315",True),("2026-11-04_0315",True),("2026-11-05_0315",False)):
    os.makedirs(f"{b}/{n}"); open(f"{b}/{n}/markentrix-db.sql.gz","wb").write(os.urandom(2000))
    if fertig: open(f"{b}/{n}/config.tar.gz","wb").write(b"cfg")
os.makedirs(b+"/zzz")
os.symlink("/etc",b+"/2026-11-06_0315")
src=open(REPO+"/bin/backup-abholen.sh").read()
assert "\nB=/opt/markentrix/backups\n" in src
open(d+"/ab.sh","w").write(src.replace("\nB=/opt/markentrix/backups\n",f"\nB={b}\n")); os.chmod(d+"/ab.sh",0o755)
def r(a): p=subprocess.run([d+"/ab.sh",a],capture_output=True); return p.returncode,p.stdout,p.stderr.decode()
rc,o,_=r("liste"); chk("Liste: nur fertige Sicherungen, ohne unfertige und Symlinks",rc==0 and o.decode().split()==["2026-11-03_0315","2026-11-04_0315"],o)
rc,o,_=r("holen 2026-11-04_0315"); t=tarfile.open(fileobj=io.BytesIO(o)); chk("Holen liefert gültiges Tar mit allen Dateien",rc==0 and sorted(t.getnames())==["2026-11-04_0315","2026-11-04_0315/config.tar.gz","2026-11-04_0315/markentrix-db.sql.gz"],t.getnames())
rc,h,_=r("hash 2026-11-04_0315"); chk("Prüfsumme passt zum gelieferten Strom (zweimal gleich)",rc==0 and h.decode().strip()==hashlib.sha256(o).hexdigest(),h)
rc,g,_=r("groesse 2026-11-04_0315"); chk("Größe wird geliefert",rc==0 and int(g)>2000,g)
for a in ("holen 2026-11-05_0315","hash 2026-11-05_0315"): chk(f"Unfertige Sicherung wird nicht herausgegeben ({a.split()[0]})",r(a)[0]==3)
chk("Symlink wird nicht herausgegeben",r("holen 2026-11-06_0315")[0]==3)
for a in ("holen ../etc","holen /etc/passwd","holen *","holen $(id)","holen 2026-11-04_0315; id","holen 2026-11-04_0315 extra","rm -rf /","id","","liste extra","holen 2026-11-04_0315\nid","holen `id`"):
    rc,o,e=r(a); chk(f"Abgelehnt: {a!r}",rc!=0 and not o,(rc,o[:50],e))
