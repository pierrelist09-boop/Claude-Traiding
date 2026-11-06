# Simulation ab 2024-11-06 (berechnet 2026-11-06)

Zwei Jahre Historie, Konto 1.000 $, Zinseszins, 8 Coins (BTC ETH SOL XRP DOGE LINK AVAX HYPE), höchstens 4 Positionen (je höchstens 1,5-faches, insgesamt 3-faches Kontovolumen). Gebühr 0,045 %, Slippage 0,02 %, Funding eingerechnet. Risiko = Verlust bis zum Stop in % des Kontos je Trade. Quelle: `research/simulation.py`.

| Lauf | Endkonto | pro Jahr | größter Rückgang | Trades | Treffer |
|---|---|---|---|---|---|
| E 2 % | 1,591 $ | +26 % | 16 % | 112 | 45 % |
| E 4 % | 2,143 $ | +47 % | 30 % | 112 | 45 % |
| E 6 % | 2,558 $ | +60 % | 40 % | 109 | 45 % |
| E 8 % | 3,136 $ | +78 % | 41 % | 98 | 45 % |
| A (altes K) 2 % | 1,322 $ | +15 % | 26 % | 178 | 40 % |
| C1 Chart-Umkehr 1 % | 2,327 $ | +53 % | 39 % | 827 | 21 % |
| adaptiv 2 % | 2,061 $ | +44 % | 53 % | 539 | 22 % |

Buy&Hold je Coin seit Start: BTC +2 %, ETH -13 %, SOL -51 %, XRP +122 %, DOGE -66 %, LINK -7 %, AVAX -68 %, HYPE +480 % (gleichgewichtet +50 %).

**E** = langsame 4h-Trendfolge (Donchian 100, Stop 4 ATR, Trail 5 ATR, nur in Richtung des Tagestrends). Sie war in allen vier Halbjahren positiv (Ø R: +0,17, +0,24, +0,11, +0,50).

## Gewinn je Coin (E, 4 % Risiko)

| Coin | Trades | Treffer | Ø R | Gewinn | Buy&Hold |
|---|---|---|---|---|---|
| BTC | 18 | 50 % | +0.42 | +304 $ | +2 % |
| ETH | 11 | 36 % | +0.32 | +141 $ | -13 % |
| SOL | 12 | 42 % | +0.02 | -21 $ | -51 % |
| XRP | 15 | 47 % | +0.54 | +347 $ | +122 % |
| DOGE | 16 | 38 % | +0.11 | -9 $ | -66 % |
| LINK | 10 | 50 % | +0.29 | +168 $ | -7 % |
| AVAX | 15 | 60 % | +0.13 | +53 $ | -68 % |
| HYPE | 15 | 33 % | +0.14 | +160 $ | +480 % |

## Verbesserungsrunden (aktiv, alle auf denselben zwei Jahren; deshalb optimistisch)

1. **Start:** altes K (A) bringt nur +15 %/Jahr bei 2 % Risiko. Die langsame Variante E: +26 %/Jahr bei 16 % Rückgang, schon bei 2 %.
2. **Walk-forward-Auswahl** (alle 91 Tage beste Kandidaten-Strategie aus abgeschlossenen Trades) schlägt E nicht (2.061 $ bei 2 % mit 53 % Rückgang gegen 1.591 $ mit 16 %): Auswahl erzeugt Rauschen und mehr Rückgang.
3. **Mehr Positionen** (6, 8) und **mehr Coins** (15) verbessern nichts: Positionen laufen gleich, Rückgang steigt (15 Coins bei 4 %: 2.049 $ mit 45 % Rückgang statt 2.143 $ mit 30 %).
4. **Einsatz:** E skaliert mit dem Risiko, aber nicht stetig (8 % → 3.136 $, 10 % → 2.814 $): der Rückgang wächst schneller als der Gewinn.
5. **Chart-Umkehr C1** ist ohne Pfad hübsch (2.144 $ bei 2 %), aber instabil über die Halbjahre, an drei Coins aufgehängt und mit 64 % Rückgang. Nicht empfohlen.

**Ehrliche Einordnung:** +2.500 $ Gewinn wären in diesen zwei Jahren mit E nur bei etwa 8 bis 10 % Risiko je Trade und rund 40 % Rückgang nahe gewesen (3.136 $ bei 8 %). Das ist eine Rückschau auf eine Periode mit starker Trendphase 2025, die sich nicht wiederholen muss. Statistisch trägt die Aussage (Ø +0,25 R je Trade, 142 Trades) nur schwach.

