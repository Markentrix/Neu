"""Zuverlässigkeit: Alarme zusammenfassen und selbst schließen, Wachdienst mit Selbstheilung und Verfügbarkeit, Update mit Rückweg."""
import httpx, subprocess, os, sys, json, tempfile, shutil, time
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
def cli(*arg): return subprocess.run(["python3","-m","app.cli",*arg],cwd=os.environ["PYTHONPATH"],env=os.environ.copy(),capture_output=True,text=True)
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
REPO=os.path.dirname(os.environ["PYTHONPATH"])

# 1) Alarme zusammenfassen
sql("delete from alarme where quelle='wachdienst'")
for _ in range(3): cli("alarm-mail","kritisch","Markentrix: Problem auf dem Server","Festplatte zu 91% voll")
cli("alarm-mail","kritisch","Markentrix: Problem auf dem Server","Container mk-n8n läuft nicht (exited)")
chk("Gleiche Meldung 3x: eine Zeile mit Zähler 3",sql("select count(*) from alarme where quelle='wachdienst' and bestaetigt_am is null and anzahl=3")=="1",sql("select anzahl from alarme where quelle='wachdienst'"))
chk("Andere Meldung: eigene Zeile",sql("select count(*) from alarme where quelle='wachdienst' and bestaetigt_am is null")=="2")
w=[x for x in a.get("/api/admin/compliance").json()["alarme"] if x["quelle"]=="wachdienst"]
chk("Oberfläche bekommt Zähler und letzte Zeit",any(x["anzahl"]==3 and x["zuletzt"] for x in w),w[:1])
cli("alarm-mail","info","Markentrix: Alles wieder in Ordnung","Die zuvor gemeldeten Probleme sind behoben.")
chk("Problem behoben: Alarme schließen sich selbst",sql("select count(*) from alarme where quelle='wachdienst' and bestaetigt_am is null")=="0" and sql("select count(*) from alarme where quelle='wachdienst' and bestaetigt_von like 'automatisch%'")=="2")
chk("Keine Alarmzeile für die Entwarnung",sql("select count(*) from alarme where titel like '%wieder in Ordnung%'")=="0")

# 1b) Migration fasst alte, gleiche Alarme zusammen
sql("delete from alarme where quelle='altwacht'")
for i in range(4): sql(f"insert into alarme (stufe,quelle,titel,details,zeit) values ('kritisch','altwacht','Alt-Problem',jsonb_build_object('text','Platte voll'),now()-interval '{4-i} days')")
sql("insert into alarme (stufe,quelle,titel,details) values ('kritisch','altwacht','Alt-Problem',jsonb_build_object('text','Anderes'))")
mig=open(f"{REPO}/db/154_alarme_zusammenfassen.sql").read()
r=subprocess.run(["su","postgres","-c","psql -q -h /var/tmp/pgtest -p 54329 markentrix -v ON_ERROR_STOP=1"],input=mig,capture_output=True,text=True)
chk("Migration läuft erneut fehlerfrei",r.returncode==0,r.stderr)
chk("Alte gleiche Alarme: 4 werden zu 1 mit Zähler 4",sql("select count(*) from alarme where quelle='altwacht' and anzahl=4")=="1" and sql("select count(*) from alarme where quelle='altwacht'")=="2",sql("select anzahl from alarme where quelle='altwacht'"))
sql("delete from alarme where quelle='altwacht'")

# 2) Verfügbarkeit aus den Wachdienst-Meldungen
sys.path.insert(0,os.environ["PYTHONPATH"])
from app.routes_system import verfuegbarkeit
jetzt=1_800_000_000.0; z=[(jetzt-10*86400+i*300,1) for i in range(0,2880)]   # 10 Tage lückenlos ok
v=verfuegbarkeit(z,jetzt); chk("Lückenlos ok: 100 %, kein Ausfall",v and v["prozent"]==100 and v["letzter_ausfall"] is None,v)
z2=[(t,0 if jetzt-3*86400<=t<jetzt-3*86400+3600 else ok) for t,ok in z]
v=verfuegbarkeit(z2,jetzt); chk("1 Stunde Problem: unter 100 %, Ausfall von etwa 60 Min.",v["prozent"]<100 and v["letzter_ausfall"] and 55<=v["letzter_ausfall"]["minuten"]<=65,v)
z3=[x for x in z if not (jetzt-5*86400<=x[0]<jetzt-5*86400+7200)]   # 2 Stunden gar keine Meldung = Server aus
v=verfuegbarkeit(z3,jetzt); chk("Stille über 15 Min. zählt als Ausfall",v["letzter_ausfall"] and 100<=v["letzter_ausfall"]["minuten"]<=125,v)
chk("Ohne Meldungen: None",verfuegbarkeit([],jetzt) is None)
chk("Zu wenig Daten: noch keine Prozentzahl",verfuegbarkeit([(jetzt-600,1),(jetzt-300,1)],jetzt)["prozent"] is None)
from app.routes_system import ampel
d={"alter_minuten":1,"backup_stunden":1,"offsite_aktiv":False,"zertifikat_tage":40,"platte_prozent":30,"verfuegbarkeit":{"prozent":99.9,"tage_daten":12.0,"letzter_ausfall":None},"heilung":["2026-11-25 21:58:28 mk-portal wurde automatisch neu gestartet (Zustand exited)"]}
p={x["id"]:x for x in ampel(d,{},None,None)}
chk("Ampel: Verfügbarkeit grün mit Text",p["verfuegbarkeit"]["status"]=="ok" and "99,9 %" in p["verfuegbarkeit"]["detail"] and "Kein Ausfall" in p["verfuegbarkeit"]["detail"],p.get("verfuegbarkeit"))
chk("Ampel: Selbstheilung als Hinweis",p["heilung"]["status"]=="warn" and "mk-portal" in p["heilung"]["detail"] and "25.11. 21:58" in p["heilung"]["detail"],p.get("heilung"))
d["verfuegbarkeit"]["prozent"]=97.0; chk("Ampel: unter 98 % rot",{x["id"]:x for x in ampel(d,{},None,None)}["verfuegbarkeit"]["status"]=="bad")

# 3) Wachdienst mit gespieltem Docker: Selbstheilung (einmal pro Stunde), Verfügbarkeitszeile, Absturzschleife
T=tempfile.mkdtemp(); os.makedirs(f"{T}/bin"); os.makedirs(f"{T}/base/backup-status"); os.makedirs(f"{T}/state")
open(f"{T}/bin/docker","w").write('''#!/usr/bin/env bash
echo "docker $*" >> "$FAKELOG"
case "$1" in
  inspect) case "$*" in *State.Status*) [ "${@: -1}" = mk-portal ] && echo exited || echo running;; *Health*) echo "";; *RestartCount*) [ "${@: -1}" = mk-n8n ] && cat "$FAKERC" || echo 0;; esac;;
  image) exit 1;;
  exec) case "$*" in *pg_database_size*) echo 42;; *) echo 0;; esac;;
esac
''')
open(f"{T}/bin/curl","w").write("#!/bin/sh\nexit 0\n"); os.chmod(f"{T}/bin/docker",0o755); os.chmod(f"{T}/bin/curl",0o755)
src=open(f"{REPO}/bin/watchdog.sh").read().replace("BASE=/opt/markentrix",f"BASE={T}/base").replace("STATE=/var/lib/markentrix-watchdog",f"STATE={T}/state")
open(f"{T}/w.sh","w").write(src)
env=dict(os.environ,FAKELOG=f"{T}/log",FAKERC=f"{T}/rc",PATH=f"{T}/bin:"+os.environ["PATH"]); open(f"{T}/rc","w").write("0")
def lauf(*arg): return subprocess.run(["bash",f"{T}/w.sh",*arg],env=env,capture_output=True,text=True)
def zaehle(t): return open(f"{T}/log").read().count(t) if os.path.exists(f"{T}/log") else 0
lauf("--zeigen"); chk("--zeigen startet nichts neu",zaehle("docker restart")==0)
lauf(); chk("Gestoppter Container wird neu gestartet",zaehle("docker restart mk-portal")==1)
chk("Heilung steht im Protokoll und im Status",os.path.exists(f"{T}/state/heilung.log") and "mk-portal" in json.load(open(f"{T}/base/backup-status/system.json"))["heilung"][0])
chk("Verfügbarkeitszeile geschrieben (Problem = 0)",open(f"{T}/base/backup-status/verfuegbarkeit.log").read().split()[-1]=="0")
lauf(); chk("Höchstens ein Neustart pro Stunde",zaehle("docker restart mk-portal")==1)
open(f"{T}/rc","w").write("5"); r=lauf("--zeigen"); chk("Absturzschleife (5 Neustarts in 5 Min.) erscheint als Problem","startet ständig neu" in r.stdout,r.stdout[-300:])
shutil.rmtree(T)

# 4) Update mit Rückweg (gespieltes Docker)
T=tempfile.mkdtemp(); os.makedirs(f"{T}/bin")
open(f"{T}/bin/docker","w").write('''#!/usr/bin/env bash
echo "docker $*" >> "$FAKELOG"
case "$1" in
  tag) [ "$2" = markentrix-portal:vorher ] && touch "$FAKEDIR/zurueck";;
  image) exit 0;;
  inspect) case "$*" in *Health*) if [ -f "$FAKEDIR/zurueck" ] || [ -f "$FAKEDIR/gut" ]; then echo healthy; else echo unhealthy; fi;; esac;;
  exec) exit 0;;
esac
''')
open(f"{T}/bin/curl","w").write("#!/bin/sh\ncase \"$*\" in *api/login*) echo 401;; *) exit 0;; esac\n"); os.chmod(f"{T}/bin/docker",0o755); os.chmod(f"{T}/bin/curl",0o755)
env=dict(os.environ,FAKELOG=f"{T}/log",FAKEDIR=T,PATH=f"{T}/bin:"+os.environ["PATH"],UPDATE_WARTEN="1",UPDATE_PAUSE="0")
def upd(fn): return subprocess.run(["bash","-c",f". {REPO}/bin/update-schutz.sh; {fn}; echo RC=$?"],env=env,capture_output=True,text=True)
r=upd("portal_version_merken"); chk("Vor dem Update wird die laufende Version gemerkt","docker tag markentrix-portal:local markentrix-portal:vorher" in open(f"{T}/log").read())
open(f"{T}/log","w").close(); open(f"{T}/gut","w").close()
r=upd('update_pruefen_oder_zurueck "docker compose"'); chk("Gesundes Update bleibt",r.stdout.rstrip().endswith("RC=0") and "up -d --no-build" not in open(f"{T}/log").read(),r.stdout)
os.remove(f"{T}/gut"); open(f"{T}/log","w").close()
r=upd('update_pruefen_oder_zurueck "docker compose"'); lg=open(f"{T}/log").read()
chk("Defektes Update: automatisch zurück auf die vorherige Version",r.stdout.rstrip().endswith("RC=2") and "docker tag markentrix-portal:vorher markentrix-portal:local" in lg and "compose up -d --no-build portal" in lg and "Update wurde NICHT übernommen" in r.stdout,r.stdout+lg)
shutil.rmtree(T)
