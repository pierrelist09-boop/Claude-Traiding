#!/usr/bin/env python3
"""Eventstudie: Was brachte jedes Chart-Signal in der Vergangenheit? (Hyperliquid-Kerzen, Kosten eingerechnet)

Aufruf: python3 research/event_study.py [1h|4h|15m ...]   -> research/results/event_study_<tf>.md/.json und chartreader/weights.json

Methode: Für jede Kerze i wird `events.detect` mit dem Wissen bis i aufgerufen (kein Blick in die Zukunft). Gemessen wird die
Rendite von Schluss i bis Schluss i+H (H = 6, 12, 24 Kerzen) in Richtung des Signals, abzüglich 0,13 % Rundlauf-Kosten
(Gebühr 2 x 0,045 % + Slippage 2 x 0,02 %). Gleiche Signale desselben Coins innerhalb von 24 Kerzen zählen nur einmal
(sonst überlappen die Messungen). Vergleich: der Durchschnitt ALLER Kerzen in derselben Richtung (Zufall/Drift). Die ersten
60 % der Zeit sind Training, die letzten 40 % ungesehener Test. Ein Signal gilt nur als bestätigt, wenn es in beiden Teilen
mehr als den Zufall plus 0,05 % bringt und im Test mindestens 30 Fälle hat.
"""
import json
import math
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.events import detect
from chartreader.series import Series

COINS = "BTC ETH SOL XRP DOGE NEAR UNI LINK AAVE AVAX BNB ADA DOT ARB".split()
HORIZONS, COST, DEDUPE = (6, 12, 24), 0.0013, 24
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def stats(v):
    if not v:
        return None
    m = sum(v) / len(v)
    sd = (sum((x - m) ** 2 for x in v) / max(1, len(v) - 1)) ** 0.5
    return {"n": len(v), "mean": m, "hit": sum(1 for x in v if x > 0) / len(v), "t": m / (sd / math.sqrt(len(v))) if sd > 0 else 0.0}


def study(tf):
    ev = defaultdict(lambda: {"train": {h: [] for h in HORIZONS}, "test": {h: [] for h in HORIZONS}})
    base = {"long": {"train": {h: [] for h in HORIZONS}, "test": {h: [] for h in HORIZONS}},
            "short": {"train": {h: [] for h in HORIZONS}, "test": {h: [] for h in HORIZONS}}}
    used = []
    for coin in COINS:
        cs = data.candles(coin, tf, 5000, use_cache=True)
        if len(cs) < 600:
            continue
        used.append(coin)
        S = Series(cs, *( (2, 2) if tf == "15m" else (3, 3) ))
        cut = int(S.n * 0.6)
        last = {}
        for i in range(210, S.n - max(HORIZONS) - 1):
            part = "train" if i < cut else "test"
            for h in HORIZONS:
                r = S.c[i + h] / S.c[i] - 1
                base["long"][part][h].append(r - COST)
                base["short"][part][h].append(-r - COST)
            for name, side in detect(S, i):
                key = (name, side)
                if i - last.get(key, -999) < DEDUPE:
                    continue
                last[key] = i
                for h in HORIZONS:
                    r = (S.c[i + h] / S.c[i] - 1) * (1 if side == "long" else -1) - COST
                    ev[key][part][h].append(r)
    return ev, base, used


def report(tf, ev, base, used):
    rows, weights = [], {}
    for (name, side), d in sorted(ev.items()):
        row = {"event": name, "side": side}
        ok = True
        for part in ("train", "test"):
            for h in HORIZONS:
                row[f"{part}{h}"] = stats(d[part][h])
        # bestätigt: Horizont 12 oder 24 in Training UND Test über Zufall + 0,05 %
        best = None
        for h in (12, 24):
            tr, te = row[f"train{h}"], row[f"test{h}"]
            b_tr, b_te = stats(base[side]["train"][h])["mean"], stats(base[side]["test"][h])["mean"]
            if tr and te and te["n"] >= 30 and tr["mean"] > b_tr + 0.0005 and te["mean"] > b_te + 0.0005:
                if best is None or te["mean"] - b_te > best[1]:
                    best = (h, te["mean"] - b_te)
        row["confirmed_h"], row["edge_test"] = (best[0], best[1]) if best else (None, None)
        weights[f"{name}:{side}"] = {"confirmed": bool(best), "horizon": best[0] if best else None, "edge": round(best[1], 5) if best else 0.0}
        rows.append(row)
    f = lambda s: "–" if not s else f"{s['mean'] * 100:+.2f}% / {s['hit'] * 100:.0f}% / n={s['n']}"
    md = [f"# Eventstudie {tf} ({time.strftime('%Y-%m-%d')})", "", f"Coins: {', '.join(used)}. Rendite netto nach 0,13 % Kosten, je Signal: Ø / Trefferquote / Anzahl.",
          "'Zufall' = Ø aller Kerzen in dieser Richtung im selben Zeitraum.", ""]
    for h in (12, 24):
        md += [f"## Horizont {h} Kerzen", "", "| Signal | Richtung | Training | Test | Zufall Test | bestätigt |", "|---|---|---|---|---|---|"]
        for r in rows:
            b = stats(base[r["side"]]["test"][h])
            md.append(f"| {r['event']} | {r['side']} | {f(r[f'train{h}'])} | {f(r[f'test{h}'])} | {b['mean'] * 100:+.2f}% | {'JA' if r['confirmed_h'] == h else ''} |")
        md.append("")
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f"event_study_{tf}.md"), "w").write("\n".join(md))
    json.dump(weights, open(os.path.join(OUT, f"weights_{tf}.json"), "w"), indent=1)
    print("\n".join(md))
    return weights


if __name__ == "__main__":
    allw = {}
    for tf in (sys.argv[1:] or ["1h", "4h"]):
        ev, base, used = study(tf)
        allw[tf] = report(tf, ev, base, used)
    p = os.path.join(os.path.dirname(OUT), "..", "chartreader", "weights.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(allw)
    json.dump(old, open(p, "w"), indent=1)
