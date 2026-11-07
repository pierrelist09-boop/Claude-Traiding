#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blickwinkel Ausbruch und Momentum: drei Kandidaten, ein Skript, reine Standardbibliothek.

K1  Squeeze-Ausbruch 4h  (Bollinger-Perzentil + Donchian-Bruch + Volumen, ATR-Trailing)
K2  Eroeffnungsspannen-Ausbruch 1h (00:00-UTC-Anker, 4-h-Spanne, Tagesausstieg)
K3  Relative Staerke Long/Short 4h (volatilitaetsbereinigtes Momentum, dollar-neutral)

Ablauf in ZWEI Stufen, damit der Test-Abschnitt wirklich nur einmal angesehen wird:
  python3 ausbruch.py selbsttest   Plausibilitaets- und Kausalitaetstests (nur synthetische Daten / Trainingsteil)
  python3 ausbruch.py dev          Training + Validierung fuer alle Varianten, Auswahl NUR auf Training,
                                   schreibt auswahl_ausbruch.json. Test wird NICHT angefasst.
  python3 ausbruch.py nachanalyse  reine Konzentrations-Diagnose K3 (gleiche Test-Beine, kein neuer Parameter, Urteil bleibt)
  python3 ausbruch.py md           schreibt nur die Markdown-Datei aus ergebnis_ausbruch.json neu (keine neue Simulation)
  python3 ausbruch.py test         liest die feste Auswahl, rechnet den Test GENAU EINMAL, schreibt
                                   ergebnis_ausbruch.json und ergebnis_ausbruch.md. Bricht ab, wenn schon vorhanden.

Aufteilung je Coin chronologisch nach Kerzenindex: erste 50 % Training, naechste 25 % Validierung, letzte 25 % Test.
Jeder Abschnitt wird getrennt simuliert (Position startet flach, am Abschnittsende wird zwangsgeschlossen bzw. der
Handel nur gewertet, wenn er im Abschnitt endet). Indikatoren sind rein kausal (nur Kerzen bis einschliesslich Signalkerze).
"""
import sys, os, json, math, random, statistics as st, datetime as dt

sys.path.insert(0, '/root/Claude-Traiding')
from chartreader import data

HIER = os.path.dirname(os.path.abspath(__file__))
F_AUSWAHL = os.path.join(HIER, 'auswahl_ausbruch.json')
F_JSON = os.path.join(HIER, 'ergebnis_ausbruch.json')
F_MD = os.path.join(HIER, 'ergebnis_ausbruch.md')

# ---------------------------------------------------------------- Kostenmodell
GEBUEHR = 0.00045            # je Seite
FUND_8H = 0.0001             # 0,01 % je 8 h, nur als Kosten auf Longs (konservativ, keine Gutschrift fuer Shorts)
SLIP_NIEDRIG = 0.0002        # BTC ETH SOL XRP HYPE
SLIP_HOCH = 0.0004           # alle anderen
NIEDRIG_K1 = {'BTC', 'ETH', 'SOL', 'XRP', 'HYPE'}
NIEDRIG_K2 = {'SOL', 'HYPE'}                 # laut Kandidatentext: 0,04 % ausser SOL und HYPE
NIEDRIG_K3 = {'BTC', 'ETH', 'SOL', 'XRP'}    # laut Kandidatentext: sonst 0,04 %

# ---------------------------------------------------------------- Portfolio-Annahmen
RISIKO = 0.02
MAX_POS = 4
MAX_HEBEL = 5.0

MS_H = 3_600_000
MS_4H = 4 * MS_H
MS_D = 24 * MS_H

COINS_K1 = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'LINK', 'AVAX', 'NEAR', 'AAVE', 'HYPE', 'BNB', 'ADA', 'UNI']
COINS_K2 = ['HYPE', 'NEAR', 'AAVE', 'SOL', 'DOGE', 'LINK', 'AVAX', 'UNI', 'ADA']
COINS_K3 = ['AAVE', 'ADA', 'AVAX', 'BNB', 'BTC', 'DOGE', 'ETH', 'LINK', 'NEAR', 'SOL', 'UNI', 'XRP']

GITTER_K1 = [(p, n) for p in (0.15, 0.30) for n in (12, 24)]
GITTER_K2 = [(f, t) for f in ('AUS', 'AN') for t in (1.5, 3.0)]
GITTER_K3 = [(l, h) for l in (18, 42) for h in (6, 18)]

MIN_TRAIN_TRADES = 30        # Auswahl nur unter Varianten mit mindestens so vielen Trainings-Trades

_cache = {}


def lade(coin, tf):
    k = (coin, tf)
    if k not in _cache:
        _cache[k] = data.candles(coin, tf, 5000, use_cache=True, max_age=10 ** 9)
    return _cache[k]


def tstr(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime('%Y-%m-%d')


# ---------------------------------------------------------------- Indikatoren
def wilder_atr(cs, n=14):
    out = [None] * len(cs)
    tr = [0.0] * len(cs)
    for i in range(1, len(cs)):
        tr[i] = max(cs[i]['h'] - cs[i]['l'], abs(cs[i]['h'] - cs[i - 1]['c']), abs(cs[i]['l'] - cs[i - 1]['c']))
    if len(cs) > n:
        a = sum(tr[1:n + 1]) / n
        out[n] = a
        for i in range(n + 1, len(cs)):
            a = (a * (n - 1) + tr[i]) / n
            out[i] = a
    return out


def k1_indikatoren(cs):
    n = len(cs)
    c = [k['c'] for k in cs]
    bbw = [None] * n
    for i in range(19, n):
        w = c[i - 19:i + 1]
        m = sum(w) / 20
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / 20)      # Populations-SD
        bbw[i] = 4 * sd / m
    pr = [None] * n
    for i in range(19 + 180, n):
        b = bbw[i]
        pr[i] = sum(1 for x in bbw[i - 180:i] if x <= b) / 180   # Rang gegen die 180 Vorgaenger (ohne i)
    sq = [None] * n                                              # kleinster PR der Kerzen i-6..i-1
    for i in range(19 + 180 + 6, n):
        sq[i] = min(pr[i - 6:i])
    vm = [None] * n
    for i in range(20, n):
        vm[i] = sum(k['v'] for k in cs[i - 20:i]) / 20           # Volumenmittel i-20..i-1
    hh, ll = {}, {}
    for N in (12, 24):
        h_ = [None] * n
        l_ = [None] * n
        for i in range(N, n):
            h_[i] = max(k['h'] for k in cs[i - N:i])
            l_[i] = min(k['l'] for k in cs[i - N:i])
        hh[N], ll[N] = h_, l_
    return dict(atr=wilder_atr(cs), bbw=bbw, pr=pr, sq=sq, vm=vm, hh=hh, ll=ll)


# ---------------------------------------------------------------- Hilfen: Statistik / Portfolio
def kennzahlen(trades):
    n = len(trades)
    if n == 0:
        return dict(n=0, avg=None, pf=None, win=None, summe=None, brutto=None, kosten=None)
    rs = [t['net_R'] for t in trades]
    gp = sum(r for r in rs if r > 0)
    gl = -sum(r for r in rs if r < 0)
    return dict(n=n, avg=sum(rs) / n, pf=(gp / gl if gl > 0 else None), win=sum(1 for r in rs if r > 0) / n,
                summe=sum(rs), brutto=sum(t['gross_R'] for t in trades) / n, kosten=sum(t['cost_R'] for t in trades) / n)


def bootstrap_ci(trades, B=2000, seed=12345):
    """Wochen-Block-Bootstrap des Mittelwerts von net_R (beruecksichtigt Bündelung der Trades in Wochen)."""
    if not trades:
        return None
    wk = {}
    for t in trades:
        wk.setdefault(t['t_in'] // (7 * MS_D), []).append(t['net_R'])
    ws = list(wk.values())
    rng = random.Random(seed)
    res = []
    for _ in range(B):
        s = 0.0
        c = 0
        for _ in ws:
            w = ws[rng.randrange(len(ws))]
            s += sum(w)
            c += len(w)
        res.append(s / c)
    res.sort()
    return dict(lo=res[int(0.025 * B)], hi=res[int(0.975 * B) - 1], p_pos=sum(1 for x in res if x > 0) / B, wochen=len(ws))


def t_stat(trades):
    if len(trades) < 3:
        return None
    rs = [t['net_R'] for t in trades]
    sd = st.stdev(rs)
    return (sum(rs) / len(rs)) / (sd / math.sqrt(len(rs))) if sd > 0 else None


def portfolio(trades, risiko=RISIKO, max_pos=MAX_POS):
    """Trades chronologisch ueber alle Coins; Risiko je Trade = risiko * aktuelles Konto (Hebel max 5), hoechstens
    max_pos gleichzeitig offen; Trade bei vollem Buch wird uebersprungen. Gewinn/Verlust wird bei Ausstieg gebucht."""
    ts = sorted(trades, key=lambda t: (t['t_in'], t['coin']))
    eq, peak, mdd = 1.0, 1.0, 0.0
    offen = []
    kurve = []
    uebersprungen = 0
    genommen = 0

    def schliesse(bis):
        nonlocal eq, peak, mdd
        offen.sort(key=lambda o: o[0])
        while offen and offen[0][0] <= bis:
            o = offen.pop(0)
            eq += o[1] * o[2] * o[3]
            peak = max(peak, eq)
            mdd = max(mdd, (peak - eq) / peak)
            kurve.append((o[0], eq))

    for t in ts:
        schliesse(t['t_in'])
        if len(offen) >= max_pos:
            uebersprungen += 1
            continue
        r_eff = min(risiko, MAX_HEBEL * t['r0f'])
        offen.append((t['t_out'], eq, r_eff, t['net_R']))
        genommen += 1
    schliesse(float('inf'))
    tage = {}
    for tm, e in kurve:
        tage[tm // MS_D] = e
    beste = schlechteste = None
    vor = 1.0
    for d in sorted(tage):
        r = tage[d] / vor - 1
        beste = r if beste is None else max(beste, r)
        schlechteste = r if schlechteste is None else min(schlechteste, r)
        vor = tage[d]
    return dict(rendite=eq - 1, rueckgang=mdd, bester_tag=beste, schlechtester_tag=schlechteste, genommen=genommen,
                uebersprungen=uebersprungen, handelstage=len(tage))


# ---------------------------------------------------------------- K1: Squeeze-Ausbruch 4h
def k1_position(cs, e, d, S, atr, hi, max_k=30):
    """Position ab Eintrittskerze e (Einstieg zum Eroeffnungskurs). Rueckgabe (k_aus, X, grund, bei_open).
    Stop gilt in der Eintrittskerze selbst; nachgezogener Stop (Chandelier 3 ATR der Signalkerze) gilt erst ab der
    Folgekerze. Stop zuerst; Gap ueber den Stop: Ausstieg zum Eroeffnungskurs; Zeitstopp: Eroeffnung der e+30-Kerze."""
    stop = S
    ext = -1e300 if d == 1 else 1e300
    for k in range(e, hi):
        c = cs[k]
        if k == e + max_k:
            return k, c['o'], 'zeit', True
        if d == 1:
            if c['o'] <= stop:
                return k, c['o'], 'stop', True
            if c['l'] <= stop:
                return k, stop, 'stop', False
            ext = max(ext, c['h'])
            stop = max(stop, ext - 3 * atr)
        else:
            if c['o'] >= stop:
                return k, c['o'], 'stop', True
            if c['h'] >= stop:
                return k, stop, 'stop', False
            ext = min(ext, c['l'])
            stop = min(stop, ext + 3 * atr)
        if k == hi - 1:
            return k, c['c'], 'abschnittsende', False
    raise RuntimeError('k1_position: e >= hi')


def kosten_frac(coin, niedrig, d, kerzen_gehalten, ms_kerze):
    slip = SLIP_NIEDRIG if coin in niedrig else SLIP_HOCH
    f = 2 * (GEBUEHR + slip)
    if d == 1:
        f += FUND_8H * kerzen_gehalten * ms_kerze / (8 * MS_H)
    return f


def trade_bauen(coin, cs, e, k, X, d, E, R0, grund, bei_open, niedrig, ms_kerze, extra=None):
    gehalten = (k - e) + (0 if bei_open else 1)
    gross = d * (X - E) / R0
    cost = kosten_frac(coin, niedrig, d, gehalten, ms_kerze) * E / R0
    t = dict(coin=coin, t_in=cs[e]['t'], t_out=cs[k]['t'] + (0 if bei_open else ms_kerze), d=d, E=E, X=X, R0=R0,
             r0f=R0 / E, gross_R=gross, cost_R=cost, net_R=gross - cost, grund=grund, kerzen=gehalten)
    if extra:
        t.update(extra)
    return t


def k1_handel(coin, cs, ind, P, N, lo, hi):
    out = []
    atr_ = ind['atr']
    warm = 19 + 180 + 6 + 1
    i = max(lo, warm, N + 1)
    while i < hi - 2:
        sq, vm, hhN, llN, atr = ind['sq'][i], ind['vm'][i], ind['hh'][N][i], ind['ll'][N][i], atr_[i]
        if None in (sq, vm, hhN, llN, atr) or sq > P or cs[i]['v'] < 1.2 * vm:
            i += 1
            continue
        c = cs[i]['c']
        d = 1 if c > hhN else (-1 if c < llN else 0)
        if d == 0:
            i += 1
            continue
        e = i + 1
        E = cs[e]['o']
        if d == 1:
            S = max(llN, E - 3 * atr)
            if E - S < atr:
                S = E - atr
        else:
            S = min(hhN, E + 3 * atr)
            if S - E < atr:
                S = E + atr
        R0 = abs(E - S)
        k, X, grund, bei_open = k1_position(cs, e, d, S, atr, hi)
        out.append(trade_bauen(coin, cs, e, k, X, d, E, R0, grund, bei_open, NIEDRIG_K1, MS_4H))
        i = max(k, i + 1)         # naechste Signalkerze frueh. die Ausstiegskerze (Position dann flach)
    return out


def abschnitte_index(n):
    return {'train': (0, n // 2), 'val': (n // 2, (3 * n) // 4), 'test': ((3 * n) // 4, n)}


def k1_lauf(abschnitt, P, N, coins=COINS_K1):
    res = {}
    for coin in coins:
        cs = lade(coin, '4h')
        if ('k1ind', coin) not in _cache:
            _cache[('k1ind', coin)] = k1_indikatoren(cs)
        lo, hi = abschnitte_index(len(cs))[abschnitt]
        res[coin] = k1_handel(coin, cs, _cache[('k1ind', coin)], P, N, lo, hi)
    return res


# ---------------------------------------------------------------- K2: Eroeffnungsspanne 1h
def k2_vorbereiten(coin):
    key = ('k2pre', coin)
    if key in _cache:
        return _cache[key]
    cs = lade(coin, '1h')
    n = len(cs)
    atr = wilder_atr(cs)
    tage = []
    for j in range(n):
        if (cs[j]['t'] // MS_H) % 24 != 0:
            continue
        if j + 24 >= n or cs[j + 24]['t'] != cs[j]['t'] + MS_D:
            continue                                   # Tag nicht vollstaendig (inkl. Ausstiegskerze 00:00 Folgetag)
        orh = max(cs[j + q]['h'] for q in range(4))
        orl = min(cs[j + q]['l'] for q in range(4))
        tage.append(dict(i0=j, orh=orh, orl=orl, br=(orh - orl) / cs[j + 3]['c'], atr=atr[j + 3]))
    for d, tg in enumerate(tage):
        vor = [x['br'] for x in tage[max(0, d - 20):d]]
        tg['med'] = st.median(vor) if len(vor) >= 10 else None
    _cache[key] = (cs, tage)
    return _cache[key]


def k2_position(cs, e, x, d, stop, target):
    """Stop vor Ziel in derselben Kerze; Gap ueber den Stop: Eroeffnungskurs; Zeitausstieg: Eroeffnung Kerze x."""
    for k in range(e, x + 1):
        c = cs[k]
        if k == x:
            return k, c['o'], 'zeit', True
        if d == 1:
            if c['o'] <= stop:
                return k, c['o'], 'stop', True
            if c['l'] <= stop:
                return k, stop, 'stop', False
            if c['h'] >= target:
                return k, target, 'ziel', False
        else:
            if c['o'] >= stop:
                return k, c['o'], 'stop', True
            if c['h'] >= stop:
                return k, stop, 'stop', False
            if c['l'] <= target:
                return k, target, 'ziel', False
    raise RuntimeError('k2_position')


def k2_handel(coin, F, T, lo, hi):
    cs, tage = k2_vorbereiten(coin)
    out = []
    for tg in tage:
        i0 = tg['i0']
        if i0 < lo or i0 + 24 > hi:                    # Tag samt Ausstiegskerze im Abschnitt (hi darf die Folgekerze sein)
            continue
        atr = tg['atr']
        if atr is None:
            continue
        if F == 'AN' and (tg['med'] is None or tg['br'] > tg['med']):
            continue
        up, dn = tg['orh'] + 0.1 * atr, tg['orl'] - 0.1 * atr
        sig = None
        for k in range(i0 + 4, i0 + 16):               # Kerzen mit Beginn 04:00 bis 15:00 UTC
            c = cs[k]['c']
            if c > up:
                sig = (k, 1)
                break
            if c < dn:
                sig = (k, -1)
                break
        if sig is None:
            continue
        k, d = sig
        e = k + 1
        E = cs[e]['o']
        gegen = tg['orl'] if d == 1 else tg['orh']
        R0 = min(max(abs(E - gegen), 0.8 * atr), 2.0 * atr)
        stop = E - d * R0
        target = E + d * T * R0
        k_aus, X, grund, bei_open = k2_position(cs, e, i0 + 24, d, stop, target)
        out.append(trade_bauen(coin, cs, e, k_aus, X, d, E, R0, grund, bei_open, NIEDRIG_K2, MS_H))
    return out


def abschnitte_1h(cs):
    n = len(cs)
    def naechster_tag(i):
        while i < n and (cs[i]['t'] // MS_H) % 24 != 0:
            i += 1
        return i
    b1, b2 = naechster_tag(n // 2), naechster_tag((3 * n) // 4)
    return {'train': (0, b1), 'val': (b1, b2), 'test': (b2, n)}


def k2_lauf(abschnitt, F, T, coins=COINS_K2):
    res = {}
    for coin in coins:
        cs, _ = k2_vorbereiten(coin)
        lo, hi = abschnitte_1h(cs)[abschnitt]
        res[coin] = k2_handel(coin, F, T, lo, hi)
    return res


# ---------------------------------------------------------------- K3: Relative Staerke Long/Short 4h
def k3_daten(coins):
    D = {}
    for c in coins:
        cs = lade(c, '4h')
        D[c] = dict(cs=cs, atr=wilder_atr(cs), lc=[math.log(k['c']) for k in cs], tidx={k['t']: j for j, k in enumerate(cs)})
    tl = sorted(set(t for c in coins for t in D[c]['tidx']))
    return D, tl


def k3_bein(cs, je, H, d, stop):
    """Bein ab Eintrittskerze je; Stop intrakerzig (Stop zuerst), Gap: Eroeffnung; sonst Ausstieg Eroeffnung Kerze je+H."""
    for k in range(je, je + H):
        c = cs[k]
        if d == 1:
            if c['o'] <= stop:
                return k, c['o'], 'stop', True
            if c['l'] <= stop:
                return k, stop, 'stop', False
        else:
            if c['o'] >= stop:
                return k, c['o'], 'stop', True
            if c['h'] >= stop:
                return k, stop, 'stop', False
    return je + H, cs[je + H]['o'], 'zeit', True


def k3_lauf(abschnitt, L, H, coins=COINS_K3, spiegeln=False, min_univ=10):
    """Liefert (beine, korbe). abschnitt: 'train'/'val'/'test' oder 'trval' (Training+Validierung zusammen)."""
    D, tl = k3_daten(coins)
    n = len(tl)
    ab = abschnitte_index(n)
    lo, hi = (ab['train'][0], ab['val'][1]) if abschnitt == 'trval' else ab[abschnitt]
    sicher_min = max(250, L + 1, 61)
    stunde0 = [i for i, t in enumerate(tl) if t % MS_D == 0 and i >= 260]
    if not stunde0:
        return [], []
    beine, korbe = [], []
    te = stunde0[0]
    while te + H <= n - 1:
        T0 = tl[te]
        if te >= lo and te + H <= min(hi, n - 1):
            uni = []
            for c in coins:
                d_ = D[c]
                js = d_['tidx'].get(T0 - MS_4H)
                if js is None or js < sicher_min:
                    continue
                cs = d_['cs']
                if js + 1 + H >= len(cs) or cs[js + 1]['t'] != T0 or cs[js + 1 + H]['t'] != T0 + H * MS_4H:
                    continue
                if d_['atr'][js] is None:
                    continue
                rets = [d_['lc'][m] - d_['lc'][m - 1] for m in range(js - 59, js + 1)]
                sd = st.stdev(rets)
                if sd <= 0:
                    continue
                S = (d_['lc'][js] - d_['lc'][js - L]) / (sd * math.sqrt(L))
                uni.append((S, c, js))
            if len(uni) >= min_univ:
                uni.sort(key=lambda x: x[0], reverse=True)
                top, bot = uni[:3], uni[-3:]
                longs, shorts = (bot, top) if spiegeln else (top, bot)
                legs = []
                for seite, d in ((longs, 1), (shorts, -1)):
                    w = [1.0 / (D[c]['atr'][js] / D[c]['cs'][js]['c']) for _, c, js in seite]
                    sw = sum(w)
                    for (S, c, js), wi in zip(seite, w):
                        cs = D[c]['cs']
                        atr = D[c]['atr'][js]
                        je = js + 1
                        E = cs[je]['o']
                        R0 = 3 * atr
                        stop = E - d * R0
                        k, X, grund, bei_open = k3_bein(cs, je, H, d, stop)
                        tr = trade_bauen(c, cs, je, k, X, d, E, R0, grund, bei_open, NIEDRIG_K3, MS_4H,
                                         extra=dict(w=wi / sw, reb=te, score=S))
                        legs.append(tr)
                beine.extend(legs)
                netto = sum(l['w'] * (l['net_R'] * l['r0f']) for l in legs)
                brutto = sum(l['w'] * (l['gross_R'] * l['r0f']) for l in legs)
                korbe.append(dict(t_in=T0, t_out=T0 + H * MS_4H, netto=netto, brutto=brutto, n=len(legs),
                                  gestoppt=sum(1 for l in legs if l['grund'] == 'stop')))
        te += H
    return beine, korbe


def korb_kennzahlen(korbe):
    n = len(korbe)
    if n == 0:
        return dict(n=0)
    r = [k['netto'] for k in korbe]
    sd = st.stdev(r) if n > 2 else None
    return dict(n=n, netto=sum(r) / n, brutto=sum(k['brutto'] for k in korbe) / n, sd=sd,
                trefferquote=sum(1 for x in r if x > 0) / n, t=(sum(r) / n) / (sd / math.sqrt(n)) if sd else None,
                gestoppt=sum(k['gestoppt'] for k in korbe) / (6 * n))


# ---------------------------------------------------------------- Urteil
def urteil(test_k, val_k, coins_pos, coins_total):
    """Regeln des Auftrags: Kandidat nur wenn Test-Ø R > 0 UND Val > 0 UND >= 30 Test-Trades UND mind. die Haelfte der Coins im Plus."""
    ta, va, tn = test_k['avg'], val_k['avg'], test_k['n']
    if tn < 30:
        return 'inconclusive'
    if ta is None or va is None or ta <= 0 or va <= 0:
        return 'no_edge'
    if coins_pos * 2 >= coins_total:
        return 'edge_candidate'
    return 'inconclusive'


def pro_coin(trades_by_coin):
    return {c: kennzahlen(v) for c, v in trades_by_coin.items()}


def alle(trades_by_coin):
    return [t for v in trades_by_coin.values() for t in v]


# ---------------------------------------------------------------- Selbsttest
def selbsttest():
    ok = True

    def check(name, cond):
        nonlocal ok
        print(('OK    ' if cond else 'FEHLER'), name)
        ok = ok and cond

    def mk(rows):
        return [dict(t=i * MS_4H, T=(i + 1) * MS_4H - 1, o=o, h=h, l=l, c=c, v=1.0) for i, (o, h, l, c) in enumerate(rows)]

    # K1 Long: Stop und Gap
    cs = mk([(100, 101, 99, 100), (100, 102, 99, 101), (101, 101, 95, 96), (96, 97, 90, 91)])
    k, X, g, bo = k1_position(cs, 1, 1, 96, 2.0, 4)
    check('K1 Stop intrakerzig bei Kerze 2 zum Stop-Preis', (k, X, g, bo) == (2, 96, 'stop', False))
    cs = mk([(100, 101, 99, 100), (100, 102, 99, 101), (94, 95, 93, 94), (94, 95, 93, 94)])
    k, X, g, bo = k1_position(cs, 1, 1, 96, 2.0, 4)
    check('K1 Gap unter Stop: Ausstieg zum Eroeffnungskurs', (k, X, g, bo) == (2, 94, 'stop', True))
    # Trailing wirkt erst ab Folgekerze: Kerze 1 macht Hoch 110 -> Stop 110-6=104 gilt ab Kerze 2
    cs = mk([(100, 101, 99, 100), (100, 110, 99, 109), (109, 109, 103, 105), (105, 106, 104, 105)])
    k, X, g, bo = k1_position(cs, 1, 1, 94, 2.0, 4)
    check('K1 Trail erst ab Folgekerze (Tief 103 < 104)', (k, X, g) == (2, 104, 'stop'))
    # Zeitstopp
    cs = mk([(100, 101, 99, 100)] * 40)
    k, X, g, bo = k1_position(cs, 1, 1, 80, 2.0, 40)
    check('K1 Zeitstopp nach 30 Kerzen am Eroeffnungskurs', (k, g, bo) == (31, 'zeit', True))
    # K1 Short Spiegel
    cs = mk([(100, 101, 99, 100), (100, 101, 98, 99), (99, 106, 98, 105)])
    k, X, g, bo = k1_position(cs, 1, -1, 104, 2.0, 3)
    check('K1 Short Stop oben', (k, X, g) == (2, 104, 'stop'))
    # K2 Stop zuerst
    cs = mk([(100, 101, 99, 100), (100, 100, 100, 100), (100, 112, 94, 100), (100, 100, 100, 100)])
    k, X, g, bo = k2_position(cs, 1, 3, 1, 95, 110)
    check('K2 Stop und Ziel in derselben Kerze: Stop zuerst', (k, X, g) == (2, 95, 'stop'))
    k, X, g, bo = k2_position(cs, 1, 3, 1, 90, 110)
    check('K2 Ziel erreicht', (k, X, g) == (2, 110, 'ziel'))
    # K3
    cs = mk([(100, 100, 100, 100), (100, 101, 99, 100), (100, 101, 96, 97), (97, 98, 96, 97)])
    k, X, g, bo = k3_bein(cs, 1, 2, 1, 97)
    check('K3 Bein gestoppt', (k, X, g) == (2, 97, 'stop'))
    k, X, g, bo = k3_bein(cs, 1, 2, 1, 90)
    check('K3 Bein laeuft bis Zeitausstieg', (k, X, g) == (3, 97, 'zeit'))

    # Kausalitaet K1-Indikatoren: auf gekuerzter Reihe identisch (nur Trainingsteil!)
    cs = lade('BTC', '4h')
    train_n = len(cs) // 2
    voll = k1_indikatoren(cs[:train_n])
    for m in (500, 900, 1200):
        kurz = k1_indikatoren(cs[:m])
        for key in ('bbw', 'pr', 'sq', 'vm', 'atr'):
            a, b = voll[key][m - 1], kurz[key][m - 1]
            check(f'K1 Kausalitaet {key}@{m - 1}', (a is None and b is None) or abs(a - b) < 1e-12)
        for N in (12, 24):
            check(f'K1 Kausalitaet hh/ll N={N}@{m - 1}', voll['hh'][N][m - 1] == kurz['hh'][N][m - 1] and voll['ll'][N][m - 1] == kurz['ll'][N][m - 1])
    # K1: Signalkerze darf nicht in die Box eingehen (hh[i] nutzt Kerzen i-N..i-1)
    x = [dict(t=i * MS_4H, T=0, o=100, h=100 + (50 if i == 40 else 1), l=99, c=100, v=1) for i in range(60)]
    ind = k1_indikatoren(x)
    check('K1 Box ohne Signalkerze (hh[40] ohne Hoch der Kerze 40)', ind['hh'][12][40] == 101 and ind['hh'][12][41] == 150)
    # K2 Kausalitaet: Spanne und Median nur aus Vorfeld; Signal-Fenster beginnt 04:00
    cs1, tage = k2_vorbereiten('BTC')
    check('K2 Spanne = Kerzen 00-03 UTC', all(cs1[t['i0']]['t'] % MS_D == 0 and abs(t['orh'] - max(cs1[t['i0'] + q]['h'] for q in range(4))) < 1e-9 for t in tage[:50]))
    check('K2 Median nur aus Vortagen', all(t['med'] is None or abs(t['med'] - st.median([x['br'] for x in tage[max(0, d - 20):d]])) < 1e-12 for d, t in enumerate(tage[:60])))
    # Portfolio
    tr = [dict(coin='A', t_in=0, t_out=10, net_R=1.0, r0f=0.01), dict(coin='B', t_in=1, t_out=11, net_R=-1.0, r0f=0.01)]
    p = portfolio(tr)
    check('Portfolio: 2 Trades, +2 % und -2 % vom Startkonto -> Rendite 0', abs(p['rendite']) < 1e-12 and p['genommen'] == 2)
    tr = [dict(coin=c, t_in=i, t_out=100, net_R=1.0, r0f=0.01) for i, c in enumerate('ABCDE')]
    p = portfolio(tr)
    check('Portfolio: hoechstens 4 gleichzeitig', p['genommen'] == 4 and p['uebersprungen'] == 1)
    print('ALLE TESTS OK' if ok else 'ES GIBT FEHLER')
    return ok


# ---------------------------------------------------------------- Entwicklung (Training + Validierung)
def tab_variante(trades_by_coin):
    return kennzahlen(alle(trades_by_coin))


def entwicklung():
    E = {}
    # K1
    v = {}
    for (P, N) in GITTER_K1:
        key = f'P={P:.2f},N={N}'
        tr, va = k1_lauf('train', P, N), k1_lauf('val', P, N)
        v[key] = dict(param=dict(P=P, N=N), train=tab_variante(tr), val=tab_variante(va),
                      train_coin=pro_coin(tr), val_coin=pro_coin(va))
    E['K1'] = dict(varianten=v)
    # K2
    v = {}
    for (F, T) in GITTER_K2:
        key = f'F={F},T={T}'
        tr, va = k2_lauf('train', F, T), k2_lauf('val', F, T)
        v[key] = dict(param=dict(F=F, T=T), train=tab_variante(tr), val=tab_variante(va),
                      train_coin=pro_coin(tr), val_coin=pro_coin(va))
    E['K2'] = dict(varianten=v)
    # K3
    v = {}
    for (L, H) in GITTER_K3:
        key = f'L={L},H={H}'
        btr, ktr = k3_lauf('train', L, H)
        bva, kva = k3_lauf('val', L, H)
        # Diagnose: gespiegelt (Umkehr), nur Training, keine Auswahlvariante
        bsp, ksp = k3_lauf('train', L, H, spiegeln=True)
        v[key] = dict(param=dict(L=L, H=H), train=kennzahlen(btr), val=kennzahlen(bva),
                      train_korb=korb_kennzahlen(ktr), val_korb=korb_kennzahlen(kva),
                      spiegel_train=kennzahlen(bsp), spiegel_train_korb=korb_kennzahlen(ksp),
                      train_coin=pro_coin(by_coin(btr)), val_coin=pro_coin(by_coin(bva)))
    E['K3'] = dict(varianten=v)
    # Auswahl nur auf Training
    for k in ('K1', 'K2', 'K3'):
        vs = E[k]['varianten']
        kand = {a: b for a, b in vs.items() if b['train']['n'] >= MIN_TRAIN_TRADES and b['train']['avg'] is not None}
        pool = kand if kand else {a: b for a, b in vs.items() if b['train']['avg'] is not None}
        wahl = max(pool, key=lambda a: pool[a]['train']['avg']) if pool else None
        E[k]['auswahl'] = wahl
        E[k]['auswahl_hinweis'] = ('regulaer' if kand else 'KEINE Variante mit genug Trainings-Trades; trotzdem beste gewaehlt')
    # K3: HYPE-Empfindlichkeit (nur Training + Validierung, nicht Test) fuer die gewaehlte Variante
    w = E['K3']['auswahl']
    if w:
        L, H = E['K3']['varianten'][w]['param']['L'], E['K3']['varianten'][w]['param']['H']
        coins13 = COINS_K3 + ['HYPE']
        b13, k13 = k3_lauf('trval', L, H, coins=coins13, min_univ=10)
        b12, k12 = k3_lauf('trval', L, H, coins=COINS_K3, min_univ=10)
        E['K3']['hype_empfindlichkeit'] = dict(mit_hype=kennzahlen(b13), ohne_hype=kennzahlen(b12),
                                              mit_hype_korb=korb_kennzahlen(k13), ohne_hype_korb=korb_kennzahlen(k12))
    return E


def by_coin(trades):
    d = {}
    for t in trades:
        d.setdefault(t['coin'], []).append(t)
    return d


def f(x, d=3, pct=False):
    if x is None:
        return '-'
    return f'{x * 100:.{d}f} %' if pct else f'{x:.{d}f}'


def drucke_dev(E):
    for k in ('K1', 'K2', 'K3'):
        print('=====', k, 'Auswahl (nur Training):', E[k]['auswahl'], '|', E[k]['auswahl_hinweis'])
        for a, b in E[k]['varianten'].items():
            print(f"  {a:16s} train n={b['train']['n']:4d} avgR={f(b['train']['avg'])} PF={f(b['train']['pf'], 2)} | val n={b['val']['n']:4d} avgR={f(b['val']['avg'])} PF={f(b['val']['pf'], 2)}",
                  end='')
            if k == 'K3':
                print(f" | Spiegel-Train n={b['spiegel_train']['n']} avgR={f(b['spiegel_train']['avg'])}", end='')
            print()
    print('K3 HYPE-Empfindlichkeit (Train+Val):', json.dumps(E['K3'].get('hype_empfindlichkeit'), default=str)[:600])


def dev():
    E = entwicklung()
    drucke_dev(E)
    wahl = {k: E[k]['auswahl'] for k in ('K1', 'K2', 'K3')}
    json.dump(dict(auswahl=wahl, dev=E), open(F_AUSWAHL, 'w'), indent=1, default=str)
    print('Auswahl geschrieben:', wahl)


# ---------------------------------------------------------------- Test (genau einmal)
def portfolio_text(p):
    return (f"Rendite {f(p['rendite'], 1, True)}, groesster Rueckgang {f(p['rueckgang'], 1, True)}, bester Tag {f(p['bester_tag'], 2, True)}, "
            f"schlechtester Tag {f(p['schlechtester_tag'], 2, True)}, genommene Trades {p['genommen']}, uebersprungen {p['uebersprungen']}")


def testlauf():
    if os.path.exists(F_JSON):
        sys.exit('ergebnis_ausbruch.json existiert bereits: Test wurde schon einmal angesehen. Abbruch (kein zweiter Blick).')
    sel = json.load(open(F_AUSWAHL))
    E = entwicklung()
    for k in ('K1', 'K2', 'K3'):
        assert E[k]['auswahl'] == sel['auswahl'][k], 'Auswahl hat sich seit dev geaendert'
    R = {'dev': E, 'test': {}}
    # ---- K1
    w = E['K1']['auswahl']
    P, N = E['K1']['varianten'][w]['param']['P'], E['K1']['varianten'][w]['param']['N']
    te = k1_lauf('test', P, N)
    allt = alle(te)
    pc = pro_coin(te)
    cp = sum(1 for c in COINS_K1 if pc[c]['n'] > 0 and pc[c]['avg'] > 0)
    R['test']['K1'] = dict(variante=w, trades=te, kz=kennzahlen(allt), pro_coin=pc, coins_pos=cp, coins_total=len(COINS_K1),
                           ci=bootstrap_ci(allt), t=t_stat(allt), portfolio=portfolio(allt),
                           gruende=count_reasons(allt), lang_kurz=long_short(allt))
    # ---- K2
    w = E['K2']['auswahl']
    F, T = E['K2']['varianten'][w]['param']['F'], E['K2']['varianten'][w]['param']['T']
    te = k2_lauf('test', F, T)
    allt = alle(te)
    pc = pro_coin(te)
    cp = sum(1 for c in COINS_K2 if pc[c]['n'] > 0 and pc[c]['avg'] > 0)
    R['test']['K2'] = dict(variante=w, trades=te, kz=kennzahlen(allt), pro_coin=pc, coins_pos=cp, coins_total=len(COINS_K2),
                           ci=bootstrap_ci(allt), t=t_stat(allt), portfolio=portfolio(allt),
                           gruende=count_reasons(allt), lang_kurz=long_short(allt))
    # ---- K3
    w = E['K3']['auswahl']
    L, H = E['K3']['varianten'][w]['param']['L'], E['K3']['varianten'][w]['param']['H']
    beine, korbe = k3_lauf('test', L, H)
    pc = pro_coin(by_coin(beine))
    cp = sum(1 for c in COINS_K3 if c in pc and pc[c]['n'] > 0 and pc[c]['avg'] > 0)
    R['test']['K3'] = dict(variante=w, trades=beine, kz=kennzahlen(beine), pro_coin=pc, coins_pos=cp, coins_total=len(COINS_K3),
                           ci=bootstrap_ci(beine), t=t_stat(beine), korb=korb_kennzahlen(korbe),
                           portfolio=portfolio(beine, risiko=0.08 / 6, max_pos=6), gruende=count_reasons(beine),
                           lang_kurz=long_short(beine))
    # Urteile
    for k in ('K1', 'K2', 'K3'):
        r = R['test'][k]
        val = E[k]['varianten'][r['variante']]['val']
        r['urteil'] = urteil(r['kz'], val, r['coins_pos'], r['coins_total'])
    # Rohtrades nicht ins JSON (gross), aber Zahlen ja
    slim = json.loads(json.dumps(R, default=str))
    for k in ('K1', 'K2', 'K3'):
        slim['test'][k].pop('trades', None)
    json.dump(slim, open(F_JSON, 'w'), indent=1)
    schreibe_md(R)
    for k in ('K1', 'K2', 'K3'):
        r = R['test'][k]
        print(k, r['variante'], 'Test', r['kz']['n'], 'Trades, Ø R', f(r['kz']['avg']), 'Coins +', r['coins_pos'], '/', r['coins_total'], '->', r['urteil'])
        print('   ', portfolio_text(r['portfolio']))


def count_reasons(trades):
    d = {}
    for t in trades:
        d[t['grund']] = d.get(t['grund'], 0) + 1
    return d


def long_short(trades):
    return dict(long=kennzahlen([t for t in trades if t['d'] == 1]), short=kennzahlen([t for t in trades if t['d'] == -1]))


# ---------------------------------------------------------------- Markdown
def zeile_kz(name, kz):
    return f"| {name} | {kz['n']} | {f(kz['avg'])} | {f(kz['pf'], 2)} | {f(kz['win'], 1, True)} | {f(kz['brutto'])} | {f(kz['kosten'])} |"


def schreibe_md(R):
    E = R['dev']
    bt = lade('BTC', '4h')
    ab4 = abschnitte_index(len(bt))
    b1 = lade('BTC', '1h')
    ab1 = abschnitte_1h(b1)
    L = []
    A = L.append
    A('# Ergebnis Ausbruch und Momentum (Blickwinkel 1 der Schnell-Recherche)')
    A('')
    A('Alle Zahlen stammen aus `research/fast/ausbruch.py` (Standardbibliothek, lokaler Cache, kein Netz). Auswahl der Variante nur auf dem Trainingsteil, '
      'Bestaetigung auf Validierung, der Test-Abschnitt wurde EINMAL gerechnet (das Skript bricht beim zweiten Lauf ab; Ergebnisse stehen in ergebnis_ausbruch.json). '
      'Nach einem reinen Formatierungsfehler beim Schreiben dieser Datei wurde sie aus dem gespeicherten JSON neu erzeugt, ohne Neuberechnung. '
      'Einzige Zweitrechnung auf Test-Daten: die K3-Nachanalyse (gleiche Beine, per assert identisch zum Testlauf, nur Konzentrationsdiagnose). Regeln, Parameter und Urteile wurden nach dem Test nicht geaendert.')
    A('')
    A('## Daten, Aufteilung, Kosten')
    A('')
    A(f"- 4h-Daten (BTC): {tstr(bt[0]['t'])} bis {tstr(bt[-1]['t'])}, {len(bt)} Kerzen. Training {tstr(bt[ab4['train'][0]]['t'])} bis {tstr(bt[ab4['train'][1] - 1]['t'])}, "
      f"Validierung {tstr(bt[ab4['val'][0]]['t'])} bis {tstr(bt[ab4['val'][1] - 1]['t'])}, Test {tstr(bt[ab4['test'][0]]['t'])} bis {tstr(bt[-1]['t'])}. HYPE hat nur 4209 4h-Kerzen (ab 2024-12-05), seine Abschnitte sind entsprechend kuerzer.")
    A(f"- 1h-Daten (BTC): {tstr(b1[0]['t'])} bis {tstr(b1[-1]['t'])}, {len(b1)} Kerzen. Training {tstr(b1[ab1['train'][0]]['t'])} bis {tstr(b1[ab1['train'][1] - 1]['t'])}, "
      f"Validierung {tstr(b1[ab1['val'][0]]['t'])} bis {tstr(b1[ab1['val'][1] - 1]['t'])}, Test {tstr(b1[ab1['test'][0]]['t'])} bis {tstr(b1[-1]['t'])} (Grenzen an 00:00 UTC ausgerichtet).")
    A('- Kosten je Seite: Gebuehr 0,045 % + Slippage (0,02 % fuer BTC/ETH/SOL/XRP/HYPE, 0,04 % sonst; K2: 0,02 % nur SOL und HYPE; K3: 0,02 % nur BTC/ETH/SOL/XRP); '
      'Funding 0,01 % je 8 h als Kosten nur auf Longs (Shorts bekommen keine Gutschrift). Roundtrip also 0,13 % bis 0,17 % plus Funding. Kosten werden in R umgerechnet (Kosten-Anteil am Nominal mal Einstieg / R0) und vom Brutto-R abgezogen.')
    A('- Kein Blick in die Zukunft: Signal nur aus abgeschlossenen Kerzen, Einstieg zum Eroeffnungskurs der Folgekerze, Stop und Ziel in derselben Kerze: Stop zuerst, Gap ueber den Stop: Ausstieg zum Eroeffnungskurs. '
      'Selbsttest (`python3 ausbruch.py selbsttest`) prueft Stop-Reihenfolge, Gap, Trail-Verzoegerung, Zeitstopp, Kausalitaet der Indikatoren auf gekuerzten Reihen und die Portfolio-Mechanik.')
    A('- Abschnitte werden getrennt simuliert (Position startet flach). K1: am Abschnittsende Zwangsschluss zum Schlusskurs. K2: nur Tage, die samt Ausstiegskerze im Abschnitt liegen. K3: nur Rebalances, deren Haltefenster im Abschnitt endet.')
    A('- Zahl der getesteten Varianten: 12 (3 Kandidaten mal 4 Gitterpunkte). Dazu 4 gespiegelte K3-Laeufe als reine Diagnose auf dem Training (nicht waehlbar). Test-Abschnitt: je Kandidat genau eine Variante, einmal.')
    A('- Kandidat-Regel: Test-Ø R nach Kosten > 0 UND Validierung > 0 UND mindestens 30 Test-Trades UND mindestens die Haelfte der Coins im Test im Plus. Sonst `no_edge` oder `inconclusive`.')
    A('- Portfolio-Rechnung (Test): Risiko 2 % des aktuellen Kontos je Trade (Hebel hoechstens 5), Trades chronologisch ueber alle Coins, hoechstens 4 gleichzeitig (weitere uebersprungen), Gewinn/Verlust bei Ausstieg gebucht, '
      'groesster Rueckgang auf dem realisierten Konto. K3 braucht 6 Beine zugleich: dort 8 %/6 = 1,33 % je Bein, hoechstens 6 Beine (gleiches Gesamtrisiko wie 4 mal 2 %).')
    A('')
    A('Uebersicht:')
    A('')
    A('| Kandidat | gewaehlte Variante (Training) | Val Ø R | Test Trades | Test Ø R | Coins im Plus | Rendite Test (2 % Risiko) | Groesster Rueckgang | Bester Tag | Urteil |')
    A('|---|---|---|---|---|---|---|---|---|---|')
    namen = {'K1': 'K1 Squeeze-Ausbruch 4h', 'K2': 'K2 Eroeffnungsspanne 1h', 'K3': 'K3 Relative Staerke L/S 4h'}
    for k in ('K1', 'K2', 'K3'):
        r = R['test'][k]
        val = E[k]['varianten'][r['variante']]['val']
        p = r['portfolio']
        A(f"| {namen[k]} | {r['variante']} | {f(val['avg'])} | {r['kz']['n']} | {f(r['kz']['avg'])} | {r['coins_pos']}/{r['coins_total']} | {f(p['rendite'], 1, True)} | {f(p['rueckgang'], 1, True)} | {f(p['bester_tag'], 2, True)} | **{r['urteil']}** |")
    A('')
    reg = {
        'K1': ('Indikatoren je 4h-Kerze i: SMA20 und Populations-SD der Schlusskurse, Bandbreite BBW = 4 SD / SMA. Perzentil-Rang PR gegen die 180 Vorgaenger. Squeeze aktiv, wenn PR <= P in mindestens einer der Kerzen i-6..i-1. '
               'Box = hoechstes Hoch / tiefstes Tief der N Kerzen i-N..i-1 (ohne i). LONG: Schluss_i > Box-Hoch UND Squeeze UND Volumen_i >= 1,2 mal Mittel der 20 Vorkerzen; SHORT gespiegelt. Einstieg Eroeffnung i+1. '
               'Anfangs-Stop Long = max(Box-Tief, Einstieg - 3 ATR14_i), mindestens 1 ATR Abstand (Short gespiegelt). Ausstieg: Chandelier-Trail (hoechstes Hoch seit Einstieg - 3 ATR14 der Signalkerze, gilt ab Folgekerze) oder Zeitstopp nach 30 Kerzen. Eine Position je Coin.',
               'Gitter P in {0,15; 0,30} mal N in {12; 24}'),
        'K2': ('Je UTC-Tag Spanne aus den 1h-Kerzen 00:00 bis 03:00 UTC (OR_H, OR_L). Signalfenster Kerzen mit Beginn 04:00 bis 15:00 UTC: erster Schluss > OR_H + 0,1 ATR14 (Long) bzw. < OR_L - 0,1 ATR14 (Short), ATR14 der 03:00-Kerze. '
               'Ein Trade je Coin und Tag, Einstieg Eroeffnung der Folgekerze. Filter AN: Spannenbreite <= Median der 20 Vortage (mindestens 10 Vortage noetig). Stop an der Gegenseite der Spanne, Risiko R0 auf 0,8 bis 2,0 ATR14 begrenzt, Ziel = T mal R0, Zeitausstieg 00:00 UTC des Folgetags.',
               'Gitter F in {AUS, AN} mal T in {1,5; 3,0}'),
        'K3': ('Rebalance auf der 4h-Kerze, die um 00:00 UTC schliesst, danach alle H Kerzen. Score = (ln c_t - ln c_(t-L)) / (SD der 60 4h-Log-Renditen mal Wurzel L). Top 3 Long, Bottom 3 Short, Gewicht je Bein proportional 1/ATR14%, '
               'Summe Long = Summe Short (dollar-neutral). Einstieg Eroeffnung der Folgekerze, Bein-Stop 3 ATR14, Ausstieg aller Beine nach H Kerzen zum Eroeffnungskurs. Hauptlauf ohne HYPE (12 Coins, mindestens 10 im Universum).',
               'Gitter L in {18; 42} mal H in {6; 18}'),
    }
    for k in ('K1', 'K2', 'K3'):
        r = R['test'][k]
        A(f'## {namen[k]}')
        A('')
        A('**Regeln.** ' + reg[k][0])
        A('')
        A(f"**Gitter (4 Varianten):** {reg[k][1]}. **Auswahl nur auf Training** (hoechster Ø R nach Kosten bei mindestens {MIN_TRAIN_TRADES} Trainings-Trades): **{r['variante']}** ({E[k]['auswahl_hinweis']}).")
        A('')
        A('Alle Varianten, Training und Validierung (Test nicht angesehen ausser der gewaehlten Variante):')
        A('')
        A('| Variante | Train Trades | Train Ø R | Train PF | Val Trades | Val Ø R | Val PF |' + (' Train gespiegelt (Umkehr) Ø R |' if k == 'K3' else ''))
        A('|---|---|---|---|---|---|---|' + ('---|' if k == 'K3' else ''))
        for a, b in E[k]['varianten'].items():
            extra = f" {f(b['spiegel_train']['avg'])} (n={b['spiegel_train']['n']}) |" if k == 'K3' else ''
            A(f"| {a}{' (gewaehlt)' if a == r['variante'] else ''} | {b['train']['n']} | {f(b['train']['avg'])} | {f(b['train']['pf'], 2)} | {b['val']['n']} | {f(b['val']['avg'])} | {f(b['val']['pf'], 2)} |{extra}")
        A('')
        sel = E[k]['varianten'][r['variante']]
        A(f"**Gewaehlte Variante {r['variante']}, je Coin (Ø R nach Kosten; n = Trades{', bei K3 = Beine' if k == 'K3' else ''}):**")
        A('')
        A('| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R | Test PF |')
        A('|---|---|---|---|---|---|---|---|')
        coins = {'K1': COINS_K1, 'K2': COINS_K2, 'K3': COINS_K3}[k]
        for c in coins:
            tr_, va_, te_ = sel['train_coin'].get(c, dict(n=0, avg=None)), sel['val_coin'].get(c, dict(n=0, avg=None)), r['pro_coin'].get(c, dict(n=0, avg=None, pf=None))
            A(f"| {c} | {tr_['n']} | {f(tr_['avg'])} | {va_['n']} | {f(va_['avg'])} | {te_['n']} | {f(te_['avg'])} | {f(te_.get('pf'), 2)} |")
        A(f"| **gesamt** | {sel['train']['n']} | {f(sel['train']['avg'])} | {sel['val']['n']} | {f(sel['val']['avg'])} | {r['kz']['n']} | {f(r['kz']['avg'])} | {f(r['kz']['pf'], 2)} |")
        A('')
        kz = r['kz']
        A('Test gesamt:')
        A('')
        A('| | Trades | Ø R netto | PF | Trefferquote | Ø R brutto | Ø Kosten (R) |')
        A('|---|---|---|---|---|---|---|')
        A(zeile_kz('alle', kz))
        A(zeile_kz('nur Long', r['lang_kurz']['long']))
        A(zeile_kz('nur Short', r['lang_kurz']['short']))
        ci = r['ci']
        A('')
        A(f"- Ausstiegsgruende im Test: {r['gruende']}. Naive t-Statistik Ø R: {f(r['t'], 2)}. Wochen-Block-Bootstrap 95 %-Intervall fuer Ø R: "
          + (f"[{f(ci['lo'])}; {f(ci['hi'])}] ({ci['wochen']} Wochen, Anteil Resamples > 0: {f(ci['p_pos'], 2)})." if ci else 'nicht berechenbar.'))
        A(f"- Coins im Test im Plus: {r['coins_pos']} von {r['coins_total']}.")
        if k == 'K3':
            kb = r['korb']
            A(f"- Korb-Sicht (dollar-neutral, Gewichte je Seite = 1): {kb['n']} Rebalances, Ø Netto-Rendite je Rebalance {f(kb.get('netto'), 3, True)} (brutto {f(kb.get('brutto'), 3, True)}), Trefferquote {f(kb.get('trefferquote'), 1, True)}, t-Statistik {f(kb.get('t'), 2)}, Anteil gestoppter Beine {f(kb.get('gestoppt'), 1, True)}.")
            h = E['K3'].get('hype_empfindlichkeit')
            if h:
                A(f"- HYPE-Empfindlichkeit (nur Training + Validierung zusammen, Test nicht angefasst): ohne HYPE {h['ohne_hype']['n']} Beine, Ø R {f(h['ohne_hype']['avg'])}; mit HYPE im Universum {h['mit_hype']['n']} Beine, Ø R {f(h['mit_hype']['avg'])}.")
        if k == 'K3':
            tr_s = E['K3']['varianten'][r['variante']]
            A(f"- Einordnung: effektive Stichprobe sind die {r['korb']['n']} Rebalances, nicht die {r['kz']['n']} Beine (Beine eines Rebalance sind korreliert). "
              f"Das Intervall oben schliesst 0 ein, die Korb-t-Statistik ist {f(r['korb'].get('t'), 2)}. Ø R auf Training war {f(tr_s['train']['avg'])} (also praktisch null), die gespiegelte Variante (Umkehr) auf Training {f(tr_s['spiegel_train']['avg'])}. "
              f"Der Gewinn kommt aus den Long-Beinen ({f(r['lang_kurz']['long']['avg'])} R), die Short-Beine liegen bei {f(r['lang_kurz']['short']['avg'])} R.")
            na = R.get('nachanalyse_K3')
            if na:
                A(f"- Nachanalyse Konzentration (dieselben Test-Beine, keine Aenderung von Regeln oder Urteil): Summe aller Beine {f(na['summe_R'], 1)} R; der staerkste einzelne Rebalance bringt {f(na['top1_summe_R'], 1)} R, die drei staerksten {f(na['top3_summe_R'], 1)} R, der mittlere Rebalance {f(na['median_summe_R'], 2)} R, Anteil Rebalances im Plus {f(na['anteil_pos'], 2)}. "
                  f"Ø R je Bein ohne den staerksten Rebalance: {f(na['avg_ohne_top1'])} ({na['n_ohne_top1']} Beine), ohne die drei staerksten: {f(na['avg_ohne_top3'])} ({na['n_ohne_top3']} Beine).")
        p = r['portfolio']
        A(f"- Portfolio-Rechnung Test ({'2 %' if k != 'K3' else '1,33 % je Bein'} Risiko): {portfolio_text(p)}.")
        A(f"- **Urteil: {r['urteil']}.**")
        A('')
    A('## Gesamtbild und Vorbehalte')
    A('')
    A('- Das Urteil richtet sich strikt nach den Regeln oben. Ein positiver Test-Ø R allein ist kein Beleg: Trades sind stark gebuendelt (Coin-Korrelation zu BTC 0,5 bis 0,8), die effektive Stichprobe ist kleiner als die Tradezahl; das Wochen-Bootstrap-Intervall ist die ehrlichere Groesse.')
    A('- `edge_candidate` heisst nur: die vorab festgelegten Huerden (Test > 0, Validierung > 0, mindestens 30 Test-Trades, mindestens die Haelfte der Coins im Plus) wurden genommen. Es ist KEIN Nachweis; weiteres Vorgehen waere ein Vorwaertstest (Paper) ohne Parameteraenderung.')
    A('- Der Test deckt nur ein Marktregime ab (4h: ca. 7 Monate, 1h: ca. 52 Tage). Mit 12 Varianten (Best-of-4 je Kandidat) ist ein Zufallsvorsprung moeglich; deshalb zaehlen nur Validierung und Test.')
    A('- Funding ist pauschal angesetzt (Longs belastet, Shorts ohne Gutschrift), echte Funding-Historie wurde nicht abgerufen. Slippage bei Ausbruechen in Marktbewegung kann hoeher sein als angesetzt.')
    A('- Die Portfolio-Zahlen zeigen, wie weit das Ergebnis von "schnell viel Geld" entfernt ist: Die Test-Rendite steht in der Uebersicht; die besten Einzeltage (bis ca. 18 %) sind Ausreisser bei hohem Risiko und keine Dauerleistung, +50 % am Tag wird nirgends erreicht. K1 und K2 verlieren im Test Geld, K3 liegt bei der Rendite im Plus, haengt aber an wenigen Ereignissen (siehe Nachanalyse).')
    A('')
    open(F_MD, 'w').write('\n'.join(L))


def nachanalyse():
    """Reine Konzentrations-Diagnose fuer K3 (einziger Kandidat). Rechnet dieselben Test-Beine nochmals (deterministisch,
    identisch zum Testlauf), aendert weder Regeln noch Parameter noch Urteil. Ergebnis wird in die JSON-Datei geschrieben."""
    R = json.load(open(F_JSON))
    w = R['test']['K3']['variante']
    L, H = int(w.split(',')[0].split('=')[1]), int(w.split(',')[1].split('=')[1])
    beine, korbe = k3_lauf('test', L, H)
    assert abs(kennzahlen(beine)['avg'] - R['test']['K3']['kz']['avg']) < 1e-12, 'Nachrechnung weicht vom Testlauf ab'
    reb = {}
    for t in beine:
        reb.setdefault(t['reb'], []).append(t)
    summen = sorted(((sum(x['net_R'] for x in v), r) for r, v in reb.items()), reverse=True)
    gesamt = sum(s for s, _ in summen)

    def ohne(top):
        ausschluss = {r for _, r in summen[:top]}
        rest = [t for t in beine if t['reb'] not in ausschluss]
        return kennzahlen(rest), len(rest)

    k1_, n1 = ohne(1)
    k3_, n3 = ohne(3)
    N_ = len(reb)
    R['nachanalyse_K3'] = dict(rebalances=N_, summe_R=gesamt, top1_summe_R=summen[0][0], top3_summe_R=sum(s for s, _ in summen[:3]),
                               median_summe_R=st.median(s for s, _ in summen), anteil_pos=sum(1 for s, _ in summen if s > 0) / N_,
                               avg_ohne_top1=k1_['avg'], n_ohne_top1=n1, avg_ohne_top3=k3_['avg'], n_ohne_top3=n3)
    json.dump(R, open(F_JSON, 'w'), indent=1)
    schreibe_md(R)
    print(json.dumps(R['nachanalyse_K3'], indent=1))


if __name__ == '__main__':
    modus = sys.argv[1] if len(sys.argv) > 1 else ''
    if modus == 'selbsttest':
        sys.exit(0 if selbsttest() else 1)
    elif modus == 'dev':
        dev()
    elif modus == 'test':
        testlauf()
    elif modus == 'nachanalyse':
        nachanalyse()
    elif modus == 'md':      # nur Markdown aus gespeichertem JSON neu schreiben, keine neue Simulation
        schreibe_md(json.load(open(F_JSON)))
    else:
        print(__doc__)
