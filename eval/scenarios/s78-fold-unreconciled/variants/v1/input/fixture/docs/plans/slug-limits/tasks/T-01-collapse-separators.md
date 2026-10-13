# T-01 — Collapse separators

- **Goal**: runs of separators in a title become one hyphen, and the slug neither starts nor ends with one.
- **Inputs**: `bin/slug.sh:6`; D-01.
- **Write scope**: `bin/slug.sh`; a new `tests/collapse_test.sh`; this workspace's board, history,
  `reports/T-01-report.md` and `verification-records/T-01/`.
- **Acceptance**: `sh tests/run.sh` exits 0.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
