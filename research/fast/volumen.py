#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blickwinkel Volumen-Schub und Volatilitaets-Cluster auf Alts: drei Kandidaten in einem Skript (nur Standardbibliothek).

K1  Kompressions-Ausbruch 4h          (ruhige 12er-Box, Close ausserhalb, Chandelier-Trail, Zeitausstieg 12 Kerzen)
K2  Ruhe-Fehlausbruch-Fade 1h         (Gegenposition zum Ausbruch, fester ATR-Stop, Zeitausstieg 12 Kerzen)
K3  Ruhe-Volumen-Schub-Fortsetzung 4h (Schub-Kerze nach Ruhe, Stop Kerzenmitte, Zeitausstieg H Kerzen)

Ablauf in Stufen, damit der Test-Abschnitt wirklich nur einmal angesehen wird:
  python3 volumen.py selbsttest   Plausibilitaets- und Kausalitaetstests (nur synthetische Daten)
  python3 volumen.py dev          Training + Validierung fuer alle 3 x 8 Varianten. Auswahl je Kandidat NUR nach
                                  Training (hoechstes Ø R bei mindestens 30 Trainings-Trades). Schreibt
                                  auswahl_volumen.json. Der Test-Abschnitt wird NICHT angefasst.
  python3 volumen.py test         liest die feste Auswahl, rechnet den Test GENAU EINMAL (je Kandidat eine Variante),
                                  schreibt ergebnis_volumen.json und ergebnis_volumen.md. Bricht ab, wenn schon vorhanden.
  python3 volumen.py md           schreibt nur die Markdown-Datei aus ergebnis_volumen.json neu (keine Neuberechnung).

Aufteilung je Coin chronologisch nach Kerzenindex: erste 50 % Training, naechste 25 % Validierung, letzte 25 % Test.
Jeder Abschnitt wird getrennt simuliert (Position startet flach). Indikatoren sind rein kausal (nur Kerzen bis einschliesslich
Signalkerze; die Historie vor dem Abschnittsbeginn darf als Rueckblick dienen). Ein Trade zaehlt nur, wenn seine laengstmoegliche
Haltedauer (Zeitausstieg) noch im Abschnitt endet; diese Regel haengt nur von der Position der Signalkerze ab, nicht vom Ergebnis.
"""
import sys, os, json, math, statistics as st, datetime as dt, itertools, random

sys.path.insert(0, '/root/Claude-Traiding')
from chartreader import data

HIER = os.path.dirname(os.path.abspath(__file__))
F_AUSWAHL = os.path.join(HIER, 'auswahl_volumen.json')
F_JSON = os.path.join(HIER, 'ergebnis_volumen.json')
F_MD = os.path.join(HIER, 'ergebnis_volumen.md')

# ---------------------------------------------------------------- Kostenmodell
FEE = 0.00045                 # Gebuehr je Seite (Taker)
SLIP_STD = 0.0003             # Slippage je Seite
SLIP_DUENN = 0.0005           # ARB, UNI, DOT
DUENN = {'ARB', 'UNI', 'DOT'}
FUND_H = 0.0000125            # Funding 0,00125 % je Stunde, immer als Kosten (auch fuer Shorts, konservativ)
TFH = {'1h': 1, '4h': 4}

# ---------------------------------------------------------------- Portfolio-Annahmen (nur Test-Auswertung)
RISIKO = 0.02
MAX_POS = 4

START_IDX = 110               # Start 110 Kerzen nach Datenbeginn
MIN_TRAIN_TRADES = 30         # Auswahl nur unter Varianten mit mindestens so vielen Trainings-Trades
MIN_TEST_TRADES = 30

KAND = {
    'K1': {'name': 'K1 Kompressions-Ausbruch 4h', 'tf': '4h',
           'coins': ['HYPE', 'ARB', 'NEAR', 'UNI', 'AAVE', 'LINK', 'DOGE', 'DOT'], 'kontrolle': ['AVAX', 'ADA'],
           'gitter': [dict(K=K, V=V, T=T) for K in (0.7, 0.85) for V in (False, True) for T in (2.5, 3.5)]},
    'K2': {'name': 'K2 Ruhe-Fehlausbruch-Fade 1h', 'tf': '1h',
           'coins': ['HYPE', 'ARB', 'NEAR', 'UNI', 'AVAX', 'AAVE', 'LINK'], 'kontrolle': ['DOGE', 'ADA', 'DOT'],
           'gitter': [dict(K=K, SF=SF, S=S) for K in (0.7, 0.85) for SF in (2.0, 3.0) for S in (False, True)]},
    'K3': {'name': 'K3 Ruhe-Volumen-Schub-Fortsetzung 4h', 'tf': '4h',
           'coins': ['HYPE', 'ARB', 'NEAR', 'UNI', 'AAVE', 'LINK', 'DOGE', 'DOT', 'AVAX', 'ADA'], 'kontrolle': [],
           'gitter': [dict(K=K, VT=VT, H=H) for K in (0.7, 0.85) for VT in (2, 3) for H in (3, 6)]},
}


def tstr(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime('%Y-%m-%d')


def vlabel(p):
    return ' '.join('%s=%s' % (k, ('an' if v is True else 'aus' if v is False else v)) for k, v in p.items())


# ---------------------------------------------------------------- Daten und Indikatoren
class Reihe:
    """Eine Kerzenreihe mit vorberechneten, rein kausalen Indikatoren (Wert an Index i nutzt nur Kerzen <= i,
    bzw. i-1 wo ausdruecklich so definiert)."""

    def __init__(self, cs):
        self.n = n = len(cs)
        self.t = [k['t'] for k in cs]
        self.T = [k['T'] for k in cs]
        self.o = [k['o'] for k in cs]
        self.h = [k['h'] for k in cs]
        self.l = [k['l'] for k in cs]
        self.c = [k['c'] for k in cs]
        self.v = [k['v'] for k in cs]
        h, l, c = self.h, self.l, self.c
        rng = [h[i] - l[i] for i in range(n)]
        tr = [rng[0]] + [max(rng[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, n)]
        self.rng = rng
        # ATR14[i] = Mittel der True Range der Kerzen i-13..i
        self.atr = [None] * n
        for i in range(14, n):
            self.atr[i] = sum(tr[i - 13:i + 1]) / 14.0
        # Box = Kerzen i-12..i-1; r12 = Mittel Hoch-Tief der Box; r96 = Mittel der Kerzen i-108..i-13
        self.bh = [None] * n
        self.bl = [None] * n
        self.r12 = [None] * n
        self.r96 = [None] * n
        self.m48 = [None] * n
        for i in range(108, n):
            self.bh[i] = max(h[i - 12:i])
            self.bl[i] = min(l[i - 12:i])
            self.r12[i] = sum(rng[i - 12:i]) / 12.0
            self.r96[i] = sum(rng[i - 108:i - 12]) / 96.0
            self.m48[i] = st.median(self.v[i - 48:i])      # Median Volumen der Kerzen i-48..i-1

    def stunde_wtag(self, i):
        d = dt.datetime.fromtimestamp(self.t[i] / 1000, dt.timezone.utc)
        return d.hour, d.weekday()


_cache = {}


def lade(coin, tf):
    k = (coin, tf)
    if k not in _cache:
        _cache[k] = Reihe(data.candles(coin, tf, 5000, use_cache=True, max_age=10 ** 9))
    return _cache[k]


def abschnitte(n):
    a, b = int(n * 0.5), int(n * 0.75)
    return {'train': (0, a), 'val': (a, b), 'test': (b, n)}


# ---------------------------------------------------------------- Signale (reine Funktionen von r und i, nur Daten <= i, Einstieg Open[i+1])
def stop_klemme(e0, d, ziel, a):
    """Anfangsstop = ziel, Abstand zum Einstieg auf 1,5 bis 3,0 x ATR begrenzt."""
    dist = d * (e0 - ziel)
    dist = min(max(dist, 1.5 * a), 3.0 * a)
    return e0 - d * dist


def signal_k1(r, i, p):
    a = r.atr[i]
    if a is None or r.r12[i] is None:
        return None
    if not (r.r12[i] < p['K'] * r.r96[i]):
        return None
    c = r.c[i]
    d = 1 if c > r.bh[i] else (-1 if c < r.bl[i] else 0)
    if d == 0:
        return None
    if p['V'] and not (r.v[i] >= 1.5 * r.m48[i]):
        return None
    e0 = r.o[i + 1]
    stop = stop_klemme(e0, d, (r.bh[i] + r.bl[i]) / 2.0, a)
    return d, stop, p['T']


def signal_k2(r, i, p):
    a = r.atr[i]
    if a is None or r.r12[i] is None:
        return None
    if not (r.r12[i] < p['K'] * r.r96[i]):
        return None
    if p['S']:
        h, wt = r.stunde_wtag(i)
        if not (12 <= h <= 21 and wt <= 4):
            return None
    c = r.c[i]
    b = 1 if c > r.bh[i] else (-1 if c < r.bl[i] else 0)
    if b == 0:
        return None
    d = -b                                        # Gegenrichtung zum Ausbruch
    e0 = r.o[i + 1]
    stop = e0 - d * p['SF'] * a
    return d, stop, None


def signal_k3(r, i, p):
    a = r.atr[i - 1]                              # ATR14 der Kerzen i-14..i-1, ohne Signalkerze
    if a is None or r.r12[i] is None:
        return None
    if not (r.r12[i] < p['K'] * r.r96[i]):
        return None
    if not (r.v[i] >= p['VT'] * r.m48[i]):
        return None
    rg = r.rng[i]
    if not (rg > 0 and rg >= 1.5 * a):
        return None
    pos = (r.c[i] - r.l[i]) / rg
    if r.c[i] > r.o[i] and pos > 0.75:
        d = 1
    elif r.c[i] < r.o[i] and pos < 0.25:
        d = -1
    else:
        return None
    e0 = r.o[i + 1]
    stop = stop_klemme(e0, d, (r.h[i] + r.l[i]) / 2.0, a)
    return d, stop, None


SIGNAL = {'K1': signal_k1, 'K2': signal_k2, 'K3': signal_k3}


def haltedauer(kid, p):
    return p['H'] if kid == 'K3' else 12


# ---------------------------------------------------------------- Trade-Simulation
def simuliere(r, i, d, stop, H, T, slip, tfh):
    """Einstieg zum Open[i+1] (Slippage ungeguenstig). Kerze k=1 ist die Einstiegskerze. Je Kerze: zuerst Stop
    (bei Gap ueber den Stop Ausstieg zum Open), dann Zeitausstieg zum Schluss der H-ten Kerze, dann (nach dem Schluss
    der Kerze) Trail-Nachfuehrung, die erst ab der Folgekerze wirkt. 1R = |Open[i+1] - Anfangsstop|.
    Kosten: Gebuehr beider Seiten auf den Kurs, Slippage beider Seiten, Funding je Stunde auf den Einstiegskurs."""
    e0 = r.o[i + 1]
    risk = abs(e0 - stop)
    if risk <= 0:
        return None
    e = e0 * (1 + d * slip)
    s = stop
    hh, ll = -math.inf, math.inf
    x, grund, k, j = None, None, 0, None
    for k in range(1, H + 1):
        j = i + k
        op, hi, lo, cl = r.o[j], r.h[j], r.l[j], r.c[j]
        if d == 1 and lo <= s:
            x, grund = min(op, s), 'stop'
            break
        if d == -1 and hi >= s:
            x, grund = max(op, s), 'stop'
            break
        if k == H:
            x, grund = cl, 'zeit'
            break
        if T is not None:
            hh, ll = max(hh, hi), min(ll, lo)
            if d == 1:
                s = max(s, hh - T * r.atr[j])
            else:
                s = min(s, ll + T * r.atr[j])
    xe = x * (1 - d * slip)
    brutto = d * (xe - e)
    kosten = FEE * (e + xe) + FUND_H * k * tfh * e
    return {'i': i, 'ei': i + 1, 'xi': j, 'd': d, 'R': (brutto - kosten) / risk, 'k': k, 'grund': grund,
            'net': (brutto - kosten) / e, 'rf': risk / e0, 'ets': r.t[i + 1], 'xts': r.T[j]}


def lauf(r, coin, kid, p, a, b):
    """Alle Trades eines Coins im Abschnitt [a, b). Eine Position je Coin, neues Signal erst nach dem Ausstieg."""
    sig = SIGNAL[kid]
    tf = KAND[kid]['tf']
    H = haltedauer(kid, p)
    slip = SLIP_DUENN if coin in DUENN else SLIP_STD
    out = []
    i = max(a, START_IDX)
    while i + H <= b - 1:
        s = sig(r, i, p)
        if s:
            d, stop, T = s
            tr = simuliere(r, i, d, stop, H, T, slip, TFH[tf])
            if tr:
                tr['coin'] = coin
                out.append(tr)
                i = tr['xi'] + 1
                continue
        i += 1
    return out


def alle_coins(kid, p, abschn, coins):
    tf = KAND[kid]['tf']
    res = {}
    for c in coins:
        r = lade(c, tf)
        a, b = abschnitte(r.n)[abschn]
        res[c] = lauf(r, c, kid, p, a, b)
    return res


# ---------------------------------------------------------------- Statistik
def stat(trades):
    n = len(trades)
    if n == 0:
        return {'n': 0, 'avg_r': 0.0, 'pf': None, 'win': None, 'se': None, 'netpct': None, 'k': None}
    R = [t['R'] for t in trades]
    gw = sum(x for x in R if x > 0)
    gl = -sum(x for x in R if x < 0)
    return {'n': n, 'avg_r': sum(R) / n, 'pf': (gw / gl if gl > 0 else None), 'win': sum(1 for x in R if x > 0) / n,
            'se': (st.stdev(R) / math.sqrt(n) if n > 1 else None), 'netpct': sum(t['net'] for t in trades) / n * 100,
            'k': sum(t['k'] for t in trades) / n}


def gepoolt(res, coins):
    allt = [t for c in coins for t in res.get(c, [])]
    s = stat(allt)
    pos = sum(1 for c in coins if res.get(c) and stat(res[c])['avg_r'] > 0)
    mit = sum(1 for c in coins if res.get(c))
    s['coins_pos'] = pos
    s['coins_mit_trades'] = mit
    s['coins_total'] = len(coins)
    return s, allt


# ---------------------------------------------------------------- Portfolio (2 % Risiko je Trade, max. 4 gleichzeitig)
def portfolio(trades, risiko=RISIKO, max_pos=MAX_POS, start=1000.0):
    ts = sorted(trades, key=lambda t: (t['ets'], t['coin']))
    eq = start
    peak = start
    maxdd = 0.0
    offen = []
    tage = {}
    genommen = uebersprungen = 0
    max_hebel = 0.0
    kurve = [(0, start)]

    def buche(bis):
        nonlocal eq, peak, maxdd
        while offen:
            offen.sort(key=lambda x: x['xts'])
            if offen[0]['xts'] > bis:
                break
            p = offen.pop(0)
            tag = dt.datetime.fromtimestamp(p['xts'] / 1000, dt.timezone.utc).strftime('%Y-%m-%d')
            if tag not in tage:
                tage[tag] = [eq, eq]
            eq += p['pnl']
            tage[tag][1] = eq
            peak = max(peak, eq)
            maxdd = max(maxdd, (peak - eq) / peak)
            kurve.append((p['xts'], eq))

    for t in ts:
        buche(t['ets'])
        if len(offen) >= max_pos:
            uebersprungen += 1
            continue
        risk_betrag = risiko * eq
        offen.append({'xts': t['xts'], 'pnl': risk_betrag * t['R'], 'notional': risk_betrag / t['rf'], 'eq0': eq})
        genommen += 1
        max_hebel = max(max_hebel, sum(o['notional'] for o in offen) / eq)
    buche(10 ** 18)
    tagesren = {d: (v[1] / v[0] - 1) * 100 for d, v in tage.items()}
    best = max(tagesren.items(), key=lambda kv: kv[1]) if tagesren else (None, 0.0)
    worst = min(tagesren.items(), key=lambda kv: kv[1]) if tagesren else (None, 0.0)
    return {'rendite_pct': (eq / start - 1) * 100, 'max_rueckgang_pct': maxdd * 100, 'bester_tag_pct': best[1],
            'bester_tag': best[0], 'schlechtester_tag_pct': worst[1], 'schlechtester_tag': worst[0],
            'genommen': genommen, 'uebersprungen': uebersprungen, 'max_hebel': max_hebel, 'endkonto': eq,
            'handelstage': len(tagesren)}


# ---------------------------------------------------------------- Selbsttest
def _synth(cands):
    """cands: Liste (o,h,l,c,v); Zeitstempel stuendlich ab 2026-01-05 00:00 UTC (Montag)."""
    t0 = int(dt.datetime(2026, 1, 5, tzinfo=dt.timezone.utc).timestamp() * 1000)
    cs = []
    for n, (o, h, l, c, v) in enumerate(cands):
        cs.append({'t': t0 + n * 3_600_000, 'T': t0 + (n + 1) * 3_600_000 - 1, 'o': o, 'h': h, 'l': l, 'c': c, 'v': v})
    return Reihe(cs)


def selbsttest():
    ok = 0

    def check(name, cond):
        nonlocal ok
        print(('OK   ' if cond else 'FAIL ') + name)
        if not cond:
            sys.exit(1)
        ok += 1

    def flach(n, p=100.0):
        return [(p, p + 0.5, p - 0.5, p, 10.0)] * n

    # 1. Stop vor Trail/Zeit; Gap ueber den Stop -> Ausstieg zum Open
    base = flach(130)
    fl = base + [(100, 100.5, 99.5, 100, 10)]       # Index 130 = Einstiegskerze (Open 100)
    # Stop long bei 98 (Risiko 2): Kerze 131 hat Tief 99 -> kein Stop; Kerze 132 mit Tief 97 -> Stop-Ausstieg bei 98
    r = _synth(fl + [(100, 101, 99.0, 100, 10), (100, 100.5, 97.0, 99, 10)] + flach(20))
    tr = simuliere(r, 129, 1, 98.0, 12, None, 0.0, 1)
    check('Stop trifft: Ausstieg zum Stopkurs', tr is not None and tr['grund'] == 'stop' and tr['k'] == 3 and tr['xi'] == 132)
    check('Stop-R etwa -1 (nur Kosten kommen dazu)', -1.06 < tr['R'] < -1.0)
    r = _synth(fl + [(100, 101, 99.0, 100, 10), (96.0, 96.5, 95.0, 96, 10)] + flach(20))
    tr = simuliere(r, 129, 1, 98.0, 12, None, 0.0, 1)
    check('Gap ueber den Stop: Ausstieg zum Open (96), R < -1', tr['grund'] == 'stop' and tr['R'] < -1.9 and tr['xi'] == 132)
    # Short gespiegelt
    r = _synth(fl + [(100, 100.5, 99.0, 100, 10), (104.0, 105, 103.5, 104, 10)] + flach(20))
    tr = simuliere(r, 129, -1, 102.0, 12, None, 0.0, 1)
    check('Short-Gap: Ausstieg zum Open (104)', tr['grund'] == 'stop' and tr['R'] < -0.9)

    # 2. Zeitausstieg: Schluss der H-ten Kerze (Einstiegskerze = Kerze 1)
    r = _synth(fl + [(100, 100.4, 99.6, 100.2, 10)] * 30)
    tr = simuliere(r, 129, 1, 95.0, 12, None, 0.0, 1)
    check('Zeitausstieg nach 12 Kerzen (Index i+12)', tr['grund'] == 'zeit' and tr['k'] == 12 and tr['xi'] == 129 + 12)
    tr = simuliere(r, 129, 1, 95.0, 3, None, 0.0, 1)
    check('Zeitausstieg H=3', tr['k'] == 3 and tr['xi'] == 132)

    # 3. Kosten bei null Kursbewegung (Open=Close, Entry=Exit): R = -Kosten/Risiko
    r = _synth(fl + [(100, 100.0, 100.0, 100, 10)] * 30)
    tr = simuliere(r, 129, 1, 95.0, 3, None, 0.0003, 1)
    e = 100 * 1.0003
    xe = 100 * (1 - 0.0003)
    erw = ((xe - e) - FEE * (e + xe) - FUND_H * 3 * 1 * e) / 5.0
    check('Kostenmodell: Gebuehr + Slippage + Funding stimmt', abs(tr['R'] - erw) < 1e-12)

    # 4. Trail wirkt erst ab der Folgekerze und nutzt nur Daten bis zur Vorkerze
    # ATR ~ 1.0 (Spanne 1). Kerze 130 (Einstieg): Hoch 110 -> Trail danach = 110 - T*ATR; in derselben Kerze noch nicht aktiv.
    sp = fl[:130] + [(100, 110.0, 99.5, 109, 10)]   # Einstiegskerze Index 130, Hoch 110, kein Stop (Stop 95)
    r = _synth(sp + [(109, 109.2, 108.5, 108.8, 10)] * 3 + [(108, 108.2, 80.0, 81, 10)] + flach(20))
    # i=129? Einstieg = Open[130] = 100 -> i = 129. Index 130..: k=1 Einstieg, 131-133 ruhig, 134 Absturz
    tr = simuliere(r, 129, 1, 95.0, 12, 2.5, 0.0, 1)
    atr_x = r.atr[130]
    erw_trail = 110.0 - 2.5 * atr_x
    check('Trail: Ausstieg am Trailkurs der Vorkerzen (>95) in Kerze 134', tr['grund'] == 'stop' and tr['xi'] == 134 and erw_trail > 95 and tr['R'] > 0)

    # 5. Kausalitaet: Signal an Index i aendert sich nicht, wenn Kerzen nach i (ausser Open[i+1]) zerstoert werden
    rnd = random.Random(7)
    cands = []
    p = 100.0
    for n in range(400):
        o = p
        c = o * (1 + rnd.gauss(0, 0.01))
        hi = max(o, c) * (1 + abs(rnd.gauss(0, 0.004)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.004)))
        cands.append((o, hi, lo, c, abs(rnd.gauss(100, 40)) + (400 if n % 37 == 0 else 0)))
        p = c
    r_voll = _synth(cands)
    gefunden = {'K1': 0, 'K2': 0, 'K3': 0}
    for kid, p_ in (('K1', dict(K=3.0, V=False, T=2.5)), ('K2', dict(K=3.0, SF=2.0, S=False)), ('K3', dict(K=3.0, VT=1.0, H=3))):
        sig = SIGNAL[kid]
        gleich = True
        for i in range(120, 380):
            a = sig(r_voll, i, p_)
            if a:
                gefunden[kid] += 1
            kaputt = cands[:i + 1] + [(cands[i + 1][0], 1e6, 1e-6, 5.0, 1e9)] + [(1e6, 1e7, 1e-6, 3.0, 1e9)] * (399 - i - 1)
            r_k = _synth(kaputt)
            b = sig(r_k, i, p_)
            if (a is None) != (b is None) or (a and (a[0] != b[0] or abs(a[1] - b[1]) > 1e-9)):
                gleich = False
                break
        check('Kausalitaet %s: Signal unabhaengig von Kerzen nach i (gefunden %d Signale)' % (kid, gefunden[kid]), gleich and gefunden[kid] > 0)

    # 6. Indikatoren: ATR/Box/Median exakt gegen Handrechnung
    i = 200
    tr_ = [max(r_voll.h[j] - r_voll.l[j], abs(r_voll.h[j] - r_voll.c[j - 1]), abs(r_voll.l[j] - r_voll.c[j - 1])) for j in range(i - 13, i + 1)]
    check('ATR14[i] = Mittel TR i-13..i', abs(r_voll.atr[i] - sum(tr_) / 14) < 1e-12)
    check('Box i-12..i-1 und r96 i-108..i-13', r_voll.bh[i] == max(r_voll.h[i - 12:i]) and r_voll.bl[i] == min(r_voll.l[i - 12:i])
          and abs(r_voll.r96[i] - sum(r_voll.rng[j] for j in range(i - 108, i - 12)) / 96) < 1e-12
          and r_voll.m48[i] == st.median(r_voll.v[i - 48:i]))

    # 7. Abschnitte: Reihenfolge, keine Ueberschneidung, Trades enden im Abschnitt
    ab = abschnitte(1000)
    check('Abschnitte 50/25/25 lueckenlos', ab == {'train': (0, 500), 'val': (500, 750), 'test': (750, 1000)})
    pv = dict(K=3.0, V=False, T=2.5)
    trs = lauf(r_voll, 'XXX', 'K1', pv, 150, 300)
    check('Abschnittsgrenzen: alle Trades enden im Abschnitt', all(150 <= t['i'] and t['xi'] <= 299 for t in trs) and len(trs) > 0)
    check('Eine Position je Coin: Einstieg nach vorigem Ausstieg', all(trs[n + 1]['i'] > trs[n]['xi'] for n in range(len(trs) - 1)))

    # 8. Klemme 1,5..3,0 ATR
    check('Stop-Klemme: nahe Mitte -> 1,5 ATR', abs(stop_klemme(100, 1, 99.9, 2.0) - 97.0) < 1e-12)
    check('Stop-Klemme: ferne Mitte -> 3,0 ATR', abs(stop_klemme(100, 1, 80, 2.0) - 94.0) < 1e-12)
    check('Stop-Klemme short gespiegelt', abs(stop_klemme(100, -1, 100.1, 2.0) - 103.0) < 1e-12)

    # 9. Portfolio: hoechstens 4 gleichzeitig, R-basierte Buchung
    tl = [{'coin': 'C%d' % n, 'ets': 1000 + n, 'xts': 5000, 'R': 1.0, 'rf': 0.04} for n in range(6)]
    pf = portfolio(tl)
    check('Portfolio: nur 4 gleichzeitige Positionen', pf['genommen'] == 4 and pf['uebersprungen'] == 2)
    check('Portfolio: 4 Trades je +1R bei 2 % Risiko = +8 %', abs(pf['rendite_pct'] - 8.0) < 1e-9)
    tl2 = [{'coin': 'A', 'ets': 1000, 'xts': 2000, 'R': -1.0, 'rf': 0.04}, {'coin': 'B', 'ets': 3000, 'xts': 4000, 'R': -1.0, 'rf': 0.04}]
    pf2 = portfolio(tl2)
    check('Portfolio: Verlust in Folge, Konto mit aktuellem Stand (0,98*0,98)', abs(pf2['endkonto'] - 1000 * 0.98 * 0.98) < 1e-9
          and abs(pf2['max_rueckgang_pct'] - (1 - 0.98 * 0.98) * 100) < 1e-9)
    print('Selbsttest bestanden (%d Pruefungen)' % ok)


# ---------------------------------------------------------------- dev: Training + Validierung, Auswahl nur nach Training
def kompakt(s):
    return {k: s[k] for k in ('n', 'avg_r', 'pf', 'win', 'se', 'netpct', 'k', 'coins_pos', 'coins_mit_trades', 'coins_total')}


def dev():
    if os.path.exists(F_JSON):
        print('Hinweis: ergebnis_volumen.json existiert schon (Test wurde gerechnet). dev wird trotzdem nicht ueberschrieben.')
        sys.exit(1)
    auswahl = {'regel': 'Je Kandidat die Variante mit dem hoechsten Trainings-Ø R (gepoolt ueber die Urteils-Coins) bei mindestens %d Trainings-Trades. Validierung und Test gehen NICHT in die Auswahl ein.' % MIN_TRAIN_TRADES,
               'kandidaten': {}}
    for kid, K in KAND.items():
        zeilen = []
        for p in K['gitter']:
            z = {'params': p}
            for ab in ('train', 'val'):
                res = alle_coins(kid, p, ab, K['coins'] + K['kontrolle'])
                s, _ = gepoolt(res, K['coins'])
                z[ab] = kompakt(s)
                if K['kontrolle']:
                    z[ab + '_kontrolle'] = kompakt(gepoolt(res, K['kontrolle'])[0])
                z[ab + '_coins'] = {c: {'n': len(res[c]), 'avg_r': stat(res[c])['avg_r']} for c in K['coins'] + K['kontrolle']}
            zeilen.append(z)
        zul = [z for z in zeilen if z['train']['n'] >= MIN_TRAIN_TRADES]
        wahl = max(zul, key=lambda z: z['train']['avg_r']) if zul else None
        auswahl['kandidaten'][kid] = {'zeilen': zeilen, 'gewaehlt': wahl['params'] if wahl else None}
        print('==', K['name'], '(%d Varianten)' % len(zeilen))
        for z in zeilen:
            m = '  <== gewaehlt (nur nach Training)' if wahl and z is wahl else ''
            tr, va = z['train'], z['val']
            pf = lambda x: ('%.2f' % x) if x is not None else '-'
            print('  %-34s Train n=%4d ØR=%+.3f PF=%s Coins>0=%d/%d | Val n=%4d ØR=%+.3f PF=%s Coins>0=%d/%d%s' % (
                vlabel(z['params']), tr['n'], tr['avg_r'], pf(tr['pf']), tr['coins_pos'], tr['coins_total'],
                va['n'], va['avg_r'], pf(va['pf']), va['coins_pos'], va['coins_total'], m))
    with open(F_AUSWAHL, 'w') as f:
        json.dump(auswahl, f, indent=1, ensure_ascii=False)
    print('Auswahl geschrieben:', F_AUSWAHL)


# ---------------------------------------------------------------- test: genau einmal
def verdikt(tr, va, te, kid):
    kriterien = {
        'test_avg_r_pos': te['avg_r'] > 0,
        'val_avg_r_pos': va['avg_r'] > 0,
        'test_trades_min30': te['n'] >= MIN_TEST_TRADES,
        'haelfte_coins_plus': te['coins_pos'] * 2 >= te['coins_total'],
    }
    if te['n'] < MIN_TEST_TRADES:
        v = 'inconclusive'
    elif all(kriterien.values()):
        v = 'edge_candidate'
    else:
        v = 'no_edge'
    return v, kriterien


def test():
    if os.path.exists(F_JSON):
        print('ergebnis_volumen.json existiert schon: der Test-Abschnitt wurde bereits einmal gerechnet. Abbruch.')
        sys.exit(1)
    if not os.path.exists(F_AUSWAHL):
        print('Erst "dev" ausfuehren.')
        sys.exit(1)
    auswahl = json.load(open(F_AUSWAHL))
    out = {'kandidaten': {}, 'varianten_gesamt': sum(len(K['gitter']) for K in KAND.values())}
    for kid, K in KAND.items():
        p = auswahl['kandidaten'][kid]['gewaehlt']
        if p is None:
            out['kandidaten'][kid] = {'name': K['name'], 'gewaehlt': None, 'hinweis': 'keine Variante mit genug Trainings-Trades'}
            continue
        coins_alle = K['coins'] + K['kontrolle']
        e = {'name': K['name'], 'tf': K['tf'], 'gewaehlt': p, 'coins': K['coins'], 'kontrolle': K['kontrolle']}
        trades_test = None
        for ab in ('train', 'val', 'test'):
            res = alle_coins(kid, p, ab, coins_alle)
            s, allt = gepoolt(res, K['coins'])
            e[ab] = kompakt(s)
            e[ab + '_coins'] = {c: kompakt(dict(stat(res[c]), coins_pos=0, coins_mit_trades=0, coins_total=0)) for c in coins_alle}
            if K['kontrolle']:
                e[ab + '_kontrolle'] = kompakt(gepoolt(res, K['kontrolle'])[0])
            if ab == 'test':
                trades_test = allt
                sec = [abschnitte(lade(c, K['tf']).n)['test'] for c in K['coins']]
                starts = [lade(c, K['tf']).t[a] for c, (a, b) in zip(K['coins'], sec)]
                ends = [lade(c, K['tf']).T[b - 1] for c, (a, b) in zip(K['coins'], sec)]
                e['test_von'] = tstr(min(starts))
                e['test_bis'] = tstr(max(ends))
                e['test_tage'] = (max(ends) - min(starts)) / 86_400_000
                e['test_coin_zeitraum'] = {c: [tstr(lade(c, K['tf']).t[a]), tstr(lade(c, K['tf']).T[b - 1])] for c, (a, b) in zip(K['coins'], sec)}
                e['portfolio'] = portfolio(trades_test)
                e['test_grund'] = {g: sum(1 for t in trades_test if t['grund'] == g) for g in ('stop', 'zeit')}
                e['test_long_short'] = {'long': sum(1 for t in trades_test if t['d'] == 1), 'short': sum(1 for t in trades_test if t['d'] == -1)}
                # Konzentrationsdiagnose: Ø R ohne die 3 besten Trades
                R = sorted((t['R'] for t in trades_test), reverse=True)
                e['test_avg_r_ohne_top3'] = (sum(R[3:]) / len(R[3:])) if len(R) > 3 else None
                e['test_beste_r'] = R[:3]
                e['test_schlechteste_r'] = R[-3:] if R else []
        v, krit = verdikt(e['train'], e['val'], e['test'], kid)
        e['verdikt'] = v
        e['kriterien'] = krit
        out['kandidaten'][kid] = e
    with open(F_JSON, 'w') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('Test genau einmal gerechnet, gespeichert:', F_JSON)
    md()
    for kid, e in out['kandidaten'].items():
        if e.get('gewaehlt') is None:
            print(kid, 'ohne Auswahl')
            continue
        t = e['test']
        print('%s %s -> %s | Test n=%d ØR=%+.3f PF=%s Coins>0=%d/%d | Val ØR=%+.3f | Train ØR=%+.3f' % (
            kid, vlabel(e['gewaehlt']), e['verdikt'], t['n'], t['avg_r'], ('%.2f' % t['pf']) if t['pf'] else '-',
            t['coins_pos'], t['coins_total'], e['val']['avg_r'], e['train']['avg_r']))


# ---------------------------------------------------------------- Markdown
def f2(x, d=2):
    return '-' if x is None else ('%+.*f' % (d, x))


def pf_(x):
    return '-' if x is None else '%.2f' % x


def md():
    J = json.load(open(F_JSON))
    A = json.load(open(F_AUSWAHL))
    L = []
    w = L.append
    w('# Ergebnis Volumen-Schub und Volatilitäts-Cluster (Blickwinkel Alts, 1h/4h)')
    w('')
    w('Alle Zahlen stammen aus `research/fast/volumen.py` (nur Standardbibliothek, lokaler Cache, kein Netz). Ablauf: `selbsttest`, dann `dev` '
      '(Training und Validierung aller Varianten, Auswahl **nur nach Training**, gespeichert in `auswahl_volumen.json`), dann `test` '
      '(Test-Abschnitt **genau einmal**, Ergebnisse in `ergebnis_volumen.json`; das Skript bricht beim zweiten Lauf ab). '
      'Nach dem Test wurden weder Regeln noch Parameter geändert.')
    w('')
    w('## Daten, Aufteilung, Kosten')
    w('')
    w('- Aufteilung je Coin chronologisch nach Kerzenindex: erste 50 % Training, nächste 25 % Validierung, letzte 25 % Test. Jeder Abschnitt wird getrennt simuliert '
      '(Position startet flach; Rückblick-Indikatoren dürfen in die Zeit vor dem Abschnitt schauen, das ist kausal). Ein Trade zählt nur, wenn sein längster möglicher '
      'Zeitausstieg noch im Abschnitt liegt (hängt nur von der Lage der Signalkerze ab, nicht vom Ergebnis). Start 110 Kerzen nach Datenbeginn.')
    for tf_, nm_ in (('4h', '4h'), ('1h', '1h')):
        rb = lade('BTC', tf_)
        ab_ = abschnitte(rb.n)
        w('- Datenfenster %s (BTC als Marktreferenz, Kursänderung im Abschnitt): ' % nm_ + '; '.join(
            '%s %s bis %s (%+.0f %%)' % (n_, tstr(rb.t[a_]), tstr(rb.T[b_ - 1]), (rb.c[b_ - 1] / rb.o[a_] - 1) * 100)
            for n_, (a_, b_) in zip(('Training', 'Validierung', 'Test'), (ab_['train'], ab_['val'], ab_['test']))) + ('. HYPE hat nur 4209 4h-Kerzen, seine Abschnitte sind kürzer.' if tf_ == '4h' else '.'))
    w('- Kosten je Seite: Gebühr 0,045 % + Slippage 0,03 % (ARB, UNI, DOT 0,05 %); Funding pauschal 0,00125 % je Stunde als Kosten (auch für Shorts, konservativ). '
      'Rundlauf damit rund 0,15 % (0,19 % bei ARB/UNI/DOT) plus Funding. Alle Kosten sind in R umgerechnet und vom Brutto-R abgezogen, ein Stop-Verlust ist also etwas größer als 1 R.')
    w('- Kein Blick in die Zukunft: Signal nur aus Kerzen bis einschließlich Signalkerze, Einstieg zum Open der Folgekerze (Slippage ungünstig), '
      'Stop und Trail in derselben Kerze: Stop zuerst, Gap über den Stop: Ausstieg zum Open, Trail-Nachführung erst ab der Folgekerze. '
      'Der Selbsttest (`python3 volumen.py selbsttest`) prüft das an synthetischen Kerzen, inklusive Kausalitätstest (Kerzen nach der Signalkerze zerstört, Signal bleibt gleich).')
    w('- Je Coin höchstens eine Position; neues Signal frühestens eine Kerze nach der Ausstiegskerze.')
    w('- Mehrfachtest-Lage: **%d Varianten** im Gitter (3 Kandidaten mal 8). Die Hypothesen selbst stammen aus einer Vorab-Suche mit rund 100 Auswertungsscheiben auf dem Trainingsteil (Recherche-Angabe). '
      'Auswahl je Kandidat: höchstes gepooltes Trainings-Ø R bei mindestens 30 Trainings-Trades; im Test wird je Kandidat genau eine Variante gerechnet (insgesamt 3 Testläufe).' % J['varianten_gesamt'])
    w('- Kandidat-Regel: Test-Ø R nach Kosten > 0 UND Validierung > 0 UND mindestens 30 Test-Trades gesamt UND mindestens die Hälfte der Urteils-Coins im Test im Plus (Nenner: alle Urteils-Coins, Coins ohne Trade zählen nicht als Plus). '
      'Sonst `no_edge`; bei weniger als 30 Test-Trades `inconclusive`. Kontroll-Coins fließen nicht ins Urteil ein.')
    w('- Portfolio-Rechnung (nur Test, nur Urteils-Coins): 2 % des aktuellen Kontos Risiko je Trade (R-basiert, Start 1000), Trades chronologisch über alle Coins, höchstens 4 gleichzeitig '
      '(weitere Signale ausgelassen), Gewinn/Verlust bei Ausstieg gebucht, größter Rückgang auf dem realisierten Konto (ohne Zwischenbewertung offener Positionen, also eher zu optimistisch).')
    w('')
    w('## Überblick')
    w('')
    w('| Kandidat | gewählte Variante (nur nach Training) | Train n / Ø R | Val n / Ø R | Test n / Ø R | Test PF | Test Gewinnquote | Coins im Plus (Test) | Urteil |')
    w('|---|---|---|---|---|---|---|---|---|')
    for kid, e in J['kandidaten'].items():
        if e.get('gewaehlt') is None:
            w('| %s | keine | - | - | - | - | - | - | inconclusive |' % e['name'])
            continue
        t, v, tr = e['test'], e['val'], e['train']
        w('| %s | %s | %d / %s | %d / %s | %d / %s | %s | %s | %d von %d | **%s** |' % (
            e['name'], vlabel(e['gewaehlt']), tr['n'], f2(tr['avg_r'], 3), v['n'], f2(v['avg_r'], 3), t['n'], f2(t['avg_r'], 3),
            pf_(t['pf']), ('%.0f %%' % (t['win'] * 100)) if t['win'] is not None else '-', t['coins_pos'], t['coins_total'], e['verdikt']))
    w('')
    for kid, e in J['kandidaten'].items():
        K = KAND[kid]
        w('## %s' % e['name'])
        w('')
        if e.get('gewaehlt') is None:
            w('Keine Variante mit mindestens %d Trainings-Trades, daher kein Test.' % MIN_TRAIN_TRADES)
            w('')
            continue
        regeln = {
            'K1': ['Zeitrahmen 4h. Signalkerze i: Ruhe `r12 < K x r96` (Box = Kerzen i-12..i-1, r12 = Mittel Hoch-Tief der Box, r96 = Mittel der Kerzen i-108..i-13) UND Close[i] > höchstes Hoch der Box (long) bzw. < tiefstes Tief (short); '
                   'mit V=an zusätzlich Volumen[i] >= 1,5 x Median-Volumen der Kerzen i-48..i-1.',
                   'Einstieg Open[i+1]. Anfangsstop = Boxmitte, Abstand zum Einstieg auf 1,5 bis 3,0 x ATR14[i] begrenzt; 1R = Abstand Einstieg-Stop.',
                   'Ausstieg: Chandelier-Trail (long: höchstes Hoch seit Einstieg minus T x ATR14, steigt nur, wirkt ab der Folgekerze; short gespiegelt) oder Zeitausstieg zum Schluss der 12. Kerze (48 h). Kein festes Ziel.'],
            'K2': ['Zeitrahmen 1h. Signal wie K1 (ohne Volumen), aber **Gegenrichtung**: Close > Boxhoch => SHORT, Close < Boxtief => LONG. Bei S=an nur Signalkerzen mit Start 12:00 bis 21:00 UTC und Montag bis Freitag.',
                   'Einstieg Open[i+1]. Fester Stop = Einstieg -/+ SF x ATR14[i]; 1R = dieser Abstand. Kein Ziel.',
                   'Ausstieg: Stop oder Zeitausstieg zum Schluss der 12. Kerze (12 h).'],
            'K3': ['Zeitrahmen 4h. Signalkerze i: (1) Ruhe `r12 < K x r96`; (2) Volumen[i] >= VT x Median-Volumen der Kerzen i-48..i-1; (3) Hoch-Tief[i] >= 1,5 x ATR14[i-1]; '
                   '(4) long, wenn Close > Open und (Close-Tief)/(Hoch-Tief) > 0,75, short, wenn Close < Open und < 0,25.',
                   'Einstieg in Kerzenrichtung zum Open[i+1]. Anfangsstop = Mitte der Schub-Kerze, Abstand auf 1,5 bis 3,0 x ATR14[i-1] begrenzt; 1R = Abstand Einstieg-Stop.',
                   'Ausstieg: Stop oder Zeitausstieg zum Schluss der H-ten Kerze nach Einstieg (H = 3: 12 h, H = 6: 24 h). Kein Ziel.'],
        }[kid]
        w('**Regeln**')
        for z in regeln:
            w('- ' + z)
        w('- Gitter (8 Varianten): ' + '; '.join('(' + vlabel(p) + ')' for p in K['gitter']))
        w('- Urteils-Coins: %s. Kontroll-Coins (getrennt, nicht im Urteil): %s.' % (', '.join(K['coins']), ', '.join(K['kontrolle']) or 'keine'))
        w('')
        w('**Alle %d Varianten auf Training und Validierung** (Auswahl nur nach Training, die Validierungsspalten wurden zur Auswahl nicht benutzt):' % len(K['gitter']))
        w('')
        w('| Variante | Train n | Train Ø R | Train PF | Train Coins>0 | Val n | Val Ø R | Val PF | Val Coins>0 | gewählt |')
        w('|---|---|---|---|---|---|---|---|---|---|')
        for z in A['kandidaten'][kid]['zeilen']:
            tr, va = z['train'], z['val']
            w('| %s | %d | %s | %s | %d/%d | %d | %s | %s | %d/%d | %s |' % (
                vlabel(z['params']), tr['n'], f2(tr['avg_r'], 3), pf_(tr['pf']), tr['coins_pos'], tr['coins_total'],
                va['n'], f2(va['avg_r'], 3), pf_(va['pf']), va['coins_pos'], va['coins_total'], 'ja' if z['params'] == e['gewaehlt'] else ''))
        w('')
        w('**Gewählte Variante: %s**' % vlabel(e['gewaehlt']))
        w('')
        w('| Abschnitt | Trades | Ø R (netto) | Standardfehler Ø R | Profit-Faktor | Gewinnquote | Ø Rendite je Trade (netto) | Ø Kerzen | Coins im Plus |')
        w('|---|---|---|---|---|---|---|---|---|')
        for ab, nm in (('train', 'Training'), ('val', 'Validierung'), ('test', 'Test')):
            s = e[ab]
            w('| %s | %d | %s | %s | %s | %s | %s %% | %s | %d von %d |' % (
                nm, s['n'], f2(s['avg_r'], 3), ('%.3f' % s['se']) if s['se'] else '-', pf_(s['pf']),
                ('%.0f %%' % (s['win'] * 100)) if s['win'] is not None else '-', f2(s['netpct'], 3) if s['netpct'] is not None else '-',
                ('%.1f' % s['k']) if s['k'] else '-', s['coins_pos'], s['coins_total']))
        w('')
        w('**Je Coin (Urteils-Coins)**')
        w('')
        w('| Coin | Test-Zeitraum | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |')
        w('|---|---|---|---|---|---|---|---|')
        for c in K['coins']:
            zr = e['test_coin_zeitraum'][c]
            w('| %s | %s bis %s | %d | %s | %d | %s | %d | %s |' % (
                c, zr[0], zr[1], e['train_coins'][c]['n'], f2(e['train_coins'][c]['avg_r'], 3) if e['train_coins'][c]['n'] else '-',
                e['val_coins'][c]['n'], f2(e['val_coins'][c]['avg_r'], 3) if e['val_coins'][c]['n'] else '-',
                e['test_coins'][c]['n'], f2(e['test_coins'][c]['avg_r'], 3) if e['test_coins'][c]['n'] else '-'))
        w('')
        if K['kontrolle']:
            w('**Kontroll-Coins (nicht im Urteil, getrennt ausgewiesen)**')
            w('')
            w('| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |')
            w('|---|---|---|---|---|---|---|')
            for c in K['kontrolle']:
                w('| %s | %d | %s | %d | %s | %d | %s |' % (
                    c, e['train_coins'][c]['n'], f2(e['train_coins'][c]['avg_r'], 3) if e['train_coins'][c]['n'] else '-',
                    e['val_coins'][c]['n'], f2(e['val_coins'][c]['avg_r'], 3) if e['val_coins'][c]['n'] else '-',
                    e['test_coins'][c]['n'], f2(e['test_coins'][c]['avg_r'], 3) if e['test_coins'][c]['n'] else '-'))
            kt = e['test_kontrolle']
            w('')
            w('Kontrollgruppe gepoolt: Train Ø R %s (n=%d), Val Ø R %s (n=%d), Test Ø R %s (n=%d).' % (
                f2(e['train_kontrolle']['avg_r'], 3), e['train_kontrolle']['n'], f2(e['val_kontrolle']['avg_r'], 3), e['val_kontrolle']['n'],
                f2(kt['avg_r'], 3), kt['n']))
            w('')
        p = e['portfolio']
        w('**Test-Portfolio bei 2 %% Risiko je Trade (Urteils-Coins, max. 4 gleichzeitig)**: Zeitraum %s bis %s (%.0f Tage).' % (e['test_von'], e['test_bis'], e['test_tage']))
        w('')
        w('| Kennzahl | Wert |')
        w('|---|---|')
        w('| Test-Rendite | %s %% |' % f2(p['rendite_pct'], 2))
        w('| Rendite pro Kalendertag (linear) | %s %% |' % f2(p['rendite_pct'] / max(e['test_tage'], 1), 3))
        w('| größter Rückgang (realisiertes Konto) | %.2f %% |' % p['max_rueckgang_pct'])
        w('| bester einzelner Tag | %s %% (%s) |' % (f2(p['bester_tag_pct'], 2), p['bester_tag']))
        w('| schlechtester einzelner Tag | %s %% (%s) |' % (f2(p['schlechtester_tag_pct'], 2), p['schlechtester_tag']))
        w('| genommene / wegen 4er-Grenze ausgelassene Trades | %d / %d |' % (p['genommen'], p['uebersprungen']))
        w('| höchster Gesamt-Nominalwert / Konto | %.2f |' % p['max_hebel'])
        w('')
        w('Test-Details: Ausstiege Stop %d / Zeit %d; Long %d / Short %d; ' % (e['test_grund']['stop'], e['test_grund']['zeit'], e['test_long_short']['long'], e['test_long_short']['short']) +
          ('Ø R ohne die 3 besten Trades %s; ' % f2(e['test_avg_r_ohne_top3'], 3) if e['test_avg_r_ohne_top3'] is not None else '') +
          'beste R: %s, schlechteste R: %s.' % (', '.join('%+.2f' % x for x in e['test_beste_r']), ', '.join('%+.2f' % x for x in e['test_schlechteste_r'])))
        w('')
        krit = e['kriterien']
        w('Kriterien: Test-Ø R > 0: **%s**; Validierung-Ø R > 0: **%s**; Test-Trades >= 30: **%s** (%d); mindestens die Hälfte der Coins im Plus: **%s** (%d von %d). => **%s**' % (
            'ja' if krit['test_avg_r_pos'] else 'nein', 'ja' if krit['val_avg_r_pos'] else 'nein', 'ja' if krit['test_trades_min30'] else 'nein', e['test']['n'],
            'ja' if krit['haelfte_coins_plus'] else 'nein', e['test']['coins_pos'], e['test']['coins_total'], e['verdikt']))
        w('')
    w('## Vorbehalte')
    w('')
    w('- Die Trades sind nicht unabhängig: Ausbrüche und Schübe treten über Alts hinweg gleichzeitig auf (gemeinsamer Marktfaktor), das effektive n ist kleiner als gezählt, die Standardfehler sind zu optimistisch.')
    w('- Mehrfachtest: 24 Gitter-Varianten plus die Vorab-Suche. Die Gewinn-Hypothesen wurden im Trainingsteil gefunden; nur Validierung und Test sind echte Außer-Stichprobe-Prüfungen.')
    w('- Regimewechsel: siehe Datenfenster oben (4h-Training Aufwärtsphase, 4h-Validierung Bärenmarkt, 4h-Test seitwärts bis leicht aufwärts bei BTC). 1h hat nur etwa 208 Tage, der 1h-Test nur etwa 52 Tage; K2 mit Sitzungsfilter hat dort zu wenige Signale.')
    w('- Das Portfolio rechnet ohne Zwischenbewertung offener Positionen; Slippage in Ausbruchskerzen dünner Alts kann über 0,03 % liegen; Funding ist pauschal angesetzt.')
    w('- Nichts hiervon ist ein „+50 %% pro Tag“-Ansatz: auch ein bestätigter Vorteil wäre bei 2 %% Risiko je Trade im Bereich weniger Zehntel Prozent Konto pro Tag.')
    w('')
    with open(F_MD, 'w') as f:
        f.write('\n'.join(L).replace('%%', '%') + '\n')
    print('Markdown geschrieben:', F_MD)


if __name__ == '__main__':
    modus = sys.argv[1] if len(sys.argv) > 1 else ''
    if modus == 'selbsttest':
        selbsttest()
    elif modus == 'dev':
        dev()
    elif modus == 'test':
        test()
    elif modus == 'md':
        md()
    else:
        print(__doc__)
