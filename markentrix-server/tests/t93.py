# Härtung des Root-Dienstes (bin/worker.py): Symlinks im Auftragsordner, Upload-Austausch, Caddy-Prüfung
import json, os, pathlib, subprocess, tempfile, secrets
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
T=pathlib.Path(tempfile.mkdtemp(prefix="t93-")); BASE=T/"b"; S=T/"s"; CS=T/"caddy-ordner"; BIN=T/"bin"; LOG=T/"docker.log"; Q=BASE/"queue"
for d in (Q,BASE/"caddy"/"sites",S/"live",S/"demos",CS,BIN): d.mkdir(parents=True,exist_ok=True)
(BIN/"docker").write_text('#!/bin/sh\necho "$@" >> '+str(LOG)+'\ncase "$*" in *validate*) [ -n "$STUB_UNGUELTIG" ] && { echo "Error: adapting config using caddyfile: ambiguous site definition: x.de" >&2; exit 1; } ;; esac\nexit 0\n'); (BIN/"docker").chmod(0o755)
(BASE/"mode").write_text("docker"); (BASE/"caddy-container").write_text("server-caddy-1"); (BASE/"caddy-sites-dir").write_text(str(CS))
def worker(**env):
    return subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":str(BASE),"MK_SITES":str(S),"PATH":str(BIN)+":"+os.environ["PATH"],**env},capture_output=True,text=True)
def hoch(name,uid=None,inhalt=None,**env):
    uid=uid or secrets.token_hex(8); st=S/"live"/f".upload-{uid}"; st.mkdir(); (st/"index.html").write_text("<h1>x</h1>")
    if inhalt: inhalt(st)
    (Q/f"auftrag-{secrets.token_hex(8)}.json").write_text(json.dumps({"aktion":"veroeffentlichen","art":"live","name":name,"upload":uid,"kunde":"k"}))
    r=worker(**env); return uid,r
# 1. Symlink an der Stelle der Ergebnisdatei: der Root-Dienst darf nicht hindurchschreiben
ziel=T/"fremd.txt"; ziel.write_text("UNVERAENDERT")
uid=secrets.token_hex(8); os.symlink(ziel,Q/f"ergebnis-{uid}.json")
uid,r=hoch("sicher-eins.de",uid=uid)
chk("Symlink-Ziel unverändert",ziel.read_text()=="UNVERAENDERT",ziel.read_text())
e=Q/f"ergebnis-{uid}.json"
chk("Ergebnis ist jetzt eine normale Datei mit Inhalt",e.is_file() and not e.is_symlink() and json.loads(e.read_text())["ok"] is True,r.stdout+r.stderr)
chk("Datei gehört dem Portal-Benutzer 10001 und ist nicht schreibbar für andere",e.stat().st_uid==10001 and (e.stat().st_mode & 0o022)==0)
# 2. Symlink statt sicherungen.json / serverip.json
for n_ in ("sicherungen.json","serverip.json"):
    (Q/n_).unlink(missing_ok=True); os.symlink(ziel,Q/n_)
worker()
chk("sicherungen.json / serverip.json: Symlink-Ziel unverändert",ziel.read_text()=="UNVERAENDERT")
chk("sicherungen.json ist danach eine normale Datei",(Q/"sicherungen.json").is_file() and not (Q/"sicherungen.json").is_symlink())
chk("Keine .tmp-Reste im Auftragsordner",not list(Q.glob(".tmp-*")))
# 3. Upload landet im privaten Ordner, Zwischenordner im Portal-Bereich ist danach weg
uid,r=hoch("sicher-zwei.de")
chk("Veröffentlicht",(S/"live"/"sicher-zwei.de"/"index.html").is_file(),r.stdout+r.stderr)
chk("Zwischenordner im Portal-Bereich weg",not (S/"live"/f".upload-{uid}").exists())
chk("Veröffentlichte Dateien gehören root",(S/"live"/"sicher-zwei.de"/"index.html").stat().st_uid==0)
chk("Privater Ordner nur für root",(S/".privat").is_dir() and ((S/".privat").stat().st_mode & 0o077)==0)
# 4. Symlink im Upload wird abgelehnt, nichts bleibt liegen
uid,r=hoch("sicher-drei.de",inhalt=lambda st: os.symlink("/etc/passwd",st/"link.txt"))
e=json.loads((Q/f"ergebnis-{uid}.json").read_text())
chk("Symlink im Upload: abgelehnt",e["ok"] is False and not (S/"live"/"sicher-drei.de").exists(),e)
chk("Nichts liegen geblieben",not list((S/"live").glob(".upload-*")) and not list((S/".privat").glob("upload-*")))
# 4b. Symlink als Zwischenordner selbst
uid=secrets.token_hex(8); os.symlink(T/"s"/"demos",S/"live"/f".upload-{uid}")
(Q/f"auftrag-{secrets.token_hex(8)}.json").write_text(json.dumps({"aktion":"veroeffentlichen","art":"live","name":"sicher-vier.de","upload":uid,"kunde":"k"})); worker()
e=json.loads((Q/f"ergebnis-{uid}.json").read_text())
chk("Zwischenordner als Symlink: abgelehnt, Ziel nicht angefasst",e["ok"] is False and (S/"demos").is_dir() and not (S/"live"/"sicher-vier.de").exists(),e)
# 5. Caddy lehnt die neue Datei erkennbar ab -> Datei wird nicht behalten, Seite online mit deutlicher Warnung
uid,r=hoch("sicher-fuenf.de",STUB_UNGUELTIG="1")
e=json.loads((Q/f"ergebnis-{uid}.json").read_text())
chk("Abgelehnte Caddy-Datei wird entfernt",not (CS/"sicher-fuenf.de.caddy").exists(),e)
chk("Meldung nennt den Grund deutlich",e["ok"] is True and "ACHTUNG" in e["text"] and "abgelehnt" in e["text"],e)
# 6. Validierung ok -> Datei bleibt
uid,r=hoch("sicher-sechs.de")
chk("Gültige Caddy-Datei bleibt",(CS/"sicher-sechs.de.caddy").is_file())
chk("Es wurde vorher validiert","caddy validate" in LOG.read_text(),LOG.read_text())
# 7. Skripte
for f in ("bin/mkctl","install.sh"): chk(f+" Syntax",subprocess.run(["bash","-n","/home/claude/markentrix-server/"+f]).returncode==0)
inst=open("/home/claude/markentrix-server/install.sh").read()
chk("install.sh gibt veröffentlichte Dateien nicht mehr rekursiv an das Portal",'chown -R 10001:10001 "$SITES/live"' not in inst)
mk=open("/home/claude/markentrix-server/bin/mkctl").read()
chk("mkctl site-add lehnt www. ab","www.*" in mk)
print("FERTIG")
