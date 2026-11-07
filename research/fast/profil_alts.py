# Profil der Alts (nur Volatilitaet/Volumen/Ereigniszahlen, KEINE Renditen) im Trainingsteil (erste 50 %)
import sys, statistics as st
sys.path.insert(0,'/root/Claude-Traiding')
from chartreader import data
COINS="HYPE ARB NEAR UNI AVAX AAVE LINK DOGE ADA DOT SOL BTC ETH".split()
for tf in ('1h','4h'):
    print('==',tf)
    for c in COINS:
        cs=data.candles(c,tf,5000,use_cache=True,max_age=10**9)
        n=len(cs); tr=cs[:n//2]
        # ATR% (14) Mittel
        atrp=[]; 
        for i in range(15,len(tr)):
            trs=[max(tr[j]['h']-tr[j]['l'],abs(tr[j]['h']-tr[j-1]['c']),abs(tr[j]['l']-tr[j-1]['c'])) for j in range(i-13,i+1)]
            atrp.append(sum(trs)/14/tr[i]['c']*100)
        qv=[k['v']*k['c'] for k in tr]
        # Volumen-Spike-Ereignisse: v > 3 * Median der letzten 48 Kerzen
        ev=0; ev_big=0
        for i in range(50,len(tr)):
            med=st.median([k['v'] for k in tr[i-48:i]])
            if med>0 and tr[i]['v']>3*med:
                ev+=1
        # Kompression: Range-Mittel(12) < 0.6 * Range-Mittel(96)
        comp=0
        for i in range(100,len(tr)):
            r12=sum(k['h']-k['l'] for k in tr[i-11:i+1])/12
            r96=sum(k['h']-k['l'] for k in tr[i-95:i+1])/96
            if r96>0 and r12<0.6*r96: comp+=1
        print(f"{c:5s} n={n:5d} ATR%={st.mean(atrp):.2f} medQuoteVol/Kerze={st.median(qv)/1e6:.2f}M Spike3x={ev} Kompr={comp}")
