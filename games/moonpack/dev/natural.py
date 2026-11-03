"""Natural base-game play: hit rate, base RTP without bonuses, and moon tier odds (no forcing, no repeats).

Usage: natural.py N [VARIANT.json]. A variant tries pays or a BR0 strip without editing the game:
{"pays": {"H1": [7 pays by size band], ...}, "BR0": {symbol counts}, "stacks": [run weights]}.
"""
import sys, os, collections, statistics, json, random
sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), "games/moonpack")]
from game_config import GameConfig
from gamestate import GameState
from src.wins.win_manager import WinManager
import make_reels
n = int(sys.argv[1])
cfg = GameConfig(); gs = GameState(cfg); gs.betmode = "base"; gs.criteria = "basegame"
gs.win_manager = WinManager(cfg.basegame_type, cfg.freegame_type, cfg.wincap)
cfg.bet_modes[0].get_distributions()  # reels BR0 only
if len(sys.argv) > 2:
    variant = json.load(open(sys.argv[2]))
    for sym, row in variant.get("pays", {}).items():
        sizes = [(5, 5), (6, 6), (7, 7), (8, 9), (10, 11), (12, 14), (15, 35)]
        for (lo, hi), pay in zip(sizes, row):
            for size in range(lo, hi + 1):
                cfg.paytable[(size, sym)] = pay
    if "BR0" in variant or "stacks" in variant:
        counts = variant.get("BR0", make_reels.STRIPS["BR0"])
        rng = random.Random("BR0")
        cfg.reels["BR0"] = [make_reels.make_strip(counts, variant.get("stacks", make_reels.STACKS["BR0"]), rng)
                            for _ in range(make_reels.REELS)]

# Tally every paying cluster by size band, symbol and whether a pack multiplied it.
by_size, by_sym, by_mult = collections.Counter(), collections.Counter(), collections.Counter()
calc = gs.get_clusters_update_wins
def tally():
    calc()
    for w in gs.win_data["wins"]:
        by_size[min(w["clusterSize"], 9)] += w["win"]; by_sym[w["symbol"]] += w["win"]
        by_mult["pack" if w["meta"]["clusterMult"] > 1 else "plain"] += w["win"]
gs.get_clusters_update_wins = tally

pays, tiers, packs = [], collections.Counter(), collections.Counter()
for sim in range(n):
    gs.reset_seed(sim); gs.reset_book(); gs.create_board_reelstrips(); gs.play_tumbles()
    pays.append(gs.win_manager.spin_win)
    tiers[min(gs.count_special_symbols("scatter"), 5)] += 1
    packs[max([len(p) for p in gs.get_packs()] or [0])] += 1
hits = [p for p in pays if p > 0]
print(f"n={n} hit rate 1 in {n/len(hits):.2f}, base RTP {sum(pays)/n:.3f}, mean hit {statistics.mean(hits):.2f}, max {max(pays)}")
print("big wins: >=5x", sum(p >= 5 for p in pays)/n, ">=10x", sum(p >= 10 for p in pays)/n, ">=50x", sum(p >= 50 for p in pays)/n, ">=100x", sum(p >= 100 for p in pays)/n)
print("std dev", round(statistics.pstdev(pays), 2))
print("moons:", {k: f"1 in {n/v:.0f}" for k, v in sorted(tiers.items())})
print("biggest pack on final board:", dict(sorted(packs.items())))
edges = [0, 0.5, 1, 2, 5, 10, 50, float("inf")]
buckets = {f"{lo}-{hi}x": sum(lo <= p < hi for p in hits) / n for lo, hi in zip(edges, edges[1:])}
print("spins by win:", {k: f"{v:.1%}" for k, v in buckets.items()}, f"under the bet {sum(p < 1 for p in hits)/len(hits):.0%} of hits")
print("RTP by cluster size (9 = 9+):", {k: round(v / n, 3) for k, v in sorted(by_size.items())})
print("RTP by symbol:", {k: round(v / n, 3) for k, v in sorted(by_sym.items())}, "| by mult:", {k: round(v / n, 3) for k, v in by_mult.items()})
