# Vorab-Prototyp der drei Kandidaten, NUR Trainingsteil (erste 50 % je Coin). Validierung und Test bleiben unberuehrt.
import sys, statistics as st, itertools, datetime
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
FEE=0.00045; SLIP=0.0003; FUND_H=0.0000125   # Gebuehr/Seite, Slippage/Seite (Alts 0.03 %), Funding je Stunde (konservativ, immer als Kosten)
HRS={'1h':1,'4h':4}
def prep(cs):
    n=len(cs); tr=[0]*n; atr=[None]*n
    for i in range(1,n): tr[i]=max(cs[i]['h']-cs[i]['l'],abs(cs[i]['h']-cs[i-1]['c']),abs(cs[i]['l']-cs[i-1]['c']))
    for i in range(14,n): atr[i]=sum(tr[i-13:i+1])/14
    return atr
def sim(cs,atr,i,d,stop,tf,H,target=None,trailT=None):
    """Einstieg Open[i+1]; Rueckgabe (R netto, Kerzen gehalten, exit_index) oder None"""
    e=cs[i+1]['o']*(1+d*SLIP); risk=abs(e-stop)
    if risk<=0 or i+2+H>=len(cs): return None
    hh=e; ll=e; trail=None; s=stop
    for k in range(1,H+1):
        j=i+k; c=cs[j]
        if k>1 or True:
            pass
        hi,lo,op,cl=c['h'],c['l'],c['o'],c['c']
        # Stop zuerst
        if d==1 and lo<=s: x=min(op,s); return fin(e,x,d,risk,k,tf,j)
        if d==-1 and hi>=s: x=max(op,s); return fin(e,x,d,risk,k,tf,j)
        if target is not None:
            if d==1 and hi>=target: return fin(e,max(op,target) if op>=target else target,d,risk,k,tf,j)
            if d==-1 and lo<=target: return fin(e,min(op,target) if op<=target else target,d,risk,k,tf,j)
        if trailT is not None:
            hh=max(hh,hi); ll=min(ll,lo)
            if d==1: s=max(s,hh-trailT*atr[j])
            else: s=min(s,ll+trailT*atr[j])
        if k==H: return fin(e,cl,d,risk,k,tf,j)
def fin(e,x,d,risk,k,tf,j):
    x=x*(1-d*SLIP)
    gross=d*(x-e)/e
    net=gross-2*FEE-FUND_H*k*HRS[tf]
    return (net/(risk/e), k, j, net)
def inwin(c):
    t=datetime.datetime.fromtimestamp(c['t']/1000,datetime.timezone.utc)
    return 12<=t.hour<=21 and t.weekday()<5
def box(cs,i):
    b=cs[i-12:i]; return max(k['h'] for k in b),min(k['l'] for k in b),sum(k['h']-k['l'] for k in b)/12,sum(k['h']-k['l'] for k in cs[i-108:i-12])/96
def med48(cs,i): return st.median([k['v'] for k in cs[i-48:i]])
def k1(cs,atr,K,V,T,tf='4h'):
    out=[]; i=110
    while i<len(cs)-20:
        a=atr[i]; BH,BL,r12,r96=box(cs,i)
        if a and r12<K*r96:
            c=cs[i]['c']; d=1 if c>BH else (-1 if c<BL else 0)
            if d and (not V or cs[i]['v']>=1.5*med48(cs,i)):
                e0=cs[i+1]['o']; mid=(BH+BL)/2
                stop=min(max(mid,e0-3*a),e0-1.5*a) if d==1 else max(min(mid,e0+3*a),e0+1.5*a)
                r=sim(cs,atr,i,d,stop,tf,12,None,T)
                if r: out.append(r); i=r[2]+1; continue
        i+=1
    return out
def k2(cs,atr,K,S,Z,tf='1h'):
    out=[]; i=110
    while i<len(cs)-20:
        a=atr[i]; BH,BL,r12,r96=box(cs,i)
        if a and r12<K*r96 and (not S or inwin(cs[i])):
            c=cs[i]['c']; b=1 if c>BH else (-1 if c<BL else 0)
            if b:
                d=-b; e0=cs[i+1]['o']
                ext=cs[i]['h'] if d==-1 else cs[i]['l']
                stop=(ext+0.25*a) if d==-1 else (ext-0.25*a)
                dist=abs(stop-e0)
                if dist<1.0*a: stop=e0-d*1.0*a; dist=1.0*a
                if dist<=2.5*a:
                    tgt=(BH+BL)/2 if Z else None
                    # Ziel nur sinnvoll, wenn es auf der Gewinnseite liegt
                    if tgt is not None and ((d==1 and tgt<=e0) or (d==-1 and tgt>=e0)): tgt=None
                    r=sim(cs,atr,i,d,stop,tf,12,tgt,None)
                    if r: out.append(r); i=r[2]+1; continue
        i+=1
    return out
def k3(cs,atr,VT,S,H,tf='1h'):
    out=[]; i=110
    while i<len(cs)-20:
        a=atr[i-1]
        if a:
            rng=cs[i]['h']-cs[i]['l']
            if rng>0 and cs[i]['v']>=VT*med48(cs,i) and rng>=1.5*a:
                b=1 if cs[i]['c']>cs[i]['o'] else -1
                pos=(cs[i]['c']-cs[i]['l'])/rng
                if (b==1 and pos>0.75) or (b==-1 and pos<0.25):
                    d=-b; e0=cs[i+1]['o']; ext=cs[i]['h'] if d==-1 else cs[i]['l']
                    stop=(ext+0.25*a) if d==-1 else (ext-0.25*a)
                    if abs(stop-e0)<S*a: stop=e0-d*S*a
                    r=sim(cs,atr,i,d,stop,tf,H,None,None)
                    if r: out.append(r); i=r[2]+1; continue
        i+=1
    return out
SETS={'K1':("HYPE ARB NEAR UNI AAVE LINK DOGE DOT".split(),'4h'),'K2':("HYPE ARB NEAR UNI AVAX AAVE LINK".split(),'1h'),'K3':("ARB UNI DOT AVAX LINK ADA AAVE DOGE NEAR".split(),'1h')}
CTRL={'K1':['AVAX','ADA'],'K2':['DOGE','ADA','DOT'],'K3':['HYPE']}
def summarize(label,res):
    allr=[x for c in res for x in res[c]]
    if not allr: print(label,'keine Trades'); return
    R=[x[0] for x in allr]; pos=sum(1 for c in res if res[c] and st.mean([x[0] for x in res[c]])>0)
    print(f"{label:28s} n={len(R):4d} ØR={st.mean(R):+.3f} Gewinnquote={sum(1 for r in R if r>0)/len(R):.2f} Ø%netto={st.mean([x[3] for x in allr])*100:+.3f} Coins>0={pos}/{len([c for c in res if res[c]])} Ø Kerzen={st.mean([x[1] for x in allr]):.1f}")
cache={}
def load(c,tf):
    if (c,tf) not in cache:
        cs=data.candles(c,tf,5000,use_cache=True,max_age=10**9); tr=cs[:len(cs)//2]; cache[(c,tf)]=(tr,prep(tr))
    return cache[(c,tf)]
which=sys.argv[1:] or ['K1','K2','K3']
if 'K1' in which:
    print('== K1 4h Kompressions-Ausbruch (Train)')
    for K,V,T in itertools.product((0.7,0.85),(False,True),(2.5,3.5)):
        res={c:k1(*load(c,'4h'),K,V,T) for c in SETS['K1'][0]}; summarize(f"K={K} Vol={V} T={T}",res)
if 'K2' in which:
    print('== K2 1h Fehlausbruch-Fade (Train)')
    for K,S,Z in itertools.product((0.7,0.85),(False,True),(False,True)):
        res={c:k2(*load(c,'1h'),K,S,Z) for c in SETS['K2'][0]}; summarize(f"K={K} Sitzung={S} Ziel={Z}",res)
if 'K3' in which:
    print('== K3 1h Volumen-Schub-Umkehr (Train)')
    for VT,S,H in itertools.product((3,4),(1.5,2.5),(6,12)):
        res={c:k3(*load(c,'1h'),VT,S,H) for c in SETS['K3'][0]}; summarize(f"Vol>={VT}x S={S} H={H}",res)
