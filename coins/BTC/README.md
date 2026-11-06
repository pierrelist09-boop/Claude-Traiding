# BTC: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 4999 4h-Kerzen ab 2024-07-26, 4999 1h-Kerzen, 2270 Tageskerzen.

**Empfehlung: nur beobachten**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.51 % | 4h 1.24 % | 1d 4.07 %
- Gleichlauf mit BTC (1h-Renditen): 1.0
- Trendneigung 4h: Autokorrelation -0.016 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 59 % der Zeit klare Struktur (auf 31 %, ab 28 %)
- Zonen-Respekt: nach 861 Ablehnungs-Kerzen an Zonen lief der Kurs in 45 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 2,167,412 $ / Verkäufer 929,818 $, Spread 0.0013 %, Tagesvolumen 2935.4 Mio $, offenes Volumen 3215.2 Mio $, Funding 0.00125 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 41 Training und Validierung. Davon sind im Test 34 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **1h** (Kontext: 4h und 1d)
- Zählende Ereignisse: alle Ereignisse
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2, 1h 1; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.75 ATR Puffer
- Ausstieg: Schluss, sobald die Struktur der Einstiegsebene gegen die Position dreht

- Training: +0.41 R, Treffer 38 %, PF 1.92, n=72
- Validierung: +0.48 R, Treffer 34 %, PF 2.00, n=32
- **Test (ungesehen): -0.40 R, Treffer 38 %, PF 0.32, n=21**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -0.45 R, Treffer 25 %, PF 0.24, n=4

## Plan

Wenn die Lesart (`python3 -m chartreader BTC`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **nur beobachten**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
