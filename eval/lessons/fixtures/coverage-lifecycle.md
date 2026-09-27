# Synthetic v2 lifecycle ledger — coverage-table derivation golden (C9)

Six role-instances, each exercising one boundary of the corrected coverage-table recipe. Hand-derived
expected output (recomputed independently in `test_coverage_table.py`, never copied from here):

- `tokens`: Eligible = 5 (R1, R2, R3, R4, R5 each reach a terminal event; R6 has no terminal and is
  not eligible). Measured = 3 (R1, R3, R5 have a `scope: role` sidecar entry joined by exact
  `run_id`; R2 and R4 do not). Result: `3/5 (60%)`.
- `duration`: Eligible = 5 (same set as above). Measured = 2 (only R1 and R2 are a `finish` with
  `Outcome: success` and a parseable start+finish `At` pair — R3's start `At` is `n/a`, R4's
  terminal is `observe-incomplete`, R5's `Outcome` is not `success`). Result: `2/5 (40%)`.

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-20-sc/T-99/Worker/01 | start | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:00:00Z | running | n/a | n/a | n/a | synthetic |
| 2026-09-20-sc/T-99/Worker/01 | finish | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:04:00Z | success | 1 | 0 | passed | synthetic |
| 2026-09-20-sc/T-99/Worker/02 | start | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:05:00Z | running | n/a | n/a | n/a | synthetic |
| 2026-09-20-sc/T-99/Worker/02 | finish | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:09:00Z | success | 1 | 0 | passed | synthetic |
| 2026-09-20-sc/T-99/Worker/03 | start | T-99 | Worker | generic | standard | n/a | medium | n/a | running | n/a | n/a | n/a | synthetic; start time not captured |
| 2026-09-20-sc/T-99/Worker/03 | finish | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:14:00Z | success | 1 | 0 | passed | synthetic |
| 2026-09-20-sc/T-99/Worker/04 | start | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:15:00Z | running | n/a | n/a | n/a | synthetic |
| 2026-09-20-sc/T-99/Worker/04 | observe-incomplete | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:20:00Z | incomplete | n/a | n/a | n/a | coordinator-observed |
| 2026-09-20-sc/T-99/Worker/05 | start | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:21:00Z | running | n/a | n/a | n/a | synthetic |
| 2026-09-20-sc/T-99/Worker/05 | finish | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:25:00Z | failed | 1 | 0 | blocked | synthetic |
| 2026-09-20-sc/T-99/Worker/06 | start | T-99 | Worker | generic | standard | n/a | medium | 2026-09-20T10:26:00Z | running | n/a | n/a | n/a | synthetic; no terminal event observed |
