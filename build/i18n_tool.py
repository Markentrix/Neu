#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Werkzeug für die englische Fassung.

    python3 build/i18n_tool.py fehlend                 # welche Texte noch keine Übersetzung haben (nach Seite)
    python3 build/i18n_tool.py fehlend --json f.json   # dieselbe Liste als Datei, mit Fundstellen
    python3 build/i18n_tool.py pruefen                 # baut probeweise und meldet Fehler in den Übersetzungen

Übersetzungen liegen in content/i18n/en/*.json als {"deutscher Text": "englischer Text"}.
"""
import argparse
import collections
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build as builder  # noqa: E402
import i18n  # noqa: E402


def probe():
    tmp = tempfile.mkdtemp(prefix="elb-i18n-")
    try:
        return builder.build(os.path.join(ROOT, "content"), os.path.join(tmp, "out"), os.path.join(ROOT, "static"), quiet=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("befehl", choices=["fehlend", "pruefen"])
    ap.add_argument("--json")
    a = ap.parse_args()
    r = probe()
    if a.befehl == "fehlend":
        miss = r["missing"]
        if a.json:
            out = [{"de": k, "wo": sorted(r["seen"].get(k, []))} for k in miss]
            with open(a.json, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
        by_page = collections.Counter(v.split(" (")[0] for v in miss.values())
        for page, n in by_page.most_common():
            print(f"{n:5d}  {page}")
        print(f"{len(miss)} Texte ohne Übersetzung")
        return 1 if miss else 0
    table = i18n.load_table(os.path.join(ROOT, "content"))
    unknown = [k for k in table if k not in r["seen"]]
    probs = [w for w in r["warnings"] if "/en/" in w or w.startswith("en/") or "Platzhalter" in w or "Zahlen" in w or "en/" in w]
    for w in probs:
        print("Fehler:", w)
    for k in unknown[:50]:
        print("Nicht mehr verwendet:", k[:120])
    print(f"{len(table)} Übersetzungen, {len(r['missing'])} fehlen, {len(probs)} Fehler, {len(unknown)} nicht mehr verwendet")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
