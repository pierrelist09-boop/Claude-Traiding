# Vorab NUR Training: je Coin und je Trainings-Haelfte (Stabilitaet) fuer (a) 1h Schub-Umkehr (Schluss am Extrem, 6 Kerzen), (b) 4h Ruhe+Schub-Fortsetzung (3 Kerzen)
import sys, statistics as st, math
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
ALTS="HYPE ARB NEAR UNI AVAX AAVE LINK DOGE ADA DOT".split()
KOST=0.0013
def atr_series(cs,n=14):
    trs=[0]*len(cs); out=[None]*len(cs)
    for i in range(1,len(cs)):
        trs[i]=max(cs[i]['h']-cs[i]['l'],abs(cs[i]['h']-cs[i-1]['c']),abs(cs[i]['l']-cs[i-1]['c']))
    for i in range(n,len(cs)): out[i]=sum(trs[i-n+1:i+1])/n
    return out
def events(c,tf,h,need_calm):
    cs=data.candles(c,tf,5000,use_cache=True,max_age=10**9); tr=cs[:len(cs)//2]; atr=atr_series(tr); out=[]
    for i in range(110,len(tr)-h-2):
        a=atr[i-1]
        if not a: continue
        med=st.median([k['v'] for k in tr[i-48:i]])
        if med<=0: continue
        rng=tr[i]['h']-tr[i]['l']
        if tr[i]['v']<3*med or rng<1.5*a or rng==0: continue
        d=1 if tr[i]['c']>tr[i]['o'] else -1
        pos=(tr[i]['c']-tr[i]['l'])/rng
        ext=(pos>0.75) if d==1 else (pos<0.25)
        if not ext: continue
        r12=sum(k['h']-k['l'] for k in tr[i-12:i])/12; r96=sum(k['h']-k['l'] for k in tr[i-108:i-12])/96
        if need_calm and not (r12<0.7*r96): continue
        e=tr[i+1]['o']; g=d*(tr[i+h]['c']-e)/e
        out.append((i/len(tr),g))
    return out
for label,tf,h,calm,sgn in (('1h Umkehr(Extrem,6)','1h',6,False,-1),('4h Ruhe+Extrem Fortsetzung(3)','4h',3,True,+1)):
    print('==',label)
    allv=[]
    for c in ALTS:
        ev=events(c,tf,h,calm); allv+=ev
        a=[sgn*g*100-KOST*100 for p,g in ev if p<0.5]; b=[sgn*g*100-KOST*100 for p,g in ev if p>=0.5]
        f=lambda v: f"n={len(v):3d} netto={st.mean(v):+.3f}%" if v else "n=0"
        print(f"{c:5s} Hälfte1 {f(a)} | Hälfte2 {f(b)}")
    a=[sgn*g*100-KOST*100 for p,g in allv if p<0.5]; b=[sgn*g*100-KOST*100 for p,g in allv if p>=0.5]
    print(f"ALLE   Hälfte1 n={len(a)} netto={st.mean(a):+.3f}% | Hälfte2 n={len(b)} netto={st.mean(b):+.3f}%")
