# Vorab NUR Training (erste 50 %): Tageszeit-/Wochentag-Profil (Volatilitaet und vorzeichenbehaftete Rendite) + je-Coin-Aufteilung der Schub-Ereignisse
import sys, statistics as st, math, datetime
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
ALTS="HYPE ARB NEAR UNI AVAX AAVE LINK DOGE ADA DOT".split()
hr={h:[] for h in range(24)}; hrabs={h:[] for h in range(24)}
wd={d:[] for d in range(7)}; wdabs={d:[] for d in range(7)}
for c in ALTS:
    cs=data.candles(c,'1h',5000,use_cache=True,max_age=10**9)
    tr=cs[:len(cs)//2]
    for k in tr:
        t=datetime.datetime.utcfromtimestamp(k['t']/1000)
        r=(k['c']-k['o'])/k['o']*100
        hr[t.hour].append(r); hrabs[t.hour].append(abs(r)); wd[t.weekday()].append(r); wdabs[t.weekday()].append(abs(r))
print('Stunde(UTC)  Ø|Rendite|%  Ø Rendite%  t')
for h in range(24):
    v=hr[h]; m=st.mean(v); sd=st.pstdev(v)
    print(f"{h:02d}  {st.mean(hrabs[h]):.3f}  {m:+.4f}  {m/(sd/math.sqrt(len(v))):+.2f}")
print('Wochentag(0=Mo)')
for d in range(7):
    v=wd[d]; m=st.mean(v); sd=st.pstdev(v)
    print(f"{d}  {st.mean(wdabs[d]):.3f}  {m:+.4f}  {m/(sd/math.sqrt(len(v))):+.2f}")
