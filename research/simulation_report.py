#!/usr/bin/env python3
"""Schreibt die Ergebnisse der Zwei-Jahres-Simulation: simulation/ergebnis.md, simulation/trades_E.csv und coins/<COIN>/simulation.md."""
import csv
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research import simulation as SM

ROOT = SM.ROOT


def month(t):
    return time.strftime("%Y-%m", time.gmtime(t / 1000))


def main():
    D = SM.load()
    bh = SM.bh(D)
    E, _ = SM.build(D, "E")
    C1, _ = SM.build(D, "C1")
    AD, chosen = SM.build(D, "adapt")
    A, _ = SM.build(D, "A")
    runs = {"E 2 %": SM.portfolio(E, 0.02), "E 4 %": SM.portfolio(E, 0.04), "E 6 %": SM.portfolio(E, 0.06), "E 8 %": SM.portfolio(E, 0.08),
            "A (altes K) 2 %": SM.portfolio(A, 0.02), "C1 Chart-Umkehr 1 %": SM.portfolio(C1, 0.01), "adaptiv 2 %": SM.portfolio(AD, 0.02)}
    os.makedirs(os.path.join(ROOT, "simulation"), exist_ok=True)
    main_run = runs["E 4 %"]
    with open(os.path.join(ROOT, "simulation", "trades_E_4pct.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["coin", "richtung", "einstieg", "ausstieg", "R_netto", "stop_abstand_anteil", "volumen_usd", "gewinn_usd"])
        for p in sorted(main_run["done"], key=lambda p: p["t"]):
            w.writerow([p["coin"], p["side"], month(p["t"]), month(p["exit"]), round(p["R"], 3), round(p["stop"], 4), round(p["notional"]), round(p["pnl"], 2)])
    L = [f"# Simulation ab 2024-11-06 (berechnet {time.strftime('%Y-%m-%d')})", "",
         "Zwei Jahre Historie, Konto 1.000 $, Zinseszins, 8 Coins (BTC ETH SOL XRP DOGE LINK AVAX HYPE), höchstens 4 Positionen (je höchstens 1,5-faches, insgesamt 3-faches Kontovolumen). Gebühr 0,045 %, Slippage 0,02 %, Funding eingerechnet. "
         "Risiko = Verlust bis zum Stop in % des Kontos je Trade. Quelle: `research/simulation.py`.", "",
         "| Lauf | Endkonto | pro Jahr | größter Rückgang | Trades | Treffer |", "|---|---|---|---|---|---|"]
    for name, r in runs.items():
        L.append(f"| {name} | {r['final']:,.0f} $ | {r['cagr'] * 100:+.0f} % | {r['dd'] * 100:.0f} % | {r['n']} | {r['win'] * 100:.0f} % |")
    L += ["", f"Buy&Hold je Coin seit Start: " + ", ".join(f"{c} {v * 100:+.0f} %" for c, v in bh.items()) + f" (gleichgewichtet {sum(bh.values()) / len(bh) * 100:+.0f} %).", "",
          "**E** = langsame 4h-Trendfolge (Donchian 100, Stop 4 ATR, Trail 5 ATR, nur in Richtung des Tagestrends). Sie war in allen vier Halbjahren positiv (Ø R: +0,17, +0,24, +0,11, +0,50).", ""]
    L += ["## Gewinn je Coin (E, 4 % Risiko)", "", "| Coin | Trades | Treffer | Ø R | Gewinn | Buy&Hold |", "|---|---|---|---|---|---|"]
    for c in SM.COINS:
        ps = [p for p in main_run["done"] if p["coin"] == c]
        L.append(f"| {c} | {len(ps)} | {sum(1 for p in ps if p['pnl'] > 0) / len(ps) * 100 if ps else 0:.0f} % | {sum(p['R'] for p in ps) / len(ps) if ps else 0:+.2f} | {sum(p['pnl'] for p in ps):+,.0f} $ | {bh.get(c, 0) * 100:+.0f} % |")
    L += ["", "## Verbesserungsrunden (aktiv, alle auf denselben zwei Jahren; deshalb optimistisch)", "",
          "1. **Start:** altes K (A) bringt nur +15 %/Jahr bei 2 % Risiko. Die langsame Variante E: +26 %/Jahr bei 16 % Rückgang, schon bei 2 %.",
          "2. **Walk-forward-Auswahl** (alle 91 Tage beste Kandidaten-Strategie aus abgeschlossenen Trades) schlägt E nicht (2.061 $ bei 2 % mit 53 % Rückgang gegen 1.591 $ mit 16 %): Auswahl erzeugt Rauschen und mehr Rückgang.",
          "3. **Mehr Positionen** (6, 8) und **mehr Coins** (15) verbessern nichts: Positionen laufen gleich, Rückgang steigt (15 Coins bei 4 %: 2.049 $ mit 45 % Rückgang statt 2.143 $ mit 30 %).",
          "4. **Einsatz:** E skaliert mit dem Risiko, aber nicht stetig (8 % → 3.136 $, 10 % → 2.814 $): der Rückgang wächst schneller als der Gewinn.",
          "5. **Chart-Umkehr C1** ist ohne Pfad hübsch (2.144 $ bei 2 %), aber instabil über die Halbjahre, an drei Coins aufgehängt und mit 64 % Rückgang. Nicht empfohlen.", "",
          "**Ehrliche Einordnung:** +2.500 $ Gewinn wären in diesen zwei Jahren mit E nur bei etwa 8 bis 10 % Risiko je Trade und rund 40 % Rückgang nahe gewesen (3.136 $ bei 8 %). "
          "Das ist eine Rückschau auf eine Periode mit starker Trendphase 2025, die sich nicht wiederholen muss. Statistisch trägt die Aussage (Ø +0,25 R je Trade, 142 Trades) nur schwach.", ""]
    open(os.path.join(ROOT, "simulation", "ergebnis.md"), "w").write("\n".join(L) + "\n")
    for c in SM.COINS:
        d = os.path.join(ROOT, "coins", c)
        os.makedirs(d, exist_ok=True)
        ps = sorted([p for p in main_run["done"] if p["coin"] == c], key=lambda p: p["t"])
        by = defaultdict(float)
        for p in ps:
            by[time.strftime("%Y-%m", time.gmtime(p["exit"] / 1000))[:4] + ("H1" if int(month(p["exit"])[5:]) <= 6 else "H2")] += p["pnl"]
        C = [f"# {c}: Simulation (zwei Jahre ab 2024-11-06, Strategie E, 4 % Risiko)", "",
             f"Konto 1.000 $, gemeinsam mit den anderen 7 Coins gehandelt (höchstens 4 Positionen). Gesamtlauf: Endkonto {main_run['final']:,.0f} $, {main_run['cagr'] * 100:+.0f} % pro Jahr, größter Rückgang {main_run['dd'] * 100:.0f} %.", "",
             f"- Trades: **{len(ps)}**, Treffer {sum(1 for p in ps if p['pnl'] > 0) / len(ps) * 100 if ps else 0:.0f} %, Ø {sum(p['R'] for p in ps) / len(ps) if ps else 0:+.2f} R",
             f"- **Beitrag zum Konto: {sum(p['pnl'] for p in ps):+,.0f} $** (Anteil am Gesamtgewinn {sum(p['pnl'] for p in ps) / max(1e-9, main_run['final'] - 1000) * 100:.0f} %)",
             f"- Zum Vergleich Buy&Hold dieses Coins seit Start: {bh.get(c, 0) * 100:+.0f} %", "- Gewinn nach Halbjahr (Ausstieg): " + ", ".join(f"{k} {v:+,.0f} $" for k, v in sorted(by.items())), "",
             "| Einstieg | Ausstieg | Richtung | R | Volumen | Gewinn |", "|---|---|---|---|---|---|"]
        for p in ps:
            C.append(f"| {month(p['t'])} | {month(p['exit'])} | {p['side']} | {p['R']:+.2f} | {p['notional']:,.0f} $ | {p['pnl']:+,.0f} $ |")
        open(os.path.join(d, "simulation.md"), "w").write("\n".join(C) + "\n")
    for name, r in runs.items():
        print(f"{name:22} {r['final']:7.0f} $ {r['cagr'] * 100:+4.0f}%/Jahr DD {r['dd'] * 100:3.0f}% Trades {r['n']}")
    print({c: round(sum(p['pnl'] for p in main_run['done'] if p['coin'] == c)) for c in SM.COINS})


if __name__ == "__main__":
    main()
