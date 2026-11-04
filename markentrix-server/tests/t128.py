# Struktur-Wächter (tools/struktur.py): läuft sauber und erkennt echte Verstöße (Selbsttest mit künstlich veränderten Daten)
import sys, copy, subprocess, json
sys.path.insert(0, "/home/claude/markentrix-server/tools")
import struktur as S
def chk(n,c,i=""): print("OK  " if c else "FAIL",n,"" if c else str(i)[:300])
r=subprocess.run([sys.executable,"/home/claude/markentrix-server/tools/struktur.py"],capture_output=True,text=True)
chk("Wächter läuft sauber (nur bekannte Altlasten)",r.returncode==0,r.stdout+r.stderr)
chk("Modulkarte ist aktuell",S.KARTE.read_text(encoding="utf-8")==S.karte(S.analyse()))
a=S.analyse(); v=S.verstoesse(a)
chk("Jedes Modul hat genau eine Gruppe",not v.get("ohne_gruppe") and not v.get("mehrfach_gruppe"),v)
chk("Keine Importschleifen",not v.get("schleife"),v.get("schleife"))
chk("Keine verwaisten Module und Skripte",not v.get("verwaist") and not v.get("js_verwaist"),v)
chk("Alle Routen-Objekte sind eingebunden",not v.get("router_nicht_eingebunden"),v.get("router_nicht_eingebunden"))
chk("Alle Gruppen haben Titel und Zweck",all(d["titel"] and d["zweck"] for d in S.GRUPPEN["gruppen"].values()))
# Selbsttest: der Wächter muss künstliche Fehler finden
b=copy.deepcopy(a); b["oben"]["db"]=set(b["oben"]["db"])|{"security"}; b["oben"]["security"]=set(b["oben"]["security"])|{"db"}
chk("Erkennt Importschleife",any("db" in x and "security" in x for x in S.verstoesse(b).get("schleife",[])))
b=copy.deepcopy(a); b["oben"]["db"]=set(b["oben"]["db"])|{"routes_shop"}
vv=S.verstoesse(b); chk("Erkennt Grundlage, die eine Routen-Datei lädt",any(x.startswith("db ") for x in vv.get("schicht",[])) and "db -> routes_shop" in vv.get("fach_importiert_route",[]))
b=copy.deepcopy(a); b["nutzer"]["sperre"]=set(); b["extern"].pop("sperre",None)
chk("Erkennt verwaistes Modul",S.verstoesse(b).get("verwaist")==["sperre"])
b=copy.deepcopy(a); b["zeilen"]["shop"]=1501
chk("Erkennt zu große Datei",any(x.startswith("shop ") for x in S.verstoesse(b).get("zu_gross",[])))
alt=S.GRUPPEN["gruppen"]["website"]["module"]
try:
    S.GRUPPEN["gruppen"]["website"]["module"]=[m for m in alt if m!="shop"]
    chk("Erkennt Modul ohne Gruppe",S.verstoesse(a).get("ohne_gruppe")==["shop"])
    S.GRUPPEN["gruppen"]["website"]["module"]=alt+["gibtsnicht"]
    chk("Erkennt Gruppeneintrag ohne Modul",S.verstoesse(a).get("gruppe_unbekanntes_modul")==["gibtsnicht"])
finally:
    S.GRUPPEN["gruppen"]["website"]["module"]=alt
# Neue Altlast darf nicht unbemerkt durchgehen: Basis ohne einen Eintrag -> Wächter scheitert
bas=json.loads(S.BASIS_DATEI.read_text(encoding="utf-8")); orig=S.BASIS_DATEI.read_text(encoding="utf-8")
try:
    bas["fach_importiert_route"]=bas["fach_importiert_route"][1:]; S.BASIS_DATEI.write_text(json.dumps(bas),encoding="utf-8")
    r=subprocess.run([sys.executable,"/home/claude/markentrix-server/tools/struktur.py"],capture_output=True,text=True)
    chk("Neuer Verstoß lässt den Wächter scheitern",r.returncode==1 and "fach_importiert_route" in r.stdout,r.stdout)
finally:
    S.BASIS_DATEI.write_text(orig,encoding="utf-8")
