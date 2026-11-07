# Vorab NUR Training: K3' = 4h Ruhe+Volumen-Schub-Fortsetzung
import sys, itertools, statistics as st, io, contextlib
sys.path.insert(0,'/root/Claude-Traiding/research/fast')
with contextlib.redirect_stdout(io.StringIO()):
    import kandidaten_train as kt
def k3b(cs,atr,K,VT,H):
    out=[]; i=110
    while i<len(cs)-20:
        a=atr[i-1]
        if a:
            rng=cs[i]['h']-cs[i]['l']
            BH,BL,r12,r96=kt.box(cs,i)
            if rng>0 and r12<K*r96 and cs[i]['v']>=VT*kt.med48(cs,i) and rng>=1.5*a:
                b=1 if cs[i]['c']>cs[i]['o'] else -1
                pos=(cs[i]['c']-cs[i]['l'])/rng
                if (b==1 and pos>0.75) or (b==-1 and pos<0.25):
                    e0=cs[i+1]['o']; mid=(cs[i]['h']+cs[i]['l'])/2
                    stop=min(max(mid,e0-3*a),e0-1.5*a) if b==1 else max(min(mid,e0+3*a),e0+1.5*a)
                    r=kt.sim(cs,kt.load.__defaults__ and atr,i,b,stop,'4h',H,None,None)
                    if r: out.append(r); i=r[2]+1; continue
        i+=1
    return out
coins="HYPE ARB NEAR UNI AAVE LINK DOGE DOT AVAX ADA".split()
for K,VT,H in itertools.product((0.7,0.85),(2,3),(3,6)):
    res={c:k3b(*kt.load(c,'4h'),K,VT,H) for c in coins}
    kt.summarize(f"K={K} Vol>={VT}x H={H}",res)
