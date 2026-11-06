# STRATEGY.md: Chart-Lesestrategie von Claude (Version 0.1)

**Das ist die Datei, die ich (Claude) vor jeder Handelsentscheidung lese.** Sie beschreibt, wie ich einen Chart lese und daraus eine
Entscheidung ableite. Sie enthält bewusst keine Einsatz- oder Prozentregeln: Einsatz, Hebel und Limits setzt der Bot (Autrionex
`app/claude1`). Die Strategie liefert Richtung, Auslöser, Ungültigkeits-Niveau und Ziele als **Kurse aus dem Chart**.

> **Stand der Simulation (Nacht 2026-11-06):** Bisher trägt nur die langsame Trendfolge E (`simulation/ergebnis.md`): über zwei Jahre auf 8 Coins +26 bis +47 %/Jahr bei 16 bis 30 % Rückgang (2 bis 4 % Risiko), in allen vier Halbjahren positiv. Die Chart-Lesart (Ereignisse) liefert Kontext, aber keinen nachgewiesenen eigenen Vorteil.
>
> **Ehrliche Beweislage (Stand 2026-11-06):** Kein einzelnes Chart-Signal und kein Zusammenspiel hat sich bisher statistisch
> bestätigt (siehe `LEARNINGS.md`). Die Lesart beschreibt den Chart genau und nachvollziehbar, sie beweist keinen Vorteil.
> Der einzige bisher gemessene Vorteil gehört zur langsamen Trendfolge (`docs/strategie_k_trendfolge.md`). Diese Datei wird nach
> jeder Messung angepasst. Was nicht belegt ist, steht hier als "Kandidat" und nicht als Regel.

## 1. So nutze ich das Repo (Ablauf jeder Runde)

1. `python3 -m chartreader COIN --log`: Lesart ausgeben und im Forward-Journal speichern (Coins: BTC ETH SOL XRP DOGE NEAR UNI + gewünschte).
2. Lesart nach Abschnitt 2 und 3 deuten, Entscheidung begründen (Analyse auf Deutsch, 3 bis 6 Sätze).
3. Bei einem Plan: dem Bot Signal mit **Stop = Ungültigkeits-Kurs** und Ziel = erstes Ziel übergeben (`tools/claude1_submit.py` im Autrionex-Repo).
4. Regelmäßig `python3 research/forward_check.py` (was tat der Kurs nach meinen Lesarten?) und die Forschung wiederholen (Abschnitt 5).

## 2. Die Lesart (von oben nach unten)

| Ebene | Frage | Werkzeug |
|---|---|---|
| Kontext 1d, 4h | Wohin zeigt die Struktur? Höhere Hochs/Tiefs = Aufwärts, tiefere = Abwärts, sonst Seitwärts | `structure.trend_at` aus bestätigten Swings |
| Ort | Liegt der Kurs an einer Zone (Häufung von Swing-Extremen, je mehr Berührungen desto stärker)? | `structure.zones_at` |
| Auslöser 1h, 15m | Was tut der Kurs an diesem Ort? Ablehnungs-Kerze, Strukturbruch, Liquiditätsjagd, Divergenz, Ausbruch | `events.detect` |
| Bestätigung | Volumenschub (≥ 1,5-fach), gleiche Richtung auf mehreren Zeitebenen, Bollinger-Spanne eng vor dem Ausbruch | `Series.vr`, `bbw_rank` |
| Kontext Markt | Funding extrem (Gegenseite überfüllt), Orderbuch-Ungleichgewicht, Spread/Tiefe (Handelbarkeit!) | `data.context` |

Zeitebenen-Gewicht: 1d = 3, 4h = 2, 1h = 1, 15m = 0,5. Ein Ereignis zählt nach Beweislage (`chartreader/evidence.json`): bestätigt = 3,
Kandidat = 1,5, Info = 0; nur das Ereignis der letzten Kerze zählt voll, eine Kerze davor halb.

## 3. Entscheidung (v0.1)

- **Tendenz** = Punktedifferenz Long minus Short: ab +3 Long, ab −3 Short, sonst neutral = **kein Trade**.
- **Einstieg** erst, wenn der Auslöser erfüllt ist: 1h-Schluss über dem letzten Swing-Hoch (Long) bzw. unter dem letzten Swing-Tief (Short).
- **Ungültig** (= Stop-Kurs für den Bot): 1h-Schluss jenseits des letzten Swings auf der anderen Seite bzw. 0,25 ATR hinter der nächsten Zone.
- **Ziele:** nächste Zonen in Handelsrichtung (1h und 4h), über dem Auslöser (Long) bzw. darunter (Short).
- **Ausstieg** außer an Ziel/Ungültigkeit: Strukturwechsel gegen die Position auf 1h oder 4h (CHoCH), oder die Tendenz kippt auf neutral und die Position steht nicht im Gewinn.
- Handelbarkeit zuerst: bei dünnem Orderbuch (wenige tausend Dollar Tiefe) handle ich die Coin nicht, weil Paper-Fills dort nicht echt sind.

## 3b. Coin-spezifische Pläne

Für jeden Coin gibt es einen Ordner in `coins/<COIN>/` mit Steckbrief (Schwankung, Gleichlauf, Trendneigung, Handelbarkeit), Optimierungsergebnis (Training/Validierung/Test),
`plan.md` (Wenn-Dann-Regeln, Checkliste, aktuelle Lesart) und `params.json`. Stand der Einzeloptimierung: im Test Ø +0,016 R über alle Coins, also kein belastbarer Vorteil
(siehe `coins/README.md`). Empfehlungen dort ('Paper-Test', 'nur beobachten', 'nicht handeln') gelten nur für kleine Paper-Experimente, bis das Forward-Journal etwas bestätigt.

## 4. Ereignisse (Definition in `chartreader/events.py`)

`pullback_rejection`, `zone_rejection`, `bos`, `bos_volume`, `choch`, `sweep_reclaim`, `rsi_divergence`, `squeeze_break` (je Long/Short).
Beweislage je Signal: `chartreader/evidence.json` (aktuell nur "kandidat" oder "info").

## 5. Verbesserungsschleife (so wird die Strategie besser)

1. **Hypothese** formulieren (z. B. "Strukturbruch mit Volumen nur im Trend der höheren Ebene").
2. In `chartreader/events.py` als Ereignis bauen (kein Blick in die Zukunft, `tests/test_chartreader.py` muss grün bleiben).
3. `python3 research/event_study.py 1h 4h` und `python3 research/confluence.py`: Training (erste 60 %) und Test (letzte 40 %), Kosten 0,13 %, Vergleich gegen Zufall.
4. Ergebnis mit Zahlen in `LEARNINGS.md` eintragen, auch wenn es negativ ist.
5. `evidence.json` nur hochstufen, wenn: positiv in Training UND Test, auf mehreren Zeitebenen, t-Wert > 3 (Mehrfachtest-Korrektur: Es werden viele Signale getestet).
6. Mit dem Forward-Journal prüfen (`research/forward_check.py`): echte, ungesehene Daten. Erst danach zählt ein Signal als bestätigt.
7. Version in dieser Datei hochzählen, Änderung im Kopf von `LEARNINGS.md` vermerken.
