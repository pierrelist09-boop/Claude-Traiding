#!/usr/bin/env python3
"""Chronologische Konto-Simulation der Chart-/Trendstrategie über zwei Jahre (ab 2024-11-06) auf BTC ETH SOL XRP DOGE LINK AVAX HYPE.

Konto 1.000 $, Zinseszins. Je Trade wird das Risiko (Verlust bis zum Stop) als fester Anteil des aktuellen Kontos eingesetzt; höchstens 4 Positionen, je Position
höchstens 1,5-faches, insgesamt 3-faches Kontovolumen. Kosten (Gebühr, Slippage, Funding) sind in R schon enthalten.
Kandidaten (vorab festgelegt): Trendfolge A, D, E, F (trend_variants.py) und drei Chart-Strategien C1 (Umkehr), C2 (Struktur), C3 (alles) auf 4h.
Schemata: fix (eine Strategie für alle) oder adaptiv (Walk-forward: alle 91 Tage wird nur mit bereits ABGESCHLOSSENEN Trades neu gewählt).
Aufruf: python3 research/simulation.py [--write]"""
import calendar
import csv
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.series import Series
from research import trend_variants as TV
from research.strategy_bt import Prep, simulate as chart_sim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COINS = "BTC ETH SOL XRP DOGE LINK AVAX HYPE".split()
START = calendar.timegm((2024, 11, 6, 0, 0, 0)) * 1000
DAY = 86_400_000
CHART = {"C1": dict(ev_set="reversal", T=4.5, ev_w=1.5, k=0.25, stop_ref="bar", exit="trail"),
         "C2": dict(ev_set="structure", T=4.5, ev_w=1.5, k=0.25, stop_ref="swing", exit="trail"),
         "C3": dict(ev_set="all", T=6.0, ev_w=3.0, k=0.25, stop_ref="swing", exit="trail")}
TREND = {k: next(v for n, v in TV.VARIANTS.items() if n.startswith(k)) for k in ("A", "D", "E", "F")}
CANDS = list(TREND) + list(CHART)


def load():
    out = {}
    for c in COINS:
        S4, SD = Series(data.candles(c, "4h", 5000, use_cache=True)), Series(data.candles(c, "1d", 5000, use_cache=True))
        tr = {}
        for k, p in TREND.items():
            tr[k] = [dict(t=x[0], R=x[1], exit=x[2], stop=x[3], side=x[4], coin=c, cand=k) for x in TV.run(S4, SD, p)]
        P = Prep("4h", S4, {"1d": SD})
        for k, p in CHART.items():
            tr[k] = [dict(t=x[0], R=x[1], exit=x[4], stop=x[5], side=x[3], coin=c, cand=k) for x in chart_sim(P, p)]
        out[c] = {"trades": tr, "S4": S4}
    return out


def stats(trs):
    n = len(trs)
    return (n, sum(x["R"] for x in trs) / n) if n else (0, 0.0)


def choose(D, t_r, pause=True):
    """Walk-forward: beste Kandidaten-Strategie gepoolt über alle Coins aus Trades, die vor t_r ABGESCHLOSSEN waren; Pause für Coins, bei denen sie nachweislich verliert."""
    best, bm = "E", -9
    for k in CANDS:
        n, m = stats([x for c in COINS for x in D[c]["trades"][k] if x["exit"] < t_r])
        if n >= 30 and m > 0 and m > bm:
            best, bm = k, m
    sel = {}
    for c in COINS:
        n, m = stats([x for x in D[c]["trades"][best] if x["exit"] < t_r])
        sel[c] = None if (pause and n >= 8 and m < -0.1) else best
    return sel, best


def build(D, scheme, pause=True):
    """Liste aller Trades des Schemas ab START (je Coin nie zwei gleichzeitig)."""
    end = max(D[c]["S4"].t[-1] for c in COINS)
    out, chosen = [], []
    if scheme in CANDS:
        periods = [(START, end + 1, {c: scheme for c in COINS})]
    else:
        periods, t = [], START
        while t <= end:
            sel, best = choose(D, t, pause)
            chosen.append((t, best, sel))
            periods.append((t, t + 91 * DAY, sel))
            t += 91 * DAY
    for c in COINS:
        last_exit = 0
        for a, b, sel in periods:
            k = sel[c]
            if not k:
                continue
            for x in D[c]["trades"][k]:
                if a <= x["t"] < b and x["t"] >= last_exit:
                    out.append(x)
                    last_exit = x["exit"]
    return out, chosen


def portfolio(trades, r, eq0=1000.0, max_pos=4, pos_cap=1.5, exp_cap=3.0):
    eq, open_, done, curve, skipped = eq0, [], [], [(START, eq0)], 0
    def settle(upto):
        nonlocal eq
        for p in sorted([p for p in open_ if p["exit"] <= upto], key=lambda p: p["exit"]):
            eq += p["pnl"]
            open_.remove(p)
            done.append(p)
            curve.append((p["exit"], eq))
    for tr in sorted(trades, key=lambda x: x["t"]):
        settle(tr["t"])
        expo = sum(p["notional"] for p in open_)
        want = r * eq / tr["stop"]
        notional = min(want, pos_cap * eq, exp_cap * eq - expo)
        if len(open_) >= max_pos or notional < 0.25 * want or eq <= 0:
            skipped += 1
            continue
        open_.append({**tr, "notional": notional, "pnl": tr["R"] * notional * tr["stop"]})
    settle(10 ** 15)
    peak, dd = eq0, 0.0
    for _, e in curve:
        peak = max(peak, e)
        dd = max(dd, 1 - e / peak)
    end = max(t for t, _ in curve)
    years = (end - START) / (365.25 * DAY)
    per = defaultdict(float)
    for p in done:
        per[p["coin"]] += p["pnl"]
    return {"final": eq, "cagr": (eq / eq0) ** (1 / years) - 1 if eq > 0 else -1, "dd": dd, "n": len(done), "skipped": skipped, "years": years,
            "win": sum(1 for p in done if p["pnl"] > 0) / len(done) if done else 0, "per_coin": dict(per), "curve": curve, "done": done}


def bh(D):
    out = {}
    for c in COINS:
        S = D[c]["S4"]
        i = next((k for k, t in enumerate(S.t) if t >= START), None)
        if i is not None:
            out[c] = S.c[-1] / S.c[i] - 1
    return out


def main():
    D = load()
    print(f"Simulation ab {time.strftime('%Y-%m-%d', time.gmtime(START / 1000))}, Konto 1.000 $, Coins: {', '.join(COINS)}\n")
    print(f"{'Schema':34} {'Risiko':>6} {'Endkonto':>10} {'pro Jahr':>9} {'größter Rückgang':>17} {'Trades':>7} {'Treffer':>8}")
    rows = {}
    schemes = [("fix A (bisheriges K)", "A"), ("fix E (K2, langsam)", "E"), ("fix F (A nur Long)", "F"), ("fix C1 (Chart Umkehr)", "C1"),
               ("adaptiv (Walk-forward)", "adapt"), ("adaptiv ohne Pause", "adapt_nopause")]
    for name, sc in schemes:
        trades, chosen = build(D, "adapt" if sc.startswith("adapt") else sc, pause=sc != "adapt_nopause")
        for r in (0.01, 0.02, 0.04):
            res = portfolio(trades, r)
            rows[(name, r)] = (res, chosen)
            print(f"{name:34} {r * 100:5.0f}% {res['final']:10.0f} {res['cagr'] * 100:+8.0f}% {res['dd'] * 100:16.0f}% {res['n']:7d} {res['win'] * 100:7.0f}%")
    b = bh(D)
    print("\nZum Vergleich Buy&Hold seit Start (je Coin):", ", ".join(f"{c} {v * 100:+.0f}%" for c, v in b.items()), f"| gleichgewichtet {sum(b.values()) / len(b) * 100:+.0f}%")
    print("\nGewinn/Verlust je Coin in $ (2 % Risiko):")
    for name, sc in schemes:
        res = rows[(name, 0.02)][0]
        print(f"  {name:28}", "  ".join(f"{c} {res['per_coin'].get(c, 0):+6.0f}" for c in COINS))
    if "--write" in sys.argv:
        write(D, rows, b)
    return D, rows


def write(D, rows, b):
    os.makedirs(os.path.join(ROOT, "simulation"), exist_ok=True)
    L = [f"# Simulation ab 2024-11-06 ({time.strftime('%Y-%m-%d')} berechnet)", "", "Konto 1.000 $, Zinseszins, 8 Coins, höchstens 4 Positionen, Kosten und Funding eingerechnet. Risiko = Verlust bis zum Stop in % des Kontos je Trade.", "",
         "| Schema | Risiko | Endkonto | pro Jahr | größter Rückgang | Trades | Treffer |", "|---|---|---|---|---|---|---|"]
    for (name, r), (res, _) in rows.items():
        L.append(f"| {name} | {r * 100:.0f} % | {res['final']:,.0f} $ | {res['cagr'] * 100:+.0f} % | {res['dd'] * 100:.0f} % | {res['n']} | {res['win'] * 100:.0f} % |")
    L += ["", "Buy&Hold je Coin seit Start: " + ", ".join(f"{c} {v * 100:+.0f} %" for c, v in b.items()) + f" (gleichgewichtet {sum(b.values()) / len(b) * 100:+.0f} %).", ""]
    open(os.path.join(ROOT, "simulation", "ergebnis.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
