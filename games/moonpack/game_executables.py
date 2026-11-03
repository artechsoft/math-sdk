from game_calculations import GameCalculations
from game_events import alpha_merge_event
from src.calculations.cluster import Cluster


class GameExecutables(GameCalculations):
    """Game dependent grouped functions."""

    def get_clusters_update_wins(self):
        """Find clusters on board and update win manager."""
        clusters = Cluster.get_clusters(self.board)
        self.win_data = self.evaluate_pack_clusters(clusters)
        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def play_tumbles(self):
        """Pay, tumble and repeat. When a drop pays nothing, packs merge into alphas and the freed
        cells tumble in; the spin ends when nothing pays or merges. Wolves and moons never explode by winning."""
        self.get_clusters_update_wins()
        self.emit_tumble_win_events()
        while not self.wincap_triggered:
            if self.win_data["totalWin"] > 0:
                self.tumble_game_board()
            elif self.merge_packs():
                self.tumble_game_board()
            else:
                break
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
        self.set_end_tumble_event()
        self.win_manager.update_gametype_wins(self.gametype)

    def wolf_positions(self) -> list:
        return [(r, w) for r, col in enumerate(self.board) for w, sym in enumerate(col) if sym.check_attribute("wolf")]

    def merge_packs(self) -> bool:
        """Each pack of 2 or more becomes one alpha wolf on its lowest cell, carrying the pack's
        multiplier. Its other wolves explode, freeing their cells. Returns whether any merged."""
        merges = []
        for pack in self.get_packs():
            if len(pack) < 2:
                continue
            r, w = max(pack, key=lambda c: (c[1], -c[0]))
            self.board[r][w].multiplier = self.pack_value(pack)
            freed = [c for c in pack if c != (r, w)]
            for fr, fw in freed:
                self.board[fr][fw].explode = True
            merges.append(((r, w), self.board[r][w].multiplier, freed))
        if merges:
            alpha_merge_event(self, merges)
        return bool(merges)
