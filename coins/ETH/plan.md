# ETH: Plan

Status: **nur beobachten**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)
- Punkteschwelle 3 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): letzter bestätigter Swing ± 0.25 ATR Puffer
- Ausstieg: Schluss, sobald die Struktur der Einstiegsebene gegen die Position dreht

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 4,688,924 $ / Verkäufer 1,656,197 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader ETH --log`.

## Aktuelle Lesart

```
=== ETH  Kurs 2237.8 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 39.4; Schwankung 92. Perzentil
     Unterstützung 2173.1–2173.1 (1x) | Widerstand 2281.5–2406.7 (7x)
     Ereignis: LONG – erster Bruch gegen die Struktur (Trendwechsel) [kandidat], vor 1 Kerzen
     Ereignis: SHORT – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [kandidat], vor 0 Kerzen
4h  Seitwärts/ohne klare Struktur; Kurs unter EMA50, unter EMA200; RSI 40.4; Schwankung 87. Perzentil
     Unterstützung 2173.1–2173.1 (1x) | Widerstand 2344.4–2391 (6x)
1h  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 37.3; Schwankung 47. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 2225.7–2225.7 (1x) | Widerstand 2225.7–2225.7 (1x)
     Ereignis: LONG – RSI-Divergenz am neuen Swing [kandidat], vor 2 Kerzen
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
     Ereignis: SHORT – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
15m Aufwärtstrend (höhere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 48.2; Schwankung 1. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 2222.9–2228.9 (5x) | Widerstand 2232.9–2238 (7x)
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
     Ereignis: LONG – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
     Ereignis: LONG – Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen [info], vor 0 Kerzen
Kontext: Funding +0.0013 %/h, offenes Volumen 2192 Mio $, Orderbuch Käufer +70 %, Spread 0.009 %
Punkte: Long 2 | Short 5.5  ->  Tendenz: SHORT
  long: 1d: erster Bruch gegen die Struktur (Trendwechsel) (kandidat, +0.75); 1h: RSI-Divergenz am neuen Swing (kandidat, +0.75); 15m: Aufwärtstrend (+0.5)
  short: 1d: Abwärtstrend (+3); 1d: Liquiditätsjagd: Docht über/unter das Extrem, Schluss wieder innen (kandidat, +1.5); 1h: Abwärtstrend (+1)
PLAN SHORT: Auslöser 1h-Schluss unter 2208.4; ungültig bei 1h-Schluss über 2250.1; Ziele [2173.1]
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
