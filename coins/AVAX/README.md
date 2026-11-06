# AVAX: Steckbrief, Ergebnis, Plan

Stand 2026-11-06 22:57. Daten: Hyperliquid, 4999 4h-Kerzen ab 2024-07-26, 4999 1h-Kerzen, 2235 Tageskerzen.

**Empfehlung: nur beobachten**

## Feinheiten des Coins

- Schwankung (Median ATR): 1h 0.91 % | 4h 2.42 % | 1d 7.67 %
- Gleichlauf mit BTC (1h-Renditen): 0.7
- Trendneigung 4h: Autokorrelation -0.02 (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in 60 % der Zeit klare Struktur (auf 31 %, ab 29 %)
- Zonen-Respekt: nach 747 Ablehnungs-Kerzen an Zonen lief der Kurs in 49 % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)
- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer 49,623 $ / Verkäufer 20,952 $, Spread 0.0071 %, Tagesvolumen 6.3 Mio $, offenes Volumen 15.8 Mio $, Funding 0.00088 %/h

## Optimierung (Training / Validierung / ungesehener Test)

Von 576 Parametersätzen bestehen 29 Training und Validierung. Davon sind im Test 17 % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).

**Gewählter Satz:**

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)
- Punkteschwelle 4.5 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): letzter bestätigter Swing ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

- Training: +0.23 R, Treffer 26 %, PF 1.40, n=42
- Validierung: +0.32 R, Treffer 26 %, PF 1.52, n=19
- **Test (ungesehen): -0.31 R, Treffer 20 %, PF 0.50, n=20**
- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: -0.29 R, Treffer 45 %, PF 0.39, n=11

## Plan

Wenn die Lesart (`python3 -m chartreader AVAX`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:

1. Einstieg am Schluss der Signalkerze der Einstiegsebene.
2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.
3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.

Status: **nur beobachten**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung.
