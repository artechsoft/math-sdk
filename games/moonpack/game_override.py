from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Moonpack state and repeat rules."""

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.tier = self.start_tier = 0
        self.werewolves = False

    def assign_special_sym_function(self):
        self.special_symbol_functions = {"W": [self.land_wolf]}

    def land_wolf(self, sym):
        """Wolves land worth 1; werewolves (Full Moon, Blood Moon) worth 2."""
        sym.multiplier = 2 if self.werewolves else 1

    def check_repeat(self) -> None:
        """Repeat the simulation when it misses its criteria."""
        if self.repeat is False:
            conditions = self.get_current_distribution_conditions()
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
            if conditions["force_freegame"] and not self.triggered_freegame:
                self.repeat = True
            # Moons can tumble in after the forced board, so check the tier that actually started.
            if conditions["force_freegame"] and self.start_tier != min(conditions["scatter_triggers"]):
                self.repeat = True
            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True
