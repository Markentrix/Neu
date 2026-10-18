import httpx, re, email, subprocess, time, json
B="http://localhost:8000"; H={"X-MK":"1"}
def sql(q): return subprocess.run(["su","postgres","-c",f"psql -q -t -A -h /var/tmp/pgtest -p 54329 markentrix -c \"{q}\""],capture_output=True,text=True).stdout.strip()
a=httpx.Client(base_url=B,headers=H); a.post("/api/login",json={"email":"chef@test.de","password":open("adminpw").read().strip()})
a.put("/api/admin/einstellungen/smtp",json={"host":"127.0.0.1","port":8025,"sicherung":"keine","absender":"info@markentrix.de"})
def tok(mailto):
    for x in reversed([x for x in open("mails.txt").read().split("\n=====\n") if x.strip()]):
        m=email.message_from_string(x)
        if mailto in str(m["To"]):
            for part in m.walk():
                if part.get_content_type()=="text/plain":
                    g=re.search(r"einladung\?token=([A-Za-z0-9_-]+)",part.get_payload(decode=True).decode()); 
                    if g: return g.group(1)
sfx=str(int(time.time()))
pid=a.post("/api/admin/vertrieb/partner",json={"name":"Smoke V","email":f"sv{sfx}@x.de","status":"aktiv"}).json()["id"]
a.post(f"/api/admin/vertrieb/partner/{pid}/einladung",json={"email":f"sv{sfx}@x.de"})
httpx.post(B+"/api/einladung",headers=H,json={"token":tok(f"sv{sfx}@x.de"),"password":"SmokePasswort11"})
v=httpx.Client(base_url=B,headers=H); print("vertrieb login",v.post("/api/login",json={"email":f"sv{sfx}@x.de","password":"SmokePasswort11"}).status_code)
kemail=sql("select email from benutzer where rolle='kunde' and email like 'tina%' order by erstellt_am desc limit 1")
k=httpx.Client(base_url=B,headers=H); print("kunde login",k.post("/api/login",json={"email":kemail,"password":"InhaberPasswort1"}).status_code)
anon=httpx.Client(base_url=B,headers=H)
ids={"kid":sql("select id from kunden order by erstellt_am desc limit 1"),"pid":pid,"lid":sql("select id from leads limit 1"),"bid":sql("select id from belege limit 1"),"aid":sql("select id from alarme limit 1"),
     "wid":sql("select id from websites limit 1"),"rid":sql("select id from provisionen limit 1")}
import sys, os
sys.path.insert(0,"/home/claude/markentrix-server/portal")
os.environ.update(DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=/var/tmp/pgtest",PORTAL_SECRET="testgeheimnis123",PORTAL_JOBS="0")
from app.main import app
spec={"paths":{}}
for r in app.routes:
    if hasattr(r,"methods") and "GET" in r.methods and r.path.startswith("/api/"): spec["paths"][r.path]={"get":1}
fehl=0; n=0
for path,ops in spec["paths"].items():
    if "get" not in ops: continue
    p=path
    for ph in re.findall(r"\{(\w+)\}",path):
        val=ids.get(ph) or ids.get({"bid":"bid"}.get(ph,""),"") or sql("select id from kunden limit 1")
        p=p.replace("{"+ph+"}",val or "00000000-0000-0000-0000-000000000000")
    for name,c in (("admin",a),("kunde",k),("vertrieb",v),("anon",anon)):
        try: r=c.get(p)
        except Exception as e: print("EXC",name,p,e); fehl+=1; continue
        n+=1
        if path.startswith("/api/admin") and name!="admin" and r.status_code not in (401,403): fehl+=1; print("LEAK",name,p,r.status_code)
        if path.startswith("/api/vertrieb") and name in ("kunde","anon") and r.status_code not in (401,403): fehl+=1; print("LEAK",name,p,r.status_code)
        if path.startswith("/api/kunde") and name in ("vertrieb","anon") and r.status_code not in (401,403): fehl+=1; print("LEAK",name,p,r.status_code)
        if r.status_code>=500: fehl+=1; print("5xx",name,p,r.status_code,r.text[:150])
print("geprüft",n,"Fehler",fehl)
