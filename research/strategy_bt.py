"""Vollständiger Backtest der Chart-Lesestrategie (Einstieg am Ereignis, Stop = Ungültigkeits-Niveau aus dem Chart, Ausstieg nach Chart).

Keine Prozent-Stops: Der Stop liegt hinter dem letzten Swing oder dem Extrem der Signalkerze (plus k x ATR Puffer), der Ausstieg ist
  zone   nächste Gegenzone (nur wenn mindestens 1 R entfernt)
  trail  Stop wandert auf das jeweils letzte bestätigte Swing-Tief/-Hoch der Einstiegsebene
  flip   Schluss, sobald die Struktur der Einstiegsebene gegen die Position dreht
Einheit der Ergebnisse ist R = Abstand Einstieg bis Stop. Kosten: Gebühr 2 x 0,045 %, Slippage 0,02 % je Seite, Funding.
Kein Blick in die Zukunft: alles an Kerze i nutzt nur bestätigte Swings und Kerzen bis i. Gleiche Kerze Stop und Ziel: Stop zuerst.
"""
import itertools
import os
import sys
from bisect import bisect_right

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader.events import detect
from chartreader.structure import nearest_zones, trend_at

FEE2, SLIP, FUND_H = 0.0009, 0.0002, 0.0000125
STRUCT, REJ, REV = {"bos", "bos_volume", "choch"}, {"pullback_rejection", "zone_rejection"}, {"sweep_reclaim", "rsi_divergence", "choch"}
EVSETS = {"all": None, "structure": STRUCT, "rejection": REJ, "reversal": REV}
TREND_W = {"1h": [("own", 1.0), ("4h", 2.0), ("1d", 3.0)], "4h": [("own", 2.0), ("1d", 3.0)]}
HOURS = {"1h": 1, "4h": 4}
MAXHOLD = {"1h": 120, "4h": 60}
GRID = {"ev_set": list(EVSETS), "T": [3.0, 4.5, 6.0], "ev_w": [1.5, 3.0], "k": [0.25, 0.75], "stop_ref": ["bar", "swing"], "exit": ["zone", "trail", "flip"]}


class Prep:
    """Alle Chart-Daten je Ereignis-Kerze einmal berechnen, damit viele Parametersätze schnell getestet werden können."""

    def __init__(self, tf, S, htfs):
        self.tf, self.S, self.bars = tf, S, []
        ends = {name: [c["T"] for c in H.cs] for name, H in htfs.items()}
        for i in range(210, S.n - 2):
            evs = detect(S, i)
            if not evs:
                continue
            tr = {"own": trend_at(S, i)}
            for name, H in htfs.items():
                j = bisect_right(ends[name], S.cs[i]["T"]) - 1
                tr[name] = trend_at(H, j) if j >= 30 else "range"
            sup, res = nearest_zones(S, i)
            hs, ls = S.highs(i, 1), S.lows(i, 1)
            self.bars.append({"i": i, "evs": evs, "tr": tr, "sup": sup, "res": res, "sh": hs[-1][1] if hs else None, "sl": ls[-1][1] if ls else None})


def simulate(P, p):
    """Alle Trades eines Parametersatzes: Liste (Einstiegszeit ms, R netto, Stunden, Richtung)."""
    S, trades, busy = P.S, [], -1
    allowed = EVSETS[p["ev_set"]]
    for b in P.bars:
        i = b["i"]
        if i <= busy:
            continue
        best = None
        for side in ("long", "short"):
            evn = [e for e, s in b["evs"] if s == side and (allowed is None or e in allowed)]
            if not evn:
                continue
            want = "up" if side == "long" else "down"
            sc = sum(w for name, w in TREND_W[P.tf] if b["tr"].get(name) == want) + p["ev_w"] * min(2, len(evn))
            if sc >= p["T"] and (best is None or sc > best[1]):
                best = (side, sc)
        if not best:
            continue
        long = best[0] == "long"
        entry = S.c[i] * (1 + SLIP if long else 1 - SLIP)
        a = max(S.atr[i], 1e-12)
        swing = b["sl"] if long else b["sh"]
        ok_swing = swing is not None and ((swing < S.c[i]) if long else (swing > S.c[i]))
        ref = swing if (p["stop_ref"] == "swing" and ok_swing) else (S.l[i] if long else S.h[i])
        stop = ref - p["k"] * a if long else ref + p["k"] * a
        d = (entry - stop) if long else (stop - entry)
        if d < 0.5 * a or d > 6 * a:
            continue
        target = None
        if p["exit"] == "zone":
            z = b["res"] if long else b["sup"]
            if not z:
                continue
            target = z["low"] if long else z["high"]
            if ((target - entry) if long else (entry - target)) < d:
                continue
        trail, k, exit_px = stop, i + 1, None
        while k < S.n:
            hi, lo = S.h[k], S.l[k]
            if (lo <= trail) if long else (hi >= trail):
                exit_px = min(trail, S.o[k]) if long else max(trail, S.o[k])
                break
            if target is not None and ((hi >= target) if long else (lo <= target)):
                exit_px = target
                break
            if p["exit"] == "trail":
                sw = S.lows(k, 1) if long else S.highs(k, 1)
                if sw:
                    lvl = sw[-1][1]
                    if long and trail < lvl < S.c[k]:
                        trail = lvl
                    elif not long and S.c[k] < lvl < trail:
                        trail = lvl
            elif p["exit"] == "flip" and trend_at(S, k) == ("down" if long else "up"):
                exit_px = S.c[k]
                break
            if k - i >= MAXHOLD[P.tf]:
                exit_px = S.c[k]
                break
            k += 1
        if exit_px is None:
            break
        exit_px *= (1 - SLIP if long else 1 + SLIP)
        hours = (k - i) * HOURS[P.tf]
        gross = ((exit_px - entry) if long else (entry - exit_px)) / d
        cost = (FEE2 + (FUND_H * hours if long else -FUND_H * hours)) * entry / d
        trades.append((S.t[i], gross - cost, hours, best[0], S.t[min(k, S.n - 1)], d / entry))
        busy = k
    return trades


def metrics(trs):
    if not trs:
        return {"n": 0, "mean": 0.0, "win": 0.0, "pf": 0.0, "sum": 0.0, "dd": 0.0}
    r = [t[1] for t in trs]
    gp, gl = sum(x for x in r if x > 0), -sum(x for x in r if x < 0)
    eq = peak = dd = 0.0
    for t in sorted(trs):
        eq += t[1]
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    return {"n": len(r), "mean": sum(r) / len(r), "win": sum(1 for x in r if x > 0) / len(r), "pf": gp / gl if gl else 99.0, "sum": sum(r), "dd": dd}


def combos():
    keys = list(GRID)
    for vals in itertools.product(*[GRID[k] for k in keys]):
        yield dict(zip(keys, vals))


def split(trs, t0, t1):
    """Aufteilung nach Zeit: Training = erste 50 %, Validierung = nächste 25 %, Test = letzte 25 %."""
    a, b = t0 + 0.5 * (t1 - t0), t0 + 0.75 * (t1 - t0)
    return [t for t in trs if t[0] < a], [t for t in trs if a <= t[0] < b], [t for t in trs if t[0] >= b]
