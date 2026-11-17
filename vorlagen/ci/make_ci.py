#!/usr/bin/env python3
"""Erzeugt das Markenhandbuch Version 3.1 als PDF (A4, 27 Seiten).
Aufruf: python3 make_ci.py [Zieldatei.pdf]   (benötigt Playwright mit Chromium)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ci_base import CSS
import ci_pages_a as A, ci_pages_b as B, ci_pages_c as C

pages = [A.p01, A.p02, A.p03, A.p04, A.p05, A.p06, A.p07, A.p08, A.p09, A.p10, B.p11, B.p12, B.p13, B.p14, B.p15, B.p16, B.p17, B.p18, B.p19, C.p20, C.p21, C.p22, C.p23, C.p24, C.p25, C.p26, C.p27]
import re
body_html = ''.join(p() for p in pages)
# Schriftname mit Ziffer muss in Anführungszeichen stehen, sonst verwirft der Browser die ganze Angabe
body_html = re.sub(r"(font:[^;\"}]*?)\bSource Sans 3\b(?!['\"])", lambda m: m.group(1) + "'Source Sans 3'", body_html)
# Pfeile und Häkchen stehen nicht in den Markenschriften: eigene Notschrift, damit keine dritte Schrift (Inter) einspringt
body_html = body_html.replace('→', '<span class="sy">→</span>').replace('✓', '<span class="sy">✓</span>')
html = '<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Markentrix · Markenhandbuch 2026 · Version 3.1</title><style>' + CSS + '.sy{font-family:\'DejaVu Sans\',sans-serif}</style></head><body>' + body_html + '</body></html>'
out = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Markentrix_CI_2026_v3.1.pdf')
tmp = os.path.splitext(out)[0] + '.html'
open(tmp, 'w', encoding='utf-8').write(html)

import subprocess
subprocess.check_call(['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render.mjs'), tmp, out])
print('PDF:', out)
