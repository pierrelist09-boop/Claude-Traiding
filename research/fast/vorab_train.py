# Vorab-Ereignisstudie NUR im Trainingsteil (erste 50 % je Coin). Validierung/Test werden nicht angefasst.
# Frage: Wie verhaelt sich der Kurs nach Volumen-Schub-Kerzen (1h), getrennt nach "davor ruhig" und "davor schon unruhig"?
import sys, statistics as st, math
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
ALTS="HYPE ARB NEAR UNI AVAX AAVE LINK DOGE ADA DOT".split()
KOST=0.00045*2+0.0002*2   # Rundlauf 0.13 %
def atr_series(cs,n=14):
    out=[None]*len(cs)
    trs=[0]*len(cs)
    for i in range(1,len(cs)):
        trs[i]=max(cs[i]['h']-cs[i]['l'],abs(cs[i]['h']-cs[i-1]['c']),abs(cs[i]['l']-cs[i-1]['c']))
    for i in range(n,len(cs)):
        out[i]=sum(trs[i-n+1:i+1])/n
    return out
def run(tf,hs):
    res={}  # key -> list of (ret_net_in_pct, ret_gross)
    for c in ALTS:
        cs=data.candles(c,tf,5000,use_cache=True,max_age=10**9)
        tr=cs[:len(cs)//2]
        atr=atr_series(tr)
        for i in range(110,len(tr)-max(hs)-2):
            a=atr[i-1]
            if not a: continue
            med=st.median([k['v'] for k in tr[i-48:i]])
            if med<=0: continue
            vr=tr[i]['v']/med
            rng=tr[i]['h']-tr[i]['l']
            if vr<3 or rng<1.5*a: continue
            d=1 if tr[i]['c']>tr[i]['o'] else -1
            r12=sum(k['h']-k['l'] for k in tr[i-12:i])/12
            r96=sum(k['h']-k['l'] for k in tr[i-108:i-12])/96
            calm = r12<0.7*r96
            # Schlusslage in der Kerze (0=Tief,1=Hoch), gespiegelt nach Richtung
            pos=(tr[i]['c']-tr[i]['l'])/rng if rng>0 else .5
            ext = (pos>0.75) if d==1 else (pos<0.25)   # Schluss am Extrem in Richtung
            e=tr[i+1]['o']
            for h in hs:
                x=tr[i+h]['c']
                g=d*(x-e)/e
                for key in (('alle',h),(('ruhig' if calm else 'unruhig'),h),(('ruhig+Extrem' if (calm and ext) else 'sonst'),h),(('Extrem' if ext else 'Docht'),h)):
                    res.setdefault(key,[]).append((g,g-KOST))
    return res
for tf,hs in (('1h',(1,3,6,12)),('4h',(1,3,6))):
    print('=====',tf,'Richtung = Fortsetzung der Schubkerze (positiv = Fortsetzung, negativ = Umkehr); Zahlen in % je Trade')
    r=run(tf,hs)
    for k in sorted(r,key=lambda z:(z[0],z[1])):
        v=r[k]; n=len(v)
        if n<20: continue
        g=[x[0]*100 for x in v]; net=[x[1]*100 for x in v]
        m=st.mean(g); sd=st.pstdev(g)
        print(f"{k[0]:13s} h={k[1]:2d} n={n:4d} brutto={m:+.3f}% netto={st.mean(net):+.3f}% t(brutto)~{m/(sd/math.sqrt(n)):+.2f} Anteil>0={sum(1 for x in g if x>0)/n:.2f}")
