import json, os, pathlib, subprocess, sys, tempfile, secrets
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
T=pathlib.Path(tempfile.mkdtemp(prefix="t65-")); BASE=T/"b"; S=T/"s"; CS=T/"caddy-ordner"; BIN=T/"bin"; LOG=T/"docker.log"
for d in (BASE/"queue",BASE/"caddy"/"sites",S/"live",S/"demos",CS,BIN): d.mkdir(parents=True,exist_ok=True)
(BIN/"docker").write_text('#!/bin/sh\necho "$@" >> '+str(LOG)+'\n[ -n "$STUB_FAIL" ] && { echo "boom" >&2; exit 1; }\nexit 0\n'); (BIN/"docker").chmod(0o755)
(BASE/"mode").write_text("docker"); (BASE/"caddy-container").write_text("server-caddy-1"); (BASE/"caddy-sites-dir").write_text(str(CS))
def worker(**env):
    return subprocess.run(["python3","/home/claude/markentrix-server/bin/worker.py"],env={**os.environ,"MK_BASE":str(BASE),"MK_SITES":str(S),"PATH":str(BIN)+":"+os.environ["PATH"],**env},capture_output=True,text=True)
def veroeffentlichen(name,**env):
    uid=secrets.token_hex(8); st=S/"live"/f".upload-{uid}"; st.mkdir(); (st/"index.html").write_text("<h1>x</h1>")
    (BASE/"queue"/f"auftrag-{secrets.token_hex(8)}.json").write_text(json.dumps({"aktion":"veroeffentlichen","art":"live","name":name,"upload":uid,"kunde":"k"}))
    r=worker(**env); e=json.loads((BASE/"queue"/f"ergebnis-{uid}.json").read_text()); return r,e
def log(): return LOG.read_text() if LOG.exists() else ""
r,e=veroeffentlichen("neu-test.de")
chk("Veröffentlichen klappt",e["ok"] is True,e)
chk("Domain-Datei liegt im Ordner des vorhandenen Caddy",(CS/"neu-test.de.caddy").is_file())
chk("Nicht im eigenen Ordner",not (BASE/"caddy"/"sites"/"neu-test.de.caddy").exists())
chk("Inhalt: beide Hosts, Website-API, Ordner",all(x in (CS/"neu-test.de.caddy").read_text() for x in ("neu-test.de, www.neu-test.de","siteapi","/srv/sites/live/neu-test.de")))
chk("Caddy-Container wurde neu geladen","exec server-caddy-1 caddy reload --config /etc/caddy/Caddyfile" in log(),log())
chk("Erfolgsmeldung ohne Warnung","ACHTUNG" not in e["text"],e["text"])
n=log().count("reload")
r,e=veroeffentlichen("neu-test.de"); chk("Erneutes Hochladen: Datei bleibt, kein weiterer Reload nötig",e["ok"] and log().count("reload")==n and "Veröffentlicht" in e["text"],e)
r,e=veroeffentlichen("zweite-seite.de",STUB_FAIL="1")
chk("Reload fehlgeschlagen: Seite trotzdem veröffentlicht, aber deutliche Warnung",e["ok"] is True and "ACHTUNG" in e["text"] and "mkctl caddy-neu" in e["text"],e)
chk("Datei liegt trotzdem da (mkctl caddy-neu kann nachladen)",(CS/"zweite-seite.de.caddy").is_file())
v=log().count("reload")
(BASE/"queue"/f"auftrag-{secrets.token_hex(8)}.json").write_text(json.dumps({"aktion":"caddy_neu_laden"})); worker()
chk("Auftrag caddy_neu_laden löst Reload aus",log().count("reload")==v+1,log())
(BASE/"caddy-container").write_text("böser name; rm -rf /"); v=log().count("reload")
(BASE/"queue"/f"auftrag-{secrets.token_hex(8)}.json").write_text(json.dumps({"aktion":"caddy_neu_laden"})); r=worker()
chk("Ungültiger Container-Name wird nie ausgeführt",log().count("reload")==v and "nicht bekannt" in r.stdout,r.stdout+r.stderr)
(BASE/"caddy-container").write_text("server-caddy-1")
# Ordner aus caddy-sites-dir fehlt -> eigener Ordner
(BASE/"caddy-sites-dir").write_text(str(T/"gibtesnicht"))
r,e=veroeffentlichen("dritte-seite.de"); chk("Fehlender Caddy-Ordner: Rückfall auf eigenen Ordner",(BASE/"caddy"/"sites"/"dritte-seite.de.caddy").is_file(),e)
# Löschen entfernt die Datei im richtigen Ordner
(BASE/"caddy-sites-dir").write_text(str(CS))
(BASE/"queue"/f"auftrag-{secrets.token_hex(8)}.json").write_text(json.dumps({"aktion":"loeschen","art":"live","name":"zweite-seite.de"})); worker()
chk("Löschen nimmt die Datei aus dem Caddy-Ordner",not (CS/"zweite-seite.de.caddy").exists())
# Modus own: unverändertes Verhalten (compose exec)
(BASE/"mode").write_text("own"); (BASE/"caddy-sites-dir").unlink(); LOG.write_text("")
r,e=veroeffentlichen("vierte-seite.de"); chk("Eigener Caddy: Datei im eigenen Ordner, Reload per compose",(BASE/"caddy"/"sites"/"vierte-seite.de.caddy").is_file() and "compose" in log() and "exec -T caddy caddy reload" in log(),log())
# mkctl / install: Skripte syntaktisch in Ordnung und mit den neuen Befehlen
for f in ("bin/mkctl","install.sh","bin/selbsttest.sh"):
    chk(f+" Syntax",subprocess.run(["bash","-n","/home/claude/markentrix-server/"+f]).returncode==0)
chk("mkctl kennt caddy-neu","caddy-neu)" in open("/home/claude/markentrix-server/bin/mkctl").read())
print("FERTIG")
