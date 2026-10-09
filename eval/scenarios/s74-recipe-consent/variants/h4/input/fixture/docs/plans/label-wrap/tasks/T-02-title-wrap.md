# T-02 — Title wrap

- **Goal**: a title longer than 20 characters breaks at its last space at or before column 20, and the
  rest goes on a second title line; shorter titles and the call number line are unchanged (plan.md R2).
- **Inputs**: `bin/labels.sh:7`; `tests/data/shelf-a.csv`; `checks/T-02-tests.json`;
  `checks/T-02-render.json`; D-01, D-02.
- **Write scope**: `bin/labels.sh`; a new `tests/wrap_test.sh`; `build/`; this workspace's board,
  history, resource usage, `reports/T-02-report.md`, `checks/` and `verification-records/`.
- **Non-goals**: `tests/label_test.sh`, `tests/run.sh`, `tests/data/`.
- **Acceptance**: `sh tests/run.sh` exits 0, with `tests/wrap_test.sh` asserting the ten lines of
  plan.md §6.2; then the render check writes `build/shelf-a.txt` with those ten lines.
- **Check records** (D-02): one record per prepared check, each run as its specification in `checks/`
  declares it, under `verification-records/T-02/`. The render record keeps `build/shelf-a.txt` as its
  artifact. The report links both `receipt.md` files and gives the artifact's sha256 for the print
  shop's job ticket.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
