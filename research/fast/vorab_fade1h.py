# Vorab NUR Training: 1h Ausbruch aus 12er-Box. Entflochten (max. 1 Signal je Coin je 12 Kerzen), mit/ohne Kompression, beide Trainingshaelften, je Coin
import sys, statistics as st, math
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
ALTS="HYPE ARB NEAR UNI AVAX AAVE LINK DOGE ADA DOT".split()
KOST=0.0013
def ev(c,tf,h,thr):
    cs=data.candles(c,tf,5000,use_cache=True,max_age=10**9); tr=cs[:len(cs)//2]; out=[]; last=-99
    for i in range(110,len(tr)-h-2):
        if i-last<12: continue
        box=tr[i-12:i]; bh=max(k['h'] for k in box); bl=min(k['l'] for k in box)
        r12=sum(k['h']-k['l'] for k in box)/12; r96=sum(k['h']-k['l'] for k in tr[i-108:i-12])/96
        comp = r12<thr*r96
        if thr is not None and not comp: continue
        cl=tr[i]['c']
        d=1 if cl>bh else (-1 if cl<bl else 0)
        if d==0: continue
        last=i
        e=tr[i+1]['o']; out.append((i/len(tr), d*(tr[i+h]['c']-e)/e*100))
    return out
for tf,h in (('1h',6),('1h',12),('4h',4)):
  for thr in (1e9,0.7):
    allv=[]; pc=[]
    for c in ALTS:
        e=ev(c,tf,h,thr); allv+=e
        pc.append((c,len(e),st.mean([g for p,g in e]) if e else 0))
    a=[g for p,g in allv if p<.5]; b=[g for p,g in allv if p>=.5]; v=[g for p,g in allv]
    sd=st.pstdev(v)
    print(f"{tf} h={h} Kompression={'nein' if thr>1e8 else 'ja<0.7'}: n={len(v)} brutto={st.mean(v):+.3f}% t~{st.mean(v)/(sd/math.sqrt(len(v))):+.2f} | H1 n={len(a)} {st.mean(a):+.3f}% | H2 n={len(b)} {st.mean(b):+.3f}%")
    print('   je Coin (n, brutto%):',' '.join(f"{c}:{n}/{m:+.2f}" for c,n,m in pc))
