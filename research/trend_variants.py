#!/usr/bin/env python3
"""Vorab festgelegte Varianten der 4h-Trendfolge, getestet über drei getrennte Zeitfenster (Walk-forward statt Gitter).

Gemeinsam: Einstieg am Schluss einer 4h-Kerze, die über das N-Kerzen-Hoch (Short: unter das Tief) schließt, nur in Richtung des Tagestrends
(Schluss > EMA50 > EMA200, RSI < 75; Short gespiegelt). Varianten unterscheiden sich in Ausstieg und Filtern. 8 Coins, Kosten wie überall."""
import os
import sys
from bisect import bisect_right

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.series import Series

COINS = "BTC ETH SOL XRP DOGE LINK AVAX NEAR UNI AAVE".split()
FEE2, SLIP, FUND_H = 0.0009, 0.0002, 0.0000125
VARIANTS = {
    "A  Donchian55, ATR-Trail 4 (bisheriges K)": dict(N=55, stop=3, exit="atr", trail=4),
    "B  Donchian55, Swing-Trail (nur Chart)": dict(N=55, stop=3, exit="swing"),
    "C  Donchian55, nur Tagestrend-Ausstieg": dict(N=55, stop=3, exit="flip"),
    "D  A + Regime-Filter (Tages-Effizienz >= 0,25)": dict(N=55, stop=3, exit="atr", trail=4, er=0.25),
    "E  Donchian100, ATR-Trail 5": dict(N=100, stop=4, exit="atr", trail=5),
    "F  A nur Long": dict(N=55, stop=3, exit="atr", trail=4, longonly=True),
    "G  A + Volumen >= 1,3": dict(N=55, stop=3, exit="atr", trail=4, vr=1.3),
    "H  Donchian30, ATR-Trail 4": dict(N=30, stop=3, exit="atr", trail=4),
}


def efficiency(c, i, n=20):
    if i < n:
        return 0.0
    path = sum(abs(c[k] - c[k - 1]) for k in range(i - n + 1, i + 1))
    return abs(c[i] - c[i - n]) / path if path else 0.0


def run(S4, SD, p):
    ends = [c["T"] for c in SD.cs]
    out, i = [], 210
    while i < S4.n - 2:
        j = bisect_right(ends, S4.cs[i]["T"]) - 1
        if j < 210:
            i += 1
            continue
        up = SD.c[j] > SD.e50[j] > SD.e200[j] and SD.rsi[j] < 75
        dn = SD.c[j] < SD.e50[j] < SD.e200[j] and SD.rsi[j] > 25
        n = p["N"]
        brk_up, brk_dn = S4.c[i] > max(S4.h[i - n:i]), S4.c[i] < min(S4.l[i - n:i])
        side = "long" if up and brk_up else "short" if dn and brk_dn else None
        if not side or (p.get("longonly") and side == "short") or (p.get("er") and efficiency(SD.c, j) < p["er"]) or (p.get("vr") and S4.vr[i] < p["vr"]):
            i += 1
            continue
        long = side == "long"
        entry = S4.c[i] * (1 + SLIP if long else 1 - SLIP)
        a = S4.atr[i]
        if p["exit"] == "swing":
            sw = S4.lows(i, 1) if long else S4.highs(i, 1)
            ref = sw[-1][1] if sw and ((sw[-1][1] < entry) if long else (sw[-1][1] > entry)) else None
            stop = ref - 0.25 * a if (long and ref) else ref + 0.25 * a if ref else (entry - p["stop"] * a if long else entry + p["stop"] * a)
        else:
            stop = entry - p["stop"] * a if long else entry + p["stop"] * a
        d = abs(entry - stop)
        if d < 0.5 * a:
            i += 1
            continue
        extreme, trail, k, ex = entry, stop, i + 1, None
        while k < S4.n:
            if (S4.l[k] <= trail) if long else (S4.h[k] >= trail):
                ex = min(trail, S4.o[k]) if long else max(trail, S4.o[k])
                break
            if p["exit"] == "atr":
                extreme = max(extreme, S4.h[k]) if long else min(extreme, S4.l[k])
                new = extreme - p["trail"] * S4.atr[k] if long else extreme + p["trail"] * S4.atr[k]
                trail = max(trail, new) if long else min(trail, new)
            elif p["exit"] == "swing":
                sw = S4.lows(k, 1) if long else S4.highs(k, 1)
                if sw:
                    lvl = sw[-1][1]
                    if long and trail < lvl < S4.c[k]:
                        trail = lvl
                    elif not long and S4.c[k] < lvl < trail:
                        trail = lvl
            jj = bisect_right(ends, S4.cs[k]["T"]) - 1
            if jj >= 0 and ((SD.c[jj] < SD.e50[jj]) if long else (SD.c[jj] > SD.e50[jj])):
                ex = S4.c[k]
                break
            k += 1
        if ex is None:
            break
        ex *= (1 - SLIP if long else 1 + SLIP)
        hours = (k - i) * 4
        r = ((ex - entry) if long else (entry - ex)) / d - (FEE2 + (FUND_H * hours if long else -FUND_H * hours)) * entry / d
        out.append((S4.t[i], r))
        i = k + 1
    return out


def main():
    data_ = {}
    for c in COINS:
        s4, sd = data.candles(c, "4h", 5000, use_cache=True), data.candles(c, "1d", 5000, use_cache=True)
        if len(s4) > 700 and len(sd) > 300:
            data_[c] = (Series(s4), Series(sd))
    t0 = min(s[0].t[210] for s in data_.values()); t1 = max(s[0].t[-1] for s in data_.values())
    cuts = [t0 + (t1 - t0) * f for f in (1 / 3, 2 / 3)]
    print(f"Coins: {', '.join(data_)}. Fenster 1 bis 3 gleich lang ({__import__('time').strftime('%Y-%m', __import__('time').gmtime(t0 / 1000))} bis {__import__('time').strftime('%Y-%m', __import__('time').gmtime(t1 / 1000))}).\n")
    print(f"{'Variante':50} {'Fenster 1':>16} {'Fenster 2':>16} {'Fenster 3':>16} {'gesamt':>18}")
    for name, p in VARIANTS.items():
        allt = []
        for c, (s4, sd) in data_.items():
            allt += run(s4, sd, p)
        cell = lambda tr: f"{sum(r for _, r in tr) / len(tr):+.2f}R n={len(tr):3d}" if tr else "–"
        w = [[x for x in allt if x[0] < cuts[0]], [x for x in allt if cuts[0] <= x[0] < cuts[1]], [x for x in allt if x[0] >= cuts[1]]]
        pos = sum(1 for tr in w if tr and sum(r for _, r in tr) / len(tr) > 0)
        print(f"{name:50} {cell(w[0]):>16} {cell(w[1]):>16} {cell(w[2]):>16} {cell(allt):>18}  {'<- in allen 3 Fenstern positiv' if pos == 3 else ''}")


if __name__ == "__main__":
    main()
