# -*- coding: utf-8 -*-
"""Vektorisiert ein einfarbiges Logo (JPG/PNG, dunkel auf hell) zu einem schlanken SVG.

Braucht Pillow, numpy und potracer (reines Python, Potrace-Algorithmus):
    pip install --target /tmp/pylib potracer
    PYTHONPATH=/tmp/pylib python3 tools/logo-from-bitmap.py logo.jpg static/ref-firma.svg --label "Firma" --color "#1e2229"

Weiße Flächen im Logo (z. B. ausgesparte Schrift) werden transparent, so funktioniert das Logo
auf hellem und (per CSS invertiert) auf dunklem Grund.
"""
import argparse

import numpy as np
import potrace
from PIL import Image, ImageFilter, ImageOps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--label", default="")
    ap.add_argument("--color", default="#1e2229")
    ap.add_argument("--threshold", type=int, default=128)
    ap.add_argument("--scale", type=float, default=2.0, help="vor dem Nachzeichnen hochrechnen (glattere Kurven)")
    a = ap.parse_args()
    im = ImageOps.exif_transpose(Image.open(a.src)).convert("L")
    if a.scale != 1:
        im = im.resize((round(im.width * a.scale), round(im.height * a.scale)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    arr = np.array(im) < a.threshold
    ys, xs = np.nonzero(arr)
    pad = 4
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad, arr.shape[0]), max(xs.min() - pad, 0), min(xs.max() + pad, arr.shape[1])
    arr = arr[y0:y1, x0:x1]
    plist = potrace.Bitmap(~arr).trace(  # potracer erwartet True = hell und invertiert selbst
        turdsize=8, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=0.3)
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    parts = []
    for curve in plist:
        sp = curve.start_point
        d = [f"M{f(sp.x)} {f(sp.y)}"]
        for seg in curve.segments:
            if seg.is_corner:
                d.append(f"L{f(seg.c.x)} {f(seg.c.y)}L{f(seg.end_point.x)} {f(seg.end_point.y)}")
            else:
                d.append(f"C{f(seg.c1.x)} {f(seg.c1.y)} {f(seg.c2.x)} {f(seg.c2.y)} {f(seg.end_point.x)} {f(seg.end_point.y)}")
        parts.append("".join(d) + "Z")
    h, w = arr.shape
    label = f' role="img" aria-label="{a.label}"' if a.label else ' aria-hidden="true"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{round(w / a.scale)}" height="{round(h / a.scale)}"{label}>'
           f'<path fill="{a.color}" fill-rule="evenodd" d="{"".join(parts)}"/></svg>\n')
    open(a.dst, "w", encoding="utf-8").write(svg)
    print(f"{a.dst}: {w} x {h}, {len(plist)} Konturen, {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
