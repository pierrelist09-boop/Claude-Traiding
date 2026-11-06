"""python -m chartreader BTC [ETH ...] [--json] [--log]   (--log speichert die Lesart im Forward-Journal)"""
import json
import sys

from . import journal
from .reader import explain, read

args = [a for a in sys.argv[1:] if not a.startswith("--")]
for coin in args or ["BTC"]:
    r = read(coin)
    if "--log" in sys.argv:
        journal.log(r)
    print(json.dumps(r, ensure_ascii=False, indent=1) if "--json" in sys.argv else explain(r))
    print()
