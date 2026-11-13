import json, itertools
from farbe import *
PAPIER=hex2rgb('#F4EFE6'); WEISS=[1,1,1]
print('Bisher: Petrol',[round(v,3) for v in oklch(hex2rgb('#0C626D'))],'Backsteinrot',[round(v,3) for v in oklch(hex2rgb('#A1311A'))],'Papier',[round(v,3) for v in oklch(PAPIER)])
haupt=[]
for h in range(170,251,6):
    for C in (0.05,0.065,0.08,0.095):
        for z in (6.0,7.0,8.5):
            c=auf_kontrast(C,h,z,PAPIER)
            if c: 
                d1=druck(c,'gestrichen'); d2=druck(c,'ungestrichen'); haupt.append(dict(hex=rgb2hex(c),h=h,C=C,z=z,dg=round(d1[2],1),du=round(d2[2],1)))
akz=[]
for h in list(range(0,121,6))+list(range(300,360,10)):
    for C in (0.08,0.11,0.14,0.17):
        for z in (4.7,5.3,6.0):
            c=auf_kontrast(C,h,z,PAPIER)
            if c:
                d1=druck(c,'gestrichen'); d2=druck(c,'ungestrichen'); akz.append(dict(hex=rgb2hex(c),h=h,C=C,z=z,dg=round(d1[2],1),du=round(d2[2],1)))
print(len(haupt),'Hauptfarben,',len(akz),'Akzente geprüft')
import collections
def tab(lst,key):
    g=collections.defaultdict(list)
    for x in lst: g[x[key]].append(x['du'])
    return {k:(round(min(v),1),round(sum(v)/len(v),1),round(max(v),1)) for k,v in sorted(g.items())}
print('Druckabweichung ungestrichen je Farbton Hauptfarbe (min, Mittel, max):',tab(haupt,'h'))
print('je Sättigung Hauptfarbe:',tab(haupt,'C'))
print('Akzent je Farbton:',tab(akz,'h'))
print('Akzent je Sättigung:',tab(akz,'C'))
json.dump(dict(haupt=haupt,akz=akz),open('kandidaten.json','w'))
paare=[]
for m in haupt:
    if m['du']>3.0: continue
    cm=hex2rgb(m['hex'])
    for a in akz:
        if a['du']>3.0 or a['z']>=m['z']: continue
        ca=hex2rgb(a['hex'])
        cvd=min(dE(sim(cm,k),sim(ca,k)) for k in CVD)
        grau=abs(oklab(cm)[0]-oklab(ca)[0])*100
        dh=abs((a['h']-m['h']+180)%360-180)
        paare.append(dict(m=m['hex'],a=a['hex'],mh=m['h'],ah=a['h'],mC=m['C'],aC=a['C'],mz=m['z'],az=a['z'],cvd=round(cvd,1),grau=round(grau,1),dh=dh,du=max(m['du'],a['du'])))
print(len(paare),'Paare nach Druckfilter')
ok=[p for p in paare if p['cvd']>=12 and p['grau']>=5]
print(len(ok),'Paare bestehen Farbfehlsicht + Graustufen')
json.dump(ok,open('paare.json','w'))
g=collections.Counter((p['ah']//12*12) for p in ok); print('Akzent-Farbtöne der bestandenen Paare:',sorted(g.items()))
