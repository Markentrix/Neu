"""Katalog aus dem Markentrix-Portal als Grundlage für eigene Produktseiten.

Das Portal erzeugt keine Seiten. Damit jeder Artikel eine eigene, auffindbare Seite mit strukturierten Daten bekommt
(und die Seite auch ohne Portal einen Katalog zeigt), holt dieses Skript den Katalog und legt ihn als
build/katalog-portal.json ab. build/build.py liest die Datei und baut daraus Produktseiten, Karten und Sitemap.

Aufruf:
  python3 build/portal_katalog.py https://ihre-domain.de/api/produkte      Katalog vom Portal holen
  python3 build/portal_katalog.py pfad/zur/antwort.json                    Katalog aus gespeicherter Antwort
  python3 build/portal_katalog.py --entfernen                              Datei löschen (Rückfall auf produkte.py)
Danach: python3 build/build.py und den Ordner website-fertig/ neu hochladen.
"""
import os, sys, json, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HERE, "katalog-portal.json")


def _pruefen(j):
    if not isinstance(j, dict) or not isinstance(j.get("produkte"), list):
        raise ValueError("Antwort ist kein Katalog (Feld 'produkte' fehlt)")
    for p in j["produkte"]:
        for k in ("id", "name", "preis"):
            if k not in p: raise ValueError(f"Artikel ohne '{k}': {str(p)[:80]}")
        if not str(p["id"]).replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Artikel-ID nicht als Dateiname geeignet: {p['id']!r}")
    return j


def holen(quelle):
    if quelle.startswith("https://"):
        req = urllib.request.Request(quelle, headers={"Accept": "application/json", "User-Agent": "schichtatelier-build"})
        with urllib.request.urlopen(req, timeout=15) as r:
            j = json.loads(r.read().decode("utf-8"))
    else:
        with open(quelle, encoding="utf-8") as f:
            j = json.load(f)
    return _pruefen(j)


def lesen():
    """Katalog aus build/katalog-portal.json oder None."""
    if not os.path.exists(DATEI): return None
    with open(DATEI, encoding="utf-8") as f:
        return _pruefen(json.load(f))


def als_artikel(j):
    """Portal-Artikel in das Format von build/produkte.py umwandeln."""
    out = []
    for i, p in enumerate(sorted(j["produkte"], key=lambda x: x.get("sort", 0))):
        if p.get("aktiv") is False: continue
        out.append(dict(
            id=str(p["id"]), name=p["name"], kat=p.get("kategorie") or "sonstiges", preis=float(p["preis"]),
            kurz=p.get("kurz") or "", lang=p.get("lang") or p.get("kurz") or "", material=p.get("material") or "",
            masse=p.get("masse") or "", gewicht=p.get("gewicht") or "", farben=list(p.get("farben") or []),
            tags=list(p.get("tags") or []), text=bool(p.get("personalisierbar")), textlabel=p.get("textlabel") or "Ihr Wunschtext",
            textmax=int(p.get("textmax") or 40), foto=True, bilder=list(p.get("bilder") or [])))
    return out


def main(argv):
    if len(argv) != 2:
        print(__doc__); return 2
    if argv[1] == "--entfernen":
        if os.path.exists(DATEI): os.remove(DATEI)
        print("katalog-portal.json entfernt"); return 0
    j = holen(argv[1])
    with open(DATEI, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    print(f"{len(j['produkte'])} Artikel gespeichert in {DATEI}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
