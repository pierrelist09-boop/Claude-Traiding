# Plugin-Test der Trendfolge E (2024-08-30 bis 2026-11-06, 10 Coins, 8 Folds)

| Variante | Trades | Ø R | Folds > 0 | Folds besser als E | Δ Ø R zu E (95 %-Block-Bootstrap) | Deflated Sharpe |
|---|---|---|---|---|---|---|
| E  Basis (Donchian 100, Trail 5) | 207 | +0.194 | 6/8 | – | – | 0.99 |
| V1 Regime: Tages-ADX >= 20 | 197 | +0.179 | 6/8 | 4/8 | -0.015 [-0.053; +0.017] | 0.97 |
| V2 Regime: Tages-ADX >= 25 | 166 | +0.223 | 5/8 | 5/8 | +0.029 [-0.094; +0.146] | 0.98 |
| V3 Regime: kein 'Chaos' (Vol-Perzentil >= 70 % und ADX < 25) | 202 | +0.204 | 6/8 | 3/8 | +0.010 [-0.011; +0.031] | 0.99 |
| V4 Regime: Hurst (100 Tage Rendite) > 0,55 | 200 | +0.173 | 6/8 | 2/8 | -0.021 [-0.056; +0.014] | 0.97 |
| V5 Zeitstopp 30 Kerzen (5 Tage), nur wenn im Minus | 222 | +0.179 | 6/8 | 3/8 | -0.015 [-0.078; +0.038] | 0.99 |
| V6 Zeitstopp 60 Kerzen (10 Tage), nur wenn im Minus | 208 | +0.192 | 6/8 | 1/8 | -0.002 [-0.011; +0.004] | 0.99 |
| V7 Gestaffelt: 25 % bei 2 R (Rest-Stop Einstand), 25 % bei 4 R | 207 | +0.187 | 6/8 | 3/8 | -0.006 [-0.044; +0.022] | 0.99 |

Deflated Sharpe: Wahrscheinlichkeit, dass der echte Sharpe je Trade größer ist als das beste Zufallsergebnis aus 8 Versuchen (Hürde laut Plugin: > 0,95). Folds: Ø R je Fold nach Einstiegszeit, leere Folds zählen weder als positiv noch als besser.

Ø R je Fold (E / beste Abweichung siehe Tabelle oben):

| Variante | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 |
|---|---|---|---|---|---|---|---|---|
| E  Basis (Donchian 100, Trail 5) | +0.25 | -0.34 | +0.03 | +0.24 | -0.25 | +0.47 | +0.88 | +0.37 |
| V1 Regime: Tages-ADX >= 20 | +0.26 | -0.36 | +0.04 | +0.08 | -0.26 | +0.50 | +1.03 | +0.36 |
| V2 Regime: Tages-ADX >= 25 | +0.29 | -0.34 | -0.21 | +0.06 | -0.23 | +0.66 | +1.22 | +0.56 |
| V3 Regime: kein 'Chaos' (Vol-Perzentil >= 70 % und ADX < 25) | +0.27 | -0.34 | +0.06 | +0.26 | -0.25 | +0.47 | +0.88 | +0.37 |
| V4 Regime: Hurst (100 Tage Rendite) > 0,55 | +0.25 | -0.36 | +0.04 | +0.28 | -0.31 | +0.34 | +0.80 | +0.37 |
| V5 Zeitstopp 30 Kerzen (5 Tage), nur wenn im Minus | +0.21 | -0.29 | +0.03 | +0.23 | -0.20 | +0.51 | +0.56 | +0.36 |
| V6 Zeitstopp 60 Kerzen (10 Tage), nur wenn im Minus | +0.25 | -0.34 | +0.03 | +0.24 | -0.24 | +0.47 | +0.82 | +0.37 |
| V7 Gestaffelt: 25 % bei 2 R (Rest-Stop Einstand), 25 % bei 4 R | +0.26 | -0.31 | +0.05 | +0.24 | -0.25 | +0.46 | +0.86 | +0.23 |

## Einsatz-Regeln auf E (142 Trades, 8 Coins, ab 2024-11-06, Konto 1.000 $)

| Regel | Endkonto | pro Jahr | größter Rückgang | Trades (übersprungen) |
|---|---|---|---|---|
| fix 4 % (bisher) | 2,143 $ | +47 % | 30 % | 112 (30) |
| fix 2 % | 1,591 $ | +26 % | 16 % | 112 (30) |
| fix 1 % | 1,292 $ | +14 % | 8 % | 112 (30) |
| Kelly 1/4 (laufend aus abgeschlossenen Trades, 0,5 bis 4 %) | 1,527 $ | +24 % | 27 % | 112 (30) |
| Kelly 1/2 (laufend, 0,5 bis 4 %) | 1,961 $ | +40 % | 30 % | 112 (30) |
| fix 4 %, aber insgesamt höchstens 8 % offenes Risiko | 1,972 $ | +41 % | 18 % | 71 (71) |
| fix 4 %, höchstens 6 % offenes Risiko | 1,649 $ | +29 % | 17 % | 71 (71) |
| fix 2 %, höchstens 6 % offenes Risiko | 1,506 $ | +23 % | 12 % | 93 (49) |

E-Trades dieser Simulation: Ø R +0.247, Streuung 1.39 R, Trefferquote 42 %. Kelly (μ/σ²) wäre voll 12.7 % Risiko je Trade, 1/4 davon 3.2 %, 1/2 davon 6.3 %. Das Plugin empfiehlt bei weniger als 100 Trades höchstens 1/10 bis 1/4 Kelly.
