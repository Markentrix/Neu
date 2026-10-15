# -*- coding: utf-8 -*-
"""Bild-Pipeline: erzeugt aus Originalfotos responsive AVIF/WebP/JPEG in mehreren Breiten.

Originale liegen in <content>/media/. Ergebnisse werden nach Änderungszeit gecacht,
damit ein erneutes Veröffentlichen schnell bleibt.
"""
import hashlib
import json
import os
import re
import shutil

WIDTHS = [480, 800, 1200, 1600]
EXT = (".jpg", ".jpeg", ".png", ".webp")


def _safe(name):
    base = os.path.splitext(name)[0].lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "bild"


def process(media_dir, out_dir, cache_dir):
    """Gibt {dateiname: {"src", "w", "h", "avif": [...], "webp": [...]}} zurück."""
    result = {}
    if not os.path.isdir(media_dir):
        return result
    try:
        from PIL import Image, ImageOps, features
        has_avif = features.check("avif")
    except Exception:  # Pillow fehlt: Originale nur kopieren
        Image = None
        has_avif = False
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "img"), exist_ok=True)
    for name in sorted(os.listdir(media_dir)):
        if not name.lower().endswith(EXT):
            continue
        src = os.path.join(media_dir, name)
        st = os.stat(src)
        key = hashlib.sha1(f"{name}|{st.st_size}|{st.st_mtime_ns}|{has_avif}".encode()).hexdigest()[:12]
        slug = _safe(name)
        meta_path = os.path.join(cache_dir, f"{slug}-{key}.json")
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path))
        else:
            meta = {"files": []}
            if Image is None:
                fn = f"{slug}-{key}{os.path.splitext(name)[1].lower()}"
                shutil.copy2(src, os.path.join(cache_dir, fn))
                meta.update(src=fn, w=1200, h=900, avif=[], webp=[], files=[fn])
            else:
                im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
                W, H = im.size
                avif, webp = [], []
                widths = [w for w in WIDTHS if w < W] + [min(W, WIDTHS[-1])]
                widths = sorted(set(widths))
                for w in widths:
                    h = round(H * w / W)
                    r = im.resize((w, h), Image.LANCZOS)
                    for fmt, lst, kw in (("webp", webp, dict(quality=78, method=5)),
                                         ("avif", avif if has_avif else None, dict(quality=55))):
                        if lst is None:
                            continue
                        fn = f"{slug}-{key}-{w}.{fmt}"
                        r.save(os.path.join(cache_dir, fn), fmt.upper(), **kw)
                        lst.append(f"img/{fn} {w}w")
                        meta["files"].append(fn)
                    if w == widths[min(1, len(widths) - 1)]:
                        fn = f"{slug}-{key}-{w}.jpg"
                        r.save(os.path.join(cache_dir, fn), "JPEG", quality=80, optimize=True, progressive=True)
                        meta.update(src=fn, w=w, h=h)
                        meta["files"].append(fn)
                meta.update(avif=avif, webp=webp)
            json.dump(meta, open(meta_path, "w"))
        for fn in meta["files"]:
            shutil.copy2(os.path.join(cache_dir, fn), os.path.join(out_dir, "img", fn))
        result[name] = {"src": "img/" + meta["src"], "w": meta["w"], "h": meta["h"], "avif": meta["avif"], "webp": meta["webp"]}
    return result
