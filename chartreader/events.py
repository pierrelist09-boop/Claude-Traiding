"""Chart-Ereignisse: eine Funktion `detect(S, i)` für Forschung UND Live-Lesen. Rückgabe: Liste (Name, Richtung).

Ereignisse (jeweils Long/Short gespiegelt):
  pullback_rejection  Aufwärts-/Abwärtstrend, Rücksetzer in eine Zone, Ablehnungs-Kerze (Pin oder Umarmung)
  zone_rejection      Ablehnungs-Kerze an einer Zone ohne Trendfilter (Vergleich)
  bos_volume          Strukturbruch in Trendrichtung (Schluss über dem letzten Swing-Hoch) mit Volumenschub
  bos                 dasselbe ohne Volumenfilter (Vergleich)
  choch               erster Schluss gegen die Struktur (Trendwechsel-Signal)
  sweep_reclaim       Liquiditätsjagd: Docht über/unter das letzte Swing-Extrem, Schluss wieder innen
  rsi_divergence      neues tieferes Tief/höheres Hoch im Kurs, aber nicht im RSI (bei Swing-Bestätigung)
  squeeze_break       Ausbruch aus enger Bollinger-Spanne mit Volumen
"""
from .structure import nearest_zones, trend_at


def candle_shape(S, i):
    o, h, l, c = S.o[i], S.h[i], S.l[i], S.c[i]
    rng = max(h - l, 1e-12)
    body = abs(c - o)
    up_w, lo_w = h - max(o, c), min(o, c) - l
    bull_pin = lo_w >= 2 * body and lo_w >= 0.55 * rng and c >= l + 0.5 * rng
    bear_pin = up_w >= 2 * body and up_w >= 0.55 * rng and c <= h - 0.5 * rng
    bull_eng = bear_eng = False
    if i > 0:
        po, pc = S.o[i - 1], S.c[i - 1]
        bull_eng = pc < po and c > o and c >= po and o <= pc and body >= abs(pc - po)
        bear_eng = pc > po and c < o and c <= po and o >= pc and body >= abs(pc - po)
    return {"bull_rej": bull_pin or bull_eng, "bear_rej": bear_pin or bear_eng}


def detect(S, i):
    if i < 60:
        return []
    out, a, c, vr = [], max(S.atr[i], 1e-12), S.c[i], S.vr[i]
    trend = trend_at(S, i)
    hs, ls = S.highs(i, 2), S.lows(i, 2)
    shape = candle_shape(S, i)
    sup, res = nearest_zones(S, i, S.c[i - 1])
    at_sup = sup is not None and S.l[i] <= sup["high"] + 0.25 * a and S.l[i] >= sup["low"] - 1.0 * a and c > sup["low"]
    at_res = res is not None and S.h[i] >= res["low"] - 0.25 * a and S.h[i] <= res["high"] + 1.0 * a and c < res["high"]
    if at_sup and shape["bull_rej"]:
        out.append(("zone_rejection", "long"))
        if trend == "up":
            out.append(("pullback_rejection", "long"))
    if at_res and shape["bear_rej"]:
        out.append(("zone_rejection", "short"))
        if trend == "down":
            out.append(("pullback_rejection", "short"))
    if hs and ls:
        last_h, last_l = hs[-1][1], ls[-1][1]
        prev_c = S.c[i - 1]
        if trend == "up" and c > last_h >= prev_c:
            out.append(("bos", "long"))
            if vr >= 1.5:
                out.append(("bos_volume", "long"))
        if trend == "down" and c < last_l <= prev_c:
            out.append(("bos", "short"))
            if vr >= 1.5:
                out.append(("bos_volume", "short"))
        if trend == "down" and c > last_h >= prev_c:
            out.append(("choch", "long"))
        if trend == "up" and c < last_l <= prev_c:
            out.append(("choch", "short"))
        if S.l[i] < last_l and c > last_l and i - ls[-1][0] <= 40:
            out.append(("sweep_reclaim", "long"))
        if S.h[i] > last_h and c < last_h and i - hs[-1][0] <= 40:
            out.append(("sweep_reclaim", "short"))
    new_h, new_l = S.new_swing_at(i)
    if new_l:
        prev = [x for x in S.lows(i) if x[0] < new_l[0]]
        if prev and new_l[1] < prev[-1][1] and S.rsi[new_l[0]] > S.rsi[prev[-1][0]]:
            out.append(("rsi_divergence", "long"))
    if new_h:
        prev = [x for x in S.highs(i) if x[0] < new_h[0]]
        if prev and new_h[1] > prev[-1][1] and S.rsi[new_h[0]] < S.rsi[prev[-1][0]]:
            out.append(("rsi_divergence", "short"))
    if S.bbw_rank(i - 1) <= 0.2 and vr >= 1.3:
        if c > S.bb_up[i]:
            out.append(("squeeze_break", "long"))
        elif c < S.bb_lo[i]:
            out.append(("squeeze_break", "short"))
    return out
