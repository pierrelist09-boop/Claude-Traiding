# XRP: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 5000 4h-Kerzen ab 2024-07-26, 5000 1h-Kerzen, 2237 Tageskerzen.

**Empfehlung: nur beobachten**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.73 % | 4h 1.92 % | 1d 6.1 %
- Gleichlauf mit BTC (1h-Renditen): 0.76
- Trendneigung 4h: Autokorrelation 0.002 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 57 % der Zeit klare Struktur (auf 26 %, ab 31 %)
- Zonen-Respekt: nach 817 Ablehnungs-Kerzen an Zonen lief der Kurs in 50 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 1,091,581 $ / Verkäufer 1,049,571 $, Spread 0.0085 %, Tagesvolumen 66.9 Mio $, offenes Volumen 204.1 Mio $, Funding 0.00037 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 108 Training und Validierung. Davon sind im Test 50 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Strukturbrüche (bos, bos_volume, choch)
- Punkteschwelle 3 (Trendpunkte: 1d 3, 4h 2; je Ereignis 3, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.75 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

- Training: +0.37 R, Treffer 38 %, PF 1.74, n=56
- Validierung: +0.36 R, Treffer 30 %, PF 1.77, n=30
- **Test (ungesehen): -0.31 R, Treffer 23 %, PF 0.43, n=26**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -1.42 R, Treffer 0 %, PF 0.00, n=2

## Plan

Wenn die Lesart (`python3 -m chartreader XRP`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **nur beobachten**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
