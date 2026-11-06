# SOL: Backtest-Tabellen

Beste 10 Sätze nach min(Training, Validierung), mit Test:

| Ebene | Ereignisse | Schwelle | Gew. | Puffer | Stop | Ausstieg | Training | Validierung | Test |
|---|---|---|---|---|---|---|---|---|---|
| 1h | rejection | 6 | 1.5 | 0.25 | bar | trail | +0.45R n=45 | +0.15R n=28 | +0.10R n=33 |
| 1h | rejection | 6 | 1.5 | 0.75 | bar | trail | +0.37R n=44 | +0.14R n=24 | +0.01R n=31 |
| 4h | all | 3 | 3 | 0.75 | swing | trail | +0.17R n=135 | +0.13R n=68 | +0.04R n=74 |
| 4h | all | 3 | 3 | 0.25 | swing | trail | +0.35R n=132 | +0.11R n=66 | -0.03R n=70 |
| 1h | all | 6 | 1.5 | 0.75 | swing | trail | +0.08R n=69 | +0.19R n=30 | -0.24R n=38 |
| 4h | all | 3 | 3 | 0.25 | bar | trail | +0.06R n=158 | +0.33R n=80 | +0.07R n=88 |
| 1h | all | 6 | 1.5 | 0.75 | bar | trail | +0.06R n=71 | +0.08R n=31 | -0.07R n=38 |
| 1h | all | 4.5 | 1.5 | 0.75 | swing | trail | +0.04R n=111 | +0.20R n=49 | +0.02R n=49 |
| 1h | structure | 6 | 1.5 | 0.25 | bar | flip | +0.04R n=21 | +0.22R n=8 | -0.25R n=18 |
| 4h | all | 3 | 3 | 0.25 | bar | flip | +0.03R n=213 | +0.11R n=102 | +0.25R n=107 |
