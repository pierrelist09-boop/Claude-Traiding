"""Öffentliche Hyperliquid-Daten (kein Schlüssel nötig): Kerzen, Funding, offenes Volumen, Orderbuch."""
import json
import os
import time
import urllib.request

HL = "https://api.hyperliquid.xyz/info"
MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}
CACHE = os.environ.get("CHARTREADER_CACHE", os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache"))


def post(body, tries=6):
    req = urllib.request.Request(HL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception:                     # meist Rate-Limit: länger warten
            time.sleep(2.5 * (a + 1))
    raise RuntimeError("Hyperliquid nicht erreichbar")


def candles(coin, interval, n=5000, use_cache=False, max_age=3 * 3600):
    """Die letzten n GESCHLOSSENEN Kerzen als Liste von Dicts {t,T,o,h,l,c,v}. Die laufende Kerze fehlt absichtlich."""
    path = os.path.join(CACHE, f"{coin}_{interval}.json")
    if use_cache and os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age:
        return json.load(open(path))
    now = int(time.time() * 1000)
    rows = post({"type": "candleSnapshot", "req": {"coin": coin, "interval": interval, "startTime": now - n * MS[interval], "endTime": now}})
    out = [{"t": r["t"], "T": r["T"], "o": float(r["o"]), "h": float(r["h"]), "l": float(r["l"]), "c": float(r["c"]), "v": float(r["v"])}
           for r in rows if r["T"] < now]
    if use_cache:
        os.makedirs(CACHE, exist_ok=True)
        json.dump(out, open(path, "w"))
        time.sleep(0.6)                       # Hyperliquid begrenzt Abfragen je IP
    return out


def context(coin):
    """Funding je Stunde, offenes Volumen, Mark-Preis, Orderbuch-Ungleichgewicht (Käufer minus Verkäufer in den ersten 10 Stufen)."""
    meta, ctx = post({"type": "metaAndAssetCtxs"})
    c = next(x for u, x in zip(meta["universe"], ctx) if u["name"] == coin)
    mark = float(c["markPx"])
    book = post({"type": "l2Book", "coin": coin})["levels"]
    side = lambda L: sum(float(x["sz"]) * float(x["px"]) for x in L[:10])
    bid, ask = side(book[0]), side(book[1])
    return {"mark": mark, "funding_per_hour": float(c["funding"]), "open_interest_usd": float(c["openInterest"]) * mark,
            "day_volume_usd": float(c["dayNtlVlm"]), "book_bid_usd": bid, "book_ask_usd": ask,
            "book_imbalance": (bid - ask) / (bid + ask) if bid + ask else 0.0,
            "spread_pct": (float(book[1][0]["px"]) - float(book[0][0]["px"])) / mark * 100}
