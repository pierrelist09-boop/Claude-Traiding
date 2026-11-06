# DOGE: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 4999 4h-Kerzen ab 2024-07-26, 4999 1h-Kerzen, 2270 Tageskerzen.

**Empfehlung: nur beobachten**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.81 % | 4h 2.38 % | 1d 7.32 %
- Gleichlauf mit BTC (1h-Renditen): 0.76
- Trendneigung 4h: Autokorrelation -0.001 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 61 % der Zeit klare Struktur (auf 27 %, ab 34 %)
- Zonen-Respekt: nach 795 Ablehnungs-Kerzen an Zonen lief der Kurs in 46 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 156,571 $ / Verkäufer 50,269 $, Spread 0.0014 %, Tagesvolumen 8.3 Mio $, offenes Volumen 69.8 Mio $, Funding 0.00125 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 19 Training und Validierung. Davon sind im Test 37 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)
- Punkteschwelle 4.5 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

- Training: +0.32 R, Treffer 27 %, PF 1.58, n=63
- Validierung: +0.29 R, Treffer 34 %, PF 1.75, n=32
- **Test (ungesehen): +1.01 R, Treffer 23 %, PF 2.82, n=30**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: +0.16 R, Treffer 40 %, PF 1.54, n=5

## Plan

Wenn die Lesart (`python3 -m chartreader DOGE`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **nur beobachten**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
