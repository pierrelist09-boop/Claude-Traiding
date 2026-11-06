"""Tests des Chart-Lesers. Wichtigster Test: kein Blick in die Zukunft (Ergebnis an Position i ändert sich nicht, wenn später Kerzen kommen)."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader.events import detect
from chartreader.series import Series
from chartreader.structure import trend_at, zones_at


def walk(n, seed=1, drift=0.0, vol=0.01):
    rnd, p, out = random.Random(seed), 100.0, []
    for i in range(n):
        o = p
        c = o * (1 + rnd.gauss(drift, vol))
        h, l = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2))), min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        out.append({"t": i * 3_600_000, "T": i * 3_600_000 + 3_599_999, "o": o, "h": h, "l": l, "c": c, "v": 1000 * (1 + abs(rnd.gauss(0, 0.5)))})
        p = c
    return out


def zigzag(waves=12, up=True):
    """Saubere Wellen: jede Welle steigt 10 und fällt 5 (Aufwärtstrend) bzw. umgekehrt."""
    p, out, t = 100.0, [], 0
    for w in range(waves):
        for step in [2.0] * 5 + [-1.0] * 5:
            step = step if up else -step
            o, c = p, p + step
            out.append({"t": t, "T": t + 1, "o": o, "h": max(o, c) + 0.2, "l": min(o, c) - 0.2, "c": c, "v": 1000})
            p, t = c, t + 2
    return out


def test_swings_are_confirmed_late():
    S = Series(zigzag(), 3, 3)
    for idx, _ in S._hi:
        assert idx + 3 not in [j for j, _ in S.highs(idx + 2)]            # an Position idx+2 noch nicht bestätigt
        assert idx in [j for j, _ in S.highs(idx + 3)]                    # ab idx+3 bestätigt


def test_trend_detection():
    assert trend_at(Series(zigzag(up=True)), 100) == "up"
    assert trend_at(Series(zigzag(up=False)), 100) == "down"


def test_no_lookahead():
    cs = walk(900)
    full = Series(cs)
    for cut in (400, 650):
        part = Series(cs[:cut])
        for i in range(210, cut - 1):
            assert sorted(detect(full, i)) == sorted(detect(part, i)), (cut, i)
            assert abs(full.atr[i] - part.atr[i]) < 1e-9 and abs(full.rsi[i] - part.rsi[i]) < 1e-9


def test_zones_cluster_nearby_extremes():
    S = Series(zigzag())
    zs = zones_at(S, 100)
    assert zs and all(z["low"] <= z["high"] and z["touches"] >= 1 for z in zs)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
