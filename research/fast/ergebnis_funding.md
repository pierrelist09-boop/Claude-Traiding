# Ergebnis Funding, Überhitzung und Gegenbewegung (Mean Reversion)

Skript: `research/fast/funding.py`. Alle Zahlen stammen aus dem tatsächlichen Lauf (`--phase final`), nichts geschätzt.

## Kurzfassung

| Lauf | Gewählte Variante (Training) | Train n / Ø R | Val n / Ø R | Test n / Ø R | Test PF | Coins im Plus | Urteil |
|---|---|---|---|---|---|---|---|
| K1 Docht-Kapitulation 1h | Range>=2.0ATR Vol>=2.0x Ziel=1.5ATR | 89 / -0.095 | 67 / -0.244 | 51 / 0.100 | 1.32 | 5/8 | **no_edge** |
| K1 Docht-Kapitulation 4h | Range>=2.0ATR Vol>=2.5x Ziel=1.5ATR | 81 / -0.132 | 37 / 0.179 | 40 / -0.449 | 0.28 | 1/8 | **no_edge** |
| K2 Überdehnung RSI3/EMA50 4h | D>=3.5ATR Trendfilter=Trend Ziel=EMA20 | 38 / 0.630 | 23 / -0.787 | 17 / 0.815 | 1.97 | 4/8 | **no_edge** |
| K2 Überdehnung RSI3/EMA50 1h | D>=3.5ATR Trendfilter=kein Ziel=EMA20 | 237 / 0.271 | 131 / -0.664 | 136 / -0.391 | 0.62 | 0/8 | **no_edge** |
| K3 Premium-Crowding 1h | |z|>=2.0 Preisweg>=2.0ATR Gate=Q75 | 31 / 0.441 | 47 / -0.446 | 29 / -0.466 | 0.38 | 2/10 | **no_edge** |

Ø R ist der mittlere Gewinn je Trade in R (1 R = Abstand Einstieg zu Stop), netto nach Gebühr, Slippage und Funding. Vorteil-Kandidat nur, wenn Test-Ø-R > 0 UND Validierung > 0 UND mindestens 30 Test-Trades UND mindestens die Hälfte der Coins im Test im Plus.

## Methode und Ehrlichkeit

- Aufteilung je Coin chronologisch: erste 50 % der Kerzen Training, nächste 25 % Validierung, letzte 25 % Test. Trades gehören zur Periode ihrer Einstiegskerze.
- Auswahl der Variante nur im Training: höchster Ø R unter Varianten mit mindestens 30 Training-Trades. Validierung bestätigt, Test genau einmal für die gewählte Variante.
- **Getestete Varianten insgesamt: 40** (5 Läufe zu je 8 Varianten: K1 1h, K1 4h, K2 4h, K2 1h, K3 1h). Je Lauf wird genau eine im Training gewählt. Außerhalb des Gitters wurde nichts probiert (Fehlersuche nur mit Trainings-/Validierungsdaten).
- Kosten je Seite: Gebühr 0,045 % plus Slippage nach Coin (BTC, ETH, BNB 0,02 %; SOL, XRP, DOGE, LINK, AVAX, DOT 0,03 %; ADA, NEAR, HYPE 0,04 %). Beim Stop-Ausstieg doppelte Slippage. Alle Ausstiege (auch Ziel) mit Slippage, also pessimistisch.
- Funding: K1 und K2 mit Normalsatz 1,25e-5 je Stunde (Long zahlt, Short erhält); K3 mit dem echten stündlichen fundingRate aus fundingHistory.
- Einstieg frühestens zum Eröffnungskurs der Folgekerze; Stop und Ziel in derselben Kerze: Stop zuerst; Eröffnung jenseits des Stops: Ausstieg zum Eröffnungskurs.
- Portfolio-Rechnung: fest 2 % des Kontos Risiko je Trade (R-basiert, Konto wächst mit realisierten Ergebnissen), Trades chronologisch über alle Coins, höchstens 4 gleichzeitig (weitere werden übersprungen).
- Bootstrap nach Einstiegstagen (4000 Ziehungen, 90-%-Intervall), weil Signale marktweit gebündelt auftreten.

## K1 Docht-Kapitulation - 1h

Regeln: Signalkerze mit Spanne >= Rmult x ATR14 (bis i-1), Volumen >= Vmult x Mittel der 48 Vorkerzen, Docht >= 50 % der Spanne, neues 24-Kerzen-Extrem; Gegenrichtung zum Docht; Einstieg Eröffnung i+1; Stop hinter Dochtende + 0,25 ATR (Risiko > 3 ATR wird übersprungen); Ziel Einstieg +/- Kmult x ATR; Zeitstopp 12 Kerzen; eine Position je Coin. Gitter: Rmult {1,5; 2,0} x Vmult {2,0; 2,5} x Kmult {1,5; 2,5}.

Coins (8): BTC, ETH, SOL, XRP, DOGE, DOT, LINK, AVAX. Varianten in diesem Lauf: 8. Auswahl: höchster Training-Ø-R unter Varianten mit >= 30 Training-Trades.

Zeiträume (Beispiel BTC): Training 2026-04-12 bis 2026-07-25, Validierung 2026-07-25 bis 2026-09-15, Test 2026-09-15 bis 2026-11-06.

### Alle Varianten (Training und Validierung)

| Variante | Train n | Train Ø R | Train PF | Val n | Val Ø R | Val PF | |
|---|---|---|---|---|---|---|---|
| Range>=1.5ATR Vol>=2.0x Ziel=1.5ATR | 156 | -0.160 | 0.68 | 121 | -0.153 | 0.69 |  |
| Range>=1.5ATR Vol>=2.0x Ziel=2.5ATR | 156 | -0.203 | 0.66 | 121 | -0.058 | 0.89 |  |
| Range>=1.5ATR Vol>=2.5x Ziel=1.5ATR | 117 | -0.183 | 0.65 | 98 | -0.143 | 0.70 |  |
| Range>=1.5ATR Vol>=2.5x Ziel=2.5ATR | 117 | -0.292 | 0.53 | 98 | -0.060 | 0.88 |  |
| Range>=2.0ATR Vol>=2.0x Ziel=1.5ATR | 89 | -0.095 | 0.78 | 67 | -0.244 | 0.53 | gewählt |
| Range>=2.0ATR Vol>=2.0x Ziel=2.5ATR | 89 | -0.099 | 0.79 | 67 | -0.210 | 0.63 |  |
| Range>=2.0ATR Vol>=2.5x Ziel=1.5ATR | 70 | -0.129 | 0.71 | 63 | -0.260 | 0.51 |  |
| Range>=2.0ATR Vol>=2.5x Ziel=2.5ATR | 70 | -0.161 | 0.67 | 63 | -0.236 | 0.59 |  |

### Gewählte Variante: Range>=2.0ATR Vol>=2.0x Ziel=1.5ATR

| Periode | Trades | Ø R netto | Ø R brutto | Trefferquote | Profit-Faktor |
|---|---|---|---|---|---|
| Training | 89 | -0.095 | 0.018 | 0.55 | 0.78 |
| Validierung | 67 | -0.244 | -0.093 | 0.51 | 0.53 |
| Test | 51 | 0.100 | 0.195 | 0.67 | 1.32 |

### Je Coin (gewählte Variante)

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| BTC | 8 | 0.022 | 12 | -0.191 | 4 | 0.345 |
| ETH | 16 | -0.119 | 13 | -0.012 | 4 | -0.185 |
| SOL | 13 | -0.057 | 8 | 0.130 | 8 | 0.210 |
| XRP | 7 | -0.409 | 7 | -0.290 | 5 | 0.342 |
| DOGE | 13 | -0.056 | 6 | -0.874 | 7 | 0.256 |
| DOT | 8 | -0.078 | 5 | -0.469 | 8 | -0.005 |
| LINK | 11 | -0.046 | 8 | -0.496 | 7 | -0.575 |
| AVAX | 13 | -0.098 | 8 | -0.171 | 8 | 0.418 |

Test-Ausstiegsarten: {'ziel': 31, 'zeit': 6, 'stop': 14}; mittlere Haltedauer 5.7 Kerzen.

### Test-Portfolio bei 2 % Risiko je Trade

- Rendite im Test: **4.93 %**, größter Rückgang: 14.54 %, bester Tag: 5.91 %, schlechtester Tag: -4.41 %.
- Gehandelte Trades: 48, wegen Limit von 4 gleichzeitigen übersprungen: 3.
- Diagnose (nachträglich, ohne Parameteränderung): bester Einstiegstag 2026-10-24 trägt 4.34 R; ohne diesen Tag bleiben 45 Test-Trades mit Ø R 0.017.
- Bootstrap nach Tagen (Test, 25 Handelstage mit Einstieg): Ø R 90-%-Intervall -0.168 bis 0.326.
- Urteil: **no_edge** (Coins im Plus 5 von 8; ein Coin ohne Trades zählt nicht als Plus).

## K1 Docht-Kapitulation - 4h

Regeln: Wie K1 1h, aber auf 4h-Kerzen (eigener Lauf, getrennt gemeldet).

Coins (8): BTC, ETH, SOL, XRP, DOGE, DOT, LINK, AVAX. Varianten in diesem Lauf: 8. Auswahl: höchster Training-Ø-R unter Varianten mit >= 30 Training-Trades.

Zeiträume (Beispiel BTC): Training 2024-07-26 bis 2025-09-16, Validierung 2025-09-16 bis 2026-04-12, Test 2026-04-12 bis 2026-11-06.

### Alle Varianten (Training und Validierung)

| Variante | Train n | Train Ø R | Train PF | Val n | Val Ø R | Val PF | |
|---|---|---|---|---|---|---|---|
| Range>=1.5ATR Vol>=2.0x Ziel=1.5ATR | 180 | -0.247 | 0.57 | 73 | -0.069 | 0.83 |  |
| Range>=1.5ATR Vol>=2.0x Ziel=2.5ATR | 180 | -0.239 | 0.62 | 73 | -0.086 | 0.80 |  |
| Range>=1.5ATR Vol>=2.5x Ziel=1.5ATR | 138 | -0.195 | 0.64 | 53 | 0.030 | 1.08 |  |
| Range>=1.5ATR Vol>=2.5x Ziel=2.5ATR | 138 | -0.179 | 0.70 | 53 | -0.044 | 0.89 |  |
| Range>=2.0ATR Vol>=2.0x Ziel=1.5ATR | 95 | -0.186 | 0.64 | 43 | 0.152 | 1.57 |  |
| Range>=2.0ATR Vol>=2.0x Ziel=2.5ATR | 95 | -0.187 | 0.68 | 43 | 0.205 | 1.71 |  |
| Range>=2.0ATR Vol>=2.5x Ziel=1.5ATR | 81 | -0.132 | 0.72 | 37 | 0.179 | 1.70 | gewählt |
| Range>=2.0ATR Vol>=2.5x Ziel=2.5ATR | 81 | -0.133 | 0.76 | 37 | 0.205 | 1.74 |  |

### Gewählte Variante: Range>=2.0ATR Vol>=2.5x Ziel=1.5ATR

| Periode | Trades | Ø R netto | Ø R brutto | Trefferquote | Profit-Faktor |
|---|---|---|---|---|---|
| Training | 81 | -0.132 | -0.097 | 0.52 | 0.72 |
| Validierung | 37 | 0.179 | 0.213 | 0.70 | 1.70 |
| Test | 40 | -0.449 | -0.403 | 0.30 | 0.28 |

### Je Coin (gewählte Variante)

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| BTC | 9 | -0.037 | 4 | -0.847 | 6 | -0.286 |
| ETH | 8 | -0.368 | 5 | 0.318 | 3 | 0.240 |
| SOL | 10 | -0.053 | 5 | 0.619 | 4 | -0.857 |
| XRP | 13 | -0.363 | 4 | 0.231 | 3 | -1.032 |
| DOGE | 14 | -0.306 | 4 | 0.216 | 9 | -0.079 |
| DOT | 12 | 0.085 | 5 | 0.460 | 9 | -0.645 |
| LINK | 11 | 0.006 | 6 | 0.299 | 2 | -1.039 |
| AVAX | 4 | 0.252 | 4 | -0.137 | 4 | -0.463 |

Test-Ausstiegsarten: {'ziel': 9, 'zeit': 8, 'stop': 23}; mittlere Haltedauer 6.2 Kerzen.

### Test-Portfolio bei 2 % Risiko je Trade

- Rendite im Test: **-25.14 %**, größter Rückgang: 26.85 %, bester Tag: 2.44 %, schlechtester Tag: -14.03 %.
- Gehandelte Trades: 36, wegen Limit von 4 gleichzeitigen übersprungen: 4.
- Diagnose (nachträglich, ohne Parameteränderung): bester Einstiegstag 2026-09-15 trägt 1.22 R; ohne diesen Tag bleiben 37 Test-Trades mit Ø R -0.519.
- Bootstrap nach Tagen (Test, 22 Handelstage mit Einstieg): Ø R 90-%-Intervall -0.685 bis -0.133.
- Urteil: **no_edge** (Coins im Plus 1 von 8; ein Coin ohne Trades zählt nicht als Plus).

## K2 Überdehnung RSI3/EMA50 - 4h

Regeln: Long: (Schluss - EMA50)/ATR <= -D und RSI(3) <= 10; Short spiegelbildlich (>= +D, RSI >= 90). Trendfilter 'Trend': Long nur bei steigender EMA200 (EMA200_i > EMA200_i-12), Short nur bei fallender. Einstieg Eröffnung i+1; Stop = Extrem der letzten 6 Kerzen -/+ 0,25 ATR (Risiko > 3 ATR übersprungen); Ausstieg zum Eröffnungskurs der Folgekerze, sobald der Schluss das Zielmittel (EMA20 oder EMA50) erreicht; Zeitstopp 12 Kerzen (4h) bzw. 24 (1h); 6 Kerzen Sperre je Coin und Richtung nach Ausstieg. Gitter: D {2,5; 3,5} x Trendfilter {kein; Trend} x Ziel {EMA20; EMA50}.

Coins (8): BTC, ETH, BNB, XRP, DOGE, LINK, AVAX, DOT. Varianten in diesem Lauf: 8. Auswahl: höchster Training-Ø-R unter Varianten mit >= 30 Training-Trades.

Zeiträume (Beispiel BTC): Training 2024-07-26 bis 2025-09-16, Validierung 2025-09-16 bis 2026-04-12, Test 2026-04-12 bis 2026-11-06.

### Alle Varianten (Training und Validierung)

| Variante | Train n | Train Ø R | Train PF | Val n | Val Ø R | Val PF | |
|---|---|---|---|---|---|---|---|
| D>=2.5ATR Trendfilter=kein Ziel=EMA20 | 456 | -0.100 | 0.89 | 252 | -0.578 | 0.41 |  |
| D>=2.5ATR Trendfilter=kein Ziel=EMA50 | 453 | -0.180 | 0.80 | 250 | -0.601 | 0.40 |  |
| D>=2.5ATR Trendfilter=Trend Ziel=EMA20 | 107 | 0.134 | 1.15 | 66 | -0.586 | 0.40 |  |
| D>=2.5ATR Trendfilter=Trend Ziel=EMA50 | 106 | 0.051 | 1.06 | 66 | -0.553 | 0.44 |  |
| D>=3.5ATR Trendfilter=kein Ziel=EMA20 | 266 | -0.223 | 0.75 | 145 | -0.230 | 0.74 |  |
| D>=3.5ATR Trendfilter=kein Ziel=EMA50 | 266 | -0.199 | 0.78 | 145 | -0.224 | 0.75 |  |
| D>=3.5ATR Trendfilter=Trend Ziel=EMA20 | 38 | 0.630 | 1.79 | 23 | -0.787 | 0.25 | gewählt |
| D>=3.5ATR Trendfilter=Trend Ziel=EMA50 | 38 | 0.597 | 1.74 | 23 | -0.784 | 0.26 |  |

### Gewählte Variante: D>=3.5ATR Trendfilter=Trend Ziel=EMA20

| Periode | Trades | Ø R netto | Ø R brutto | Trefferquote | Profit-Faktor |
|---|---|---|---|---|---|
| Training | 38 | 0.630 | 0.773 | 0.29 | 1.79 |
| Validierung | 23 | -0.787 | -0.617 | 0.09 | 0.25 |
| Test | 17 | 0.815 | 1.012 | 0.29 | 1.97 |

### Je Coin (gewählte Variante)

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| BTC | 4 | 1.815 | 2 | -1.153 | 2 | 4.869 |
| ETH | 5 | 0.199 | 4 | -1.089 | 3 | 1.248 |
| BNB | 2 | -1.232 | 1 | -1.358 | 1 | -1.324 |
| XRP | 7 | 3.089 | 4 | -1.181 | 5 | -0.551 |
| DOGE | 7 | -0.650 | 2 | -1.120 | 1 | -1.091 |
| LINK | 3 | 3.436 | 3 | -1.161 | 2 | 1.917 |
| AVAX | 5 | -0.672 | 3 | 1.054 | 0 | - |
| DOT | 5 | -1.173 | 4 | -0.701 | 3 | 0.567 |

Test-Ausstiegsarten: {'mittel': 3, 'stop': 12, 'zeit': 2}; mittlere Haltedauer 4.0 Kerzen.

### Test-Portfolio bei 2 % Risiko je Trade

- Rendite im Test: **21.81 %**, größter Rückgang: 21.64 %, bester Tag: 44.13 %, schlechtester Tag: -9.73 %.
- Gehandelte Trades: 17, wegen Limit von 4 gleichzeitigen übersprungen: 0.
- Diagnose (nachträglich, ohne Parameteränderung): bester Einstiegstag 2026-06-15 trägt 20.78 R; ohne diesen Tag bleiben 13 Test-Trades mit Ø R -0.533.
- Bootstrap nach Tagen (Test, 9 Handelstage mit Einstieg): Ø R 90-%-Intervall -0.844 bis 2.531.
- Urteil: **no_edge** (Coins im Plus 4 von 8; ein Coin ohne Trades zählt nicht als Plus).

## K2 Überdehnung RSI3/EMA50 - 1h

Regeln: Wie K2 4h, aber auf 1h-Kerzen (eigener Lauf, getrennt gemeldet).

Coins (8): BTC, ETH, BNB, XRP, DOGE, LINK, AVAX, DOT. Varianten in diesem Lauf: 8. Auswahl: höchster Training-Ø-R unter Varianten mit >= 30 Training-Trades.

Zeiträume (Beispiel BTC): Training 2026-04-12 bis 2026-07-25, Validierung 2026-07-25 bis 2026-09-15, Test 2026-09-15 bis 2026-11-06.

### Alle Varianten (Training und Validierung)

| Variante | Train n | Train Ø R | Train PF | Val n | Val Ø R | Val PF | |
|---|---|---|---|---|---|---|---|
| D>=2.5ATR Trendfilter=kein Ziel=EMA20 | 398 | -0.023 | 0.98 | 227 | -0.500 | 0.54 |  |
| D>=2.5ATR Trendfilter=kein Ziel=EMA50 | 391 | 0.023 | 1.02 | 220 | -0.466 | 0.59 |  |
| D>=2.5ATR Trendfilter=Trend Ziel=EMA20 | 91 | -0.247 | 0.78 | 62 | -0.571 | 0.48 |  |
| D>=2.5ATR Trendfilter=Trend Ziel=EMA50 | 91 | -0.134 | 0.88 | 61 | -0.581 | 0.50 |  |
| D>=3.5ATR Trendfilter=kein Ziel=EMA20 | 237 | 0.271 | 1.31 | 131 | -0.664 | 0.41 | gewählt |
| D>=3.5ATR Trendfilter=kein Ziel=EMA50 | 232 | 0.238 | 1.25 | 127 | -0.609 | 0.47 |  |
| D>=3.5ATR Trendfilter=Trend Ziel=EMA20 | 22 | 0.164 | 1.17 | 18 | -0.908 | 0.20 |  |
| D>=3.5ATR Trendfilter=Trend Ziel=EMA50 | 22 | 0.746 | 1.75 | 18 | -1.072 | 0.13 |  |

### Gewählte Variante: D>=3.5ATR Trendfilter=kein Ziel=EMA20

| Periode | Trades | Ø R netto | Ø R brutto | Trefferquote | Profit-Faktor |
|---|---|---|---|---|---|
| Training | 237 | 0.271 | 0.629 | 0.34 | 1.31 |
| Validierung | 131 | -0.664 | -0.266 | 0.18 | 0.41 |
| Test | 136 | -0.391 | -0.074 | 0.21 | 0.62 |

### Je Coin (gewählte Variante)

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| BTC | 36 | 0.051 | 15 | -0.716 | 15 | -0.381 |
| ETH | 31 | 0.537 | 13 | -0.579 | 18 | -0.118 |
| BNB | 29 | 0.578 | 17 | -1.161 | 16 | -0.417 |
| XRP | 31 | -0.495 | 17 | -1.233 | 18 | -0.513 |
| DOGE | 26 | 0.616 | 14 | -0.301 | 18 | -0.391 |
| LINK | 30 | 0.380 | 19 | -0.644 | 21 | -0.212 |
| AVAX | 22 | -0.283 | 16 | -0.010 | 15 | -0.470 |
| DOT | 32 | 0.719 | 20 | -0.567 | 15 | -0.724 |

Test-Ausstiegsarten: {'stop': 107, 'mittel': 28, 'zeit': 1}; mittlere Haltedauer 5.1 Kerzen.

### Test-Portfolio bei 2 % Risiko je Trade

- Rendite im Test: **-76.44 %**, größter Rückgang: 78.60 %, bester Tag: 36.27 %, schlechtester Tag: -25.36 %.
- Gehandelte Trades: 127, wegen Limit von 4 gleichzeitigen übersprungen: 9.
- Diagnose (nachträglich, ohne Parameteränderung): bester Einstiegstag 2026-10-18 trägt 29.79 R; ohne diesen Tag bleiben 129 Test-Trades mit Ø R -0.643.
- Bootstrap nach Tagen (Test, 40 Handelstage mit Einstieg): Ø R 90-%-Intervall -0.834 bis 0.159.
- Urteil: **no_edge** (Coins im Plus 0 von 8; ein Coin ohne Trades zählt nicht als Plus).

## K3 Premium-Crowding - 1h

Regeln: Premium aus fundingHistory: z = (Mittel der letzten 6 Premium-Werte - Mittel der letzten 168) / Std. der letzten 168, nur Einträge bis zur Eröffnungszeit der Signalkerze. Long: z <= -Z und Schluss(i) - Schluss(i-24) <= -E x ATR14 und Schluss > Eröffnung; Short spiegelbildlich. Gate 'Q75': ATR/Kurs im oberen Quartil der letzten 720 Kerzen. Einstieg Eröffnung i+1; Stop = Extrem der letzten 12 Kerzen -/+ 0,25 ATR (Risiko > 3 ATR übersprungen); Ziel +/- 3 ATR; Ausstieg zum Eröffnungskurs, sobald z auf -0,5 bzw. +0,5 zurück ist; Zeitstopp 24 Kerzen; echtes stündliches fundingRate verbucht. Gitter: Z {1,5; 2,0} x E {1,0; 2,0} x Gate {kein; Q75}.

Coins (10): BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, NEAR, HYPE. Varianten in diesem Lauf: 8. Auswahl: höchster Training-Ø-R unter Varianten mit >= 30 Training-Trades.

Zeiträume (Beispiel BTC): Training 2026-04-12 bis 2026-07-25, Validierung 2026-07-25 bis 2026-09-15, Test 2026-09-15 bis 2026-11-06.

### Alle Varianten (Training und Validierung)

| Variante | Train n | Train Ø R | Train PF | Val n | Val Ø R | Val PF | |
|---|---|---|---|---|---|---|---|
| |z|>=1.5 Preisweg>=1.0ATR Gate=kein | 308 | -0.066 | 0.90 | 168 | -0.316 | 0.57 |  |
| |z|>=1.5 Preisweg>=1.0ATR Gate=Q75 | 82 | -0.046 | 0.92 | 79 | -0.355 | 0.54 |  |
| |z|>=1.5 Preisweg>=2.0ATR Gate=kein | 261 | -0.080 | 0.88 | 148 | -0.273 | 0.62 |  |
| |z|>=1.5 Preisweg>=2.0ATR Gate=Q75 | 72 | 0.025 | 1.05 | 74 | -0.354 | 0.54 |  |
| |z|>=2.0 Preisweg>=1.0ATR Gate=kein | 125 | -0.086 | 0.86 | 76 | -0.365 | 0.51 |  |
| |z|>=2.0 Preisweg>=1.0ATR Gate=Q75 | 36 | 0.372 | 2.10 | 48 | -0.420 | 0.46 |  |
| |z|>=2.0 Preisweg>=2.0ATR Gate=kein | 111 | -0.121 | 0.81 | 71 | -0.377 | 0.49 |  |
| |z|>=2.0 Preisweg>=2.0ATR Gate=Q75 | 31 | 0.441 | 2.34 | 47 | -0.446 | 0.44 | gewählt |

### Gewählte Variante: |z|>=2.0 Preisweg>=2.0ATR Gate=Q75

| Periode | Trades | Ø R netto | Ø R brutto | Trefferquote | Profit-Faktor |
|---|---|---|---|---|---|
| Training | 31 | 0.441 | 0.529 | 0.61 | 2.34 |
| Validierung | 47 | -0.446 | -0.371 | 0.26 | 0.44 |
| Test | 29 | -0.466 | -0.394 | 0.24 | 0.38 |

### Je Coin (gewählte Variante)

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| BTC | 0 | - | 1 | 0.410 | 0 | - |
| ETH | 0 | - | 4 | -0.297 | 3 | -0.534 |
| SOL | 4 | 0.406 | 6 | -1.082 | 1 | -1.110 |
| XRP | 4 | 0.490 | 4 | 0.027 | 2 | -1.058 |
| DOGE | 5 | 0.664 | 8 | 0.437 | 5 | -1.063 |
| ADA | 4 | 1.113 | 6 | -0.393 | 4 | -0.768 |
| AVAX | 1 | 0.400 | 6 | -0.691 | 4 | -0.324 |
| LINK | 5 | 1.552 | 5 | -0.695 | 2 | 1.517 |
| NEAR | 7 | -0.892 | 6 | -1.044 | 4 | -0.908 |
| HYPE | 1 | 0.400 | 1 | -1.033 | 4 | 0.400 |

Test-Ausstiegsarten: {'stop': 20, 'mittel': 4, 'zeit': 3, 'ziel': 2}; mittlere Haltedauer 8.1 Kerzen.

### Test-Portfolio bei 2 % Risiko je Trade

- Rendite im Test: **-21.56 %**, größter Rückgang: 33.06 %, bester Tag: 8.22 %, schlechtester Tag: -14.31 %.
- Gehandelte Trades: 27, wegen Limit von 4 gleichzeitigen übersprungen: 2.
- Diagnose (nachträglich, ohne Parameteränderung): bester Einstiegstag 2026-11-05 trägt 4.11 R; ohne diesen Tag bleiben 28 Test-Trades mit Ø R -0.629.
- Bootstrap nach Tagen (Test, 12 Handelstage mit Einstieg): Ø R 90-%-Intervall -0.807 bis 0.252.
- Urteil: **no_edge** (Coins im Plus 2 von 10; ein Coin ohne Trades zählt nicht als Plus).

## Carry-Referenz (nur Rechnung, kein Handel)

Annahme: dauerhaft Short-Perp halten und den Funding-Satz einsammeln (marktneutral wäre eine Spot-Gegenseite nötig, die das Perp-Paper-Konto nicht hat; der Preisrisiko-Anteil ist hier NICHT enthalten). Rechnung: Summe des echten stündlichen fundingRate im Testzeitraum abzüglich Roundtrip-Kosten (2 x (Gebühr + Slippage)), in Prozent des Einsatzes.

| Coin | Test-Tage | Funding-Summe % | Kosten % | Netto % | Netto % je Tag | USD je Tag bei 1000 USD |
|---|---|---|---|---|---|---|
| BTC | 52.1 | 1.321 | 0.130 | 1.191 | 0.0229 | 0.229 |
| ETH | 52.1 | 1.205 | 0.130 | 1.075 | 0.0206 | 0.206 |
| SOL | 52.1 | 1.129 | 0.150 | 0.979 | 0.0188 | 0.188 |
| XRP | 52.1 | 1.500 | 0.150 | 1.350 | 0.0259 | 0.259 |
| DOGE | 52.1 | 1.578 | 0.150 | 1.428 | 0.0274 | 0.274 |
| ADA | 52.1 | -0.051 | 0.170 | -0.221 | -0.0042 | -0.042 |
| AVAX | 52.1 | 0.994 | 0.150 | 0.844 | 0.0162 | 0.162 |
| LINK | 52.1 | 1.325 | 0.150 | 1.175 | 0.0226 | 0.226 |
| NEAR | 52.1 | 1.987 | 0.170 | 1.817 | 0.0349 | 0.349 |
| HYPE | 52.1 | 1.659 | 0.170 | 1.489 | 0.0286 | 0.286 |

Mittel über 10 Coins: netto 1.113 % im Testfenster, 0.0214 % je Tag. Das ist weit entfernt von 'schnell viel Geld'.

## Vorbehalte

- Nur ein Marktregime je Zeitrahmen: das 1h-Testfenster (ab ca. Mitte September 2026, rund 52 Tage) enthält keinen großen Crash; die 4h-Validierung enthält den Flush vom 10.10.2025, der 4h-Test beginnt ca. April 2026.
- Signale sind marktweit gebündelt (ein Panik-Tag erzeugt Trades in allen Coins); die Zahl unabhängiger Ereignisse ist kleiner als die Tradezahl (siehe Bootstrap nach Tagen).
- Hyperliquid-Volumen ist nur das Volumen dieser Börse; echte Liquidationsdaten fehlen, Docht plus Volumen ist ein Stellvertreter.
- Mehrfachtest: 40 Varianten insgesamt; die Auswahl je Lauf erfolgte nur im Training, trotzdem bleibt ein Rest-Zufallsrisiko bei kleinen Stichproben.
- Premium-Nutzung (K3) ist eine eigene Ableitung aus Doku-Formel und Stichproben; fehlende Funding-Stunden wurden mit dem letzten Wert fortgeschrieben (Anzahl je Coin in ergebnis_funding.json).
- Kosten pessimistisch (Slippage auch auf Zielausstiegen, doppelt auf Stops); reale Limit-Ziele wären etwas günstiger, reale Kaskaden-Stops eher schlechter.
- Ø R ist nicht gleich Konto-Rendite: bei 2 % Risiko je Trade, höchstens 4 Positionen und wenigen Signalen ist die Kontoentwicklung klein (siehe Portfolio-Abschnitte).
