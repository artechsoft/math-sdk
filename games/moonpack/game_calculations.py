from src.executables.executables import Executables
from src.calculations.cluster import Cluster


class GameCalculations(Executables):
    """Wolf packs and pack-multiplied cluster wins."""

    def get_packs(self) -> list:
        """Groups of orthogonally touching wolves, as lists of (reel, row)."""
        seen, packs = set(), []
        for reel, column in enumerate(self.board):
            for row, sym in enumerate(column):
                if (reel, row) in seen or not sym.check_attribute("wolf"):
                    continue
                pack, stack = [], [(reel, row)]
                seen.add((reel, row))
                while stack:
                    r, w = stack.pop()
                    pack.append((r, w))
                    for nr, nw in ((r - 1, w), (r + 1, w), (r, w - 1), (r, w + 1)):
                        if (
                            0 <= nr < len(self.board)
                            and 0 <= nw < len(self.board[nr])
                            and (nr, nw) not in seen
                            and self.board[nr][nw].check_attribute("wolf")
                        ):
                            seen.add((nr, nw))
                            stack.append((nr, nw))
                packs.append(sorted(pack))
        return packs

    def pack_value(self, pack: list) -> int:
        """A pack multiplies by the sum of its wolves: wolves count 1, werewolves 2,
        and an alpha the total of the pack it merged from. Capped at config.pack_cap."""
        return min(sum(self.board[r][w].multiplier for r, w in pack), self.config.pack_cap)

    def evaluate_pack_clusters(self, clusters: dict) -> dict:
        """Pay each cluster, multiplied by the biggest pack it touches. Using the biggest
        (not the sum) makes merging two packs always worth more than the parts."""
        packs = self.get_packs()
        return_data = {"totalWin": 0, "wins": []}
        for sym, sym_clusters in clusters.items():
            for cluster in sym_clusters:
                size = len(cluster)
                if (size, sym) not in self.config.paytable:
                    continue
                cells = set(cluster)
                best = None
                for pack in packs:
                    if any((r + dr, w + dw) in cells for r, w in pack for dr, dw in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        if best is None or self.pack_value(pack) > self.pack_value(best):
                            best = pack
                mult = self.pack_value(best) if best else 1
                sym_win = self.config.paytable[(size, sym)]
                win = round(sym_win * mult, 2)
                return_data["totalWin"] += win
                positions = [{"reel": r, "row": w} for r, w in cluster]
                central = Cluster.get_central_cluster_position(positions)
                return_data["wins"].append(
                    {
                        "symbol": sym,
                        "clusterSize": size,
                        "win": win,
                        "positions": positions,
                        "meta": {
                            "globalMult": 1,
                            "clusterMult": mult,
                            "winWithoutMult": sym_win,
                            "overlay": {"reel": central[0], "row": central[1]},
                            # Rows offset by 1 for the padding row, like "positions" in the event.
                            "pack": [{"reel": r, "row": w + 1} for r, w in best] if best else [],
                        },
                    }
                )
                for r, w in cluster:
                    self.board[r][w].explode = True
        return_data["totalWin"] = round(return_data["totalWin"], 2)
        return return_data
