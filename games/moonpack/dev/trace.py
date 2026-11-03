import sys, os
sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), "games/moonpack")]
from game_config import GameConfig
from gamestate import GameState
from src.wins.win_manager import WinManager
mode, criteria, sim = sys.argv[1], sys.argv[2], int(sys.argv[3])
cfg = GameConfig(); gs = GameState(cfg); gs.betmode = mode; gs.criteria = criteria
gs.win_manager = WinManager(cfg.basegame_type, cfg.freegame_type, cfg.wincap)
gs.run_spin(sim)
for e in gs.book.events:
    t = e["type"]
    if t == "reveal":
        b = [[s["name"] for s in col[1:-1]] for col in e["board"]]
        print(e["gameType"], "reveal wolves", sum(r.count("W") for r in b))
        for row in range(5): print("   ", " ".join(f"{b[r][row]:2}" for r in range(7)))
    elif t == "winInfo":
        print("   win", [(w["symbol"], w["clusterSize"], w["meta"]["clusterMult"], w["win"]/100) for w in e["wins"]])
    elif t in ("moonTier", "freeSpinTrigger", "freeSpinEnd", "finalWin"):
        print(t, {k: v for k, v in e.items() if k not in ("index", "positions")})
