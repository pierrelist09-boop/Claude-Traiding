# LINK: Plan

Status: **Paper-Test (klein)**. Stand 2026-11-06 22:57.

## Wenn-Dann-Regeln

- Einstiegsebene: **4h** (Kontext: 1d)
- Zählende Ereignisse: alle Ereignisse
- Punkteschwelle 6 (Trendpunkte: 1d 3, 4h 2; je Ereignis 1.5, höchstens zwei)
- Stop (Ungültigkeit): letzter bestätigter Swing ± 0.75 ATR Puffer
- Ausstieg: Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch

**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).
**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.

## Checkliste vor jedem Einstieg

1. Orderbuch-Tiefe prüfen (aktuell Käufer 168,688 $ / Verkäufer 120,253 $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.
2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.
3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).
4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader LINK --log`.

## Aktuelle Lesart

```
=== LINK  Kurs 10.923 ===
1d  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 38.3; Schwankung 75. Perzentil
     Unterstützung 9.7456–9.7456 (1x) | Widerstand 11.526–11.526 (1x)
4h  Abwärtstrend (tiefere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 43.7; Schwankung 76. Perzentil
     Unterstützung 10.5–10.623 (2x) | Widerstand 10.993–10.993 (1x)
     Ereignis: LONG – RSI-Divergenz am neuen Swing [kandidat], vor 2 Kerzen
     Ereignis: SHORT – Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
     Ereignis: SHORT – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 0 Kerzen
1h  Aufwärtstrend (höhere Hochs und Tiefs); Kurs unter EMA50, unter EMA200; RSI 46.0; Schwankung 50. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 10.792–10.792 (1x) | Widerstand 10.939–11.045 (6x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
     Ereignis: LONG – Rücksetzer mit Ablehnungs-Kerze an einer Zone [info], vor 1 Kerzen
15m Abwärtstrend (tiefere Hochs und Tiefs); Kurs über EMA50, unter EMA200; RSI 52.5; Schwankung 14. Perzentil; Bollinger-Spanne eng (Ausbruch möglich)
     Unterstützung 10.773–10.857 (13x) | Widerstand 10.909–10.978 (7x)
     Ereignis: LONG – Ablehnungs-Kerze an einer Zone [info], vor 2 Kerzen
Kontext: Funding +0.0013 %/h, offenes Volumen 53 Mio $, Orderbuch Käufer +22 %, Spread 0.009 %
Punkte: Long 1.75 | Short 5.5  ->  Tendenz: SHORT
  long: 4h: RSI-Divergenz am neuen Swing (kandidat, +0.75); 1h: Aufwärtstrend (+1)
  short: 1d: Abwärtstrend (+3); 4h: Abwärtstrend (+2); 15m: Abwärtstrend (+0.5)
PLAN SHORT: Auslöser 1h-Schluss unter 10.792; ungültig bei 1h-Schluss über 11.0772; Ziele [10.623]
Kein Signal ist statistisch bestätigt (siehe LEARNINGS.md): die Lesart beschreibt den Chart, sie beweist keinen Vorteil.
```
