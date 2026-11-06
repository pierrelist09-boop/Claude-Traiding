"""Forward-Journal: jede Lesart wird mit Zeit, Preis, Punkten und Ereignissen gespeichert (journal/readings.jsonl). Später prüft
research/forward_check.py, was der Kurs danach wirklich getan hat. Das ist der einzige echte Test ohne Rückblick-Verzerrung."""
import json
import os
import time

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "journal", "readings.jsonl")


def log(r):
    ev = [{"tf": tf, "event": e["event"], "side": e["side"], "evidence": e["evidence"], "bars_ago": e["bars_ago"]}
          for tf, t in r["timeframes"].items() for e in t["events"]]
    row = {"ts": int(time.time()), "coin": r["coin"], "price": r["price"], "bias": r["bias"], "score": r["score"],
           "trend": {tf: t["trend"] for tf, t in r["timeframes"].items()}, "events": ev, "plan": r["plan"]}
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
