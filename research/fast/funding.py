#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
funding.py - Blickwinkel "Funding, Ueberhitzung und Gegenbewegung" (Mean Reversion).

Drei Kandidaten, jeweils mit kleinem Gitter, chronologisch 50 % Training / 25 % Validierung / 25 % Test:
  K1  Docht-Kapitulation (Liquidations-Rueckläufer)       1h und 4h, 8 Coins, 8 Varianten je Zeitrahmen
  K2  Ueberdehnungs-Rueckläufer RSI(3) + ATR-Abstand EMA50  4h und 1h, 8 Coins, 8 Varianten je Zeitrahmen
  K3  Premium-Crowding (Hyperliquid fundingHistory)         1h, 10 Coins, 8 Varianten
Gesamt 40 Varianten (5 Läufe x 8). Es wird NICHTS ausserhalb des Gitters getestet.

Ablauf (nur reine Standardbibliothek, kein numpy):
  python3 funding.py --fetch          Funding-Historie holen und in funding_cache/ ablegen (nur K3, sparsam, Pause >= 1 s)
  python3 funding.py --phase dev      nur Training + Validierung ausgeben (Fehlersuche, kein Blick auf Test)
  python3 funding.py --phase final    wie dev, danach Test GENAU EINMAL fuer die im Training gewählte Variante,
                                      schreibt ergebnis_funding.md und ergebnis_funding.json

Regeln gegen Blick in die Zukunft:
  - Signal nur aus Kerzen bis einschliesslich Signalkerze i; Einstieg zum Eröffnungskurs der Kerze i+1 (plus Slippage).
  - Stop und Ziel in derselben Kerze: Stop zuerst. Eröffnet eine Kerze jenseits des Stops: Ausstieg zum Eröffnungskurs.
  - Auswahl der Variante nur im Training (höchster Ø-R bei >= 30 Training-Trades), Validierung bestätigt, Test einmal.
  - Trades werden der Periode ihrer Einstiegskerze zugeordnet (Indexgrenzen 50 % / 75 % je Coin).
"""
import sys, os, json, math, time, random, argparse, bisect, datetime, itertools

sys.path.insert(0, '/root/Claude-Traiding')
from chartreader import data

OUT_DIR = '/root/Claude-Traiding/research/fast'
FCACHE = os.path.join(OUT_DIR, 'funding_cache')

# ---------------------------------------------------------------- Kosten
FEE = 0.00045                       # Gebühr je Seite (Taker)
SLIP = {                            # Slippage je Seite; beim Stop-Ausstieg doppelt
    'BTC': 0.0002, 'ETH': 0.0002, 'BNB': 0.0002,
    'SOL': 0.0003, 'XRP': 0.0003, 'DOGE': 0.0003, 'LINK': 0.0003, 'AVAX': 0.0003, 'DOT': 0.0003,
    'ADA': 0.0004, 'NEAR': 0.0004, 'HYPE': 0.0004,
}
FUND_BASE = 1.25e-5                 # Hyperliquid-Normalfunding je Stunde (Long zahlt, Short erhält)
RISK = 0.02                         # Risiko je Trade (Anteil des Kontos) für die Portfolio-Rechnung
MAXPOS = 4                          # höchstens gleichzeitige Positionen
TFH = {'1h': 1, '4h': 4}
MIN_TRAIN_TRADES = 30               # Auswahlregel: nur Varianten mit mindestens so vielen Training-Trades

COINS_K1 = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'DOT', 'LINK', 'AVAX']
COINS_K2 = ['BTC', 'ETH', 'BNB', 'XRP', 'DOGE', 'LINK', 'AVAX', 'DOT']
COINS_K3 = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'NEAR', 'HYPE']


# ---------------------------------------------------------------- Indikatoren
def wilder_atr(h, l, c, n=14):
    """atr[k] nutzt Kerzen bis einschliesslich k; davor None."""
    m = len(c)
    tr = [h[0] - l[0]] + [max(h[k] - l[k], abs(h[k] - c[k - 1]), abs(l[k] - c[k - 1])) for k in range(1, m)]
    out = [None] * m
    if m < n:
        return out
    a = sum(tr[:n]) / n
    out[n - 1] = a
    for k in range(n, m):
        a = (a * (n - 1) + tr[k]) / n
        out[k] = a
    return out


def ema(c, n):
    m = len(c)
    out = [None] * m
    if m < n:
        return out
    e = sum(c[:n]) / n
    out[n - 1] = e
    al = 2.0 / (n + 1)
    for k in range(n, m):
        e = e + al * (c[k] - e)
        out[k] = e
    return out


def wilder_rsi(c, n=3):
    m = len(c)
    out = [None] * m
    if m <= n:
        return out
    g = [max(c[k] - c[k - 1], 0.0) for k in range(1, m)]
    ls = [max(c[k - 1] - c[k], 0.0) for k in range(1, m)]
    ag = sum(g[:n]) / n
    al = sum(ls[:n]) / n
    out[n] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    for k in range(n + 1, m):
        ag = (ag * (n - 1) + g[k - 1]) / n
        al = (al * (n - 1) + ls[k - 1]) / n
        out[k] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    return out


def quantile(xs, q):
    s = sorted(xs)
    if not s:
        return None
    p = (len(s) - 1) * q
    lo = int(math.floor(p))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (p - lo)


# ---------------------------------------------------------------- Daten
def load_series(coin, tf):
    cs = data.candles(coin, tf, 5000, use_cache=True, max_age=10 ** 9)      # nur Cache, kein Netz
    S = {
        'coin': coin, 'tf': tf, 'tfh': TFH[tf], 'n': len(cs),
        't': [x['t'] for x in cs], 'T': [x['T'] for x in cs],
        'o': [x['o'] for x in cs], 'h': [x['h'] for x in cs], 'l': [x['l'] for x in cs],
        'c': [x['c'] for x in cs], 'v': [x['v'] for x in cs],
    }
    S['s1'] = int(0.5 * S['n'])
    S['s2'] = int(0.75 * S['n'])
    S['atr'] = wilder_atr(S['h'], S['l'], S['c'], 14)
    return S


def period_of(S, e_idx):
    return 'train' if e_idx < S['s1'] else ('val' if e_idx < S['s2'] else 'test')


def fetch_funding(coin, t_start, t_end):
    """fundingHistory seitenweise holen (je Seite ca. 500 Einträge), Pause >= 1,1 s, Cache in funding_cache/."""
    os.makedirs(FCACHE, exist_ok=True)
    path = os.path.join(FCACHE, coin + '.json')
    if os.path.exists(path):
        return json.load(open(path))
    rows, st = [], t_start
    for _ in range(16):
        r = data.post({'type': 'fundingHistory', 'coin': coin, 'startTime': st}, tries=3)
        time.sleep(1.1)
        if not r:
            break
        rows += r
        last = r[-1]['time']
        if len(r) < 500 or last >= t_end:
            break
        st = last + 1
    seen, out = set(), []
    for x in rows:
        if x['time'] in seen:
            continue
        seen.add(x['time'])
        out.append({'time': x['time'], 'fundingRate': float(x['fundingRate']), 'premium': float(x['premium'])})
    out.sort(key=lambda x: x['time'])
    json.dump(out, open(path, 'w'))
    return out


HOUR = 3600000


def prep_funding(S, coin):
    """Hängt z-Wert des Premiums und eine Funding-Summenfunktion an S. Rückgabe: Anzahl fehlender Stunden."""
    path = os.path.join(FCACHE, coin + '.json')
    rows = json.load(open(path))
    hm = {}
    for x in rows:
        hm[(x['time'] // HOUR) * HOUR] = (x['fundingRate'], x['premium'])
    h0 = min(hm)
    h1 = max(max(hm), S['t'][-1])
    grid = list(range(h0, h1 + HOUR, HOUR))
    prem, rate, miss = [], [], 0
    lp, lr = 0.0, FUND_BASE
    for hh in grid:
        if hh in hm:
            lr, lp = hm[hh]
        else:
            miss += 1                                  # Lücke: letzten Wert fortschreiben
        prem.append(lp)
        rate.append(lr)
    S['f_h0'] = h0
    S['f_rows'] = len(rows)
    # Zeit-Prefixsumme der echten Raten (Stundenstempel) für die Funding-Verbuchung
    cum = [0.0]
    for r in rate:
        cum.append(cum[-1] + r)

    def fund_sum(t_from, t_to):
        """Summe der Stundensätze mit Zeitstempel in (t_from, t_to]."""
        a = (t_from - h0) // HOUR           # Stunden mit Index > a
        b = (t_to - h0) // HOUR             # bis einschliesslich b
        a = max(a, -1)
        b = min(b, len(rate) - 1)
        if b <= a:
            return 0.0
        return cum[b + 1] - cum[a + 1]
    S['fund'] = fund_sum
    # z-Wert je Kerze: nur Einträge mit Zeit <= Eröffnungszeit der Kerze (plus 1 h Zusatzverzögerung durch Signal am Schluss)
    z = [None] * S['n']
    for k in range(S['n']):
        idx = (S['t'][k] - h0) // HOUR
        if idx < 167 or idx >= len(prem):
            continue
        w = prem[idx - 167: idx + 1]
        mu = sum(w) / 168.0
        var = sum((x - mu) ** 2 for x in w) / 168.0
        sd = math.sqrt(var)
        p6 = sum(prem[idx - 5: idx + 1]) / 6.0
        z[k] = 0.0 if sd == 0 else (p6 - mu) / sd
    S['z'] = z
    return miss


# ---------------------------------------------------------------- Trade-Simulation (gemeinsam)
def sim_trade(S, side, i, stop, target, maxhold, close_exit=None, fund=None):
    """Einstieg zum Eröffnungskurs von i+1. Rückgabe: Trade-Dict (R netto nach Kosten, Rg brutto)."""
    n = S['n']
    coin = S['coin']
    o, h, l, c, t, T = S['o'], S['h'], S['l'], S['c'], S['t'], S['T']
    e = i + 1
    e0 = o[e]
    slip = SLIP[coin]
    ef = e0 * (1 + side * slip)                         # Einstiegsfüllung inkl. Slippage
    risk = abs(ef - stop)                               # 1 R
    last = min(e + maxhold - 1, n - 1)
    xp = xt = None
    why = None
    stopexit = False
    k = e
    for k in range(e, last + 1):
        if k > e and side * (o[k] - stop) <= 0:         # Eröffnung jenseits des Stops
            xp, xt, why, stopexit = o[k], t[k], 'stop_luecke', True
            break
        hit_stop = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hit_stop:                                    # Stop zuerst
            xp, xt, why, stopexit = stop, T[k] + 1, 'stop', True
            break
        if target is not None:
            hit_t = (h[k] >= target) if side == 1 else (l[k] <= target)
            if hit_t:
                xp, xt, why = target, T[k] + 1, 'ziel'
                break
        if k == last:
            xp, xt = c[k], T[k] + 1
            why = 'zeit' if (k - e + 1) == maxhold else 'ende'
            break
        if close_exit is not None and close_exit(k):    # Schlusskurs-Signal: Ausstieg zum Eröffnungskurs der nächsten Kerze
            xp, xt, why = o[k + 1], t[k + 1], 'mittel'
            if side * (xp - stop) <= 0:
                stopexit = True
            break
    sx = slip * (2 if stopexit else 1)
    xf = xp * (1 - side * sx)
    if fund is None:
        fsum = FUND_BASE * (xt - t[e]) / HOUR
    else:
        fsum = fund(t[e], xt)
    fcost = side * fsum * e0                            # Long zahlt bei positivem Satz, Short erhält
    net = side * (xf - ef) - FEE * (ef + xf) - fcost
    gross = side * (xp - e0)
    return {
        'coin': coin, 'side': side, 'sig_i': i, 'e_idx': e, 'exit_idx': k,
        'entry_t': t[e], 'exit_t': xt, 'R': net / risk, 'Rg': gross / risk,
        'why': why, 'hold': k - e + 1, 'per': period_of(S, e),
    }


# ---------------------------------------------------------------- Kandidat 1: Docht-Kapitulation
def run_k1(S, params):
    Rm, Vm, Km = params
    n = S['n']
    o, h, l, c, v, atr = S['o'], S['h'], S['l'], S['c'], S['v'], S['atr']
    out = []
    i = 50
    while i < n - 1:
        a = atr[i - 1]                                  # ATR bis i-1 (Signalkerze nicht eingerechnet)
        rng = h[i] - l[i]
        if a and rng > 0 and rng >= Rm * a:
            vol48 = sum(v[i - 48:i]) / 48.0
            if v[i] >= Vm * vol48:
                lw = (min(o[i], c[i]) - l[i]) / rng
                uw = (h[i] - max(o[i], c[i])) / rng
                is_long = lw >= 0.5 and l[i] < min(l[i - 24:i])
                is_short = uw >= 0.5 and h[i] > max(h[i - 24:i])
                if is_long != is_short:                 # beide Seiten gleichzeitig = mehrdeutig, überspringen
                    side = 1 if is_long else -1
                    stop = l[i] - 0.25 * a if side == 1 else h[i] + 0.25 * a
                    e0 = o[i + 1]
                    rk = side * (e0 - stop)
                    if 0 < rk <= 3 * a:
                        target = e0 + side * Km * a
                        tr = sim_trade(S, side, i, stop, target, 12)
                        out.append(tr)
                        i = tr['exit_idx']
                        continue
        i += 1
    return out


GRID_K1 = list(itertools.product((1.5, 2.0), (2.0, 2.5), (1.5, 2.5)))


def lab_k1(p):
    return f"Range>={p[0]}ATR Vol>={p[1]}x Ziel={p[2]}ATR"


# ---------------------------------------------------------------- Kandidat 2: Ueberdehnung RSI3 / EMA50
def prep_k2(S):
    S['ema20'] = ema(S['c'], 20)
    S['ema50'] = ema(S['c'], 50)
    S['ema200'] = ema(S['c'], 200)
    S['rsi3'] = wilder_rsi(S['c'], 3)


def run_k2(S, params):
    D, filt, tgt = params
    n = S['n']
    o, h, l, c, atr = S['o'], S['h'], S['l'], S['c'], S['atr']
    e50, e200, rsi = S['ema50'], S['ema200'], S['rsi3']
    et = S['ema20'] if tgt == 'EMA20' else S['ema50']
    hold = 12 if S['tf'] == '4h' else 24
    out = []
    lock = {1: -100, -1: -100}
    i = 215
    while i < n - 1:
        a = atr[i]                                      # ATR bis einschliesslich Signalkerze
        if a and e50[i] is not None and rsi[i] is not None and e200[i - 12] is not None:
            dist = (c[i] - e50[i]) / a
            side = 0
            if dist <= -D and rsi[i] <= 10:
                side = 1
            elif dist >= D and rsi[i] >= 90:
                side = -1
            if side and filt == 'Trend':
                if side == 1 and not e200[i] > e200[i - 12]:
                    side = 0
                if side == -1 and not e200[i] < e200[i - 12]:
                    side = 0
            if side and i >= lock[side] + 6:
                stop = min(l[i - 5:i + 1]) - 0.25 * a if side == 1 else max(h[i - 5:i + 1]) + 0.25 * a
                e0 = o[i + 1]
                rk = side * (e0 - stop)
                if 0 < rk <= 3 * a:
                    sd = side
                    ce = (lambda k: c[k] >= et[k]) if sd == 1 else (lambda k: c[k] <= et[k])
                    tr = sim_trade(S, side, i, stop, None, hold, close_exit=ce)
                    out.append(tr)
                    lock[side] = tr['exit_idx']
                    i = tr['exit_idx']
                    continue
        i += 1
    return out


GRID_K2 = list(itertools.product((2.5, 3.5), ('kein', 'Trend'), ('EMA20', 'EMA50')))


def lab_k2(p):
    return f"D>={p[0]}ATR Trendfilter={p[1]} Ziel={p[2]}"


# ---------------------------------------------------------------- Kandidat 3: Premium-Crowding
def run_k3(S, params):
    Z, E, gate = params
    n = S['n']
    o, h, l, c, atr, z = S['o'], S['h'], S['l'], S['c'], S['atr'], S['z']
    out = []
    i = 240
    while i < n - 1:
        a = atr[i]
        zi = z[i]
        if a and zi is not None:
            side = 0
            mv = c[i] - c[i - 24]
            if zi <= -Z and mv <= -E * a and c[i] > o[i]:
                side = 1
            elif zi >= Z and mv >= E * a and c[i] < o[i]:
                side = -1
            if side and gate == 'Q75':
                w = [atr[j] / c[j] for j in range(max(0, i - 719), i + 1) if atr[j]]
                q = quantile(w, 0.75)
                if a / c[i] < q:
                    side = 0
            if side:
                stop = min(l[i - 11:i + 1]) - 0.25 * a if side == 1 else max(h[i - 11:i + 1]) + 0.25 * a
                e0 = o[i + 1]
                rk = side * (e0 - stop)
                if 0 < rk <= 3 * a:
                    target = e0 + side * 3 * a
                    sd = side
                    ce = (lambda k: z[k] is not None and z[k] >= -0.5) if sd == 1 else (lambda k: z[k] is not None and z[k] <= 0.5)
                    tr = sim_trade(S, side, i, stop, target, 24, close_exit=ce, fund=S['fund'])
                    out.append(tr)
                    i = tr['exit_idx']
                    continue
        i += 1
    return out


GRID_K3 = list(itertools.product((1.5, 2.0), (1.0, 2.0), ('kein', 'Q75')))


def lab_k3(p):
    return f"|z|>={p[0]} Preisweg>={p[1]}ATR Gate={p[2]}"


# ---------------------------------------------------------------- Statistik
def stats(trs):
    n = len(trs)
    if n == 0:
        return {'trades': 0, 'avg_r': None, 'profit_factor': None, 'win_rate': None, 'avg_r_gross': None, 'sum_r': 0.0}
    rs = [t['R'] for t in trs]
    gp = sum(r for r in rs if r > 0)
    gl = -sum(r for r in rs if r < 0)
    return {
        'trades': n, 'avg_r': sum(rs) / n,
        'profit_factor': (gp / gl) if gl > 0 else None,
        'win_rate': sum(1 for r in rs if r > 0) / n,
        'avg_r_gross': sum(t['Rg'] for t in trs) / n,
        'sum_r': sum(rs),
    }


def fmt(x, d=3):
    return '-' if x is None else f"{x:.{d}f}"


def day_of(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime('%Y-%m-%d')


def bootstrap_days(trs, nb=4000, seed=7):
    """Bootstrap nach Kalendertagen (Einstiegstag): 90-%-Intervall für Ø-R. Signale sind marktweit gebündelt."""
    if not trs:
        return None
    days = {}
    for t in trs:
        days.setdefault(day_of(t['entry_t']), []).append(t['R'])
    keys = list(days)
    rng = random.Random(seed)
    means = []
    for _ in range(nb):
        s, cnt = 0.0, 0
        for _ in keys:
            d = days[keys[rng.randrange(len(keys))]]
            s += sum(d)
            cnt += len(d)
        means.append(s / cnt)
    means.sort()
    return {'tage': len(keys), 'lo': means[int(0.05 * nb)], 'hi': means[int(0.95 * nb)]}


def portfolio(trs):
    """Fest 2 % Risiko je Trade (R-basiert), chronologisch über alle Coins, höchstens MAXPOS gleichzeitig."""
    order = sorted(trs, key=lambda t: (t['entry_t'], t['coin']))
    eq = 1.0
    open_pos, events, skipped, taken = [], [], 0, 0

    def settle(upto):
        nonlocal eq
        open_pos.sort(key=lambda p: p['exit_t'])
        while open_pos and (upto is None or open_pos[0]['exit_t'] <= upto):
            p = open_pos.pop(0)
            before = eq
            eq = eq + p['R'] * p['risk_amt']
            events.append((p['exit_t'], before, eq))
    for t in order:
        settle(t['entry_t'])
        if len(open_pos) >= MAXPOS:
            skipped += 1
            continue
        open_pos.append({'exit_t': t['exit_t'], 'R': t['R'], 'risk_amt': RISK * eq})
        taken += 1
    settle(None)
    peak, mdd = 1.0, 0.0
    for _, _, after in events:
        peak = max(peak, after)
        mdd = max(mdd, (peak - after) / peak)
    days = {}
    for tt, before, after in events:
        d = day_of(tt)
        if d not in days:
            days[d] = [before, after]
        else:
            days[d][1] = after
    best = max(((a / b - 1) for b, a in days.values()), default=0.0)
    worst = min(((a / b - 1) for b, a in days.values()), default=0.0)
    return {'return_pct': (eq - 1) * 100, 'max_drawdown_pct': mdd * 100, 'best_day_pct': best * 100,
            'worst_day_pct': worst * 100, 'taken': taken, 'skipped': skipped}


# ---------------------------------------------------------------- Lauf je Kandidat/Zeitrahmen
def run_candidate(key, name, tf, coins, grid, runner, lab, Sd, phase, log):
    """Alle Varianten rechnen, im Training wählen, in Validierung bestätigen, Test einmal (nur final)."""
    res = {'key': key, 'name': name, 'tf': tf, 'coins': coins, 'n_variants': len(grid), 'variants': []}
    allv = {}
    for p in grid:
        per_coin = {c: runner(Sd[c], p) for c in coins}
        allv[p] = per_coin
        row = {'params': list(p), 'label': lab(p)}
        for per in ('train', 'val'):
            pooled = [t for c in coins for t in per_coin[c] if t['per'] == per]
            row[per] = stats(pooled)
        res['variants'].append(row)
    # Auswahl NUR im Training
    ok = [r for r in res['variants'] if r['train']['trades'] >= MIN_TRAIN_TRADES and r['train']['avg_r'] is not None]
    if ok:
        best = max(ok, key=lambda r: r['train']['avg_r'])
        res['selection_note'] = f"höchster Training-Ø-R unter Varianten mit >= {MIN_TRAIN_TRADES} Training-Trades"
    else:
        best = max(res['variants'], key=lambda r: r['train']['trades'])
        res['selection_note'] = f"keine Variante mit >= {MIN_TRAIN_TRADES} Training-Trades; Ersatz: meiste Trades"
    p = tuple(best['params'])
    res['chosen'] = best
    res['chosen_params'] = list(p)
    log(f"\n== {name} [{tf}] Varianten={len(grid)} ==")
    for r in res['variants']:
        mark = ' <== gewählt (Training)' if r is best else ''
        log(f"  {r['label']:<46} Train n={r['train']['trades']:>4} Ø R={fmt(r['train']['avg_r'])} PF={fmt(r['train']['profit_factor'],2)}"
            f" | Val n={r['val']['trades']:>4} Ø R={fmt(r['val']['avg_r'])} PF={fmt(r['val']['profit_factor'],2)}{mark}")
    pc = allv[p]
    res['per_coin_train_val'] = {c: {per: stats([t for t in pc[c] if t['per'] == per]) for per in ('train', 'val')} for c in coins}
    if phase == 'final':
        # TEST: genau einmal, nur die gewählte Variante
        test_tr = [t for c in coins for t in pc[c] if t['per'] == 'test']
        res['test'] = stats(test_tr)
        res['per_coin_test'] = {c: stats([t for t in pc[c] if t['per'] == 'test']) for c in coins}
        res['test_portfolio'] = portfolio(test_tr)
        res['test_bootstrap_days'] = bootstrap_days(test_tr)
        res['test_why'] = {}
        for t in test_tr:
            res['test_why'][t['why']] = res['test_why'].get(t['why'], 0) + 1
        res['test_hold_avg'] = (sum(t['hold'] for t in test_tr) / len(test_tr)) if test_tr else None
        # Nachträgliche Diagnose (keine Parameteränderung): Test ohne den Einstiegstag mit der grössten R-Summe
        dsum = {}
        for t in test_tr:
            dsum[day_of(t['entry_t'])] = dsum.get(day_of(t['entry_t']), 0.0) + t['R']
        if dsum:
            bd = max(dsum, key=dsum.get)
            rest = [t for t in test_tr if day_of(t['entry_t']) != bd]
            res['test_ex_best_day'] = {'tag': bd, 'summe_r': dsum[bd], 'rest': stats(rest)}
        res['test_start'] = {c: day_of(Sd[c]['t'][Sd[c]['s2']]) for c in coins}
        res['test_end'] = {c: day_of(Sd[c]['T'][-1]) for c in coins}
        res['train_span'] = {c: [day_of(Sd[c]['t'][0]), day_of(Sd[c]['t'][Sd[c]['s1'] - 1])] for c in coins}
        res['val_span'] = {c: [day_of(Sd[c]['t'][Sd[c]['s1']]), day_of(Sd[c]['t'][Sd[c]['s2'] - 1])] for c in coins}
        coins_pos = sum(1 for c in coins if res['per_coin_test'][c]['trades'] > 0 and res['per_coin_test'][c]['avg_r'] > 0)
        res['coins_positive'] = coins_pos
        # Verdikt
        tr_, va, te = best['train'], best['val'], res['test']
        cand = (te['avg_r'] is not None and te['avg_r'] > 0 and va['avg_r'] is not None and va['avg_r'] > 0
                and te['trades'] >= 30 and coins_pos >= len(coins) / 2.0)
        neg_early = (tr_['avg_r'] is None or tr_['avg_r'] <= 0 or va['avg_r'] is None or va['avg_r'] <= 0)
        neg_test = te['trades'] >= 30 and te['avg_r'] is not None and te['avg_r'] <= 0
        if cand:
            res['verdict'] = 'edge_candidate'
        elif neg_early or neg_test:
            res['verdict'] = 'no_edge'
        else:
            res['verdict'] = 'inconclusive'
        log(f"  TEST (einmalig, gewählte Variante): n={te['trades']} Ø R={fmt(te['avg_r'])} PF={fmt(te['profit_factor'],2)}"
            f" Coins im Plus {coins_pos}/{len(coins)} -> {res['verdict']}")
    return res


# ---------------------------------------------------------------- Bericht
def md_report(R, extra):
    L = []
    w = L.append
    w("# Ergebnis Funding, Überhitzung und Gegenbewegung (Mean Reversion)\n")
    w("Skript: `research/fast/funding.py`. Alle Zahlen stammen aus dem tatsächlichen Lauf (`--phase final`), nichts geschätzt.\n")
    w("## Kurzfassung\n")
    w("| Lauf | Gewählte Variante (Training) | Train n / Ø R | Val n / Ø R | Test n / Ø R | Test PF | Coins im Plus | Urteil |")
    w("|---|---|---|---|---|---|---|---|")
    for r in R:
        b = r['chosen']
        te = r['test']
        w(f"| {r['name']} {r['tf']} | {b['label']} | {b['train']['trades']} / {fmt(b['train']['avg_r'])} | {b['val']['trades']} / {fmt(b['val']['avg_r'])} | "
          f"{te['trades']} / {fmt(te['avg_r'])} | {fmt(te['profit_factor'],2)} | {r['coins_positive']}/{len(r['coins'])} | **{r['verdict']}** |")
    w("")
    w("Ø R ist der mittlere Gewinn je Trade in R (1 R = Abstand Einstieg zu Stop), netto nach Gebühr, Slippage und Funding. "
      "Vorteil-Kandidat nur, wenn Test-Ø-R > 0 UND Validierung > 0 UND mindestens 30 Test-Trades UND mindestens die Hälfte der Coins im Test im Plus.\n")
    w("## Methode und Ehrlichkeit\n")
    w("- Aufteilung je Coin chronologisch: erste 50 % der Kerzen Training, nächste 25 % Validierung, letzte 25 % Test. Trades gehören zur Periode ihrer Einstiegskerze.")
    w(f"- Auswahl der Variante nur im Training: höchster Ø R unter Varianten mit mindestens {MIN_TRAIN_TRADES} Training-Trades. Validierung bestätigt, Test genau einmal für die gewählte Variante.")
    w("- **Getestete Varianten insgesamt: 40** (5 Läufe zu je 8 Varianten: K1 1h, K1 4h, K2 4h, K2 1h, K3 1h). Je Lauf wird genau eine im Training gewählt. Außerhalb des Gitters wurde nichts probiert (Fehlersuche nur mit Trainings-/Validierungsdaten).")
    w(f"- Kosten je Seite: Gebühr 0,045 % plus Slippage nach Coin (BTC, ETH, BNB 0,02 %; SOL, XRP, DOGE, LINK, AVAX, DOT 0,03 %; ADA, NEAR, HYPE 0,04 %). Beim Stop-Ausstieg doppelte Slippage. Alle Ausstiege (auch Ziel) mit Slippage, also pessimistisch.")
    w(f"- Funding: K1 und K2 mit Normalsatz 1,25e-5 je Stunde (Long zahlt, Short erhält); K3 mit dem echten stündlichen fundingRate aus fundingHistory.")
    w("- Einstieg frühestens zum Eröffnungskurs der Folgekerze; Stop und Ziel in derselben Kerze: Stop zuerst; Eröffnung jenseits des Stops: Ausstieg zum Eröffnungskurs.")
    w(f"- Portfolio-Rechnung: fest {RISK*100:.0f} % des Kontos Risiko je Trade (R-basiert, Konto wächst mit realisierten Ergebnissen), Trades chronologisch über alle Coins, höchstens {MAXPOS} gleichzeitig (weitere werden übersprungen).")
    w("- Bootstrap nach Einstiegstagen (4000 Ziehungen, 90-%-Intervall), weil Signale marktweit gebündelt auftreten.\n")
    for r in R:
        b = r['chosen']
        te = r['test']
        pf = r['test_portfolio']
        bs = r['test_bootstrap_days']
        w(f"## {r['name']} - {r['tf']}\n")
        w(f"Regeln: {r['rules']}\n")
        w(f"Coins ({len(r['coins'])}): {', '.join(r['coins'])}. Varianten in diesem Lauf: {r['n_variants']}. Auswahl: {r['selection_note']}.\n")
        sp = r['train_span'][r['coins'][0]]
        vs = r['val_span'][r['coins'][0]]
        w(f"Zeiträume (Beispiel {r['coins'][0]}): Training {sp[0]} bis {sp[1]}, Validierung {vs[0]} bis {vs[1]}, Test {r['test_start'][r['coins'][0]]} bis {r['test_end'][r['coins'][0]]}.\n")
        w("### Alle Varianten (Training und Validierung)\n")
        w("| Variante | Train n | Train Ø R | Train PF | Val n | Val Ø R | Val PF | |")
        w("|---|---|---|---|---|---|---|---|")
        for v in r['variants']:
            mk = 'gewählt' if v['label'] == b['label'] else ''
            w(f"| {v['label']} | {v['train']['trades']} | {fmt(v['train']['avg_r'])} | {fmt(v['train']['profit_factor'],2)} | "
              f"{v['val']['trades']} | {fmt(v['val']['avg_r'])} | {fmt(v['val']['profit_factor'],2)} | {mk} |")
        w("")
        w(f"### Gewählte Variante: {b['label']}\n")
        w("| Periode | Trades | Ø R netto | Ø R brutto | Trefferquote | Profit-Faktor |")
        w("|---|---|---|---|---|---|")
        for nm, s in (('Training', b['train']), ('Validierung', b['val']), ('Test', te)):
            w(f"| {nm} | {s['trades']} | {fmt(s['avg_r'])} | {fmt(s['avg_r_gross'])} | {fmt(s['win_rate'],2) if s['win_rate'] is not None else '-'} | {fmt(s['profit_factor'],2)} |")
        w("")
        w("### Je Coin (gewählte Variante)\n")
        w("| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |")
        w("|---|---|---|---|---|---|---|")
        for c in r['coins']:
            tv = r['per_coin_train_val'][c]
            ts = r['per_coin_test'][c]
            w(f"| {c} | {tv['train']['trades']} | {fmt(tv['train']['avg_r'])} | {tv['val']['trades']} | {fmt(tv['val']['avg_r'])} | {ts['trades']} | {fmt(ts['avg_r'])} |")
        w("")
        w(f"Test-Ausstiegsarten: {r['test_why']}; mittlere Haltedauer {fmt(r['test_hold_avg'],1)} Kerzen.\n")
        w(f"### Test-Portfolio bei {RISK*100:.0f} % Risiko je Trade\n")
        w(f"- Rendite im Test: **{pf['return_pct']:.2f} %**, größter Rückgang: {pf['max_drawdown_pct']:.2f} %, bester Tag: {pf['best_day_pct']:.2f} %, schlechtester Tag: {pf['worst_day_pct']:.2f} %.")
        w(f"- Gehandelte Trades: {pf['taken']}, wegen Limit von {MAXPOS} gleichzeitigen übersprungen: {pf['skipped']}.")
        xb = r.get('test_ex_best_day')
        if xb:
            w(f"- Diagnose (nachträglich, ohne Parameteränderung): bester Einstiegstag {xb['tag']} trägt {xb['summe_r']:.2f} R; ohne diesen Tag bleiben {xb['rest']['trades']} Test-Trades mit Ø R {fmt(xb['rest']['avg_r'])}.")
        if bs:
            w(f"- Bootstrap nach Tagen (Test, {bs['tage']} Handelstage mit Einstieg): Ø R 90-%-Intervall {bs['lo']:.3f} bis {bs['hi']:.3f}.")
        w(f"- Urteil: **{r['verdict']}** (Coins im Plus {r['coins_positive']} von {len(r['coins'])}; ein Coin ohne Trades zählt nicht als Plus).\n")
        if r.get('extra'):
            w(r['extra'] + "\n")
    w("## Carry-Referenz (nur Rechnung, kein Handel)\n")
    w(extra.get('carry_md', 'nicht berechnet'))
    w("\n## Vorbehalte\n")
    for s in extra['caveats']:
        w(f"- {s}")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--phase', choices=['dev', 'final'], default='dev')
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    out_lines = []

    def log(s):
        print(s)
        out_lines.append(s)

    if args.fetch:
        for c in COINS_K3:
            S = load_series(c, '1h')
            rows = fetch_funding(c, S['t'][0] - 8 * 86400000, S['T'][-1])
            print(c, len(rows), day_of(rows[0]['time']), day_of(rows[-1]['time']))
        return

    Sd1 = {c: load_series(c, '1h') for c in sorted(set(COINS_K1 + COINS_K2 + COINS_K3))}
    Sd4 = {c: load_series(c, '4h') for c in sorted(set(COINS_K1 + COINS_K2))}
    for d in (Sd1, Sd4):
        for c in d:
            prep_k2(d[c])

    # K3: Funding laden (Cache), Coins mit zu wenig Roh-Ereignissen im TRAINING ausschliessen
    k3_info = {}
    miss_total = 0
    for c in COINS_K3:
        if not os.path.exists(os.path.join(FCACHE, c + '.json')):
            print(f"Funding-Cache fehlt für {c}; zuerst --fetch ausführen")
            sys.exit(1)
        miss = prep_funding(Sd1[c], c)
        k3_info[c] = {'fehlende_stunden': miss, 'eintraege': Sd1[c]['f_rows']}
        miss_total += miss
    raw_k3 = {}
    for c in COINS_K3:
        trs = run_k3(Sd1[c], (1.5, 1.0, 'kein'))
        raw_k3[c] = sum(1 for t in trs if t['per'] == 'train')
    k3_coins = [c for c in COINS_K3 if raw_k3[c] >= 5]
    log(f"K3 Roh-Ereignisse im Training (lockerste Variante, Trades): {raw_k3}; gepoolt {sum(raw_k3.values())}; Coins im Lauf: {k3_coins}")

    jobs = [
        ('K1_1h', 'K1 Docht-Kapitulation', '1h', COINS_K1, GRID_K1, run_k1, lab_k1, Sd1,
         "Signalkerze mit Spanne >= Rmult x ATR14 (bis i-1), Volumen >= Vmult x Mittel der 48 Vorkerzen, Docht >= 50 % der Spanne, neues 24-Kerzen-Extrem; "
         "Gegenrichtung zum Docht; Einstieg Eröffnung i+1; Stop hinter Dochtende + 0,25 ATR (Risiko > 3 ATR wird übersprungen); Ziel Einstieg +/- Kmult x ATR; Zeitstopp 12 Kerzen; eine Position je Coin. "
         "Gitter: Rmult {1,5; 2,0} x Vmult {2,0; 2,5} x Kmult {1,5; 2,5}."),
        ('K1_4h', 'K1 Docht-Kapitulation', '4h', COINS_K1, GRID_K1, run_k1, lab_k1, Sd4,
         "Wie K1 1h, aber auf 4h-Kerzen (eigener Lauf, getrennt gemeldet)."),
        ('K2_4h', 'K2 Überdehnung RSI3/EMA50', '4h', COINS_K2, GRID_K2, run_k2, lab_k2, Sd4,
         "Long: (Schluss - EMA50)/ATR <= -D und RSI(3) <= 10; Short spiegelbildlich (>= +D, RSI >= 90). Trendfilter 'Trend': Long nur bei steigender EMA200 (EMA200_i > EMA200_i-12), Short nur bei fallender. "
         "Einstieg Eröffnung i+1; Stop = Extrem der letzten 6 Kerzen -/+ 0,25 ATR (Risiko > 3 ATR übersprungen); Ausstieg zum Eröffnungskurs der Folgekerze, sobald der Schluss das Zielmittel (EMA20 oder EMA50) erreicht; "
         "Zeitstopp 12 Kerzen (4h) bzw. 24 (1h); 6 Kerzen Sperre je Coin und Richtung nach Ausstieg. Gitter: D {2,5; 3,5} x Trendfilter {kein; Trend} x Ziel {EMA20; EMA50}."),
        ('K2_1h', 'K2 Überdehnung RSI3/EMA50', '1h', COINS_K2, GRID_K2, run_k2, lab_k2, Sd1,
         "Wie K2 4h, aber auf 1h-Kerzen (eigener Lauf, getrennt gemeldet)."),
        ('K3_1h', 'K3 Premium-Crowding', '1h', k3_coins, GRID_K3, run_k3, lab_k3, Sd1,
         "Premium aus fundingHistory: z = (Mittel der letzten 6 Premium-Werte - Mittel der letzten 168) / Std. der letzten 168, nur Einträge bis zur Eröffnungszeit der Signalkerze. "
         "Long: z <= -Z und Schluss(i) - Schluss(i-24) <= -E x ATR14 und Schluss > Eröffnung; Short spiegelbildlich. Gate 'Q75': ATR/Kurs im oberen Quartil der letzten 720 Kerzen. "
         "Einstieg Eröffnung i+1; Stop = Extrem der letzten 12 Kerzen -/+ 0,25 ATR (Risiko > 3 ATR übersprungen); Ziel +/- 3 ATR; Ausstieg zum Eröffnungskurs, sobald z auf -0,5 bzw. +0,5 zurück ist; "
         "Zeitstopp 24 Kerzen; echtes stündliches fundingRate verbucht. Gitter: Z {1,5; 2,0} x E {1,0; 2,0} x Gate {kein; Q75}."),
    ]
    results = []
    for key, name, tf, coins, grid, runner, lab, Sd, rules in jobs:
        if args.only and args.only != key:
            continue
        r = run_candidate(key, name, tf, coins, grid, runner, lab, Sd, args.phase, log)
        r['rules'] = rules
        results.append(r)

    if args.phase != 'final':
        return

    # Carry-Referenz (K3-Coins, Testzeitraum): Short-Perp-Seite sammelt fundingRate ein
    carry = {}
    days_t = None
    for c in COINS_K3:
        S = Sd1[c]
        t_from = S['t'][S['s2']]
        t_to = S['T'][-1] + 1
        fs = S['fund'](t_from, t_to)                     # Summe der Stundensätze im Test
        days = (t_to - t_from) / 86400000.0
        cost = 2 * (FEE + SLIP[c])
        carry[c] = {'funding_pct': fs * 100, 'cost_pct': cost * 100, 'netto_pct': (fs - cost) * 100, 'tage': days,
                    'pro_tag_pct': (fs - cost) * 100 / days, 'usd_pro_tag_bei_1000': 1000 * (fs - cost) / days}
    avg_net = sum(v['netto_pct'] for v in carry.values()) / len(carry)
    avg_day = sum(v['pro_tag_pct'] for v in carry.values()) / len(carry)
    cm = ["Annahme: dauerhaft Short-Perp halten und den Funding-Satz einsammeln (marktneutral wäre eine Spot-Gegenseite nötig, die das Perp-Paper-Konto nicht hat; der Preisrisiko-Anteil ist hier NICHT enthalten). "
          "Rechnung: Summe des echten stündlichen fundingRate im Testzeitraum abzüglich Roundtrip-Kosten (2 x (Gebühr + Slippage)), in Prozent des Einsatzes.\n",
          "| Coin | Test-Tage | Funding-Summe % | Kosten % | Netto % | Netto % je Tag | USD je Tag bei 1000 USD |", "|---|---|---|---|---|---|---|"]
    for c, v in carry.items():
        cm.append(f"| {c} | {v['tage']:.1f} | {v['funding_pct']:.3f} | {v['cost_pct']:.3f} | {v['netto_pct']:.3f} | {v['pro_tag_pct']:.4f} | {v['usd_pro_tag_bei_1000']:.3f} |")
    cm.append(f"\nMittel über {len(carry)} Coins: netto {avg_net:.3f} % im Testfenster, {avg_day:.4f} % je Tag. Das ist weit entfernt von 'schnell viel Geld'.")
    caveats = [
        "Nur ein Marktregime je Zeitrahmen: das 1h-Testfenster (ab ca. Mitte September 2026, rund 52 Tage) enthält keinen großen Crash; die 4h-Validierung enthält den Flush vom 10.10.2025, der 4h-Test beginnt ca. April 2026.",
        "Signale sind marktweit gebündelt (ein Panik-Tag erzeugt Trades in allen Coins); die Zahl unabhängiger Ereignisse ist kleiner als die Tradezahl (siehe Bootstrap nach Tagen).",
        "Hyperliquid-Volumen ist nur das Volumen dieser Börse; echte Liquidationsdaten fehlen, Docht plus Volumen ist ein Stellvertreter.",
        "Mehrfachtest: 40 Varianten insgesamt; die Auswahl je Lauf erfolgte nur im Training, trotzdem bleibt ein Rest-Zufallsrisiko bei kleinen Stichproben.",
        "Premium-Nutzung (K3) ist eine eigene Ableitung aus Doku-Formel und Stichproben; fehlende Funding-Stunden wurden mit dem letzten Wert fortgeschrieben (Anzahl je Coin in ergebnis_funding.json).",
        "Kosten pessimistisch (Slippage auch auf Zielausstiegen, doppelt auf Stops); reale Limit-Ziele wären etwas günstiger, reale Kaskaden-Stops eher schlechter.",
        "Ø R ist nicht gleich Konto-Rendite: bei 2 % Risiko je Trade, höchstens 4 Positionen und wenigen Signalen ist die Kontoentwicklung klein (siehe Portfolio-Abschnitte).",
    ]
    extra = {'carry_md': "\n".join(cm), 'caveats': caveats}
    md = md_report(results, extra)
    open(os.path.join(OUT_DIR, 'ergebnis_funding.md'), 'w').write(md)
    json.dump({'results': results, 'carry': carry, 'k3_info': k3_info, 'k3_raw_train': raw_k3,
               'k3_coins': k3_coins}, open(os.path.join(OUT_DIR, 'ergebnis_funding.json'), 'w'), indent=1, default=str)
    print("\nGeschrieben: ergebnis_funding.md und ergebnis_funding.json")


if __name__ == '__main__':
    main()
