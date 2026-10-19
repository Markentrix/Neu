# -*- coding: utf-8 -*-
"""Macht aus einer Illustrator-PDF (nur Vektorpfade) ein schlankes, eng zugeschnittenes Web-SVG.

    pdftocairo -svg Logo.pdf roh.svg
    python3 tools/logo-from-pdf.py roh.svg static/logo.svg --map "#ffffff=#ffffff" --drop-bg --label "ElbDetail"

--drop-bg     entfernt das Hintergrund-Rechteck aus der Grafik
--map A=B     ersetzt Füllfarbe A durch B (Hex, mehrfach möglich); "*=#hex" färbt alles ein
--pad N       Rand um die Grafik in SVG-Einheiten (Standard 1)
"""
import argparse
import re


def hexcol(rgb):
    nums = [float(x) for x in re.findall(r"([\d.]+)%", rgb)]
    return "#" + "".join(f"{round(n * 2.55):02x}" for n in nums)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--map", action="append", default=[])
    ap.add_argument("--drop-bg", action="store_true")
    ap.add_argument("--pad", type=float, default=1.0)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    svg = open(a.src, encoding="utf-8").read()
    cmap = dict(m.lower().split("=", 1) for m in a.map)
    paths, xs, ys = [], [], []
    for m in re.finditer(r'<path[^>]*?fill="(rgb\([^)]*\))"[^>]*?d="([^"]+)"', svg):
        col, d = hexcol(m.group(1)), m.group(2)
        col = cmap.get("*", cmap.get(col, col))
        nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
        xs += nums[0::2]
        ys += nums[1::2]
        d = re.sub(r"-?\d+\.\d+", lambda n: f"{float(n.group(0)):.2f}".rstrip("0").rstrip("."), d)
        d = re.sub(r"\s+", " ", d).strip()
        paths.append((col, d))
    x0, y0, x1, y1 = min(xs) - a.pad, min(ys) - a.pad, max(xs) + a.pad, max(ys) + a.pad
    w, h = x1 - x0, y1 - y0
    groups = {}
    for col, d in paths:
        groups.setdefault(col, []).append(d)
    body = "".join(f'<g fill="{c}">' + "".join(f'<path d="{d}"/>' for d in ds) + "</g>" for c, ds in groups.items())
    label = f' role="img" aria-label="{a.label}"' if a.label else ' aria-hidden="true"'
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}" '
           f'width="{w:.0f}" height="{h:.0f}"{label}>{body}</svg>\n')
    open(a.dst, "w", encoding="utf-8").write(out)
    print(f"{a.dst}: {w:.1f} x {h:.1f}, {len(paths)} Pfade, {len(out) // 1024} KB")


if __name__ == "__main__":
    main()
