"""Vektorisiert das Younic-Logo (build/brand-src/younic-original.png) in zwei Farbebenen und speichert die Pfade
als build/brand-src/younic-paths.json. Aufruf: python3 build/trace_logo.py"""
import json, os, numpy as np, potrace
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), "brand-src", "younic-original.png")
OUT = os.path.join(os.path.dirname(__file__), "brand-src", "younic-paths.json")
UP = 3  # Hochskalieren für glattere Kanten

im = Image.open(SRC).convert("RGB")
W, H = im.size
a = np.asarray(im).astype(np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
orange = np.clip((R - B) / 255.0, 0, 1)          # Orange: R hoch, B niedrig
blue = np.clip((255.0 - R) / 255.0, 0, 1)        # Blau: R niedrig
blue = np.where(orange > 0.35, 0, blue)           # Orange nicht doppelt zählen

def up(m):
    img = Image.fromarray((m * 255).astype(np.uint8)).resize((W * UP, H * UP), Image.BICUBIC)
    return np.asarray(img) > 127

def trace(mask):
    bm = potrace.Bitmap(mask)
    plist = bm.trace(turdsize=40 * UP, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=0.5)
    paths = []
    for curve in plist:
        parts = []
        s = curve.start_point
        parts.append("M%.1f %.1f" % (s.x / UP, s.y / UP))
        for seg in curve.segments:
            if seg.is_corner:
                parts.append("L%.1f %.1f L%.1f %.1f" % (seg.c.x / UP, seg.c.y / UP, seg.end_point.x / UP, seg.end_point.y / UP))
            else:
                parts.append("C%.1f %.1f %.1f %.1f %.1f %.1f" % (seg.c1.x / UP, seg.c1.y / UP, seg.c2.x / UP, seg.c2.y / UP, seg.end_point.x / UP, seg.end_point.y / UP))
        parts.append("Z")
        xs = [curve.start_point.x / UP] + [p / UP for seg in curve.segments for p in ((seg.c.x, seg.end_point.x) if seg.is_corner else (seg.c1.x, seg.c2.x, seg.end_point.x))]
        ys = [curve.start_point.y / UP] + [p / UP for seg in curve.segments for p in ((seg.c.y, seg.end_point.y) if seg.is_corner else (seg.c1.y, seg.c2.y, seg.end_point.y))]
        paths.append({"d": "".join(parts), "bbox": [min(xs), min(ys), max(xs), max(ys)]})
    return paths

res = {"w": W, "h": H, "blau": trace(up(blue)), "orange": trace(up(orange))}
json.dump(res, open(OUT, "w"))
print("Pfade: blau", len(res["blau"]), "orange", len(res["orange"]))
for k in ("blau", "orange"):
    for p in res[k]:
        print(k, [round(v) for v in p["bbox"]], len(p["d"]))
