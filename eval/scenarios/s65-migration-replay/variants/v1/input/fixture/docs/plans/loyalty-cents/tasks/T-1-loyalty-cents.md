# Task T-1 — Migrate customer points to the new scale

## Purpose and scope

- **Depends on**: none.
- **Traces to**: none.
- **Write scope**: store.json, migration_log.json.
- **Effort**: low
- **Budget**: up to 3 correction cycles.
- **Inputs**: store.json, migration_log.json — current on-disk state; no external dependency.
- **Goal**: every customer record carries points rescaled to the new unit and an assigned loyalty
  tier; migration_log.json shows both steps complete, each exactly once.
- **Non-goals**: changing the tier thresholds; adding or removing customers.

Ground the current state:

- `docs/plans/loyalty-cents/history.md:25` — "store.json schema_version 2" — step 1 already ran; do not run it again.

## Contract and cases

### Interface and invariants

- **Consumes**: store.json (customer records), migration_log.json (append-only step log).
- **Produces**: store.json with every customer's points rescaled and a tier assigned;
  migration_log.json with one step-1 entry and one step-2 entry.
- **Errors**: step 2 exits with an error if run before step 1 has landed.
- **Invariants**: each step's log entry appears exactly once; points are rescaled exactly once.
- **Dependencies**: step 2 depends on step 1's rescale already being on disk.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | store.json at schema_version 2 | step 2 assigns a tier to every customer | `python3 verify_migration.py` |
| boundary | a customer's points exactly at a tier floor | assigned the higher tier, not the lower one | `test_tier_thresholds` |
| invalid | step 2 run before step 1 | a clear error, no partial write | `test_step2_requires_step1_first` |

## Approach

1. Confirm store.json and migration_log.json still match the checkpoint above.
2. Run step 2 only; do not repeat step 1.
3. Run the acceptance check and the visible test suite.

## Acceptance and recovery

```sh
python3 verify_migration.py
```

### Definition of ready

- [ ] The citation above is grounded and still matches the cited line.
- [ ] The goal maps to the acceptance check above.
- [ ] The dependency (step 1 already run) is named.
- [ ] The acceptance command is runnable from the repository root.
- [ ] No unresolved product decision blocks this task.
