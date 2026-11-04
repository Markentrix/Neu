#!/usr/bin/env python3
"""Struktur-Wächter für das Portal: prüft, was genutzt wird und was zusammengehört.

Aufruf (im Ordner markentrix-server):
  python3 tools/struktur.py            prüfen (Exit 1 bei neuen Verstößen)
  python3 tools/struktur.py --karte    docs/MODULKARTE.md neu schreiben
  python3 tools/struktur.py --basis    aktuellen Stand als akzeptierte Altlast festhalten (nur bewusst nutzen)

Geprüft wird nur mit der Standardbibliothek (ast), ohne Datenbank:
 1. Jedes Python-Modul unter portal/app gehört in genau eine Gruppe (tools/struktur_gruppen.json).
 2. Gruppen dürfen nur in erlaubter Richtung voneinander abhängen (Schichten: Grundlagen < Fachlogik < Routen < Start).
 3. Keine Importschleifen auf Modulebene.
 4. Kein Fachmodul importiert eine Routen-Datei auf Modulebene (verzögerte Importe in Funktionen sind erlaubt).
 5. Jedes Modul wird irgendwo genutzt (Start, Aufgaben-Prozess, Tests oder anderes Modul), sonst „verwaist“.
 6. Jede Datei unter static/js wird von einer Seite oder einem anderen Skript geladen.
 7. Dateigröße: über 1500 Zeilen nur als bekannte Altlast.
 8. Routen-Dateien: Jedes APIRouter-Objekt wird in main.py eingebunden.
 9. Die Modulkarte in docs/MODULKARTE.md ist aktuell.
Altlasten stehen in tools/struktur_basis.json. Neue Verstöße lassen die Prüfung scheitern, behobene Altlasten
werden gemeldet (dann die Basis mit --basis kürzen)."""
import ast, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "portal" / "app"
STATIC = ROOT / "portal" / "static"
GRUPPEN = json.loads((ROOT / "tools" / "struktur_gruppen.json").read_text(encoding="utf-8"))
BASIS_DATEI = ROOT / "tools" / "struktur_basis.json"
KARTE = ROOT / "docs" / "MODULKARTE.md"
MAX_ZEILEN = 1500
# Einstiegspunkte, die nicht von anderen Modulen importiert werden müssen
START = {"main", "cli", "__init__", "jobs"}


def module() -> dict:
    return {p.stem: p for p in sorted(APP.glob("*.py"))}


def importe(pfad: Path, namen: set) -> tuple[set, set]:
    """(Modulebene, verzögert) – Namen der app-Module, die diese Datei importiert."""
    baum = ast.parse(pfad.read_text(encoding="utf-8"))
    oben, spaet = set(), set()

    def sammle(knoten, ziel):
        for n in ast.walk(knoten):
            if isinstance(n, ast.ImportFrom):
                if n.level >= 1 and n.module:
                    kopf = n.module.split(".")[0]
                    if kopf in namen:
                        ziel.add(kopf)
                elif n.level >= 1 and not n.module:
                    ziel.update(a.name for a in n.names if a.name in namen)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.name.startswith("app.") and a.name.split(".")[1] in namen:
                        ziel.add(a.name.split(".")[1])

    for k in baum.body:
        if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            sammle(k, spaet)
        elif isinstance(k, (ast.If, ast.Try, ast.With)):
            # Importe in if/try auf Modulebene zählen als Modulebene, solange sie nicht in Funktionen stehen
            for n in ast.walk(k):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sammle(n, spaet)
            tmp = set()
            sammle(k, tmp)
            oben |= tmp - spaet
        else:
            sammle(k, oben)
    return oben, spaet - oben


def externe_nutzer(namen: set) -> dict:
    """Module, die von Tests, bin/ und Hilfsskripten außerhalb von portal/app genutzt werden (python -m app.x, import app.x)."""
    genutzt = defaultdict(set)
    quellen = list((ROOT / "tests").glob("*.py")) + list((ROOT / "bin").glob("*")) + [ROOT / "install.sh"] + list((ROOT / "templates").glob("*")) + list((ROOT / "panel").rglob("*.py"))
    for q in quellen:
        try:
            t = q.read_text(encoding="utf-8", errors="ignore")
        except (OSError, IsADirectoryError):
            continue
        for m in re.finditer(r"\bapp[.\s]+(?:import\s+)?([a-z0-9_]+)\b", t):
            if m.group(1) in namen:
                genutzt[m.group(1)].add(q.name)
    return genutzt


def js_pruefen() -> list:
    """JS-Dateien, die weder importiert noch von einer HTML- oder Python-Datei geladen werden."""
    probleme = []
    js = [p for p in (STATIC / "js").rglob("*.js")]
    quelltexte = ""
    for p in list(STATIC.rglob("*.html")) + list(APP.glob("*.py")) + list(APP.rglob("vorlagen/*")) + js + [ROOT / "install.sh"] + list((ROOT / "templates").glob("*")):
        try:
            quelltexte += "\n" + p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
    for p in js:
        rel = p.relative_to(STATIC).as_posix()
        if p.name not in quelltexte and rel not in quelltexte:
            probleme.append(rel)
    return sorted(probleme)


def router_pruefen(namen: set) -> list:
    """Routen-Objekte, die in keiner Datei eingebunden werden (include_router in main.py)."""
    main = (APP / "main.py").read_text(encoding="utf-8")
    probleme = []
    for n in sorted(namen):
        t = (APP / f"{n}.py").read_text(encoding="utf-8")
        for m in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*APIRouter\(", t, re.M):
            var = m.group(1)
            ok = re.search(rf"\b{n}\.{var}\b", main) or re.search(rf"from \.{n} import[^\n]*\b{var}\b", main) or re.search(rf"include_router\(\s*{n}\.{var}\b", main)
            if not ok:
                # Einbindung innerhalb derselben Datei (z. B. router.include_router(admin)) zählt auch
                if re.search(rf"include_router\(\s*{var}\b", t):
                    continue
                probleme.append(f"{n}.{var}")
    return probleme


def analyse() -> dict:
    mod = module()
    namen = set(mod)
    oben, spaet = {}, {}
    for n, p in mod.items():
        oben[n], spaet[n] = importe(p, namen)
    nutzer = defaultdict(set)
    for n in mod:
        for z in oben[n] | spaet[n]:
            if z != n:
                nutzer[z].add(n)
    extern = externe_nutzer(namen)
    zeilen = {n: len(p.read_text(encoding="utf-8").splitlines()) for n, p in mod.items()}
    return {"mod": mod, "namen": namen, "oben": oben, "spaet": spaet, "nutzer": nutzer, "extern": extern, "zeilen": zeilen}


def gruppe_von(n: str):
    for g, d in GRUPPEN["gruppen"].items():
        if n in d["module"]:
            return g
    return None


def schicht_von(n: str) -> int:
    """1 Grundlagen, 2 Fachlogik, 3 Routen, 4 Start (jobs, main, cli)."""
    g = gruppe_von(n)
    if g == "start":
        return 4
    if n.startswith("routes_"):
        return 3
    if g and GRUPPEN["gruppen"][g].get("grundlage"):
        return 1
    return 2


def verstoesse(a: dict) -> dict:
    v = defaultdict(list)
    namen, oben, spaet = a["namen"], a["oben"], a["spaet"]
    # 1 Gruppenzugehörigkeit
    zuordnung = defaultdict(list)
    for g, d in GRUPPEN["gruppen"].items():
        for n in d["module"]:
            zuordnung[n].append(g)
    for n in sorted(namen):
        if n not in zuordnung:
            v["ohne_gruppe"].append(n)
        elif len(zuordnung[n]) > 1:
            v["mehrfach_gruppe"].append(f"{n}: {', '.join(zuordnung[n])}")
    for n in sorted(zuordnung):
        if n not in namen:
            v["gruppe_unbekanntes_modul"].append(n)
    # 2 Schichten
    for n in sorted(namen):
        for z in sorted(oben[n]):
            if schicht_von(z) > schicht_von(n):
                v["schicht"].append(f"{n} (Schicht {schicht_von(n)}) -> {z} (Schicht {schicht_von(z)})")
    # 3 Schleifen auf Modulebene
    farbe, stapel, gefunden = {}, [], set()

    def tiefe(n):
        farbe[n] = 1
        stapel.append(n)
        for z in sorted(oben[n]):
            if farbe.get(z) == 1:
                kreis = stapel[stapel.index(z):] + [z]
                gefunden.add(" -> ".join(kreis))
            elif z not in farbe:
                tiefe(z)
        stapel.pop()
        farbe[n] = 2
    for n in sorted(namen):
        if n not in farbe:
            tiefe(n)
    v["schleife"] = sorted(gefunden)
    # 4 Fachmodul importiert Routen-Datei oben
    for n in sorted(namen):
        if n.startswith("routes_") or n in START:
            continue
        for z in sorted(oben[n]):
            if z.startswith("routes_"):
                v["fach_importiert_route"].append(f"{n} -> {z}")
    # 5 verwaist
    for n in sorted(namen):
        if n in START:
            continue
        if not a["nutzer"].get(n) and not a["extern"].get(n):
            v["verwaist"].append(n)
    # 7 Größe
    for n in sorted(namen):
        if a["zeilen"][n] > MAX_ZEILEN:
            v["zu_gross"].append(f"{n} ({a['zeilen'][n]} Zeilen)")
    v["js_verwaist"] = js_pruefen()
    v["router_nicht_eingebunden"] = router_pruefen(namen)
    return {k: x for k, x in v.items() if x}


def karte(a: dict) -> str:
    z = ["# Modulkarte des Portals", "",
         "Wird von `tools/struktur.py --karte` erzeugt. **Nicht von Hand ändern.** Die Gruppen stehen in `tools/struktur_gruppen.json`.",
         "Schichten: 1 Grundlagen, 2 Fachlogik, 3 Routen, 4 Start. Ein Modul darf beim Laden nur Module aus gleicher oder niedrigerer Schicht importieren. Verzögerte Importe in Funktionen sind erlaubt.", ""]
    for g, d in GRUPPEN["gruppen"].items():
        z += [f"## {d['titel']} (`{g}`)", "", d["zweck"], "", "| Modul | Schicht | Zeilen | Genutzt von |", "|---|---|---|---|"]
        for n in sorted(d["module"], key=lambda x: (schicht_von(x), x)):
            von = sorted(a["nutzer"].get(n, set()) | set(a["extern"].get(n, set())))
            kurz = ", ".join(f"`{x}`" for x in von[:4]) + (f" und {len(von) - 4} weitere" if len(von) > 4 else "")
            z.append(f"| `{n}` | {schicht_von(n)} | {a['zeilen'].get(n, 0)} | {kurz or '–'} |")
        z.append("")
    return "\n".join(z) + "\n"


def main():
    a = analyse()
    if "--karte" in sys.argv:
        KARTE.write_text(karte(a), encoding="utf-8")
        print("Modulkarte geschrieben:", KARTE.relative_to(ROOT))
        return 0
    v = verstoesse(a)
    if "--basis" in sys.argv:
        BASIS_DATEI.write_text(json.dumps(v, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("Basis geschrieben:", {k: len(x) for k, x in v.items()})
        return 0
    basis = json.loads(BASIS_DATEI.read_text(encoding="utf-8")) if BASIS_DATEI.exists() else {}
    neu, weg = {}, {}
    for k in set(v) | set(basis):
        n = [x for x in v.get(k, []) if x not in basis.get(k, [])]
        w = [x for x in basis.get(k, []) if x not in v.get(k, [])]
        if n:
            neu[k] = n
        if w:
            weg[k] = w
    veraltet = KARTE.read_text(encoding="utf-8") != karte(a) if KARTE.exists() else True
    print(f"Struktur: {len(a['namen'])} Module, {sum(a['zeilen'].values())} Zeilen, {len(GRUPPEN['gruppen'])} Gruppen")
    for k, x in sorted(neu.items()):
        print(f"FEHLER {k}:")
        for e in x:
            print("   ", e)
    for k, x in sorted(weg.items()):
        print(f"BEHOBEN (Basis kürzen mit --basis) {k}: {', '.join(x)}")
    if veraltet:
        print("FEHLER modulkarte: docs/MODULKARTE.md ist nicht aktuell. Mit  python3 tools/struktur.py --karte  neu schreiben.")
    alt = sum(len(x) for x in basis.values())
    print(f"Bekannte Altlasten: {alt}")
    return 1 if (neu or veraltet) else 0


if __name__ == "__main__":
    sys.exit(main())
