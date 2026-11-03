# Tuning probes

Run from `math-sdk/`. They play rounds in memory and write no books, so they are safe while you tune strips.

- `env/bin/python games/moonpack/dev/probe.py MODE CRITERIA N [STRIP]`: plays N rounds of one distribution and prints mean, percentiles, max, share under 20x, counts of 5,000x+ and 10,000x+, and upgrades. STRIP (for example WCAP) replaces the bonus strip and drops the win criterion, to measure tail reach. A VARIANT.json in its place rebuilds strips in memory with other counts or run weights (format in the script's docstring).
- `env/bin/python games/moonpack/dev/natural.py N [VARIANT.json]`: natural base-game spins with no forcing: hit rate, base RTP, big-win shares, std dev, moon odds, win buckets and RTP by cluster size, symbol and pack. A variant file tries other pays or BR0 counts and run weights in memory (format in the script's docstring), so several candidates can run in parallel without editing the game.
- `env/bin/python games/moonpack/dev/trace.py MODE CRITERIA SIM`: prints one round's boards and wins.

Do not edit the game while `make run` is running: its worker processes re-import the code and crash.
