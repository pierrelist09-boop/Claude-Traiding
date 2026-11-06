# BTC: Backtest-Tabellen

Beste 10 Sätze nach min(Training, Validierung), mit Test:

| Ebene | Ereignisse | Schwelle | Gew. | Puffer | Stop | Ausstieg | Training | Validierung | Test |
|---|---|---|---|---|---|---|---|---|---|
| 1h | all | 6 | 1.5 | 0.75 | bar | flip | +0.41R n=72 | +0.48R n=32 | -0.40R n=21 |
| 1h | rejection | 6 | 1.5 | 0.75 | bar | flip | +0.40R n=56 | +0.38R n=24 | -0.50R n=18 |
| 4h | reversal | 3 | 3 | 0.25 | bar | trail | +0.38R n=140 | +0.71R n=52 | +0.27R n=70 |
| 4h | reversal | 3 | 3 | 0.25 | swing | trail | +0.35R n=117 | +1.03R n=44 | -0.16R n=60 |
| 1h | all | 6 | 1.5 | 0.25 | swing | flip | +0.73R n=72 | +0.34R n=30 | -0.41R n=23 |
| 1h | structure | 4.5 | 1.5 | 0.25 | swing | flip | +0.40R n=37 | +0.31R n=10 | +0.10R n=15 |
| 4h | all | 3 | 3 | 0.25 | swing | trail | +0.29R n=130 | +0.43R n=63 | +0.05R n=74 |
| 1h | rejection | 6 | 1.5 | 0.25 | swing | flip | +0.28R n=53 | +0.32R n=23 | -0.48R n=19 |
| 1h | structure | 4.5 | 1.5 | 0.25 | swing | trail | +0.43R n=29 | +0.25R n=8 | +0.25R n=13 |
| 1h | structure | 4.5 | 1.5 | 0.75 | swing | flip | +0.32R n=37 | +0.25R n=10 | +0.06R n=14 |
