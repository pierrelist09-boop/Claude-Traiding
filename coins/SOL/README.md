# SOL: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 4999 4h-Kerzen ab 2024-07-26, 4999 1h-Kerzen, 2244 Tageskerzen.

**Empfehlung: Paper-Test (klein)**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.8 % | 4h 2.2 % | 1d 7.64 %
- Gleichlauf mit BTC (1h-Renditen): 0.83
- Trendneigung 4h: Autokorrelation 0.013 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 59 % der Zeit klare Struktur (auf 31 %, ab 28 %)
- Zonen-Respekt: nach 816 Ablehnungs-Kerzen an Zonen lief der Kurs in 48 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 110,398 $ / Verkäufer 424,932 $, Spread 0.0011 %, Tagesvolumen 218.6 Mio $, offenes Volumen 514.5 Mio $, Funding -0.00113 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 20 Training und Validierung. Davon sind im Test 50 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **1h** (Kontext: 4h und 1d)
- Zählende Ereignisse: Ablehnungs-Kerzen an Zonen
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2, 1h 1; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

- Training: +0.45 R, Treffer 22 %, PF 1.62, n=45
- Validierung: +0.15 R, Treffer 25 %, PF 1.19, n=28
- **Test (ungesehen): +0.10 R, Treffer 27 %, PF 1.14, n=33**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -0.04 R, Treffer 19 %, PF 0.91, n=16

## Plan

Wenn die Lesart (`python3 -m chartreader SOL`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **Paper-Test (klein)**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
