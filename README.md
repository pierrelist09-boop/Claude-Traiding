# Claude-Traiding

Chart-Lese-Strategie für Hyperliquid-Perpetuals, entwickelt von Claude gemeinsam mit dem Besitzer. Ziel: Charts so genau wie möglich deuten und die
Strategie ständig mit Messungen verbessern. Gehandelt wird im Autrionex-Bot (Projekt Claude-1, zuerst nur Paper).

**Für Claude (zuerst lesen):** `STRATEGY.md` (wie ich lese und entscheide) → `LEARNINGS.md` (was gemessen wurde, nächste Hypothesen).

## Schnellstart
```bash
python3 -m chartreader BTC ETH --log        # Lesart mit Plan, speichert ins Forward-Journal
python3 -m chartreader ZEC --json           # maschinenlesbar
python3 research/event_study.py 1h 4h       # Wirkt jedes Chart-Signal? (Training/Test, Kosten)
python3 research/confluence.py              # Zusammenspiel 1h + 4h
python3 research/forward_check.py           # Was tat der Kurs nach meinen Lesarten?
python3 research/optimize_coins.py [COIN]   # Strategie je Coin testen und optimieren, schreibt coins/<COIN>/
python3 tests/test_chartreader.py           # Tests inkl. "kein Blick in die Zukunft"
```
Nur Standardbibliothek, keine Abhängigkeiten. Daten: öffentliche Hyperliquid-API, kein Schlüssel.

## Aufbau
- `chartreader/`: `series.py` (Indikatoren, bestätigte Swings), `structure.py` (Trend, Zonen), `events.py` (Chart-Ereignisse),
  `reader.py` (Lesart + Plan), `evidence.json` (Beweislage je Signal), `journal.py` (Forward-Journal).
- `research/`: Eventstudie, Zusammenspiel, Forward-Check; Ergebnisse in `research/results/`.
- `coins/`: ein Ordner je Coin (BTC ETH SOL XRP DOGE LINK AVAX HYPE) mit Steckbrief, Ergebnis, Plan; Übersicht in `coins/README.md`.
- `simulation/`: Zwei-Jahres-Konto-Simulation (`ergebnis.md`, `trades_E_4pct.csv`); je Coin `coins/<COIN>/simulation.md`. Skripte `research/simulation.py`, `research/simulation_report.py`.
- `docs/strategie_k_trendfolge.md`: die bisher einzige gemessene Strategie (4h-Trendfolge).
- `journal/readings.jsonl`: gespeicherte Lesarten.

## Grundsätze
- Kein Blick in die Zukunft: dieselbe Erkennung läuft in der Forschung und live (Test sichert das).
- Jede Messung wird protokolliert, auch negative. Ein Signal gilt erst als bestätigt nach Training + Test + mehreren Zeitebenen + Forward-Journal.
- Der Plan nennt Chart-Niveaus (Auslöser, Ungültigkeit, Ziele). Der Bot setzt als Stop den Ungültigkeits-Kurs; ohne Stop wird nicht gehandelt (Sicherheit, bei Echtgeld zwingend).
- Paper-Ergebnisse auf dünnen Büchern sind unecht: vor dem Handeln Tiefe prüfen (`context`).
