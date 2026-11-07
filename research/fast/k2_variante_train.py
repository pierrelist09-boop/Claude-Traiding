# Vorab NUR Training: K2 mit festem ATR-Stop statt Strukturstop (Strukturstop liess den Drift verschwinden)
import sys, itertools, statistics as st
sys.path.insert(0,'/root/Claude-Traiding/research/fast')
import kandidaten_train as kt
def k2b(cs,atr,K,S,Sess,H):
    out=[]; i=110
    while i<len(cs)-20:
        a=atr[i]; BH,BL,r12,r96=kt.box(cs,i)
        if a and r12<K*r96 and (not Sess or kt.inwin(cs[i])):
            c=cs[i]['c']; b=1 if c>BH else (-1 if c<BL else 0)
            if b:
                d=-b; e0=cs[i+1]['o']; stop=e0-d*S*a
                r=kt.sim(cs,atr,i,d,stop,'1h',H,None,None)
                if r: out.append(r); i=r[2]+1; continue
        i+=1
    return out
coins="HYPE ARB NEAR UNI AVAX AAVE LINK".split()
for K,S,Sess,H in itertools.product((0.7,0.85),(2.0,3.0),(False,True),(12,)):
    res={c:k2b(*kt.load(c,'1h'),K,S,Sess,H) for c in coins}
    kt.summarize(f"K={K} Stop={S}ATR Sitzung={Sess} H={H}",res)
