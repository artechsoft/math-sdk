MOON_TIER = "moonTier"
ALPHA_MERGE = "alphaMerge"


def alpha_merge_event(gamestate, merges: list):
    """Packs merging into alphas: the alpha's cell and new value, and the cells its wolves leave."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": ALPHA_MERGE,
            # Rows offset by 1 for the padding row, like other position events.
            "merges": [
                {
                    "alpha": {"reel": r, "row": w + 1},
                    "value": value,
                    "freed": [{"reel": fr, "row": fw + 1} for fr, fw in freed],
                }
                for (r, w), value, freed in merges
            ],
        }
    )


def moon_tier_event(gamestate, seed: list, upgrade: bool = False):
    """Which bonus tier started, whether wolves are werewolves, and the Blood Moon's starting pack."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": MOON_TIER,
            "tier": gamestate.tier,
            "werewolves": gamestate.werewolves,
            "upgrade": upgrade,
            # Rows offset by 1 for the padding row, like other position events.
            "seedPack": [{"reel": r, "row": w + 1} for r, w in seed],
        }
    )
