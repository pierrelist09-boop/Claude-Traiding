# Vorab NUR Training: Ruhe-Box-Ausbruch (Close ausserhalb der 12-Kerzen-Box nach Kompression), Haltedauer h Kerzen, brutto/netto
import sys, statistics as st, math, datetime
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
ALTS="HYPE ARB NEAR UNI AVAX AAVE LINK DOGE ADA DOT".split()
KOST=0.0013
def run(tf,hs,comp_thr,sess):
    res={h:[] for h in hs}
    for c in ALTS:
        cs=data.candles(c,tf,5000,use_cache=True,max_age=10**9); tr=cs[:len(cs)//2]
        for i in range(110,len(tr)-max(hs)-2):
            box=tr[i-12:i]  # Box = 12 Kerzen VOR der Signalkerze
            bh=max(k['h'] for k in box); bl=min(k['l'] for k in box)
            r12=sum(k['h']-k['l'] for k in box)/12
            r96=sum(k['h']-k['l'] for k in tr[i-108:i-12])/96
            if not (r12<comp_thr*r96): continue
            cl=tr[i]['c']
            if cl>bh: d=1
            elif cl<bl: d=-1
            else: continue
            if sess and tf=='1h':
                t=datetime.datetime.fromtimestamp(tr[i]['t']/1000, datetime.timezone.utc)
                if not (12<=t.hour<=21 and t.weekday()<5): continue
            e=tr[i+1]['o']
            for h in hs: res[h].append(d*(tr[i+h]['c']-e)/e*100)
    return res
for tf,hs in (('1h',(3,6,12)),('4h',(2,4,8))):
    for thr in (0.5,0.7):
        for sess in ((False,True) if tf=='1h' else (False,)):
            r=run(tf,hs,thr,sess)
            for h in hs:
                v=r[h]
                if len(v)<20: continue
                m=st.mean(v); sd=st.pstdev(v)
                print(f"{tf} Kompr<{thr} Sitzung={sess!s:5s} h={h:2d} n={len(v):4d} brutto={m:+.3f}% netto={m-KOST*100:+.3f}% t~{m/(sd/math.sqrt(len(v))):+.2f}")
