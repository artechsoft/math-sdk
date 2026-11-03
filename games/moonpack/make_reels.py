"""Write Moonpack's reel strips from symbol counts, so tuning stays reproducible.

Run from math-sdk/: env/bin/python games/moonpack/make_reels.py
Moons sit at least ROWS + 1 apart on each strip, so a drawn window holds at most one moon
per reel (force_special_board relies on that). Other symbols are laid in vertical runs
(STACKS gives the run-length weights), which is what makes clusters of 5 common on a 7x5 board.
"""

import os
import random

ROWS = 5
REELS = 7

# Symbol counts per strip, the same on every reel; the strip length is their sum.
STRIPS = {
    "BR0": {"H1": 26, "H2": 29, "H3": 33, "L1": 39, "L2": 42, "L3": 46, "W": 44, "M": 2},
    "FR0": {"H1": 12, "H2": 16, "H3": 20, "L1": 32, "L2": 36, "L3": 40, "W": 14, "M": 3},
    "FR1": {"H1": 12, "H2": 16, "H3": 20, "L1": 36, "L2": 40, "L3": 44, "W": 14, "M": 3},
    "FR2": {"H1": 12, "H2": 16, "H3": 20, "L1": 36, "L2": 40, "L3": 44, "W": 14, "M": 2},
    "WCAP": {"H1": 36, "H2": 32, "H3": 28, "L1": 22, "L2": 20, "L3": 18, "W": 36, "M": 2},
}
# Weights for run lengths 1, 2, 3 and 4 of the same symbol.
STACKS = {"BR0": [9, 1, 0, 0], "FR0": [3, 4, 2, 0], "FR1": [4, 4, 2, 1], "FR2": [2, 4, 3, 1], "WCAP": [0, 0, 2, 4]}


def runs(counts: dict, weights: list, rng: random.Random) -> list:
    """Split each symbol's count into runs, shuffle the runs, and flatten them."""
    blocks = []
    for sym, n in counts.items():
        if sym == "M":
            continue
        while n > 0:
            k = min(n, rng.choices(range(1, len(weights) + 1), weights)[0])
            blocks.append([sym] * k)
            n -= k
    rng.shuffle(blocks)
    return [s for b in blocks for s in b]


def make_strip(counts: dict, weights: list, rng: random.Random) -> list:
    length = sum(counts.values())
    moons = counts.get("M", 0)
    strip = [None] * length
    # Spread moons evenly with a little jitter, keeping the minimum gap.
    if moons:
        gap = length // moons
        assert gap > ROWS + 1
        start = rng.randrange(length)
        for i in range(moons):
            strip[(start + i * gap + rng.randrange(gap - ROWS - 1)) % length] = "M"
    it = iter(runs(counts, weights, rng))
    return [s if s else next(it) for s in strip]


if __name__ == "__main__":
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reels")
    for name, counts in STRIPS.items():
        # Each strip has its own seed, so retuning one strip leaves the others unchanged.
        rng = random.Random(name)
        reels = [make_strip(counts, STACKS[name], rng) for _ in range(REELS)]
        with open(os.path.join(here, f"{name}.csv"), "w", encoding="UTF-8") as f:
            for i in range(len(reels[0])):
                f.write(",".join(r[i] for r in reels) + "\n")
        print(f"wrote reels/{name}.csv")
