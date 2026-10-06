# -*- coding: utf-8 -*-
"""Lädt Produktbilder von italiacamper24.de (Jimdo-CDN), dedupliziert per Bild-Hash, schreibt WebP + src/imagemap.json
Aufruf: python3 tools/fetch_images.py"""
import json, os, io, hashlib, sys, urllib.request, concurrent.futures as cf
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), "..")
cat = json.load(open(f"{ROOT}/src/catalog.json"))
OUT = f"{ROOT}/site/assets/img/p"; os.makedirs(OUT, exist_ok=True)
MAXPER = 6
want = []
for p in cat["products"]:
    for i in p["images"][:MAXPER]: want.append(i)
for q in cat["parts"]:
    for i in q["img"][:1]: want.append(i)
want = list(dict.fromkeys(want))
mp_path = f"{ROOT}/src/imagemap.json"
imap = json.load(open(mp_path)) if os.path.exists(mp_path) else {}
def get(i):
    iid, ver, ext = i.split("/")
    url = f"https://image.jimcdn.com/app/cms/image/transf/dimension=800x800:format={ext}/path/s2583cff5a45b5728/image/{iid}/version/{ver}/image.{ext}"
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40) as r: return i, r.read()
        except Exception as e: err = e
    return i, None
def ahash(im):
    g = im.convert("L").resize((16, 16)); px = list(g.getdata()); avg = sum(px) / len(px)
    return hashlib.md5("".join("1" if v > avg else "0" for v in px).encode()).hexdigest()[:12]
todo = [i for i in want if i not in imap]
print(len(want), "Bilder,", len(todo), "neu")
def proc(i):
    _, data = get(i)
    if not data: return i, None
    im = Image.open(io.BytesIO(data))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[3]); im = bg
    else: im = im.convert("RGB")
    h = ahash(im) + f"-{im.width*100//max(im.height,1)}"
    base = f"{OUT}/{h}"
    if not os.path.exists(base + "-720.webp"):
        for w, q in ((720, 72), (360, 70)):
            k = im.copy(); k.thumbnail((w, w * 2)); k.save(f"{base}-{w}.webp", quality=q, method=6)
    return i, [h, im.width, im.height]
with cf.ThreadPoolExecutor(14) as ex:
    for n, (i, r) in enumerate(ex.map(proc, todo)):
        if r: imap[i] = r
        if n % 100 == 0: print(n, flush=True)
json.dump(imap, open(mp_path, "w"))
files = os.listdir(OUT); print("fertig:", len(imap), "->", len(files) // 2, "unique;", sum(os.path.getsize(f"{OUT}/{f}") for f in files) // 1024 // 1024, "MB")
