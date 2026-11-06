# ETH: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 4999 4h-Kerzen ab 2024-07-26, 4999 1h-Kerzen, 2270 Tageskerzen.

**Empfehlung: nur beobachten**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.68 % | 4h 1.87 % | 1d 5.33 %
- Gleichlauf mit BTC (1h-Renditen): 0.88
- Trendneigung 4h: Autokorrelation 0.017 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 58 % der Zeit klare Struktur (auf 31 %, ab 27 %)
- Zonen-Respekt: nach 859 Ablehnungs-Kerzen an Zonen lief der Kurs in 46 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 4,688,924 $ / Verkäufer 1,656,197 $, Spread 0.0045 %, Tagesvolumen 744.3 Mio $, offenes Volumen 2191.9 Mio $, Funding 0.00125 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 16 Training und Validierung. Davon sind im Test 0 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)
- Punkteschwelle 3 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): letzter bestätigter Swing ± 0.25 ATR Puffer
- Ausstieg: Schluss, sobald die Struktur der Einstiegsebene gegen die Position dreht

- Training: +0.18 R, Treffer 41 %, PF 1.38, n=86
- Validierung: +0.49 R, Treffer 44 %, PF 2.10, n=36
- **Test (ungesehen): -0.41 R, Treffer 28 %, PF 0.24, n=36**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -0.43 R, Treffer 18 %, PF 0.29, n=11

## Plan

Wenn die Lesart (`python3 -m chartreader ETH`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **nur beobachten**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
