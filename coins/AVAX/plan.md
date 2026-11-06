# AVAX: Plan

Status: **nur beobachten**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)
- Punkteschwelle 4.5 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): letzter bestätigter Swing ± 0.25 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 49,623 $ / Verkäufer 20,952 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader AVAX --log`.

## Aktuelle Lesart

```
=== AVAX  Kurs 8.396 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 35.1; Schwankung 64. Perzentil
     Unterstützung 6.6847–7.1697 (7x) | Widerstand 9.1598–9.2568 (2x)
     Ereignis: SHORT – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [kandidat], vor 1 Kerzen
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 46.5; Schwankung 68. Perzentil
     Unterstützung 8.2735–8.2801 (2x) | Widerstand 8.553–8.7596 (7x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 2 Kerzen
1h  Aufwärtstrend (höhere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 46.5; Schwankung 43. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 8.2735–8.3393 (5x) | Widerstand 8.4362–8.5064 (4x)
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 2 Kerzen
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: LONG – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
15m Abwärtstrend (tiefere Hochs und Tiefs); Kurs über EMA50, unter EMA200; RSI 51.0; Schwankung 15. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 8.2832–8.3606 (12x) | Widerstand 8.3946–8.3946 (1x)
Kontext: Funding +0.0009 %/h, offenes Volumen 16 Mio $, Orderbuch Käufer +31 %, Spread 0.027 %
Punkte: Long 1 | Short 4.25  ->  Tendenz: SHORT
  long: 1h: Aufwärtstrend (+1)
  short: 1d: Abwärtstrend (+3); 1d: Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen (kandidat, +0.75); 15m: Abwärtstrend (+0.5)
PLAN SHORT: Auslöser 1h-Schluss unter 8.299; ungültig bei 1h-Schluss über 8.52877; Ziele [8.2801]
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
