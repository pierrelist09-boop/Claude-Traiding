# Ergebnis Ausbruch und Momentum (Blickwinkel 1 der Schnell-Recherche)

Alle Zahlen stammen aus `research/fast/ausbruch.py` (Standardbibliothek, lokaler Cache, kein Netz). Auswahl der Variante nur auf dem Trainingsteil, Bestaetigung auf Validierung, der Test-Abschnitt wurde EINMAL gerechnet (das Skript bricht beim zweiten Lauf ab; Ergebnisse stehen in ergebnis_ausbruch.json). Nach einem reinen Formatierungsfehler beim Schreiben dieser Datei wurde sie aus dem gespeicherten JSON neu erzeugt, ohne Neuberechnung. Einzige Zweitrechnung auf Test-Daten: die K3-Nachanalyse (gleiche Beine, per assert identisch zum Testlauf, nur Konzentrationsdiagnose). Regeln, Parameter und Urteile wurden nach dem Test nicht geaendert.

## Daten, Aufteilung, Kosten

- 4h-Daten (BTC): 2024-07-26 bis 2026-11-06, 4999 Kerzen. Training 2024-07-26 bis 2025-09-16, Validierung 2025-09-16 bis 2026-04-12, Test 2026-04-12 bis 2026-11-06. HYPE hat nur 4209 4h-Kerzen (ab 2024-12-05), seine Abschnitte sind entsprechend kuerzer.
- 1h-Daten (BTC): 2026-04-12 bis 2026-11-06, 4999 Kerzen. Training 2026-04-12 bis 2026-07-25, Validierung 2026-07-26 bis 2026-09-15, Test 2026-09-16 bis 2026-11-06 (Grenzen an 00:00 UTC ausgerichtet).
- Kosten je Seite: Gebuehr 0,045 % + Slippage (0,02 % fuer BTC/ETH/SOL/XRP/HYPE, 0,04 % sonst; K2: 0,02 % nur SOL und HYPE; K3: 0,02 % nur BTC/ETH/SOL/XRP); Funding 0,01 % je 8 h als Kosten nur auf Longs (Shorts bekommen keine Gutschrift). Roundtrip also 0,13 % bis 0,17 % plus Funding. Kosten werden in R umgerechnet (Kosten-Anteil am Nominal mal Einstieg / R0) und vom Brutto-R abgezogen.
- Kein Blick in die Zukunft: Signal nur aus abgeschlossenen Kerzen, Einstieg zum Eroeffnungskurs der Folgekerze, Stop und Ziel in derselben Kerze: Stop zuerst, Gap ueber den Stop: Ausstieg zum Eroeffnungskurs. Selbsttest (`python3 ausbruch.py selbsttest`) prueft Stop-Reihenfolge, Gap, Trail-Verzoegerung, Zeitstopp, Kausalitaet der Indikatoren auf gekuerzten Reihen und die Portfolio-Mechanik.
- Abschnitte werden getrennt simuliert (Position startet flach). K1: am Abschnittsende Zwangsschluss zum Schlusskurs. K2: nur Tage, die samt Ausstiegskerze im Abschnitt liegen. K3: nur Rebalances, deren Haltefenster im Abschnitt endet.
- Zahl der getesteten Varianten: 12 (3 Kandidaten mal 4 Gitterpunkte). Dazu 4 gespiegelte K3-Laeufe als reine Diagnose auf dem Training (nicht waehlbar). Test-Abschnitt: je Kandidat genau eine Variante, einmal.
- Kandidat-Regel: Test-Ø R nach Kosten > 0 UND Validierung > 0 UND mindestens 30 Test-Trades UND mindestens die Haelfte der Coins im Test im Plus. Sonst `no_edge` oder `inconclusive`.
- Portfolio-Rechnung (Test): Risiko 2 % des aktuellen Kontos je Trade (Hebel hoechstens 5), Trades chronologisch ueber alle Coins, hoechstens 4 gleichzeitig (weitere uebersprungen), Gewinn/Verlust bei Ausstieg gebucht, groesster Rueckgang auf dem realisierten Konto. K3 braucht 6 Beine zugleich: dort 8 %/6 = 1,33 % je Bein, hoechstens 6 Beine (gleiches Gesamtrisiko wie 4 mal 2 %).

Uebersicht:

| Kandidat | gewaehlte Variante (Training) | Val Ø R | Test Trades | Test Ø R | Coins im Plus | Rendite Test (2 % Risiko) | Groesster Rueckgang | Bester Tag | Urteil |
|---|---|---|---|---|---|---|---|---|---|
| K1 Squeeze-Ausbruch 4h | P=0.15,N=24 | -0.196 | 229 | 0.026 | 6/13 | -25.8 % | 35.4 % | 18.00 % | **no_edge** |
| K2 Eroeffnungsspanne 1h | F=AN,T=1.5 | -0.160 | 214 | -0.047 | 3/9 | -36.9 % | 47.9 % | 14.07 % | **no_edge** |
| K3 Relative Staerke L/S 4h | L=42,H=18 | 0.043 | 414 | 0.041 | 10/12 | 22.0 % | 13.3 % | 13.54 % | **edge_candidate** |

## K1 Squeeze-Ausbruch 4h

**Regeln.** Indikatoren je 4h-Kerze i: SMA20 und Populations-SD der Schlusskurse, Bandbreite BBW = 4 SD / SMA. Perzentil-Rang PR gegen die 180 Vorgaenger. Squeeze aktiv, wenn PR <= P in mindestens einer der Kerzen i-6..i-1. Box = hoechstes Hoch / tiefstes Tief der N Kerzen i-N..i-1 (ohne i). LONG: Schluss_i > Box-Hoch UND Squeeze UND Volumen_i >= 1,2 mal Mittel der 20 Vorkerzen; SHORT gespiegelt. Einstieg Eroeffnung i+1. Anfangs-Stop Long = max(Box-Tief, Einstieg - 3 ATR14_i), mindestens 1 ATR Abstand (Short gespiegelt). Ausstieg: Chandelier-Trail (hoechstes Hoch seit Einstieg - 3 ATR14 der Signalkerze, gilt ab Folgekerze) oder Zeitstopp nach 30 Kerzen. Eine Position je Coin.

**Gitter (4 Varianten):** Gitter P in {0,15; 0,30} mal N in {12; 24}. **Auswahl nur auf Training** (hoechster Ø R nach Kosten bei mindestens 30 Trainings-Trades): **P=0.15,N=24** (regulaer).

Alle Varianten, Training und Validierung (Test nicht angesehen ausser der gewaehlten Variante):

| Variante | Train Trades | Train Ø R | Train PF | Val Trades | Val Ø R | Val PF |
|---|---|---|---|---|---|---|
| P=0.15,N=12 | 485 | 0.129 | 1.37 | 284 | -0.093 | 0.77 |
| P=0.15,N=24 (gewaehlt) | 383 | 0.150 | 1.47 | 244 | -0.196 | 0.57 |
| P=0.30,N=12 | 659 | 0.120 | 1.34 | 391 | -0.012 | 0.97 |
| P=0.30,N=24 | 524 | 0.107 | 1.32 | 328 | -0.083 | 0.80 |

**Gewaehlte Variante P=0.15,N=24, je Coin (Ø R nach Kosten; n = Trades):**

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R | Test PF |
|---|---|---|---|---|---|---|---|
| BTC | 32 | 0.051 | 25 | -0.115 | 19 | -0.112 | 0.79 |
| ETH | 25 | 0.054 | 22 | -0.048 | 21 | 0.020 | 1.04 |
| SOL | 36 | 0.294 | 24 | -0.380 | 18 | 0.247 | 1.55 |
| XRP | 29 | -0.076 | 16 | 0.398 | 19 | 0.174 | 1.89 |
| DOGE | 29 | 0.396 | 18 | -0.416 | 19 | -0.109 | 0.78 |
| LINK | 28 | 0.284 | 20 | -0.261 | 15 | 0.291 | 1.97 |
| AVAX | 30 | 0.269 | 17 | -0.187 | 18 | -0.015 | 0.96 |
| NEAR | 35 | 0.150 | 17 | -0.021 | 18 | -0.054 | 0.86 |
| AAVE | 30 | 0.056 | 17 | -0.370 | 15 | 0.039 | 1.10 |
| HYPE | 23 | 0.276 | 17 | -0.023 | 16 | -0.029 | 0.89 |
| BNB | 30 | -0.148 | 17 | -0.350 | 14 | -0.224 | 0.57 |
| ADA | 29 | 0.174 | 17 | -0.430 | 19 | 0.227 | 1.67 |
| UNI | 27 | 0.172 | 17 | -0.289 | 18 | -0.133 | 0.73 |
| **gesamt** | 383 | 0.150 | 244 | -0.196 | 229 | 0.026 | 1.06 |

Test gesamt:

| | Trades | Ø R netto | PF | Trefferquote | Ø R brutto | Ø Kosten (R) |
|---|---|---|---|---|---|---|
| alle | 229 | 0.026 | 1.06 | 33.2 % | 0.066 | 0.040 |
| nur Long | 117 | 0.152 | 1.36 | 34.2 % | 0.200 | 0.049 |
| nur Short | 112 | -0.105 | 0.73 | 32.1 % | -0.074 | 0.031 |

- Ausstiegsgruende im Test: {'stop': 207, 'zeit': 22}. Naive t-Statistik Ø R: 0.34. Wochen-Block-Bootstrap 95 %-Intervall fuer Ø R: [-0.251; 0.341] (29 Wochen, Anteil Resamples > 0: 0.54).
- Coins im Test im Plus: 6 von 13.
- Portfolio-Rechnung Test (2 % Risiko): Rendite -25.8 %, groesster Rueckgang 35.4 %, bester Tag 18.00 %, schlechtester Tag -5.60 %, genommene Trades 159, uebersprungen 70.
- **Urteil: no_edge.**

## K2 Eroeffnungsspanne 1h

**Regeln.** Je UTC-Tag Spanne aus den 1h-Kerzen 00:00 bis 03:00 UTC (OR_H, OR_L). Signalfenster Kerzen mit Beginn 04:00 bis 15:00 UTC: erster Schluss > OR_H + 0,1 ATR14 (Long) bzw. < OR_L - 0,1 ATR14 (Short), ATR14 der 03:00-Kerze. Ein Trade je Coin und Tag, Einstieg Eroeffnung der Folgekerze. Filter AN: Spannenbreite <= Median der 20 Vortage (mindestens 10 Vortage noetig). Stop an der Gegenseite der Spanne, Risiko R0 auf 0,8 bis 2,0 ATR14 begrenzt, Ziel = T mal R0, Zeitausstieg 00:00 UTC des Folgetags.

**Gitter (4 Varianten):** Gitter F in {AUS, AN} mal T in {1,5; 3,0}. **Auswahl nur auf Training** (hoechster Ø R nach Kosten bei mindestens 30 Trainings-Trades): **F=AN,T=1.5** (regulaer).

Alle Varianten, Training und Validierung (Test nicht angesehen ausser der gewaehlten Variante):

| Variante | Train Trades | Train Ø R | Train PF | Val Trades | Val Ø R | Val PF |
|---|---|---|---|---|---|---|
| F=AUS,T=1.5 | 827 | -0.184 | 0.69 | 417 | -0.147 | 0.74 |
| F=AUS,T=3.0 | 827 | -0.219 | 0.65 | 417 | -0.074 | 0.87 |
| F=AN,T=1.5 (gewaehlt) | 439 | -0.162 | 0.73 | 222 | -0.160 | 0.73 |
| F=AN,T=3.0 | 439 | -0.207 | 0.68 | 222 | -0.079 | 0.87 |

**Gewaehlte Variante F=AN,T=1.5, je Coin (Ø R nach Kosten; n = Trades):**

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R | Test PF |
|---|---|---|---|---|---|---|---|
| HYPE | 45 | -0.295 | 33 | 0.204 | 23 | -0.006 | 0.99 |
| NEAR | 50 | -0.109 | 20 | -0.306 | 26 | 0.354 | 1.96 |
| AAVE | 47 | -0.004 | 29 | -0.160 | 20 | -0.273 | 0.58 |
| SOL | 51 | -0.228 | 25 | -0.009 | 23 | -0.308 | 0.55 |
| DOGE | 51 | -0.158 | 22 | -0.266 | 27 | -0.232 | 0.61 |
| LINK | 49 | -0.196 | 25 | -0.294 | 21 | -0.192 | 0.68 |
| AVAX | 55 | -0.095 | 24 | -0.613 | 23 | 0.127 | 1.29 |
| UNI | 42 | -0.291 | 21 | 0.301 | 25 | -0.079 | 0.87 |
| ADA | 49 | -0.108 | 23 | -0.421 | 26 | 0.107 | 1.25 |
| **gesamt** | 439 | -0.162 | 222 | -0.160 | 214 | -0.047 | 0.91 |

Test gesamt:

| | Trades | Ø R netto | PF | Trefferquote | Ø R brutto | Ø Kosten (R) |
|---|---|---|---|---|---|---|
| alle | 214 | -0.047 | 0.91 | 43.9 % | 0.047 | 0.093 |
| nur Long | 93 | -0.311 | 0.53 | 32.3 % | -0.214 | 0.097 |
| nur Short | 121 | 0.156 | 1.34 | 52.9 % | 0.247 | 0.091 |

- Ausstiegsgruende im Test: {'stop': 98, 'ziel': 70, 'zeit': 46}. Naive t-Statistik Ø R: -0.61. Wochen-Block-Bootstrap 95 %-Intervall fuer Ø R: [-0.271; 0.173] (9 Wochen, Anteil Resamples > 0: 0.36).
- Coins im Test im Plus: 3 von 9.
- Portfolio-Rechnung Test (2 % Risiko): Rendite -36.9 %, groesster Rueckgang 47.9 %, bester Tag 14.07 %, schlechtester Tag -14.36 %, genommene Trades 162, uebersprungen 52.
- **Urteil: no_edge.**

## K3 Relative Staerke L/S 4h

**Regeln.** Rebalance auf der 4h-Kerze, die um 00:00 UTC schliesst, danach alle H Kerzen. Score = (ln c_t - ln c_(t-L)) / (SD der 60 4h-Log-Renditen mal Wurzel L). Top 3 Long, Bottom 3 Short, Gewicht je Bein proportional 1/ATR14%, Summe Long = Summe Short (dollar-neutral). Einstieg Eroeffnung der Folgekerze, Bein-Stop 3 ATR14, Ausstieg aller Beine nach H Kerzen zum Eroeffnungskurs. Hauptlauf ohne HYPE (12 Coins, mindestens 10 im Universum).

**Gitter (4 Varianten):** Gitter L in {18; 42} mal H in {6; 18}. **Auswahl nur auf Training** (hoechster Ø R nach Kosten bei mindestens 30 Trainings-Trades): **L=42,H=18** (regulaer).

Alle Varianten, Training und Validierung (Test nicht angesehen ausser der gewaehlten Variante):

| Variante | Train Trades | Train Ø R | Train PF | Val Trades | Val Ø R | Val PF | Train gespiegelt (Umkehr) Ø R |
|---|---|---|---|---|---|---|---|
| L=18,H=6 | 2238 | -0.025 | 0.89 | 1242 | -0.025 | 0.89 | -0.028 (n=2238) |
| L=18,H=18 | 744 | -0.013 | 0.96 | 408 | 0.016 | 1.04 | -0.019 (n=744) |
| L=42,H=6 | 2238 | -0.023 | 0.90 | 1242 | -0.008 | 0.96 | -0.033 (n=2238) |
| L=42,H=18 (gewaehlt) | 744 | -0.003 | 0.99 | 408 | 0.043 | 1.11 | -0.011 (n=744) |

**Gewaehlte Variante L=42,H=18, je Coin (Ø R nach Kosten; n = Trades, bei K3 = Beine):**

| Coin | Train n | Train Ø R | Val n | Val Ø R | Test n | Test Ø R | Test PF |
|---|---|---|---|---|---|---|---|
| AAVE | 78 | 0.048 | 39 | 0.021 | 42 | -0.082 | 0.77 |
| ADA | 55 | 0.006 | 29 | 0.093 | 36 | 0.039 | 1.12 |
| AVAX | 53 | -0.022 | 28 | 0.187 | 32 | 0.023 | 1.07 |
| BNB | 63 | -0.000 | 43 | -0.028 | 36 | 0.043 | 1.13 |
| BTC | 73 | -0.075 | 32 | 0.057 | 27 | 0.056 | 1.16 |
| DOGE | 54 | 0.120 | 35 | -0.054 | 34 | 0.062 | 1.17 |
| ETH | 60 | 0.098 | 37 | -0.109 | 33 | 0.074 | 1.23 |
| LINK | 49 | -0.403 | 17 | 0.145 | 24 | 0.161 | 1.50 |
| NEAR | 54 | -0.096 | 42 | 0.094 | 42 | 0.122 | 1.36 |
| SOL | 62 | 0.047 | 30 | -0.256 | 37 | 0.064 | 1.23 |
| UNI | 67 | 0.035 | 43 | 0.313 | 43 | 0.085 | 1.27 |
| XRP | 76 | 0.102 | 33 | 0.060 | 28 | -0.153 | 0.56 |
| **gesamt** | 744 | -0.003 | 408 | 0.043 | 414 | 0.041 | 1.12 |

Test gesamt:

| | Trades | Ø R netto | PF | Trefferquote | Ø R brutto | Ø Kosten (R) |
|---|---|---|---|---|---|---|
| alle | 414 | 0.041 | 1.12 | 47.3 % | 0.078 | 0.036 |
| nur Long | 207 | 0.119 | 1.36 | 45.9 % | 0.162 | 0.043 |
| nur Short | 207 | -0.037 | 0.89 | 48.8 % | -0.007 | 0.030 |

- Ausstiegsgruende im Test: {'zeit': 320, 'stop': 94}. Naive t-Statistik Ø R: 0.85. Wochen-Block-Bootstrap 95 %-Intervall fuer Ø R: [-0.035; 0.125] (30 Wochen, Anteil Resamples > 0: 0.85).
- Coins im Test im Plus: 10 von 12.
- Korb-Sicht (dollar-neutral, Gewichte je Seite = 1): 69 Rebalances, Ø Netto-Rendite je Rebalance 0.418 % (brutto 0.812 %), Trefferquote 50.7 %, t-Statistik 0.72, Anteil gestoppter Beine 22.7 %.
- HYPE-Empfindlichkeit (nur Training + Validierung zusammen, Test nicht angefasst): ohne HYPE 1158 Beine, Ø R 0.014; mit HYPE im Universum 1158 Beine, Ø R 0.013.
- Einordnung: effektive Stichprobe sind die 69 Rebalances, nicht die 414 Beine (Beine eines Rebalance sind korreliert). Das Intervall oben schliesst 0 ein, die Korb-t-Statistik ist 0.72. Ø R auf Training war -0.003 (also praktisch null), die gespiegelte Variante (Umkehr) auf Training -0.011. Der Gewinn kommt aus den Long-Beinen (0.119 R), die Short-Beine liegen bei -0.037 R.
- Nachanalyse Konzentration (dieselben Test-Beine, keine Aenderung von Regeln oder Urteil): Summe aller Beine 17.0 R; der staerkste einzelne Rebalance bringt 6.7 R, die drei staerksten 17.4 R, der mittlere Rebalance 0.10 R, Anteil Rebalances im Plus 0.52. Ø R je Bein ohne den staerksten Rebalance: 0.025 (408 Beine), ohne die drei staerksten: -0.001 (396 Beine).
- Portfolio-Rechnung Test (1,33 % je Bein Risiko): Rendite 22.0 %, groesster Rueckgang 13.3 %, bester Tag 13.54 %, schlechtester Tag -4.22 %, genommene Trades 414, uebersprungen 0.
- **Urteil: edge_candidate.**

## Gesamtbild und Vorbehalte

- Das Urteil richtet sich strikt nach den Regeln oben. Ein positiver Test-Ø R allein ist kein Beleg: Trades sind stark gebuendelt (Coin-Korrelation zu BTC 0,5 bis 0,8), die effektive Stichprobe ist kleiner als die Tradezahl; das Wochen-Bootstrap-Intervall ist die ehrlichere Groesse.
- `edge_candidate` heisst nur: die vorab festgelegten Huerden (Test > 0, Validierung > 0, mindestens 30 Test-Trades, mindestens die Haelfte der Coins im Plus) wurden genommen. Es ist KEIN Nachweis; weiteres Vorgehen waere ein Vorwaertstest (Paper) ohne Parameteraenderung.
- Der Test deckt nur ein Marktregime ab (4h: ca. 7 Monate, 1h: ca. 52 Tage). Mit 12 Varianten (Best-of-4 je Kandidat) ist ein Zufallsvorsprung moeglich; deshalb zaehlen nur Validierung und Test.
- Funding ist pauschal angesetzt (Longs belastet, Shorts ohne Gutschrift), echte Funding-Historie wurde nicht abgerufen. Slippage bei Ausbruechen in Marktbewegung kann hoeher sein als angesetzt.
- Die Portfolio-Zahlen zeigen, wie weit das Ergebnis von "schnell viel Geld" entfernt ist: Die Test-Rendite steht in der Uebersicht; die besten Einzeltage (bis ca. 18 %) sind Ausreisser bei hohem Risiko und keine Dauerleistung, +50 % am Tag wird nirgends erreicht. K1 und K2 verlieren im Test Geld, K3 liegt bei der Rendite im Plus, haengt aber an wenigen Ereignissen (siehe Nachanalyse).
