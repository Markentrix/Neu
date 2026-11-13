"""Erzeugt Prüfbögen: python3 bogen.py <name> ; liest kombis aus kombis_<name>.json"""
import json, sys
from farbe import *
name=sys.argv[1]; K=json.load(open(f'kombis_{name}.json'))
def hell(c,ink,z=6.5):
    L,C,h=oklch(hex2rgb(c)); return rgb2hex(farbe(min(C*1.05,0.13),h,z,hex2rgb(ink),dunkler=False))
for k in K:
    k.setdefault('ink','#1E1C19'); k.setdefault('paper','#F4EFE6'); k.setdefault('surf','#E6DCCA')
    k['mainDk']=hell(k['main'],k['ink']); k['accDk']=hell(k['acc'],k['ink'],7.5)
    k['accOn']='#FFFFFF' if kontrast([1,1,1],hex2rgb(k['acc']))>=4.5 else k['ink']
    k['info']=f"Akzent auf Papier {kontrast(hex2rgb(k['acc']),hex2rgb(k['paper'])):.1f} · Text auf Akzent {kontrast(hex2rgb(k['accOn']),hex2rgb(k['acc'])):.1f} · Haupt auf Papier {kontrast(hex2rgb(k['main']),hex2rgb(k['paper'])):.1f}"
html=open('bogen_vorlage.html').read().replace('/*DATA*/',json.dumps(K))
open(f'bogen_{name}.html','w').write(html)
