#!/usr/bin/env python3
"""Prüft das Forward-Journal gegen den echten Kursverlauf: Was tat der Kurs 6/12/24 Stunden nach jeder Lesart?

Auswertung je Tendenz (long/short/neutral) und je Ereignis mit Beweislage. Nur Lesarten, die mindestens 24 Stunden alt sind.
Aufruf: python3 research/forward_check.py"""
import json
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.journal import PATH

H = (6, 12, 24)
COST = 0.0013


def main():
    if not os.path.exists(PATH):
        print("Noch kein Journal. Mit `python -m chartreader BTC --log` füllen."); return
    rows = [json.loads(x) for x in open(PATH) if x.strip()]
    now, cache, res = time.time(), {}, defaultdict(lambda: {h: [] for h in H})
    for r in rows:
        if now - r["ts"] < 24 * 3600:
            continue
        cs = cache.setdefault(r["coin"], data.candles(r["coin"], "1h", 1000))
        after = [c for c in cs if c["T"] / 1000 >= r["ts"]]
        for h in H:
            if len(after) <= h:
                continue
            ret = after[h - 1]["c"] / r["price"] - 1
            if r["bias"] in ("long", "short"):
                res[f"Tendenz {r['bias']}"][h].append((ret if r["bias"] == "long" else -ret) - COST)
            for e in r["events"]:
                if e["bars_ago"] == 0 and e["tf"] in ("1h", "4h"):
                    res[f"{e['event']}:{e['side']} [{e['evidence']}] ({e['tf']})"][h].append((ret if e["side"] == "long" else -ret) - COST)
    print(f"{len(rows)} Lesarten im Journal, ausgewertet nur solche mit >= 24 h Abstand\n")
    print(f"{'Gruppe':58} {'n':>4}  " + "  ".join(f"Ø {h}h" for h in H) + "   Treffer 24h")
    for k, d in sorted(res.items()):
        n = len(d[24]) or len(d[12]) or len(d[6])
        avg = lambda v: f"{sum(v) / len(v) * 100:+6.2f}%" if v else "    – "
        hit = f"{sum(1 for x in d[24] if x > 0) / len(d[24]) * 100:.0f}%" if d[24] else "–"
        print(f"{k:58} {n:4}  " + "  ".join(avg(d[h]) for h in H) + f"   {hit}")


if __name__ == "__main__":
    main()
