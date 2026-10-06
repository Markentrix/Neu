# -*- coding: utf-8 -*-
"""Lädt alle Anleitungs-PDFs der Originalseite, dedupliziert per Inhalt -> site/downloads/, schreibt src/docmap.json
Aufruf: python3 tools/fetch_docs.py"""
import json, os, re, hashlib, unicodedata, urllib.request, urllib.parse, concurrent.futures as cf
ROOT = os.path.join(os.path.dirname(__file__), ".."); OUT = f"{ROOT}/site/downloads"; os.makedirs(OUT, exist_ok=True)
cat = json.load(open(f"{ROOT}/src/catalog.json"))
urls = {}
for p in cat["products"]:
    for d in p["docs"]: urls[d["url"]] = d["name"]
mp = f"{ROOT}/src/docmap.json"; dmap = json.load(open(mp)) if os.path.exists(mp) else {}
def slug(s):
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    return re.sub(r"-+", "-", re.sub(r"[^A-Za-z0-9]+", "-", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode())).strip("-")[:80]
def get(u):
    for q in (u, urllib.parse.quote(urllib.parse.unquote(u), safe=":/%+?=")):
        for _ in range(2):
            try:
                with urllib.request.urlopen(urllib.request.Request(q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r: return u, r.read()
            except Exception as e: err = e
    return u, None
todo = [u for u in urls if not dmap.get(u)]; print(len(urls), "Links,", len(todo), "neu")
by_hash = {v["sha"]: v["file"] for v in dmap.values() if v}
with cf.ThreadPoolExecutor(12) as ex:
    for n, (u, data) in enumerate(ex.map(get, todo)):
        ext = os.path.splitext(urllib.parse.unquote(u.split("?")[0]))[1].lower() or ".pdf"
        if not data or ext not in (".pdf", ".docx", ".doc", ".jpg", ".png") or (ext == ".pdf" and data[:4] != b"%PDF"): dmap[u] = None; continue
        sha = hashlib.sha256(data).hexdigest()[:16]
        if sha not in by_hash:
            fn = f"{slug(urls[u]) or 'anleitung'}-{sha[:6]}{ext}"; open(f"{OUT}/{fn}", "wb").write(data); by_hash[sha] = fn
        dmap[u] = {"file": by_hash[sha], "sha": sha, "kb": len(data) // 1024}
        if n % 100 == 0: print(n, flush=True)
json.dump(dmap, open(mp, "w"), ensure_ascii=False)
fs = os.listdir(OUT); print("fertig:", sum(1 for v in dmap.values() if v), "Links ->", len(fs), "eindeutige PDFs,", sum(os.path.getsize(f"{OUT}/{f}") for f in fs) // 1024 // 1024, "MB;", sum(1 for v in dmap.values() if not v), "nicht abrufbar")
