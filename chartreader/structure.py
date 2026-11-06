"""Marktstruktur und Zonen aus bestätigten Swings."""


def trend_at(S, i):
    """'up' bei höherem Hoch UND höherem Tief, 'down' bei tieferem Hoch UND tieferem Tief, sonst 'range'."""
    hs, ls = S.highs(i, 2), S.lows(i, 2)
    if len(hs) < 2 or len(ls) < 2:
        return "range"
    up_h, up_l = hs[-1][1] > hs[-2][1], ls[-1][1] > ls[-2][1]
    if up_h and up_l:
        return "up"
    if not up_h and not up_l:
        return "down"
    return "range"


def zones_at(S, i, look=300, k=12, tol=0.5):
    """Preiszonen aus den letzten bestätigten Swings: dicht beieinander liegende Extreme werden zu einer Zone verschmolzen.
    Rückgabe: Liste {low, high, touches, last, kind}, sortiert nach Preis. Breite relativ zur ATR (tol)."""
    pts = [(p, "H") for j, p in S.highs(i, k) if i - j <= look] + [(p, "L") for j, p in S.lows(i, k) if i - j <= look]
    if not pts:
        return []
    a = max(S.atr[i], 1e-12)
    pts.sort()
    groups, cur = [], [pts[0]]
    for p in pts[1:]:
        if p[0] - cur[-1][0] <= tol * a:
            cur.append(p)
        else:
            groups.append(cur)
            cur = [p]
    groups.append(cur)
    return [{"low": min(p for p, _ in g), "high": max(p for p, _ in g), "touches": len(g)} for g in groups]


def nearest_zones(S, i, price=None):
    """(nächste Unterstützung unter dem Preis, nächster Widerstand darüber) als Zonen oder None."""
    price = S.c[i] if price is None else price
    zs = zones_at(S, i)
    below = [z for z in zs if z["high"] <= price + 0.2 * S.atr[i]]
    above = [z for z in zs if z["low"] >= price - 0.2 * S.atr[i]]
    return (max(below, key=lambda z: z["high"]) if below else None), (min(above, key=lambda z: z["low"]) if above else None)
