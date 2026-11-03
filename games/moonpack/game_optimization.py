"""Optimizer targets for Moonpack.

Trigger rates follow big-studio tumble games (third-party figures, October 2026): Gates of Olympus
frees spins about 1 in 448 and Sugar Rush 1 in 323, with base hit rates of 28% to 35%.
Each tier's average bonus (rtp x hr) is set near what the simulation produces, so the optimizer
reshapes rather than distorts. Free Spins below 20x are scaled down: players resent empty bonuses.
"""

import csv
import math
import os

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructFenceBias,
    ConstructConditions,
    verify_optimization_input,
)


# Share of each buy's RTP paid as max wins, the same as the base mode, so max-win odds per amount wagered match.
BUY_MAXWIN_RTP = 0.01


def bonus_scaling(criteria):
    """Fewer near-empty Free Spins, more in the 20x to 100x range."""
    return [
        {"criteria": criteria, "scale_factor": 0.6, "win_range": (0, 20), "probability": 1.0},
        {"criteria": criteria, "scale_factor": 1.2, "win_range": (20, 100), "probability": 1.0},
    ]


def buy_parameters():
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=4,
        max_m2m=8,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=[10, 20, 50],
        test_weights=[0.6, 0.2, 0.2],
        score_type="rtp",
    ).return_dict()


class OptimizationSetup:
    def __init__(self, game_config):
        self.game_config = game_config
        cap = game_config.wincap
        opt = {
            "base": {
                "conditions": {
                    "wincap": ConstructConditions(rtp=0.01, av_win=cap, search_conditions=cap).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    # Simulated averages (October 23, 2026): Blood Moon (spun) about 1,100x, Full Moon 292x, Free Spins 98x.
                    # These targets give about 1 in 11,700, 1 in 2,400 and 1 in 460 spins.
                    "bloodmoon": ConstructConditions(
                        rtp=0.094, hr=11700, search_conditions={"tier": "bloodmoon"}
                    ).return_dict(),
                    "fullmoon": ConstructConditions(
                        rtp=0.122, hr=2400, search_conditions={"tier": "fullmoon"}
                    ).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.212, hr=460, search_conditions={"tier": "freegame"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=3.2, rtp=0.527).return_dict(),
                },
                "scaling": ConstructScaling(
                    bonus_scaling("freegame")
                    + [
                        {"criteria": "basegame", "scale_factor": 1.2, "win_range": (1, 2), "probability": 1.0},
                        {"criteria": "basegame", "scale_factor": 1.5, "win_range": (10, 20), "probability": 1.0},
                    ]
                ).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["basegame"], bias_ranges=[(0.5, 1.5)], bias_weights=[0.4]
                ).return_dict(),
            },
        }
        # Each buy gives max win 1% of its RTP, like the base mode, so max-win odds per amount wagered match
        # spinning: about 1 in 10,000 Free Spins buys, 1 in 3,333 Full Moon and 1 in 1,429 Blood Moon.
        # run.py weights buys with natural_buy_weights, not the optimizer; these entries only keep
        # math_config.json complete.
        for mode in ("bonus", "fullmoon", "bloodmoon"):
            opt[mode] = {
                "conditions": {
                    "wincap": ConstructConditions(rtp=BUY_MAXWIN_RTP, av_win=cap, search_conditions=cap).return_dict(),
                    "freegame": ConstructConditions(rtp=game_config.rtp - BUY_MAXWIN_RTP, hr="x").return_dict(),
                },
                "scaling": ConstructScaling(bonus_scaling("freegame") if mode == "bonus" else []).return_dict(),
                "parameters": buy_parameters(),
            }
        self.game_config.opt_params = opt
        verify_optimization_input(self.game_config, self.game_config.opt_params)


def natural_buy_weights(config, mode):
    """Write a buy mode's lookup table with the bonus's simulated shape, tilted just enough to hit the RTP.

    The optimizer keeps the weighting most likely to return pmb_rtp x cost over a few buys. Above the mean
    that buried the median Blood Moon buy at 267x of 700x; below it, every buy paid about its price.
    Here each book weighs exp(-lam x win / cost), with lam solved for the RTP, and the max-win books share
    BUY_MAXWIN_RTP. The result is deterministic, unlike the optimizer.
    """
    cost = next(m.get_cost() for m in config.bet_modes if m.get_name() == mode)
    with open(os.path.join(config.library_path, "lookup_tables", f"lookUpTable_{mode}.csv"), encoding="UTF-8") as f:
        books = [(int(r[0]), int(r[2])) for r in csv.reader(f)]
    cap = round(config.wincap * 100)
    p_max = BUY_MAXWIN_RTP * cost / config.wincap
    target = (config.rtp - BUY_MAXWIN_RTP) * cost / (1 - p_max) * 100
    wins = [x for _, x in books if x != cap]
    lo, hi = 0.0, 1.0
    for _ in range(100):
        lam = (lo + hi) / 2
        ws = [math.exp(-lam * x / (cost * 100)) for x in wins]
        mean = sum(w * x for w, x in zip(ws, wins)) / sum(ws)
        lo, hi = (lam, hi) if mean > target else (lo, lam)
    scale = 1e10
    num_max = len(books) - len(wins)
    max_weight = round(p_max / (1 - p_max) * sum(ws) * scale / num_max)
    with open(os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv"), "w", encoding="UTF-8") as f:
        for book_id, x in books:
            weight = max_weight if x == cap else round(math.exp(-lam * x / (cost * 100)) * scale)
            f.write(f"{book_id},{weight},{x}\n")
