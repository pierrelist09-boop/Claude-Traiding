# coins/: Ergebnis je Coin

Stand 2026-11-06 22:58. Chart-Strategie (STRATEGY.md) einzeln je Coin optimiert, Training 50 % / Validierung 25 % / Test 25 % (ungesehen). R = Abstand Einstieg bis Stop, nach Kosten.

| Coin | Empfehlung | bestanden | Robustheit | gewählt | Test | gemeinsamer Satz (Test) |
|---|---|---|---|---|---|---|
| [BTC](./BTC/README.md) | nur beobachten | 41/576 | 34 % | 1h all flip | -0.40 R (n=21) | -0.45 R (n=4) |
| [ETH](./ETH/README.md) | nur beobachten | 16/576 | 0 % | 4h reversal flip | -0.41 R (n=36) | -0.43 R (n=11) |
| [SOL](./SOL/README.md) | Paper-Test (klein) | 20/576 | 50 % | 1h rejection trail | +0.10 R (n=33) | -0.04 R (n=16) |
| [XRP](./XRP/README.md) | nur beobachten | 108/576 | 50 % | 4h structure trail | -0.31 R (n=26) | -1.42 R (n=2) |
| [DOGE](./DOGE/README.md) | nur beobachten | 19/576 | 37 % | 4h reversal trail | +1.01 R (n=30) | +0.16 R (n=5) |
| [LINK](./LINK/README.md) | Paper-Test (klein) | 118/576 | 62 % | 4h all trail | +0.13 R (n=23) | -0.32 R (n=4) |
| [AVAX](./AVAX/README.md) | nur beobachten | 29/576 | 17 % | 4h reversal trail | -0.31 R (n=20) | -0.29 R (n=11) |
| [HYPE](./HYPE/README.md) | Paper-Test (klein) | 95/576 | 61 % | 1h structure trail | +0.21 R (n=20) | -0.17 R (n=12) |

**Gesamt über alle Coins im ungesehenen Test (gewählte Sätze):** 209 Trades, Ø +0.016 R je Trade, 4 von 8 Coins im Plus. Ein Durchschnitt nahe null heißt: Die Einzeloptimierung findet im Test keinen verlässlichen Vorteil, die Auswahl aus vielen Sätzen erzeugt Rauschen.
**Achtung:** Der Test wurde jetzt gesehen. Weiteres Feintuning auf denselben Daten verfälscht ihn. Neue Bestätigung nur mit dem Forward-Journal (neue, ungesehene Daten).

Gemeinsamer Satz (für alle Coins gleich, gewählt auf Training+Validierung gepoolt): `1h {"T": 6.0, "ev_set": "reversal", "ev_w": 1.5, "exit": "flip", "k": 0.25, "stop_ref": "swing"}`

Lesehilfe: 'Robustheit' ist der Anteil der Sätze, die Training und Validierung bestehen und im Test positiv bleiben. Liegt er unter 50 %, ist die Auswahl größtenteils Glück.
