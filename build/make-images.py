#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt die kleineren Bildformate (AVIF, WebP) aus den Originalen in public/assets.

    pip install pillow
    python3 build/make-images.py

Die Ergebnisse liegen im Ordner public/assets und werden mit eingecheckt. Dieses Skript muss nur
laufen, wenn sich Logo oder Porträt ändern. build.py selbst braucht kein Pillow.
Originale: portrait.jpg, logo.png, logo-dark.png, og-image.jpg.
"""
from pathlib import Path

from PIL import Image

A = Path(__file__).resolve().parent.parent / "public" / "assets"
total_before = total_after = 0


def kb(p):
    return f"{p.stat().st_size / 1024:.1f} KB"


def save(im, name, **kw):
    p = A / name
    im.save(p, **kw)
    print(f"  {name:28} {im.size[0]}x{im.size[1]:<5} {kb(p)}")
    return p


def resized(im, w):
    h = round(im.size[1] * w / im.size[0])
    return im.resize((w, h), Image.LANCZOS)


# Porträt: drei Breiten, zwei moderne Formate. Das JPEG-Original bleibt als Ersatz für alte Browser.
print("Porträt")
src = Image.open(A / "portrait.jpg").convert("RGB")
for w in (360, 543):
    im = src if w == src.size[0] else resized(src, w)
    save(im, f"portrait-{w}.avif", quality=52, speed=2)
    save(im, f"portrait-{w}.webp", quality=78, method=6)
save(resized(src, 360), "portrait-360.jpg", quality=80, optimize=True, progressive=True)

# Logos mit Transparenz: Anzeigehöhe 40 bis 52 Pixel, also reichen 1x, 2x und 3x der größten Höhe
print("Logos")
for base in ("logo", "logo-dark"):
    src = Image.open(A / f"{base}.png").convert("RGBA")
    for w in (187, 374, 546):
        im = src if w == src.size[0] else resized(src, w)
        save(im, f"{base}-{w}.webp", quality=82, method=6, alpha_quality=100)

# Vorschaubild für soziale Netzwerke: gleiche Größe, aber kleiner gespeichert
print("Vorschaubild")
og = Image.open(A / "og-image.jpg").convert("RGB")
before = (A / "og-image.jpg").stat().st_size
tmp = A / "og-image.tmp.jpg"
og.save(tmp, quality=82, optimize=True, progressive=True)
if tmp.stat().st_size < before:
    tmp.replace(A / "og-image.jpg")
    print(f"  og-image.jpg                 {before / 1024:.1f} KB -> {kb(A / 'og-image.jpg')}")
else:
    tmp.unlink()
    print("  og-image.jpg bleibt unverändert")
