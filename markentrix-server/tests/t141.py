"""Admin: Alarme zeigen die Meldung des Wachdienstes und lassen sich löschen (einzeln und alle)."""
import httpx, subprocess
B="http://localhost:8000"; H={"X-MK":"1"}
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("/var/tmp/pt/adminpw").read().strip()})
for i in range(3):
    sql(f"insert into alarme (stufe,quelle,titel,details) values ('kritisch','wachdienst','T141 Problem {i}',jsonb_build_object('text','Festplatte zu 91% voll'))")
d=a.get("/api/admin/compliance").json()
mine=[x for x in d["alarme"] if x["titel"].startswith("T141")]
chk("Alarm liefert die Meldung des Wachdienstes",len(mine)==3 and all(x["text"]=="Festplatte zu 91% voll" for x in mine),mine[:1])
r=a.delete(f"/api/admin/alarme/{mine[0]['id']}"); chk("Einzeln löschen",r.status_code==200 and sql(f"select count(*) from alarme where id={mine[0]['id']}")=="0",r.text)
chk("Unbekannter Alarm: 404",a.delete("/api/admin/alarme/999999999").status_code==404)
r=a.delete("/api/admin/alarme"); chk("Alle offenen löschen",r.status_code==200 and sql("select count(*) from alarme where bestaetigt_am is null")=="0",r.text)
chk("Löschen steht im Protokoll",int(sql("select count(*) from audit_log where aktion in ('alarm_geloescht','alarme_geloescht')"))>=2)
