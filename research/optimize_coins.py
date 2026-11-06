#!/usr/bin/env python3
"""Testet die Chart-Strategie auf der Vergangenheit und optimiert sie je Coin einzeln; schreibt pro Coin einen Ordner nach coins/<COIN>/.

Aufruf: python3 research/optimize_coins.py [COIN ...]   (Standard: BTC ETH SOL XRP DOGE LINK AVAX HYPE)

Ablauf je Coin: 288 Parametersätze x Einstiegsebenen 1h/4h. Zeit wird geteilt in Training (erste 50 %), Validierung (nächste 25 %) und Test
(letzte 25 %). Ein Satz kommt nur in Frage, wenn er in Training UND Validierung positiv ist (mindestens 20 bzw. 8 Trades); der beste nach
min(Training, Validierung) wird gewählt. Der Test wird erst danach angesehen. Dazu: wie viele der bestandenen Sätze sind im Test positiv
(Robustheit der Auswahl), und ein gemeinsamer Parametersatz für alle Coins als Vergleich (bringt Einzeloptimierung etwas?)."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chartreader import data
from chartreader.series import Series
from research.coin_profile import profile, returns
from research.strategy_bt import Prep, combos, metrics, simulate, split

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COINS = "BTC ETH SOL XRP DOGE LINK AVAX HYPE".split()
MIN = {"train": 20, "val": 8}


def evaluate(coin):
    S = {tf: Series(data.candles(coin, tf, 5000, use_cache=True)) for tf in ("1h", "4h", "1d")}
    out = {}
    for tf, htfs in (("1h", {"4h": S["4h"], "1d": S["1d"]}), ("4h", {"1d": S["1d"]})):
        P = Prep(tf, S[tf], htfs)
        t0, t1 = S[tf].t[210], S[tf].t[-1]
        out[tf] = [(p, *[metrics(x) for x in split(simulate(P, p), t0, t1)]) for p in combos()]
    return out


def passes(tr, va):
    return tr["n"] >= MIN["train"] and va["n"] >= MIN["val"] and tr["mean"] > 0 and va["mean"] > 0


def pick(rows):
    """rows: [(tf, p, tr, va, te)] -> (bester, alle bestandenen)"""
    good = [r for r in rows if passes(r[2], r[3])]
    good.sort(key=lambda r: -min(r[2]["mean"], r[3]["mean"]))
    return (good[0] if good else None), good


def fmt(m):
    return f"{m['mean']:+.2f} R, Treffer {m['win'] * 100:.0f} %, PF {m['pf']:.2f}, n={m['n']}"


def describe(tf, p):
    sets = {"all": "alle Ereignisse", "structure": "Strukturbrüche (bos, bos_volume, choch)", "rejection": "Ablehnungs-Kerzen an Zonen",
            "reversal": "Umkehr-Ereignisse (sweep_reclaim, rsi_divergence, choch)"}
    ex = {"zone": "nächste Gegenzone (mindestens 1 R entfernt)", "trail": "Stop wandert auf das letzte bestätigte Swing-Tief/-Hoch",
          "flip": "Schluss, sobald die Struktur der Einstiegsebene gegen die Position dreht"}
    ref = "letzter bestätigter Swing" if p["stop_ref"] == "swing" else "Extrem der Signalkerze"
    return [f"- Einstiegsebene: **{tf}** (Kontext: " + ("4h und 1d" if tf == "1h" else "1d") + ")",
            f"- Zählende Ereignisse: {sets[p['ev_set']]}",
            f"- Punkteschwelle {p['T']:g} (Trendpunkte: " + ("1d 3, 4h 2, 1h 1" if tf == "1h" else "1d 3, 4h 2") + f"; je Ereignis {p['ev_w']:g}, höchstens zwei)",
            f"- Stop (Ungültigkeit): {ref} ± {p['k']:g} ATR Puffer", f"- Ausstieg: {ex[p['exit']]}"]


def main():
    coins = sys.argv[1:] or COINS
    btc = returns(Series(data.candles("BTC", "1h", 5000, use_cache=True)))
    results, profiles = {}, {}
    for coin in coins:
        t = time.time()
        results[coin] = evaluate(coin)
        profiles[coin] = profile(coin, btc)
        print(f"{coin}: {sum(len(v) for v in results[coin].values())} Sätze getestet ({time.time() - t:.0f}s)", flush=True)
    # gemeinsamer Parametersatz: gepoolt über alle Coins je (Ebene, Satz)
    pooled = {}
    for coin, byt in results.items():
        for tf, rows in byt.items():
            for p, tr, va, te in rows:
                key = (tf, json.dumps(p, sort_keys=True))
                a = pooled.setdefault(key, {"tr": [], "va": [], "te": []})
                a["tr"].append(tr), a["va"].append(va), a["te"].append((coin, te))
    def pool(ms):
        n = sum(m["n"] for m in ms)
        return {"n": n, "mean": sum(m["mean"] * m["n"] for m in ms) / n if n else 0.0}
    gbest, gscore = None, -9
    for key, a in pooled.items():
        tr, va = pool(a["tr"]), pool(a["va"])
        if tr["n"] >= 80 and va["n"] >= 30 and tr["mean"] > 0 and va["mean"] > 0 and min(tr["mean"], va["mean"]) > gscore:
            gbest, gscore = key, min(tr["mean"], va["mean"])
    summary = {}
    for coin in coins:
        rows = [(tf, p, tr, va, te) for tf, lst in results[coin].items() for p, tr, va, te in lst]
        best, good = pick(rows)
        pos_test = sum(1 for r in good if r[4]["n"] >= 5 and r[4]["mean"] > 0)
        rob = pos_test / len(good) if good else 0.0
        gl = None
        if gbest:
            tf, ps = gbest[0], json.loads(gbest[1])
            gl = next(((tf, p, tr, va, te) for tf2, p, tr, va, te in rows if tf2 == tf and p == ps), None)
        verdict = "nicht handeln"
        if best:
            te = best[4]
            verdict = "Paper-Test (klein)" if te["n"] >= 15 and te["mean"] > 0 and rob >= 0.5 else "nur beobachten"
        summary[coin] = {"best": best, "good": good, "robust": rob, "global": gl, "verdict": verdict, "n_pass": len(good), "n_total": len(rows)}
        write_coin(coin, profiles[coin], summary[coin], rows)
    write_overview(summary, profiles, gbest)


def write_coin(coin, prof, s, rows):
    d = os.path.join(ROOT, "coins", coin)
    os.makedirs(d, exist_ok=True)
    best, good = s["best"], s["good"]
    now = time.strftime("%Y-%m-%d %H:%M")
    json.dump({"coin": coin, "stand": now, "verdict": s["verdict"], "bestanden": s["n_pass"], "getestet": s["n_total"], "robustheit": round(s["robust"], 2),
               "profil": prof, "gewaehlt": None if not best else {"ebene": best[0], "params": best[1], "train": best[2], "val": best[3], "test": best[4]},
               "gemeinsamer_satz_test": None if not s["global"] else s["global"][4]}, open(os.path.join(d, "params.json"), "w"), indent=1, ensure_ascii=False)
    L = [f"# {coin}: Steckbrief, Ergebnis, Plan", "", f"Stand {now}. Daten: Hyperliquid, {prof['kerzen_4h']} 4h-Kerzen ab {prof['von']}, {prof['kerzen_1h']} 1h-Kerzen, {prof['kerzen_1d']} Tageskerzen.", "",
         f"**Empfehlung: {s['verdict']}**", "", "## Feinheiten des Coins", "",
         f"- Schwankung (Median ATR): 1h {prof['atr_pct_1h']} % | 4h {prof['atr_pct_4h']} % | 1d {prof['atr_pct_1d']} %",
         f"- Gleichlauf mit BTC (1h-Renditen): {prof.get('korrelation_btc_1h')}",
         f"- Trendneigung 4h: Autokorrelation {prof['autokorr_4h']} (über 0 = Trend setzt sich eher fort, unter 0 = kehrt eher um); in {prof['trend_anteil_4h'] * 100:.0f} % der Zeit klare Struktur (auf {prof['aufwaerts_4h'] * 100:.0f} %, ab {prof['abwaerts_4h'] * 100:.0f} %)",
         f"- Zonen-Respekt: nach {prof['zonen_ablehnungen']} Ablehnungs-Kerzen an Zonen lief der Kurs in {(prof['zonen_respekt'] or 0) * 100:.0f} % der Fälle 1 ATR in Richtung der Ablehnung, bevor er 1 ATR dagegen lief (50 % = Zufall)"]
    if "orderbuch_kaeufer_usd" in prof:
        L.append(f"- Handelbarkeit jetzt: Orderbuch (10 Stufen) Käufer {prof['orderbuch_kaeufer_usd']:,} $ / Verkäufer {prof['orderbuch_verkaeufer_usd']:,} $, Spread {prof['spread_pct']} %, Tagesvolumen {prof['tagesvolumen_mio']} Mio $, offenes Volumen {prof['offenes_volumen_mio']} Mio $, Funding {prof['funding_pro_stunde_pct']} %/h")
    L += ["", "## Optimierung (Training / Validierung / ungesehener Test)", ""]
    if best:
        tf, p, tr, va, te = best
        L += [f"Von {s['n_total']} Parametersätzen bestehen {s['n_pass']} Training und Validierung. Davon sind im Test {s['robust'] * 100:.0f} % positiv (Robustheit der Auswahl; unter 50 % heißt: die Auswahl war größtenteils Glück).", "",
              "**Gewählter Satz:**", ""] + describe(tf, p) + ["", f"- Training: {fmt(tr)}", f"- Validierung: {fmt(va)}", f"- **Test (ungesehen): {fmt(te)}**"]
        if s["global"]:
            g = s["global"]
            L.append(f"- Zum Vergleich der gemeinsame Satz für alle Coins im Test dieses Coins: {fmt(g[4])}")
    else:
        L += [f"Von {s['n_total']} Parametersätzen besteht **keiner** Training und Validierung zugleich. Für diesen Coin wurde kein Vorteil gefunden: nicht handeln."]
    L += ["", "## Plan", ""]
    if best and s["verdict"] != "nicht handeln":
        L += ["Wenn die Lesart (`python3 -m chartreader " + coin + "`) ein Ereignis der gewählten Art in Trendrichtung zeigt und die Punkteschwelle erreicht ist:", "",
              "1. Einstieg am Schluss der Signalkerze der Einstiegsebene.", "2. Stop = Ungültigkeits-Niveau (siehe oben), vorher dem Bot als Stop-Kurs mitgeben.",
              "3. Ausstieg nach der gewählten Regel; kein fester Prozentwert.", "",
              f"Status: **{s['verdict']}**. Der Test ist die ehrlichste Zahl; erst das Forward-Journal (`research/forward_check.py`) gibt ungesehene Bestätigung."]
    else:
        L += ["Kein Plan. Der Coin wird beobachtet, die Lesart (`python3 -m chartreader " + coin + "`) dient nur als Kontext."]
    open(os.path.join(d, "README.md"), "w").write("\n".join(L) + "\n")
    write_plan(d, coin, prof, s)
    B = [f"# {coin}: Backtest-Tabellen", "", "Beste 10 Sätze nach min(Training, Validierung), mit Test:", "", "| Ebene | Ereignisse | Schwelle | Gew. | Puffer | Stop | Ausstieg | Training | Validierung | Test |", "|---|---|---|---|---|---|---|---|---|---|"]
    for tf, p, tr, va, te in good[:10]:
        B.append(f"| {tf} | {p['ev_set']} | {p['T']:g} | {p['ev_w']:g} | {p['k']:g} | {p['stop_ref']} | {p['exit']} | {tr['mean']:+.2f}R n={tr['n']} | {va['mean']:+.2f}R n={va['n']} | {te['mean']:+.2f}R n={te['n']} |")
    if not good:
        B.append("| – | keiner besteht | | | | | | | | |")
    open(os.path.join(d, "backtest.md"), "w").write("\n".join(B) + "\n")


def write_plan(d, coin, prof, s):
    """plan.md: Wenn-Dann-Regeln, Checkliste und die aktuelle Lesart (Stand der Erzeugung)."""
    from chartreader.reader import explain, read
    best = s["best"]
    L = [f"# {coin}: Plan", "", f"Status: **{s['verdict']}**. Stand {time.strftime('%Y-%m-%d %H:%M')}.", ""]
    if best and s["verdict"] != "nicht handeln":
        tf, p, tr, va, te = best
        L += ["## Wenn-Dann-Regeln", ""] + describe(tf, p) + ["",
              "**Long:** Ereignis der gewählten Art in Long-Richtung an der Kerze, die gerade geschlossen hat, und Punkte ≥ Schwelle (Trend der Ebenen zählt mit).",
              "**Short:** spiegelbildlich. **Sonst: nichts tun.** Gegenläufige Signale in einer offenen Position werden nicht gehandelt.", ""]
    else:
        L += ["## Regeln", "", "Für diesen Coin wurde kein belastbarer Vorteil gefunden. Nicht handeln; die Lesart nur als Kontext nutzen.", ""]
    L += ["## Checkliste vor jedem Einstieg", "",
          f"1. Orderbuch-Tiefe prüfen (aktuell Käufer {prof.get('orderbuch_kaeufer_usd', '?'):,} $ / Verkäufer {prof.get('orderbuch_verkaeufer_usd', '?'):,} $ in 10 Stufen): Position höchstens ein Viertel der Tiefe.",
          "2. Stop-Kurs aus dem Chart bestimmen (Ungültigkeits-Niveau der Regel) und dem Bot mitgeben, ohne Stop wird nicht gehandelt.",
          "3. Nicht zwei Positionen mit gleichem Marktbild gleichzeitig (BTC, ETH, SOL laufen oft gleich).",
          "4. Lesart ins Forward-Journal schreiben: `python3 -m chartreader " + coin + " --log`.", "", "## Aktuelle Lesart", "", "```"]
    try:
        L.append(explain(read(coin)))
    except Exception as e:  # noqa: BLE001
        L.append(f"(Lesart nicht verfügbar: {e})")
    L += ["```", ""]
    open(os.path.join(d, "plan.md"), "w").write("\n".join(L))


def write_overview(summary, profiles, gbest):
    L = ["# coins/: Ergebnis je Coin", "", f"Stand {time.strftime('%Y-%m-%d %H:%M')}. Chart-Strategie (STRATEGY.md) einzeln je Coin optimiert, Training 50 % / Validierung 25 % / Test 25 % (ungesehen). R = Abstand Einstieg bis Stop, nach Kosten.", "",
         "| Coin | Empfehlung | bestanden | Robustheit | gewählt | Test | gemeinsamer Satz (Test) |", "|---|---|---|---|---|---|---|"]
    for coin, s in summary.items():
        b = s["best"]
        L.append(f"| [{coin}](./{coin}/README.md) | {s['verdict']} | {s['n_pass']}/{s['n_total']} | {s['robust'] * 100:.0f} % | " +
                 (f"{b[0]} {b[1]['ev_set']} {b[1]['exit']} | {b[4]['mean']:+.2f} R (n={b[4]['n']}) | " if b else "– | – | ") + (f"{s['global'][4]['mean']:+.2f} R (n={s['global'][4]['n']})" if s["global"] else "–") + " |")
    sel = [(c, s["best"][4]) for c, s in summary.items() if s["best"]]
    n = sum(m["n"] for _, m in sel)
    if n:
        pos = sum(1 for _, m in sel if m["mean"] > 0)
        L += ["", f"**Gesamt über alle Coins im ungesehenen Test (gewählte Sätze):** {n} Trades, Ø {sum(m['mean'] * m['n'] for _, m in sel) / n:+.3f} R je Trade, {pos} von {len(sel)} Coins im Plus. "
              "Ein Durchschnitt nahe null heißt: Die Einzeloptimierung findet im Test keinen verlässlichen Vorteil, die Auswahl aus vielen Sätzen erzeugt Rauschen.",
              "**Achtung:** Der Test wurde jetzt gesehen. Weiteres Feintuning auf denselben Daten verfälscht ihn. Neue Bestätigung nur mit dem Forward-Journal (neue, ungesehene Daten)."]
    L += ["", f"Gemeinsamer Satz (für alle Coins gleich, gewählt auf Training+Validierung gepoolt): `{gbest[0]} {gbest[1]}`" if gbest else "Kein gemeinsamer Satz besteht Training und Validierung.",
          "", "Lesehilfe: 'Robustheit' ist der Anteil der Sätze, die Training und Validierung bestehen und im Test positiv bleiben. Liegt er unter 50 %, ist die Auswahl größtenteils Glück."]
    open(os.path.join(ROOT, "coins", "README.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
