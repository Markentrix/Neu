import json
from farbe import *
PAP=hex2rgb('#F7F4EE'); INK=hex2rgb('#0C2128'); W=[1,1,1]
F={'Kreide':'#F7F4EE','Tiefsee':'#0C2128','Pfauenblau':'#045268','Leinen':'#EAE2D3'}
F['Kupfer']=rgb2hex(auf_kontrast(0.130,56,3.2,PAP))
L,C,h=oklch(hex2rgb(F['Kupfer'])); F['Kupfer dunkel']=rgb2hex(farbe(0.12,h,5.6,PAP))
L,C,h=oklch(hex2rgb(F['Pfauenblau'])); F['Pfauenblau hell']=rgb2hex(farbe(0.09,h,7.0,INK,dunkler=False))
L,C,h=oklch(hex2rgb(F['Kupfer'])); F['Kupfer hell']=rgb2hex(farbe(0.12,h,8.0,INK,dunkler=False))
F['Nebel']=rgb2hex(from_oklch(0.945,0.018,224)[0])
spec={}
for n,hx in F.items():
    c=hex2rgb(hx); L,C,h=oklch(c); g=druck(c,'gestrichen'); u=druck(c,'ungestrichen')
    spec[n]=dict(hex=hx,rgb=[round(v*255) for v in c],oklch=[round(L,3),round(C,3),round(h)],cmyk_g=g[0],dE_g=round(g[2],1),cmyk_u=u[0],dE_u=round(u[2],1),proof_u=rgb2hex(u[1]),grau=round(lum(c)**(1/2.2)*100))
    print(f"{n:16s} {hx} rgb{spec[n]['rgb']} oklch{spec[n]['oklch']} | gestrichen {g[0]} dE {g[2]:.1f} | ungestrichen {u[0]} dE {u[2]:.1f} -> {rgb2hex(u[1])}")
K=lambda a,b: round(kontrast(hex2rgb(F[a]) if a in F else hex2rgb(a),hex2rgb(F[b]) if b in F else hex2rgb(b)),1)
pairs=[('Tiefsee','Kreide'),('Tiefsee','#FFFFFF'),('Tiefsee','Leinen'),('Pfauenblau','Kreide'),('Pfauenblau','#FFFFFF'),('Pfauenblau','Leinen'),('#FFFFFF','Pfauenblau'),('Kreide','Pfauenblau'),
       ('Kupfer','Kreide'),('Kupfer','#FFFFFF'),('Kupfer','Leinen'),('Tiefsee','Kupfer'),('#FFFFFF','Kupfer'),('Kupfer dunkel','Kreide'),('Kupfer dunkel','#FFFFFF'),('Kupfer dunkel','Leinen'),('#FFFFFF','Kupfer dunkel'),
       ('Kreide','Tiefsee'),('Pfauenblau hell','Tiefsee'),('Kupfer hell','Tiefsee'),('Kupfer','Tiefsee'),('Kupfer','Pfauenblau'),('Tiefsee','Nebel'),('Pfauenblau','Nebel'),('Pfauenblau','Tiefsee')]
kon={f'{a} auf {b}':K(a,b) for a,b in pairs}
for k,v in kon.items(): print(f'  {k}: {v}')
m=hex2rgb(F['Pfauenblau']); a=hex2rgb(F['Kupfer'])
tr={k:round(dE(sim(m,k),sim(a,k)),1) for k in CVD}; tr['normal']=round(dE(m,a),1); tr['Graustufen']=round(abs(oklab(m)[0]-oklab(a)[0])*100,1)
o=hex2rgb('#0C626D'); r=hex2rgb('#A1311A')
alt={k:round(dE(sim(o,k),sim(r,k)),1) for k in CVD}; alt['normal']=round(dE(o,r),1); alt['Graustufen']=round(abs(oklab(o)[0]-oklab(r)[0])*100,1)
print('Trennung neu',tr); print('Trennung alt (Petrol/Backsteinrot)',alt)
json.dump(dict(farben=spec,kontraste=kon,trennung=tr,trennung_alt=alt),open('spezifikation.json','w'),indent=1,ensure_ascii=False)
