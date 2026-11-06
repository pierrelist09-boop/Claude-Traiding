# Claude-1: Regelwerk (Strategie K, 4h-Trendfolge)

Claude (das Modell) handelt in Claude-1 selbst, alle 4 Stunden kurz nach dem Schluss der 4h-Kerze (00, 04, 08, 12, 16, 20 Uhr
UTC, jeweils um :07). Die Regeln rechnet `tools/claude1_round.py` deterministisch aus, Claude prüft die Vorschläge, schreibt
die Analyse und reicht sie ein. Der Bot (`app/claude1`) prüft jedes Signal gegen seine Limits und überwacht Stop-Loss alle
5 Sekunden.

## Warum diese Strategie (Backtest `tools/claude1_backtest.py`)

Hyperliquid-Kerzen, Gebühren 0,045 % je Seite, Slippage 0,02 %, Funding eingerechnet; erste 60 % der Zeit Training, letzte
40 % ungesehener Test; nur etablierte Coins (BTC ETH SOL XRP DOGE NEAR UNI), weil neue Coins den Test durch Survivorship-Bias
verzerren.

| Variante | Test (ungesehen) |
|---|---|
| Alle 1h-Varianten (Rücksetzer, Ausbruch, feste Ziele) | klar negativ, bis minus 21 % bei 0,5 % Risiko: Gebühren fressen den Vorteil |
| 4h Rücksetzer, 4h Ausbruch 20 | im Training knapp positiv, im Test mit etablierten Coins um null oder negativ |
| **K: 4h Ausbruch 55, Trail 4 ATR** | **Training PF 1,15, Test PF 1,39, Ø +0,17 R je Trade, 92 Trades, Long und Short im Plus, 5 von 7 Coins im Plus** |

**Ehrlich:** 92 Test-Trades sind statistisch dünn (Ø 0,17 R bei Streuung von etwa 1,5 R: nicht signifikant). K ist der beste
Kandidat und deckt sich mit der bekannten Wirkung von Trendfolge, aber kein bewiesener Vorteil. Typisch sind niedrige
Trefferquote (etwa 40 %), lange Verlustserien und wenige große Gewinne. Der größte Rückgang im Test war 18 R, bei 1 %
Risiko wären das etwa 18 % des Kontos. Nach 30 echten Paper-Trades wird neu gemessen.

## Regeln

- **Trend (1d):** Long, wenn Tagesschluss > EMA50 > EMA200 und RSI < 75. Short spiegelbildlich (RSI > 25). Sonst kein Trade.
- **Einstieg (4h):** Der letzte geschlossene 4h-Schluss liegt über dem höchsten Hoch der 55 Kerzen davor (Short: unter dem
  tiefsten Tief), in Richtung des Tagestrends. Nur wenn diese Kerze höchstens 90 Minuten her geschlossen hat.
- **Stop:** 3 × ATR(4h) vom Kurs, mindestens 1 %. Kein festes Ziel.
- **Nachziehen:** Stop = höchstes Hoch seit Einstieg − 4 × ATR(4h) (Short: tiefstes Tief + 4 × ATR). Nur enger, nie lockerer.
- **Ausstieg:** Tagesschluss auf der falschen Seite der EMA50.
- **Größe:** Risiko 4 % des Kontos bis zum Stop (`risk_pct` 0,04), Hebel 3. Höchstens 4 Positionen. (Auftrag des Besitzers: Ziel +2.500 $ ohne Zeitlimit. Monte-Carlo über 229 K-Trades: bei 5 % Risiko erreicht man das Ziel in 2 Jahren mit 34 % Chance bei 11 % Risiko, die Schutzgrenze zu reißen; bei 1 % praktisch nie. Größter historischer Rückgang bei 5 % Risiko: 61 %.) Kein neuer Einstieg bei
  Verlust heute ab 5 % (der Bot sperrt bei 25 %).
- Pro Coin nur eine Position, nie aufstocken.

## Disziplin

Regeln nicht für knappe Fälle verbiegen und keine Signale aus Gefühl erfinden. Ein vorgeschlagenes Signal darf nur bei
Auffälligkeiten abgelehnt werden (Bot-Fehler, unplausible Daten, Börse gestört), mit Begründung in der Analyse.
Änderungen an der Strategie nur nach einem neuen Backtest.

## Echtgeld

Echtgeld schaltet nur der Besitzer im Panel frei (Modus Live). Dann gelten dieselben Regeln und Limits; der Modus wird in
jeder Meldung genannt. Stop-Loss ist keine Order an der Börse, sondern wird vom laufenden Bot ausgelöst: fällt der Server aus,
greift er nicht.
