#!/usr/bin/env python3
"""Verbesserungsversuch der Trendfolge E mit Ideen aus dem Plugin trading-skills (agiprolabs): Regime-Filter, Zeitstopp, gestaffelter Ausstieg,
Kelly-/Risikogrenzen beim Einsatz und Overfit-Prüfung (Walk-forward-Folds, Deflated Sharpe Ratio).

Alle Hypothesen sind VOR dem Lauf festgelegt (siehe VARIANTS). Basis = E (Donchian 100, Stop 4 ATR, Trail 5 ATR, Tagestrend EMA50/200, RSI-Grenzen),
Kosten wie überall (Gebühr 2 x 0,045 %, Slippage 0,02 %, Funding). 10 Coins, 4h-Daten ca. 833 Tage, 8 Folds nach Einstiegszeit.
Nur Standardbibliothek. Aufruf: python3 research/plugin_test.py [--write]

Abweichung vom Plugin: Dessen Deflated-Sharpe-Skript nutzt als erwartetes Maximum den reinen Normal-Quantil (setzt Varianz der Sharpe-Werte der
Versuche = 1). Für Sharpe-Werte je Trade (klein) ist das falsch und würde alles verwerfen; hier wird wie bei Lopez de Prado mit der echten Streuung
der Versuche skaliert."""
import math
import os
import sys
import time
from bisect import bisect_right
from statistics import NormalDist

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.series import Series
from research import trend_variants as TV

ND = NormalDist()
COINS = TV.COINS
SIM_COINS = "BTC ETH SOL XRP DOGE LINK AVAX HYPE".split()
FEE2, SLIP, FUND_H = TV.FEE2, TV.SLIP, TV.FUND_H
DAY = 86_400_000
FOLDS = 8

# ------------------------------------------------------------------ Regime-Kennzahlen aus dem Plugin (nur Tageskerzen, kausal bis Index j)


def ewm(x, span):
    a, out, m = 2 / (span + 1), [], None
    for v in x:
        m = v if m is None else a * v + (1 - a) * m
        out.append(m)
    return out


def adx_series(h, l, c, period=14):
    n = len(c)
    pdm, mdm, tr = [0.0] * n, [0.0] * n, [0.0] * n
    for i in range(1, n):
        up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
        p, m = max(up, 0.0), max(dn, 0.0)
        if p < m:
            p = 0.0
        if m < p:
            m = 0.0
        pdm[i], mdm[i] = p, m
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    atr, pe, me = ewm(tr, period), ewm(pdm, period), ewm(mdm, period)
    dx = []
    for i in range(n):
        if atr[i] <= 0:
            dx.append(0.0)
            continue
        pdi, mdi = 100 * pe[i] / atr[i], 100 * me[i] / atr[i]
        dx.append(100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi > 0 else 0.0)
    return ewm(dx, period)


def pct_rank_window(x, i, look=100):
    w = x[max(0, i - look + 1):i + 1]
    return sum(1 for v in w if v <= x[i]) / len(w)


def hurst_rs(r, lags=(5, 8, 10, 16, 20, 25, 33, 50)):
    """R/S-Schätzung des Hurst-Exponenten auf einer Renditereihe (Plugin-Methode, wenige feste Lags für Tempo)."""
    pts = []
    for lag in lags:
        vals = []
        for s in range(0, len(r) - lag + 1, lag):
            ch = r[s:s + lag]
            m = sum(ch) / lag
            cum, lo, hi = 0.0, 0.0, 0.0
            for v in ch:
                cum += v - m
                lo, hi = min(lo, cum), max(hi, cum)
            sd = math.sqrt(sum((v - m) ** 2 for v in ch) / (lag - 1))
            if sd > 0 and hi - lo > 0:
                vals.append((hi - lo) / sd)
        if vals:
            pts.append((math.log(lag), math.log(sum(vals) / len(vals))))
    if len(pts) < 5:
        return 0.5
    mx, my = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den if den else 0.5


def daily_regime(SD):
    adx = adx_series(SD.h, SD.l, SD.c)
    volp = [pct_rank_window(SD.atr, j) for j in range(SD.n)]
    ret = [0.0] + [math.log(SD.c[j] / SD.c[j - 1]) for j in range(1, SD.n)]
    hur = [0.5] * SD.n
    for j in range(100, SD.n):
        hur[j] = hurst_rs(ret[j - 99:j + 1])
    return adx, volp, hur


# ------------------------------------------------------------------ E mit optionalen Plugin-Bausteinen


def run(S4, SD, reg, p):
    adx, volp, hur = reg
    ends = [c["T"] for c in SD.cs]
    out, i = [], 210
    while i < S4.n - 2:
        j = bisect_right(ends, S4.cs[i]["T"]) - 1
        if j < 210:
            i += 1
            continue
        up = SD.c[j] > SD.e50[j] > SD.e200[j] and SD.rsi[j] < 75
        dn = SD.c[j] < SD.e50[j] < SD.e200[j] and SD.rsi[j] > 25
        n = p.get("N", 100)
        brk_up, brk_dn = S4.c[i] > max(S4.h[i - n:i]), S4.c[i] < min(S4.l[i - n:i])
        side = "long" if up and brk_up else "short" if dn and brk_dn else None
        if side:
            if p.get("adx") and adx[j] < p["adx"]:
                side = None
            elif p.get("q4") and volp[j] >= 0.70 and adx[j] < 25:
                side = None
            elif p.get("hurst") and hur[j] <= p["hurst"]:
                side = None
        if not side:
            i += 1
            continue
        long = side == "long"
        entry = S4.c[i] * (1 + SLIP if long else 1 - SLIP)
        a = S4.atr[i]
        stop = entry - 4 * a if long else entry + 4 * a
        d = abs(entry - stop)
        if d < 0.5 * a:
            i += 1
            continue
        extreme, trail, k, ex = entry, stop, i + 1, None
        parts = []                                    # (Gewicht, Ausstiegskurs, Bar) für gestaffelte Teilverkäufe
        taken = set()
        while k < S4.n:
            if (S4.l[k] <= trail) if long else (S4.h[k] >= trail):
                ex = min(trail, S4.o[k]) if long else max(trail, S4.o[k])
                break
            if p.get("partial"):
                for mult, w in ((2.0, 0.25), (4.0, 0.25)):
                    lvl = entry + mult * d if long else entry - mult * d
                    if mult not in taken and ((S4.h[k] >= lvl) if long else (S4.l[k] <= lvl)):
                        taken.add(mult)
                        parts.append((w, lvl, k))
                        if mult == 2.0:               # Rest-Stop auf Einstand (Plugin: nach erster Tranche Break-even)
                            trail = max(trail, entry) if long else min(trail, entry)
            extreme = max(extreme, S4.h[k]) if long else min(extreme, S4.l[k])
            new = extreme - 5 * S4.atr[k] if long else extreme + 5 * S4.atr[k]
            trail = max(trail, new) if long else min(trail, new)
            if p.get("tstop") and k - i >= p["tstop"]:
                unreal = ((S4.c[k] - entry) if long else (entry - S4.c[k])) / d
                if unreal < 0:                        # Plugin: Zeitstopp nur, wenn der Trade nicht im Plus ist
                    ex = S4.c[k]
                    break
            jj = bisect_right(ends, S4.cs[k]["T"]) - 1
            if jj >= 0 and ((SD.c[jj] < SD.e50[jj]) if long else (SD.c[jj] > SD.e50[jj])):
                ex = S4.c[k]
                break
            k += 1
        if ex is None:
            break

        def leg(price, bar):
            price *= (1 - SLIP if long else 1 + SLIP)
            hours = (bar - i) * 4
            return ((price - entry) if long else (entry - price)) / d - (FEE2 + (FUND_H * hours if long else -FUND_H * hours)) * entry / d

        w_rest = 1.0 - sum(w for w, _, _ in parts)
        r = sum(w * leg(px, b) for w, px, b in parts) + w_rest * leg(ex, k)
        out.append(dict(t=S4.t[i], R=r, exit=S4.t[min(k, S4.n - 1)], stop=d / entry, side=side))
        i = k + 1
    return out


VARIANTS = [                                       # vorab festgelegt, 8 Versuche inklusive Basis
    ("E  Basis (Donchian 100, Trail 5)", {}),
    ("V1 Regime: Tages-ADX >= 20", dict(adx=20)),
    ("V2 Regime: Tages-ADX >= 25", dict(adx=25)),
    ("V3 Regime: kein 'Chaos' (Vol-Perzentil >= 70 % und ADX < 25)", dict(q4=True)),
    ("V4 Regime: Hurst (100 Tage Rendite) > 0,55", dict(hurst=0.55)),
    ("V5 Zeitstopp 30 Kerzen (5 Tage), nur wenn im Minus", dict(tstop=30)),
    ("V6 Zeitstopp 60 Kerzen (10 Tage), nur wenn im Minus", dict(tstop=60)),
    ("V7 Gestaffelt: 25 % bei 2 R (Rest-Stop Einstand), 25 % bei 4 R", dict(partial=True)),
]

# ------------------------------------------------------------------ Statistik


def moments(x):
    n = len(x)
    m = sum(x) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1)) if n > 1 else 0.0
    if sd == 0:
        return m, 0.0, 0.0, 3.0
    sk = sum(((v - m) / sd) ** 3 for v in x) / n
    ku = sum(((v - m) / sd) ** 4 for v in x) / n
    return m, sd, sk, ku


def sharpe_pt(x):
    m, sd, _, _ = moments(x)
    return m / sd if sd else 0.0


def dsr(trs_R, all_sr):
    """Deflated Sharpe (Lopez de Prado): Wahrscheinlichkeit, dass der echte Sharpe je Trade > erwartetes Maximum unter Nichtwissen liegt."""
    n = len(trs_R)
    m, sd, sk, ku = moments(trs_R)
    sr = m / sd if sd else 0.0
    nt = len(all_sr)
    v = sum((s - sum(all_sr) / nt) ** 2 for s in all_sr) / (nt - 1) if nt > 1 else 0.0
    g = 0.5772156649
    emax = math.sqrt(v) * ((1 - g) * ND.inv_cdf(1 - 1 / nt) + g * ND.inv_cdf(1 - 1 / (nt * math.e))) if nt > 1 else 0.0
    se = math.sqrt(max(1e-12, (1 - sk * sr + (ku - 1) / 4 * sr * sr) / (n - 1)))
    return ND.cdf((sr - emax) / se), sr, emax


def avg(x):
    return sum(x) / len(x) if x else float("nan")


def boot_diff(base, var, t0, t1, blocks_days=14, reps=2000):
    """Block-Bootstrap (14-Tage-Blöcke nach Einstiegszeit) der Differenz Ø R(Variante) - Ø R(Basis). Zufall deterministisch (LCG)."""
    nb = max(1, int((t1 - t0) / (blocks_days * DAY)) + 1)
    sb, nbk = [[0.0, 0] for _ in range(nb)], None
    sv = [[0.0, 0] for _ in range(nb)]
    for tr in base:
        b = int((tr["t"] - t0) / (blocks_days * DAY))
        sb[b][0] += tr["R"]; sb[b][1] += 1
    for tr in var:
        b = int((tr["t"] - t0) / (blocks_days * DAY))
        sv[b][0] += tr["R"]; sv[b][1] += 1
    seed, diffs = 12345, []
    for _ in range(reps):
        idx = []
        for _ in range(nb):
            seed = (1103515245 * seed + 12345) % (2 ** 31)
            idx.append(seed % nb)
        nbs, nbn = sum(sb[k][0] for k in idx), sum(sb[k][1] for k in idx)
        nvs, nvn = sum(sv[k][0] for k in idx), sum(sv[k][1] for k in idx)
        if nbn and nvn:
            diffs.append(nvs / nvn - nbs / nbn)
    diffs.sort()
    return diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs))]


# ------------------------------------------------------------------ Einsatz-Regeln (Kelly, Risikogrenze) auf den E-Trades


def portfolio(trades, rule, eq0=1000.0, max_pos=4, pos_cap=1.5, exp_cap=3.0, risk_cap=None, start=None):
    eq, open_, done, curve, skipped = eq0, [], [], [(start, eq0)], 0

    def settle(upto):
        nonlocal eq
        for p in sorted([p for p in open_ if p["exit"] <= upto], key=lambda p: p["exit"]):
            eq += p["pnl"]
            open_.remove(p)
            done.append(p)
            curve.append((p["exit"], eq))

    for tr in sorted(trades, key=lambda x: x["t"]):
        settle(tr["t"])
        r = rule(tr["t"], [p["R"] for p in done])
        risk_open = sum(p["risk"] for p in open_)
        risk = r * eq
        if risk_cap is not None:
            risk = min(risk, max(0.0, risk_cap * eq - risk_open))
        want = r * eq / tr["stop"]
        notional = min(risk / tr["stop"], pos_cap * eq, exp_cap * eq - sum(p["notional"] for p in open_))
        if len(open_) >= max_pos or notional < 0.25 * want or eq <= 0:
            skipped += 1
            continue
        open_.append({**tr, "notional": notional, "risk": notional * tr["stop"], "pnl": tr["R"] * notional * tr["stop"]})
    settle(10 ** 15)
    peak, dd = eq0, 0.0
    for _, e in curve:
        peak = max(peak, e)
        dd = max(dd, 1 - e / peak)
    years = (max(t for t, _ in curve) - start) / (365.25 * DAY)
    return dict(final=eq, cagr=(eq / eq0) ** (1 / years) - 1 if eq > 0 else -1.0, dd=dd, n=len(done), skipped=skipped)


def kelly_rule(frac, lo=0.005, hi=0.04, min_n=30, fallback=0.01):
    def rule(t, Rs):
        if len(Rs) < min_n:
            return fallback
        m, sd, _, _ = moments(Rs)
        if m <= 0 or sd == 0:
            return lo
        return min(hi, max(lo, frac * m / (sd * sd)))
    return rule


def main():
    write = "--write" in sys.argv
    D = {}
    for c in sorted(set(COINS) | set(SIM_COINS)):
        s4, sd = data.candles(c, "4h", 5000, use_cache=True, max_age=10 ** 9), data.candles(c, "1d", 5000, use_cache=True, max_age=10 ** 9)
        if len(s4) > 700 and len(sd) > 300:
            S4, SD = Series(s4), Series(sd)
            D[c] = (S4, SD, daily_regime(SD))
    SIG = [c for c in COINS if c in D]
    t0 = min(D[c][0].t[210] for c in SIG)
    t1 = max(D[c][0].t[-1] for c in SIG)
    cuts = [t0 + (t1 - t0) * k / FOLDS for k in range(FOLDS + 1)]
    out = [f"# Plugin-Test der Trendfolge E ({time.strftime('%Y-%m-%d', time.gmtime(t0 / 1000))} bis {time.strftime('%Y-%m-%d', time.gmtime(t1 / 1000))}, {len(SIG)} Coins, {FOLDS} Folds)\n"]
    res = {}
    for name, p in VARIANTS:
        trs = [x | dict(coin=c) for c in SIG for x in run(D[c][0], D[c][1], D[c][2], p)]
        res[name] = trs
    base = res[VARIANTS[0][0]]
    all_sr = [sharpe_pt([x["R"] for x in v]) for v in res.values() if len(v) > 5]
    out.append("| Variante | Trades | Ø R | Folds > 0 | Folds besser als E | Δ Ø R zu E (95 %-Block-Bootstrap) | Deflated Sharpe |\n|---|---|---|---|---|---|---|")
    fold_avg = {}
    for name, trs in res.items():
        fa = [avg([x["R"] for x in trs if cuts[k] <= x["t"] < cuts[k + 1]]) for k in range(FOLDS)]
        fold_avg[name] = fa
    for name, trs in res.items():
        Rs = [x["R"] for x in trs]
        pos = sum(1 for v in fold_avg[name] if v == v and v > 0)
        better = sum(1 for k in range(FOLDS) if fold_avg[name][k] == fold_avg[name][k] and fold_avg[VARIANTS[0][0]][k] == fold_avg[VARIANTS[0][0]][k] and fold_avg[name][k] > fold_avg[VARIANTS[0][0]][k])
        if name == VARIANTS[0][0]:
            lo = hi = None
        else:
            lo, hi = boot_diff(base, trs, t0, t1)
        d, sr, emax = dsr(Rs, all_sr)
        out.append(f"| {name} | {len(trs)} | {avg(Rs):+.3f} | {pos}/{FOLDS} | {'–' if name == VARIANTS[0][0] else str(better) + '/' + str(FOLDS)} | "
                   f"{'–' if lo is None else f'{avg(Rs) - avg([x['R'] for x in base]):+.3f} [{lo:+.3f}; {hi:+.3f}]'} | {d:.2f} |")
    out.append(f"\nDeflated Sharpe: Wahrscheinlichkeit, dass der echte Sharpe je Trade größer ist als das beste Zufallsergebnis aus {len(all_sr)} Versuchen (Hürde laut Plugin: > 0,95). "
               "Folds: Ø R je Fold nach Einstiegszeit, leere Folds zählen weder als positiv noch als besser.\n")
    out.append("Ø R je Fold (E / beste Abweichung siehe Tabelle oben):\n\n| Variante | " + " | ".join(f"F{k + 1}" for k in range(FOLDS)) + " |\n|---|" + "---|" * FOLDS)
    for name in res:
        out.append(f"| {name} | " + " | ".join("–" if v != v else f"{v:+.2f}" for v in fold_avg[name]) + " |")

    # ---- Einsatz-Regeln: 8 Coins ab 2024-11-06, nur E-Trades (wie research/simulation.py)
    start = 1730851200000
    sim_trades = [x | dict(coin=c) for c in SIM_COINS if c in D for x in run(D[c][0], D[c][1], D[c][2], {}) if x["t"] >= start]
    sim_trades.sort(key=lambda x: x["t"])
    out.append(f"\n## Einsatz-Regeln auf E ({len(sim_trades)} Trades, 8 Coins, ab 2024-11-06, Konto 1.000 $)\n")
    out.append("| Regel | Endkonto | pro Jahr | größter Rückgang | Trades (übersprungen) |\n|---|---|---|---|---|")
    rules = [("fix 4 % (bisher)", lambda t, R: 0.04, None), ("fix 2 %", lambda t, R: 0.02, None), ("fix 1 %", lambda t, R: 0.01, None),
             ("Kelly 1/4 (laufend aus abgeschlossenen Trades, 0,5 bis 4 %)", kelly_rule(0.25), None),
             ("Kelly 1/2 (laufend, 0,5 bis 4 %)", kelly_rule(0.5), None),
             ("fix 4 %, aber insgesamt höchstens 8 % offenes Risiko", lambda t, R: 0.04, 0.08),
             ("fix 4 %, höchstens 6 % offenes Risiko", lambda t, R: 0.04, 0.06),
             ("fix 2 %, höchstens 6 % offenes Risiko", lambda t, R: 0.02, 0.06)]
    for name, rule, cap in rules:
        r = portfolio(sim_trades, rule, risk_cap=cap, start=start)
        out.append(f"| {name} | {r['final']:,.0f} $ | {r['cagr'] * 100:+.0f} % | {r['dd'] * 100:.0f} % | {r['n']} ({r['skipped']}) |")
    Rs = [x["R"] for x in sim_trades]
    m, sd, _, _ = moments(Rs)
    out.append(f"\nE-Trades dieser Simulation: Ø R {m:+.3f}, Streuung {sd:.2f} R, Trefferquote {sum(1 for v in Rs if v > 0) / len(Rs) * 100:.0f} %. "
               f"Kelly (μ/σ²) wäre voll {m / (sd * sd) * 100:.1f} % Risiko je Trade, 1/4 davon {m / (sd * sd) * 25:.1f} %, 1/2 davon {m / (sd * sd) * 50:.1f} %. "
               "Das Plugin empfiehlt bei weniger als 100 Trades höchstens 1/10 bis 1/4 Kelly.")
    text = "\n".join(out)
    print(text)
    if write:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fast", "ergebnis_plugin.md"), "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
