"""Run Moonpack criteria directly (no books written) and summarize payouts.
Usage, from math-sdk/: env/bin/python <this> MODE CRITERIA N [freegame_strip | VARIANT.json]
A variant rebuilds strips in memory without editing the game: {"FR0": {symbol counts}, "stacks": {"FR0": [run weights]}}."""
import sys, os, time, statistics, json, random
sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), "games/moonpack")]
from game_config import GameConfig
from gamestate import GameState
from src.wins.win_manager import WinManager
import make_reels

mode, criteria, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
cfg = GameConfig()
variant = json.load(open(sys.argv.pop(4))) if len(sys.argv) > 4 and sys.argv[4].endswith(".json") else {}
for name in variant.keys() - {"stacks"}:
    rng = random.Random(name)
    stacks = variant.get("stacks", {}).get(name, make_reels.STACKS[name])
    cfg.reels[name] = [make_reels.make_strip(variant[name], stacks, rng) for _ in range(make_reels.REELS)]
gs = GameState(cfg)
gs.betmode = mode
gs.win_manager = WinManager(cfg.basegame_type, cfg.freegame_type, cfg.wincap)
cond = gs.get_betmode(mode)
for d in cond.get_distributions():
    if d._criteria == criteria and len(sys.argv) > 4:
        d._conditions["reel_weights"][cfg.freegame_type] = {sys.argv[4]: 1}
        d._win_criteria = None
gs.criteria = criteria
pays, t, ups = [], time.time(), 0
for sim in range(n):
    gs.run_spin(sim)
    pays.append(gs.final_win)
    ups += any(e["type"] == "moonTier" and e.get("upgrade") for e in gs.book.events)
pays.sort()
cost = cond.get_cost()
q = lambda p: pays[min(int(p * n), n - 1)]
print(f"{mode}/{criteria} n={n} {time.time()-t:.1f}s mean={statistics.mean(pays):.2f} (rtp/cost {statistics.mean(pays)/cost:.3f}) "
      f"sd={statistics.pstdev(pays):.1f} p10={q(.1)} p25={q(.25)} median={q(.5)} p75={q(.75)} p90={q(.9)} p99={q(.99)} max={pays[-1]} "
      f"under20={sum(p < 20 for p in pays)/n:.2f} zero={sum(p == 0 for p in pays)/n:.2f} ge5k={sum(p >= 5000 for p in pays)} ge10k={sum(p >= 10000 for p in pays)} ge25k={sum(p >= 25000 for p in pays)} upgrades={ups}")
