# SOL: Plan

Status: **Paper-Test (klein)**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **1h** (Kontext: 4h und 1d)
- Zählende Ereignisse: Ablehnungs-Kerzen an Zonen
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2, 1h 1; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 110,398 $ / Verkäufer 424,932 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader SOL --log`.

## Aktuelle Lesart

```
=== SOL  Kurs 90.28 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 28.7; Schwankung 59. Perzentil
     Unterstützung 73.329–77.822 (7x) | Widerstand 95.75–100.34 (5x)
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
     Ereignis: SHORT – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 39.9; Schwankung 85. Perzentil
     Unterstützung 88.242–88.242 (1x) | Widerstand 89.848–90.827 (2x)
     Ereignis: LONG – RSI-Divergenz am neuen Swing [kandidat], vor 2 Kerzen
1h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 40.4; Schwankung 50. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 89.605–89.848 (3x) | Widerstand 90.398–91.57 (5x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: LONG – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
15m Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 46.9; Schwankung 22. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 89.45–90.015 (12x) | Widerstand 90.237–90.57 (7x)
Kontext: Funding -0.0011 %/h, offenes Volumen 515 Mio $, Orderbuch Verkäufer +87 %, Spread 0.010 %
Punkte: Long 0.75 | Short 3  ->  Tendenz: NEUTRAL
  long: 4h: RSI-Divergenz am neuen Swing (kandidat, +0.75)
  short: 1d: Abwärtstrend (+3)
PLAN: keiner (Tendenz neutral)
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
