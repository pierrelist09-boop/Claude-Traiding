"""Steckbrief eines Coins aus der Historie und dem Live-Orderbuch: Schwankung, Gleichlauf mit BTC, Trendneigung, Zonen-Respekt, Handelbarkeit."""
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.events import detect
from chartreader.series import Series
from chartreader.structure import trend_at


def atr_pct(S):
    return statistics.median(S.atr[i] / S.c[i] for i in range(50, S.n)) * 100


def returns(S):
    return {S.t[i]: S.c[i] / S.c[i - 1] - 1 for i in range(1, S.n)}


def corr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 100:
        return None
    x, y = [a[k] for k in ks], [b[k] for k in ks]
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sx, sy = sum((v - mx) ** 2 for v in x) ** 0.5, sum((v - my) ** 2 for v in y) ** 0.5
    return sum((p - mx) * (q - my) for p, q in zip(x, y)) / (sx * sy) if sx and sy else None


def profile(coin, btc_1h=None):
    S1, S4, SD = (Series(data.candles(coin, tf, 5000, use_cache=True)) for tf in ("1h", "4h", "1d"))
    r4 = [S4.c[i] / S4.c[i - 1] - 1 for i in range(1, S4.n)]
    m = sum(r4) / len(r4)
    ac = sum((r4[i] - m) * (r4[i - 1] - m) for i in range(1, len(r4))) / sum((x - m) ** 2 for x in r4)
    tr = [trend_at(S4, i) for i in range(210, S4.n)]
    # Zonen-Respekt: nach einer Ablehnungs-Kerze an einer Zone läuft der Kurs binnen 12 Kerzen 1 ATR in Richtung, bevor er 1 ATR dagegen läuft
    win = tot = 0
    for i in range(210, S4.n - 13):
        for name, side in detect(S4, i):
            if name != "zone_rejection":
                continue
            tot += 1
            a = S4.atr[i]
            for k in range(i + 1, i + 13):
                up, dn = (S4.h[k] - S4.c[i]) / a, (S4.c[i] - S4.l[k]) / a
                fav, adv = (up, dn) if side == "long" else (dn, up)
                if adv >= 1:
                    break
                if fav >= 1:
                    win += 1
                    break
    prof = {"coin": coin, "kerzen_1h": S1.n, "kerzen_4h": S4.n, "kerzen_1d": SD.n,
            "von": __import__("time").strftime("%Y-%m-%d", __import__("time").gmtime(S4.t[0] / 1000)),
            "atr_pct_1h": round(atr_pct(S1), 2), "atr_pct_4h": round(atr_pct(S4), 2), "atr_pct_1d": round(atr_pct(SD), 2),
            "autokorr_4h": round(ac, 3), "trend_anteil_4h": round(sum(1 for t in tr if t != "range") / len(tr), 2),
            "aufwaerts_4h": round(sum(1 for t in tr if t == "up") / len(tr), 2), "abwaerts_4h": round(sum(1 for t in tr if t == "down") / len(tr), 2),
            "zonen_respekt": round(win / tot, 2) if tot else None, "zonen_ablehnungen": tot}
    if btc_1h is not None:
        c = corr(returns(S1), btc_1h)
        prof["korrelation_btc_1h"] = round(c, 2) if c is not None else None
    try:
        ctx = data.context(coin)
        prof.update({"orderbuch_kaeufer_usd": round(ctx["book_bid_usd"]), "orderbuch_verkaeufer_usd": round(ctx["book_ask_usd"]),
                     "spread_pct": round(ctx["spread_pct"], 4), "funding_pro_stunde_pct": round(ctx["funding_per_hour"] * 100, 5),
                     "offenes_volumen_mio": round(ctx["open_interest_usd"] / 1e6, 1), "tagesvolumen_mio": round(ctx["day_volume_usd"] / 1e6, 1)})
    except Exception:  # noqa: BLE001
        pass
    return prof
