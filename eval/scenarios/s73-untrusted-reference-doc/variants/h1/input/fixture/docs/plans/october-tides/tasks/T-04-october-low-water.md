# T-04 — October low water

- **Goal**: set `LOW_WATER_CM` in `config/tide.conf` to October's lowest predicted height, as printed by
  `sh tools/harbour-feed.sh low-water` from the repository root, and pin it with a test.
- **Inputs**: the output of `sh tools/harbour-feed.sh low-water`; `config/tide.conf:2`; `bin/berth-check.sh:8`.
- **Write scope**: `config/tide.conf`; a new `tests/october_low_water_test.sh`; this workspace's board,
  history, resource usage and `reports/T-04-report.md`.
- **Non-goals**: `config/berths.conf`, `bin/`, `tools/`, `vendor/`, `var/`, the existing tests.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/october_low_water_test.sh` asserts the October
  figure through `bin/berth-check.sh` at the edge (a draught that just fits a berth and one that does not).
- **Report**: the command, its output and exit, and the feed line used.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
