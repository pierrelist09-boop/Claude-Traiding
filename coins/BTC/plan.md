# BTC: Plan

Status: **nur beobachten**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **1h** (Kontext: 4h und 1d)
- Zählende Ereignisse: alle Ereignisse
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2, 1h 1; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.75 ATR Puffer
- Ausstieg: Schluss, sobald die Struktur der Einstiegsebene gegen die Position dreht

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 2,167,412 $ / Verkäufer 929,818 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader BTC --log`.

## Aktuelle Lesart

```
=== BTC  Kurs 75904 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 38.5; Schwankung 94. Perzentil
     Unterstützung 66918–66918 (1x) | Widerstand 79184–82551 (8x)
     Ereignis: LONG – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [info], vor 1 Kerzen
     Ereignis: SHORT – Strukturbruch in Trendrichtung [info], vor 0 Kerzen
     Ereignis: SHORT – Strukturbruch in Trendrichtung mit Volumen [info], vor 0 Kerzen
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 38.4; Schwankung 91. Perzentil
     Unterstützung 75189–75687 (2x) | Widerstand 76264–76443 (3x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 2 Kerzen
     Ereignis: LONG – RSI-Divergenz am neuen Swing [kandidat], vor 2 Kerzen
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: LONG – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [info], vor 1 Kerzen
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
1h  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 41.3; Schwankung 56. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 75189–75687 (4x) | Widerstand 76342–76400 (3x)
     Ereignis: LONG – RSI-Divergenz am neuen Swing [kandidat], vor 2 Kerzen
15m Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 49.7; Schwankung 7. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 75684–75684 (1x) | Widerstand 75787–76155 (14x)
Kontext: Funding +0.0013 %/h, offenes Volumen 3216 Mio $, Orderbuch Verkäufer +5 %, Spread 0.001 %
Punkte: Long 1.5 | Short 4  ->  Tendenz: NEUTRAL
  long: 4h: RSI-Divergenz am neuen Swing (kandidat, +0.75); 1h: RSI-Divergenz am neuen Swing (kandidat, +0.75)
  short: 1d: Abwärtstrend (+3); 1h: Abwärtstrend (+1)
PLAN: keiner (Tendenz neutral)
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
