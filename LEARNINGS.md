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

## 2026-11-06 (spät): Vorab festgelegte Varianten der 4h-Trendfolge, drei Zeitfenster (`research/trend_variants.py`)

10 Coins (BTC ETH SOL XRP DOGE LINK AVAX NEAR UNI AAVE), 4h-Einstieg, Tagestrend-Filter, 8 vorab festgelegte Varianten, drei gleich lange Zeitfenster (2024-08 bis 2026-11), R netto nach Kosten:

| Variante | Fenster 1 | Fenster 2 | Fenster 3 | gesamt |
|---|---|---|---|---|
| A Donchian55 + ATR-Trail 4 (bisheriges K) | −0,04 R (117) | +0,29 (120) | −0,11 (97) | **+0,06 R (334)** |
| B Donchian55 + Swing-Trail (nur Chart) | −0,05 | +0,09 | −0,04 | +0,00 (379) |
| C nur Tagestrend-Ausstieg | −0,28 | +0,22 | +0,06 | −0,01 (210) |
| D A + Regime-Filter (Tages-Effizienz ≥ 0,25) | −0,06 | +0,17 | +0,71 | +0,18 (163) |
| E Donchian100 + ATR-Trail 5 | +0,02 (71) | +0,27 (83) | +0,30 (53) | **+0,19 (207), in allen 3 Fenstern positiv** |
| F A nur Long | +0,05 (68) | +0,17 (44) | +0,27 (17) | +0,12 (129), in allen 3 Fenstern positiv |
| G A + Volumen ≥ 1,3 | −0,01 | +0,30 | −0,05 | +0,09 (297) |
| H Donchian30 + ATR-Trail 4 | −0,01 | +0,22 | −0,15 | +0,03 (423) |

Auswertung: (1) K (A) ist breit gemessen nur +0,06 R und instabil (Fenster 2 trägt alles). Die frühere Zahl (+0,10 R auf 7 Coins, Test PF 1,39) war optimistischer. (2) **Langsamer ist besser** (E, D):
weniger Trades, Kosten fallen weniger ins Gewicht, die Aussage deckt sich mit der Theorie. (3) Mehrfachtest: Bei 8 Varianten × 3 Fenstern erwartet man zufällig etwa eine Variante, die in allen Fenstern positiv ist.
E und F sind deshalb **Kandidaten, kein Beweis**. (4) Der Chart-Trail (B) ist nicht besser als der ATR-Trail.

Konsequenz fürs Ziel: Bei Ø +0,06 bis +0,19 R pro Trade und rund 100 Trades im Jahr wächst ein Konto selbst mit hohem Einsatz langsam und mit großen Rückgängen. Ein Gewinn von +250 % ist so
keine Frage von Stunden oder Tagen, sondern von Jahren und Glück, und das Ergebnis ist nicht garantiert.

## 2026-11-06 (Nacht): Zwei-Jahres-Konto-Simulation (`research/simulation.py`, Bericht `simulation/ergebnis.md`, je Coin `coins/<COIN>/simulation.md`)

Chronologisch ab 2024-11-06, Konto 1.000 $, 8 Coins, höchstens 4 Positionen, Kosten und Funding drin. **Langsame Trendfolge E** (Donchian 100, Stop 4 ATR, Trail 5 ATR, nur mit Tagestrend):
2 % Risiko je Trade: 1.591 $ (+26 %/Jahr, Rückgang 16 %), 4 %: 2.143 $ (+47 %/Jahr, Rückgang 30 %), 6 %: 2.558 $ (Rückgang 40 %), 8 %: 3.136 $ (Rückgang 41 %). 112 Trades, 45 % Treffer.
Beitrag je Coin bei 4 %: XRP +347 $, BTC +304 $, LINK +168 $, HYPE +160 $, ETH +141 $, AVAX +53 $, DOGE −9 $, SOL −21 $. Buy&Hold gleichgewichtet +50 % in zwei Jahren (Einzelcoins −68 % bis +480 %).
E war in allen vier Halbjahren positiv (Ø R +0,17 / +0,24 / +0,11 / +0,50). Der Gewinn hängt an wenigen großen Trades (z. B. ein XRP-Long mit +6,8 R trägt 30 % des XRP-Beitrags): typisch Trendfolge.

Verbesserungsrunden (alle auf denselben zwei Jahren, also optimistisch):
1. Altes K (A): nur +15 %/Jahr bei 2 %. → langsamere Variante E übernommen.
2. Walk-forward-Auswahl (alle 91 Tage beste Strategie aus abgeschlossenen Trades, mit Pause für Verlierer-Coins): 2.061 $ bei 2 %, aber 53 % Rückgang. Schlägt E nicht. Auswahl erzeugt Rauschen.
3. Mehr Positionen (6/8) und mehr Coins (15): keine Verbesserung (Positionen laufen gleich), Rückgang steigt (15 Coins bei 4 %: 2.049 $ mit 45 % Rückgang).
4. Höherer Einsatz: nicht stetig (8 % → 3.136 $, 10 % → 2.814 $). Mehr Risiko kauft mehr Rückgang, nicht proportional mehr Gewinn.
5. Chart-Umkehr C1: schönes Endkonto (2.327 $ bei 1 %), aber instabil (nur 2 von 4 Halbjahren positiv, drei Coins tragen, XRP −465 $ und HYPE −374 $), 827 Trades mit 21 % Treffern, 39 bis 76 % Rückgang, Parameter mit Leck aus der Einzeloptimierung. Verworfen.

Bewertung: E ist die belastbarste Basis (beständig, gleichmäßig, geringer Rückgang), aber 142 Trades tragen die Aussage nur schwach, und 2025 war eine starke Trendphase. **Das Ziel +2.500 $ Gewinn wäre in diesen zwei Jahren nur bei 8 bis 10 % Risiko je Trade (Rückgang ~40 %) nahe gewesen. Eine Wiederholung ist nicht garantiert.**

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
