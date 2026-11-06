# HYPE: Plan

Status: **Paper-Test (klein)**. Stand 2026-11-06 22:58.

## Wenn-Dann-Regeln

- Einstiegsebene: **1h** (Kontext: 4h und 1d)
- Zählende Ereignisse: Strukturbrüche (bos, bos_volume, choch)
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2, 1h 1; je Ereignis 3, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 59,890 $ / Verkäufer 25,913 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader HYPE --log`.

## Aktuelle Lesart

```
=== HYPE  Kurs 78.557 ===
1d  Seitwärts/ohne klare Struktur; Kurs unter EMA50, über EMA200; RSI 39.2; Schwankung 100. Perzentil
     Unterstützung 74.357–76.021 (3x) | Widerstand 82.472–89.771 (7x)
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 37.3; Schwankung 67. Perzentil
     Unterstützung 74.357–78.829 (11x) | Widerstand 80.356–81 (3x)
1h  Aufwärtstrend (höhere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 44.7; Schwankung 30. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 78.23–78.23 (1x) | Widerstand 78.23–78.23 (1x)
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
15m Aufwärtstrend (höhere Hochs und Tiefs); Kurs über EMA50, unter EMA200; RSI 50.6; Schwankung 26. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 77.04–77.329 (4x) | Widerstand 79.365–79.365 (1x)
Kontext: Funding +0.0013 %/h, offenes Volumen 1753 Mio $, Orderbuch Käufer +66 %, Spread 0.001 %
Punkte: Long 1.5 | Short 0  ->  Tendenz: NEUTRAL
  long: 1h: Aufwärtstrend (+1); 15m: Aufwärtstrend (+0.5)
PLAN: keiner (Tendenz neutral)
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
