"""Simulate, optimize and check Moonpack."""

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup, natural_buy_weights
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    num_threads = 10
    rust_threads = 20
    # Each process holds its batch's books in memory, about 0.5 MB per bonus book. Batches of
    # 50,000 swapped on 32 GB; 2,000 keeps it near 1 GB per process. Books are identical either way.
    batching_size = 2000
    compression = True
    profiling = False

    num_sim_args = {
        "base": int(1e5),
        "bonus": int(1e5),
        "fullmoon": int(1e5),
        "bloodmoon": int(1e5),
    }

    run_conditions = {
        "run_sims": True,
        "run_optimization": True,
        "run_analysis": True,
        "run_format_checks": True,
    }
    target_modes = list(num_sim_args)

    config = GameConfig()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        # Only the base mode needs the optimizer; buys keep their simulated shape (see natural_buy_weights).
        OptimizationExecution().run_all_modes(config, ["base"], rust_threads)
        for mode in target_modes:
            if mode != "base":
                natural_buy_weights(config, mode)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
