# HYPE: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:58. Daten: Hyperliquid, 4209 4h-Kerzen ab 2024-12-05, 5000 1h-Kerzen, 701 Tageskerzen.

**Empfehlung: Paper-Test (klein)**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 1.1 % | 4h 3.26 % | 1d 7.53 %
- Gleichlauf mit BTC (1h-Renditen): 0.57
- Trendneigung 4h: Autokorrelation -0.057 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 61 % der Zeit klare Struktur (auf 30 %, ab 31 %)
- Zonen-Respekt: nach 759 Ablehnungs-Kerzen an Zonen lief der Kurs in 47 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 59,890 $ / Verkäufer 25,913 $, Spread 0.0013 %, Tagesvolumen 406.5 Mio $, offenes Volumen 1754.1 Mio $, Funding 0.00125 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 95 Training und Validierung. Davon sind im Test 61 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **1h** (Kontext: 4h und 1d)
- Zählende Ereignisse: Strukturbrüche (bos, bos_volume, choch)
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2, 1h 1; je Ereignis 3, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

- Training: +0.41 R, Treffer 38 %, PF 1.74, n=40
- Validierung: +0.91 R, Treffer 26 %, PF 2.37, n=27
- **Test (ungesehen): +0.21 R, Treffer 25 %, PF 1.33, n=20**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -0.17 R, Treffer 42 %, PF 0.51, n=12

## Plan

Wenn die Lesart (`python3 -m chartreader HYPE`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **Paper-Test (klein)**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
