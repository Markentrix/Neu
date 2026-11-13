"""Farbwerkzeuge für die Markentrix-Farbsuche: OKLCH, Kontrast, Farbfehlsicht, Druck-Simulation."""
import math, numpy as np
from PIL import Image, ImageCms
ICC='/usr/share/color/icc/'
_srgb=ImageCms.createProfile('sRGB')
def _tf(p):
    c=ImageCms.getOpenProfile(ICC+p)
    f=ImageCms.Flags.BLACKPOINTCOMPENSATION
    return (ImageCms.buildTransform(_srgb,c,'RGB','CMYK',renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,flags=f),
            ImageCms.buildTransform(c,_srgb,'CMYK','RGB',renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,flags=f))
PRINT={'gestrichen':_tf('PSOcoated_v3.icc'),'ungestrichen':_tf('PSOuncoated_v3_FOGRA52.icc')}
def hex2rgb(h): h=h.lstrip('#'); return [int(h[i:i+2],16)/255 for i in (0,2,4)]
def rgb2hex(c): return '#%02X%02X%02X'%tuple(max(0,min(255,round(x*255))) for x in c)
def lin(c): return [v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in c]
def unlin(c): return [12.92*v if v<=0.0031308 else 1.055*max(v,0)**(1/2.4)-0.055 for v in c]
def lum(c): r=lin(c); return 0.2126*r[0]+0.7152*r[1]+0.0722*r[2]
def kontrast(a,b):
    x,y=sorted([lum(a),lum(b)],reverse=True); return (x+0.05)/(y+0.05)
def lin2oklab(r):
    l=0.4122214708*r[0]+0.5363325363*r[1]+0.0514459929*r[2]; m=0.2119034982*r[0]+0.6806995451*r[1]+0.1073969566*r[2]; s=0.0883024619*r[0]+0.2817188376*r[1]+0.6299787005*r[2]
    l,m,s=[math.copysign(abs(v)**(1/3),v) for v in (l,m,s)]
    return [0.2104542553*l+0.7936177850*m-0.0040720468*s, 1.9779984951*l-2.4285922050*m+0.4505937099*s, 0.0259040371*l+0.7827717662*m-0.8086757660*s]
def oklab(c): return lin2oklab(lin(c))
def oklch(c):
    L,a,b=oklab(c); return L,math.hypot(a,b),math.degrees(math.atan2(b,a))%360
def from_oklch(L,C,h):
    a,b=C*math.cos(math.radians(h)),C*math.sin(math.radians(h))
    l=(L+0.3963377774*a+0.2158037573*b)**3; m=(L-0.1055613458*a-0.0638541728*b)**3; s=(L-0.0894841775*a-1.2914855480*b)**3
    r=[4.0767416621*l-3.3077115913*m+0.2309699292*s,-1.2684380046*l+2.6097574011*m-0.3413193965*s,-0.0041960863*l-0.7034186147*m+1.7076147010*s]
    return unlin(r), all(-1e-4<=v<=1+1e-4 for v in r)
def dE(a,b): return 100*math.dist(oklab(a),oklab(b))
CVD={'Rotschwäche':[[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
     'Grünschwäche':[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
     'Blauschwäche':[[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]}
def sim(c,k):
    r=lin(c); M=CVD[k]; return unlin([min(1,max(0,sum(M[i][j]*r[j] for j in range(3)))) for i in range(3)])
def druck(c,papier):
    to,back=PRINT[papier]; im=Image.new('RGB',(1,1),tuple(round(v*255) for v in c))
    cm=ImageCms.applyTransform(im,to); k=[round(v/255*100) for v in cm.getpixel((0,0))]
    rb=[v/255 for v in ImageCms.applyTransform(cm,back).getpixel((0,0))]
    return k,rb,dE(c,rb)
def auf_kontrast(C,h,ziel,bg,dunkler=True):
    """Sucht die Helligkeit, bei der die Farbe (C,h) den Zielkontrast zu bg erreicht."""
    best=None
    for i in range(80,980):
        L=i/1000; c,ok=from_oklch(L,C,h)
        if not ok: continue
        if dunkler and lum(c)>lum(bg): continue
        if not dunkler and lum(c)<lum(bg): continue
        d=abs(kontrast(c,bg)-ziel)
        if best is None or d<best[0]: best=(d,c)
    return best[1] if best and best[0]<0.15 else None

def farbe(C,h,ziel,bg,dunkler=True):
    """Wie auf_kontrast, nimmt aber die Sättigung zurück, bis die Farbe am Bildschirm darstellbar ist."""
    while C>0.01:
        c=auf_kontrast(C,h,ziel,bg,dunkler)
        if c: return c
        C-=0.005
    return None
