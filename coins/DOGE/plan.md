# DOGE: Plan

Status: **nur beobachten**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)
- Punkteschwelle 4.5 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 156,571 $ / Verkäufer 50,269 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader DOGE --log`.

## Aktuelle Lesart

```
=== DOGE  Kurs 0.072745 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 32.2; Schwankung 34. Perzentil
     Unterstützung 0.0678–0.069048 (4x) | Widerstand 0.071436–0.07603 (8x)
     Ereignis: SHORT – Strukturbruch in Trendrichtung [info], vor 0 Kerzen
     Ereignis: SHORT – Strukturbruch in Trendrichtung mit Volumen [info], vor 0 Kerzen
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 43.7; Schwankung 84. Perzentil
     Unterstützung 0.073164–0.073164 (1x) | Widerstand 0.073164–0.073164 (1x)
1h  Aufwärtstrend (höhere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 46.8; Schwankung 50. Perzentil
     Unterstützung 0.07194–0.072258 (2x) | Widerstand 0.072815–0.072815 (1x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: LONG – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
15m Abwärtstrend (tiefere Hochs und Tiefs); Kurs über EMA50, unter EMA200; RSI 47.5; Schwankung 8. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 0.072672–0.072672 (1x) | Widerstand 0.072672–0.072672 (1x)
     Ereignis: LONG – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [info], vor 0 Kerzen
Kontext: Funding +0.0013 %/h, offenes Volumen 70 Mio $, Orderbuch Verkäufer +20 %, Spread 0.001 %
Punkte: Long 1 | Short 3.5  ->  Tendenz: NEUTRAL
  long: 1h: Aufwärtstrend (+1)
  short: 1d: Abwärtstrend (+3); 15m: Abwärtstrend (+0.5)
PLAN: keiner (Tendenz neutral)
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
