"""Der Chart-Leser: liest Hyperliquid-Charts auf 1d, 4h, 1h und 15m und fasst sie zu einer Lesart mit Plan zusammen.

Der Plan nennt NUR Chart-Niveaus (Auslöser, Ungültigkeit, Ziele), keine Prozentwerte. Das Ungültigkeits-Niveau ist der Kurs, bei dem
die Lesart falsch war. Der Bot braucht aus Sicherheitsgründen einen Stop-Kurs: dieser Kurs ist genau dieses Niveau."""
import json
import os

from . import data
from .events import detect
from .series import Series
from .structure import nearest_zones, trend_at

TF = {"1d": (400, 3, 3, 3.0), "4h": (400, 3, 3, 2.0), "1h": (400, 3, 3, 1.0), "15m": (300, 2, 2, 0.5)}   # Kerzen, links, rechts, Gewicht
EVIDENCE = json.load(open(os.path.join(os.path.dirname(__file__), "evidence.json")))
TXT = {"up": "Aufwärtstrend (höhere Hochs und Tiefs)", "down": "Abwärtstrend (tiefere Hochs und Tiefs)", "range": "Seitwärts/ohne klare Struktur"}
EVT = {"pullback_rejection": "Rücksetzer mit Ablehnungs-Kerze an einer Zone", "zone_rejection": "Ablehnungs-Kerze an einer Zone",
       "bos_volume": "Strukturbruch in Trendrichtung mit Volumen", "bos": "Strukturbruch in Trendrichtung", "choch": "erster Bruch gegen die Struktur (Trendwechsel)",
       "sweep_reclaim": "Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen", "rsi_divergence": "RSI-Divergenz am neuen Swing",
       "squeeze_break": "Ausbruch aus enger Bollinger-Spanne mit Volumen"}


def px(x):
    return float(f"{x:.6g}") if x is not None else None


def read_tf(tf, cs):
    n, left, right, _ = TF[tf]
    S = Series(cs, left, right)
    i = S.n - 1
    sup, res = nearest_zones(S, i)
    hs, ls = S.highs(i, 2), S.lows(i, 2)
    recent = []
    for k in range(i - 2, i + 1):                        # Ereignisse der letzten 3 geschlossenen Kerzen
        for name, side in detect(S, k):
            recent.append({"event": name, "side": side, "bars_ago": i - k, "evidence": EVIDENCE.get(f"{name}:{side}", "info")})
    atr_series = S.atr
    rank = sum(1 for v in atr_series[-100:] if v <= atr_series[i]) / max(1, len(atr_series[-100:]))
    return {"tf": tf, "close": S.c[i], "trend": trend_at(S, i), "atr": px(S.atr[i]), "atr_rank": round(rank, 2),
            "rsi": round(S.rsi[i], 1), "vs_ema50": "über" if S.c[i] > S.e50[i] else "unter", "vs_ema200": "über" if S.c[i] > S.e200[i] else "unter",
            "squeeze": S.bbw_rank(i) <= 0.2, "volume_ratio": round(S.vr[i], 2),
            "last_swing_high": px(hs[-1][1]) if hs else None, "last_swing_low": px(ls[-1][1]) if ls else None,
            "support": {k: px(sup[k]) for k in ("low", "high")} | {"touches": sup["touches"]} if sup else None,
            "resistance": {k: px(res[k]) for k in ("low", "high")} | {"touches": res["touches"]} if res else None,
            "events": recent, "_S": S}


def read(coin, ctx=True):
    tfs = {}
    for tf, (n, *_rest) in TF.items():
        cs = data.candles(coin, tf, n)
        if len(cs) < 120:
            continue
        tfs[tf] = read_tf(tf, cs)
    score = {"long": 0.0, "short": 0.0}; why = {"long": [], "short": []}
    for tf, r in tfs.items():
        w = TF[tf][3]
        if r["trend"] == "up":
            score["long"] += w; why["long"].append(f"{tf}: Aufwärtstrend (+{w:g})")
        elif r["trend"] == "down":
            score["short"] += w; why["short"].append(f"{tf}: Abwärtstrend (+{w:g})")
        for e in r["events"]:
            pts = {"kandidat": 1.5, "bestätigt": 3.0}.get(e["evidence"], 0.0) * (1.0 if e["bars_ago"] == 0 else 0.5)
            if pts:
                score[e["side"]] += pts; why[e["side"]].append(f"{tf}: {EVT[e['event']]} ({e['evidence']}, +{pts:g})")
    c = data.context(coin) if ctx else None
    if c:
        if c["funding_per_hour"] > 0.00005:
            score["short"] += 0.5; why["short"].append("Funding hoch positiv (Longs überfüllt, +0,5)")
        if c["funding_per_hour"] < -0.00005:
            score["long"] += 0.5; why["long"].append("Funding negativ (Shorts überfüllt, +0,5)")
    diff = score["long"] - score["short"]
    bias = "long" if diff >= 3 else "short" if diff <= -3 else "neutral"
    plan = make_plan(tfs, bias) if bias != "neutral" else None
    for r in tfs.values():
        r.pop("_S")
    return {"coin": coin, "price": (c or {}).get("mark") or tfs["1h"]["close"], "timeframes": tfs, "context": c, "score": score, "why": why,
            "bias": bias, "plan": plan, "evidence_note": "Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil."}


def make_plan(tfs, bias):
    """Plan aus Chart-Niveaus (Zeitebene 1h): Auslöser, Ungültigkeit, Ziele."""
    t = tfs.get("1h")
    if not t:
        return None
    long = bias == "long"
    a = t["atr"]
    if long:
        inval = t["last_swing_low"]
        if t["support"]:
            inval = min(inval, t["support"]["low"] - 0.25 * a) if inval else t["support"]["low"] - 0.25 * a
        trigger = t["last_swing_high"]
        targets = [x for x in (tfs.get("1h", {}).get("resistance"), tfs.get("4h", {}).get("resistance")) if x]
        tg = sorted({px(x["low"]) for x in targets if not trigger or x["low"] > trigger})
    else:
        inval = t["last_swing_high"]
        if t["resistance"]:
            inval = max(inval, t["resistance"]["high"] + 0.25 * a) if inval else t["resistance"]["high"] + 0.25 * a
        trigger = t["last_swing_low"]
        targets = [x for x in (tfs.get("1h", {}).get("support"), tfs.get("4h", {}).get("support")) if x]
        tg = sorted({px(x["high"]) for x in targets if not trigger or x["high"] < trigger}, reverse=True)
    return {"richtung": bias, "ausloeser": f"1h-Schluss {'über' if long else 'unter'} {trigger}" if trigger else None,
            "ungueltig": f"1h-Schluss {'unter' if long else 'über'} {px(inval)}" if inval else None, "ungueltig_kurs": px(inval), "ziele": tg}


def explain(r):
    """Lesart als lesbarer deutscher Text."""
    out = [f"=== {r['coin']}  Kurs {r['price']:g} ==="]
    for tf in ("1d", "4h", "1h", "15m"):
        t = r["timeframes"].get(tf)
        if not t:
            continue
        line = f"{tf:3} {TXT[t['trend']]}; Kurs {t['vs_ema50']} EMA50, {t['vs_ema200']} EMA200; RSI {t['rsi']}; Schwankung {t['atr_rank'] * 100:.0f}. Perzentil"
        if t["squeeze"]:
            line += "; Bollinger-Spanne eng (Ausbruch möglich)"
        out.append(line)
        if t["support"] or t["resistance"]:
            s, w = t["support"], t["resistance"]
            out.append("     " + (f"Unterstützung {s['low']:g}–{s['high']:g} ({s['touches']}x)" if s else "keine Unterstützung") + " | " +
                       (f"Widerstand {w['low']:g}–{w['high']:g} ({w['touches']}x)" if w else "kein Widerstand"))
        for e in t["events"]:
            out.append(f"     Ereignis: {e['side'].upper()} – {EVT[e['event']]} [{e['evidence']}], vor {e['bars_ago']} Kerzen")
    c = r["context"]
    if c:
        out.append(f"Kontext: Funding {c['funding_per_hour'] * 100:+.4f} %/h, offenes Volumen {c['open_interest_usd'] / 1e6:.0f} Mio $, Orderbuch {'Käufer' if c['book_imbalance'] > 0 else 'Verkäufer'} +{abs(c['book_imbalance']) * 100:.0f} %, Spread {c['spread_pct']:.3f} %")
    out.append(f"Punkte: Long {r['score']['long']:g} | Short {r['score']['short']:g}  ->  Tendenz: {r['bias'].upper()}")
    for side in ("long", "short"):
        if r["why"][side]:
            out.append(f"  {side}: " + "; ".join(r["why"][side]))
    p = r["plan"]
    if p:
        out.append(f"PLAN {p['richtung'].upper()}: Auslöser {p['ausloeser']}; ungültig bei {p['ungueltig']}; Ziele {p['ziele'] or 'nächste Zonen prüfen'}")
    else:
        out.append("PLAN: keiner (Tendenz neutral)")
    out.append(r["evidence_note"])
    return "\n".join(out)
