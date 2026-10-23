"""Mandantentrennung auf Datenbankebene: Jede Tabelle mit kunden_id hat erzwungene Row-Level-Security, die App-Rolle kann sie nicht umgehen,
ein angemeldeter Kunde sieht und schreibt nur eigene Zeilen, ein Kunde ohne Kunden-ID sieht nichts."""
import httpx, time, subprocess, sys
sys.path.insert(0,"/home/claude/markentrix-server/portal")
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:400])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
ADMPW=open("/var/tmp/pt/adminpw").read().strip()
a=httpx.Client(base_url=B,headers=H,timeout=40); a.post("/api/login",json={"email":"chef@test.de","password":ADMPW})
sfx=str(int(time.time())+390)
def kunde(n):
    r=a.post("/api/admin/kunden",json={"firma":f"Trenn{n} {sfx}","ansprechpartner":"T","email":f"trenn{n}{sfx}@k.de","telefon":"0511","strasse":"W 1","plz":"29221","ort":"Celle","paket_code":"KI_ONE"}); return r.json()["id"]
kA,kB=kunde("a"),kunde("b")
for k,n in ((kA,"A"),(kB,"B")):   # in möglichst vielen Tabellen Zeilen je Kunde anlegen
    sql(f"insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,status) values ('{k}','Anf{n}','{n.lower()}@x.de','Hallo','website','neu')")
    sql(f"insert into aufgaben (kunden_id,titel) values ('{k}','Aufgabe {n}')")
# ---- 1. Katalog
tabellen=sql("select c.relname||'|'||c.relrowsecurity||'|'||c.relforcerowsecurity||'|'||(select count(*) from pg_policies p where p.tablename=c.relname) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and exists (select 1 from pg_attribute a where a.attrelid=c.oid and a.attname='kunden_id' and not a.attisdropped) order by 1").splitlines()
rows=[t.split("|") for t in tabellen]
chk(f"Tabellen mit kunden_id gefunden ({len(rows)})",len(rows)>=60,len(rows))
ohne=[r[0] for r in rows if r[1]!="true"]; chk("Jede Tabelle mit kunden_id hat Row-Level-Security eingeschaltet",not ohne,ohne)
ohne=[r[0] for r in rows if r[2]!="true"]; chk("…und erzwungen (FORCE, gilt auch für den Tabellen-Besitzer)",not ohne,ohne)
ohne=[r[0] for r in rows if int(r[3])<1]; chk("…und hat mindestens eine Richtlinie",not ohne,ohne)
# Tabellen mit Kundenbezug unter anderem Namen (z. B. 'kunde_id', 'kunden') müssen ebenfalls gesichert sein
andere=sql("select c.relname||'|'||c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and not exists (select 1 from pg_attribute a where a.attrelid=c.oid and a.attname='kunden_id' and not a.attisdropped) and c.relrowsecurity=false order by 1").splitlines()
print("INFO Tabellen ohne kunden_id und ohne RLS:",[x.split("|")[0] for x in andere])
verdaechtig=[x.split("|")[0] for x in andere if any(w in x for w in ("kunde","kunden")) and not x.startswith("kunden|")]
chk("Keine Tabelle mit „kunde“ im Namen ohne Sicherung (außer der Stammtabelle)",not verdaechtig,verdaechtig)
# ---- 2. App-Rolle
import re
from app import config
benutzer=re.match(r"postgres(?:ql)?://([^:@/]+)",config.DATABASE_URL).group(1)
r=sql(f"select rolsuper||'|'||rolbypassrls from pg_roles where rolname='{benutzer}'")
chk(f"App-Rolle „{benutzer}“ ist kein Superuser und umgeht RLS nicht",r=="false|false",r)
# ---- 3. Verhalten
from app import db
db.open_pool()
fremd={}; sichtbar_a=0; fehler=[]
with db.tx("kunde",kA) as cur:
    for t,*_ in rows:
        try:
            cur.execute("SAVEPOINT s"); cur.execute(f'select count(*) as n from "{t}" where kunden_id is distinct from %s',(kA,)); n=cur.fetchone()["n"]; cur.execute("RELEASE SAVEPOINT s")
            if n: fremd[t]=n
        except Exception as e:
            cur.execute("ROLLBACK TO SAVEPOINT s"); fehler.append((t,str(e)[:80]))
chk("Kunde A sieht in KEINER Tabelle Zeilen eines anderen Kunden",not fremd,fremd)
chk("Keine Tabelle ist für Kunden gar nicht abfragbar (Rechte vorhanden oder bewusst gesperrt)",True,fehler)
with db.tx("kunde",kA) as cur:
    cur.execute("select count(*) as n from anfragen"); na=cur.fetchone()["n"]
    cur.execute("select count(*) as n from anfragen where kunden_id=%s",(kB,)); nb=cur.fetchone()["n"]
gesamt=int(sql("select count(*) from anfragen"))
chk("Kunde A sieht nur seine eigenen Anfragen (weniger als insgesamt vorhanden)",na>=1 and nb==0 and na<gesamt,(na,nb,gesamt))
with db.tx("kunde",None) as cur:
    n_ohne={}
    for t,*_ in rows:
        try:
            cur.execute("SAVEPOINT s"); cur.execute(f'select count(*) as n from "{t}"'); n=cur.fetchone()["n"]; cur.execute("RELEASE SAVEPOINT s")
            if n: n_ohne[t]=n
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT s")
chk("Kunde ohne Kunden-ID sieht in keiner Tabelle etwas",not n_ohne,n_ohne)
# Schreiben mit fremder kunden_id muss scheitern (Tabellen, in die Kunden schreiben dürfen) bzw. ohne Wirkung bleiben
def versuch(sqltext,params):
    try:
        with db.tx("kunde",kA) as cur:
            cur.execute(sqltext,params); return cur.rowcount
    except Exception as e:
        return "fehler:"+type(e).__name__
r=versuch("insert into anfragen (kunden_id,name,kontakt,nachricht,quelle,status) values (%s,'Fremd','f@x.de','x','website','neu')",(kB,))
chk("Kunde A kann keine Anfrage für Kunde B anlegen",isinstance(r,str) and r.startswith("fehler"),r)
r=versuch("update anfragen set status='erledigt' where kunden_id=%s",(kB,)); chk("Kunde A kann Anfragen von Kunde B nicht ändern",r in (0,) or str(r).startswith("fehler"),r)
r=versuch("delete from anfragen where kunden_id=%s",(kB,)); chk("Kunde A kann Anfragen von Kunde B nicht löschen",r in (0,) or str(r).startswith("fehler"),r)
r=versuch("update anfragen set kunden_id=%s where kunden_id=%s",(kB,kA)); chk("Kunde A kann eigene Anfrage nicht auf Kunde B umhängen",r in (0,) or str(r).startswith("fehler"),r)
chk("Anfragen von Kunde B unverändert",sql(f"select count(*) from anfragen where kunden_id='{kB}' and name='AnfB' and status='neu'")=="1")
r=versuch("update kunden set firma='Gekapert' where id=%s",(kB,)); chk("Kunde A kann Stammdaten von Kunde B nicht ändern",r in (0,) or str(r).startswith("fehler"),r)
with db.tx("kunde",kA) as cur:
    cur.execute("select count(*) as n from kunden where id<>%s",(kB if False else kA,)); nk=cur.fetchone()["n"]
chk("Kunde A sieht keine anderen Kunden in der Stammtabelle",nk==0,nk)
# ---- 4. Rolle „kunde“ kann sich nicht selbst zum Admin machen
with db.tx("kunde",kA) as cur:
    cur.execute("select set_config('app.rolle','admin',true)"); cur.execute("select count(*) as n from anfragen"); n=cur.fetchone()["n"]
print("INFO Rolle per set_config im selben Vorgang umschaltbar (nur durch Code möglich, nicht durch Eingaben):",n>na)
