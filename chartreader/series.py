"""Eine Kerzenreihe mit allen Indikatoren und bestätigten Wendepunkten (Swings).

Lookahead-Schutz: Ein Swing mit `left`/`right` Kerzen wird erst `right` Kerzen NACH seinem Extrem bestätigt. Alle Abfragen
`highs(i)` / `lows(i)` liefern nur Swings, die an Position i schon bestätigt waren. So misst die Forschung genau das, was man
live sehen konnte."""
from bisect import bisect_right

from .indicators import atr, bollinger, ema, pct_rank, rsi


class Series:
    def __init__(self, candles, left=3, right=3):
        self.cs, self.left, self.right = candles, left, right
        self.t = [c["t"] for c in candles]
        self.o, self.h, self.l = [c["o"] for c in candles], [c["h"] for c in candles], [c["l"] for c in candles]
        self.c, self.v = [c["c"] for c in candles], [c["v"] for c in candles]
        self.n = len(candles)
        self.atr = atr(self.h, self.l, self.c)
        self.rsi = rsi(self.c)
        self.e20, self.e50, self.e200 = ema(self.c, 20), ema(self.c, 50), ema(self.c, 200)
        self.bb_up, self.bb_lo, self.bb_w = bollinger(self.c)
        self.vr = [0.0] * self.n                      # Volumen relativ zum Schnitt der 20 Kerzen davor
        for i in range(self.n):
            w = self.v[max(0, i - 20):i]
            self.vr[i] = self.v[i] / (sum(w) / len(w)) if w and sum(w) > 0 else 1.0
        self._hi, self._lo = [], []                   # (Position, Preis)
        for i in range(left, self.n - right):
            win_h, win_l = self.h[i - left:i + right + 1], self.l[i - left:i + right + 1]
            if self.h[i] == max(win_h) and all(self.h[i] > x for x in self.h[i - left:i]):
                self._hi.append((i, self.h[i]))
            if self.l[i] == min(win_l) and all(self.l[i] < x for x in self.l[i - left:i]):
                self._lo.append((i, self.l[i]))
        self._hi_conf = [i + right for i, _ in self._hi]   # ab dieser Position bestätigt
        self._lo_conf = [i + right for i, _ in self._lo]

    def highs(self, i, k=None):
        """Bestätigte Swing-Hochs bis Position i (älteste zuerst), optional nur die letzten k."""
        m = bisect_right(self._hi_conf, i)
        return self._hi[max(0, m - k):m] if k else self._hi[:m]

    def lows(self, i, k=None):
        m = bisect_right(self._lo_conf, i)
        return self._lo[max(0, m - k):m] if k else self._lo[:m]

    def new_swing_at(self, i):
        """(Hoch, Tief), das genau an Position i bestätigt wurde (sonst None)."""
        j = bisect_right(self._hi_conf, i)
        hi = self._hi[j - 1] if j and self._hi_conf[j - 1] == i else None
        m = bisect_right(self._lo_conf, i)
        lo = self._lo[m - 1] if m and self._lo_conf[m - 1] == i else None
        return hi, lo

    def bbw_rank(self, i):
        return pct_rank(self.bb_w, i)
