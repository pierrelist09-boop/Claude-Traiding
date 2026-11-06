# XRP: Plan

Status: **nur beobachten**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Strukturbrüche (bos, bos_volume, choch)
- Punkteschwelle 3 (Trendpunkte: 1d 3, 4h 2; je Ereignis 3, höchstens zwei)
- Stop (Ungültigkeit): Extrem der Signalkerze ± 0.75 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 1,091,581 $ / Verkäufer 1,049,571 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader XRP --log`.

## Aktuelle Lesart

```
=== XRP  Kurs 1.1789 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 35.6; Schwankung 35. Perzentil
     Unterstützung 1.1635–1.2 (4x) | Widerstand 1.2487–1.2554 (3x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 2 Kerzen
     Ereignis: LONG – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [info], vor 0 Kerzen
     Ereignis: SHORT – Ausbruch aus enger Bollinger-Spanne mit Volumen [info], vor 0 Kerzen
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 31.0; Schwankung 90. Perzentil
     keine Unterstützung | Widerstand 1.2–1.2 (1x)
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
1h  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 27.0; Schwankung 73. Perzentil
     keine Unterstützung | Widerstand 1.1737–1.1772 (2x)
     Ereignis: LONG – RSI-Divergenz am neuen Swing [kandidat], vor 2 Kerzen
     Ereignis: SHORT – Strukturbruch in Trendrichtung [info], vor 0 Kerzen
     Ereignis: SHORT – Strukturbruch in Trendrichtung mit Volumen [info], vor 0 Kerzen
15m Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 41.9; Schwankung 17. Perzentil
     Unterstützung 1.1719–1.1737 (2x) | Widerstand 1.1772–1.1813 (4x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
Kontext: Funding +0.0004 %/h, offenes Volumen 204 Mio $, Orderbuch Verkäufer +4 %, Spread 0.008 %
Punkte: Long 0.75 | Short 4.5  ->  Tendenz: SHORT
  long: 1h: RSI-Divergenz am neuen Swing (kandidat, +0.75)
  short: 1d: Abwärtstrend (+3); 1h: Abwärtstrend (+1); 15m: Abwärtstrend (+0.5)
PLAN SHORT: Auslöser 1h-Schluss unter 1.1737; ungültig bei 1h-Schluss über 1.1993; Ziele nächste Zonen prüfen
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
