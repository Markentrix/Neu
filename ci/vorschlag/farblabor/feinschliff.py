import json, itertools
from farbe import *
PAP=hex2rgb('#F7F4EE'); W=[1,1,1]; INK=hex2rgb('#0C2128')
best=[]
for mh in range(214,233,2):
  for mC in (0.070,0.078,0.086,0.094):
    for mz in (7.6,8.2,8.8):
      m=auf_kontrast(mC,mh,mz,PAP)
      if not m: continue
      dm=max(druck(m,'gestrichen')[2],druck(m,'ungestrichen')[2])
      if dm>1.0: continue
      for ah in range(44,65,2):
        for aC in (0.110,0.122,0.134):
          for az in (3.15,3.35,3.6):
            a=auf_kontrast(aC,ah,az,PAP)
            if not a: continue
            if kontrast(INK,a)<4.5: continue
            da=max(druck(a,'gestrichen')[2],druck(a,'ungestrichen')[2])
            if da>1.5: continue
            cvd=min(dE(sim(m,k),sim(a,k)) for k in CVD)
            grau=abs(oklab(m)[0]-oklab(a)[0])*100
            dh=abs((ah-mh+180)%360-180)
            score=cvd+0.5*grau+0.05*dh-2*(dm+da)+20*min(aC,0.125)
            best.append((score,rgb2hex(m),rgb2hex(a),mh,mC,mz,ah,aC,az,round(cvd,1),round(grau,1),round(dm,1),round(da,1),round(kontrast(INK,a),2)))
best.sort(reverse=True)
print(len(best),'Varianten im Feinschliff')
for b in best[:8]: print(b)
