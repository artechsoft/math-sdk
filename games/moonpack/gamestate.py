from game_override import GameStateOverride
from game_events import moon_tier_event
from src.events.events import reveal_event


class GameState(GameStateOverride):
    """Base spins and the three moon bonuses."""

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()
            self.play_tumbles()

            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        self.tier = self.start_tier = min(self.count_special_symbols(scatter_key), 5)
        # The optimizer finds each tier's books by this record.
        self.record({"tier": self.config.tier_names[self.tier]})
        super().run_freespin_from_base(scatter_key)

    def run_freespin(self):
        self.reset_fs_spin()
        self.werewolves = self.tier >= 4
        seed = []
        if self.tier == 5:
            seed = self.config.blood_moon_seed["spun" if self.betmode == "base" else "bought"]
        moon_tier_event(self, seed)

        # Wolves stay between bonus spins: each new board keeps them where the last spin left them.
        # A spun Blood Moon's starting werewolves are worth more than bought ones (config.spun_seed_value).
        sticky = [(r, w, self.create_symbol("W")) for r, w in seed]
        if self.tier == 5 and self.betmode == "base":
            for *_, sym in sticky:
                sym.multiplier = self.config.spun_seed_value
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board(emit_event=False)
            for r, w, sym in sticky:
                sym.explode = False
                self.board[r][w] = sym
            self.get_special_symbols_on_board()
            reveal_event(self)

            self.play_tumbles()
            sticky = [(r, w, self.board[r][w]) for r, w in self.wolf_positions()]

            # 4 or 5 moons raise a lower tier: werewolves from now on, and the higher tier's extra spins.
            moons = min(self.count_special_symbols("scatter"), 5)
            if moons >= 4 and moons > self.tier:
                self.tot_fs += self.config.tier_spins[moons] - self.config.tier_spins[self.tier]
                self.tier, self.werewolves = moons, True
                moon_tier_event(self, [], upgrade=True)
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()
