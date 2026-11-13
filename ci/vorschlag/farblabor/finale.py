import json
from farbe import *
P=hex2rgb('#F4EFE6')
M={'Petrol bisher':hex2rgb('#0C626D'),'Tiefpetrol':farbe(0.070,206,7.6,P),'Pfauenblau':farbe(0.080,224,7.6,P),'Seegrün':farbe(0.065,188,7.6,P)}
A={'Backsteinrot bisher':hex2rgb('#A1311A'),'Zinnober gebrannt':farbe(0.150,38,5.0,P),'Siena':farbe(0.130,47,5.0,P),'Kupfer':farbe(0.115,56,5.0,P),'Bernstein':farbe(0.110,70,5.0,P),'Altgold':farbe(0.095,88,5.0,P),'Pflaume':farbe(0.110,348,5.0,P)}
out={'M':{k:rgb2hex(v) for k,v in M.items()},'A':{k:rgb2hex(v) for k,v in A.items()}}
print(out)
for mn,m in M.items():
    print(f'\n{mn} {rgb2hex(m)}  Papier {kontrast(m,P):.1f}  Druck g/u {druck(m,"gestrichen")[2]:.1f}/{druck(m,"ungestrichen")[2]:.1f}')
    for an,a in A.items():
        c={k:dE(sim(m,k),sim(a,k)) for k in CVD}
        print(f'   {an:20s} {rgb2hex(a)} Papier {kontrast(a,P):.1f} | normal {dE(m,a):5.1f} | Rot- {c["Rotschwäche"]:5.1f} Grün- {c["Grünschwäche"]:5.1f} Blauschwäche {c["Blauschwäche"]:5.1f} | Grau {abs(oklab(m)[0]-oklab(a)[0])*100:4.1f} | Druck u {druck(a,"ungestrichen")[2]:.1f}')
json.dump(out,open('finale.json','w'))
