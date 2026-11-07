# Ergebnis Volumen-Schub und Volatilitäts-Cluster (Blickwinkel Alts, 1h/4h)

Alle Zahlen stammen aus `research/fast/volumen.py` (nur Standardbibliothek, lokaler Cache, kein Netz). Ablauf: `selbsttest`, dann `dev` (Training und Validierung aller Varianten, Auswahl **nur nach Training**, gespeichert in `auswahl_volumen.json`), dann `test` (Test-Abschnitt **genau einmal**, Ergebnisse in `ergebnis_volumen.json`; das Skript bricht beim zweiten Lauf ab). Nach dem Test wurden weder Regeln noch Parameter geändert.

## Daten, Aufteilung, Kosten

- Aufteilung je Coin chronologisch nach Kerzenindex: erste 50 % Training, nächste 25 % Validierung, letzte 25 % Test. Jeder Abschnitt wird getrennt simuliert (Position startet flach; Rückblick-Indikatoren dürfen in die Zeit vor dem Abschnitt schauen, das ist kausal). Ein Trade zählt nur, wenn sein längster möglicher Zeitausstieg noch im Abschnitt liegt (hängt nur von der Lage der Signalkerze ab, nicht vom Ergebnis). Start 110 Kerzen nach Datenbeginn.
- Datenfenster 4h (BTC als Marktreferenz, Kursänderung im Abschnitt): Training 2024-07-26 bis 2025-09-16 (+71 %); Validierung 2025-09-16 bis 2026-04-12 (-38 %); Test 2026-04-12 bis 2026-11-06 (+6 %). HYPE hat nur 4209 4h-Kerzen, seine Abschnitte sind kürzer.
- Datenfenster 1h (BTC als Marktreferenz, Kursänderung im Abschnitt): Training 2026-04-12 bis 2026-07-25 (-9 %); Validierung 2026-07-25 bis 2026-09-15 (+18 %); Test 2026-09-15 bis 2026-11-06 (-0 %).
- Kosten je Seite: Gebühr 0,045 % + Slippage 0,03 % (ARB, UNI, DOT 0,05 %); Funding pauschal 0,00125 % je Stunde als Kosten (auch für Shorts, konservativ). Rundlauf damit rund 0,15 % (0,19 % bei ARB/UNI/DOT) plus Funding. Alle Kosten sind in R umgerechnet und vom Brutto-R abgezogen, ein Stop-Verlust ist also etwas größer als 1 R.
- Kein Blick in die Zukunft: Signal nur aus Kerzen bis einschließlich Signalkerze, Einstieg zum Open der Folgekerze (Slippage ungünstig), Stop und Trail in derselben Kerze: Stop zuerst, Gap über den Stop: Ausstieg zum Open, Trail-Nachführung erst ab der Folgekerze. Der Selbsttest (`python3 volumen.py selbsttest`) prüft das an synthetischen Kerzen, inklusive Kausalitätstest (Kerzen nach der Signalkerze zerstört, Signal bleibt gleich).
- Je Coin höchstens eine Position; neues Signal frühestens eine Kerze nach der Ausstiegskerze.
- Mehrfachtest-Lage: **24 Varianten** im Gitter (3 Kandidaten mal 8). Die Hypothesen selbst stammen aus einer Vorab-Suche mit rund 100 Auswertungsscheiben auf dem Trainingsteil (Recherche-Angabe). Auswahl je Kandidat: höchstes gepooltes Trainings-Ø R bei mindestens 30 Trainings-Trades; im Test wird je Kandidat genau eine Variante gerechnet (insgesamt 3 Testläufe).
- Kandidat-Regel: Test-Ø R nach Kosten > 0 UND Validierung > 0 UND mindestens 30 Test-Trades gesamt UND mindestens die Hälfte der Urteils-Coins im Test im Plus (Nenner: alle Urteils-Coins, Coins ohne Trade zählen nicht als Plus). Sonst `no_edge`; bei weniger als 30 Test-Trades `inconclusive`. Kontroll-Coins fließen nicht ins Urteil ein.
- Portfolio-Rechnung (nur Test, nur Urteils-Coins): 2 % des aktuellen Kontos Risiko je Trade (R-basiert, Start 1000), Trades chronologisch über alle Coins, höchstens 4 gleichzeitig (weitere Signale ausgelassen), Gewinn/Verlust bei Ausstieg gebucht, größter Rückgang auf dem realisierten Konto (ohne Zwischenbewertung offener Positionen, also eher zu optimistisch).

## Überblick

| Kandidat | gewählte Variante (nur nach Training) | Train n / Ø R | Val n / Ø R | Test n / Ø R | Test PF | Test Gewinnquote | Coins im Plus (Test) | Urteil |
|---|---|---|---|---|---|---|---|---|
| K1 Kompressions-Ausbruch 4h | K=0.85 V=an T=2.5 | 373 / +0.257 | 226 / -0.012 | 191 / -0.116 | 0.77 | 34 % | 3 von 8 | **no_edge** |
| K2 Ruhe-Fehlausbruch-Fade 1h | K=0.7 SF=2.0 S=an | 36 / +0.162 | 21 / +0.220 | 12 / +0.198 | 1.37 | 42 % | 3 von 7 | **inconclusive** |
| K3 Ruhe-Volumen-Schub-Fortsetzung 4h | K=0.7 VT=3 H=3 | 89 / +0.190 | 72 / -0.051 | 33 / -0.141 | 0.72 | 42 % | 2 von 10 | **no_edge** |

## K1 Kompressions-Ausbruch 4h

**Regeln**
- Zeitrahmen 4h. Signalkerze i: Ruhe `r12 < K x r96` (Box = Kerzen i-12..i-1, r12 = Mittel Hoch-Tief der Box, r96 = Mittel der Kerzen i-108..i-13) UND Close[i] > höchstes Hoch der Box (long) bzw. < tiefstes Tief (short); mit V=an zusätzlich Volumen[i] >= 1,5 x Median-Volumen der Kerzen i-48..i-1.
- Einstieg Open[i+1]. Anfangsstop = Boxmitte, Abstand zum Einstieg auf 1,5 bis 3,0 x ATR14[i] begrenzt; 1R = Abstand Einstieg-Stop.
- Ausstieg: Chandelier-Trail (long: höchstes Hoch seit Einstieg minus T x ATR14, steigt nur, wirkt ab der Folgekerze; short gespiegelt) oder Zeitausstieg zum Schluss der 12. Kerze (48 h). Kein festes Ziel.
- Gitter (8 Varianten): (K=0.7 V=aus T=2.5); (K=0.7 V=aus T=3.5); (K=0.7 V=an T=2.5); (K=0.7 V=an T=3.5); (K=0.85 V=aus T=2.5); (K=0.85 V=aus T=3.5); (K=0.85 V=an T=2.5); (K=0.85 V=an T=3.5)
- Urteils-Coins: HYPE, ARB, NEAR, UNI, AAVE, LINK, DOGE, DOT. Kontroll-Coins (getrennt, nicht im Urteil): AVAX, ADA.

**Alle 8 Varianten auf Training und Validierung** (Auswahl nur nach Training, die Validierungsspalten wurden zur Auswahl nicht benutzt):

| Variante | Train n | Train Ø R | Train PF | Train Coins>0 | Val n | Val Ø R | Val PF | Val Coins>0 | gewählt |
|---|---|---|---|---|---|---|---|---|---|
| K=0.7 V=aus T=2.5 | 332 | +0.162 | 1.37 | 7/8 | 221 | -0.091 | 0.81 | 2/8 |  |
| K=0.7 V=aus T=3.5 | 329 | +0.131 | 1.27 | 7/8 | 219 | -0.141 | 0.75 | 1/8 |  |
| K=0.7 V=an T=2.5 | 210 | +0.222 | 1.55 | 7/8 | 139 | -0.032 | 0.93 | 3/8 |  |
| K=0.7 V=an T=3.5 | 210 | +0.204 | 1.47 | 6/8 | 138 | -0.098 | 0.82 | 3/8 |  |
| K=0.85 V=aus T=2.5 | 548 | +0.208 | 1.50 | 8/8 | 331 | -0.055 | 0.88 | 4/8 |  |
| K=0.85 V=aus T=3.5 | 536 | +0.178 | 1.38 | 8/8 | 327 | -0.083 | 0.84 | 1/8 |  |
| K=0.85 V=an T=2.5 | 373 | +0.257 | 1.70 | 8/8 | 226 | -0.012 | 0.97 | 3/8 | ja |
| K=0.85 V=an T=3.5 | 368 | +0.215 | 1.52 | 8/8 | 225 | -0.062 | 0.88 | 3/8 |  |

**Gewählte Variante: K=0.85 V=an T=2.5**

| Abschnitt | Trades | Ø R (netto) | Standardfehler Ø R | Profit-Faktor | Gewinnquote | Ø Rendite je Trade (netto) | Ø Kerzen | Coins im Plus |
|---|---|---|---|---|---|---|---|---|
| Training | 373 | +0.257 | 0.070 | 1.70 | 43 % | +1.061 % | 8.4 | 8 von 8 |
| Validierung | 226 | -0.012 | 0.070 | 0.97 | 39 % | -0.210 % | 7.5 | 3 von 8 |
| Test | 191 | -0.116 | 0.090 | 0.77 | 34 % | -0.447 % | 7.6 | 3 von 8 |

**Je Coin (Urteils-Coins)**

| Coin | Test-Zeitraum | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|---|
| HYPE | 2026-05-15 bis 2026-11-06 | 34 | +0.203 | 20 | +0.322 | 21 | +0.011 |
| ARB | 2026-04-12 bis 2026-11-06 | 46 | +0.265 | 32 | -0.019 | 21 | +0.222 |
| NEAR | 2026-04-12 bis 2026-11-06 | 55 | +0.285 | 29 | -0.098 | 18 | -0.012 |
| UNI | 2026-04-12 bis 2026-11-06 | 44 | +0.240 | 31 | -0.076 | 21 | +0.208 |
| AAVE | 2026-04-12 bis 2026-11-06 | 48 | +0.337 | 26 | +0.112 | 27 | -0.197 |
| LINK | 2026-04-12 bis 2026-11-06 | 50 | +0.202 | 31 | -0.222 | 24 | -0.286 |
| DOGE | 2026-04-12 bis 2026-11-06 | 50 | +0.424 | 28 | -0.062 | 34 | -0.358 |
| DOT | 2026-04-12 bis 2026-11-06 | 46 | +0.065 | 29 | +0.077 | 25 | -0.270 |

**Kontroll-Coins (nicht im Urteil, getrennt ausgewiesen)**

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| AVAX | 50 | +0.184 | 26 | -0.010 | 26 | -0.317 |
| ADA | 37 | +0.158 | 30 | -0.036 | 29 | -0.255 |

Kontrollgruppe gepoolt: Train Ø R +0.173 (n=87), Val Ø R -0.024 (n=56), Test Ø R -0.284 (n=55).

**Test-Portfolio bei 2 % Risiko je Trade (Urteils-Coins, max. 4 gleichzeitig)**: Zeitraum 2026-04-12 bis 2026-11-06 (208 Tage).

| Kennzahl | Wert |
|---|---|
| Test-Rendite | -47.56 % |
| Rendite pro Kalendertag (linear) | -0.228 % |
| größter Rückgang (realisiertes Konto) | 47.56 % |
| bester einzelner Tag | +25.44 % (2026-08-21) |
| schlechtester einzelner Tag | -7.12 % (2026-09-15) |
| genommene / wegen 4er-Grenze ausgelassene Trades | 174 / 17 |
| höchster Gesamt-Nominalwert / Konto | 3.45 |

Test-Details: Ausstiege Stop 138 / Zeit 53; Long 85 / Short 106; Ø R ohne die 3 besten Trades -0.212; beste R: +8.91, +4.61, +4.17, schlechteste R: -1.09, -1.10, -1.11.

Kriterien: Test-Ø R > 0: **nein**; Validierung-Ø R > 0: **nein**; Test-Trades >= 30: **ja** (191); mindestens die Hälfte der Coins im Plus: **nein** (3 von 8). => **no_edge**

## K2 Ruhe-Fehlausbruch-Fade 1h

**Regeln**
- Zeitrahmen 1h. Signal wie K1 (ohne Volumen), aber **Gegenrichtung**: Close > Boxhoch => SHORT, Close < Boxtief => LONG. Bei S=an nur Signalkerzen mit Start 12:00 bis 21:00 UTC und Montag bis Freitag.
- Einstieg Open[i+1]. Fester Stop = Einstieg -/+ SF x ATR14[i]; 1R = dieser Abstand. Kein Ziel.
- Ausstieg: Stop oder Zeitausstieg zum Schluss der 12. Kerze (12 h).
- Gitter (8 Varianten): (K=0.7 SF=2.0 S=aus); (K=0.7 SF=2.0 S=an); (K=0.7 SF=3.0 S=aus); (K=0.7 SF=3.0 S=an); (K=0.85 SF=2.0 S=aus); (K=0.85 SF=2.0 S=an); (K=0.85 SF=3.0 S=aus); (K=0.85 SF=3.0 S=an)
- Urteils-Coins: HYPE, ARB, NEAR, UNI, AVAX, AAVE, LINK. Kontroll-Coins (getrennt, nicht im Urteil): DOGE, ADA, DOT.

**Alle 8 Varianten auf Training und Validierung** (Auswahl nur nach Training, die Validierungsspalten wurden zur Auswahl nicht benutzt):

| Variante | Train n | Train Ø R | Train PF | Train Coins>0 | Val n | Val Ø R | Val PF | Val Coins>0 | gewählt |
|---|---|---|---|---|---|---|---|---|---|
| K=0.7 SF=2.0 S=aus | 208 | +0.078 | 1.16 | 4/7 | 117 | +0.178 | 1.40 | 4/7 |  |
| K=0.7 SF=2.0 S=an | 36 | +0.162 | 1.58 | 4/7 | 21 | +0.220 | 1.67 | 4/7 | ja |
| K=0.7 SF=3.0 S=aus | 197 | +0.065 | 1.21 | 6/7 | 114 | +0.080 | 1.25 | 4/7 |  |
| K=0.7 SF=3.0 S=an | 36 | +0.122 | 1.71 | 5/7 | 21 | +0.201 | 2.19 | 4/7 |  |
| K=0.85 SF=2.0 S=aus | 433 | +0.038 | 1.08 | 4/7 | 228 | -0.058 | 0.89 | 4/7 |  |
| K=0.85 SF=2.0 S=an | 118 | +0.042 | 1.10 | 3/7 | 56 | -0.099 | 0.78 | 4/7 |  |
| K=0.85 SF=3.0 S=aus | 408 | +0.003 | 1.01 | 4/7 | 223 | -0.065 | 0.82 | 3/7 |  |
| K=0.85 SF=3.0 S=an | 118 | +0.027 | 1.09 | 3/7 | 56 | -0.017 | 0.94 | 3/7 |  |

**Gewählte Variante: K=0.7 SF=2.0 S=an**

| Abschnitt | Trades | Ø R (netto) | Standardfehler Ø R | Profit-Faktor | Gewinnquote | Ø Rendite je Trade (netto) | Ø Kerzen | Coins im Plus |
|---|---|---|---|---|---|---|---|---|
| Training | 36 | +0.162 | 0.145 | 1.58 | 61 % | +0.496 % | 10.2 | 4 von 7 |
| Validierung | 21 | +0.220 | 0.259 | 1.67 | 52 % | +0.516 % | 10.0 | 4 von 7 |
| Test | 12 | +0.198 | 0.441 | 1.37 | 42 % | +1.066 % | 8.5 | 3 von 7 |

**Je Coin (Urteils-Coins)**

| Coin | Test-Zeitraum | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|---|
| HYPE | 2026-09-15 bis 2026-11-06 | 3 | -0.407 | 0 | - | 2 | -0.833 |
| ARB | 2026-09-15 bis 2026-11-06 | 4 | +0.516 | 3 | +0.082 | 3 | +1.145 |
| NEAR | 2026-09-15 bis 2026-11-06 | 4 | +0.446 | 4 | +0.949 | 1 | -0.378 |
| UNI | 2026-09-15 bis 2026-11-06 | 6 | -0.109 | 2 | +1.014 | 0 | - |
| AVAX | 2026-09-15 bis 2026-11-06 | 5 | +0.432 | 4 | +0.155 | 1 | +1.416 |
| AAVE | 2026-09-15 bis 2026-11-06 | 8 | -0.131 | 4 | -0.220 | 1 | -1.070 |
| LINK | 2026-09-15 bis 2026-11-06 | 6 | +0.457 | 4 | -0.295 | 4 | +0.160 |

**Kontroll-Coins (nicht im Urteil, getrennt ausgewiesen)**

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|
| DOGE | 6 | +0.198 | 5 | +0.051 | 0 | - |
| ADA | 5 | -0.148 | 2 | -0.147 | 1 | -1.085 |
| DOT | 5 | +0.170 | 5 | +0.449 | 0 | - |

Kontrollgruppe gepoolt: Train Ø R +0.081 (n=16), Val Ø R +0.184 (n=12), Test Ø R -1.085 (n=1).

**Test-Portfolio bei 2 % Risiko je Trade (Urteils-Coins, max. 4 gleichzeitig)**: Zeitraum 2026-09-15 bis 2026-11-06 (52 Tage).

| Kennzahl | Wert |
|---|---|
| Test-Rendite | +4.37 % |
| Rendite pro Kalendertag (linear) | +0.084 % |
| größter Rückgang (realisiertes Konto) | 10.19 % |
| bester einzelner Tag | +7.16 % (2026-09-23) |
| schlechtester einzelner Tag | -5.44 % (2026-11-03) |
| genommene / wegen 4er-Grenze ausgelassene Trades | 12 / 0 |
| höchster Gesamt-Nominalwert / Konto | 2.54 |

Test-Details: Ausstiege Stop 5 / Zeit 7; Long 7 / Short 5; Ø R ohne die 3 besten Trades -0.487; beste R: +3.58, +1.77, +1.42, schlechteste R: -1.08, -1.09, -1.09.

Kriterien: Test-Ø R > 0: **ja**; Validierung-Ø R > 0: **ja**; Test-Trades >= 30: **nein** (12); mindestens die Hälfte der Coins im Plus: **nein** (3 von 7). => **inconclusive**

## K3 Ruhe-Volumen-Schub-Fortsetzung 4h

**Regeln**
- Zeitrahmen 4h. Signalkerze i: (1) Ruhe `r12 < K x r96`; (2) Volumen[i] >= VT x Median-Volumen der Kerzen i-48..i-1; (3) Hoch-Tief[i] >= 1,5 x ATR14[i-1]; (4) long, wenn Close > Open und (Close-Tief)/(Hoch-Tief) > 0,75, short, wenn Close < Open und < 0,25.
- Einstieg in Kerzenrichtung zum Open[i+1]. Anfangsstop = Mitte der Schub-Kerze, Abstand auf 1,5 bis 3,0 x ATR14[i-1] begrenzt; 1R = Abstand Einstieg-Stop.
- Ausstieg: Stop oder Zeitausstieg zum Schluss der H-ten Kerze nach Einstieg (H = 3: 12 h, H = 6: 24 h). Kein Ziel.
- Gitter (8 Varianten): (K=0.7 VT=2 H=3); (K=0.7 VT=2 H=6); (K=0.7 VT=3 H=3); (K=0.7 VT=3 H=6); (K=0.85 VT=2 H=3); (K=0.85 VT=2 H=6); (K=0.85 VT=3 H=3); (K=0.85 VT=3 H=6)
- Urteils-Coins: HYPE, ARB, NEAR, UNI, AAVE, LINK, DOGE, DOT, AVAX, ADA. Kontroll-Coins (getrennt, nicht im Urteil): keine.

**Alle 8 Varianten auf Training und Validierung** (Auswahl nur nach Training, die Validierungsspalten wurden zur Auswahl nicht benutzt):

| Variante | Train n | Train Ø R | Train PF | Train Coins>0 | Val n | Val Ø R | Val PF | Val Coins>0 | gewählt |
|---|---|---|---|---|---|---|---|---|---|
| K=0.7 VT=2 H=3 | 177 | +0.130 | 1.36 | 6/10 | 120 | +0.086 | 1.21 | 6/10 |  |
| K=0.7 VT=2 H=6 | 171 | +0.050 | 1.10 | 6/10 | 119 | -0.062 | 0.89 | 4/10 |  |
| K=0.7 VT=3 H=3 | 89 | +0.190 | 1.57 | 8/10 | 72 | -0.051 | 0.88 | 4/10 | ja |
| K=0.7 VT=3 H=6 | 89 | -0.160 | 0.70 | 3/10 | 72 | -0.304 | 0.50 | 2/10 |  |
| K=0.85 VT=2 H=3 | 349 | +0.114 | 1.34 | 7/10 | 218 | +0.069 | 1.17 | 6/10 |  |
| K=0.85 VT=2 H=6 | 327 | +0.135 | 1.28 | 5/10 | 207 | +0.056 | 1.11 | 6/10 |  |
| K=0.85 VT=3 H=3 | 194 | +0.154 | 1.46 | 9/10 | 131 | +0.066 | 1.17 | 6/10 |  |
| K=0.85 VT=3 H=6 | 191 | +0.004 | 1.01 | 4/10 | 129 | -0.018 | 0.96 | 5/10 |  |

**Gewählte Variante: K=0.7 VT=3 H=3**

| Abschnitt | Trades | Ø R (netto) | Standardfehler Ø R | Profit-Faktor | Gewinnquote | Ø Rendite je Trade (netto) | Ø Kerzen | Coins im Plus |
|---|---|---|---|---|---|---|---|---|
| Training | 89 | +0.190 | 0.123 | 1.57 | 51 % | +0.877 % | 2.8 | 8 von 10 |
| Validierung | 72 | -0.051 | 0.118 | 0.88 | 43 % | -0.115 % | 2.7 | 4 von 10 |
| Test | 33 | -0.141 | 0.181 | 0.72 | 42 % | -0.251 % | 2.5 | 2 von 10 |

**Je Coin (Urteils-Coins)**

| Coin | Test-Zeitraum | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R |
|---|---|---|---|---|---|---|---|
| HYPE | 2026-05-15 bis 2026-11-06 | 2 | +1.416 | 4 | -0.311 | 3 | +0.712 |
| ARB | 2026-04-12 bis 2026-11-06 | 8 | +0.220 | 9 | +0.108 | 6 | -0.638 |
| NEAR | 2026-04-12 bis 2026-11-06 | 10 | +0.230 | 8 | -0.048 | 0 | - |
| UNI | 2026-04-12 bis 2026-11-06 | 13 | -0.448 | 9 | +0.436 | 6 | +0.299 |
| AAVE | 2026-04-12 bis 2026-11-06 | 5 | +1.007 | 7 | -0.465 | 1 | -0.308 |
| LINK | 2026-04-12 bis 2026-11-06 | 9 | +0.296 | 7 | +0.165 | 2 | -0.027 |
| DOGE | 2026-04-12 bis 2026-11-06 | 10 | +0.297 | 11 | -0.202 | 7 | -0.111 |
| DOT | 2026-04-12 bis 2026-11-06 | 11 | -0.008 | 5 | -0.247 | 2 | -0.340 |
| AVAX | 2026-04-12 bis 2026-11-06 | 8 | +0.174 | 7 | -0.207 | 3 | -0.977 |
| ADA | 2026-04-12 bis 2026-11-06 | 13 | +0.295 | 5 | +0.010 | 3 | -0.006 |

**Test-Portfolio bei 2 % Risiko je Trade (Urteils-Coins, max. 4 gleichzeitig)**: Zeitraum 2026-04-12 bis 2026-11-06 (208 Tage).

| Kennzahl | Wert |
|---|---|
| Test-Rendite | -9.74 % |
| Rendite pro Kalendertag (linear) | -0.047 % |
| größter Rückgang (realisiertes Konto) | 13.87 % |
| bester einzelner Tag | +6.79 % (2026-09-03) |
| schlechtester einzelner Tag | -4.46 % (2026-08-10) |
| genommene / wegen 4er-Grenze ausgelassene Trades | 33 / 0 |
| höchster Gesamt-Nominalwert / Konto | 2.73 |

Test-Details: Ausstiege Stop 13 / Zeit 20; Long 17 / Short 16; Ø R ohne die 3 besten Trades -0.343; beste R: +3.40, +1.15, +1.06, schlechteste R: -1.12, -1.12, -1.13.

Kriterien: Test-Ø R > 0: **nein**; Validierung-Ø R > 0: **nein**; Test-Trades >= 30: **ja** (33); mindestens die Hälfte der Coins im Plus: **nein** (2 von 10). => **no_edge**

## Vorbehalte

- Die Trades sind nicht unabhängig: Ausbrüche und Schübe treten über Alts hinweg gleichzeitig auf (gemeinsamer Marktfaktor), das effektive n ist kleiner als gezählt, die Standardfehler sind zu optimistisch.
- Mehrfachtest: 24 Gitter-Varianten plus die Vorab-Suche. Die Gewinn-Hypothesen wurden im Trainingsteil gefunden; nur Validierung und Test sind echte Außer-Stichprobe-Prüfungen.
- Regimewechsel: siehe Datenfenster oben (4h-Training Aufwärtsphase, 4h-Validierung Bärenmarkt, 4h-Test seitwärts bis leicht aufwärts bei BTC). 1h hat nur etwa 208 Tage, der 1h-Test nur etwa 52 Tage; K2 mit Sitzungsfilter hat dort zu wenige Signale.
- Das Portfolio rechnet ohne Zwischenbewertung offener Positionen; Slippage in Ausbruchskerzen dünner Alts kann über 0,03 % liegen; Funding ist pauschal angesetzt.
- Nichts hiervon ist ein „+50 % pro Tag“-Ansatz: auch ein bestätigter Vorteil wäre bei 2 % Risiko je Trade im Bereich weniger Zehntel Prozent Konto pro Tag.

