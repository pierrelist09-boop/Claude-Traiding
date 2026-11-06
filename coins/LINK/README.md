# LINK: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 5000 4h-Kerzen ab 2024-07-26, 5000 1h-Kerzen, 2267 Tageskerzen.

**Empfehlung: Paper-Test (klein)**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.87 % | 4h 2.32 % | 1d 7.03 %
- Gleichlauf mit BTC (1h-Renditen): 0.76
- Trendneigung 4h: Autokorrelation 0.001 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 61 % der Zeit klare Struktur (auf 31 %, ab 30 %)
- Zonen-Respekt: nach 784 Ablehnungs-Kerzen an Zonen lief der Kurs in 46 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 168,688 $ / Verkäufer 120,253 $, Spread 0.0549 %, Tagesvolumen 8.2 Mio $, offenes Volumen 53.2 Mio $, Funding 0.00125 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 118 Training und Validierung. Davon sind im Test 62 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: alle Ereignisse
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): letzter bestätigter Swing ± 0.75 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

- Training: +0.74 R, Treffer 26 %, PF 3.00, n=31
- Validierung: +0.86 R, Treffer 30 %, PF 3.18, n=20
- **Test (ungesehen): +0.13 R, Treffer 26 %, PF 1.32, n=23**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -0.32 R, Treffer 50 %, PF 0.44, n=4

## Plan

Wenn die Lesart (`python3 -m chartreader LINK`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **Paper-Test (klein)**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
