#!/usr/bin/env python3
"""Zusammenspiel: ein 1h-Signal zählt nur, wenn der 4h-Trend in dieselbe Richtung zeigt (und optional die 4h-Lage passt).

Vergleich ('Zufall') ist hier der Durchschnitt ALLER 1h-Kerzen mit demselben 4h-Trend in derselben Richtung, damit der Trend selbst
nicht als Vorteil des Signals durchgeht. Zeiträume und Kosten wie in event_study.py."""
import os
import sys
from collections import defaultdict
from bisect import bisect_right

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.events import detect
from chartreader.series import Series
from chartreader.structure import trend_at
from research.event_study import COINS, COST, DEDUPE, HORIZONS, stats

H = 24


def run():
    ev = defaultdict(lambda: {"train": [], "test": []}); base = {"long": {"train": [], "test": []}, "short": {"train": [], "test": []}}
    for coin in COINS:
        c1, c4 = data.candles(coin, "1h", 5000, use_cache=True), data.candles(coin, "4h", 5000, use_cache=True)
        if len(c1) < 600 or len(c4) < 300:
            continue
        S1, S4 = Series(c1), Series(c4)
        t4 = [c["T"] for c in c4]; last = {}; cut = int(S1.n * 0.6)
        for i in range(210, S1.n - H - 1):
            j = bisect_right(t4, c1[i]["T"]) - 1                      # letzte geschlossene 4h-Kerze
            if j < 210:
                continue
            tr4 = trend_at(S4, j); part = "train" if i < cut else "test"
            r = S1.c[i + H] / S1.c[i] - 1
            if tr4 == "up":
                base["long"][part].append(r - COST)
            if tr4 == "down":
                base["short"][part].append(-r - COST)
            for name, side in detect(S1, i):
                if (side == "long" and tr4 != "up") or (side == "short" and tr4 != "down"):
                    continue
                key = (name, side)
                if i - last.get(key, -999) < DEDUPE:
                    continue
                last[key] = i
                ev[key][part].append((r if side == "long" else -r) - COST)
    f = lambda s: "–" if not s else f"{s['mean'] * 100:+.2f}% / {s['hit'] * 100:.0f}% / n={s['n']} / t={s['t']:+.1f}"
    lines = [f"# Zusammenspiel 1h-Signal + gleichgerichteter 4h-Trend, Horizont {H} Kerzen", "",
             "| Signal | Richtung | Training | Test | Zufall im selben 4h-Trend (Test) | bestätigt |", "|---|---|---|---|---|---|"]
    for (name, side), d in sorted(ev.items()):
        tr, te, b_tr, b_te = stats(d["train"]), stats(d["test"]), stats(base[side]["train"]), stats(base[side]["test"])
        ok = bool(tr and te and te["n"] >= 30 and tr["mean"] > b_tr["mean"] + 0.0005 and te["mean"] > b_te["mean"] + 0.0005)
        lines.append(f"| {name} | {side} | {f(tr)} | {f(te)} | {b_te['mean'] * 100:+.2f}% | {'JA' if ok else ''} |")
    out = "\n".join(lines)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "confluence_1h_4h.md"), "w").write(out)
    print(out)


if __name__ == "__main__":
    run()
