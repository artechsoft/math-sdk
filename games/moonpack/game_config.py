"""Moonpack game configuration."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Singleton Moonpack configuration: 7x5 cluster pays with tumbles, wolf packs and moon tiers."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "moonpack"
        self.provider_number = 0
        self.working_name = "Moonpack"
        self.wincap = 10000.0
        self.win_type = "cluster"
        self.rtp = 0.9650
        self.construct_paths()

        self.num_reels = 7
        self.num_rows = [5] * self.num_reels

        # H1 fangs, H2 lanterns, H3 pines, L1-L3 runes. Clusters of 5 or more pay.
        sizes = [(5, 5), (6, 6), (7, 7), (8, 9), (10, 11), (12, 14), (15, 35)]
        pays = {
            "H1": [2.0, 2.5, 3.0, 4.0, 8.0, 20.0, 50.0],
            "H2": [1.5, 1.8, 2.2, 3.0, 6.0, 15.0, 40.0],
            "H3": [1.0, 1.2, 1.5, 2.5, 5.0, 10.0, 30.0],
            "L1": [0.4, 0.5, 0.8, 1.2, 2.5, 5.0, 12.0],
            "L2": [0.3, 0.4, 0.6, 1.0, 2.0, 4.0, 10.0],
            "L3": [0.2, 0.3, 0.5, 0.8, 1.5, 3.0, 8.0],
        }
        self.paytable = self.convert_range_table(
            {(size, sym): pay for sym, row in pays.items() for size, pay in zip(sizes, row)}
        )

        self.include_padding = True
        # W wolves never pay or explode; touching wolves form a pack that multiplies wins.
        # When a board settles, each pack merges into one alpha and the freed cells tumble in.
        # In bonuses wolves stay between spins, and 4 or 5 moons upgrade a lower tier.
        # M moons are the scatter.
        self.special_symbols = {"scatter": ["M"], "wolf": ["W"]}

        # Tier by moons on the board when the spin's tumbles end: 3 Free Spins, 4 Full Moon, 5+ Blood Moon.
        # Free Spins play 10 spins, Full Moon 12, Blood Moon 15; 3 moons in a bonus add 3.
        self.tier_spins = {3: 10, 4: 12, 5: 15}
        self.freespin_triggers = {
            self.basegame_type: {n: self.tier_spins[min(n, 5)] for n in range(3, 36)},
            self.freegame_type: {n: 3 for n in range(3, 36)},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        self.tier_names = {3: "freegame", 4: "fullmoon", 5: "bloodmoon"}

        # Blood Moon starts with a pack on the board: 5 wolves when spun, 3 when bought.
        self.blood_moon_seed = {
            "spun": [(2, 3), (3, 3), (4, 3), (2, 4), (3, 4)],
            "bought": [(2, 4), (3, 4), (4, 4)],
        }

        # Every pack multiplier tops out here, alphas included.
        self.pack_cap = 1000
        # Spun Blood Moon's 5 starting werewolves are worth 8 each (x40); bought, 3 worth 2 (x6).
        self.spun_seed_value = 8

        reels = {n: f"{n}.csv" for n in ("BR0", "FR0", "FR1", "FR2", "WCAP")}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        base, free = self.basegame_type, self.freegame_type

        def bonus(criteria, quota, moons, wincap=False, mode_cap=None):
            """A distribution that forces a bonus of the tier `moons` starts."""
            strip = {3: "FR0", 4: "FR1", 5: "FR2"}[moons]
            return Distribution(
                criteria=criteria,
                quota=quota,
                win_criteria=mode_cap if wincap else None,
                conditions={
                    # Each tier has its own bonus strip; wincap runs mix in the rich WCAP strip.
                    "reel_weights": {base: {"BR0": 1}, free: {strip: 1, "WCAP": 5} if wincap else {strip: 1}},
                    "scatter_triggers": {moons: 1},
                    "force_wincap": wincap,
                    "force_freegame": True,
                },
            )

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    bonus("wincap", 0.001, 5, wincap=True, mode_cap=self.wincap),
                    bonus("bloodmoon", 0.01, 5),
                    bonus("fullmoon", 0.03, 4),
                    bonus("freegame", 0.06, 3),
                    Distribution(
                        criteria="0",
                        quota=0.4,
                        win_criteria=0.0,
                        conditions={"reel_weights": {base: {"BR0": 1}}, "force_wincap": False, "force_freegame": False},
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.5,
                        conditions={"reel_weights": {base: {"BR0": 1}}, "force_wincap": False, "force_freegame": False},
                    ),
                ],
            ),
        ]
        for name, cost, moons in (("bonus", 100, 3), ("fullmoon", 300, 4), ("bloodmoon", 700, 5)):
            self.bet_modes.append(
                BetMode(
                    name=name,
                    cost=cost,
                    rtp=self.rtp,
                    max_win=self.wincap,
                    auto_close_disabled=False,
                    is_feature=False,
                    is_buybonus=True,
                    distributions=[
                        bonus("wincap", 0.001, moons, wincap=True, mode_cap=self.wincap),
                        bonus("freegame", 0.999, moons),
                    ],
                )
            )
