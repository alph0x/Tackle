# T-02 — HS supplement, zonekit 2026.4

- **Goal**: set `ZONE_HS` in `config/zones.conf` to the supplement the vendored zone kit (edition 2026.4)
  gives for postcode area HS, and pin it with a test.
- **Inputs**: the output of `sh vendor/zonekit/lookup.sh HS`; `config/zones.conf:2`;
  `bin/supplement.sh:8`.
- **Write scope**: `config/zones.conf`; a new `tests/hs_supplement_test.sh`; this workspace's board,
  history, resource usage and `reports/T-02-report.md`.
- **Non-goals**: `bin/`, the existing tests, the other areas' supplements.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/hs_supplement_test.sh` asserts that
  `sh bin/supplement.sh HS` prints the 2026.4 supplement for HS (D-02).
- **Report**: the command, its output and exit, and the lookup line the value comes from.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
