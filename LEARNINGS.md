# LEARNINGS.md: Messprotokoll (neueste Einträge unten)

Regel: Jede Messung kommt hier hinein, auch negative. Zahlen netto nach Kosten (Gebühr 0,045 % + Slippage 0,02 % je Seite, Funding).

## 2026-11-06: Ausgangslage und erste Messungen

**Live-Ergebnis Paper (Autrionex, Projekt Claude-1):** Stündliche/Kurzfrist-Wetten haben 183 $ verloren (ZEC-Short +27 $, LIT-Long −38 $, PUMP-Long −162 $,
Gebühren ca. 21 $). Konto von 1.000 auf 817 $.

**Backtests (Hyperliquid-Kerzen, Training 60 % / Test 40 %):**
- 1h-Strategien (Rücksetzer, Ausbruch, feste Ziele) auf 14 Coins: alle im Test negativ, bis −21 % bei 0,5 % Risiko. Gebühren fressen den Vorteil.
- 5m-Ausbrüche auf 18 liquiden Coins: alle im Test negativ (bester Wert −0,09 % je Trade).
- 5m-Ausbrüche auf 6 Meme-Perps (PUMP, FARTCOIN, CASHCAT, USELESS, PONS, DOGE): Mitgehen Ø −0,19 %, Dagegen Ø −0,12 % je Trade. Kein Vorteil.
- **4h-Trendfolge K** (Donchian-55-Ausbruch in Richtung 1d-Trend, Trail 4 ATR) auf BTC ETH SOL XRP DOGE NEAR UNI: 229 Trades über 2,2 Jahre, Ø +0,10 R, Trefferquote 39 %,
  Training PF 1,15, Test PF 1,39. Der einzige gemessene Vorteil, aber schwach belegt. Details: `docs/strategie_k_trendfolge.md`.
- Hinweis Survivorship-Bias: Coins, die heute groß sind (HYPE, ZEC, PUMP), ließen Longs gut aussehen. Danach nur etablierte Coins verwendet.

**Neu gebaut:** `chartreader` (Lesart auf 1d/4h/1h/15m), `research/event_study.py`, `research/confluence.py`, Forward-Journal.

**Eventstudie 4h (14 Coins, Horizonte 12/24 Kerzen):** Von 16 Signalen bestehen 5 die Schwelle (Training UND Test über Zufall + 0,05 %) bei Horizont 24:
bos_volume:short, choch:long, rsi_divergence:long, squeeze_break:long, sweep_reclaim:short. Die Vorteile sind klein (0,1 bis 0,5 %) und viele Mittelwerte im Test negativ.
**Eventstudie 1h:** bestehen bos_volume:long (H24), sweep_reclaim:short (H12), zone_rejection:short (H12).
**Schnittmenge 1h und 4h:** nur `sweep_reclaim:short`, und selbst das nur relativ zum Zufall (1h Test −0,28 % absolut gegen −0,36 % Zufall).
Auswertung: Bei 16 Signalen × 2 Horizonten × 2 Zeitebenen sind einige Treffer durch Zufall zu erwarten. **Kein Signal gilt als bestätigt.**

**Zusammenspiel (1h-Signal + gleichgerichteter 4h-Trend, Horizont 24):** bos_volume:long (Test +1,31 %, t=+1,4) und choch:long (+1,38 %, t=+1,5) über dem Zufall
(+0,71 %) im Aufwärtstrend; Training aber nur +0,18 % / +0,16 %. rsi_divergence:long: Test +2,06 % (t=+2,2), Training −0,50 %. Nicht belastbar. Short-Signale im 4h-Abwärtstrend
liegen im Test unter dem Zufall (bos:short −1,52 %, t=−4,1: eher Gegenindikator, im Test Gegentrend-Phase).

### Fazit der ersten Runde
Kein Chart-Signal ist bestätigt. Die Struktur-Lesart ist solide gebaut und beschreibt den Chart, aber sie sagt die nächsten Kerzen nicht verlässlich voraus.
Bestätigt ist nur die langsame Trendfolge (K), und auch die nur schwach.

## 2026-11-06 (später): Vollständiger Strategie-Backtest und Einzeloptimierung je Coin

Aufbau: `research/strategy_bt.py` (Einstieg am Ereignis, Stop = Ungültigkeits-Niveau aus dem Chart, Ausstieg Zone / Swing-Trail / Strukturwechsel, Einheit R),
`research/optimize_coins.py` (576 Parametersätze je Coin über Einstiegsebene 1h/4h; Training 50 % / Validierung 25 % / Test 25 %). Ergebnisse in `coins/<COIN>/`.

Ergebnis im ungesehenen Test (gewählter Satz je Coin): BTC −0,40 R (n=21), ETH −0,41 (36), SOL +0,10 (33), XRP −0,31 (26), DOGE +1,01 (30), LINK +0,13 (23),
AVAX −0,31 (20), HYPE +0,21 (20). **Gesamt: 209 Trades, Ø +0,016 R, 4 von 8 Coins im Plus. Das ist praktisch null.** Robustheit der Auswahl (Anteil der bestandenen
Sätze, die im Test positiv bleiben): 0 bis 62 %, bei 5 von 8 Coins unter 50 %. Der gemeinsame Satz für alle Coins ist im Test ebenfalls ohne Vorteil und mit wenigen Trades.

Lehre: Einzeloptimierung aus vielen Parametern findet im Training und in der Validierung "Vorteile", die im Test verschwinden (typische Überanpassung). Der Test wurde jetzt
gesehen und darf nicht mehr zum Feintuning dienen. Weitere Bestätigung nur mit neuen Daten (Forward-Journal) und mit weniger Freiheitsgraden (statt 576 Sätzen wenige, vorab begründete).
Auffällig: Das Zonen-Verhalten ist bei den Coins kaum besser als Zufall (Zonen-Respekt um 46 bis 52 %, 50 % = Zufall); DOGE und LINK zeigen die höchste Trendfortsetzung nach Umkehr-Ereignissen.

## Nächste Hypothesen (Reihenfolge nach Erfolgsaussicht)
0. **Weniger Freiheitsgrade:** vorab begründete Regeln statt Gitter von 576 Sätzen; Walk-forward über mehrere Zeitfenster statt eines Splits.
1. **Regime-Filter auf K** (Effizienzverhältnis/ADX): Trendfolge nur in Trendphasen, nicht in Seitwärtsphasen.
2. **Längere Zeitebenen für Ereignisse** (4h/1d) mit Haltedauer in Tagen: dort sind Kosten relativ klein.
3. **Funding-Extreme als Gegenindikator** (Funding-Verlauf ist über die API abrufbar).
4. **Führende Coins:** BTC-Impuls → Altcoin-Reaktion mit Verzögerung (5m/15m), Kosten prüfen.
5. **Tageszeit/Wochentag-Effekte** (Liquiditätsfenster).
6. **Kombination vieler schwacher Signale** (Punktesystem mit gelernten Gewichten statt fester Werte), nur mit Out-of-Sample-Test.
7. **Eigene Ideen des Besitzers:** Muster, die er im Chart liest (z. B. bestimmte Formationen, Wyckoff, Elliott-Wellen, Orderflow). Jede Idee wird als Ereignis codiert und nach Schritt 3 getestet.

## Ideen vom Besitzer (hier eintragen, dann testen)
- (offen)
